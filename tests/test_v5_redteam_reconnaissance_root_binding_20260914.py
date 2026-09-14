from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "docs" / "agent" / "V5_FULL104_RECONNAISSANCE_AUTHORITY_V1.json"

_DIAGNOSTICS = [
    "donor_operator_source_study_technology_counts",
    "depth_detection_distributions",
    "sparsity_zero_support_missingness",
    "feature_variance_covariance_conditioning",
    "effective_rank_redundancy",
    "view_overlap_redundancy",
    "donor_heterogeneity_leverage",
    "technical_variable_correlations",
    "cell_state_support_across_donors",
    "matched_null_stratum_size_singleton_rates",
    "matching_state_discreteness",
    "operator_source_dataset_variance_dominance",
    "control_estimability",
    "io_memory_parallelization_mechanics",
]


def _receipt() -> dict[str, object]:
    evidence = {diagnostic: hashlib.sha256(diagnostic.encode("utf-8")).hexdigest() for diagnostic in _DIAGNOSTICS}
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "schema": "JEPA_V5_FULL104_RECONNAISSANCE_RECEIPT_V1",
        "full104_dimension_input_artifact_sha256": "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad",
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "addresses": 41_238,
        "diagnostics_completed": list(_DIAGNOSTICS),
        "diagnostic_evidence_sha256": evidence,
        "reconnaissance_evidence_root_sha256": hashlib.sha256(canonical).hexdigest(),
        "d_shared_outcomes_inspected": False,
        "rank_selection_inspected": False,
        "decision_bearing_effects_inspected": False,
        "pathology_used": False,
        "protected_data_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
        "terminal": "PASS_FULL104_OUTCOME_BLIND_RECONNAISSANCE_V1",
    }


def test_reconnaissance_rejects_root_not_derived_from_complete_evidence_map():
    m = importlib.import_module("sea_ad_jepa.v5.full104_reconnaissance_authority_v1")
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    bad = _receipt()
    bad["reconnaissance_evidence_root_sha256"] = "f" * 64
    with pytest.raises(m.Full104ReconnaissanceStop, match="EVIDENCE_ROOT|EVIDENCE"):
        m.seal_full104_reconnaissance_receipt_v1(authority, bad)
