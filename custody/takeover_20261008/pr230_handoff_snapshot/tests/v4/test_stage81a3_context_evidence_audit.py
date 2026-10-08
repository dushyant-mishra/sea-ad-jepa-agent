from __future__ import annotations

import importlib.util
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/v4/stage81a3_audit_context_evidence.py"
SPEC = importlib.util.spec_from_file_location("stage81a3_context_audit", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_read_h5_series_preserves_categorical_identity(tmp_path: Path) -> None:
    path = tmp_path / "fixture.h5"
    with h5py.File(path, "w") as handle:
        obs = handle.create_group("obs")
        field = obs.create_group("donor")
        field.create_dataset("categories", data=np.asarray([b"D1", b"D2"]))
        field.create_dataset("codes", data=np.asarray([0, 1, -1, 0]))
    with h5py.File(path, "r") as handle:
        assert MODULE.read_h5_series(handle["obs"], "donor").tolist() == ["D1", "D2", "", "D1"]


def test_source_hash_matches_frozen_vocabulary_contract() -> None:
    frame = MODULE.pd.read_csv(ROOT / "results/v4/stage81a2_foundation_vocabulary.csv")
    assert len(frame) == 4096
    assert MODULE.source_hash(frame.canonical_ensembl_gene_id) == MODULE.VOCABULARY_HASH


def test_worktree_classification_keeps_data_and_unrelated_files_out() -> None:
    assert MODULE.classify_worktree("data/external/example.h5ad") == "DATA - do not commit"
    assert MODULE.classify_worktree("docs/stage_c_finetuning_analysis.md") == "UNRELATED - exclude"
    assert "candidate" in MODULE.classify_worktree("scripts/v4/stage81a3_new_audit.py")


def test_supported_regulator_contract_is_complete_and_ordered() -> None:
    assert MODULE.SUPPORTED_REGULATORS == ("ELF1", "SPI1", "STAT1", "BACH1", "CEBPA", "IRF8", "RELA")
