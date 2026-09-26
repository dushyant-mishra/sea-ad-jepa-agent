"""Prevent historical/small-run or synthetic D_shared values being laundered into V5."""
from dataclasses import asdict, replace

import pytest

from sea_ad_jepa.v5.provisional_diagnostic_parameter_firewall_v1 import (
    PROVENANCE, SHA_ROOTS, G3_ROOTS, SCHEMA, ProvisionalDiagnosticParameterManifestV1,
    from_strict_payload,
)


def fixture(phase="ENGINEERING_SMOKE_ONLY"):
    """All numeric values are INVALID AS PRODUCTION VALUES: fixture-only."""
    return ProvisionalDiagnosticParameterManifestV1(
        phase=phase,
        population_role="READER_FIT_DISCOVERY_ONLY",
        model_width=12, model_depth=1, attention_heads=3,
        presentations_per_update=2, maximum_updates=3,
        max_teacher_tokens_per_microbatch=24,
        ema_half_life_presentations=5, run_seed=7,
        source_population_sha256="a"*64, fit_split_sha256="b"*64,
        feature_support_sha256="c"*64, teacher_target_candidate_sha256="d"*64,
        target_address_candidate_sha256="e"*64, masking_candidate_sha256="f"*64,
        scientific_weight_law_sha256="1"*64, schedule_candidate_sha256="2"*64,
        rng_candidate_sha256="3"*64, resource_budget_justification_sha256="4"*64,
        parameter_provenance=dict(PROVENANCE),
        d_shared=None, d_private=None, d_obs=None,
        qualified_dimension_authority_sha256=None,
        production_geometry_authority_sha256=None,
        g3_fit_objective_code_sha256="5"*64 if phase=="READER_FIT_DEVELOPMENT_DIAGNOSTIC" else None,
        g3_six_state_evidence_contract_sha256="6"*64 if phase=="READER_FIT_DEVELOPMENT_DIAGNOSTIC" else None,
        g3_primary_fit_objective="PRODUCTION_OBJECTIVE_MATCHED"
        if phase=="READER_FIT_DEVELOPMENT_DIAGNOSTIC" else None,
        training_authorized=False,
    )


def test_smoke_requires_only_explicit_provisional_parameters():
    cfg=fixture()
    cfg.validate()
    receipt=cfg.nontraining_receipt()
    assert receipt["training_authorized"] is False
    assert receipt["physical_roots_rehashed_here"] is False
    assert receipt["d_shared_qualified"] is False


def test_scientific_development_requires_explicit_g3_and_six_state_roots():
    cfg=fixture("READER_FIT_DEVELOPMENT_DIAGNOSTIC")
    cfg.validate()
    assert cfg.nontraining_receipt()["scope"]=="READER_FIT_DEVELOPMENT_DIAGNOSTIC"


def test_canonical_digest_changes_if_provisional_architecture_changes():
    cfg=fixture()
    assert cfg.canonical_digest()!=replace(cfg,model_width=24).canonical_digest()


@pytest.mark.parametrize("name", tuple(PROVENANCE))
def test_zero_or_omitted_numeric_parameter_cannot_be_inherited(name):
    cfg=fixture()
    with pytest.raises(ValueError,match="explicit positive integer"):
        replace(cfg,**{name:0}).validate()


@pytest.mark.parametrize("name", (
    "d_shared","d_private","d_obs",
    "qualified_dimension_authority_sha256",
    "production_geometry_authority_sha256",
))
def test_historical_or_synthetic_rank_cannot_enter_diagnostic(name):
    cfg=fixture()
    bad="a"*64 if name.endswith("_sha256") else 160
    with pytest.raises(ValueError,match="cannot claim qualified dimensions"):
        replace(cfg,**{name:bad}).validate()


@pytest.mark.parametrize("name", tuple(SHA_ROOTS))
def test_forged_or_malformed_source_root_rejected(name):
    cfg=fixture()
    with pytest.raises(ValueError,match="canonical lowercase"):
        replace(cfg,**{name:"placeholder_from_test_fixture"}).validate()


@pytest.mark.parametrize("name", tuple(G3_ROOTS))
def test_scientific_development_missing_g3_or_six_state_root_rejected(name):
    cfg=fixture("READER_FIT_DEVELOPMENT_DIAGNOSTIC")
    with pytest.raises(ValueError,match="canonical lowercase"):
        replace(cfg,**{name:None}).validate()


def test_scientific_development_rejects_historical_cell_weight_primary():
    cfg=fixture("READER_FIT_DEVELOPMENT_DIAGNOSTIC")
    with pytest.raises(ValueError,match="objective-matched"):
        replace(cfg,g3_primary_fit_objective="CURRENT_CELL_WEIGHTED").validate()


def test_engineering_smoke_cannot_masquerade_as_g3_scientific_evaluation():
    cfg=fixture()
    with pytest.raises(ValueError,match="engineering-only"):
        replace(cfg,g3_primary_fit_objective="PRODUCTION_OBJECTIVE_MATCHED").validate()


@pytest.mark.parametrize("role",(
    "reader_validation","READER_ORACLE","FOUNDATION_DEVELOPMENT","SEALED_SILETTI",
))
def test_holdout_or_external_role_rejected(role):
    with pytest.raises(ValueError,match="nonfit/protected population"):
        replace(fixture(),population_role=role).validate()


def test_training_authorization_cannot_be_set_even_on_healthy_smoke():
    with pytest.raises(ValueError,match="never authorizes training"):
        replace(fixture(),training_authorized=True).validate()


def test_provenance_cannot_be_replaced_with_historical_import():
    cfg=fixture()
    p=dict(PROVENANCE)
    p["model_width"]="INHERITED_V4_160"
    with pytest.raises(ValueError,match="historical/default import"):
        replace(cfg,parameter_provenance=p).validate()


def test_partial_provenance_cannot_autofill_unmentioned_parameter():
    cfg=fixture()
    p=dict(PROVENANCE)
    del p["ema_half_life_presentations"]
    with pytest.raises(ValueError,match="missing/altered parameter provenance"):
        replace(cfg,parameter_provenance=p).validate()


def test_unknown_payload_keys_rejected_before_object_creation():
    data=asdict(fixture())
    data["historical_magic_width"]=160
    with pytest.raises(ValueError,match="manifest keys differ"):
        from_strict_payload(data)


def test_missing_payload_keys_rejected_instead_of_default():
    data=asdict(fixture())
    del data["run_seed"]
    with pytest.raises(ValueError,match="manifest keys differ"):
        from_strict_payload(data)


def test_run_seed_boolean_not_accepted_as_valid_integer():
    with pytest.raises(ValueError,match="run_seed"):
        replace(fixture(),run_seed=True).validate()


def test_width_and_heads_must_be_consistent():
    with pytest.raises(ValueError,match="divisible"):
        replace(fixture(),model_width=13).validate()


def test_real_data_derivation_not_asserted_by_matching_fixture_sha():
    receipt=fixture().nontraining_receipt()
    assert receipt["status"]=="PARAMETERS_DECLARED__NO_RUNTIME_SOURCE_ATTESTATION"
    assert receipt["production_geometry_qualified"] is False
    assert receipt["run_previously_started"] is False
    assert receipt["protected_outcomes_opened"] is False


def test_scientific_scope_never_grants_training_authority():
    receipt=fixture("READER_FIT_DEVELOPMENT_DIAGNOSTIC").nontraining_receipt()
    assert receipt["training_authorized"] is False
    assert receipt["d_shared_qualified"] is False


def test_schema_is_versioned_and_not_geometry_authority():
    assert SCHEMA=="V26_PROVISIONAL_JEPA_DIAGNOSTIC_PARAMETER_MANIFEST_V1"
