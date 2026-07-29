from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Server Form - AI Guard Protected</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f6f9; }
        .container { max-width: 600px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { color: #0078d4; }
        input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #0078d4; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #005a9e; }
        .result { margin-top: 20px; padding: 15px; background: #e7f3fe; border-left: 6px solid #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Protected Application Form</h2>
        <p>Search products or submit queries:</p>
        <form action="/search" method="GET">
            <input type="text" name="q" placeholder="e.g. laptops, phones..." value="{{ query or '' }}" required>
            <button type="submit">Submit Query</button>
        </form>

        {% if query %}
        <div class="result">
            <h3>Backend WebServer Response</h3>
            <p><strong>Query processed successfully:</strong> {{ query }}</p>
            <p><em>Status: Safe query passed through Envoy + AI Model Guard filter.</em></p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, query=None)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.args.get("q") or request.form.get("q") or ""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        query = data.get("query", query)

    if request.headers.get("Accept") == "application/json" or request.is_json:
        return jsonify(
            {
                "status": "success",
                "message": "Query processed by backend WebServer",
                "query": query,
                "data": [
                    f"Result item for '{query}' #1",
                    f"Result item for '{query}' #2",
                ],
            }
        )

    return render_template_string(HTML_TEMPLATE, query=query)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
