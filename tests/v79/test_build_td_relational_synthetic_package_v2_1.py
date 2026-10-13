from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import build_td_relational_synthetic_package_v2_1 as G
import finalize_td_relational_synthetic_package_v2_1 as F


TEST_SEED = "31" * 32
TEST_NONCE = "a7" * 32
TD_SHA = "2" * 40
INTERFACE_HASHES = {
    "package_validator_sha256": "1" * 64,
    "synthetic_adapter_sha256": "2" * 64,
    "disk_preflight_sha256": "3" * 64,
    "qualification_runner_v3_sha256": "4" * 64,
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build(tmp_path: Path) -> Path:
    out = tmp_path / "pkg"
    G.main(str(out), realization_seed_hex=TEST_SEED, blind_nonce=TEST_NONCE)
    return out


def _fit_by_capability(root: Path, capability: str):
    binding = _load(root / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    controller = _load(root / "controller" / "controller_manifest.json")
    cid = controller["claims"][capability]["challenge_id"]
    sha = next(rec["sha256"] for rec in binding["fit_views"] if rec["challenge_id"] == cid)
    return cid, controller["claims"][capability], np.load(root / "fit_views" / f"{sha}.npz", allow_pickle=False)


def test_v21_all_nine_challenges_have_identical_structural_shape_and_five_controls(tmp_path):
    root = _build(tmp_path)
    binding = _load(root / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    assert len(binding["fit_views"]) == 9
    shapes = set()
    donor_counts = set()
    for rec in binding["fit_views"]:
        with np.load(root / "fit_views" / f"{rec['sha256']}.npz", allow_pickle=False) as z:
            n = z["z_values"].shape[0]
            shapes.add((n, z["z_values"].shape[1], z["x_values"].shape[1], z["y_values"].shape[1]))
            donor_counts.add(len(set(z["donor_ids"].astype(str).tolist())))
            assert z["control_ids"].shape == (5,)
            assert z["control_focal_masks"].shape == (5, n)
            assert z["control_neighbor_pool_masks"].shape == (5, n)
    assert shapes == {(210, 512, 512, 512)}
    assert donor_counts == {6}


def test_prefit_binding_has_no_semantic_mapping_or_secret_realization_material(tmp_path):
    root = _build(tmp_path)
    text = (root / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json").read_text(encoding="utf-8")
    for token in G.CAPABILITIES + G.CONTROL_ROLES + (TEST_SEED, TEST_NONCE, "blind_nonce", "claims"):
        assert token not in text
    assert not (root / "controller_manifest.json").exists()
    assert (root / "controller" / "controller_manifest.json").is_file()
    assert (root / "controller" / "controller_realization_receipt.json").is_file()


def test_controller_manifest_v3_uses_nonce_and_secret_seed_changes_opaque_mapping(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    G.main(str(a), realization_seed_hex=TEST_SEED, blind_nonce=TEST_NONCE)
    G.main(str(b), realization_seed_hex="32" * 32, blind_nonce=TEST_NONCE)
    ca = _load(a / "controller" / "controller_manifest.json")
    cb = _load(b / "controller" / "controller_manifest.json")
    assert ca["schema"] == "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V3"
    assert ca["blind_nonce"] == TEST_NONCE
    map_a = {cap: claim["challenge_id"] for cap, claim in ca["claims"].items()}
    map_b = {cap: claim["challenge_id"] for cap, claim in cb["claims"].items()}
    assert map_a != map_b


def test_same_seed_is_byte_deterministic_but_seed_is_controller_only(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    G.main(str(a), realization_seed_hex=TEST_SEED, blind_nonce=TEST_NONCE)
    G.main(str(b), realization_seed_hex=TEST_SEED, blind_nonce=TEST_NONCE)
    af = {str(p.relative_to(a)): hashlib.sha256(p.read_bytes()).hexdigest() for p in a.rglob("*") if p.is_file()}
    bf = {str(p.relative_to(b)): hashlib.sha256(p.read_bytes()).hexdigest() for p in b.rglob("*") if p.is_file()}
    assert af == bf
    prefit_paths = [p for p in a.rglob("*") if p.is_file() and "controller" not in p.parts]
    assert all(TEST_SEED not in p.read_bytes().decode("latin1") for p in prefit_paths)


def test_source_visibility_stress_preserves_sampling_identity_and_changes_observation_only(tmp_path):
    root = _build(tmp_path)
    _, _, broad = _fit_by_capability(root, "REL_BROAD_MESO_POSITIVE")
    _, _, stress = _fit_by_capability(root, "REL_SOURCE_VISIBILITY_STRESS")
    try:
        for field in ("source", "panel_id", "donor_ids", "operator_ids", "global_rows", "z_values", "x_values", "focal_mask", "neighbor_pool_mask"):
            assert np.array_equal(broad[field], stress[field]), field
        assert not np.array_equal(broad["y_measured"], stress["y_measured"])
        assert not np.array_equal(broad["source_library"], stress["source_library"])
    finally:
        broad.close(); stress.close()


def test_underpowered_keeps_six_donors_but_only_four_focal_recurring(tmp_path):
    root = _build(tmp_path)
    _, _, arrays = _fit_by_capability(root, "REL_UNDERPOWERED_POSITIVE")
    try:
        donors = arrays["donor_ids"].astype(str)
        focal = arrays["focal_mask"]
        active = {d for d in set(donors.tolist()) if np.any(focal[donors == d])}
        assert len(set(donors.tolist())) == 6
        assert len(active) == 4
    finally:
        arrays.close()


def test_rare_role_controls_are_controller_mapped_and_role_faithful(tmp_path):
    root = _build(tmp_path)
    for capability in G.RARE_CONTROL_CAPABILITIES:
        _, claim, arrays = _fit_by_capability(root, capability)
        try:
            ids = arrays["control_ids"].astype(str).tolist()
            id_to_index = {value: i for i, value in enumerate(ids)}
            donors = arrays["donor_ids"].astype(str)
            primary = arrays["focal_mask"]
            primary_donors = {d for d in set(donors.tolist()) if np.any(primary[donors == d])}
            assert set(claim["control_roles"]) == set(G.CONTROL_ROLES)
            mapped = [claim["control_roles"][role][0] for role in G.CONTROL_ROLES]
            assert set(mapped) == set(ids)

            donor_mask = arrays["control_focal_masks"][id_to_index[claim["control_roles"]["DONOR_MATCHED_COMMON"][0]]]
            source_mask = arrays["control_focal_masks"][id_to_index[claim["control_roles"]["SOURCE_OPERATOR_MATCHED"][0]]]
            depth_mask = arrays["control_focal_masks"][id_to_index[claim["control_roles"]["DEPTH_DETECTED_SUM_MATCHED"][0]]]
            pseudo_mask = arrays["control_focal_masks"][id_to_index[claim["control_roles"]["PSEUDO_RARE_TECHNICAL"][0]]]
            wrong_mask = arrays["control_focal_masks"][id_to_index[claim["control_roles"]["WRONG_CELL"][0]]]

            for mask in (donor_mask, source_mask, depth_mask, pseudo_mask, wrong_mask):
                active = {d for d in set(donors.tolist()) if np.any(mask[donors == d])}
                assert active == primary_donors
                assert not np.any(mask & primary)

            # Depth/detection matching is prospective and meaningfully closer than the intentionally wrong-cell control.
            p_lib = float(np.median(arrays["source_library"][primary]))
            p_det = float(np.median(arrays["detected_genes"][primary]))
            depth_distance = abs(float(np.median(arrays["source_library"][depth_mask])) - p_lib) / max(p_lib, 1.0)
            depth_distance += abs(float(np.median(arrays["detected_genes"][depth_mask])) - p_det) / max(p_det, 1.0)
            wrong_distance = abs(float(np.median(arrays["source_library"][wrong_mask])) - p_lib) / max(p_lib, 1.0)
            wrong_distance += abs(float(np.median(arrays["detected_genes"][wrong_mask])) - p_det) / max(p_det, 1.0)
            assert depth_distance <= wrong_distance + 0.10

            # Pseudo-rare is measurement-degraded, not a hidden biological positive.
            pseudo_support = float(arrays["x_measured"][pseudo_mask].mean())
            donor_support = float(arrays["x_measured"][donor_mask].mean())
            assert pseudo_support < donor_support
        finally:
            arrays.close()


def test_control_array_order_is_secret_seed_dependent(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    G.main(str(a), realization_seed_hex=TEST_SEED, blind_nonce=TEST_NONCE)
    G.main(str(b), realization_seed_hex="99" * 32, blind_nonce=TEST_NONCE)
    ca = _load(a / "controller" / "controller_manifest.json")
    cb = _load(b / "controller" / "controller_manifest.json")
    cap = "REL_RARE_LOCAL_ISLAND_POSITIVE"
    ida = ca["claims"][cap]["challenge_id"]
    idb = cb["claims"][cap]["challenge_id"]
    ba = _load(a / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    bb = _load(b / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    sha_a = next(r["sha256"] for r in ba["fit_views"] if r["challenge_id"] == ida)
    sha_b = next(r["sha256"] for r in bb["fit_views"] if r["challenge_id"] == idb)
    with np.load(a / "fit_views" / f"{sha_a}.npz", allow_pickle=False) as za, np.load(b / "fit_views" / f"{sha_b}.npz", allow_pickle=False) as zb:
        assert za["control_ids"].astype(str).tolist() != zb["control_ids"].astype(str).tolist()


def test_prefit_transport_excludes_controller_bytes_and_controller_transport_is_separate(tmp_path):
    root = _build(tmp_path)
    prefit = tmp_path / "prefit.tar.xz"
    controller = tmp_path / "controller.tar.xz"
    receipt = F.build_separated_transport_archives(
        package_dir=root,
        prefit_archive_path=prefit,
        controller_archive_path=controller,
        td_commit_sha=TD_SHA,
        td_interface_hashes=INTERFACE_HASHES,
    )
    with tarfile.open(prefit, "r:xz") as tf:
        names = set(tf.getnames())
        assert all(not name.startswith("controller/") for name in names)
        assert "pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json" in names
        assert len([name for name in names if name.endswith(".npz")]) == 9
    with tarfile.open(controller, "r:xz") as tf:
        names = set(tf.getnames())
        assert "controller/controller_manifest.json" in names
        assert "controller/controller_realization_receipt.json" in names
        assert all(not name.endswith(".npz") for name in names)
    assert receipt["prefit_archive_sha256"] != receipt["controller_archive_sha256"]
