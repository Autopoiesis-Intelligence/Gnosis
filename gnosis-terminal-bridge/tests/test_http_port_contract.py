from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from src.chat_server import GnozisChatHandler


def _request(server, path, payload=None, *, authorization=None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST" if payload is not None else "GET")
    req.add_header("Content-Type", "application/json")
    if authorization is False:
        pass
    elif isinstance(authorization, str):
        req.add_header("Authorization", authorization)
    else:
        token = os.environ.get("GNOZIS_PORT_API_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), GnozisChatHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(autouse=True)
def _configured_api_token(monkeypatch):
    monkeypatch.setenv("GNOZIS_PORT_API_TOKEN", "test-secret")


def _request_with_origin(server, path, origin):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Origin", origin)
    with urllib.request.urlopen(req, timeout=2) as response:
        return response.status, response.headers


def _handshake(server):
    return _request(server, "/v1/handshake", {
        "protocol": "gnozis-port/1",
        "client_id": "test-client",
        "provenance": {"source": "test-client"},
                "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "ALLOWED"},
            "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "ALLOWED"},
            "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "ALLOWED"},
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
            "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "ALLOWED"},
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
            "authorization": {"source": "test-client", "purpose": "test", "operation": "request", "destination": "core", "status": "ALLOWED"},
        }
        assert _request(server, "/v1/exchange", payload)[0] == 200
        assert _request(server, "/v1/exchange", payload)[0] == 401
    finally:
        server.shutdown(); server.server_close()



def test_cors_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("GNOZIS_PORT_ALLOWED_ORIGINS", raising=False)
    server = _server()
    try:
        status, headers = _request_with_origin(server, "/health", "https://untrusted.example")
        assert status == 200
        assert headers.get("Access-Control-Allow-Origin") is None
    finally:
        server.shutdown()
        server.server_close()


def test_cors_allows_only_exact_configured_origins(monkeypatch):
    monkeypatch.setenv("GNOZIS_PORT_ALLOWED_ORIGINS", "https://trusted.example")
    server = _server()
    try:
        status, trusted_headers = _request_with_origin(
            server, "/health", "https://trusted.example"
        )
        assert status == 200
        assert trusted_headers.get("Access-Control-Allow-Origin") == "https://trusted.example"
        assert trusted_headers.get("Vary") == "Origin"

        status, untrusted_headers = _request_with_origin(
            server, "/health", "https://untrusted.example"
        )
        assert status == 200
        assert untrusted_headers.get("Access-Control-Allow-Origin") is None
    finally:
        server.shutdown()
        server.server_close()



def test_post_fails_closed_when_authentication_is_not_configured(monkeypatch):
    monkeypatch.delenv("GNOZIS_PORT_API_TOKEN", raising=False)
    server = _server()
    try:
        status, body = _request(
            server,
            "/v1/handshake",
            {
                "protocol": "gnozis-port/1",
                "client_id": "test-client",
                "provenance": {"source": "test"},
            },
            authorization=False,
        )
        assert status == 503
        assert body["error"] == "port authentication is not configured"
    finally:
        server.shutdown()
        server.server_close()


def test_post_rejects_invalid_bearer_token():
    server = _server()
    try:
        status, body = _request(
            server,
            "/v1/handshake",
            {
                "protocol": "gnozis-port/1",
                "client_id": "test-client",
                "provenance": {"source": "test"},
            },
            authorization="Bearer wrong-token",
        )
        assert status == 401
        assert body["error"] == "missing or invalid bearer token"
    finally:
        server.shutdown()
        server.server_close()
