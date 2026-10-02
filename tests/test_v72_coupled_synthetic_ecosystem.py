import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v72_coupled_synthetic_ecosystem.py"
VALIDATOR = ROOT / "scripts/v64/validate_v72_coupled_synthetic_ecosystem.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    root = tmp_path / "challenge"
    load(BUILDER, "v72_builder").build(root, seed=7202, n_cells=720)
    return root


def test_v72_clean_coupled_ecosystem_passes(tmp_path):
    root = fixture(tmp_path)
    assert load(VALIDATOR, "v72_validator").validate(root) == []


def test_v72_truth_is_physically_separate(tmp_path):
    root = fixture(tmp_path)
    assert (root / "hidden_truth/TRUTH_LATENTS.npz").exists()
    assert (root / "hidden_truth/TRUTH_GRAPH.json").exists()
    assert not any("truth" in p.name.lower() for p in (root / "observable_raw").rglob("*") if p.is_file())


def test_v72_full104_has_structural_missingness_not_measured_zero(tmp_path):
    root = fixture(tmp_path)
    z = np.load(root / "observable_raw/FULL104_like/rna_counts.npz", allow_pickle=False)
    assert np.any(z["availability"] == 0)
    assert np.all(z["counts"][z["availability"] == 0] == 0)
    assert z["availability"].dtype == np.uint8


def test_v72_stage4_control_is_promoter_fixed_distance_matched_and_nonoverlapping(tmp_path):
    import csv
    root = fixture(tmp_path)
    with open(root / "observable_raw/NIH_CARD_STAGE4_like/pair_ledger.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    for r in rows:
        assert r["control_policy"] == "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL"
        ls, le = int(r["linked_start"]), int(r["linked_end"])
        cs, ce = int(r["control_start"]), int(r["control_end"])
        assert ce <= ls or le <= cs
        ld, cd = abs(int(r["linked_distance"])), abs(int(r["control_distance"]))
        assert abs(cd - ld) <= max(.10 * ld, 10_000)
        assert r["linked_accessible"] == r["control_accessible"] == "1"


def test_v72_stage4_windows_include_multi_overlap_positive_control(tmp_path):
    import csv
    root = fixture(tmp_path)
    with open(root / "observable_raw/NIH_CARD_STAGE4_like/overlapping_5kb_windows.bed.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    starts = [(int(r["start"]), int(r["end"])) for r in rows]
    assert any(sum(s <= ((a+b)//2) < e for s,e in starts) > 1 for a,b in starts)


def test_v72_barcode_suffix_is_not_donor_identity(tmp_path):
    import csv
    from collections import defaultdict
    root = fixture(tmp_path)
    with open(root / "observable_raw/GSE214979_SCENICPLUS_like/barcode_to_donor.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    suffix = defaultdict(set)
    for r in rows:
        suffix[r["barcode"].rsplit("-",1)[-1]].add(r["donor"])
    assert any(len(donors) > 1 for donors in suffix.values())


def test_v72_morabito_like_has_no_fake_cell_pairing(tmp_path):
    root = fixture(tmp_path)
    rna = np.load(root / "observable_raw/MORABITO_like/rna.npz", allow_pickle=False)
    atac = np.load(root / "observable_raw/MORABITO_like/atac.npz", allow_pickle=False)
    assert not (set(rna["cells"].tolist()) & set(atac["cells"].tolist()))


def test_v72_detects_digest_corruption(tmp_path):
    root = fixture(tmp_path)
    p = root / "observable_raw/ECOSYSTEM_MANIFEST.json"
    d = json.loads(p.read_text())
    d["n_master_cells"] += 1
    p.write_text(json.dumps(d))
    errors = load(VALIDATOR, "v72_validator_corrupt").validate(root)
    assert any(x.startswith("DIGEST_MISMATCH:ECOSYSTEM_MANIFEST.json") for x in errors)


def test_v72_detects_truth_leak(tmp_path):
    root = fixture(tmp_path)
    leak = root / "observable_raw/TRUTH_LEAK.json"
    shutil.copy(root / "hidden_truth/TRUTH_GRAPH.json", leak)
    errors = load(VALIDATOR, "v72_validator_leak").validate(root)
    assert any(x.startswith("TRUTH_FIREWALL_PATH:") for x in errors)


def test_v72_stage4_selection_mechanism_exercises_trimming(tmp_path):
    import csv
    root = fixture(tmp_path)
    audit = root / "observable_raw/NIH_CARD_STAGE4_like/control_selection_audit.csv"
    with open(audit, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 48
    trimmed = [r for r in rows if r["status"] == "TRIM_NO_ADMISSIBLE_CONTROL"]
    assert len(trimmed) == 1
    assert trimmed[0]["edge_id"] == "EDGE047"
    assert int(trimmed[0]["n_admissible"]) == 0
    selected = [r for r in rows if r["status"] == "SELECTED"]
    assert selected
    assert all(int(r["n_admissible"]) >= 1 for r in selected)
