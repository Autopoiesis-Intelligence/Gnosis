import pytest

from src.chat_server import _port_handler
from src.internet_port import InternetPort, PortError


def handshake(port):
    return port.handshake({
        "protocol": "gnozis-port/1",
        "client_id": "test-client",
        "provenance": {"source": "test"},
    })


def exchange_payload(session_id, message_id, status):
    return {
        "protocol": "gnozis-port/1",
        "session_id": session_id,
        "message_id": message_id,
        "type": "request",
        "provenance": {"source": "test"},
        "authorization": {
            "source": "test-client",
            "purpose": "test",
            "operation": "observe",
            "destination": "core",
            "status": status,
        },
        "payload": {"value": 1},
    }


def test_exchange_does_not_trust_client_allowed_authorization():
    port = InternetPort(_port_handler)
    session = handshake(port)
    result = port.exchange(
        exchange_payload(session["session_id"], "m1", "ALLOWED")
    )
    assert result["status"] == "accepted"
    assert result["result"]["authorization_status"] == "UNKNOWN"
    assert result["result"]["effect"] == "proposal_only"
    assert result["result"]["authority_granted"] is False


@pytest.mark.parametrize("status", ["UNKNOWN", "DENIED", "EXPIRED", "REVOKED"])
def test_exchange_treats_client_authorization_status_as_untrusted_claim(status):
    port = InternetPort(_port_handler)
    session = handshake(port)
    result = port.exchange(
        exchange_payload(session["session_id"], "m1", status)
    )
    assert result["status"] == "accepted"
    assert result["result"]["authorization_status"] == "UNKNOWN"
    assert result["result"]["effect"] == "proposal_only"
    assert result["result"]["authority_granted"] is False


def test_exchange_rejects_missing_authorization():
    port = InternetPort(_port_handler)
    session = handshake(port)
    payload = exchange_payload(session["session_id"], "m1", "ALLOWED")
    payload.pop("authorization")
    with pytest.raises(PortError):
        port.exchange(payload)
