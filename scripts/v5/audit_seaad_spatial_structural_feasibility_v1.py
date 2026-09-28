"""Lane R4: structural feasibility audit of SEA-AD public spatial resources.

STRUCTURAL ONLY.  TRAINING=OFF.  No biological claim is produced or permitted.

All ``obs`` access routes through ``seaad_spatial_pathology_firewall_v1``; the
expression matrix ``X`` is never read.  Gene identity is read from ``var``
(panel membership is a property of the assay design, not of any donor).

Writes a machine-readable artifact to the lane output directory.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from collections import Counter

import h5py
import numpy as np

_HERE = pathlib.Path(__file__).resolve()
_FW_PATH = _HERE.parent / "seaad_spatial_pathology_firewall_v1.py"
_spec = importlib.util.spec_from_file_location("seaad_spatial_firewall", _FW_PATH)
fw = importlib.util.module_from_spec(_spec)
sys.modules["seaad_spatial_firewall"] = fw
_spec.loader.exec_module(fw)

OUT_DIR = pathlib.Path(r"D:/jepa_v5_outputs_20260925/out_seaad-spatial")

ASSETS = {
    "MTG_MERFISH": {
        "path": r"D:/Jepa project/data/external/v4/sea_ad/merfish/SEAAD_MTG_MERFISH.2024-12-11.h5ad",
        "public_url": "https://sea-ad-spatial-transcriptomics.s3.amazonaws.com/middle-temporal-gyrus/combined_anndata_object/SEAAD_MTG_MERFISH.2024-12-11.h5ad",
        "assay": "MERFISH (Vizgen MERSCOPE)",
        "region": "MTG (middle temporal gyrus)",
        "release": "2024-12-11",
        "recorded_sha256": "3e3dac22446a8ce66afd07c209cd74df260b2f3d7c4085ffe4732390d2054a24",
        "celltype_cols": ["Class", "Subclass", "Supertype"],
        "donor_col": "Donor ID",
        "section_col": "Section",
    },
    "HIP_MERSCOPE": {
        "path": r"D:/Jepa project/data/external/v4/sea_ad/merfish/1444211893_HPF_mapped.h5ad",
        "public_url": "https://sea-ad-spatial-transcriptomics.s3.amazonaws.com/hippocampus/combined_anndata_object/1444211893_HPF_mapped.h5ad",
        "assay": "MERSCOPE",
        "region": "HIP (hippocampus)",
        "release": "2026-06-30",
        "recorded_sha256": "0136fbb0650646b6b0e3d4d8759ea29c52d92f17ca5846600fbf24fbd4cb4f21",
        "celltype_cols": ["Class_scANVI", "Subclass_scANVI", "Supertype_scANVI"],
        "donor_col": None,
        "section_col": None,
    },
    "MEC_MERSCOPE": {
        "path": r"D:/Jepa project/data/external/v4/sea_ad/merfish/1444201261_MEC_mapped.h5ad",
        "public_url": "https://sea-ad-spatial-transcriptomics.s3.amazonaws.com/medial-entorhinal-cortex/combined_anndata_object/1444201261_MEC_mapped.h5ad",
        "assay": "MERSCOPE",
        "region": "MEC (medial entorhinal cortex)",
        "release": "2026-06-30",
        "recorded_sha256": "612cc24bb15e82c74fa9ef3f9710f355defbb03f7037ba8520b3a71f1674fca8",
        "celltype_cols": ["Class_scANVI", "Subclass_scANVI", "Supertype_scANVI"],
        "donor_col": None,
        "section_col": None,
    },
    "CaH_XENIUM": {
        "path": r"D:/Jepa project/data/external/v4/sea_ad/xenium/CaH_Xenium.2026-01-07.h5ad",
        "public_url": "https://sea-ad-spatial-transcriptomics.s3.amazonaws.com/caudate_nucleus/combined_anndata_object/CaH_Xenium.2026-01-07.h5ad",
        "assay": "Xenium (10x Genomics)",
        "region": "CaH (caudate nucleus)",
        "release": "2026-01-07",
        "recorded_sha256": "8ab8eac92946f55e26aace7f20c8e56027704e3f0bdd92f2609e1a843271432a",
        "celltype_cols": ["Subclass", "Supertype"],
        "donor_col": "Donor ID",
        "section_col": None,
    },
}

PROGRAMS = {
    "homeostatic": ["P2RY12", "TMEM119", "CX3CR1", "GPR34", "SALL1"],
    "lipid_DAM": ["APOE", "LPL", "GPNMB", "TREM2", "APOC1", "ABCA1"],
    "antigen_presentation": [
        "HLA-DRA", "HLA-DPA1", "HLA-DMB", "HLA-DMA", "CD74", "CTSS", "IFI30",
    ],
}

MICROGLIA_TOKENS = ("microglia", "micro-pvm", "micro_pvm", "micro/pvm", "pvm")


def read_var_index(path: str) -> list[str]:
    with h5py.File(path, "r") as f:
        idx = f["var"].attrs.get("_index")
        idx = idx.decode() if isinstance(idx, bytes) else idx
        vals = f["var"][idx][...]
    return [v.decode() if isinstance(v, bytes) else str(v) for v in vals]


def n_obs(path: str) -> int:
    with h5py.File(path, "r") as f:
        idx = f["obs"].attrs.get("_index")
        idx = idx.decode() if isinstance(idx, bytes) else idx
        node = f["obs"][idx]
        if isinstance(node, h5py.Group):
            return int(node["codes"].shape[0])
        return int(node.shape[0])


def numeric_summary_by_group(path, value_col, group_vals, group_name):
    """Median/mean of an allow-listed numeric QC column within a cell group.

    Technical measurement-process quantities only (segmentation geometry and
    transcript counters).  No biological quantity is summarised.
    """
    verdict, _ = fw.classify_column(value_col)
    if verdict != "ALLOW":
        raise fw.PathologyFirewallViolation(f"{value_col} not allow-listed")
    with h5py.File(path, "r") as f:
        if value_col not in f["obs"]:
            return None
        node = f["obs"][value_col]
        if isinstance(node, h5py.Group):
            return None
        vals = node[...].astype("float64")
    mask = group_vals == group_name
    if mask.sum() == 0:
        return None
    sel = vals[mask]
    oth = vals[~mask]
    return {
        "n_in_group": int(mask.sum()),
        "median_in_group": float(np.nanmedian(sel)),
        "median_all_other_cells": float(np.nanmedian(oth)),
        "ratio_group_over_other": (
            float(np.nanmedian(sel) / np.nanmedian(oth))
            if np.nanmedian(oth) not in (0.0, np.nan)
            else None
        ),
    }


def audit_asset(key: str, spec: dict) -> dict:
    path = spec["path"]
    rec: dict = {
        "asset_key": key,
        "assay": spec["assay"],
        "region": spec["region"],
        "release": spec["release"],
        "local_path": path,
        "public_url": spec["public_url"],
        "recorded_sha256_stage81a1b": spec["recorded_sha256"],
        "file_size_bytes": pathlib.Path(path).stat().st_size,
    }

    # ---- column-name screen (existence only; no values read) -------------
    with h5py.File(path, "r") as f:
        obs_cols = [c for c in f["obs"].keys()]
    screened = fw.screen_columns(obs_cols)
    rec["obs_column_screen"] = {
        "n_total": len(obs_cols),
        "protected_columns_present_names_only": sorted(screened["PROTECTED"]),
        "n_protected": len(screened["PROTECTED"]),
        "demographic_columns_present_names_only": sorted(screened["DENY_NOT_NEEDED"]),
        "allow_listed": sorted(screened["ALLOW"]),
        "refused_unknown": sorted(screened["REFUSED_UNKNOWN"]),
    }
    rec["protected_pathology_in_same_table"] = len(screened["PROTECTED"]) > 0
    rec["protected_values_read"] = False

    # ---- panel ------------------------------------------------------------
    genes = read_var_index(path)
    upper = {g.upper(): g for g in genes}
    rec["n_features_in_object"] = len(genes)
    rec["n_cells"] = n_obs(path)

    panel_hits = {}
    for prog, glist in PROGRAMS.items():
        present = [g for g in glist if g.upper() in upper]
        absent = [g for g in glist if g.upper() not in upper]
        panel_hits[prog] = {
            "n_total": len(glist),
            "n_present": len(present),
            "present": present,
            "absent": absent,
            "fraction_present": round(len(present) / len(glist), 4),
        }
    rec["program_panel_representation"] = panel_hits
    rec["gene_panel"] = sorted(genes)

    # ---- allow-listed obs -------------------------------------------------
    want = [c for c in spec["celltype_cols"] if c in obs_cols]
    if spec["donor_col"] and spec["donor_col"] in obs_cols:
        want.append(spec["donor_col"])
    if spec["section_col"] and spec["section_col"] in obs_cols:
        want.append(spec["section_col"])
    for extra in ("segmentation_method", "region", "Brain Region"):
        if extra in obs_cols:
            want.append(extra)

    frame = fw.load_allowlisted_obs(path, want)
    rec["obs_columns_actually_read"] = list(frame.columns)

    if spec["donor_col"] and spec["donor_col"] in frame:
        donors = sorted({str(d) for d in frame[spec["donor_col"]] if d is not None})
        rec["donor_id_column"] = spec["donor_col"]
        rec["n_donors"] = len(donors)
        rec["donor_ids"] = donors
    else:
        rec["donor_id_column"] = None
        rec["n_donors"] = 0
        rec["donor_ids"] = []
        rec["donor_linkage_note"] = (
            "No donor identifier column is present in the public object; "
            "donor identity is NOT recoverable from this file alone."
        )

    if spec["section_col"] and spec["section_col"] in frame:
        rec["n_sections"] = int(frame[spec["section_col"]].nunique())
    else:
        rec["n_sections"] = None

    for c in ("segmentation_method", "region", "Brain Region"):
        if c in frame:
            rec[f"values_{c}"] = sorted({str(v) for v in frame[c].unique()})[:20]

    # ---- cell-type annotation + microglia count ---------------------------
    ct = {}
    micro_total = None
    micro_label_used = None
    micro_col_used = None
    for col in spec["celltype_cols"]:
        if col not in frame:
            continue
        vals = frame[col].astype(str).values
        counts = Counter(vals)
        ct[col] = {
            "n_labels": len(counts),
            "labels": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        }
        micro_labels = [
            lbl for lbl in counts
            if any(t in lbl.lower() for t in MICROGLIA_TOKENS)
        ]
        if micro_labels and micro_total is None:
            micro_total = int(sum(counts[m] for m in micro_labels))
            micro_label_used = micro_labels
            micro_col_used = col
    rec["cell_type_annotations"] = ct
    rec["microglia_label_column"] = micro_col_used
    rec["microglia_labels_matched"] = micro_label_used
    rec["n_microglia"] = micro_total
    rec["microglia_fraction"] = (
        round(micro_total / rec["n_cells"], 5) if micro_total else None
    )

    # microglia per donor (identity-only aggregation)
    if micro_col_used and rec["donor_ids"]:
        dcol = spec["donor_col"]
        vals = frame[micro_col_used].astype(str).values
        mmask = np.array([
            any(t in v.lower() for t in MICROGLIA_TOKENS) for v in vals
        ])
        dser = frame[dcol].astype(str).values
        per = Counter(dser[mmask])
        rec["microglia_per_donor"] = dict(sorted(per.items()))
        rec["microglia_per_donor_min"] = int(min(per.values())) if per else 0
        rec["microglia_per_donor_median"] = (
            float(np.median(list(per.values()))) if per else 0
        )
        rec["n_donors_with_microglia"] = len(per)

    # ---- segmentation-geometry comparison (technical only) ----------------
    if micro_col_used:
        vals = frame[micro_col_used].astype(str).values
        seg = {}
        for qc_col in (
            "cell_area", "nucleus_area", "Cell volume",
            "transcript_counts", "total_counts",
            "Genes detected", "Number of spots", "nucleus_count",
        ):
            if qc_col not in obs_cols:
                continue
            mmask_names = [
                lbl for lbl in set(vals)
                if any(t in lbl.lower() for t in MICROGLIA_TOKENS)
            ]
            if not mmask_names:
                continue
            grp = np.isin(vals, mmask_names)
            verdict, _ = fw.classify_column(qc_col)
            if verdict != "ALLOW":
                continue
            with h5py.File(path, "r") as f:
                node = f["obs"][qc_col]
                if isinstance(node, h5py.Group):
                    continue
                arr = node[...].astype("float64")
            seg[qc_col] = {
                "microglia_median": float(np.nanmedian(arr[grp])),
                "other_cells_median": float(np.nanmedian(arr[~grp])),
                "ratio_microglia_over_other": (
                    float(np.nanmedian(arr[grp]) / np.nanmedian(arr[~grp]))
                    if np.nanmedian(arr[~grp]) else None
                ),
            }
        rec["segmentation_geometry_microglia_vs_other"] = seg

    return rec


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for key, spec in ASSETS.items():
        print(f"[audit] {key} ...", flush=True)
        results[key] = audit_asset(key, spec)

    payload = {
        "schema": "JEPA_LANE_R4_SEAAD_SPATIAL_STRUCTURAL_FEASIBILITY_V1",
        "date": "2026-09-28",
        "training": "OFF",
        "scope": "STRUCTURAL_FEASIBILITY_ONLY__NO_BIOLOGICAL_CLAIM",
        "protected_outcomes_opened": False,
        "programs_checked": PROGRAMS,
        "assets": results,
    }
    out = OUT_DIR / "SEAAD_SPATIAL_STRUCTURAL_AUDIT_V1.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"[written] {out}")
    print(f"[sha256] {hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
