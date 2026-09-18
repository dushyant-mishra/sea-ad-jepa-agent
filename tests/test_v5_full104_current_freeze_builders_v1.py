from pathlib import Path

BUILDER_PATHS = (
    "scripts/agent/build_full104_target_evidence_budget_template_authority_v1_20260918.py",
    "scripts/agent/build_full104_burden_ladder_authority_v2_20260918.py",
    "scripts/agent/build_full104_rng_replay_authority_v2_20260918.py",
    "scripts/agent/build_full104_masking_design_authority_v2_20260918.py",
)


def test_current_full104_freeze_builders_compile_and_exclude_spillover_tokens():
    for rel in BUILDER_PATHS:
        source = Path(rel).read_text(encoding="utf-8")
        compile(source, rel, "exec")
        lowered = source.lower()
        assert "full104_masking_prospective_freeze_status_20260917" not in lowered
        assert "qualification_800_v1" not in lowered
        assert "qualification_6000_v1" not in lowered
        assert "placeholder" not in lowered


def test_final_design_builder_does_not_bind_obsolete_discovery_universe_or_concrete_burden():
    source = Path(BUILDER_PATHS[-1]).read_text(encoding="utf-8")
    assert "address_universe_ladder" not in source
    assert "target_evidence_budget_authority_sha256" not in source
    assert "target_evidence_budget_template_sha256" in source
    assert "burden_ladder_authority_sha256" in source
