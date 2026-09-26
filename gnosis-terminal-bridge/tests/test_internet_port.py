import pytest

from src.internet_port import InternetPort, PortError, PROTOCOL


def make_port():
    return InternetPort(lambda envelope: {"echo_type": envelope["type"], "sha256": envelope["payload_sha256"]})


def test_handshake_and_exchange():
    port = make_port()
    hs = port.handshake({
        "protocol": PROTOCOL,
        "client_id": "test-agent",
        "provenance": {"provider": "test"},
            "authorization": {"source": "test-agent", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
        "authorization": {"source": "test-agent", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
    })
    response = port.exchange({
        "protocol": PROTOCOL,
        "session_id": hs["session_id"],
        "message_id": "m1",
        "type": "hypothesis",
        "payload": {"x": 1},
        "provenance": {"provider": "test"},
        "authorization": {"source": "test-agent", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
    })
    assert response["status"] == "accepted"
    assert response["message_id"] == "m1"
    assert response["result"]["echo_type"] == "hypothesis"


def test_wrong_protocol_fails_closed():
    port = make_port()
    with pytest.raises(PortError):
        port.handshake({"protocol": "gnozis-port/999", "client_id": "x", "provenance": {}})


def test_unknown_session_fails():
    port = make_port()
    with pytest.raises(PortError):
        port.exchange({"protocol": PROTOCOL, "session_id": "bad", "message_id": "m1", "type": "request", "payload": {}, "provenance": {}})


def test_replay_fails():
    port = make_port()
    hs = port.handshake({"protocol": PROTOCOL, "client_id": "x", "provenance": {}})
    msg = {"protocol": PROTOCOL, "session_id": hs["session_id"], "message_id": "same", "type": "request", "payload": {}, "provenance": {}, "authorization": {"source": "test-agent", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"}}
    port.exchange(msg)
    with pytest.raises(PortError, match="replayed"):
        port.exchange(msg)


def test_invalid_type_and_payload_fail():
    port = make_port()
    hs = port.handshake({"protocol": PROTOCOL, "client_id": "x", "provenance": {}})
    base = {"protocol": PROTOCOL, "session_id": hs["session_id"], "message_id": "m", "payload": {}, "provenance": {}}
    with pytest.raises(PortError):
        port.exchange({**base, "type": "unknown"})
    with pytest.raises(PortError):
        port.exchange({**base, "message_id": "m2", "type": "request", "payload": []})
