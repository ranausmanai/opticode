from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_dashboard_data(opticode_dir: Path) -> dict:
    chat_path = opticode_dir / "chat_history.json"
    prompt_path = opticode_dir / "prompt_history.json"
    facts_path = opticode_dir / "facts.json"

    chat = _read_json(chat_path, {}).get("messages", [])
    prompts = _read_json(prompt_path, {}).get("prompts", [])
    facts = _read_json(facts_path, {}).get("facts", [])

    return {
        "chat": chat[-50:],
        "prompts": prompts[-50:],
        "facts": facts,
    }


def run_dashboard(opticode_dir: Path, port: int) -> None:
    data = _load_dashboard_data(opticode_dir)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/data":
                payload = json.dumps(data, indent=2).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", payload)
                return
            if self.path != "/":
                self._send(404, "text/plain; charset=utf-8", b"Not found")
                return

            html = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Opticode Dashboard</title>
    <style>
      :root {{
        --bg: #0f141b;
        --panel: #151b23;
        --text: #e6edf3;
        --muted: #9aa7b2;
        --accent: #2dba4e;
        --border: #243040;
      }}
      body {{
        margin: 0;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background: var(--bg);
        color: var(--text);
      }}
      header {{
        padding: 20px 24px;
        border-bottom: 1px solid var(--border);
      }}
      h1 {{
        margin: 0 0 6px 0;
        font-size: 20px;
      }}
      .sub {{
        color: var(--muted);
        font-size: 12px;
      }}
      .wrap {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        padding: 16px;
      }}
      .card {{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
      }}
      h2 {{
        margin: 0 0 8px 0;
        font-size: 14px;
        color: var(--accent);
      }}
      pre {{
        white-space: pre-wrap;
        word-wrap: break-word;
        font-size: 12px;
        color: var(--text);
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
      li {{
        margin: 6px 0;
        color: var(--text);
      }}
      .muted {{
        color: var(--muted);
      }}
      @media (max-width: 900px) {{
        .wrap {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <header>
      <h1>Opticode Dashboard</h1>
      <div class="sub">Recent prompts, chat history, and facts</div>
    </header>
    <div class="wrap">
      <div class="card">
        <h2>Recent Prompts</h2>
        <pre id="prompts" class="muted">Loading...</pre>
      </div>
      <div class="card">
        <h2>Chat History</h2>
        <pre id="chat" class="muted">Loading...</pre>
      </div>
      <div class="card">
        <h2>Facts</h2>
        <ul id="facts"><li class="muted">Loading...</li></ul>
      </div>
    </div>
    <script>
      fetch("/data").then(r => r.json()).then(data => {{
        const prompts = data.prompts || [];
        const chat = data.chat || [];
        const facts = data.facts || [];
        const pEl = document.getElementById("prompts");
        const cEl = document.getElementById("chat");
        const fEl = document.getElementById("facts");

        pEl.textContent = prompts.length ? prompts.map(p => p.prompt).join("\\n\\n---\\n\\n") : "No prompts yet.";
        cEl.textContent = chat.length ? chat.map(m => `> ${m.request}\\n${m.task || ""}`).join("\\n\\n") : "No chat yet.";
        fEl.innerHTML = facts.length ? facts.map(f => `<li>${f}</li>`).join("") : '<li class="muted">No facts yet.</li>';
      }});
    </script>
  </body>
</html>
"""
            self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Dashboard running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
