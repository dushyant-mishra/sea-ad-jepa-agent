from pathlib import Path

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import CANONICAL_RUNTIME_SOURCE_FILES


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v5-inactive-runtime-step-guard.yml"


def test_v2_continuation_is_in_transitive_runtime_provenance():
    assert "ema_persisted_continuation_v2.py" in CANONICAL_RUNTIME_SOURCE_FILES, (
        "canonical continuation can change without moving runtime provenance digest"
    )


def test_v2_continuation_changes_trigger_focused_runtime_ci():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py" in text, (
        "canonical continuation source is not watched by focused runtime CI"
    )
    assert "tests/test_v5_ema_continuation_canonicalization_red.py" in text, (
        "canonicalization guard itself is not executed by focused runtime CI"
    )
