"""ChatGPT repair guards for PR #477 against immutable Macha #483.

Fixture mechanics only. Live producer iterables remain an explicit trust-boundary
limitation. T2-D external scan issuer remains RED and is not touched here.
"""
import traceback

import pytest

from scripts.production_synthetic import canonical_v1 as C


class _BytesSub(bytes):
    pass


class _ListSub(list):
    def __iter__(self):
        raise RuntimeError("subclass iterator must never run")


def test_bytes_family_subclasses_do_not_gain_semantic_sha_dispatch():
    with pytest.raises(C.CanonicalError):
        C.semantic_sha256(_BytesSub(b"x"))


def test_list_subclass_is_rejected_without_running_overridden_iterator():
    with pytest.raises(C.CanonicalError, match="exact built-in"):
        C.ordered_registry_digest(_ListSub([{"id": "a"}]), ["id"])


class _PayloadTypeError(TypeError):
    def __str__(self):
        raise RuntimeError("payload __str__ must not run")


class _Rows:
    def __iter__(self):
        raise _PayloadTypeError()


@pytest.mark.parametrize("fn", [C.ordered_registry_digest, C.semantic_row_set_sha256])
def test_iterator_typeerror_is_suppressed_from_domain_error_chain(fn):
    with pytest.raises(C.CanonicalError) as info:
        fn(_Rows(), ["id"])
    assert info.value.__cause__ is None
    # Formatting/logging the public domain error must not format the payload.
    traceback.format_exception(info.value)


def test_live_generator_behavior_is_preserved_as_explicit_limitation():
    def rows():
        yield {"id": "a"}
        raise RuntimeError("producer failure")

    with pytest.raises(RuntimeError, match="producer failure"):
        C.ordered_registry_digest(rows(), ["id"])
