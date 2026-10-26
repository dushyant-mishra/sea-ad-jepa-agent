"""Author-disclosed RED for production-synthetic Task 1 (canonical_v1).

Macha (the Task 1 author) found these while reproducing Tasks 1-2 at
ff597faf for independent review. They are disclosed, not self-accepted.

Defect class: the encoder dispatches with isinstance and then calls
methods a subclass can override (__int__, __float__, str.replace, items,
__iter__, bytes.decode), so a value can carry canonical bytes that do not
describe it. The integer domain also follows the interpreter's
int-to-str digit limit, so whether a value has an identity at all depends
on PYTHONINTMAXSTRDIGITS.

Each test accepts either repair: refuse the object (CanonicalError), or
encode its true base-type value. Only forged bytes fail.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pytest

from scripts.production_synthetic import canonical_v1 as C

REPO = Path(__file__).resolve().parents[2]


def _refused_or_true(fn, true_bytes):
    try:
        got = fn()
    except C.CanonicalError:
        return
    assert got == true_bytes, f"forged canonical bytes: {got!r} (true value encodes as {true_bytes!r})"


class _ForgedInt(int):
    def __int__(self):
        return 999

    def __index__(self):
        return 999

    def __str__(self):
        return "999"

    def __repr__(self):
        return "999"


def test_int_subclass_cannot_forge_canonical_bytes():
    x = _ForgedInt(5)
    assert x == 5 and x + 0 == 5  # behaves as 5 everywhere else
    _refused_or_true(lambda: C.canonical_json_bytes(x), b"5")


class _ForgedFloat(float):
    def __float__(self):
        return 2.5

    def __repr__(self):
        return "2.5"


def test_float_subclass_cannot_forge_canonical_bytes():
    x = _ForgedFloat(1.5)
    assert x == 1.5
    _refused_or_true(lambda: C.canonical_json_bytes(x), b"1.5")


class _ForgedStr(str):
    def replace(self, *args, **kwargs):
        return "FORGED"


def test_str_subclass_cannot_forge_value_bytes():
    s = _ForgedStr("ok")
    assert s == "ok"
    _refused_or_true(lambda: C.canonical_json_bytes(s), b'"ok"')


def test_str_subclass_cannot_forge_mapping_key_bytes():
    _refused_or_true(lambda: C.canonical_json_bytes({_ForgedStr("k"): 1}), b'{"k":1}')


class _ForgedDict(dict):
    def items(self):
        return [("k", "forged")]


def test_dict_subclass_cannot_forge_mapping_bytes():
    d = _ForgedDict({"k": "real"})
    assert d["k"] == "real"
    _refused_or_true(lambda: C.canonical_json_bytes(d), b'{"k":"real"}')


class _DuckMapping(Mapping):
    """items() and item access disagree; there is no single value to hash."""

    def __init__(self):
        self._d = {"k": "real"}

    def __getitem__(self, k):
        return self._d[k]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return 1

    def items(self):
        return [("k", "forged")]


def test_mapping_whose_items_disagree_with_lookup_is_refused():
    m = _DuckMapping()
    assert m["k"] == "real"
    with pytest.raises(C.CanonicalError):
        C.canonical_json_bytes(m)


class _ForgedList(list):
    def __iter__(self):
        return iter([9, 9])


def test_list_subclass_cannot_forge_sequence_bytes():
    seq = _ForgedList([1, 2])
    assert seq[0] == 1 and seq[1] == 2
    _refused_or_true(lambda: C.canonical_json_bytes(seq), b"[1,2]")


class _ForgedTuple(tuple):
    def __iter__(self):
        return iter([9, 9])


def test_tuple_subclass_cannot_forge_sequence_bytes():
    seq = _ForgedTuple((1, 2))
    assert seq[0] == 1
    _refused_or_true(lambda: C.canonical_json_bytes(seq), b"[1,2]")


class _ForgedNpInt(np.int64):
    def __int__(self):
        return 999


def test_numpy_integer_subclass_cannot_forge_canonical_bytes():
    x = _ForgedNpInt(5)
    assert x == 5
    _refused_or_true(lambda: C.canonical_json_bytes(x), b"5")


class _ForgedRow(dict):
    def items(self):
        return [("id", "a"), ("v", 999)]  # well-formed, so only the value is forged


@pytest.mark.parametrize("digest", ["semantic_row_set_sha256", "ordered_registry_digest"])
def test_forged_row_cannot_forge_registry_identity(digest):
    fn = getattr(C, digest)
    row = _ForgedRow({"id": "a", "v": 1})
    assert row["v"] == 1
    true = fn([{"id": "a", "v": 1}], ["id"])
    try:
        got = fn([row], ["id"])
    except C.CanonicalError:
        return
    assert got == true, f"forged {digest}: equals digest of v=999? {got == fn([{'id': 'a', 'v': 999}], ['id'])}"


class _ForgedBytes(bytes):
    def decode(self, *args, **kwargs):
        return '{"k":"forged"}'


def test_bytes_subclass_cannot_forge_loaded_json():
    raw = _ForgedBytes(b'{"k":"real"}')
    try:
        got = C.load_canonical_json(raw)
    except C.CanonicalError:
        return
    assert got == {"k": "real"}, f"forged load: {got!r}"


def test_bytes_subclass_cannot_forge_text_identity():
    true = C.semantic_text_sha256(b'{"k":"real"}')
    try:
        got = C.semantic_text_sha256(_ForgedBytes(b'{"k":"real"}'))
    except C.CanonicalError:
        return
    assert got == true, "forged text identity"


# -- integer domain must not depend on interpreter configuration ------------

_PROBE = r"""
import sys
sys.path.insert(0, {repo!r})
from scripts.production_synthetic import canonical_v1 as C
n = 10 ** {digits_minus_one}
which = {which!r}
try:
    if which == "encode":
        out = C.canonical_json_bytes(n)
        print("OK", len(out), C.semantic_sha256(n))
    else:
        obj = C.load_canonical_json(b"[1" + b"0" * {digits_minus_one} + b"]")
        print("OK", len(str(obj[0])) if obj[0] == n else -1, C.semantic_sha256(obj))
except C.CanonicalError as exc:
    print("REFUSED", type(exc).__name__)
"""


def _probe(which, digits_minus_one, limit):
    env = dict(os.environ)
    env.pop("PYTHONINTMAXSTRDIGITS", None)
    if limit is not None:
        env["PYTHONINTMAXSTRDIGITS"] = str(limit)
    code = _PROBE.format(repo=str(REPO), digits_minus_one=digits_minus_one, which=which)
    # No -I/-E: the child must honour PYTHONINTMAXSTRDIGITS for this test to mean anything.
    proc = subprocess.run([sys.executable, "-c", code], env=env, cwd=str(REPO), capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return proc.stdout.strip()


@pytest.mark.parametrize("which", ["encode", "load"])
def test_integer_beyond_default_domain_refused_regardless_of_interpreter_limit(which):
    # 5001 digits: outside the documented 4300-digit default domain.
    default = _probe(which, 5000, None)
    unlimited = _probe(which, 5000, 0)
    assert unlimited == default, (
        f"identity domain depends on PYTHONINTMAXSTRDIGITS: default={default!r} unlimited={unlimited!r}"
    )
    assert default.startswith("REFUSED"), default


@pytest.mark.parametrize("which", ["encode", "load"])
def test_integer_inside_default_domain_identity_independent_of_interpreter_limit(which):
    # 1001 digits: inside the documented 4300-digit domain.
    default = _probe(which, 1000, None)
    lowered = _probe(which, 1000, 640)
    assert default.startswith("OK"), default
    assert lowered == default, (
        f"identity of a lawful integer depends on PYTHONINTMAXSTRDIGITS: default={default!r} lowered={lowered!r}"
    )
