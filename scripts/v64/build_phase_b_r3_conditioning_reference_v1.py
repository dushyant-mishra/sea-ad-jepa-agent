#!/usr/bin/env python3
"""Materialise the R3 conditioning identity as substrate DATA, not as prose.

S60. Statistical contract V3 says the realised large-arm draw is "recorded per pair
alongside the reference". The substrate schema described ENUMERATION_ONLY rows only as
edge_index x drawn_side x hg19_start, which does not say WHICH arm was large, WHAT its
realised draw was, or that the resulting reference is conditional. Stage 4 would then have
had to reconstruct the conditioning identity -- after outcomes exist. Reconstructing a
reference distribution once the answer is visible is precisely what the substrate freeze
is for, so the conditioning identity becomes frozen data here.

Everything emitted is structural: it comes from the Phase-A artifact and the committed
admissible sets. No matrix value is read and no biological quantity is computed.

The realised large-arm draw is NOT re-drawn. It is read from the frozen Phase-A row, so
the conditioning record cannot drift from the population it conditions on.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import nihcard_stage3_phase_a_exact_executor_v2 as EX            # noqa: E402

OUT = "results/v64/phase_b_design"
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
NULL_V3 = os.path.join(OUT, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
RULE_ID = "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"
LABEL = "CONDITIONAL_ON_REALISED_LARGE_ARM"
W = B.W


class Stop(Exception):
    pass


def main() -> int:
    V3 = json.load(open(NULL_V3))
    sec = V3["SECTION_10_ENUMERATION_REFERENCE_RULES"]
    if RULE_ID not in sec:
        raise Stop(f"{RULE_ID} absent from the statistical contract")
    r3spec = sec[RULE_ID]
    if r3spec["MANDATORY_CAVEAT_ON_UNCERTAINTY"]["required_label"] != LABEL:
        raise Stop("required label disagrees with the statistical contract")

    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    by = defaultdict(dict)
    for r in rows:
        by[r["edge_index"]]["L" if r["population"] == "LINKED"
                            else r["control_role"]] = r
    A = EX.load_A_exact()

    def members(e, s):
        iv, sup = A[e][s]
        o = []
        for a, b in iv:
            o.extend(range(a, b + 1))
        o.extend(sup)
        return sorted(o)

    recs = []
    for e in sorted(by):
        v = by[e]
        if "B" not in v:
            continue
        na, nb = v["A"]["admissible_start_count"], v["B"]["admissible_start_count"]
        sa, sb = v["A"]["drawn_side"], v["B"]["drawn_side"]
        if na == 1 or nb == 1:
            continue
        if not (na <= 10 or nb <= 10) or (na <= 10 and nb <= 10):
            continue
        small, large = ("A", "B") if na <= 10 else ("B", "A")
        sm, lg = v[small], v[large]
        alt = members(e, sm["drawn_side"])
        if len(alt) != sm["admissible_start_count"]:
            raise Stop(f"e{e}: enumerated {len(alt)} alternatives but the Phase-A row "
                       f"records support {sm['admissible_start_count']}")
        if sm["hg19_start"] not in alt:
            raise Stop(f"e{e}: the realised small-arm draw is not in its own admissible set")
        recs.append({
          "reference_id": f"R3:e{e}",
          "edge_index": e,
          "reference_rule_id": RULE_ID,
          "small_arm_role": small,
          "small_arm_drawn_side": sm["drawn_side"],
          "small_arm_admissible_support": sm["admissible_start_count"],
          "small_arm_realised_hg19_start": sm["hg19_start"],
          "small_arm_enumerated_alternatives_hg19_start": alt,
          "large_arm_role": large,
          "realised_large_arm_drawn_side": lg["drawn_side"],
          "realised_large_arm_hg19_start": lg["hg19_start"],
          "realised_large_arm_hg19_end": lg["hg19_end"],
          "realised_large_arm_hg38_start": lg["hg38_start"],
          "realised_large_arm_hg38_end": lg["hg38_end"],
          "large_arm_admissible_support": lg["admissible_start_count"],
          "arms_on_same_side": sm["drawn_side"] == lg["drawn_side"],
          "required_label": LABEL,
          "promoter_key": v["L"]["promoter_key"],
          "distal_chrom": v["L"]["distal_chrom"]})

    if not recs:
        raise Stop("no R3 pairs found; the rule would be vacuous")
    n_a = sum(1 for r in recs if r["small_arm_role"] == "A")
    same = sum(1 for r in recs if r["arms_on_same_side"])
    declared = r3spec["pairs"]
    if len(recs) != declared:
        raise Stop(f"materialised {len(recs)} records but V3 declares {declared} pairs")
    w = r3spec["which_arm_is_small"]
    if n_a != w["CONTROL_A_is_the_small_arm"] or (len(recs) - n_a) != w[
            "CONTROL_B_is_the_small_arm"]:
        raise Stop("small-arm split disagrees with the statistical contract")
    g = r3spec["arm_geometry_measured"]
    if same != g["pairs_drawing_on_the_SAME_side"]:
        raise Stop("same-side count disagrees with the statistical contract")
    ids = [r["reference_id"] for r in recs]
    if len(ids) != len(set(ids)):
        raise Stop("reference_id is not unique")

    art = {
      "schema": "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1", "date": "2026-09-30",
      "closes": "S60",
      "what_this_is": "the frozen conditioning identity for every pair governed by the R3 "
                      "conditional reference, so Stage 4 reads it rather than "
                      "reconstructing it after outcomes exist",
      "authority": {"path": NULL_V3, "sha256": B.sha_file(NULL_V3),
                    "section": "SECTION_10_ENUMERATION_REFERENCE_RULES",
                    "rule_id": RULE_ID,
                    "rule_semantic_sha256": B.sha_bytes(
                        json.dumps(r3spec, sort_keys=True,
                                   separators=(",", ":")).encode())},
      "binding_rule": "every R3 ENUMERATION_ONLY substrate row carries reference_id and "
                      "must resolve to exactly one record here",
      "large_arm_is_not_redrawn": "the realised large-arm draw is READ from the frozen "
                                  "Phase-A row, never re-sampled, so this record cannot "
                                  "drift from the population it conditions on",
      "counts": {"r3_pairs": len(recs),
                 "small_arm_is_CONTROL_A": n_a,
                 "small_arm_is_CONTROL_B": len(recs) - n_a,
                 "arms_on_same_side": same,
                 "arms_on_different_sides": len(recs) - same,
                 "total_enumerated_small_arm_alternatives": sum(
                     len(r["small_arm_enumerated_alternatives_hg19_start"])
                     for r in recs)},
      "required_label_on_every_derived_quantity": LABEL,
      "records": recs,
      "governance": V3["governance"],
      "producer": {"path": os.path.relpath(os.path.abspath(__file__), os.getcwd()),
                   "sha256": B.sha_file(os.path.abspath(__file__))}}

    p = os.path.join(OUT, "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(art, fh, indent=2)
    print(json.dumps(art["counts"], indent=2))
    print(f"\nreference artifact {p}\n  sha256 {B.sha_file(p)}")
    print(f"  rule semantic sha256 {art['authority']['rule_semantic_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
