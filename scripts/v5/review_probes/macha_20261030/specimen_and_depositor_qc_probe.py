"""Donor/specimen hierarchy and depositor-QC support (metadata only; aggregates only).

usage: python -I specimen_and_depositor_qc_probe.py <repo-root> > out.json

Reads, for reader_fit rows only (index-selected inside each H5AD column, so other
partitions' rows are never materialized):
  - SEA-AD: Donor ID, Brain Region, sample_id, exp_component_name, method,
    cell_prep_type, Number of UMIs, Genes detected, Fraction mitochondrial UMIs
    (all on the project allowlist) and Doublet score (depositor QC; not on the
    analytic allowlist, not on the forbidden list);
  - HVS: donor_id, tissue, suspension_type, assay, exp_component_name, the three QC
    columns (allowlist) and is_primary_data (CELLxGENE curation flag; not on the
    allowlist, not forbidden);
  - per-cell source_library from the FULL104 Level-4 block metadata (a library
    total; no gene-level value) for the depositor-UMI comparison.
Never reads pathology/disease columns, count matrices, quarantined NPH52 cells,
reader_validation/oracle rows, DEV or SEALED data. Emits no donor or sample IDs.
"""
import glob
import json
import os
import sys

import h5py
import numpy as np
import pandas as pd

ROOT = sys.argv[1].rstrip("/") + "/"
F104 = ROOT + "outputs/full104_v014_20260826/"
FORBIDDEN = {"disease", "disease_ontology_term_id", "Neurotypical reference", "Overall AD neuropathological Change",
             "Thal", "Braak", "CERAD score", "Cognitive Status", "APOE Genotype", "Severely Affected Donor",
             "Highest Lewy Body Disease", "LATE", "Atherosclerosis", "Arteriolosclerosis"}
COLUMNS = {
    "SEA_AD": ["Donor ID", "Brain Region", "sample_id", "exp_component_name", "method", "cell_prep_type",
               "Number of UMIs", "Genes detected", "Fraction mitochondrial UMIs", "Doublet score"],
    "HVS": ["donor_id", "tissue", "suspension_type", "assay", "exp_component_name", "Number of UMIs",
            "Genes detected", "Fraction mitochrondrial UMIs", "is_primary_data"],
}
assert not FORBIDDEN & {c for cols in COLUMNS.values() for c in cols}


def read_rows(obs, key, rows):
    """Values of one obs column at the given sorted row indices only."""
    if key not in obs:
        return None
    node = obs[key]
    if isinstance(node, h5py.Group) and "codes" in node:
        codes = node["codes"][rows]
        cats = node["categories"][:]
        cats = np.array([c.decode() if isinstance(c, bytes) else c for c in cats], dtype=object)
        out = np.empty(len(codes), dtype=object)
        valid = codes >= 0
        out[valid] = cats[codes[valid]]
        out[~valid] = None
        return out
    values = node[rows]
    if values.dtype.kind in ("S", "O"):
        return np.array([v.decode() if isinstance(v, bytes) else v for v in values], dtype=object)
    return values


def q(series, probs=(0.0, 0.001, 0.5, 0.999, 1.0)):
    s = pd.to_numeric(pd.Series(series), errors="coerce").dropna()
    return {f"p{p:g}": float(s.quantile(p)) for p in probs} | {"n": int(len(s))}


lineage = pd.concat(pd.read_csv(f, dtype=str, usecols=["source", "operator_index", "matrix_id", "donor_id",
                                                       "canonical_cell_id", "source_row", "reader_partition"])
                    for f in sorted(glob.glob(F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/*.csv.gz")))
assert set(lineage.reader_partition) == {"reader_fit"}
assets = pd.read_csv(ROOT + "results/v4/stage81a2_canonical_asset_registry.csv", dtype=str).set_index("dataset_id")

# Level-4 per-cell library totals, keyed by (operator, canonical_cell_id).
library = {}
for meta in glob.glob(F104 + "03_phase2_state_derivation_v1/expression_level4/blocks/op*/block-*.meta.csv"):
    op = int(os.path.basename(os.path.dirname(meta))[2:])
    frame = pd.read_csv(meta, dtype={"canonical_cell_id": str}, usecols=["canonical_cell_id", "source_library"])
    for cid, lib in zip(frame.canonical_cell_id, pd.to_numeric(frame.source_library, errors="coerce")):
        library[(op, cid)] = lib

frames = {}
for source in ("SEA_AD", "HVS"):
    parts = []
    for matrix_id, group in lineage[lineage.source.eq(source)].groupby("matrix_id"):
        rows = np.sort(group.source_row.astype(np.int64).to_numpy())
        order = group.assign(_r=group.source_row.astype(np.int64)).sort_values("_r")
        with h5py.File(ROOT + assets.loc[matrix_id, "matrix_path_or_object"], "r") as handle:
            data = {c: read_rows(handle["obs"], c, rows) for c in COLUMNS[source]}
        frame = pd.DataFrame({c: v for c, v in data.items() if v is not None})
        frame["matrix_id"] = matrix_id
        frame["lineage_donor"] = order.donor_id.to_numpy()
        frame["operator_index"] = order.operator_index.astype(int).to_numpy()
        frame["canonical_cell_id"] = order.canonical_cell_id.to_numpy()
        frame["missing_columns"] = ",".join(c for c, v in data.items() if v is None)
        parts.append(frame)
    frames[source] = pd.concat(parts, ignore_index=True)


def nesting(frame, donor, region, sample):
    f = frame.copy()
    f["library"] = f.exp_component_name.astype(str).str.split("-", n=1).str[1]
    out = {"cells": int(len(f)), "donors": int(f[donor].nunique()), "matrices": int(f.matrix_id.nunique()),
           "donor_column_equals_lineage_donor": bool((f[donor].astype(str) == f.lineage_donor.astype(str)).all()),
           "missing_columns_by_matrix": sorted({m for m in f.missing_columns if m})}
    if region:
        out["region_values"] = sorted(f[region].dropna().astype(str).unique().tolist())
        out["regions_per_matrix_max"] = int(f.groupby("matrix_id")[region].nunique().max())
    if sample and sample in f:
        s = f[f[sample].notna()]
        out["sample_id_missing_cells"] = int(f[sample].isna().sum())
        out["sample_id_missing_by_matrix"] = {m: int(v) for m, v in f[f[sample].isna()].groupby("matrix_id").size().items()}
        out["sample_id_distinct_values"] = int(s[sample].nunique())
        out["sample_id_cells_with_value"] = int(len(s))
        out["sample_id_is_unique_per_cell"] = bool(s[sample].nunique() == len(s))
    # Library token: exp_component_name after the cell barcode ("L<n>TX_<date>_<plate>_<well>-<number>").
    # It names a 10x reaction; the meaning of the trailing number is not documented here.
    lib = f[f.library.notna() & f.library.ne("nan")]
    per_lib = lib.groupby("library")[donor].nunique()
    out["libraries_total"] = int(lib.library.nunique())
    out["libraries_with_more_than_one_donor"] = int((per_lib > 1).sum())
    out["libraries_with_more_than_one_matrix"] = int((lib.groupby("library").matrix_id.nunique() > 1).sum())
    if region:
        out["libraries_with_more_than_one_region"] = int((lib.groupby("library")[region].nunique() > 1).sum())
        per_dr = lib.groupby([donor, region]).library.nunique()
        out["libraries_per_donor_region"] = {"median": float(per_dr.median()), "max": int(per_dr.max()),
                                             "donor_regions": int(len(per_dr)),
                                             "donor_regions_with_more_than_one_library": int((per_dr > 1).sum())}
    per_donor = lib.groupby(donor).library.nunique()
    out["libraries_per_donor"] = {"median": float(per_donor.median()), "max": int(per_donor.max())}
    out["cell_keys_in_more_than_one_matrix"] = int((f.groupby("exp_component_name").matrix_id.nunique() > 1).sum())
    return out


def at_floor(values):
    """Cells sitting exactly at the observed minimum, whose inclusion can flip on one gene or molecule."""
    v = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    floor = float(v.min())
    return {"floor": floor, "cells_at_floor": int((v == floor).sum()),
            "cells_within_1pct_of_floor": int((v <= floor * 1.01).sum()), "cells": int(len(v))}


def qc(frame, mito):
    f = frame
    ours = np.array([library.get((op, cid), np.nan) for op, cid in zip(f.operator_index, f.canonical_cell_id)])
    theirs = pd.to_numeric(f["Number of UMIs"], errors="coerce").to_numpy()
    both = ~np.isnan(ours) & ~np.isnan(theirs)
    ratio = ours[both] / theirs[both]
    return {"genes_detected_floor": at_floor(f["Genes detected"]), "number_of_umis_floor": at_floor(f["Number of UMIs"]),
            "number_of_umis": q(f["Number of UMIs"]), "genes_detected": q(f["Genes detected"]),
            "fraction_mitochondrial": q(f[mito]), "doublet_score": q(f["Doublet score"]) if "Doublet score" in f else None,
            "is_primary_data": {str(k): int(v) for k, v in f["is_primary_data"].value_counts(dropna=False).items()}
            if "is_primary_data" in f else None,
            "level4_library_matched_cells": int(both.sum()),
            "level4_library_equals_depositor_umis": int((ours[both] == theirs[both]).sum()),
            "level4_library_over_depositor_umis": q(ratio)}


nph = lineage[lineage.source.eq("NPH52")]
nph_lib = np.array([library.get((int(op), cid), np.nan) for op, cid in zip(nph.operator_index, nph.canonical_cell_id)])
out = {
    "schema": "JEPA_MACHA_SPECIMEN_AND_DEPOSITOR_QC_PROBE_V1",
    "level4_library_cells_indexed": len(library),
    "SEA_AD": {"nesting": nesting(frames["SEA_AD"], "Donor ID", "Brain Region", "sample_id"),
               "qc": qc(frames["SEA_AD"], "Fraction mitochondrial UMIs"),
               "method": {str(k): int(v) for k, v in frames["SEA_AD"].method.value_counts(dropna=False).items()},
               "cell_prep_type": {str(k): int(v) for k, v in frames["SEA_AD"].cell_prep_type.value_counts(dropna=False).items()}},
    "HVS": {"nesting": nesting(frames["HVS"], "donor_id", None, None),
            "qc": qc(frames["HVS"], "Fraction mitochrondrial UMIs"),
            "tissue": {str(k): int(v) for k, v in frames["HVS"].tissue.value_counts(dropna=False).items()},
            "suspension_type": {str(k): int(v) for k, v in frames["HVS"].suspension_type.value_counts(dropna=False).items()},
            "assay": {str(k): int(v) for k, v in frames["HVS"].assay.value_counts(dropna=False).items()}},
    "NPH52_retained_reader_fit_only": {"cells": int(len(nph)), "donors": int(nph.donor_id.nunique()),
                                       "level4_library": q(nph_lib[~np.isnan(nph_lib)]),
                                       "level4_library_floor": at_floor(nph_lib[~np.isnan(nph_lib)]),
                                       "quarantined_cells_read": 0},
}
print(json.dumps(out, indent=1, sort_keys=True, default=str))
