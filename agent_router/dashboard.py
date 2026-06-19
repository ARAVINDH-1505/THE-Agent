from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .models import RouteRequest
from .router import route_task
from .storage import dashboard_stats, log_route

HOST = "127.0.0.1"
PORT = 8765

STYLE = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f7f7f4;color:#202124}.wrap{max-width:1100px;margin:0 auto;padding:28px}h1{font-size:28px;margin:0 0 6px}.muted{color:#626262}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0}.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px}.num{font-size:30px;font-weight:700}.form{display:grid;gap:10px;background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px}textarea,input,select{font:inherit;padding:10px;border:1px solid #bbb;border-radius:6px}textarea{min-height:120px}button{background:#185abc;color:#fff;border:0;border-radius:6px;padding:10px 14px;font-weight:600;cursor:pointer}table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #ddd}th,td{text-align:left;padding:10px;border-bottom:1px solid #eee;vertical-align:top}pre{white-space:pre-wrap;background:#202124;color:#f8f8f2;padding:14px;border-radius:8px;overflow:auto}@media(max-width:800px){.grid{grid-template-columns:1fr}}
"""


def page(content: str) -> bytes:
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Agent Router Dashboard</title><style>{STYLE}</style></head><body><div class='wrap'>{content}</div></body></html>".encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        stats = dashboard_stats()
        rows = "".join(
            f"<tr><td>{escape(row['created_at'])}</td><td>{escape(row['primary_agent'])}</td><td>{escape(row['risk'])}</td><td>{escape(row['task_type'])}</td><td>{escape(row['task'][:120])}</td></tr>"
            for row in stats["recent"]
        )
        by_agent = "".join(f"<li>{escape(x['primary_agent'])}: {x['count']}</li>" for x in stats["by_agent"])
        by_type = "".join(f"<li>{escape(x['task_type'])}: {x['count']}</li>" for x in stats["by_type"])
        content = f"""
        <h1>Agent Router Dashboard</h1>
        <p class='muted'>Track how the router chooses Claude, Cursor, Codex, and Antigravity.</p>
        <div class='grid'>
          <div class='card'><div class='muted'>Total routed tasks</div><div class='num'>{stats['total']}</div></div>
          <div class='card'><div class='muted'>By agent</div><ul>{by_agent or '<li>No data yet</li>'}</ul></div>
          <div class='card'><div class='muted'>By task type</div><ul>{by_type or '<li>No data yet</li>'}</ul></div>
        </div>
        <form class='form' method='POST'>
          <strong>Try a route</strong>
          <textarea name='task' placeholder='Example: Review my PyTorch experiment plan and reduce hallucination risk'></textarea>
          <textarea name='context' placeholder='Optional logs, snippets, notes'></textarea>
          <select name='mode'><option>balanced</option><option>fast</option><option>careful</option><option>research</option><option>coding</option><option>build</option><option>learning</option></select>
          <select name='budget'><option>medium</option><option>low</option><option>high</option></select>
          <button>Route task</button>
        </form>
        <h2>Recent routes</h2>
        <table><thead><tr><th>Time</th><th>Agent</th><th>Risk</th><th>Type</th><th>Task</th></tr></thead><tbody>{rows or '<tr><td colspan="5">No tasks routed yet.</td></tr>'}</tbody></table>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(content))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode())
        request = RouteRequest(
            task=form.get("task", [""])[0],
            context=form.get("context", [None])[0] or None,
            mode=form.get("mode", ["balanced"])[0],
            budget=form.get("budget", ["medium"])[0],
        )
        decision = route_task(request)
        log_route(request.task, request.mode, request.budget, decision)
        content = f"""
        <h1>Route Result</h1>
        <p><a href='/'>Back to dashboard</a></p>
        <div class='card'><strong>Recommended:</strong> {escape(decision['primary_agent']['display_name'])}<br><strong>Risk:</strong> {escape(decision['risk'])}<br><strong>Task type:</strong> {escape(decision['task_type'])}</div>
        <h2>Handoff Prompt</h2>
        <pre>{escape(decision['handoff'])}</pre>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(content))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Dashboard running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
