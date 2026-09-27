import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"


def mutation_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in {"apply", "commit", "commit_once", "append"}:
                    found.append((node.lineno, node.func.attr))
            elif isinstance(node.func, ast.Name):
                if node.func.id in {"SemanticCommit", "commit_once"}:
                    found.append((node.lineno, node.func.id))
    return found


def test_ast_inventory_finds_indirect_mutation_like_calls():
    fixture = ast.parse(
        """
from core.commit import SemanticCommit as SC

def forged(history, record):
    c = SC(candidate=None, admission=None)
    history.commit_once(record, None, None)
"""
    )
    names = []
    for node in ast.walk(fixture):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "SC":
                names.append("SemanticCommit-alias")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "commit_once":
                names.append("commit_once")
    assert names == ["SemanticCommit-alias", "commit_once"]


def test_production_ast_inventory_has_no_forbidden_direct_semantic_commit_constructor():
    offenders = []
    for path in CORE.glob("*.py"):
        if path.name == "commit.py":
            continue
        for _, name in mutation_calls(path):
            if name == "SemanticCommit":
                offenders.append(path.name)
    assert offenders == []
