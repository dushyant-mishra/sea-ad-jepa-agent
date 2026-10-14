import sea_ad_jepa.v5.runtime_target_semantics_boundary_v1 as boundary


def test_v5_reference_loss_declares_mechanics_only_not_scientific_target_authority():
    assert boundary.assert_runtime_target_semantics_non_authorizing() is True
    assert boundary.SCIENTIFIC_TARGET_SEMANTICS_AUTHORIZED is False
    assert boundary.REFERENCE_LOSS_ROLE == "MECHANICS_FIXTURE_ONLY__NOT_TARGET_AUTHORITY"
    assert boundary.FULL_RICH_TEACHER_REALIZATION_MATCHING_AUTHORIZED is False
    assert boundary.RICH_TEACHER_PARTIAL_STUDENT_CLASSIFICATION == (
        "RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA"
    )
    assert boundary.TARGET_WINNER_SELECTED is False
    assert boundary.UNCERTAINTY_MODEL_SELECTED is False
    assert boundary.STAGE_A_EXECUTION_AUTHORIZED is False
    assert boundary.TRAINING_AUTHORIZED is False
