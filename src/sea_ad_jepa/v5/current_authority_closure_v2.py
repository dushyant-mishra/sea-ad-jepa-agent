"""Explicit current-V5 scientific/runtime authority closure V2.

V2 promotes masking population/design/execution, target construction/necessity/
execution, runtime, measurement, geometry and geometry-specific memorization to
first-class roots. It validates a complete current graph but deliberately does
not authorize training; a separate final training authority must consume this
closure after preexecution/receipt/optimizer guards are closed.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .address_universe_ladder_authority_v1 import AddressUniverseLadderAuthorityV1
from .anti_cheat_authority_bundle_v2 import AntiCheatAuthorityBundleV2
from .base_training_estimand_recovery_v1 import validate_current_recovered_base_estimand_v1
from .canonical_address_registry_authority_v1 import CanonicalAddressRegistryAuthorityV1
from .current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from .current_masking_policy_authority_v2 import CurrentMaskingPolicyAuthorityV2
from .current_runtime_source_authority_v1 import CurrentRuntimeSourceAuthorityV1
from .current_target_address_provider_authority_v1 import (
    CurrentTargetAddressProviderAuthorityV1,
    bind_provider_to_registry_authority,
)
from .ema_timescale_authority_v2 import EmaTimescaleAuthorityV2
from .geometry_memorization_qualification_authority_v1 import (
    GeometryMemorizationQualificationAuthorityV1,
)
from .masking_qualification_design_authority_v1 import MaskingQualificationDesignAuthorityV1
from .masking_qualification_execution_authority_v1 import MaskingQualificationExecutionAuthorityV1
from .masking_rng_replay_authority_v1 import MaskingRngReplayAuthorityV1
from .measurement_robustness_authority_v2 import MeasurementRobustnessAuthorityV2
from .model_geometry_authority_v2 import ModelGeometryAuthorityV2
from .outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from .precision_authority_v1 import QualificationPrecisionAuthorityV1
from .remaining_rna_execution_authority_v1 import RemainingRnaExecutionAuthorityV1
from .remaining_rna_necessity_v1 import RemainingRnaNecessityAuthorityV1
from .target_construction_authority_v1 import TargetConstructionAuthorityV1
from .target_evidence_budget_authority_v1 import TargetEvidenceBudgetAuthorityV1
from .target_identity_shortcut_gate_authority_v1 import TargetIdentityShortcutGateAuthorityV1
from .target_panel_authority_v1 import TargetPanelAuthorityV1
from .teacher_target_semantics_authority_v2 import (
    TeacherTargetSemanticsAuthorityV2,
    bind_teacher_semantics_to_target_construction_v1,
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _auth(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


def _eq(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise ValueError(message)


def _require_type(value: Any, cls: type, field: str) -> None:
    if not isinstance(value, cls):
        raise ValueError(f"{field} must use the current {cls.__name__} schema")


def validate_current_v5_authority_closure_v2(
    *,
    full104_substrate_sha256: str,
    representation: Any,
    support_estimability: Any,
    canonical_address_registry: CanonicalAddressRegistryAuthorityV1,
    base_training_weight_law: Any,
    base_training_estimand: Any,
    target_address: CurrentTargetAddressProviderAuthorityV1,
    target_evidence_budget: TargetEvidenceBudgetAuthorityV1,
    precision: QualificationPrecisionAuthorityV1,
    outer_split: OuterDonorSplitAuthorityV1,
    target_panel: TargetPanelAuthorityV1,
    address_universe_ladder: AddressUniverseLadderAuthorityV1,
    masking_rng_replay: MaskingRngReplayAuthorityV1,
    masking_qualification_design: MaskingQualificationDesignAuthorityV1,
    masking_qualification_execution: MaskingQualificationExecutionAuthorityV1,
    masking: CurrentMaskingPolicyAuthorityV2,
    target_construction: TargetConstructionAuthorityV1,
    remaining_rna_necessity: RemainingRnaNecessityAuthorityV1,
    remaining_rna_execution: RemainingRnaExecutionAuthorityV1,
    teacher_target: TeacherTargetSemanticsAuthorityV2,
    schedule_authority_sha256: str,
    ema: EmaTimescaleAuthorityV2,
    measurement_robustness: MeasurementRobustnessAuthorityV2,
    target_identity_gate: TargetIdentityShortcutGateAuthorityV1,
    anti_cheat: AntiCheatAuthorityBundleV2,
    model_geometry: ModelGeometryAuthorityV2,
    geometry_memorization_qualification: GeometryMemorizationQualificationAuthorityV1,
    protected_registry: Any,
    critical_test: Any,
    observation_gradient_firewall_authority_sha256: str,
    runtime_source: CurrentRuntimeSourceAuthorityV1,
) -> dict[str, Any]:
    typed = (
        (canonical_address_registry, CanonicalAddressRegistryAuthorityV1, "canonical_address_registry"),
        (target_address, CurrentTargetAddressProviderAuthorityV1, "target_address"),
        (target_evidence_budget, TargetEvidenceBudgetAuthorityV1, "target_evidence_budget"),
        (precision, QualificationPrecisionAuthorityV1, "precision"),
        (outer_split, OuterDonorSplitAuthorityV1, "outer_split"),
        (target_panel, TargetPanelAuthorityV1, "target_panel"),
        (address_universe_ladder, AddressUniverseLadderAuthorityV1, "address_universe_ladder"),
        (masking_rng_replay, MaskingRngReplayAuthorityV1, "masking_rng_replay"),
        (masking_qualification_design, MaskingQualificationDesignAuthorityV1, "masking_qualification_design"),
        (masking_qualification_execution, MaskingQualificationExecutionAuthorityV1, "masking_qualification_execution"),
        (masking, CurrentMaskingPolicyAuthorityV2, "masking"),
        (target_construction, TargetConstructionAuthorityV1, "target_construction"),
        (remaining_rna_necessity, RemainingRnaNecessityAuthorityV1, "remaining_rna_necessity"),
        (remaining_rna_execution, RemainingRnaExecutionAuthorityV1, "remaining_rna_execution"),
        (teacher_target, TeacherTargetSemanticsAuthorityV2, "teacher_target"),
        (ema, EmaTimescaleAuthorityV2, "ema"),
        (measurement_robustness, MeasurementRobustnessAuthorityV2, "measurement_robustness"),
        (target_identity_gate, TargetIdentityShortcutGateAuthorityV1, "target_identity_gate"),
        (anti_cheat, AntiCheatAuthorityBundleV2, "anti_cheat"),
        (model_geometry, ModelGeometryAuthorityV2, "model_geometry"),
        (geometry_memorization_qualification, GeometryMemorizationQualificationAuthorityV1, "geometry_memorization_qualification"),
        (runtime_source, CurrentRuntimeSourceAuthorityV1, "runtime_source"),
    )
    for value, cls, field in typed:
        _require_type(value, cls, field)

    full = _sha(full104_substrate_sha256, "full104_substrate_sha256")
    schedule = _sha(schedule_authority_sha256, "schedule_authority_sha256")
    firewall = _sha(
        observation_gradient_firewall_authority_sha256,
        "observation_gradient_firewall_authority_sha256",
    )

    rep = _auth(representation, "representation")
    support = _auth(support_estimability, "support estimability")
    registry = _auth(canonical_address_registry, "canonical address registry")
    est = _auth(base_training_estimand, "base training estimand")
    address = _auth(target_address, "target address provider")
    budget = _auth(target_evidence_budget, "target evidence budget")
    precision_sha = _auth(precision, "precision")
    split = _auth(outer_split, "outer split")
    panel = _auth(target_panel, "target panel")
    ladder = _auth(address_universe_ladder, "address universe ladder")
    rng = _auth(masking_rng_replay, "masking RNG replay")
    design = _auth(masking_qualification_design, "masking qualification design")
    mask_exec = _auth(masking_qualification_execution, "masking qualification execution")
    mask = _auth(masking, "masking")
    construction = _auth(target_construction, "target construction")
    necessity = _auth(remaining_rna_necessity, "remaining RNA necessity")
    rna_exec = _auth(remaining_rna_execution, "remaining RNA execution")
    teacher = _auth(teacher_target, "teacher target")
    ema_sha = _auth(ema, "EMA")
    measurement = _auth(measurement_robustness, "measurement robustness")
    identity = _auth(target_identity_gate, "target identity gate")
    anti = _auth(anti_cheat, "anti cheat")
    geometry = _auth(model_geometry, "model geometry")
    mem = _auth(geometry_memorization_qualification, "geometry memorization qualification")
    protected = _auth(protected_registry, "protected registry")
    critical = _auth(critical_test, "critical test")
    runtime = _auth(runtime_source, "runtime source")

    validate_current_recovered_base_estimand_v1(base_training_weight_law, base_training_estimand)

    # Frozen substrate/support chain.
    _eq(getattr(representation, "substrate_authority_sha256", None), full, "representation substrate root mismatch")
    _eq(getattr(support_estimability, "full104_substrate_sha256", None), full, "support substrate root mismatch")
    _eq(
        getattr(support_estimability, "measurement_support_authority_sha256", None),
        getattr(representation, "support_authority_sha256", None),
        "support measurement root mismatch",
    )
    _eq(canonical_address_registry.full104_block_manifest_sha256, full, "registry FULL104 substrate root mismatch")
    _eq(getattr(base_training_estimand, "support_estimability_authority_sha256", None), support, "estimand support root mismatch")

    # Registry/address/population/masking qualification chain.
    bind_provider_to_registry_authority(provider=target_address, registry_authority=canonical_address_registry)
    _eq(target_evidence_budget.support_estimability_authority_sha256, support, "budget support root mismatch")
    _eq(precision.support_estimability_authority_sha256, support, "precision support root mismatch")
    _eq(outer_split.full104_substrate_sha256, full, "outer split FULL104 root mismatch")
    _eq(target_panel.full104_substrate_sha256, full, "target panel FULL104 root mismatch")
    _eq(target_panel.canonical_registry_authority_sha256, registry, "target panel registry root mismatch")
    _eq(target_panel.support_estimability_authority_sha256, support, "target panel support root mismatch")
    _eq(address_universe_ladder.canonical_registry_authority_sha256, registry, "address ladder registry root mismatch")
    _eq(address_universe_ladder.support_estimability_authority_sha256, support, "address ladder support root mismatch")
    _eq(masking_rng_replay.canonical_registry_authority_sha256, registry, "masking RNG registry root mismatch")
    _eq(masking_rng_replay.outer_split_authority_sha256, split, "masking RNG split root mismatch")
    _eq(masking_rng_replay.target_panel_authority_sha256, panel, "masking RNG target-panel root mismatch")
    masking.bind_live_authorities(
        support_estimability=support_estimability,
        target_evidence_budget=target_evidence_budget,
        rng_replay=masking_rng_replay,
    )
    _eq(masking.canonical_registry_authority_sha256, registry, "masking registry root mismatch")

    # Query-local target and remaining-RNA chain.
    _eq(remaining_rna_necessity.representation_authority_sha256, rep, "remaining-RNA representation root mismatch")
    _eq(remaining_rna_necessity.support_estimability_authority_sha256, support, "remaining-RNA support root mismatch")
    _eq(remaining_rna_necessity.target_address_provider_authority_sha256, address, "remaining-RNA target-address root mismatch")
    _eq(remaining_rna_necessity.masking_authority_sha256, mask, "remaining-RNA masking root mismatch")
    _eq(remaining_rna_necessity.precision_authority_sha256, precision_sha, "remaining-RNA precision root mismatch")
    target_construction.bind_live_authorities(
        representation=representation,
        support_estimability=support_estimability,
        target_address_provider=target_address,
    )
    bind_teacher_semantics_to_target_construction_v1(teacher_target, target_construction)
    _eq(teacher_target.representation_authority_sha256, rep, "teacher representation root mismatch")
    _eq(teacher_target.support_estimability_authority_sha256, support, "teacher support root mismatch")
    _eq(teacher_target.target_address_query_authority_sha256, address, "teacher target-address root mismatch")
    _eq(teacher_target.scientific_weight_authority_sha256, est, "teacher estimand root mismatch")
    _eq(teacher_target.masking_authority_sha256, mask, "teacher masking root mismatch")
    _eq(teacher_target.remaining_rna_necessity_authority_sha256, necessity, "teacher remaining-RNA root mismatch")

    # Masking design/execution uses one exact population/attacker graph.
    _eq(masking_qualification_design.full104_substrate_sha256, full, "masking design FULL104 root mismatch")
    _eq(masking_qualification_design.representation_authority_sha256, rep, "masking design representation root mismatch")
    _eq(masking_qualification_design.support_estimability_authority_sha256, support, "masking design support root mismatch")
    _eq(masking_qualification_design.canonical_registry_authority_sha256, registry, "masking design registry root mismatch")
    _eq(masking_qualification_design.teacher_target_semantics_authority_sha256, teacher, "masking design teacher root mismatch")
    masking_qualification_design.bind_live_authorities(
        target_evidence_budget=target_evidence_budget,
        precision=precision,
        outer_split=outer_split,
        target_panel=target_panel,
        address_universe_ladder=address_universe_ladder,
        rng_replay=masking_rng_replay,
    )
    masking_qualification_execution.bind_qualification_design(masking_qualification_design)
    if masking_qualification_execution.passed is not True:
        raise ValueError("masking qualification execution must be EXECUTED_PASS")

    remaining_rna_execution.bind_live_authorities(
        remaining_rna_necessity=remaining_rna_necessity,
        precision=precision,
        target_construction=target_construction,
        target_panel=target_panel,
        outer_split=outer_split,
    )
    if remaining_rna_execution.passed is not True:
        raise ValueError("remaining-RNA execution must be EXECUTED_PASS")

    # EMA / measurement / identity / anti-cheat chain.
    _eq(ema.base_training_estimand_sha256, est, "EMA estimand root mismatch")
    _eq(ema.schedule_authority_sha256, schedule, "EMA schedule root mismatch")
    _eq(teacher_target.ema_boundary_authority_sha256, ema_sha, "teacher EMA root mismatch")
    _eq(measurement_robustness.representation_authority_sha256, rep, "measurement representation root mismatch")
    _eq(measurement_robustness.teacher_target_semantics_sha256, teacher, "measurement teacher root mismatch")
    _eq(measurement_robustness.precision_authority_sha256, precision_sha, "measurement precision root mismatch")
    if measurement_robustness.passed is not True:
        raise ValueError("measurement robustness execution must be EXECUTED_PASS")
    _eq(target_identity_gate.teacher_target_semantics_sha256, teacher, "identity gate teacher root mismatch")
    _eq(target_identity_gate.representation_authority_sha256, rep, "identity gate representation root mismatch")
    _eq(target_identity_gate.base_training_estimand_sha256, est, "identity gate estimand root mismatch")
    _eq(target_identity_gate.masking_authority_sha256, mask, "identity gate masking root mismatch")
    _eq(anti_cheat.target_identity_gate_authority_sha256, identity, "anti-cheat identity root mismatch")
    _eq(anti_cheat.masking_authority_sha256, mask, "anti-cheat masking root mismatch")
    _eq(anti_cheat.masking_qualification_execution_authority_sha256, mask_exec, "anti-cheat masking execution root mismatch")
    _eq(anti_cheat.remaining_rna_execution_authority_sha256, rna_exec, "anti-cheat remaining-RNA execution root mismatch")
    _eq(anti_cheat.measurement_robustness_authority_sha256, measurement, "anti-cheat measurement root mismatch")
    _eq(anti_cheat.observation_gradient_firewall_authority_sha256, firewall, "anti-cheat observation firewall root mismatch")
    _eq(anti_cheat.critical_test_authority_sha256, critical, "anti-cheat critical-test root mismatch")
    anti_cheat.bind_execution_evidence(
        masking_qualification_execution=masking_qualification_execution,
        remaining_rna_execution=remaining_rna_execution,
    )

    # Geometry-specific deferred Stage-A predicate must now be executed.
    _eq(model_geometry.protected_registry_authority_sha256, protected, "geometry protected-registry root mismatch")
    _eq(model_geometry.memorization_qualification_authority_sha256, mem, "geometry memorization root mismatch")
    _eq(
        geometry_memorization_qualification.geometry_artifact_sha256,
        model_geometry.geometry_artifact_sha256,
        "geometry artifact root mismatch",
    )
    _eq(
        geometry_memorization_qualification.protected_registry_authority_sha256,
        protected,
        "geometry memorization protected-registry root mismatch",
    )
    if geometry_memorization_qualification.passed is not True:
        raise ValueError("geometry memorization qualification must be EXECUTED_PASS")

    roots = {
        "full104_substrate_sha256": full,
        "representation_authority_sha256": rep,
        "support_estimability_authority_sha256": support,
        "canonical_address_registry_authority_sha256": registry,
        "base_training_estimand_sha256": est,
        "target_address_provider_authority_sha256": address,
        "target_evidence_budget_authority_sha256": budget,
        "precision_authority_sha256": precision_sha,
        "outer_split_authority_sha256": split,
        "target_panel_authority_sha256": panel,
        "address_universe_ladder_authority_sha256": ladder,
        "masking_rng_replay_authority_sha256": rng,
        "masking_qualification_design_authority_sha256": design,
        "masking_qualification_execution_authority_sha256": mask_exec,
        "masking_authority_sha256": mask,
        "target_construction_authority_sha256": construction,
        "remaining_rna_necessity_authority_sha256": necessity,
        "remaining_rna_execution_authority_sha256": rna_exec,
        "teacher_target_semantics_authority_sha256": teacher,
        "schedule_authority_sha256": schedule,
        "ema_authority_sha256": ema_sha,
        "measurement_robustness_authority_sha256": measurement,
        "target_identity_gate_authority_sha256": identity,
        "anti_cheat_authority_sha256": anti,
        "model_geometry_authority_sha256": geometry,
        "geometry_memorization_qualification_authority_sha256": mem,
        "protected_registry_authority_sha256": protected,
        "critical_test_authority_sha256": critical,
        "observation_gradient_firewall_authority_sha256": firewall,
        "runtime_source_authority_sha256": runtime,
    }
    if tuple(roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:
        raise RuntimeError("internal V2 authority root order mismatch")

    payload = {
        "schema": "V5_CURRENT_AUTHORITY_CLOSURE_V2",
        "authority_roots": roots,
        "training_authorized": False,
    }
    return {**payload, "closure_digest": _digest(payload)}
