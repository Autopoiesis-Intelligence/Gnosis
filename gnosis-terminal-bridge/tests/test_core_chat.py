from core import State

from src.agency_context import AgencyContext, AgencyIdentity
from src.core_chat import CoreChat


def make_context():
    return AgencyContext(
        identity=AgencyIdentity(
            provider="github",
            subject="synthetic-test-user",
            authenticated=True,
        ),
        epoch=1,
        generation=2,
        height=3,
        expires_at=9999999999,
    )


def test_chat_message_goes_through_core_engine_and_evolves_state():
    chat = CoreChat(make_context())

    result = chat.send("Hello, Gnozis")

    assert result["response"] == "Gnozis core received the message and evolved its state."
    assert result["state"]["turn"] == 1
    assert result["state"]["last_message"] == "Hello, Gnozis"
    assert result["state"]["agency_subject"] == "synthetic-test-user"
    assert result["state"]["height"] == 3
    assert "input_message" not in result["state"]


def test_chat_preserves_history_across_multiple_core_steps():
    chat = CoreChat(make_context())

    chat.send("first")
    result = chat.send("second")

    assert result["state"]["turn"] == 2
    assert result["state"]["history"] == [
        {"role": "user", "content": "first"},
        {
            "role": "core",
            "content": "Gnozis core received the message and evolved its state.",
        },
        {"role": "user", "content": "second"},
        {
            "role": "core",
            "content": "Gnozis core received the message and evolved its state.",
        },
    ]
    assert "input_message" not in result["state"]


def test_chat_rejects_empty_message():
    chat = CoreChat(make_context())

    try:
        chat.send("   ")
    except ValueError as exc:
        assert str(exc) == "message must not be empty"
    else:
        raise AssertionError("Empty messages must be rejected")


def test_chat_uses_immutable_core_state():
    chat = CoreChat(make_context(), state=State(values={"turn": 7, "history": []}))

    result = chat.send("continue")

    assert result["state"]["turn"] == 8


def test_chat_transition_reads_message_from_explicit_state():
    chat = CoreChat(make_context())

    chat.state = State(values={
        "turn": 4,
        "history": [],
        "input_message": "state-owned message",
    })
    result = chat.engine.step(chat.state)

    assert result.values["last_message"] == "state-owned message"
    assert "input_message" not in result.values
