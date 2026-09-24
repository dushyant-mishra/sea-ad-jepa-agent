"""Synthetic red-team: GSE178317 V2 source-lane support cannot be pooled.

All generated counts/identities are synthetic. Passing engineering tests says
nothing about the truth of any GSE178317 real sgRNA assignment or the number
of biological replicates represented by its four sequencing lanes.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


SCRIPT = (Path(__file__).resolve().parents[1] / "analysis" /
          "therapeutic_perturbation_etl" / "scripts" /
          "recover_gse178317_guide_assignments_v2.py")
SPEC = importlib.util.spec_from_file_location("gse178317_v2_under_review", SCRIPT)
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)
LANES = ("L1", "L2", "L3", "L4")


def target_rows(n=30, distribution=(10, 10, 10, 10)):
    return [
        {"target_gene": "SYNTHETIC_TARGET_%02d" % k, "lane": lane}
        for k in range(n)
        for lane, count in zip(LANES, distribution)
        for _ in range(count)
    ]


def control_rows(distribution=(10, 10, 10, 10)):
    return [
        {"target_gene": "NTC", "lane": lane}
        for lane, count in zip(LANES, distribution)
        for _ in range(count)
    ]


def test_positive_paired_lanes_are_only_development_support():
    out = producer.assess_lane_usable_assignments(
        target_rows() + control_rows(), LANES
    )
    assert out["support_pass"] is True
    assert len(out["usable_targets"]) == 30
    assert out["ntc_supported_lanes"] == list(LANES)
    assert all(len(v["paired_lanes"]) == 4 for v in out["target_support"].values())


def test_1200_target_cells_one_lane_and_40_controls_elsewhere_fail():
    # PRE-PATCH DEFECT: 30 targets*40 cells and 40 NTC cells produced PASS
    # despite the absence of even one target-vs-NTC matched lane.
    out = producer.assess_lane_usable_assignments(
        target_rows(distribution=(40, 0, 0, 0)) +
        control_rows(distribution=(0, 40, 0, 0)), LANES
    )
    assert out["support_pass"] is False
    assert not out["usable_targets"]
    assert out["ntc_cells"] == 40
    assert any("same-lane NTC" in r for r in out["failure_reasons"])


def test_sufficient_per_target_counts_but_unpaired_controls_fail():
    out = producer.assess_lane_usable_assignments(
        target_rows(distribution=(20, 10, 10, 0)) +
        control_rows(distribution=(0, 0, 0, 40)), LANES
    )
    assert out["support_pass"] is False
    assert not out["usable_targets"]


def test_40_target_cells_without_three_ten_cell_lanes_fail():
    out = producer.assess_lane_usable_assignments(
        target_rows(distribution=(30, 5, 5, 0)) +
        control_rows(), LANES
    )
    assert out["support_pass"] is False
    assert not out["usable_targets"]


def test_29_valid_targets_do_not_meet_target_coverage_gate():
    out = producer.assess_lane_usable_assignments(
        target_rows(n=29) + control_rows(), LANES
    )
    assert out["support_pass"] is False
    assert len(out["usable_targets"]) == 29


def test_even_40_ntc_cells_only_two_lanes_fail():
    out = producer.assess_lane_usable_assignments(
        target_rows() + control_rows(distribution=(20, 20, 0, 0)), LANES
    )
    assert out["support_pass"] is False
    assert out["ntc_cells"] == 40
    assert len(out["ntc_supported_lanes"]) == 2


@pytest.mark.parametrize("lanes", [("L1", "L1", "L3", "L4"), ("L1", "L2")])
def test_invalid_lane_census_rejected(lanes):
    with pytest.raises(ValueError, match="lane identities"):
        producer.assess_lane_usable_assignments(target_rows() + control_rows(), lanes)


def test_unknown_lane_does_not_silently_enter_pool():
    rows = target_rows() + control_rows()
    rows.append({"target_gene": "SYNTHETIC_TARGET_00", "lane": "L5"})
    with pytest.raises(ValueError, match="unknown lane"):
        producer.assess_lane_usable_assignments(rows, LANES)


def test_actual_stage_call_reports_false_pooled_pass_as_fail(tmp_path, monkeypatch):
    """Exercise actual receipt path, not only the new pure helper.

    The test injects synthetic scores so that every fake cell receives its
    designated guide. This deliberately tests ONLY downstream lane support.
    """
    rows = target_rows(distribution=(40, 0, 0, 0)) + control_rows(
        distribution=(0, 40, 0, 0)
    )
    genes = sorted(set(r["target_gene"] for r in rows))
    lookup = {g: i for i, g in enumerate(genes)}
    counts = np.zeros((len(rows), len(genes)), dtype=np.int32)
    ids, lanes = [], []
    for i, row in enumerate(rows):
        counts[i, lookup[row["target_gene"]]] = 20
        ids.append(row["lane"] + "_FAKECELL%08d" % i)
        lanes.append(row["lane"])
    file = tmp_path / "synthetic-counts-NOT-PHYSICAL.npz"
    np.savez_compressed(file, counts=counts,
                        cell_ids=np.asarray(ids, dtype=str),
                        cell_lane=np.asarray(lanes, dtype=str),
                        guides=np.asarray(genes, dtype=str),
                        guide_target=np.asarray(genes, dtype=str))
    receipt_path = tmp_path / "synthetic-count-receipt.json"
    receipt_path.write_text("{}")
    monkeypatch.setattr(
        producer, "validate_count_stage_receipt",
        lambda counts_npz, receipt_path: {
            "schema": "GSE178317_GUIDE_COUNT_STAGE_V2",
            "matrix": {
                "cells": len(rows), "guides": len(genes),
                "total_umis": int(counts.sum()),
            },
        },
    )
    monkeypatch.setattr(producer, "robust_z",
                        lambda m, t: (np.where(m > 0, 10.0, 0.0),
                                      np.zeros(m.shape[1], dtype=bool)))
    monkeypatch.setattr(
        producer, "poisson_sf_log",
        lambda k, lam: np.full_like(k, -1000.0, dtype=float),
    )
    out_dir = tmp_path / "synthetic-output-NOT-PHYSICAL"
    assert producer.stage_call(SimpleNamespace(
        counts_npz=str(file), count_receipt=str(receipt_path), out_dir=str(out_dir)
    )) == 0
    receipt = json.loads(
        (out_dir / "gse178317_guide_assignment_receipt_v2.json").read_text()
    )
    assert receipt["cells_assigned"] == 1240
    assert receipt["verdict"] == "FAIL_LANE_SUPPORT"
    assert receipt["verdict_basis"]["usable_targets"] == 0
    assert receipt["qualification_scope"] == (
        "DEVELOPMENT_POST_SMOKE_NOT_GUIDE_IDENTITY_VALIDATION"
    )
    assert receipt["guide_identity_independently_verified"] is False
    assert receipt["biological_replication_verified"] is False
