from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_f1_decision_sources_are_pinned_to_lf():
    lines = {
        line.strip()
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "scripts/v4/contextual_target_f1_decision_v1.py text eol=lf" in lines
    assert "scripts/v4/contextual_target_f1_decision_v4.py text eol=lf" in lines


def test_exact_bytes_history_remains_binary_preserved():
    lines = {
        line.strip()
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "docs/history/exact_bytes/** -text" in lines
