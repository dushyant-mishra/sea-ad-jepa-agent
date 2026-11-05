"""Actual PR547 FIT-only data stress tests. This cannot adjudicate any C."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path

import numpy as np
import pytest

from scripts.v79 import audit_synth2048_source_depth_c3_feasibility_v1 as a


@pytest.fixture(scope="module")
def material():
    path = os.environ.get("JEPA_SYNTH2048_DEV_ZIP")
    if not path:
        pytest.skip("exact verified original PR547 archive required")
    return a.load_verified_zip(Path(path))


def test_all_five_actual_fit_members_and_frozen_identity(material):
    receipt, student, roster, extra = material
    assert receipt["world_identity_sha256"] == (
        "30073c84b32f57ef65cbb5749e6a7ebdf79d95ad8837d25c9898cbd0e35c1eb5"
    )
    assert receipt["observed_csr_sha256"] == (
        "818047eb8b959fe87d51926e4bcd5a51e889dafb702eaa3ae576aabd542bb14f"
    )
    assert receipt["all_six_candidate_recoverability"] == "UNASSESSED"
    assert set(student) == {
        "rna_base_counts", "rna_base_support", "rna_base_address_ids",
        "projected_base_depth",
    }
    assert set(roster) == {
        "donor_id", "synthetic_source", "split", "rna_entity_id",
        "atac_same_entity_id", "atac_separate_entity_id", "perturbation_arm",
    }
    assert set(extra) == {"teacher_support"}


def test_shared_c2_view_roles_are_real_independent_measured_addresses(material):
    receipt, student, _, extra = material
    views, panels, lookup = a.validate_view_roles(receipt, student, extra["teacher_support"])
    assert len(views) == 3
    assert all(len(v) == 512 for v in views)
    assert len(set(np.concatenate(views).tolist())) == 1536
    assert all(np.all(student["rna_base_support"][:, lookup[v]]) for v in views)


def test_old_48_gene_c3_source_eligibility_does_not_transfer_to_2048(material):
    receipt, student, roster, extra = material
    report = a.summarize_verified_fit(receipt, student, roster, extra)
    assert report["C3_learned_context_above_wrong_query"] == "UNASSESSED"
    assert report["C2_relational_correct_cell_biology"] == "UNASSESSED"
    assert [report["per_source"][s]["C3_query_and_other8_structurally_estimable_cells"]
            for s in a.SOURCES] == [480, 480, 480]
    assert all(report["per_source"][s]["donors"] == 12 for s in a.SOURCES)
    assert report["all_three_C2_512_address_views_present"] is True
    assert report["four_C3_query_plus_other8_panels_present"] is True


def test_no_q_or_whole_library_depth_in_student(material):
    _, student, _, _ = material
    assert student["rna_base_counts"].shape == (1440, 2044)
    assert not set(a.EXPECTED_Q) & set(student["rna_base_address_ids"].tolist())
    assert np.array_equal(
        student["projected_base_depth"],
        student["rna_base_counts"].sum(axis=1, dtype=np.int64),
    )


def test_source_depth_and_detection_are_reported_but_never_a_pass(material):
    receipt, student, roster, extra = material
    report = a.summarize_verified_fit(receipt, student, roster, extra)
    medians = [
        report["per_source"][s]["median_student_base_depth"]
        for s in a.SOURCES
    ]
    assert all(v > 0 and np.isfinite(v) for v in medians)
    assert report["source_depth_median_max_to_min_ratio"] == max(medians) / min(medians)
    assert set(report["per_source"]) == set(a.SOURCES)
    assert report["source_and_donor_not_independently_randomized"] is True
    assert report["C1_C2_C3_C4_C5_C6_status"] == "ALL_UNASSESSED"
    assert report["training_or_student_scoring_executed"] is False
    assert report["selection_or_threshold_freeze_produced"] is False


def test_structural_measured_zero_not_confused_with_absence(material):
    _, student, _, _ = material
    support = student["rna_base_support"]
    counts = student["rna_base_counts"]
    assert np.any((counts == 0) & support)
    assert np.any(~support)
    assert not np.any(counts[~support])


def test_adversarial_query_ids_and_panel_alias_refused(material):
    receipt, student, _, extra = material
    forged = deepcopy(receipt)
    forged["frozen_preoutcome_address_roles"]["query_addresses"][0] += 1
    with pytest.raises(a.AuditRefusal, match="QUERY_IDS_CHANGED"):
        a.validate_view_roles(forged, student, extra["teacher_support"])
    forged = deepcopy(receipt)
    forged["frozen_preoutcome_address_roles"]["query_other8_panels"][0][0] = \
        forged["frozen_preoutcome_address_roles"]["relational_views_3x512"][0][0]
    with pytest.raises(a.AuditRefusal, match="PANEL_ALIAS"):
        a.validate_view_roles(forged, student, extra["teacher_support"])


def test_shifting_2044_address_ids_to_zero_based_refused(material):
    receipt, student, _, extra = material
    forged = dict(student)
    forged["rna_base_address_ids"] = np.arange(2044, dtype=np.int32)
    with pytest.raises(a.AuditRefusal, match="GENE_IDS_SHIFTED_OR_QUERY_VISIBLE"):
        a.validate_view_roles(receipt, forged, extra["teacher_support"])


def test_forged_physical_depth_and_unmeasured_counts_refused(material):
    receipt, student, _, extra = material
    forged = dict(student)
    forged["projected_base_depth"] = student["projected_base_depth"].copy()
    forged["projected_base_depth"][0] += 10
    with pytest.raises(a.AuditRefusal, match="BASE_DEPTH_LEAK_OR_MISMATCH"):
        a.validate_view_roles(receipt, forged, extra["teacher_support"])
    forged = dict(student)
    forged["rna_base_counts"] = student["rna_base_counts"].copy()
    r, c = np.argwhere(~student["rna_base_support"])[0]
    forged["rna_base_counts"][r, c] = 1
    forged["projected_base_depth"] = forged["rna_base_counts"].sum(axis=1, dtype=np.int64)
    with pytest.raises(a.AuditRefusal, match="STRUCTURAL_ABSENCE_AS_DETECTION"):
        a.validate_view_roles(receipt, forged, extra["teacher_support"])


def test_cross_split_donor_and_source_forgery_refused(material):
    receipt, student, roster, extra = material
    forged = dict(roster)
    forged["split"] = roster["split"].copy()
    same = np.flatnonzero(roster["donor_id"] == roster["donor_id"][0])
    forged["split"][same[-1]] = "test" if forged["split"][same[-1]] != "test" else "train"
    with pytest.raises(a.AuditRefusal, match="DONOR_CROSSES_SPLIT_OR_SOURCE"):
        a.summarize_verified_fit(receipt, student, forged, extra)


def test_archive_byte_mutation_fails_closed(tmp_path, material):
    p = Path(os.environ["JEPA_SYNTH2048_DEV_ZIP"])
    value = bytearray(p.read_bytes())
    value[100] ^= 0x01
    altered = tmp_path / "tampered.zip"
    altered.write_bytes(value)
    with pytest.raises(a.AuditRefusal, match="FIT_SHA_CHANGED"):
        a.load_verified_zip(altered)


def test_report_does_not_overclaim_any_biology(material):
    receipt, student, roster, extra = material
    report = a.summarize_verified_fit(receipt, student, roster, extra)
    assert report["student_q_values_or_teacher_q_values_read"] is False
    assert report["controller_truth_or_sealed_v80_used"] is False
    assert report["training_or_student_scoring_executed"] is False
    assert report["authority"] == a.AUTHORITY
