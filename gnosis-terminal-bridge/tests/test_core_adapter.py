import pytest

from core import State
from src.agency_context import AgencyContext, AgencyIdentity
from src.core_adapter import agency_context_to_core_state


def test_verified_agency_context_becomes_credential_free_core_state():
    context = AgencyContext(
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

    state = agency_context_to_core_state(context)

    assert isinstance(state, State)
    assert state.values["agency"]["identity"]["provider"] == "github"
    assert state.values["agency"]["identity"]["subject"] == "synthetic-test-user"
    assert state.values["agency"]["identity"]["authenticated"] is True
    assert state.values["agency"]["epoch"] == 1
    assert state.values["agency"]["generation"] == 2
    assert state.values["agency"]["height"] == 3
    assert "access_token" not in state.values
    assert "device_code" not in state.values


def test_unauthenticated_agency_cannot_enter_core():
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

    with pytest.raises(ValueError, match="not authenticated"):
        agency_context_to_core_state(context)
