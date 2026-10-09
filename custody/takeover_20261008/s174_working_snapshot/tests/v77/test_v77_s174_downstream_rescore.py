"""S174 downstream re-score: the committed record is what the committed code produces, the re-scorer
reproduces every count the old records recorded before it says anything new, every record that depends on
the replayed inputs is classified, and no new verdict is computed from a threshold."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v77" / "rescore_s174_downstream.py"
REC = ROOT / "results" / "v77" / "s174_replay" / "S174_DOWNSTREAM_RESCORE_V1.json"
MD = ROOT / "docs" / "agent" / "S174_DOWNSTREAM_RESCORE.md"
spec = importlib.util.spec_from_file_location("s174_rescore", SCRIPT)
R = importlib.util.module_from_spec(spec)
sys.modules["s174_rescore"] = R
spec.loader.exec_module(R)
# Records that name the cache-derived universe but are not replayed here, each for a reason the record states.
NOT_MATERIAL_PREFIXES = ("V77_S157_", "V77_CONTEXT_SHORTCUT_AUDIT_", "REHEARSAL_", "V77_RUNTIME_HANDOFF_",
                         "V77_SYNTHETIC_STATUS_AND_DEFECT_REGISTER_")
# The old real target values these records quote: expression and detection points, abundance, T5.
OLD_TARGET_VALUES = ("0.3291", "0.377", "0.6148", "1843.8", "0.8871", "0.8605", "1.012", "1976.6", "1685.8", "0.5621")


def _rec() -> dict:
    return json.loads(REC.read_text(encoding="utf-8"))


def test_band_membership_and_ratios_ignore_non_finite_values():
    e = {"t": {"point": 2.0, "accept_low": 1.0, "accept_high": 3.0}}
    assert R.inside({"t": 1.0}, e, ["t"]) == ["t"] and R.inside({"t": 3.5}, e, ["t"]) == []
    assert R.inside({"t": float("nan")}, e, ["t"]) == []
    assert R.ratio(float("nan"), e, "t") is None and R.ratio(3.0, e, "t") == 1.5
    assert R.r4(float("nan")) is None and R.r4(None) is None


def test_committed_record_and_rendering_are_reproduced_by_committed_code(tmp_path):
    rec = _rec()
    assert rec["code_sha256"] == R.sha(SCRIPT)
    fresh = json.loads(json.dumps(R.build(tmp_path / "x.json")))
    assert {k: v for k, v in fresh.items() if k != "record_path"} == \
           {k: v for k, v in rec.items() if k != "record_path"}
    assert MD.read_text(encoding="utf-8") == R.markdown(rec)


def test_the_rescorer_is_faithful_before_it_says_anything_new():
    rec = _rec()
    assert rec["substate_search"]["faithful_to_recorded_counts"] is True
    bg = rec["background_rounds"]
    assert bg["faithful_to_recorded_counts"] is True
    rows = [r for rd in bg["rounds"] for r in rd["rows"]]
    assert rows and all(r["recorded_n_inside"] == r["old_n_inside_recomputed"] for r in rows)
    assert all(v["same_candidates"] and v["same_recorded_statistics"] for v in bg["duplicates_counted_once"].values())


def test_step3_figures_are_bound_to_the_recorded_text():
    s3 = json.loads((ROOT / "results/v77/V77_STEP3_BACKGROUND_CALIBRATION_RESULT_V1.json").read_text(encoding="utf-8"))
    text = s3["WHY_STEP_3_IS_NOT_CLOSED"]["systematic_failure"]
    for val, tgt in R.STEP3_FIGURES.values():
        assert val in text and tgt in text
    sd = json.loads((ROOT / "results/v77/V77_SUBSTATE_FAMILY_DECISION_V1.json").read_text(encoding="utf-8"))
    dial = sd["BEST_SETTING_AND_WHY_IT_REVEALS_THE_MECHANISM"]["why_abundance_scale_is_the_dial"]
    assert all(f"{v} at {k}" in dial for k, v in R.SUBSTATE_DIAL.items())


def test_every_record_that_depends_on_the_replayed_inputs_is_classified():
    """A record depends on the replayed inputs if it names one, or embeds one of the old real target values.
    Each such record must be re-scored here, pending a synthetic replay, replayed, or classified with a reason."""
    rec = _rec()
    replayed = {p.name for p in (ROOT / "results" / "v77" / "s174_replay").glob("*.json")}
    markers = [n[:-5] for n in replayed if n.startswith("V77_")] + ["frozen_evaluation_universe",
                                                                     "TRAIN_PREVALENCE05_19569"]
    rescored = {Path(k).name for k in rec["inputs"] if "/s174_replay/" not in k}
    classified = rescored | set(rec["pending_synthetic_replay"]) | set(rec["classified_elsewhere"]) | replayed
    unclassified = []
    for p in sorted((ROOT / "results" / "v77").glob("*.json")):
        if p.name in classified or p.name.startswith(NOT_MATERIAL_PREFIXES + ("S174_",)):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if any(m in t for m in markers) or any(re.search(r"(?<![0-9.])" + re.escape(v) + r"(?![0-9])", t)
                                               for v in OLD_TARGET_VALUES):
            unclassified.append(p.name)
    assert not unclassified, unclassified


def test_no_new_verdict_is_computed():
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    new_verdicts = {k for k in keys(_rec()) if k.lower() in ("verdict", "decision", "winner", "selected", "status")}
    assert not new_verdicts, new_verdicts
