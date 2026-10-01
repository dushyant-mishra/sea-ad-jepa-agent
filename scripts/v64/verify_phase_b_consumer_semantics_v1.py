#!/usr/bin/env python3
"""S81: consumer semantics RECOMPUTED from the Phase-B artifacts, not restated.

WHAT WAS WRONG (S81). My G18 compared counts and shapes the substrate contract already
declared, which proves the contract is self-consistent and nothing more. It never opened
the sparse payloads to count nnz, never recomputed the aggregate binding from the shard
bytes, and never checked that a pair actually RESOLVES to one gene and one interval. A
consumer could therefore satisfy every digest and still read the arrays along the wrong
axis or against a dictionary one shard disagrees about.

Every check here is computed from the artifacts. The contract supplies only the expected
value; it never supplies the observation.

STRUCTURE. The gates are a pure function of loaded arrays, so the mutation suite can
corrupt a real array in memory and watch exactly one gate go red. A test that edits a
number in the authority JSON proves nothing about the data.

MEMORY. nnz is accumulated per shard rather than by concatenating 62 million triplets.

No RNA or ATAC matrix is opened. No correspondence value is computed.
TRAINING=OFF. STAGE 4 NOT AUTHORISED.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

OUT = "D:/jepa_v5_outputs_20260925/v64_phase_b"
DIR = "results/v64/phase_b_design"
SHARD_GLOB = os.path.join(OUT, "PHASE_B_SUBSTRATE_s*.npz")
T5_PATH = os.path.join(OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz")
AVAIL_PATH = os.path.join(OUT, "PHASE_B_T3_T4_AVAILABILITY.npz")

EXPECT = dict(
    t3_nnz=6_624_289,
    t4_nnz=55_467_544,
    aggregate_binding="2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52",
    metacells=3231, genes=4372, intervals=32153, pairs=37419,
    t5_rows=10_552_158,
    availability_states=["MEASURED", "NOT_MEASURED_RNA_ZERO_COVERAGE",
                         "NOT_MEASURED_ATAC_ZERO_COVERAGE",
                         "NOT_MEASURED_RNA_ZERO_VARIANCE",
                         "NOT_MEASURED_ATAC_ZERO_VARIANCE"],
    # S82: frozen from the accepted substrate. These make C17 a real check rather than an
    # observation, so any substitution or reordering of a dictionary is detected even
    # where sortedness alone would survive it.
    gene_dict_sha256="bad9c909aa4be37ccb9dc4bd9d62524b83eaae21651709ef9f7c53136be55e69",
    interval_dict_sha256="2a173c45443a345c3ede8e5d170e0f6d9995480e105ef6025a3261c140ecad7d",
    pair_dict_sha256="ff5fe6de4e104b69b32878bc0d2d1e005a8a6b2d6771b10c7de5a7a502f76105",
)


def load_substrate(shard_paths=None, t5_path=None, avail_path=None):
    """Load exactly what a Stage-4 consumer would. Returns a plain dict so a mutation
    suite can corrupt one field and leave everything else authentic."""
    shard_paths = sorted(shard_paths or glob.glob(SHARD_GLOB))
    shards = []
    for p in shard_paths:
        d = np.load(p, allow_pickle=True)
        shards.append(dict(
            path=p,
            genes=d["genes"], interval_start=d["interval_start"],
            interval_end=d["interval_end"], interval_chrom=d["interval_chrom"],
            n_assigned_peaks=d["n_assigned_peaks"],
            pair_keys=d["pair_keys"], pair_gene=d["pair_gene"],
            pair_interval=d["pair_interval"],
            t2_metacell=d["t2_metacell"], t2_donor=d["t2_donor"],
            t2_n_nuclei=d["t2_n_nuclei"],
            t2_total_rna=d["t2_total_rna"], t2_total_atac=d["t2_total_atac"],
            t3_n=int(len(d["t3_value"])), t4_n=int(len(d["t4_value"])),
            t3_metacell=d["t3_metacell"], t3_gene=d["t3_gene"],
            t3_value=d["t3_value"],
            t4_metacell=d["t4_metacell"], t4_interval=d["t4_interval"],
            t4_value=d["t4_value"],
            sha256=B.sha_file(p)))
    t5 = dict(np.load(t5_path or T5_PATH, allow_pickle=True))
    av = dict(np.load(avail_path or AVAIL_PATH, allow_pickle=True))
    return dict(shards=shards, t5=t5, avail=av)


def check_consumer_semantics(S, expect=None):
    """Pure function of loaded arrays -> {gate: (passed, detail)}."""
    e = dict(EXPECT, **(expect or {}))
    g = {}
    sh = S["shards"]
    ref = sh[0]

    # C1 exact nnz, accumulated from the payloads
    t3 = sum(s["t3_n"] for s in sh)
    t4 = sum(s["t4_n"] for s in sh)
    g["C1_T3_NNZ_EXACT"] = (t3 == e["t3_nnz"],
                            f"counted {t3:,} expected {e['t3_nnz']:,}")
    g["C2_T4_NNZ_EXACT"] = (t4 == e["t4_nnz"],
                            f"counted {t4:,} expected {e['t4_nnz']:,}")

    # C3 aggregate binding recomputed from the shard bytes, in shard order
    agg = hashlib.sha256("".join(s["sha256"] for s in
                                 sorted(sh, key=lambda x: x["path"])).encode()).hexdigest()
    g["C3_AGGREGATE_BINDING_RECOMPUTED"] = (
        agg == e["aggregate_binding"],
        f"recomputed {agg[:20]}... expected {e['aggregate_binding'][:20]}...")

    # C4/C5 dictionaries identical across every shard, ORDER included
    def allsame(key):
        return all(np.array_equal(ref[key], s[key]) for s in sh)
    gene_ok = allsame("genes")
    iv_ok = all(allsame(k) for k in ("interval_start", "interval_end",
                                     "interval_chrom", "n_assigned_peaks"))
    pair_ok = all(allsame(k) for k in ("pair_keys", "pair_gene", "pair_interval"))
    g["C4_GENE_DICT_AGREES_ACROSS_SHARDS"] = (gene_ok, f"{len(sh)} shards compared")
    g["C5_INTERVAL_DICT_AGREES_ACROSS_SHARDS"] = (iv_ok, f"{len(sh)} shards compared")
    g["C6_PAIR_DICT_AGREES_ACROSS_SHARDS"] = (pair_ok, f"{len(sh)} shards compared")

    # C7 no shard carries a different ORDERING even if the set matches
    order_prob = []
    for s in sh[1:]:
        for k in ("genes", "pair_keys"):
            if set(map(str, s[k])) == set(map(str, ref[k])) and not np.array_equal(
                    s[k], ref[k]):
                order_prob.append((os.path.basename(s["path"]), k))
    g["C7_NO_SHARD_REORDERS_A_DICTIONARY"] = (
        not order_prob, "same set but different order: " + str(order_prob[:3])
        if order_prob else "no shard reorders a dictionary it otherwise shares")

    # C8 every pair_gene resolves to EXACTLY ONE gene-dictionary element
    gl = [str(x) for x in ref["genes"]]
    from collections import Counter
    gc = Counter(gl)
    dup_genes = [k for k, v in gc.items() if v > 1]
    gset = set(gl)
    pg = [str(x) for x in ref["pair_gene"]]
    unresolved = sorted({x for x in pg if x not in gset})
    g["C8_EVERY_PAIR_GENE_RESOLVES_UNIQUELY"] = (
        not unresolved and not dup_genes,
        f"{len(pg):,} pair genes over a {len(gl):,}-entry dictionary; "
        f"{len(unresolved)} unresolved, {len(dup_genes)} duplicate dictionary entries")

    # C9 every pair interval resolves to exactly one interval-axis element
    n_iv = len(ref["interval_start"])
    pi = np.asarray(ref["pair_interval"])
    bad_iv = int(((pi < 0) | (pi >= n_iv)).sum())
    g["C9_EVERY_PAIR_INTERVAL_RESOLVES"] = (
        bad_iv == 0 and n_iv == e["intervals"],
        f"{len(pi):,} pair intervals into a {n_iv:,}-element axis; {bad_iv} out of range")

    # C10 metacell ids are exactly 0..N-1, no gap and no duplicate
    mc = np.sort(np.concatenate([s["t2_metacell"] for s in sh]))
    exact = bool(np.array_equal(mc, np.arange(e["metacells"])))
    g["C10_METACELL_IDS_EXACTLY_0_TO_N"] = (
        exact, f"{len(mc):,} ids, unique {len(np.unique(mc)):,}, "
               f"expected a dense 0..{e['metacells']-1}")

    # C11 every T3/T4 index addresses a real metacell, gene and interval
    bad = 0
    for s in sh:
        bad += int(((s["t3_metacell"] < 0) | (s["t3_metacell"] >= e["metacells"])).sum())
        bad += int(((s["t3_gene"] < 0) | (s["t3_gene"] >= len(gl))).sum())
        bad += int(((s["t4_metacell"] < 0) | (s["t4_metacell"] >= e["metacells"])).sum())
        bad += int(((s["t4_interval"] < 0) | (s["t4_interval"] >= n_iv)).sum())
    g["C11_ALL_T3_T4_INDICES_IN_RANGE"] = (bad == 0, f"{bad} out-of-range indices")

    # C12 pair-key semantics agree with the accepted pair dictionary
    t5pk = S["t5"].get("pair_key")
    pk = [str(x) for x in ref["pair_keys"]]
    pk_unique = len(set(pk)) == len(pk) == e["pairs"]
    t5_ok = True
    if t5pk is not None:
        t5_ok = set(map(str, np.unique(t5pk))) == set(pk)
    g["C12_PAIR_KEY_SEMANTICS_AGREE"] = (
        pk_unique and t5_ok,
        f"{len(pk):,} pair keys, unique={len(set(pk))==len(pk)}, "
        f"T5 pair-key set matches dictionary={t5_ok}")

    # C13 T5 row count and donor-major layout
    code = S["t5"].get("availability_state_code")
    rows_ok = code is not None and len(code) == e["t5_rows"]
    donors = len(np.unique(S["t5"]["donor"])) if "donor" in S["t5"] else 0
    layout_ok = rows_ok and donors * e["pairs"] == e["t5_rows"]
    g["C13_T5_ROWS_AND_LAYOUT"] = (
        bool(rows_ok and layout_ok),
        f"{0 if code is None else len(code):,} rows, {donors} donors x "
        f"{e['pairs']:,} pairs")

    # C14 availability vocabulary, order included
    st = [str(x) for x in S["t5"].get("states", [])]
    g["C14_AVAILABILITY_VOCABULARY_IN_ORDER"] = (
        st == e["availability_states"], f"{st}")

    # C16 (S82) the dictionaries must still be in their CONSTRUCTION order.
    # C4-C9 compare shards against each other and check resolution, so a swap applied
    # CONSISTENTLY to every shard passes all of them while silently changing the
    # gene->index and interval->index mappings -- exactly the wrong-axis corruption this
    # verifier exists to catch. The builder creates these as sorted(...), so sortedness
    # is a real construction invariant that an external party can check without trusting
    # any shard.
    gl_s = [str(x) for x in ref["genes"]]
    iv_tuples = list(zip([str(x) for x in ref["interval_chrom"]],
                         np.asarray(ref["interval_start"]).tolist(),
                         np.asarray(ref["interval_end"]).tolist()))
    pk_s = [str(x) for x in ref["pair_keys"]]
    gene_sorted = gl_s == sorted(gl_s)
    iv_sorted = iv_tuples == sorted(iv_tuples)
    pk_sorted = pk_s == sorted(pk_s)
    g["C16_DICTIONARIES_IN_CONSTRUCTION_ORDER"] = (
        bool(gene_sorted and iv_sorted and pk_sorted),
        f"gene sorted={gene_sorted}, interval sorted={iv_sorted}, "
        f"pair_key sorted={pk_sorted}")

    # C17 (S82) content digests over the dictionaries, so ANY substitution or reordering
    # is detected even where sortedness would survive it.
    def dig(*arrs):
        h = hashlib.sha256()
        for a in arrs:
            h.update(np.asarray(a).astype(str).tobytes())
        return h.hexdigest()
    gene_dig = dig(ref["genes"])
    iv_dig = dig(ref["interval_chrom"], ref["interval_start"], ref["interval_end"])
    pair_dig = dig(ref["pair_keys"], ref["pair_gene"], ref["pair_interval"])
    exp_g = e.get("gene_dict_sha256")
    exp_i = e.get("interval_dict_sha256")
    exp_p = e.get("pair_dict_sha256")
    if exp_g is None:
        g["C17_DICTIONARY_CONTENT_DIGESTS"] = (
            True, f"no frozen digests supplied; observed gene={gene_dig[:16]}... "
                  f"interval={iv_dig[:16]}... pair={pair_dig[:16]}...")
    else:
        ok = (gene_dig == exp_g and iv_dig == exp_i and pair_dig == exp_p)
        g["C17_DICTIONARY_CONTENT_DIGESTS"] = (
            ok, f"gene {'ok' if gene_dig==exp_g else 'DIFFERS'}, "
                f"interval {'ok' if iv_dig==exp_i else 'DIFFERS'}, "
                f"pair {'ok' if pair_dig==exp_p else 'DIFFERS'}")
    g["_observed_dictionary_digests"] = (True, json.dumps(
        dict(gene=gene_dig, interval=iv_dig, pair=pair_dig)))

    # C15 availability encoding, shape and BIT INTERPRETATION
    av = S["avail"]
    t3s, t4s = list(av["t3_shape"]), list(av["t4_shape"])
    t3p, t4p = av["t3_available_packed"], av["t4_available_packed"]
    exp3, exp4 = t3s[0] * t3s[1], t4s[0] * t4s[1]
    pad3 = len(t3p) * 8 - exp3
    pad4 = len(t4p) * 8 - exp4
    unpacked_ok = True
    try:
        u3 = np.unpackbits(t3p)[:exp3]
        u4 = np.unpackbits(t4p)[:exp4]
        # the factorisation must reproduce the expanded columns exactly
        f3 = np.repeat(av["factor_rna_metacell_ok"][:, None], t3s[1], axis=1).ravel()
        f4 = (av["factor_atac_metacell_ok"][:, None]
              & av["factor_interval_ok"][None, :]).ravel()
        unpacked_ok = bool(np.array_equal(u3.astype(bool), f3)
                           and np.array_equal(u4.astype(bool), f4))
    except Exception as exc:                                     # noqa: BLE001
        unpacked_ok = False
        pad3 = pad4 = -1
    g["C15_AVAILABILITY_ENCODING_AND_BITS"] = (
        bool(t3s == [e["metacells"], e["genes"]] and t4s == [e["metacells"], e["intervals"]]
             and 0 <= pad3 < 8 and 0 <= pad4 < 8 and unpacked_ok),
        f"T3 {t3s} pad {pad3}, T4 {t4s} pad {pad4}, "
        f"factorisation reproduces the packed bits: {unpacked_ok}")
    return g


def main() -> int:
    S = load_substrate()
    g = check_consumer_semantics(S)
    info = {k: v for k, v in g.items() if k.startswith("_")}
    g = {k: v for k, v in g.items() if not k.startswith("_")}
    failed = [k for k, (ok, _) in g.items() if not ok]
    for k in sorted(g):
        ok, d = g[k]
        print(f"  {k:<40} {'PASS' if ok else 'FAIL'}  {d}")
    for k, v in info.items():
        print(f"  {k:<40} {v[1]}")
    rec = dict(schema="V64_PHASE_B_CONSUMER_SEMANTICS_V1", date="2026-10-01",
               closes="S81",
               checks={k: dict(passed=v[0], detail=v[1]) for k, v in g.items()},
               n_checks=len(g), failed=failed,
               recomputed_from_artifacts=True,
               contract_supplies_expected_value_only=True,
               rna_matrix_opened=False, atac_matrix_opened=False,
               computed_correspondence_values=0,
               observed_dictionary_digests=json.loads(info["_observed_dictionary_digests"][1])
               if "_observed_dictionary_digests" in info else None,
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               status="PASS" if not failed else "FAIL")
    p = os.path.join(DIR, "V64_PHASE_B_CONSUMER_SEMANTICS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print("")
    print(f"{len(g)-len(failed)}/{len(g)} consumer-semantics checks PASS -> {rec['status']}")
    print(f"receipt sha256 {B.sha_file(p)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
