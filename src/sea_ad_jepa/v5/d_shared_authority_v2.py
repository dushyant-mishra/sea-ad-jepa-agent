from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping, Sequence

from .full104_dimension_interface_v1 import validate_full104_dimension_input


class DSharedAuthorityStop(RuntimeError):
    pass


FROZEN_D_SHARED_AUTHORITY_V2_SHA256 = "f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2"
_EXPECTED_QIDS = {
    "shared_matched_null_exceedance",
    "shared_subspace_stability",
    "shared_held_donor_cross_view_predictability",
    "shared_independent_view_agreement",
    "shared_measurement_shortcut_increment",
}
_EXPECTED_MATCHING = ["donor", "operator", "Q_DEPTH", "Q_DETECT", "support_measurability"]
_EXPECTED_GENERATOR = "DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1"
_EXPECTED_EFFECT = "SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1"
_EXPECTED_ALPHA = 0.05 / (10 * 512)
_EXPECTED_PARENT_KEYS = {
    "block_manifest_sha256",
    "materialization_contract_sha256",
    "materialization_audit_sha256",
    "selection_sha256",
    "selection_manifest_sha256",
    "metadata_sqlite_sha256",
}


def canonical_d_shared_authority_bytes(authority: Mapping[str, object]) -> bytes:
    if not isinstance(authority, Mapping):
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_NOT_MAPPING")
    return (json.dumps(authority, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _hoeffding_n(range_width: float, eps: float, alpha: float) -> int:
    return int(math.ceil((range_width * range_width * math.log(2.0 / alpha)) / (2.0 * eps * eps)))


def validate_d_shared_authority_v2(authority: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(authority, Mapping):
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_NOT_MAPPING")
    if authority.get("schema") != "JEPA_V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_SCHEMA")
    if authority.get("status") != "FROZEN_BEFORE_D_SHARED_OUTCOME_ACCESS":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_STATUS")
    if (authority.get("rank_min"), authority.get("rank_max"), authority.get("rank_count")) != (1, 512, 512):
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_RANK_ENVELOPE")
    if authority.get("quantity_family_count_for_precision") != 10:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_QUANTITY_FAMILY_COUNT")
    alpha = authority.get("alpha_per_quantity_rank")
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isclose(float(alpha), _EXPECTED_ALPHA, rel_tol=0.0, abs_tol=1e-15):
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_RISK_ALLOCATION")
    if authority.get("risk_allocation_method") != "BONFERRONI_EQUAL_QUANTITY_BY_RANK_10X512":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_RISK_METHOD")
    if authority.get("precision_method") != "HOEFFDING_FIXED_N_V1":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_PRECISION_METHOD")
    if authority.get("matched_null_generator") != _EXPECTED_GENERATOR:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_MATCHED_NULL_GENERATOR")
    if authority.get("matching_tuple") != _EXPECTED_MATCHING:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_MATCHING_TUPLE")
    if authority.get("matching_state_discreteness_required") is not True:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_MATCHING_DISCRETENESS_RULE")
    if authority.get("effect_criterion") != _EXPECTED_EFFECT:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_EFFECT_CRITERION")
    if authority.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_NULL_GEOMETRY")
    if authority.get("rng_replay_policy") != "SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_RNG_POLICY")
    if authority.get("decision_metric_population") != "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_POPULATION")
    if authority.get("estimator_failure_policy") != "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY":
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_FAILURE_POLICY")
    parents = authority.get("full104_parent_bindings")
    if not isinstance(parents, Mapping) or set(parents) != _EXPECTED_PARENT_KEYS:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_PARENT_BINDINGS")
    provenance = authority.get("supersedes_for_d_shared_execution")
    if not isinstance(provenance, Mapping) or provenance.get("v1_outcomes_generated") is not False:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_SUPERSESSION_PROVENANCE")
    for field in ("survivor_only_intervals_forbidden","post_outcome_replication_tuning_forbidden","gate_ablation_required","redundancy_identity_check_required","precision_is_not_effect_criterion"):
        if authority.get(field) is not True:
            raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_REQUIRED_TRUE:{field}")
    for field in ("outcomes_inspected_before_freeze","d_shared_outcomes_used","checkpoint_outcomes_used","pathology_used","protected_data_used","d_private_execution_authorized","d_obs_execution_authorized","training_authorized","td60_authorized","relational_target_activation_authorized"):
        if authority.get(field) is not False:
            raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_PRE_FREEZE_ACCESS:{field}")
    quantities = authority.get("quantities")
    if not isinstance(quantities, Sequence) or isinstance(quantities, (str, bytes)) or len(quantities) != 5:
        raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_QUANTITY_COUNT")
    seen: set[str] = set(); plan: dict[str, dict[str, object]] = {}
    for row in quantities:
        if not isinstance(row, Mapping): raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_QUANTITY_NOT_MAPPING")
        qid = row.get("quantity_id")
        if qid not in _EXPECTED_QIDS or qid in seen: raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_QUANTITY_ID")
        seen.add(str(qid))
        if (row.get("rank_min"), row.get("rank_max")) != (1, 512): raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_RANK_ENVELOPE:{qid}")
        lo, hi, eps, row_alpha = row.get("lower_bound"), row.get("upper_bound"), row.get("absolute_precision_tolerance"), row.get("risk_allocation_per_rank")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in (lo,hi,eps,row_alpha)): raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_QUANTITY_NUMERIC:{qid}")
        if not math.isclose(float(row_alpha), _EXPECTED_ALPHA, rel_tol=0.0, abs_tol=1e-15): raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_RISK_ALLOCATION:{qid}")
        expected = _hoeffding_n(float(hi)-float(lo), float(eps), float(row_alpha))
        if row.get("replicates_per_rank") != expected: raise DSharedAuthorityStop(f"STOP_D_SHARED_AUTHORITY_REPLICATE_COUNT:{qid}")
        plan[str(qid)] = {"replicates_per_rank":expected,"rank_min":1,"rank_max":512,"lower_bound":float(lo),"upper_bound":float(hi),"absolute_precision_tolerance":float(eps),"risk_allocation_per_rank":float(row_alpha)}
    if seen != _EXPECTED_QIDS: raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_QUANTITY_SET")
    return {"passed":True,"terminal":"PASS_V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2","rank_count":512,"alpha_per_quantity_rank":_EXPECTED_ALPHA,"matched_null_generator":_EXPECTED_GENERATOR,"matching_tuple":list(_EXPECTED_MATCHING),"effect_criterion":_EXPECTED_EFFECT,"quantity_plan":plan,"training_authorized":False}


def bind_d_shared_execution_plan_v2(authority: Mapping[str, object], *, authority_sha256: str) -> dict[str, object]:
    if authority_sha256 != FROZEN_D_SHARED_AUTHORITY_V2_SHA256: raise DSharedAuthorityStop("STOP_D_SHARED_EXECUTION_PLAN_UNFROZEN_AUTHORITY_SHA")
    if hashlib.sha256(canonical_d_shared_authority_bytes(authority)).hexdigest() != authority_sha256: raise DSharedAuthorityStop("STOP_D_SHARED_EXECUTION_PLAN_AUTHORITY_BYTES_MISMATCH")
    validated = validate_d_shared_authority_v2(authority)
    return {"schema":"JEPA_V5_D_SHARED_PRECISION_EXECUTION_PLAN_V2","d_shared_authority_v2_sha256":authority_sha256,"authority_terminal":validated["terminal"],"rank_min":1,"rank_max":512,"rank_count":512,"quantity_plan":validated["quantity_plan"],"matched_null_generator":validated["matched_null_generator"],"matching_tuple":validated["matching_tuple"],"effect_criterion":validated["effect_criterion"],"rng_replay_policy":authority["rng_replay_policy"],"decision_metric_population":authority["decision_metric_population"],"estimator_failure_policy":authority["estimator_failure_policy"],"informational_max_replicates_per_rank":max(int(v["replicates_per_rank"]) for v in validated["quantity_plan"].values()),"d_shared_metric_execution_authorized":True,"d_private_execution_authorized":False,"d_obs_execution_authorized":False,"training_authorized":False}


def bind_full104_d_shared_preoutcome_v2(authority: Mapping[str, object], *, authority_sha256: str, full104_dimension_envelope: Mapping[str, object], full104_artifact_sha256: str, dimension_interface_sha256: str, superseded_v1_precision_sha256: str, superseded_v1_cross_binding_sha256: str) -> dict[str, object]:
    plan = bind_d_shared_execution_plan_v2(authority, authority_sha256=authority_sha256)
    if full104_artifact_sha256 != authority.get("full104_dimension_input_artifact_sha256") or full104_dimension_envelope.get("artifact_sha256") != full104_artifact_sha256:
        raise DSharedAuthorityStop("STOP_D_SHARED_V2_FULL104_ARTIFACT_SHA_MISMATCH")
    if dimension_interface_sha256 != authority.get("dimension_interface_sha256"):
        raise DSharedAuthorityStop("STOP_D_SHARED_V2_DIMENSION_INTERFACE_SHA_MISMATCH")
    provenance = authority.get("supersedes_for_d_shared_execution")
    if not isinstance(provenance, Mapping) or superseded_v1_precision_sha256 != provenance.get("precision_authority_v1_sha256") or superseded_v1_cross_binding_sha256 != provenance.get("full104_precision_cross_binding_v1_sha256"):
        raise DSharedAuthorityStop("STOP_D_SHARED_V2_SUPERSEDED_V1_PROVENANCE_MISMATCH")
    try:
        payload = validate_full104_dimension_input(full104_dimension_envelope)
    except (ValueError, RuntimeError) as exc:
        raise DSharedAuthorityStop("STOP_D_SHARED_V2_FULL104_INPUT_INVALID") from exc
    parents = authority.get("full104_parent_bindings")
    if not isinstance(parents, Mapping): raise DSharedAuthorityStop("STOP_D_SHARED_AUTHORITY_PARENT_BINDINGS")
    for field in sorted(_EXPECTED_PARENT_KEYS):
        if payload.get(field) != parents.get(field): raise DSharedAuthorityStop(f"STOP_D_SHARED_V2_FULL104_PARENT_MISMATCH:{field}")
    return {**plan,"schema":"JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2","full104_dimension_input_artifact_sha256":full104_artifact_sha256,"dimension_interface_sha256":dimension_interface_sha256,"superseded_v1_precision_sha256":superseded_v1_precision_sha256,"superseded_v1_cross_binding_sha256":superseded_v1_cross_binding_sha256,"all_full104_parents_match_d_shared_authority_v2":True,"d_shared_metric_execution_authorized":True,"d_private_execution_authorized":False,"d_obs_execution_authorized":False,"training_authorized":False,"protected_data_authorized":False,"td60_authorized":False,"relational_target_activation_authorized":False}
