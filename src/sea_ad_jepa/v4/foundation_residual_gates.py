"""Fail-closed adjudication for residual Foundation representation gates.

Pure functions only. No raw expression access and no authority creation.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping


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
