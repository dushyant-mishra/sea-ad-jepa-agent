"""R8 red cases — the adjudicator readiness contradiction.

R7 repaired the readiness semantics for the canonical *freeze* path by building a
parallel authority. It did not reach the *adjudication* path:
`t0_adjudicator_v2._adjudicate_from_raw_v2` calls the frozen
`verify_pretarget_execution_authority` at line 34 and
`verify_preadjudication_execution_authority` at line 48, and both require
`real_execution_ready is True` from loaders that refuse anything but `False`.

So the confirmation adjudicator is unreachable for exactly the reason the
Stage 1/2 STOP identified, and R7's repair does not apply to it.

The first group pins that contradiction against the frozen package. Those must
keep passing after R8, because R8 supersedes the frozen module rather than
editing it. The second group describes the repaired v2 loaders, which do not
exist yet.

Scope: no numeric AT8 of any kind is read here, discovery or confirmation. No
DEV or SEALED path is opened. No discovery refit. No scientific constant is
touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

FROZEN = (Path("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project")
          / "cdf819f6-5db4-4119-9a97-37fef1d27909" / "scratchpad"
          / "v20_recovery" / "current" / "code")
frozen_available = FROZEN.is_dir()


def _frozen(module: str):
    if str(FROZEN) not in sys.path:
        sys.path.insert(0, str(FROZEN))
    return __import__(module)


def _base_pretarget(eia):
    return {
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


def _base_preadjudication(eia):
    return {
        "schema": eia.ADJ_SCHEMA,
        "upstream_package_roots": {"pretarget_execution_input": "a" * 64,
                                   "donor_role": "b" * 64,
                                   "target": "c" * 64, "tail": "d" * 64,
                                   "discovery_authority": "e" * 64,
                                   "technical_registry": "f" * 64,
                                   "target_family": "0" * 64},
        "confirmation_metadata_columns": ["donor_id", "AT8", "age", "sex",
                                          "IMMUNE_FRACTION"],
        "confirmation_metadata_payload_sha256": "1" * 64,
        "confirmation_expression_payload": {"payload_sha256": "2" * 64,
                                            "cells": 1, "scalar_features": 1,
                                            "canonical_donors": ["D1"]},
        "technical_blocks": {},
        "family_status_authority_sha256": "3" * 64,
        "family_historical_rare5_status": "NOT_DECISION_CAPABLE_AUTHORITY_MISSING",
        "external_source_authority_hashes": {"src": "4" * 64},
        "chronology": ("BUILT_AFTER_TARGET_TAIL_TECHNICAL_FAMILY_FREEZE"
                       "__BEFORE_CONFIRMATION_INFERENCE"),
    }


# ---------------------------------------------------------------------------
# The contradiction, pinned. These must keep passing after R8.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_adjudicator_gates_on_readiness_true_at_two_lines() -> None:
    source = (FROZEN / "t0_adjudicator_v2.py").read_text(encoding="utf-8")
    gate = ("real_execution_ready'] is not True and not "
            "allow_synthetic_test_fixture")
    assert source.count(gate) == 2, "expected the gate at both lines 34 and 48"
    assert "STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED" in source


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_pretarget_loader_refuses_readiness_true(tmp_path) -> None:
    eia = _frozen("t0_execution_input_authority_v1")
    obj = dict(_base_pretarget(eia), real_execution_ready=True)
    eia._write_package(tmp_path / "pre", eia.PRE_MEMBER, eia.PRE_MANIFEST,
                       eia.PRE_ROOT, obj)
    with pytest.raises(ValueError) as excinfo:
        eia.load_pretarget_execution_authority(tmp_path / "pre")
    assert "pretarget authority metadata mismatch" in str(excinfo.value)


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_preadjudication_loader_refuses_readiness_true(
        tmp_path) -> None:
    eia = _frozen("t0_execution_input_authority_v1")
    obj = dict(_base_preadjudication(eia), real_execution_ready=True)
    eia._write_package(tmp_path / "adj", eia.ADJ_MEMBER, eia.ADJ_MANIFEST,
                       eia.ADJ_ROOT, obj)
    with pytest.raises(ValueError) as excinfo:
        eia.load_preadjudication_execution_authority(tmp_path / "adj")
    assert "preadjudication authority metadata mismatch" in str(excinfo.value)


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_frozen_builders_never_write_readiness_true() -> None:
    source = (FROZEN / "t0_execution_input_authority_v1.py").read_text(
        encoding="utf-8").replace(" ", "")
    assert source.count("'real_execution_ready':False}") == 2
    assert "'real_execution_ready':True" not in source


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_v20_contract_declares_production_requires_readiness_true(
) -> None:
    """The constant that makes the frozen loader a defect rather than a choice."""
    import json

    constants = (FROZEN.parents[1] / "contract"
                 / "T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json")
    obj = json.loads(constants.read_text(encoding="utf-8"))
    assert obj["production_requires_real_execution_ready"] is True
    assert obj["synthetic_test_authorities_real_execution_ready"] is False


# ---------------------------------------------------------------------------
# The repaired v2 loaders. Do not exist yet.
# ---------------------------------------------------------------------------

def _v2():
    import t0_execution_input_authority_v2 as v2
    return v2


def test_the_repaired_module_exists_and_names_its_single_change() -> None:
    v2 = _v2()
    assert v2.SUPERSEDES == "t0_execution_input_authority_v1"
    assert v2.BEHAVIOURAL_DIFFERENCE == "READINESS_VALUE_CHECK_ONLY"


def test_the_repaired_loaders_are_derived_by_textual_substitution() -> None:
    """Everything but the readiness condition must be byte-identical.

    Derived from `inspect.getsource` of the frozen functions, exactly as the C2
    lane attributed the T1 defect to one line. That makes "only the readiness
    check differs" a verifiable property rather than a claim.

    Four functions are derived, not two, and the count here says so rather than
    hiding it. The two loaders have their readiness value check corrected. The
    two builders have their hardcoded `False` replaced by a derived call,
    because Stage 3 needs packages carrying True and the frozen builders can
    only write False. One removed and one added line each, so eight in total,
    and every one of them must touch the readiness field.
    """
    v2 = _v2()
    diff = v2.source_diff()
    assert "real_execution_ready" in diff
    changed = [l for l in diff.splitlines()
               if (l.startswith("+") or l.startswith("-"))
               and not l.startswith(("+++", "---"))]
    assert len(changed) == 8, changed
    for line in changed:
        assert "real_execution_ready" in line, line


def test_the_derived_builder_refuses_an_undeclared_readiness() -> None:
    """True cannot be asserted by a caller; it must be a recorded derivation."""
    v2 = _v2()
    v2.clear_readiness_derivation()
    try:
        with pytest.raises(AssertionError) as excinfo:
            v2._r8_derived_readiness()
        assert v2.STOP_READINESS_NOT_DERIVED in str(excinfo.value)
        for bad in ("True", 1, None):
            with pytest.raises(AssertionError):
                v2.record_readiness_derivation(value=bad, derivation="x",
                                               evidence={})
        with pytest.raises(AssertionError):
            v2.record_readiness_derivation(value=True, derivation="",
                                           evidence={})
        v2.record_readiness_derivation(value=True, derivation="R7",
                                       evidence={"root": "a" * 64})
        assert v2._r8_derived_readiness() is True
    finally:
        v2.clear_readiness_derivation()


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_repaired_pretarget_loader_accepts_readiness_true(
        tmp_path) -> None:
    eia = _frozen("t0_execution_input_authority_v1")
    v2 = _v2()
    obj = dict(_base_pretarget(eia), real_execution_ready=True)
    eia._write_package(tmp_path / "pre", eia.PRE_MEMBER, eia.PRE_MANIFEST,
                       eia.PRE_ROOT, obj)
    loaded = v2.load_pretarget_execution_authority(tmp_path / "pre")
    assert loaded["authority"]["real_execution_ready"] is True


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_repaired_pretarget_loader_still_accepts_readiness_false(
        tmp_path) -> None:
    """Non-production packages stay lawful; the change is not a loosening."""
    eia = _frozen("t0_execution_input_authority_v1")
    v2 = _v2()
    obj = dict(_base_pretarget(eia), real_execution_ready=False)
    eia._write_package(tmp_path / "pre", eia.PRE_MEMBER, eia.PRE_MANIFEST,
                       eia.PRE_ROOT, obj)
    loaded = v2.load_pretarget_execution_authority(tmp_path / "pre")
    assert loaded["authority"]["real_execution_ready"] is False


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_repaired_loader_refuses_a_non_boolean_readiness(
        tmp_path) -> None:
    """The check becomes a type check, not an absence of a check."""
    eia = _frozen("t0_execution_input_authority_v1")
    v2 = _v2()
    for bad in ("True", 1, None, "yes"):
        obj = dict(_base_pretarget(eia), real_execution_ready=bad)
        target = tmp_path / ("pre_%s" % type(bad).__name__ + str(bad))
        eia._write_package(target, eia.PRE_MEMBER, eia.PRE_MANIFEST,
                           eia.PRE_ROOT, obj)
        with pytest.raises(ValueError):
            v2.load_pretarget_execution_authority(target)


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_repaired_preadjudication_loader_accepts_readiness_true(
        tmp_path) -> None:
    eia = _frozen("t0_execution_input_authority_v1")
    v2 = _v2()
    obj = dict(_base_preadjudication(eia), real_execution_ready=True)
    eia._write_package(tmp_path / "adj", eia.ADJ_MEMBER, eia.ADJ_MANIFEST,
                       eia.ADJ_ROOT, obj)
    loaded = v2.load_preadjudication_execution_authority(tmp_path / "adj")
    assert loaded["authority"]["real_execution_ready"] is True


@pytest.mark.skipif(not frozen_available, reason="frozen V20 package absent")
def test_the_adjudicator_gate_condition_is_satisfiable_after_the_repair(
        tmp_path) -> None:
    """The whole point: the frozen gate can now be passed by a real package."""
    eia = _frozen("t0_execution_input_authority_v1")
    v2 = _v2()
    for base, member, manifest, root, loader in (
            (_base_pretarget(eia), eia.PRE_MEMBER, eia.PRE_MANIFEST,
             eia.PRE_ROOT, v2.load_pretarget_execution_authority),
            (_base_preadjudication(eia), eia.ADJ_MEMBER, eia.ADJ_MANIFEST,
             eia.ADJ_ROOT, v2.load_preadjudication_execution_authority)):
        obj = dict(base, real_execution_ready=True)
        target = tmp_path / member
        eia._write_package(target, member, manifest, root, obj)
        loaded = loader(target)
        # The frozen adjudicator's condition, evaluated verbatim.
        assert not (loaded["authority"]["real_execution_ready"] is not True)


def test_the_repair_touches_no_scientific_constant() -> None:
    v2 = _v2()
    assert v2.SCIENTIFIC_DESIGN_UNCHANGED is True
    assert v2.DISCOVERY_REFIT is False
    assert v2.CONFIRMATION_NUMERIC_AT8_READ is False


def test_the_repaired_module_declares_the_accurate_byte_semantics() -> None:
    v2 = _v2()
    assert v2.CODE_BYTE_SEMANTICS.startswith(
        "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT")


# ---------------------------------------------------------------------------
# The Stage 3 role-label defect, pinned.
#
# Stage 3 reused the discovery endpoint reader for the confirmation read. The
# reader digested the loaded donor set with the role hardcoded to "DISCOVERY",
# so it produced the right eighteen donors under the wrong role label and the
# frozen-expectation check refused it. The guard worked; the caller was wrong.
# ---------------------------------------------------------------------------

def test_the_endpoint_reader_requires_an_explicit_role() -> None:
    """No default, so a caller cannot silently inherit the wrong one."""
    import inspect
    import t0_stage2b_discovery_at8_v1 as s2b

    assert not hasattr(s2b, "load_discovery_at8"), (
        "the old name kept the trap alive; it must be gone")
    sig = inspect.signature(s2b.load_role_numeric_at8)
    assert sig.parameters["role"].default is inspect.Parameter.empty
    assert sig.parameters["role"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize("bad", ["discovery", "Discovery", "", None, "BOTH",
                                 "DISCOVERY ", 1])
def test_an_unrecognised_role_is_refused(bad) -> None:
    import t0_stage2b_discovery_at8_v1 as s2b

    with pytest.raises(AssertionError) as excinfo:
        s2b.load_role_numeric_at8(
            Path("unused"), role=bad, endpoint_identity="a",
            donor_id_field="b", included_donors=set(), excluded_donors=set(),
            expected_source_sha256="0" * 64, expected_donor_set_sha256="0" * 64)
    assert s2b.STOP_DONOR_SET in str(excinfo.value)


def test_the_two_role_digests_differ_over_the_same_donors() -> None:
    """Why the wrong label was caught rather than silently accepted."""
    import t0_execution_input_readiness_authority_v1 as r

    donors = ["H20.33.%03d" % i for i in range(18)]
    as_confirmation = r.donor_set_digest("CONFIRMATION", donors)
    as_discovery = r.donor_set_digest("DISCOVERY", donors)
    assert as_confirmation != as_discovery
    # Order-independent within a role, so the difference is the label alone.
    assert as_confirmation == r.donor_set_digest("CONFIRMATION",
                                                 list(reversed(donors)))


def test_the_stage3_call_sites_state_their_role() -> None:
    source = (ROOT / "scripts" / "v4"
              / "t0_stage3_confirmation_v1.py").read_text(encoding="utf-8")
    assert 'role="DISCOVERY"' in source
    assert 'role="CONFIRMATION"' in source
    assert "load_discovery_at8" not in source
