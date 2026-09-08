from __future__ import annotations

import copy

import pytest
import torch

from scripts.agent.validate_healthy_teacher_execution_binding_overlay_v1 import (
    validate_overlay,
)
from scripts.v4.f1b_reference_candidates_v1 import reference_vulnerable
from scripts.v4.f1b_successor_attack_suite_v1 import prove_polarity, run_suite
from scripts.v4.teacher_student_f1b_attack_adapter_v1 import canonical_candidate
from scripts.v4.healthy_teacher_continuation_runner_v1 import (
    validate_continuation_authority,
    validate_u40_qualification,
)
from sea_ad_jepa.v4.ipb_jepa import BlockPredictor, IPBEncoder
from sea_ad_jepa.v4.teacher_student_checkpoint import (
    CHECKPOINT_SCHEMA,
    environment_fingerprint,
    validate_checkpoint_header,
    validate_environment_fingerprint,
)
from sea_ad_jepa.v4.teacher_student_movement import (
    adjudicate_tensor,
    decay_only_counterfactual,
    source_sha256 as movement_source_sha256,
)
from sea_ad_jepa.v4.teacher_student_source_authority import verify_source_authority
from sea_ad_jepa.v4.teacher_student_runtime import (
    BACKBONE_REGISTRY_SHA256,
    FROZEN_BACKBONE_REGISTRY,
    FROZEN_PREDICTOR_REGISTRY,
    F1B_ATTACK_AUTHORITY_ROOT,
    HEALTHY_TEACHER_BASE_ROOT,
    POPULATION_ACCESS_ROOT,
    PREDICTOR_REGISTRY_SHA256,
    PRODUCTION_CONFIG,
    TeacherStudentConfig,
    sample_uniform_target_blocks,
    validate_production_config,
    validate_update_chronology,
)


def test_production_config_is_exact_and_drift_rejects() -> None:
    assert validate_production_config(PRODUCTION_CONFIG)["passed"]
    changed = TeacherStudentConfig(microbatch=4)
    with pytest.raises(RuntimeError):
        validate_production_config(changed)


def test_backbone_registry_is_exact_48_and_present_in_encoder() -> None:
    assert len(FROZEN_BACKBONE_REGISTRY) == 48
    assert len(set(FROZEN_BACKBONE_REGISTRY)) == 48
    model = IPBEncoder(
        vocabulary_size=64, width=160, heads=4, blocks=6, gradient_checkpointing=False
    )
    names = set(dict(model.named_parameters()))
    assert set(FROZEN_BACKBONE_REGISTRY) <= names
    assert len(BACKBONE_REGISTRY_SHA256) == 64


def test_predictor_registry_is_exact_complete_and_frozen() -> None:
    predictor = BlockPredictor(width=160, heads=4)
    names = tuple(name for name, p in predictor.named_parameters() if p.requires_grad)
    assert names == FROZEN_PREDICTOR_REGISTRY
    assert len(names) == 15
    assert PREDICTOR_REGISTRY_SHA256 == (
        "43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592"
    )


def test_uniform_mask_is_exact_deterministic_and_measured_only() -> None:
    measured = torch.zeros((2, 64), dtype=torch.bool)
    measured[0, :50] = True
    measured[1, 10:60] = True
    keys = torch.tensor([101, 202], dtype=torch.int64)
    a = sample_uniform_target_blocks(
        measured,
        production_seed=8_113_002,
        cell_indices=keys,
        sample_pass=0,
        view_index=0,
        mask_fraction=0.40,
        block_count=16,
    )
    b = sample_uniform_target_blocks(
        measured,
        production_seed=8_113_002,
        cell_indices=keys,
        sample_pass=0,
        view_index=0,
        mask_fraction=0.40,
        block_count=16,
    )
    assert torch.equal(a.hidden_mask, b.hidden_mask)
    assert torch.equal(a.indices, b.indices)
    assert torch.equal(a.member_mask, b.member_mask)
    assert a.hidden_mask.sum(dim=1).tolist() == [20, 20]
    assert not bool((a.hidden_mask & ~measured).any())
    assert a.member_mask.sum(dim=(1, 2)).tolist() == [20, 20]


def test_movement_pure_decay_fails_but_any_real_deviation_passes() -> None:
    baseline = torch.tensor([1.0, -2.0, 3.0], dtype=torch.float32)
    decay = decay_only_counterfactual(
        baseline, learning_rate=1e-4, weight_decay=0.01, valid_steps=40
    )
    pure = adjudicate_tensor(
        baseline,
        decay,
        learning_rate=1e-4,
        weight_decay=0.01,
        valid_steps=40,
    )
    assert pure["passed"] is False
    assert pure["status"] == "NOT_ABOVE_DECAY_ONLY"

    changed = decay.clone()
    changed[0] = changed[0] - 1e-3
    live = adjudicate_tensor(
        baseline,
        changed,
        learning_rate=1e-4,
        weight_decay=0.01,
        valid_steps=40,
    )
    assert live["passed"] is True
    assert live["status"] == "EXCEEDS_DECAY_ONLY"


def test_movement_zero_baseline_cannot_pass_without_real_movement() -> None:
    baseline = torch.zeros(4, dtype=torch.float32)
    dead = adjudicate_tensor(
        baseline,
        baseline.clone(),
        learning_rate=1e-4,
        weight_decay=0.01,
        valid_steps=40,
    )
    assert dead["passed"] is False
    moved = baseline.clone()
    moved[2] = torch.nextafter(torch.tensor(0.0), torch.tensor(1.0))
    live = adjudicate_tensor(
        baseline,
        moved,
        learning_rate=1e-4,
        weight_decay=0.01,
        valid_steps=40,
    )
    assert live["passed"] is True


def _checkpoint_authorities() -> dict[str, str]:
    return {
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "population_access_root": POPULATION_ACCESS_ROOT,
        "f1b_attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "integrated_successor_source_root": "d" * 64,
        "integrated_successor_commit": "1" * 40,
        "predictor_mandatory_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "movement_adjudicator_source_sha256": movement_source_sha256(),
    }


def test_checkpoint_header_binds_config_authorities_and_counters() -> None:
    authorities = _checkpoint_authorities()
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "phase": "U0",
        "config_sha256": PRODUCTION_CONFIG.digest(),
        "authority_bindings": authorities,
        "schedule_cursor": 0,
        "global_update_step": 0,
        "ema_update_count": 0,
        "accumulation_position": 0,
    }
    validate_checkpoint_header(
        payload,
        config=PRODUCTION_CONFIG,
        expected_authorities=authorities,
        expected_schedule_cursor=0,
    )
    attacked = copy.deepcopy(payload)
    attacked["authority_bindings"]["integrated_successor_source_root"] = "e" * 64
    with pytest.raises(RuntimeError):
        validate_checkpoint_header(
            attacked,
            config=PRODUCTION_CONFIG,
            expected_authorities=authorities,
        )
    attacked = copy.deepcopy(payload)
    attacked["authority_bindings"]["healthy_teacher_base_root"] = "a" * 64
    with pytest.raises(RuntimeError):
        validate_checkpoint_header(
            attacked,
            config=PRODUCTION_CONFIG,
            expected_authorities=attacked["authority_bindings"],
        )
    attacked = copy.deepcopy(payload)
    attacked["ema_update_count"] = 1
    with pytest.raises(RuntimeError):
        validate_checkpoint_header(
            attacked,
            config=PRODUCTION_CONFIG,
            expected_authorities=authorities,
        )
    attacked = copy.deepcopy(payload)
    attacked["schedule_cursor"] = 1
    with pytest.raises(RuntimeError):
        validate_checkpoint_header(
            attacked,
            config=PRODUCTION_CONFIG,
            expected_authorities=authorities,
        )
    attacked = copy.deepcopy(payload)
    attacked["authority_bindings"].pop("integrated_successor_commit")
    with pytest.raises(RuntimeError):
        validate_checkpoint_header(
            attacked,
            config=PRODUCTION_CONFIG,
            expected_authorities=attacked["authority_bindings"],
        )


def _valid_overlay() -> dict:
    return {
        "schema": "HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1",
        "healthy_teacher_base_package_root": HEALTHY_TEACHER_BASE_ROOT,
        "may_modify_base_contract": False,
        "overlay_itself_is_execution_authority": False,
        "integrated_successor": {
            "commit": "1" * 40,
            "source_manifest_root": "2" * 64,
        },
        "independent_review": {
            "terminal": "PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW",
            "artifact_sha256": "3" * 64,
            "reviewed_commit": "1" * 40,
        },
        "successor_u0": {
            "path": "healthy_teacher_u0000.pt",
            "sha256": "4" * 64,
            "materialization_attestation_sha256": "5" * 64,
            "schedule_cursor": 0,
            "global_update_step": 0,
            "ema_update_count": 0,
            "frozen_before_u1": True,
        },
        "predictor_mandatory_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "movement_adjudicator_source_sha256": "6" * 64,
        "execution_authorized": False,
        "terminal": (
            "PASS_HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY__EXECUTION_STILL_UNAUTHORIZED"
        ),
    }


def test_overlay_is_binding_only_and_cannot_self_authorize() -> None:
    assert validate_overlay(_valid_overlay())["terminal"].startswith("PASS_")
    attacked = _valid_overlay()
    attacked["execution_authorized"] = True
    assert validate_overlay(attacked)["terminal"].startswith("STOP_")
    attacked = _valid_overlay()
    attacked["overlay_itself_is_execution_authority"] = True
    assert validate_overlay(attacked)["terminal"].startswith("STOP_")


def test_overlay_rejects_forged_movement_source_hash() -> None:
    attacked = _valid_overlay()
    attacked["movement_adjudicator_source_sha256"] = "6" * 64
    result = validate_overlay(attacked)
    assert result["terminal"].startswith("STOP_")
    assert any("executing source bytes" in item for item in result["failures"])


def test_checkpoint_runtime_environment_mismatch_is_rejected() -> None:
    saved = environment_fingerprint()
    validate_environment_fingerprint(saved)
    attacked = copy.deepcopy(saved)
    attacked["torch"] = "forged-runtime"
    with pytest.raises(RuntimeError, match="runtime/environment mismatch"):
        validate_environment_fingerprint(attacked)


def test_overlay_requires_external_review_of_exact_integrated_commit() -> None:
    attacked = _valid_overlay()
    attacked["independent_review"]["reviewed_commit"] = "9" * 40
    result = validate_overlay(attacked)
    assert result["terminal"].startswith("STOP_")
    assert any("does not equal" in item for item in result["failures"])


def test_canonical_runtime_defends_all_frozen_f1b_attacks() -> None:
    report = run_suite(canonical_candidate())
    assert report["terminal"] == "PASS_F1B_ATTACK_SUITE", report
    assert report["vulnerable"] == []
    assert report["not_applicable"] == []
    assert report["attack_defective"] == []
    assert len(report["defended"]) == 14


def test_canonical_runtime_preserves_attack_polarity() -> None:
    report = prove_polarity(reference_vulnerable(), canonical_candidate())
    assert report["terminal"] == "PASS_ATTACK_POLARITY", report
    assert report["defective"] == []


def _valid_continuation_authority() -> dict:
    return {
        "schema": "HEALTHY_TEACHER_U40_U205_CONTINUATION_AUTHORITY_V1",
        "authorized": True,
        "phase": "U40_TO_U205",
        "final_update": 205,
        "execution_binding_overlay_sha256": "a" * 64,
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "u40_checkpoint_sha256": "b" * 64,
        "u40_qualification_sha256": "c" * 64,
        "u40_independent_review": {
            "terminal": "PASS_HEALTHY_TEACHER_U40_INDEPENDENT_REVIEW",
            "artifact_sha256": "d" * 64,
            "reviewed_checkpoint_sha256": "b" * 64,
            "reviewed_qualification_sha256": "c" * 64,
        },
        "authorization_id": "prospective-test-authority",
        "terminal": "AUTHORIZE_HEALTHY_TEACHER_U40_TO_U205_MECHANICS_CONTINUATION",
    }


def test_continuation_requires_exact_reviewed_u40_and_cannot_change_horizon() -> None:
    payload = _valid_continuation_authority()
    validate_continuation_authority(
        payload,
        overlay_sha256="a" * 64,
        u40_checkpoint_sha256="b" * 64,
        u40_qualification_sha256="c" * 64,
    )
    attacked = copy.deepcopy(payload)
    attacked["final_update"] = 300
    with pytest.raises(RuntimeError):
        validate_continuation_authority(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
            u40_qualification_sha256="c" * 64,
        )
    attacked = copy.deepcopy(payload)
    attacked["u40_independent_review"]["reviewed_checkpoint_sha256"] = "e" * 64
    with pytest.raises(RuntimeError):
        validate_continuation_authority(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
            u40_qualification_sha256="c" * 64,
        )
    attacked = copy.deepcopy(payload)
    attacked["authorized"] = False
    with pytest.raises(RuntimeError):
        validate_continuation_authority(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
            u40_qualification_sha256="c" * 64,
        )


def _valid_u40_qualification() -> dict:
    return {
        "schema": "HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION_V1",
        "updates": 40,
        "u40_checkpoint": {"sha256": "b" * 64},
        "biology_opened": False,
        "automatic_continuation_authorized": False,
        "overlay_sha256": "a" * 64,
        "terminal": (
            "PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED"
        ),
    }


def test_u40_qualification_self_binds_checkpoint_and_cannot_self_continue() -> None:
    payload = _valid_u40_qualification()
    validate_u40_qualification(
        payload,
        overlay_sha256="a" * 64,
        u40_checkpoint_sha256="b" * 64,
    )
    attacked = copy.deepcopy(payload)
    attacked["u40_checkpoint"]["sha256"] = "e" * 64
    with pytest.raises(RuntimeError):
        validate_u40_qualification(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
        )
    attacked = copy.deepcopy(payload)
    attacked["automatic_continuation_authorized"] = True
    with pytest.raises(RuntimeError):
        validate_u40_qualification(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
        )
    attacked = copy.deepcopy(payload)
    attacked["biology_opened"] = True
    with pytest.raises(RuntimeError):
        validate_u40_qualification(
            attacked,
            overlay_sha256="a" * 64,
            u40_checkpoint_sha256="b" * 64,
        )


def test_canonical_adapter_uses_only_canonical_diagnostics() -> None:
    from scripts.v4 import teacher_student_f1b_attack_adapter_v1 as adapter

    for name in (
        "routing_report",
        "routing_metrics",
        "refit_g5_probe",
        "enforce_frozen_horizon",
        "directional_claim",
        "target_equivalence",
        "select_g5_endpoints",
    ):
        fn = getattr(adapter, name)
        assert fn.__module__ == "sea_ad_jepa.v4.teacher_student_diagnostics", name


def test_production_surface_has_no_retired_training_dependency() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    active = [
        root / "src/sea_ad_jepa/v4/teacher_student_runtime.py",
        root / "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
        root / "src/sea_ad_jepa/v4/teacher_student_movement.py",
        root / "src/sea_ad_jepa/v4/teacher_student_diagnostics.py",
        root / "scripts/v4/teacher_student_f1b_attack_adapter_v1.py",
        root / "scripts/v4/materialize_healthy_teacher_u0_v1.py",
        root / "scripts/v4/healthy_teacher_qualification_runner_v1.py",
        root / "scripts/v4/healthy_teacher_continuation_runner_v1.py",
    ]
    forbidden = (
        "f1b_c3_training_successor_v2",
        "stage81a3_prod41k_teacher_t1",
        "c2_corrective_run_update_v3",
    )
    for path in active:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (path, token)


def test_update_chronology_is_bound_to_optimizer_and_ema() -> None:
    from types import SimpleNamespace

    controller = SimpleNamespace(global_update_step=7, ema_update_count=7)
    assert validate_update_chronology(controller, 7) == {
        "schedule_cursor": 7,
        "global_update_step": 7,
        "ema_update_count": 7,
    }
    with pytest.raises(RuntimeError, match="schedule cursor"):
        validate_update_chronology(controller, 6)
    controller.ema_update_count = 6
    with pytest.raises(RuntimeError, match="optimizer/EMA counters"):
        validate_update_chronology(controller, 7)


def test_executing_source_authority_rejects_tampered_code(tmp_path) -> None:
    import csv
    import shutil

    source_root = (
        ROOT / "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V2.txt"
    ).read_text(encoding="utf-8").strip()
    assert verify_source_authority(source_root, root=ROOT)["passed"] is True

    for rel in (
        "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V2.csv",
        "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V2.txt",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)

    manifest = tmp_path / "docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V2.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        target = tmp_path / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / row["path"], target)

    assert verify_source_authority(source_root, root=tmp_path)["passed"] is True
    attacked = tmp_path / rows[0]["path"]
    attacked.write_bytes(attacked.read_bytes() + b"\n# tamper\n")
    with pytest.raises(RuntimeError, match="executing source bytes"):
        verify_source_authority(source_root, root=tmp_path)
