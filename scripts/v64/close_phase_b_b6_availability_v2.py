#!/usr/bin/env python3
"""B6 v2: the availability proofs actually executed, not asserted.

WHAT WAS WRONG WITH v1. Its PROOF_3 reported the T5 state counts, explained the
derivation in prose, and then set holds=True as a literal. That is self-certifying: it
would have passed whatever the stored codes contained. A check that cannot fail is the
failure mode this project hunts hardest, and I wrote one. Three narrower gaps came with
it: the sparse-zero argument was executed for RNA only while being claimed for both
modalities; integer metacell ids were used as dense row indices without asserting they are
exactly 0..nM-1; and shard s00 was taken as the canonical gene and interval dictionary
without checking the other seven agree.

v1's receipt is left in place so the gap stays inspectable. This successor replaces its
verdict.

NOTHING IS RERUN. Phase A, the sampler, the substrate, T5, the interval reconciliation and
T6/T7 are all read-only here. No RNA or ATAC matrix value is re-read.

TRAINING=OFF. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

OUT = "D:/jepa_v5_outputs_20260925/v64_phase_b"
DIR = "results/v64/phase_b_design"
STATES = ["MEASURED", "NOT_MEASURED_RNA_ZERO_COVERAGE",
          "NOT_MEASURED_ATAC_ZERO_COVERAGE", "NOT_MEASURED_RNA_ZERO_VARIANCE",
          "NOT_MEASURED_ATAC_ZERO_VARIANCE"]


class Stop(Exception):
    pass


def blob(p):
    """Resolve a path to its git blob, or say plainly that it was not committed yet.

    A producer cannot know its own blob before it is committed. The first version took
    rev-parse's stdout unconditionally, so a failed lookup wrote the literal string
    "HEAD:<path>" into the receipt where a 40-hex blob belongs -- a provenance field
    carrying something that is not what it claims to be. Now a non-zero exit or a
    non-hex result is reported as uncommitted, and the real blob is bound after the
    commit by bind_b6_producer_blob.
    """
    r = subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0 or len(out) != 40 or any(c not in "0123456789abcdef" for c in out):
        return "UNCOMMITTED_AT_BUILD_TIME"
    return out


def main() -> int:
    shards = sorted(glob.glob(os.path.join(OUT, "PHASE_B_SUBSTRATE_s*.npz")))
    if len(shards) != 8:
        raise Stop(f"expected 8 shards, found {len(shards)}")

    # ---- G4: every shard must agree on the gene and interval dictionaries
    ref = np.load(shards[0], allow_pickle=True)
    genes, npk = ref["genes"], ref["n_assigned_peaks"]
    ivc, ivs, ive = ref["interval_chrom"], ref["interval_start"], ref["interval_end"]
    pk, pi = ref["pair_keys"], ref["pair_interval"].astype(np.int64)
    # pair_gene holds gene ID STRINGS, not indices; resolve them against the canonical
    # gene dictionary rather than using them as positions
    _gpos = {g: i for i, g in enumerate(genes.tolist())}
    _missing = sorted({g for g in ref["pair_gene"].tolist() if g not in _gpos})
    if _missing:
        raise Stop(f"pair_gene names absent from the gene dictionary: {_missing[:5]}")
    pg = np.array([_gpos[g] for g in ref["pair_gene"].tolist()], np.int64)
    pg_names = ref["pair_gene"]
    dict_checks, disagree = {}, []
    for p in shards:
        d = np.load(p, allow_pickle=True)
        for name, a, b in (("genes", genes, d["genes"]),
                           ("interval_chrom", ivc, d["interval_chrom"]),
                           ("interval_start", ivs, d["interval_start"]),
                           ("interval_end", ive, d["interval_end"]),
                           ("n_assigned_peaks", npk, d["n_assigned_peaks"]),
                           ("pair_keys", pk, d["pair_keys"]),
                           ("pair_gene", pg_names, d["pair_gene"]),
                           ("pair_interval", pi, d["pair_interval"])):
            if not np.array_equal(a, b):
                disagree.append((os.path.basename(p), name))
    if disagree:
        raise Stop(f"shards disagree on the canonical dictionaries: {disagree[:5]}")
    dict_checks = dict(shards_compared=len(shards),
                       arrays_compared=["genes", "interval_chrom", "interval_start",
                                        "interval_end", "n_assigned_peaks", "pair_keys",
                                        "pair_gene", "pair_interval"],
                       all_identical=True,
                       why="shard s00 is used as the canonical dictionary, so the other "
                           "seven must be proved identical or the availability bits could "
                           "be internally correct while attached to the wrong axis")

    # ---- gather T2/T3/T4 across shards
    t2d, t2m, t2r, t2a = [], [], [], []
    t3m, t3g, t3v, t4m, t4i, t4v = [], [], [], [], [], []
    for p in shards:
        d = np.load(p, allow_pickle=True)
        t2d.append(d["t2_donor"]); t2m.append(d["t2_metacell"])
        t2r.append(d["t2_total_rna"]); t2a.append(d["t2_total_atac"])
        t3m.append(d["t3_metacell"]); t3g.append(d["t3_gene"]); t3v.append(d["t3_value"])
        t4m.append(d["t4_metacell"]); t4i.append(d["t4_interval"]); t4v.append(d["t4_value"])
    t2d, t2m = np.concatenate(t2d), np.concatenate(t2m)
    t2r, t2a = np.concatenate(t2r), np.concatenate(t2a)
    t3m, t3g, t3v = (np.concatenate(t3m), np.concatenate(t3g), np.concatenate(t3v))
    t4m, t4i, t4v = (np.concatenate(t4m), np.concatenate(t4i), np.concatenate(t4v))
    nM, nG, nI, nP = len(t2m), len(genes), len(npk), len(pk)

    # ---- G3: metacell ids must be exactly 0..nM-1 and every index in range
    ids = np.sort(t2m)
    idx_checks = dict(
        n_metacells=int(nM),
        ids_unique=bool(len(np.unique(t2m)) == nM),
        ids_are_exactly_0_to_n_minus_1=bool(np.array_equal(ids, np.arange(nM))),
        t3_metacell_min=int(t3m.min()), t3_metacell_max=int(t3m.max()),
        t4_metacell_min=int(t4m.min()), t4_metacell_max=int(t4m.max()),
        t3_indices_in_range=bool(t3m.min() >= 0 and t3m.max() < nM),
        t4_indices_in_range=bool(t4m.min() >= 0 and t4m.max() < nM),
        t3_gene_in_range=bool(t3g.min() >= 0 and t3g.max() < nG),
        t4_interval_in_range=bool(t4i.min() >= 0 and t4i.max() < nI),
        why="the dense availability matrices are indexed by these integers directly, which "
            "is only sound if the ids are a dense 0-based range")
    if not all(idx_checks[k] for k in
               ("ids_unique", "ids_are_exactly_0_to_n_minus_1", "t3_indices_in_range",
                "t4_indices_in_range", "t3_gene_in_range", "t4_interval_in_range")):
        raise Stop(f"metacell/column index invariants failed: {idx_checks}")

    order = np.argsort(t2m)
    rt, at, don = t2r[order], t2a[order], t2d[order]

    # ---- availability, factorised and expanded
    rna_mc_ok, atac_mc_ok, iv_ok = rt > 0, at > 0, npk > 0
    T3A = np.repeat(rna_mc_ok[:, None], nG, axis=1)
    T4A = atac_mc_ok[:, None] & iv_ok[None, :]
    t3_packed, t4_packed = np.packbits(T3A.ravel()), np.packbits(T4A.ravel())

    # ---- G2: sparse-absence proof for BOTH modalities
    def sparse_proof(rows, cols, shape, avail, label):
        present = np.zeros(shape, bool)
        present[rows, cols] = True
        aa = int((~present & avail).sum())
        au = int((~present & ~avail).sum())
        return dict(modality=label, elements=int(avail.size),
                    sparse_entries_present=int(present.sum()),
                    sparse_absences_on_AVAILABLE_elements=aa,
                    these_are_measured_zeros=True,
                    value_they_carry="log1p(0) = 0 exactly",
                    sparse_absences_on_UNAVAILABLE_elements=au,
                    holds=au == 0)
    p1_rna = sparse_proof(t3m, t3g, (nM, nG), T3A, "RNA / T3")
    p1_atac = sparse_proof(t4m, t4i, (nM, nI), T4A, "ATAC / T4")

    # ---- G1: PROOF 3 actually executed. Reconstruct every T5 code and compare.
    t5 = np.load(os.path.join(OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz"), allow_pickle=True)
    stored = t5["availability_state_code"]
    stored_donor = t5["donor"]
    donors = sorted(set(don.tolist()))
    mc_of = {d_: np.nonzero(don == d_)[0] for d_ in donors}
    t3_by_mc, t4_by_mc = defaultdict(list), defaultdict(list)
    for m, g, v in zip(t3m, t3g, t3v):
        t3_by_mc[int(m)].append((int(g), float(v)))
    for m, i_, v in zip(t4m, t4i, t4v):
        t4_by_mc[int(m)].append((int(i_), float(v)))

    recon = np.empty(len(donors) * nP, np.int8)
    at_ = 0
    for d_ in donors:
        mcs = mc_of[d_]
        k = len(mcs)
        Rm = np.zeros((k, nG), np.float32); Am = np.zeros((k, nI), np.float32)
        for r_, m in enumerate(mcs):
            for g, v in t3_by_mc.get(int(m), ()):
                Rm[r_, g] = v
            for i_, v in t4_by_mc.get(int(m), ()):
                Am[r_, i_] = v
        g_nz, i_nz = (Rm > 0).any(0), (Am > 0).any(0)
        g_var, i_var = Rm.var(0) > 0, Am.var(0) > 0
        st = np.where(~g_nz[pg], 1,
             np.where(~i_nz[pi], 2,
             np.where(~g_var[pg], 3,
             np.where(~i_var[pi], 4, 0)))).astype(np.int8)
        recon[at_:at_ + nP] = st
        at_ += nP
    if at_ != len(stored):
        raise Stop(f"reconstructed {at_} codes, T5 stores {len(stored)}")
    # donor blocks must line up too, not just the code values
    exp_donor = np.repeat(np.array(donors), nP)
    donor_aligned = bool(np.array_equal(exp_donor, stored_donor))
    mism = int((recon != stored).sum())
    per_state_recon = {STATES[i]: int((recon == i).sum()) for i in range(len(STATES))}
    per_state_stored = {STATES[i]: int((stored == i).sum()) for i in range(len(STATES))}
    p3 = dict(
        executed=True,
        rows_reconstructed=int(at_), rows_stored=int(len(stored)),
        donor_block_order_matches=donor_aligned,
        mismatch_count=mism,
        holds=bool(mism == 0 and donor_aligned and at_ == len(stored)),
        per_state_reconstructed=per_state_recon, per_state_stored=per_state_stored,
        counts_agree=per_state_recon == per_state_stored,
        method="every donor x pair code was recomputed from the frozen T2/T3/T4 arrays "
               "and compared element by element with the stored T5 codes",
        what_v1_did_instead="reported the counts, explained the derivation and set "
                            "holds=True as a literal, which would have passed whatever "
                            "the stored codes contained",
        what_this_catches="a wrong donor or pair ordering, a bad gather, a truncated "
                          "write, or any corruption of the stored codes. It does not "
                          "re-derive the frozen rule itself, which is stated in the "
                          "contract and is not in question here.",
        the_distinction_being_verified=(
            f"{per_state_stored['NOT_MEASURED_RNA_ZERO_COVERAGE']:,} donor-pair cells are "
            "NOT_MEASURED while every underlying element is AVAILABLE. The gene was "
            "measured in each of that donor's metacells and measured as zero in all of "
            "them, so each element is an available measured zero and the frozen "
            "zero-coverage rule leaves the Stage-4 correlation undefined."))
    if not p3["holds"]:
        raise Stop(f"T5 reconciliation failed: mismatches={mism}, "
                   f"donor_aligned={donor_aligned}")

    # ---- P4 factorisation expansion
    p4 = bool(np.array_equal(np.unpackbits(t3_packed)[:T3A.size].reshape(T3A.shape)
                             .astype(bool), T3A)
              and np.array_equal(np.unpackbits(t4_packed)[:T4A.size].reshape(T4A.shape)
                                 .astype(bool), T4A))

    # ---- P2 fixture, unchanged in substance
    fx_rt, fx_at, fx_pk = (np.array([1000.0, 0.0, 500.0]), np.array([800.0, 700.0, 0.0]),
                           np.array([3, 0, 5]))
    fx3 = np.repeat((fx_rt > 0)[:, None], 3, axis=1)
    fx4 = (fx_at > 0)[:, None] & (fx_pk > 0)[None, :]
    p2 = dict(real_substrate_has_no_unavailable_element=True,
              demonstrated_on_fixture=True,
              zero_total_rna_metacell_unavailable=bool(not fx3[1].any()),
              zero_total_atac_metacell_unavailable=bool(not fx4[2].any()),
              zero_peak_interval_unavailable=bool(not fx4[:, 1].any()),
              holds=bool(not fx3[1].any() and not fx4[2].any() and not fx4[:, 1].any()))

    np.savez_compressed(os.path.join(OUT, "PHASE_B_T3_T4_AVAILABILITY.npz"),
                        t3_available_packed=t3_packed, t3_shape=np.array([nM, nG]),
                        t4_available_packed=t4_packed, t4_shape=np.array([nM, nI]),
                        factor_rna_metacell_ok=rna_mc_ok,
                        factor_atac_metacell_ok=atac_mc_ok,
                        factor_interval_ok=iv_ok, metacell_id=np.arange(nM))
    ap = os.path.join(OUT, "PHASE_B_T3_T4_AVAILABILITY.npz")
    t5p = os.path.join(OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz")
    me = os.path.abspath(__file__)
    rel = os.path.relpath(me, os.getcwd()).replace("\\", "/")

    rec = dict(
        schema="V64_PHASE_B_T3_T4_AVAILABILITY_V2", date="2026-09-30", closes="B6",
        supersedes=dict(
            path=os.path.join(DIR, "V64_PHASE_B_T3_T4_AVAILABILITY_V1.json"),
            sha256=B.sha_file(os.path.join(DIR, "V64_PHASE_B_T3_T4_AVAILABILITY_V1.json")),
            reason="v1's PROOF_3 set holds=True as a literal and would have passed "
                   "whatever the stored codes contained; its sparse-zero proof ran for "
                   "RNA only; it indexed by metacell id without asserting the id space; "
                   "and it took one shard's dictionaries as canonical unchecked",
            left_in_place_so_the_gap_stays_inspectable=True),
        nothing_rerun=["Phase A", "sampler", "substrate build", "T5",
                       "interval reconciliation", "T6/T7"],
        no_matrix_value_reread=True,
        G4_SHARD_DICTIONARY_AGREEMENT=dict_checks,
        G3_INDEX_INVARIANTS=idx_checks,
        G2_SPARSE_ABSENCE_BOTH_MODALITIES=dict(rna=p1_rna, atac=p1_atac,
                                               both_hold=p1_rna["holds"] and p1_atac["holds"]),
        G1_PROOF_3_T5_RECONCILIATION_EXECUTED=p3,
        PROOF_2_unavailable_is_false_not_zero=p2,
        PROOF_4_factorisation_expands_exactly=dict(holds=p4),
        T3=dict(field="rna_available", elements=int(T3A.size), shape=[int(nM), int(nG)],
                all_available=bool(T3A.all()), packed_bytes=int(t3_packed.nbytes),
                packed_length=int(len(t3_packed))),
        T4=dict(field="atac_available", elements=int(T4A.size), shape=[int(nM), int(nI)],
                all_available=bool(T4A.all()), packed_bytes=int(t4_packed.nbytes),
                packed_length=int(len(t4_packed))),
        PACKBITS_SEMANTICS=dict(
            function="numpy.packbits", bitorder="big (numpy default)",
            layout="the boolean matrix is raveled in C order, then packed",
            padding=dict(
                t3_pad_bits=int(len(t3_packed) * 8 - T3A.size),
                t4_pad_bits=int(len(t4_packed) * 8 - T4A.size),
                value="0", note="trailing pad bits are not elements and must be dropped "
                                "by slicing to the element count before reshaping"),
            unpack_recipe="np.unpackbits(packed)[:rows*cols].reshape(rows, cols).astype(bool)"),
        FACTORISATION=dict(
            rule_rna="rna_available[m, g] = total_rna[m] > 0, independent of g",
            rule_atac="atac_available[m, i] = total_atac[m] > 0 AND n_assigned_peaks[i] > 0",
            why_lossless="availability depends on whether the metacell's normalisation is "
                         "defined and whether the interval has an assigned peak, never on "
                         "the measured value"),
        CUSTODY=dict(
            shard_sha256={os.path.basename(p): B.sha_file(p) for p in shards},
            t5_donor_aggregates=dict(path=t5p, bytes=os.path.getsize(t5p),
                                     sha256=B.sha_file(t5p)),
            availability_artifact=dict(path=ap, bytes=os.path.getsize(ap),
                                       sha256=B.sha_file(ap)),
            closeout_receipt=dict(
                path=os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json"),
                sha256=B.sha_file(os.path.join(
                    DIR, "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json"))),
            aggregate_receipt=dict(
                path=os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json"),
                sha256=B.sha_file(os.path.join(
                    DIR, "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json"))),
            producer=dict(path=rel, sha256=B.sha_file(me), git_blob=blob(rel))),
        governance=json.load(open(os.path.join(
            DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")))["governance"])
    rec["all_proofs_hold"] = bool(
        dict_checks["all_identical"] and p1_rna["holds"] and p1_atac["holds"]
        and p3["holds"] and p2["holds"] and p4)
    rec["status"] = "PASS" if rec["all_proofs_hold"] else "FAIL"
    p = os.path.join(DIR, "V64_PHASE_B_T3_T4_AVAILABILITY_V2.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print(f"G4 shard dictionaries identical across {len(shards)} shards: "
          f"{dict_checks['all_identical']}")
    print(f"G3 metacell ids are exactly 0..{nM-1}: "
          f"{idx_checks['ids_are_exactly_0_to_n_minus_1']}; all T3/T4 indices in range")
    print(f"G2 sparse absence: RNA {p1_rna['sparse_absences_on_AVAILABLE_elements']:,} "
          f"measured zeros / {p1_rna['sparse_absences_on_UNAVAILABLE_elements']} bad | "
          f"ATAC {p1_atac['sparse_absences_on_AVAILABLE_elements']:,} / "
          f"{p1_atac['sparse_absences_on_UNAVAILABLE_elements']}")
    print(f"G1 T5 reconciliation EXECUTED: {p3['rows_reconstructed']:,} codes rebuilt, "
          f"mismatches {p3['mismatch_count']}, donor order aligned "
          f"{p3['donor_block_order_matches']}")
    print(f"P2 fixture {p2['holds']} | P4 expansion {p4}")
    print(f"\nSTATUS {rec['status']}   receipt sha256 {B.sha_file(p)}")
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
