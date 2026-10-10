import json
import logging
import math
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from src.evaluate import evaluate as evaluate_patient


KNOWLEDGE_BASE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "ada2026_prescription_kb.json"
)
MAX_REQUEST_BYTES = 1_048_576


@lru_cache(maxsize=1)
def load_knowledge_base():
    with KNOWLEDGE_BASE_PATH.open(encoding="utf-8") as source:
        return json.load(source)


def validate_patient(patient, knowledge_base):
    schema = {item["field"]: item for item in knowledge_base["patient_fields"]}
    schema.update({name: {"type": "number"} for name in ("fpg", "ogtt_2h")})
    schema.update({name: {"type": "bool"} for name in ("classic_symptoms", "crisis", "repeat_confirmed")})
    if not patient or not any(value is not None for value in patient.values()):
        raise ValueError("Enter at least one patient parameter.")
    errors = []
    for name, value in patient.items():
        field = schema.get(name)
        if field is None:
            errors.append(f"Unknown patient field: {name}")
            continue
        if value is None:
            continue
        kind = field["type"]
        if kind == "bool" and not isinstance(value, bool):
            errors.append(f"{name} must be true or false.")
        elif kind == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                errors.append(f"{name} must be a finite number.")
            elif value < 0 or (name == "age" and value > 130) or (name in ("a1c", "a1c_goal") and not 0 < value <= 30):
                errors.append(f"{name} is outside the supported range.")
        elif kind == "enum" and value not in field.get("notes", "").split("|"):
            errors.append(f"Invalid option for {name}.")
    if errors:
        raise ValueError(" ".join(errors))


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if status == 405:
            self.send_header("Allow", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(405, {"error": "Use POST with a patient object."})

    def do_OPTIONS(self):
        self._send_json(200, {"methods": ["POST", "OPTIONS"]})

    do_PUT = do_GET
    do_DELETE = do_GET
    do_PATCH = do_GET

    def do_POST(self):
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            self._send_json(415, {"error": "Content-Type must be application/json."})
            return
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
            knowledge_base = load_knowledge_base()
        except (OSError, ValueError):
            logging.exception("Knowledge base could not be loaded")
            self._send_json(503, {"error": "Knowledge base unavailable."})
            return
        try:
            validate_patient(patient, knowledge_base)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        try:
            result = evaluate_patient(patient, knowledge_base)
        except Exception:
            logging.error("Rule evaluation failed")
            self._send_json(500, {"error": "Evaluation unavailable."})
            return

        self._send_json(200, result)
