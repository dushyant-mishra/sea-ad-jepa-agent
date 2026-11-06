"""Independent review probe: #463 encoder (blob 8c05ea3a) vs accepted Unified Task 1 encoder (5f9a5249).

Usage: python -I probe.py <enc_dir> <out_json>
<enc_dir> holds canon_old.py and canon_new.py (exact `git show` copies). Synthetic values only.
"""
import importlib.util
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ENC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])


def load(name):
    spec = importlib.util.spec_from_file_location(name, ENC / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


OLD, NEW = load("canon_old"), load("canon_new")


def outcome(mod, value):
    try:
        return ["bytes", mod.canonical_bytes(value).decode("utf-8")]
    except mod.CanonicalError:
        return ["refused", None]
    except BaseException as exc:  # noqa: BLE001 - the point is to see what escapes
        return ["escaped", type(exc).__name__]


report = {"python": sys.version.split()[0], "numpy": np.__version__, "platform": sys.platform}

# A. Every concrete NumPy scalar class: old vs new outcome on one lawful value.
def all_scalar_classes():
    seen, stack = set(), [np.generic]
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        stack.extend(cls.__subclasses__())
    seen.update(v for v in np.sctypeDict.values() if isinstance(v, type))
    return sorted(seen, key=lambda c: (c.__module__, c.__qualname__, id(c)))


def sample(cls):
    try:
        kind = np.dtype(cls).kind
    except TypeError:
        return None, None
    makers = {"b": lambda: cls(True), "i": lambda: cls(7), "u": lambda: cls(7), "f": lambda: cls(1.5),
              "c": lambda: cls(1 + 2j), "M": lambda: cls(1, "D"), "m": lambda: cls(1, "D"),
              "U": lambda: cls("x"), "S": lambda: cls(b"x")}
    try:
        return kind, makers[kind]()
    except Exception:  # noqa: BLE001
        return kind, None


coverage = []
for cls in all_scalar_classes():
    kind, value = sample(cls)
    if value is None or type(value) is not cls:
        continue
    o, n = outcome(OLD, value), outcome(NEW, value)
    coverage.append({"class": f"{cls.__module__}.{cls.__qualname__}", "name_alias": np.dtype(cls).name,
                     "kind": kind, "itemsize": np.dtype(cls).itemsize, "old": o, "new": n, "same": o == n})
report["numpy_class_coverage"] = coverage
report["numpy_class_asymmetries"] = [c for c in coverage if not c["same"]]

# B. Frozen known answer.
KAT = {"a": 1, "b": [True, None, 1.0]}
report["kat"] = {"old": OLD.canonical_sha256(KAT), "new": NEW.canonical_sha256(KAT),
                 "expected": "8b441603e35b6bb16384a91a82453ad13144a79cc9b5b15750a4dc00d09030e9"}

# C. Seeded differential over lawful values (every accepted NumPy class, ints to 4301 digits).
rng = random.Random(20261027)
NUMPY_LAWFUL = [c for c in all_scalar_classes()
                if outcome(OLD, sample(c)[1] if sample(c)[1] is not None else object())[0] == "bytes"]


def rand_int():
    r = rng.random()
    if r < 0.4:
        return rng.randint(-10**6, 10**6)
    if r < 0.6:
        return rng.choice([-1, 1]) * rng.choice([2**63 - 1, 2**63, 2**64 - 1, 2**64, 10**9, 10**9 - 1, 10**18 + 7])
    digits = rng.choice([1, 9, 10, 18, 19, 27, 100, 640, 641, 4299, 4300, 4301])
    lo = 10 ** (digits - 1) if digits > 1 else 0
    value = rng.randrange(lo, 10 ** digits)
    if rng.random() < 0.3:  # internal zero chunks
        value = 10 ** (digits - 1) + rng.randint(0, 9)
    return value * rng.choice([-1, 1])


def rand_float():
    return rng.choice([rng.uniform(-1e6, 1e6), rng.random() * 1e-310, -0.0, 0.0, 1e308, 5e-324,
                       float(rng.randint(-2**53, 2**53)), rng.gauss(0, 1)])


def rand_str():
    alphabet = ["a", "Z", "\r", "\n", "\r\n", "\t", '"', "\\", "\x00", "\x1f", "é", "中", "\U0001f600", "\b", "\f"]
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))


def rand_numpy():
    cls = rng.choice(NUMPY_LAWFUL)
    kind = np.dtype(cls).kind
    if kind == "b":
        return cls(rng.random() < 0.5)
    if kind in "iu":
        info = np.iinfo(cls)
        return cls(rng.choice([info.min, info.max, 0, rng.randint(int(info.min), int(info.max))]))
    return cls(rng.choice([rng.uniform(-1e4, 1e4), -0.0, 0.1, 65504.0 if cls is np.float16 else 3.4e38]))


def rand_value(depth=0):
    r = rng.random()
    if depth < 3 and r < 0.15:
        return {rand_str(): rand_value(depth + 1) for _ in range(rng.randint(0, 4))}
    if depth < 3 and r < 0.3:
        items = [rand_value(depth + 1) for _ in range(rng.randint(0, 4))]
        return items if rng.random() < 0.5 else tuple(items)
    return rng.choice([None, True, False, rand_int(), rand_float(), rand_str(), rand_numpy()])


_C_INT = {c for c in (getattr(np, "intc", None), getattr(np, "uintc", None)) if c is not None
          and c is not np.int32 and c is not np.uint32}


def _holds_c_int(v):
    if type(v) is dict:
        return any(_holds_c_int(x) for x in v.values())
    if type(v) is list or type(v) is tuple:
        return any(_holds_c_int(x) for x in v)
    return type(v) in _C_INT


diff = {"n": 0, "bytes_equal": 0, "refused_both": 0, "asymmetric": 0, "escaped": 0, "examples": []}
with np.errstate(all="ignore"):
    for _ in range(20000):
        value = {"v": rand_value()}
        o, n = outcome(OLD, value), outcome(NEW, value)
        diff["n"] += 1
        if "escaped" in (o[0], n[0]):
            diff["escaped"] += 1
        if o == n:
            diff["bytes_equal" if o[0] == "bytes" else "refused_both"] += 1
        else:
            diff["asymmetric"] += 1
            if _holds_c_int(value) and o[0] == "bytes" and n[0] == "refused":
                diff["asymmetric_explained_by_intc_uintc"] = diff.get("asymmetric_explained_by_intc_uintc", 0) + 1
            if len(diff["examples"]) < 5:
                diff["examples"].append({"type": type(value["v"]).__name__, "old": o[0], "new": n[0]})
report["differential_seed_20261027"] = diff

# D. Integer domain under PYTHONINTMAXSTRDIGITS, both encoders, in fresh interpreters.
CHILD = r"""
import importlib.util, json, sys
from pathlib import Path
out = {}
for name in ("canon_old", "canon_new"):
    spec = importlib.util.spec_from_file_location(name, Path(sys.argv[1]) / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    row = {}
    for digits in (640, 641, 1000, 4299, 4300, 4301):
        for sign in (1, -1):
            v = sign * (10 ** digits - 1)          # exactly `digits` digits
            try:
                row[f"{sign*digits}"] = mod.canonical_sha256({"n": v})[:12]
            except mod.CanonicalError:
                row[f"{sign*digits}"] = "REFUSED"
    out[name] = row
print(json.dumps(out))
"""
matrix = {}
for setting in (None, "0", "640", "4300"):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONINTMAXSTRDIGITS"}
    if setting is not None:
        env["PYTHONINTMAXSTRDIGITS"] = setting
    res = subprocess.run([sys.executable, "-c", CHILD, str(ENC)], env=env, capture_output=True, text=True, timeout=300)
    matrix[setting or "unset"] = json.loads(res.stdout) if res.returncode == 0 else {"error": res.stderr[-300:]}
report["int_domain_matrix"] = matrix
report["int_domain_new_invariant"] = len({json.dumps(m.get("canon_new"), sort_keys=True) for m in matrix.values()}) == 1
report["int_domain_old_invariant"] = len({json.dumps(m.get("canon_old"), sort_keys=True) for m in matrix.values()}) == 1
report["int_domain_new_equals_old_default"] = matrix["unset"].get("canon_new") == matrix["unset"].get("canon_old")

# E. Hostile catalogue beyond #461 (new encoder): lawful outcomes are refusal or the true bytes.
class _F64Sub(np.float64):
    def __float__(self):
        return 999.0

    def __repr__(self):
        return "999.0"


class _IntSub(int):
    def __str__(self):
        return "999"


class _EscapeMeta(type):
    def __getattribute__(cls, name):
        if name == "__name__":
            raise StopIteration("chosen by the payload")
        return type.__getattribute__(cls, name)


class _Escaper(metaclass=_EscapeMeta):
    pass


class _StrKey(str):
    pass


deep = []
cur = deep
for _ in range(200000):
    nxt = []
    cur.append(nxt)
    cur = nxt
selfref = []
selfref.append(selfref)

hostile = {
    "np_float64_subclass": _F64Sub(1.5),
    "int_subclass": _IntSub(5),
    "zero_d_array": np.array(5),
    "complex128": np.complex128(1 + 2j),
    "datetime64": np.datetime64(1, "D"),
    "timedelta64": np.timedelta64(1, "D"),
    "np_str_": np.str_("x"),
    "np_bytes_": np.bytes_(b"x"),
    "longdouble": np.longdouble(1.5),
    "str_subclass_key": {_StrKey("k"): 1},
    "colliding_eol_keys": {"a\r\n": 1, "a\n": 2},
    "lone_surrogate": "\ud800",
    "self_reference": selfref,
    "deep_nesting_200k": deep,
    "metaclass_name_escape": _Escaper(),
}
cat = {}
for name, value in hostile.items():
    cat[name] = {"old": outcome(OLD, {"v": value})[0:2], "new": outcome(NEW, {"v": value})[0:2]}
t0 = time.perf_counter()
cat["huge_int_10e6_digits"] = {"new": outcome(NEW, 10 ** (10 ** 6))[0], "seconds": round(time.perf_counter() - t0, 3)}
report["hostile_catalogue"] = cat

# F. Does the payload-chosen exception silently truncate a consumer that maps the digest?
rows = [{"i": 1}, {"i": 2}, {"bad": _Escaper()}, {"i": 4}]
try:
    digests = list(map(NEW.canonical_sha256, rows))
    report["map_truncation"] = {"rows": len(rows), "digests": len(digests), "silently_truncated": len(digests) < len(rows)}
except BaseException as exc:  # noqa: BLE001
    report["map_truncation"] = {"raised": type(exc).__name__}

OUT.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("python", "numpy", "kat", "differential_seed_20261027",
                                          "int_domain_new_invariant", "int_domain_old_invariant",
                                          "int_domain_new_equals_old_default", "map_truncation")}, indent=1))
print("numpy asymmetries:", json.dumps(report["numpy_class_asymmetries"], indent=1))
print("hostile:", json.dumps(cat, indent=1))
