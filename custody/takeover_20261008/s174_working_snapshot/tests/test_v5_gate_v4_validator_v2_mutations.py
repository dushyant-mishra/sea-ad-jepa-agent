"""Mutations the independent probe did NOT specify, against validator v2.

WHY THIS FILE EXISTS SEPARATELY FROM THE SUPPLIED PROBE

  The reviewer's `JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py` defines
  21 corrupted receipts and checks that each is rejected for its own reason.
  Validator v1 admitted 16 of them; v2 rejects all 21.

  But v2 was written AFTER reading that probe, so passing it is necessary and
  not sufficient. A validator tuned to a known attack list proves only that it
  handles the listed attacks. Every mutation below is therefore one the probe
  does not contain, chosen to attack a DIFFERENT seam of the same receipt, and
  each asserts BOTH that the receipt is rejected and that the stated reason is
  the intended one. A rejection for the wrong reason is a failure here, exactly
  as it is in the probe.

  These run against the committed 33,401-byte frozen receipt, so they exercise
  the real object rather than a hand-built template that might not share its
  shape.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "results" / "v29" / "TEACHER_FIDELITY_SYNTHETIC_GATE_V4.json"
VALIDATOR = ROOT / "scripts" / "v5" / "gate_v4_receipt_validator_v2.py"
PRODUCER = ROOT / "scripts" / "v5" / "teacher_fidelity_synthetic_gate_v4.py"

REG = "A_tuning_sparse"


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("gate_v4_validator_v2", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def v2():
    return _load_module(VALIDATOR)


@pytest.fixture(scope="module")
def receipt():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def shas(receipt):
    """The digests the validator must be given: script digest == producer field."""
    import hashlib
    rsha = hashlib.sha256(RECEIPT.read_bytes()).hexdigest()
    return receipt["producer_sha256"], rsha


def _cal(r, arm="NEG_CAP", regime=REG):
    return r["calibration"]["%s|%s" % (regime, arm)]


def _arm(r, arm="NEG_CAP", regime=REG):
    return r["results"][regime][arm]


# --------------------------------------------------------------------------
# Mutations absent from the supplied probe
# --------------------------------------------------------------------------

def m_p_below_permutation_floor(r):
    """99 sham draws cannot produce p < 1/100. This p is arithmetically impossible."""
    _arm(r, "POS_AMP")["channels"]["full"]["sham_null_p"] = 0.001


def m_donor_fraction_above_one(r):
    _arm(r, "POS_COMP")["channels"]["full"]["fraction_donors_positive"] = 1.5


def m_channels_run_disagrees_with_channels(r):
    _arm(r)["channels_run"] = ["full", "composition_only"]


def m_qualified_exceeds_datasets_used(r):
    _cal(r)["qualified"] = _cal(r)["datasets_used"] + 1


def m_qualified_is_float_not_int(r):
    c = _cal(r)
    c["qualified"] = float(c["qualified"])


def m_negative_arm_relabelled_positive(r):
    """Polarity flip, not deletion: NEG_CAP claims it was required to qualify."""
    _cal(r, "NEG_CAP")["required_qualification"] = True


def m_producer_field_deleted(r):
    del r["producer_sha256"]


def m_rate_is_nan(r):
    _cal(r)["rate"] = float("nan")


def m_negative_cell_qualifies_everywhere(r):
    """Every negative dataset qualifying puts the CP upper limit at 1.0."""
    c = _cal(r)
    c["qualified"] = c["datasets_used"]
    c["rate"] = 1.0
    c["binomial_upper95"] = 1.0


def m_incomplete_records_present(r):
    r["incomplete_records"] = [{"regime": REG, "arm": "NEG_CAP",
                                "why": "fit did not converge"}]


def m_self_consistent_undersized_calibration(r):
    """The subtle one: shrink a negative cell from 120 to 60 datasets and keep
    every derived field internally consistent. Nothing contradicts anything;
    it is simply not the original-v4 design any more."""
    from scipy.stats import beta
    c = _cal(r)
    c["datasets_requested"] = 60
    c["datasets_used"] = 60
    c["qualified"] = 3
    c["rate"] = 3 / 60
    c["binomial_upper95"] = float(beta.ppf(0.975, 4, 57))
    c["complete"] = True


def m_amplitude_bins_emptied(r):
    _arm(r)["amplitude_leakage"]["conditional_means_by_z_bin"] = []


def m_amplitude_scalar_is_string(r):
    _arm(r)["amplitude_leakage"]["r2_gain_from_z_terms"] = "0.31"


MUTANTS = [
    ("p_below_permutation_floor", m_p_below_permutation_floor, r"(?i)sham_null_p|finite|within"),
    ("donor_fraction_above_one", m_donor_fraction_above_one, r"(?i)fraction_donors_positive|within"),
    ("channels_run_disagrees", m_channels_run_disagrees_with_channels, r"(?i)channels_run"),
    ("qualified_exceeds_used", m_qualified_exceeds_datasets_used, r"(?i)exceeds|qualified"),
    ("qualified_is_float", m_qualified_is_float_not_int, r"(?i)integer|qualified"),
    ("negative_arm_relabelled_positive", m_negative_arm_relabelled_positive, r"(?i)polarity|required_qualification"),
    ("producer_field_deleted", m_producer_field_deleted, r"(?i)producer|digest|mismatch"),
    ("rate_is_nan", m_rate_is_nan, r"(?i)rate"),
    ("negative_cell_qualifies_everywhere", m_negative_cell_qualifies_everywhere, r"(?i)clopper|exceeds|upper"),
    ("incomplete_records_present", m_incomplete_records_present, r"(?i)incomplete"),
    ("self_consistent_undersized_calibration", m_self_consistent_undersized_calibration, r"(?i)datasets_requested|original-v4"),
    ("amplitude_bins_emptied", m_amplitude_bins_emptied, r"(?i)amplitude|conditional_means"),
    ("amplitude_scalar_is_string", m_amplitude_scalar_is_string, r"(?i)amplitude|finite"),
]


def test_the_pristine_receipt_validates(v2, receipt, shas):
    """Baseline. If this fails, every rejection below proves nothing."""
    ssha, rsha = shas
    out = v2.validate(copy.deepcopy(receipt), ssha, rsha)
    assert out["validated_pass"] is True, (
        "the frozen receipt must validate, otherwise the mutation tests are "
        f"rejecting a receipt that was already broken: {out['failures'][:5]}")
    assert out["recomputed_verdict_flags"]["gate_pass"] is True


@pytest.mark.parametrize("name,mutate,reason", MUTANTS,
                         ids=[m[0] for m in MUTANTS])
def test_mutation_is_rejected_for_its_own_reason(v2, receipt, shas, name, mutate, reason):
    ssha, rsha = shas
    altered = copy.deepcopy(receipt)
    mutate(altered)
    # Type-sensitive vacuity guard. `==` is NOT enough: 6 == 6.0 is True in
    # Python, so an int-to-float corruption compares equal and a real mutation
    # would be dismissed as vacuous. json.dumps renders them "6" and "6.0".
    assert (json.dumps(altered, sort_keys=True, allow_nan=True)
            != json.dumps(receipt, sort_keys=True, allow_nan=True)), (
        f"{name}: vacuous mutation, the fixture is unchanged")

    out = v2.validate(altered, ssha, rsha)
    assert out["validated_pass"] is False, (
        f"{name}: FALSE GREEN — a corrupted receipt validated clean")
    assert any(re.search(reason, str(x)) for x in out["failures"]), (
        f"{name}: rejected for the WRONG reason. Expected a failure matching "
        f"{reason!r}, got {out['failures'][:6]}")


def test_digest_binding_is_blocking_not_informational(v2, receipt, shas):
    """v1 computed this comparison and then ignored it. v2 must fail on it."""
    _, rsha = shas
    out = v2.validate(copy.deepcopy(receipt), "0" * 64, rsha)
    assert out["validated_pass"] is False
    assert out["script_sha_matches_producer_field"] is False
    assert any("producer digest mismatch" in str(x) for x in out["failures"])


def test_duplicate_raw_json_keys_are_rejected_before_dict_construction(v2):
    """json.load silently keeps the last repeat, so a second regime vanishes."""
    raw = RECEIPT.read_text(encoding="utf-8")
    needle = '"%s": {' % REG
    assert raw.count(needle) >= 1
    forged = raw.replace(needle, needle + '}, "%s": {' % REG, 1)

    # plain json.load cannot see the problem at all
    assert json.loads(forged) == json.loads(raw), (
        "the forged text must parse identically, which is exactly why a "
        "dict-level check cannot catch it")

    with pytest.raises(v2.DuplicateJSONKey):
        json.loads(forged, object_pairs_hook=v2._no_duplicate_pairs)


def test_the_frozen_qualification_rule_reproduces_every_stored_flag(v2, receipt):
    """v2 recomputes `qualifies` rather than trusting it, which is only sound
    if the recomputation reproduces the real receipt exactly."""
    mismatches = []
    n = 0
    for regime, arms in receipt["results"].items():
        for arm_name, rec in arms.items():
            for ch, cv in rec["channels"].items():
                n += 1
                want = (cv["sham_null_p"] <= v2.ALPHA
                        and cv["fraction_donors_positive"] >= v2.DONOR_FRACTION)
                if bool(cv["qualifies"]) != want:
                    mismatches.append((regime, arm_name, ch))
    assert n == 48, f"expected 48 channel observations, saw {n}"
    assert not mismatches, (
        "the frozen rule p <= ALPHA and donors >= 2/3 does not reproduce the "
        f"receipt's own flags at {mismatches}; v2 must not recompute "
        "qualification if the rule is not the one that produced the receipt")


def test_a_truthy_string_does_not_pass_as_boolean_true(v2, receipt, shas):
    """bool('false') is True. v1 coerced, so a string qualified silently."""
    assert bool("false") is True          # the trap itself
    ssha, rsha = shas
    altered = copy.deepcopy(receipt)
    _arm(altered, "POS_COMP")["channels"]["full"]["qualifies"] = "false"
    out = v2.validate(altered, ssha, rsha)
    assert out["validated_pass"] is False
    assert any("not a JSON boolean" in str(x) for x in out["failures"])


def test_validator_v1_is_preserved_unmodified_beside_v2():
    """v1 is historical execution evidence; v2 is a successor, not an edit."""
    v1 = ROOT / "scripts" / "v5" / "gate_v4_receipt_validator_v1.py"
    assert v1.exists(), "v1 must remain on disk as historical evidence"
    assert VALIDATOR.exists() and VALIDATOR != v1
    assert PRODUCER.exists(), "the frozen v4 producer must remain on disk"
