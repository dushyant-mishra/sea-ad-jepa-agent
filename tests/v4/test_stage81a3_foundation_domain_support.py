from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.foundation_domain_support import descriptor_distance, nearest_domains


REPORT = ROOT / "results/v4/stage81a3_foundation_heterogeneity_reality_audit.json"


def descriptor(mask: str, technology: str, tissue: str, shift: float = 0.0) -> dict[str, object]:
    return {
        "mask_hash": mask, "technology": technology, "tissue": tissue,
        "library_median": 1000.0 + shift, "detected_median": 500.0 + shift,
        "zero_fraction_median": 0.5, "nonzero_median": 1.0,
    }


def test_identical_descriptor_has_zero_distance() -> None:
    assert descriptor_distance(descriptor("a", "sn", "brain"), descriptor("a", "sn", "brain"))["total_distance"] == 0.0


def test_mask_difference_is_explicit() -> None:
    result = descriptor_distance(descriptor("a", "sn", "brain"), descriptor("b", "sn", "brain"))
    assert result["measurement_mask_distance"] == 1.0


def test_technology_and_tissue_matches_are_reported() -> None:
    result = descriptor_distance(descriptor("a", "sn", "brain"), descriptor("a", "sc", "blood"))
    assert result["technology_match"] is False
    assert result["tissue_match"] is False


def test_nearest_domain_excludes_self() -> None:
    rows = nearest_domains({"a": descriptor("a", "sn", "brain"), "b": descriptor("a", "sn", "brain", 1), "c": descriptor("b", "sc", "blood")})
    assert all(row["matrix_id"] != row["nearest_matrix_id"] for row in rows)


def test_generated_report_contract_when_present() -> None:
    if not REPORT.exists():
        return
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["foundation_inventory"]["datasets"] == 13
    assert report["foundation_inventory"]["matrices"] == 36
    assert report["measurement_support"]["all_genes_supported"] is True
    assert report["safety"]["neural_optimizer_updates"] == 0


def test_generated_outputs_contain_no_cell_level_rna_when_present() -> None:
    if not REPORT.exists():
        return
    forbidden = {"expression", "raw_counts", "cell_id"}
    for path in ROOT.glob("results/v4/stage81a3_foundation_*.csv"):
        columns = set(pd.read_csv(path, nrows=0).columns)
        assert not forbidden & columns


def test_generated_reference_edges_never_fabricate_direct_teacher_when_present() -> None:
    path = ROOT / "results/v4/stage81a3_foundation_reference_graph.csv"
    if not path.exists():
        return
    frame = pd.read_csv(path)
    if len(frame):
        assert not frame.literal_teacher_allowed.astype(str).str.lower().eq("true").any()


def test_generated_pca_is_exactly_160d_when_present() -> None:
    if not REPORT.exists():
        return
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["real_diagnostic_pca160"]["dimensions"] == 160


def test_generated_forward_smoke_is_zero_update_when_present() -> None:
    if not REPORT.exists():
        return
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    smoke = report["real_forward_mechanics"]
    assert smoke["optimizer_steps"] == 0
    assert smoke["ema_updates"] == 0
    assert smoke["finite"] is True


def test_domain_imprint_forces_qualification_when_present() -> None:
    if not REPORT.exists():
        return
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    classifiers = report["real_diagnostic_pca160"]["predictability"]["pca160"].values()
    if any(item.get("balanced_accuracy", 0.0) > 0.75 for item in classifiers):
        assert report["classifications"]["primary"].startswith("B.")
        assert report["classifications"]["accountable_160d_state"] == "PLAUSIBLE-BUT-DOMAIN-QUALIFICATION-NEEDED"
