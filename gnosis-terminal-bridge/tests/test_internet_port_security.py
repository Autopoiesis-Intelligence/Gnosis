from __future__ import annotations

import time
import pytest
from src.internet_port import InternetPort, PortError, MAX_BODY_BYTES


def _port():
    return InternetPort(lambda envelope: {"ok": True})


def _handshake(port):
    return port.handshake({
        "protocol": "gnozis-port/1",
        "client_id": "security-test",
        "provenance": {"source": "test"},
        "authorization": {"source": "security-test", "purpose": "test", "operation": "transform", "destination": "core", "status": "allowed"},
    })


def _exchange(session_id, message_id="m1", body=None, **extra):
    payload = {
        "protocol": "gnozis-port/1",
        "session_id": session_id,
        "message_id": message_id,
        "type": "hypothesis",
        "payload": {} if body is None else body,
        "provenance": {"source": "test"},
    }
    payload.update(extra)
    return payload


def test_unknown_session_rejected():
    with pytest.raises(PortError):
        _port().exchange(_exchange("missing"))


def test_expired_session_rejected():
    port = _port()
    session = _handshake(port)
    port.sessions[session["session_id"]].expires_at = time.time() - 1
    with pytest.raises(PortError, match="expired"):
        port.exchange(_exchange(session["session_id"]))


def test_unsupported_type_rejected():
    port = _port()
    session = _handshake(port)
    with pytest.raises(PortError):
        port.exchange(_exchange(session["session_id"], type="arbitrary"))


def test_missing_provenance_rejected():
    port = _port()
    with pytest.raises(PortError):
        port.handshake({"protocol": "gnozis-port/1", "client_id": "x"})


def test_non_object_payload_rejected():
    port = _port()
    session = _handshake(port)
    with pytest.raises(PortError):
        port.exchange(_exchange(session["session_id"], body="not-an-object"))


def test_message_is_marked_seen_before_handler_result():
    calls = []
    def handler(envelope):
        calls.append(envelope["message_id"])
        raise RuntimeError("downstream failure")
    port = InternetPort(handler)
    session = _handshake(port)
    with pytest.raises(RuntimeError):
        port.exchange(_exchange(session["session_id"], "once"))
    with pytest.raises(PortError, match="replayed"):
        port.exchange(_exchange(session["session_id"], "once"))
    assert calls == ["once"]


def test_max_body_constant_is_positive():
    assert MAX_BODY_BYTES > 0
