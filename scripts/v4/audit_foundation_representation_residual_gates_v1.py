#!/usr/bin/env python3
"""Build non-authorizing residual Foundation representation receipts from compact evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_residual_gates.py"
_spec = importlib.util.spec_from_file_location("foundation_residual_gates_runtime", MODULE)
_gates = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_gates)
adjudicate_conditional_technology_imprint = _gates.adjudicate_conditional_technology_imprint
adjudicate_heldout_donor_evidence = _gates.adjudicate_heldout_donor_evidence
adjudicate_resource_benchmark = _gates.adjudicate_resource_benchmark
matrix_label_identifiability = _gates.matrix_label_identifiability


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _exclusive_atomic_json(path: Path, obj: dict) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as fh:
            tmp = Path(fh.name); fh.write(data); fh.flush(); os.fsync(fh.fileno())
        os.link(tmp, path)
        tmp.unlink(); tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _exclusive_matrix_csv(path: Path, rows: list[dict]) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("matrix ledger is empty")
    cooked = []
    for row in rows:
        rec = dict(row)
        if isinstance(rec.get("unseen_native_labels"), list):
            rec["unseen_native_labels"] = "|".join(rec["unseen_native_labels"])
        cooked.append(rec)
    with path.open("x", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cooked[0]), lineterminator="\n")
        w.writeheader(); w.writerows(cooked)


def run(sample_freeze, shortcut_atlas, technology_json, resource_json, out_json, matrix_csv):
    paths = {
        "sample_freeze": Path(sample_freeze),
        "shortcut_atlas": Path(shortcut_atlas),
        "technology_diagnostic": Path(technology_json),
        "resource_benchmark": Path(resource_json),
    }
    matrix = matrix_label_identifiability(_read_csv(paths["sample_freeze"]))
    donor = adjudicate_heldout_donor_evidence(_read_csv(paths["shortcut_atlas"]))
    tech = adjudicate_conditional_technology_imprint(json.loads(paths["technology_diagnostic"].read_text(encoding="utf-8")))
    resource = adjudicate_resource_benchmark(json.loads(paths["resource_benchmark"].read_text(encoding="utf-8")))
    broad_states = [x["broad_label_identifiability"] for x in matrix]
    rec = {
        "schema": "FOUNDATION_REPRESENTATION_RESIDUAL_GATES_AUDIT_V1",
        "input_sha256": {k: sha256_file(v) for k, v in paths.items()},
        "heldout_donor_evidence": donor,
        "matrix_identifiability_summary": {
            "matrices": len(matrix),
            "broad_available": broad_states.count("AVAILABLE"),
            "broad_partial": broad_states.count("PARTIAL"),
            "broad_unavailable": broad_states.count("UNAVAILABLE"),
        },
        "conditional_technology_imprint": tech,
        "resource_benchmark": resource,
        "representation_freeze_authorized": False,
        "training_authorized": False,
        "target_discovery_value_read_authorized": False,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "terminal": "RESIDUAL_GATES_AUDITED__REPRESENTATION_FREEZE_BLOCKED__TRAINING_OFF",
    }
    _exclusive_matrix_csv(Path(matrix_csv), matrix)
    _exclusive_atomic_json(Path(out_json), rec)
    return rec


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sample-freeze", required=True)
    p.add_argument("--shortcut-atlas", required=True)
    p.add_argument("--technology-json", required=True)
    p.add_argument("--resource-json", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--matrix-csv", required=True)
    a = p.parse_args(argv)
    run(a.sample_freeze, a.shortcut_atlas, a.technology_json, a.resource_json, a.out_json, a.matrix_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
