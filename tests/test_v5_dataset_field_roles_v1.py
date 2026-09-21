import pytest

from sea_ad_jepa.v5.dataset_field_roles_v1 import (
    CURRENT_FULL104_FIELD_ROLES,
    DatasetFieldRole,
    require_legal_exact_decoy_roles,
)


def test_current_full104_operator_is_not_declared_pure_technical() -> None:
    assert CURRENT_FULL104_FIELD_ROLES["matrix_id"] is DatasetFieldRole.MIXED_BIO_TECH
    assert CURRENT_FULL104_FIELD_ROLES["operator_index"] is DatasetFieldRole.MIXED_BIO_TECH


def test_biological_and_identity_fields_are_not_legal_exact_decoy_strata() -> None:
    assert CURRENT_FULL104_FIELD_ROLES["native_class"] is DatasetFieldRole.BIOLOGICAL
    assert CURRENT_FULL104_FIELD_ROLES["broad_class"] is DatasetFieldRole.BIOLOGICAL
    assert CURRENT_FULL104_FIELD_ROLES["donor_id"] is DatasetFieldRole.GROUPING_ONLY
    assert CURRENT_FULL104_FIELD_ROLES["cell_id"] is DatasetFieldRole.GROUPING_ONLY


def test_source_is_domain_nuisance_not_claimed_exogenous_technical() -> None:
    assert CURRENT_FULL104_FIELD_ROLES["source"] is DatasetFieldRole.DOMAIN_NUISANCE


def test_mixed_role_fails_closed_for_exact_decoy() -> None:
    with pytest.raises(ValueError, match="reject mixed"):
        require_legal_exact_decoy_roles("DOMAIN_NUISANCE", "MIXED_BIO_TECH")


def test_only_domain_or_exogenous_roles_are_legal_exact_decoy_strata() -> None:
    out = require_legal_exact_decoy_roles("DOMAIN_NUISANCE", "EXOGENOUS_TECHNICAL")
    assert out == (
        DatasetFieldRole.DOMAIN_NUISANCE,
        DatasetFieldRole.EXOGENOUS_TECHNICAL,
    )


def test_support_fingerprint_is_not_legal_exact_nuisance() -> None:
    # NPH52 support fingerprints are tied to native-class-pure operators, so the
    # field carries mixed biological/measurement structure and cannot be used as
    # an exact nuisance-only decoy stratum.
    assert CURRENT_FULL104_FIELD_ROLES["support_fingerprint"] is DatasetFieldRole.MIXED_BIO_TECH
    with pytest.raises(ValueError, match="reject mixed"):
        require_legal_exact_decoy_roles(CURRENT_FULL104_FIELD_ROLES["support_fingerprint"])
