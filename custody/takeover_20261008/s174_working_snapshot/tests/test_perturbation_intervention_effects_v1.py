"""Adversarial regression tests for the GSE301119 intervention-effect tables.

These check the committed measured receipts, not simulated data. They exist so a
later edit cannot quietly weaken the qualification: the counts are pinned to the
historical Stage81A1C-P object audit, the feature universes are pinned to the
nesting relation that resolved the blocker, and the biological direction of each
CRISPR modality is asserted.

A failure here means either the receipts changed or the underlying claim did.
Nothing here opens FULL104 protected outcomes, trains JEPA, or ranks compounds.
"""
from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "analysis/therapeutic_perturbation_etl/evidence"
G = EV / "gse301119"

#: From stage81a1c_p_seurat_object_audit.csv, not from the objects we produced.
HISTORICAL = {
    "CRISPRa": dict(features=19_162, cells=23_584, guides=1_090, targets=207,
                    nt_cells=2_117, nt_guides=99),
    "CRISPRi": dict(features=36_601, cells=28_466, guides=1_114, targets=207,
                    nt_cells=2_184, nt_guides=99),
}


def _rows(name: str) -> list[dict]:
    p = G / name
    if not p.is_file():
        pytest.fail(f"{p} missing; the intervention-effect receipt is not present")
    return list(csv.DictReader(p.open(encoding="utf-8")))


def _effects(tag: str) -> list[dict]:
    return _rows(f"{tag}_target_engagement.csv")


def _guides(tag: str) -> list[dict]:
    return _rows(f"{tag}_guide_donor_meta.csv")


def _measured_fc(tag: str) -> list[float]:
    return [float(r["target_log2fc_mean"]) for r in _effects(tag)
            if r["target_gene_measured"] == "TRUE"
            and r["target_log2fc_mean"] not in ("", "NA")]


# --------------------------------------------------------------------------- #
# identity: the receipts must still describe the audited objects
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tag", ["CRISPRa", "CRISPRi"])
def test_guide_and_donor_structure_matches_the_historical_object_audit(tag):
    rows = _guides(tag)
    exp = HISTORICAL[tag]
    assert len({r["guide_identity"] for r in rows}) == exp["guides"]
    assert sorted({r["donor"] for r in rows}) == ["D1", "D2"]
    assert sum(int(r["n_cells"]) for r in rows) == exp["cells"]
    nt = [r for r in rows if r["crispr"] == "NT"]
    assert len({r["guide_identity"] for r in nt}) == exp["nt_guides"]
    assert sum(int(r["n_cells"]) for r in nt) == exp["nt_cells"]


@pytest.mark.parametrize("tag", ["CRISPRa", "CRISPRi"])
def test_guide_donor_groups_are_unique_and_non_empty(tag):
    rows = _guides(tag)
    keys = [r["guide_donor"] for r in rows]
    assert len(keys) == len(set(keys)), "a guide x donor group is duplicated"
    assert all(int(r["n_cells"]) > 0 for r in rows)
    assert all(float(r["total_counts"]) > 0 for r in rows)


@pytest.mark.parametrize("tag", ["CRISPRa", "CRISPRi"])
def test_every_effect_row_has_controls_and_replication(tag):
    for r in _effects(tag):
        assert int(r["n_nt_guides"]) > 0, "an effect row has no non-targeting control"
        assert int(r["n_nt_cells"]) > 0
        assert int(r["n_guides"]) > 0
        assert int(r["n_cells"]) > 0
        assert r["donor"] in ("D1", "D2")


@pytest.mark.parametrize("tag", ["CRISPRa", "CRISPRi"])
def test_effects_cover_each_target_once_per_donor(tag):
    seen = [(r["target_gene"], r["donor"]) for r in _effects(tag)]
    assert len(seen) == len(set(seen)), "a target is reported twice for one donor"


# --------------------------------------------------------------------------- #
# the mask: an unmeasured gene is never a zero
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tag", ["CRISPRa", "CRISPRi"])
def test_unmeasured_target_genes_carry_no_fabricated_effect(tag):
    unmeasured = [r for r in _effects(tag) if r["target_gene_measured"] != "TRUE"]
    for r in unmeasured:
        assert r["target_log2fc_mean"] in ("", "NA"), (
            "an unmeasured target gene carries a numeric effect; an absent feature "
            "must never be read as zero expression")


def test_crispra_features_are_a_strict_subset_of_crispri():
    """The relation that resolved the feature blocker. If it ever stops holding,
    the shared measurement mask is no longer valid."""
    fa, fi = G / "CRISPRa_features.txt", G / "CRISPRi_features.txt"
    for f in (fa, fi):
        if not f.is_file():
            pytest.fail(f"{f} missing; the feature universes are committed evidence "
                        "and this relation is what resolved the blocker")
    A = set(fa.read_text(encoding="utf-8").split())
    I = set(fi.read_text(encoding="utf-8").split())
    assert len(A) == HISTORICAL["CRISPRa"]["features"]
    assert len(I) == HISTORICAL["CRISPRi"]["features"]
    assert A < I


# --------------------------------------------------------------------------- #
# biology: each modality must move its target in its own direction
# --------------------------------------------------------------------------- #

def test_crispri_represses_its_targets():
    fc = _measured_fc("CRISPRi")
    assert len(fc) > 400
    assert st.median(fc) < -0.5, "CRISPRi target engagement is not repressive"
    assert sum(1 for v in fc if v < 0) / len(fc) > 0.70


def test_crispra_induces_its_targets():
    fc = _measured_fc("CRISPRa")
    assert len(fc) > 400
    assert st.median(fc) > +1.0, "CRISPRa target engagement is not inductive"
    assert sum(1 for v in fc if v > 0) / len(fc) > 0.70


def test_the_two_modalities_oppose_each_other_in_sign():
    def by_target(tag):
        out = {}
        for r in _effects(tag):
            if r["target_gene_measured"] == "TRUE" and r["target_log2fc_mean"] not in ("", "NA"):
                out.setdefault(r["target_gene"], []).append(float(r["target_log2fc_mean"]))
        return {k: st.mean(v) for k, v in out.items()}
    i, a = by_target("CRISPRi"), by_target("CRISPRa")
    shared = sorted(set(i) & set(a))
    assert len(shared) > 150
    opposite = sum(1 for t in shared if i[t] < 0 < a[t])
    assert opposite / len(shared) > 0.70, (
        "CRISPRi and CRISPRa do not oppose each other; the modality assignment or "
        "the control definition is suspect")


@pytest.mark.parametrize("tag,expect_sign", [("CRISPRi", -1), ("CRISPRa", +1)])
def test_donors_replicate_each_other(tag, expect_sign):
    """D1 and D2 are independent donors, so the effect must transport."""
    by = {}
    for r in _effects(tag):
        if r["target_gene_measured"] == "TRUE" and r["target_log2fc_mean"] not in ("", "NA"):
            by.setdefault(r["target_gene"], {})[r["donor"]] = float(r["target_log2fc_mean"])
    both = {k: v for k, v in by.items() if len(v) == 2}
    assert len(both) > 150
    d1 = [v["D1"] for v in both.values()]
    d2 = [v["D2"] for v in both.values()]
    n, m1, m2 = len(d1), st.mean(d1), st.mean(d2)
    r = (sum((x - m1) * (y - m2) for x, y in zip(d1, d2)) / (n - 1)) / (st.stdev(d1) * st.stdev(d2))
    assert r > 0.4, f"donor reproducibility too low: r={r:.3f}"
    agree = sum(1 for v in both.values()
                if (v["D1"] * expect_sign > 0) and (v["D2"] * expect_sign > 0))
    assert agree / len(both) > 0.5


# --------------------------------------------------------------------------- #
# scope guards
# --------------------------------------------------------------------------- #

def test_modalities_are_never_merged_in_the_receipts():
    for tag in ("CRISPRa", "CRISPRi"):
        assays = {r["assay_object"] for r in _effects(tag)}
        assert assays == {tag}, "an effect table mixes CRISPR modalities"
        studies = {r["study"] for r in _effects(tag)}
        assert studies == {"GSE301119"}, "an effect table mixes studies"


def test_no_therapeutic_or_training_claim_is_encoded():
    text = (ROOT / "analysis/therapeutic_perturbation_etl"
            / "GSE301119_QUALIFICATION_AND_INTERVENTION_EFFECTS_20260923.md").read_text(encoding="utf-8")
    assert "JEPA_TRAINING=OFF" in text
    assert "THERAPEUTIC_RANKING=OFF" in text
    assert "PROTECTED_FULL104_OUTCOMES=UNOPENED" in text
