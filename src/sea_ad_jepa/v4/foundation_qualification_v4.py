"""Current, non-authorizing adjudication of preserved foundation-state evidence.

This module does not read raw expression and cannot create training or target-discovery
value-read authority. It only maps an authenticated historical report into current
fail-closed scientific/governance statements.
"""
from __future__ import annotations

from typing import Any, Mapping


_REQUIRED_GOVERNANCE = {
    "pathology_blind": True,
    "neural_optimizer_updates": 0,
    "production_basis_frozen": False,
    "stage81b_started": False,
    "train_expression_only": True,
    "development_expression_forbidden": True,
    "sealed_expression_forbidden": True,
}


def _require_governance(report: Mapping[str, Any]) -> dict[str, Any]:
    governance = dict(report.get("governance") or {})
    for key, expected in _REQUIRED_GOVERNANCE.items():
        if governance.get(key) != expected:
            label = "optimizer" if key == "neural_optimizer_updates" else key
            raise ValueError(f"historical evidence fails current {label} firewall: {key}={governance.get(key)!r}")
    if report.get("all_hard_gates_pass") is not True:
        raise ValueError("historical evidence did not pass its declared hard gates")
    return governance


def requalify_historical_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Re-adjudicate preserved pathology-blind evidence without promoting it.

    Strong downstream transfer cannot compensate for weak earlier levels in the
    prospective donor -> matrix -> dataset -> technology ladder.
    """
    _require_governance(report)
    cls = dict(report.get("classifications") or {})

    subspace = cls.get("state_subspace")
    axes = cls.get("state_axes")
    coordinate = cls.get("coordinate_uncertainty")
    if subspace == "STABLE" and axes == "ROTATING-WITHIN-STABLE-SUBSPACE":
        basis_uncertainty = "SUBSPACE_ONLY"
    elif coordinate == "SUBSPACE-ONLY":
        basis_uncertainty = "SUBSPACE_ONLY"
    else:
        basis_uncertainty = "UNRESOLVED"

    evidence = cls.get("biological_evidence_response")
    depth = cls.get("measurement_depth_response")
    separation = cls.get("biology_measurement_separation")
    uncertainty = (
        "SEPARATE_RESPONSES_SUPPORTED_HISTORICALLY"
        if evidence == "DISTINCT" and depth == "SUPPORTED" and separation == "SUPPORTED"
        else "UNRESOLVED"
    )

    transfer = {
        "donor": cls.get("cross_donor_transfer", "UNRESOLVED"),
        "matrix": cls.get("cross_matrix_transfer", "UNRESOLVED"),
        "dataset": cls.get("cross_dataset_transfer", "UNRESOLVED"),
        "technology": cls.get("cross_technology_transfer", "UNRESOLVED"),
    }
    transfer_all_strong = all(value == "STRONG" for value in transfer.values())

    domain = cls.get("two_axis_domain_support", "UNRESOLVED")
    historical_basis = cls.get("balanced_pca160", "UNRESOLVED")
    production_ready = (
        historical_basis == "QUALIFIED"
        and basis_uncertainty != "UNRESOLVED"
        and uncertainty != "UNRESOLVED"
        and transfer_all_strong
        and domain == "INFORMATIVE"
    )

    performance = dict(report.get("performance") or {})
    return {
        "schema": "FOUNDATION_REPRESENTATION_QUALIFICATION_V4_REQUALIFICATION_V1",
        "source_status": "HISTORICAL_EVIDENCE__NOT_CURRENT_PRODUCTION_AUTHORITY",
        "foundation_datasets": report.get("foundation_datasets"),
        "foundation_matrices": report.get("foundation_matrices"),
        "historical_basis_classification": historical_basis,
        "basis_uncertainty": basis_uncertainty,
        "biology_measurement_uncertainty": uncertainty,
        "two_axis_domain_support": domain,
        "transfer_ladder": transfer,
        "transfer_ladder_all_strong": transfer_all_strong,
        "historical_resource_evidence": {
            "peak_cpu_rss_bytes": performance.get("peak_cpu_rss_bytes"),
            "temporary_disk_bytes": performance.get("temporary_disk_bytes"),
            "status": "HISTORICAL_MEASUREMENT__NOT_PRODUCTION_RESOURCE_GUARANTEE",
        },
        "representation_freeze_authorized": bool(production_ready),
        "training_authorized": False,
        "target_discovery_value_read_authorized": False,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "stage4_authorized": False,
        "terminal": (
            "HISTORICAL_EVIDENCE_REQUALIFIED__CURRENT_REPRESENTATION_FREEZE_ELIGIBLE_FOR_SEPARATE_REVIEW"
            if production_ready
            else "HISTORICAL_EVIDENCE_REQUALIFIED__CURRENT_REPRESENTATION_FREEZE_BLOCKED"
        ),
    }
