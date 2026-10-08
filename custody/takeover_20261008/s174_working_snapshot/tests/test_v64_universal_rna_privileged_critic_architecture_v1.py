from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_universal_teacher_remains_rna_and_privileged_is_auxiliary():
    p = json.loads(
        (ROOT / "results/v64/V64_UNIVERSAL_RNA_PLUS_PRIVILEGED_CRITIC_ARCHITECTURE_V1.json").read_text()
    )
    assert p["universal_teacher"] == "RNA_EMA_TEACHER"
    assert p["universal_student_input"] == "LAWFUL_RNA_ONLY"
    assert p["privileged_role_before_recoverability"] == "AUXILIARY_CRITIC_OR_VALIDATOR"
    assert p["full_rich_teacher_imitation_authorized"] is False
    assert p["joint_multimodal_training_authorized"] is False


def test_private_and_missing_privileged_state_cannot_be_forced_into_universal_loss():
    p = json.loads(
        (ROOT / "results/v64/V64_UNIVERSAL_RNA_PLUS_PRIVILEGED_CRITIC_ARCHITECTURE_V1.json").read_text()
    )
    assert p["private_state_policy"] == "PRESERVE_NO_COMPULSORY_RNA_STUDENT_LOSS"
    assert p["missing_privileged_policy"] == "MASK_NOT_ZERO"
    assert p["paired_subset_sets_universal_mass"] is False


def test_test_set_cannot_choose_rotation_or_shared_rank():
    p = json.loads(
        (ROOT / "results/v64/V64_UNIVERSAL_RNA_PLUS_PRIVILEGED_CRITIC_ARCHITECTURE_V1.json").read_text()
    )
    assert p["test_selects_rotation"] is False
    assert p["test_selects_shared_rank"] is False
    assert p["governance"]["training"] == "OFF"
