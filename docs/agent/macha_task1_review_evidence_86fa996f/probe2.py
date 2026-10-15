import sys, subprocess, json
sys.path.insert(0, r"D:/jepa_task1_review_86fa996f")
from scripts.v5.td_unified import canonical_v1 as U
# old Task 1 frozen known-answer object and bytes (frozen in ff597faf test file)
old_src = subprocess.check_output(["git","-C",r"D:/Jepa project","show","ff597faf:scripts/production_synthetic/canonical_v1.py"])
ns = {}; exec(compile(old_src, "old_canonical_v1", "exec"), ns)
obj = {"s": "\x00\x1f\t\n\x7f\u00e9\U0001F600", "f": [1e16, 1e-5, 5e-324, 0.1, -0.0, 1.0]}
o = ns["canonical_json_bytes"](obj); u = U.canonical_bytes(obj)
print("old==unified bytes on KAT object:", o == u)
import random
random.seed(20261015); mism = 0
def rnd(d=0):
    t = random.random()
    if d > 3 or t < 0.3: return random.choice([None, True, False, 0, -0.0, 1.0, 3, 2**60, 1e-300, 5e-324, 1e308, 0.1, "a\r\nb", "\u00e9", "\x00", "z"])
    if t < 0.6: return [rnd(d+1) for _ in range(random.randint(0,4))]
    return {random.choice(["a","b","c","\u00e9","k\r"])+str(random.randint(0,3)): rnd(d+1) for _ in range(random.randint(0,4))}
for _ in range(3000):
    x = rnd()
    try: a = ns["canonical_json_bytes"](x)
    except Exception as e: a = ("ERR", type(e).__name__)
    try: b = U.canonical_bytes(x)
    except Exception as e: b = ("ERR", type(e).__name__)
    if (isinstance(a, bytes) or isinstance(b, bytes)) and a != b: mism += 1; ex = (x, a, b)
print("random mismatches old vs unified:", mism)
if mism: print("example:", ex)
