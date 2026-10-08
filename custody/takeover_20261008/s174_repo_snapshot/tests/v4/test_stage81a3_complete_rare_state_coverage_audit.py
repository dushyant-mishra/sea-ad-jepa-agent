from __future__ import annotations

import importlib.util
import json
from collections import deque
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/stage81a3_complete_rare_state_coverage_audit.py"
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3_rare_state_coverage_resolution.yaml").read_text())
SPEC = importlib.util.spec_from_file_location("expanded_rscr", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def test_amended_contract_keeps_four_mandatory_and_exact_rarity_thresholds() -> None:
    assert AUDIT.MANDATORY == {
        "CN LAMP5-CXCL14 GABASubclass", "STR RSPO2 GABASubclass", "VipSubclass", "EpendymalSubclass"
    }
    assert AUDIT.KNN_K == 15
    assert CONFIG["fixed"]["target_cell_cap"] == 256
    assert CONFIG["expanded"]["resample_roots"] == [8117201, 8117202, 8117203, 8117204]


def test_diverse_sampling_is_deterministic_unique_and_capped() -> None:
    frame = pd.DataFrame({"source_key": [f"c{i}" for i in range(1000)], "donor_id": [f"d{i % 20}" for i in range(1000)], "matrix_id": [f"m{i % 7}" for i in range(1000)]})
    first = AUDIT.diverse_sample(frame, 256, 8117201)
    second = AUDIT.diverse_sample(frame, 256, 8117201)
    assert first.source_key.tolist() == second.source_key.tolist()
    assert len(first) == 256 and not first.source_key.duplicated().any()
    assert first.donor_id.nunique() == 20


def test_bounded_diverse_sampling_matches_exhaustive_queue_order() -> None:
    frame = pd.DataFrame({
        "source_key": [f"cell-{index}" for index in range(5000)],
        "donor_id": [f"donor-{index % 11}" for index in range(5000)],
        "matrix_id": [f"matrix-{index % 5}" for index in range(5000)],
    })
    donor_queues = {}
    for donor, donor_frame in frame.groupby("donor_id", sort=False):
        matrix_queues = {
            matrix: deque(sorted(
                indices,
                key=lambda index: AUDIT.hash_score(8116991, frame.at[index, "source_key"]),
            ))
            for matrix, indices in donor_frame.groupby("matrix_id").groups.items()
        }
        matrices = sorted(matrix_queues, key=lambda matrix: AUDIT.hash_score(8116991, donor, matrix))
        queue = []
        while any(matrix_queues.values()):
            for matrix in matrices:
                if matrix_queues[matrix]:
                    queue.append(matrix_queues[matrix].popleft())
        donor_queues[str(donor)] = deque(queue)
    donors = sorted(donor_queues, key=lambda donor: AUDIT.hash_score(8116991, donor))
    expected = []
    while len(expected) < 256 and any(donor_queues.values()):
        for donor in donors:
            if donor_queues[donor] and len(expected) < 256:
                expected.append(donor_queues[donor].popleft())
    actual = AUDIT.diverse_sample(frame, 256, 8116991)
    assert actual.index.tolist() == list(range(256))
    assert actual.source_key.tolist() == frame.loc[sorted(expected), "source_key"].tolist()


def test_governance_and_architecture_are_not_reopened() -> None:
    governance = CONFIG["governance"]
    assert governance["pathology_opened"] is False
    assert governance["development_expression_accessed"] is False
    assert governance["sealed_expression_accessed"] is False
    assert governance["intrinsic_optimizer_updates"] == 0
    assert governance["intrinsic_backward_calls"] == 0
    assert governance["context_optimizer_updates"] == 0
    text = SCRIPT.read_text().lower()
    assert "optimizer.step" not in text and ".backward(" not in text
    assert "perceiver" not in text and "graph message" not in text


def test_expanded_classifier_uses_every_discovered_annotation() -> None:
    annotations = [*sorted(AUDIT.MANDATORY), "Additional donor-recurring state"]
    rows = []
    for annotation in annotations:
        for representation in (
            "MOLECULAR_LEDGER_ALL_4096_TOKENS",
            "BALANCED_PCA160",
            "BALANCED_REP160_DIAGNOSTIC",
        ):
            rows.append({
                "annotation": annotation,
                "representation": representation,
                "identifiable": True,
                "same_class_knn_purity": 0.8,
                "donor_heldout_recall": 0.8,
            })
    decisions, proposal, rep_advantage, any_critical = AUDIT.classify_all_targets(
        pd.DataFrame(rows),
        annotations,
    )
    assert decisions.annotation.tolist() == annotations
    assert decisions.decision.eq("ADEQUATELY PRESERVED").all()
    assert proposal.startswith("A.")
    assert rep_advantage == "NONE"
    assert any_critical is False


def test_final_outputs_cover_all_recurring_states_when_present() -> None:
    report_path = ROOT / CONFIG["outputs"]["report"]
    if not report_path.exists() or json.loads(report_path.read_text()).get("stage") != "stage81a3_rscr_expanded":
        return
    report = json.loads(report_path.read_text())
    support = pd.read_csv(ROOT / CONFIG["outputs"]["all_target_support"])
    preservation = pd.read_csv(ROOT / CONFIG["outputs"]["all_preservation"])
    assert len(support) == report["donor_recurring_rare_classes"]
    assert set(AUDIT.MANDATORY).issubset(support.annotation)
    assert preservation.groupby("annotation").representation.nunique().eq(4).all()
    assert preservation.groupby("annotation").paired_target_cell_hash.nunique().eq(1).all()
    assert preservation.groupby("annotation").paired_reference_cell_hash.nunique().eq(1).all()
    assert (preservation.loc[preservation.representation.str.contains("LEDGER"), "ledger_gene_tokens_used"] == 4096).all()
    assert report["molecular_ledger"]["parameter_hash_before"] == report["molecular_ledger"]["parameter_hash_after"]
    assert report["unannotated_rare_molecular_states_exhaustively_tested"] is False
