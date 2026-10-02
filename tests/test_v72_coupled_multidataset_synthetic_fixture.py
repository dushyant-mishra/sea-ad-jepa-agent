import csv
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v72_coupled_multidataset_synthetic_fixture.py"
VALIDATOR = ROOT / "scripts/v64/validate_v72_coupled_multidataset_synthetic_fixture.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    root = tmp_path / "challenge"
    load(BUILDER, "v72_builder").build(root)
    return root


def errors(root):
    return load(VALIDATOR, "v72_validator").validate(root)


def test_clean_coupled_fixture_passes(tmp_path):
    assert errors(fixture(tmp_path)) == []


def test_all_required_dataset_families_are_materialized(tmp_path):
    root = fixture(tmp_path)
    manifest = json.loads((root / "observable_raw/MANIFEST.json").read_text())
    assert set(manifest["dataset_families"]) == {
        "FULL104_LIKE",
        "STAGE4_LIKE",
        "SCENICPLUS_LIKE",
        "MORABITO_LIKE",
        "PERTURBATION_LIKE",
        "SPATIAL_LIKE",
        "CHECKPOINT_TWIN",
    }


def test_truth_is_physically_disjoint_from_observables(tmp_path):
    root = fixture(tmp_path)
    assert (root / "hidden_truth/LATENTS.npz").exists()
    assert (root / "hidden_truth/REGULATORY_GRAPH.json").exists()
    assert not any("truth" in p.name.lower() for p in (root / "observable_raw").rglob("*"))


def test_first_overlap_only_corruption_is_detected(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/STAGE4_LIKE/all_overlap_crosswalk.csv"
    with open(p, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]
    peak = body[0][0]
    kept_one = False
    corrupted = []
    for row in body:
        if row[0] == peak:
            if kept_one:
                continue
            kept_one = True
        corrupted.append(row)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(corrupted)
    assert any(x.startswith("STAGE4_ALL_OVERLAP_CROSSWALK_MISMATCH") for x in errors(root))


def test_stage4_random_or_wrong_control_construction_is_rejected(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/STAGE4_LIKE/decision_contract.json"
    obj = json.loads(p.read_text())
    obj["control_construction"] = "GLOBAL_RANDOM_CONTROL"
    p.write_text(json.dumps(obj))
    assert "STAGE4_CONTROL_CONSTRUCTION_NOT_FROZEN_MATCHED" in errors(root)


def test_g2_gap_cannot_be_silently_closed_by_fixture(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/STAGE4_LIKE/decision_contract.json"
    obj = json.loads(p.read_text())
    obj["G2"]["status"] = "QUALIFIED"
    obj["G2"]["numeric_threshold_frozen_here"] = True
    p.write_text(json.dumps(obj))
    e = errors(root)
    assert "STAGE4_G2_SPEC_GAP_SILENTLY_CLOSED" in e
    assert "STAGE4_G2_POSTHOC_THRESHOLD_PRESENT" in e


def test_barcode_suffix_cannot_become_donor_authority(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/SCENICPLUS_LIKE/route_config.json"
    obj = json.loads(p.read_text())
    obj["donor_map_source"] = "BARCODE_SUFFIX"
    obj["barcode_suffix_is_donor"] = True
    p.write_text(json.dumps(obj))
    e = errors(root)
    assert "SCENIC_DONOR_MAP_NOT_METADATA_AUTHORITY" in e
    assert "SCENIC_SUFFIX_DONOR_INFERENCE_ALLOWED" in e


def test_synthetic_cohort_contains_real_suffix_collision_positive_control(tmp_path):
    root = fixture(tmp_path)
    rows = list(csv.DictReader(open(root / "observable_raw/SCENICPLUS_LIKE/metadata.csv", encoding="utf-8")))
    mapping = {}
    for r in rows:
        mapping.setdefault(r["barcode"].rsplit("-", 1)[-1], set()).add(r["donor"])
    assert any(len(v) > 1 for v in mapping.values())


def test_route_specific_rankings_cannot_be_shared(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/SCENICPLUS_LIKE/route_config.json"
    obj = json.loads(p.read_text())
    obj["rankings_shared_across_routes"] = True
    p.write_text(json.dumps(obj))
    assert "SCENIC_ROUTE_RANKINGS_ILLEGALLY_SHARED" in errors(root)


def test_rng_and_thread_pins_are_enforced(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/SCENICPLUS_LIKE/route_config.json"
    obj = json.loads(p.read_text())
    obj["ranking_seed"] = None
    obj["blas_threads"] = 16
    p.write_text(json.dumps(obj))
    e = errors(root)
    assert "SCENIC_RANKING_SEED_NOT_PINNED" in e
    assert "SCENIC_BLAS_NOT_PINNED" in e


def test_morabito_like_fixture_forbids_fake_cell_pairing(tmp_path):
    import numpy as np

    root = fixture(tmp_path)
    p = root / "observable_raw/MORABITO_LIKE/atac.npz"
    z = np.load(p, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    rna = np.load(root / "observable_raw/MORABITO_LIKE/rna.npz", allow_pickle=False)
    d["nuclei"] = d["nuclei"].copy()
    d["nuclei"][0] = rna["nuclei"][0]
    np.savez_compressed(p, **d)
    assert "MORABITO_FAKE_CELL_PAIRING" in errors(root)


def test_checkpoint_failure_positive_controls_are_behavioral(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/CHECKPOINT_TWIN/checkpoint_behaviors.json"
    obj = json.loads(p.read_text())
    for cp in obj["checkpoints"]:
        if cp["id"] == "PRIVATE_STATE_LEAK":
            cp["private_r2"] = 0.01
    p.write_text(json.dumps(obj))
    assert "CHECKPOINT_PRIVATE_LEAK_POSITIVE_CONTROL_WEAK" in errors(root)


def test_truth_file_exposure_is_rejected(tmp_path):
    root = fixture(tmp_path)
    shutil.copy(
        root / "hidden_truth/REGULATORY_GRAPH.json",
        root / "observable_raw/SCENICPLUS_LIKE/TRUTH_LEAK.json",
    )
    assert any(x.startswith("TRUTH_FIREWALL_PATH:") for x in errors(root))
