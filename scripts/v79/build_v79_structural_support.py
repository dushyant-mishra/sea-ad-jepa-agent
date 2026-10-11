#!/usr/bin/env python3
"""Structural measurement support for the compact-cache genes, at operator (= Stage81A2R matrix) x gene resolution.

MEASURED_SCALAR != STRUCTURALLY_UNMEASURED. The compact analysis cache stores counts only, so an entry whose matrix
does not measure the gene's molecular address looks like a measured zero. This builder joins:

  cache operator index --(S174 shard operator bridge)--> matrix_id
  (matrix_id, molecular_address_index) --(Stage81A2R matrix-level measurement support)--> measured_address

and writes a hash-bound boolean array measured_op_gene[operator row, cache gene]. It fails closed when:
- an input hash differs from its pin;
- an operator is bridged to more than one matrix;
- any (matrix, address) pair is absent from the authority (absence never defaults to measured);
- the measured flag contradicts the measurement status;
- any nonzero count sits on an unmeasured entry (the authority and the cache disagree).

That last custody check reads the stored values of unmeasured entries once, here, only to prove they are zero.
The replay itself never reads them.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA = "V79_G500_STRUCTURAL_SUPPORT_V1"
AUTHORITY_COMMIT = "95d2cafe5cde68773f81c4aa64afc5788ae1d73b"
AUTHORITY_REL = "results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz"
BRIDGE_REL = "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
PINS = {
    "cache": "2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62",      # G500 compact cache
    "bridge": "b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92",     # S174 shard operator bridge
    "authority": "ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa",  # Stage81A2R support @95d2cafe
}
UNMEASURED_STATUS = "structurally_unmeasured"


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def array_sha256(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def operator_matrix_map(rows) -> dict[int, str]:
    out: dict[int, set] = {}
    for r in rows:
        out.setdefault(int(r["operator_index"]), set()).add(str(r["matrix_id"]))
    bad = {k: sorted(v) for k, v in out.items() if len(v) != 1}
    if bad:
        raise SystemExit(f"STOP: operator bridged to several matrices: {bad}")
    return {k: next(iter(v)) for k, v in out.items()}


def read_support_authority(path, matrices: set, addresses: set) -> dict[tuple[str, int], bool]:
    """(matrix_id, address) -> measured, for the requested matrices and addresses only."""
    out: dict[tuple[str, int], bool] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            mid = row["matrix_id"]
            if mid not in matrices:
                continue
            addr = int(row["molecular_address_index"])
            if addr not in addresses:
                continue
            flag = row["measured_address"]
            if flag not in ("True", "False"):
                raise SystemExit(f"STOP: measured_address is not a boolean for {(mid, addr)}: {flag!r}")
            measured = flag == "True"
            if measured == (row["measurement_status"] == UNMEASURED_STATUS):
                raise SystemExit(f"STOP: measured flag contradicts measurement status for {(mid, addr)}")
            if (mid, addr) in out and out[(mid, addr)] != measured:
                raise SystemExit(f"STOP: conflicting support rows for {(mid, addr)}")
            out[(mid, addr)] = measured
    return out


def support_matrix(operator_levels: np.ndarray, addresses: np.ndarray, op_to_matrix: dict[int, str],
                   authority: dict[tuple[str, int], bool]) -> np.ndarray:
    m = np.zeros((len(operator_levels), len(addresses)), dtype=bool)
    missing = []
    for i, op in enumerate(operator_levels.tolist()):
        if op not in op_to_matrix:
            raise SystemExit(f"STOP: cache operator {op} has no bridge row")
        mid = op_to_matrix[op]
        for g, addr in enumerate(addresses.tolist()):
            key = (mid, int(addr))
            if key not in authority:
                missing.append(key)
                continue
            m[i, g] = authority[key]
    if missing:
        raise SystemExit(f"STOP: {len(missing)} (matrix, address) pairs absent from the support authority, "
                         f"e.g. {missing[:3]}; absence never defaults to measured")
    return m


def cell_mask(op: np.ndarray, operator_levels: np.ndarray, measured_op_gene: np.ndarray) -> np.ndarray:
    """cells x genes measured mask; operators matched by value."""
    rows = np.searchsorted(operator_levels, op)
    if np.any(rows >= len(operator_levels)) or np.any(operator_levels[np.minimum(rows, len(operator_levels) - 1)] != op):
        raise SystemExit("STOP: a cache operator is missing from the support operator levels")
    return measured_op_gene[rows]


def support_summary(measured_op_gene: np.ndarray, operator_levels: np.ndarray, op: np.ndarray,
                    src: np.ndarray, source_levels=None) -> dict:
    cm = cell_mask(op, operator_levels, measured_op_gene)
    n_cells, n_genes = cm.shape
    srcs = np.unique(src)
    full = np.zeros(n_genes, dtype=bool)
    partial = np.zeros(n_genes, dtype=bool)
    by_source = {}
    for s in srcs:
        sm = cm[src == s]
        fs = ~sm.any(0)
        ps = sm.any(0) & ~sm.all(0)
        full |= fs
        partial |= ps
        name = source_levels[int(s)] if source_levels is not None else str(int(s))
        by_source[name] = {"genes_fully_unmeasured": int(fs.sum()), "genes_partially_unmeasured": int(ps.sum()),
                           "unmeasured_entries": int((~sm).sum())}
    return {"n_cells": int(n_cells), "n_genes": int(n_genes), "entries": int(cm.size),
            "entries_unmeasured": int((~cm).sum()), "fraction_unmeasured": float((~cm).mean()),
            "genes_any_unmeasured": int((~cm).any(0).sum()), "genes_fully_unmeasured_in_a_source": int(full.sum()),
            "genes_partially_unmeasured_within_a_source": int(partial.sum()), "by_source": by_source}


def write_support(out_npz, measured_op_gene: np.ndarray, operator_levels: np.ndarray, gene_address_index: np.ndarray,
                  cache_npz_sha256: str, provenance: dict) -> Path:
    """Write the support array and its record; the record binds the exact cache bytes it describes."""
    out_npz = Path(out_npz)
    measured_op_gene = np.asarray(measured_op_gene, dtype=bool)
    operator_levels = np.asarray(operator_levels, dtype=np.int64)
    gene_address_index = np.asarray(gene_address_index, dtype=np.int64)
    if measured_op_gene.shape != (len(operator_levels), len(gene_address_index)):
        raise SystemExit("STOP: support array shape disagrees with operator levels / genes")
    if len(np.unique(operator_levels)) != len(operator_levels):
        raise SystemExit("STOP: duplicate operator levels in support")
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_npz, measured_op_gene=measured_op_gene, operator_levels=operator_levels,
             gene_address_index=gene_address_index)
    rec = dict(schema=SCHEMA, npz=out_npz.name, npz_sha256=sha256(out_npz), cache_npz_sha256=cache_npz_sha256,
               measured_op_gene_sha256=array_sha256(measured_op_gene),
               operator_levels=operator_levels.tolist(), **provenance)
    rec_path = out_npz.with_suffix(".json")
    rec_path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return rec_path


def build(cache_npz, cache_receipt, bridge_json, authority_csv_gz, out_npz, pins: dict = PINS,
          dev_reference_op_x_gene_sha256: str | None = None) -> Path:
    import run_v79_s174_structure_replay as R

    cache_npz, bridge_json, authority_csv_gz = Path(cache_npz), Path(bridge_json), Path(authority_csv_gz)
    got = {"cache": sha256(cache_npz), "bridge": sha256(bridge_json), "authority": sha256(authority_csv_gz)}
    for k, v in got.items():
        if v != pins[k]:
            raise SystemExit(f"STOP: {k} sha256 {v} != pinned {pins[k]}")
    data = R.load_compact_cache(cache_npz, cache_receipt)
    rows = json.loads(bridge_json.read_text(encoding="utf-8"))["rows"]
    op_to_matrix = operator_matrix_map(rows)
    operator_levels = np.unique(data["op"]).astype(np.int64)
    addresses = np.asarray(data["gene_address_index"], dtype=np.int64)
    authority = read_support_authority(authority_csv_gz, {op_to_matrix[int(o)] for o in operator_levels if int(o) in op_to_matrix},
                                       set(addresses.tolist()))
    m = support_matrix(operator_levels, addresses, op_to_matrix, authority)
    cm = cell_mask(data["op"], operator_levels, m)
    nonzero_unmeasured = int((data["counts_selected"][~cm] != 0).sum())   # custody check (the only read of these)
    if nonzero_unmeasured:
        raise SystemExit(f"STOP: {nonzero_unmeasured} nonzero counts on structurally unmeasured entries")
    receipt = json.loads(Path(cache_receipt).read_text(encoding="utf-8"))
    summary = support_summary(m, operator_levels, data["op"], data["src"], receipt.get("source_levels"))
    provenance = {
        "authority": {"path": AUTHORITY_REL, "commit": AUTHORITY_COMMIT, "sha256": got["authority"],
                      "columns_read": ["matrix_id", "molecular_address_index", "measured_address", "measurement_status"]},
        "bridge": {"path": BRIDGE_REL, "sha256": got["bridge"]},
        "cache_receipt_sha256": sha256(cache_receipt),
        "matrix_of_operator": {str(int(o)): op_to_matrix[int(o)] for o in operator_levels},
        "mask_rule": ("cell i, gene g is MEASURED iff measured_address(matrix_id(operator_i), address_g) is True in the "
                      "Stage81A2R matrix-level support authority; otherwise STRUCTURALLY_UNMEASURED and outside every "
                      "likelihood, metric and permutation test. Resolution: operator (= matrix) x gene."),
        "nonzero_counts_on_unmeasured_entries": nonzero_unmeasured,
        **summary,
    }
    if dev_reference_op_x_gene_sha256 is not None:
        provenance["reproduces_development_mask"] = {
            "reference": "V79_G500_STRUCTURAL_SUPPORT_DEV.json op_x_gene_sha256 (struct_mask.py; used by the masked "
                         "planting calibration V2)",
            "reference_sha256": dev_reference_op_x_gene_sha256,
            "match": array_sha256(m) == dev_reference_op_x_gene_sha256}
        if not provenance["reproduces_development_mask"]["match"]:
            raise SystemExit("STOP: committed builder does not reproduce the development support mask")
    return write_support(out_npz, m, operator_levels, addresses, got["cache"], provenance)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cache")
    ap.add_argument("receipt")
    ap.add_argument("bridge")
    ap.add_argument("authority")
    ap.add_argument("out_npz")
    ap.add_argument("--dev-reference-op-x-gene-sha256", default=None)
    a = ap.parse_args()
    rec = build(a.cache, a.receipt, a.bridge, a.authority, a.out_npz,
                dev_reference_op_x_gene_sha256=a.dev_reference_op_x_gene_sha256)
    print(rec.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
