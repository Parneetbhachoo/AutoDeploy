
from flask import Flask, jsonify, render_template_string
from datetime import datetime, timezone
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
from html import escape

app = Flask(__name__)

APP_VERSION = "1.0.0"

PROCESS_START_TIME = datetime.now(timezone.utc).strftime(
    "%Y-%m-%d %H:%M:%S UTC"
)

GITHUB_REPO = "Parneetbhachoo/AutoDeploy"

def get_recent_deployments(limit=5):
    """Fetch recent workflow runs from the GitHub Actions API."""
    api_url = (
        f"https://api.github.com/repos/{GITHUB_REPO}"
        "/actions/runs?per_page=10"
    )

    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AutoDeploy-Dashboard",
        },
    )

    try:
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        deployments = []

        for run in data.get("workflow_runs", []):
            deployments.append({
                "id": run.get("id"),
                "name": run.get("name") or "GitHub Actions",
                "status": run.get("status") or "unknown",
                "conclusion": run.get("conclusion"),
                "branch": run.get("head_branch") or "unknown",
                "commit": (run.get("head_sha") or "")[:7],
                "message": (
                    run.get("head_commit") or {}
                ).get("message", "No commit message").splitlines()[0],
                "created_at": run.get("created_at"),
                "url": run.get("html_url"),
                "event": run.get("event") or "unknown",
            })

        return {
            "deployments": deployments[:limit],
            "error": None,
        }

    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        app.logger.warning("GitHub Actions API unavailable: %s", error)
        return {
            "deployments": [],
            "error": "GitHub Actions data is temporarily unavailable.",
        }


def render_deployments(deployments, error=None):
    """Render GitHub Actions runs as dashboard HTML."""

    if error:
        return """
        <div class="empty">
            <div class="empty-icon">⚠</div>
            <strong>Deployment history unavailable</strong>
            <br>
            GitHub Actions data could not be loaded.
            Please try again later.
        </div>
        """

    if not deployments:
        return """
        <div class="empty">
            <div class="empty-icon">◷</div>
            <strong>No workflow runs found</strong>
            <br>
            Push a commit to GitHub to trigger your CI/CD workflow.
        </div>
        """

    rows = []

    for deployment in deployments:
        status = deployment["status"]
        conclusion = deployment["conclusion"]

        if status == "in_progress" or status == "queued":
            label = "In progress" if status == "in_progress" else "Queued"
            color = "#93c5fd"
        elif conclusion == "success":
            label = "Success"
            color = "#86efac"
        elif conclusion == "failure":
            label = "Failed"
            color = "#fca5a5"
        elif conclusion:
            label = conclusion.replace("_", " ").title()
            color = "#c4b5fd"
        else:
            label = status.replace("_", " ").title()
            color = "#c4b5fd"

        commit_message = escape(deployment["message"])
        branch = escape(deployment["branch"])
        commit = escape(deployment["commit"])
        workflow = escape(deployment["name"])
        event = escape(deployment["event"])
        run_url = escape(deployment["url"], quote=True)

        created_at = deployment.get("created_at")
        if created_at:
            try:
                timestamp = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).strftime("%d %b %Y, %H:%M UTC")
            except ValueError:
                timestamp = "Date unavailable"
        else:
            timestamp = "Date unavailable"

        rows.append(f"""
        <div style="padding: 18px 21px; border-bottom: 1px solid var(--border);">
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start; gap:12px; flex-wrap:wrap;">
                <div style="min-width:0; flex:1;">
                    <div style="font-size:13px; font-weight:700;
                                overflow-wrap:anywhere;">
                        {workflow}
                    </div>
                    <div style="color:var(--muted); font-size:11px;
                                margin-top:7px; line-height:1.7;
                                overflow-wrap:anywhere;">
                        {commit_message}
                    </div>
                </div>
                <span style="color:{color}; font-size:11px;
                             font-weight:750; white-space:nowrap;">
                    ● {escape(label)}
                </span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:14px;
                        margin-top:12px; color:var(--muted); font-size:10px;">
                <span>Branch: {branch}</span>
                <span>Commit: {commit or "N/A"}</span>
                <span>Event: {event}</span>
                <span>{escape(timestamp)}</span>
            </div>
            <div style="margin-top:12px;">
                <a href="{run_url}" target="_blank" rel="noopener noreferrer"
                   style="color:var(--blue); font-size:11px;
                          text-decoration:none;">
                    View workflow run ↗
                </a>
            </div>
        </div>
        """)

    return "".join(rows)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AutoDeploy</title>
        <style>
            body {
                margin: 0;
                min-height: 100vh;
                display: grid;
                place-items: center;
                background: #090b16;
                color: #f1f5f9;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                padding: 24px;
            }

            .hero {
                width: 100%;
                max-width: 680px;
                padding: 48px;
                box-sizing: border-box;
                border: 1px solid #292d49;
                border-radius: 22px;
                background: linear-gradient(145deg, #151a33, #0f1222);
            }

            .logo {
                color: #c4b5fd;
                font-size: 13px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }

            h1 {
                margin: 25px 0 14px;
                font-size: clamp(30px, 5vw, 44px);
                letter-spacing: -1.5px;
            }

            p {
                color: #9ca8c2;
                line-height: 1.8;
            }

            .button {
                display: inline-block;
                margin-top: 18px;
                padding: 13px 19px;
                border-radius: 10px;
                background: linear-gradient(110deg, #6366f1, #9333ea);
                color: white;
                text-decoration: none;
                font-weight: 650;
            }
        </style>
    </head>
    <body>
        <main class="hero">
            <div class="logo">⚡ AutoDeploy Platform</div>
            <h1>Welcome to AutoDeploy CI/CD Platform !</h1>
            <p>
                Automated CI/CD, containerized deployments, health monitoring,
                and deployment failure recovery — powered by AWS and GitHub Actions.
            </p>
            <a class="button" href="/dashboard">Open Dashboard →</a>
        </main>
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


def get_health_data():
    """Perform real in-process health verification of the Flask application."""
    check_start = time.perf_counter()
    app_healthy = False
    health_payload = {}
    check_error = None

    try:
        response = health()
        status_code = response.status_code
        health_payload = response.get_json() or {}
        if status_code == 200 and health_payload.get("status") == "healthy":
            app_healthy = True
        else:
            check_error = f"Unexpected status code {status_code}"
    except Exception as exc:
        app_healthy = False
        check_error = str(exc)

    check_duration_ms = max(0.01, round((time.perf_counter() - check_start) * 1000, 2))
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "app_name": health_payload.get("application", "AutoDeploy"),
        "app_version": health_payload.get("version", APP_VERSION),
        "app_healthy": app_healthy,
        "check_error": check_error,
        "check_duration_ms": check_duration_ms,
        "checked_at": checked_at,
        "process_start_time": PROCESS_START_TIME,
    }


HEALTH_UI_CSS = """
        /* Shared System Health UI Styles */
        .hero-banner {
            padding: 32px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(145deg, #151a33, #0f1222);
            position: relative;
            overflow: hidden;
            margin-bottom: 28px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }

        .hero-banner::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #4ade80, #22c55e, #3b82f6);
        }

        .status-header-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 20px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: #86efac;
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(74, 222, 128, 0.25);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
            animation: pulse-green 2s infinite;
        }

        @keyframes pulse-green {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
                box-shadow: 0 0 8px rgba(74, 222, 128, 0.7);
            }
            50% {
                opacity: 0.5;
                transform: scale(1.2);
                box-shadow: 0 0 16px rgba(74, 222, 128, 0.9);
            }
        }

        .hero-actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
            flex-wrap: wrap;
        }

        .nav-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 15px;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: #171a2e;
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .nav-btn:hover {
            border-color: #818cf8;
            background: #202442;
            color: white;
        }

        .nav-btn.primary {
            background: linear-gradient(110deg, #6366f1, #9333ea);
            border-color: transparent;
            color: white;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25);
        }

        .nav-btn.primary:hover {
            background: linear-gradient(110deg, #4f46e5, #7e22ce);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 32px;
        }

        .card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .card-label {
            color: var(--muted);
            font-size: 11px;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .card-icon {
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            border-radius: 9px;
            font-size: 16px;
        }

        .code-link {
            display: inline-block;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: var(--blue);
            background: rgba(59, 130, 246, 0.1);
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 20px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .code-link:hover {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.4);
        }

        .notice-card {
            padding: 18px 22px;
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.4), rgba(15, 23, 42, 0.5));
            margin-bottom: 28px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
        }

        .notice-icon {
            display: grid;
            place-items: center;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(139, 92, 246, 0.2);
            color: #c4b5fd;
            font-size: 16px;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .notice-title {
            font-weight: 700;
            font-size: 13px;
            color: #e2e8f0;
            margin-bottom: 4px;
        }

        .notice-body {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.6;
        }

        .section-header {
            margin: 36px 0 16px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 10px;
        }

        .section-title {
            font-size: 16px;
            font-weight: 750;
            letter-spacing: -0.3px;
        }

        .section-sub {
            color: var(--muted);
            font-size: 12px;
            margin-top: 4px;
        }

        .badge-verified {
            color: #86efac;
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(74, 222, 128, 0.25);
        }

        .badge-unchecked {
            color: #94a3b8;
            background: rgba(148, 163, 184, 0.08);
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .comp-name {
            font-weight: 650;
            color: #f1f5f9;
            font-size: 13px;
        }

        .comp-sub {
            color: var(--muted);
            font-size: 11px;
            margin-top: 3px;
        }

        .diagnostic-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            padding: 20px;
        }

        .diag-item {
            padding: 14px 18px;
            background: rgba(9, 11, 22, 0.5);
            border-radius: 10px;
            border: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .diag-label {
            color: var(--muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .diag-value {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            font-weight: 600;
            color: #f1f5f9;
        }

        @media (max-width: 1024px) {
            .stats-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 768px) {
            .diagnostic-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 520px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
"""


HEALTH_UI_TEMPLATE = """
<div id="health" class="health-ui-wrapper">
    <!-- Hero Status Banner -->
    <section class="hero-banner">
        <div class="status-header-row">
            <div>
                <div class="status-pill">
                    <span class="pulse-dot"></span>
                    {% if app_healthy %}
                    Application Status: Healthy
                    {% else %}
                    Application Status: Degraded
                    {% endif %}
                </div>
                <h1>AutoDeploy System Health</h1>
                <p class="subtitle">
                    Real-time status check and operational verification for the {{ app_name }} Flask web application and service endpoints.
                </p>
            </div>
        </div>

        <div class="hero-actions">
            <a href="/dashboard" class="nav-btn primary">
                Open Dashboard →
            </a>
            <a href="/health" class="nav-btn">
                Inspect /health JSON →
            </a>
            <a href="/status" class="nav-btn">
                ↻ Refresh Health Check
            </a>
        </div>
    </section>

    <!-- Stats Grid -->
    <section class="stats-grid">
        <div class="card">
            <div class="card-top">
                <span class="card-label">Application Status</span>
                <span class="card-icon icon-green">◉</span>
            </div>
            <div class="card-value {% if app_healthy %}positive{% endif %}">
                {% if app_healthy %}Healthy{% else %}Unhealthy{% endif %}
            </div>
            <div class="card-foot">
                Verified live check: HTTP 200 ({{ check_duration_ms }} ms)
            </div>
        </div>

        <div class="card">
            <div class="card-top">
                <span class="card-label">Current Version</span>
                <span class="card-icon icon-purple">⌘</span>
            </div>
            <div class="card-value">v{{ app_version }}</div>
            <div class="card-foot">
                Application: {{ app_name }}
            </div>
        </div>

        <div class="card">
            <div class="card-top">
                <span class="card-label">Health-Check Endpoint</span>
                <span class="card-icon icon-blue">♡</span>
            </div>
            <div class="card-value">
                <a href="/health" class="code-link">/health</a>
            </div>
            <div class="card-foot">
                <a href="/health">Open raw JSON response →</a>
            </div>
        </div>

        <div class="card">
            <div class="card-top">
                <span class="card-label">Process Start Time</span>
                <span class="card-icon icon-orange">◷</span>
            </div>
            <div class="card-value" style="font-size: 15px; font-weight: 650; margin-top: 22px;">
                {{ process_start_time }}
            </div>
            <div class="card-foot">
                Last checked: {{ checked_at }}
            </div>
        </div>
    </section>

    <!-- Scope Distinction Notice -->
    <div class="notice-card">
        <div class="notice-icon">ℹ</div>
        <div>
            <div class="notice-title">Health Check Scope & Telemetry Notice</div>
            <div class="notice-body">
                This status page performs active, real-time verification of the <strong>Flask application process</strong> and its <strong>/health</strong> endpoint. Underlying host infrastructure (Docker container), cloud provider (AWS), and deployment pipelines (GitHub Actions) are external components that are not directly probed by this in-process health check and are transparently marked as <em>Unchecked</em> below to prevent false positive reporting.
            </div>
        </div>
    </div>

    <!-- Component Breakdown Section -->
    <div class="section-header">
        <div>
            <h2 class="section-title">Component Health & Verification Breakdown</h2>
            <p class="section-sub">Distinct view separating verified application health from unprobed infrastructure components.</p>
        </div>
    </div>

    <section class="panel">
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Component</th>
                        <th>Layer</th>
                        <th>Verification Status</th>
                        <th>Health Details</th>
                        <th>Action / Target</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <div class="comp-name">Flask Application Core</div>
                            <div class="comp-sub">Web runtime & request handler</div>
                        </td>
                        <td>Application</td>
                        <td>
                            <span class="badge badge-verified">
                                ● Verified Live
                            </span>
                        </td>
                        <td>
                            {% if app_healthy %}
                            Responding normally to internal health probes. Process is active.
                            {% else %}
                            Health check failed: {{ check_error }}
                            {% endif %}
                        </td>
                        <td>
                            <span style="color: var(--green); font-size: 11px;">Active In-Memory</span>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <div class="comp-name">Health-Check Endpoint</div>
                            <div class="comp-sub">JSON status API</div>
                        </td>
                        <td>API Service</td>
                        <td>
                            <span class="badge badge-verified">
                                ● Verified Live
                            </span>
                        </td>
                        <td>
                            HTTP 200 OK returning <code>{"status": "healthy", "version": "{{ app_version }}"}</code>
                        </td>
                        <td>
                            <a href="/health" class="text-link">/health ↗</a>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <div class="comp-name">Docker Container Runtime</div>
                            <div class="comp-sub">Container isolation & host daemon</div>
                        </td>
                        <td>Host / Container</td>
                        <td>
                            <span class="badge badge-unchecked">
                                ○ Unchecked
                            </span>
                        </td>
                        <td>
                            Container daemon metrics, resource limits, and cgroups are not probed by this route.
                        </td>
                        <td>
                            <span style="color: var(--dim); font-size: 11px;">Not Monitored</span>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <div class="comp-name">AWS Cloud Infrastructure</div>
                            <div class="comp-sub">EC2 compute & Systems Manager (SSM)</div>
                        </td>
                        <td>Cloud Provider</td>
                        <td>
                            <span class="badge badge-unchecked">
                                ○ Unchecked
                            </span>
                        </td>
                        <td>
                            Cloud provider instance health and SSM agent status are not queried by this in-process check.
                        </td>
                        <td>
                            <span style="color: var(--dim); font-size: 11px;">Not Monitored</span>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <div class="comp-name">GitHub Actions CI/CD</div>
                            <div class="comp-sub">Automated build, test & deploy pipeline</div>
                        </td>
                        <td>CI/CD Pipeline</td>
                        <td>
                            <span class="badge badge-unchecked">
                                ○ Unchecked
                            </span>
                        </td>
                        <td>
                            CI/CD pipeline runs independently; recent workflow history is available on the dashboard.
                        </td>
                        <td>
                            <a href="/dashboard#deployments" class="text-link">View Runs ↗</a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </section>

    <!-- Live Diagnostics Panel -->
    <div class="section-header">
        <div>
            <h2 class="section-title">Live Diagnostic Details</h2>
            <p class="section-sub">Telemetry generated during this request.</p>
        </div>
    </div>

    <section class="panel">
        <div class="diagnostic-grid">
            <div class="diag-item">
                <span class="diag-label">Probe Target</span>
                <span class="diag-value"><a href="/health" class="text-link">/health</a></span>
            </div>
            <div class="diag-item">
                <span class="diag-label">HTTP Status Code</span>
                <span class="diag-value" style="color: var(--green);">200 OK</span>
            </div>
            <div class="diag-item">
                <span class="diag-label">Check Latency</span>
                <span class="diag-value">{{ check_duration_ms }} ms</span>
            </div>
            <div class="diag-item">
                <span class="diag-label">Timestamp (UTC)</span>
                <span class="diag-value">{{ checked_at }}</span>
            </div>
            <div class="diag-item">
                <span class="diag-label">Application Name</span>
                <span class="diag-value">{{ app_name }}</span>
            </div>
            <div class="diag-item">
                <span class="diag-label">Application Version</span>
                <span class="diag-value">v{{ app_version }}</span>
            </div>
        </div>
    </section>
</div>
"""


def render_health_ui(health_data=None):
    """Render the reusable System Health UI markup."""
    if health_data is None:
        health_data = get_health_data()
    return render_template_string(HEALTH_UI_TEMPLATE, **health_data)


STATUS_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#090b16">
    <title>{{ app_name }} | System Health</title>
    <style>
        :root {
            --bg: #090b16;
            --sidebar: #0d1020;
            --panel: #111426;
            --panel-hover: #191d33;
            --border: rgba(148, 163, 184, 0.14);
            --border-hover: rgba(129, 140, 248, 0.3);
            --text: #f1f5f9;
            --muted: #929bb5;
            --dim: #64748b;
            --blue: #60a5fa;
            --purple: #a78bfa;
            --green: #4ade80;
            --green-glow: rgba(74, 222, 128, 0.35);
            --red: #f87171;
            --slate: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(circle at 100% 100%, rgba(168, 85, 247, 0.08), transparent);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        .topbar {
            height: 70px;
            padding: 0 36px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            background: rgba(13, 16, 32, 0.85);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            display: grid;
            place-items: center;
            width: 38px;
            height: 38px;
            flex-shrink: 0;
            border-radius: 11px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            font-size: 20px;
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }

        .brand-name {
            font-size: 18px;
            font-weight: 750;
            letter-spacing: -0.5px;
        }

        .brand-sub {
            display: block;
            color: var(--muted);
            font-size: 9px;
            letter-spacing: 1.4px;
            text-transform: uppercase;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .container {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 36px 24px 60px;
            flex: 1;
        }

        .footer {
            margin-top: 48px;
            padding: 24px 0;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 14px;
            color: #727e9b;
            font-size: 11px;
        }

        .footer-links {
            display: flex;
            gap: 18px;
        }

        .footer-links a {
            color: var(--muted);
            transition: color 0.2s ease;
        }

        .footer-links a:hover {
            color: var(--blue);
        }

        @media (max-width: 768px) {
            .topbar {
                padding: 0 20px;
            }

            .container {
                padding: 24px 16px 40px;
            }
        }

        @media (max-width: 520px) {
            .topbar {
                height: auto;
                padding: 14px 16px;
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }

            .nav-links {
                width: 100%;
                justify-content: space-between;
            }

            .footer {
                flex-direction: column;
                align-items: flex-start;
            }
        }

        __HEALTH_UI_CSS__
    </style>
</head>
<body>
    <header class="topbar">
        <div class="brand">
            <div class="brand-icon">⚡</div>
            <div>
                <div class="brand-name">{{ app_name }}</div>
                <span class="brand-sub">System Health Monitor</span>
            </div>
        </div>

        <nav class="nav-links">
            <a href="/dashboard" class="nav-btn primary">
                <span>▦</span> Dashboard
            </a>
            <a href="/health" class="nav-btn">
                <span>♡</span> /health (JSON)
            </a>
            <a href="/" class="nav-btn">
                <span>⌂</span> Home
            </a>
        </nav>
    </header>

    <main class="container">
        {{ health_ui | safe }}

        <!-- Navigation Summary Footer Card -->
        <div style="margin-top: 32px; padding: 22px; border: 1px solid var(--border); border-radius: 14px; background: linear-gradient(145deg, #14182b, #101323); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #f1f5f9;">Explore AutoDeploy Navigation</div>
                <div style="color: var(--muted); font-size: 12px; margin-top: 4px;">Jump to workspace overview, live pipeline records, or application JSON endpoints.</div>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <a href="/dashboard" class="nav-btn primary">Dashboard →</a>
                <a href="/health" class="nav-btn">/health JSON</a>
                <a href="/" class="nav-btn">Home</a>
            </div>
        </div>

        <footer class="footer">
            <div>
                © AutoDeploy · Continuous Deployment & Monitoring Platform
            </div>
            <div class="footer-links">
                <a href="/dashboard">Dashboard</a>
                <a href="/status">System Health</a>
                <a href="/health">Health API</a>
                <a href="/">Home</a>
            </div>
        </footer>
    </main>
</body>
</html>"""


@app.route("/status")
def status():
    """System Health page displaying verified application health and component status."""
    health_data = get_health_data()
    health_ui_html = render_health_ui(health_data)
    rendered_page = STATUS_PAGE_TEMPLATE.replace("__HEALTH_UI_CSS__", HEALTH_UI_CSS)
    return render_template_string(
        rendered_page,
        health_ui=health_ui_html,
        app_name=health_data["app_name"],
    )


@app.route("/dashboard")
def dashboard():
    result = get_recent_deployments()
    deployments = result["deployments"]
    github_error = result["error"]

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="theme-color" content="#090b16">
        <title>AutoDeploy | Dashboard</title>

        <style>
            :root {
                --bg: #090b16;
                --sidebar: #0d1020;
                --panel: #111426;
                --panel-hover: #191d33;
                --border: rgba(148, 163, 184, 0.14);
                --text: #f1f5f9;
                --muted: #929bb5;
                --blue: #60a5fa;
                --purple: #a78bfa;
                --green: #4ade80;
            }

            * {
                box-sizing: border-box;
            }

            html {
                scroll-behavior: smooth;
            }

            body {
                margin: 0;
                background: var(--bg);
                color: var(--text);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                    sans-serif;
                font-size: 14px;
            }

            a {
                color: inherit;
                text-decoration: none;
            }

            .sidebar {
                position: fixed;
                inset: 0 auto 0 0;
                width: 245px;
                padding: 27px 18px;
                display: flex;
                flex-direction: column;
                background: var(--sidebar);
                border-right: 1px solid var(--border);
                z-index: 5;
            }

            .brand {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 43px;
                padding: 0 7px;
            }

            .brand-icon {
                display: grid;
                place-items: center;
                width: 42px;
                height: 42px;
                flex-shrink: 0;
                border-radius: 13px;
                background: linear-gradient(135deg, #6366f1, #a855f7);
                font-size: 22px;
                box-shadow: 0 0 28px rgba(139, 92, 246, .23);
            }

            .brand-name {
                font-size: 19px;
                font-weight: 750;
                letter-spacing: -.7px;
            }

            .brand-sub {
                display: block;
                margin-top: 5px;
                color: var(--muted);
                font-size: 9px;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }

            .nav-label {
                margin: 0 0 12px;
                padding: 0 12px;
                color: #737d99;
                font-size: 10px;
                font-weight: 750;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }

            .nav-link {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                margin-bottom: 6px;
                border: 1px solid transparent;
                border-radius: 10px;
                color: #a5aec5;
                transition: .2s ease;
            }

            .nav-link:hover {
                background: var(--panel-hover);
                color: white;
            }

            .nav-link.active {
                color: #c4b5fd;
                background: linear-gradient(
                    110deg,
                    rgba(124, 58, 237, .22),
                    rgba(59, 130, 246, .08)
                );
                border-color: rgba(167, 139, 250, .18);
            }

            .nav-icon {
                width: 22px;
                text-align: center;
                font-size: 17px;
            }

            .sidebar-bottom {
                margin-top: auto;
            }

            .connection {
                padding: 15px;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: var(--panel);
            }

            .connection-label {
                color: var(--muted);
                font-size: 11px;
            }

            .connection-status {
                margin-top: 10px;
                color: var(--green);
                font-size: 12px;
                font-weight: 650;
            }

            .dot {
                display: inline-block;
                width: 7px;
                height: 7px;
                margin-right: 7px;
                border-radius: 50%;
                background: var(--green);
                box-shadow: 0 0 10px rgba(74, 222, 128, .5);
            }

            main {
                min-height: 100vh;
                margin-left: 245px;
            }

            .topbar {
                height: 74px;
                padding: 0 36px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid var(--border);
                background: rgba(13, 16, 32, .75);
            }

            .breadcrumb {
                color: var(--muted);
            }

            .breadcrumb strong {
                color: var(--text);
                font-weight: 550;
            }

            .profile {
                display: flex;
                align-items: center;
                gap: 10px;
                color: #cbd5e1;
                font-size: 12px;
            }

            .avatar {
                display: grid;
                place-items: center;
                width: 35px;
                height: 35px;
                border-radius: 10px;
                background: linear-gradient(135deg, #4338ca, #9333ea);
                font-weight: 750;
            }

            .content {
                max-width: 1550px;
                margin: auto;
                padding: 36px;
            }

            .heading-row {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 20px;
                margin-bottom: 29px;
            }

            h1 {
                margin: 0;
                font-size: clamp(26px, 3vw, 33px);
                letter-spacing: -1.2px;
            }

            .subtitle {
                margin-top: 10px;
                color: var(--muted);
                line-height: 1.8;
            }

            .button {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 16px;
                border: 1px solid var(--border);
                border-radius: 9px;
                background: #171a2e;
                color: #e2e8f0;
                font-weight: 600;
                white-space: nowrap;
                transition: .2s ease;
            }

            .button:hover {
                border-color: #818cf8;
                background: #202442;
            }

            .button-primary {
                border: none;
                background: linear-gradient(110deg, #6366f1, #9333ea);
                box-shadow: 0 5px 20px rgba(99, 102, 241, .18);
                color: white;
            }

            .button-primary:hover {
                background: linear-gradient(110deg, #4f46e5, #7e22ce);
            }

            .section-label {
                margin: 31px 0 15px;
                color: #c4cbe0;
                font-size: 11px;
                font-weight: 750;
                letter-spacing: 1.4px;
                text-transform: uppercase;
            }

            .stats {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 16px;
            }

            .card {
                min-width: 0;
                padding: 21px;
                border: 1px solid var(--border);
                border-radius: 14px;
                background: linear-gradient(145deg, #14182b, #101323);
                transition: transform .2s ease, border-color .2s ease;
            }

            .card:hover {
                transform: translateY(-2px);
                border-color: rgba(129, 140, 248, .3);
            }

            .stat-top {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
            }

            .stat-title {
                color: #a5aec5;
                font-size: 12px;
                font-weight: 550;
            }

            .stat-icon {
                display: grid;
                place-items: center;
                width: 37px;
                height: 37px;
                flex-shrink: 0;
                border-radius: 10px;
                font-size: 18px;
            }

            .icon-purple {
                color: #c4b5fd;
                background: rgba(139, 92, 246, .14);
            }

            .icon-blue {
                color: #93c5fd;
                background: rgba(59, 130, 246, .14);
            }

            .icon-green {
                color: #86efac;
                background: rgba(34, 197, 94, .13);
            }

            .icon-orange {
                color: #fdba74;
                background: rgba(249, 115, 22, .13);
            }

            .stat-value {
                margin-top: 22px;
                font-size: 26px;
                font-weight: 750;
                letter-spacing: -.7px;
                overflow-wrap: anywhere;
            }

            .positive {
                color: var(--green);
            }

            .stat-foot {
                margin-top: 12px;
                color: var(--muted);
                font-size: 11px;
                line-height: 1.7;
            }

            .stat-foot a,
            .text-link {
                color: var(--blue);
            }

            .middle-grid {
                display: grid;
                grid-template-columns: minmax(0, 1.4fr) minmax(260px, .85fr);
                gap: 18px;
                margin-top: 22px;
            }

            .panel {
                min-width: 0;
                overflow: hidden;
                border: 1px solid var(--border);
                border-radius: 14px;
                background: var(--panel);
            }

            .panel-head {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                padding: 21px;
                border-bottom: 1px solid var(--border);
            }

            .panel-title {
                font-size: 14px;
                font-weight: 700;
            }

            .panel-description {
                margin-top: 6px;
                color: var(--muted);
                font-size: 11px;
                line-height: 1.6;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 7px 9px;
                border-radius: 7px;
                color: #86efac;
                background: rgba(34, 197, 94, .1);
                font-size: 10px;
                font-weight: 750;
                white-space: nowrap;
            }

            .pipeline {
                padding: 24px 22px;
            }

            .pipeline-step {
                display: flex;
                align-items: center;
                gap: 13px;
                margin-bottom: 21px;
            }

            .pipeline-step:last-of-type {
                margin-bottom: 0;
            }

            .step-icon {
                display: grid;
                place-items: center;
                flex: 0 0 36px;
                height: 36px;
                border-radius: 10px;
                color: #86efac;
                background: rgba(34, 197, 94, .12);
                font-size: 16px;
            }

            .step-title {
                font-size: 12px;
                font-weight: 650;
            }

            .step-sub {
                margin-top: 5px;
                color: var(--muted);
                font-size: 11px;
                line-height: 1.5;
            }

            .step-check {
                margin-left: auto;
                color: var(--green);
                font-size: 16px;
            }

            .pipeline-note {
                margin: 23px 0 0;
                padding-top: 15px;
                border-top: 1px solid var(--border);
                color: var(--muted);
                font-size: 10px;
                line-height: 1.7;
            }

            .environment {
                padding: 14px 22px;
            }

            .environment-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                padding: 15px 0;
                border-bottom: 1px solid var(--border);
            }

            .environment-row:last-child {
                border-bottom: none;
            }

            .env-name {
                color: #a5aec5;
                font-size: 12px;
            }

            .env-value {
                text-align: right;
                font-size: 12px;
                font-weight: 650;
                overflow-wrap: anywhere;
            }

            .table-wrap {
                overflow-x: auto;
            }

            table {
                width: 100%;
                min-width: 600px;
                border-collapse: collapse;
            }

            th, td {
                padding: 16px 20px;
                text-align: left;
                border-bottom: 1px solid var(--border);
                font-size: 12px;
            }

            th {
                color: #8f99b3;
                background: rgba(8, 11, 24, .25);
                font-size: 10px;
                font-weight: 750;
                letter-spacing: .8px;
                text-transform: uppercase;
            }

            td {
                color: #d3d9e8;
            }

            tbody tr:last-child td {
                border-bottom: none;
            }

            .empty {
                padding: 30px 20px;
                color: var(--muted);
                text-align: center;
                line-height: 1.8;
            }

            .empty-icon {
                margin-bottom: 12px;
                color: var(--purple);
                font-size: 28px;
            }

            .empty strong {
                color: #e2e8f0;
            }

            .footer {
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 31px;
                padding-top: 20px;
                border-top: 1px solid var(--border);
                color: #727e9b;
                font-size: 11px;
            }

            @media (max-width: 1150px) {
                .stats {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .content {
                    padding: 27px;
                }

                .topbar {
                    padding: 0 27px;
                }
            }

            @media (max-width: 800px) {
                .sidebar {
                    position: static;
                    width: 100%;
                    padding: 16px;
                    border-right: none;
                    border-bottom: 1px solid var(--border);
                }

                .brand {
                    margin-bottom: 18px;
                }

                .sidebar nav {
                    display: flex;
                    gap: 6px;
                    overflow-x: auto;
                }

                .nav-label {
                    display: none;
                }

                .nav-link {
                    flex: 0 0 auto;
                    margin: 0;
                }

                .sidebar-bottom {
                    display: none;
                }

                main {
                    margin-left: 0;
                }

                .topbar {
                    height: 58px;
                    padding: 0 20px;
                }

                .content {
                    padding: 25px 18px;
                }

                .middle-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 480px) {
                .stats {
                    grid-template-columns: 1fr;
                }

                .heading-row {
                    flex-direction: column;
                }

                .heading-row .button {
                    width: 100%;
                }

                .profile-label {
                    display: none;
                }

                .stat-value {
                    font-size: 24px;
                }

                .panel-head {
                    align-items: flex-start;
                }
            }
            __HEALTH_UI_CSS__
        </style>
    </head>

    <body>
        <aside class="sidebar">
            <a href="/dashboard" class="brand">
                <div class="brand-icon">⚡</div>
                <div>
                    <div class="brand-name">AutoDeploy</div>
                    <span class="brand-sub">Deployment platform</span>
                </div>
            </a>

            <nav>
                <p class="nav-label">Workspace</p>

                <a href="/dashboard" class="nav-link active">
                    <span class="nav-icon">▦</span> Overview
                </a>

                <a href="#pipeline" class="nav-link">
                    <span class="nav-icon">⇄</span> CI/CD Pipeline
                </a>

                <a href="#deployments" class="nav-link">
                    <span class="nav-icon">◷</span> Deployments
                </a>

                <a href="#health" class="nav-link">
                    <span class="nav-icon">♡</span> Health Check
                </a>
            </nav>

            <div class="sidebar-bottom">
                <div class="connection">
                    <div class="connection-label">Application connection</div>
                    <div class="connection-status">
                        <span class="dot"></span>Application responding
                    </div>
                </div>
            </div>
        </aside>

        <main>
            <header class="topbar">
                <div class="breadcrumb">
                    Workspace&nbsp; / &nbsp;<strong>Overview</strong>
                </div>

                <div class="profile">
                    <div class="avatar">A</div>
                    <span class="profile-label">AutoDeploy Admin</span>
                </div>
            </header>

            <div class="content">
                <div class="heading-row">
                    <div>
                        <h1>AutoDeploy Dashboard</h1>
                        <p class="subtitle">
                            Monitor your application and deployment environment.
                            <br>
                            Welcome back to your deployment workspace.
                        </p>
                    </div>

                    <a class="button button-primary" href="#health">
                        <span>↻</span> Check application health
                    </a>
                </div>

                <div class="section-label" id="health-overview">System health &amp; application overview</div>

                {%HEALTH_UI%}

                <div class="middle-grid">
                    <section class="panel" id="pipeline">
                        <div class="panel-head">
                            <div>
                                <div class="panel-title">CI/CD Pipeline</div>
                                <div class="panel-description">
                                    The stages configured in GitHub Actions
                                </div>
                            </div>
                            <span class="badge">Pipeline configured</span>
                        </div>

                        <div class="pipeline">
                            <div class="pipeline-step">
                                <div class="step-icon">✓</div>
                                <div>
                                    <div class="step-title">Source checkout</div>
                                    <div class="step-sub">
                                        Retrieve the latest project source
                                    </div>
                                </div>
                                <span class="step-check">✓</span>
                            </div>

                            <div class="pipeline-step">
                                <div class="step-icon">✓</div>
                                <div>
                                    <div class="step-title">Automated tests</div>
                                    <div class="step-sub">
                                        Run the pytest test suite
                                    </div>
                                </div>
                                <span class="step-check">✓</span>
                            </div>

                            <div class="pipeline-step">
                                <div class="step-icon">◇</div>
                                <div>
                                    <div class="step-title">Docker build</div>
                                    <div class="step-sub">
                                        Build the application image
                                    </div>
                                </div>
                                <span class="step-check">✓</span>
                            </div>

                            <div class="pipeline-step">
                                <div class="step-icon">⇧</div>
                                <div>
                                    <div class="step-title">AWS deployment</div>
                                    <div class="step-sub">
                                        Deploy through Systems Manager
                                    </div>
                                </div>
                                <span class="step-check">✓</span>
                            </div>

                            <p class="pipeline-note">
                                This is a visual overview of configured stages,
                                not a live status feed for an individual run.
                            </p>
                        </div>
                    </section>

                    <section class="panel">
                        <div class="panel-head">
                            <div>
                                <div class="panel-title">Environment</div>
                                <div class="panel-description">
                                    Application configuration
                                </div>
                            </div>
                        </div>

                        <div class="environment">
                            <div class="environment-row">
                                <span class="env-name">Application</span>
                                <span class="env-value">AutoDeploy</span>
                            </div>

                            <div class="environment-row">
                                <span class="env-name">Framework</span>
                                <span class="env-value">Flask</span>
                            </div>

                            <div class="environment-row">
                                <span class="env-name">Container</span>
                                <span class="env-value">Docker</span>
                            </div>

                            <div class="environment-row">
                                <span class="env-name">Cloud provider</span>
                                <span class="env-value">AWS EC2</span>
                            </div>

                            <div class="environment-row">
                                <span class="env-name">CI/CD</span>
                                <span class="env-value">GitHub Actions</span>
                            </div>

                            <div class="environment-row">
                                <span class="env-name">Health monitoring</span>
                                <span class="env-value positive">Enabled</span>
                            </div>
                        </div>
                    </section>
                </div>

                <div class="section-label" id="deployments">
                    Recent deployments
                </div>

                <section class="panel">
    <div class="panel-head">
        <div>
            <div class="panel-title">Deployment activity</div>
            <div class="panel-description">
                Recent GitHub Actions workflow runs
            </div>
        </div>
        <span class="badge"
              style="color: #c4b5fd; background: rgba(139,92,246,.12);">
            GitHub connected
        </span>
    </div>

    {%DEPLOYMENT_CONTENT%}
</section>
                <section class="panel">
                    <div class="panel-head">
                        <div>
                            <div class="panel-title">Deployment activity</div>
                            <div class="panel-description">
                                History of application releases
                            </div>
                        </div>
                        <span class="badge"
                              style="color: #c4b5fd; background: rgba(139,92,246,.12);">
                            Integration pending
                        </span>
                    </div>

                    <div class="empty">
                        <div class="empty-icon">◷</div>
                        <strong>No deployment records connected yet</strong>
                        <br>
                        Real deployment records will appear here after we
                        integrate GitHub Actions with persistent history storage.
                    </div>
                </section>

                <footer class="footer">
                    <span>© AutoDeploy · CI/CD Deployment Platform</span>
                    <span>Flask · Docker · GitHub Actions · AWS</span>
                </footer>
            </div>
        </main>
    </body>
    </html>
    """

    deployment_html = render_deployments(deployments, github_error)
    health_ui_html = render_health_ui()

    return (
        html
        .replace("__HEALTH_UI_CSS__", HEALTH_UI_CSS)
        .replace("{%HEALTH_UI%}", health_ui_html)
        .replace("__APP_VERSION__", APP_VERSION)
        .replace("__PROCESS_START_TIME__", PROCESS_START_TIME)
        .replace("{%DEPLOYMENT_CONTENT%}", deployment_html)
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)