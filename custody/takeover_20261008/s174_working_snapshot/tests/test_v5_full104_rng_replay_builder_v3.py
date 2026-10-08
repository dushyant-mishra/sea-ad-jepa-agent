from pathlib import Path


RNG_BUILDER = Path("scripts/agent/build_full104_rng_replay_authority_v3_20260921.py")
PARAMETERS_BUILDER = Path("scripts/agent/build_full104_masking_parameters_authority_v3_20260919.py")


def test_rng_v3_builder_consumes_the_parameters_v3_declared_digest_key() -> None:
    rng_source = RNG_BUILDER.read_text(encoding="utf-8")
    parameters_source = PARAMETERS_BUILDER.read_text(encoding="utf-8")

    # The producer's public payload contract is parameter-specific. Changing this
    # key would alter already-materialized authority bytes and downstream roots.
    assert '"parameter_authority_sha256": authority.canonical_digest()' in parameters_source

    # The RNG-V3 consumer must read that exact declared key when validating the
    # same MaskingQualificationParametersAuthorityV3 dataclass.
    expected = '''parameters = typed(
        parameters_payload,
        MaskingQualificationParametersAuthorityV3,
        "parameter_authority_sha256",
    )'''
    assert expected in rng_source

    # The adjacent burden-ladder authority intentionally uses the generic key;
    # keeping both assertions prevents another copy/paste regression.
    burden_expected = '''burden = typed(
        burden_payload,
        MaskingBurdenLadderAuthorityV2,
        "authority_sha256",
    )'''
    assert burden_expected in rng_source


def test_rng_v3_builder_and_parameters_builder_compile() -> None:
    for path in (RNG_BUILDER, PARAMETERS_BUILDER):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
