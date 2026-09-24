"""Adversarial qualification of the physical N1 lineage adapter.

Every test calls the adapter's real validation entry points. Each negative case is
paired with a positive control, and each asserts the *specific* guard message, so a
rejection caused by an unrelated earlier error cannot be mistaken for the intended
gate firing.

Nothing here opens molecular data, selects a target, draws a mask or authorizes N1.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_physical_lineage_adapter_v1 import (
    CORRECTED_DERIVATIVE_SHA256,
    EXPECTED_FOLD_COUNTS,
    EXPECTED_SOURCE_COUNTS,
    ExecutionMode,
    FROZEN_PASS1_SHA256,
    PhysicalExecutionContext,
    PhysicalLineageError,
    QUARANTINED,
    QUARANTINED_ORIGINAL_SHA256,
    UNRESOLVED,
    authenticate_file,
    build_context,
    canonical_digest,
    emit_adapter_qualification_receipt,
    order_digest,
    reject_historical_donor_count,
    require_n1_execution_authority,
    require_order,
    sha256_file,
)

PHYS = ExecutionMode.PHYSICAL_QUALIFICATION


def _f(tmp: Path, name: str, data: bytes) -> tuple[Path, str]:
    p = tmp / name
    p.write_bytes(data)
    return p, hashlib.sha256(data).hexdigest()


def _ctx(**kw) -> PhysicalExecutionContext:
    return PhysicalExecutionContext(
        mode=kw.pop("mode", PHYS), task=kw.pop("task", "adapter-qual"),
        code_sha256=kw.pop("code_sha256", "a" * 64), **kw)


# --------------------------------------------------------------------------- #
# synthetic fixtures disguised as real FULL104 data
# --------------------------------------------------------------------------- #

def test_positive_control_authentic_file_is_accepted(tmp_path):
    p, sha = _f(tmp_path, "real.bin", b"corrected bytes")
    got = authenticate_file(role="corrected_derivative", path=p,
                            expected_sha256=sha, mode=PHYS)
    assert got.sha256 == sha


def test_synthetic_mode_cannot_authenticate_physical_input(tmp_path):
    p, sha = _f(tmp_path, "fixture.bin", b"synthetic")
    with pytest.raises(PhysicalLineageError,
                       match="must never satisfy a physical requirement"):
        authenticate_file(role="corrected_derivative", path=p, expected_sha256=sha,
                          mode=ExecutionMode.SYNTHETIC_TEST)


def test_synthetic_bytes_under_a_physical_role_are_rejected(tmp_path):
    fake, _ = _f(tmp_path, "fake.npz", b"synthetic stand-in")
    with pytest.raises(PhysicalLineageError, match="byte digest mismatch"):
        authenticate_file(role="corrected_derivative", path=fake,
                          expected_sha256=CORRECTED_DERIVATIVE_SHA256, mode=PHYS)


# --------------------------------------------------------------------------- #
# the quarantined original
# --------------------------------------------------------------------------- #

def test_the_quarantined_original_is_registered_with_its_reason():
    assert QUARANTINED_ORIGINAL_SHA256 in QUARANTINED
    assert "transposed source encoding" in QUARANTINED[QUARANTINED_ORIGINAL_SHA256]
    assert CORRECTED_DERIVATIVE_SHA256 not in QUARANTINED


def test_a_quarantined_artifact_cannot_reach_the_execution_context(tmp_path):
    p, sha = _f(tmp_path, "ok.bin", b"fine")
    good = authenticate_file(role="r", path=p, expected_sha256=sha, mode=PHYS)
    build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[good],
                  identity_digests={}, parameters={})            # positive control
    from sea_ad_jepa.v5.audit_b_n1_physical_lineage_adapter_v1 import PhysicalInput
    poisoned = PhysicalInput(role="corrected_derivative", path="x",
                             sha256=QUARANTINED_ORIGINAL_SHA256, bytes_=1)
    with pytest.raises(PhysicalLineageError, match="quarantined artifact reached"):
        build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[poisoned],
                      identity_digests={}, parameters={})


# --------------------------------------------------------------------------- #
# identity permutations that preserve aggregate counts
# --------------------------------------------------------------------------- #

def test_positive_control_correct_identity_order_passes():
    donors = [f"D{i:03d}" for i in range(104)]
    require_order(name="donor", observed=donors, expected_digest=order_digest(donors))


def test_donor_source_swap_preserving_41_17_46_is_rejected():
    src = [0] * 41 + [1] * 17 + [2] * 46
    assert tuple(np.bincount(src, minlength=3)) == EXPECTED_SOURCE_COUNTS
    expected = order_digest(src)
    swapped = src.copy()
    i, j = src.index(1), src.index(2)
    swapped[i], swapped[j] = swapped[j], swapped[i]
    assert tuple(np.bincount(swapped, minlength=3)) == EXPECTED_SOURCE_COUNTS, \
        "the census is preserved by construction"
    with pytest.raises(PhysicalLineageError, match="order digest mismatch"):
        require_order(name="donor_source", observed=swapped, expected_digest=expected)


def test_within_source_donor_swap_is_rejected():
    """Two donors of the SAME source exchanged: every census is untouched."""
    donors = [f"D{i:03d}" for i in range(104)]
    expected = order_digest(donors)
    swapped = donors.copy()
    swapped[3], swapped[7] = swapped[7], swapped[3]
    assert sorted(swapped) == sorted(donors)
    with pytest.raises(PhysicalLineageError, match="order digest mismatch"):
        require_order(name="donor", observed=swapped, expected_digest=expected)


def test_fold_reassignment_preserving_28_26_25_25_is_rejected():
    folds = [0] * 28 + [1] * 26 + [2] * 25 + [3] * 25
    assert tuple(np.bincount(folds, minlength=4)) == EXPECTED_FOLD_COUNTS
    expected = order_digest(folds)
    moved = folds.copy()
    a, b = moved.index(0), moved.index(3)
    moved[a], moved[b] = moved[b], moved[a]
    assert tuple(np.bincount(moved, minlength=4)) == EXPECTED_FOLD_COUNTS
    with pytest.raises(PhysicalLineageError, match="order digest mismatch"):
        require_order(name="fold_by_donor", observed=moved, expected_digest=expected)


@pytest.mark.parametrize("name", ["strict_core_order", "frozen_target_order"])
def test_feature_and_target_reordering_is_rejected(name):
    vals = list(range(2048))
    expected = order_digest(vals)
    require_order(name=name, observed=vals, expected_digest=expected)   # positive
    moved = vals.copy()
    moved[0], moved[1] = moved[1], moved[0]
    with pytest.raises(PhysicalLineageError, match="order digest mismatch"):
        require_order(name=name, observed=moved, expected_digest=expected)


# --------------------------------------------------------------------------- #
# containers, historical fixtures, missing inputs
# --------------------------------------------------------------------------- #

def test_identical_arrays_in_a_different_container_are_a_different_input(tmp_path):
    a = np.arange(256, dtype=np.int64)
    p1, p2 = tmp_path / "u.npz", tmp_path / "c.npz"
    np.savez(p1, x=a)
    np.savez_compressed(p2, x=a)
    assert np.array_equal(np.load(p1)["x"], np.load(p2)["x"])
    sha1 = sha256_file(p1)
    authenticate_file(role="m", path=p1, expected_sha256=sha1, mode=PHYS)   # positive
    with pytest.raises(PhysicalLineageError, match="different container are\\s+still a different input|byte digest mismatch"):
        authenticate_file(role="m", path=p2, expected_sha256=sha1, mode=PHYS)


def test_historical_smaller_run_donor_counts_are_rejected():
    reject_historical_donor_count(104)                                  # positive
    for n in (6, 42, 48):
        with pytest.raises(PhysicalLineageError, match="historical smaller-run fixture"):
            reject_historical_donor_count(n)
    with pytest.raises(PhysicalLineageError, match="requires 104 donors"):
        reject_historical_donor_count(103)


def test_missing_physical_input_stops_with_no_substitute(tmp_path):
    with pytest.raises(PhysicalLineageError,
                       match="no\\s+synthetic fixture, historical smaller run, zero array or default"):
        authenticate_file(role="corrected_derivative", path=tmp_path / "gone.npz",
                          expected_sha256=CORRECTED_DERIVATIVE_SHA256, mode=PHYS)


def test_an_input_without_an_authenticated_digest_is_refused(tmp_path):
    p, _ = _f(tmp_path, "x.bin", b"d")
    for bad in ("", "nope", UNRESOLVED, "A" * 64):
        with pytest.raises(PhysicalLineageError, match="no authenticated expected digest"):
            authenticate_file(role="r", path=p, expected_sha256=bad, mode=PHYS)


# --------------------------------------------------------------------------- #
# historical parameter defaults
# --------------------------------------------------------------------------- #

def test_positive_control_resolved_parameters_build_a_context():
    ctx = build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[],
                        identity_digests={}, parameters={"rung": "1/20"})
    assert len(ctx.digest()) == 64


def test_an_unresolved_parameter_blocks_the_context_and_the_receipt(tmp_path):
    with pytest.raises(PhysicalLineageError, match="may not be borrowed from a previous experiment"):
        build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[],
                      identity_digests={}, parameters={"rung": UNRESOLVED})
    ctx = _ctx(parameters={"rung": UNRESOLVED})
    with pytest.raises(PhysicalLineageError, match="may not be borrowed"):
        emit_adapter_qualification_receipt(path=tmp_path / "r.json", ctx=ctx, body={})
    assert not (tmp_path / "r.json").exists()


# --------------------------------------------------------------------------- #
# context identity and stale journals
# --------------------------------------------------------------------------- #

def test_context_digest_moves_with_every_bound_element(tmp_path):
    p, sha = _f(tmp_path, "i.bin", b"b")
    inp = authenticate_file(role="r", path=p, expected_sha256=sha, mode=PHYS)
    base = build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[inp],
                         identity_digests={"donor": order_digest(["a"])},
                         parameters={"rung": "1/20"})
    d0 = base.digest()
    for mutate in (
        lambda c: setattr(c, "task", "other"),
        lambda c: setattr(c, "code_sha256", "b" * 64),
        lambda c: c.parameters.update({"rung": "1/10"}),
        lambda c: c.identity_digests.update({"donor": order_digest(["b"])}),
        lambda c: setattr(c, "n1_execution_authorized", True),
    ):
        ctx = build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[inp],
                            identity_digests={"donor": order_digest(["a"])},
                            parameters={"rung": "1/20"})
        mutate(ctx)
        assert ctx.digest() != d0


def test_a_validly_rehashed_journal_from_another_context_is_not_the_right_journal(tmp_path):
    ctx_a = build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[],
                          identity_digests={}, parameters={"rung": "1/20"})
    ctx_b = build_context(mode=PHYS, task="t", code_sha256="a" * 64, inputs=[],
                          identity_digests={}, parameters={"rung": "1/10"})
    record = {"unit": "t0_f0_r0", "context_digest": ctx_a.digest()}
    record["self_digest"] = canonical_digest(record)
    assert record["self_digest"] == canonical_digest(
        {k: v for k, v in record.items() if k != "self_digest"}), "internally valid"
    assert record["context_digest"] != ctx_b.digest(), (
        "a journal unit carries the context it was written under; re-sealing its own "
        "hash does not make it belong to this execution")


# --------------------------------------------------------------------------- #
# the gate that stays shut
# --------------------------------------------------------------------------- #

def test_adapter_qualification_does_not_authorize_n1():
    ctx = build_context(mode=PHYS, task="adapter-qual", code_sha256="a" * 64,
                        inputs=[], identity_digests={}, parameters={})
    with pytest.raises(PhysicalLineageError, match="STOP_N1_NOT_AUTHORIZED"):
        require_n1_execution_authority(ctx)


def test_production_mode_alone_does_not_authorize_n1():
    ctx = _ctx(mode=ExecutionMode.PRODUCTION)
    with pytest.raises(PhysicalLineageError, match="no reviewed execution authorization"):
        require_n1_execution_authority(ctx)


def test_synthetic_mode_cannot_emit_a_physical_qualification_receipt(tmp_path):
    ctx = _ctx(mode=ExecutionMode.SYNTHETIC_TEST)
    with pytest.raises(PhysicalLineageError,
                       match="only PHYSICAL_QUALIFICATION"):
        emit_adapter_qualification_receipt(path=tmp_path / "r.json", ctx=ctx, body={})
    assert not (tmp_path / "r.json").exists()


def test_a_qualification_receipt_never_claims_n1_authority(tmp_path):
    ctx = build_context(mode=PHYS, task="adapter-qual", code_sha256="a" * 64,
                        inputs=[], identity_digests={}, parameters={})
    with pytest.raises(PhysicalLineageError, match="six distinct"):
        emit_adapter_qualification_receipt(
            path=tmp_path / "r.json", ctx=ctx,
            body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW"},
        )
    assert not (tmp_path / "r.json").exists()
