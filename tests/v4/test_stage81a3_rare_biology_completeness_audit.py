from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/stage81a3_rare_biology_completeness_audit.py"
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3_rare_state_coverage_resolution.yaml").read_text())
SPEC = importlib.util.spec_from_file_location("rare_completeness", SCRIPT); AUDIT = importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(AUDIT)


def test_predeclared_discovery_contract_is_fixed() -> None:
    contract = CONFIG["rare_biology_completeness"]
    assert contract["local_isolation_k"] == 30
    assert contract["candidate_fraction"] == 0.01
    assert contract["neighborhood_overlap_fraction"] == 0.50
    assert contract["family_cell_cap"] >= 667
    assert contract["resample_roots"] == [8117301, 8117302, 8117303, 8117304]
    assert contract["donor_fractions"] == [0.25, 0.50, 0.75, 1.00]


def test_local_isolation_and_candidate_count_are_deterministic() -> None:
    similarity = np.eye(100); similarity += 0.25 * (np.ones((100, 100)) - np.eye(100)); similarity[0, 1:] = similarity[1:, 0] = -0.5
    isolation, neighbors = AUDIT.local_isolation(similarity, 30); mask = AUDIT.candidate_mask(isolation, 0.01)
    assert neighbors.shape == (100, 30); assert mask.sum() == 1; assert mask[0]


def test_representation_agreement_categories_are_exact() -> None:
    assert AUDIT.agreement_label(True, True, True) == "RNA + LEDGER + PCA RARE"
    assert AUDIT.agreement_label(True, True, False) == "RNA + LEDGER RARE / PCA NOT RARE"
    assert AUDIT.agreement_label(True, False, False) == "RNA RARE / LEDGER NOT RARE"
    assert AUDIT.agreement_label(False, True, False) == "LEDGER RARE / RNA NOT RARE"
    assert AUDIT.agreement_label(False, False, True) == "PCA RARE ONLY"


def test_recurring_neighborhood_stability_uses_exactly_four_roots() -> None:
    size = 160
    frame = pd.DataFrame({
        "source_key": [f"cell-{index}" for index in range(size)],
        "donor_id": [f"donor-{index % 20}" for index in range(size)],
        "matrix_id": [f"matrix-{index % 4}" for index in range(size)],
    })
    coordinates = np.linspace(0.0, 1.0, size)
    similarity = 1.0 - np.abs(coordinates[:, None] - coordinates[None, :])
    similarities = {name: similarity.copy() for name in ("RNA", "LEDGER", "PCA")}
    isolation = {name: AUDIT.local_isolation(value, 30)[0] for name, value in similarities.items()}
    definitions = [{
        "rare_neighborhood_id": "family::001",
        "broad_family": "family",
        "candidate_indices": [0, 1],
        "member_indices": list(range(40)),
        "donors": 20,
    }]
    rows = AUDIT.family_resample_stability(
        frame,
        similarities,
        isolation,
        definitions,
        CONFIG["rare_biology_completeness"],
    )
    assert [row["resample_root"] for row in rows] == [8117301, 8117302, 8117303, 8117304]
    assert all(0.0 <= row["candidate_membership_jaccard"] <= 1.0 for row in rows)


def test_new_stability_output_is_registered() -> None:
    assert CONFIG["rare_biology_outputs"]["resample_stability"].endswith(".csv")
    assert 'summary = {"broad_family": family' in SCRIPT.read_text()


def test_class_c_encoder_loss_requires_stability_and_low_technical_concern() -> None:
    frame = pd.DataFrame({
        "rna_rare": [True, True, True, False],
        "ledger_rare": [False, False, False, False],
        "donor_recurrence_retained_all": [True, False, True, True],
        "technical_concern": [
            "LOW TECHNICAL CONCERN",
            "LOW TECHNICAL CONCERN",
            "MIXED TECHNICAL ASSOCIATION",
            "LOW TECHNICAL CONCERN",
        ],
    })
    assert AUDIT.supported_encoder_loss_mask(frame).tolist() == [True, False, False, False]


def test_completeness_stage_owns_final_combined_freeze_readiness() -> None:
    text = SCRIPT.read_text()
    assert '"data_defined_recurring_conclusions_stable"' in text
    assert 'config["outputs"]["freeze_readiness"]' in text


def test_governance_forbids_training_and_pathology() -> None:
    text = SCRIPT.read_text().lower()
    assert "optimizer.step" not in text and ".backward(" not in text
    assert "plaque" not in text and "braak" not in text and "tau" not in text
    assert CONFIG["governance"]["pathology_opened"] is False
    assert CONFIG["governance"]["development_expression_accessed"] is False
    assert CONFIG["governance"]["sealed_expression_accessed"] is False
