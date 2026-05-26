"""
TalentBridge recruitment agents — stdlib HTTP server (no pip dependencies).
Run: python run.py
"""

from __future__ import annotations

import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from agents.escalation_compliance import EscalationComplianceAgent
from agents.pipeline_insights import PipelineInsightsAgent

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "pipeline.json"
STATIC_DIR = ROOT / "static"
PORT = 8000


def load_pipeline() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def json_response(handler: BaseHTTPRequestHandler, data: object, status: int = 200) -> None:
    body = json.dumps(data, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


class TalentBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        print(f"[{self.address_string()}] {format % args}")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        req_id = query.get("requisition_id", [None])[0]

        if path == "/" or path == "/index.html":
            return self._serve_file(STATIC_DIR / "index.html")

        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            return self._serve_file(STATIC_DIR / rel)

        if path == "/api/health":
            return json_response(self, {"status": "ok", "service": "TalentBridge Agents API"})

        if path == "/api/requisitions":
            data = load_pipeline()
            return json_response(
                self,
                [
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "client": r.get("client"),
                        "status": r.get("status"),
                        "priority": r.get("priority"),
                        "candidate_count": len(r.get("candidates", [])),
                    }
                    for r in data.get("requisitions", [])
                ],
            )

        if path == "/api/agents/pipeline-insights":
            agent = PipelineInsightsAgent(load_pipeline())
            return json_response(self, agent.run(req_id))

        if path == "/api/agents/escalation-compliance":
            agent = EscalationComplianceAgent(load_pipeline())
            return json_response(self, agent.run(req_id))

        if path == "/api/agents/combined":
            data = load_pipeline()
            return json_response(
                self,
                {
                    "pipeline_insights": PipelineInsightsAgent(data).run(req_id),
                    "escalation_compliance": EscalationComplianceAgent(data).run(req_id),
                },
            )

        if path == "/api/pipeline/raw":
            return json_response(self, load_pipeline())

        self.send_error(404, "Not Found")

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.send_error(404, "File not found")
            return
        content = file_path.read_bytes()
        mime, _ = mimetypes.guess_type(str(file_path))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), TalentBridgeHandler)
    print(f"TalentBridge dashboard: http://127.0.0.1:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
