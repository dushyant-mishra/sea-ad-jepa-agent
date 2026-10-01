#!/usr/bin/env python3
"""V69 Route A: build the pycisTopic object from the frozen submitted-peak substrate.

Runs INSIDE the validated SCENIC+ container.

This is the ATAC side of Route A. It takes the already-frozen cell x region count
matrix (built from the depositor's submitted peaks, for the frozen cohort) and wraps
it as a cisTopic object with donor and published-subcluster annotations attached, so
that every downstream step can stratify by DONOR -- the replication unit -- rather
than by nucleus.

Deliberately NOT done here:
  * no QC filtering of cells. The cohort is already frozen, and re-filtering cells
    here would make the Route-A cell set differ from the frozen one and from Route B,
    turning a region-universe comparison into a cell-selection comparison.
  * no pathology covariate is attached. Only donor, published subcluster, and the
    technical covariates needed for stratification.

Fails closed if the matrix does not reconcile with the frozen receipt.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

FORBIDDEN_COVARIATES = ("Status", "Braak", "Diagnosis", "APOE_Status")


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


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def remap(p: str, host_prefix: str, container_prefix: str) -> Path:
    """Translate a host path recorded in a receipt to its bind-mounted location.

    Receipts record the absolute HOST path at which an artifact actually lived, which
    is the honest provenance record and is deliberately not rewritten. A producer
    running inside a container sees that artifact at a different mount point, so the
    translation is applied here, explicitly, and recorded in the output receipt -- it
    is never done by silently editing the source receipt.
    """
    if not host_prefix:
        return Path(p)
    n = p.replace("\\", "/")
    h = host_prefix.replace("\\", "/").rstrip("/")
    if n.lower().startswith(h.lower()):
        return Path(container_prefix.rstrip("/") + n[len(h):])
    return Path(p)


def build(routea_receipt: Path, cohort_receipt: Path, population: str,
          out_dir: Path, host_prefix: str = "", container_prefix: str = "") -> dict:
    def R(p):
        return remap(str(p), host_prefix, container_prefix)
    ra = json.loads(routea_receipt.read_text())
    coh = json.loads(cohort_receipt.read_text())
    if not str(ra.get("status", "")).startswith("PASS"):
        raise FailClosed("FAIL__ROUTEA_RECEIPT_IS_NOT_PASS", status=ra.get("status"))

    pop = ra["populations"][population]
    atac = pop["modalities"]["ATAC_SUBMITTED_PEAKS"]

    mpath = R(atac["matrix_path"])
    if sha256_file(mpath) != atac["matrix_sha256"]:
        raise FailClosed("FAIL__ATAC_MATRIX_DIGEST_MISMATCH", path=str(mpath))

    mat = sparse.load_npz(mpath).tocsr()          # regions x cells
    feats = pd.read_csv(R(atac["feature_table_path"]))
    bc = pd.read_csv(R(coh["populations"][population]["barcode_file"]))

    if mat.shape[0] != len(feats) or mat.shape[1] != len(bc):
        raise FailClosed("FAIL__MATRIX_SHAPE_DOES_NOT_RECONCILE",
                         matrix_shape=list(mat.shape),
                         n_features=int(len(feats)), n_cells=int(len(bc)))

    leaked = [c for c in FORBIDDEN_COVARIATES if c in bc.columns]
    if leaked:
        raise FailClosed("FAIL__PATHOLOGY_COLUMN_PRESENT_IN_CELL_ANNOTATION",
                         columns=leaked)

    cell_data = pd.DataFrame({
        "barcode": bc["barcode"].astype(str),
        "donor": bc["donor"].astype(str),
        "published_subcluster": bc["subcluster"].astype(str),
    }).set_index("barcode")
    cell_data["n_regions_detected"] = np.asarray((mat > 0).sum(axis=0)).ravel()
    cell_data["total_counts_in_peaks"] = np.asarray(mat.sum(axis=0)).ravel()

    region_names = feats["id"].astype(str).tolist()
    region_detect = np.asarray((mat > 0).sum(axis=1)).ravel()

    out_dir.mkdir(parents=True, exist_ok=True)
    obj = {
        "schema": "V69_ROUTEA_CISTOPIC_INPUT_V1",
        "population": population,
        "region_names": region_names,
        "cell_names": cell_data.index.tolist(),
        "cell_data": cell_data,
        "count_matrix_regions_by_cells": mat,
    }
    p = out_dir / ("V69_ROUTEA_CISTOPIC_INPUT_%s.pkl" % population)
    with open(p, "wb") as fh:
        pickle.dump(obj, fh, protocol=4)

    return {
        "schema": "V69_ROUTEA_CISTOPIC_INPUT_RECEIPT_V1",
        "built_utc": utcnow(),
        "population": population,
        "source_matrix_sha256": atac["matrix_sha256"],
        "n_regions": int(mat.shape[0]),
        "n_cells": int(mat.shape[1]),
        "n_donors": int(cell_data["donor"].nunique()),
        "cells_per_donor": {k: int(v) for k, v in
                            cell_data["donor"].value_counts().sort_index().items()},
        "subclusters": {k: int(v) for k, v in
                        cell_data["published_subcluster"].value_counts()
                        .sort_index().items()},
        "nnz": int(mat.nnz),
        "regions_detected_in_zero_cells": int((region_detect == 0).sum()),
        "regions_detected_in_at_least_one_cell": int((region_detect > 0).sum()),
        "cells_with_zero_regions": int((cell_data["n_regions_detected"] == 0).sum()),
        "detected_regions_per_cell": {
            "min": int(cell_data["n_regions_detected"].min()),
            "median": float(cell_data["n_regions_detected"].median()),
            "max": int(cell_data["n_regions_detected"].max()),
        },
        "no_cell_qc_applied_here": (
            "The cohort is already frozen. Re-filtering cells here would make the "
            "Route-A cell set differ from the frozen set and from Route B, converting "
            "a region-universe comparison into a cell-selection comparison."),
        "pathology_covariates_attached": [],
        "pathology_blindness_check": "PASS__NO_FORBIDDEN_COLUMN_IN_CELL_ANNOTATION",
        "output_path": str(p),
        "output_sha256": sha256_file(p),
        "path_remapping": {
            "applied": bool(host_prefix),
            "host_prefix": host_prefix or None,
            "container_prefix": container_prefix or None,
            "note": ("Receipts record the absolute HOST path where each artifact "
                     "actually lived; that is the honest provenance record and is "
                     "never rewritten. A producer running inside a container sees the "
                     "same bytes at a different mount point, so the translation is "
                     "applied at read time and recorded here."),
        },
        "status": "PASS__CISTOPIC_INPUT_BUILT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--routea-receipt", required=True)
    ap.add_argument("--cohort-receipt", required=True)
    ap.add_argument("--population", default="DEV_NO_MORABITO_OVERLAP")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--host-prefix", default="",
                    help="Host path prefix recorded in the input receipts, e.g. "
                         "D:/jepa_v5_outputs_20260925/v69_scenicplus")
    ap.add_argument("--container-prefix", default="",
                    help="Where that prefix is mounted here, e.g. /data")
    a = ap.parse_args(argv)
    try:
        r = build(Path(a.routea_receipt), Path(a.cohort_receipt), a.population,
                  Path(a.out_dir), a.host_prefix, a.container_prefix)
    except FailClosed as e:
        r = {"schema": "V69_ROUTEA_CISTOPIC_INPUT_RECEIPT_V1",
             "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:4000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
