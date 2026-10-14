"""Tests for the canonical identity and serialization contract (V3.1 section 3)."""
import hashlib
import itertools
import random

import numpy as np
import pytest

import scripts.production_synthetic.canonical_v1 as C


def test_key_permutation_invariance_nested():
    a = {"a": 1, "b": {"x": [1, 2, {"q": 1, "p": 2}], "y": None}, "c": "s"}
    b = {"c": "s", "b": {"y": None, "x": [1, 2, {"p": 2, "q": 1}]}, "a": 1}
    assert C.canonical_json_bytes(a) == C.canonical_json_bytes(b)
    assert C.semantic_sha256(a) == C.semantic_sha256(b)
    keys = ["k1", "k2", "k3", "k4"]
    ref = C.semantic_sha256({k: keys.index(k) for k in keys})
    for perm in itertools.permutations(keys):
        assert C.semantic_sha256({k: keys.index(k) for k in perm}) == ref


def test_canonical_format_compact_sorted_no_newline():
    assert C.canonical_json_bytes({"b": [1, 2.5], "a": None}) == b'{"a":null,"b":[1,2.5]}'


def test_list_order_is_significant():
    assert C.semantic_sha256([1, 2]) != C.semantic_sha256([2, 1])


def test_tuple_treated_as_list():
    assert C.canonical_json_bytes((1, 2)) == C.canonical_json_bytes([1, 2])


def test_raw_sha256_distinct_bytes_and_known_value():
    assert C.raw_sha256(b"") == hashlib.sha256(b"").hexdigest()
    assert C.raw_sha256(b"a\n") != C.raw_sha256(b"a\r\n")
    assert C.raw_sha256(b"a") != C.raw_sha256(b"b")


def test_raw_sha256_rejects_non_bytes():
    for bad in ("text", 1, None, bytearray(b"x"), memoryview(b"x")):
        with pytest.raises(C.CanonicalError):
            C.raw_sha256(bad)


def test_crlf_vs_lf_text_same_semantic_different_raw():
    lf = b"id\tv\nA\t1\nB\t2\n"
    crlf = lf.replace(b"\n", b"\r\n")
    cr = lf.replace(b"\n", b"\r")
    assert len({C.raw_sha256(lf), C.raw_sha256(crlf), C.raw_sha256(cr)}) == 3
    t = C.semantic_text_sha256
    assert t(lf) == t(crlf) == t(cr)
    assert t(lf) != t(lf + b"x")


def test_text_bom_stripped_and_bad_utf8_rejected():
    assert C.semantic_text_sha256(b"\xef\xbb\xbfabc") == C.semantic_text_sha256(b"abc")
    with pytest.raises(C.CanonicalError):
        C.semantic_text_sha256(b"\xff\xfe\x00")
    with pytest.raises(C.CanonicalError):
        C.semantic_text_sha256("str")


def test_semantic_sha256_rejects_bytes_no_type_dispatch():
    for bad in (b"abc", b"", bytearray(b"x")):
        with pytest.raises(C.CanonicalError):
            C.semantic_sha256(bad)


def test_json_file_identity_vs_text_identity():
    a = b'{"a":1,"b":[1,2]}'
    b = b'\xef\xbb\xbf{ "b" : [1, 2],\r\n  "a" : 1 }\r\n'
    assert C.raw_sha256(a) != C.raw_sha256(b)
    assert C.semantic_json_file_sha256(a) == C.semantic_json_file_sha256(b)
    assert C.semantic_text_sha256(a) != C.semantic_text_sha256(b)
    assert C.semantic_json_file_sha256(a) == C.semantic_sha256({"a": 1, "b": [1, 2]})
    with pytest.raises(C.CanonicalError):
        C.semantic_json_file_sha256(b'{"a":1,"a":2}')


def test_string_values_line_endings_normalized_no_unicode_normalization():
    assert C.canonical_json_bytes("a\r\nb\rc") == C.canonical_json_bytes("a\nb\nc")
    assert C.canonical_json_bytes({"k\r\n": 1}) == C.canonical_json_bytes({"k\n": 1})
    # identifiers stay exact: composed vs decomposed e-acute differ
    assert C.semantic_sha256("\u00e9") != C.semantic_sha256("e\u0301")
    assert C.canonical_json_bytes("\u00e9") == b'"\xc3\xa9"'


def test_nan_inf_rejected():
    for bad in (float("nan"), float("inf"), float("-inf"), np.float64("nan"), np.float32("inf")):
        with pytest.raises(C.CanonicalError):
            C.canonical_json_bytes({"x": [bad]})


def test_none_distinct_from_zero_and_zero_float():
    vals = (None, 0, 0.0, False, "", [], {})
    assert len({C.semantic_sha256(v) for v in vals}) == len(vals)
    assert C.canonical_json_bytes(None) == b"null"


def test_bool_distinct_from_int():
    assert C.semantic_sha256(True) != C.semantic_sha256(1)
    assert C.semantic_sha256(False) != C.semantic_sha256(0)
    assert C.canonical_json_bytes([True, 1]) == b"[true,1]"


def test_negative_zero_equals_zero_semantically():
    assert C.semantic_sha256(-0.0) == C.semantic_sha256(0.0)
    assert C.canonical_json_bytes({"x": -0.0}) == b'{"x":0.0}'
    assert C.semantic_sha256(np.float64(-0.0)) == C.semantic_sha256(0.0)


def test_float_one_distinct_from_int_one():
    assert C.semantic_sha256(1.0) != C.semantic_sha256(1)
    assert C.canonical_json_bytes([1.0, 1]) == b"[1.0,1]"


def test_float_shortest_roundtrip_and_large_int_exact():
    assert C.canonical_json_bytes(0.1) == b"0.1"
    assert C.canonical_json_bytes(2 ** 70) == str(2 ** 70).encode()
    x = 1.0 / 3.0
    assert float(C.canonical_json_bytes(x)) == x


def test_non_str_keys_rejected():
    for bad in ({1: "a"}, {None: "a"}, {("a",): 1}, {True: 1}, {1.5: 1}):
        with pytest.raises(C.CanonicalError):
            C.canonical_json_bytes(bad)


def test_colliding_keys_after_line_ending_normalization_rejected():
    with pytest.raises(C.CanonicalError):
        C.canonical_json_bytes({"a\r\n": 1, "a\n": 2})


def test_unsupported_types_rejected():
    for bad in ({1, 2}, frozenset([1]), np.array([1, 2]), b"raw", object(), 1 + 2j):
        with pytest.raises(C.CanonicalError):
            C.canonical_json_bytes(bad)


def test_numpy_scalars_convert_to_python_equivalents():
    assert C.canonical_json_bytes(np.int64(5)) == b"5"
    assert C.canonical_json_bytes(np.uint8(7)) == b"7"
    assert C.canonical_json_bytes(np.float64(2.5)) == b"2.5"
    assert C.canonical_json_bytes(np.float32(0.5)) == b"0.5"
    assert C.canonical_json_bytes(np.bool_(True)) == b"true"
    assert C.semantic_sha256({"a": np.int32(3)}) == C.semantic_sha256({"a": 3})
    assert C.semantic_sha256(np.float64(1.0)) == C.semantic_sha256(1.0)
    assert C.semantic_sha256(np.bool_(False)) != C.semantic_sha256(0)


def test_semantic_differs_from_raw_for_identical_bytes():
    obj = {"a": 1}
    data = C.canonical_json_bytes(obj)
    assert C.semantic_sha256(obj) != C.raw_sha256(data)
    assert C.semantic_text_sha256(b"abc") != C.raw_sha256(b"abc")
    # text-domain and json-domain are distinct too
    assert C.semantic_text_sha256(b'"abc"') != C.semantic_sha256("abc")


def _rows(n=50):
    return [{"address_index": i, "address_id": f"ADDR{i:05d}", "v": float(i) / 7} for i in range(n)]


def test_ordered_registry_digest_order_sensitive():
    rows = _rows()
    d = C.ordered_registry_digest(rows, ["address_id"])
    swapped = list(rows)
    swapped[3], swapped[4] = swapped[4], swapped[3]
    assert C.ordered_registry_digest(swapped, ["address_id"]) != d
    assert C.ordered_registry_digest(rows[::-1], ["address_id"]) != d
    assert C.ordered_registry_digest(rows, ["address_id"]) == d


def test_ordered_registry_digest_key_perm_invariant_but_content_bound():
    rows = _rows()
    ik = ["address_index", "address_id"]
    d = C.ordered_registry_digest(rows, ik)
    rows2 = [dict(reversed(list(r.items()))) for r in rows]
    assert C.ordered_registry_digest(rows2, ik) == d
    rows3 = [dict(r) for r in rows]
    rows3[10]["v"] += 1.0
    assert C.ordered_registry_digest(rows3, ik) != d
    assert C.ordered_registry_digest(rows, ["address_id"]) != d  # identity_keys bound
    assert C.ordered_registry_digest(rows[:-1], ik) != d


def test_ordered_registry_digest_rejections():
    rows = _rows(5)
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest([], ["address_id"])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows, [])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows, ["nope"])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows + [dict(rows[0])], ["address_id"])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows, ["address_id", "address_id"])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows, "address_id")
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest([1, 2], ["a"])
    bad = [dict(r) for r in rows]
    bad[2]["address_id"] = None  # a missing value cannot be an identity
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(bad, ["address_id"])


def test_registry_distinct_from_row_set_domain():
    rows = _rows(5)
    assert C.ordered_registry_digest(rows, ["address_id"]) != C.semantic_row_set_sha256(rows, ["address_id"])


def test_row_set_permutation_and_shard_reordering_invariance():
    rows = _rows(60)
    ref = C.semantic_row_set_sha256(rows, ["address_id"])
    rng = random.Random(0)
    for _ in range(5):
        p = list(rows)
        rng.shuffle(p)
        assert C.semantic_row_set_sha256(p, ["address_id"]) == ref
    shards = [rows[0:10], rows[10:35], rows[35:60]]
    for order in itertools.permutations(range(3)):
        cat = [r for i in order for r in shards[i]]
        assert C.semantic_row_set_sha256(cat, ["address_id"]) == ref
    flipped = [dict(reversed(list(r.items()))) for r in rows]
    assert C.semantic_row_set_sha256(flipped, ["address_id"]) == ref


def test_row_set_sensitive_to_values_and_membership():
    rows = _rows(20)
    ref = C.semantic_row_set_sha256(rows, ["address_id"])
    mod = [dict(r) for r in rows]
    mod[5]["v"] = None
    assert C.semantic_row_set_sha256(mod, ["address_id"]) != ref
    mod = [dict(r) for r in rows]
    mod[5]["v"] = 0
    assert C.semantic_row_set_sha256(mod, ["address_id"]) != ref
    assert C.semantic_row_set_sha256(rows[:-1], ["address_id"]) != ref
    with pytest.raises(C.CanonicalError):
        C.semantic_row_set_sha256(rows + [dict(rows[1])], ["address_id"])
    with pytest.raises(C.CanonicalError):
        C.semantic_row_set_sha256([], ["address_id"])


def test_row_set_int_vs_string_identity_not_confusable():
    a = [{"id": 1, "v": 0}, {"id": 2, "v": 0}]
    b = [{"id": "1", "v": 0}, {"id": "2", "v": 0}]
    assert C.semantic_row_set_sha256(a, ["id"]) != C.semantic_row_set_sha256(b, ["id"])


def test_full_41238_registry_digest_deterministic_and_swap_sensitive():
    n = 41238
    rows = [{"address_index": i, "address_id": f"ADDR{i:05d}"} for i in range(n)]
    keys = ["address_index", "address_id"]
    d1 = C.ordered_registry_digest(rows, keys)
    d2 = C.ordered_registry_digest([dict(r) for r in rows], keys)
    assert d1 == d2 and len(d1) == 64
    s = list(rows)
    s[100], s[20000] = s[20000], s[100]
    assert C.ordered_registry_digest(s, keys) != d1
    # the order-invariant set identity does not move under the same swap
    assert C.semantic_row_set_sha256(s, keys) == C.semantic_row_set_sha256(rows, keys)
    assert C.ordered_registry_digest((r for r in rows), keys) == d1


def test_huge_int_beyond_str_limit_rejected_as_canonical_error():
    with pytest.raises(C.CanonicalError):
        C.canonical_json_bytes(10 ** 5000)


def test_numpy_datetime_and_timedelta_rejected():
    for bad in (np.timedelta64(5, "s"), np.timedelta64("NaT"), np.datetime64("2020-01-01"), np.datetime64("NaT")):
        with pytest.raises(C.CanonicalError):
            C.canonical_json_bytes({"x": bad})


def test_identity_keys_normalized_like_row_keys():
    rows = [{"a\r\n": 1, "v": 0}, {"a\r\n": 2, "v": 0}]
    d = C.ordered_registry_digest(rows, ["a\n"])
    assert d == C.ordered_registry_digest([{"a\n": 1, "v": 0}, {"a\n": 2, "v": 0}], ["a\r\n"])
    assert C.semantic_row_set_sha256(rows, ["a\n"]) == C.semantic_row_set_sha256(rows, ["a\r\n"])
    with pytest.raises(C.CanonicalError):
        C.ordered_registry_digest(rows, ["a\n", "a\r\n"])


def test_load_canonical_json_equivalent_serializations():
    a, b = b'{"a":1}', b'{ "a" : 1 }\r\n'
    assert C.raw_sha256(a) != C.raw_sha256(b)
    assert C.semantic_sha256(C.load_canonical_json(a)) == C.semantic_sha256(C.load_canonical_json(b))
    assert C.load_canonical_json(b"\xef\xbb\xbf" + a) == {"a": 1}
    assert C.load_canonical_json(b"[1.0,1]") == [1.0, 1]
    assert isinstance(C.load_canonical_json(b"[1.0]")[0], float)


def test_load_canonical_json_rejections():
    for bad in (b'{"a":1,"a":2}', b'{"a":{"b":1,"b":1}}', b'{"a":NaN}', b'[Infinity]', b'[-Infinity]',
                b'{"a":1} x', b'{"a":1}{"b":2}', b'[1e999]', b'\xff', b'', b'{', b'[1' + b'0' * 5000 + b']'):
        with pytest.raises(C.CanonicalError):
            C.load_canonical_json(bad)
    with pytest.raises(C.CanonicalError):
        C.load_canonical_json('{"a":1}')


def test_row_set_missing_identity_key_and_none_identity_rejected():
    rows = _rows(5)
    with pytest.raises(C.CanonicalError):
        C.semantic_row_set_sha256(rows, ["nope"])
    bad = [dict(r) for r in rows]
    bad[1]["address_id"] = None
    with pytest.raises(C.CanonicalError):
        C.semantic_row_set_sha256(bad, ["address_id"])


def test_loader_rejects_underflow_to_zero_but_accepts_true_zero():
    for bad in (b"1e-400", b"2.4e-324", b"-1e-400", b"[0.000001e-999]"):
        with pytest.raises(C.CanonicalError):
            C.load_canonical_json(bad)
    for ok in (b"0e-400", b"0.0", b"-0.0", b"0", b"0.000e5"):
        assert C.load_canonical_json(ok) == 0
    v = C.load_canonical_json(b"5e-324")
    assert v == 5e-324 and v != 0.0
    assert C.load_canonical_json(b"0.10000000000000000001") == 0.1  # documented float64 rounding


def test_loader_rejects_lone_surrogates():
    for bad in (rb'"\ud800"', rb'["\udfff"]', rb'{"k":"x\ud800y"}', rb'{"\ud800":1}'):
        with pytest.raises(C.CanonicalError):
            C.load_canonical_json(bad)
    assert C.load_canonical_json(rb'"\ud83d\ude00"') == "\U0001F600"


def test_loader_rejects_keys_colliding_after_eol_normalization():
    with pytest.raises(C.CanonicalError):
        C.load_canonical_json(rb'{"a\r\n":1,"a\n":2}')
    with pytest.raises(C.CanonicalError):
        C.load_canonical_json(rb'{"x":{"a\r":1,"a\n":2}}')


def test_non_iterable_rows_rejected_in_both_digests():
    for bad in (None, 5, 1.5):
        with pytest.raises(C.CanonicalError):
            C.ordered_registry_digest(bad, ["a"])
        with pytest.raises(C.CanonicalError):
            C.semantic_row_set_sha256(bad, ["a"])


def test_identity_key_order_canonicalized_in_both_digests():
    rows = [{"a": i, "b": str(i), "v": 0} for i in range(5)]
    assert C.ordered_registry_digest(rows, ["a", "b"]) == C.ordered_registry_digest(rows, ["b", "a"])
    assert C.semantic_row_set_sha256(rows, ["a", "b"]) == C.semantic_row_set_sha256(rows, ("b", "a"))
    assert C.ordered_registry_digest(rows, ["a", "b"]) != C.ordered_registry_digest(rows, ["a"])


@pytest.mark.skipif(np.dtype(np.longdouble).itemsize <= 8, reason="longdouble is float64 on this platform")
def test_wide_numpy_float_rejected():
    with pytest.raises(C.CanonicalError):
        C.canonical_json_bytes(np.longdouble(0.1))


def test_numpy_float16_float32_widen_to_float64():
    assert C.canonical_json_bytes(np.float16(0.5)) == b"0.5"
    assert C.canonical_json_bytes(np.float32(0.1)) == repr(float(np.float32(0.1))).encode()


def _rand_obj(rng, depth=0):
    kind = rng.randrange(8 if depth < 4 else 6)
    if kind == 0:
        return None
    if kind == 1:
        return rng.random() < 0.5
    if kind == 2:
        return rng.randrange(-10 ** 12, 10 ** 12)
    if kind == 3:
        return rng.choice([0.0, -0.0, 1.0, 0.1, 1e16, 1e-5, 5e-324, 1.7976931348623157e308,
                           rng.uniform(-1e6, 1e6), rng.uniform(-1, 1) * 10.0 ** rng.randrange(-300, 300)])
    if kind in (4, 5):
        alphabet = ["a", "b", "\x00", "\x1f", "\t", "\n", "\x7f", "é", "é", "\U0001F600", '"', "\\", " "]
        return "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 6)))
    if kind == 6:
        return [_rand_obj(rng, depth + 1) for _ in range(rng.randrange(0, 4))]
    return {_rand_obj_key(rng): _rand_obj(rng, depth + 1) for _ in range(rng.randrange(0, 4))}


def _rand_obj_key(rng):
    alphabet = ["k", "j", "\n", "é", "\U0001F600", '"', "\\", "\x01"]
    return "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 4)))


def test_canonical_bytes_are_a_fixed_point_of_strict_load_property():
    rng = random.Random(20261014)
    for _ in range(3000):
        x = _rand_obj(rng)
        b = C.canonical_json_bytes(x)
        assert C.canonical_json_bytes(C.load_canonical_json(b)) == b


# ---------------------------------------------------------------------------
# Known-answer tests: frozen byte format. Values were computed once from the
# implementation and cross-checked against an independent re-implementation
# written only from the module docstring. A change here is a format break.
# ---------------------------------------------------------------------------

def test_kat_canonical_bytes_with_escapes_unicode_and_floats():
    obj = {
        "s": "\x00\x1f\t\n\x7fé\U0001F600",
        "f": [1e16, 1e-5, 5e-324, 0.1, -0.0, 1.0],
    }
    expected = (
        b'{"f":[1e+16,1e-05,5e-324,0.1,0.0,1.0],'
        b'"s":"\\u0000\\u001f\\t\\n\x7f\xc3\xa9\xf0\x9f\x98\x80"}'
    )
    assert C.canonical_json_bytes(obj) == expected


def test_kat_semantic_sha256_json_object():
    obj = {"b": [1, 2.5, None, True], "a": {"z": 0, "y": 0.0}, "c": "x"}
    assert C.canonical_json_bytes(obj) == b'{"a":{"y":0.0,"z":0},"b":[1,2.5,null,true],"c":"x"}'
    assert C.semantic_sha256(obj) == "9985d6352461c786289baa95b34c9523d607f6559dd0df4f02b8ab43ab321ecd"


def test_kat_semantic_text_sha256():
    assert C.semantic_text_sha256(b"id\tv\r\nA\t1\r\n") == (
        "383690d22cc9059e6132f0b6ad1ef3ef9f9e9c4e3caf183ec57a4667df61165b"
    )
    assert C.semantic_text_sha256(b"id\tv\nA\t1\n") == (
        "383690d22cc9059e6132f0b6ad1ef3ef9f9e9c4e3caf183ec57a4667df61165b"
    )


def test_kat_registry_and_row_set_digests():
    rows = [{"i": 0, "n": "A"}, {"i": 1, "n": "B"}, {"i": 2, "n": "C"}]
    assert C.ordered_registry_digest(rows, ["i"]) == (
        "5d2356c29572e267f707a806e8ca28c7a8addd7c98b83d32395b4ab24e8c1387"
    )
    assert C.ordered_registry_digest(rows, ["n", "i"]) == (
        "034242f85237cd803e081c91fa6adc709f68e8b7740026bf42655e6b6f2b8d39"
    )
    assert C.ordered_registry_digest(rows, ["i", "n"]) == C.ordered_registry_digest(rows, ["n", "i"])
    assert C.semantic_row_set_sha256(rows, ["i"]) == (
        "7c65a8d0ddf15b5411458a2c91437c6001c701f0db51433d8eefcdbf8c3a5586"
    )
    assert C.semantic_row_set_sha256(rows[::-1], ["i"]) == C.semantic_row_set_sha256(rows, ["i"])
