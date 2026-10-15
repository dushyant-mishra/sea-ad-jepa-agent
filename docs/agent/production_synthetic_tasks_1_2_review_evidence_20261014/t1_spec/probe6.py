import sys, random
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import numpy as np
import scripts.production_synthetic.canonical_v1 as C
print("all:", C.__all__)
def t(l, f):
    try: print(l, "OK", f())
    except C.CanonicalError as e: print(l, "CE", str(e)[:70])
    except Exception as e: print(l, "OTHER", type(e).__name__, e)
lf = b"id\tv\nA\t1\n"; crlf = lf.replace(b"\n", b"\r\n"); cr = lf.replace(b"\n", b"\r")
print("text eol eq:", C.semantic_text_sha256(lf) == C.semantic_text_sha256(crlf) == C.semantic_text_sha256(cr), len({C.raw_sha256(x) for x in (lf, crlf, cr)}) == 3)
t("semantic_sha256(bytes)", lambda: C.semantic_sha256(b"abc"))
t("semantic_sha256(bytearray)", lambda: C.semantic_sha256(bytearray(b"abc")))
print("json file equiv:", C.semantic_json_file_sha256(b'{"b":1,"a":[1.0]}') == C.semantic_json_file_sha256(b'\xef\xbb\xbf{ "a" : [1.0],\r\n "b" : 1 }\r\n') == C.semantic_sha256({"a": [1.0], "b": 1}))
print("text vs json domains differ:", C.semantic_text_sha256(b'"abc"') != C.semantic_sha256("abc") != C.semantic_json_file_sha256(b'"abc"') or True, C.semantic_text_sha256(b'"abc"') != C.semantic_json_file_sha256(b'"abc"'))
rows = [{"id": f"X{i}", "k": i, "v": i * 0.5} for i in range(300)]
d0 = C.ordered_registry_digest(rows, ["id", "k"]); ds = set()
for i in range(299):
    s = list(rows); s[i], s[i+1] = s[i+1], s[i]; ds.add(C.ordered_registry_digest(s, ["id", "k"]))
print("registry adjacent swaps distinct:", len(ds) == 299 and d0 not in ds, "rev differs:", C.ordered_registry_digest(rows[::-1], ["id","k"]) != d0)
print("idkey order irrelevant:", C.ordered_registry_digest(rows, ["k", "id"]) == d0, C.semantic_row_set_sha256(rows, ["k","id"]) == C.semantic_row_set_sha256(rows, ["id","k"]))
ref = C.semantic_row_set_sha256(rows, ["id"]); sh = list(rows); random.Random(5).shuffle(sh)
shards = [rows[:50], rows[50:220], rows[220:]]
print("rowset invariant:", C.semantic_row_set_sha256(sh, ["id"]) == ref, all(C.semantic_row_set_sha256([r for j in o for r in shards[j]], ["id"]) == ref for o in [(2,0,1),(1,2,0)]))
t("dup across shards", lambda: C.semantic_row_set_sha256(rows[150:] + rows[:151], ["id"]))
t("rows=None", lambda: C.ordered_registry_digest(None, ["id"]))
t("rows=5", lambda: C.semantic_row_set_sha256(5, ["id"]))
t("idkeys collide after norm", lambda: C.ordered_registry_digest([{"a\n": 1}], ["a\r", "a\n"]))
t("composite id ambiguity", lambda: C.ordered_registry_digest([{"a": 1, "b": 2}, {"a": 2, "b": 1}], ["b", "a"]))
t("longdouble", lambda: C.canonical_json_bytes(np.longdouble(0.1)))
print("longdouble itemsize:", np.dtype(np.longdouble).itemsize)
t("float16/32/64", lambda: [C.canonical_json_bytes(t(0.1)) for t in (np.float16, np.float32, np.float64)])
t("loader underflow", lambda: C.load_canonical_json(b"1e-400"))
t("10**5000", lambda: C.canonical_json_bytes(10**5000))
t("nan", lambda: C.semantic_sha256({"a": [np.float32("nan")]}))
print("REG41238", C.ordered_registry_digest([{"address_index": i, "address_id": f"ADDR{i:05d}"} for i in range(41238)], ["address_index", "address_id"]))
