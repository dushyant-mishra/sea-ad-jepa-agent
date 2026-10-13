from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import build_td_relational_synthetic_package_v2 as G


CAPABILITIES = (
    "REL_BROAD_MESO_POSITIVE",
    "REL_FINE_RECURRENT_POSITIVE",
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_SOURCE_VISIBILITY_STRESS",
    "REL_TECHNICAL_TWIN_NEGATIVE",
    "REL_NULL_NEGATIVE",
    "REL_UNDERPOWERED_POSITIVE",
)
SEMANTIC_TOKENS = (
    "REL_", "POSITIVE", "NEGATIVE", "UNDERPOWER", "UNDERIDENT", "STRESS",
    "RARE", "BROAD", "MESO", "FINE", "NULL", "TECHNICAL", "DONOR_RESTRICTED",
    "MULTI_ISLAND", "WRONG_CELL", "PSEUDO_RARE", "DONOR_MATCHED_COMMON",
    "DEPTH_DETECTED_SUM_MATCHED", "SOURCE_OPERATOR_MATCHED",
)
EXPECTED_NPZ_FIELDS = {
    "source", "panel_id",
    "z_values", "x_values", "y_values",
    "z_measured", "x_measured", "y_measured",
    "z_feature_ids", "x_feature_ids", "y_feature_ids",
    "donor_ids", "operator_ids", "global_rows",
    "source_library", "detected_genes",
    "focal_mask", "neighbor_pool_mask", "min_focal_anchors_per_donor",
    "control_ids", "control_focal_masks", "control_neighbor_pool_masks",
    "control_min_focal_anchors_per_donor",
}
BINDING_AUTHORITY = {
    "synthetic_world_generation_authorized",
    "synthetic_world_regeneration_authorized",
    "qualification_model_fitting_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
}
CONTROLLER_AUTHORITY = {
    "synthetic_world_generation_authorized",
    "synthetic_world_regeneration_authorized",
    "real_execution_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
}
RARE_CONTROL_CAPABILITIES = {
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_TECHNICAL_TWIN_NEGATIVE",
}
CONTROL_ROLES = (
    "DONOR_MATCHED_COMMON",
    "DEPTH_DETECTED_SUM_MATCHED",
    "SOURCE_OPERATOR_MATCHED",
    "WRONG_CELL",
    "PSEUDO_RARE_TECHNICAL",
)


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(scope="module")
def pkg(tmp_path_factory):
    root = tmp_path_factory.mktemp("td-rel-v2")
    G.main(str(root))
    return root


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_binding_v2_is_semantically_blind_and_contains_exactly_nine_opaque_challenges(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    assert set(binding) == {
        "schema", "package_id", "package_sha256", "controller_truth_sha256",
        "fit_view_fields", "fit_views", "authority",
    }
    assert binding["schema"] == "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2"
    assert set(binding["authority"]) == BINDING_AUTHORITY
    assert all(value is False for value in binding["authority"].values())
    assert set(binding["fit_view_fields"]) == EXPECTED_NPZ_FIELDS
    assert len(binding["fit_views"]) == 9
    challenge_ids = [rec["challenge_id"] for rec in binding["fit_views"]]
    assert len(set(challenge_ids)) == 9
    for challenge_id in challenge_ids:
        assert challenge_id
        assert not any(token in challenge_id.upper() for token in SEMANTIC_TOKENS)
    text = (pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json").read_text(encoding="utf-8")
    for forbidden in CAPABILITIES + ("semantic_class", "expected_status", "control_roles", "capabilities", "claims"):
        assert forbidden not in text


def test_package_root_and_controller_hashes_are_bound_without_a_hash_cycle(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    fit_root = load_json(pkg / "fit_package_root.json")
    controller = load_json(pkg / "controller_manifest.json")
    assert canonical_sha(fit_root) == binding["package_sha256"]
    assert controller["package_sha256"] == binding["package_sha256"]
    assert canonical_sha(controller) == binding["controller_truth_sha256"]


def test_each_fit_is_sha_named_raw_512_feature_npz_with_exactly_five_opaque_controls(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    fit_dir = pkg / "fit_views"
    for rec in binding["fit_views"]:
        path = fit_dir / f"{rec['sha256']}.npz"
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]
        with np.load(path, allow_pickle=False) as arrays:
            assert set(arrays.files) == EXPECTED_NPZ_FIELDS
            for key in arrays.files:
                assert arrays[key].dtype.kind != "O"
            n = arrays["z_values"].shape[0]
            assert arrays["z_values"].shape == (n, 512)
            assert arrays["x_values"].shape == (n, 512)
            assert arrays["y_values"].shape == (n, 512)
            assert arrays["z_measured"].shape == (n, 512)
            assert arrays["x_measured"].shape == (n, 512)
            assert arrays["y_measured"].shape == (n, 512)
            assert arrays["z_feature_ids"].shape == (512,)
            assert arrays["x_feature_ids"].shape == (512,)
            assert arrays["y_feature_ids"].shape == (512,)
            assert len(set(arrays["global_rows"].tolist())) == n
            assert arrays["control_ids"].shape == (5,)
            assert arrays["control_focal_masks"].shape == (5, n)
            assert arrays["control_neighbor_pool_masks"].shape == (5, n)
            assert arrays["control_min_focal_anchors_per_donor"].shape == (5,)
            control_ids = arrays["control_ids"].astype(str).tolist()
            assert len(set(control_ids)) == 5
            assert all(not any(token in control.upper() for token in SEMANTIC_TOKENS) for control in control_ids)
            assert np.all(~arrays["focal_mask"] | arrays["neighbor_pool_mask"])
            assert np.all(~arrays["control_focal_masks"] | arrays["control_neighbor_pool_masks"])


def test_no_td_geometry_or_verdict_is_delivered_pre_fit(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    forbidden_fields = {
        "z_distances", "x_distances", "y_distances", "null_y_identity_maps",
        "pair_coordinates", "pair_signs", "relational_triplets", "observed_statistic",
        "null_statistics", "status", "expected_status", "capability_id", "semantic_class",
    }
    assert forbidden_fields.isdisjoint(binding["fit_view_fields"])
    for path in (pkg / "fit_views").glob("*.npz"):
        with np.load(path, allow_pickle=False) as arrays:
            assert forbidden_fields.isdisjoint(arrays.files)


def test_controller_manifest_v2_is_the_only_challenge_semantic_mapping(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    controller = load_json(pkg / "controller_manifest.json")
    assert set(controller) == {"schema", "package_sha256", "claims", "authority"}
    assert controller["schema"] == "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V2"
    assert set(controller["authority"]) == CONTROLLER_AUTHORITY
    assert all(value is False for value in controller["authority"].values())
    assert tuple(controller["claims"]) == CAPABILITIES
    challenge_ids = {rec["challenge_id"] for rec in binding["fit_views"]}
    seen = set()
    for capability in CAPABILITIES:
        claim = controller["claims"][capability]
        assert set(claim) == {"challenge_id", "semantic_class", "control_roles", "expected_status"}
        assert claim["challenge_id"] in challenge_ids
        assert claim["challenge_id"] not in seen
        seen.add(claim["challenge_id"])
        assert claim["semantic_class"] in {"POSITIVE_TRUTH", "NEGATIVE_TRUTH", "UNDERIDENTIFIED_TRUTH", "STRESS_TRUTH"}
        if capability in RARE_CONTROL_CAPABILITIES:
            assert tuple(claim["control_roles"]) == CONTROL_ROLES
            role_ids = [ids[0] for ids in claim["control_roles"].values()]
            assert len(set(role_ids)) == 5
        else:
            assert claim["control_roles"] == {}
        if capability == "REL_SOURCE_VISIBILITY_STRESS":
            assert claim["expected_status"] in {"PASS", "FAIL", "NOT_ESTIMABLE"}
        else:
            assert claim["expected_status"] is None
    assert seen == challenge_ids


def test_underpowered_world_plants_truth_but_only_four_donors_without_injecting_td_status(pkg):
    binding = load_json(pkg / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    controller = load_json(pkg / "controller_manifest.json")
    cid = controller["claims"]["REL_UNDERPOWERED_POSITIVE"]["challenge_id"]
    sha = next(rec["sha256"] for rec in binding["fit_views"] if rec["challenge_id"] == cid)
    with np.load(pkg / "fit_views" / f"{sha}.npz", allow_pickle=False) as arrays:
        assert len(set(arrays["donor_ids"].astype(str).tolist())) == 4
        assert "status" not in arrays.files
        assert "expected_status" not in arrays.files


def test_source_visibility_pair_shares_controller_latent_truth_but_differs_only_in_observation_layer():
    worlds = G.build_worlds_for_self_audit()
    broad = worlds["REL_BROAD_MESO_POSITIVE"]
    stress = worlds["REL_SOURCE_VISIBILITY_STRESS"]
    assert np.array_equal(broad["latent"], stress["latent"])
    assert np.array_equal(broad["primary_focal"], stress["primary_focal"])
    assert not np.array_equal(broad["y_measured"], stress["y_measured"])


def test_donor_restricted_world_has_five_active_donors_and_at_least_one_true_zero_donor():
    worlds = G.build_worlds_for_self_audit()
    world = worlds["REL_DONOR_RESTRICTED_POSITIVE"]
    donors = world["donor_ids"].astype(str)
    focal = world["primary_focal"]
    active = {donor for donor in set(donors.tolist()) if np.any(focal[donors == donor])}
    zero = set(donors.tolist()) - active
    assert len(active) == 5
    assert zero


def test_generation_is_byte_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    G.main(str(a))
    G.main(str(b))
    af = {str(p.relative_to(a)): hashlib.sha256(p.read_bytes()).hexdigest() for p in a.rglob("*") if p.is_file()}
    bf = {str(p.relative_to(b)): hashlib.sha256(p.read_bytes()).hexdigest() for p in b.rglob("*") if p.is_file()}
    assert af == bf
