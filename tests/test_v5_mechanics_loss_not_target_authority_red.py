import sea_ad_jepa.v5.inactive_update_reference as module


def test_v5_reference_loss_declares_mechanics_only_not_scientific_target_authority():
    assert getattr(module, "SCIENTIFIC_TARGET_SEMANTICS_AUTHORIZED", None) is False, (
        "the runtime mechanics harness does not explicitly disclaim scientific target authority"
    )
    assert getattr(module, "REFERENCE_LOSS_ROLE", None) == (
        "MECHANICS_FIXTURE_ONLY__NOT_TARGET_AUTHORITY"
    ), "deterministic teacher-block loss is not explicitly classified as mechanics-only"
    assert getattr(module, "FULL_RICH_TEACHER_REALIZATION_MATCHING_AUTHORIZED", None) is False, (
        "runtime must not imply that partial RNA can point-predict arbitrary teacher-private evidence"
    )
