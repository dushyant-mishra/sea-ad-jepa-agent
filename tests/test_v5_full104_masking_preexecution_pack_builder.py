from pathlib import Path

def test_preexecution_builder_contains_no_placeholder_or_selected_policy_path():
    source=Path("scripts/agent/build_full104_masking_preexecution_pack_20260918.py").read_text(encoding="utf-8")
    forbidden=(
        "PLACEHOLDER",
        "UNRESOLVED_",
        "Stage81A3",
        "stage81a3",
        "t1_checkpoint",
        "0.996",
        "selected_policy_id=",
        "training_authorized=True",
        "terminal_masking_outcomes_inspected=True",
    )
    assert [x for x in forbidden if x in source] == []


def test_preexecution_builder_binds_current_successor_classes():
    source=Path("scripts/agent/build_full104_masking_preexecution_pack_20260918.py").read_text(encoding="utf-8")
    required=(
        "MaskingQualificationDesignAuthorityV2",
        "MaskingTargetSemanticsAuthorityV1",
        "QualificationPrecisionAuthorityV4",
        "MaskingBurdenLadderAuthorityV2",
        "MaskingRngReplayAuthorityV2",
        "NonlinearMaskingChallengeAuthorityV2",
        "TargetPanelAuthorityV2",
        "OuterDonorSplitAuthorityV1",
    )
    assert [x for x in required if x not in source] == []


def test_preexecution_builder_uses_authority_digests_not_json_file_hashes_for_core_roles():
    source=Path("scripts/agent/build_full104_masking_preexecution_pack_20260918.py").read_text(encoding="utf-8")
    assert "representation.canonical_digest()" in source
    assert "support.canonical_digest()" in source
    assert "registry.canonical_digest()" in source
    assert "parameters.canonical_digest()" in source
