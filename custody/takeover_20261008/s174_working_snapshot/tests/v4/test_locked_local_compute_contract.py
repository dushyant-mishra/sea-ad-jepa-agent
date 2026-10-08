from __future__ import annotations

from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT / "configs/v4/locked_local_compute_contract.yaml"


def load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_verified_hardware_and_runtime_are_locked() -> None:
    contract = load_contract()
    hardware = contract["captured_hardware"]
    runtime = contract["validated_runtime"]
    assert contract["status"] == "locked"
    assert hardware["physical_cpu_cores"] == 8
    assert hardware["logical_processors"] == 16
    assert hardware["system_ram_bytes"] == 34_115_739_648
    assert hardware["gpu_vram_mib"] == 16_384
    assert hardware["gpu_count"] == 1
    assert hardware["large_data_filesystem"] == "exFAT"
    assert runtime["python"] == "3.11.15"
    assert runtime["pytorch"] == "2.7.0+cu128"
    assert runtime["pytorch_cuda_runtime"] == "12.8"
    assert runtime["cuda_available"] is True
    assert runtime["hardware_preflight_required"] is False
    assert runtime["driver_reported_cuda_alignment_required"] is False


def test_fixed_model_envelope_and_compute_conservation() -> None:
    contract = load_contract()
    envelope = contract["fixed_model_envelope"]
    authority = contract["compute_authority"]
    assert envelope == {
        "architecture": "perceiver_gene_token_to_latent_cross_attention",
        "gene_vocabulary_target": 4096,
        "gene_identities_frozen_once_during_feature_contract": True,
        "gene_identity_dimension": 48,
        "model_width": 160,
        "latent_slots": 24,
        "latent_blocks": 2,
        "attention_heads": 4,
        "cell_latent_dimension": 160,
        "dropout": 0.10,
        "precision": "fp16_mixed",
        "initial_microbatch_size": 8,
        "target_effective_batch_size": 256,
        "production_seed_count": 1,
        "full_gene_to_gene_attention": "forbidden",
        "model_dimension_search": "forbidden",
    }
    assert authority["production_checkpoint_lineages"] == 1
    assert authority["canonical_feature_vocabularies"] == 1
    assert authority["donor_splits"] == 1
    assert authority["production_seeds"] == 1
    assert authority["cloud_compute_authorized"] is False
    assert authority["distributed_training_available"] is False
    assert "disposable_pilot_training" in authority["forbidden"]


def test_memory_fallback_startup_and_data_rules() -> None:
    contract = load_contract()
    assert contract["cuda_oom_fallback"]["ordered_actions"] == [
        "set_microbatch_to_4",
        "set_microbatch_to_2",
        "set_microbatch_to_1",
        "increase_gradient_accumulation_to_preserve_effective_batch",
        "enable_activation_checkpointing",
    ]
    startup = contract["production_startup_window"]
    assert startup["optimizer_steps"] == 300
    assert startup["belongs_to_production_trajectory"] is True
    assert startup["disposable_pilot"] is False
    assert startup["model_reinitialization_at_step_300"] == "forbidden"
    assert startup["pathology_diagnosis_or_downstream_biology_in_gate"] == "forbidden"
    assert contract["data_authority"]["current_stage_training_allowed"] is False
    assert contract["data_authority"]["asset_download_does_not_assign_dataset_role"] is True
    assert set(contract["data_authority"]["requires_later_explicit_approval"]) == {
        "raw_fastq", "bam", "raw_optical_image_stacks"
    }


def test_exfat_rules_and_portability() -> None:
    contract = load_contract()
    safety = contract["exfat_safety"]
    assert safety["download_suffix"] == ".part"
    assert safety["verify_size_before_rename"] is True
    assert safety["verify_sha256_before_rename"] is True
    assert safety["overwrite_existing_different_hash"] == "forbidden"
    assert safety["source_files_immutable"] is True
    assert safety["verify_frozen_artifact_after_write"] is True
    assert safety["tracked_reports_may_contain_machine_absolute_paths"] is False
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert not any(marker in text for marker in ["C:\\", "D:\\", "/mnt/c/", "/mnt/d/", "file://"])
