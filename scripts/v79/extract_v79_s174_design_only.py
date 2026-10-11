#!/usr/bin/env python3
"""Extract the value-blind S174 cell design (no expression) from the authenticated G500 compact cache.

V2_CORE qualification worlds use the exact S174 design for Q10/Q11, and the S174 design marginals to build the
crossed base design for the other worlds. Only these arrays are copied: log library (centred), broad class, source,
donor, operator (= Stage81A2R matrix). counts_selected, gene_address_index and prevalence_selected are never read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

CACHE_SHA256 = "2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62"
DESIGN_KEYS = ("log_lib_centered", "cls", "src", "donor", "op")
SCHEMA = "V79_S174_DESIGN_ONLY_V1"


def extract(cache: Path, out_npz: Path) -> dict:
    raw = cache.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != CACHE_SHA256:
        raise SystemExit(f"STOP: cache sha256 {got} != authenticated {CACHE_SHA256}")
    z = np.load(cache, allow_pickle=False)
    arrays = {k: np.asarray(z[k]) for k in DESIGN_KEYS}
    n = len(arrays["cls"])
    if any(len(v) != n for v in arrays.values()):
        raise SystemExit("STOP: design arrays disagree on rows")
    for k in ("cls", "src", "donor", "op"):
        arrays[k] = arrays[k].astype(np.int64)
    arrays["log_lib_centered"] = arrays["log_lib_centered"].astype(np.float64)
    donors = np.unique(arrays["donor"])
    if any(len(np.unique(arrays["src"][arrays["donor"] == d])) != 1 for d in donors):
        raise SystemExit("STOP: a donor spans several sources")
    if any(len(np.unique(arrays["src"][arrays["op"] == m])) != 1 for m in np.unique(arrays["op"])):
        raise SystemExit("STOP: an operator spans several sources")
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_npz, **arrays)
    rec = dict(schema=SCHEMA, source_cache_sha256=CACHE_SHA256, keys=list(DESIGN_KEYS), n_cells=int(n),
               n_donors=int(len(donors)), n_operators=int(len(np.unique(arrays["op"]))),
               donors_per_source=[int(len(np.unique(arrays["donor"][arrays["src"] == s]))) for s in range(3)],
               npz=out_npz.name, npz_sha256=hashlib.sha256(out_npz.read_bytes()).hexdigest(),
               expression_read=False)
    out_npz.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cache", type=Path)
    ap.add_argument("out_npz", type=Path)
    a = ap.parse_args()
    print(json.dumps(extract(a.cache, a.out_npz), indent=1))


if __name__ == "__main__":
    main()
