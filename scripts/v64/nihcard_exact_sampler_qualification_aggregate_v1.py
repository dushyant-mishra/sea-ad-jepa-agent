#!/usr/bin/env python3
"""Aggregate the sharded real-edge qualification into one auditable verdict.

Establishes, simultaneously and from the shard receipts alone:

   1  exactly 64 unique PREDECLARED comparison IDs
   2  no duplicate and no missing IDs
   3  64 completed
   4  exact SET equality, not cardinality equality
   5  zero algebra_only
   6  zero oracle_only
   7  explicit non_empty count
   8  explicit 0-vs-0 count
   9  total candidate starts actually challenged
  10  number of comparisons involving the supplement path
  11  run-1 versus run-2 deterministic equality
  12  positive-control sensitivity retained
  13  aggregate receipt hash bound to all four shard receipts

WHY THE IDS ARE PREDECLARED HERE RATHER THAN READ OFF THE RECEIPTS. If the expected set
were derived from what the shards produced, a shard that silently skipped an edge-side
would shrink both the expectation and the result together and the check would pass. So
the 64 IDs are regenerated independently from seed 20260929 and the frozen E2 table, and
the receipts are then required to cover exactly that set.

WHY ZERO algebra_only AND ZERO oracle_only FOLLOW RIGOROUSLY. Each comparison stores
exact_set_equality computed as (sorted A_exact == sorted oracle) over integer starts.
When that is True the symmetric difference is empty by definition, so both directional
counts are exactly zero -- the stored only_in_* samples are capped at 10 elements, but
that cap can only matter for a comparison that already failed, and a single failure
stops the suite.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

QUAL = "D:/jepa_v5_outputs_20260925/v64_qual"
RUN1 = "D:/jepa_v5_outputs_20260925/v64_qual_run1_logs"
SEED = 20260929
N_EDGES = 32
N_SHARDS = 4

LINE = re.compile(r"e(\d+)\|([+-]\d+) band=\s*([\d,]+) A=\s*([\d,]+) "
                  r"oracle=\s*([\d,]+) eq=(True|False)")


def predeclared_ids():
    """The 64 comparison IDs, regenerated independently of any shard output."""
    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise SystemExit("STOP: E2 digest mismatch while predeclaring IDs")
    n_rows = len(raw.decode().rstrip("\n").split("\n")) - 1
    rng = np.random.default_rng(SEED)
    sel = sorted(int(x) for x in rng.choice(n_rows, N_EDGES, replace=False))
    return [f"e{i}|{s:+d}" for i in sel for s in (1, -1)], sel, n_rows


def parse_log(path):
    out = {}
    if not os.path.exists(path):
        return out
    for l in open(path):
        m = LINE.search(l)
        if m:
            out[f"e{m.group(1)}|{int(m.group(2)):+d}"] = (
                int(m.group(3).replace(",", "")), int(m.group(4).replace(",", "")),
                int(m.group(5).replace(",", "")), m.group(6) == "True")
    return out


def main() -> int:
    ids, sel_edges, n_rows = predeclared_ids()
    expected = set(ids)

    shard_files, recs, shard_hashes = [], [], {}
    for s in range(N_SHARDS):
        p = os.path.join(QUAL, f"edges_s{s:02d}.receipt.json")
        if not os.path.exists(p):
            raise SystemExit(f"STOP: missing shard receipt {p}")
        shard_files.append(p)
        shard_hashes[os.path.basename(p)] = B.sha_file(p)
        recs.append(json.load(open(p)))

    # ---- inputs agreed across shards
    inp = {k: {r.get(k) for r in recs}
           for k in ("producer_sha256", "sampler_sha256", "builder_sha256",
                     "liftover_sha256", "nih_peaks_sha256", "pu1_sha256",
                     "minmatch", "window_bp", "seed", "n_shards")}
    inputs_consistent = all(len(v) == 1 for v in inp.values())

    # ---- 1,2,3 identity coverage
    produced = []
    for r in recs:
        for c in r["edge_side_checks"]:
            produced.append(f"e{c['edge_index']}|{c['side']:+d}")
    cnt = Counter(produced)
    dupes = {k: v for k, v in cnt.items() if v > 1}
    missing = sorted(expected - set(produced))
    unexpected = sorted(set(produced) - expected)

    # ---- 4,5,6,7,8,9,10 comparison evidence
    all_checks = [c for r in recs for c in r["edge_side_checks"]]
    eq_all = all(c["exact_set_equality"] for c in all_checks)
    alg_only = sum(len(c.get("only_in_A", [])) for c in all_checks)
    orc_only = sum(len(c.get("only_in_oracle", [])) for c in all_checks)
    non_empty = [c for c in all_checks if c.get("non_empty")]
    zero_zero = [c for c in all_checks
                 if c.get("A_exact_card", 0) == 0 and c.get("oracle_card", 0) == 0]
    supp_ran = [c for c in all_checks if c.get("supplement_candidates", 0) > 0]
    supp_contrib = [c for c in all_checks if c.get("A_supplement_card", 0) > 0]
    challenged = sum(c.get("band_positions", 0) for c in all_checks)
    supp_challenged = sum(c.get("supplement_candidates", 0) for c in all_checks)

    # ---- 11 determinism, run 1 versus run 2
    r1, r2 = {}, {}
    for s in range(N_SHARDS):
        r1.update(parse_log(os.path.join(RUN1, f"edges_s{s:02d}.log")))
        r2.update(parse_log(os.path.join(QUAL, f"edges_s{s:02d}.log")))
    shared = sorted(set(r1) & set(r2))
    mismatched = [k for k in shared if r1[k] != r2[k]]
    det = dict(run1_comparisons=len(r1), run2_comparisons=len(r2),
               compared_in_both=len(shared), mismatched=len(mismatched),
               mismatch_examples={k: {"run1": r1[k], "run2": r2[k]}
                                  for k in mismatched[:5]},
               run1_only=sorted(set(r1) - set(r2))[:5],
               run2_only=sorted(set(r2) - set(r1))[:5],
               identical=len(mismatched) == 0 and set(r1) == set(r2),
               what_is_compared="band positions, |A_exact|, |oracle| and the equality "
                                "verdict for every comparison ID, not merely the 64/64 "
                                "total")

    # ---- 12 positive-control sensitivity
    pc_path = os.path.join(QUAL, "edges_positive_control.receipt.json")
    pc = json.load(open(pc_path)) if os.path.exists(pc_path) else None
    fx_path = os.path.join(QUAL, "fixtures.receipt.json")
    fx = json.load(open(fx_path)) if os.path.exists(fx_path) else None

    verdict = dict(
        schema="V64_NIH_CARD_EXACT_SAMPLER_REAL_EDGE_AGGREGATE_V1",
        governs="V64_NIH_CARD_STAGE3_PHASE_A_EXACT_SAMPLER_TEST_CONTRACT_V1",
        date="2026-09-30",
        R1_predeclared_ids=len(expected),
        R1_how_predeclared="regenerated from seed 20260929 over the frozen E2 table "
                           f"({n_rows} rows, sha256 {B.E2_SHA[:16]}...), independently "
                           "of any shard output",
        R2_duplicate_ids=dupes, R2_missing_ids=missing, R2_unexpected_ids=unexpected,
        R2_identity_clean=(not dupes and not missing and not unexpected),
        R3_completed=len(all_checks),
        R3_all_64_completed=len(all_checks) == 64,
        R4_comparison_kind="EXACT SET EQUALITY on sorted integer start lists, not "
                           "cardinality equality",
        R4_all_equal=eq_all,
        R5_algebra_only_total=alg_only,
        R6_oracle_only_total=orc_only,
        R7_non_empty_comparisons=len(non_empty),
        R8_zero_vs_zero_comparisons=len(zero_zero),
        R9_total_candidate_starts_challenged=challenged,
        R9_of_which_pushed_through_liftover_as_supplement_candidates=supp_challenged,
        R10_comparisons_where_supplement_path_ran=len(supp_ran),
        R10_comparisons_where_supplement_contributed_starts=len(supp_contrib),
        R10_total_supplement_starts_in_A_exact=sum(
            c.get("A_supplement_card", 0) for c in all_checks),
        R11_determinism=det,
        R12_positive_control=pc,
        R12_historical_evidence_the_comparator_fires={
            "event": "fixture F3 on the pre-S50 code returned exact_set_equality=False",
            "algebra_returned": 10001, "oracle_returned": 2001,
            "why_it_matters": "the same comparator, on the same code path, has already "
                              "produced a FAIL. It is not a check that cannot fail."},
        R13_shard_receipt_sha256=shard_hashes,
        R13_aggregate_binding=hashlib.sha256(
            "".join(shard_hashes[k] for k in sorted(shard_hashes)).encode()).hexdigest(),
        inputs_agreed_across_shards=inputs_consistent,
        inputs={k: (sorted(v)[0] if len(v) == 1 else sorted(map(str, v)))
                for k, v in inp.items()},
        non_empty_support_note=(
            "A 0-vs-0 equality is structurally weak evidence. The force of this test "
            "comes from the non-empty comparisons and from the total starts actually "
            "challenged, both reported above and neither inferred."),
        governance=dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                        td60="BLOCKED", Morabito="PROTECTED",
                        correspondence_opened=False))

    gates = {
        "R2_identity_clean": verdict["R2_identity_clean"],
        "R3_all_64_completed": verdict["R3_all_64_completed"],
        "R4_all_equal": eq_all,
        "R5_zero_algebra_only": alg_only == 0,
        "R6_zero_oracle_only": orc_only == 0,
        "R7_non_empty_present": len(non_empty) > 0,
        "R11_run1_run2_identical": det["identical"],
        "R12_positive_control_retained": bool(pc and pc.get("sensitivity_retained")),
        "inputs_agreed_across_shards": inputs_consistent,
    }
    verdict["gates"] = gates
    verdict["failed_gates"] = [k for k, v in gates.items() if not v]
    verdict["status"] = "PASS" if not verdict["failed_gates"] else "FAIL"
    verdict["phase_a_authorised_by_this_artifact"] = verdict["status"] == "PASS"

    out = os.path.join(QUAL, "edges_AGGREGATE.receipt.json")
    with open(out, "w", newline="\n") as fh:
        json.dump(verdict, fh, indent=2)

    print(json.dumps({k: verdict[k] for k in (
        "R1_predeclared_ids", "R2_identity_clean", "R3_completed",
        "R4_all_equal", "R5_algebra_only_total", "R6_oracle_only_total",
        "R7_non_empty_comparisons", "R8_zero_vs_zero_comparisons",
        "R9_total_candidate_starts_challenged",
        "R9_of_which_pushed_through_liftover_as_supplement_candidates",
        "R10_comparisons_where_supplement_path_ran",
        "R10_comparisons_where_supplement_contributed_starts",
        "R10_total_supplement_starts_in_A_exact",
        "inputs_agreed_across_shards", "failed_gates", "status")}, indent=2))
    print("determinism:", json.dumps(
        {k: det[k] for k in ("run1_comparisons", "run2_comparisons",
                             "compared_in_both", "mismatched", "identical")}))
    print("aggregate binding:", verdict["R13_aggregate_binding"])
    return 0 if verdict["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
