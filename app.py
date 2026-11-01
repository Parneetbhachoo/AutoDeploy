
from flask import Flask, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

APP_VERSION = "1.0.0"

# Records when this application process starts.
PROCESS_START_TIME = datetime.now(timezone.utc).strftime(
    "%Y-%m-%d %H:%M:%S UTC"
)


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoDeploy</title>
    </head>
    <body>
        <h1>Welcome to AutoDeploy CI/CD Platform! version 2</h1>
        <p>Automated CI/CD with Failure Recovery</p>
        <p>Application is running successfully.</p>
        <p><a href="/dashboard">Open Deployment Dashboard</a></p>
    </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "AutoDeploy",
        "version": APP_VERSION
    })


@app.route("/dashboard")
def dashboard():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AutoDeploy Dashboard</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 40px 20px;
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #f1f5f9;
            }}

            .container {{
                max-width: 900px;
                margin: auto;
            }}

            h1 {{
                color: #60a5fa;
            }}

            .subtitle {{
                color: #94a3b8;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}

            .card {{
                background: #1e293b;
                padding: 24px;
                border: 1px solid #334155;
                border-radius: 14px;
            }}

            .card h2 {{
                font-size: 18px;
                margin-top: 0;
                color: #cbd5e1;
            }}

            .value {{
                font-size: 22px;
                font-weight: bold;
            }}

            .healthy {{
                color: #4ade80;
            }}

            .info {{
                color: #93c5fd;
                font-size: 14px;
                overflow-wrap: anywhere;
            }}

            a {{
                color: #60a5fa;
            }}

            .footer {{
                margin-top: 30px;
                color: #94a3b8;
                font-size: 14px;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>AutoDeploy Dashboard 🚀</h1>
            <p class="subtitle">
                Automated CI/CD and deployment monitoring
            </p>

            <div class="grid">
                <div class="card">
                    <h2>Application Status</h2>
                    <p class="value healthy">● Running</p>
                    <p class="info">Application: AutoDeploy</p>
                </div>

                <div class="card">
                    <h2>Application Version</h2>
                    <p class="value">v{APP_VERSION}</p>
                    <p class="info">Currently configured version</p>
                </div>

                <div class="card">
                    <h2>Health Check</h2>
                    <p class="value healthy">Available</p>
                    <p><a href="/health">View health response →</a></p>
                </div>

                <div class="card">
                    <h2>Process Start Time</h2>
                    <p class="info">{PROCESS_START_TIME}</p>
                    <p class="info">
                        This time resets when the application process restarts.
                    </p>
                </div>
            </div>

            <p class="footer">
                AutoDeploy · Powered by Flask, Docker, GitHub Actions and AWS
            </p>

            <p><a href="/">← Back to homepage</a></p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
