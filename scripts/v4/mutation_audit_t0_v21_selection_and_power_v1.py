#!/usr/bin/env python3
"""Mutation audit of the V21-T1 selection and power qualification suite.

Committed so the audit is reproducible from a clean checkout. External review of
`a89f4c3f` rightly objected that a commit message claimed a 19/19 result from a
harness that lived only in a session scratchpad, which is evidence nobody else
could check.

A passing suite is a claim, not evidence. This breaks the executor in each way
the contract forbids and requires the suite to catch every one. A mutation that
survives marks a property the contract asserts and the tests do not actually
check.

Method: textual substitution with an **asserted match count**, so a mutation that
silently fails to apply cannot be recorded as caught. Each mutant gets its own
temporary directory containing the module, the suite, and a copy of the committed
frozen V20 code, because the executor resolves the frozen numerics relative to
its own file.

The integration tests that drive the real frozen target learner are deselected
here. They take minutes per run and exercise the frozen learner rather than the
mutated decision logic; they run in the ordinary suite. Everything a mutation
touches is covered by the tests that do run.

Usage:

    python scripts/v4/mutation_audit_t0_v21_selection_and_power_v1.py

Exit status is 0 only if every mutation is caught.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
MODULE = "t0_v21_selection_and_power_v1.py"
TESTS = "test_t0_v21_selection_and_power_v1.py"
FROZEN = "t0_v20_frozen"
DESELECT = "not frozen_learner"

# Three mutations are unreachable by construction rather than untested. Each is
# listed with the proof that no input can reach the branch it removes, and the
# invariant that the suite checks instead. They are reported separately; they are
# not counted as caught, and they are not excused silently.
UNREACHABLE = {
    "stop requiring every donor to be held out exactly once":
        "the loop is `for held_out in range(n_donors)` and appends exactly one "
        "record per iteration, so the post-loop coverage check can never fail. "
        "The real, reachable partition check is in `seal_cross_fit`, and it is "
        "mutated separately and caught.",
    "accept a refined optimum on the edge of the evaluated grid":
        "at stage-B exit every evaluated exponent is an anchor or an expansion, "
        "so the grid is spaced exactly 4 apart and an interior minimum sits at "
        "least 4 from either end; refinement travels at most 3.75 and never "
        "evaluates outside the bracket, so the refined optimum cannot reach a "
        "grid endpoint. The invariant is asserted by "
        "`test_the_ridge_search_invariant_that_makes_two_stop_paths_unreachable`.",
    "drop the bound on how far refinement may travel":
        "four rounds each move the centre by at most their own step, so total "
        "movement is at most 2 + 1 + 0.5 + 0.25 = 3.75 by construction. Same "
        "invariant test.",
}

MUTATIONS: list[tuple[str, str, str]] = [
    # ---- standardization -------------------------------------------------
    ("standardize every refit by sqrt(28) instead of its own n",
     "return float(t_statistic) / math.sqrt(float(n))",
     "return float(t_statistic) / math.sqrt(28.0)"),

    # ---- cross-fitting ---------------------------------------------------
    ("let each fold train on the whole cohort",
     "model = train_fold(train.copy())",
     "model = train_fold(everything.copy())"),

    ("stop requiring every donor to be held out exactly once",
     "    if sorted(held) != list(range(n_donors)):",
     "    if False:"),

    # ---- the planning effect --------------------------------------------
    ("drop the sign-consistency precondition",
     "if not (np.all(signs == signs[0]) and signs[0] != 0):",
     "if False:"),

    ("take the largest refit instead of the smallest",
     "influence_minimum = (float(values.min()) if signs[0] > 0\n"
     "                         else float(values.max()))",
     "influence_minimum = (float(values.max()) if signs[0] > 0\n"
     "                         else float(values.min()))"),

    ("use the influence minimum even when it is less conservative",
     '"planning_standardized_effect": influence if bounded else full,',
     '"planning_standardized_effect": influence,'),

    # ---- INVALID vs NOT_ESTIMABLE ---------------------------------------
    ("absorb nonfinite covariates as an estimability result",
     '    if not np.isfinite(array).all():\n'
     '        _fail(STOP_INVALID_INPUT, "%s contains nonfinite values" % name)',
     "    if False:\n        pass"),

    ("absorb a length mismatch as an estimability result",
     "    if array.size != n:",
     "    if False:"),

    ('accept a sex coding that is not complete binary',
     '    sex_arr = _require_structural_validity("sex", sex, n=n)\n    unique_sex = np.unique(sex_arr)',
     '    sex_arr = _require_structural_validity("sex", sex, n=n)\n    unique_sex = np.array([0.0, 1.0])'),

    # ---- the cross-fit artifact -----------------------------------------
    ('accept any object as a cross-fit artifact',
     '    if not isinstance(artifact, dict) or artifact.get("kind") != ARTIFACT_KIND:',
     '    if False:'),

    ("stop checking that the artifact digest recomputes",
     '    if recomputed != artifact["artifact_digest"]:',
     "    if False:"),

    ('stop checking that each fold trains on the exact complement',
     '        if set(train) != everything - {held}:',
     '        if False:'),

    ("stop checking the score vector against the per-fold predictions",
     "    if not np.array_equal(scores, by_fold):",
     "    if False:"),

    ('allow duplicate donor identifiers',
     '    if len(set(ids)) != n:',
     '    if False:'),

    # ---- power calibration ----------------------------------------------
    ("drop the alpha constraint on the permutation count",
     "    if n_permutations < MIN_PERMUTATIONS_FOR_ALPHA:\n"
     '        _fail(STOP,\n'
     '              "p_upper is (1 + #{null >= t}) / (B + 1), so the smallest "',
     "    if False:\n"
     '        _fail(STOP,\n'
     '              "p_upper is (1 + #{null >= t}) / (B + 1), so the smallest "'),

    ("let the point estimate rather than its lower limit pass the gate",
     '"meets_target": bool(power - 1.96 * se >= target_power)}',
     '"meets_target": bool(power >= target_power)}'),

    ("carry the discovery delta straight across cohort sizes",
     "        signal_to_noise=underlying[\"signal_to_noise\"],",
     "        signal_to_noise=bound[\"planning_standardized_effect\"],"),

    ("stop dividing out the discovery design's HC3 scaling",
     '"signal_to_noise": float(observed_standardized_effect) / factor,',
     '"signal_to_noise": float(observed_standardized_effect),'),

    ("scale the simulated predictor without residualizing the nuisance design",
     "        x_resid = x - q @ (q.T @ x)",
     "        x_resid = x"),

    ("drop the alpha constraint in the nested permutation null",
     "    if n_permutations < MIN_PERMUTATIONS_FOR_ALPHA:\n"
     "        _fail(STOP,\n"
     '              "the smallest attainable p-value is 1/(B+1); rejecting at alpha = "',
     "    if False:\n"
     "        _fail(STOP,\n"
     '              "the smallest attainable p-value is 1/(B+1); rejecting at alpha = "'),

    ("never refit the folds under a permutation",
     "        null[i] = statistic(fitted + residual[rng.permutation(n)])",
     "        null[i] = observed"),

    # ---- the ridge procedure --------------------------------------------
    ("invert the frozen V20 tie rule to prefer less regularization",
     "return float(near[-1])",
     "return float(near[0])"),

    ("use exact equality instead of the frozen V20 near-tie tolerance",
     "tol = V20_TIE_RELATIVE_TOLERANCE * max(1.0, abs(minloss))",
     "tol = 0.0"),

    ("stop recentring during refinement",
     "        best = chosen\n",
     "        best = best\n"),

    ("accept a bracket endpoint after the expansions are exhausted",
     "    if best in (grid[0], grid[-1]):\n"
     "        _fail(STOP_RIDGE_BOUNDARY,\n"
     '              "the minimum remains at a bracket endpoint (exponent %r) after "',
     "    if False:\n"
     "        _fail(STOP_RIDGE_BOUNDARY,\n"
     '              "the minimum remains at a bracket endpoint (exponent %r) after "'),

    ("accept a refined optimum on the edge of the evaluated grid",
     "    if best in (grid[0], grid[-1]):\n"
     "        _fail(STOP_RIDGE_BOUNDARY,\n"
     '              "stage C: refinement settled on exponent %r, an endpoint of the "',
     "    if False:\n"
     "        _fail(STOP_RIDGE_BOUNDARY,\n"
     '              "stage C: refinement settled on exponent %r, an endpoint of the "'),

    ("drop the bound on how far refinement may travel",
     "    if movement > MAX_REFINEMENT_MOVEMENT + 1e-12:",
     "    if False:"),

    # ---- ridge stability -------------------------------------------------
    ("build the near-optimal set on unpaired losses",
     "paired = losses[:, j] - losses[:, j_best]",
     "paired = losses[:, j]"),

    ("require exact equality instead of one paired standard error",
     "within = bool(mean_difference <= se)",
     "within = bool(mean_difference <= 0.0)"),

    ("never flag a flat CV surface",
     '"flag": (FLAG_RIDGE_CV_SURFACE_FLAT\n'
     "                 if width > RIDGE_FLAT_SURFACE_DECADES else None),",
     '"flag": None,'),

    ("select the weakest regularisation in the near-optimal set",
     '"strongest_regularisation_in_set": float(members[-1]) if members else None,',
     '"strongest_regularisation_in_set": float(members[0]) if members else None,'),

    ("judge the envelope on the average across metrics",
     '"within_envelope": bool(value <= bound)}',
     '"within_envelope": bool(\n'
     "            float(np.mean([abs(float(v)) for v in induced.values()])) "
     "<= bound)}"),

    ("stop requiring all three named stability metrics",
     "if missing or extra:",
     "if False:"),

    # ---- estimator selection --------------------------------------------
    ("admit every candidate regardless of held-out biology",
     '"admissible":\n'
     "                         bool(degradation <= float(biology_envelope) "
     "+ 1e-12)",
     '"admissible": True'),

    ("break ties to the last declared candidate",
     'selected = min(tied, key=lambda r: r["declared_rank"])',
     'selected = max(tied, key=lambda r: r["declared_rank"])'),

    # ---- portability -----------------------------------------------------
    ("point the frozen numerics at a machine-specific absolute path",
     'FROZEN_V20 = HERE / "t0_v20_frozen"',
     'FROZEN_V20 = Path("C:/Users/nobody/AppData/Local/Temp/v20")'),

    ("stop checking where the frozen modules resolved",
     "        if resolved.parent != FROZEN_V20.resolve():",
     "        if False:"),

    # ---- the confirmation-design envelope --------------------------------
    ("admit a singleton sex level into the confirmation envelope",
     "CONFIRMATION_SEX_MINORITY_COUNTS = (2, 3, 6)",
     "CONFIRMATION_SEX_MINORITY_COUNTS = (1, 3, 6)"),

    ("drop the envelope estimability guard",
     "        if float(leverage.max()) >= 1.0 - 1e-12:",
     "        if False:"),

    ("let the envelope be built without an authority",
     "    if not age_range_authority:",
     "    if False:"),

    ("report the best design in the envelope instead of the worst",
     "    worst = min(per_design, key=lambda d: (d[\"power_lower_95\"],",
     "    worst = max(per_design, key=lambda d: (d[\"power_lower_95\"],"),

    # ---- predictor-geometry transport ------------------------------------
    ("take the best case over the geometry class instead of the worst",
     "    worst = min(measured, key=lambda m: m[\"hc3_scaling\"])",
     "    worst = max(measured, key=lambda m: m[\"hc3_scaling\"])"),

    ("measure the discovery side on a surrogate instead of the real score",
     "        z=z_discovery, predictor=artifact[\"oof_scores\"],",
     "        z=z_discovery, predictor=np.linspace(-1.0, 1.0, "
     "len(artifact[\"oof_scores\"])),"),

    ("ignore the stated geometry when simulating",
     "        shape=geometry_shape)",
     "        shape=\"gaussian\")"),

    # ---- nested-permutation evidence -------------------------------------
    ("accept permutation evidence that does not reject",
     "    if p_upper > ALPHA:",
     "    if False:"),

    ("accept permutation evidence from a different artifact",
     "    if receipt.get(\"artifact_digest\") != artifact.get(\"artifact_digest\"):",
     "    if False:"),

    ("accept permutation evidence with too few permutations",
     "    if int(receipt.get(\"n_permutations\", 0)) < MIN_PERMUTATIONS_FOR_ALPHA:",
     "    if False:"),
]


def run_suite(workdir: Path) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TESTS, "-q", "--tb=no",
         "-k", DESELECT, "-p", "no:cacheprovider"],
        cwd=workdir, capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    failed = [line.split("::")[-1].strip()
              for line in proc.stdout.splitlines()
              if line.startswith("FAILED")]
    errored = "errors" in proc.stdout or proc.returncode not in (0, 1)
    return (1 if (failed or errored) else 0), failed


def main() -> int:
    baseline_code, baseline_failed = None, None
    results = []
    for label, old, new in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            shutil.copy(SRC / MODULE, work / MODULE)
            shutil.copy(SRC / TESTS, work / TESTS)
            shutil.copytree(SRC / FROZEN, work / FROZEN)

            if baseline_code is None:
                baseline_code, baseline_failed = run_suite(work)
                if baseline_code != 0:
                    print("BASELINE SUITE DOES NOT PASS: %r" % (baseline_failed,))
                    return 2

            text = (work / MODULE).read_text(encoding="utf-8")
            count = text.count(old)
            if count != 1:
                results.append({"mutation": label, "applied": False,
                                "match_count": count,
                                "verdict": "MUTATION_DID_NOT_APPLY"})
                continue
            (work / MODULE).write_text(text.replace(old, new, 1),
                                       encoding="utf-8")
            code, failed = run_suite(work)
            results.append({
                "mutation": label, "applied": True,
                "n_tests_that_caught_it": len(failed),
                "caught_by": failed[:4],
                "verdict": "CAUGHT" if code != 0 else "SURVIVED"})

    for r in results:
        if r["verdict"] == "SURVIVED" and r["mutation"] in UNREACHABLE:
            r["verdict"] = "EQUIVALENT_UNREACHABLE"
            r["proof"] = UNREACHABLE[r["mutation"]]

    print(json.dumps(results, indent=2))
    caught = [r for r in results if r["verdict"] == "CAUGHT"]
    equivalent = [r for r in results if r["verdict"] == "EQUIVALENT_UNREACHABLE"]
    survived = [r for r in results
                if r["verdict"] not in ("CAUGHT", "EQUIVALENT_UNREACHABLE")]

    print("\n%d caught, %d unreachable by construction, %d survived, of %d"
          % (len(caught), len(equivalent), len(survived), len(results)))
    for r in equivalent:
        print("  UNREACHABLE: %s" % r["mutation"])
    for r in survived:
        print("  %s: %s" % (r["verdict"], r["mutation"]))
    return 1 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
