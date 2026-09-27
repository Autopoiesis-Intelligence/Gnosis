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


def test_duplicate_message_race_is_not_atomic():
    """Adversarial proof: check-then-add must not accept the same message twice."""
    import threading

    class BarrierSet(set):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._barrier = threading.Barrier(2)

        def __contains__(self, item):
            result = super().__contains__(item)
            self._barrier.wait(timeout=2)
            return result

    calls = 0
    calls_lock = threading.Lock()

    def handler(_envelope):
        nonlocal calls
        with calls_lock:
            calls += 1
        return {"ok": True}

    port = InternetPort(handler)
    hs = port.handshake({
        "protocol": PROTOCOL,
        "client_id": "race-test",
        "provenance": {},
    })
    session = port.sessions[hs["session_id"]]
    session.seen_messages = BarrierSet()

    message = {
        "protocol": PROTOCOL,
        "session_id": hs["session_id"],
        "message_id": "race",
        "type": "request",
        "payload": {},
        "provenance": {},
    }

    results = []
    errors = []

    def run():
        try:
            results.append(port.exchange(message))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert not any(thread.is_alive() for thread in threads)
    assert calls == 1
    assert len(results) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], PortError)
    assert "replayed" in str(errors[0])
