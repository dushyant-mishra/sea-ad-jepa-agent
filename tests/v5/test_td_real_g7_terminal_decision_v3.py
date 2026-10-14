from __future__ import annotations

import pytest

import scripts.v5.td_real_g7_terminal_decision_v3 as G

BINDING = "1" * 64


def _qual(ok=True):
    return {
        "schema": G.QUAL_SCHEMA,
        "status": G.QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_G7_V3",
        "known_truth_power_qualified": bool(ok),
    }


def _rows(source, n=8, displacement=0.02, added=1, binding=BINDING):
    return [
        {
            "source": source,
            "donor_id": f"{source}_D{i:02d}",
            "terminal_displacement": displacement,
            "penultimate_supported_evidence": 10,
            "full_supported_evidence": 10 + added,
            "added_supported_evidence": added,
            "input_binding_sha256": binding,
        }
        for i in range(n)
    ]


def _unit(row):
    return f'{row["source"]}::{row["donor_id"]}'


def _ref(rows, margin=0.1, binding=BINDING):
    return {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": G.METRIC,
        "orientation": G.ORIENTATION,
        "reference_kind": "U_REFIT",
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "2" * 64,
        "unit_margins": {_unit(r): float(margin) for r in rows},
    }


def _decide(rows, required_sources, ref=None, qual=None):
    return G.adjudicate_g7_terminal_v3(
        rows=rows,
        required_sources=required_sources,
        decision_qualification=_qual() if qual is None else qual,
        reference_artifact=_ref(rows) if ref is None else ref,
        alpha=0.01,
    )


def test_all_required_sources_must_pass_independently():
    rows = _rows("SEA_AD") + _rows("NPH52")
    out = _decide(rows, ["SEA_AD", "NPH52"])
    assert out["status"] == "PASS"
    assert out["source_status"] == {"NPH52": "PASS", "SEA_AD": "PASS"}


def test_fail_in_one_required_source_cannot_be_rescued_by_other_source():
    rows = _rows("SEA_AD", displacement=0.02) + _rows("NPH52", displacement=0.5)
    out = _decide(rows, ["SEA_AD", "NPH52"])
    assert out["status"] == "FAIL"
    assert out["source_status"]["SEA_AD"] == "PASS"
    assert out["source_status"]["NPH52"] == "FAIL"


def test_not_estimable_required_source_cannot_be_averaged_away():
    rows = _rows("SEA_AD", n=8) + _rows("HVS", n=7)
    out = _decide(rows, ["SEA_AD", "HVS"])
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["source_status"]["SEA_AD"] == "PASS"
    assert out["source_status"]["HVS"] == "NOT_ESTIMABLE"


def test_no_added_physical_support_is_source_specific_not_global():
    rows = _rows("SEA_AD", n=8, added=1) + _rows("HVS", n=8, displacement=0.0, added=0)
    out = _decide(rows, ["SEA_AD", "HVS"])
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["source_status"]["SEA_AD"] == "PASS"
    assert out["source_status"]["HVS"] == "NOT_ESTIMABLE"
    assert out["source_details"]["HVS"]["reason"] == "NO_DONORS_WITH_ADDED_SUPPORTED_EVIDENCE"


def test_missing_required_source_is_not_estimable_not_implicit_pass():
    rows = _rows("SEA_AD")
    out = _decide(rows, ["SEA_AD", "NPH52"])
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["source_status"]["NPH52"] == "NOT_ESTIMABLE"
    assert out["source_details"]["NPH52"]["reason"] == "REQUIRED_SOURCE_ABSENT"


def test_unlisted_source_rows_are_rejected_instead_of_silently_ignored():
    rows = _rows("SEA_AD") + _rows("NPH52")
    with pytest.raises(G.G7DecisionError, match="source"):
        _decide(rows, ["SEA_AD"])


def test_reference_margin_is_bound_to_source_and_donor_unit():
    rows = _rows("SEA_AD") + _rows("NPH52")
    ref = _ref(rows)
    ref["unit_margins"].pop("NPH52::NPH52_D00")
    with pytest.raises(G.G7DecisionError, match="margin"):
        _decide(rows, ["SEA_AD", "NPH52"], ref=ref)


def test_reference_input_binding_must_match_exact_deciding_realization():
    rows = _rows("SEA_AD", binding="3" * 64)
    with pytest.raises(G.G7DecisionError, match="binding"):
        _decide(rows, ["SEA_AD"], ref=_ref(rows, binding="1" * 64))


def test_known_truth_v3_covers_source_fail_ne_and_missing_source():
    q = G.qualify_known_truth_g7_v3()
    assert q["status"] == G.QUAL_PASS
    assert q["worlds"] == {
        "ALL_REQUIRED_SOURCES_CONVERGED": "PASS",
        "ONE_SOURCE_NONCONVERGED": "FAIL",
        "ONE_SOURCE_UNDERPOWERED": "NOT_ESTIMABLE",
        "ONE_SOURCE_NO_ADDED_SUPPORT": "NOT_ESTIMABLE",
        "MISSING_REQUIRED_SOURCE": "NOT_ESTIMABLE",
    }
    assert all(value is False for value in q["authority"].values())


def test_authority_remains_off():
    rows = _rows("SEA_AD")
    out = _decide(rows, ["SEA_AD"])
    assert all(value is False for value in out["authority"].values())
