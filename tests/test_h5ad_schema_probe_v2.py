"""Qualification suite for h5ad_schema_probe_v2.

The point of these tests is not that the probe runs. It is that the probe
RECOVERS PLANTED QUANTITIES where recovery is possible, and REFUSES TO REPORT A
NUMBER where it is not. A probe that returns a confident value in a state it
cannot measure is worse than one that returns nothing, because the value is
indistinguishable from a real measurement.

The defect this suite exists to lock down: v1.0 reported

    "n_total_paired_with_atac": 0

on fixture B, whose planted truth is 35 paired microglia. Zero is a measurement.
The true state was "the namespaces do not line up, so this cannot be measured".

Required coverage, from the work order:
  - exact barcode namespace                      test_A_*
  - unresolved namespace                         test_B_*, test_C_*
  - safe sample+barcode diagnostic               test_composite_*
  - zero-microglia donors                        test_A_zero_microglia_donor_*
  - donor-label mismatch                         test_A_donor_label_mismatch_*
  - modern AnnData categorical layout            test_modern_categorical_*
  - count-like vs transformed slot classification test_slot_*

Plus, added here because the suite would otherwise be unable to fail for the
right reason:
  - the v1.0 regression, run against the preserved v1.0 file             test_v1_*
  - a positive control that the fail-closed guard can actually trip      test_guard_*
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "scripts" / "v63" / "h5ad_schema_probe_v2.py"
V1 = ROOT / "scripts" / "v63" / "h5ad_schema_probe_v1_0_as_received.py"
MAKE = ROOT / "scripts" / "v63" / "make_h5ad_fixtures_v2.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def fixtures(tmp_path_factory):
    """Build A, B, C once and return (dir, planted_truth)."""
    pytest.importorskip("anndata")
    d = tmp_path_factory.mktemp("h5ad_fixtures")
    mk = _load(MAKE, "make_h5ad_fixtures_v2")
    truth = mk.main(str(d))
    return d, truth


def run_v2(d, name, *extra, out=None):
    probe = _load(V2, "h5ad_schema_probe_v2")
    out = out or (d / f"{name}_receipt.json")
    argv = ["--rna", str(d / f"{name}_rna.h5ad"), "--atac", str(d / f"{name}_atac.h5ad"),
            "--out", str(out), *extra]
    assert probe.main(argv) == 0
    return json.loads(Path(out).read_text())


# ---------------------------------------------------------------- fixture A
# Exact namespace. Every planted quantity must be recovered exactly.

def test_A_exact_namespace_is_resolved(fixtures):
    d, truth = fixtures
    r = run_v2(d, "A")
    assert r["pairing"]["state"] == "PAIRING_RESOLVED_EXACT"
    assert r["pairing"]["n_shared_exact"] == truth["A"]["shared"]
    assert r["pairing"]["basis_used_for_counts"] == "EXACT_INDEX"


def test_A_recovers_planted_microglia_counts(fixtures):
    d, truth = fixtures
    r = run_v2(d, "A")
    mg = r["microglia"]
    assert mg["n_total_rna"] == truth["A"]["mg_total"]
    assert mg["n_total_paired_with_atac"] == truth["A"]["mg_paired"]
    assert mg["per_donor_counts"] == truth["A"]["mg_per_donor"]


def test_A_zero_microglia_donor_is_reported_not_dropped(fixtures):
    """D01 has zero microglia. A donor with no cells of the type must appear with
    an explicit 0, not vanish from the table -- otherwise donor counts silently
    disagree with the cohort size."""
    d, truth = fixtures
    r = run_v2(d, "A")
    mg = r["microglia"]
    assert mg["per_donor_counts"]["D01"] == 0
    assert "D01" in mg["donors_with_zero_microglia"]
    assert mg["n_donors"] == len(truth["A"]["mg_per_donor"])


def test_A_donor_label_mismatch_is_detected(fixtures):
    """One ATAC nucleus carries sample_id 'WRONG'. It must be counted."""
    d, _ = fixtures
    r = run_v2(d, "A")
    dl = r["donor_label_agreement_on_shared"]
    assert dl["checked"] is True
    assert dl["n_mismatch"] == 1
    assert dl["consistent"] is False


def test_A_fails_qualification_because_of_that_mismatch(fixtures):
    """Recovering every count is NOT the same as qualifying. A has a real donor
    label inconsistency, and the rule requires zero."""
    d, _ = fixtures
    r = run_v2(d, "A")
    assert r["qualification"]["pairing_resolved"] is True
    assert r["qualification"]["donor_labels_consistent"] is False
    assert r["qualification"]["QUALIFIED_FOR_PAIRED_USE"] is False
    assert r["probe_status"] == "PROBE_INCOMPLETE"


def test_A_per_donor_paired_counts_are_reported(fixtures):
    """v1.0 computed these and discarded them (`counts_paired` was assigned and
    never used)."""
    d, truth = fixtures
    r = run_v2(d, "A")
    perp = r["microglia"]["per_donor_paired_counts"]
    assert perp is not None
    assert sum(perp.values()) == truth["A"]["mg_paired"]
    for donor, total in r["microglia"]["per_donor_counts"].items():
        assert perp[donor] <= total, "paired can never exceed total for a donor"


# ---------------------------------------------------------------- fixture B
# THE v1.0 DEFECT. Different barcode conventions; pairing is unresolvable.

def test_B_unresolved_namespace_is_named_as_such(fixtures):
    d, _ = fixtures
    r = run_v2(d, "B")
    assert r["pairing"]["state"] == "PAIRING_NAMESPACE_UNRESOLVED"
    assert r["pairing"]["n_shared_exact"] == 0
    assert r["pairing"]["basis_used_for_counts"] == "NONE__UNRESOLVED"


def test_B_paired_microglia_is_null_not_zero(fixtures):
    """The regression. v1.0 said 0; the planted truth is 35. The only honest
    answer is 'not measurable', and it must not be encoded as a number."""
    d, truth = fixtures
    r = run_v2(d, "B")
    mg = r["microglia"]
    assert mg["n_total_paired_with_atac"] is None
    assert mg["n_total_paired_with_atac"] != 0
    assert mg["per_donor_paired_counts"] is None
    assert mg["paired_status"] == "PAIRING_NAMESPACE_UNRESOLVED"
    assert truth["B"]["mg_paired"] == 35  # the number v1.0 rendered as 0


def test_B_unpaired_quantities_are_still_reported(fixtures):
    """Failing closed on pairing must not suppress what IS measurable."""
    d, truth = fixtures
    r = run_v2(d, "B")
    assert r["microglia"]["n_total_rna"] == truth["B"]["mg_total"]
    assert r["microglia"]["per_donor_counts"] == truth["B"]["mg_per_donor"]


def test_B_donor_agreement_not_checkable_is_not_a_pass(fixtures):
    d, _ = fixtures
    r = run_v2(d, "B")
    dl = r["donor_label_agreement_on_shared"]
    assert dl["checked"] is False
    assert dl["consistent"] is None
    assert r["qualification"]["QUALIFIED_FOR_PAIRED_USE"] is False


# ------------------------------------------------- composite diagnostic (B, C)

def test_composite_diagnostic_is_computed_but_not_authoritative(fixtures):
    d, truth = fixtures
    for name in ("B", "C"):
        r = run_v2(d, name)
        cd = r["pairing"]["composite_diagnostic"]
        assert cd["computable"] is True
        assert cd["AUTHORITATIVE"] is False
        assert cd["would_resolve"] is True
        assert r["pairing"]["basis_used_for_counts"] == "NONE__UNRESOLVED"
        assert r["microglia"]["n_total_paired_with_atac"] is None


def test_composite_opt_in_recovers_truth_but_never_qualifies(fixtures):
    """The operator may assert the convention. Doing so must recover the planted
    number AND leave the qualification flags false, because an assertion is not
    an observation."""
    d, truth = fixtures
    for name, key in (("B", "mg_paired"), ("C", "mg_paired")):
        r = run_v2(d, name, "--trust-composite-pairing",
                   out=d / f"{name}_composite.json")
        assert r["microglia"]["n_total_paired_with_atac"] == truth[name][key]
        assert r["pairing"]["basis_used_for_counts"] == \
            "COMPOSITE_SAMPLE_BARCODE__OPERATOR_ASSERTED"
        assert r["qualification"]["pairing_resolved"] is False
        assert r["qualification"]["QUALIFIED_FOR_PAIRED_USE"] is False
        assert "operator_assertion" in r["pairing"]


def test_C_realistic_10x_barcodes_and_cross_sample_collision(fixtures):
    """C reuses the SAME raw barcodes across two samples. Barcode-only matching
    would fuse nuclei from different donors; qualifying by sample must not."""
    d, truth = fixtures
    probe = _load(V2, "h5ad_schema_probe_v2")
    assert probe.raw_barcode("NABEC_1234_AAACGAAAGCAGAGCT-1") == "AAACGAAAGCAGAGCT-1"
    assert probe.raw_barcode("AAACGAAAGCAGAGCT-1_NABEC_1234") == "AAACGAAAGCAGAGCT-1"
    r = run_v2(d, "C", "--trust-composite-pairing", out=d / "C_composite.json")
    cd = r["pairing"]["composite_diagnostic"]
    assert cd["n_shared_composite"] == truth["C"]["shared_composite"]
    perp = r["microglia"]["per_donor_paired_counts"]
    assert sum(perp.values()) == truth["C"]["mg_paired"]
    # Both samples must be present: a collision-fused match would pile onto one.
    assert set(perp) == set(truth["C"]["mg_per_donor"])
    assert all(v > 0 for v in perp.values())


def test_C_spelled_out_microglia_label_matches(fixtures):
    d, truth = fixtures
    r = run_v2(d, "C")
    assert r["microglia_labels_matched"] == ["Microglia"]
    assert r["microglia"]["n_total_rna"] == truth["C"]["mg_total"]


# ---------------------------------------------------------- schema / slots

def test_slot_classification_counts_vs_transformed(fixtures):
    """A: X is log-normalised, layers/counts is integer. B: X is integer."""
    d, _ = fixtures
    a = run_v2(d, "A")
    assert a["rna"]["matrix_slots"]["X"]["verdict"] == "NONINTEGER_LOG_LIKE"
    assert a["rna"]["matrix_slots"]["layers/counts"]["verdict"] == "COUNT_LIKE_INTEGER_MATRIX"
    assert a["rna"]["count_like_slots"] == ["layers/counts"]
    b = run_v2(d, "B")
    assert b["rna"]["matrix_slots"]["X"]["verdict"] == "COUNT_LIKE_INTEGER_MATRIX"


def test_slot_language_does_not_claim_raw_provenance(fixtures):
    """The verdict must not assert 'raw' or 'CellBender'; values alone cannot
    establish that."""
    d, _ = fixtures
    a = run_v2(d, "A")
    for slot in a["rna"]["matrix_slots"].values():
        assert "RAW" not in slot["verdict"].upper()
        assert "does not establish raw" in slot["verdict_note"]


def test_modern_categorical_layout_is_read(fixtures):
    """anndata >= 0.8 writes categoricals as a group with categories+codes. The
    donor, celltype and cohort columns are all categorical in the fixtures."""
    import h5py
    d, _ = fixtures
    probe = _load(V2, "h5ad_schema_probe_v2")
    with h5py.File(d / "A_rna.h5ad", "r") as f:
        node = f["obs"]["cell_type"]
        assert isinstance(node, h5py.Group)
        assert "categories" in node and "codes" in node
        vals = probe.read_column(f["obs"], "cell_type")
    assert set(map(str, vals)) >= {"MG", "ExN", "Oligo"}
    assert len(vals) == 1450


def test_receipt_survives_json_round_trip(fixtures):
    """v1.0 used float quantile keys, so receipt['per_donor_quantiles'][0.5]
    worked in memory and raised KeyError after reloading from disk."""
    d, _ = fixtures
    r = run_v2(d, "A")
    q = r["microglia"]["per_donor_quantiles"]
    assert "0.5" in q and all(isinstance(k, str) for k in q)


# ------------------------------------------------------- v1.0 regression

def test_v1_reproduces_the_original_defect(fixtures):
    """Runs the PRESERVED v1.0 file and shows the defect is real, so the
    successor is justified by evidence rather than by assertion. If this ever
    stops failing, v1.0 was not the file we thought it was."""
    d, truth = fixtures
    out = d / "B_receipt_v1.json"
    proc = subprocess.run(
        [sys.executable, str(V1), "--rna", str(d / "B_rna.h5ad"),
         "--atac", str(d / "B_atac.h5ad"), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-800:]
    v1 = json.loads(out.read_text())
    assert v1["microglia"]["n_total_paired_with_atac"] == 0
    assert truth["B"]["mg_paired"] == 35
    v2 = run_v2(d, "B")
    assert v2["microglia"]["n_total_paired_with_atac"] is None


# ------------------------------------------------------- positive controls

def test_guard_can_actually_fail(fixtures):
    """A qualification flag that is always False proves nothing. Construct the
    one state that SHOULD qualify -- exact namespace, no donor mismatch -- and
    confirm the probe says so."""
    pytest.importorskip("anndata")
    import anndata as ad
    d, _ = fixtures
    mk = _load(MAKE, "make_h5ad_fixtures_v2")
    clean = d / "clean"
    clean.mkdir(exist_ok=True)
    # Same generator, mismatch disabled, exact namespace kept.
    mk.rng = __import__("numpy").random.default_rng(7)
    mk.build("K", [300, 300], [50, 40], raw_in_x=True, atac_sep="_",
             mismatch=False, outdir=str(clean))
    r = run_v2(clean, "K")
    assert r["pairing"]["state"] == "PAIRING_RESOLVED_EXACT"
    assert r["donor_label_agreement_on_shared"]["n_mismatch"] == 0
    assert r["qualification"]["QUALIFIED_FOR_PAIRED_USE"] is True
    assert r["probe_status"] == "PROBE_OK"


def test_threshold_is_predeclared_not_data_dependent():
    probe = _load(V2, "h5ad_schema_probe_v2")
    assert probe.HIGH_OVERLAP_MIN == 0.50
    assert probe.TOOL_VERSION == "2.0.0"
    assert probe.SUPERSEDES == "1.0.0"
