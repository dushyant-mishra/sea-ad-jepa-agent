"""The gate executor must refuse to start rather than pass by not running.

POSITIVE CONTROL FIRST. `test_the_v4_parse_still_produces_the_vacuous_roster`
reproduces the original defect directly: v4's roster expression turns an empty
`--regimes` into an empty list, after which every verdict predicate is an
`all()` over an empty container and Python returns True. If that test ever
stops failing to produce an empty roster, the defect being guarded against has
changed and these guards need rereading. A refusal test whose target no longer
exists is the check that cannot fail.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXEC_V5 = ROOT / "scripts" / "v5" / "teacher_fidelity_gate_executor_v5.py"
GATE_V4 = ROOT / "scripts" / "v5" / "teacher_fidelity_synthetic_gate_v4.py"

FROZEN = ["A_tuning_sparse", "B_tuning_dense",
          "C_untuned_highcap", "D_untuned_verysparse"]
ARMS = ["NEG_CAP", "NEG_NOCAP", "POS_AMP", "POS_COMP"]
CHANNELS = ["full", "composition_only", "amplitude_only"]


@pytest.fixture(scope="module")
def ex():
    spec = importlib.util.spec_from_file_location("gate_executor_v5", EXEC_V5)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_v4_parse_still_produces_the_vacuous_roster():
    """The defect this file guards against, reproduced from v4's own source."""
    src = GATE_V4.read_text(encoding="utf-8")
    assert 'for r in a.regimes.split(",") if r.strip()' in src, (
        "v4's roster expression has changed; v4 is historical evidence and "
        "must not be edited, so investigate before touching these guards")
    # the expression itself, applied to the empty argument
    assert [r.strip() for r in "".split(",") if r.strip()] == []
    # and the consequence that made it dangerous
    assert all([]) is True


@pytest.mark.parametrize("raw,code", [
    ("",                                   "REFUSE_EMPTY_ROSTER"),
    ("   ",                                "REFUSE_EMPTY_ROSTER"),
    (",",                                  "REFUSE_EMPTY_ROSTER"),
    ("A_tuning_sparse,",                   "REFUSE_MALFORMED_ROSTER"),
    ("A_tuning_sparse,,B_tuning_dense",    "REFUSE_MALFORMED_ROSTER"),
    ("A_tuning_sparse,A_tuning_sparse",    "REFUSE_DUPLICATE_REGIME"),
    ("A_tuning_sparse,NOT_A_REGIME",       "REFUSE_UNKNOWN_REGIME"),
    ("A_tuning_sparse",                    "REFUSE_SILENT_SUBSET"),
])
def test_roster_refusals_name_their_own_reason(ex, raw, code):
    with pytest.raises(SystemExit) as got:
        ex.parse_roster(raw, FROZEN, allow_partial=False)
    assert code in str(got.value), (
        f"refused for the wrong reason: expected {code}, got {got.value}")


def test_none_roster_is_refused(ex):
    with pytest.raises(SystemExit) as got:
        ex.parse_roster(None, FROZEN, allow_partial=False)
    assert "REFUSE_NO_ROSTER" in str(got.value)


def test_duplicate_is_caught_before_the_dict_would_collapse_it(ex):
    """dict() would silently turn A,A into one regime and look like a clean run."""
    assert len({"A_tuning_sparse": 1, "A_tuning_sparse": 2}) == 1   # the trap
    with pytest.raises(SystemExit) as got:
        ex.parse_roster("A_tuning_sparse,A_tuning_sparse", FROZEN,
                        allow_partial=False)
    assert "before the list becomes a dict" in str(got.value)


def test_full_roster_is_accepted_and_not_partial(ex):
    roster, partial = ex.parse_roster(",".join(FROZEN), FROZEN,
                                      allow_partial=False)
    assert roster == FROZEN and partial is False


def test_subset_is_accepted_only_with_the_explicit_flag(ex):
    roster, partial = ex.parse_roster("A_tuning_sparse", FROZEN,
                                      allow_partial=True)
    assert roster == ["A_tuning_sparse"] and partial is True


def test_completeness_check_rejects_every_missing_piece(ex):
    """assert_complete must notice absence, which is what all() cannot."""
    full_arm = {"status": "OK", "channels": {c: {} for c in CHANNELS}}
    results = {r: {a: dict(full_arm) for a in ARMS} for r in FROZEN}
    calib = {f"{r}|{a}": {} for r in FROZEN for a in ARMS}

    assert ex.assert_complete(results, calib, FROZEN, ARMS, CHANNELS) == []

    assert ex.assert_complete({}, calib, FROZEN, ARMS, CHANNELS)
    assert ex.assert_complete(results, {}, FROZEN, ARMS, CHANNELS)

    missing_arm = {r: {a: dict(full_arm) for a in ARMS} for r in FROZEN}
    del missing_arm[FROZEN[0]]["NEG_CAP"]
    assert any("arms" in p for p in
               ex.assert_complete(missing_arm, calib, FROZEN, ARMS, CHANNELS))

    missing_ch = {r: {a: {"status": "OK",
                          "channels": {c: {} for c in CHANNELS}}
                      for a in ARMS} for r in FROZEN}
    del missing_ch[FROZEN[1]]["POS_AMP"]["channels"]["amplitude_only"]
    assert any("channels" in p for p in
               ex.assert_complete(missing_ch, calib, FROZEN, ARMS, CHANNELS))

    short_cal = dict(calib)
    short_cal.pop(f"{FROZEN[2]}|POS_COMP")
    probs = ex.assert_complete(results, short_cal, FROZEN, ARMS, CHANNELS)
    assert any("no calibration cell" in p for p in probs)


def test_executor_imports_v4_science_rather_than_reimplementing_it(ex):
    """The estimand must not drift while an executor bug is being fixed."""
    v4 = ex._load_v4()
    for name in ("one_arm", "simulate", "stable_seed", "binom_upper95",
                 "amplitude_leakage", "REGIMES", "ARMS", "CHANNELS",
                 "SEED", "ALPHA", "DONOR_FRACTION",
                 "FP_UPPER_LIMIT", "POWER_LOWER_LIMIT"):
        assert hasattr(v4, name), f"v4 no longer exposes {name}"
    assert list(v4.REGIMES) == FROZEN
    assert list(v4.ARMS) == ARMS
    assert list(v4.CHANNELS) == CHANNELS
    # importing v4 must not run its Monte Carlo
    assert v4.__name__ != "__main__"


def test_v4_is_preserved_unmodified_beside_the_successor():
    assert GATE_V4.exists(), "v4 is execution evidence and must remain"
    assert EXEC_V5.exists() and EXEC_V5 != GATE_V4
