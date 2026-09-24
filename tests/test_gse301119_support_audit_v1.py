"""Independent CPU tests on committed authenticated light metadata, never heavy RNA."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from sea_ad_jepa.perturbation.gse301119_support_audit_v1 import (
    SupportCensusError, census,
)

EVIDENCE = (
    Path(__file__).resolve().parents[1]
    / "analysis/therapeutic_perturbation_etl/evidence/gse301119_rawpb_v1"
)


def load_rows(modality):
    path = EVIDENCE / f"{modality}_guide_donor_meta.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_authenticated_lightweight_producer_metadata_support():
    a = census(EVIDENCE / "CRISPRa_guide_donor_meta.csv", modality="CRISPRa")
    i = census(EVIDENCE / "CRISPRi_guide_donor_meta.csv", modality="CRISPRi")
    assert a["input_sha256"].startswith("e13c3bb2")
    assert i["input_sha256"].startswith("ce96daa6")
    assert (a["guide_donor_rows"], a["cells_total"]) == (2098, 23584)
    assert (i["guide_donor_rows"], i["cells_total"]) == (2137, 28466)
    assert a["role_rows"] == {"Perturbed": 1906, "NT": 192}
    assert i["role_rows"] == {"Perturbed": 1949, "NT": 188}
    assert (a["both_donor_targets"], i["both_donor_targets"]) == (206, 206)
    assert (a["at_least_two_guides_per_donor"], i["at_least_two_guides_per_donor"]) == (205, 206)
    assert (a["at_least_three_guides_per_donor"], i["at_least_three_guides_per_donor"]) == (200, 203)
    assert a["nt_controls"] == {
        "D1": {"guides": 99, "cells": 1446},
        "D2": {"guides": 93, "cells": 671},
    }
    assert i["nt_controls"] == {
        "D1": {"guides": 98, "cells": 1425},
        "D2": {"guides": 90, "cells": 759},
    }
    assert a["de_results_executed"] is False
    assert i["physical_counts_reaggregated_here"] is False
    assert a["report_sha256"] == census(
        EVIDENCE / "CRISPRa_guide_donor_meta.csv", modality="CRISPRa",
    )["report_sha256"]


def test_guide_replication_limit_not_a_biological_donor_claim():
    a = census(EVIDENCE / "CRISPRa_guide_donor_meta.csv", modality="CRISPRa")
    i = census(EVIDENCE / "CRISPRi_guide_donor_meta.csv", modality="CRISPRi")
    hexa = {t["target"]: t for t in a["targets"]}["HEXA"]
    assert (hexa["guides_D1"], hexa["guides_D2"]) == (1, 1)
    assert (hexa["cells_D1"], hexa["cells_D2"]) == (21, 9)
    assert hexa["support_status"] == (
        "SINGLE_GUIDE_IN_AT_LEAST_ONE_DONOR_NO_WITHIN_DONOR_GUIDE_VARIANCE"
    )
    assert all(t["guides_D1"] >= 2 and t["guides_D2"] >= 2 for t in i["targets"])
    assert a["statistical_claim"] == (
        "DESCRIPTIVE_REPLICATION_SUPPORT_ONLY__N_BIOLOGICAL_DONORS_2"
    )


def test_source_file_mutation_rejected_before_metadata_interpretation(tmp_path):
    original = EVIDENCE / "CRISPRa_guide_donor_meta.csv"
    changed = tmp_path / original.name
    changed.write_bytes(original.read_bytes() + b"\n")
    with pytest.raises(SupportCensusError, match="SHA differs"):
        census(changed, modality="CRISPRa")


def test_swapped_donor_identity_preserving_counts_rejected_by_composite_key(tmp_path):
    rows = load_rows("CRISPRa")
    row = next(x for x in rows if x["crispr"] == "Perturbed" and x["donor"] == "D1")
    row["donor"] = "D2"
    p = tmp_path / "swapped.csv"
    write_rows(p, rows)
    with pytest.raises(SupportCensusError, match="composite identity drift"):
        census(p, modality="CRISPRa", test_fixture=True)


def test_same_guide_cannot_change_target_or_role_across_donors(tmp_path):
    rows = load_rows("CRISPRi")
    guide = next(x["guide_identity"] for x in rows if x["crispr"] == "Perturbed")
    mutated = [x for x in rows if x["guide_identity"] == guide and x["donor"] == "D2"]
    assert len(mutated) == 1
    mutated[0]["Gene_Targeted"] = "FAKE_SECOND_TARGET"
    p = tmp_path / "target_drift.csv"
    write_rows(p, rows)
    with pytest.raises(SupportCensusError, match="target/role changed"):
        census(p, modality="CRISPRi", test_fixture=True)


def test_duplicate_guide_donor_rejected(tmp_path):
    rows = load_rows("CRISPRa")
    rows.append(dict(rows[0]))
    p = tmp_path / "duplicate.csv"
    write_rows(p, rows)
    with pytest.raises(SupportCensusError, match="duplicated guide"):
        census(p, modality="CRISPRa", test_fixture=True)


def test_zero_cells_rejected_and_test_fixture_cannot_emit_physical_receipt(tmp_path):
    rows = load_rows("CRISPRi")
    rows[0]["n_cells"] = "0"
    p = tmp_path / "zero_cells.csv"
    write_rows(p, rows)
    with pytest.raises(SupportCensusError, match="zero/negative"):
        census(p, modality="CRISPRi", test_fixture=True)
    # A fixture on unmodified copied CSV may be interpreted for gate testing,
    # but its result MUST be labeled synthetic and omit physical report digest.
    rows[0]["n_cells"] = "7"
    write_rows(p, rows)
    fake = census(p, modality="CRISPRi", test_fixture=True)
    assert fake["evidence_role"].startswith("SYNTHETIC_TEST_ONLY")
    assert "report_sha256" not in fake
