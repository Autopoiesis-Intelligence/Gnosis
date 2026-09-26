import pytest
from core.canonical_chain import admit_transition
from core.history import AppendOnlyHistory, TransitionRecord
from core.provenance import Provenance

def test_durable_canonical_path_requires_audited_store():
    record=TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")
    proof=Provenance("s0","e0","k1")
    class Store:
        def __init__(self): self.called=False
        def commit_once_with_audit(self,*args):
            self.called=True
            return "AUDITED"
    store=Store()
    result=admit_transition(AppendOnlyHistory(),record,proof,"old","new",1,(1,),durable_store=store)
    assert result=="AUDITED"
    assert store.called

def test_durable_path_is_not_silent_history_only():
    record=TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")
    proof=Provenance("s0","e0","k1")
    with pytest.raises(AttributeError):
        admit_transition(AppendOnlyHistory(),record,proof,"old","new",1,(1,),durable_store=object())
