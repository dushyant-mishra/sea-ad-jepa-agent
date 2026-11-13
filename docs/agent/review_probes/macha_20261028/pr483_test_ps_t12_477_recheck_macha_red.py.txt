"""Macha independent review of PR #477 (PS canonical V1/V2 repair) at c83088de.

Fixture-only. Nothing here touches T2-D, the external scan issuer, which
stays RED. GREEN tests are guards or characterizations of a limitation;
`test_red_*` cases state required behavior the reviewed head lacks.
"""
from __future__ import annotations

import traceback

import pytest

from scripts.production_synthetic import canonical_v1 as C

_CALLS: list = []


class _RaisingClass:
    """`isinstance(x, T)` reads x.__class__ when type(x) is not a subclass of T."""

    @property
    def __class__(self):  # noqa: D401 - payload attribute
        _CALLS.append("__class__")
        raise RuntimeError("payload-chosen exception")


class _LyingClass:
    @property
    def __class__(self):
        _CALLS.append("__class__")
        return list


def _outcome(call):
    _CALLS.clear()
    try:
        call()
        escaped = "returned"
    except C.CanonicalError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    ran = len(_CALLS)
    return None if escaped is None and not ran else f"escape={escaped} payload_calls={ran}"


_ROUTES = {
    "semantic_sha256": lambda x: C.semantic_sha256(x),
    "ordered_registry_digest": lambda x: C.ordered_registry_digest(x, ["id"]),
    "semantic_row_set_sha256": lambda x: C.semantic_row_set_sha256(x, ["id"]),
}


@pytest.mark.parametrize("cls", [_RaisingClass, _LyingClass], ids=["raises", "lies"])
@pytest.mark.parametrize("route", sorted(_ROUTES))
def test_red_isinstance_guard_runs_payload_class_attribute(route, cls):
    """`isinstance(obj, (bytes, bytearray, memoryview))` in semantic_sha256 and
    `isinstance(rows, (list, tuple))` in _iter_rows run before any exact-type
    check. CPython's isinstance reads obj.__class__ for a non-subclass, so a
    payload property runs inside the refusal guard and may choose the exception
    (only AttributeError is swallowed). `type(x) is ...` checks run no code."""
    finding = _outcome(lambda: _ROUTES[route](cls()))
    if finding:
        pytest.fail(finding, pytrace=False)


class _PayloadTypeError(TypeError):
    def __str__(self):
        _CALLS.append("__str__")
        return "payload text"


class _IterRaises:
    def __iter__(self):
        raise _PayloadTypeError()


@pytest.mark.parametrize("route", ["ordered_registry_digest", "semantic_row_set_sha256"])
def test_red_domain_error_does_not_carry_a_payload_exception_into_formatting(route):
    """_iter_rows re-raises `from exc`, so the CanonicalError carries the
    payload's exception object as __cause__ and formatting the domain error
    (logs, CI) runs payload __str__. `from None` suppresses the chain."""
    _CALLS.clear()
    with pytest.raises(C.CanonicalError) as info:
        _ROUTES[route](_IterRaises())
    "".join(traceback.format_exception(info.value))
    if _CALLS:
        pytest.fail(f"formatting the domain error ran payload code {len(_CALLS)}x", pytrace=False)


def test_characterize_live_iterables_run_payload_code_and_escape_unwrapped():
    """LIMITATION (by design: 'ordinary generators remain lawful'). Rows may be
    any iterable, so producer code runs during digesting and its exceptions
    leave as themselves. The snapshot-first rule would accept only exact
    list/tuple rows, materialized before digesting."""
    def rows():
        yield {"id": "a"}
        raise RuntimeError("producer failure mid-digest")

    with pytest.raises(RuntimeError):
        C.ordered_registry_digest(rows(), ["id"])


def test_exact_dispatch_routes_stay_closed():
    """Guards: the encoder, raw/text/JSON byte entry points and numpy scalar
    whitelist use identity checks and run no payload code."""
    for fn in (C.canonical_json_bytes, C.raw_sha256, C.semantic_text_sha256,
               C.semantic_json_file_sha256, C.load_canonical_json):
        assert _outcome(lambda fn=fn: fn(_RaisingClass())) is None, fn.__name__
