"""Independent ChatGPT probes of #498 on unchanged canonical_v1.py.

These tests do not authenticate the external Task2 T2-D scan issuer. The
generator-stream input remains a known, intentional untrusted-code boundary.
"""
import traceback
import numpy as np
import pytest

from scripts.production_synthetic import canonical_v1 as C


class Spoof:
    calls = 0

    @property
    def __class__(self):
        Spoof.calls += 1
        raise RuntimeError("payload __class__ executed")


@pytest.mark.parametrize("fn", [
    lambda x: C.semantic_sha256(x),
    lambda x: C.canonical_json_bytes(x),
    lambda x: C.ordered_registry_digest(x, ["id"]),
    lambda x: C.semantic_row_set_sha256(x, ["id"]),
])
def test_payload_class_cannot_run_in_canonical_entry(fn):
    Spoof.calls = 0
    with pytest.raises(C.CanonicalError):
        fn(Spoof())
    assert Spoof.calls == 0


class EvilBytes(bytes):
    calls = 0
    @property
    def __class__(self):
        EvilBytes.calls += 1
        raise RuntimeError("inherited bytes class property executed")


def test_bytes_subclass_refused_with_no_user_attribute_dispatch():
    EvilBytes.calls = 0
    with pytest.raises(C.CanonicalError):
        C.semantic_sha256(EvilBytes(b"a"))
    with pytest.raises(C.CanonicalError):
        C.raw_sha256(EvilBytes(b"a"))
    assert EvilBytes.calls == 0


class MutatingList(list):
    calls = 0
    def __iter__(self):
        MutatingList.calls += 1
        raise RuntimeError("payload iteration")

    @property
    def __class__(self):
        MutatingList.calls += 1
        raise RuntimeError("payload fake list")


@pytest.mark.parametrize("fn", [
    C.ordered_registry_digest, C.semantic_row_set_sha256,
])
def test_list_subclass_refused_without_iteration_or_class_access(fn):
    MutatingList.calls = 0
    with pytest.raises(C.CanonicalError):
        fn(MutatingList([{"id": "a"}]), ["id"])
    assert MutatingList.calls == 0


class MaliciousTypeError(TypeError):
    calls = 0
    def __str__(self):
        MaliciousTypeError.calls += 1
        raise RuntimeError("malicious exception formatting")


class IterFail:
    def __iter__(self):
        raise MaliciousTypeError()


@pytest.mark.parametrize("fn", [
    C.ordered_registry_digest, C.semantic_row_set_sha256,
])
def test_preiteration_typeerror_is_static_and_unlinked(fn):
    MaliciousTypeError.calls = 0
    with pytest.raises(C.CanonicalError) as info:
        fn(IterFail(), ["id"])
    assert info.value.__cause__ is None
    traceback.format_exception(info.value)
    assert MaliciousTypeError.calls == 0


@pytest.mark.parametrize("value,expected", [
    (np.int64(2**63-1), str(2**63-1).encode()),
    (np.uint64(2**64-1), str(2**64-1).encode()),
    (np.float32(0.1), repr(float(np.float32(0.1))).encode()),
    (np.bool_(True), b"true"),
])
def test_exact_numpy_scalar_domain_kept(value,expected):
    assert C.canonical_json_bytes(value) == expected


def test_live_iterator_remains_explicit_untrusted_producer_limitation():
    def rows():
        yield {"id": "A", "value": 1}
        raise RuntimeError("untrusted live producer")
    with pytest.raises(RuntimeError, match="untrusted live producer"):
        C.ordered_registry_digest(rows(), ["id"])
    # This is characterization of a remaining RED trust boundary,
    # not endorsement of generator source as externally authenticated.
