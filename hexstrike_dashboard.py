#!/usr/bin/env python3
"""
HexStrike AI - Web Dashboard GUI
Connects to the HexStrike API server and provides a visual interface
for monitoring and managing the server.

Usage:
    python3 hexstrike_dashboard.py [--port PORT] [--api-url URL]

Access the dashboard at: http://localhost:5000
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
import requests

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Default configuration
DASHBOARD_PORT = int(os.environ.get('DASHBOARD_PORT', 5000))
DASHBOARD_HOST = os.environ.get('DASHBOARD_HOST', '0.0.0.0')
API_BASE_URL = os.environ.get('HEXSTRIKE_API_URL', 'http://localhost:8888')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def api_get(endpoint, params=None, timeout=5):
    """Perform a GET request to the HexStrike API server."""
    try:
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to HexStrike API server", "offline": True}
    except requests.exceptions.Timeout:
        return {"error": "API server request timed out", "offline": True}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "offline": True}


def api_post(endpoint, data=None, timeout=10):
    """Perform a POST request to the HexStrike API server."""
    try:
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        response = requests.post(url, json=data or {}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to HexStrike API server", "offline": True}
    except requests.exceptions.Timeout:
        return {"error": "API server request timed out", "offline": True}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "offline": True}


def get_server_status():
    """Check if the HexStrike API server is online and get basic status."""
    start = time.time()
    result = api_get("health", timeout=5)
    response_time = round((time.time() - start) * 1000, 1)

    if result.get("offline") or result.get("error"):
        return {
            "online": False,
            "status": "offline",
            "response_time_ms": None,
            "api_url": API_BASE_URL,
            "error": result.get("error", "Unknown error")
        }

    return {
        "online": True,
        "status": result.get("status", "unknown"),
        "response_time_ms": response_time,
        "api_url": API_BASE_URL,
        "version": result.get("version", "unknown"),
        "uptime": result.get("uptime"),
        "total_tools_available": result.get("total_tools_available", 0),
        "total_tools_count": result.get("total_tools_count", 0),
        "all_essential_tools_available": result.get("all_essential_tools_available", False),
        "category_stats": result.get("category_stats", {}),
        "tools_status": result.get("tools_status", {}),
        "cache_stats": result.get("cache_stats", {}),
        "telemetry": result.get("telemetry", {}),
    }


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html", api_url=API_BASE_URL)


@app.route("/processes")
def processes():
    """Process management page."""
    return render_template("processes.html", api_url=API_BASE_URL)


@app.route("/cache")
def cache():
    """Cache statistics page."""
    return render_template("cache.html", api_url=API_BASE_URL)


@app.route("/tools")
def tools():
    """Security tools inventory page."""
    return render_template("tools.html", api_url=API_BASE_URL)


@app.route("/logs")
def logs():
    """Live logs and command execution page."""
    return render_template("logs.html", api_url=API_BASE_URL)


# ============================================================================
# API PROXY ROUTES (Dashboard -> HexStrike Server)
# ============================================================================

@app.route("/api/status")
def api_status():
    """Get combined server status for the dashboard."""
    status = get_server_status()
    return jsonify(status)


@app.route("/api/health")
def api_health():
    """Proxy health endpoint."""
    return jsonify(api_get("health"))


@app.route("/api/telemetry")
def api_telemetry():
    """Proxy telemetry endpoint."""
    return jsonify(api_get("api/telemetry"))


@app.route("/api/cache/stats")
def api_cache_stats():
    """Proxy cache stats endpoint."""
    return jsonify(api_get("api/cache/stats"))


@app.route("/api/cache/clear", methods=["POST"])
def api_cache_clear():
    """Proxy cache clear endpoint."""
    return jsonify(api_post("api/cache/clear"))


@app.route("/api/processes/list")
def api_processes_list():
    """Proxy processes list endpoint."""
    return jsonify(api_get("api/processes/list"))


@app.route("/api/processes/dashboard")
def api_processes_dashboard():
    """Proxy processes dashboard endpoint."""
    return jsonify(api_get("api/processes/dashboard"))


@app.route("/api/processes/terminate/<int:pid>", methods=["POST"])
def api_terminate_process(pid):
    """Proxy process terminate endpoint."""
    return jsonify(api_post(f"api/processes/terminate/{pid}"))


@app.route("/api/processes/pause/<int:pid>", methods=["POST"])
def api_pause_process(pid):
    """Proxy process pause endpoint."""
    return jsonify(api_post(f"api/processes/pause/{pid}"))


@app.route("/api/processes/resume/<int:pid>", methods=["POST"])
def api_resume_process(pid):
    """Proxy process resume endpoint."""
    return jsonify(api_post(f"api/processes/resume/{pid}"))


@app.route("/api/execute", methods=["POST"])
def api_execute():
    """Proxy command execution endpoint."""
    data = request.get_json(force=True) or {}
    command = data.get("command", "")
    if not command:
        return jsonify({"error": "Command parameter is required"}), 400
    return jsonify(api_post("api/command", {"command": command}, timeout=60))


@app.route("/api/system/metrics")
def api_system_metrics():
    """Get system metrics via the telemetry endpoint."""
    telemetry = api_get("api/telemetry")
    proc_dashboard = api_get("api/processes/dashboard")

    system_load = proc_dashboard.get("system_load", {}) if not proc_dashboard.get("offline") else {}

    return jsonify({
        "telemetry": telemetry,
        "system_load": system_load,
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HexStrike AI Web Dashboard")
    parser.add_argument(
        "--port",
        type=int,
        default=DASHBOARD_PORT,
        help=f"Dashboard port (default: {DASHBOARD_PORT})"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=API_BASE_URL,
        help=f"HexStrike API server URL (default: {API_BASE_URL})"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    args = parser.parse_args()

    API_BASE_URL = args.api_url
    DASHBOARD_PORT = args.port

    print(f"""
\033[38;5;196m\033[1m
██╗  ██╗███████╗██╗  ██╗███████╗████████╗██████╗ ██╗██╗  ██╗███████╗
██║  ██║██╔════╝╚██╗██╔╝██╔════╝╚══██╔══╝██╔══██╗██║██║ ██╔╝██╔════╝
███████║█████╗   ╚███╔╝ ███████╗   ██║   ██████╔╝██║█████╔╝ █████╗
██╔══██║██╔══╝   ██╔██╗ ╚════██║   ██║   ██╔══██╗██║██╔═██╗ ██╔══╝
██║  ██║███████╗██╔╝ ██╗███████║   ██║   ██║  ██║██║██║  ██╗███████╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝
\033[0m
\033[38;5;160m┌─────────────────────────────────────────────────────────────────────┐
│  \033[97m🌐 Dashboard GUI v6.0 - Web Interface\033[38;5;160m                              │
│  \033[38;5;196m📡 API Server: {args.api_url:<55}\033[38;5;160m│
│  \033[38;5;208m🚀 Dashboard:  http://localhost:{args.port:<42}\033[38;5;160m│
└─────────────────────────────────────────────────────────────────────┘\033[0m
""")

    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=args.debug)
