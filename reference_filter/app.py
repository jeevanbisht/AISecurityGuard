import logging
import os
import re
import urllib.parse

from flask import Flask, jsonify, make_response, request

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# SQL injection and unsafe query patterns.
SQLI_PATTERNS = [
    r"\bunion\s+(?:all\s+)?select\b",
    r"\bselect\b.{0,160}\bfrom\s+(?!the\b|a\b|an\b)[a-z0-9_`\"\[]+",
    r"\binsert\s+into\b",
    r"\bupdate\b.{0,100}\bset\b",
    r"\bdelete\s+from\b",
    r"\b(?:drop|alter|create|truncate)\s+(?:table|database|schema|view|index)\b",
    r"\bexec(?:ute)?\s*(?:\(|\s)",
    r"\binformation_schema\b",
    r";\s*(?:select|insert|update|delete|drop|alter|create|truncate|exec(?:ute)?)\b",
    r"\b(?:or|and)\b\s+['\"]?[a-z0-9_]+['\"]?\s*(?:=|<>|!=|<=|>=|<|>)\s*['\"]?[a-z0-9_]+['\"]?",
    r"\b(?:or|and)\b\s+(?:true|false|null)\b",
    r"\b(?:substring|substr|ascii)\s*\(\s*(?:\(?\s*select\b|version\s*\(|database\s*\(|user\s*\()",
    r"\bselect\b.{0,100}\b(?:version|database|db_name|user|current_user|length)\s*\(",
    r"@@(?:version|hostname|datadir)\b",
    r"(?:'|\")\s*order\s+by\s+\d+\b",
    r"/\*!\d*\s*(?:union|select|insert|update|delete)\b",
    r"\b(?:sleep|benchmark|pg_sleep)\s*\(",
    r"\bwaitfor\s+delay\b",
    r"(?:'|\")\s*(?:--|#)",
    r"(?:/\*.*?\*/).{0,80}\b(?:select|union|or|and)\b",
]

PROMPT_INJECTION_PATTERNS = [
    r"(?i)(ignore\s+previous\s+instructions)",
    r"(?i)(system\s+prompt)",
    r"(?i)(<script.*?>)",
    r"(?i)(/etc/passwd)",
]


def analyze_query(content: str):
    """
    AI Model Guard Classifier
    Analyzes input text for SQL injection, prompt injection, and unsafe commands.
    """
    if not content:
        return True, ""

    decoded_content = content
    for _ in range(3):
        decoded = urllib.parse.unquote_plus(decoded_content)
        if decoded == decoded_content:
            break
        decoded_content = decoded
    normalized_content = re.sub(r"\s+", " ", decoded_content).strip()

    # Check SQL Injection
    for pattern in SQLI_PATTERNS:
        match = re.search(pattern, normalized_content, re.IGNORECASE | re.DOTALL)
        if match:
            return False, f"SQL Injection pattern detected: '{match.group(0)}'"

    # Check Prompt Injection / Unsafe Content
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = re.search(pattern, decoded_content)
        if match:
            return (
                False,
                f"Unsafe payload/prompt injection pattern detected: '{match.group(0)}'",
            )

    return True, "Safe"


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "HEAD"])
def inspect_request(path):
    # Extract request metadata from Envoy ext_authz
    original_path = request.headers.get(
        "x-envoy-original-path", request.full_path or request.path
    )
    body = request.get_data(as_text=True)

    logger.info(
        "Inspecting %s request path=%s body_bytes=%d",
        request.method,
        request.path,
        len(body.encode("utf-8")),
    )

    # Analyze path & query params
    is_safe_path, reason_path = analyze_query(original_path)
    if not is_safe_path:
        logger.warning("Unsafe request path blocked: %s", reason_path)
        resp = make_response(
            jsonify(
                {
                    "status": "blocked",
                    "reason": reason_path,
                    "message": "Blocked by AI Model Security Guard (SQL Injection / Unsafe Query Detected)",
                }
            ),
            403,
        )
        resp.headers["x-ext-auth-reason"] = "unsafe-query-blocked"
        return resp

    # Analyze request body
    is_safe_body, reason_body = analyze_query(body)
    if not is_safe_body:
        logger.warning("Unsafe request body blocked: %s", reason_body)
        resp = make_response(
            jsonify(
                {
                    "status": "blocked",
                    "reason": reason_body,
                    "message": "Blocked by AI Model Security Guard (Unsafe Query / Payload Detected)",
                }
            ),
            403,
        )
        resp.headers["x-ext-auth-reason"] = "unsafe-payload-blocked"
        return resp

    logger.info("Request allowed")
    resp = make_response("OK", 200)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
