from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Iterable, Mapping


MODULE_NAME = "jepa_post_td_harness_contract_v1"
if MODULE_NAME in sys.modules:
    C = sys.modules[MODULE_NAME]
else:
    module_path = Path(__file__).with_name(f"{MODULE_NAME}.py")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    C = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = C
    spec.loader.exec_module(C)


class PostTDTournamentError(ValueError):
    pass


@dataclass(frozen=True)
class ArchitectureArm:
    arm_id: str
    teacher_topology: str
    student_topology: str
    internal_factorization: str
    ema_half_life_presentations: int


def _authority_off() -> dict:
    return {
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
        "real_data_authorized": False,
    }


def build_zero_update_teacher_screen(portfolio: Mapping) -> dict:
    if portfolio.get("schema") != C.PORTFOLIO_SCHEMA:
        raise PostTDTournamentError("invalid target portfolio schema")
    blocks = []
    for block in portfolio.get("blocks", ()):
        block_type = str(block.get("block_type", "")).upper()
        blocks.append({
            "block_id": block.get("block_id"),
            "block_type": block_type,
            "policies": list(C.allowed_teacher_policies(block_type)),
            "read_expression_values_before_freeze": False,
            "policy_selection_authorized": False,
        })
    if not blocks:
        raise PostTDTournamentError("target portfolio contains no blocks")
    return {
        "schema": "JEPA_POST_TD_ZERO_UPDATE_TEACHER_SCREEN_V1",
        "status": "READY_FOR_ZERO_UPDATE_TARGET_CONSTRUCTION_SCREEN__NO_TRAINING",
        "portfolio_sha256": portfolio.get("portfolio_sha256"),
        "blocks": blocks,
        "optimizer_updates": 0,
        "ema_updates": 0,
        "authority": _authority_off(),
    }


def supervision_record(state: str) -> dict:
    value = str(state).upper()
    if value == "ELIGIBLE":
        direct = True
    elif value in {"NOT_ESTIMABLE", "TEACHER_PRIVATE"}:
        direct = False
    else:
        raise PostTDTournamentError(f"unknown supervision eligibility state: {value}")
    return {
        "state": value,
        "direct_supervision_allowed": direct,
        "encode_missing_as_zero": False,
    }


_RECOVERABILITY_TO_SEMANTICS = {
    "POINT_IDENTIFIABLE": frozenset({"POINT_STATE", "CONDITIONAL_MEAN"}),
    "STOCHASTIC_IDENTIFIABLE": frozenset({"STATE_PLUS_UNCERTAINTY", "CONDITIONAL_DISTRIBUTION"}),
    "TEACHER_PRIVATE": frozenset({"TEACHER_PRIVATE_CRITIC_ONLY"}),
    "NOT_ESTIMABLE": frozenset({"ABSTAIN_NOT_ESTIMABLE"}),
}


def validate_recoverability_assignment(recoverability: str, semantics: str) -> str:
    r = str(recoverability).upper()
    s = str(semantics).upper()
    if r not in _RECOVERABILITY_TO_SEMANTICS:
        raise PostTDTournamentError(f"unknown recoverability class: {r}")
    C.output_semantics_spec(s)
    if s not in _RECOVERABILITY_TO_SEMANTICS[r]:
        raise PostTDTournamentError(f"{r} cannot be assigned student semantics {s}")
    return s


def _validate_arm(
    arm: ArchitectureArm,
    *,
    portfolio: Mapping,
    interference_established: bool,
    negative_transfer_established: bool,
    multimodal_authorized: bool,
) -> dict:
    if not isinstance(arm.arm_id, str) or not arm.arm_id.strip():
        raise PostTDTournamentError("architecture arm_id must be nonempty")
    teacher = C.validate_teacher_topology(
        arm.teacher_topology,
        interference_established=interference_established,
        multimodal_authorized=multimodal_authorized,
    )
    student = C.validate_student_topology(
        arm.student_topology,
        negative_transfer_established=negative_transfer_established,
    )
    blocks = list(portfolio.get("blocks", ()))
    factorization = C.validate_internal_factorization(
        arm.internal_factorization, block_count=len(blocks)
    )
    C.ema_momentum_for_presentations(1, arm.ema_half_life_presentations)
    return {
        **asdict(arm),
        "teacher_topology": teacher,
        "student_topology": student,
        "internal_factorization": factorization,
        "ema_native_unit": "SUCCESSFUL_BASE_CELL_PRESENTATIONS",
        "production_selection_authority": False,
    }


def build_architecture_tournament_manifest(
    *,
    portfolio: Mapping,
    arms: Iterable[ArchitectureArm],
    compute_contracts: Mapping[str, C.MatchedComputeContract],
    rare_preservation_required: bool,
    interference_established: bool = False,
    negative_transfer_established: bool = False,
    multimodal_authorized: bool = False,
) -> dict:
    if portfolio.get("schema") != C.PORTFOLIO_SCHEMA:
        raise PostTDTournamentError("invalid target portfolio schema")
    arm_list = list(arms)
    if not arm_list:
        raise PostTDTournamentError("at least one architecture arm is required")
    ids = [arm.arm_id for arm in arm_list]
    if len(set(ids)) != len(ids):
        raise PostTDTournamentError("architecture arm IDs must be unique")
    if set(compute_contracts) != set(ids):
        raise PostTDTournamentError("compute contract IDs must exactly match architecture arm IDs")

    validated = [
        _validate_arm(
            arm,
            portfolio=portfolio,
            interference_established=interference_established,
            negative_transfer_established=negative_transfer_established,
            multimodal_authorized=multimodal_authorized,
        )
        for arm in arm_list
    ]

    reference_id = ids[0]
    reference = compute_contracts[reference_id]
    compute_reports = {reference_id: {"status": "REFERENCE", "contract": asdict(reference)}}
    for arm_id in ids[1:]:
        report = C.validate_matched_compute(reference, compute_contracts[arm_id])
        compute_reports[arm_id] = report

    block_types = [str(block["block_type"]) for block in portfolio.get("blocks", ())]
    gates = C.required_evaluator_gates(
        block_types=block_types,
        rare_preservation_required=rare_preservation_required,
    )
    return {
        "schema": "JEPA_POST_TD_ARCHITECTURE_TOURNAMENT_MANIFEST_V1",
        "status": "READY_FOR_AUTHORIZED_SYNTHETIC_ARCHITECTURE_REHEARSAL",
        "portfolio_sha256": portfolio.get("portfolio_sha256"),
        "arms": validated,
        "reference_arm_id": reference_id,
        "compute_reports": compute_reports,
        "required_evaluator_gates": list(gates),
        "noncompensation_required": True,
        "aggregate_score_selection_authority": False,
        "authority": _authority_off(),
    }


def build_ema_screen_manifest(
    *,
    architecture_arm: ArchitectureArm,
    half_lives_presentations: Iterable[int],
) -> dict:
    values = [int(x) for x in half_lives_presentations]
    if len(values) != 3 or len(set(values)) != 3 or any(x <= 0 for x in values):
        raise PostTDTournamentError("EMA screen requires exactly three distinct positive half-lives")
    ordered = sorted(values)
    labels = ("SHORT", "INTERMEDIATE", "LONG")
    arms = []
    for label, half_life in zip(labels, ordered):
        C.ema_momentum_for_presentations(1, half_life)
        arms.append({
            "label": label,
            "half_life_presentations": half_life,
            "architecture_arm_id": architecture_arm.arm_id,
        })
    return {
        "schema": "JEPA_POST_TD_EMA_SCREEN_MANIFEST_V1",
        "status": "READY_FOR_AUTHORIZED_EMA_TIMESCALE_SCREEN",
        "native_unit": "SUCCESSFUL_BASE_CELL_PRESENTATIONS",
        "architecture_arm": asdict(architecture_arm),
        "arms": arms,
        "production_half_life_selected": False,
        "historical_fixed_beta_has_authority": False,
        "authority": _authority_off(),
    }


def reduce_architecture_evidence(
    *,
    arm_id: str,
    block_gate_results: Mapping[str, Mapping[str, str]],
    declared_not_estimable: set[str],
    aggregate_score: float | None,
) -> dict:
    if not isinstance(arm_id, str) or not arm_id:
        raise PostTDTournamentError("arm_id required")
    failures: list[str] = []
    declared: list[str] = []
    observed = 0
    for block_id, gate_results in block_gate_results.items():
        if not isinstance(gate_results, Mapping) or not gate_results:
            raise PostTDTournamentError(f"gate results required for block {block_id}")
        for gate, raw_status in gate_results.items():
            key = f"{block_id}:{gate}"
            status = str(raw_status).upper()
            observed += 1
            if status == "PASS":
                continue
            if status == "FAIL":
                failures.append(key)
                continue
            if status == "NOT_ESTIMABLE":
                if key in declared_not_estimable:
                    declared.append(key)
                else:
                    failures.append(key)
                continue
            raise PostTDTournamentError(f"unknown gate result {status!r} for {key}")
    if observed == 0:
        raise PostTDTournamentError("at least one block/gate result is required")
    if failures:
        status = "FAIL"
    elif declared:
        status = "PASS_WITH_DECLARED_NOT_ESTIMABLE"
    else:
        status = "PASS"
    return {
        "schema": "JEPA_POST_TD_ARCHITECTURE_EVIDENCE_REDUCTION_V1",
        "arm_id": arm_id,
        "status": status,
        "failed_block_gates": sorted(failures),
        "declared_not_estimable_block_gates": sorted(declared),
        "aggregate_score": aggregate_score,
        "aggregate_score_has_authority": False,
        "authority": _authority_off(),
    }
