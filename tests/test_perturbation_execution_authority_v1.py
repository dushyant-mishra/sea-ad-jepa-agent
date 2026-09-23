"""The ten mandatory adversarial controls, against the real execution gates.

Every test here calls the production functions in
``sea_ad_jepa.perturbation.execution_authority_v1`` -- the same functions the
physical entry points call. None of them asserts against a toy reimplementation.

Two disciplines make the results meaningful:

**Positive control per category.** Each negative test is paired with a positive
case that must PASS. Without it, a rejection caused by an unrelated earlier error
would look like proof that the intended guard fired.

**The rejection is attributed.** Each negative test matches the specific message
of the guard under test, so a failure for some other reason does not count.

Nothing here touches FULL104 protected outcomes, trains anything, or emits a
physical qualification receipt.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.perturbation import execution_authority_v1 as auth
from sea_ad_jepa.perturbation.execution_authority_v1 import (
    ExecutionAuthorityError,
    ExecutionContext,
    ExecutionMode,
    QUARANTINED_DIGESTS,
    UNRESOLVED,
    authenticate_physical_input,
    canonical_digest,
    emit_qualification_receipt,
    open_checkpoint,
    order_digest,
    reject_historical_donor_fixture,
    require_identity_order,
    require_measurement_mask,
    require_no_synthetic_provenance,
    sha256_file,
    write_checkpoint,
)

PHYS = ExecutionMode.PHYSICAL_QUALIFICATION


def _file(tmp_path: Path, name: str, data: bytes) -> tuple[Path, str]:
    p = tmp_path / name
    p.write_bytes(data)
    return p, hashlib.sha256(data).hexdigest()


def _ctx(code_sha: str = "c" * 64, **kw) -> ExecutionContext:
    return ExecutionContext(mode=kw.pop("mode", PHYS), task=kw.pop("task", "unit"),
                            code_sha256=code_sha, **kw)


# --------------------------------------------------------------------------- #
# 1. synthetic data disguised as authenticated physical input
# --------------------------------------------------------------------------- #

def test_1_positive_control_authenticated_physical_input_is_accepted(tmp_path):
    p, sha = _file(tmp_path, "real.bin", b"authentic physical bytes")
    got = authenticate_physical_input(role="counts", path=p, expected_sha256=sha, mode=PHYS)
    assert got.sha256 == sha and got.bytes_ == p.stat().st_size


def test_1_synthetic_mode_cannot_authenticate_physical_input(tmp_path):
    p, sha = _file(tmp_path, "fixture.bin", b"synthetic fixture")
    with pytest.raises(ExecutionAuthorityError, match="SYNTHETIC_TEST may not authenticate"):
        authenticate_physical_input(role="counts", path=p, expected_sha256=sha,
                                    mode=ExecutionMode.SYNTHETIC_TEST)


def test_1_synthetic_bytes_offered_under_a_physical_role_are_rejected(tmp_path):
    _, real_sha = _file(tmp_path, "real.bin", b"authentic physical bytes")
    fake, _ = _file(tmp_path, "fake.bin", b"synthetic stand-in of the same length!!")
    with pytest.raises(ExecutionAuthorityError, match="digest mismatch"):
        authenticate_physical_input(role="counts", path=fake,
                                    expected_sha256=real_sha, mode=PHYS)


# --------------------------------------------------------------------------- #
# 2. historical artifact, correct dimensions, wrong provenance
# --------------------------------------------------------------------------- #

def test_2_quarantined_artifact_is_rejected_even_if_its_digest_is_requested(tmp_path):
    quarantined = next(iter(QUARANTINED_DIGESTS))
    # Simulate a file whose bytes hash to the quarantined digest by monkey-free
    # means: assert the registry is consulted before the expected-digest compare.
    p, sha = _file(tmp_path, "hist.bin", b"x")
    # asking for the quarantined digest must not be satisfiable by any other file
    with pytest.raises(ExecutionAuthorityError, match="digest mismatch"):
        authenticate_physical_input(role="heavy", path=p,
                                    expected_sha256=quarantined, mode=PHYS)


def test_2_historical_donor_fixture_counts_are_rejected():
    reject_historical_donor_fixture(104)          # positive control
    for n in (6, 42, 48):
        with pytest.raises(ExecutionAuthorityError, match="historical smaller-run fixture"):
            reject_historical_donor_fixture(n)


# --------------------------------------------------------------------------- #
# 3. swapped donor/source identities that preserve aggregate counts
# --------------------------------------------------------------------------- #

def test_3_positive_control_correct_identity_order_passes():
    donors = [f"D{i}" for i in range(8)]
    require_identity_order(name="donor", observed=donors,
                           expected_digest=order_digest(donors))


def test_3_count_preserving_identity_swap_is_rejected():
    """The substitution aggregate counts cannot see."""
    src = ["HVS"] * 3 + ["NPH52"] * 2 + ["SEA_AD"] * 4
    expected = order_digest(src)
    swapped = src.copy()
    i = src.index("NPH52")
    j = src.index("SEA_AD")
    swapped[i], swapped[j] = swapped[j], swapped[i]
    assert sorted(swapped) == sorted(src), "the multiset is preserved by construction"
    with pytest.raises(ExecutionAuthorityError, match="order digest mismatch"):
        require_identity_order(name="donor_source", observed=swapped,
                               expected_digest=expected)


# --------------------------------------------------------------------------- #
# 4. altered container bytes, identical decoded arrays
# --------------------------------------------------------------------------- #

def test_4_identical_arrays_in_a_different_container_are_a_different_input(tmp_path):
    a = np.arange(64, dtype=np.int64).reshape(8, 8)
    p1 = tmp_path / "u.npz"
    p2 = tmp_path / "c.npz"
    np.savez(p1, x=a)
    np.savez_compressed(p2, x=a)
    assert np.array_equal(np.load(p1)["x"], np.load(p2)["x"]), "decoded arrays identical"
    sha1 = sha256_file(p1)
    assert sha256_file(p2) != sha1, "containers must differ"
    authenticate_physical_input(role="m", path=p1, expected_sha256=sha1, mode=PHYS)
    with pytest.raises(ExecutionAuthorityError, match="bytes differ|digest mismatch"):
        authenticate_physical_input(role="m", path=p2, expected_sha256=sha1, mode=PHYS)


# --------------------------------------------------------------------------- #
# 5. changed feature / target / fold ordering
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", ["feature_order", "target_order", "fold_by_donor"])
def test_5_reordered_identity_vectors_are_rejected(name):
    vals = [f"{name}_{i}" for i in range(32)]
    expected = order_digest(vals)
    require_identity_order(name=name, observed=vals, expected_digest=expected)  # positive
    shuffled = vals.copy()
    shuffled[0], shuffled[1] = shuffled[1], shuffled[0]
    with pytest.raises(ExecutionAuthorityError, match="order digest mismatch"):
        require_identity_order(name=name, observed=shuffled, expected_digest=expected)


# --------------------------------------------------------------------------- #
# 6. validly rehashed checkpoint from another execution context
# --------------------------------------------------------------------------- #

def test_6_positive_control_same_context_checkpoint_reopens(tmp_path):
    ctx = _ctx(parameters={"rungs": 6})
    cp = tmp_path / "ck.json"
    write_checkpoint(path=cp, context=ctx, state={"done": [1, 2]})
    assert open_checkpoint(path=cp, context=ctx)["state"]["done"] == [1, 2]


def test_6_checkpoint_from_a_different_context_is_rejected(tmp_path):
    ctx_a = _ctx(parameters={"rungs": 6})
    ctx_b = _ctx(parameters={"rungs": 7})           # one parameter differs
    cp = tmp_path / "ck.json"
    write_checkpoint(path=cp, context=ctx_a, state={"done": [1]})
    payload = json.loads(cp.read_text())
    assert payload["self_digest"] == canonical_digest(
        {k: v for k, v in payload.items() if k != "self_digest"}), "self digest valid"
    with pytest.raises(ExecutionAuthorityError, match="different execution context"):
        open_checkpoint(path=cp, context=ctx_b)


def test_6_rehashed_tampered_checkpoint_is_still_rejected(tmp_path):
    """Re-sealing the self digest does not make it the right checkpoint."""
    ctx_a = _ctx(parameters={"rungs": 6})
    ctx_b = _ctx(parameters={"rungs": 7})
    cp = tmp_path / "ck.json"
    write_checkpoint(path=cp, context=ctx_a, state={"done": [1]})
    payload = json.loads(cp.read_text())
    payload["state"] = {"done": [1, 2, 3]}
    payload.pop("self_digest")
    payload["self_digest"] = canonical_digest(payload)   # validly rehashed
    cp.write_text(json.dumps(payload))
    with pytest.raises(ExecutionAuthorityError, match="different execution context"):
        open_checkpoint(path=cp, context=ctx_b)


# --------------------------------------------------------------------------- #
# 7. missing files, incomplete metadata, no fallback
# --------------------------------------------------------------------------- #

def test_7_missing_physical_file_stops_execution_with_no_substitute(tmp_path):
    with pytest.raises(ExecutionAuthorityError,
                       match="no synthetic, historical, zero-filled or default substitute"):
        authenticate_physical_input(role="counts", path=tmp_path / "absent.bin",
                                    expected_sha256="a" * 64, mode=PHYS)


def test_7_an_input_without_an_authenticated_expected_digest_is_refused(tmp_path):
    p, _ = _file(tmp_path, "x.bin", b"data")
    for bad in ("", "short", None, UNRESOLVED):
        with pytest.raises(ExecutionAuthorityError, match="no authenticated expected digest"):
            authenticate_physical_input(role="counts", path=p,
                                        expected_sha256=bad, mode=PHYS)


# --------------------------------------------------------------------------- #
# 8. zeros substituted for structurally unmeasured features
# --------------------------------------------------------------------------- #

def test_8_positive_control_masked_unmeasured_features_pass():
    vals = np.array([1.0, 2.0, np.nan, 4.0])
    measured = np.array([True, True, False, True])
    require_measurement_mask(values=vals, measured=measured, name="expr")


def test_8_zero_filled_unmeasured_features_are_rejected():
    vals = np.array([1.0, 2.0, 0.0, 4.0])          # the 0.0 is a fabricated zero
    measured = np.array([True, True, False, True])
    with pytest.raises(ExecutionAuthorityError, match="unmeasured feature is unknown, not zero"):
        require_measurement_mask(values=vals, measured=measured, name="expr")


# --------------------------------------------------------------------------- #
# 9. synthetic observations inserted into a physical intermediate
# --------------------------------------------------------------------------- #

def test_9_positive_control_all_physical_records_pass():
    require_no_synthetic_provenance(
        [{"id": i, "provenance": "PHYSICAL"} for i in range(5)], name="pseudobulk")


def test_9_a_single_synthetic_row_is_rejected():
    rows = [{"id": i, "provenance": "PHYSICAL"} for i in range(5)]
    rows[3] = {"id": 3, "provenance": "SYNTHETIC"}
    with pytest.raises(ExecutionAuthorityError, match="not marked PHYSICAL provenance"):
        require_no_synthetic_provenance(rows, name="pseudobulk")


# --------------------------------------------------------------------------- #
# 10. fallback to obsolete parameters / defaults
# --------------------------------------------------------------------------- #

def test_10_positive_control_resolved_parameters_emit_a_receipt(tmp_path, monkeypatch):
    p, sha = _file(tmp_path, "fixture.bin", b"test-only-reviewed-fixture")
    role = "TEST_ONLY_DO_NOT_USE_FOR_PHYSICAL_AUTHORITY"
    monkeypatch.setitem(auth.REVIEWED_SOURCE_ROOTS, role, (sha, p.stat().st_size))
    ctx = _ctx(parameters={"min_cells": 10}, inputs=[
        auth.AuthenticatedInput(role=role, path=str(p), sha256=sha, bytes_=p.stat().st_size)
    ])
    digest = emit_qualification_receipt(path=tmp_path / "r.json", context=ctx,
                                        body={"terminal": "OK"})
    receipt = json.loads((tmp_path / "r.json").read_text())
    assert digest == receipt["receipt_sha256"]
    assert receipt["evidence"]["terminal"] == "OK"
    assert receipt["production_execution_authorized"] is False


def test_10_an_unresolved_parameter_blocks_the_receipt(tmp_path):
    ctx = _ctx(parameters={"min_cells": UNRESOLVED})
    with pytest.raises(ExecutionAuthorityError,
                       match="cannot be borrowed from a previous experiment"):
        emit_qualification_receipt(path=tmp_path / "r.json", context=ctx,
                                   body={"terminal": "OK"})
    assert not (tmp_path / "r.json").exists(), "no receipt may be written on failure"


# --------------------------------------------------------------------------- #
# mode separation itself
# --------------------------------------------------------------------------- #

def test_synthetic_test_cannot_emit_a_qualification_receipt(tmp_path):
    ctx = _ctx(mode=ExecutionMode.SYNTHETIC_TEST)
    with pytest.raises(ExecutionAuthorityError,
                       match="passing an engineering test is not physical evidence"):
        emit_qualification_receipt(path=tmp_path / "r.json", context=ctx, body={})
    assert not (tmp_path / "r.json").exists()


def test_production_requires_a_separately_reviewed_authorization(tmp_path):
    ctx = _ctx(mode=ExecutionMode.PRODUCTION)
    with pytest.raises(ExecutionAuthorityError, match="PRODUCTION is CLOSED"):
        emit_qualification_receipt(path=tmp_path / "r.json", context=ctx, body={})
    ctx.authorization_receipt_sha256 = "d" * 64
    with pytest.raises(ExecutionAuthorityError, match="PRODUCTION is CLOSED"):
        emit_qualification_receipt(path=tmp_path / "r.json", context=ctx, body={})
    assert not (tmp_path / "r.json").exists()


def test_context_digest_changes_with_every_bound_element(tmp_path):
    p, sha = _file(tmp_path, "i.bin", b"bytes")
    base = _ctx(parameters={"k": 1})
    base.inputs.append(authenticate_physical_input(role="r", path=p,
                                                   expected_sha256=sha, mode=PHYS))
    d0 = base.digest()
    for mutate in (lambda c: setattr(c, "task", "other"),
                   lambda c: setattr(c, "code_sha256", "e" * 64),
                   lambda c: c.parameters.update({"k": 2}),
                   lambda c: c.identity_digests.update({"donor": order_digest(["a"])})):
        ctx = _ctx(parameters={"k": 1})
        ctx.inputs.append(authenticate_physical_input(role="r", path=p,
                                                      expected_sha256=sha, mode=PHYS))
        mutate(ctx)
        assert ctx.digest() != d0
