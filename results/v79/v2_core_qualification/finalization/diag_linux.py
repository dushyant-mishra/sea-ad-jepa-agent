"""Diagnostic only: rebuild the V2 draft on Linux and list the JSON paths whose values differ from the committed
draft. Reads the repository read-only from /w; writes nothing into it."""
import json
import sys

sys.path.insert(0, "/w/scripts/v79")
from pathlib import Path

import build_v79_v2_core_contract as B
import numpy
import scipy

root = Path("/w")
rebuilt = B.build(root)
committed = json.loads((root / B.CONTRACT_REL).read_text(encoding="utf-8"))
diffs = []


def walk(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]")
    elif a != b:
        diffs.append((path, a, b))


walk(rebuilt, committed, "")
print("python", sys.version.split()[0], "numpy", numpy.__version__, "scipy", scipy.__version__)
print("n_diffs", len(diffs))
for p, a, b in diffs[:40]:
    print(p, "| linux:", repr(a), "| committed:", repr(b))
print("text_identical", (json.dumps(rebuilt, indent=1) + "\n") == (root / B.CONTRACT_REL).read_text(encoding="utf-8"))
