import pytest

from sea_ad_jepa.v5.group_split_integrity_v1 import audit_group_split_integrity_v1


def test_donor_disjoint_split_passes_and_reports_other_group_overlap():
    out=audit_group_split_integrity_v1(
        row_ids=["r0","r1","r2","r3","r4","r5"],
        donor_ids=["d0","d0","d1","d1","d2","d2"],
        source_ids=["s0","s0","s0","s1","s1","s1"],
        operator_ids=["o0","o0","o1","o1","o0","o0"],
        split_labels=["train","train","validation","validation","test","test"],
        split_plan_sha256="a"*64,
        parent_sha256="b"*64,
    )
    assert out["donor_overlap_pairs"] == []
    assert out["rows_by_split"] == {"test":2,"train":2,"validation":2}
    assert out["source_overlap_pairs"]
    assert out["operator_overlap_pairs"]
    assert out["authority_classification"] == "SPLIT_INTEGRITY_MECHANICS_ONLY__NOT_GENERALIZATION_PROOF"
    assert out["training_authorized"] is False


def test_donor_crossing_partitions_fails_closed():
    with pytest.raises(RuntimeError,match="DONOR_LEAKAGE"):
        audit_group_split_integrity_v1(
            row_ids=["r0","r1","r2","r3"],
            donor_ids=["d0","d0","d1","d2"],
            source_ids=["s0"]*4,
            operator_ids=["o0"]*4,
            split_labels=["train","test","validation","test"],
            split_plan_sha256="a"*64,parent_sha256="b"*64,
        )


def test_duplicate_rows_or_missing_required_partition_fail_closed():
    common=dict(
        donor_ids=["d0","d0","d1","d1"],source_ids=["s0"]*4,operator_ids=["o0"]*4,
        split_plan_sha256="a"*64,parent_sha256="b"*64,
    )
    with pytest.raises(ValueError,match="row_ids"):
        audit_group_split_integrity_v1(row_ids=["r0","r0","r2","r3"],split_labels=["train","train","validation","test"],**common)
    with pytest.raises(RuntimeError,match="MISSING_SPLIT"):
        audit_group_split_integrity_v1(row_ids=["r0","r1","r2","r3"],split_labels=["train","train","test","test"],**common)


def test_unknown_split_label_is_rejected():
    with pytest.raises(ValueError,match="split_labels"):
        audit_group_split_integrity_v1(
            row_ids=["r0","r1","r2","r3"], donor_ids=["d0","d0","d1","d1"],
            source_ids=["s0"]*4,operator_ids=["o0"]*4,
            split_labels=["train","train","validation","holdout"],
            split_plan_sha256="a"*64,parent_sha256="b"*64,
        )


def test_outcome_feedback_and_authority_escalation_are_forbidden():
    common=dict(
        row_ids=["r0","r1","r2","r3","r4","r5"],
        donor_ids=["d0","d0","d1","d1","d2","d2"],source_ids=["s0"]*6,operator_ids=["o0"]*6,
        split_labels=["train","train","validation","validation","test","test"],
        split_plan_sha256="a"*64,parent_sha256="b"*64,
    )
    for field in ("d_shared_outcomes_used","protected_data_used","pathology_used","training_authorized"):
        with pytest.raises(RuntimeError,match="STOP_SPLIT_INTEGRITY_FORBIDDEN"):
            audit_group_split_integrity_v1(**common,**{field:True})
