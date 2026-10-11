"""Fail-closed adjudication for residual Foundation representation gates.

Pure functions only. No raw expression access and no authority creation.
"""
from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Iterable, Mapping


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _require_prefrozen(record: Mapping[str, Any]) -> None:
    if record.get("contract_frozen_before_candidate_evaluation") is not True:
        raise ValueError("acceptance contract must be frozen before candidate evaluation")


def matrix_label_identifiability(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_matrix: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rec = {k: "" if v is None else str(v) for k, v in row.items()}
        if not rec.get("matrix_id"):
            raise ValueError("matrix_id is required")
        by_matrix[rec["matrix_id"]].append(rec)
    native = {m: {r.get("native_class", "") for r in rr if r.get("native_class", "")} for m, rr in by_matrix.items()}
    out = []
    for matrix_id in sorted(by_matrix):
        rr = by_matrix[matrix_id]
        other_native: set[str] = set()
        for other, labels in native.items():
            if other != matrix_id:
                other_native.update(labels)
        seen = sum(bool(r.get("native_class")) and r["native_class"] in other_native for r in rr)
        unseen = sorted({r.get("native_class", "") for r in rr if r.get("native_class") and r["native_class"] not in other_native})
        broad_n = sum(bool(r.get("broad_class", "").strip()) for r in rr)
        if broad_n == 0:
            broad_state = "UNAVAILABLE"
        elif broad_n == len(rr):
            broad_state = "AVAILABLE"
        else:
            broad_state = "PARTIAL"
        out.append({
            "matrix_id": matrix_id,
            "source": rr[0].get("source", ""),
            "cells": len(rr),
            "donors": len({r.get("donor_id", "") for r in rr if r.get("donor_id", "")}),
            "native_labels": len(native[matrix_id]),
            "native_cell_coverage_seen_elsewhere": seen / len(rr),
            "unseen_native_label_count": len(unseen),
            "unseen_native_labels": unseen,
            "broad_label_available_fraction": broad_n / len(rr),
            "broad_label_identifiability": broad_state,
        })
    return out


def adjudicate_heldout_donor_evidence(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    selected = [dict(r) for r in rows if str(r.get("checkpoint")) == "u205" and str(r.get("representation")) == "rich_H" and "45 heldout TRAIN donors" in str(r.get("evaluation", ""))]
    values = {str(r.get("target")): float(r["value"]) for r in selected if r.get("value") not in (None, "")}
    deltas = {str(r.get("target")): float(r["u205_minus_u0"]) for r in selected if r.get("u205_minus_u0") not in (None, "")}
    required = ("source", "operator", "support_measured_count", "broad_annotation")
    missing = [k for k in required if k not in values]
    if missing:
        raise ValueError(f"missing heldout donor evidence: {missing}")
    return {
        "schema": "FOUNDATION_T1_HELDOUT_DONOR_EVIDENCE_V1",
        "heldout_donors": 45,
        "checkpoint": "u205",
        "representation": "rich_H",
        "source_balanced_accuracy": values["source"],
        "operator_balanced_accuracy": values["operator"],
        "support_measured_count_r2": values["support_measured_count"],
        "broad_annotation_balanced_accuracy": values["broad_annotation"],
        "broad_annotation_u205_minus_u0": deltas.get("broad_annotation"),
        "innovation_tail_r2": values.get("innovation_tail"),
        "innovation_tail_u205_minus_u0": deltas.get("innovation_tail"),
        "donor_transfer_qualified": False,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": "CURRENT_HELDOUT_DONOR_EVIDENCE_AVAILABLE__NO_PREFROZEN_PASS_THRESHOLD__NOT_FREEZE_QUALIFIED",
    }


def adjudicate_conditional_technology_imprint(record: Mapping[str, Any]) -> dict[str, Any]:
    scope = str(record.get("scope", ""))
    if "FIT_POPULATION_ONLY" not in scope:
        raise ValueError("conditional technology diagnostic must declare its evidence scope")
    baseline = float(record["broad_class_only_balanced_accuracy"])
    joint = float(record["broad_class_plus_state_balanced_accuracy"])
    return {
        "schema": "FOUNDATION_T1_CONDITIONAL_TECHNOLOGY_ADJUDICATION_V1",
        **dict(record),
        "residual_source_increment_over_broad_class": joint - baseline,
        "technology_invariance_qualified": False,
        "heldout_transfer_authority": False,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": "RESIDUAL_SOURCE_IMPRINT_OBSERVED__FIT_POPULATION_DIAGNOSTIC__TECHNOLOGY_INVARIANCE_NOT_QUALIFIED",
    }


def adjudicate_resource_benchmark(record: Mapping[str, Any]) -> dict[str, Any]:
    measurements = [dict(x) for x in record.get("measurements", [])]
    if not measurements:
        raise ValueError("resource measurements required")
    cells = {int(x["cells"]): x for x in measurements}
    recommended = 4 if 4 in cells else min(cells)
    device = str(record.get("device", "")).lower()
    final_pass = device.startswith("cuda") and bool(record.get("final_production_path"))
    return {
        "schema": "FOUNDATION_T1_RESOURCE_ADJUDICATION_V1",
        **dict(record),
        "bounded_cpu_resource_evidence": device == "cpu",
        "recommended_cpu_batch_ceiling": recommended,
        "final_production_resource_gate_pass": final_pass,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": ("FINAL_PRODUCTION_RESOURCE_MEASUREMENT_AVAILABLE__SEPARATE_REVIEW_REQUIRED" if final_pass else "BOUNDED_CPU_RESOURCE_EVIDENCE__FINAL_PRODUCTION_GPU_BENCHMARK_PENDING"),
    }


def adjudicate_successor_donor_transfer(record: Mapping[str, Any]) -> dict[str, Any]:
    """Prospective donor-transfer gate for a future, unopened representation candidate.

    The rule is null-calibrated rather than margin-tuned: biology must exceed its
    permutation envelope while residual source/operator/support prediction must not.
    """
    _require_prefrozen(record)
    if str(record.get("scope")) != "HELDOUT_TRAIN_DONORS":
        raise ValueError("successor donor gate requires HELDOUT_TRAIN_DONORS scope")
    biology = _finite(record.get("biology_observed"), "biology_observed")
    biology_null = _finite(record.get("biology_permutation_q95"), "biology_permutation_q95")
    nuisance = {}
    for name in ("source", "operator", "support"):
        observed = _finite(record.get(f"{name}_residual_observed"), f"{name}_residual_observed")
        null = _finite(record.get(f"{name}_residual_permutation_q95"), f"{name}_residual_permutation_q95")
        nuisance[name] = {"observed": observed, "permutation_q95": null, "pass": observed <= null}
    biology_pass = biology > biology_null
    passed = biology_pass and all(v["pass"] for v in nuisance.values())
    return {
        "schema": "FOUNDATION_SUCCESSOR_DONOR_TRANSFER_GATE_V1",
        "contract_frozen_before_candidate_evaluation": True,
        "scope": "HELDOUT_TRAIN_DONORS",
        "biology": {"observed": biology, "permutation_q95": biology_null, "pass": biology_pass},
        "residual_nuisance": nuisance,
        "donor_transfer_qualified": passed,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": "PASS_SUCCESSOR_DONOR_TRANSFER_GATE" if passed else "FAIL_SUCCESSOR_DONOR_TRANSFER_GATE",
    }


def adjudicate_successor_matrix_transfer(
    rows: Iterable[Mapping[str, Any]], *, contract_frozen_before_candidate_evaluation: bool
) -> dict[str, Any]:
    """Prospective leave-one-matrix gate with explicit identifiable-cell accounting."""
    if contract_frozen_before_candidate_evaluation is not True:
        raise ValueError("acceptance contract must be frozen before candidate evaluation")
    rr = [dict(r) for r in rows]
    if not rr:
        raise ValueError("matrix rows required")
    total_cells = 0
    eligible_cells = 0
    nonidentifiable = []
    per_matrix = []
    for row in rr:
        matrix_id = str(row.get("matrix_id", ""))
        if not matrix_id:
            raise ValueError("matrix_id required")
        total = int(row.get("total_cells", 0))
        eligible = int(row.get("eligible_cells", 0))
        if total <= 0 or eligible < 0 or eligible > total:
            raise ValueError("matrix cell counts invalid")
        total_cells += total
        eligible_cells += eligible
        if eligible == 0:
            nonidentifiable.append(matrix_id)
            per_matrix.append({"matrix_id": matrix_id, "eligible_cells": 0, "total_cells": total, "evaluable": False, "pass": None})
            continue
        biology = _finite(row.get("biology_observed"), "biology_observed")
        biology_null = _finite(row.get("biology_permutation_q95"), "biology_permutation_q95")
        residual = _finite(row.get("matrix_residual_observed"), "matrix_residual_observed")
        residual_null = _finite(row.get("matrix_residual_permutation_q95"), "matrix_residual_permutation_q95")
        passed = biology > biology_null and residual <= residual_null
        per_matrix.append({
            "matrix_id": matrix_id,
            "eligible_cells": eligible,
            "total_cells": total,
            "evaluable": True,
            "biology_observed": biology,
            "biology_permutation_q95": biology_null,
            "matrix_residual_observed": residual,
            "matrix_residual_permutation_q95": residual_null,
            "pass": passed,
        })
    evaluable = [x for x in per_matrix if x["evaluable"]]
    qualified = bool(evaluable) and all(x["pass"] for x in evaluable)
    return {
        "schema": "FOUNDATION_SUCCESSOR_MATRIX_TRANSFER_GATE_V1",
        "contract_frozen_before_candidate_evaluation": True,
        "identifiable_cell_fraction": eligible_cells / total_cells,
        "evaluable_matrices": len(evaluable),
        "nonidentifiable_matrices": sorted(nonidentifiable),
        "per_matrix": per_matrix,
        "matrix_transfer_qualified": qualified,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": "PASS_SUCCESSOR_MATRIX_TRANSFER_GATE" if qualified else "FAIL_SUCCESSOR_MATRIX_TRANSFER_GATE",
    }


def adjudicate_successor_conditional_technology(record: Mapping[str, Any]) -> dict[str, Any]:
    """Prospective held-out conditional source/technology invariance gate."""
    _require_prefrozen(record)
    scope = str(record.get("scope", ""))
    if scope != "HELDOUT_DONORS_OR_HELDOUT_MATRICES":
        raise ValueError("successor conditional technology gate requires held-out scope")
    biology = _finite(record.get("biology_observed"), "biology_observed")
    biology_null = _finite(record.get("biology_permutation_q95"), "biology_permutation_q95")
    control = _finite(record.get("biology_control_source_score"), "biology_control_source_score")
    joint = _finite(record.get("biology_plus_state_source_score"), "biology_plus_state_source_score")
    increment_null = _finite(record.get("source_increment_permutation_q95"), "source_increment_permutation_q95")
    increment = joint - control
    biology_pass = biology > biology_null
    invariance_pass = increment <= increment_null
    passed = biology_pass and invariance_pass
    return {
        "schema": "FOUNDATION_SUCCESSOR_CONDITIONAL_TECHNOLOGY_GATE_V1",
        "contract_frozen_before_candidate_evaluation": True,
        "scope": scope,
        "biology_observed": biology,
        "biology_permutation_q95": biology_null,
        "biology_pass": biology_pass,
        "biology_control_source_score": control,
        "biology_plus_state_source_score": joint,
        "residual_source_increment": increment,
        "source_increment_permutation_q95": increment_null,
        "technology_invariance_qualified": passed,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "terminal": "PASS_SUCCESSOR_CONDITIONAL_TECHNOLOGY_GATE" if passed else "FAIL_SUCCESSOR_CONDITIONAL_TECHNOLOGY_GATE",
    }
