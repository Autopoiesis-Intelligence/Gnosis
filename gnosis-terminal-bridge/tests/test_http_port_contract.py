from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from src.chat_server import GnozisChatHandler


def _request(server, path, payload=None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), GnozisChatHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _handshake(server):
    return _request(server, "/v1/handshake", {
        "protocol": "gnozis-port/1",
        "client_id": "test-client",
        "provenance": {"source": "test-client"},
                "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "allowed"},
            "authorization": {"source": "test-client", "purpose": "test", "operation": "transform", "destination": "core", "status": "allowed"},
            "authorization": {"source": "test-client", "purpose": "test", "operation": "transform", "destination": "core", "status": "allowed"},
    })


def test_health_exposes_port_protocol():
    server = _server()
    try:
        status, body = _request(server, "/health")
        assert status == 200
        assert body["protocol"] == "gnozis-port/1"
    finally:
        server.shutdown(); server.server_close()


def test_handshake_and_exchange_roundtrip():
    server = _server()
    try:
        status, handshake = _handshake(server)
        assert status == 200
        assert handshake["protocol"] == "gnozis-port/1"
        session_id = handshake["session_id"]

        status, result = _request(server, "/v1/exchange", {
            "protocol": "gnozis-port/1",
            "session_id": session_id,
            "message_id": "msg-1",
            "type": "hypothesis",
            "payload": {"text": "test"},
            "provenance": {"source": "test-client"},
            "authorization": {"source": "test-client", "purpose": "test", "operation": "transform", "destination": "core", "status": "allowed"},
        })
        assert status == 200
        assert result["status"] == "accepted"
        assert result["message_id"] == "msg-1"
        assert result["result"]["accepted"] is True
    finally:
        server.shutdown(); server.server_close()


def test_replay_is_rejected():
    server = _server()
    try:
        _, handshake = _handshake(server)
        payload = {
            "protocol": "gnozis-port/1", "session_id": handshake["session_id"],
            "message_id": "same-message", "type": "hypothesis",
            "payload": {"text": "test"}, "provenance": {"source": "test-client"},
        }
        assert _request(server, "/v1/exchange", payload)[0] == 200
        assert _request(server, "/v1/exchange", payload)[0] == 401
    finally:
        server.shutdown(); server.server_close()
