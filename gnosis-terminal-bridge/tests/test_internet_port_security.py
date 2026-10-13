from __future__ import annotations

import time
import pytest
from src.internet_port import InternetPort, PortError, MAX_BODY_BYTES
from src.information_adapter import information_from_exchange
from core.information_contract import AuthorizationStatus


def _port():
    return InternetPort(lambda envelope: {"ok": True})


def _handshake(port):
    return port.handshake({
        "protocol": "gnozis-port/1",
        "client_id": "security-test",
        "provenance": {"source": "test"},
        "authorization": {"source": "security-test", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
        "authorization": {"source": "security-test", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
    })


def _exchange(session_id, message_id="m1", body=None, **extra):
    payload = {
        "protocol": "gnozis-port/1",
        "session_id": session_id,
        "message_id": message_id,
        "type": "hypothesis",
        "payload": {} if body is None else body,
        "provenance": {"source": "test"},
        "authorization": {"source": "security-test", "purpose": "test", "operation": "transform", "destination": "core", "status": "ALLOWED"},
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



def test_client_cannot_grant_itself_authorization():
    envelope = {
        "message_id": "external-message",
        "payload_sha256": "a" * 64,
        "provenance": {"source": "untrusted-client"},
        "payload": {"action": "execute"},
        "type": "request",
        "authorization": {
            "source": "untrusted-client",
            "purpose": "test",
            "operation": "execute",
            "destination": "core",
            "status": "ALLOWED",
            "validity_ref": "client-invented-reference",
        },
    }

    information = information_from_exchange(envelope)

    assert information.authorization.status is AuthorizationStatus.UNKNOWN
    with pytest.raises(PermissionError, match="status=UNKNOWN"):
        information.require_authorized()


def test_transport_acceptance_is_not_authority_grant():
    envelope = {
        "message_id": "external-message",
        "payload_sha256": "b" * 64,
        "provenance": {"source": "untrusted-client"},
        "payload": {"text": "proposal"},
        "type": "hypothesis",
        "authorization": {
            "source": "untrusted-client",
            "purpose": "research",
            "operation": "submit",
            "destination": "core",
            "status": "ALLOWED",
        },
    }
    port = InternetPort(lambda value: {
        "accepted": True,
        "effect": "proposal_only",
        "authority_granted": False,
        "authorization_status": information_from_exchange(value).authorization.status.value,
    })
    session = _handshake(port)
    result = port.exchange(_exchange(session["session_id"], "proposal-1"))

    assert result["status"] == "accepted"
    assert result["result"]["effect"] == "proposal_only"
    assert result["result"]["authority_granted"] is False
    assert result["result"]["authorization_status"] == "UNKNOWN"
