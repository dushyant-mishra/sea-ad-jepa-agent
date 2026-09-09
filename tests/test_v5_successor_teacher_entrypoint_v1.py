"""The successor teacher entrypoint must not silently produce an ungated run.

The entrypoint derives a training module from the historical teacher script by
redirecting its single update call at the gated step. Everything that makes that
trustworthy is a refusal: refusing a substitution that did not land where it was
meant to, refusing a root that cannot supply what training reads, and refusing to
leave any ungated call site behind. Those are what is tested.

Synthetic roots are used for the refusals so the cases can be constructed
exactly. The real derivation is checked against the actual historical script,
which is what the claim is about.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v4 import v5_successor_teacher_entrypoint_v1 as entry  # noqa: E402

REAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), ROOT)


def _a_root(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "scripts" / "v4" / "stage81a3_prod41k_teacher_t1.py"
    script.parent.mkdir(parents=True)
    script.write_text(body, encoding="utf-8")
    return tmp_path


def test_the_real_derivation_changes_exactly_the_update_call() -> None:
    report = entry.verify_derivation()
    assert len(report["added"]) == 1 and len(report["removed"]) == 1
    assert entry.ORIGINAL_CALL in report["removed"][0]
    assert entry.SUCCESSOR_CALL in report["added"][0]
    assert report["ungated_call_sites_remaining"] == 0


def test_no_ungated_call_survives_in_the_derived_source() -> None:
    """The property the whole entrypoint exists to establish."""
    assert entry.ORIGINAL_CALL not in entry.derived_source()


def test_a_root_without_the_historical_script_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError) as caught:
        entry.verify_derivation(tmp_path)
    assert entry.STOP_DERIVATION in str(caught.value)


def test_a_missing_call_site_is_refused(tmp_path: Path) -> None:
    """A script the substitution does not match must not yield a module."""
    root = _a_root(tmp_path, "def main():\n    result = something_else()\n")
    with pytest.raises(RuntimeError) as caught:
        entry.derived_source(root)
    assert entry.STOP_DERIVATION in str(caught.value)


def test_two_call_sites_are_refused(tmp_path: Path) -> None:
    """Substituting the first of two would leave a live ungated path."""
    root = _a_root(tmp_path, "def main():\n"
                             "    result = phase_e.run_update(a)\n"
                             "    result = phase_e.run_update(b)\n")
    with pytest.raises(RuntimeError) as caught:
        entry.derived_source(root)
    assert entry.STOP_DERIVATION in str(caught.value)


def test_a_root_that_cannot_run_training_is_refused_before_it_starts(
        tmp_path: Path) -> None:
    """Reported for inspection, but refused for execution.

    Deriving and reading the diff in a checkout without the data is useful;
    starting a run there is not, and the failure would otherwise surface deep
    inside the loader.
    """
    root = _a_root(tmp_path, "def main():\n    result = phase_e.run_update(a)\n")
    assert entry.verify_derivation(root)["missing_execution_inputs"]
    with pytest.raises(RuntimeError) as caught:
        entry.build_module(root)
    assert "cannot run training" in str(caught.value)


def test_a_root_holding_the_data_reports_nothing_missing() -> None:
    """Otherwise the execution check would refuse every real root."""
    for root in REAL_ROOTS:
        if (root / "exports" / "contextual_biology_v6r5a_20260822").exists():
            assert entry.verify_derivation(root)["missing_execution_inputs"] == []
            return
    pytest.skip("no root with the training exports is reachable here")


def test_the_historical_script_is_not_modified() -> None:
    """The derivation must leave the provenance-bound file alone."""
    text = entry.HISTORICAL.read_text(encoding="utf-8")
    assert entry.ORIGINAL_CALL in text
    assert entry.SUCCESSOR_CALL not in text
