"""Hostile tests: compact public E2G receipt cannot become training authority."""
import csv
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("e2g_result_check",
 ROOT/"scripts/regulatory/validate_e2g_seven_track_result_receipt_v1.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STAGE=ROOT/"results/v4/stage81a1b_existing_regulatory_evidence_integration.csv"
RESULTS=ROOT/"results/regulatory"
COUNTS=RESULTS/"e2g_public_7track_27gene_prediction_counts_v1_20261027.csv"
DISTAL=RESULTS/"e2g_public_7track_27gene_distal_counts_v1_20261027.csv"
RECEIPT=RESULTS/"e2g_public_7track_provisional_result_receipt_v1_20261027.json"

def test_actual_results_are_frozen_and_non_deciding():
    assert m.check(STAGE,COUNTS,DISTAL,RECEIPT)["result"].startswith("PASS_")

def test_cannot_overclaim_causality(tmp_path):
    path=tmp_path/"receipt.json"
    record=json.loads(RECEIPT.read_text())
    record["hard_prohibitions"]["causality"]=True
    path.write_text(json.dumps(record))
    with pytest.raises(m.AuditError):
        m.check(STAGE,COUNTS,DISTAL,path)

def test_cannot_promote_symbol_to_ensembl(tmp_path):
    path=tmp_path/"receipt.json"
    record=json.loads(RECEIPT.read_text())
    record["results"]["canonical_ensembl_identity_verified"]=True
    path.write_text(json.dumps(record))
    with pytest.raises(m.AuditError):
        m.check(STAGE,COUNTS,DISTAL,path)

def test_cannot_make_distal_exceed_all(tmp_path):
    path=tmp_path/"distal.csv"
    lines=DISTAL.read_text().splitlines()
    parts=lines[1].split(",")
    parts[1]="999"
    lines[1]=",".join(parts)
    path.write_text("\n".join(lines)+"\n")
    with pytest.raises(m.AuditError):
        m.check(STAGE,COUNTS,path,RECEIPT)

def test_cannot_substitute_source_hash(tmp_path):
    path=tmp_path/"receipt.json"
    record=json.loads(RECEIPT.read_text())
    record["source_results"][0]["source_sha256"]="NOT_A_HASH"
    path.write_text(json.dumps(record))
    with pytest.raises(m.AuditError):
        m.check(STAGE,COUNTS,DISTAL,path)
