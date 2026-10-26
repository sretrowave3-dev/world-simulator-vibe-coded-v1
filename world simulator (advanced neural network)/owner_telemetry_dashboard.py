"""
owner_telemetry_dashboard.py

Standalone Web Dashboard & Analytics Hub for the World Simulator Owner.
Zero dependencies: runs purely on Python standard library (http.server).

Features:
- Live Active Users Counter: Tracks how many people are running the simulation right now (via 15m heartbeats).
- Unique Installations Metric: Displays total distinct anonymized client IDs.
- Multi-Tier World State Telemetry Explorer:
  - Summary views (population, biomass, seasons, diversity).
  - Deep ecosystem metrics (oldest organisms, genetics, neural complexity).
  - Full World State Dump Inspector ("literally everything" - inspect entities, neural weights, and download raw JSON).
- Local Log Ingestion: Reads logs/telemetry/anonymized_telemetry.jsonl in real-time.
- Remote REST Ingestion: Exposes POST /api/telemetry for remote users.
- Discord Webhook Bridge: Automatically relays active user pings and world dumps to Discord if configured.

Usage:
    python owner_telemetry_dashboard.py [--port 8080]
"""

from __future__ import annotations

import argparse
import base64
import html
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.request
import zlib
from typing import Dict, Any, List, Optional
from project.core.telemetry_config import DEFAULT_OWNER_WEBHOOK

WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))
LOCAL_TELEMETRY_DIR = os.path.join(WORKSPACE_DIR, "logs", "telemetry")
LOCAL_LOG_FILE = os.path.join(LOCAL_TELEMETRY_DIR, "anonymized_telemetry.jsonl")

# In-memory store for active sessions and world states
active_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> latest session data
unique_clients: set = set()
world_snapshots: List[Dict[str, Any]] = []
recent_logs: List[Dict[str, Any]] = []
configured_discord_webhook: str = os.environ.get("SIMULATOR_TELEMETRY_WEBHOOK", DEFAULT_OWNER_WEBHOOK)


def load_local_telemetry_log() -> None:
    """Reads existing telemetry events from logs/telemetry/anonymized_telemetry.jsonl."""
    if not os.path.exists(LOCAL_LOG_FILE):
        return

    try:
        with open(LOCAL_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        process_telemetry_event(record, relay_to_discord=False)
                    except Exception:
                        pass
    except Exception as e:
        print(f"⚠️ [LOG INGESTION] Error reading local log: {e}")


def process_telemetry_event(event: Dict[str, Any], relay_to_discord: bool = True) -> None:
    """Processes an incoming telemetry event (heartbeat or world state)."""
    event_type = event.get("event_type", "")
    client_id = event.get("client_id", "anon")
    data = event.get("data", {})
    ts = event.get("timestamp", time.time())

    unique_clients.add(client_id)
    recent_logs.append(event)
    if len(recent_logs) > 500:
        recent_logs.pop(0)

    # 1. Heartbeats & Active Sessions
    if event_type == "ACTIVE_USER_HEARTBEAT":
        sess_id = data.get("session_id", client_id)
        active_sessions[sess_id] = {
            "client_id": client_id,
            "session_id": sess_id,
            "last_seen": ts,
            "status": data.get("status", "active"),
            "uptime_seconds": data.get("uptime_seconds", 0),
            "sim_tick": data.get("sim_tick", 0),
            "entities_alive": data.get("entities_alive", 0),
            "performance": data.get("performance", {}),
            "environment": data.get("environment", {}),
        }

    # 2. World State Telemetry ("Summary to literally everything")
    elif "WORLD_STATE" in event_type:
        tier = data.get("tier", "SUMMARY")
        snap_record = {
            "client_id": client_id,
            "received_at": ts,
            "datetime_utc": event.get("datetime_utc", ""),
            "event_type": event_type,
            "tier": tier,
            "data": data,
        }

        # Check if full dump was compressed; decode if so
        if tier == "FULL_DUMP_COMPRESSED" and "payload_b64" in data:
            try:
                raw_compressed = base64.b64decode(data["payload_b64"])
                decompressed_str = zlib.decompress(raw_compressed).decode("utf-8")
                snap_record["decompressed_full_dump"] = json.loads(decompressed_str)
            except Exception as de:
                snap_record["decompression_error"] = str(de)

        world_snapshots.append(snap_record)
        if len(world_snapshots) > 100:
            world_snapshots.pop(0)

    # Optional: Relay to Discord if webhook configured
    if relay_to_discord and configured_discord_webhook:
        _relay_event_to_discord(configured_discord_webhook, event)


def _relay_event_to_discord(webhook_url: str, payload: Dict[str, Any]) -> None:
    """Dispatches event to owner's Discord webhook."""
    try:
        from project.core.telemetry_dispatcher import telemetry_dispatcher
        telemetry_dispatcher._dispatch_to_webhook(webhook_url, payload)
    except Exception:
        pass


def get_live_active_users_count(window_seconds: float = 900.0) -> int:
    """Calculates active users seen within the last window (15 minutes)."""
    now = time.time()
    count = 0
    for sess in active_sessions.values():
        if (now - sess.get("last_seen", 0)) <= window_seconds and sess.get("status") != "session_end":
            count += 1
    return count


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>World Simulator — Owner Telemetry & Research Hub</title>
    <style>
        :root {
            --bg-dark: #0D1117;
            --card-bg: #161B22;
            --border: #30363D;
            --text-main: #E6EDF3;
            --text-muted: #8B949E;
            --accent-cyan: #58A6FF;
            --accent-green: #3FB950;
            --accent-amber: #D29922;
            --accent-red: #F85149;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", monospace;
            padding: 24px;
            line-height: 1.5;
        }
        .container { max-width: 1300px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }
        h1 { font-size: 24px; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 10px; }
        .badge {
            background: rgba(63, 185, 80, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(63, 185, 80, 0.4);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
        }
        .metric-title { font-size: 12px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; }
        .metric-val { font-size: 32px; font-weight: 700; color: var(--accent-cyan); margin: 6px 0; }
        .metric-sub { font-size: 12px; color: var(--text-muted); }

        .tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .tab-btn.active { color: var(--accent-cyan); border-bottom-color: var(--accent-cyan); }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
        th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); }
        th { background: #1c2128; color: var(--text-muted); font-weight: 600; }
        tr:hover { background: rgba(88, 166, 255, 0.04); }

        .status-pill {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .status-active { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .status-idle { background: rgba(210, 153, 34, 0.2); color: var(--accent-amber); }
        .status-ended { background: rgba(139, 148, 158, 0.2); color: var(--text-muted); }

        .card-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .raw-box {
            background: #090d13;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 14px;
            font-family: monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            color: #79c0ff;
        }
        .btn {
            background: #238636;
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
        }
        .btn:hover { background: #2ea043; }
        .input-text {
            background: #090d13;
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 6px;
            width: 100%;
            font-size: 13px;
            margin-top: 6px;
            margin-bottom: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🌍 World Simulator <span class="badge">OWNER HUB</span></h1>
                <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">
                    Real-time Active User Tracking & Planetary Simulation State Telemetry
                </p>
            </div>
            <div>
                <button class="btn" onclick="location.reload()">🔄 Refresh Dashboard</button>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Live Active Users (Now)</div>
                <div class="metric-val" style="color: var(--accent-green);">{{ACTIVE_USERS_COUNT}}</div>
                <div class="metric-sub">Simulators active in the last 15 min</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Unique Client Installs</div>
                <div class="metric-val">{{UNIQUE_CLIENTS_COUNT}}</div>
                <div class="metric-sub">Distinct client UUIDs registered</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Active Sessions</div>
                <div class="metric-val">{{ACTIVE_SESSIONS_COUNT}}</div>
                <div class="metric-sub">Sessions launched across all environments</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">World Snapshots Received</div>
                <div class="metric-val" style="color: var(--accent-cyan);">{{WORLD_SNAPSHOTS_COUNT}}</div>
                <div class="metric-sub">From Summary to Literally Everything</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('sessions')">🟢 Active Users & Sessions ({{ACTIVE_SESSIONS_COUNT}})</button>
            <button class="tab-btn" onclick="switchTab('worlds')">🌍 World & State Telemetry ({{WORLD_SNAPSHOTS_COUNT}})</button>
            <button class="tab-btn" onclick="switchTab('webhook')">⚙️ Discord Webhook & Ingestion API</button>
        </div>

        <!-- Tab 1: Active Sessions -->
        <div id="tab-sessions" class="tab-content active">
            <div class="card-box">
                <h3 style="margin-bottom: 12px;">Active & Recent Simulation Sessions</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Client ID</th>
                            <th>Uptime</th>
                            <th>Sim Tick</th>
                            <th>Entities Alive</th>
                            <th>FPS / UPS</th>
                            <th>Platform</th>
                            <th>Version (Commit)</th>
                            <th>Last Ping</th>
                        </tr>
                    </thead>
                    <tbody>
                        {{SESSIONS_ROWS}}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab 2: World State Telemetry ("Summary to literally everything") -->
        <div id="tab-worlds" class="tab-content">
            <div class="card-box">
                <h3 style="margin-bottom: 14px;">Planetary State Snapshots ("Summary to Literally Everything")</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">
                    Users who consented in the setup wizard transmit their simulation states here for research & observation.
                </p>
                {{WORLD_SNAPSHOTS_CARDS}}
            </div>
        </div>

        <!-- Tab 3: Discord Webhook & Ingestion API -->
        <div id="tab-webhook" class="tab-content">
            <div class="card-box">
                <h3 style="margin-bottom: 10px;">📡 Discord Webhook Relay</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 12px;">
                    Incoming telemetry can be mirrored automatically to your private Discord channel.
                </p>
                <form method="POST" action="/api/configure_webhook">
                    <label style="font-size: 12px; font-weight: 600; color: var(--text-muted);">DISCORD WEBHOOK URL:</label>
                    <input class="input-text" type="text" name="webhook_url" value="{{DISCORD_WEBHOOK_URL}}" placeholder="https://discord.com/api/webhooks/..." />
                    <button type="submit" class="btn">💾 Save Webhook</button>
                </form>
            </div>

            <div class="card-box">
                <h3 style="margin-bottom: 10px;">🔌 Remote REST API Ingestion Endpoint</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 12px;">
                    Simulators can transmit telemetry directly to this server:
                </p>
                <div class="raw-box">POST http://&lt;your-ip-or-domain&gt;:{{PORT}}/api/telemetry
Content-Type: application/json

{
  "client_id": "anon_...",
  "event_type": "ACTIVE_USER_HEARTBEAT",
  "data": { ... }
}</div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }

        // Auto refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""


class TelemetryDashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler serving the dashboard UI and receiving telemetry POST requests."""

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/dashboard":
            self._render_dashboard()
        elif self.path == "/api/stats":
            self._serve_json_stats()
        elif self.path.startswith("/api/download_dump/"):
            self._serve_dump_download()
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self) -> None:
        if self.path == "/api/telemetry":
            self._handle_telemetry_post()
        elif self.path == "/api/configure_webhook":
            self._handle_webhook_config()
        else:
            self.send_error(404, "Unknown Endpoint")

    def _render_dashboard(self) -> None:
        load_local_telemetry_log()
        now = time.time()
        active_count = get_live_active_users_count()

        # Build session rows
        session_rows = []
        for sess in reversed(list(active_sessions.values())):
            age_s = now - sess.get("last_seen", now)
            is_recent = age_s <= 900.0 and sess.get("status") != "session_end"
            status_class = "status-active" if is_recent else "status-ended"
            status_label = "🟢 ACTIVE" if is_recent else sess.get("status", "OFFLINE").upper()

            uptime_m = round(sess.get("uptime_seconds", 0) / 60.0, 1)
            perf = sess.get("performance", {})
            env = sess.get("environment", {})

            row = f"""<tr>
                <td><span class="status-pill {status_class}">{status_label}</span></td>
                <td><code>{html.escape(sess.get('client_id', 'anon'))}</code></td>
                <td>{uptime_m} min</td>
                <td>{sess.get('sim_tick', 0):,}</td>
                <td><b>{sess.get('entities_alive', 0)}</b></td>
                <td>{perf.get('fps', 0)} / {perf.get('ups', 0)}</td>
                <td>{html.escape(str(env.get('os', 'Unknown')))}</td>
                <td>{html.escape(str(env.get('app_version', '2.1.0')))} ({html.escape(str(env.get('commit_sha', 'HEAD')))})</td>
                <td>{int(age_s)}s ago</td>
            </tr>"""
            session_rows.append(row)

        if not session_rows:
            session_rows.append('<tr><td colspan="9" style="text-align:center; color:var(--text-muted);">No active simulator sessions detected yet. Launch the simulator to see live heartbeats.</td></tr>')

        # Build world snapshots cards
        world_cards = []
        for idx, snap in enumerate(reversed(world_snapshots)):
            tier = snap.get("tier", "SUMMARY")
            data = snap.get("data", {})
            cid = snap.get("client_id", "anon")
            dt_str = snap.get("datetime_utc", "")

            dump_content = ""
            if "decompressed_full_dump" in snap:
                dump_json = json.dumps(snap["decompressed_full_dump"], indent=2)[:3000]
                dump_content = f"""
                <div style="margin-top: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-size:12px; font-weight:600; color:var(--accent-cyan);">🔬 FULL SERIALIZED SIMULATION DUMP ("LITERALLY EVERYTHING")</span>
                    </div>
                    <div class="raw-box">{html.escape(dump_json)}\\n... (truncated preview)</div>
                </div>"""
            else:
                raw_preview = json.dumps(data, indent=2)[:1500]
                dump_content = f'<div class="raw-box">{html.escape(raw_preview)}</div>'

            card = f"""<div class="card-box" style="margin-bottom: 14px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <div>
                        <span class="badge" style="background:rgba(88,166,255,0.15); color:var(--accent-cyan);">{tier}</span>
                        <strong style="margin-left: 8px;">Client: <code>{html.escape(cid)}</code></strong>
                    </div>
                    <span style="font-size:12px; color:var(--text-muted);">{dt_str}</span>
                </div>
                {dump_content}
            </div>"""
            world_cards.append(card)

        if not world_cards:
            world_cards.append('<p style="color:var(--text-muted);">No world state telemetry received yet. Type <code>telemetry send_world</code> in the simulator console to dispatch a snapshot.</p>')

        page = HTML_TEMPLATE
        page = page.replace("{{ACTIVE_USERS_COUNT}}", str(active_count))
        page = page.replace("{{UNIQUE_CLIENTS_COUNT}}", str(len(unique_clients)))
        page = page.replace("{{ACTIVE_SESSIONS_COUNT}}", str(len(active_sessions)))
        page = page.replace("{{WORLD_SNAPSHOTS_COUNT}}", str(len(world_snapshots)))
        page = page.replace("{{SESSIONS_ROWS}}", "\n".join(session_rows))
        page = page.replace("{{WORLD_SNAPSHOTS_CARDS}}", "\n".join(world_cards))
        page = page.replace("{{DISCORD_WEBHOOK_URL}}", html.escape(configured_discord_webhook))
        page = page.replace("{{PORT}}", str(self.server.server_address[1]))

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def _handle_telemetry_post(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            payload = json.loads(body)
            process_telemetry_event(payload, relay_to_discord=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Telemetry received"}')
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f'{{"error": "{e}"}}'.encode("utf-8"))

    def _handle_webhook_config(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        from urllib.parse import parse_qs
        params = parse_qs(body)
        new_hook = params.get("webhook_url", [""])[0].strip()

        global configured_discord_webhook
        configured_discord_webhook = new_hook

        # Also update telemetry_config.py
        try:
            cfg_path = os.path.join(WORKSPACE_DIR, "project", "core", "telemetry_config.py")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_text = f.read()
                import re
                cfg_text = re.sub(
                    r'DEFAULT_OWNER_WEBHOOK\s*=\s*os\.environ\.get\([^)]+\)',
                    f'DEFAULT_OWNER_WEBHOOK = "{new_hook}"',
                    cfg_text
                )
                with open(cfg_path, "w", encoding="utf-8") as f:
                    f.write(cfg_text)
        except Exception:
            pass

        self.send_response(303)
        self.send_header("Location", "/dashboard")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Quiet standard HTTP access log
        pass


def run_dashboard_server(port: int = 8080) -> None:
    load_local_telemetry_log()
    server_address = ("", port)
    httpd = socketserver.TCPServer(server_address, TelemetryDashboardHandler)
    print("════════════════════════════════════════════════════════════════════════")
    print(f"🌍 WORLD SIMULATOR — OWNER TELEMETRY & RESEARCH HUB")
    print(f"📡 Dashboard live at: http://localhost:{port}/")
    print(f"🔌 Ingestion API:     http://localhost:{port}/api/telemetry")
    print("════════════════════════════════════════════════════════════════════════")
    print("Press Ctrl+C to stop the dashboard server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="World Simulator Owner Telemetry Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()
    run_dashboard_server(port=args.port)
