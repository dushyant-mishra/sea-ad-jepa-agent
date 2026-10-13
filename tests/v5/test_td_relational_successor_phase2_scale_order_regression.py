from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v3 as D3
import td_relational_successor_gate_v2 as G
import td_relational_successor_qualification_runner_v2 as Q2
import td_test_qualification_package_v2 as P


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


def _raw_profile(scale_results) -> dict:
    return {
        "source": "S0",
        "panel_id": "P0",
        "profile_id": "opaque-profile",
        "scale_results": scale_results,
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


def test_phase2_reader_still_accepts_frozen_order_scale_grid():
    restored = D3._profile(_raw_profile({label: _scale(label) for label in G.SCALE_LABELS}))
    assert tuple(restored.scale_results) == G.SCALE_LABELS


def _missing_label() -> dict:
    return {label: _scale(label) for label in G.SCALE_LABELS[:-1]}


def _extra_label() -> dict:
    grid = {label: _scale(label) for label in G.SCALE_LABELS}
    grid["1/5"] = _scale("1/5")
    return grid


def _substituted_label() -> dict:
    # Same cardinality as the frozen grid, different label set.
    grid = {label: _scale(label) for label in G.SCALE_LABELS[:-1]}
    grid["1/5"] = _scale("1/5")
    return grid


def _empty_grid() -> dict:
    return {}


def _list_grid() -> list:
    return [_scale(label) for label in G.SCALE_LABELS]


@pytest.mark.parametrize(
    "build_grid",
    [_missing_label, _extra_label, _substituted_label, _empty_grid, _list_grid],
    ids=["missing", "extra", "substituted", "empty", "not_a_mapping"],
)
def test_phase2_reader_fails_closed_on_non_frozen_scale_label_set(build_grid):
    grid = build_grid()
    if isinstance(grid, dict) and grid:
        assert set(grid) != set(G.SCALE_LABELS)
    on_disk = json.loads(json.dumps(_raw_profile(grid), sort_keys=True, separators=(",", ":")))
    with pytest.raises(D3.DiskRunnerV3Error, match="frozen profile scale grid mismatch"):
        D3._profile(on_disk)


_UNSORTED_DONORS = ("D9", "D1", "D5", "D3", "D7")


def _scale_receipt(label: str) -> G.ScaleResult:
    numerator, denominator = map(int, label.split("/"))
    return G.ScaleResult(
        scale_label=label,
        numerator=numerator,
        denominator=denominator,
        status="FAIL",
        reason="RELATION_NOT_ESTABLISHED",
        observed_statistic=0.1 + 1.0 / denominator,
        family_null_p95=None,
        n_observed_donors=len(_UNSORTED_DONORS),
        observed_donor_agreements={d: 0.25 + 0.01 * i for i, d in enumerate(_UNSORTED_DONORS)},
        observed_resolved_relations={d: 20 + i for i, d in enumerate(_UNSORTED_DONORS)},
        null_source_statistics=tuple([0.5, None] * 32),
        n_sampled_triplets=320,
        eligible_donors=_UNSORTED_DONORS,
    )


def _profile_receipt(profile_id: str) -> G.RelationalProfileReceipt:
    return G.RelationalProfileReceipt(
        source="S0",
        panel_id="P0",
        profile_id=profile_id,
        scale_results={label: _scale_receipt(label) for label in G.SCALE_LABELS},
        characterization=("NO_RELATION_ESTABLISHED",),
        focal_anchor_count=40,
        failure_scope="SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
        authority={
            "training_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
        },
    )


def test_full_blinded_receipt_roundtrips_through_durable_sorted_writer(tmp_path):
    fit_views = {f"q-{i:02d}-z": f"{i + 1:064x}" for i in (3, 0, 2, 1)}
    package = P.ValidatedExternalPackage(
        package_id="pkg-scale-order",
        package_sha256="a" * 64,
        fit_views=fit_views,
        controller_truth_sha256="b" * 64,
        fit_view_fields=("x",),
    )
    fit = Q2.BlindedFitReceipt(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        profiles={cid: _profile_receipt(cid) for cid in fit_views},
        controls={
            cid: {f"c-{j}": _profile_receipt(f"{cid}::c-{j}") for j in (4, 0, 3, 1, 2)}
            for cid in fit_views
        },
        authority={key: False for key in sorted(Q2.RUN_AUTHORITY_KEYS)},
    )
    document = {
        "schema": D3.BLINDED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "fit_receipt": fit,
        "authority": {**D3._PHASE_AUTHORITY, "controller_truth_opened": False},
    }
    path = tmp_path / "blinded.json"
    D3._write_json_durable(path, document)
    on_disk = D3._read_json(path)
    for profile in on_disk["fit_receipt"]["profiles"].values():
        assert tuple(profile["scale_results"]) != G.SCALE_LABELS

    restored = D3._fit_receipt_from_document(on_disk, package)
    assert restored == fit
    for profile in restored.profiles.values():
        assert tuple(profile.scale_results) == G.SCALE_LABELS
    for local in restored.controls.values():
        for profile in local.values():
            assert tuple(profile.scale_results) == G.SCALE_LABELS

    reserialized = json.dumps(
        D3._jsonable({**on_disk, "fit_receipt": restored}),
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ) + "\n"
    assert reserialized.encode("utf-8") == path.read_bytes()
