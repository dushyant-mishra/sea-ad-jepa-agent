#!/usr/bin/env python3
"""DEV2048 V5 pilot pre-flight: inputs, target leakage, EMA route and lineage.

NOT a trainer. Nothing here runs a forward or backward pass, an optimizer
step or an EMA update. ``run_authorized_one_update`` performs every check
below *before* it hands control to the single canonical PR224 V5 route,
and it refuses unless an owner authorization record is supplied; this draft
does not contain or create one. Tests replace the canonical route with a mock.

Encoder input mode
------------------
The only mode implemented is ``SHARED_BASE_MASKED_BLOCK_JEPA``: teacher and
student receive the *same* 2,044 base address values from PR547's
q-excluded student member; query addresses 1672-1675 are unmeasured for
both, and the student's visible set is that base minus the hidden target
blocks. The vocabulary still spans all 2,048 addresses. A teacher-only
query mode (teacher sees q values, student never does) is the historical
L04 EMERGENT/TRANSFER decision recorded as owner-pending
(``JEPA_SYNTH2048_V5_FINE_GRAIN_CHECKPOINT_PREFREEZE_V1.json``:
``L04_OWNER_DECISION_PENDING__NO_IMPLICIT_SHARED_Q_DESCENDANT_TO_C3``); it is
not implemented and must not be added silently.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from scripts.v5 import jepa_v5_pipeline_identity_contract_v1 as contract
from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

SCHEMA = "JEPA_V5_DEV2048_PILOT_PREFLIGHT_V1"
AUTHORITY = contract.AUTHORITY
ENCODER_INPUT_MODE = "SHARED_BASE_MASKED_BLOCK_JEPA"
TEACHER_ONLY_QUERY_MODE = "L04_OWNER_DECISION_PENDING__NOT_IMPLEMENTED"
Q = tuple(gate.DEV_QUERY_GENE_ADDRESSES)
CELL_KEY_OFFSET = 11_000_000          # PR548 stable-cell-key convention
TARGET_BLOCK_SEED = 8813003           # PR548 target-block production seed
RUN_SEED = 8113002
M1_ROWS = (1, 3, 8, 10, 28, 32, 34, 35, 49, 54, 65, 74, 79, 81, 83, 90)
AUTHORIZATION_SCHEMA = "JEPA_V5_DEV2048_PILOT_OWNER_AUTHORIZATION_V1"
AUTHORIZATION_FIELDS = {
    "schema", "milestone", "horizon", "rows", "half_life_presentations",
    "encoder_input_mode", "contract_sha256", "fit_zip_sha256",
    "premise_state_blob", "code_commit", "run_directory", "owner",
    "authorized_on", "expires_on", "owner_authorized",
}
# Static lineage: the canonical route and the V4 code it intentionally uses.
CANONICAL_ROUTE = ("sea_ad_jepa.v5.ema_bound_runtime_proof_v1",
                   "run_presentation_ema_bound_guarded_reference_update")
INTENTIONAL_V4 = {
    "src/sea_ad_jepa/v4/ipb_jepa.py": "BlockPredictor, TargetBlocks, gather_block_states, "
                                      "EncoderOutput, KernelLinearAttention",
    "src/sea_ad_jepa/v4/gene_tokenizer.py": "GeneExpressionTokenizer",
    "src/sea_ad_jepa/v4/contracts.py": "MECHANICS_CONTRACT (gene-identity width 48)",
    "src/sea_ad_jepa/v4/masking.py": "keyed_mask_seed",
    "src/sea_ad_jepa/v4/teacher_student_runtime.py": "sample_uniform_target_blocks only",
}
FORBIDDEN_LINEAGE = {
    "old V4 trainer": ("healthy_teacher_qualification_runner_v1", "production_update",
                       "build_teacher_student_components", "execute_scaled_backward"),
    "legacy V4 EMA": ("update_ema_target", "EMATargetEncoder", "create_ema_target",
                      "ema_target_module", "EMAOptimizerStepController"),
    "toy actor": ("TinyStudent", "online.value_encoder.weight"),
    "scalar-momentum route": ("run_guarded_inactive_reference_update",
                              "run_inactive_reference_update"),
}


class PilotPreflightRefusal(ValueError):
    pass


def refuse(reason: str) -> None:
    raise PilotPreflightRefusal("REFUSE_V5_DEV2048_PILOT_PREFLIGHT_V1__" + reason)


# --------------------------------------------------------------- inputs

def build_shared_base_inputs(fit_zip: Path, rows: tuple[int, ...] = M1_ROWS) -> dict:
    """One shared input for both encoders, from the q-excluded member only.

    Reuses the PR548 adapter (verified FIT bytes, address restoration with q
    unmeasured, roster audit). The teacher member is hashed by the adapter
    but never parsed here, so no query value or q-derived depth exists.
    """
    import numpy as np
    import torch
    from scripts.v5 import jepa_synth2048_v5_readiness as adapter
    receipt, student, roster = adapter.verified_fit(Path(fit_zip))
    full, support, _report = adapter.audit_fit(receipt, student, roster)
    index = np.asarray(rows, dtype=np.int64)
    if (len(set(rows)) != len(rows)
            or not bool(np.all(roster["split"][index] == "train"))
            or len(set(roster["synthetic_source"][index].tolist())) != 1):
        refuse("ROWS_NOT_UNIQUE_TRAIN_SINGLE_SOURCE")
    expression = torch.from_numpy(np.log1p(full[index]).astype(np.float32))
    measured = torch.from_numpy(support[index].copy())
    q = list(Q)
    if bool(measured[:, q].any()) or bool((expression[:, q] != 0).any()):
        refuse("QUERY_VALUE_OR_SUPPORT_IN_SHARED_BASE_INPUT")
    if bool((expression[~measured] != 0).any()):
        refuse("UNMEASURED_ADDRESS_CARRIES_VALUE")
    return {
        "mode": ENCODER_INPUT_MODE,
        "rows": tuple(int(r) for r in rows),
        "expression": expression,          # identical tensor for teacher and student
        "measurement_mask": measured,
        "stable_cell_keys": torch.as_tensor(index + CELL_KEY_OFFSET, dtype=torch.int64),
        "operator_ids": [0] * len(rows),
        "measured_tokens_by_operator": {0: int(measured.sum(dim=1).max())},
        "scientific_cell_weights": torch.ones(len(rows), dtype=torch.float32),
    }


def sample_m1_target_blocks(measurement_mask, stable_cell_keys, *, update_index: int = 0):
    """PR548's V4 block sampler (the only teacher_student_runtime use)."""
    from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
    return sample_uniform_target_blocks(
        measurement_mask, production_seed=TARGET_BLOCK_SEED,
        cell_indices=stable_cell_keys, sample_pass=update_index, view_index=0,
        mask_fraction=0.40, block_count=16)


def validate_target_blocks(blocks: Any, measurement_mask: Any) -> dict:
    """Refuse target leakage BEFORE any forward, backward or mutation.

    For every cell the valid block members must be exactly the hidden
    positions, each once, inside measured support and never a query address;
    padding must be -1. The runtime alone only checks hidden within support,
    so a member pointing at a still-visible gene would be predicted from a
    value the student can see.
    """
    import torch
    hidden, indices, members = blocks.hidden_mask, blocks.indices, blocks.member_mask
    cells, genes = measurement_mask.shape
    if (hidden.shape != measurement_mask.shape or hidden.dtype != torch.bool
            or indices.ndim != 3 or members.shape != indices.shape
            or members.dtype != torch.bool or indices.shape[0] != cells):
        refuse("TARGET_BLOCK_SHAPE")
    if bool((hidden & ~measurement_mask).any()):
        refuse("TARGET_BLOCK_OUTSIDE_MEASURED_SUPPORT")
    if bool((indices[~members] != -1).any()):
        refuse("TARGET_BLOCK_PADDING_NOT_EMPTY")
    for row in range(cells):
        valid = indices[row][members[row]]
        if bool(((valid < 0) | (valid >= genes)).any()):
            refuse("TARGET_BLOCK_INDEX_OUT_OF_RANGE")
        listed = valid.tolist()
        if len(listed) != len(set(listed)):
            refuse("TARGET_BLOCK_MEMBER_REPEATED")
        if set(listed) != set(torch.nonzero(hidden[row]).flatten().tolist()):
            refuse("TARGET_BLOCK_MEMBER_NOT_HIDDEN_OR_HIDDEN_NOT_MEMBER")
        if set(listed) & set(Q):
            refuse("TARGET_BLOCK_CONTAINS_QUERY_ADDRESS")
    return {"cells": cells, "hidden_per_cell": hidden.sum(dim=1).tolist()}


# ------------------------------------------------- EMA pairing and route

def validate_ema_pairing(modules: Any) -> dict:
    """Teacher mirrors the student encoder name-for-name; AdamW owns only
    the student encoder and predictor. The PR224 EMA zips parameters()
    positionally, so order is part of the pairing."""
    online = list(modules.online.named_parameters())
    teacher = list(modules.teacher.named_parameters())
    if [n for n, _ in online] != [n for n, _ in teacher]:
        refuse("TEACHER_STUDENT_PARAMETER_NAMES_OR_ORDER_DIFFER")
    for (name, s), (_, t) in zip(online, teacher):
        if s.shape != t.shape or s.dtype != t.dtype or s is t:
            refuse("TEACHER_STUDENT_PARAMETER_PAIR_INVALID__" + name)
    if any(t.requires_grad for _, t in teacher) or modules.teacher.training:
        refuse("TEACHER_NOT_FROZEN_EVAL")
    predictor = {id(p) for p in modules.predictor.parameters()}
    student = {id(p) for _, p in online}
    owned = [id(p) for g in modules.optimizer.param_groups for p in g["params"]]
    if len(owned) != len(set(owned)) or set(owned) != student | predictor:
        refuse("OPTIMIZER_MUST_OWN_EXACTLY_STUDENT_ENCODER_AND_PREDICTOR")
    if {id(t) for _, t in teacher} & (student | predictor):
        refuse("TEACHER_PARAMETER_SHARED_WITH_STUDENT_OR_PREDICTOR")
    return {"paired_tensors": len(online), "optimizer_tensors": len(owned),
            "predictor_tensors": len(predictor), "teacher_in_optimizer": False}


def canonical_route():
    from sea_ad_jepa.v5 import ema_bound_runtime_proof_v1 as ema_v1
    return getattr(ema_v1, CANONICAL_ROUTE[1])


def require_canonical_ema_route(route: Any) -> None:
    """Only the presentation-bound route; never the scalar-momentum ones."""
    from sea_ad_jepa.v5 import ema_bound_runtime_proof_v1 as ema_v1
    if route is not getattr(ema_v1, CANONICAL_ROUTE[1]):
        refuse("NOT_THE_CANONICAL_PRESENTATION_EMA_ROUTE")


def expected_presentation_ema(*, parent_presentations_seen: int, base_cells: int,
                              half_life_presentations: int) -> dict:
    from sea_ad_jepa.v5.ema_presentation_v1 import ema_momentum_for_presentations
    return {
        "half_life_presentations": half_life_presentations,
        "presentations_this_update": base_cells,
        "parent_presentations_seen": parent_presentations_seen,
        "child_presentations_seen": parent_presentations_seen + base_cells,
        "momentum": ema_momentum_for_presentations(
            presentations_this_update=base_cells,
            half_life_presentations=half_life_presentations),
    }


# ------------------------------------------- authorization and custody path

def verify_pilot_authorization(record: Any, *, expected: Mapping[str, Any]) -> str:
    """The owner's M1 record; this draft contains none and creates none."""
    if type(record) is not dict or set(record) != AUTHORIZATION_FIELDS:
        refuse("OWNER_AUTHORIZATION_MISSING_OR_MALFORMED")
    if (record["schema"] != AUTHORIZATION_SCHEMA or record["owner_authorized"] is not True
            or record["milestone"] != "M1" or record["horizon"] != 1
            or record["encoder_input_mode"] != ENCODER_INPUT_MODE):
        refuse("OWNER_AUTHORIZATION_NOT_FOR_SHARED_BASE_M1_ONE_UPDATE")
    for key, value in expected.items():
        if record.get(key) != value:
            refuse("OWNER_AUTHORIZATION_PIN_MISMATCH__" + key)
    return contract.canonical_sha256(record)


def require_separate_dev_checkpoint_path(path: Path, *, u0_journal_root: Path) -> Path:
    """Post-update checkpoints never go into the U0-only journal."""
    target, u0 = Path(path).absolute(), Path(u0_journal_root).absolute()
    if target == u0 or u0 in target.parents or target in u0.parents:
        refuse("DEV_CHECKPOINT_PATH_OVERLAPS_U0_ONLY_JOURNAL")
    for directory in (target, *target.parents):
        lock = directory / "run.lock.json"
        if lock.is_file() and json.loads(lock.read_text(encoding="utf-8")).get(
                "original_v5_u0_only") is True:
            refuse("DEV_CHECKPOINT_PATH_INSIDE_U0_ONLY_JOURNAL")
    return target


@dataclass(frozen=True)
class PilotUpdateRecord:
    authorization_sha256: str
    rows: tuple[int, ...]
    half_life_presentations: int
    presentations_this_update: int
    parent_presentations_seen: int
    child_presentations_seen: int
    momentum: float
    optimizer_step_before: int
    optimizer_step_after: int
    completion_proof_sha256: str
    encoder_input_mode: str = ENCODER_INPUT_MODE
    biological_result: bool = False
    training_authorized_by_runtime: bool = False


def run_authorized_one_update(*, modules: Any, inputs: Mapping[str, Any], blocks: Any,
                              authority: Any, authorization: Any,
                              expected_authorization: Mapping[str, Any],
                              half_life_presentations: int,
                              completion_checkpoint_digest: Any | None = None) -> PilotUpdateRecord:
    """All checks first; then exactly one call of the canonical route.

    M1 is the genesis update only: update_index 0 from u0 (0 presentations).
    """
    parent_presentations_seen = 0
    authorization_sha = verify_pilot_authorization(authorization, expected=expected_authorization)
    if inputs.get("mode") != ENCODER_INPUT_MODE or tuple(inputs["rows"]) != tuple(authorization["rows"]):
        refuse("INPUTS_NOT_THE_AUTHORIZED_SHARED_BASE_ROWS")
    if authorization["half_life_presentations"] != half_life_presentations:
        refuse("HALF_LIFE_NOT_AUTHORIZED")
    validate_ema_pairing(modules)
    validate_target_blocks(blocks, inputs["measurement_mask"])
    want = expected_presentation_ema(
        parent_presentations_seen=parent_presentations_seen,
        base_cells=len(inputs["rows"]), half_life_presentations=half_life_presentations)
    route = canonical_route()
    report = route(
        modules, authority=authority, half_life_presentations=half_life_presentations,
        completion_checkpoint_digest=completion_checkpoint_digest,
        expression=inputs["expression"], measurement_mask=inputs["measurement_mask"],
        stable_cell_keys=inputs["stable_cell_keys"], operator_ids=inputs["operator_ids"],
        measured_tokens_by_operator=inputs["measured_tokens_by_operator"],
        scientific_cell_weights=inputs["scientific_cell_weights"],
        target_block_views=[blocks],
        max_teacher_tokens_per_microbatch=len(inputs["rows"]) *
        max(inputs["measured_tokens_by_operator"].values()),
        run_seed=RUN_SEED, update_index=0)
    proof = report.get("presentation_ema_completion_proof")
    if (report.get("optimizer_step_after") != report.get("optimizer_step_before", -2) + 1
            or report.get("guarded_optimizer_step") is not True
            or report.get("guarded_ema") is not True
            or report.get("ema_presentations_this_update") != want["presentations_this_update"]
            or report.get("ema_half_life_presentations") != half_life_presentations
            or report.get("ema_child_presentations_seen") != want["child_presentations_seen"]
            or report.get("ema_momentum_used") != want["momentum"]
            or not isinstance(proof, Mapping)):
        refuse("CANONICAL_ROUTE_REPORT_DOES_NOT_PROVE_ONE_STEP_THEN_ONE_EMA")
    return PilotUpdateRecord(
        authorization_sha256=authorization_sha, rows=tuple(inputs["rows"]),
        half_life_presentations=half_life_presentations,
        presentations_this_update=want["presentations_this_update"],
        parent_presentations_seen=parent_presentations_seen,
        child_presentations_seen=want["child_presentations_seen"],
        momentum=want["momentum"],
        optimizer_step_before=report["optimizer_step_before"],
        optimizer_step_after=report["optimizer_step_after"],
        completion_proof_sha256=sha256(json.dumps(
            proof, sort_keys=True, default=str).encode("utf-8")).hexdigest())
