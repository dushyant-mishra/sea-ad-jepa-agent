#!/usr/bin/env python3
"""Deterministic tests for the Phase-B measurement substrate contract.

Each test carries a planted violation that the same assertion must reject, so a test
that would pass regardless of content is reported as not a real test.

TRAINING=OFF. PHASE B=STOPPED. No matrix values are read.
"""
from __future__ import annotations

import copy
import gzip
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import nihcard_stage3_phase_a_exact_executor_v2 as EX            # noqa: E402

DIR = "results/v64/phase_b_design"
SUB = os.path.join(DIR, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json")
NULL_V2 = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V2.json")
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
RESULTS = []


def check(name, requirement, fn, real, bad):
    ok, why = fn(real)
    okb, _ = fn(bad)
    r = dict(name=name, requirement=requirement, passes_on_real_contract=ok,
             rejects_planted_violation=not okb,
             is_a_real_test=bool(ok and not okb), detail=why)
    RESULTS.append(r)
    print(f"  {name:<48} real={ok!s:<5} rejects={not okb!s:<5} "
          f"real_test={r['is_a_real_test']}")


def main() -> int:
    C = json.load(open(SUB))

    # ---- T11 metacell-level vectors persisted, not only donor means
    def t11(c):
        t = c["SUBSTRATE_TABLES"]
        for need in ("T1_METACELL_ASSIGNMENT", "T2_METACELL_DEPTH", "T3_RNA_VECTORS",
                     "T4_ATAC_VECTORS", "T5_PAIR_DONOR_AGGREGATES"):
            if need not in t:
                return False, f"{need} missing"
        if "metacell_id" not in t["T3_RNA_VECTORS"]["key"]:
            return False, "RNA vectors are not metacell-level"
        if "metacell_id" not in t["T4_ATAC_VECTORS"]["key"]:
            return False, "ATAC vectors are not metacell-level"
        if "total_rna_counts_all_genes" not in t["T2_METACELL_DEPTH"]["fields"]:
            return False, "per-metacell RNA depth absent, depth sensitivity unrecoverable"
        if "total_atac_counts_all_peaks" not in t["T2_METACELL_DEPTH"]["fields"]:
            return False, "per-metacell ATAC depth absent"
        return True, ("metacell-level RNA and ATAC vectors plus per-metacell depth are "
                      "all persisted, so Stage 4 need not reopen the matrices")
    bad = copy.deepcopy(C)
    bad["SUBSTRATE_TABLES"]["T3_RNA_VECTORS"]["key"] = "donor_id x gene_id"
    check("T11_metacell_level_vectors_persisted",
          "the substrate carries metacell-level vectors, not only donor means",
          t11, C, bad)

    # ---- T12 Phase B never computes a two-modality statistic
    def t12(c):
        ln = c["THE_LINE_PHASE_B_MAY_NOT_CROSS"]
        may, mayn = ln["phase_B_MAY_compute"], ln["phase_B_MAY_NOT_compute"]
        if not any("correlation" in x.lower() for x in mayn):
            return False, "correlation is not explicitly forbidden to Phase B"
        for x in may:
            xl = x.lower()
            if "rna" in xl and "atac" in xl and "slope" not in xl and "depth" not in xl:
                return False, f"a permitted item couples both modalities: {x}"
        if "two-modality" not in json.dumps(c["STOP_CONDITIONS"]).lower():
            return False, "no stop condition on computing a two-modality statistic"
        return True, "single-modality and depth terms permitted; correlation reserved"
    bad = copy.deepcopy(C)
    bad["THE_LINE_PHASE_B_MAY_NOT_CROSS"]["phase_B_MAY_compute"].append(
        "per-donor Pearson correlation between the RNA and ATAC metacell vectors")
    check("T12_phase_B_computes_no_two_modality_statistic",
          "Phase B may look at one modality at a time but never couples them",
          t12, C, bad)

    # ---- T13 enumeration rows change nothing about the population
    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    by = defaultdict(dict)
    for r in rows:
        by[r["edge_index"]]["L" if r["population"] == "LINKED"
                            else r["control_role"]] = r

    def t13(c):
        t = c["SUBSTRATE_TABLES"]["T6_ENUMERATION_ONLY"]
        if t.get("label") != "ENUMERATION_ONLY":
            return False, "rows are not labelled ENUMERATION_ONLY"
        sem = " ".join(t["semantics"]).lower()
        for must in ("not change retention", "not increase n",
                     "not enter the primary population"):
            if must not in sem:
                return False, f"semantics do not state they do {must}"
        e = c["EXACT_ENUMERATION_REQUIREMENT"]["MATERIALISATION"]
        # the enumeration must not alter the retained population
        if c["SUBSTRATE_SCALE_MEASURED"]["pair_rows"] != len(rows):
            return False, "pair row count differs from the Phase-A artifact"
        # recompute the requirement independently
        A = EX.load_A_exact()

        def members(ei, s):
            iv, sup = A[ei][s]
            o = []
            for a, b in iv:
                o.extend(range(a, b + 1))
            o.extend(sup)
            return o
        need = set()
        for ei, v in by.items():
            na, sa = v["A"]["admissible_start_count"], v["A"]["drawn_side"]
            if 2 <= na <= 10:
                need.update((ei, sa, x) for x in members(ei, sa))
            if "B" not in v:
                continue
            nb, sb = v["B"]["admissible_start_count"], v["B"]["drawn_side"]
            if na == 1 or nb == 1 or not (na <= 10 or nb <= 10):
                continue
            if na <= 10 and nb <= 10:
                for side in {sa, sb}:
                    need.update((ei, side, x) for x in members(ei, side))
            else:
                ss = sa if na <= 10 else sb
                need.update((ei, ss, x) for x in members(ei, ss))
        already = {(ei, v[k]["drawn_side"], v[k]["hg19_start"])
                   for ei, v in by.items() for k in ("A", "B") if k in v}
        if e["additional_ENUMERATION_ONLY_rows"] != len(need - already):
            return False, (f"claimed {e['additional_ENUMERATION_ONLY_rows']} extra rows, "
                           f"recomputed {len(need - already)}")
        return True, (f"{e['additional_ENUMERATION_ONLY_rows']} extra rows recomputed "
                      f"independently; retention and N unchanged")
    bad = copy.deepcopy(C)
    bad["EXACT_ENUMERATION_REQUIREMENT"]["MATERIALISATION"][
        "additional_ENUMERATION_ONLY_rows"] = 999
    check("T13_enumeration_rows_change_no_population",
          "ENUMERATION_ONLY rows do not alter retention, N or the primary population",
          t13, C, bad)

    # ---- T14 the recoverability firewall does not remove donors from Phase B
    def t14(c):
        f = c["RECOVERABILITY_TEST_DONOR_FIREWALL_SCOPE"]
        if "withdrawn" not in f["CORRECTION"].lower():
            return False, "the conflated wording is not withdrawn"
        w = f["what_governs_Phase_B"]
        if "does not remove donors" not in w["statement"].lower():
            return False, "Phase-B population is not explicitly protected from the split"
        if w["population"] != "the full NIH-CARD correspondence cohort":
            return False, f"Phase-B population is {w['population']}"
        if "EXPLICIT prospective amendment" not in f["if_global_sequestration_is_wanted"]:
            return False, "global sequestration is not gated behind an amendment"
        r = f["what_the_split_actually_governs"]["restriction"].lower()
        if "recoverability" not in r:
            return False, "the restriction is not scoped to recoverability"
        return True, ("split scoped to recoverability selection only; Phase B keeps its "
                      "own donor-population authority")
    bad = copy.deepcopy(C)
    bad["RECOVERABILITY_TEST_DONOR_FIREWALL_SCOPE"]["what_governs_Phase_B"][
        "population"] = "the full cohort minus the 4 recoverability TEST donors"
    check("T14_recoverability_firewall_precisely_scoped",
          "the recoverability split does not silently shrink the Phase-B population",
          t14, C, bad)

    # ---- T15 no protected obs column was read
    PROT = {"Age", "Sex", "Ancestry", "Ethnicity", "Race", "PMI", "Brain_bank"}

    def t15(c):
        d = c["DONOR_POPULATION_MEASURED_FROM_LAWFUL_METADATA"]
        read = set(d["obs_columns_read"])
        if read & PROT:
            return False, f"protected columns read: {sorted(read & PROT)}"
        if read != {"SampleID", "cell_type"}:
            return False, f"unexpected columns read: {sorted(read)}"
        notread = set(d["obs_columns_deliberately_not_read"])
        if not PROT <= notread:
            return False, f"protected columns not declared excluded: {sorted(PROT-notread)}"
        if "any protected obs column is read" not in c["STOP_CONDITIONS"]:
            return False, "no stop condition on protected column access"
        return True, (f"only {sorted(read)} read; all {len(PROT)} protected demographic "
                      f"columns declared excluded")
    bad = copy.deepcopy(C)
    bad["DONOR_POPULATION_MEASURED_FROM_LAWFUL_METADATA"]["obs_columns_read"].append("Age")
    check("T15_no_protected_obs_column_read",
          "only donor identity and cell type were read; demographics were not",
          t15, C, bad)

    # ---- T16 statistical decisions unchanged by this contract
    def t16(c):
        if c.get("changes_no_statistical_decision") is not True:
            return False, "contract does not declare itself statistically neutral"
        n = json.load(open(NULL_V2))
        if c["governance"] != n["governance"]:
            return False, "governance diverges from the statistical contract"
        a = c["authority"]["statistical_contract"]
        if a["sha256"] != B.sha_file(NULL_V2):
            return False, "bound statistical contract digest is stale"
        return True, "statistically neutral and bound to the accepted V2 digest"
    bad = copy.deepcopy(C)
    bad["governance"] = dict(bad["governance"], phase_B="RUNNING")
    check("T16_no_statistical_decision_changed",
          "the substrate contract changes no statistical decision",
          t16, C, bad)

    real = [r for r in RESULTS if r["is_a_real_test"]]
    out = dict(schema="V64_PHASE_B_MEASUREMENT_SUBSTRATE_TESTS_V1", date="2026-09-30",
               contract=dict(path=SUB, sha256=B.sha_file(SUB)),
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               tests=RESULTS, n_tests=len(RESULTS), n_real_tests=len(real),
               status="PASS" if len(real) == len(RESULTS) else "FAIL")
    p = os.path.join(DIR, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_TESTS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n{len(real)}/{len(RESULTS)} real tests -> {out['status']}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
