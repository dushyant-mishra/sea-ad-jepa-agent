from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


hpa = load("scripts/v4/stage81a3_context_human_provenance_adjudication.py", "ucdq_hpa")
ucdq = load("scripts/v4/stage81a3_uniform_context_data_qualification.py", "ucdq_base")
CFG = yaml.safe_load((ROOT / "configs/v4/stage81a3_uniform_context_data_qualification.yaml").read_text(encoding="utf-8"))


def broad_input(provenance: str):
    return {
        "spatial_entity_type": "NUCLEUS",
        "measurement_semantics": "RAW_UMI_COUNT",
        "pairing_class": "SAME_ENTITY_EXACT",
        "physical_geometry": True,
        "frozen4096_supported": 4096,
        "frozen4096_support_fraction": 1.0,
        "source_feature_count": 36601,
        "pathology_blind_provenance": provenance,
        "exact_donors": 1,
        "forced_role": "",
    }


def test_unknown_provenance_fails_broad_core_role():
    role, _ = ucdq.role_for(broad_input("UNKNOWN"), CFG)
    assert role == "QUARANTINED_PENDING_GOVERNANCE"


def test_neurotypical_declared_passes_unchanged_broad_gate():
    role, _ = ucdq.role_for(broad_input("NEUROTYPICAL_DECLARED"), CFG)
    assert role == "CORE_SAME_ENTITY_BROAD_CONTEXT"


def test_contract_thresholds_and_hashes_are_immutable():
    assert CFG["pairing"]["exact_min_fraction_spatial_matched"] == 0.95
    assert CFG["role_gates"]["CORE_SAME_ENTITY_BROAD_CONTEXT"]["min_frozen4096_support_fraction"] == 0.90
    checks = hpa.verify_immutable_inputs(ROOT)
    assert all(item["pass"] for item in checks.values())


def test_original_ucdq_outputs_remain_preserved():
    for relative, expected in hpa.ORIGINAL_OUTPUT_HASHES.items():
        assert hpa.sha256(ROOT / relative) == expected


def test_publication_adjudication_does_not_depend_on_pathology_value():
    addendum, _ = hpa.adjudicate(ROOT)
    assert addendum["pathology_values_used"] is False
    assert "disease=normal" not in addendum["evidence_summary"]
    assert addendum["publication_doi"] == "10.1038/s41586-023-06837-4"


def test_broad_anchor_plus_independent_high_plex_yields_cross_donor_yes():
    _, decision = hpa.adjudicate(ROOT)
    assert decision["CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE"] == "YES"
    assert decision["independent_high_plex_replication"]["exact_donors"] == 2


def test_slidetags_and_merfish_are_distinct_technologies():
    _, decision = hpa.adjudicate(ROOT)
    assert decision["broad_anchor"]["technology"] == "Slide-tags"
    assert decision["independent_high_plex_replication"]["technology"] == "MERFISH"


def test_cross_technology_identifiability_is_yes():
    _, decision = hpa.adjudicate(ROOT)
    assert decision["CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE"] == "YES"


def test_fang_mtg_remains_excluded():
    _, decision = hpa.adjudicate(ROOT)
    assert decision["excluded_from_core_decision"] == {
        "fang_mtg_experiments": 5,
        "reason": "SURGICAL_TISSUE_PROVENANCE_REVIEW",
    }


def test_no_context_benefit_or_experiment_claim():
    _, decision = hpa.adjudicate(ROOT)
    assert decision["context_benefit_demonstrated"] is False
    assert decision["experiment_run"] is False
    assert decision["context_model_training_started"] is False
