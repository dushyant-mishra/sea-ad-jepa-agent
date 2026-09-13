from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Mapping, Sequence

from .full104_dimension_interface_v1 import validate_full104_dimension_input


class PrecisionAuthorityStop(RuntimeError):
    pass


FROZEN_PRECISION_AUTHORITY_SHA256 = "cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_PARENT_KEYS = {
    "block_manifest_sha256",
    "materialization_contract_sha256",
    "materialization_audit_sha256",
    "selection_sha256",
    "selection_manifest_sha256",
    "metadata_sqlite_sha256",
}
_REQUIRED_TRUE = {
    "survivor_only_intervals_forbidden",
    "precision_is_not_effect_criterion",
    "post_outcome_replication_tuning_forbidden",
    "gate_ablation_required",
    "redundancy_identity_check_required",
}
_REQUIRED_FALSE = {
    "outcomes_inspected_before_freeze",
    "checkpoint_outcomes_used",
    "pathology_used",
    "protected_data_used",
    "training_authorized",
    "dimension_outcomes_used",
}
_ALLOWED_KINDS = {"null", "donor", "operator"}


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_INVALID_NUMERIC:{field}")
    out = float(value)
    if not math.isfinite(out):
        raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_INVALID_NUMERIC:{field}")
    return out


def _require_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_INVALID_SHA:{field}")
    return value


def derive_hoeffding_fixed_n(range_width: float, tolerance: float, alpha: float) -> int:
    """Worst-case fixed N for a bounded-mean absolute-error guarantee."""
    r = _finite_number(range_width, "range_width")
    eps = _finite_number(tolerance, "tolerance")
    a = _finite_number(alpha, "alpha")
    if r <= 0 or eps <= 0 or not (0 < a < 1):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_INVALID_HOEFFDING_ARGUMENT")
    return int(math.ceil((r * r * math.log(2.0 / a)) / (2.0 * eps * eps)))


def canonical_precision_authority_bytes(authority: Mapping[str, object]) -> bytes:
    if not isinstance(authority, Mapping):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_NOT_MAPPING")
    return (json.dumps(authority, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _validate_parent_bindings(authority: Mapping[str, object]) -> None:
    parents = authority.get("full104_parent_bindings")
    if not isinstance(parents, Mapping) or set(parents) != _REQUIRED_PARENT_KEYS:
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_PARENT_BINDINGS_INCOMPLETE")
    for key in sorted(_REQUIRED_PARENT_KEYS):
        value = parents.get(key)
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_INVALID_PARENT_SHA:{key}")
    interface_sha = authority.get("dimension_interface_sha256")
    if not isinstance(interface_sha, str) or _SHA256.fullmatch(interface_sha) is None:
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_INVALID_DIMENSION_INTERFACE_SHA")


def validate_precision_authority_v1(authority: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(authority, Mapping):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_NOT_MAPPING")
    if authority.get("schema") != "JEPA_V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_SCHEMA")
    if authority.get("status") != "FROZEN_BEFORE_DIMENSION_OUTCOME_ACCESS":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_NOT_PROSPECTIVELY_FROZEN")
    if authority.get("method") != "HOEFFDING_FIXED_N_V1":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_METHOD")
    if authority.get("risk_allocation_method") != "BONFERRONI_EQUAL_10":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_RISK_METHOD")
    if authority.get("decision_metric_population") != "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_UNCONDITIONAL_REQUIRED")
    if authority.get("estimator_failure_policy") != "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_ESTIMATOR_FAILURE_POLICY")
    if authority.get("rng_replay_policy") != "SHA256_PARENT_QUANTITY_REPLICATE_INDEX_V1":
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_RNG_POLICY")

    for field in sorted(_REQUIRED_TRUE):
        if authority.get(field) is not True:
            if field == "survivor_only_intervals_forbidden":
                raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_SURVIVOR_ONLY_FORBIDDEN")
            if field == "precision_is_not_effect_criterion":
                raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_PRECISION_EFFECT_CONFLATION")
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_REQUIRED_TRUE:{field}")
    for field in sorted(_REQUIRED_FALSE):
        if authority.get(field) is not False:
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_PRE_FREEZE_ACCESS:{field}")

    _validate_parent_bindings(authority)

    family_risk = _finite_number(authority.get("familywise_precision_risk"), "familywise_precision_risk")
    if not (0 < family_risk < 1):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_INVALID_FAMILY_RISK")

    quantities = authority.get("quantities")
    if not isinstance(quantities, Sequence) or isinstance(quantities, (str, bytes)) or len(quantities) != 10:
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_QUANTITY_COUNT")

    seen: set[str] = set()
    risk_sum = 0.0
    maxima = {"null": 0, "donor": 0, "operator": 0}
    for row in quantities:
        if not isinstance(row, Mapping):
            raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_QUANTITY_NOT_MAPPING")
        qid = row.get("quantity_id")
        if not isinstance(qid, str) or not qid:
            raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_QUANTITY_ID")
        if qid in seen:
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_DUPLICATE_QUANTITY:{qid}")
        seen.add(qid)
        kind = row.get("resampling_kind")
        if kind not in _ALLOWED_KINDS:
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_RESAMPLING_KIND:{qid}")
        lo = _finite_number(row.get("lower_bound"), f"{qid}.lower_bound")
        hi = _finite_number(row.get("upper_bound"), f"{qid}.upper_bound")
        tol = _finite_number(row.get("absolute_precision_tolerance"), f"{qid}.absolute_precision_tolerance")
        alpha = _finite_number(row.get("risk_allocation"), f"{qid}.risk_allocation")
        if hi <= lo or tol <= 0 or not (0 < alpha < 1):
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_INVALID_QUANTITY_GEOMETRY:{qid}")
        expected_alpha = family_risk / 10.0
        if not math.isclose(alpha, expected_alpha, rel_tol=0.0, abs_tol=1e-15):
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_RISK_ALLOCATION_MISMATCH:{qid}")
        risk_sum += alpha
        expected_n = derive_hoeffding_fixed_n(hi - lo, tol, alpha)
        declared_n = row.get("replicates")
        if isinstance(declared_n, bool) or not isinstance(declared_n, int) or declared_n != expected_n:
            raise PrecisionAuthorityStop(f"STOP_PRECISION_AUTHORITY_REPLICATE_COUNT_MISMATCH:{qid}")
        maxima[str(kind)] = max(maxima[str(kind)], declared_n)

    if not math.isclose(risk_sum, family_risk, rel_tol=0.0, abs_tol=1e-12):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_RISK_ALLOCATION_MISMATCH:family")

    return {
        "passed": True,
        "terminal": "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1",
        "quantity_count": 10,
        "familywise_precision_risk": family_risk,
        "full_refit_null_replicates": maxima["null"],
        "donor_resamples": maxima["donor"],
        "operator_resamples": maxima["operator"],
        "training_authorized": False,
    }


def bind_precision_execution_plan_v1(
    authority: Mapping[str, object],
    *,
    authority_sha256: str,
) -> dict[str, object]:
    """Fail-closed pre-outcome execution plan for any future dimension metric producer."""
    if authority_sha256 != FROZEN_PRECISION_AUTHORITY_SHA256:
        raise PrecisionAuthorityStop("STOP_PRECISION_EXECUTION_PLAN_UNFROZEN_AUTHORITY_SHA")
    actual = hashlib.sha256(canonical_precision_authority_bytes(authority)).hexdigest()
    if actual != authority_sha256:
        raise PrecisionAuthorityStop("STOP_PRECISION_EXECUTION_PLAN_AUTHORITY_BYTES_MISMATCH")
    validated = validate_precision_authority_v1(authority)
    return {
        "schema": "JEPA_V5_DIMENSION_PRECISION_EXECUTION_PLAN_V1",
        "precision_authority_sha256": authority_sha256,
        "precision_authority_terminal": validated["terminal"],
        "precision_authority_frozen_before_dimension_outcomes": True,
        "null_replicates": validated["full_refit_null_replicates"],
        "donor_resamples": validated["donor_resamples"],
        "operator_resamples": validated["operator_resamples"],
        "rng_replay_policy": authority["rng_replay_policy"],
        "decision_metric_population": authority["decision_metric_population"],
        "estimator_failure_policy": authority["estimator_failure_policy"],
        "training_authorized": False,
    }


def bind_full104_precision_execution_plan_v1(
    authority: Mapping[str, object],
    *,
    authority_sha256: str,
    full104_dimension_envelope: Mapping[str, object],
    full104_artifact_sha256: str,
    dimension_interface_sha256: str,
) -> dict[str, object]:
    """Bind exact FULL104 dimension input and frozen precision policy before outcomes exist."""
    plan = bind_precision_execution_plan_v1(authority, authority_sha256=authority_sha256)
    expected_full104_sha = _require_sha256(full104_artifact_sha256, "full104_artifact_sha256")
    expected_interface_sha = _require_sha256(dimension_interface_sha256, "dimension_interface_sha256")

    envelope_sha = full104_dimension_envelope.get("artifact_sha256") if isinstance(full104_dimension_envelope, Mapping) else None
    if envelope_sha != expected_full104_sha:
        raise PrecisionAuthorityStop("STOP_PRECISION_BINDING_FULL104_ARTIFACT_SHA_MISMATCH")

    authority_interface_sha = authority.get("dimension_interface_sha256")
    if expected_interface_sha != authority_interface_sha:
        raise PrecisionAuthorityStop("STOP_PRECISION_BINDING_DIMENSION_INTERFACE_SHA_MISMATCH")

    try:
        full104_payload = validate_full104_dimension_input(full104_dimension_envelope)
    except (ValueError, RuntimeError) as exc:
        raise PrecisionAuthorityStop("STOP_PRECISION_BINDING_FULL104_DIMENSION_INPUT_INVALID") from exc

    parents = authority.get("full104_parent_bindings")
    if not isinstance(parents, Mapping):
        raise PrecisionAuthorityStop("STOP_PRECISION_AUTHORITY_PARENT_BINDINGS_INCOMPLETE")
    for field in sorted(_REQUIRED_PARENT_KEYS):
        if full104_payload.get(field) != parents.get(field):
            raise PrecisionAuthorityStop(f"STOP_PRECISION_BINDING_FULL104_PARENT_MISMATCH:{field}")

    out = dict(plan)
    out.update({
        "schema": "JEPA_V5_FULL104_PRECISION_PREOUTCOME_BINDING_V1",
        "full104_dimension_input_artifact_sha256": expected_full104_sha,
        "dimension_interface_sha256": expected_interface_sha,
        "all_full104_parents_match_precision_authority": True,
        "dimension_outcomes_authorized": True,
        "training_authorized": False,
    })
    return out
