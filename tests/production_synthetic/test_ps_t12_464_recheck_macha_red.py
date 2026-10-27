"""Independent hostile RED against ChatGPT's PS Task 1/2 repair #464 (tests only).

Target: scripts/production_synthetic/canonical_v1.py at
f6ee226c146c4c31d88ce5b845449ce21758cdeb. #458's twelve mechanical cases pass there;
these are the two classes Macha found in the Unified Task 1 encoder (#466) and ChatGPT
repaired there in #467, re-checked in the production-synthetic encoder.

V1  Platform type coverage (introduced by #464). The new exact-type whitelist names sized
    aliases only. On Windows `numpy.intc` / `numpy.uintc` (dtype chars 'i'/'I') are classes
    distinct from `numpy.int32` / `numpy.uint32` ('l'/'L'), so C-int scalars that the
    previous check (`type(x) is x.dtype.type`) encoded as plain integers are now refused.
    Where the classes coincide (Linux) this passes, so it needs a Windows job.
V2  The payload chooses the exception (pre-existing). Six refusal messages format
    `type(x).__name__`, which runs a metaclass `__getattribute__`; a StopIteration raised
    there leaves the encoder and silently shortens `list(map(semantic_sha256, rows))`.

Synthetic values only; nothing here grants authority.
"""
from __future__ import annotations

import warnings

import numpy as np
import pytest

from scripts.production_synthetic import canonical_v1 as C


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
def test_v1_every_numpy_scalar_class_keeps_the_lawful_bytes(cls):
    dtype = np.dtype(cls)
    if dtype.kind == "b":
        value, true_bytes = cls(True), b'{"v":true}'
    elif dtype.kind in "iu":
        value, true_bytes = cls(7), b'{"v":7}'
    elif dtype.itemsize <= 8:
        value, true_bytes = cls(1.5), b'{"v":1.5}'
    else:
        with pytest.raises(C.CanonicalError):  # wider than float64: refused, as before
            C.canonical_json_bytes({"v": cls(1.5)})
        return
    assert C.canonical_json_bytes({"v": value}) == true_bytes, f"{cls.__name__} (dtype char {dtype.char!r})"


class _ExceptionChoosingMeta(type):
    def __getattribute__(cls, name):
        if name == "__name__":
            raise StopIteration("chosen by the payload")
        return type.__getattribute__(cls, name)


class _ExceptionChooser(metaclass=_ExceptionChoosingMeta):
    pass


_V2_ROUTES = {
    "canonical_json_bytes": lambda: C.canonical_json_bytes({"v": _ExceptionChooser()}),
    "raw_sha256": lambda: C.raw_sha256(_ExceptionChooser()),
    "semantic_text_sha256": lambda: C.semantic_text_sha256(_ExceptionChooser()),
    "load_canonical_json": lambda: C.load_canonical_json(_ExceptionChooser()),
    "ordered_registry_digest_rows": lambda: C.ordered_registry_digest(_ExceptionChooser(), ["k"]),
    "ordered_registry_digest_row_key": lambda: C.ordered_registry_digest(
        [{"k": "a", _ExceptionChooser(): 1}], ["k"]),
}


def _escape(call):
    """Run ``call``; report what left the encoder as a plain string (no traceback kept,
    because pytest itself reads ``__name__`` of hostile classes while rendering one)."""
    try:
        call()
    except C.CanonicalError:
        return None
    except BaseException as exc:  # noqa: BLE001 - the escape type is the measurement
        return type(exc).__name__
    return "NO_ERROR"


@pytest.mark.parametrize("route", sorted(_V2_ROUTES))
def test_v2_payload_cannot_choose_the_exception_that_leaves_the_encoder(route):
    escaped = _escape(_V2_ROUTES[route])
    if escaped is not None:
        pytest.fail(f"{route}: {escaped} left the encoder instead of CanonicalError", pytrace=False)


def test_v2_hostile_row_cannot_silently_shorten_a_mapped_digest_list():
    rows = [{"i": 1}, {"bad": _ExceptionChooser()}, {"i": 3}]
    out = []
    escaped = _escape(lambda: out.extend(map(C.semantic_sha256, rows)))
    if escaped is not None:
        pytest.fail(f"{escaped}: mapped digest list has {len(out)} of 3 entries and no CanonicalError",
                    pytrace=False)
