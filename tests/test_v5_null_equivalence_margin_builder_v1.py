from pathlib import Path


def test_null_margin_builder_is_fixed_and_has_no_free_numeric_cli():
    path = Path("scripts/agent/build_full104_null_equivalence_margin_authority_v1_20260918.py")
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "NullEquivalenceMarginAuthorityV1" in source
    assert "HISTORICAL_SCALE_CONTEXT_SHA256" in source
    assert "Within-donor shuffled negative: mean delta -0.000240" in source
    assert "0.0030 to 0.0116" in source
    assert "--margin" not in source
    assert "--null-equivalence-margin-numerator" not in source
    assert "--null-equivalence-margin-denominator" not in source
    for forbidden in (
        "stage81",
        "t1_checkpoint",
        "X_common6000",
        "terminal_masking_policy_outcomes",
    ):
        assert forbidden.lower() not in source.lower()
