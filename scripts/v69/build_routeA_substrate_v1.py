#!/usr/bin/env python3
"""V69 Route A: build the submitted-peak-matrix substrate for the frozen cohort.

Route A accepts the region universe exactly as the depositors submitted it
(10x Cell Ranger ARC peaks in the filtered feature-barcode matrix). It is the
fast broad baseline. Route B later reconstructs the region universe from the raw
fragments; the two are deliberately independent constructions of the same biology.

The producer fails closed if:
  * the HDF5 digest does not equal the digest in the acquisition receipt,
  * any frozen cohort barcode is absent from the matrix,
  * the matrix barcodes are not unique,
  * the declared genome build is not single-valued,
  * the recovered cell ORDER does not reproduce the frozen ordered digest.

Only the required CSC column slices are read, so the full 927M-nonzero matrix is
never materialised.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse


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


def _dec(a):
    return np.array([x.decode() if isinstance(x, (bytes, np.bytes_)) else str(x)
                     for x in a], dtype=object)


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def build(h5_path: Path, acq_receipt: Path, cohort_receipt: Path, out_dir: Path) -> dict:
    acq = json.loads(Path(acq_receipt).read_text())
    coh = json.loads(Path(cohort_receipt).read_text())

    observed = sha256_file(h5_path)
    if acq.get("sha256") != observed:
        raise FailClosed("FAIL__MATRIX_DIGEST_DOES_NOT_MATCH_ACQUISITION_RECEIPT",
                         receipt_sha256=acq.get("sha256"), observed_sha256=observed)
    if not str(acq.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__ACQUISITION_RECEIPT_IS_NOT_PASS",
                         acquisition_status=acq.get("status"))

    out_dir.mkdir(parents=True, exist_ok=True)
    populations = {}

    with h5py.File(h5_path, "r") as h:
        g = h["matrix"]
        n_feat, n_cells = (int(x) for x in g["shape"][:])
        barcodes = _dec(g["barcodes"][:])
        if len(set(barcodes)) != len(barcodes):
            raise FailClosed("FAIL__MATRIX_BARCODES_NOT_UNIQUE",
                             n_barcodes=len(barcodes), n_unique=len(set(barcodes)))
        fg = g["features"]
        f_id = _dec(fg["id"][:])
        f_name = _dec(fg["name"][:])
        f_type = _dec(fg["feature_type"][:])
        f_genome = _dec(fg["genome"][:])
        f_interval = _dec(fg["interval"][:]) if "interval" in fg else np.array(
            ["UNMEASURED"] * n_feat, dtype=object)

        builds = sorted(set(f_genome.tolist()))
        if len(builds) != 1:
            raise FailClosed("FAIL__MULTIPLE_OR_ABSENT_GENOME_BUILDS", builds=builds)
        genome_build = builds[0]

        rna_rows = np.flatnonzero(f_type == "Gene Expression")
        peak_rows = np.flatnonzero(f_type == "Peaks")
        if rna_rows.size == 0 or peak_rows.size == 0:
            raise FailClosed("FAIL__MATRIX_IS_NOT_PAIRED_RNA_PLUS_PEAKS",
                             feature_types=sorted(set(f_type.tolist())))

        indptr = g["indptr"][:]
        pos = {b: i for i, b in enumerate(barcodes)}

        for pop_name, pop in coh["populations"].items():
            bc_df = pd.read_csv(pop["barcode_file"])
            want = bc_df["barcode"].astype(str).tolist()
            if ordered_digest(want) != pop["ordered_barcode_digest"]:
                raise FailClosed("FAIL__COHORT_BARCODE_FILE_ORDER_CHANGED",
                                 population=pop_name)
            missing = [b for b in want if b not in pos]
            if missing:
                raise FailClosed("FAIL__COHORT_BARCODES_ABSENT_FROM_MATRIX",
                                 population=pop_name, n_missing=len(missing),
                                 first_missing=missing[:5])

            cols = [pos[b] for b in want]
            data_parts, idx_parts, counts = [], [], []
            dset_d, dset_i = g["data"], g["indices"]
            for c in cols:
                a, b = int(indptr[c]), int(indptr[c + 1])
                data_parts.append(dset_d[a:b])
                idx_parts.append(dset_i[a:b])
                counts.append(b - a)
            dat = np.concatenate(data_parts) if data_parts else np.array([], dtype=np.int32)
            idx = np.concatenate(idx_parts) if idx_parts else np.array([], dtype=np.int32)
            ptr = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
            full = sparse.csc_matrix((dat, idx, ptr), shape=(n_feat, len(cols)))

            rec = {"population_id": pop_name, "n_cells": len(cols),
                   "n_donors": pop["n_donors"],
                   "ordered_barcode_digest": pop["ordered_barcode_digest"],
                   "modalities": {}}
            for mod, rows in (("RNA", rna_rows), ("ATAC_SUBMITTED_PEAKS", peak_rows)):
                sub = full[rows, :].tocsc()
                mp = out_dir / ("ROUTEA_%s_%s.npz" % (pop_name, mod))
                sparse.save_npz(mp, sub, compressed=True)
                fp = out_dir / ("ROUTEA_%s_features.csv.gz" % mod)
                if not fp.exists():
                    pd.DataFrame({
                        "row_index": np.arange(rows.size),
                        "matrix_feature_index": rows,
                        "id": f_id[rows], "name": f_name[rows],
                        "feature_type": f_type[rows], "genome": f_genome[rows],
                        "interval": f_interval[rows],
                    }).to_csv(fp, index=False, compression="gzip")
                n_cells_sub = sub.shape[1]
                detected_per_cell = np.diff(sub.indptr)
                rec["modalities"][mod] = {
                    "n_features": int(rows.size),
                    "n_cells": int(n_cells_sub),
                    "nnz": int(sub.nnz),
                    "total_counts": int(sub.data.sum()),
                    "matrix_path": str(mp),
                    "matrix_sha256": sha256_file(mp),
                    "feature_table_path": str(fp),
                    "feature_table_sha256": sha256_file(fp),
                    "ordered_feature_digest": ordered_digest(f_id[rows].tolist()),
                    "detected_features_per_cell": {
                        "min": int(detected_per_cell.min()),
                        "median": float(np.median(detected_per_cell)),
                        "max": int(detected_per_cell.max()),
                    },
                    "n_cells_with_zero_detected_features": int(
                        (detected_per_cell == 0).sum()),
                }
            populations[pop_name] = rec

    return {
        "schema": "V69_ROUTEA_SUBMITTED_PEAK_SUBSTRATE_V1",
        "network_version_reserved": "GSE214979_SCENICPLUS_SUBMITTED_PEAKS_V1",
        "built_utc": utcnow(),
        "source_matrix_path": str(h5_path),
        "source_matrix_sha256": observed,
        "source_acquisition_receipt": str(acq_receipt),
        "cohort_freeze_receipt": str(cohort_receipt),
        "cohort_metadata_sha256": coh["source_metadata_sha256"],
        "matrix_shape_features_by_cells": [n_feat, n_cells],
        "genome_build_declared_by_source": genome_build,
        "feature_type_counts": {"Gene Expression": int(rna_rows.size),
                                "Peaks": int(peak_rows.size)},
        "region_universe_provenance": (
            "SUBMITTED_BY_DEPOSITOR__NOT_RECONSTRUCTED. Route A accepts the peak set "
            "present in the filtered feature-barcode matrix as published. Route B "
            "independently reconstructs a region universe from the raw fragments."),
        "populations": populations,
        "status": "PASS__ROUTEA_SUBSTRATE_BUILT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5", required=True)
    ap.add_argument("--acquisition-receipt", required=True)
    ap.add_argument("--cohort-receipt", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    try:
        r = build(Path(a.h5), Path(a.acquisition_receipt), Path(a.cohort_receipt),
                  Path(a.out_dir))
    except FailClosed as e:
        r = {"schema": "V69_ROUTEA_SUBMITTED_PEAK_SUBSTRATE_V1",
             "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:5000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
