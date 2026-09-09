import csv
import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "bind_full104_expression_blocks_v4.py"
spec = importlib.util.spec_from_file_location("full104_bind_v4", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sh(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fixture(tmp_path):
    root = tmp_path / "expr"
    (root / "blocks/op00").mkdir(parents=True)
    db = tmp_path / "meta.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "create table cells(source text,matrix_id text,operator_index integer,"
        "local_row integer,donor_id text,partition text,cell_id text,stable_key integer)"
    )
    con.execute(
        "insert into cells values(?,?,?,?,?,?,?,?)",
        ("HVS", "HVS::x", 0, 0, "d0", "reader_fit", "c0", 1),
    )
    con.commit()
    con.close()

    cp = root / "blocks/op00/block-00000.counts.npz"
    cp.write_bytes(b"counts")
    mp = root / "blocks/op00/block-00000.meta.csv"
    with mp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.META_COLUMNS)
        w.writeheader()
        w.writerow({
            "selection_row": 0,
            "canonical_cell_id": "c0",
            "donor_id": "d0",
            "expression_row": 0,
            "primary_row_weight": 1.0,
            "source_library": 1,
        })
    bm = tmp_path / "manifest.csv"
    with bm.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.MANIFEST_COLUMNS)
        w.writeheader()
        w.writerow({
            "block_key": "op00/block-00000",
            "source": "HVS",
            "operator_index": 0,
            "matrix_id": "HVS::x",
            "rows": 1,
            "nnz": 1,
            "counts_path": "blocks/op00/block-00000.counts.npz",
            "counts_sha256": sh(cp),
            "meta_path": "blocks/op00/block-00000.meta.csv",
            "meta_sha256": sh(mp),
        })
    contract = {
        "schema": "full104-phase2-expression-materialization-v1",
        "status": "PASS_PHASE2_EXPRESSION_MATERIALIZED",
        "cells": 1,
        "donors": 1,
        "operators": 1,
        "addresses": 8,
        "sample_level": 4,
        "block_rows": 512,
        "selection_sha256": "sel",
        "selection_manifest_sha256": "selm",
        "normalization_deferred": "raw integer counts plus full-source library; downstream applies log1p(raw*10000/library) exactly once",
        "identity_is_audit_metadata_not_model_input": True,
        "original_mixed_nph_denied": True,
        "no_validation_oracle_dev_sealed_pathology": True,
        "no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": True,
    }
    c = tmp_path / "contract.json"
    c.write_text(json.dumps(contract))
    audit = {
        "schema": "full104-phase2-expression-materialization-v1",
        "status": "PASS_PHASE2_EXPRESSION_MATERIALIZED",
        "cells": 1,
        "operators": 1,
        "addresses": 8,
        "sample_level": 4,
        "blocks": 1,
        "nnz": 1,
        "block_manifest_sha256": sh(bm),
        "original_mixed_nph_opened": False,
        "protected_expression_opened": False,
        "reader_validation_oracle_dev_sealed_pathology_opened": False,
        "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": False,
    }
    a = tmp_path / "audit.json"
    a.write_text(json.dumps(audit))
    return root, db, bm, c, a


def invoke(root, db, bm, c, a, tmp_path, **overrides):
    kwargs = dict(
        block_manifest=bm,
        materialization_contract=c,
        materialization_audit=a,
        block_root=root,
        metadata_sqlite=db,
        expected_metadata_sha256=sh(db),
        scratch_dir=tmp_path,
        _expected_block_manifest_sha256=sh(bm),
        _expected_contract_sha256=sh(c),
        _expected_audit_sha256=sh(a),
        _expected_cells=1,
        _expected_donors=1,
        _expected_operators=1,
        _expected_matrices=1,
        _expected_blocks=1,
        _expected_addresses=8,
        _expected_sources=("HVS",),
        _expected_selection_sha256="sel",
        _expected_selection_manifest_sha256="selm",
    )
    kwargs.update(overrides)
    return m.bind_full104_blocks(**kwargs)


def rewrite_manifest_and_audit(bm, a, rows):
    with bm.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.MANIFEST_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    audit = json.loads(a.read_text())
    audit["block_manifest_sha256"] = sh(bm)
    audit["nnz"] = sum(int(r["nnz"]) for r in rows)
    a.write_text(json.dumps(audit))


def test_cross_ledger_identity_closure(tmp_path):
    root, db, bm, c, a = fixture(tmp_path)
    out = invoke(root, db, bm, c, a, tmp_path)
    assert out["cross_ledger_identity_mismatches"] == 0
    assert out["test_fixture_mode"] is True
    assert out["synthetic_data_used"] is True


def test_wrong_block_cell_fails(tmp_path):
    root, db, bm, c, a = fixture(tmp_path)
    mp = root / "blocks/op00/block-00000.meta.csv"
    with mp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.META_COLUMNS)
        w.writeheader()
        w.writerow({
            "selection_row": 0,
            "canonical_cell_id": "wrong",
            "donor_id": "d0",
            "expression_row": 0,
            "primary_row_weight": 1.0,
            "source_library": 1,
        })
    rows = list(csv.DictReader(bm.open()))
    rows[0]["meta_sha256"] = sh(mp)
    rewrite_manifest_and_audit(bm, a, rows)
    try:
        invoke(root, db, bm, c, a, tmp_path)
    except RuntimeError as e:
        assert "CROSS_LEDGER_IDENTITY_MISMATCH" in str(e)
    else:
        raise AssertionError("wrong cell must fail")


def test_zero_library_fails(tmp_path):
    root, db, bm, c, a = fixture(tmp_path)
    mp = root / "blocks/op00/block-00000.meta.csv"
    with mp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.META_COLUMNS)
        w.writeheader()
        w.writerow({
            "selection_row": 0,
            "canonical_cell_id": "c0",
            "donor_id": "d0",
            "expression_row": 0,
            "primary_row_weight": 1.0,
            "source_library": 0,
        })
    rows = list(csv.DictReader(bm.open()))
    rows[0]["meta_sha256"] = sh(mp)
    rewrite_manifest_and_audit(bm, a, rows)
    try:
        invoke(root, db, bm, c, a, tmp_path)
    except RuntimeError as e:
        assert "META_VALUE_SEMANTICS" in str(e)
    else:
        raise AssertionError("zero source library must fail")


def test_manifest_source_identity_fails(tmp_path):
    root, db, bm, c, a = fixture(tmp_path)
    rows = list(csv.DictReader(bm.open()))
    rows[0]["source"] = "SEA_AD"
    rewrite_manifest_and_audit(bm, a, rows)
    try:
        invoke(root, db, bm, c, a, tmp_path, _expected_sources=("SEA_AD",))
    except RuntimeError as e:
        assert "CROSS_LEDGER_IDENTITY_MISMATCH" in str(e)
    else:
        raise AssertionError("source identity mismatch must fail")


def test_duplicate_selection_row_fails(tmp_path):
    root = tmp_path / "expr"
    (root / "blocks/op00").mkdir(parents=True)
    db = tmp_path / "meta.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "create table cells(source text,matrix_id text,operator_index integer,"
        "local_row integer,donor_id text,partition text,cell_id text,stable_key integer)"
    )
    con.executemany(
        "insert into cells values(?,?,?,?,?,?,?,?)",
        [
            ("HVS", "HVS::x", 0, 0, "d0", "reader_fit", "c0", 1),
            ("HVS", "HVS::x", 0, 1, "d0", "reader_fit", "c1", 2),
        ],
    )
    con.commit()
    con.close()
    cp = root / "blocks/op00/block-00000.counts.npz"
    cp.write_bytes(b"counts")
    mp = root / "blocks/op00/block-00000.meta.csv"
    with mp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.META_COLUMNS)
        w.writeheader()
        for cell, expr in (("c0", 0), ("c1", 1)):
            w.writerow({
                "selection_row": 0,
                "canonical_cell_id": cell,
                "donor_id": "d0",
                "expression_row": expr,
                "primary_row_weight": 1.0,
                "source_library": 1,
            })
    bm = tmp_path / "manifest.csv"
    with bm.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=m.MANIFEST_COLUMNS)
        w.writeheader()
        w.writerow({
            "block_key": "op00/block-00000",
            "source": "HVS",
            "operator_index": 0,
            "matrix_id": "HVS::x",
            "rows": 2,
            "nnz": 1,
            "counts_path": "blocks/op00/block-00000.counts.npz",
            "counts_sha256": sh(cp),
            "meta_path": "blocks/op00/block-00000.meta.csv",
            "meta_sha256": sh(mp),
        })
    contract = {
        "schema": "full104-phase2-expression-materialization-v1",
        "status": "PASS_PHASE2_EXPRESSION_MATERIALIZED",
        "cells": 2,
        "donors": 1,
        "operators": 1,
        "addresses": 8,
        "sample_level": 4,
        "block_rows": 512,
        "selection_sha256": "sel",
        "selection_manifest_sha256": "selm",
        "normalization_deferred": "raw integer counts plus full-source library; downstream applies log1p(raw*10000/library) exactly once",
        "identity_is_audit_metadata_not_model_input": True,
        "original_mixed_nph_denied": True,
        "no_validation_oracle_dev_sealed_pathology": True,
        "no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": True,
    }
    audit = {
        "schema": "full104-phase2-expression-materialization-v1",
        "status": "PASS_PHASE2_EXPRESSION_MATERIALIZED",
        "cells": 2,
        "operators": 1,
        "addresses": 8,
        "sample_level": 4,
        "blocks": 1,
        "nnz": 1,
        "block_manifest_sha256": sh(bm),
        "original_mixed_nph_opened": False,
        "protected_expression_opened": False,
        "reader_validation_oracle_dev_sealed_pathology_opened": False,
        "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": False,
    }
    c = tmp_path / "contract.json"
    c.write_text(json.dumps(contract))
    a = tmp_path / "audit.json"
    a.write_text(json.dumps(audit))
    try:
        invoke(root, db, bm, c, a, tmp_path, _expected_cells=2)
    except RuntimeError as e:
        assert "DUPLICATE_SELECTION_OR_CANONICAL_CELL_ID" in str(e)
    else:
        raise AssertionError("duplicate selection row must fail")
