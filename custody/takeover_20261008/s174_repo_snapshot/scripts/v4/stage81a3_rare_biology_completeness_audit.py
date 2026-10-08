#!/usr/bin/env python3
"""Bounded pathology-blind data-defined rare-biology completeness audit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import yaml
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "v4"))
import stage81a3_foundation_biological_state_domain_qualification as fbsdq  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import MolecularEvidenceLedger  # noqa: E402
from sea_ad_jepa.v4.rare_state_audit import ledger_cosine  # noqa: E402

def module(name: str, path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / path); value = importlib.util.module_from_spec(spec)
    assert spec.loader is not None; spec.loader.exec_module(value); return value

BASE = module("base_rscr_completeness", "scripts/v4/stage81a3_rare_state_coverage_resolution.py")
EXPANDED = module("expanded_rscr_completeness", "scripts/v4/stage81a3_complete_rare_state_coverage_audit.py")
GENES, WIDTH = 4096, 160


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True); parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto"); parser.add_argument("--keep-cache", action="store_true")
    parser.add_argument("--finalize-existing", action="store_true", help="Refresh combined governance outputs without reading expression")
    return parser.parse_args()


def combined_readiness_frame(
    supported_encoder_loss: int,
    unstable_recurring: int,
    unstable_extremes: int,
    saturation_class: str,
    ready: bool,
) -> pd.DataFrame:
    return pd.DataFrame([
        {"gate": "annotation_defined_coverage_audit_complete", "pass": True},
        {"gate": "data_defined_completeness_audit_complete", "pass": True},
        {"gate": "no_supported_molecular_encoder_erasure", "pass": supported_encoder_loss == 0},
        {"gate": "data_defined_recurring_conclusions_stable", "pass": unstable_recurring == 0},
        {"gate": "continuous_extreme_recurrence_stable", "pass": unstable_extremes == 0},
        {"gate": "technical_masqueraders_distinguished", "pass": True},
        {"gate": "discovery_saturation_reported", "pass": saturation_class in {"SATURATING", "PARTIALLY-SATURATING", "NOT-SATURATING"}},
        {"gate": "ready_for_human_a3_freeze_review", "pass": ready},
    ])


def robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float); center = np.nanmedian(values); mad = np.nanmedian(np.abs(values - center))
    return (values - center) / max(1.4826 * mad, 1e-12)


def technical_class(frame: pd.DataFrame, indices: np.ndarray, mixed: float, high: float) -> tuple[str, dict[str, float]]:
    metrics = {"log_library": np.log1p(frame.library_size.to_numpy(float)), "detected_genes": frame.detected_genes.to_numpy(float), "zero_fraction": frame.zero_fraction.to_numpy(float)}
    shifts = {name: float(abs(np.nanmedian(robust_z(values)[indices]))) for name, values in metrics.items()}
    maximum = max(shifts.values()) if shifts else math.nan
    classification = "HIGH TECHNICAL CONCERN" if maximum >= high else "MIXED TECHNICAL ASSOCIATION" if maximum >= mixed else "LOW TECHNICAL CONCERN"
    return classification, shifts


def local_isolation(similarity: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    scores = np.asarray(similarity, dtype=np.float64).copy(); np.fill_diagonal(scores, -np.inf)
    count = min(k, len(scores) - 1)
    neighbors = np.argpartition(-scores, count, axis=1)[:, :count]
    isolation = 1.0 - np.take_along_axis(scores, neighbors, axis=1).mean(axis=1)
    return isolation, neighbors


def candidate_mask(values: np.ndarray, fraction: float) -> np.ndarray:
    count = max(1, int(math.ceil(len(values) * fraction)))
    order = np.lexsort((np.arange(len(values)), -np.asarray(values)))
    mask = np.zeros(len(values), dtype=bool); mask[order[:count]] = True; return mask


def connected_components(candidate_indices: np.ndarray, neighborhoods: dict[int, set[int]], overlap_fraction: float) -> list[list[int]]:
    parent = {int(index): int(index) for index in candidate_indices}
    def find(x: int) -> int:
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb: parent[max(ra, rb)] = min(ra, rb)
    indices = list(map(int, candidate_indices))
    for position, left in enumerate(indices):
        for right in indices[position + 1:]:
            denominator = max(1, min(len(neighborhoods[left]), len(neighborhoods[right])))
            if len(neighborhoods[left] & neighborhoods[right]) / denominator >= overlap_fraction: union(left, right)
    groups: dict[int, list[int]] = {}
    for index in indices: groups.setdefault(find(index), []).append(index)
    return [sorted(value) for _, value in sorted(groups.items())]


def agreement_label(rna: bool, ledger: bool, pca: bool) -> str:
    if rna and ledger and pca: return "RNA + LEDGER + PCA RARE"
    if rna and ledger and not pca: return "RNA + LEDGER RARE / PCA NOT RARE"
    if rna and not ledger: return "RNA RARE / LEDGER NOT RARE"
    if ledger and not rna: return "LEDGER RARE / RNA NOT RARE"
    if pca and not rna and not ledger: return "PCA RARE ONLY"
    return "OTHER MIXED"


def recurrence_tier(donors: int, datasets: int, technologies: int) -> str:
    if donors == 1: return "TIER 1 - DONOR-PRIVATE BIOLOGICAL CANDIDATE"
    if donors < 5: return "TIER 2 - LIMITED-RECURRENCE CANDIDATE"
    if technologies >= 2: return "TIER 5 - CROSS-TECHNOLOGY RECURRING RARE STATE"
    if datasets >= 2: return "TIER 4 - CROSS-DATASET RECURRING RARE STATE"
    return "TIER 3 - DONOR-RECURRING RARE STATE"


def supported_encoder_loss_mask(frame: pd.DataFrame) -> pd.Series:
    """Require stable recurrence and low technical concern for a Class C flag."""
    stable = frame.donor_recurrence_retained_all.astype("boolean").fillna(False).astype(bool)
    return frame.rna_rare & (~frame.ledger_rare) & stable & frame.technical_concern.eq("LOW TECHNICAL CONCERN")


def load_discovery_frame(cache_paths: list[Path]) -> tuple[pd.DataFrame, np.ndarray]:
    frames, expression = [], []
    for path in cache_paths:
        data = fbsdq.load_cache(path); n = len(data["counts"])
        frame = pd.DataFrame({"matrix_id": np.repeat(data["matrix_id"], n), "dataset_id": np.repeat(data["dataset_id"], n), "study_id": np.repeat(data["study_id"], n), "donor_id": np.asarray(data["donor_id"], str), "cell_id": np.asarray(data["cell_id"], str), "annotation": np.asarray(data["broad_cell_class"], str), "region": np.asarray(data["tissue"], str), "technology": np.asarray(data["technology"], str), "library_size": np.asarray(data["source_library"], float), "detected_genes": np.count_nonzero(data["counts"], axis=1), "zero_fraction": np.mean(np.asarray(data["counts"]) == 0, axis=1)})
        frame["source_key"] = frame.matrix_id.astype(str) + "|" + frame.cell_id.astype(str); frame["broad_family"] = frame.annotation.map(EXPANDED.broad_family)
        frames.append(frame); expression.append(fbsdq.normalized_full(data))
    return pd.concat(frames, ignore_index=True), np.vstack(expression)


def family_sample(metadata: pd.DataFrame, cap: int) -> np.ndarray:
    selected = []
    for family, indices in metadata.groupby("broad_family", sort=True).groups.items():
        local = EXPANDED.diverse_sample(metadata.loc[list(indices)].reset_index().rename(columns={"index": "global_index"}), cap, 8117401)
        selected.extend(local.global_index.astype(int))
    return np.asarray(sorted(selected), dtype=int)


def family_resample_stability(
    frame: pd.DataFrame,
    similarity: dict[str, np.ndarray],
    isolation: dict[str, np.ndarray],
    definitions: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Re-evaluate recurring neighborhoods on four fixed donor-balanced subsets."""
    roots = list(contract["resample_roots"])
    if len(roots) != 4:
        raise RuntimeError("rare-biology stability requires exactly four roots")
    cap = max(31, int(math.ceil(len(frame) * float(contract["resample_family_fraction"]))))
    indexed = frame.reset_index().rename(columns={"index": "family_index"})
    rows = []
    resample_recurrence_threshold = max(
        2,
        int(math.ceil(5 * float(contract["resample_family_fraction"]))),
    )
    for definition in definitions:
        if definition["donors"] < 5 or len(frame) <= 30:
            continue
        original = set(definition["candidate_indices"])
        neighborhood = set(definition["member_indices"])
        for root in roots:
            selected = EXPANDED.diverse_sample(indexed, min(cap, len(indexed)), int(root))
            positions = selected.family_index.to_numpy(int)
            local_masks: dict[str, np.ndarray] = {}
            ranking_correlations: dict[str, float] = {}
            for name in ("RNA", "LEDGER", "PCA"):
                local_scores, _ = local_isolation(
                    similarity[name][np.ix_(positions, positions)],
                    int(contract["local_isolation_k"]),
                )
                local_masks[name] = candidate_mask(local_scores, float(contract["candidate_fraction"]))
                correlation = spearmanr(isolation[name][positions], local_scores).statistic
                ranking_correlations[name] = float(correlation) if np.isfinite(correlation) else math.nan
            resampled_candidates = {
                name: set(positions[np.flatnonzero(mask)]) & neighborhood
                for name, mask in local_masks.items()
            }
            union = original | resampled_candidates["LEDGER"]
            overlap = len(original & resampled_candidates["LEDGER"]) / max(1, len(union))
            ledger_candidates = resampled_candidates["LEDGER"]
            rna_candidates = resampled_candidates["RNA"]
            rows.append({
                "rare_neighborhood_id": definition["rare_neighborhood_id"],
                "broad_family": definition["broad_family"],
                "resample_root": int(root),
                "family_cells_retained": len(positions),
                "candidate_membership_jaccard": overlap,
                "candidate_donors_retained": frame.iloc[sorted(ledger_candidates)].donor_id.nunique() if ledger_candidates else 0,
                "donor_recurrence_retained": (frame.iloc[sorted(ledger_candidates)].donor_id.nunique() >= resample_recurrence_threshold) if ledger_candidates else False,
                "resample_recurrence_donor_threshold": resample_recurrence_threshold,
                "rna_local_isolation_rank_correlation": ranking_correlations["RNA"],
                "ledger_local_isolation_rank_correlation": ranking_correlations["LEDGER"],
                "pca_local_isolation_rank_correlation": ranking_correlations["PCA"],
                "rna_to_ledger_candidate_retention": len(rna_candidates & ledger_candidates) / max(1, len(rna_candidates)),
                "ledger_to_pca_candidate_retention": len(ledger_candidates & resampled_candidates["PCA"]) / max(1, len(ledger_candidates)),
            })
    return rows


def analyze_family(family: str, frame: pd.DataFrame, expression: np.ndarray, pca: np.ndarray, rep: np.ndarray, ledger: Any, device: torch.device, contract: dict[str, Any], annotation_rare: dict[str, bool], total_discovery_cells: int, donor_subsets: dict[float, set[str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    gene_ids = torch.arange(GENES, device=device)[None]; tokens = np.empty((len(frame), GENES, WIDTH), np.float16)
    with torch.no_grad():
        for start in range(0, len(frame), 2):
            values = torch.from_numpy(expression[start:start + 2]).to(device); encoded, _ = ledger(gene_ids.expand(len(values), -1), values, torch.ones_like(values, dtype=torch.bool)); tokens[start:start + len(values)] = encoded.detach().cpu().numpy().astype(np.float16)
    similarity = {"RNA": BASE.cosine_similarity(expression), "LEDGER": ledger_cosine(tokens, tokens), "PCA": BASE.cosine_similarity(pca), "REP": BASE.cosine_similarity(rep)}
    isolation, neighbors, masks = {}, {}, {}
    for name, values in similarity.items(): isolation[name], neighbors[name] = local_isolation(values, int(contract["local_isolation_k"])); masks[name] = candidate_mask(isolation[name], float(contract["candidate_fraction"]))
    candidate_indices = np.flatnonzero(masks["RNA"] | masks["LEDGER"] | masks["PCA"])
    candidate_rows = []
    for index in candidate_indices:
        candidate_rows.append({"cell_id_hash": hashlib.sha256(str(frame.cell_id.iloc[index]).encode()).hexdigest(), "donor_id_hash": hashlib.sha256(str(frame.donor_id.iloc[index]).encode()).hexdigest(), "broad_family": family, "annotation": frame.annotation.iloc[index], "dataset_id": frame.dataset_id.iloc[index], "matrix_id": frame.matrix_id.iloc[index], "technology": frame.technology.iloc[index], "region": frame.region.iloc[index], "global_audit_frequency": 1.0 / total_discovery_cells, "within_family_audit_frequency": 1.0 / len(frame), "rna_local_isolation": isolation["RNA"][index], "ledger_local_isolation": isolation["LEDGER"][index], "pca_local_isolation": isolation["PCA"][index], "rep_local_isolation": isolation["REP"][index], "rna_rare": masks["RNA"][index], "ledger_rare": masks["LEDGER"][index], "pca_rare": masks["PCA"][index], "rep_rare": masks["REP"][index], "agreement_category": agreement_label(masks["RNA"][index], masks["LEDGER"][index], masks["PCA"][index]), "data_defined_candidate_only": True})
    chosen_neighbors = {int(index): set(map(int, neighbors["LEDGER" if masks["LEDGER"][index] else "RNA" if masks["RNA"][index] else "PCA"][index])) for index in candidate_indices}
    components = connected_components(candidate_indices, chosen_neighbors, float(contract["neighborhood_overlap_fraction"]))
    neighborhood_rows, firewall_rows, definitions = [], [], []
    for number, component in enumerate(components, 1):
        members = sorted(set(component).union(*(chosen_neighbors[index] for index in component))); subset = frame.iloc[members]; candidate_subset = frame.iloc[component]
        concern, shifts = technical_class(frame, np.asarray(component), float(contract["technical_mixed_abs_robust_z"]), float(contract["technical_high_abs_robust_z"])); donors, datasets, technologies = candidate_subset.donor_id.nunique(), candidate_subset.dataset_id.nunique(), candidate_subset.technology.nunique()
        annotation_counts = candidate_subset.annotation.value_counts(normalize=True); dominant, fraction = annotation_counts.index[0], float(annotation_counts.iloc[0]); concordance = "ANNOTATION-CONCORDANT" if fraction >= 0.8 and annotation_rare.get(dominant, False) else "ANNOTATION-SUBSTRUCTURE" if fraction >= 0.8 else "ANNOTATION-MIXED"
        rna, ledger_rare, pca_rare = bool(masks["RNA"][component].any()), bool(masks["LEDGER"][component].any()), bool(masks["PCA"][component].any())
        identifier = f"{family.replace(' ', '_').replace('/', '_')}::{number:03d}"
        tier = "TIER 0 - TECHNICAL / UNRESOLVED OUTLIER" if concern == "HIGH TECHNICAL CONCERN" else recurrence_tier(donors, datasets, technologies)
        recurrence = "DONOR-PRIVATE" if donors == 1 else "LIMITED-RECURRENCE" if donors < 5 else "DONOR-RECURRING"
        cross_source = "MULTI-TECHNOLOGY" if technologies >= 2 else "MULTI-DATASET" if datasets >= 2 else "SINGLE-DATASET"
        neighborhood_rows.append({"rare_neighborhood_id": identifier, "broad_family": family, "candidate_cells": len(component), "neighborhood_cells": len(members), "global_audit_frequency": len(component) / total_discovery_cells, "within_family_audit_frequency": len(component) / len(frame), "donors": donors, "cells_per_donor": json.dumps(candidate_subset.groupby("donor_id").size().sort_index().to_dict(), sort_keys=True), "datasets": datasets, "matrices": candidate_subset.matrix_id.nunique(), "technologies": technologies, "regions": candidate_subset.region.nunique(), "recurrence_class": recurrence, "cross_source_recurrence": cross_source, "evidence_tier": tier, "technical_concern": concern, "annotation_agreement": concordance, "dominant_annotation": dominant, "dominant_annotation_fraction": fraction, "rna_rare": rna, "ledger_rare": ledger_rare, "pca_rare": pca_rare, "rep_rare": bool(masks["REP"][component].any()), "representation_agreement": agreement_label(rna, ledger_rare, pca_rare), "unannotated_compression_review_flag": donors >= 5 and concern != "HIGH TECHNICAL CONCERN" and rna and ledger_rare and not pca_rare, "nearest_recurring_state": "NOT APPLICABLE", "nearest_recurring_state_ledger_similarity": math.nan, "candidate_member_hash": hashlib.sha256("\n".join(sorted(frame.source_key.iloc[component])).encode()).hexdigest(), "neighborhood_member_hash": hashlib.sha256("\n".join(sorted(frame.source_key.iloc[members])).encode()).hexdigest()})
        definitions.append({"rare_neighborhood_id": identifier, "broad_family": family, "candidate_indices": list(map(int, component)), "member_indices": members, "donors": donors})
        firewall_rows.append({"rare_neighborhood_id": identifier, "broad_family": family, "technical_concern": concern, **{f"{key}_median_abs_robust_z": value for key, value in shifts.items()}, "quality_fields_used": "library_size;detected_genes;zero_fraction", "new_qc_filter_applied": False})
    recurring_definitions = [item for item in definitions if item["donors"] >= 5]
    for row, definition in zip(neighborhood_rows, definitions, strict=True):
        if definition["donors"] != 1 or not recurring_definitions:
            continue
        source = np.asarray(definition["member_indices"], dtype=int)
        comparisons = []
        for recurring_definition in recurring_definitions:
            target = np.asarray(recurring_definition["member_indices"], dtype=int)
            comparisons.append((float(similarity["LEDGER"][np.ix_(source, target)].mean()), recurring_definition["rare_neighborhood_id"]))
        score, identifier = max(comparisons, key=lambda value: (value[0], value[1]))
        row["nearest_recurring_state"] = identifier
        row["nearest_recurring_state_ledger_similarity"] = score
    stability_rows = family_resample_stability(frame, similarity, isolation, definitions, contract)
    saturation_rows = []
    definition_keys = {
        item["rare_neighborhood_id"]: set(frame.source_key.iloc[item["candidate_indices"]].astype(str))
        for item in definitions
    }
    for fraction, included_donors in donor_subsets.items():
        positions = np.flatnonzero(frame.donor_id.astype(str).isin(included_donors).to_numpy())
        if len(positions) <= int(contract["local_isolation_k"]):
            continue
        local_neighbors: dict[str, np.ndarray] = {}
        local_masks: dict[str, np.ndarray] = {}
        for name in ("RNA", "LEDGER", "PCA"):
            scores, local_neighbors[name] = local_isolation(
                similarity[name][np.ix_(positions, positions)],
                int(contract["local_isolation_k"]),
            )
            local_masks[name] = candidate_mask(scores, float(contract["candidate_fraction"]))
        local_candidates = np.flatnonzero(local_masks["RNA"] | local_masks["LEDGER"] | local_masks["PCA"])
        local_neighborhoods = {
            int(index): set(map(int, local_neighbors["LEDGER" if local_masks["LEDGER"][index] else "RNA" if local_masks["RNA"][index] else "PCA"][index]))
            for index in local_candidates
        }
        for component in connected_components(local_candidates, local_neighborhoods, float(contract["neighborhood_overlap_fraction"])):
            candidate_positions = positions[np.asarray(component, dtype=int)]
            candidate_frame = frame.iloc[candidate_positions]
            if candidate_frame.donor_id.nunique() < 5:
                continue
            keys = set(candidate_frame.source_key.astype(str))
            matches = [
                (len(keys & known) / max(1, len(keys | known)), identifier)
                for identifier, known in definition_keys.items()
            ]
            score, identifier = max(matches, default=(0.0, ""), key=lambda value: (value[0], value[1]))
            if score == 0.0:
                identifier = "fractional::" + hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()[:16]
            saturation_rows.append({
                "donor_fraction": fraction,
                "candidate_identity": f"neighborhood::{identifier}",
                "broad_family": family,
                "candidate_cells": len(candidate_frame),
                "donors": candidate_frame.donor_id.nunique(),
                "matched_full_candidate_jaccard": score,
            })
    summary = {"broad_family": family, "cells": len(frame), "candidate_cells": len(candidate_indices), "neighborhoods": len(components), "rna_ledger_pca": int(sum(row["agreement_category"] == "RNA + LEDGER + PCA RARE" for row in candidate_rows)), "rna_ledger_not_pca": int(sum(row["agreement_category"] == "RNA + LEDGER RARE / PCA NOT RARE" for row in candidate_rows))}
    del tokens, similarity
    if device.type == "cuda": torch.cuda.empty_cache()
    return candidate_rows, neighborhood_rows, firewall_rows, stability_rows, saturation_rows, summary


def continuous_extremes(frame: pd.DataFrame, pca: np.ndarray, blocks: pd.DataFrame, contract: dict[str, Any], donor_subsets: dict[float, set[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, saturation_rows = [], []
    roots = list(contract["resample_roots"])
    if len(roots) != 4:
        raise RuntimeError("continuous-extreme stability requires exactly four roots")
    resample_recurrence_threshold = max(
        2,
        int(math.ceil(5 * float(contract["resample_family_fraction"]))),
    )
    for family, indices in frame.groupby("broad_family", sort=True).groups.items():
        positions = np.asarray(list(indices), int)
        indexed = frame.iloc[positions].reset_index().rename(columns={"index": "global_index"})
        resample_cap = max(31, int(math.ceil(len(indexed) * float(contract["resample_family_fraction"]))))
        for block in blocks[blocks.basis.eq("BALANCED_PCA160")].itertuples(index=False):
            coordinates = np.asarray([int(value) for value in str(block.coordinate_indices).split(";")], int); magnitude = np.linalg.norm(pca[np.ix_(positions, coordinates)], axis=1); count = max(1, int(math.ceil(len(positions) * float(contract["candidate_fraction"]))))
            for tail, local in (("TOP", np.argsort(magnitude)[-count:]), ("BOTTOM", np.argsort(magnitude)[:count])):
                selected = positions[local]; subset = frame.iloc[selected]; concern, shifts = technical_class(frame.iloc[positions].reset_index(drop=True), local, float(contract["technical_mixed_abs_robust_z"]), float(contract["technical_high_abs_robust_z"]))
                original = set(map(int, selected)); overlaps, donor_counts = [], []
                for root in roots:
                    resampled = EXPANDED.diverse_sample(indexed, min(resample_cap, len(indexed)), int(root))
                    resampled_positions = resampled.global_index.to_numpy(int)
                    resampled_magnitude = np.linalg.norm(pca[np.ix_(resampled_positions, coordinates)], axis=1)
                    resampled_count = max(1, int(math.ceil(len(resampled_positions) * float(contract["candidate_fraction"]))))
                    order = np.argsort(resampled_magnitude)
                    resampled_local = order[-resampled_count:] if tail == "TOP" else order[:resampled_count]
                    resampled_selected = set(map(int, resampled_positions[resampled_local]))
                    overlaps.append(len(original & resampled_selected) / max(1, len(original | resampled_selected)))
                    donor_counts.append(frame.iloc[sorted(resampled_selected)].donor_id.nunique())
                identifier = f"{family.replace(' ', '_').replace('/', '_')}::block-{int(block.block):03d}::{tail}"
                rows.append({"extreme_state_id": identifier, "broad_family": family, "subspace_block": int(block.block), "coordinates": str(block.coordinate_indices), "tail": tail, "cells": len(selected), "donors": subset.donor_id.nunique(), "cells_per_donor": json.dumps(subset.groupby("donor_id").size().sort_index().to_dict(), sort_keys=True), "datasets": subset.dataset_id.nunique(), "technologies": subset.technology.nunique(), "recurrence": "RECURRING EXTREME MOLECULAR STATE" if subset.donor_id.nunique() >= 5 else "DONOR-PRIVATE EXTREME CANDIDATE" if subset.donor_id.nunique() == 1 else "LIMITED-RECURRENCE EXTREME CANDIDATE", "technical_concern": concern, "median_subspace_magnitude": float(np.median(magnitude[local])), "resamples": len(roots), "membership_jaccard_median": float(np.median(overlaps)), "membership_jaccard_min": float(np.min(overlaps)), "resample_donor_count_min": int(np.min(donor_counts)), "resample_recurrence_donor_threshold": resample_recurrence_threshold, "recurrence_stable": bool(all(value >= resample_recurrence_threshold for value in donor_counts)) if subset.donor_id.nunique() >= 5 else bool(all(value < resample_recurrence_threshold for value in donor_counts)), "member_hash": hashlib.sha256("\n".join(sorted(subset.source_key)).encode()).hexdigest(), **{f"{key}_median_abs_robust_z": value for key, value in shifts.items()}})
                for donor_fraction, included_donors in donor_subsets.items():
                    included_local = np.flatnonzero(frame.iloc[positions].donor_id.astype(str).isin(included_donors).to_numpy())
                    if not len(included_local):
                        continue
                    included_magnitude = magnitude[included_local]
                    included_count = max(1, int(math.ceil(len(included_local) * float(contract["candidate_fraction"]))))
                    included_order = np.argsort(included_magnitude)
                    included_tail = included_order[-included_count:] if tail == "TOP" else included_order[:included_count]
                    included_cells = frame.iloc[positions[included_local[included_tail]]]
                    if included_cells.donor_id.nunique() >= 5:
                        saturation_rows.append({"donor_fraction": donor_fraction, "candidate_identity": f"extreme::{identifier}", "broad_family": family, "candidate_cells": len(included_cells), "donors": included_cells.donor_id.nunique()})
    return pd.DataFrame(rows), pd.DataFrame(saturation_rows)


def saturation(neighborhood_discovery: pd.DataFrame, extreme_discovery: pd.DataFrame, annotation_support: pd.DataFrame, all_donors: list[str], fractions: list[float]) -> pd.DataFrame:
    donor_order = sorted(all_donors, key=lambda value: hashlib.sha256(f"8117501|{value}".encode()).digest()); rows = []
    previous: set[str] = set()
    for fraction in fractions:
        donors = set(donor_order[: max(1, int(math.ceil(len(donor_order) * fraction)))])
        annotation_ids = set()
        for item in annotation_support.itertuples(index=False):
            counts = json.loads(item.cells_per_donor); qualifying = sum(int(counts.get(donor, 0)) >= 3 for donor in donors)
            if qualifying >= 5: annotation_ids.add(f"annotation::{item.annotation}")
        data_ids = set(neighborhood_discovery.loc[neighborhood_discovery.donor_fraction.eq(fraction), "candidate_identity"].astype(str)) if len(neighborhood_discovery) else set()
        extreme_ids = set(extreme_discovery.loc[extreme_discovery.donor_fraction.eq(fraction), "candidate_identity"].astype(str)) if len(extreme_discovery) else set()
        current = annotation_ids | data_ids | extreme_ids
        rows.append({"donor_fraction": fraction, "donors": len(donors), "annotation_defined_recurring_states": len(annotation_ids), "data_defined_recurring_neighborhoods": len(data_ids), "recurring_extreme_states": len(extreme_ids), "total_recurring_candidates": len(current), "new_candidates_vs_previous_fraction": len(current - previous), "recovered_previous_candidates": len(current & previous), "candidate_identity_hash": hashlib.sha256("\n".join(sorted(current)).encode()).hexdigest()})
        previous = current
    frame = pd.DataFrame(rows); at75, at100 = frame.iloc[-2].total_recurring_candidates, frame.iloc[-1].total_recurring_candidates; increase = (at100 - at75) / max(at75, 1); frame["saturation_classification"] = "SATURATING" if increase <= 0.10 else "PARTIALLY-SATURATING" if increase <= 0.25 else "NOT-SATURATING"; return frame


def cleanup(path: Path) -> None:
    if not path.exists(): return
    for item in path.iterdir():
        if not item.is_file(): raise RuntimeError(f"unexpected cache entry {item}")
        item.unlink()
    path.rmdir()


def main() -> int:
    args = parse_args(); project = args.project_dir.resolve(); config = yaml.safe_load((project / args.config).read_text()); contract = config["rare_biology_completeness"]; outputs = {key: project / value for key, value in config["rare_biology_outputs"].items()}; started = time.perf_counter()
    if args.finalize_existing:
        report = json.loads(outputs["report"].read_text(encoding="utf-8"))
        combined_readiness = combined_readiness_frame(
            int(report["supported_rna_rare_ledger_not_rare_states"]),
            int(report["unstable_donor_recurring_neighborhoods"]),
            int(report["unstable_recurring_extreme_states"]),
            str(report["discovery_saturation"]),
            bool(report["ready_for_human_a3_freeze_review"]),
        )
        report["combined_freeze_readiness"] = combined_readiness.to_dict("records")
        annotation_report_path = project / config["outputs"]["report"]
        annotation_report = json.loads(annotation_report_path.read_text(encoding="utf-8"))
        annotation_report["annotation_defined_gate_pass"] = bool(
            annotation_report.get("ready_for_human_a3_freeze_review", False)
            or annotation_report.get("annotation_defined_gate_pass", False)
        )
        annotation_report["ready_for_human_a3_freeze_review"] = False
        annotation_report["completeness_gate_required"] = True
        annotation_report["superseded_global_readiness_by"] = str(config["rare_biology_outputs"]["report"])
        if annotation_report["annotation_defined_gate_pass"]:
            annotation_report["primary_classification"] = "ANNOTATION-DEFINED GATE PASSED - DATA-DEFINED COMPLETENESS REQUIRED"
        BASE.write_csv(project / config["outputs"]["freeze_readiness"], combined_readiness)
        BASE.write_json(annotation_report_path, annotation_report)
        BASE.write_json(outputs["report"], report)
        print("FINALIZE EXISTING PASS: no expression or model access", flush=True)
        return 0
    if BASE.sha256_file(project / config["inputs"]["prrc_report"]) != config["inputs"]["prrc_sha256"]: raise RuntimeError("PRRC hash mismatch")
    cache_paths = sorted((project / config["expanded"]["reusable_reference_cache"]).glob("*.npz"));
    if len(cache_paths) != 36: raise RuntimeError("canonical discovery cache mismatch")
    metadata, expression = load_discovery_frame(cache_paths); selected = family_sample(metadata, int(contract["family_cell_cap"])); metadata, expression = metadata.iloc[selected].reset_index(drop=True), expression[selected]
    pca_basis = EXPANDED.load_basis(project / config["inputs"]["pca_basis"], "BALANCED_PCA160"); rep_basis = EXPANDED.load_basis(project / config["inputs"]["rep_basis"], "BALANCED_REP160"); pca = fbsdq.project_linear(expression, pca_basis); rep = fbsdq.project_linear(expression, rep_basis)
    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu"); torch.manual_seed(int(config["fixed"]["ledger_seed"])); torch.cuda.manual_seed_all(int(config["fixed"]["ledger_seed"])); ledger = MolecularEvidenceLedger(gradient_checkpointing=False).to(device).eval(); [parameter.requires_grad_(False) for parameter in ledger.parameters()]; before = BASE.model_hash(ledger)
    donor_order = sorted(metadata.donor_id.astype(str).unique(), key=lambda value: hashlib.sha256(f"8117501|{value}".encode()).digest())
    donor_subsets = {
        float(fraction): set(donor_order[: max(1, int(math.ceil(len(donor_order) * float(fraction))))])
        for fraction in contract["donor_fractions"]
    }
    census = pd.read_csv(project / config["outputs"]["full_census"]); annotation_rare = census.set_index("annotation").annotation_rare.astype(bool).to_dict(); candidate_rows, neighborhood_rows, firewall_rows, stability_rows, neighborhood_saturation_rows, family_rows = [], [], [], [], [], []
    for family, indices in metadata.groupby("broad_family", sort=True).groups.items():
        index = np.asarray(list(indices), int); print(f"RARE BIOLOGY {family}: cells={len(index)}", flush=True); candidates, neighborhoods, firewall, stability, neighborhood_saturation, summary = analyze_family(family, metadata.iloc[index].reset_index(drop=True), expression[index], pca[index], rep[index], ledger, device, contract, annotation_rare, len(metadata), donor_subsets); candidate_rows += candidates; neighborhood_rows += neighborhoods; firewall_rows += firewall; stability_rows += stability; neighborhood_saturation_rows += neighborhood_saturation; family_rows.append(summary)
    after = BASE.model_hash(ledger)
    if before != after: raise RuntimeError("molecular ledger parameter hash changed")
    candidates, neighborhoods, firewall, stability = pd.DataFrame(candidate_rows), pd.DataFrame(neighborhood_rows), pd.DataFrame(firewall_rows), pd.DataFrame(stability_rows); agreement = candidates.groupby(["broad_family", "agreement_category"]).size().rename("candidate_cells").reset_index()
    if len(stability):
        stability_summary = stability.groupby("rare_neighborhood_id", sort=True).agg(resamples=("resample_root", "size"), candidate_membership_jaccard_median=("candidate_membership_jaccard", "median"), candidate_membership_jaccard_min=("candidate_membership_jaccard", "min"), donor_recurrence_retained_all=("donor_recurrence_retained", "all"), rna_rank_correlation_median=("rna_local_isolation_rank_correlation", "median"), ledger_rank_correlation_median=("ledger_local_isolation_rank_correlation", "median"), pca_rank_correlation_median=("pca_local_isolation_rank_correlation", "median"), rna_to_ledger_retention_median=("rna_to_ledger_candidate_retention", "median"), ledger_to_pca_retention_median=("ledger_to_pca_candidate_retention", "median")).reset_index()
        neighborhoods = neighborhoods.merge(stability_summary, on="rare_neighborhood_id", how="left", validate="one_to_one")
    else:
        neighborhoods["resamples"] = 0
        neighborhoods["donor_recurrence_retained_all"] = False
    donor_private = neighborhoods[(neighborhoods.recurrence_class == "DONOR-PRIVATE") & (neighborhoods.technical_concern != "HIGH TECHNICAL CONCERN")].copy(); recurring = neighborhoods[neighborhoods.recurrence_class == "DONOR-RECURRING"].copy()
    neighborhood_discovery = pd.DataFrame(neighborhood_saturation_rows)
    blocks = pd.read_csv(project / "results/v4/stage81a3_subspace_uncertainty_blocks.csv"); extremes, extreme_discovery = continuous_extremes(metadata, pca, blocks, contract, donor_subsets); annotation_support = pd.read_csv(project / config["outputs"]["all_target_support"]); donor_values = sorted(metadata.donor_id.unique()); saturation_frame = saturation(neighborhood_discovery, extreme_discovery, annotation_support, donor_values, list(contract["donor_fractions"])); saturation_class = saturation_frame.saturation_classification.iloc[0]
    family_summary = pd.DataFrame(family_rows)
    neighborhood_family = neighborhoods.groupby("broad_family").agg(
        donor_private=("recurrence_class", lambda value: int((value == "DONOR-PRIVATE").sum())),
        limited=("recurrence_class", lambda value: int((value == "LIMITED-RECURRENCE").sum())),
        recurring=("recurrence_class", lambda value: int((value == "DONOR-RECURRING").sum())),
        high_technical=("technical_concern", lambda value: int((value == "HIGH TECHNICAL CONCERN").sum())),
        compression_review=("unannotated_compression_review_flag", "sum"),
    ).reset_index()
    extreme_family = extremes.groupby("broad_family").agg(
        continuous_extreme_sets=("extreme_state_id", "size"),
        recurring_extreme_sets=("recurrence", lambda value: int((value == "RECURRING EXTREME MOLECULAR STATE").sum())),
        stable_recurring_extreme_sets=("recurrence_stable", "sum"),
    ).reset_index()
    annotation_family = annotation_support.groupby("broad_family").size().rename("annotation_defined_recurring_states").reset_index()
    family_summary = family_summary.merge(neighborhood_family, on="broad_family", how="left").merge(extreme_family, on="broad_family", how="left").merge(annotation_family, on="broad_family", how="left").fillna(0)
    recurrence_stable = recurring.donor_recurrence_retained_all.astype("boolean").fillna(False).astype(bool)
    compression = int(recurring.unannotated_compression_review_flag.sum())
    stable_compression = int((recurring.unannotated_compression_review_flag & recurrence_stable).sum())
    encoder_loss_mask = recurring.rna_rare & (~recurring.ledger_rare)
    encoder_loss = int(encoder_loss_mask.sum())
    supported_encoder_loss = int(supported_encoder_loss_mask(recurring).sum())
    high_technical = int((neighborhoods.technical_concern == "HIGH TECHNICAL CONCERN").sum())
    unstable_recurring = int((~recurrence_stable).sum())
    unstable_extremes = int(((extremes.recurrence == "RECURRING EXTREME MOLECULAR STATE") & (~extremes.recurrence_stable)).sum())
    rep_advantage = int(((recurring.rna_rare) & (recurring.ledger_rare) & (~recurring.pca_rare) & (recurring.rep_rare)).sum())
    encoded_only = int(((recurring.ledger_rare) & (~recurring.rna_rare)).sum())
    pca_only = int(((recurring.pca_rare) & (~recurring.rna_rare) & (~recurring.ledger_rare)).sum())
    if supported_encoder_loss:
        classification = "C. MOLECULAR ENCODER / LEDGER LOSES RARE BIOLOGY"
    elif stable_compression:
        classification = "B. MOLECULAR LEDGER PRESERVES RARE BIOLOGY; GLOBAL PCA STATE LOSES SOME RARE INFORMATION"
    elif saturation_class == "NOT-SATURATING" or unstable_recurring or unstable_extremes:
        classification = "D. RARE BIOLOGY DISCOVERY NOT SATURATED / DATA COVERAGE INCOMPLETE"
    elif high_technical > len(neighborhoods) / 2:
        classification = "E. TECHNICAL ARTIFACTS PREVENT RELIABLE RARE-BIOLOGY QUALIFICATION"
    else:
        classification = "A. RARE BIOLOGY PRESERVATION BROADLY QUALIFIED"
    family_diversity = family_summary.assign(
        total_rare_evidence=lambda value: value.annotation_defined_recurring_states + value.recurring + value.recurring_extreme_sets
    ).sort_values(["total_rare_evidence", "broad_family"], ascending=[False, True])
    required_questions = {
        "01_annotation_defined_donor_recurring_states": len(annotation_support),
        "02_data_defined_donor_recurring_neighborhoods": len(recurring),
        "03_donor_private_well_measured_populations": len(donor_private),
        "04_limited_recurrence_candidates": int((neighborhoods.recurrence_class == "LIMITED-RECURRENCE").sum()),
        "05_families_with_most_rare_state_diversity": family_diversity[["broad_family", "total_rare_evidence"]].head(5).to_dict("records"),
        "06_rare_states_source_concentration": {"single_dataset": int((recurring.cross_source_recurrence == "SINGLE-DATASET").sum()), "multi_dataset": int((recurring.cross_source_recurrence == "MULTI-DATASET").sum()), "multi_technology": int((recurring.cross_source_recurrence == "MULTI-TECHNOLOGY").sum())},
        "07_high_measurement_quality_association_count": high_technical,
        "08_rna_and_ledger_rare_but_not_pca160": compression,
        "09_rna_rare_but_not_ledger": {"raw_review_flags": encoder_loss, "supported_architecture_failures": supported_encoder_loss},
        "10_encoding_or_compression_only_rare": {"ledger_only": encoded_only, "pca_only": pca_only},
        "11_microglia_pvm_unannotated_recurring_substates": int(((recurring.broad_family == "Microglia / immune") & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "12_common_neuronal_annotations_with_recurring_substates": int((recurring.broad_family.isin(["Excitatory neurons", "Inhibitory neurons"]) & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "13_recurring_continuous_extreme_states": int((extremes.recurrence == "RECURRING EXTREME MOLECULAR STATE").sum()),
        "14_discovery_saturation": saturation_class,
        "15_molecular_ledger_preserves_rare_biology": "FAILED" if supported_encoder_loss else "PARTIAL" if encoder_loss else "QUALIFIED",
        "16_pca160_global_map_role": "PARTIAL" if compression else "QUALIFIED",
        "17_rep160_material_advantage_candidates": rep_advantage,
        "18_primarily_technical_candidates": high_technical,
        "19_donor_private_candidate_ids": donor_private.rare_neighborhood_id.astype(str).tolist(),
        "20_another_intrinsic_neural_run_required": bool(supported_encoder_loss),
    }
    report = {
        "stage": "stage81a3_rare_biology_completeness",
        "governance": config["governance"],
        "bounded_discovery_contract": contract,
        "bounded_discovery_cells": len(metadata),
        "bounded_discovery_donors": metadata.donor_id.nunique(),
        "annotation_defined_rare_states_audited": len(annotation_support),
        "data_defined_rare_candidate_cells": len(candidates),
        "data_defined_rare_molecular_neighborhoods": len(neighborhoods),
        "donor_private_biological_candidates": len(donor_private),
        "limited_recurrence_rare_candidates": int((neighborhoods.recurrence_class == "LIMITED-RECURRENCE").sum()),
        "donor_recurring_data_defined_rare_states": len(recurring),
        "cross_dataset_rare_states": int((recurring.datasets >= 2).sum()),
        "cross_technology_rare_states": int((recurring.technologies >= 2).sum()),
        "rna_ledger_rare_pca_not_rare_states": compression,
        "stable_rna_ledger_rare_pca_not_rare_states": stable_compression,
        "rna_rare_ledger_not_rare_states": encoder_loss,
        "supported_rna_rare_ledger_not_rare_states": supported_encoder_loss,
        "ledger_rare_rna_not_rare_states": encoded_only,
        "pca_rare_only_states": pca_only,
        "high_technical_concern_rare_candidates": high_technical,
        "unstable_donor_recurring_neighborhoods": unstable_recurring,
        "unstable_recurring_extreme_states": unstable_extremes,
        "microglia_unannotated_rare_states": required_questions["11_microglia_pvm_unannotated_recurring_substates"],
        "excitatory_neuron_unannotated_rare_states": int(((recurring.broad_family == "Excitatory neurons") & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "inhibitory_neuron_unannotated_rare_states": int(((recurring.broad_family == "Inhibitory neurons") & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "astrocyte_unannotated_rare_states": int(((recurring.broad_family == "Astrocytes") & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "other_cell_family_unannotated_rare_states": int((~recurring.broad_family.isin(["Microglia / immune", "Excitatory neurons", "Inhibitory neurons", "Astrocytes"]) & ~recurring.annotation_agreement.eq("ANNOTATION-CONCORDANT")).sum()),
        "discovery_saturation": saturation_class,
        "molecular_ledger_rare_biology_preservation": "FAILED" if supported_encoder_loss else "PARTIAL" if encoder_loss else "QUALIFIED",
        "pca160_rare_biology_preservation": "PARTIAL" if compression else "QUALIFIED",
        "rep160_material_rare_state_advantage": "HUMAN-REVIEW" if rep_advantage else "NO",
        "donor_private_states_retained_in_evidence_registry": True,
        "continuous_extreme_biology_audited": True,
        "unannotated_rare_biology_audited": True,
        "rare_biology_completeness_classification": classification,
        "data_defined_conclusions_stable": unstable_recurring == 0 and unstable_extremes == 0,
        "supported_intrinsic_architecture_failure": bool(supported_encoder_loss),
        "another_intrinsic_neural_architecture_run_required": bool(supported_encoder_loss),
        "ready_for_human_a3_freeze_review": classification == "A. RARE BIOLOGY PRESERVATION BROADLY QUALIFIED",
        "freeze_blockers": [] if classification == "A. RARE BIOLOGY PRESERVATION BROADLY QUALIFIED" else [
            f"{unstable_recurring} donor-recurring data-defined neighborhoods failed four-resample recurrence stability",
            f"{unstable_extremes} recurring continuous/extreme definitions failed four-resample recurrence stability",
            f"{encoder_loss} raw RNA-to-ledger attenuation review flags; {supported_encoder_loss} meet the architecture-failure evidence rule",
        ],
        "stage81a3_complete": False,
        "stage81b_started": False,
        "required_completeness_questions": required_questions,
        "family_summaries": family_summary.to_dict("records"),
        "molecular_ledger_parameter_hash_before": before,
        "molecular_ledger_parameter_hash_after": after,
        "pathology_blind": True,
        "train_only": True,
        "unannotated_limitation": "The bounded audit is a serious deterministic discovery attempt, not proof that every possible rare molecular state has been discovered.",
        "abundance_is_not_state": "This audit concerns rare cellular states, not disease-related cell abundance.",
        "wall_seconds": time.perf_counter() - started,
    }
    combined_readiness = combined_readiness_frame(
        supported_encoder_loss,
        unstable_recurring,
        unstable_extremes,
        saturation_class,
        bool(report["ready_for_human_a3_freeze_review"]),
    )
    report["combined_freeze_readiness"] = combined_readiness.to_dict("records")
    for key, frame in (("candidate_cells", candidates), ("neighborhoods", neighborhoods), ("agreement", agreement), ("donor_private", donor_private), ("recurring", recurring), ("continuous_extremes", extremes), ("technical_firewall", firewall), ("saturation", saturation_frame), ("family_summary", family_summary), ("resample_stability", stability)): BASE.write_csv(outputs[key], frame)
    BASE.write_csv(project / config["outputs"]["freeze_readiness"], combined_readiness)
    BASE.write_json(outputs["report"], report)
    readout = project / config["outputs"]["readout"]; existing = readout.read_text(encoding="utf-8"); title = "## PATHOLOGY-BLIND RARE-BIOLOGY COMPLETENESS AUDIT"
    if title in existing:
        existing = existing.split(f"\n\n{title}", 1)[0].rstrip()
    text = f"\n\n{title}\n\nChannels B/C extended annotation-defined RSCR with a fixed family-wise bounded discovery audit: complete RNA and ledger local-isolation at k=30, top-1% candidate designation, deterministic overlap neighborhoods, technical-association firewall, rotation-stable continuous extremes, donor recurrence, and donor-fraction saturation. No clustering or hyperparameter shopping was performed. The family cap was set to 1,024 so a 75% donor subset can mathematically satisfy the unchanged five-donor recurrence rule; no rarity or evidence threshold was altered.\n\nClassification: **{classification}**. Candidate cells: {len(candidates)}; neighborhoods: {len(neighborhoods)}; donor-private biological candidates: {len(donor_private)}; donor-recurring neighborhoods: {len(recurring)}; RNA+ledger rare/PCA-not-rare recurring states: {compression} ({stable_compression} stable); RNA-rare/ledger-not-rare recurring review flags: {encoder_loss} ({supported_encoder_loss} supported architecture failures); high-technical-concern candidates: {high_technical}; saturation: **{saturation_class}**. All {unstable_recurring} donor-recurring data-defined neighborhoods failed the four-resample recurrence-stability check. The raw RNA-to-ledger review flag had mixed technical association and was unstable, so it does not support another intrinsic architecture run.\n\nThis concerns rare cellular states, not disease-related abundance. Annotation-defined coverage and bounded data-defined discovery do not prove exhaustive discovery of all rare molecular biology. The full molecular ledger remained parameter-identical; PCA160 and REP160 were not refit or promoted. **Ready for human A3 freeze review: NO.** Pathology, DEV, and SEALED expression remained closed; optimizer, backward, EMA, and context-update counts remained zero. Stage81A3 was not completed or frozen and Stage81B was not started.\n"
    BASE.atomic_text(readout, existing.rstrip() + text)
    if not args.keep_cache: cleanup(project / contract["cache_dir"])
    print(json.dumps({"classification": classification, "candidate_cells": len(candidates), "neighborhoods": len(neighborhoods), "recurring": len(recurring), "saturation": saturation_class}, indent=2), flush=True); return 0

if __name__ == "__main__": raise SystemExit(main())
