#!/usr/bin/env python3
"""Fail-closed corrected-TRAIN execution driver for V79 detection localization."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "v77"))

import v79_detection_localization as LOC  # noqa: E402
import run_v78_signed_detection_marginal_tournament as V78  # noqa: E402

SCHEMA_GATE = "V79_DETECTION_LOCALIZATION_PREEXECUTION_GATE_V1"
SCHEMA_CANONICAL = "V79_DETECTION_LOCALIZATION_CANONICAL_V1"
SCHEMA_SENSITIVITY = "V79_DETECTION_LOCALIZATION_SENSITIVITY_V1"
SCHEMA_RULING = "V79_DETECTION_LOCALIZATION_RULING_V1"

RECEIPT_FILENAMES = {
    "gate": "V79_DETECTION_LOCALIZATION_PREEXECUTION_GATE_V1.json",
    "canonical": "V79_DETECTION_LOCALIZATION_CANONICAL_V1.json",
    "sensitivity": "V79_DETECTION_LOCALIZATION_SENSITIVITY_V1.json",
    "ruling": "V79_DETECTION_LOCALIZATION_RULING_V1.json",
}

ALLOWED_MECHANISM_FAMILIES = {
    "RICHER_BIOLOGICAL_MIXTURE",
    "COUPLED_DEPTH_CAPTURE_OBSERVER",
    "PHYSICALLY_INTERPRETABLE_OBSERVATION_OPERATOR",
    "PRESERVE_DONOR_LINKED_BIOLOGY",
    "RICHER_WITHIN_STATE_BIOLOGY",
    "FACTORIAL_BIOLOGY_X_OBSERVATION_TOURNAMENT",
}


def preexecution_gate(e2_reference, operator_bridge, marginal_authority, corrected_cache_root) -> dict:
    base = V78.preexecution_gate(e2_reference, operator_bridge, marginal_authority, corrected_cache_root)
    blockers: list[str] = []
    if base.get("status") != "READY" or base.get("blockers"):
        blockers.append("v78_custody_gate")
    details = base.get("details", {})
    e2 = details.get("e2_reference", {})
    if e2.get("evaluation_universe_sha256") != V78.EXPECTED_EVALUATION_UNIVERSE_SHA256:
        blockers.append("evaluation_universe_mismatch")
    if e2.get("class_authority_sha256") != V78.EXPECTED_CLASS_AUTHORITY_SHA256:
        blockers.append("class_authority_mismatch")
    marginal = details.get("marginal_authority", {})
    if base.get("training_authorized") is True or marginal.get("training_authorized") is True:
        blockers.append("training_authorization_contamination")
    blockers = sorted(set(blockers))
    return {
        "schema": SCHEMA_GATE,
        "status": "READY" if not blockers else "BLOCKED",
        "blockers": blockers,
        "v78_gate": base,
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "synthetic_arm_promoted": None,
    }


def require_execution_authority(gate: dict) -> None:
    if gate.get("status") != "READY" or gate.get("blockers"):
        raise PermissionError("V79 localization blocked: " + ", ".join(gate.get("blockers", [])))
    if gate.get("training_authorized") is True:
        raise PermissionError("V79 localization cannot consume a training-authorized gate")


def _binary_selected(counts, universe, selected_positions) -> np.ndarray:
    X = counts.tocsr() if sparse.issparse(counts) else sparse.csr_matrix(np.asarray(counts))
    sub = (X[:, np.asarray(universe, dtype=np.int64)] > 0).astype(np.float64)
    return np.asarray(sub[:, np.asarray(selected_positions, dtype=np.int64)].todense())


def _supported_l2_cell_strata(counts, universe, broad_class, selected_positions) -> np.ndarray:
    X = counts.tocsr() if sparse.issparse(counts) else sparse.csr_matrix(np.asarray(counts))
    universe = np.asarray(universe, dtype=np.int64)
    broad_class = np.asarray(broad_class).astype(str)
    H = _binary_selected(X, universe, selected_positions)
    detected = np.asarray((X[:, universe] > 0).sum(1)).ravel().astype(np.float64)
    out = np.full(X.shape[0], "", dtype=object)
    for cls in sorted(np.unique(broad_class).tolist()):
        cix = np.flatnonzero(broad_class == cls)
        bins = LOC.quantile_depth_bins(detected[cix])
        if not bins["supported"]:
            continue
        labels = np.asarray(bins["labels"], dtype=np.int64)
        for b in range(int(bins["n_bins"])):
            ix = cix[labels == b]
            rec = LOC._corr_from_binary(H[ix])
            support = LOC.support_status(len(ix), rec["variable_gene_count"])
            if support["supported"]:
                out[ix] = f"{cls}|detbin{b}of{bins['n_bins']}"
    return out.astype(str)


def _realized_l3_cell_strata(H, base_strata, operator_labels, source_labels) -> np.ndarray:
    H = np.asarray(H, dtype=np.float64)
    base = np.asarray(base_strata).astype(str)
    op = np.asarray(operator_labels).astype(str)
    src = np.asarray(source_labels).astype(str)
    out = np.full(len(base), "", dtype=object)
    for b in sorted(x for x in np.unique(base).tolist() if x):
        bix = np.flatnonzero(base == b)
        unsupported: dict[str, list[int]] = {}
        for operator in sorted(np.unique(op[bix]).tolist()):
            ix = bix[op[bix] == operator]
            sources = np.unique(src[ix])
            if len(sources) != 1:
                continue
            rec = LOC._corr_from_binary(H[ix])
            status = LOC.support_status(len(ix), rec["variable_gene_count"])
            if status["supported"]:
                out[ix] = f"{b}|operator:{operator}"
            else:
                unsupported.setdefault(str(sources[0]), []).extend(ix.tolist())
        for source, indices in sorted(unsupported.items()):
            ix = np.asarray(indices, dtype=np.int64)
            rec = LOC._corr_from_binary(H[ix])
            status = LOC.support_status(len(ix), rec["variable_gene_count"])
            if status["supported"]:
                out[ix] = f"{b}|source:{source}"
    return out.astype(str)


def _selection_receipt(selection: dict) -> dict:
    selected = np.asarray(selection["selected_universe_ids"], dtype=np.int64)
    return {
        "selection_rule": selection["selection_rule"],
        "n_hvg_requested": int(selection["n_hvg_requested"]),
        "n_selected": int(selection["n_selected"]),
        "selected_ids_sha256": hashlib.sha256(selected.tobytes()).hexdigest(),
        "selected_ids_exported": False,
    }


def _support_rows(view: dict) -> list[dict]:
    rows = []
    for row in view.get("strata", []):
        keep = {k: v for k, v in row.items() if k not in {"corr", "summary"}}
        rows.append(keep)
    return rows


def _canonical_level(view: dict) -> dict:
    return {
        "summary": view.get("summary"),
        "n_supported_strata": int(view.get("n_supported_strata", 0)),
        "strata": _support_rows(view),
    }


def mechanism_ruling(localization: dict) -> dict:
    observed = {}
    families = []
    level_specs = [
        ("L0", localization.get("L0"), None),
        ("L1", localization.get("L1"), "RICHER_BIOLOGICAL_MIXTURE"),
        ("L2", localization.get("L2", {}).get("primary"), "COUPLED_DEPTH_CAPTURE_OBSERVER"),
        ("L3", localization.get("L3"), "PHYSICALLY_INTERPRETABLE_OBSERVATION_OPERATOR"),
        ("L4", localization.get("L4"), "PRESERVE_DONOR_LINKED_BIOLOGY"),
    ]
    for name, view, family in level_specs:
        if not isinstance(view, dict):
            continue
        summary = view.get("summary")
        if summary is None:
            continue
        observed[name] = {
            "pos_over_neg_ratio_0p30": summary.get("canonical", {}).get("pos_over_neg_ratio"),
            "negative_fraction_0p30": summary.get("canonical", {}).get("frac_neg_lt_m0p3"),
            "positive_fraction_0p30": summary.get("canonical", {}).get("frac_pos_gt_0p3"),
        }
        if family is not None:
            families.append(family)
    l5 = localization.get("L5", {})
    can = l5.get("thresholds", {}).get("0.30", {}) if isinstance(l5, dict) else {}
    if can.get("persistent_negative_count", 0) > 0:
        families.append("RICHER_WITHIN_STATE_BIOLOGY")
    if len(set(families)) > 1:
        families.append("FACTORIAL_BIOLOGY_X_OBSERVATION_TOURNAMENT")
    if not families:
        families = ["FACTORIAL_BIOLOGY_X_OBSERVATION_TOURNAMENT"]
    families = [f for f in dict.fromkeys(families) if f in ALLOWED_MECHANISM_FAMILIES]
    return {
        "schema": SCHEMA_RULING,
        "status": "DESCRIPTIVE_ONLY__NO_BAYESIAN_UNCERTAINTY_AUTHORITY",
        "observed_localization_path": observed,
        "candidate_mechanism_families": families,
        "unique_causal_winner_claimed": False,
        "interpretation": "Mechanism families remain prospective candidates; attenuation magnitudes are descriptive, not significance gates.",
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "synthetic_arm_promoted": None,
    }


def _jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_jsonable(payload), indent=2, allow_nan=False) + "\n")
    os.replace(tmp, path)


def run_localization(counts, universe, broad_class, source_labels, operator_labels, donor_labels,
                     gate_receipt: dict, n_hvg: int = 3000, output_dir: Path | None = None) -> dict:
    require_execution_authority(gate_receipt)
    X = counts.tocsr() if sparse.issparse(counts) else sparse.csr_matrix(np.asarray(counts))
    universe = np.asarray(universe, dtype=np.int64)
    broad_class = np.asarray(broad_class).astype(str)
    source_labels = np.asarray(source_labels).astype(str)
    operator_labels = np.asarray(operator_labels).astype(str)
    donor_labels = np.asarray(donor_labels).astype(str)
    n = X.shape[0]
    if any(len(v) != n for v in (broad_class, source_labels, operator_labels, donor_labels)):
        raise ValueError("all localization metadata must align one-to-one with count rows")

    l0l2 = LOC.build_l0_l2(X, universe, broad_class, n_hvg=int(n_hvg), retain_stratum_corr=False)
    sel = np.asarray(l0l2["selection"]["selected_positions"], dtype=np.int64)
    H = _binary_selected(X, universe, sel)
    base = _supported_l2_cell_strata(X, universe, broad_class, sel)
    mask3 = base != ""
    if mask3.any():
        l3 = LOC.localize_operator_source(H[mask3], base[mask3], operator_labels[mask3], source_labels[mask3],
                                         retain_stratum_corr=False)
        realized3 = _realized_l3_cell_strata(H[mask3], base[mask3], operator_labels[mask3], source_labels[mask3])
        mask4_local = realized3 != ""
        l4 = LOC.localize_donor(H[mask3][mask4_local], realized3[mask4_local], donor_labels[mask3][mask4_local],
                                retain_stratum_corr=False) if mask4_local.any() else {
                                    "interpretation": "BIOLOGICAL_OR_AMBIGUOUS", "strata": [], "combined_corr": None,
                                    "summary": None, "n_supported_strata": 0}
    else:
        l3 = {"strata": [], "combined_corr": None, "summary": None, "n_supported_strata": 0,
              "fallback_rule": "unsupported_operator_cells_by_authenticated_source_within_base_stratum_only"}
        l4 = {"interpretation": "BIOLOGICAL_OR_AMBIGUOUS", "strata": [], "combined_corr": None,
              "summary": None, "n_supported_strata": 0}

    l5 = LOC.aggregate_residual_persistence({
        "L1": l0l2["L1"], "L2": l0l2["L2"]["primary"], "L3": l3, "L4": l4,
    })
    localization = {"L0": l0l2["L0"], "L1": l0l2["L1"], "L2": l0l2["L2"], "L3": l3, "L4": l4, "L5": l5}
    ruling = mechanism_ruling(localization)

    canonical = {
        "schema": SCHEMA_CANONICAL,
        "claim_class": "TRAIN_ONLY_LOCALIZATION__NON_PROMOTING",
        "selection": _selection_receipt(l0l2["selection"]),
        "L0": {"summary": l0l2["L0"]["summary"], "n_cells": l0l2["L0"]["n_cells"],
               "variable_gene_count": l0l2["L0"]["variable_gene_count"],
               "constant_gene_count": l0l2["L0"]["constant_gene_count"]},
        "L1": _canonical_level(l0l2["L1"]),
        "L2": _canonical_level(l0l2["L2"]["primary"]),
        "L3": _canonical_level(l3),
        "L4": {**_canonical_level(l4), "interpretation": "BIOLOGICAL_OR_AMBIGUOUS"},
        "L5": l5,
        "canonical_threshold": LOC.CANONICAL_THRESHOLD,
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "synthetic_arm_promoted": None,
    }
    sensitivity = {
        "schema": SCHEMA_SENSITIVITY,
        "claim_class": "DESCRIPTIVE_SENSITIVITY_ONLY",
        "library_depth_L2": _canonical_level(l0l2["L2"]["sensitivity"]),
        "thresholds": list(LOC.SENSITIVITY_THRESHOLDS),
        "L5_threshold_sweep": l5.get("thresholds", {}),
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "synthetic_arm_promoted": None,
    }
    result = {"gate": gate_receipt, "canonical": canonical, "sensitivity": sensitivity, "ruling": ruling}
    if output_dir is not None:
        out = Path(output_dir)
        for key, filename in RECEIPT_FILENAMES.items():
            _atomic_json(out / filename, result[key])
    return result


def load_corrected_train(cache_root: Path, operator_bridge_path: Path):
    cache_root = Path(cache_root)
    bridge = json.loads(Path(operator_bridge_path).read_text())
    blocks = []
    broad, donor, source, operator = [], [], [], []
    for row in sorted(bridge.get("rows", []), key=lambda r: int(r["operator_index"])):
        stem = str(row["stem"])
        op = str(int(row["operator_index"]))
        src = str(row["source"])
        cp = cache_root / f"{stem}.counts.npz"
        mp = cache_root / f"{stem}.meta.npz"
        if not cp.is_file() or not mp.is_file():
            raise FileNotFoundError(f"authenticated shard pair unavailable for {stem}")
        X = sparse.load_npz(cp).tocsr()
        meta = np.load(mp, allow_pickle=False)
        required = ("broad_cell_class", "donor_id", "cell_id", "source_library")
        if any(k not in meta.files for k in required):
            raise RuntimeError(f"repaired meta missing required fields for {stem}")
        if any(len(meta[k]) != X.shape[0] for k in required):
            raise RuntimeError(f"repaired meta/count row mismatch for {stem}")
        blocks.append(X)
        broad.extend(meta["broad_cell_class"].astype(str).tolist())
        donor.extend(meta["donor_id"].astype(str).tolist())
        source.extend([src] * X.shape[0])
        operator.extend([op] * X.shape[0])
    if not blocks:
        raise RuntimeError("operator bridge contains no shard rows")
    return (sparse.vstack(blocks, format="csr"), np.asarray(broad), np.asarray(source),
            np.asarray(operator), np.asarray(donor))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2-reference", required=True)
    ap.add_argument("--operator-bridge", required=True)
    ap.add_argument("--marginal-authority", required=True)
    ap.add_argument("--corrected-cache-root", required=True)
    ap.add_argument("--evaluation-universe-npz", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    gate = preexecution_gate(a.e2_reference, a.operator_bridge, a.marginal_authority, a.corrected_cache_root)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    _atomic_json(out / RECEIPT_FILENAMES["gate"], gate)
    require_execution_authority(gate)
    X, cls, src, op, donor = load_corrected_train(Path(a.corrected_cache_root), Path(a.operator_bridge))
    with np.load(a.evaluation_universe_npz, allow_pickle=False) as z:
        universe = np.asarray(z["evaluation_universe"], dtype=np.int64)
    run_localization(X, universe, cls, src, op, donor, gate, output_dir=out)


if __name__ == "__main__":
    main()
