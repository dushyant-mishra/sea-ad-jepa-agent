import sys, time, json, random, math
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import numpy as np
import scripts.production_synthetic.canonical_v1 as C

# test line 66 chars
src = open("D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic/test_canonical_v1.py", encoding="utf-8").read().splitlines()[65]
print("line66 codepoints:", [hex(ord(c)) for c in src if ord(c) > 127])

# float repr formats
for x in (1e16, 1e-5, 1e22, 123456789012345680.0, 5e-324, 1.5e300, 0.0001, 1e15):
    print(x, C.canonical_json_bytes(x))
# string escaping vs json.dumps
s = "".join(chr(i) for i in range(0, 0x80)) + "\u2028\u00e9\U0001F600"
mine = C.canonical_json_bytes(s)
ref = json.dumps(C._norm_eol(s), ensure_ascii=False).encode()
print("escape matches json.dumps(ensure_ascii=False):", mine == ref)
# key sort: code point vs UTF-16
k1, k2 = "\uffff", "\U00010000"
print("keys order:", C.canonical_json_bytes({k1: 1, k2: 2}).decode("utf-8").encode("unicode_escape"))
# identity_keys order sensitivity on row set
rows = [{"a": i, "b": f"x{i}"} for i in range(5)]
print("rowset idkey-order-sensitive:", C.semantic_row_set_sha256(rows, ["a","b"]) != C.semantic_row_set_sha256(rows, ["b","a"]))
print("registry idkey-order-sensitive:", C.ordered_registry_digest(rows, ["a","b"]) != C.ordered_registry_digest(rows, ["b","a"]))
# non-CanonicalError leaks
for name, fn in [("rows=None", lambda: C.ordered_registry_digest(None, ["a"])),
                 ("rowset rows=5", lambda: C.semantic_row_set_sha256(5, ["a"])),
                 ("cyclic", lambda: (lambda l: (l.append(l), C.canonical_json_bytes(l)))([])),
                 ("deep", lambda: C.canonical_json_bytes(eval("["*3000 + "]"*3000))),
                 ("loader deep", lambda: C.load_canonical_json(b"["*100000 + b"]"*100000)),
                 ]:
    try:
        fn(); print(name, "ACCEPTED")
    except C.CanonicalError as e:
        print(name, "CanonicalError")
    except Exception as e:
        print(name, "LEAK", type(e).__name__, str(e)[:60])
# int/str enum subclasses
import enum
class E(enum.IntEnum):
    A = 1
class S(str, enum.Enum):
    X = "x"
print("IntEnum:", C.canonical_json_bytes(E.A), "StrEnum:", C.canonical_json_bytes(S.X))
# longdouble
ld = np.longdouble(1)/np.longdouble(3)
print("longdouble finfo eps:", np.finfo(np.longdouble).eps, C.canonical_json_bytes(ld))
# np.str_, np.bytes_
print("np.str_", C.canonical_json_bytes(np.str_("a")))
try: C.canonical_json_bytes(np.bytes_(b"a")); print("np.bytes_ accepted")
except C.CanonicalError: print("np.bytes_ rejected")
# roundtrip idempotence property
rng = random.Random(1)
def gen(d=0):
    t = rng.randrange(8 if d < 3 else 5)
    if t == 0: return None
    if t == 1: return rng.choice([True, False])
    if t == 2: return rng.randint(-10**20, 10**20)
    if t == 3:
        return rng.choice([rng.uniform(-1e6,1e6), 10**rng.uniform(-320,308), -0.0, 1e16, 5e-324])
    if t == 4: return "".join(chr(rng.choice([0,9,10,13,34,92,0x7f,0xe9,0x2028,0x1F600, 65])) for _ in range(rng.randrange(6)))
    if t in (5,6): return [gen(d+1) for _ in range(rng.randrange(4))]
    return {"".join(rng.choice("abc\r\n") for _ in range(3)) + str(i): gen(d+1) for i in range(rng.randrange(4))}
bad = 0
for _ in range(20000):
    o = gen()
    try: b = C.canonical_json_bytes(o)
    except C.CanonicalError: continue
    b2 = C.canonical_json_bytes(C.load_canonical_json(b))
    if b != b2: bad += 1
print("roundtrip mismatches:", bad)
