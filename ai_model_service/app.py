import logging
import os
import re
import urllib.parse

import torch
from flask import Flask, jsonify, make_response, request
from transformers import MobileBertForSequenceClassification, MobileBertTokenizer

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

MODEL_ID = os.getenv(
    "SQL_INJECTION_MODEL_ID",
    "cssupport/mobilebert-sql-injection-detect",
)
TOKENIZER_ID = os.getenv(
    "SQL_INJECTION_TOKENIZER_ID",
    "google/mobilebert-uncased",
)
SQL_INJECTION_THRESHOLD = float(os.getenv("SQL_INJECTION_THRESHOLD", "0.70"))
SQL_INJECTION_CLASS_ID = 1

SQL_INJECTION_PATTERNS = [
    r"\bunion\s+(?:all\s+)?select\b",
    r"\bselect\b.{0,160}\bfrom\s+(?!the\b|a\b|an\b)[a-z0-9_`\"\[]+",
    r"\b(?:insert\s+into|delete\s+from)\b",
    r"\bupdate\b.{0,100}\bset\b",
    r"\b(?:drop|alter|create|truncate)\s+(?:table|database|schema|view)\b",
    r"\b(?:or|and)\b\s+['\"]?[a-z0-9_]+['\"]?\s*=\s*['\"]?[a-z0-9_]+['\"]?",
    r";\s*(?:select|insert|update|delete|drop|alter|create|truncate)\b",
]

PROMPT_INJECTION_PATTERNS = [
    r"(?i)(ignore\s+previous\s+instructions)",
    r"(?i)(system\s+prompt)",
    r"(?i)(<script.*?>)",
    r"(?i)(/etc/passwd)",
]

tokenizer = None
model = None


def load_model():
    global tokenizer, model
    if tokenizer is None or model is None:
        logger.info("Loading SQL injection model: %s", MODEL_ID)
        tokenizer = MobileBertTokenizer.from_pretrained(TOKENIZER_ID)
        model = MobileBertForSequenceClassification.from_pretrained(MODEL_ID)
        model.eval()
        logger.info("SQL injection model loaded")
    return tokenizer, model


def decode_content(content: str) -> str:
    decoded_content = content
    for _ in range(3):
        decoded = urllib.parse.unquote_plus(decoded_content)
        if decoded == decoded_content:
            break
        decoded_content = decoded
    return re.sub(r"\s+", " ", decoded_content).strip()


def strip_authorization_prefix(path: str) -> str:
    if path == "/check":
        return "/"
    if path.startswith("/check/"):
        return path[len("/check") :]
    return path


def predict_sql_injection(content: str) -> float:
    loaded_tokenizer, loaded_model = load_model()
    inputs = loaded_tokenizer(
        content,
        padding=False,
        truncation=True,
        return_tensors="pt",
        max_length=512,
    )

    with torch.inference_mode():
        logits = loaded_model(**inputs).logits

    probabilities = torch.softmax(logits, dim=-1)
    return probabilities[0, SQL_INJECTION_CLASS_ID].item()


def analyze_query(content: str):
    """Classify text with MobileBERT and retain non-SQL prompt checks."""
    if not content:
        return True, ""

    normalized_content = decode_content(content)
    for pattern in SQL_INJECTION_PATTERNS:
        match = re.search(pattern, normalized_content, re.IGNORECASE | re.DOTALL)
        if match:
            return False, f"SQL injection pattern detected: '{match.group(0)}'"

    sql_injection_probability = predict_sql_injection(normalized_content)
    if sql_injection_probability >= SQL_INJECTION_THRESHOLD:
        return (
            False,
            "SQL injection detected by MobileBERT "
            f"(confidence: {sql_injection_probability:.3f})",
        )

    for pattern in PROMPT_INJECTION_PATTERNS:
        match = re.search(pattern, normalized_content)
        if match:
            return (
                False,
                f"Unsafe payload/prompt injection pattern detected: '{match.group(0)}'",
            )

    return True, "Safe"


def blocked_response(reason: str, header_reason: str):
    response = make_response(
        jsonify(
            {
                "status": "blocked",
                "reason": reason,
                "message": "Blocked by AI Model Security Guard",
            }
        ),
        403,
    )
    response.headers["x-ext-auth-reason"] = header_reason
    return response


@app.route(
    "/",
    defaults={"path": ""},
    methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
)
@app.route(
    "/<path:path>",
    methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
)
def inspect_request(path):
    original_path = request.headers.get(
        "x-envoy-original-path",
        request.full_path or request.path,
    )
    original_path = strip_authorization_prefix(original_path)
    body = request.get_data(as_text=True)

    logger.info(
        "Inspecting %s request path=%s body_bytes=%d",
        request.method,
        request.path,
        len(body.encode("utf-8")),
    )

    is_safe_path, reason_path = analyze_query(original_path)
    if not is_safe_path:
        logger.warning("Unsafe request path blocked: %s", reason_path)
        return blocked_response(reason_path, "unsafe-query-blocked")

    is_safe_body, reason_body = analyze_query(body)
    if not is_safe_body:
        logger.warning("Unsafe request body blocked: %s", reason_body)
        return blocked_response(reason_body, "unsafe-payload-blocked")

    logger.info("Request allowed")
    return make_response("OK", 200)


if __name__ == "__main__":
    load_model()
    app.run(host="0.0.0.0", port=5000)
