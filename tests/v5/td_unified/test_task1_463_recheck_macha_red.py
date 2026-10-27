"""Independent hostile RED against ChatGPT's Unified Task 1 repair #463 (tests only).

Target: scripts/v5/td_unified/canonical_v1.py blob 8c05ea3a at
84b05952112ca405436ee3ccf35cc1c0df53c14d. #461's U1-U6 pass there; these are cases #461
did not anticipate. A refusal or the TRUE bytes is acceptable where stated; nothing else is.

V1  Platform type coverage. The frozen whitelist names sized aliases, but on Windows with
    NumPy 2.x `numpy.intc` / `numpy.uintc` are classes distinct from `numpy.int32` /
    `numpy.uint32` (dtype chars 'i'/'I' vs 'l'/'L'), so the C-int scalars that the accepted
    encoder (5f9a5249) encoded as plain integers are refused there. Where those classes
    coincide (Linux) this passes, so it needs the Windows job.
V2  The payload chooses the exception that leaves the encoder: building the refusal message
    reads `type(value).__name__`, which runs a metaclass `__getattribute__`. A StopIteration
    raised there silently shortens `list(map(canonical_sha256, rows))`. Present at 5f9a5249 too.

Synthetic values only; nothing here grants authority.
"""
from __future__ import annotations

import warnings

import numpy as np
import pytest

from scripts.v5.td_unified import canonical_v1 as U


def _numpy_scalar_classes():
    """Concrete bool/int/float scalar classes NumPy itself defines here (never test subclasses)."""
    seen, stack = set(), [np.generic]
    while stack:
        cls = stack.pop()
        if cls not in seen:
            seen.add(cls)
            stack.extend(cls.__subclasses__())
    concrete = []
    for cls in seen:
        if cls.__module__ != "numpy":
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                dtype = np.dtype(cls)
            except TypeError:
                continue
        if dtype.type is cls and dtype.kind in "biuf":
            concrete.append(cls)
    return sorted(concrete, key=lambda c: c.__name__)


_CLASSES = _numpy_scalar_classes()


def test_v1_enumeration_is_not_vacuous():
    required = {np.bool_, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32,
                np.uint64, np.float16, np.float32, np.float64}
    assert required <= set(_CLASSES)


@pytest.mark.parametrize("cls", _CLASSES, ids=lambda c: c.__name__)
def test_v1_every_numpy_scalar_class_keeps_the_accepted_bytes(cls):
    dtype = np.dtype(cls)
    if dtype.kind == "b":
        value, true_bytes = cls(True), b'{"v":true}'
    elif dtype.kind in "iu":
        value, true_bytes = cls(7), b'{"v":7}'
    elif dtype.itemsize <= 8:
        value, true_bytes = cls(1.5), b'{"v":1.5}'
    else:
        with pytest.raises(U.CanonicalError):  # wider than float64: refused, as at 5f9a5249
            U.canonical_bytes({"v": cls(1.5)})
        return
    assert U.canonical_bytes({"v": value}) == true_bytes, f"{cls.__name__} (dtype char {dtype.char!r})"


class _ExceptionChoosingMeta(type):
    def __getattribute__(cls, name):
        if name == "__name__":
            raise StopIteration("chosen by the payload")
        return type.__getattribute__(cls, name)


class _ExceptionChooser(metaclass=_ExceptionChoosingMeta):
    pass


def test_v2_payload_cannot_choose_the_exception_that_leaves_the_encoder():
    with pytest.raises(U.CanonicalError):
        U.canonical_bytes({"v": _ExceptionChooser()})


def test_v2_hostile_row_cannot_silently_shorten_a_mapped_digest_list():
    rows = [{"i": 1}, {"bad": _ExceptionChooser()}, {"i": 3}]
    with pytest.raises(U.CanonicalError):
        list(map(U.canonical_sha256, rows))
