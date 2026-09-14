from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class DSharedExecutionStop(RuntimeError):
    pass


AUTHORITY_SHA = "f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2"
PREOUTCOME_SCHEMA = "JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2"
MATCHED_NULL_GENERATOR = "DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1"
MATCHING_TUPLE = ["donor", "operator", "Q_DEPTH", "Q_DETECT", "support_measurability"]
QIDS = (
    "shared_matched_null_exceedance",
    "shared_subspace_stability",
    "shared_held_donor_cross_view_predictability",
    "shared_independent_view_agreement",
    "shared_measurement_shortcut_increment",
)


@dataclass(frozen=True)
class DSharedExecutionFirewallV2:
    expected_preoutcome_binding_sha256: str

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        if receipt.get("schema") != "JEPA_V5_D_SHARED_RAW_EXECUTION_RECEIPT_V1":
            raise DSharedExecutionStop("STOP_D_SHARED_V2_RECEIPT_SCHEMA")
        if receipt.get("preoutcome_binding_schema") != PREOUTCOME_SCHEMA:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_PREOUTCOME_BINDING_REQUIRED")
        if receipt.get("preoutcome_binding_sha256") != self.expected_preoutcome_binding_sha256:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_PREOUTCOME_BINDING_SHA_MISMATCH")
        if receipt.get("d_shared_authority_v2_sha256") != AUTHORITY_SHA:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_AUTHORITY_SHA_MISMATCH")
        if any(k in receipt for k in ("null_replicates", "donor_resamples", "operator_resamples")):
            raise DSharedExecutionStop("STOP_D_SHARED_V2_SCALAR_REPLICATE_AUTHORITY_FORBIDDEN")
        if receipt.get("population_mode") != "FULL_READER_FIT_STREAM":
            raise DSharedExecutionStop("STOP_D_SHARED_V2_NOT_FULL_STREAM")
        expected_geometry = {
            "reader_fit_rows_used": 4_553_407,
            "unique_stable_keys_used": 4_553_407,
            "donors_used": 104,
            "operators_used": 42,
            "addresses": 41_238,
        }
        for field, expected in expected_geometry.items():
            if receipt.get(field) != expected:
                raise DSharedExecutionStop(f"STOP_D_SHARED_V2_GEOMETRY_MISMATCH:{field}")
        for field in ("sampled_stratum_cap", "cells_per_stratum_cap", "row_cap"):
            if receipt.get(field) not in (None, "NONE", 0):
                raise DSharedExecutionStop(f"STOP_D_SHARED_V2_SUBSTRATE_CAPPED:{field}")
        if (receipt.get("rank_min"), receipt.get("rank_max")) != (1, 512):
            raise DSharedExecutionStop("STOP_D_SHARED_V2_RANK_ENVELOPE")
        if receipt.get("matched_null_generator") != MATCHED_NULL_GENERATOR:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_MATCHED_NULL_GENERATOR")
        if receipt.get("matching_tuple") != MATCHING_TUPLE:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_MATCHING_TUPLE")
        if receipt.get("matching_state_discreteness_verified") is not True:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_MATCHED_NULL_STRATIFICATION_UNSPECIFIED")
        if receipt.get("null_geometry") != "FULL_REFIT_EVERY_REPLICATE" or receipt.get("full_refit_every_null_replicate_verified") is not True:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_NULL_NOT_FULL_REFIT")
        if receipt.get("rng_replay_policy") != "SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2":
            raise DSharedExecutionStop("STOP_D_SHARED_V2_RNG_POLICY")
        if receipt.get("decision_metric_population") != "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION":
            raise DSharedExecutionStop("STOP_D_SHARED_V2_CONDITIONAL_DENOMINATOR")
        if receipt.get("estimator_failure_policy") != "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY":
            raise DSharedExecutionStop("STOP_D_SHARED_V2_FAILURE_POLICY")
        if receipt.get("estimator_failures_in_denominator") is not True:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_FAILURE_DROPPED")
        if receipt.get("post_outcome_replication_extension") is not False:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_POST_OUTCOME_EXTENSION")
        if receipt.get("rank_search_executed_before_metric_seal") is not False:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_RANK_SEARCH_BEFORE_SEAL")
        quantity_execution = receipt.get("quantity_execution")
        if not isinstance(quantity_execution, Mapping) or set(quantity_execution) != set(QIDS):
            raise DSharedExecutionStop("STOP_D_SHARED_V2_QUANTITY_EXECUTION_MISMATCH")
        expected_row = {"rank_min": 1, "rank_max": 512, "replicates_per_rank": 9784}
        for qid in QIDS:
            row = quantity_execution.get(qid)
            if not isinstance(row, Mapping) or dict(row) != expected_row:
                raise DSharedExecutionStop(f"STOP_D_SHARED_V2_QUANTITY_EXECUTION_MISMATCH:{qid}")
        for field in ("synthetic_data_used", "pathology_used", "protected_data_used", "checkpoint_outcomes_used", "training_authorized"):
            if receipt.get(field) is not False:
                raise DSharedExecutionStop(f"STOP_D_SHARED_V2_FORBIDDEN_STATE:{field}")
        if receipt.get("d_private_execution_attempted") is not False or receipt.get("d_obs_execution_attempted") is not False:
            raise DSharedExecutionStop("STOP_D_SHARED_V2_DOWNSTREAM_STAGE")
        return {
            "passed": True,
            "terminal": "PASS_V5_D_SHARED_EXECUTION_FIREWALL_V2",
            "d_shared_metric_execution_validated": True,
            "d_private_execution_authorized": False,
            "d_obs_execution_authorized": False,
            "training_authorized": False,
        }
