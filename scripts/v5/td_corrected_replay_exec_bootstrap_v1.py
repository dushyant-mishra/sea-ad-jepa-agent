#!/usr/bin/env python3
"""Run one frozen TD executor from its exact bytes with only its /mnt/data inputs redirected.

--kind td56    The TD56 primaries are top-level scripts. Their numpy file I/O under /mnt/data is mapped to --mnt.
               Any other path is refused. The code object is compiled from the verified bytes.
--kind module  TD57B, TD57C and TD59 define main(). The module is loaded from the verified bytes. Only ARRAY_ROOT,
               SUPPORT_PATH, META_PATHS and the input-SHA constants (ARRAY_SHA256, META_SHA256, SUPPORT_SHA256) are
               pointed at the adapter-built inputs, whose SHAs are passed in. Then main() runs with the given args.
Nothing else in the executor is touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("td56", "module"), required=True)
    ap.add_argument("--executor", required=True)
    ap.add_argument("--executor-sha256", required=True)
    ap.add_argument("--mnt", required=True)
    ap.add_argument("--input-sha-json", required=True)
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    raw = Path(a.executor).read_bytes()
    if hashlib.sha256(raw).hexdigest() != a.executor_sha256:
        raise SystemExit(f"STOP: executor bytes are not {a.executor_sha256}")
    mnt = Path(a.mnt).resolve()
    shas = json.loads(a.input_sha_json)

    import numpy as np

    if a.kind == "td56":
        def mapped(path):
            s = os.fspath(path).replace("\\", "/")
            if not s.startswith("/mnt/data/"):
                raise SystemExit(f"STOP: TD56 executor touched a path outside /mnt/data: {s}")
            return str(mnt / s[len("/mnt/data/"):])
        load, savez = np.load, np.savez
        np.load = lambda f, *x, **k: load(mapped(f), *x, **k)
        np.savez = lambda f, *x, **k: savez(mapped(f), *x, **k)
        code = compile(raw, a.executor, "exec")
        exec(code, {"__name__": "__main__", "__file__": a.executor})
        return 0

    import importlib.util
    spec = importlib.util.spec_from_loader("td_frozen_executor", loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = a.executor
    sys.modules["td_frozen_executor"] = module
    exec(compile(raw, a.executor, "exec"), module.__dict__)
    support_rel = shas["support_rel"]
    module.ARRAY_ROOT = mnt / "td_matrix_npz" / "arrays"
    module.SUPPORT_PATH = mnt / support_rel
    module.META_PATHS = {s: mnt / f"td50_{s}.npz" for s in module.META_PATHS}
    module.ARRAY_SHA256 = {n: shas[f"td_matrix_npz/arrays/{n}"] for n in module.ARRAY_SHA256}
    module.META_SHA256 = {s: shas[f"td50_{s}.npz"] for s in module.META_SHA256}
    module.SUPPORT_SHA256 = shas[support_rel]
    sys.argv = [a.executor] + [x for x in a.rest if x != "--"]
    result = module.main()
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
