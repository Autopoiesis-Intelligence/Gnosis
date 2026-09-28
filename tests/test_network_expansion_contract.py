from core.network_expansion_contract import ExpansionRequest, decide_expansion


def test_expansion_is_requested_only_on_capacity_deficit():
    request = ExpansionRequest("r1", "math", "work", 12, 5, "snapshot")
    decision = decide_expansion(request)
    assert decision.expand is True
    assert decision.deficit_units == 7
    assert decision.request_digest == request.digest()


def test_expansion_is_not_requested_when_capacity_is_sufficient():
    request = ExpansionRequest("r1", "math", "work", 5, 5, "snapshot")
    decision = decide_expansion(request)
    assert decision.expand is False
    assert decision.deficit_units == 0


def test_expansion_rejects_non_positive_requirement():
    try:
        ExpansionRequest("r1", "math", "work", 0, 1, "snapshot")
    except ValueError:
        return
    raise AssertionError("non-positive required units must be rejected")
