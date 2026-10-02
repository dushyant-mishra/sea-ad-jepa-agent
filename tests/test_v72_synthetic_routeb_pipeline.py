import csv
import gzip
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v72_coupled_synthetic_ecosystem.py"
ROUTEB = ROOT / "scripts/v64/run_v72_synthetic_routeb_pipeline.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    challenge = tmp_path / "challenge"
    load(BUILDER, "v72_builder_routeb").build(challenge, seed=7202, n_cells=720)
    scenic = challenge / "observable_raw/GSE214979_SCENICPLUS_like"
    out = tmp_path / "routeb"
    receipt = load(ROUTEB, "v72_routeb").run(scenic, out, min_bin_count=2)
    return challenge, out, receipt


def test_routeb_pipeline_runs_from_raw_fragments(tmp_path):
    _, out, receipt = fixture(tmp_path)
    assert receipt["status"] == "PASS__SYNTHETIC_ROUTEB_PIPELINE"
    assert receipt["records_scanned"] > 0
    assert receipt["n_pseudobulks"] > 1
    assert (out / "consensus_regions.bed").exists()
    assert receipt["consensus"]["n_regions"] > 0


def test_routeb_suffix_collision_positive_control_is_live(tmp_path):
    _, _, receipt = fixture(tmp_path)
    collisions = receipt["donor_identity"]["suffix_collision_positive_control"]
    assert collisions
    assert all(len(donors) > 1 for donors in collisions.values())


def test_routeb_pseudobulk_unit_is_donor_by_subcluster(tmp_path):
    _, _, receipt = fixture(tmp_path)
    assert receipt["pseudobulk_unit"] == "donor x subcluster"
    assert all("__MG_SUB_" in key for key in receipt["pseudobulks"])


def test_routeb_receipt_explicitly_not_real_macs(tmp_path):
    _, _, receipt = fixture(tmp_path)
    assert receipt["scientific_scope"] == "INTERFACE_AND_ETL_QUALIFICATION_ONLY__NOT_MACS_OR_REAL_PEAK_CALLING"
    assert "Real Route-B uses pycisTopic/MACS" in receipt["synthetic_peak_caller"]["why_not_macs"]


def test_routeb_fails_on_fragment_barcode_not_in_authority(tmp_path):
    challenge = tmp_path / "challenge"
    load(BUILDER, "v72_builder_badbc").build(challenge, seed=7202, n_cells=720)
    scenic = challenge / "observable_raw/GSE214979_SCENICPLUS_like"
    fragments = scenic / "fragments.tsv.gz"
    with gzip.open(fragments, "at") as fh:
        fh.write("chr1\t1\t151\tUNKNOWN-5\t1\n")
    try:
        load(ROUTEB, "v72_routeb_badbc").run(scenic, tmp_path / "routeb")
    except ValueError as ex:
        assert str(ex).startswith("FAIL__FRAGMENT_BARCODE_NOT_IN_AUTHORITY")
    else:
        raise AssertionError("unknown fragment barcode did not fail closed")


def test_routeb_pseudobulk_receipts_bind_reread_disk_files(tmp_path):
    _, out, receipt = fixture(tmp_path)
    for key, meta in receipt["pseudobulks"].items():
        p = Path(meta["path"])
        assert p.exists()
        assert sum(1 for _ in open(p)) == meta["records"]
