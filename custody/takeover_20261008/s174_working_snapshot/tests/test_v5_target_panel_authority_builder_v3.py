from pathlib import Path

def test_target_panel_v3_builder_binds_live_selector_and_authenticated_cache():
    source=Path("scripts/agent/build_full104_target_panel_authority_v3_20260918.py").read_text(encoding="utf-8")
    compile(source,"builder","exec")
    assert "load_control_calibration_cache" in source
    assert "selection.selected_target_cols!=expected_prefix" in source
    assert "inspect.getfile(selector_impl)" in source
    assert "--sizing-plan" in source
    assert "--control-calibration-precision-plan" in source
    assert "--capacity-receipt" in source
    assert "--capacity-verdict" in source
    assert "verdict.bind_capacity_receipt(receipt)" in source
    assert "precision_plan.bind_calibration_cache(cache.manifest)" in source
    assert "TargetPanelAuthorityV3" in source
    for forbidden in ("stage81","t1_checkpoint","post_u0_t1","0.996","analysis/"):
        assert forbidden.lower() not in source.lower()
