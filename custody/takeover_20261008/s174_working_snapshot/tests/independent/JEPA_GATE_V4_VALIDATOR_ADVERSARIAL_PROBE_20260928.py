#!/usr/bin/env python3
"""Independent, read-only mutation probe for Claude's gate-v4 receipt validator.

Intentionally RED on known-unsafe versions. Does not run Monte Carlo, inspect
real expression, write to GitHub, or authorize a biological experiment.

Usage inside the JEPA checkout:
  python JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py \
    --validator scripts/v5/gate_v4_receipt_validator_v1.py \
    --receipt results/v29/TEACHER_FIDELITY_SYNTHETIC_GATE_V4.json \
    --producer scripts/v5/teacher_fidelity_synthetic_gate_v4.py

  python JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py --self-check

Version-specific: the ORIGINAL v4 4-regime, 4-arm, 3-channel receipt only.
A test that rejects for the wrong reason is not counted as a successful mutant.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Callable

REGIMES = ["A_tuning_sparse", "B_tuning_dense", "C_untuned_highcap",
           "D_untuned_verysparse"]
ARMS = ["NEG_CAP", "NEG_NOCAP", "POS_AMP", "POS_COMP"]
CHANNELS = ["full", "composition_only", "amplitude_only"]
PRODUCER_SHA = "648dee5850670c3587e3f8bbe346003ec1d4c08d20fdd54f724a4b959d71eab6"
RECEIPT_SHA = "09f66e2049fad95235d10343daaaaec38380c1266519b691d964e03c10d12ea2"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cal(r: dict, arm: str = "NEG_CAP", regime: str = REGIMES[0]) -> dict:
    return r["calibration"][f"{regime}|{arm}"]


def arm(r: dict, name: str = "NEG_CAP", regime: str = REGIMES[0]) -> dict:
    return r["results"][regime][name]


def zero_regimes(r):
    r["results"] = {}
    r["calibration"] = {}
    r["incomplete_records"] = []


def partial_regimes(r):
    del r["results"][REGIMES[-1]]
    for a in ARMS:
        del r["calibration"][f"{REGIMES[-1]}|{a}"]


def substituted_calibration_key(r):
    r["calibration"]["FAKE_REGIME|POS_COMP"] = r["calibration"].pop(
        f"{REGIMES[0]}|POS_COMP")
    assert len(r["calibration"]) == 16, "must preserve 16-cell count"


def missing_one_arm(r):
    del r["results"][REGIMES[0]]["NEG_CAP"]
    del r["calibration"][f"{REGIMES[0]}|NEG_CAP"]


def swapped_positive_composition(r):
    arm(r, "POS_COMP")["channels"]["composition_only"]["qualifies"] = False


def swapped_positive_amplitude(r):
    arm(r, "POS_AMP")["channels"]["amplitude_only"]["qualifies"] = False


def hidden_incomplete_calibration(r):
    cal(r)["datasets_requested"] += 1
    # Its status remains `complete: true` — inconsistent on purpose.


def altered_calibration_rate(r):
    cal(r)["rate"] = 0.99


def missing_cp_endpoint(r):
    del cal(r)["binomial_upper95"]


def missing_required_label(r):
    del cal(r, "POS_AMP")["required_qualification"]


def missing_model_family(r):
    del arm(r)["model_families"]


def substituted_poisson_model(r):
    arm(r)["model_families"] = ["poisson"]
    arm(r)["poisson_fallbacks"] = 0


def absent_fallback_counter(r):
    del arm(r)["poisson_fallbacks"]


def zero_requested_shams(r):
    arm(r)["sham_draws_requested"] = 0


def positive_string_not_boolean(r):
    arm(r, "POS_COMP")["channels"]["full"]["qualifies"] = "true"


def nonfinite_positive_p(r):
    arm(r, "POS_AMP")["channels"]["full"]["sham_null_p"] = float("inf")


def contradictory_p_and_qualification(r):
    # Positive arm's preexisting qualifies=True remains unchanged; p cannot qualify.
    arm(r, "POS_COMP")["channels"]["full"]["sham_null_p"] = 0.99


def missing_nonlinear_diagnostic(r):
    del arm(r, "POS_COMP")["amplitude_leakage"]


def contradictory_overall_verdict(r):
    r["gate_pass"] = False


def missing_channel(r):
    del arm(r)["channels"]["amplitude_only"]


def silent_nb_fallback(r):
    arm(r)["poisson_fallbacks"] = 1


# Each regex is about the INTENDED defect; 'it failed somehow' is not enough.
MUTANTS: list[tuple[str, Callable, str]] = [
    ("empty_regimes", zero_regimes, r"(?i)regime|zero"),
    ("partial_regimes", partial_regimes, r"(?i)regime|calibration"),
    ("substituted_calibration_key", substituted_calibration_key, r"(?i)calibration.*(name|key|census|set)|unexpected|unknown"),
    ("missing_arm", missing_one_arm, r"(?i)arm|calibration"),
    ("wrong_pos_comp_channel", swapped_positive_composition, r"(?i)channel|composition|pattern"),
    ("wrong_pos_amp_channel", swapped_positive_amplitude, r"(?i)channel|amplitude|pattern"),
    ("inconsistent_calibration_counts", hidden_incomplete_calibration, r"(?i)calibration|dataset|count"),
    ("tampered_stored_rate", altered_calibration_rate, r"(?i)rate|calibration"),
    ("missing_cp_endpoint", missing_cp_endpoint, r"(?i)endpoint|clopper|binomial|calibration"),
    ("missing_calibration_arm_type", missing_required_label, r"(?i)calibration|require|type|arm"),
    ("missing_model_family", missing_model_family, r"(?i)model|negative.binomial|family"),
    ("poisson_disguised_as_nb", substituted_poisson_model, r"(?i)model|negative.binomial|poisson|family"),
    ("missing_fallback_counter", absent_fallback_counter, r"(?i)fallback|missing|model"),
    ("zero_requested_shams", zero_requested_shams, r"(?i)sham|draw|count"),
    ("string_boolean", positive_string_not_boolean, r"(?i)bool|type|qualif|channel"),
    ("infinite_p", nonfinite_positive_p, r"(?i)finite|infinite|range|p.value|nonfinite"),
    ("p_qualification_contradiction", contradictory_p_and_qualification, r"(?i)p.value|sham|null|qualif|threshold"),
    ("missing_nonlinear_amplitude_diagnostic", missing_nonlinear_diagnostic, r"(?i)amplitude|nonlinear|diagnostic"),
    ("contradictory_overall_gate", contradictory_overall_verdict, r"(?i)gate|verdict|contradict|receipt"),
    ("missing_channel", missing_channel, r"(?i)channel"),
    ("positive_fallback_counter", silent_nb_fallback, r"(?i)poisson|fallback"),
]


def self_check() -> None:
    """Verify mutation construction, NOT the GitHub producer or validator."""
    from scipy.stats import beta
    template = {"results": {}, "calibration": {}, "incomplete_records": [],
                "gate_pass": True, "producer_sha256": PRODUCER_SHA}
    pattern = {"NEG_CAP": (False, False, False), "NEG_NOCAP": (False, False, False),
               "POS_AMP": (True, False, True), "POS_COMP": (True, True, False)}
    for g in REGIMES:
        template["results"][g] = {}
        for a in ARMS:
            qualified = a.startswith("POS")
            n = 30 if qualified else 120
            k = n if qualified else 6
            c = {"datasets_requested": n, "datasets_used": n, "complete": True,
                 "qualified": k, "rate": k/n,
                 "binomial_upper95": (1.0 if k == n else float(beta.ppf(.975,k+1,n-k))),
                 "required_qualification": qualified}
            template["calibration"][f"{g}|{a}"] = c
            cs = {}
            for ch, want in zip(CHANNELS, pattern[a]):
                cs[ch] = {"qualifies": want, "sham_null_p": .01 if want else .8,
                          "fraction_donors_positive": .9 if want else .4,
                          "median_increment": .1 if want else -.01}
            template["results"][g][a] = {
                "status": "OK", "channels": cs, "channels_run": CHANNELS[:],
                "sham_draws_requested": 99, "qualifies": qualified,
                "arm_pass": True, "required": qualified,
                "model_families": ["negative_binomial"],
                "poisson_fallbacks": 0,
                "amplitude_leakage": {"r2_gain_from_z_terms": .0001}}
    fingerprints = set()
    baseline = json.dumps(template, sort_keys=True)
    for name, mutant, _ in MUTANTS:
        sample = copy.deepcopy(template)
        mutant(sample)
        fp = json.dumps(sample, sort_keys=True)
        assert fp != baseline, f"{name}: vacuous fixture"
        assert fp not in fingerprints, f"{name}: duplicate mutation fixture"
        fingerprints.add(fp)
    # Independent numerical witness for the frozen pair-specific denominator.
    # The 29-address artifact excludes all three query/panel groups (15), all
    # six historical readouts, and eight reference genes: 29 * 2 = 58.
    # Each directed comparison keeps the UNUSED group's five addresses.
    d29 = 1000 - 29 * 2
    naive = d29 - 19 * 1
    protocol = 1000 - (10 + 6 + 8) * 2 - 19 * 1
    assert (d29, naive, protocol) == (942, 923, 933)
    print("DENOMINATOR SELF-CHECK PASS: D29=942, naive=923, frozen pairwise=933")
    print(f"FIXTURE SELF-CHECK PASS: {len(MUTANTS)} distinct nonvacuous mutations")
    print("NOT a test of the actual GitHub validator; use --validator/--receipt/--producer.")


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("jepa_validator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def duplicate_json_key_cli_test(source: Path, base: dict, producer: Path, receipt: Path) -> dict:
    """JSON object keys are duplicated in raw bytes; json.load normally hides that.

    Use matching mutated-file digest solely to isolate the duplicate-key parser
    check. This does NOT authenticate the published original receipt.
    """
    raw = receipt.read_text(encoding="utf-8")
    needle = '"A_tuning_sparse": {'
    assert raw.count(needle) >= 1
    forged = raw.replace(needle, needle + '}, "A_tuning_sparse": {', 1)
    parsed = json.loads(forged)
    assert parsed == base, "duplicate-key probe must preserve parsed content"
    with tempfile.TemporaryDirectory(prefix="jepa_duplicate_key_probe_") as t:
        root = Path(t)
        p = root / "duplicate.json"
        p.write_text(forged, encoding="utf-8")
        outdir = root / "out"
        run = subprocess.run([
            sys.executable, str(source), "--receipt", str(p),
            "--script", str(producer), "--out-dir", str(outdir),
            "--expect-script-sha256", PRODUCER_SHA,
            "--expect-receipt-sha256", sha(p),
        ], capture_output=True, text=True)
    return {"case": "duplicate_raw_json_key", "status": "REJECTED" if run.returncode != 0
            else "FALSE_GREEN", "exit_code": run.returncode,
            "note": "mutated-file SHA supplied to isolate duplicate parser check; not proof of source authenticity",
            "stdout_tail": run.stdout[-450:], "stderr_tail": run.stderr[-300:]}


def cross_process_seed_check(producer: Path) -> dict:
    """Compare actual generator seed outputs in separate Python processes."""
    code = (
        "import importlib.util,json,sys; "
        "s=importlib.util.spec_from_file_location('jepa_v4_generator',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "print(json.dumps([m.stable_seed(m.SEED,'A_tuning_sparse','NEG_CAP'), "
        "m.stable_seed(m.SEED,'D_untuned_verysparse','POS_COMP','cal',17)]))"
    )
    outputs = []
    for seed in ("1", "777"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-c", code, str(producer)], env=env,
                           capture_output=True, text=True, timeout=90)
        if p.returncode:
            return {"case": "cross_process_seed_stability", "status": "ERROR",
                    "process": seed, "stderr": p.stderr[-600:]}
        outputs.append(p.stdout.strip().splitlines()[-1])
    return {"case": "cross_process_seed_stability",
            "status": "PASS" if outputs[0] == outputs[1] else "FAIL_SEED_DRIFT",
            "note": "PASS means no cross-process seed divergence was detected",
            "values": outputs}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--validator", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--producer", type=Path)
    p.add_argument("--out-json", type=Path)
    a = p.parse_args()
    if a.self_check:
        self_check()
        return 0
    if not all([a.validator, a.receipt, a.producer]):
        p.error("supply --validator, --receipt and --producer or --self-check")
    ssha, rsha = sha(a.producer), sha(a.receipt)
    if (ssha, rsha) != (PRODUCER_SHA, RECEIPT_SHA):
        raise SystemExit("REFUSE: original input digests differ from pinned v4 artifacts")
    base = json.loads(a.receipt.read_text(encoding="utf-8"))
    m = load_validator(a.validator)
    pass_baseline = m.validate(copy.deepcopy(base), ssha, rsha)
    if pass_baseline.get("validated_pass") is not True:
        raise SystemExit("REFUSE: original published receipt failed validator precondition")
    rows = []
    for name, mutant, reason in MUTANTS:
        altered = copy.deepcopy(base)
        mutant(altered)
        assert altered != base, f"{name}: VACUOUS MUTATION"
        result = m.validate(altered, ssha, rsha)
        rejected = result.get("validated_pass") is False
        failures = result.get("failures", [])
        reason_correct = any(re.search(reason, str(f)) for f in failures)
        status = ("REJECTED_INTENDED_REASON" if rejected and reason_correct
                  else "REJECTED_WRONG_REASON" if rejected else "FALSE_GREEN")
        rows.append({"case": name, "status": status, "failure_reasons": failures[:5]})
    # The producer/receipt binding mismatch cannot be represented by a JSON-only mutant.
    wrong_source = m.validate(copy.deepcopy(base), "0" * 64, rsha)
    rejected = wrong_source.get("validated_pass") is False
    relevant = any(re.search("sha|digest|producer|script|source", str(f), re.I)
                   for f in wrong_source.get("failures", []))
    rows.append({"case": "forged_producer_sha_argument",
                 "status": "REJECTED_INTENDED_REASON" if rejected and relevant
                           else "REJECTED_WRONG_REASON" if rejected else "FALSE_GREEN",
                 "failure_reasons": wrong_source.get("failures", [])[:5]})
    rows.append(duplicate_json_key_cli_test(a.validator, base, a.producer, a.receipt))
    rows.append(cross_process_seed_check(a.producer))
    tally = {q: sum(x["status"] == q for x in rows) for q in
             ["REJECTED_INTENDED_REASON", "REJECTED", "REJECTED_WRONG_REASON", "FALSE_GREEN", "PASS", "FAIL_SEED_DRIFT", "ERROR"]}
    output = {"scope": "original pinned v4 only; receipt mutations; no Monte Carlo",
              "producer_sha256": ssha, "receipt_sha256": rsha,
              "baseline_pass": True, "results": rows, "tally": tally}
    print(json.dumps(output, indent=2, allow_nan=False))
    if a.out_json:
        a.out_json.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    return 0 if all(r["status"] in ("REJECTED_INTENDED_REASON", "REJECTED", "PASS")
                    for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
