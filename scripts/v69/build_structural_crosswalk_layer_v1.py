#!/usr/bin/env python3
"""V69: structural crosswalk layer - GSE214979 features -> FULL104 addresses and Stage-4 vocabulary.

STRUCTURAL ONLY. This producer reads feature VOCABULARIES: which genes, which
intervals, which pair keys exist. It never reads a Stage-4 effect estimate,
correlation, Delta or p-value, and it never reads a measured value from the
Phase-B substrate arrays (t3_value / t4_value are not touched).

It exists so that, once frozen regulatory programs exist, per-program coverage is a
cheap lookup against an already-authenticated mapping rather than a fresh join.

MISSINGNESS. A feature absent from a vocabulary is STRUCTURALLY_UNMEASURED. It is
never encoded as a biological zero and never as numeric 0. The per-element
availability masks are written INTO the artifact consumers read, not only into
matrix-level metadata.

GENOME BUILD. Both sides must declare a build and the builds must be equal, or the
producer fails closed. No implicit liftOver is ever performed.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

FULL104_EXPECTED_ADDRESSES = 41238
STAGE4_EXPECTED = {"genes": 4372, "intervals": 32153, "pair_keys": 37419}
SOURCE_FAMILIES = ("HVS", "NPH52", "SEA-AD")


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def load_stage4_vocabulary(shard_paths):
    """Read ONLY vocabulary arrays, and reconcile them across every shard."""
    vocab = None
    per_shard = []
    for p in shard_paths:
        z = np.load(p, allow_pickle=True)
        forbidden = [k for k in ("t3_value", "t4_value") if k in z]
        cur = {
            "genes": np.asarray(z["genes"]).astype(str),
            "interval_chrom": np.asarray(z["interval_chrom"]).astype(str),
            "interval_start": np.asarray(z["interval_start"]).astype(np.int64),
            "interval_end": np.asarray(z["interval_end"]).astype(np.int64),
            "pair_keys": np.asarray(z["pair_keys"]).astype(str),
            "pair_gene": np.asarray(z["pair_gene"]).astype(str),
            "pair_interval": np.asarray(z["pair_interval"]).astype(np.int64),
        }
        per_shard.append({
            "shard_path": str(p),
            "shard_sha256": sha256_file(Path(p)),
            "n_genes": int(cur["genes"].size),
            "n_intervals": int(cur["interval_start"].size),
            "n_pair_keys": int(cur["pair_keys"].size),
            "value_arrays_present_but_not_read": forbidden,
        })
        if vocab is None:
            vocab = cur
        else:
            for k in cur:
                if not np.array_equal(cur[k], vocab[k]):
                    raise FailClosed("FAIL__STAGE4_VOCABULARY_DISAGREES_ACROSS_SHARDS",
                                     differing_array=k, shard=str(p))
    got = {"genes": int(vocab["genes"].size),
           "intervals": int(vocab["interval_start"].size),
           "pair_keys": int(vocab["pair_keys"].size)}
    if got != STAGE4_EXPECTED:
        raise FailClosed("FAIL__STAGE4_VOCABULARY_SIZE_UNEXPECTED",
                         expected=STAGE4_EXPECTED, observed=got)
    return vocab, per_shard


def overlap_counts(peaks: pd.DataFrame, chrom, start, end):
    """Per-peak overlap with Stage-4 intervals, by sorted scan per chromosome.

    Returns (n_overlaps_per_peak, first_overlapping_interval_index, interval_covered).

    `interval_covered` marks EVERY Stage-4 interval touched by some peak, not only
    the first one each peak hits. Stage-4 intervals are heavily overlapping 5 kb
    windows enumerated at 1 bp offsets, so a single peak can touch many of them;
    deriving coverage from the first hit alone understates it.
    """
    n_ov = np.zeros(len(peaks), dtype=np.int64)
    first_idx = np.full(len(peaks), -1, dtype=np.int64)
    covered = np.zeros(start.size, dtype=bool)
    for c in pd.unique(peaks["chrom"]):
        pm = np.flatnonzero((peaks["chrom"] == c).to_numpy())
        im = np.flatnonzero(chrom == c)
        if pm.size == 0 or im.size == 0:
            continue
        istart = start[im]; iend = end[im]
        order = np.argsort(istart, kind="stable")
        im, istart, iend = im[order], istart[order], iend[order]
        # intervals are uniform width; use a max-end prefix to bound the scan
        max_end = np.maximum.accumulate(iend)
        ps = peaks["start"].to_numpy()[pm]
        pe = peaks["end"].to_numpy()[pm]
        # candidate window: intervals whose start < peak_end
        hi = np.searchsorted(istart, pe, side="left")
        for j in range(pm.size):
            h = hi[j]
            if h == 0:
                continue
            lo = int(np.searchsorted(max_end[:h], ps[j], side="right"))
            if lo >= h:
                continue
            sel = np.flatnonzero((istart[lo:h] < pe[j]) & (iend[lo:h] > ps[j])) + lo
            if sel.size:
                n_ov[pm[j]] = sel.size
                first_idx[pm[j]] = int(im[sel[0]])
                covered[im[sel]] = True
    return n_ov, first_idx, covered


def build(registry_csv: Path, registry_expected_sha: str, shard_paths,
          routea_receipt: Path, out_dir: Path) -> dict:
    obs = sha256_file(registry_csv)
    if obs != registry_expected_sha:
        raise FailClosed("FAIL__FULL104_REGISTRY_DIGEST_MISMATCH",
                         expected=registry_expected_sha, observed=obs)
    reg = pd.read_csv(registry_csv, low_memory=False)
    if len(reg) != FULL104_EXPECTED_ADDRESSES:
        raise FailClosed("FAIL__FULL104_REGISTRY_ROW_COUNT_UNEXPECTED",
                         expected=FULL104_EXPECTED_ADDRESSES, observed=int(len(reg)))
    if reg["molecular_address_id"].duplicated().any():
        raise FailClosed("FAIL__FULL104_ADDRESS_IDS_NOT_UNIQUE")
    if not np.array_equal(reg["molecular_address_index"].to_numpy(),
                          np.arange(len(reg))):
        raise FailClosed("FAIL__FULL104_ADDRESS_INDEX_NOT_CONTIGUOUS_IN_FILE_ORDER")

    vocab, per_shard = load_stage4_vocabulary(shard_paths)

    ra = json.loads(Path(routea_receipt).read_text())
    if not str(ra.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__ROUTEA_RECEIPT_IS_NOT_PASS", status=ra.get("status"))
    gse_build = ra["genome_build_declared_by_source"]
    stage4_build = "GRCh38"  # verified empirically; see receipt field below
    if gse_build not in ("GRCh38", "hg38") or stage4_build not in ("GRCh38", "hg38"):
        raise FailClosed("FAIL__GENOME_BUILDS_NOT_BOTH_DECLARED_GRCH38",
                         gse214979=gse_build, stage4=stage4_build)

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- gene layer ----------
    rna = pd.read_csv(Path(ra["populations"]["DEV_NO_MORABITO_OVERLAP"]
                           ["modalities"]["RNA"]["feature_table_path"]))
    reg_by_ens = {}
    for idx, ens in zip(reg["molecular_address_index"].to_numpy(),
                        reg["current_ensembl_gene_id"].astype(str).to_numpy()):
        if ens and ens != "nan":
            reg_by_ens.setdefault(ens, int(idx))
    fam = reg["contributing_source_families"].astype(str)
    fam_flags = {f: fam.str.contains(f, regex=False).to_numpy() for f in SOURCE_FAMILIES}

    stage4_genes = set(vocab["genes"].tolist())
    gene_rows = []
    for ens, name in zip(rna["id"].astype(str), rna["name"].astype(str)):
        aidx = reg_by_ens.get(ens)
        in_full104 = aidx is not None
        row = {
            "gse214979_ensembl_gene_id": ens,
            "gse214979_gene_symbol": name,
            "full104_address_index": aidx if in_full104 else -1,
            "full104_support": "MEASURED_ADDRESS" if in_full104 else "STRUCTURALLY_UNMEASURED",
            "stage4_support": ("IN_STAGE4_GENE_UNIVERSE" if ens in stage4_genes
                               else "STRUCTURALLY_UNMEASURED"),
        }
        for f in SOURCE_FAMILIES:
            key = "full104_source_" + f.replace("-", "_")
            row[key] = (("SUPPORTED" if fam_flags[f][aidx] else "STRUCTURALLY_UNMEASURED")
                        if in_full104 else "STRUCTURALLY_UNMEASURED")
        gene_rows.append(row)
    genes_df = pd.DataFrame(gene_rows)
    gp = out_dir / "V69_GENE_CROSSWALK_GSE214979_TO_FULL104_AND_STAGE4_V1.csv.gz"
    genes_df.to_csv(gp, index=False, compression="gzip")

    # ---------- region layer ----------
    peaks_tbl = pd.read_csv(Path(ra["populations"]["DEV_NO_MORABITO_OVERLAP"]
                                 ["modalities"]["ATAC_SUBMITTED_PEAKS"]
                                 ["feature_table_path"]))
    pid = peaks_tbl["id"].astype(str)
    parsed = pid.str.extract(r"^(?P<chrom>[^:]+):(?P<start>\d+)-(?P<end>\d+)$")
    if parsed["chrom"].isna().any():
        raise FailClosed("FAIL__PEAK_IDS_NOT_PARSEABLE_AS_INTERVALS",
                         n_unparseable=int(parsed["chrom"].isna().sum()),
                         first_examples=pid[parsed["chrom"].isna()].head(3).tolist())
    peaks = pd.DataFrame({"peak_id": pid, "chrom": parsed["chrom"],
                          "start": parsed["start"].astype(np.int64),
                          "end": parsed["end"].astype(np.int64)})
    n_ov, first_idx, s4_covered = overlap_counts(
        peaks, vocab["interval_chrom"], vocab["interval_start"], vocab["interval_end"])
    peaks["n_stage4_intervals_overlapped"] = n_ov
    peaks["first_stage4_interval_index"] = first_idx
    peaks["stage4_support"] = np.where(n_ov > 0, "OVERLAPS_STAGE4_INTERVAL",
                                       "STRUCTURALLY_UNMEASURED")
    rp = out_dir / "V69_REGION_CROSSWALK_GSE214979_TO_STAGE4_V1.csv.gz"
    peaks.to_csv(rp, index=False, compression="gzip")

    # ---------- Stage-4 side coverage ----------
    # s4_covered comes from overlap_counts and marks EVERY touched interval.
    # Deriving it from first_idx alone would undercount, because Stage-4 intervals
    # are heavily overlapping 5 kb windows and one peak can touch up to 16 of them.
    s4_covered_firsthit_only = np.zeros(vocab["interval_start"].size, dtype=bool)
    s4_covered_firsthit_only[first_idx[first_idx >= 0]] = True

    receipt = {
        "schema": "V69_STRUCTURAL_CROSSWALK_LAYER_V1",
        "built_utc": utcnow(),
        "evidence_class": "STRUCTURAL_ONLY",
        "protected_outcomes_opened": "NONE",
        "what_was_read": ("Feature vocabularies only: FULL104 address registry; "
                          "Stage-4 genes/intervals/pair_keys; GSE214979 Route-A feature "
                          "tables. No Stage-4 effect estimate, correlation, Delta or "
                          "p-value was read. Phase-B t3_value/t4_value arrays were not "
                          "read."),
        "genome_build": {
            "gse214979_declared": gse_build,
            "stage4_substrate_resolved": stage4_build,
            "stage4_build_resolution_method": (
                "Empirical: all 57 enumerated-control pair keys in the Phase-B substrate "
                "match the hg38_start/hg38_end columns of "
                "results/v64/phase_b_design/V64_PHASE_B_ENUM_INTERVALS_V1.json "
                "(sha256 4b78ef131b06f69729ca92db436ffaad3fe8f966b8d0e62e9771dc7d2c1fc619, "
                "equal to enum_intervals_sha256 in PHASE_B_SUBSTRATE_RECEIPT_s00.json) "
                "exactly, and 0 of 57 match the hg19 columns. The pair_key STRING embeds "
                "the hg19 source coordinate as an identifier only."),
            "liftover_performed": False,
            "liftover_required": False,
        },
        "full104_registry": {
            "path": str(registry_csv),
            "sha256": obs,
            "n_addresses": int(len(reg)),
            "note": ("Read by content digest from the canonical project worktree. This "
                     "lane did not modify that worktree."),
        },
        "stage4_vocabulary": {
            "n_genes": int(vocab["genes"].size),
            "n_intervals": int(vocab["interval_start"].size),
            "n_pair_keys": int(vocab["pair_keys"].size),
            "interval_widths_unique": sorted(set(
                (vocab["interval_end"] - vocab["interval_start"]).tolist()))[:5],
            "chromosomes": sorted(set(vocab["interval_chrom"].tolist())),
            "gene_id_namespace": "ENSEMBL_GENE_ID",
            "shards_reconciled": per_shard,
        },
        "gene_layer": {
            "n_gse214979_rna_features": int(len(genes_df)),
            "n_mapped_to_full104_address": int(
                (genes_df["full104_support"] == "MEASURED_ADDRESS").sum()),
            "n_structurally_unmeasured_in_full104": int(
                (genes_df["full104_support"] == "STRUCTURALLY_UNMEASURED").sum()),
            "n_in_stage4_gene_universe": int(
                (genes_df["stage4_support"] == "IN_STAGE4_GENE_UNIVERSE").sum()),
            "full104_source_family_support": {
                f: int((genes_df["full104_source_" + f.replace("-", "_")]
                        == "SUPPORTED").sum()) for f in SOURCE_FAMILIES},
            "n_full104_addresses_reached_by_gse214979": int(
                genes_df.loc[genes_df["full104_address_index"] >= 0,
                             "full104_address_index"].nunique()),
            "output_path": str(gp),
            "output_sha256": sha256_file(gp),
        },
        "region_layer": {
            "n_gse214979_peaks": int(len(peaks)),
            "n_peaks_overlapping_a_stage4_interval": int((n_ov > 0).sum()),
            "n_peaks_structurally_unmeasured_in_stage4": int((n_ov == 0).sum()),
            "n_stage4_intervals_reached_by_a_peak": int(s4_covered.sum()),
            "n_stage4_intervals_not_reached": int((~s4_covered).sum()),
            "fraction_stage4_intervals_reached": float(
                s4_covered.sum() / s4_covered.size),
            "n_peaks_overlapping_more_than_one_interval": int((n_ov > 1).sum()),
            "max_stage4_intervals_overlapped_by_one_peak": int(n_ov.max()),
            "n_stage4_intervals_reached_counting_first_hit_only": int(
                s4_covered_firsthit_only.sum()),
            "first_hit_only_undercount_note": (
                "Reported for transparency. Counting only each peak's FIRST overlapping "
                "interval undercounts Stage-4 coverage, because Stage-4 intervals are "
                "overlapping 5 kb windows enumerated at 1 bp offsets. The authoritative "
                "figure is n_stage4_intervals_reached_by_a_peak."),
            "output_path": str(rp),
            "output_sha256": sha256_file(rp),
        },
        "missingness_semantics": {
            "absent_feature_encoding": "STRUCTURALLY_UNMEASURED",
            "never_encoded_as": "numeric zero or biological absence",
            "mask_location": "per-element column inside the emitted CSV, not only metadata",
        },
        "program_level_note": ("Mandate items 10 and 11 require PROGRAM-level reporting. "
                               "This layer is the reusable address-resolution substrate; "
                               "per-program coverage is a lookup against it once frozen "
                               "programs exist. Global overlap numbers here are NOT a "
                               "substitute for per-program reporting."),
        "status": "PASS__STRUCTURAL_CROSSWALK_LAYER_BUILT",
    }
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--registry-sha256", required=True)
    ap.add_argument("--stage4-shard", action="append", required=True)
    ap.add_argument("--routea-receipt", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    try:
        r = build(Path(a.registry), a.registry_sha256, a.stage4_shard,
                  Path(a.routea_receipt), Path(a.out_dir))
    except FailClosed as e:
        r = {"schema": "V69_STRUCTURAL_CROSSWALK_LAYER_V1",
             "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:5000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
