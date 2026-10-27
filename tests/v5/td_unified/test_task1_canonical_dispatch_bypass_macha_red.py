"""Independent hostile RED against the ACCEPTED Unified Task 1 encoder (tests-only).

Target: scripts/v5/td_unified/canonical_v1.py blob 5f9a5249, identical at the Task 1 freeze
799d2e23, the Task 3 freeze 117dd51d, Task 4 #454 (028ecbd8) and #459 (57e70714). Found while
reviewing the parallel PS Task 1 repair (#453), whose R1-R3 bypasses (PR #458) share this code shape.

Every test FAILS at 799d2e23 for the reason in its comment. A refusal (CanonicalError) or output
equal to the TRUE value's bytes is acceptable; forged bytes are not. Synthetic dummies only; no
protected values. Nothing here grants authority.
"""
from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from scripts.v5.td_unified import canonical_v1 as U

REPO = Path(__file__).resolve().parents[3]


def _refused_or_true(fn, true_bytes):
    try:
        got = fn()
    except U.CanonicalError:
        return
    assert got == true_bytes, f"forged canonical bytes: {got!r} != true {true_bytes!r}"


# U1/U2: `_is_exact_numpy_scalar` trusts `type(v) is v.dtype.type`, but `dtype` is an attribute a
# subclass can override; the value is then read through the subclass's own __int__/__float__.
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


@pytest.mark.parametrize("forged,true_bytes", [(_DtypeLyingInt64(5), b'{"v":5}'),
                                               (_DtypeLyingFloat64(1.5), b'{"v":1.5}')], ids=["int64", "float64"])
def test_u1_u2_numpy_subclass_overriding_dtype_cannot_forge_bytes(forged, true_bytes):
    _refused_or_true(lambda: U.canonical_bytes({"v": forged}), true_bytes)


# U3: a non-numpy object: isinstance() follows its `__class__` property and the exactness check
# reads its `dtype` property. The only lawful outcome for a non-built-in, non-numpy object is refusal.
class _NumpyImpostor:
    __class__ = property(lambda self: np.int64)
    dtype = property(lambda self: types.SimpleNamespace(type=_NumpyImpostor, itemsize=8))

    def __int__(self):
        return 999

    def __index__(self):
        return 999


def test_u3_non_numpy_object_claiming_a_numpy_class_is_refused():
    with pytest.raises(U.CanonicalError):
        U.canonical_bytes({"v": _NumpyImpostor()})


# U4: `value_type in (list, tuple)` is an equality test on type objects; a metaclass __eq__ makes a
# list/tuple subclass "equal" to list, and its overridden __iter__ supplies the elements.
class _PermissiveEqMeta(type):
    def __eq__(cls, other):
        return True

    __hash__ = type.__hash__


class _ForgedList(list, metaclass=_PermissiveEqMeta):
    def __iter__(self):
        return iter([999])


class _ForgedTuple(tuple, metaclass=_PermissiveEqMeta):
    def __iter__(self):
        return iter([999])


@pytest.mark.parametrize("forged", [_ForgedList([5]), _ForgedTuple((5,))], ids=["list", "tuple"])
def test_u4_sequence_subclass_with_permissive_metaclass_eq_cannot_forge_bytes(forged):
    assert type(forged) in (list, tuple) and type(forged) is not list and type(forged) is not tuple
    _refused_or_true(lambda: U.canonical_bytes({"v": forged}), b'{"v":[5]}')


# U5: the forgery reaches the digest every consumer imports (actor_registry_v1, manifest_v1,
# registry_v1_legacy): a payload holding 5 must not share the identity of a payload holding 999.
@pytest.mark.parametrize("forged", [_DtypeLyingInt64(5), _ForgedList([5])], ids=["numpy", "metaclass"])
def test_u5_forged_values_cannot_take_another_payloads_identity(forged):
    try:
        digest = U.canonical_sha256({"v": forged})
    except U.CanonicalError:
        return
    assert digest != U.canonical_sha256({"v": 999 if not isinstance(forged, list) else [999]})


# U6: the exact-int path is `int.__str__`, so whether an integer HAS an identity depends on the
# interpreter's PYTHONINTMAXSTRDIGITS configuration (the T1-C class #453 closed for PS Task 1 with
# a portable 4,300-digit domain). The same payload must get the same outcome under every setting.
_PROBE = r"""
import sys
sys.path.insert(0, sys.argv[1])
from scripts.v5.td_unified import canonical_v1 as U
for digits in (1000, 4300, 5000):
    try:
        print(digits, U.canonical_sha256({"n": 10 ** (digits - 1)})[:16])
    except U.CanonicalError:
        print(digits, "REFUSED")
"""


def _probe(setting):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONINTMAXSTRDIGITS"}
    if setting is not None:
        env["PYTHONINTMAXSTRDIGITS"] = setting
    # No -I: isolated mode would ignore the PYTHONINTMAXSTRDIGITS setting under test.
    return subprocess.run([sys.executable, "-c", _PROBE, str(REPO)], env=env,
                          capture_output=True, text=True, timeout=120, check=True).stdout


def test_u6_integer_identity_domain_does_not_depend_on_interpreter_configuration():
    outcomes = {setting: _probe(setting) for setting in (None, "0", "640")}
    assert len(set(outcomes.values())) == 1, outcomes
