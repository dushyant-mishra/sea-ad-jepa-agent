import sys, json, math, random, hashlib
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import numpy as np
import scripts.production_synthetic.canonical_v1 as C

def tryit(label, f):
    try:
        r = f()
        print(f"{label}: OK -> {r!r}")
    except C.CanonicalError as e:
        print(f"{label}: CanonicalError {e}")
    except Exception as e:
        print(f"{label}: OTHER {type(e).__name__}: {e}")

# floats
for x in [0.1+0.2, 1e-320, 5e-324, 1e308, 1e16, 1e22, -1e-7, 123456789012345680.0, 2.0**53, 2.0**53+2]:
    b = C.canonical_json_bytes(x)
    print("float", x, b, float(b) == x, isinstance(json.loads(b), float))
for t in [np.float16, np.float32, np.float64, np.longdouble]:
    v = t(0.1)
    tryit(f"np {t.__name__} 0.1", lambda: C.canonical_json_bytes(v))
tryit("float16 nan", lambda: C.canonical_json_bytes(np.float16("nan")))
tryit("np int64 2**62+1", lambda: C.canonical_json_bytes(np.int64(2**62+1)))
tryit("np uint64 max", lambda: C.canonical_json_bytes(np.uint64(2**64-1)))
tryit("py big int 2**200", lambda: C.canonical_json_bytes(2**200))
tryit("py 10**5000", lambda: C.canonical_json_bytes(10**5000))
tryit("np bool_", lambda: C.canonical_json_bytes([np.bool_(True), np.bool_(False)]))
# timedelta64 is subclass of np.signedinteger
print("issubclass timedelta64 signedinteger:", issubclass(np.timedelta64, np.signedinteger))
tryit("td64 5s", lambda: C.canonical_json_bytes(np.timedelta64(5, "s")))
tryit("td64 5ms", lambda: C.canonical_json_bytes(np.timedelta64(5, "ms")))
tryit("td64 5D", lambda: C.canonical_json_bytes(np.timedelta64(5, "D")))
tryit("td64 NaT", lambda: C.canonical_json_bytes(np.timedelta64("NaT")))
tryit("dt64", lambda: C.canonical_json_bytes(np.datetime64("2020-01-01")))
tryit("np.str_", lambda: C.canonical_json_bytes(np.str_("abc")))
tryit("np.bytes_", lambda: C.canonical_json_bytes(np.bytes_(b"abc")))
tryit("0-d array", lambda: C.canonical_json_bytes(np.array(5)))
tryit("np complex", lambda: C.canonical_json_bytes(np.complex128(1)))
from decimal import Decimal
from fractions import Fraction
tryit("Decimal", lambda: C.canonical_json_bytes(Decimal("1.5")))
tryit("Fraction", lambda: C.canonical_json_bytes(Fraction(1,2)))
try:
    import pandas as pd
    tryit("pd.NA", lambda: C.canonical_json_bytes(pd.NA))
    tryit("pd.NaT", lambda: C.canonical_json_bytes(pd.NaT))
    tryit("pd.Timestamp", lambda: C.canonical_json_bytes(pd.Timestamp("2020-01-01")))
except ImportError:
    print("no pandas")
# NaN nested & in identity
tryit("nested nan", lambda: C.canonical_json_bytes({"a": [{"b": (1, float("nan"))}]}))
tryit("nan identity", lambda: C.ordered_registry_digest([{"id": float("nan")}], ["id"]))
tryit("np nan identity rowset", lambda: C.semantic_row_set_sha256([{"id": np.float32("nan")}], ["id"]))
# surrogates
tryit("lone surrogate", lambda: C.canonical_json_bytes("\ud800"))
tryit("lone surrogate key", lambda: C.canonical_json_bytes({"\udc00": 1}))
# cycles
l = []; l.append(l)
tryit("cyclic list", lambda: C.canonical_json_bytes(l))
d = {}; d["x"] = d
tryit("cyclic dict", lambda: C.canonical_json_bytes(d))
# lone CR / mixed
print("CR CRLF mix:", C.canonical_json_bytes("a\r\r\nb"), C.canonical_json_bytes("a\n\nb"))
print("text CR CRLF mix eq:", C.semantic_sha256(b"a\r\r\nb") == C.semantic_sha256(b"a\n\nb"))
# collisions in identity via CRLF
tryit("registry id CRLF collision", lambda: C.ordered_registry_digest([{"id": "a\r\nb"}, {"id": "a\nb"}], ["id"]))
tryit("rowset id CR collision across shards", lambda: C.semantic_row_set_sha256([{"id": "a\rb"}] + [{"id": "a\nb"}], ["id"]))
tryit("registry -0.0 vs 0.0 id", lambda: C.ordered_registry_digest([{"id": -0.0}, {"id": 0.0}], ["id"]))
tryit("registry True vs 1 id", lambda: C.ordered_registry_digest([{"id": True}, {"id": 1}], ["id"]))
tryit("registry tuple vs list id", lambda: C.ordered_registry_digest([{"id": (1,2)}, {"id": [1,2]}], ["id"]))
# identity key normalized mismatch
tryit("idkey a\n vs row key a\r\n", lambda: C.ordered_registry_digest([{"a\r\n": 1}], ["a\n"]))
print("idkey CR vs LF header collision:",
      C.ordered_registry_digest([{"a\r": 1}], ["a\r"]) == C.ordered_registry_digest([{"a\n": 1}], ["a\n"]))
# identity key order
r = [{"a": 1, "b": 2}, {"a": 2, "b": 1}]
print("idkeys order sensitive (registry):", C.ordered_registry_digest(r, ["a","b"]) != C.ordered_registry_digest(r, ["b","a"]))
print("idkeys order sensitive (rowset):", C.semantic_row_set_sha256(r, ["a","b"]) != C.semantic_row_set_sha256(r, ["b","a"]))
# nested vs string
print("nested list vs string distinct:", C.semantic_sha256(["a"]) != C.semantic_sha256('["a"]'))
print("identity tuple ambiguity:", C.ordered_registry_digest([{"a": "x,y", "b": "z"}], ["a","b"]) != C.ordered_registry_digest([{"a": "x", "b": "y,z"}], ["a","b"]))
# row content containing framing-like bytes
fr = (8).to_bytes(8, "big").decode("latin-1")
tryit("row with framing bytes", lambda: C.ordered_registry_digest([{"id": "x" + fr + "y"}], ["id"]))
# semantic str vs bytes text
print("str vs bytes text semantic differ:", C.semantic_sha256("abc") != C.semantic_sha256(b"abc"))
# two BOMs
print("two BOMs stripped only one:", C.semantic_sha256(b"\xef\xbb\xbf\xef\xbb\xbfa") != C.semantic_sha256(b"a"))
# rows as dict / str
tryit("rows=dict", lambda: C.ordered_registry_digest({"id": 1}, ["id"]))
tryit("rows=str", lambda: C.ordered_registry_digest("abc", ["id"]))
tryit("identity_keys generator", lambda: C.ordered_registry_digest([{"id":1}], (k for k in ["id"])))
