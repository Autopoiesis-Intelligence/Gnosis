from core import State

from src.agency_context import AgencyContext, AgencyIdentity
from src.core_evolution import engine_from_agency_context
from core import Uroboros


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


def test_agency_context_is_available_to_transition_and_evolution_needs_no_external_call():
    context = make_context()
    calls = []

    def transition(state, agency_context):
        calls.append(agency_context.identity.subject)
        return state.evolve(
            values={
                **state.values,
                "agency_seen": agency_context.identity.subject,
                "next_height": agency_context.height + 1,
            }
        )

    engine = engine_from_agency_context(context, transition)
    initial = State(values={"value": 10})
    uroboros = Uroboros(state=initial, engine=engine)

    evolved = uroboros.step()

    assert evolved.state.values["value"] == 10
    assert evolved.state.values["agency_seen"] == "synthetic-test-user"
    assert evolved.state.values["next_height"] == 4
    assert calls == ["synthetic-test-user"]

    evolved_again = evolved.step()
    assert evolved_again.state.values["agency_seen"] == "synthetic-test-user"
    assert calls == ["synthetic-test-user", "synthetic-test-user"]


def test_same_state_and_same_agency_context_are_deterministic():
    context = make_context()

    def transition(state, agency_context):
        return state.evolve(
            values={
                **state.values,
                "subject": agency_context.identity.subject,
                "height": agency_context.height,
            }
        )

    engine = engine_from_agency_context(context, transition)
    initial = State(values={"seed": 7})

    first = engine.step(initial)
    second = engine.step(initial)

    assert first == second


def test_unauthenticated_context_cannot_create_evolution_engine():
    context = AgencyContext(
        identity=AgencyIdentity(
            provider="github",
            subject="untrusted",
            authenticated=False,
        ),
        epoch=1,
        generation=2,
        height=3,
        expires_at=9999999999,
    )

    def transition(state, agency_context):
        return state

    try:
        engine_from_agency_context(context, transition)
    except ValueError as exc:
        assert str(exc) == "Agency identity is not authenticated"
    else:
        raise AssertionError("Unauthenticated context must be rejected")


def test_context_is_captured_once_and_three_evolution_steps_need_no_external_input():
    context = make_context()
    external_calls = []
    transition_calls = []

    def transition(state, agency_context):
        transition_calls.append(agency_context.identity.subject)
        return state.evolve(
            values={
                **state.values,
                "steps": state.values.get("steps", 0) + 1,
                "subject": agency_context.identity.subject,
            }
        )

    engine = engine_from_agency_context(context, transition)
    initial = State(values={"steps": 0})
    uroboros = Uroboros(state=initial, engine=engine)

    first = uroboros.step()
    second = first.step()
    third = second.step()

    assert third.state.values["steps"] == 3
    assert third.state.values["subject"] == "synthetic-test-user"
    assert transition_calls == [
        "synthetic-test-user",
        "synthetic-test-user",
        "synthetic-test-user",
    ]
    assert external_calls == []
