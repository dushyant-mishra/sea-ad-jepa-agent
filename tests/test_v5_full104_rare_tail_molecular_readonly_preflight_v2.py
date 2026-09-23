"""Outcome-blind regression for physical structural binding and pair-hash guard."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_rare_tail_molecular_primitives_v1 import (
    verify_pair_address_hash,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample"
SCRIPT = ROOT / "scripts/agent/preflight_full104_rare_tail_molecular_readonly_v2_20260922.py"
STRUCTURAL = SAMPLE / "RARE_TAIL_STRUCTURAL_PREFLIGHT_V1.json"
PROVENANCE = SAMPLE / "RARE_TAIL_STRUCTURAL_PREFLIGHT_PROVENANCE.json"
CONTRACT = SAMPLE / "RARE_TAIL_MOLECULAR_EXECUTION_CONTRACT_V1.json"
OLD_PREFLIGHT = SAMPLE / "RARE_TAIL_MOLECULAR_READONLY_PREFLIGHT_V1.json"


def module():
    spec = importlib.util.spec_from_file_location("structural_pinned_preflight_v2", SCRIPT)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def verified_structure(m, *, result=STRUCTURAL, provenance=PROVENANCE):
    return m.authenticate_structural_evidence(
        structural_receipt_path=result,
        structural_provenance_path=provenance,
        sample_dir=SAMPLE,
        expected_canonical_sha256="f0d71c9b2f25d31a0b277b9a55f2a31f44d9084b924c3c14c67ef0c4c4a4bc89",
    )


def test_original_physical_structural_receipt_is_bound_by_bytes_and_validator():
    m = module()
    out = verified_structure(m)
    assert out["structural_validation_status"] == (
        "PASS_FULL104_RARE_TAIL_STRUCTURAL_PREFLIGHT_RECEIPT_V1"
    )
    assert out["structural_receipt_file_sha256"] == m.STRUCTURAL_RECEIPT_FILE_SHA256
    assert out["structural_provenance_file_sha256"] == m.STRUCTURAL_PROVENANCE_FILE_SHA256


@pytest.mark.parametrize("which", ["receipt", "provenance"])
def test_coherent_forged_sha_and_false_flags_cannot_replace_frozen_files(tmp_path, which):
    m = module()
    orig = STRUCTURAL if which == "receipt" else PROVENANCE
    altered = tmp_path / orig.name
    altered.write_bytes(orig.read_bytes() + b" ")
    with pytest.raises(ValueError, match="physical structural"):
        verified_structure(
            m,
            result=altered if which == "receipt" else STRUCTURAL,
            provenance=altered if which == "provenance" else PROVENANCE,
        )


def test_structural_semantic_validator_is_not_bypassed_by_resealing(tmp_path, monkeypatch):
    m = module()
    bad = copy.deepcopy(json.loads(STRUCTURAL.read_text(encoding="utf-8")))
    bad["operators_present"] = 41
    semantic = {k: v for k, v in bad.items() if k != "structural_preflight_sha256"}
    bad["structural_preflight_sha256"] = m.canonical_digest(semantic)
    path = tmp_path / "resealed.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    sha_real = m.sha256_file
    monkeypatch.setattr(
        m, "sha256_file",
        lambda p: m.STRUCTURAL_RECEIPT_FILE_SHA256 if p == path else sha_real(p),
    )
    # Simulate a hypothetical compromised outer file pin: inner semantic validator still fails.
    with pytest.raises(ValueError, match="structural preflight must retain all 42 operators"):
        verified_structure(m, result=path)


@pytest.mark.parametrize("field", [
    "expression_opened",
    "count_matrices_opened",
    "molecular_rare_tail_gate_executed_after_structural_pass",
])
def test_provenance_flags_still_required_if_file_pin_is_bypassed(tmp_path, monkeypatch, field):
    m = module()
    bad = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    bad[field] = True
    path = tmp_path / "forged-provenance.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    sha_real = m.sha256_file
    monkeypatch.setattr(
        m, "sha256_file",
        lambda p: m.STRUCTURAL_PROVENANCE_FILE_SHA256 if p == path else sha_real(p),
    )
    with pytest.raises(ValueError, match="unsafe or missing flag"):
        verified_structure(m, provenance=path)


def test_v2_creates_a_new_review_only_receipt_without_opening_counts(monkeypatch):
    m = module()
    previous = json.loads(OLD_PREFLIGHT.read_text(encoding="utf-8"))
    monkeypatch.setattr(m, "run_preflight", lambda **kwargs: previous)
    receipt = m.run_preflight_v2(
        authority_path=SAMPLE / "RARE_TAIL_MOLECULAR_AUTHORITY_V1.json",
        execution_contract_path=CONTRACT,
        sample_dir=SAMPLE,
        split_receipt_path=SAMPLE / "outer_split_receipt.json",
        level4_root=ROOT / "NONEXISTENT_MANIFEST_ONLY_ROOT",
        target_eligibility_path=SAMPLE / "target_eligibility.json",
        structural_receipt_path=STRUCTURAL,
        structural_provenance_path=PROVENANCE,
        repo_root=ROOT,
    )
    assert receipt["state"] == "READY_FOR_INDEPENDENT_REVIEW__NO_RNA_OPENED"
    assert receipt["receipt_sha256"] == m.canonical_digest({
        k: v for k, v in receipt.items() if k != "receipt_sha256"
    })
    assert receipt["expression_opened"] is False
    assert receipt["molecular_outcome_opened"] is False
    assert receipt["training_authorized"] is False


def test_direct_pair_address_hash_guard_rejects_mutation_without_mutating_eligibility():
    # This exercises the downstream guard independently of the earlier fixed eligibility SHA.
    fabricated = np.zeros((2048, 2), dtype=np.int64)
    with pytest.raises(ValueError, match="TD59 pair-address hash mismatch"):
        verify_pair_address_hash(fabricated, panel=0, view="X")
