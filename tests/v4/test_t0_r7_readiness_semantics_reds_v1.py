"""R7 red cases for the execution-input readiness-semantics contradiction.

Committed red, before the repair. The contradiction, as demonstrated at the
Stage 1/2 STOP:

    t0_execution_input_authority_v1.build_pretarget_execution_authority
        writes real_execution_ready = False, always
    t0_execution_input_authority_v1.load_pretarget_execution_authority
        raises unless it IS False
    t0_canonical_freeze_v2._verified
        raises STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED
        unless it IS True

So a package that loads cannot run, and a package that could run cannot load.
The first three tests pin that unreachability against the frozen package, so the
repair has something to be measured against and the claim is not merely asserted
in prose.

The remaining tests describe the repaired production authority that does not
exist yet, and therefore fail by absence.

Scope: fixtures and this repository's own artifacts. **No numeric AT8 is read by
any test here**, no DEV or SEALED path is opened, and no scientific design
constant is touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

# The recovered frozen V20 package. Read-only reference; never modified.
FROZEN = (Path("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project")
          / "cdf819f6-5db4-4119-9a97-37fef1d27909" / "scratchpad"
          / "v20_recovery" / "current" / "code")

frozen_available = FROZEN.is_dir()


def _frozen(module: str):
    if str(FROZEN) not in sys.path:
        sys.path.insert(0, str(FROZEN))
    return __import__(module)


# ---------------------------------------------------------------------------
# The contradiction itself, pinned against the frozen package.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_builder_always_writes_readiness_false() -> None:
    source = (FROZEN / "t0_execution_input_authority_v1.py").read_text(
        encoding="utf-8")
    assert "'real_execution_ready':False}" in source.replace(" ", "")
    # And never True, anywhere in the frozen package.
    for path in sorted(FROZEN.glob("*.py")):
        text = path.read_text(encoding="utf-8").replace(" ", "")
        assert "'real_execution_ready':True" not in text, path.name


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_loader_refuses_readiness_true(tmp_path) -> None:
    """A package that could satisfy the canonical gate cannot be loaded."""
    eia = _frozen("t0_execution_input_authority_v1")
    base = {
        "schema": eia.PRE_SCHEMA,
        "donor_role_package_root_sha256": "a" * 64,
        "role_metadata_payload_sha256": "b" * 64,
        "discovery_metadata_payload_sha256": "c" * 64,
        "discovery_expression_payload": {"payload_sha256": "d" * 64,
                                         "cells": 1, "scalar_features": 1,
                                         "canonical_donors": ["D1"]},
        "external_source_authority_hashes": {"src": "e" * 64},
        "chronology": "BUILT_AFTER_ROLE_FREEZE__BEFORE_TARGET_FIT",
    }
    ok = dict(base, real_execution_ready=False)
    eia._write_package(tmp_path / "false", eia.PRE_MEMBER, eia.PRE_MANIFEST,
                       eia.PRE_ROOT, ok)
    assert eia.load_pretarget_execution_authority(tmp_path / "false")

    ready = dict(base, real_execution_ready=True)
    eia._write_package(tmp_path / "true", eia.PRE_MEMBER, eia.PRE_MANIFEST,
                       eia.PRE_ROOT, ready)
    with pytest.raises(ValueError) as excinfo:
        eia.load_pretarget_execution_authority(tmp_path / "true")
    assert "pretarget authority metadata mismatch" in str(excinfo.value)


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_canonical_production_entrypoint_is_unreachable() -> None:
    """The composition: loadable implies False, and False implies refusal."""
    cf2 = _frozen("t0_canonical_freeze_v2")
    kwargs = {k: None for k in (
        "role_dir", "scalar_raw_counts", "scalar_feature_ids", "matrix_id",
        "local_row", "cell_id", "donor_id", "stable_key", "source_library",
        "donor_metadata", "feature_split_csv", "membership_csv")}
    # A loaded frozen authority necessarily carries False, per the test above.
    loaded = {"package_root_sha256": "f" * 64,
              "authority": {"real_execution_ready": False}}
    original = cf2.verify_pretarget_execution_authority
    cf2.verify_pretarget_execution_authority = lambda *a, **k: loaded
    try:
        with pytest.raises(ValueError) as excinfo:
            cf2._verified("dir", None, dict(kwargs), False)
        assert excinfo.value.args[0] == (
            "STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED")
        # The bypass exists only on the test entrypoint.
        assert cf2._verified("dir", None, dict(kwargs), True) is loaded
    finally:
        cf2.verify_pretarget_execution_authority = original


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_test_only_and_v1_entrypoints_stay_non_production() -> None:
    """The repair must not make a bypass or a superseded path acceptable."""
    import inspect

    cf2 = _frozen("t0_canonical_freeze_v2")
    ad2 = _frozen("t0_adjudicator_v2")
    for func in (cf2.freeze_target_after_role_v2,
                 cf2.freeze_tail_after_discovery_authority_v2,
                 ad2.adjudicate_from_raw_v2):
        assert "allow_synthetic_test_fixture" not in inspect.signature(
            func).parameters
    for name in ("freeze_target_after_role_v2_for_test",
                 "freeze_tail_after_discovery_authority_v2_for_test"):
        assert hasattr(cf2, name)
    assert hasattr(ad2, "adjudicate_from_raw_v2_for_test")


# ---------------------------------------------------------------------------
# The repaired production authority. Does not exist yet; these fail by absence.
# ---------------------------------------------------------------------------

def _repaired():
    import t0_execution_input_readiness_authority_v1 as r
    return r


REQUIRED_BINDINGS = (
    "b2_population_raw_source_root_sha256",
    "b2_authority_package_root_sha256",
    "technical_completeness_root_sha256",
    "technical_completeness_package_root_sha256",
    "at8_availability_root_sha256",
    "at8_availability_package_root_sha256",
    "age_sex_root_sha256",
    "age_sex_package_root_sha256",
    "eligible_donor_root_sha256",
    "donor_role_root_sha256",
    "eligible_donor_package_root_sha256",
    "stage_a_preflight_root_sha256",
    "input_dependency_contract_root_sha256",
    "authorization_record_root_sha256",
    "at8_endpoint_identity",
    "pathology_source_sha256",
    "discovery_donor_set_sha256",
    "confirmation_donor_set_sha256",
    "code_byte_semantics_audit",
)


def test_the_repaired_authority_module_exists() -> None:
    r = _repaired()
    assert r.SCHEMA == "JEPA_T0_EXECUTION_INPUT_READINESS_AUTHORITY_V1"


def test_the_repaired_authority_declares_every_required_binding() -> None:
    r = _repaired()
    for field in REQUIRED_BINDINGS:
        assert field in r.REQUIRED_BINDINGS, field


def test_readiness_is_derived_by_the_stated_conjunction() -> None:
    r = _repaired()
    assert r.READINESS_DERIVATION == (
        "VERIFIED_FROM_STAGE1_PARENT_CHAIN_AND_AUTHORIZATION")
    assert r.READINESS_DERIVATION_STATEMENT == (
        "real_execution_ready = all_required_stage1_bindings_verified "
        "AND staged_authorization_present AND no_forbidden_gate_opened")


def test_a_production_package_missing_a_required_root_is_refused(
        tmp_path) -> None:
    r = _repaired()
    for field in REQUIRED_BINDINGS:
        obj = r.lawful_fixture_object()
        del obj["bindings"][field]
        with pytest.raises(AssertionError) as excinfo:
            r.assert_production_authority_lawful(obj)
        assert r.STOP_BINDING_ABSENT in str(excinfo.value)
        assert field in str(excinfo.value)


def test_a_production_package_with_the_wrong_donor_set_is_refused() -> None:
    r = _repaired()
    for field in ("discovery_donor_set_sha256",
                  "confirmation_donor_set_sha256"):
        obj = r.lawful_fixture_object()
        obj["bindings"][field] = "0" * 64
        with pytest.raises(AssertionError) as excinfo:
            r.assert_production_authority_lawful(obj)
        assert r.STOP_DONOR_SET in str(excinfo.value)


def test_a_production_package_with_the_wrong_endpoint_or_source_is_refused(
) -> None:
    r = _repaired()
    obj = r.lawful_fixture_object()
    obj["bindings"]["at8_endpoint_identity"] = "some other column"
    with pytest.raises(AssertionError) as excinfo:
        r.assert_production_authority_lawful(obj)
    assert r.STOP_ENDPOINT in str(excinfo.value)

    obj = r.lawful_fixture_object()
    obj["bindings"]["pathology_source_sha256"] = "0" * 64
    with pytest.raises(AssertionError) as excinfo:
        r.assert_production_authority_lawful(obj)
    assert r.STOP_ENDPOINT in str(excinfo.value)


def test_a_production_package_with_a_false_byte_semantics_label_is_refused(
) -> None:
    r = _repaired()
    obj = r.lawful_fixture_object()
    obj["code_byte_semantics"] = "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"
    with pytest.raises(AssertionError) as excinfo:
        r.assert_production_authority_lawful(obj)
    assert r.STOP_BYTE_SEMANTICS in str(excinfo.value)


def test_readiness_false_is_refused_for_production_canonical_input() -> None:
    r = _repaired()
    obj = r.lawful_fixture_object()
    obj["real_execution_ready"] = False
    with pytest.raises(AssertionError) as excinfo:
        r.assert_production_authority_lawful(obj)
    assert r.STOP_NOT_READY in str(excinfo.value)


def test_readiness_true_without_the_derivation_marker_is_refused() -> None:
    """True must be derived, never asserted."""
    r = _repaired()
    for bad in (None, "", "MANUALLY_SET", "TRUE", "ASSERTED_BY_CALLER"):
        obj = r.lawful_fixture_object()
        obj["readiness_derivation"] = bad
        with pytest.raises(AssertionError) as excinfo:
            r.assert_production_authority_lawful(obj)
        assert r.STOP_DERIVATION in str(excinfo.value)


def test_a_self_attested_package_is_refused() -> None:
    """Expected roots must come from outside the package being checked."""
    r = _repaired()
    obj = r.lawful_fixture_object()
    with pytest.raises(AssertionError) as excinfo:
        r.assert_production_authority_lawful(obj, expected=obj["bindings"])
    assert r.STOP_SELF_ATTESTED in str(excinfo.value)


def test_a_package_claiming_a_forbidden_gate_was_opened_is_refused() -> None:
    r = _repaired()
    for gate in r.FORBIDDEN_GATES:
        obj = r.lawful_fixture_object()
        obj["forbidden_gates_opened"][gate] = True
        with pytest.raises(AssertionError) as excinfo:
            r.assert_production_authority_lawful(obj)
        assert r.STOP_FORBIDDEN_GATE in str(excinfo.value)


def test_a_non_production_package_may_still_carry_readiness_false() -> None:
    """False stays lawful for pre-run, test, fixture and candidate packages."""
    r = _repaired()
    for kind in r.NON_PRODUCTION_KINDS:
        obj = r.lawful_fixture_object()
        obj["package_kind"] = kind
        obj["real_execution_ready"] = False
        obj["readiness_derivation"] = r.READINESS_DERIVATION_NON_PRODUCTION
        assert r.assert_non_production_authority_lawful(obj) is True


def test_the_repair_reads_no_numeric_at8_and_opens_no_gate() -> None:
    r = _repaired()
    source = (ROOT / "scripts" / "v4"
              / "t0_execution_input_readiness_authority_v1.py").read_text(
                  encoding="utf-8")
    # The readiness authority binds the endpoint identity and the source digest.
    # It must never parse a magnitude from that source.
    assert "numeric_at8_value_read" in source
    obj = r.lawful_fixture_object()
    assert obj["numeric_at8_value_read"] is False
    for gate in r.FORBIDDEN_GATES:
        assert obj["forbidden_gates_opened"][gate] is False


def test_the_scientific_design_constants_are_untouched_by_the_repair() -> None:
    """R7 repairs readiness plumbing only."""
    r = _repaired()
    assert r.SCIENTIFIC_DESIGN_UNCHANGED is True
    assert r.CONFIRMATION_DONORS == 18
    assert r.DISCOVERY_DONORS == 28
    assert r.INELIGIBLE_DONORS == 0
