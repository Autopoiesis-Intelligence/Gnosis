from __future__ import annotations

import hmac
import json
import os
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .chat_api import create_chat, handle_chat
from .internet_port import InternetPort, PortError, MAX_BODY_BYTES
from .information_adapter import information_from_exchange

RATE_WINDOW_SECONDS = 60
RATE_LIMIT = 60


def _port_handler(envelope: dict[str, Any]) -> dict[str, Any]:
    """Accept a transport proposal without granting execution authority."""
    information = information_from_exchange(envelope)
    return {
        "accepted": True,
        "effect": "proposal_only",
        "authority_granted": False,
        "message_type": envelope["type"],
        "payload_sha256": envelope["payload_sha256"],
        "information_id": information.information_id,
        "authorization_status": information.authorization.status.value,
    }


class GnozisChatHandler(BaseHTTPRequestHandler):
    """HTTP adapter for Gnozis chat and gnozis-port/1 interoperability."""

    internet_port = InternetPort(_port_handler)
    _rate_lock = threading.Lock()
    _rate_events: dict[str, deque[float]] = defaultdict(deque)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.chat = create_chat()
        super().__init__(*args, **kwargs)

    def _rate_limited(self) -> bool:
        now = time.monotonic()
        peer = self.client_address[0]
        with self._rate_lock:
            events = self._rate_events[peer]
            cutoff = now - RATE_WINDOW_SECONDS
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= RATE_LIMIT:
                return True
            events.append(now)
            return False

    def _require_api_auth(self) -> bool:
        expected = os.environ.get("GNOZIS_PORT_API_TOKEN", "")
        if not expected:
            self._json(503, {"error": "port authentication is not configured"})
            return False

        authorization = self.headers.get("Authorization", "")
        scheme, separator, supplied = authorization.partition(" ")
        if (
            not separator
            or scheme.lower() != "bearer"
            or not supplied
            or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))
        ):
            self._json(401, {"error": "missing or invalid bearer token"})
            return False
        return True

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        allowed_origins = {
            item.strip()
            for item in os.environ.get("GNOZIS_PORT_ALLOWED_ORIGINS", "").split(",")
            if item.strip() and item.strip() != "*"
        }
        if origin and origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "content-type, authorization")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._json(204, {})

    def do_GET(self) -> None:
        if self.path == "/health":
            try:
                create_chat()
            except Exception as exc:
                self._json(503, {"status": "degraded", "core": "unavailable", "error": str(exc)})
                return
            self._json(200, {"status": "online", "core": "ready", "protocol": "gnozis-port/1"})
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self._rate_limited():
            self._json(429, {"error": "rate limit exceeded"})
            return

        try:
            length_header = self.headers.get("Content-Length")
            length = int(length_header) if length_header is not None else 0
            if length < 0 or length > MAX_BODY_BYTES:
                self._json(413, {"error": "request body too large"})
                return
            if not self._require_api_auth():
                return
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")

            if self.path == "/v1/handshake":
                result = self.internet_port.handshake(payload)
                self._json(200, result)
                return

            if self.path == "/v1/exchange":
                result = self.internet_port.exchange(payload)
                self._json(200, result)
                return

            if self.path != "/chat":
                self._json(404, {"error": "Not found"})
                return

            result = handle_chat(payload, self.chat)
        except (PortError, PermissionError) as exc:
            self._json(401, {"error": str(exc)})
            return
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._json(500, {"error": str(exc)})
            return

        self._json(200, result)

    def log_message(self, format: str, *args: object) -> None:
        return


class GnozisHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(host: str = "0.0.0.0", port: int = 8788) -> None:
    server = GnozisHTTPServer((host, port), GnozisChatHandler)
    print(f"Gnozis Core API listening on http://{host}:{port}", flush=True)
    print("POST /chat   GET /health   POST /v1/handshake   POST /v1/exchange", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
