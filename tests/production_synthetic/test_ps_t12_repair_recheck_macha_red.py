"""Independent hostile recheck of the PS Task 1-2 repair chain (#453 @ 8641a62a, #456 @ 3b42b6c1).

Tests-only. Every test here FAILS at 3b42b6c1 for the reason stated in its comment; none changes an
implementation file. Inputs are tiny synthetic dummies: no production nonce, withheld specification,
protected value or real data. Nothing here grants authority.

Scope: the #453 claim "exact built-in containers and numerics only" (canonical_v1) and the #456
claim "exact built-in secret/root, SHA text, tag and budget types" (custody_v1). A refusal, or output
equal to the TRUE value's bytes, is acceptable everywhere; forged output is not.
"""
from __future__ import annotations

import types
from pathlib import Path

import numpy as np
import pytest

from scripts.production_synthetic import canonical_v1 as C
from scripts.production_synthetic import custody_v1 as CU
from tests.production_synthetic import custody_fixtures_v1 as fx


def _refused_or_equal(fn, true_value):
    try:
        got = fn()
    except C.CanonicalError:
        return
    assert got == true_value, f"forged output: {got!r} != true {true_value!r}"


# ---------------------------------------------------------------------------
# R1 (Task 1, #453): `_exact_numpy_scalar` trusts `type(x) is x.dtype.type`, but `dtype` is an
# ordinary attribute a subclass can override. A np.int64 / np.float64 subclass that reports its own
# class as dtype.type passes as an "exact" numpy scalar, then `int(obj)` / `float(obj)` call the
# subclass's __int__ / __float__: an int64 equal to 5 encodes as 999.
# ---------------------------------------------------------------------------
class _DtypeLyingInt64(np.int64):
    dtype = property(lambda self: types.SimpleNamespace(type=_DtypeLyingInt64, itemsize=8))

    def __int__(self):
        return 999

    def __index__(self):
        return 999


class _DtypeLyingFloat64(np.float64):
    dtype = property(lambda self: types.SimpleNamespace(type=_DtypeLyingFloat64, itemsize=8))

    def __float__(self):
        return 999.0


@pytest.mark.parametrize("forged, true_bytes", [(_DtypeLyingInt64(5), b"5"), (_DtypeLyingFloat64(1.5), b"1.5")],
                         ids=["int64", "float64"])
def test_r1_numpy_scalar_subclass_that_overrides_dtype_cannot_forge_bytes(forged, true_bytes):
    _refused_or_equal(lambda: C.canonical_json_bytes({"v": forged}), b'{"v":' + true_bytes + b"}")


# ---------------------------------------------------------------------------
# R2 (Task 1, #453): a plain object that is NOT numpy at all. `isinstance(x, np.generic)` follows the
# instance's `__class__` attribute, and the exactness check reads its `dtype` attribute, so a duck
# with both properties is serialized as an integer of its own choosing. The only lawful outcome for a
# non-numpy, non-built-in object is refusal.
# ---------------------------------------------------------------------------
class _NumpyImpostor:
    __class__ = property(lambda self: np.int64)
    dtype = property(lambda self: types.SimpleNamespace(type=_NumpyImpostor, itemsize=8))

    def __int__(self):
        return 999

    def __index__(self):
        return 999


def test_r2_non_numpy_object_claiming_a_numpy_class_is_refused():
    with pytest.raises(C.CanonicalError):
        C.canonical_json_bytes({"v": _NumpyImpostor()})


# ---------------------------------------------------------------------------
# R3 (Task 1, #453): `kind in (list, tuple)` is an EQUALITY test on type objects. A metaclass with a
# permissive __eq__ makes a list/tuple subclass compare equal to `list`, so the subclass's overridden
# __iter__ supplies the serialized elements: [5] encodes as [999]. Exact dispatch needs `is`.
# ---------------------------------------------------------------------------
class _PermissiveEqMeta(type):
    def __eq__(cls, other):
        return True

    __hash__ = type.__hash__


class _ForgedListByMeta(list, metaclass=_PermissiveEqMeta):
    def __iter__(self):
        return iter([999])


class _ForgedTupleByMeta(tuple, metaclass=_PermissiveEqMeta):
    def __iter__(self):
        return iter([999])


@pytest.mark.parametrize("forged", [_ForgedListByMeta([5]), _ForgedTupleByMeta((5,))], ids=["list", "tuple"])
def test_r3_sequence_subclass_with_permissive_metaclass_eq_cannot_forge_bytes(forged):
    assert type(forged) in (list, tuple) and type(forged) is not list and type(forged) is not tuple
    _refused_or_equal(lambda: C.canonical_json_bytes(forged), b"[5]")


# ---------------------------------------------------------------------------
# R4 (Task 1, #453): `_check_keys` uses `type(identity_keys) not in (list, tuple)`, the same equality
# test. A key container that stores ["id"] but iterates ["other"] makes the row-set digest bind a
# DIFFERENT identity-key set than the caller passed (here byte-identical to keys=["other"]).
# ---------------------------------------------------------------------------
class _ForgedKeysByMeta(list, metaclass=_PermissiveEqMeta):
    def __iter__(self):
        return iter(["other"])


_ROWS = [{"id": "a", "other": "x", "v": 1}, {"id": "b", "other": "y", "v": 2}]


@pytest.mark.parametrize("fn", ["semantic_row_set_sha256", "ordered_registry_digest"])
def test_r4_identity_key_container_with_permissive_metaclass_eq_cannot_rebind_keys(fn):
    true = getattr(C, fn)(_ROWS, ["id"])
    assert true != getattr(C, fn)(_ROWS, ["other"])
    _refused_or_equal(lambda: getattr(C, fn)(_ROWS, _ForgedKeysByMeta(["id"])), true)


# ---------------------------------------------------------------------------
# R5 (Task 1, MINOR; pre-existing at ff597faf, not introduced by #453): `rows` is any iterable by
# documented design (generators/shards), but a LIST-typed container whose iteration disagrees with its
# stored contents gives a digest of rows nobody stored: stored v=1, digest equals that of v=999.
# Smallest repair: exact list/tuple when a sequence is passed (generators stay allowed).
# ---------------------------------------------------------------------------
class _RowsIterateDifferently(list):
    def __iter__(self):
        return iter([{"id": "a", "v": 999}])


@pytest.mark.parametrize("fn", ["semantic_row_set_sha256", "ordered_registry_digest"])
def test_r5_list_typed_rows_container_cannot_digest_rows_it_does_not_store(fn):
    stored = [{"id": "a", "v": 1}]
    true = getattr(C, fn)(stored, ["id"])
    _refused_or_equal(lambda: getattr(C, fn)(_RowsIterateDifferently(stored), ["id"]), true)


# ---------------------------------------------------------------------------
# T2-R1 (Task 2; pre-existing, NOT swept by #456): scan_secret_absence still accepts
# `isinstance(secret_bytes, bytes)` and reads `len(...)`. A 4-byte secret that claims 64 bytes is
# scanned and attested absent, bypassing the declared 16-byte (128-bit) PROSPECTIVE_CONVENTION minimum.
# ---------------------------------------------------------------------------
class _ShortSecretClaimingLength(bytes):
    def __len__(self):
        return 64


def _tree(tmp_path: Path) -> Path:
    tree = tmp_path / "tree"
    (tree / "d").mkdir(parents=True)
    (tree / "d" / "public.txt").write_bytes(b"public fixture\n")
    return tree


def test_t2r1_secret_scan_refuses_a_secret_below_the_physical_minimum_length(tmp_path):
    secret = _ShortSecretClaimingLength(b"\x01\x02\x03\x04")
    assert bytes.__len__(secret) == 4 < CU.MIN_SCAN_SECRET_BYTES
    with pytest.raises(CU.CustodyError):
        CU.scan_secret_absence(_tree(tmp_path), secret)


# ---------------------------------------------------------------------------
# T2-R2 (Task 2; pre-existing, NOT swept by #456): the scanner builds its hex needle with the
# caller object's own `.hex()`. A bytes subclass overriding hex() makes a tree that CONTAINS the
# secret's hex encoding attest `secret_absent=True` (exact bytes correctly report False).
# ---------------------------------------------------------------------------
class _HexHidingSecret(bytes):
    def hex(self, *args):
        return "zz" * bytes.__len__(self)


def test_t2r2_secret_scan_cannot_be_blinded_by_a_bytes_subclass(tmp_path):
    secret = bytes(range(40, 72))
    tree = _tree(tmp_path)
    (tree / "d" / "leak.txt").write_bytes(b"value=" + secret.hex().encode("ascii") + b"\n")
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is False
    try:
        att = CU.scan_secret_absence(tree, _HexHidingSecret(secret))
    except CU.CustodyError:
        return
    assert att["secret_absent"] is False, "false secret-absence attestation for a hex-encoded leak"


# ---------------------------------------------------------------------------
# T2-R3 (Task 2, LOW; introduced by the chain: #453 made canonical_v1 strict, #456 did not wrap this
# call): a str-subclass realization_id passes `isinstance(..., str)` in attest_realization_set and then
# escapes as a raw C.CanonicalError from the unwrapped semantic_row_set_sha256 call. Fail-closed, but
# the module contract is "CustodyError for every custody refusal" (no-echo wrapping).
# ---------------------------------------------------------------------------
class _RealizationIdSubclass(str):
    pass


def test_t2r3_str_subclass_realization_id_is_refused_as_a_custody_error(tmp_path):
    freeze, qnonce = fx.make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(freeze, led)
    nonces = {fx.DEBUG: fx.dummy_nonce(), fx.QUAL: qnonce}
    for tag in (fx.DEBUG, fx.QUAL):
        CU.record_nonce_commitment(freeze, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
    fx.commit_withheld(freeze, qnonce, led, fx.make_tree(tmp_path))
    budget = freeze.realization_budget(fx.DEBUG)
    root = CU.sealed_root(nonces[fx.DEBUG], freeze.generator_semantic_hash, fx.DEBUG, budget)
    rows = [dict(r, realization_id=_RealizationIdSubclass(r["realization_id"])) for r in fx.emit(root, fx.DEBUG, budget)]
    with pytest.raises(CU.CustodyError):
        CU.attest_realization_set(freeze, led, root=root, class_tag=fx.DEBUG, emitted=rows)


# ---------------------------------------------------------------------------
# T2-D (Task 2 DESIGN, author-disclosed by Macha, who wrote this code; pre-existing at ff597faf):
# record_withheld_commitment accepts any hand-written mapping with the scan keys as a
# "secret-absence attestation" -- no scan has to have run, and tree_identity is never checked against
# anything. The WITHHELD_COMMITTED entry therefore proves only that the caller asserted absence. The
# Tasks 1-2 checkpoint declares this for defect records (O8) but not for scans. Remedies (deciding
# lane): bind attestations to module-issued private records, OR declare the narrower trust model IN
# CODE and convert this test to a strict xfail referencing that declaration.
# ---------------------------------------------------------------------------
def test_t2d_hand_written_secret_absence_attestation_is_not_accepted_as_a_scan():
    freeze, qnonce = fx.make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(freeze, led)
    for tag in (fx.DEBUG, fx.QUAL):
        n = qnonce if tag == fx.QUAL else fx.dummy_nonce()
        CU.record_nonce_commitment(freeze, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(n))
    never_scanned = [{"secret_absent": True, "tree_identity": "a" * 64, "files_scanned": 1,
                      "nonce_commitment": CU.nonce_commitment(qnonce)}]
    with pytest.raises(CU.CustodyError):
        CU.record_withheld_commitment(freeze, led, withheld_class_tag=fx.WTAG,
                                      nonce_commitment=CU.nonce_commitment(qnonce),
                                      secret_absence_attestations=never_scanned,
                                      code_path_attestation=fx.code_path_attestation())
