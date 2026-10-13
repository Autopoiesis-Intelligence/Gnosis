from __future__ import annotations

import json
from http.client import HTTPConnection
from threading import Thread

from src.chat_server import GnozisChatHandler, ThreadingHTTPServer


def test_chat_server_health_and_chat_roundtrip(monkeypatch) -> None:
    import os
    monkeypatch.setenv("GNOZIS_PORT_API_TOKEN", "test-secret")
    server = ThreadingHTTPServer(("127.0.0.1", 0), GnozisChatHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        connection.request("GET", "/health")
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read()) == {
            "status": "online",
            "core": "ready",
            "protocol": "gnozis-port/1",
        }

        connection.request(
            "POST",
            "/chat",
            body=json.dumps({"message": "hello"}),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['GNOZIS_PORT_API_TOKEN']}"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["state"]["turn"] == 1
        assert payload["state"]["last_message"] == "hello"
        assert payload["response"]
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_chat_handler_creates_isolated_chat_per_handler_instance() -> None:
    first = object.__new__(GnozisChatHandler)
    second = object.__new__(GnozisChatHandler)
    first.chat = __import__("src.chat_api", fromlist=["create_chat"]).create_chat("first")
    second.chat = __import__("src.chat_api", fromlist=["create_chat"]).create_chat("second")

    assert first.chat is not second.chat
    first.chat.send("one")
    assert second.chat.state.values["turn"] == 0
    assert second.chat.state.values["history"] == ()
