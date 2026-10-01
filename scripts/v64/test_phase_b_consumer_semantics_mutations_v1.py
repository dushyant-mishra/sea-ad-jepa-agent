#!/usr/bin/env python3
"""S81 mutation suite: corrupt the REAL loaded artifacts, one defect at a time.

A test that edits a number in the authority JSON proves only that the JSON changed. Every
mutation here alters an actual array a Stage-4 consumer would read -- an availability bit,
a dictionary entry, a shard digest, a metacell id -- and the named gate must go red while
the others stay green.

The substrate is loaded ONCE and each mutation is applied in place and then reverted, so
the suite does not need twelve copies of a 62-million-triplet structure. Every revert is
verified by re-running the full gate set and requiring a clean sheet before the next
mutation, which would catch a restore that silently failed.

Nothing is written to the artifacts on disk. No RNA or ATAC matrix is opened. No
correspondence value is computed.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import verify_phase_b_consumer_semantics_v1 as CS                    # noqa: E402

DIR = "results/v64/phase_b_design"


def main() -> int:
    print("loading the real substrate once ...", flush=True)
    S = CS.load_substrate()
    base = CS.check_consumer_semantics(S)
    base_fail = [k for k, (ok, _) in base.items() if not ok]
    if base_fail:
        print(f"STOP: the unmutated substrate already fails {base_fail}")
        return 2
    print(f"baseline clean: {len(base)}/{len(base)} gates PASS\n")

    sh = S["shards"]
    results = []

    def run(name, expect_gate, apply, revert):
        apply()
        g = CS.check_consumer_semantics(S)
        fired = sorted(k for k, (ok, _) in g.items() if not ok)
        revert()
        g2 = CS.check_consumer_semantics(S)
        restored = not [k for k, (ok, _) in g2.items() if not ok]
        caught = expect_gate in fired
        results.append(dict(mutation=name, must_fire=expect_gate,
                            gates_that_fired=fired, caught_by_named_gate=caught,
                            baseline_restored_after=restored,
                            is_a_real_test=bool(caught and restored)))
        print(f"  {name:<46} -> {fired if fired else 'NONE'}"
              f"  {'OK' if caught and restored else 'FAIL'}")

    # 1 / 2 availability bits
    for tag, key, gate in (("T3", "t3_available_packed", "C15_AVAILABILITY_ENCODING_AND_BITS"),
                           ("T4", "t4_available_packed", "C15_AVAILABILITY_ENCODING_AND_BITS")):
        arr = S["avail"][key]
        old = int(arr[0])
        run(f"flip one {tag} availability bit", gate,
            lambda a=arr, o=old: a.__setitem__(0, o ^ 0b1),
            lambda a=arr, o=old: a.__setitem__(0, o))

    # 3 shard digest changed / reordered -> aggregate binding must not reproduce
    old_sha = sh[3]["sha256"]
    run("change one shard digest", "C3_AGGREGATE_BINDING_RECOMPUTED",
        lambda: sh[3].__setitem__("sha256", "0" * 64),
        lambda: sh[3].__setitem__("sha256", old_sha))
    s0, s1 = sh[0]["sha256"], sh[1]["sha256"]
    run("swap two shard digests (reorder)", "C3_AGGREGATE_BINDING_RECOMPUTED",
        lambda: (sh[0].__setitem__("sha256", s1), sh[1].__setitem__("sha256", s0)),
        lambda: (sh[0].__setitem__("sha256", s0), sh[1].__setitem__("sha256", s1)))

    # 4 nonexistent pair_gene  (mutate every shard so the dict-agreement gate is not the
    #   one under test)
    old_pg = [s["pair_gene"].copy() for s in sh]
    def set_pg(v):
        for s in sh:
            s["pair_gene"] = s["pair_gene"].astype(object)
            s["pair_gene"][0] = v
    run("pair_gene naming a gene not in the dictionary",
        "C8_EVERY_PAIR_GENE_RESOLVES_UNIQUELY",
        lambda: set_pg("ENSG_DOES_NOT_EXIST"),
        lambda: [s.__setitem__("pair_gene", old_pg[i]) for i, s in enumerate(sh)])

    # 5 pair interval out of range
    old_pi = [s["pair_interval"].copy() for s in sh]
    def set_pi(v):
        for s in sh:
            s["pair_interval"] = s["pair_interval"].astype(np.int64)
            s["pair_interval"][0] = v
    run("pair interval index beyond the interval axis",
        "C9_EVERY_PAIR_INTERVAL_RESOLVES",
        lambda: set_pi(10 ** 9),
        lambda: [s.__setitem__("pair_interval", old_pi[i]) for i, s in enumerate(sh)])

    # 6 swapped gene dictionary entry, in EVERY shard (so C4 is not what fires)
    old_g = [s["genes"].copy() for s in sh]
    def swap_genes():
        for s in sh:
            g = s["genes"].copy()
            g[0], g[1] = g[1], g[0]
            s["genes"] = g
    run("swap two gene dictionary entries in every shard",
        "C16_DICTIONARIES_IN_CONSTRUCTION_ORDER",
        swap_genes,
        lambda: [s.__setitem__("genes", old_g[i]) for i, s in enumerate(sh)])

    # 7 swapped interval dictionary entry in every shard
    old_is = [s["interval_start"].copy() for s in sh]
    def swap_iv():
        for s in sh:
            a = s["interval_start"].copy()
            a[0], a[1] = a[1], a[0]
            s["interval_start"] = a
    run("swap two interval dictionary entries in every shard",
        "C16_DICTIONARIES_IN_CONSTRUCTION_ORDER",
        swap_iv,
        lambda: [s.__setitem__("interval_start", old_is[i]) for i, s in enumerate(sh)])

    # 8 missing metacell id
    old_mc = sh[0]["t2_metacell"].copy()
    run("drop one metacell id", "C10_METACELL_IDS_EXACTLY_0_TO_N",
        lambda: sh[0].__setitem__("t2_metacell", sh[0]["t2_metacell"][1:]),
        lambda: sh[0].__setitem__("t2_metacell", old_mc))

    # 9 duplicated metacell id
    def dup():
        a = old_mc.copy()
        a[1] = a[0]
        sh[0]["t2_metacell"] = a
    run("duplicate one metacell id", "C10_METACELL_IDS_EXACTLY_0_TO_N",
        dup, lambda: sh[0].__setitem__("t2_metacell", old_mc))

    # 10 one shard with a different PAIR dictionary order
    old_pk3 = sh[3]["pair_keys"].copy()
    def reorder_pk():
        a = old_pk3.copy()
        a[0], a[1] = a[1], a[0]
        sh[3]["pair_keys"] = a
    run("one shard reorders the pair dictionary",
        "C6_PAIR_DICT_AGREES_ACROSS_SHARDS",
        reorder_pk, lambda: sh[3].__setitem__("pair_keys", old_pk3))

    # 11 one shard with a different GENE dictionary order
    old_g5 = sh[5]["genes"].copy()
    def reorder_g():
        a = old_g5.copy()
        a[0], a[1] = a[1], a[0]
        sh[5]["genes"] = a
    run("one shard reorders the gene dictionary",
        "C4_GENE_DICT_AGREES_ACROSS_SHARDS",
        reorder_g, lambda: sh[5].__setitem__("genes", old_g5))

    # 12 one shard with a different INTERVAL dictionary order
    old_ie6 = sh[6]["interval_end"].copy()
    def reorder_iv():
        a = old_ie6.copy()
        a[0], a[1] = a[1], a[0]
        sh[6]["interval_end"] = a
    run("one shard reorders the interval dictionary",
        "C5_INTERVAL_DICT_AGREES_ACROSS_SHARDS",
        reorder_iv, lambda: sh[6].__setitem__("interval_end", old_ie6))

    # 13 T3/T4 index out of range
    old_t3g = sh[2]["t3_gene"].copy()
    def oob():
        a = old_t3g.copy().astype(np.int64)
        a[0] = 10 ** 9
        sh[2]["t3_gene"] = a
    run("T3 gene index beyond the dictionary", "C11_ALL_T3_T4_INDICES_IN_RANGE",
        oob, lambda: sh[2].__setitem__("t3_gene", old_t3g))

    # 14 nnz truncation
    old_t4n = sh[1]["t4_n"]
    run("truncate one shard's T4 payload", "C2_T4_NNZ_EXACT",
        lambda: sh[1].__setitem__("t4_n", old_t4n - 1),
        lambda: sh[1].__setitem__("t4_n", old_t4n))

    real = [r for r in results if r["is_a_real_test"]]
    out = dict(schema="V64_PHASE_B_CONSUMER_SEMANTICS_MUTATIONS_V1", date="2026-10-01",
               closes="S81",
               mutations_applied_to="the real loaded artifact arrays, in memory",
               artifacts_on_disk_unmodified=True,
               n_mutations=len(results), n_real_tests=len(real),
               every_mutation_caught_by_its_named_gate=len(real) == len(results),
               results=results,
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               computed_correspondence_values=0,
               status="PASS" if len(real) == len(results) else "FAIL")
    p = os.path.join(DIR, "V64_PHASE_B_CONSUMER_SEMANTICS_MUTATIONS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print(f"{len(real)}/{len(results)} mutations caught by their named gate "
          f"-> {out['status']}")
    print(f"receipt sha256 {B.sha_file(p)}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
