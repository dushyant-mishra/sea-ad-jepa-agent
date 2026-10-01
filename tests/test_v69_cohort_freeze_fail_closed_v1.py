"""Degenerate-input tests for the V69 GSE214979 cohort-freeze contract.

Each test drives the producer into a distinct failure state and proves it refuses
to emit PASS. The happy-path test proves PASS is reachable, so no assertion here
is a check that cannot fail.

The order-sensitivity test is the important one: downstream matrices index cells
positionally, so a digest that only certifies *membership* would silently accept a
permuted cell dictionary.
"""
from __future__ import annotations

import gzip
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / \
    "audit_gse214979_metadata_and_freeze_cohort_v1.py"
_spec = importlib.util.spec_from_file_location("v69_cohort", _MOD)
coh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(coh)


def _frame(n_per_donor=4, donors=("1224", "1230", "1238", "4482", "3329"),
           micro_per_donor=2):
    rows = []
    for d in donors:
        repo = "UCI" if d in ("1224", "1230", "1238") else "HBSFRC"
        for i in range(n_per_donor):
            is_mic = i < micro_per_donor
            rows.append({
                "Unnamed: 0": f"BC{d}_{i}",
                "id": d,
                "predicted.id": "Microglia" if is_mic else "Astrocytes",
                "subs": "Mic_0" if is_mic else "Ast_0",
                "Repository": repo,
                "Status": "Ctrl",
                "Braak": 3.0,
                "Diagnosis": "Unaffected",
                "APOE_Status": "E3/E3",
            })
    return pd.DataFrame(rows)


def _write(df, tmp_path, name="meta.csv.gz"):
    p = tmp_path / name
    with gzip.open(p, "wt", newline="") as fh:
        df.to_csv(fh, index=False)
    return p


def test_pass_is_reachable_and_counts_are_exact(tmp_path):
    df = _frame()
    r = coh.audit(_write(df, tmp_path), tmp_path / "out")
    assert r["status"] == "PASS__COHORT_FROZEN_PATHOLOGY_BLIND"
    assert r["populations"]["ALL_MICROGLIA"]["n_cells"] == 10
    assert r["populations"]["ALL_MICROGLIA"]["n_donors"] == 5
    # three excluded donors x 2 microglia each are removed
    assert r["populations"]["DEV_NO_MORABITO_OVERLAP"]["n_cells"] == 4
    assert r["populations"]["DEV_NO_MORABITO_OVERLAP"]["n_donors"] == 2


def test_forbidden_columns_are_named_and_not_used(tmp_path):
    r = coh.audit(_write(_frame(), tmp_path), tmp_path / "out")
    named = r["pathology_blindness"]["forbidden_columns_enumerated_by_name_only"]
    assert set(named) == {"APOE_Status", "Braak", "Diagnosis", "Status"}
    assert r["pathology_blindness"]["forbidden_columns_read_into_selection"] is False


def test_pathology_values_cannot_change_the_selection(tmp_path):
    """Positive control for blindness: flipping every pathology value must not move a cell."""
    a = _frame()
    b = a.copy()
    b["Status"] = "AD"
    b["Braak"] = 6.0
    b["Diagnosis"] = "Alzheimer's"
    b["APOE_Status"] = "E4/E4"
    ra = coh.audit(_write(a, tmp_path, "a.csv.gz"), tmp_path / "oa")
    rb = coh.audit(_write(b, tmp_path, "b.csv.gz"), tmp_path / "ob")
    for pop in ("ALL_MICROGLIA", "DEV_NO_MORABITO_OVERLAP"):
        assert (ra["populations"][pop]["ordered_barcode_digest"]
                == rb["populations"][pop]["ordered_barcode_digest"])


def test_ordered_digest_detects_permutation_that_membership_cannot(tmp_path):
    """A reordered cell dictionary must change the ordered digest but not the unordered one."""
    df = _frame()
    ra = coh.audit(_write(df, tmp_path, "a.csv.gz"), tmp_path / "oa")
    rb = coh.audit(_write(df.iloc[::-1].reset_index(drop=True), tmp_path, "b.csv.gz"),
                   tmp_path / "ob")
    pa = ra["populations"]["ALL_MICROGLIA"]
    pb = rb["populations"]["ALL_MICROGLIA"]
    assert pa["unordered_barcode_digest"] == pb["unordered_barcode_digest"], \
        "same members, so the membership digest must agree"
    assert pa["ordered_barcode_digest"] != pb["ordered_barcode_digest"], \
        "order changed, so the order-pinning digest MUST disagree"


def test_ambiguous_published_annotation_fails_closed(tmp_path):
    df = _frame()
    # one nucleus labelled Microglia at the coarse level but not at the subcluster level
    df.loc[0, "subs"] = "Ast_0"
    r = coh.audit(_write(df, tmp_path), tmp_path / "out")
    assert r["status"] == "FAIL__PUBLISHED_MICROGLIA_ANNOTATION_AMBIGUOUS"
    assert "populations" not in r


def test_duplicate_barcodes_fail_closed(tmp_path):
    df = _frame()
    df.loc[1, "Unnamed: 0"] = df.loc[0, "Unnamed: 0"]
    r = coh.audit(_write(df, tmp_path), tmp_path / "out")
    assert r["status"] == "FAIL__DUPLICATE_BARCODES_IN_METADATA"


def test_absent_declared_column_fails_closed(tmp_path):
    df = _frame().drop(columns=["subs"])
    r = coh.audit(_write(df, tmp_path), tmp_path / "out")
    assert r["status"] == "FAIL__DECLARED_COLUMNS_ABSENT"
    assert r["missing_columns"] == ["subs"]


def test_exclusion_structural_claim_can_report_non_coincidence(tmp_path):
    """The repository-coincidence claim must be falsifiable, not always true."""
    df = _frame()
    # add a fourth UCI donor that is NOT in the exclusion set
    extra = _frame(donors=("9999",), micro_per_donor=2)
    extra["Repository"] = "UCI"
    r = coh.audit(_write(pd.concat([df, extra], ignore_index=True), tmp_path),
                  tmp_path / "out")
    assert r["prospective_donor_exclusion"]["structural_basis"]["verified_claim"] == \
        "EXCLUSION_SET_DOES_NOT_EQUAL_A_SINGLE_SOURCE_REPOSITORY"


def test_absent_excluded_donor_is_reported_not_assumed(tmp_path):
    df = _frame(donors=("4482", "3329"))
    r = coh.audit(_write(df, tmp_path), tmp_path / "out")
    assert r["prospective_donor_exclusion"]["all_present_in_this_cohort"] == []
    assert r["prospective_donor_exclusion"]["excluded_donors"] == ["1224", "1230", "1238"]
