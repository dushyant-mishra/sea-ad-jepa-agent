from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/preflight_full104_rare_tail_molecular_readonly_v1_20260922.py"
AUTHORITY = ROOT / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample/RARE_TAIL_MOLECULAR_AUTHORITY_V1.json"
CONTRACT = ROOT / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample/RARE_TAIL_MOLECULAR_EXECUTION_CONTRACT_V1.json"


def _module():
    spec = importlib.util.spec_from_file_location("rare_tail_readonly_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_preflight_source_contains_no_molecular_materialization_call() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attrs = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "materialize_panel" not in called_names
    assert "evaluate_panel" not in called_names
    assert "load_npz" not in called_attrs


def test_committed_execution_contract_round_trips_through_preflight_loader() -> None:
    m = _module()
    payload, contract = m.load_execution_contract(CONTRACT)
    assert payload["contract_sha256"] == contract.canonical_digest()
    assert contract.molecular_execution_authorized is True
    assert contract.training_authorized is False


def test_readonly_preflight_can_complete_without_count_matrix_access(
    tmp_path: Path, monkeypatch
) -> None:
    m = _module()
    _, contract = m.load_execution_contract(CONTRACT)

    fold = np.asarray([i % 4 for i in range(104)], dtype=np.int64)
    source = np.asarray(([0] * 41) + ([1] * 17) + ([2] * 46), dtype=np.int64)
    sample = {
        "fold_by_donor": fold,
        "donor_source_code": source,
    }
    sample_payload = {"sample_receipt_sha256": contract.sample_receipt_sha256}
    split = {
        "receipt_sha256": contract.outer_split_receipt_sha256,
        "fold_by_donor": fold.tolist(),
        "donor_source_code": source.tolist(),
    }

    monkeypatch.setattr(m, "load_sample", lambda _: (sample_payload, sample))
    monkeypatch.setattr(m, "load_split", lambda _: split)
    monkeypatch.setattr(m, "load_manifest", lambda _: [{"block_key": str(i)} for i in range(8915)])
    monkeypatch.setattr(m, "sha256_file", lambda _: contract.target_eligibility_file_sha256)

    expected_by_suffix = {
        Path(relative).name: getattr(contract, field)
        for field, relative in m.SOURCE_PATHS.items()
    }
    monkeypatch.setattr(
        m,
        "normalized_text_sha256",
        lambda path: expected_by_suffix[path.name],
    )

    monkeypatch.setattr(
        m,
        "PANEL_PAIR_ADDRESS_SHA256",
        {0: {"Z": "h", "X": "h", "Y": "h"}, 1: {"Z": "h", "X": "h", "Y": "h"}},
    )
    monkeypatch.setattr(
        m,
        "select_gene_views",
        lambda common, panel: {"Z": common[:512], "X": common[512:1024], "Y": common[1024:1536]},
    )
    monkeypatch.setattr(
        m,
        "select_pairs",
        lambda genes, panel, view: (np.zeros((2048, 2), dtype=np.int64), np.zeros((2048, 2), dtype=np.int64)),
    )
    monkeypatch.setattr(m, "verify_pair_address_hash", lambda addresses, panel, view: "h")

    eligibility = tmp_path / "eligibility.json"
    eligibility.write_text(
        json.dumps({
            "schema": "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
            "strict_core_cols": list(range(17186)),
        }),
        encoding="utf-8",
    )
    provenance = tmp_path / "structural.json"
    provenance.write_text(
        json.dumps({
            "structural_preflight_sha256": contract.structural_preflight_sha256,
            "expression_opened": False,
            "count_matrices_opened": False,
        }),
        encoding="utf-8",
    )

    receipt = m.run_preflight(
        authority_path=AUTHORITY,
        execution_contract_path=CONTRACT,
        sample_dir=tmp_path,
        split_receipt_path=tmp_path / "split.json",
        level4_root=tmp_path,
        target_eligibility_path=eligibility,
        structural_provenance_path=provenance,
        repo_root=ROOT,
    )
    assert receipt["state"] == "READY_FOR_REVIEW__NO_RNA_OPENED"
    assert receipt["expression_opened"] is False
    assert receipt["count_matrices_opened"] is False
    assert receipt["molecular_outcome_opened"] is False
    assert receipt["training_authorized"] is False
