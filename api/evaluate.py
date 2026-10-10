import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from src.evaluate import evaluate as evaluate_patient


KNOWLEDGE_BASE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "ada2026_prescription_kb.json"
)
MAX_REQUEST_BYTES = 1_048_576


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(405, {"error": "Use POST with a patient object."})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"error": "A valid Content-Length header is required."})
            return

        if content_length < 1:
            self._send_json(400, {"error": "Request body must not be empty."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body exceeds the 1 MiB limit."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        patient = payload.get("patient") if isinstance(payload, dict) else None
        if not isinstance(patient, dict):
            self._send_json(400, {"error": "Request JSON must contain a patient object."})
            return

        try:
            with KNOWLEDGE_BASE_PATH.open(encoding="utf-8") as knowledge_base_file:
                knowledge_base = json.load(knowledge_base_file)
            result = evaluate_patient(patient, knowledge_base)
        except (KeyError, TypeError, ValueError):
            self._send_json(400, {"error": "Patient data could not be evaluated."})
            return

        self._send_json(200, result)
