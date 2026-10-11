import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "scripts/v5/td_donor_resampling_audit.py"
spec = importlib.util.spec_from_file_location("td_donor_resampling_audit", MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def cases():
    return [
        {"case_id":"s0h0","source":"HVS","donor_ids":["d1","d2","d3"]},
        {"case_id":"s0h1","source":"HVS","donor_ids":["d4","d5","d6"]},
        {"case_id":"s1h0","source":"HVS","donor_ids":["d1","d4","d5"]},
        {"case_id":"s1h1","source":"HVS","donor_ids":["d2","d3","d6"]},
    ]


def test_detects_overlapping_resamples_and_unique_biological_units():
    out=m.audit_cases(cases())
    assert out["case_count"]==4
    assert out["unique_donors"]==6
    assert out["all_cases_pairwise_independent"] is False
    assert out["terminal"]=="ROBUSTNESS_RESAMPLES_NOT_INDEPENDENT_REPLICATES"
    assert out["max_case_memberships_per_donor"]==2


def test_disjoint_cases_can_be_called_independent_by_membership_only():
    cs=[
      {"case_id":"a","source":"HVS","donor_ids":["d1","d2"]},
      {"case_id":"b","source":"HVS","donor_ids":["d3","d4"]},
    ]
    out=m.audit_cases(cs)
    assert out["all_cases_pairwise_independent"] is True
    assert out["terminal"]=="CASE_MEMBERSHIPS_DISJOINT__NO_BROADER_INDEPENDENCE_CLAIM"


def test_within_partition_halves_disjoint_but_cross_partition_overlap_reported():
    out=m.audit_cases(cases())
    by={tuple(x["case_pair"]):x for x in out["pairwise"]}
    assert by[("s0h0","s0h1")]["overlap_count"]==0
    assert by[("s0h0","s1h0")]["overlap_count"]==1


def test_duplicate_donor_within_case_rejected():
    cs=cases(); cs[0]["donor_ids"]=["d1","d1"]
    with pytest.raises(m.ResamplingAuditError):
        m.audit_cases(cs)


def test_duplicate_case_ids_rejected():
    cs=cases(); cs[1]["case_id"]="s0h0"
    with pytest.raises(m.ResamplingAuditError):
        m.audit_cases(cs)


def test_mixed_sources_rejected_in_one_audit():
    cs=cases(); cs[-1]["source"]="SEA_AD"
    with pytest.raises(m.ResamplingAuditError):
        m.audit_cases(cs)


def test_empty_donor_case_rejected():
    cs=cases(); cs[0]["donor_ids"]=[]
    with pytest.raises(m.ResamplingAuditError):
        m.audit_cases(cs)


def test_authority_is_always_false():
    out=m.audit_cases(cases())
    assert out["authority"] == {
       "target_selected":False,
       "representation_selected":False,
       "training_authorized":False,
       "value_read_authorized":False,
    }


def test_case_count_is_never_returned_as_independent_n_when_overlap_exists():
    out=m.audit_cases(cases())
    assert out["independent_n_from_case_rows"] is None
    assert out["biological_unit_n"]==6
