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


SUPPORT_SEMANTIC_SHA = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
REGISTRY_SEMANTIC_SHA = "3321f6a0acd5ae89faa4912dde2d2ebc7c9d52d2bccf82ef63e415ace51158c9"
REPRESENTATION_SEMANTIC_SHA = "92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1"
TEACHER_TARGET_SEMANTIC_SHA = "a5c4702eae54ffeb9d3a92957ce3176e29db25c805843a48cf3a6121037d89d2"


def test_full104_ingress_builders_pin_exact_current_semantic_authorities():
    support_ingress = (
        "scripts/agent/build_full104_census_authority_v2_20260918.py",
        "scripts/agent/build_full104_control_calibration_cache_v1.py",
        "scripts/agent/build_full104_target_panel_authority_v3_20260918.py",
        "scripts/agent/build_full104_precision_authority_v4_20260918.py",
        "scripts/agent/build_full104_target_evidence_budget_template_authority_v1_20260918.py",
        "scripts/agent/build_full104_masking_design_authority_v2_20260918.py",
    )
    for rel in support_ingress:
        source = Path(rel).read_text(encoding="utf-8")
        assert SUPPORT_SEMANTIC_SHA in source, rel
        assert "exact current semantic authority" in source, rel

    registry_ingress = (
        "scripts/agent/build_full104_target_panel_authority_v3_20260918.py",
        "scripts/agent/build_full104_rng_replay_authority_v2_20260918.py",
        "scripts/agent/build_full104_masking_design_authority_v2_20260918.py",
    )
    for rel in registry_ingress:
        source = Path(rel).read_text(encoding="utf-8")
        assert REGISTRY_SEMANTIC_SHA in source, rel
        assert "exact current semantic authority" in source, rel

    design = Path(
        "scripts/agent/build_full104_masking_design_authority_v2_20260918.py"
    ).read_text(encoding="utf-8")
    assert REPRESENTATION_SEMANTIC_SHA in design
    assert TEACHER_TARGET_SEMANTIC_SHA in design


def test_current_template_canonically_names_no_extra_retained_floor_policy():
    source = Path("src/sea_ad_jepa/v5/target_evidence_budget_template_authority_v1.py").read_text(
        encoding="utf-8"
    )
    builder = Path(
        "scripts/agent/build_full104_target_evidence_budget_template_authority_v1_20260918.py"
    ).read_text(encoding="utf-8")
    policy = "NO_ADDITIONAL_RETAINED_COUNT_FLOOR__FROZEN_BURDEN_LADDER_OWNS_MASK_FRACTION_V1"
    assert policy in source
    assert "min_retained_policy_id" in source
    assert "min_retained_policy_id=MIN_RETAINED_POLICY_ID" in builder
