from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/run_full104_rare_tail_molecular_prequalification_v1_20260922.py"
AUTHORITY = (
    ROOT
    / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample/"
    / "RARE_TAIL_MOLECULAR_AUTHORITY_V1.json"
)


def _module():
    spec = importlib.util.spec_from_file_location("rare_tail_molecular_runner", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_molecular_authority_round_trips() -> None:
    m = _module()
    a = m.load_authority(AUTHORITY)
    payload = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    assert payload["authority_sha256"] == a.canonical_digest()
    assert payload["authority_sha256"] == (
        "0b5629ca5e7087b1535e006021ec35d24a981986d5096eb4c99f001294c4c000"
    )
    assert a.molecular_execution_authorized is True
    assert a.teacher_tail_evaluation_authorized is False
    assert a.training_authorized is False


def test_materialize_panel_binds_selection_donor_source_operator_and_log1p10k(
    tmp_path: Path,
) -> None:
    m = _module()
    level4 = tmp_path / "level4"
    level4.mkdir()

    # Two selected rows, 1536 requested addresses, full ledger width.
    raw = sp.csr_matrix(
        (
            np.array([2, 4, 3], dtype=np.int64),
            (
                np.array([0, 0, 1]),
                np.array([0, 512, 1024]),
            ),
        ),
        shape=(2, m.N_LEDGER),
    )
    counts = level4 / "counts.npz"
    sp.save_npz(counts, raw)

    meta = level4 / "meta.csv"
    with meta.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=m.META_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerow(
            {
                "selection_row": 11,
                "canonical_cell_id": "c11",
                "donor_id": "D0",
                "expression_row": 0,
                "primary_row_weight": 1,
                "source_library": 20,
            }
        )
        w.writerow(
            {
                "selection_row": 22,
                "canonical_cell_id": "c22",
                "donor_id": "D1",
                "expression_row": 1,
                "primary_row_weight": 1,
                "source_library": "1e1",
            }
        )

    manifest_rows = [
        {
            "block_key": "b0",
            "source": "HVS",
            "operator_index": "0",
            "matrix_id": "m0",
            "rows": "2",
            "nnz": str(raw.nnz),
            "counts_path": counts.name,
            "counts_sha256": _sha(counts),
            "meta_path": meta.name,
            "meta_sha256": _sha(meta),
        }
    ]
    views = {
        "Z": np.arange(0, 512, dtype=np.int64),
        "X": np.arange(512, 1024, dtype=np.int64),
        "Y": np.arange(1024, 1536, dtype=np.int64),
    }
    out = m.materialize_panel(
        level4_root=level4,
        manifest_rows=manifest_rows,
        selected_rows=np.array([11, 22], dtype=np.int64),
        donor_code=np.array([0, 1], dtype=np.int64),
        donor_id_to_code={"D0": 0, "D1": 1},
        donor_source_code=np.array([0, 0], dtype=np.int64),
        genes_by_view=views,
    )
    values = out["values"]
    assert values.shape == (2, 1536)
    assert values[0, 0] == np.float32(np.log1p(2 * 10000 / 20))
    assert values[0, 512] == np.float32(np.log1p(4 * 10000 / 20))
    assert values[1, 1024] == np.float32(np.log1p(3 * 10000 / 10))
    assert out["operator_code"].tolist() == [0, 0]
    assert out["detected_count"].tolist() == [2, 1]


def test_materialize_panel_rejects_sample_donor_identity_drift(tmp_path: Path) -> None:
    m = _module()
    level4 = tmp_path / "level4"
    level4.mkdir()
    raw = sp.csr_matrix((1, m.N_LEDGER), dtype=np.int64)
    counts = level4 / "counts.npz"
    sp.save_npz(counts, raw)
    meta = level4 / "meta.csv"
    with meta.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=m.META_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerow(
            {
                "selection_row": 7,
                "canonical_cell_id": "c7",
                "donor_id": "D0",
                "expression_row": 0,
                "primary_row_weight": 1,
                "source_library": 1,
            }
        )
    manifest_rows = [
        {
            "block_key": "b0",
            "source": "HVS",
            "operator_index": "0",
            "matrix_id": "m0",
            "rows": "1",
            "nnz": "0",
            "counts_path": counts.name,
            "counts_sha256": _sha(counts),
            "meta_path": meta.name,
            "meta_sha256": _sha(meta),
        }
    ]
    views = {
        "Z": np.arange(0, 512),
        "X": np.arange(512, 1024),
        "Y": np.arange(1024, 1536),
    }
    try:
        m.materialize_panel(
            level4_root=level4,
            manifest_rows=manifest_rows,
            selected_rows=np.array([7]),
            donor_code=np.array([1]),  # authenticated metadata says donor 0
            donor_id_to_code={"D0": 0, "D1": 1},
            donor_source_code=np.array([0, 0]),
            genes_by_view=views,
        )
    except ValueError as exc:
        assert "donor_code disagrees" in str(exc)
    else:
        raise AssertionError("donor identity drift must fail closed")
