import sys, json, random
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import numpy as np
import scripts.production_synthetic.canonical_v1 as C

rng = random.Random(12345)
def rand_obj(d=0):
    t = rng.randrange(8 if d < 4 else 5)
    if t == 0: return None
    if t == 1: return rng.choice([True, False])
    if t == 2: return rng.randrange(-10**20, 10**20)
    if t == 3: return rng.uniform(-1e10, 1e10) * rng.choice([1, 1e-300, 1e290])
    if t == 4: return "".join(rng.choice("ab\"\\n\t\x01\u00e9\u2028\U0001F600") for _ in range(rng.randrange(6)))
    if t == 5: return [rand_obj(d+1) for _ in range(rng.randrange(4))]
    if t == 6: return tuple(rand_obj(d+1) for _ in range(rng.randrange(3)))
    return {("k%d" % rng.randrange(50)) + rng.choice(["", "\u00e9", "Z", "a"]): rand_obj(d+1) for _ in range(rng.randrange(5))}

def norm(o):
    if isinstance(o, tuple): return [norm(x) for x in o]
    if isinstance(o, list): return [norm(x) for x in o]
    if isinstance(o, dict): return {k: norm(v) for k, v in o.items()}
    return o

objs = [rand_obj() for _ in range(3000)]
bad = 0
for o in objs:
    b = C.canonical_json_bytes(o)
    back = json.loads(b)
    if C.canonical_json_bytes(back) != b: bad += 1
    if json.dumps(norm(o), sort_keys=True) != json.dumps(back, sort_keys=True):
        # compare float equality structurally
        bad += 1
print("roundtrip mismatches:", bad)

# key-permutation fuzz
def shuffle_keys(o):
    if isinstance(o, dict):
        items = list(o.items()); rng.shuffle(items)
        return {k: shuffle_keys(v) for k, v in items}
    if isinstance(o, (list, tuple)): return type(o)(shuffle_keys(x) for x in o)
    return o
pm = sum(C.semantic_sha256(o) != C.semantic_sha256(shuffle_keys(o)) for o in objs)
print("key-perm mismatches:", pm)

# digests for hash-seed comparison
rows = [{"address_index": i, "address_id": f"ADDR{i:05d}", "s": {f"f{j}": j * 0.1 for j in range(5)}} for i in range(41238)]
print("REG", C.ordered_registry_digest(rows, ["address_index", "address_id"]))
sh = list(rows); random.Random(7).shuffle(sh)
print("SET", C.semantic_row_set_sha256(rows, ["address_id"]), C.semantic_row_set_sha256(sh, ["address_id"]) == C.semantic_row_set_sha256(rows, ["address_id"]))
print("SEM", C.semantic_sha256({str(k): {"x": k} for k in range(2000)}))
# shards with duplicate split across shards
s1 = rows[:100]; s2 = rows[99:200]
try:
    C.semantic_row_set_sha256(s2 + s1, ["address_id"]); print("dup across shards NOT rejected")
except C.CanonicalError as e: print("dup across shards rejected:", e)
# registry order sensitivity: every adjacent swap in a 200 row registry distinct
base = C.ordered_registry_digest(rows[:200], ["address_id"])
ds = set()
for i in range(199):
    s = list(rows[:200]); s[i], s[i+1] = s[i+1], s[i]
    ds.add(C.ordered_registry_digest(s, ["address_id"]))
print("adjacent swaps distinct:", len(ds) == 199 and base not in ds)
# registry: n_rows framing - two registries where concatenation differs
a = C.ordered_registry_digest([{"id": "a", "v": "b"}], ["id"])
print("registry len", len(a))
