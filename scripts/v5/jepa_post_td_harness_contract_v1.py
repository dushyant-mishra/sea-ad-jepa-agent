from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Iterable, Mapping


class PostTDContractError(ValueError):
    pass


PORTFOLIO_SCHEMA = "JEPA_POST_TD_TARGET_PORTFOLIO_V1"
ARCHITECTURE_SCHEMA = "JEPA_POST_TD_ARCHITECTURE_PLAN_V1"
REHEARSAL_SCHEMA = "JEPA_POST_TD_SYNTHETIC_REHEARSAL_PREFLIGHT_V1"

_AUTHORITY_OFF = {
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}

_BLOCKS = {
    "C1": {"block_id": "C1_SHARED", "candidate": "C1", "block_type": "SHARED"},
    "C2": {"block_id": "C2_RELATIONAL", "candidate": "C2", "block_type": "RELATIONAL"},
    "C3": {"block_id": "C3_QUERY", "candidate": "C3", "block_type": "QUERY"},
    "C5": {"block_id": "C5_SPECIALIST", "candidate": "C5", "block_type": "SPECIALIST"},
}

_COMPOSITE_EXPANSION = {
    "C6": ("C1", "C3"),
    "C4": ("C1", "C3", "C2"),
}

_COMPOSITE_REQUIRED_PASSES = {
    "C6": ("C1", "C3", "C6"),
    "C4": ("C1", "C2", "C3", "C4"),
}

_RUNTIME_FILES = (
    "src/sea_ad_jepa/v4/teacher_student_runtime.py",
    "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
    "src/sea_ad_jepa/v4/ema.py",
    "src/sea_ad_jepa/v4/ipb_jepa.py",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _qualification_status(value: object) -> str:
    if isinstance(value, str):
        return value.upper()
    if isinstance(value, Mapping):
        raw = value.get("status")
        if isinstance(raw, str):
            return raw.upper()
    return ""


def _require_pass(qualifications: Mapping[str, object], candidate: str) -> object:
    receipt = qualifications.get(candidate)
    if _qualification_status(receipt) != "PASS":
        raise PostTDContractError(f"{candidate} must be PASS before it can enter a target portfolio")
    return receipt


def _portfolio_block(candidate: str, qualification_receipt: object) -> dict:
    block = dict(_BLOCKS[candidate])
    block["qualification_receipt"] = qualification_receipt
    block["rare_preservation_cross_cutting"] = True
    return block


def build_target_portfolio(
    *,
    qualifications: Mapping[str, object],
    selected_candidate: str | None = None,
    foundation_candidates: Iterable[str] = (),
    specialist_candidates: Iterable[str] = (),
) -> dict:
    foundations = tuple(str(x).upper() for x in foundation_candidates)
    selected = None if selected_candidate is None else str(selected_candidate).upper()
    if selected is not None and foundations:
        raise PostTDContractError("use selected_candidate or foundation_candidates, not both")

    fused_candidate = None
    if selected is not None:
        if selected == "C5":
            raise PostTDContractError("C5 is specialist-only and cannot be the foundation portfolio")
        if selected not in {"C1", "C2", "C3", "C4", "C6"}:
            raise PostTDContractError(f"unknown target candidate: {selected}")
        if selected in _COMPOSITE_REQUIRED_PASSES:
            for candidate in _COMPOSITE_REQUIRED_PASSES[selected]:
                _require_pass(qualifications, candidate)
            foundations = _COMPOSITE_EXPANSION[selected]
            fused_candidate = selected
        else:
            _require_pass(qualifications, selected)
            foundations = (selected,)
    else:
        if not foundations:
            raise PostTDContractError("at least one foundation candidate is required")
        if len(foundations) != len(set(foundations)):
            raise PostTDContractError("foundation candidates must be unique")
        unknown = set(foundations) - {"C1", "C2", "C3"}
        if "C5" in foundations:
            raise PostTDContractError("C5 is specialist-only and cannot be the foundation portfolio")
        if unknown:
            raise PostTDContractError(f"unknown foundation candidate(s): {sorted(unknown)}")
        for candidate in foundations:
            _require_pass(qualifications, candidate)

    blocks = [
        _portfolio_block(candidate, _require_pass(qualifications, candidate))
        for candidate in foundations
    ]

    specialists = tuple(str(x).upper() for x in specialist_candidates)
    if len(specialists) != len(set(specialists)):
        raise PostTDContractError("specialist candidates must be unique")
    for specialist in specialists:
        if specialist != "C5":
            raise PostTDContractError(f"unknown specialist candidate: {specialist}")
        blocks.append(_portfolio_block(specialist, _require_pass(qualifications, specialist)))

    result = {
        "schema": PORTFOLIO_SCHEMA,
        "selected_candidate": selected,
        "foundation_candidates": list(foundations),
        "fused_candidate": fused_candidate,
        "specialist_candidates": list(specialists),
        "blocks": blocks,
        "qualifications": {str(k): v for k, v in sorted(qualifications.items(), key=lambda item: str(item[0]))},
        "authority": dict(_AUTHORITY_OFF),
    }
    result["portfolio_sha256"] = _canonical_sha256(result)
    return result


def allowed_teacher_policies(block_type: str) -> tuple[str, ...]:
    block = str(block_type).upper()
    if block == "QUERY":
        return (
            "RICH_Q_VISIBLE_REFERENCE",
            "RICH_Q_BLIND_COMPLEMENTARY",
            "SAME_EVIDENCE_Q_BLIND_CONTROL",
            "RESIDUAL_DIAGNOSTIC",
        )
    if block in {"SHARED", "RELATIONAL", "SPECIALIST"}:
        values = ["RICH_COMPLEMENTARY", "SAME_EVIDENCE_CONTROL"]
        if block in {"SHARED", "RELATIONAL"}:
            values.append("WHOLE_BLOCK_BLIND_CONDITIONAL")
        return tuple(values)
    raise PostTDContractError(f"unknown biological block type: {block}")


def derive_teacher_evidence_set(
    *,
    policy: str,
    measured_addresses: Iterable[int],
    student_visible_addresses: Iterable[int],
    query_address: int | None,
    target_block_addresses: Iterable[int],
) -> frozenset[int]:
    """Derive lawful teacher evidence without reading expression values.

    This is a structural mask constructor. It cannot select a target, infer biology,
    or grant training authority.
    """
    value = str(policy).upper()
    measured = frozenset(int(x) for x in measured_addresses)
    student = frozenset(int(x) for x in student_visible_addresses)
    block = frozenset(int(x) for x in target_block_addresses)
    if not student <= measured:
        raise PostTDContractError("student-visible evidence must be a subset of measured evidence")
    if not block <= measured:
        raise PostTDContractError("target block must be a subset of measured evidence")
    if query_address is not None and int(query_address) not in measured:
        raise PostTDContractError("query address must be measured when supplied")
    query = None if query_address is None else int(query_address)

    if value == "RICH_Q_VISIBLE_REFERENCE":
        if query is None:
            raise PostTDContractError("RICH_Q_VISIBLE_REFERENCE requires a query address")
        return measured
    if value == "RICH_Q_BLIND_COMPLEMENTARY":
        if query is None:
            raise PostTDContractError("RICH_Q_BLIND_COMPLEMENTARY requires a query address")
        return frozenset(x for x in measured if x != query)
    if value == "SAME_EVIDENCE_Q_BLIND_CONTROL":
        if query is None:
            raise PostTDContractError("SAME_EVIDENCE_Q_BLIND_CONTROL requires a query address")
        return frozenset(x for x in student if x != query)
    if value == "WHOLE_BLOCK_BLIND_CONDITIONAL":
        return measured - block
    if value == "RICH_COMPLEMENTARY":
        return measured
    if value == "SAME_EVIDENCE_CONTROL":
        return student
    if value == "RESIDUAL_DIAGNOSTIC":
        if query is None:
            raise PostTDContractError("RESIDUAL_DIAGNOSTIC requires a query address")
        return measured
    raise PostTDContractError(f"unknown teacher evidence policy: {value}")


def validate_teacher_topology(
    topology: str,
    *,
    interference_established: bool,
    multimodal_authorized: bool = False,
) -> str:
    value = str(topology).upper()
    if value in {"SINGLE_RICH", "SHARED_TYPED_HEADS"}:
        return value
    if value == "INDEPENDENT_COMPLEMENTARY_TEAM":
        if not interference_established:
            raise PostTDContractError("independent teacher team requires prospectively established interference")
        return value
    if value == "RNA_PLUS_PRIVILEGED_CRITICS":
        if not multimodal_authorized:
            raise PostTDContractError("privileged critics require separate multimodal authority")
        return value
    raise PostTDContractError(f"unknown teacher topology: {value}")


def validate_student_topology(topology: str, *, negative_transfer_established: bool) -> str:
    value = str(topology).upper()
    if value in {"SINGLE_SHARED", "SHARED_TYPED_HEADS"}:
        return value
    if value in {"CORE_PLUS_SPECIALISTS", "LIGHT_SHARED_STEM_PLUS_SPECIALISTS"}:
        if not negative_transfer_established:
            raise PostTDContractError("specialist student topology requires prospectively established negative-transfer evidence")
        return value
    raise PostTDContractError(f"unknown student topology: {value}")


_OUTPUT_SEMANTICS = {
    "POINT_STATE": {"point_loss_allowed": True, "direct_target_loss_required": True},
    "CONDITIONAL_MEAN": {"point_loss_allowed": True, "direct_target_loss_required": True},
    "STATE_PLUS_UNCERTAINTY": {"point_loss_allowed": True, "direct_target_loss_required": True},
    "CONDITIONAL_DISTRIBUTION": {"point_loss_allowed": False, "direct_target_loss_required": True},
    "TEACHER_PRIVATE_CRITIC_ONLY": {"point_loss_allowed": False, "direct_target_loss_required": False},
    "ABSTAIN_NOT_ESTIMABLE": {"point_loss_allowed": False, "direct_target_loss_required": False},
}


def output_semantics_spec(semantics: str) -> dict:
    value = str(semantics).upper()
    if value not in _OUTPUT_SEMANTICS:
        raise PostTDContractError(f"unknown student output semantics: {value}")
    return {"semantics": value, **_OUTPUT_SEMANTICS[value]}


def ema_momentum_for_presentations(successful_presentations: int, half_life_presentations: int | float) -> float:
    presentations = int(successful_presentations)
    half_life = float(half_life_presentations)
    if presentations < 0:
        raise PostTDContractError("successful presentations must be non-negative")
    if not math.isfinite(half_life) or half_life <= 0:
        raise PostTDContractError("EMA half-life must be finite and positive")
    return math.exp(math.log(0.5) * presentations / half_life)


def adjudicate_noncompensation(
    *,
    block_results: Mapping[str, str],
    allow_not_estimable: set[str],
    aggregate_score: float | None = None,
) -> dict:
    allowed_statuses = {"PASS", "FAIL", "NOT_ESTIMABLE"}
    failed: list[str] = []
    declared_ne: list[str] = []
    for block, raw_status in block_results.items():
        status = str(raw_status).upper()
        if status not in allowed_statuses:
            raise PostTDContractError(f"unknown block result for {block}: {status}")
        if status == "FAIL":
            failed.append(str(block))
        elif status == "NOT_ESTIMABLE":
            if block in allow_not_estimable:
                declared_ne.append(str(block))
            else:
                failed.append(str(block))
    if failed:
        status = "FAIL"
    elif declared_ne:
        status = "PASS_WITH_DECLARED_NOT_ESTIMABLE"
    else:
        status = "PASS"
    return {
        "status": status,
        "failed_blocks": sorted(failed),
        "declared_not_estimable_blocks": sorted(declared_ne),
        "aggregate_score": aggregate_score,
        "aggregate_score_has_authority": False,
    }


@dataclass(frozen=True)
class MatchedComputeContract:
    trainable_parameters: int
    teacher_flops: float
    student_flops: float
    cell_presentations: int
    optimizer_updates: int
    evaluation_exposures: int
    evidence_budget: float
    mask_budget: float
    hardware_class: str


def validate_matched_compute(
    reference: MatchedComputeContract,
    challenger: MatchedComputeContract,
    *,
    parameter_relative_tolerance: float = 0.02,
    flop_relative_tolerance: float = 0.02,
) -> dict:
    if parameter_relative_tolerance < 0 or flop_relative_tolerance < 0:
        raise PostTDContractError("matched-compute tolerances must be non-negative")
    r = asdict(reference)
    c = asdict(challenger)
    exact_fields = (
        "cell_presentations",
        "optimizer_updates",
        "evaluation_exposures",
        "evidence_budget",
        "mask_budget",
        "hardware_class",
    )
    for field in exact_fields:
        if r[field] != c[field]:
            raise PostTDContractError(f"matched-compute mismatch: {field}")

    def relative_difference(a: float, b: float) -> float:
        denom = max(abs(float(a)), abs(float(b)), 1.0)
        return abs(float(a) - float(b)) / denom

    if relative_difference(reference.trainable_parameters, challenger.trainable_parameters) > parameter_relative_tolerance:
        raise PostTDContractError("matched-compute mismatch: trainable_parameters")
    for field in ("teacher_flops", "student_flops"):
        if relative_difference(r[field], c[field]) > flop_relative_tolerance:
            raise PostTDContractError(f"matched-compute mismatch: {field}")
    return {"status": "MATCHED_COMPUTE_PASS", "reference": r, "challenger": c}


def required_evaluator_gates(*, block_types: Iterable[str], rare_preservation_required: bool) -> tuple[str, ...]:
    blocks = {str(x).upper() for x in block_types}
    unknown = blocks - {"SHARED", "QUERY", "RELATIONAL", "SPECIALIST"}
    if unknown:
        raise PostTDContractError(f"unknown evaluator block types: {sorted(unknown)}")
    gates = [
        "HELD_DONOR_TRANSPORT",
        "EVIDENCE_RESPONSE",
        "DEPTH_RESPONSE",
        "SUPPORT_NOT_ESTIMABLE",
        "SUBSPACE_HEALTH",
    ]
    if "QUERY" in blocks:
        gates.extend(["QUERY_SPECIFICITY", "WRONG_Q_CONTROL"])
    if "RELATIONAL" in blocks:
        gates.append("RELATIONAL_PRESERVATION")
    if "SPECIALIST" in blocks:
        gates.extend(["SOURCE_OPERATOR_CONTROL", "MEASUREMENT_QUALITY_CONTROL"])
    if rare_preservation_required:
        gates.append("RARE_PRESERVATION")
    return tuple(dict.fromkeys(gates))


def validate_internal_factorization(mode: str, *, block_count: int) -> str:
    value = str(mode).upper()
    if block_count < 1:
        raise PostTDContractError("block_count must be positive")
    if value == "GLOBAL_OPF" and block_count > 1:
        raise PostTDContractError("GLOBAL_OPF is forbidden across biological blocks")
    allowed = {"NONE", "MULTIHEAD_CONTROL", "FIXED_ORTHOGONAL", "BLOCKWISE_OPF", "GLOBAL_OPF"}
    if value not in allowed:
        raise PostTDContractError(f"unknown internal factorization: {value}")
    return value


def _default_teacher_policy(block_type: str) -> str:
    block = block_type.upper()
    if block == "QUERY":
        return "RICH_Q_BLIND_COMPLEMENTARY"
    return "RICH_COMPLEMENTARY"


def build_architecture_plan(
    *,
    portfolio: Mapping,
    ema_half_life_presentations: int | None,
    teacher_topology: str = "SHARED_TYPED_HEADS",
    student_topology: str = "SHARED_TYPED_HEADS",
    internal_factorization: str = "NONE",
    interference_established: bool = False,
    negative_transfer_established: bool = False,
    multimodal_authorized: bool = False,
) -> dict:
    if portfolio.get("schema") != PORTFOLIO_SCHEMA:
        raise PostTDContractError("invalid target portfolio schema")
    if ema_half_life_presentations is None:
        raise PostTDContractError("explicit EMA half-life in successful presentations is required")
    ema_half_life_presentations = int(ema_half_life_presentations)
    ema_momentum_for_presentations(1, ema_half_life_presentations)
    teacher = validate_teacher_topology(
        teacher_topology,
        interference_established=interference_established,
        multimodal_authorized=multimodal_authorized,
    )
    student = validate_student_topology(
        student_topology,
        negative_transfer_established=negative_transfer_established,
    )
    blocks = list(portfolio.get("blocks", ()))
    factorization = validate_internal_factorization(internal_factorization, block_count=len(blocks))
    teacher_policies = {
        block["block_id"]: _default_teacher_policy(block["block_type"])
        for block in blocks
    }
    output_semantics = {
        block["block_id"]: {
            **output_semantics_spec("CONDITIONAL_MEAN"),
            "production_selection_authority": False,
            "use": "MECHANICS_REHEARSAL_PLACEHOLDER_ONLY",
        }
        for block in blocks
    }
    result = {
        "schema": ARCHITECTURE_SCHEMA,
        "status": "IMPLEMENTATION_PLAN_ONLY__TRAINING_OFF",
        "portfolio_sha256": portfolio.get("portfolio_sha256"),
        "teacher_topology": teacher,
        "teacher_policies": teacher_policies,
        "student_topology": student,
        "output_semantics": output_semantics,
        "ema": {
            "native_unit": "SUCCESSFUL_BASE_CELL_PRESENTATIONS",
            "half_life_presentations": ema_half_life_presentations,
            "production_half_life_selected": False,
        },
        "internal_factorization": factorization,
        "authority": dict(_AUTHORITY_OFF),
    }
    result["architecture_sha256"] = _canonical_sha256(result)
    return result


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_runtime_identity(repo_root: Path | str) -> dict[str, str]:
    root = Path(repo_root).resolve()
    identity: dict[str, str] = {}
    for relative in _RUNTIME_FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise PostTDContractError(f"canonical runtime file missing or symlinked: {relative}")
        identity[relative] = _sha256_file(path)
    return identity


def build_synthetic_rehearsal_preflight(
    *,
    repo_root: Path | str,
    portfolio: Mapping,
    architecture_plan: Mapping,
    synthetic_package_sha256: str,
    output_root: Path | str,
) -> dict:
    if portfolio.get("schema") != PORTFOLIO_SCHEMA:
        raise PostTDContractError("invalid target portfolio schema")
    if architecture_plan.get("schema") != ARCHITECTURE_SCHEMA:
        raise PostTDContractError("invalid architecture plan schema")
    if architecture_plan.get("portfolio_sha256") != portfolio.get("portfolio_sha256"):
        raise PostTDContractError("architecture plan is not bound to this target portfolio")
    if not isinstance(synthetic_package_sha256, str) or not _HEX64.fullmatch(synthetic_package_sha256):
        raise PostTDContractError("synthetic package SHA-256 must be lowercase 64-hex")
    output = Path(output_root)
    if output.is_symlink() or not output.is_dir():
        raise PostTDContractError("rehearsal output root must be an existing non-symlink directory")
    runtime_identity = build_runtime_identity(repo_root)
    return {
        "schema": REHEARSAL_SCHEMA,
        "status": "READY_FOR_SYNTHETIC_REHEARSAL_ONLY",
        "portfolio_sha256": portfolio.get("portfolio_sha256"),
        "architecture_sha256": architecture_plan.get("architecture_sha256"),
        "synthetic_package_sha256": synthetic_package_sha256,
        "runtime_identity": runtime_identity,
        "runtime_identity_sha256": _canonical_sha256(runtime_identity),
        "output_root": str(output.resolve()),
        "authority": {
            **_AUTHORITY_OFF,
            "real_data_authorized": False,
            "synthetic_training_authorized": False,
        },
    }
