"""Differential: PS canonical_v1 at base vs head on seeded lawful payloads. Synthetic values only.

usage: python -I diff_probe.py <base_canonical.py> <head_canonical.py>
"""
import importlib.util
import json
import random
import sys
import warnings

import numpy as np


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BASE, HEAD = load("ps_base", sys.argv[1]), load("ps_head", sys.argv[2])

seen, stack = set(), [np.generic]
while stack:
    c = stack.pop()
    if c not in seen:
        seen.add(c)
        stack.extend(c.__subclasses__())
classes = []
for c in seen:
    if c.__module__ != "numpy":
        continue
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            d = np.dtype(c)
        except TypeError:
            continue
    if d.type is c:
        classes.append(c)
classes.sort(key=lambda c: c.__name__)

rng = random.Random(20261027)


def scalar():
    r = rng.random()
    if r < 0.35:
        c = rng.choice(classes)
        k = np.dtype(c).kind
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if k == "b":
                    return c(rng.random() < 0.5)
                if k in "iu":
                    return c(rng.randint(0, 100))
                if k in "fc":
                    return c(rng.choice([0.0, -0.0, 1.5, 0.1, 1e300, 2.5e-7]))
                if k in "mM":
                    return c(rng.randint(0, 10), "D")
                if k in "US":
                    return c("ab")
                return c()
            except Exception:  # noqa: BLE001
                return None
    if r < 0.55:
        return rng.randint(-10**30, 10**30)
    if r < 0.7:
        return rng.choice([0.0, -0.0, 1.5, 0.1, 3.14159, 1e-300])
    if r < 0.85:
        return "".join(rng.choice("ab\r\né中\"\\") for _ in range(rng.randint(0, 6)))
    return rng.choice([None, True, False])


def payload(depth=0):
    r = rng.random()
    if depth > 3 or r < 0.4:
        return scalar()
    if r < 0.7:
        return [payload(depth + 1) for _ in range(rng.randint(0, 4))]
    if r < 0.8:
        return tuple(payload(depth + 1) for _ in range(rng.randint(0, 3)))
    return {"k" + str(i): payload(depth + 1) for i in range(rng.randint(0, 4))}


def outcome(mod, obj):
    try:
        return ("bytes", mod.canonical_json_bytes(obj))
    except mod.CanonicalError:
        return ("refused", None)
    except BaseException as exc:  # noqa: BLE001
        return ("escaped", type(exc).__name__)


tally = {"n": 0, "bytes_equal": 0, "refused_both": 0, "asymmetric": 0, "escaped": 0}
asym_classes = {}


def classes_in(obj):
    if isinstance(obj, dict):
        return set().union(*[classes_in(v) for v in obj.values()]) if obj else set()
    if isinstance(obj, (list, tuple)):
        return set().union(*[classes_in(v) for v in obj]) if obj else set()
    return {type(obj).__name__} if isinstance(obj, np.generic) else set()


for _ in range(20000):
    p = payload()
    a, b = outcome(BASE, p), outcome(HEAD, p)
    tally["n"] += 1
    if "escaped" in (a[0], b[0]):
        tally["escaped"] += 1
    elif a == b:
        tally["bytes_equal" if a[0] == "bytes" else "refused_both"] += 1
    else:
        tally["asymmetric"] += 1
        key = ",".join(sorted(classes_in(p))) or "no-numpy"
        asym_classes[key] = asym_classes.get(key, 0) + 1
explained = sum(v for k, v in asym_classes.items() if "intc" in k.split(",") or "uintc" in k.split(","))
print(json.dumps({"numpy": np.__version__, "platform": sys.platform, "tally": tally,
                  "asymmetric_explained_by_intc_uintc": explained}, sort_keys=True))
