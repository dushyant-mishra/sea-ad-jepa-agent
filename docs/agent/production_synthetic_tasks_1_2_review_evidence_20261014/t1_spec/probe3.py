import sys, json, random
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import numpy as np
import scripts.production_synthetic.canonical_v1 as C
def t(label, f):
    try: print(f"{label}: OK -> {f()!r}")
    except C.CanonicalError as e: print(f"{label}: CanonicalError {e}")
    except Exception as e: print(f"{label}: OTHER {type(e).__name__}: {e}")
L = C.load_canonical_json
S = lambda b: C.semantic_sha256(L(b))
# (b) loader
t("dup in nested array of objects", lambda: L(b'{"x":[{"a":1},{"b":1,"b":2}]}'))
t("dup via escape", lambda: L(b'{"a":1,"\u0061":2}'))
t("dup after CRLF norm (loader)", lambda: L(b'{"a\r\n":1,"a\n":2}'))
t("dup after CRLF norm (semantic)", lambda: S(b'{"a\r\n":1,"a\n":2}'))
t("-0 int", lambda: L(b'[-0, 0]'))
t("-0 vs 0 semantic equal", lambda: S(b'-0') == S(b'0'))
t("-0.0", lambda: L(b'-0.0'))
t("1e999", lambda: L(b'1e999')); t("-1e999", lambda: L(b'-1E999'))
t("1e-400 underflow", lambda: L(b'1e-400'))
t("1e-400 semantic == 0.0", lambda: S(b'1e-400') == S(b'0.0'))
t("2.5e-324 underflow", lambda: L(b'2.4e-324'))
t("precision loss", lambda: L(b'0.10000000000000000001'))
t("lone surrogate escape loader", lambda: L(b'"\ud800"'))
t("lone surrogate escape semantic", lambda: S(b'"\ud800"'))
t("surrogate pair escape", lambda: L(b'"\ud83d\ude00"'))
t("raw control char", lambda: L(b'"a\x01b"'))
t("two BOMs", lambda: L(b'\xef\xbb\xbf\xef\xbb\xbf1'))
t("utf16 BOM", lambda: L(b'\xff\xfe1\x00'))
t("leading zeros", lambda: L(b'01'))
t("deep nesting", lambda: L(b'[' * 100000 + b']' * 100000))
t("bytearray", lambda: L(bytearray(b'1')))
t("whitespace only", lambda: L(b'  \r\n '))
t("big int 4300 digits", lambda: len(str(L(b'1' + b'0' * 4299))))
t("big int 4301 digits", lambda: L(b'1' + b'0' * 4300))
# (a) identity key normalization
rows = [{"a\r": i, "a\n": i} for i in range(2)]
t("row with colliding keys registry", lambda: C.ordered_registry_digest(rows, ["a\n"]))
t("row with colliding keys rowset", lambda: C.semantic_row_set_sha256(rows, ["a\n"]))
t("row non-str key", lambda: C.ordered_registry_digest([{"id": 1, 2: 3}], ["id"]))
base = [{"id": f"X{i}", "v": i} for i in range(300)]
d0 = C.ordered_registry_digest(base, ["id"]); ds = set()
for i in range(299):
    s = list(base); s[i], s[i+1] = s[i+1], s[i]; ds.add(C.ordered_registry_digest(s, ["id"]))
print("adjacent swaps distinct:", len(ds) == 299 and d0 not in ds)
sh = list(base); random.Random(3).shuffle(sh)
print("rowset shuffle invariant:", C.semantic_row_set_sha256(sh, ["id"]) == C.semantic_row_set_sha256(base, ["id"]))
t("dup across shards", lambda: C.semantic_row_set_sha256(base[150:] + base[:151], ["id"]))
t("CRLF id collision", lambda: C.ordered_registry_digest([{"id": "a\r\nb"}, {"id": "a\nb"}], ["id"]))
print("REG41238", C.ordered_registry_digest([{"address_index": i, "address_id": f"ADDR{i:05d}"} for i in range(41238)], ["address_index", "address_id"]))
# prior probes
t("10**5000", lambda: C.canonical_json_bytes(10**5000))
t("td64", lambda: C.canonical_json_bytes(np.timedelta64(5, "ms")))
t("nested nan", lambda: C.canonical_json_bytes({"a": [(1, np.float32("nan"))]}))
print("float rt:", all(float(C.canonical_json_bytes(x)) == x for x in [0.1+0.2, 1e-320, 5e-324, 1e308, 2.0**53+2]))
