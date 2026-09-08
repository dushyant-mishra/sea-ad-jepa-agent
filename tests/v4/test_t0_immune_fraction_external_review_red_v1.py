"""External red tests for the T0 IMMUNE_FRACTION production boundary.

Written against producing head 760c68efdba022a14670fa5bcaa4c985e28b686d.
They are review tests, not an authority PASS.
"""
from __future__ import annotations

import inspect
import pytest

import t0_immune_fraction_authority_v1 as ifa


def _forged_production_rows():
    rows = []
    for i in range(46):
        rows.append({
            "donor_id": f"FORGED_{i:02d}",
            "immune_n_donor": 453 if i < 12 else 452,
            "total_op31_n_donor": 13873 if i < 38 else 13872,
        })
    assert sum(r["immune_n_donor"] for r in rows) == 20804
    assert sum(r["total_op31_n_donor"] for r in rows) == 638150
    return rows


def test_detached_rows_cannot_be_promoted_with_parent_digest_labels(tmp_path):
    with pytest.raises(AssertionError):
        ifa.build_authority(
            tmp_path / "forged",
            rows=_forged_production_rows(),
            membership_sha256="a" * 64,
            complete_manifest_sha256="b" * 64,
            selected_op31_blocks=1247,
            consumed_meta_sha256={f"m/{i}.csv": "c" * 64 for i in range(1247)},
            derivation_code_sha256="d" * 64,
            check_production_geometry=True,
        )


def test_one_shot_production_constructor_exists():
    names = set(dir(ifa))
    assert (
        "build_production_immune_fraction_authority" in names
        or "derive_and_build_production_authority" in names
    )


def test_loader_requires_external_parent_chain():
    sig = inspect.signature(ifa.load_authority)
    required = {
        "expected_membership_sha256",
        "expected_complete_manifest_sha256",
        "expected_derivation_code_sha256",
        "expected_formula_specification_root_sha256",
    }
    assert not (required - set(sig.parameters))


def test_loader_validates_internal_manifest_against_captured_member_bytes():
    src = inspect.getsource(ifa.load_authority)
    assert "DictReader" in src and "sha256" in src and "MANIFEST" in src, (
        "loader captures manifest bytes but does not validate its declared "
        "registry/metadata member length+digest rows"
    )


def test_formula_freeze_must_be_bound_not_merely_described():
    assert ifa.FORMULA_SPECIFICATION_STATUS != (
        "SUCCESSOR_SPECIFICATION__AWAITING_EXPLICIT_OWNER_FREEZE"
    )
