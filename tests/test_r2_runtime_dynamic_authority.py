import pytest

from core.admission import Admission, require_admitted
from core.commit import SemanticCommit


def test_raw_dynamic_lookup_does_not_create_admission():
    target = getattr(__import__("core.commit", fromlist=["SemanticCommit"]), "SemanticCommit")
    assert target is SemanticCommit

    forged = target.__new__(target)
    with pytest.raises((TypeError, ValueError, AttributeError)):
        require_admitted(forged)


def test_dynamic_callable_without_admission_is_rejected():
    forged = SemanticCommit.__new__(SemanticCommit)
    callable_apply = getattr(forged, "apply", None)
    assert callable_apply is not None

    # A dynamically obtained method on an uninitialised/unauthorised object
    # cannot cross the admission gate.
    with pytest.raises((TypeError, ValueError, AttributeError)):
        callable_apply()


def test_authority_type_is_not_obtained_from_callable_identity():
    def dynamic_factory():
        return object()

    produced = dynamic_factory()
    assert not isinstance(produced, Admission)
