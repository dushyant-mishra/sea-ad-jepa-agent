from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v3 as D3
import td_relational_successor_gate_v2 as G


def _scale(label: str) -> dict:
    numerator, denominator = map(int, label.split("/"))
    return {
        "scale_label": label,
        "numerator": numerator,
        "denominator": denominator,
        "status": "FAIL",
        "reason": "RELATION_NOT_ESTABLISHED",
        "observed_statistic": 0.5,
        "family_null_p95": 0.6,
        "n_observed_donors": 5,
        "observed_donor_agreements": {f"D{i}": 0.5 for i in range(5)},
        "observed_resolved_relations": {f"D{i}": 20 for i in range(5)},
        "null_source_statistics": [0.5] * 64,
        "n_sampled_triplets": 320,
        "eligible_donors": [f"D{i}" for i in range(5)],
    }


def test_phase2_reader_accepts_scale_grid_after_phase1_sorted_json_serialization():
    profile = {
        "source": "S0",
        "panel_id": "P0",
        "profile_id": "opaque-profile",
        "scale_results": {label: _scale(label) for label in G.SCALE_LABELS},
        "characterization": ["NO_RELATION_ESTABLISHED"],
        "focal_anchor_count": 40,
        "failure_scope": "SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
        "authority": {
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }

    # This is the phase-1 durable writer behavior: json.dumps(..., sort_keys=True).
    on_disk = json.loads(json.dumps(profile, sort_keys=True, separators=(",", ":")))

    assert tuple(on_disk["scale_results"]) == ("1/2", "1/3", "1/4", "1/6", "1/8")
    assert set(on_disk["scale_results"]) == set(G.SCALE_LABELS)

    restored = D3._profile(on_disk)
    assert tuple(restored.scale_results) == G.SCALE_LABELS
    assert set(restored.scale_results) == set(G.SCALE_LABELS)
