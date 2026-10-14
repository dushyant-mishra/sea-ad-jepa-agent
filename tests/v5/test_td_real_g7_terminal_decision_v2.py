from __future__ import annotations

import pytest
import scripts.v5.td_real_g7_terminal_decision_v2 as G


def _qual(ok=True):
    return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":ok}


def _ref(donors, margin=0.1, binding="1"*64):
    return {
        "schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,
        "orientation":G.ORIENTATION,"reference_kind":"U_REFIT","deciding_namespace_disjoint":True,
        "input_binding_sha256":binding,"reference_receipt_sha256":"2"*64,
        "donor_margins":{d:margin for d in donors},
    }


def _rows(n=8, displacement=0.02, added=1, binding="1"*64):
    return [{"donor_id":f"D{i}","terminal_displacement":displacement,
             "penultimate_supported_evidence":10,"full_supported_evidence":10+added,
             "added_supported_evidence":added,"input_binding_sha256":binding} for i in range(n)]


def test_convergence_pass_requires_change_within_qualified_margin_across_donors():
    rows=_rows()
    out=G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows]))
    assert out["status"]=="PASS"


def test_reference_must_bind_exact_deciding_realization():
    rows=_rows(binding="3"*64)
    with pytest.raises(G.G7DecisionError, match="input binding"):
        G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows], binding="1"*64))


def test_mixed_deciding_bindings_are_rejected():
    rows=_rows(); rows[-1]["input_binding_sha256"]="4"*64
    with pytest.raises(G.G7DecisionError, match="single deciding input"):
        G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows]))


def test_nominal_right_with_zero_added_support_is_not_evidence_of_convergence():
    rows=_rows(8, displacement=0.0, added=0)
    out=G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows]))
    assert out["status"]=="NOT_ESTIMABLE"
    assert out["reason"]=="NO_DONORS_WITH_ADDED_SUPPORTED_EVIDENCE"


def test_support_cannot_decrease_from_penultimate_to_full():
    rows=_rows(); rows[0]["full_supported_evidence"]=9
    with pytest.raises(G.G7DecisionError, match="support"):
        G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows]))


def test_large_terminal_change_fails_when_resolved():
    rows=_rows(8, displacement=0.5, added=1)
    out=G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows], margin=0.1))
    assert out["status"]=="FAIL"


def test_underpowered_donor_roster_is_not_estimable():
    rows=_rows(7)
    out=G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=_ref([r["donor_id"] for r in rows]))
    assert out["status"]=="NOT_ESTIMABLE"
    assert out["reason"]=="DONOR_SIGN_RESOLUTION_INSUFFICIENT"


def test_unqualified_known_truth_decision_cannot_fail_human_candidate():
    rows=_rows(8, displacement=0.5)
    out=G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(False), reference_artifact=_ref([r["donor_id"] for r in rows]))
    assert out["status"]=="NOT_ESTIMABLE"
    assert out["reason"]=="DECISION_KNOWN_TRUTH_NOT_QUALIFIED"


def test_reference_must_be_same_metric_disjoint_and_roster_bound():
    rows=_rows(); donors=[r["donor_id"] for r in rows]
    ref=_ref(donors); ref["metric"]="OTHER"
    with pytest.raises(G.G7DecisionError, match="metric"):
        G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=ref)
    ref=_ref(donors); ref["deciding_namespace_disjoint"]=False
    with pytest.raises(G.G7DecisionError, match="disjoint"):
        G.adjudicate_g7_terminal(rows=rows, decision_qualification=_qual(), reference_artifact=ref)


def test_known_truth_qualification_covers_converged_nonconverged_sparse_and_underpowered():
    q=G.qualify_known_truth_g7_decision()
    assert q["status"]==G.QUAL_PASS
    assert q["worlds"]=={
        "CONVERGED":"PASS","NONCONVERGED":"FAIL","NO_ADDED_SUPPORT":"NOT_ESTIMABLE","UNDERPOWERED":"NOT_ESTIMABLE"
    }
    assert all(v is False for v in q["authority"].values())
