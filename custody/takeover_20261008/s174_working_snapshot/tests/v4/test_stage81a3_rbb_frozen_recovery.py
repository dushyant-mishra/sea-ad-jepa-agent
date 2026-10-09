from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_frozen_recovery as recovery  # noqa: E402


SOURCE = Path(recovery.__file__).read_text(encoding="utf-8")


def test_exact_seed_and_update_contract():
    assert recovery.base.SEED == 8114001 and recovery.base.UPDATES == 150


def test_exact_microbatch_and_effective_batch():
    assert recovery.frozen.MICROBATCH == 64 and recovery.base.EFFECTIVE_BATCH == 256


def test_reuses_frozen_training_function():
    assert "frozen.train_belief_only" in inspect.getsource(recovery.main)


def test_milestone_callback_persists_incrementally():
    source = inspect.getsource(recovery.main)
    assert "persist_milestone" in source and 'base.atomic_json(OUTPUTS["json"]' in source


def test_checkpoint_precedes_primary_evaluation():
    source = inspect.getsource(recovery.main)
    assert source.index("checkpoint_belief(") < source.index("primary_mask_evaluation(")


def test_checkpoint_excludes_frozen_ledger():
    source = inspect.getsource(recovery.checkpoint_belief)
    assert 'not name.startswith("ledger.")' in source
    assert '"contains_frozen_molecular_weights": False' in source


def test_checkpoint_records_required_provenance():
    source = inspect.getsource(recovery.checkpoint_belief)
    for term in ("basis_sha256", "tokenizer_sha256", "molecular_encoder_sha256", "mask_bank_sha256", "prior_sha256", "noise_sha256", "updates"):
        assert term in source


def test_primary_families_persist_separately():
    source = inspect.getsource(recovery.primary_mask_evaluation)
    assert 'status"] = f"primary_{family.lower()}_persisted"' in source
    assert 'base.atomic_json(OUTPUTS["json"], payload)' in source


def test_counterfactual_runs_after_primary_serialization():
    source = inspect.getsource(recovery.main)
    assert source.index('"all_primary_evidence_persisted"') < source.index("frozen.evaluate_counterfactual")


def test_counterfactual_failure_cannot_erase_primary():
    source = inspect.getsource(recovery.main)
    assert "failed_without_primary_evidence_loss" in source and "except Exception as exc" in source


def test_dtype_fix_is_present():
    source = inspect.getsource(recovery.frozen.evaluate_counterfactual)
    assert "unit.to(counterfactual[2].dtype)" in source


def test_all_correlated_amplitudes_are_persisted():
    source = inspect.getsource(recovery.primary_mask_evaluation)
    assert "range(R_MAX)" in source and "amplitude_{rank:02d}" in source


def test_replicate_factor_consistency_is_persisted():
    source = inspect.getsource(recovery.primary_mask_evaluation)
    assert "prediction_correlation" in source and "b_factor_r2_under_a_map" in source


def test_no_real_rna_or_pathology_surface():
    lower = SOURCE.lower()
    assert "anndata" not in lower and "h5ad" not in lower and "amyloid" not in lower


def test_no_scientific_sweep_or_new_loss():
    training = inspect.getsource(recovery.frozen.train_belief_only)
    assert "base.rbb_nll" in training and "scheduler" not in training and "preservation" not in training


def test_checkpoint_tensor_hash_is_deterministic():
    value = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    assert recovery.tensor_hash(value) == recovery.tensor_hash(value.clone())
