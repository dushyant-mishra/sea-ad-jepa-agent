"""Controls for the SEA-AD spatial pathology firewall (Lane R4, 2026-09-28).

The firewall's job is to make "do not read protected pathology" executable.
A firewall that cannot fail is worthless, so this file carries three controls:

* POSITIVE  -- the filter fires on the *real* SEA-AD column names, one column
               at a time, so a single broad token cannot carry the whole suite.
* NEGATIVE  -- the filter does not fire on identity / annotation / geometry
               columns, i.e. it is not a trivial "refuse everything".
* MUTATION  -- with the 'braak' rule deleted the positive control *fails*,
               proving the positive control is load-bearing and not a
               tautology; and the loader still refuses by deny-by-default,
               proving the defence is layered.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

_MOD_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "v5"
    / "seaad_spatial_pathology_firewall_v1.py"
)
_spec = importlib.util.spec_from_file_location("seaad_spatial_firewall", _MOD_PATH)
fw = importlib.util.module_from_spec(_spec)
sys.modules["seaad_spatial_firewall"] = fw
assert _spec.loader is not None
_spec.loader.exec_module(fw)


# Verbatim column names observed in the public SEA-AD spatial objects
# SEAAD_MTG_MERFISH.2024-12-11.h5ad and CaH_Xenium.2026-01-07.h5ad.
REAL_PROTECTED_COLUMNS = [
    "Braak",
    "CERAD score",
    "Thal",
    "Overall AD neuropathological Change",
    "Cognitive Status",
    "Last MMSE Score",
    "Last CASI Score",
    "Last MOCA Score",
    "Interval from last MMSE in months",
    "Interval from last CASI in months",
    "Interval from last MOCA in months",
    "LATE",
    "Highest Lewy Body Disease",
    "Overall CAA Score",
    "Arteriolosclerosis",
    "Atherosclerosis",
    "Total Microinfarcts (not observed grossly)",
    "Total microinfarcts in screening sections",
    "Continuous Pseudo-progression Score",
    "APOE4 Status",
    "APOE Genotype",
    "Neurotypical reference",
    "Primary Study Name",
    "Secondary Study Name",
]

REAL_DEMOGRAPHIC_COLUMNS = [
    "Age at Death",
    "Sex",
    "Gender",
    "Hispanic",
    "Years of education",
    "Highest level of education",
    "PMI",
    "Brain pH",
    "Fresh Brain Weight",
    "Race (choice=Asian)",
    "specify other race",
]

REAL_ALLOWED_COLUMNS = [
    "Donor ID",
    "Specimen Barcode",
    "Specimen_ID",
    "LIMS2_Barcode",
    "Merscope",
    "Section",
    "Brain Region",
    "region",
    "Cell ID",
    "cell_id",
    "Class",
    "Subclass",
    "Supertype",
    "Supertype confidence",
    "Class_scANVI",
    "Subclass_scANVI",
    "Supertype_scANVI",
    "Subclass_conf_scANVI",
    "cell_labels",
    "Neighborhood",
    "Cell volume",
    "cell_area",
    "nucleus_area",
    "nucleus_count",
    "Genes detected",
    "Number of spots",
    "total_counts",
    "transcript_counts",
    "control_probe_counts",
    "segmentation_method",
    "z_level",
    "Layer annotation",
    "Depth from pia",
    "Normalized depth from pia",
]


# ----------------------------------------------------------------- POSITIVE
@pytest.mark.parametrize("col", REAL_PROTECTED_COLUMNS)
def test_positive_control_filter_fires_on_real_protected_columns(col):
    """Every real SEA-AD pathology/cognition column classifies PROTECTED."""
    verdict, hits = fw.classify_column(col)
    assert verdict == "PROTECTED", f"{col!r} classified {verdict}, expected PROTECTED"
    assert hits, f"{col!r} matched no protected pattern"


def test_positive_control_frame_containing_braak_is_refused():
    """The mandated control: a frame carrying `Braak` must be refused."""
    with pytest.raises(fw.PathologyFirewallViolation) as exc:
        fw.assert_frame_is_clean(["Donor ID", "Subclass", "Braak"])
    assert "Braak" in str(exc.value)


def test_positive_control_loader_refuses_braak_before_opening_file():
    """The loader refuses a protected request without touching the file."""
    with pytest.raises(fw.PathologyFirewallViolation):
        fw.load_allowlisted_obs("/nonexistent/path/does_not_exist.h5ad", ["Braak"])


@pytest.mark.parametrize("col", REAL_DEMOGRAPHIC_COLUMNS)
def test_demographic_columns_are_refused_but_classified_separately(col):
    """Demographics are refused, but not mislabelled as protected pathology."""
    verdict, _ = fw.classify_column(col)
    assert verdict == "DENY_NOT_NEEDED", f"{col!r} classified {verdict}"


def test_unknown_column_is_refused_by_default():
    """Deny-by-default: a column matching no rule is refused, not admitted."""
    verdict, _ = fw.classify_column("Some Future Column Nobody Anticipated")
    assert verdict == "REFUSED_UNKNOWN"
    with pytest.raises(fw.PathologyFirewallViolation):
        fw.assert_frame_is_clean(["Some Future Column Nobody Anticipated"])


def test_protected_wins_over_allow_when_both_match():
    """A column matching both an allow and a protected token is refused."""
    verdict, _ = fw.classify_column("Braak region")
    assert verdict == "PROTECTED"


# ----------------------------------------------------------------- NEGATIVE
@pytest.mark.parametrize("col", REAL_ALLOWED_COLUMNS)
def test_negative_control_filter_does_not_fire_on_identity_columns(col):
    """Identity / annotation / geometry columns are admitted."""
    verdict, _ = fw.classify_column(col)
    assert verdict == "ALLOW", f"{col!r} classified {verdict}, expected ALLOW"


def test_negative_control_clean_frame_passes():
    """A frame of only allow-listed columns raises nothing."""
    fw.assert_frame_is_clean(["Donor ID", "Subclass", "Section", "cell_area"])


def test_negative_control_filter_is_not_refuse_everything():
    """Guard against a degenerate filter that refuses every input."""
    screened = fw.screen_columns(REAL_ALLOWED_COLUMNS)
    assert screened["ALLOW"], "filter admitted nothing; it is degenerate"
    assert not screened["PROTECTED"]
    assert not screened["REFUSED_UNKNOWN"]


# ----------------------------------------------------------------- MUTATION
def test_mutation_control_positive_control_fails_when_braak_rule_deleted(monkeypatch):
    """Delete the 'braak' rule: the positive control must then fail.

    This proves the positive control is load-bearing.  It also shows the
    defence is layered: with the specific rule gone the column is no longer
    labelled PROTECTED, but deny-by-default still refuses the read, so the
    loader does not silently start returning Braak values.
    """
    mutated = tuple(p for p in fw.PROTECTED_PATTERNS if p != "braak")
    assert len(mutated) == len(fw.PROTECTED_PATTERNS) - 1, "mutation was a no-op"
    monkeypatch.setattr(fw, "PROTECTED_PATTERNS", mutated)

    # The specific positive-control assertion now fails -> the test can fail.
    verdict, _ = fw.classify_column("Braak")
    assert verdict != "PROTECTED", (
        "mutation had no effect; the positive control cannot fail and is a tautology"
    )

    # Layered defence: still refused, because unknown columns are refused.
    assert verdict == "REFUSED_UNKNOWN"
    with pytest.raises(fw.PathologyFirewallViolation):
        fw.assert_frame_is_clean(["Braak"])


def test_mutation_control_negative_control_fails_when_allow_list_emptied(monkeypatch):
    """Empty the allow-list: the negative control must then fail."""
    monkeypatch.setattr(fw, "ALLOW_PATTERNS", ())
    verdict, _ = fw.classify_column("Donor ID")
    assert verdict != "ALLOW", "mutation had no effect on the negative control"
    with pytest.raises(fw.PathologyFirewallViolation):
        fw.assert_frame_is_clean(["Donor ID"])
