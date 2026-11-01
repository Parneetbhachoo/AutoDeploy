
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <html>
        <head>
            <title>AutoDeploy</title>
        </head>
        <body>
            <h1>Welcome to AutoDeploy!</h1>
            <p>Automated CI/CD with Failure Recovery</p>
            <p>Application is running successfully.</p>
        </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "AutoDeploy",
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
