from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import td_relational_successor_capability_reducer_v1 as C
import td_relational_successor_gate_v1 as G
import td_relational_successor_geometry_v1 as M
import td_relational_successor_qualification_runner_v1 as Q
import td_relational_successor_synthetic_adapter_v1 as A


class ReadinessError(ValueError):
    pass


MANDATORY_CAPABILITIES = A.MANDATORY_RELATIONAL_CAPABILITIES
_EXECUTOR_FILES = (
    "scripts/v5/td_relational_successor_geometry_v1.py",
    "scripts/v5/td_relational_successor_estimability_v1.py",
    "scripts/v5/td_relational_successor_gate_v1.py",
    "scripts/v5/td_relational_successor_observed_executor_v1.py",
)
_DECISION_FILES = (
    "scripts/v5/td_relational_successor_capability_reducer_v1.py",
    "scripts/v5/td_test_of_test_controller_v1.py",
)
_AUTHORITY_KEYS = frozenset({
    "real_execution_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
})


@dataclass(frozen=True)
class MinimalQualificationReference:
    status: str
    package_sha256: str
    qualified_gate_executor_sha256: str
    estimand_sha256: str
    decision_rule_sha256: str


@dataclass(frozen=True)
class RelationalSuccessorReadinessReceipt:
    status: str
    binding: dict
    package_sha256: str | None
    qualification_status: str | None
    real_execution_authorized: bool
    authority: dict[str, bool]


def _canonical_sha256(value) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        raise ReadinessError(f"required TD implementation file missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_bundle(root: Path, paths: tuple[str, ...]) -> dict[str,str]:
    return {path:_file_sha256(root/path) for path in paths}


def build_relational_gate_binding(repo_root: Path | str) -> dict:
    root=Path(repo_root)
    executor_files=_code_bundle(root,_EXECUTOR_FILES)
    decision_files=_code_bundle(root,_DECISION_FILES)
    executor_identity={
        "schema":"JEPA_TD_RELATIONAL_SUCCESSOR_EXECUTOR_IDENTITY_V1",
        "files":executor_files,
    }
    estimand={
        "schema":"JEPA_TD_RELATIONAL_SUCCESSOR_ESTIMAND_V1",
        "view_feature_count":M.VIEW_FEATURE_COUNT,
        "pair_width":M.PAIR_WIDTH,
        "min_informative_coordinates":M.MIN_INFORMATIVE_COORDINATES,
        "scale_grid":[list(v) for v in G.SCALE_GRID],
        "min_neighbors":G.MIN_NEIGHBORS,
        "min_source_donors":G.MIN_SOURCE_DONORS,
        "min_resolved_relations_per_donor":G.MIN_RESOLVED_RELATIONS_PER_DONOR,
        "triplet_cap_per_stratum":G.TRIPLET_CAP_PER_STRATUM,
        "n_null":G.N_NULL,
        "null_p95_index":G.NULL_P95_INDEX,
        "distance":"mean_abs_pair_sign_difference_divided_by_2",
        "selector":"independent_Z_rank_locality",
        "tested_relation":"X_Y_anchored_triplet_order_agreement",
        "source_statistic":"median_donor_agreement",
        "multiplicity":"max_null_across_five_frozen_scales",
        "null":"TD37A_v1_1_donor_operator_depth_detection_block_Y_identity_shift",
    }
    decision_rule={
        "schema":"JEPA_TD_RELATIONAL_SUCCESSOR_DECISION_RULE_V1",
        "files":decision_files,
        "scale_pass":"observed_source_median_gt_0.5_AND_gt_family_max_null_p95",
        "fine_labels":["1/8","1/6","1/4","1/3"],
        "mesoscale_label":"1/2",
        "rare_increment":"program_margin_strictly_exceeds_max_matched_control_margin",
        "mandatory_rare_control_roles":list(Q.MANDATORY_CONTROL_ROLES),
        "capabilities":list(MANDATORY_CAPABILITIES),
        "underpowered_expected":"NOT_ESTIMABLE",
        "failure_scope":"TEST_QUALIFICATION_ONLY",
        "no_early_stopping":True,
        "no_candidate_or_dataset_elimination":True,
    }
    return {
        "qualified_gate_executor_sha256":_canonical_sha256(executor_identity),
        "estimand_sha256":_canonical_sha256(estimand),
        "decision_rule_sha256":_canonical_sha256(decision_rule),
        "failure_scope":"TEST_QUALIFICATION_ONLY",
        "required_capabilities":list(MANDATORY_CAPABILITIES),
        "executor_files":executor_files,
        "decision_files":decision_files,
        "estimand_manifest_sha256":_canonical_sha256(estimand),
        "decision_manifest_sha256":_canonical_sha256(decision_rule),
    }


def _reference_from_receipt(receipt) -> MinimalQualificationReference:
    if isinstance(receipt, MinimalQualificationReference):
        return receipt
    if isinstance(receipt, Q.RelationalQualificationRunReceipt):
        gate=receipt.gate_qualification
        if gate is None:
            return MinimalQualificationReference(
                receipt.status,
                receipt.package_sha256,
                "",
                "",
                "",
            )
        return MinimalQualificationReference(
            receipt.status,
            receipt.package_sha256,
            gate.executor_sha256,
            gate.estimand_sha256,
            gate.decision_rule_sha256,
        )
    raise ReadinessError("qualification_receipt has unsupported type")


def assess_relational_successor_readiness(
    *,
    binding: Mapping,
    external_package_present: bool,
    qualification_receipt=None,
) -> RelationalSuccessorReadinessReceipt:
    required={
        "qualified_gate_executor_sha256","estimand_sha256","decision_rule_sha256",
        "failure_scope","required_capabilities","executor_files","decision_files",
        "estimand_manifest_sha256","decision_manifest_sha256",
    }
    if not isinstance(binding,Mapping) or set(binding) != required:
        raise ReadinessError("binding fields differ from frozen readiness schema")
    authority={key:False for key in sorted(_AUTHORITY_KEYS)}
    if not external_package_present:
        return RelationalSuccessorReadinessReceipt(
            "BLOCKED_EXTERNAL_SYNTHETIC_PACKAGE_NOT_DELIVERED",dict(binding),None,None,False,authority
        )
    if qualification_receipt is None:
        return RelationalSuccessorReadinessReceipt(
            "BLOCKED_TEST_OF_TEST_QUALIFICATION_NOT_EXECUTED",dict(binding),None,None,False,authority
        )
    ref=_reference_from_receipt(qualification_receipt)
    if ref.status != "QUALIFIED":
        return RelationalSuccessorReadinessReceipt(
            "BLOCKED_TEST_OF_TEST_NOT_QUALIFIED",dict(binding),ref.package_sha256,ref.status,False,authority
        )
    identity=(
        ref.qualified_gate_executor_sha256 == binding["qualified_gate_executor_sha256"] and
        ref.estimand_sha256 == binding["estimand_sha256"] and
        ref.decision_rule_sha256 == binding["decision_rule_sha256"]
    )
    if not identity:
        return RelationalSuccessorReadinessReceipt(
            "BLOCKED_QUALIFICATION_IDENTITY_MISMATCH",dict(binding),ref.package_sha256,ref.status,False,authority
        )
    return RelationalSuccessorReadinessReceipt(
        "READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY",
        dict(binding),ref.package_sha256,ref.status,False,authority,
    )
