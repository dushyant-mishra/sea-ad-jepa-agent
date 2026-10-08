from pathlib import Path

def test_outer_split_builder_uses_current_census_receipt_and_no_historical_fixture():
    p=Path("scripts/agent/build_full104_outer_split_authority_v1_20260918.py")
    source=p.read_text(encoding="utf-8")
    compile(source,str(p),"exec")
    assert "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1" in source
    assert "EXPECTED_FOLD_SIZES=(28,26,25,25)" in source
    assert "V5_FULL104_DONOR_REGISTRY_SEMANTIC_V1" in source
    for forbidden in ("stage81","t1_checkpoint","0.996","analysis/"):
        assert forbidden.lower() not in source.lower()

def test_precision_v4_builder_requires_final_target_panel_and_outer_split_authorities():
    p=Path("scripts/agent/build_full104_precision_authority_v4_20260918.py")
    source=p.read_text(encoding="utf-8")
    compile(source,str(p),"exec")
    assert "TargetPanelAuthorityV3" in source
    assert "OuterDonorSplitAuthorityV1" in source
    assert "QualificationPrecisionAuthorityV4" in source
    assert "authority.bind_target_panel(panel,sizing)" in source
    assert "required_target_count=panel.target_count" in source
    for forbidden in ("stage81","t1_checkpoint","0.996","analysis/"):
        assert forbidden.lower() not in source.lower()
