import csv
import gzip
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v72_coupled_multidataset_synthetic_fixture.py"
ROUTEB = ROOT / "scripts/v64/run_v72_synthetic_routeb_pipeline.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(tmp_path):
    root = tmp_path / "challenge"
    load(BUILDER, "v72_builder_routeb").build(root)
    return root


def test_routeb_ci_pipeline_runs_from_raw_fragments_to_consensus(tmp_path):
    root = build(tmp_path)
    out = tmp_path / "routeb"
    r = load(ROUTEB, "v72_routeb").run(root, out)
    assert r["status"] == "PASS__RAW_TO_CONSENSUS_INTERFACE_QUALIFIED"
    assert r["fragment_records_scanned"] > 0
    assert r["n_pseudobulks"] > 1
    assert r["consensus"]["n_regions"] > 0
    assert r["outputs_verified_by_reread"] is True
    assert r["consensus"]["recurrence_filter_applied"] is False


def test_routeb_ci_counts_and_discards_out_of_cohort_fragment(tmp_path):
    root = build(tmp_path)
    frag = root / "observable_raw/SCENICPLUS_LIKE/fragments.tsv.gz"
    with gzip.open(frag, "at", encoding="utf-8") as fh:
        fh.write("chr1\t10000\t10070\tNOT_IN_COHORT-5\t1\n")
    out = tmp_path / "routeb"
    r = load(ROUTEB, "v72_routeb_ooc").run(root, out)
    assert r["out_of_cohort_records_counted_and_discarded"] == 1


def test_routeb_consensus_recurrence_has_multiple_donors(tmp_path):
    root = build(tmp_path)
    out = tmp_path / "routeb"
    load(ROUTEB, "v72_routeb_recurrence").run(root, out)
    rows = list(csv.DictReader(open(
        out / "V72_ROUTE_B_CI_CONSENSUS_RECURRENCE.csv", encoding="utf-8"
    )))
    assert rows
    assert any(int(r["n_donors"]) > 1 for r in rows)


def test_routeb_receipt_never_claims_real_macs_qualification(tmp_path):
    root = build(tmp_path)
    out = tmp_path / "routeb"
    r = load(ROUTEB, "v72_routeb_scope").run(root, out)
    assert r["is_macrophysical_peak_caller"] is False
    assert r["real_routeb_still_requires_macs_pycistopic"] is True
