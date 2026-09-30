#!/usr/bin/env python3
"""Deterministic tests for the Phase-B downstream null / statistical contract.

Every test carries a NEGATIVE CONTROL: a deliberately violating input that the same
assertion must reject. A test that passes on the real artifact but would also pass on a
violating one proves nothing, and this project has been bitten by exactly that before.
Each result therefore reports `is_a_real_test`, which is true only when the check passes
on the real contract AND fails on the planted violation.

TRAINING=OFF. PHASE B=STOPPED. No matrix values are read.
"""
from __future__ import annotations

import copy
import gzip
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
CONTRACT = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V1.json")
STATE = os.path.join(DIR, "V64_PHASE_B_DECISION_STATE_V1.json")
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"

RESULTS = []


def check(name, requirement, fn, real, violating):
    ok_real, why_real = fn(real)
    ok_bad, _ = fn(violating)
    rec = dict(name=name, requirement=requirement,
               passes_on_real_contract=ok_real,
               rejects_planted_violation=not ok_bad,
               is_a_real_test=bool(ok_real and not ok_bad),
               detail=why_real)
    RESULTS.append(rec)
    print(f"  {name:<46} real={ok_real!s:<5} rejects_violation={not ok_bad!s:<5} "
          f"real_test={rec['is_a_real_test']}")
    return rec


def main() -> int:
    C = json.load(open(CONTRACT))
    S = json.load(open(STATE))
    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]

    # ---- T1 singleton coincidences excluded from calibration evidence
    def t1(c):
        sec = c["SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION"]
        ex = sec["EXCLUDED_FROM_CALIBRATION_EVIDENCE"]
        forced = ex.get("STRUCTURALLY_FORCED_IDENTICAL", {})
        if forced.get("contributes") != "ZERO evidence":
            return False, "forced coincidences not declared zero-evidence"
        if "STRUCTURALLY_FORCED_IDENTICAL" in sec["eligible_classes"]:
            return False, "forced class is inside the eligible denominator"
        cls = sec["class_counts"]
        expect = cls["FULLY_RANDOMIZED_SUPPORT_GT10"] + cls["FULLY_RANDOMIZED_SMALL_SUPPORT"]
        if sec["eligible_denominator_frozen_now"] != expect:
            return False, "denominator does not equal the fully randomized classes"
        return True, (f"denominator {expect:,} excludes "
                      f"{cls['STRUCTURALLY_FORCED_IDENTICAL']} forced and "
                      f"{cls['PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM']} partially forced")
    bad = copy.deepcopy(C)
    sec = bad["SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION"]
    sec["eligible_classes"].append("STRUCTURALLY_FORCED_IDENTICAL")
    sec["eligible_denominator_frozen_now"] += sec["class_counts"]["STRUCTURALLY_FORCED_IDENTICAL"]
    check("T1_singleton_coincidences_excluded",
          "the 158 structurally forced coincidences contribute zero calibration evidence",
          t1, C, bad)

    # ---- T2 CONTROL_B cannot alter primary retention
    def t2(c):
        if "NULL AND CALIBRATION ONLY" not in c[
                "SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION"]["control_B_role"]:
            return False, "CONTROL_B role not restricted"
        fa = c["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]
        n = fa["retained_edges"]
        if c["SECTION_1_PRIMARY_LINKED_VS_CONTROL_A"]["n"] != n:
            return False, "primary n differs from retained edges"
        # the decisive arithmetic: B succeeded on 2,200 edges where A failed, and the
        # retained population is unchanged by them
        if fa["null_arm_availability"]["A_failed_B_succeeded_not_rescued"] <= 0:
            return False, "no evidence the non-rescue rule was exercised"
        if n + fa["null_arm_availability"]["A_failed_B_succeeded_not_rescued"] == n:
            return False, "degenerate"
        return True, (f"{fa['null_arm_availability']['A_failed_B_succeeded_not_rescued']:,} "
                      f"edges had a valid CONTROL_B and were still not retained")
    bad = copy.deepcopy(C)
    bad["SECTION_1_PRIMARY_LINKED_VS_CONTROL_A"]["n"] = (
        C["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["retained_edges"]
        + C["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["null_arm_availability"][
            "A_failed_B_succeeded_not_rescued"])
    check("T2_control_B_cannot_alter_retention",
          "CONTROL_B is a null arm only and never changes the primary population",
          t2, C, bad)

    # ---- T3 missingness is not zero-filled
    def t3(c):
        m = c["SECTION_5_MISSINGNESS"]
        if m.get("required_rule") != "NOT_MEASURED != 0":
            return False, "the NOT_MEASURED != 0 rule is absent"
        if m.get("zero_fill") != "FORBIDDEN for RNA, ATAC and regulatory evidence alike":
            return False, "zero-fill not forbidden"
        need = {"MEASURED_AND_SUPPORTS", "MEASURED_AND_DOES_NOT_SUPPORT",
                "NOT_MEASURED", "UNRESOLVED"}
        if set(m.get("states", [])) != need:
            return False, f"states are {m.get('states')}"
        for f in ("promoter_activity", "distal_accessibility"):
            if "never 0" not in c["SECTION_8_PHASE_B_FIELD_SEMANTICS"][f]["missingness"]:
                return False, f"{f} missingness does not forbid 0"
        return True, "four states, zero-fill forbidden, both Phase-B fields covered"
    bad = copy.deepcopy(C)
    bad["SECTION_5_MISSINGNESS"]["zero_fill"] = "allowed when convenient"
    check("T3_missingness_not_zero_filled",
          "NOT_MEASURED is never encoded as zero, in four explicit states",
          t3, C, bad)

    # ---- T4 all three randomness strata represented, and matching the artifact
    def t4(c):
        st = c["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["control_A_support_strata"]
        need = {"RANDOMIZED_SUPPORT_GT10", "SMALL_RANDOMIZED_SUPPORT_2_TO_10",
                "FORCED_SINGLETON_SUPPORT_1"}
        if set(st) != need:
            return False, f"strata are {set(st)}"
        if sum(st.values()) != c["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["retained_edges"]:
            return False, "strata do not sum to the retained population"
        # recompute independently from the artifact rather than trusting the contract
        by = defaultdict(dict)
        for r in rows:
            if r["population"] == "CONTROL":
                by[r["edge_index"]][r["control_role"]] = r
        live = Counter()
        for e, v in by.items():
            n = v["A"]["admissible_start_count"]
            live["FORCED_SINGLETON_SUPPORT_1" if n == 1 else
                 "SMALL_RANDOMIZED_SUPPORT_2_TO_10" if n <= 10 else
                 "RANDOMIZED_SUPPORT_GT10"] += 1
        if dict(live) != st:
            return False, f"contract strata {st} != artifact {dict(live)}"
        # every stratum must have an explicit per-stratum uncertainty rule
        per = c["SECTION_3_UNCERTAINTY_REPORTING"]["per_stratum_rules"]
        for k in ("control_A_support_1", "control_A_support_2_to_10",
                  "control_B_unavailable", "A_B_coincide_by_chance",
                  "A_B_coincide_structurally"):
            if k not in per:
                return False, f"no uncertainty rule for {k}"
        return True, f"{st} verified against the artifact, all with uncertainty rules"
    bad = copy.deepcopy(C)
    bad["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["control_A_support_strata"].pop(
        "SMALL_RANDOMIZED_SUPPORT_2_TO_10")
    check("T4_all_three_strata_represented",
          "every randomness stratum is present, sums to the population, and has a rule",
          t4, C, bad)

    # ---- T5 Phase B remains stopped
    def t5(c):
        g = c["governance"]
        want = dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                    td60="BLOCKED", Morabito="PROTECTED")
        for k, v in want.items():
            if g.get(k) != v:
                return False, f"{k} is {g.get(k)}, expected {v}"
        if g.get("correspondence_opened") is not False:
            return False, "correspondence flag is not False"
        if c["SECTION_9_FIREWALL_OBSERVED_IN_BUILDING_THIS_CONTRACT"][
                "rna_matrix_values_read"] is not False:
            return False, "contract admits reading RNA matrix values"
        return True, "all governance locks in force, no matrix values read"
    bad = copy.deepcopy(C)
    bad["governance"]["phase_B"] = "RUNNING"
    check("T5_phase_B_remains_stopped",
          "governance locks are in force and no matrix value was read",
          t5, C, bad)

    # ---- T6 no biological outcome FIELDS present anywhere
    # This is a structural check over keys and leaf values, not a substring scan over
    # prose. A prose scan is the wrong test: the contract MUST name the things it
    # forbids -- its firewall section lists "rna-atac correlation" precisely to declare
    # it was not inspected -- so a word-level scan flags the prohibition itself. What
    # the rule actually forbids is a FIELD carrying an outcome, i.e. a key whose name
    # denotes a statistic, or a numeric value sitting under such a key.
    # Terms must denote a RESULT, not the contrast. A section named for the
    # linked-versus-control comparison is a heading; "linked_vs_control_result" is an
    # outcome. An over-broad term flags the contract's own structure, which is why the
    # bare contrast name is not in this list.
    OUTCOME_KEY_TERMS = ["correlation", "effect_size", "effectsize", "p_value", "pvalue",
                         "q_value", "fdr", "residual_association",
                         "linked_vs_control_result", "linked_vs_control_estimate",
                         "linked_vs_control_statistic",
                         "braak", "cerad", "at8", "auc", "odds_ratio", "beta_hat",
                         "t_statistic", "z_statistic", "estimate", "coefficient",
                         "test_statistic", "significance"]

    def t6(c):
        hits = []

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    kl = str(k).lower()
                    for t in OUTCOME_KEY_TERMS:
                        if t in kl:
                            hits.append(dict(path=f"{path}/{k}", term=t,
                                             kind="outcome-named key"))
                            break
                    walk(v, f"{path}/{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                pl = path.lower()
                for t in OUTCOME_KEY_TERMS:
                    if t in pl:
                        hits.append(dict(path=path, term=t, kind="numeric outcome value"))
                        break

        walk(c)
        return (not hits), (f"no outcome-named keys and no numeric values under one; "
                            f"{len(OUTCOME_KEY_TERMS)} field terms scanned structurally"
                            if not hits else f"found {hits[:2]}")
    bad = copy.deepcopy(C)
    bad["RESULT"] = {"linked_vs_control_result": 0.31, "p_value": 1e-9}
    check("T6_no_biological_outcome_fields",
          "the contract contains no correspondence result, effect size or outcome value",
          t6, C, bad)

    # ---- T7 primary view frozen and reconciliation holds
    def t7(c):
        v = c["SECTION_4_PREDECLARED_SENSITIVITY_VIEWS"]
        prim = [k for k in v if isinstance(v[k], dict) and v[k].get("is_primary")]
        if len(prim) != 1:
            return False, f"{len(prim)} primary views declared"
        sec = c["SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION"]["class_counts"]
        if sum(sec.values()) != c["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS"]["retained_edges"]:
            return False, "calibration classes do not reconcile to the population"
        return True, f"single primary view {prim[0]}, calibration classes reconcile"
    bad = copy.deepcopy(C)
    bad["SECTION_4_PREDECLARED_SENSITIVITY_VIEWS"][
        "V3_randomized_support_gt10_only"]["is_primary"] = True
    check("T7_single_frozen_primary_view",
          "exactly one primary view is declared and classes reconcile to the population",
          t7, C, bad)

    real = [r for r in RESULTS if r["is_a_real_test"]]
    out = dict(schema="V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_TESTS_V1", date="2026-09-30",
               contract=dict(path=CONTRACT, sha256=B.sha_file(CONTRACT)),
               state=dict(path=STATE, sha256=B.sha_file(STATE)),
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               tests=RESULTS, n_tests=len(RESULTS),
               n_real_tests=len(real),
               every_test_has_a_working_negative_control=len(real) == len(RESULTS),
               status="PASS" if len(real) == len(RESULTS) else "FAIL",
               note="a test is counted as real only if it passes on the actual contract "
                    "AND rejects a deliberately planted violation")
    p = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_TESTS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n{len(real)}/{len(RESULTS)} tests are real tests -> {out['status']}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
