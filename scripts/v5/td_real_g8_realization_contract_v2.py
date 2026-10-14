"""Outcome-blind G8 realization/metric/support semantics.

This module closes the semantic gap left by the conformal-bound mechanics in
``td_real_measurement_reference_v1``.  It defines what a calibration draw is,
how support fractions are denominated, and what must be frozen before a real
G8 reference can be generated.  It does not evaluate candidate biology.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

import td_real_measurement_reference_v1 as REF


class G8ContractError(ValueError):
    pass


UNIT_SCHEMA = "JEPA_TD_REAL_G8_REFERENCE_UNIT_V2"
METRIC_SCHEMA = "JEPA_TD_REAL_G8_METRIC_CONTRACT_V2"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REALIZATION = "INDEPENDENT_TECHNICAL_MONTE_CARLO_PAIR_CONDITIONAL_ON_FIXED_REAL_UNIT"
_ORIENTATION = "SMALLER_IS_MORE_STABLE"
_ALLOWED_ATOM_STATES = {
    "RESOLVED_NONZERO",
    "RESOLVED_MEASURED_ZERO",
    "MEASUREMENT_UNRESOLVED",
    "UNSUPPORTED_STRUCTURAL",
    "BLOCKED_EVIDENCE_CONTRACT",
}
_RESOLVED_STATES = {"RESOLVED_NONZERO", "RESOLVED_MEASURED_ZERO"}
_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise G8ContractError(f"{label} must be a lowercase SHA-256 hash")
    return value


def validate_unit_manifest(manifest: Mapping[str, object]) -> dict:
    if not isinstance(manifest, Mapping):
        raise G8ContractError("unit manifest must be a mapping")
    required = {
        "schema", "candidate_id", "source", "donor_id", "operator_scope_id",
        "endpoint_id", "input_binding_sha256", "metric_manifest_sha256",
        "support_universe_sha256", "atomic_support_unit",
        "biological_replication_unit", "calibration_realization",
        "calibration_draws_are_biological_replicates", "metric_orientation",
        "metric_frozen_before_values", "support_denominator_frozen_before_thinning",
        "measured_zero_is_supported_measurement", "unsupported_atoms_are_abstentions",
    }
    if set(manifest) != required:
        missing = sorted(required - set(manifest))
        extra = sorted(set(manifest) - required)
        raise G8ContractError(f"exact unit manifest required; missing={missing}, extra={extra}")
    if manifest["schema"] != UNIT_SCHEMA:
        raise G8ContractError("unit schema mismatch")
    for key in ("candidate_id", "source", "donor_id", "operator_scope_id", "endpoint_id", "atomic_support_unit"):
        if not isinstance(manifest[key], str) or not manifest[key]:
            raise G8ContractError(f"{key} must be a nonempty string")
    _require_hash(manifest["input_binding_sha256"], "input binding")
    _require_hash(manifest["metric_manifest_sha256"], "metric manifest")
    _require_hash(manifest["support_universe_sha256"], "support universe")
    if manifest["biological_replication_unit"] != "DONOR":
        raise G8ContractError("G8 biological replication unit must remain DONOR")
    if manifest["calibration_realization"] != _REALIZATION:
        raise G8ContractError("G8 calibration realization semantics mismatch")
    if manifest["calibration_draws_are_biological_replicates"] is not False:
        raise G8ContractError("technical calibration draws may not become biological replicates")
    if manifest["metric_orientation"] != _ORIENTATION:
        raise G8ContractError("G8 metric orientation mismatch")
    for key in (
        "metric_frozen_before_values",
        "support_denominator_frozen_before_thinning",
        "measured_zero_is_supported_measurement",
        "unsupported_atoms_are_abstentions",
    ):
        if manifest[key] is not True:
            raise G8ContractError(f"{key} must be true")
    return dict(manifest)


def validate_metric_contract(contract: Mapping[str, object]) -> dict:
    if not isinstance(contract, Mapping):
        raise G8ContractError("metric contract must be a mapping")
    required = {
        "schema", "metric_id", "candidate_id", "metric_manifest_sha256",
        "orientation", "same_metric_reference_and_decision", "frozen_before_values",
        "outcome_adaptive_parameters", "invariance_class",
    }
    if set(contract) != required:
        raise G8ContractError("exact metric contract required")
    if contract["schema"] != METRIC_SCHEMA:
        raise G8ContractError("metric schema mismatch")
    for key in ("metric_id", "candidate_id", "invariance_class"):
        if not isinstance(contract[key], str) or not contract[key]:
            raise G8ContractError(f"{key} must be a nonempty string")
    _require_hash(contract["metric_manifest_sha256"], "metric manifest")
    if contract["orientation"] != _ORIENTATION:
        raise G8ContractError("metric orientation must be SMALLER_IS_MORE_STABLE")
    if contract["same_metric_reference_and_decision"] is not True:
        raise G8ContractError("the same metric must serve reference and decision")
    if contract["frozen_before_values"] is not True:
        raise G8ContractError("metric must be frozen before values")
    if contract["outcome_adaptive_parameters"] is not False:
        raise G8ContractError("metric may not contain outcome-adaptive parameters")
    return dict(contract)


def support_fraction(*, eligible_atoms: Sequence[str], atom_states: Mapping[str, str]) -> dict:
    if isinstance(eligible_atoms, (str, bytes)) or not isinstance(eligible_atoms, Sequence) or not eligible_atoms:
        raise G8ContractError("eligible_atoms must be a nonempty sequence")
    atoms = [str(atom) for atom in eligible_atoms]
    if len(set(atoms)) != len(atoms):
        raise G8ContractError("eligible atom identifiers must be unique")
    if not isinstance(atom_states, Mapping) or set(atom_states) != set(atoms):
        raise G8ContractError("atom_states must exactly match the frozen pre-thinning denominator")
    bad = {value for value in atom_states.values() if value not in _ALLOWED_ATOM_STATES}
    if bad:
        raise G8ContractError(f"unknown atom support states: {sorted(bad)}")
    resolved = sum(atom_states[atom] in _RESOLVED_STATES for atom in atoms)
    measured_zero = sum(atom_states[atom] == "RESOLVED_MEASURED_ZERO" for atom in atoms)
    denominator = len(atoms)
    return {
        "denominator": denominator,
        "resolved_count": resolved,
        "measured_zero_count": measured_zero,
        "abstained_count": denominator - resolved,
        "support_fraction": resolved / denominator,
        "denominator_semantics": "FROZEN_PRETHINNING_ELIGIBLE_ATOM_UNIVERSE",
    }


def build_calibration_plan(
    *,
    unit_manifest: Mapping[str, object],
    family_alpha: float,
    calibration_namespace: str,
    deciding_namespace: str,
    null_namespace: str,
) -> dict:
    unit = validate_unit_manifest(unit_manifest)
    if isinstance(family_alpha, bool) or not isinstance(family_alpha, (int, float)):
        raise G8ContractError("family_alpha must be numeric")
    family_alpha = float(family_alpha)
    if not math.isfinite(family_alpha) or not (0.0 < family_alpha < 1.0):
        raise G8ContractError("family_alpha must lie in (0,1)")
    names = [calibration_namespace, deciding_namespace, null_namespace]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != 3:
        raise G8ContractError("calibration, deciding, and null namespaces must be nonempty and disjoint")
    alpha_eff = family_alpha / (len(REF.DEPTHS) * len(REF.PROTECTED_ENDPOINTS))
    required_n = REF.minimum_calibration_size(alpha_eff)
    return {
        "schema": "JEPA_TD_REAL_G8_CALIBRATION_PLAN_V2",
        "unit": unit,
        "depths": list(REF.DEPTHS),
        "protected_endpoints": list(REF.PROTECTED_ENDPOINTS),
        "family_alpha": family_alpha,
        "alpha_eff": alpha_eff,
        "required_calibration_draws_per_depth": required_n,
        "draw_indices": list(range(required_n)),
        "calibration_namespace": calibration_namespace,
        "deciding_namespace": deciding_namespace,
        "null_namespace": null_namespace,
        "calibration_draw_semantics": _REALIZATION,
        "support_statistic_per_draw": "SUPPORT_FRACTION_OF_DESIGNATED_A_REPLICATE_OVER_FROZEN_PRETHINNING_UNIVERSE",
        "displacement_statistic_per_draw": "CANDIDATE_FROZEN_METRIC_BETWEEN_A_AND_B_TECHNICAL_REPLICATES",
        "deciding_displacement": "SAME_FROZEN_METRIC_BETWEEN_FULL_ANCHOR_AND_T_DEPTH_REPLICATE",
        "biological_replication_unit": "DONOR",
        "biological_donor_count_contributed": 1,
        "technical_draws_do_not_increase_biological_n": True,
        "authority": dict(_NO_AUTHORITY),
    }


def execution_readiness(
    *,
    unit_manifest: Mapping[str, object],
    metric_contract_qualified: bool,
    support_universe_qualified: bool,
) -> dict:
    unit = validate_unit_manifest(unit_manifest)
    ready = metric_contract_qualified is True and support_universe_qualified is True
    return {
        "schema": "JEPA_TD_REAL_G8_EXECUTION_READINESS_V2",
        "status": (
            "READY_FOR_OUTCOME_BLIND_G8_REFERENCE_GENERATION_ONLY"
            if ready else "BLOCKED_G8_CONTRACT_DEPENDENCY"
        ),
        "unit": unit,
        "metric_contract_qualified": bool(metric_contract_qualified),
        "support_universe_qualified": bool(support_universe_qualified),
        "human_g8_adjudication_authorized": False,
        "authority": dict(_NO_AUTHORITY),
    }
