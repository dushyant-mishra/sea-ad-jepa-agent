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
NULL_V3 = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
R3REF = os.path.join(DIR, "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json")
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
        n = json.load(open(NULL_V3))
        if c["governance"] != n["governance"]:
            return False, "governance diverges from the statistical contract"
        a = c["authority"]["statistical_contract"]
        if a["sha256"] != B.sha_file(NULL_V3):
            return False, "bound statistical contract digest is stale"
        return True, "statistically neutral and bound to the accepted V3 digest"
    bad = copy.deepcopy(C)
    bad["governance"] = dict(bad["governance"], phase_B="RUNNING")
    check("T16_no_statistical_decision_changed",
          "the substrate contract changes no statistical decision",
          t16, C, bad)

    # ---- T17 every substrate enumeration rule exists in the STATISTICAL contract
    def t17(c):
        ids = c["EXACT_ENUMERATION_REQUIREMENT"].get("rule_identifiers_implemented_here")
        if not ids:
            return False, "substrate declares no rule identifiers"
        auth = c["EXACT_ENUMERATION_REQUIREMENT"].get("AUTHORITY")
        if not auth or not auth.get("this_contract_only_implements_them"):
            return False, "substrate does not defer to an upstream authority"
        st = json.load(open(NULL_V3))
        sec = st.get("SECTION_10_ENUMERATION_REFERENCE_RULES")
        if not sec:
            return False, "statistical contract has no enumeration-rule section"
        missing = [i for i in ids if i not in sec]
        if missing:
            return False, f"rules implemented with no statistical authority: {missing}"
        if auth["sha256"] != B.sha_file(NULL_V3):
            return False, "bound authority digest is stale"
        if st.get("THIS_CONTRACT_MAKES_A_STATISTICAL_DECISION", {}).get(
                "declared") is not True:
            return False, "the statistical contract does not declare R3 as its decision"
        # SEMANTIC drift: a name bind cannot see eligibility or conditioning changing
        # under an unchanged identifier, so each rule's full definition is digested.
        sd = c["EXACT_ENUMERATION_REQUIREMENT"].get("RULE_SEMANTIC_DIGESTS")
        if not sd:
            return False, "no per-rule semantic digests recorded"
        for i in ids:
            live = B.sha_bytes(json.dumps(sec[i], sort_keys=True,
                                          separators=(",", ":")).encode())
            if sd["digests"].get(i) != live:
                return False, f"semantic drift under identifier {i}"
            declared = sec[i].get("edges") or sec[i].get("pairs")
            if sd["declared_counts_cross_checked"].get(i) != declared:
                return False, f"declared count drift under {i}"
        return True, (f"all {len(ids)} rules bound by NAME, by full-definition semantic "
                      f"digest and by declared count")
    bad = copy.deepcopy(C)
    bad["EXACT_ENUMERATION_REQUIREMENT"]["rule_identifiers_implemented_here"].append(
        "R4_SOME_RULE_INVENTED_DOWNSTREAM")
    check("T17_every_enumeration_rule_has_upstream_authority",
          "no inferential rule is introduced by the substrate contract (S58)",
          t17, C, bad)

    # ---- T18 the enumeration fraction denominator is recomputed, not hardcoded
    def t18(c):
        m = c["EXACT_ENUMERATION_REQUIREMENT"]["MATERIALISATION"]
        if not m.get("S57_denominator_is_recomputed_not_hardcoded"):
            return False, "denominator is not declared recomputed"
        n_ctl = m.get("control_rows_already_measured")
        live = sum(1 for r in rows if r["population"] == "CONTROL")
        if n_ctl != live:
            return False, f"claimed {n_ctl} control rows, artifact has {live}"
        want = round(m["additional_ENUMERATION_ONLY_rows"] / live, 6)
        if abs(m["as_fraction_of_controls_already_measured"] - want) > 1e-9:
            return False, "fraction does not equal extra/control_rows"
        return True, (f"denominator {live:,} recomputed from the artifact and the "
                      f"fraction follows from it")
    # planted violation: CONTROL_B availability changes, so a hardcoded denominator breaks
    bad = copy.deepcopy(C)
    bad["EXACT_ENUMERATION_REQUIREMENT"]["MATERIALISATION"][
        "control_rows_already_measured"] = 24187 - 1000
    check("T18_enumeration_denominator_recomputed",
          "the fraction denominator tracks the artifact and is not a literal (S57)",
          t18, C, bad)

    # ---- T19 R3 conditioning identity is persisted as DATA and independently recovers
    def t19(c):
        t7 = c["SUBSTRATE_TABLES"].get("T7_R3_CONDITIONING_REFERENCE")
        if not t7:
            return False, "no R3 conditioning table in the substrate schema"
        need = {"reference_id", "edge_index", "reference_rule_id", "small_arm_role",
                "small_arm_drawn_side", "large_arm_role",
                "realised_large_arm_drawn_side", "realised_large_arm_hg19_start",
                "realised_large_arm_hg19_end", "required_label"}
        missing = need - set(t7["required_fields"])
        if missing:
            return False, f"T7 lacks required fields: {sorted(missing)}"
        if t7.get("required_label_value") != "CONDITIONAL_ON_REALISED_LARGE_ARM":
            return False, "the mandatory conditional label is not fixed"
        if t7["materialised_artifact"]["sha256"] != B.sha_file(R3REF):
            return False, "the bound conditioning artifact digest is stale"
        # T6 rows under R3 must point at it
        t6 = c["SUBSTRATE_TABLES"]["T6_ENUMERATION_ONLY"]
        if "reference_id" not in t6.get("required_fields", []):
            return False, "ENUMERATION_ONLY rows carry no reference_id"
        if "resolve to exactly one" not in t6.get("reference_id_rule", ""):
            return False, "no row->reference binding rule"

        # independently recover every property from the Phase-A artifact
        R = json.load(open(R3REF))
        recs = {r["reference_id"]: r for r in R["records"]}
        A = EX.load_A_exact()

        def members(e, sd_):
            iv, sup = A[e][sd_]
            o = []
            for a, b in iv:
                o.extend(range(a, b + 1))
            o.extend(sup)
            return sorted(o)
        live = []
        for e, v in by.items():
            if "B" not in v:
                continue
            na, nb = v["A"]["admissible_start_count"], v["B"]["admissible_start_count"]
            if na == 1 or nb == 1:
                continue
            if not (na <= 10 or nb <= 10) or (na <= 10 and nb <= 10):
                continue
            live.append((e, "A" if na <= 10 else "B"))
        if len(live) != 21:
            return False, f"recovered {len(live)} R3 pairs, expected 21"
        n_a = sum(1 for _, sm in live if sm == "A")
        if (n_a, len(live) - n_a) != (11, 10):
            return False, f"small-arm split {(n_a, len(live)-n_a)}, expected (11, 10)"
        same = 0
        for e, sm in live:
            rid = f"R3:e{e}"
            if rid not in recs:
                return False, f"no conditioning record for {rid}"
            r = recs[rid]
            lg = "B" if sm == "A" else "A"
            if r["small_arm_role"] != sm or r["large_arm_role"] != lg:
                return False, f"{rid}: arm roles disagree with the artifact"
            # the realised large-arm draw must EQUAL the frozen Phase-A row
            pa = by[e][lg]
            if (r["realised_large_arm_hg19_start"] != pa["hg19_start"]
                    or r["realised_large_arm_hg19_end"] != pa["hg19_end"]
                    or r["realised_large_arm_drawn_side"] != pa["drawn_side"]):
                return False, f"{rid}: realised large arm differs from frozen Phase A"
            if r["required_label"] != "CONDITIONAL_ON_REALISED_LARGE_ARM":
                return False, f"{rid}: missing conditional label"
            alt = members(e, by[e][sm]["drawn_side"])
            if r["small_arm_enumerated_alternatives_hg19_start"] != alt:
                return False, f"{rid}: enumerated alternatives disagree"
            if by[e][sm]["hg19_start"] not in alt:
                return False, f"{rid}: realised small arm not in its own set"
            if r["arms_on_same_side"]:
                same += 1
        if same != 0:
            return False, f"{same} pairs recorded as same-side, expected 0"
        if len(recs) != 21:
            return False, f"{len(recs)} records, expected 21"
        return True, ("21 pairs, 11 A-small / 10 B-small, 0 same-side / 21 different-side, "
                      "every realised large-arm draw equal to frozen Phase A, every "
                      "label present, every row->reference binding resolvable")
    bad = copy.deepcopy(C)
    bad["SUBSTRATE_TABLES"]["T7_R3_CONDITIONING_REFERENCE"][
        "required_label_value"] = "UNCONDITIONAL"
    check("T19_R3_conditioning_identity_persisted",
          "the R3 conditioning identity is frozen data that independently recovers (S60)",
          t19, C, bad)

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
