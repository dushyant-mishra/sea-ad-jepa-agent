from __future__ import annotations

import csv
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/run_full104_rare_tail_structural_preflight_v1_20260922.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("rare_tail_structural_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_metadata(path: Path, selection_rows: list[int]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "selection_row",
                "canonical_cell_id",
                "donor_id",
                "expression_row",
                "primary_row_weight",
                "source_library",
            ],
        )
        writer.writeheader()
        for row in selection_rows:
            writer.writerow(
                {
                    "selection_row": row,
                    "canonical_cell_id": f"cell-{row}",
                    "donor_id": f"donor-{row % 4}",
                    "expression_row": row,
                    "primary_row_weight": "1",
                    "source_library": "10",
                }
            )


def _write_level4_fixture(root: Path, *, duplicate_selected_row: bool = False):
    root.mkdir(parents=True)
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    rows = []
    selected = []
    for op in range(42):
        meta = root / f"meta_{op}.csv"
        selection_row = op
        if duplicate_selected_row and op == 41:
            selection_row = 0
        _write_metadata(meta, [selection_row])
        selected.append(selection_row)
        rows.append(
            {
                "block_key": f"block-{op}",
                "source": "HVS" if op < 24 else ("NPH52" if op < 31 else "SEA_AD"),
                "operator_index": str(op),
                "matrix_id": f"matrix-{op}",
                "rows": "1",
                "nnz": "0",
                "counts_path": f"counts_{op}.npz",
                "counts_sha256": "0" * 64,
                "meta_path": meta.name,
                "meta_sha256": _sha(meta),
            }
        )

    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "block_key",
                "source",
                "operator_index",
                "matrix_id",
                "rows",
                "nnz",
                "counts_path",
                "counts_sha256",
                "meta_path",
                "meta_sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return manifest, np.asarray(selected, dtype=np.int64)


def test_operator_derivation_uses_authenticated_metadata_only(tmp_path: Path, monkeypatch) -> None:
    cli = _load_cli_module()
    level4 = tmp_path / "level4"
    manifest, selected = _write_level4_fixture(level4)
    monkeypatch.setattr(cli, "EXPECTED_BLOCK_MANIFEST_SHA256", _sha(manifest))

    operator, blocks = cli._derive_selected_operator_codes(
        level4_root=level4,
        selected_rows=selected,
    )
    assert operator.tolist() == list(range(42))
    assert blocks == {str(i): 1 for i in range(42)}

    source = SCRIPT.read_text(encoding="utf-8")
    assert "np.load(" in source  # qualification identity arrays only
    assert "scipy" not in source
    assert "load_npz" not in source
    assert "X_log1p10k" not in source
    assert "counts_path).open" not in source
    assert "molecular_distance_computed" in source
    assert '"molecular_distance_computed": False' in source


def test_operator_derivation_rejects_selected_row_in_two_blocks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli_module()
    level4 = tmp_path / "level4"
    manifest, selected = _write_level4_fixture(level4, duplicate_selected_row=True)
    monkeypatch.setattr(cli, "EXPECTED_BLOCK_MANIFEST_SHA256", _sha(manifest))

    # Ask for each unique selected row. Row 0 is present in two authenticated blocks.
    unique = np.unique(selected)
    with pytest.raises(SystemExit, match="more than one authenticated block"):
        cli._derive_selected_operator_codes(
            level4_root=level4,
            selected_rows=unique,
        )


def test_operator_derivation_rejects_metadata_hash_drift(tmp_path: Path, monkeypatch) -> None:
    cli = _load_cli_module()
    level4 = tmp_path / "level4"
    manifest, selected = _write_level4_fixture(level4)
    monkeypatch.setattr(cli, "EXPECTED_BLOCK_MANIFEST_SHA256", _sha(manifest))

    meta = level4 / "meta_7.csv"
    meta.write_text(meta.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="metadata block hash mismatch"):
        cli._derive_selected_operator_codes(
            level4_root=level4,
            selected_rows=selected,
        )


def test_cli_refuses_to_overwrite_existing_result(tmp_path: Path, monkeypatch) -> None:
    cli = _load_cli_module()
    out = tmp_path / "result.json"
    out.write_text("sentinel", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            str(SCRIPT),
            "--sample-dir",
            str(tmp_path / "sample"),
            "--level4-root",
            str(tmp_path / "level4"),
            "--out",
            str(out),
        ],
    )
    with pytest.raises(SystemExit, match="refuse overwrite"):
        cli.main()
    assert out.read_text(encoding="utf-8") == "sentinel"
