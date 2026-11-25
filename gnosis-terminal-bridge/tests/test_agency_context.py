from gnosis_terminal_bridge import GnosisTerminalBridge
from src.agency_context import AgencyIdentity


def test_verified_challenge_can_carry_agency_identity():
    bridge = GnosisTerminalBridge(ttl_seconds=300)
    context = {"epoch": 1, "generation": 2, "height": 1}
    identity = AgencyIdentity(
        provider="github",
        subject="synthetic-test-user",
    )

    issued = bridge.initiate_challenge(context)
    challenge = issued["challenge"]

    result = bridge.verify_challenge(
        challenge["challenge_id"],
        challenge["value"],
        context["epoch"],
        context["generation"],
        context["height"],
        identity=identity,
    )

    assert result["status"] == "VERIFIED"
    assert result["agency"]["identity"]["provider"] == "github"
    assert result["agency"]["identity"]["subject"] == "synthetic-test-user"
    assert result["agency"]["identity"]["authenticated"] is True
    assert result["agency"]["epoch"] == 1
    assert result["agency"]["generation"] == 2
    assert result["agency"]["height"] == 1


def test_handle_accepts_agency_identity_without_exposing_credentials():
    bridge = GnosisTerminalBridge(ttl_seconds=300)
    context = {"epoch": 1, "generation": 2, "height": 1}
    identity = AgencyIdentity(
        provider="github",
        subject="synthetic-test-user",
    )

    issued = bridge.initiate_challenge(context)
    challenge = issued["challenge"]

    result = bridge.verify_challenge(
        challenge["challenge_id"],
        challenge["value"],
        1,
        2,
        1,
        identity=identity,
    )

    assert result["status"] == "VERIFIED"
    assert "access_token" not in result
    assert "device_code" not in result
