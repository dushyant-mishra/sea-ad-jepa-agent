from __future__ import annotations

import pytest

import scripts.v5.td_real_g2_content_decision_v1 as G

BINDING = "a" * 64
BASELINES = ("constant_train_mean", "technical_operator_only", "address_support_operator")


def _qual(ok=True):
    return {
        "schema": G.QUAL_SCHEMA,
        "status": G.QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_G2",
        "known_truth_power_qualified": bool(ok),
    }


def _rows(*, sources=("SEA_AD",), endpoints=("PRIMARY",), candidate=0.80, baselines=None, donors=8, shared_donor_ids=False):
    baselines = baselines or {name: 0.20 for name in BASELINES}
    rows = []
    for source in sources:
        for endpoint in endpoints:
            for i in range(donors):
                donor_id = f"D{i:02d}" if shared_donor_ids else f"{source}_{endpoint}_D{i:02d}"
                rows.append({
                    "source": source,
                    "endpoint": endpoint,
                    "donor_id": donor_id,
                    "candidate_score": float(candidate),
                    "baseline_scores": {name: float(value) for name, value in baselines.items()},
                    "support_state": "SUPPORTED",
                    "input_binding_sha256": BINDING,
                })
    return rows


def _unit_key(row):
    return f'{row["source"]}::{row["endpoint"]}::{row["donor_id"]}'


def _reference(rows, *, margin=0.10, binding=BINDING, per_unit=None):
    margins = {
        _unit_key(r): float(margin)
        for r in rows
        if r["support_state"] == "SUPPORTED"
    }
    if per_unit:
        margins.update({str(k): float(v) for k, v in per_unit.items()})
    return {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": G.METRIC,
        "orientation": G.ORIENTATION,
        "input_binding_sha256": binding,
        "reference_namespace_disjoint": True,
        "reference_receipt_sha256": "b" * 64,
        "margins": margins,
    }


def test_candidate_must_beat_every_frozen_baseline_by_reference_margin():
    rows = _rows(baselines={
        "constant_train_mean": 0.10,
        "technical_operator_only": 0.25,
        "address_support_operator": 0.35,
    })
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, margin=0.10),
        alpha=0.01,
    )
    assert out["status"] == "PASS"
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["strongest_baseline_ids"] == ["address_support_operator"] * 8


def test_tiny_recurrent_advantage_below_reference_margin_fails():
    rows = _rows(candidate=0.31, baselines={name: 0.25 for name in BASELINES})
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, margin=0.10),
        alpha=0.01,
    )
    assert out["status"] == "FAIL"


def test_required_sources_and_endpoints_are_noncompensating():
    good = _rows(sources=("SEA_AD",), candidate=0.8)
    bad = _rows(sources=("NPH52",), candidate=0.21)
    rows = good + bad
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY"), ("NPH52", "PRIMARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, margin=0.10),
        alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert out["stratum_status"]["SEA_AD::PRIMARY"] == "PASS"
    assert out["stratum_status"]["NPH52::PRIMARY"] == "FAIL"


def test_same_donor_can_have_distinct_endpoint_bound_margins():
    rows = _rows(endpoints=("PRIMARY", "SECONDARY"), donors=8, shared_donor_ids=True)
    secondary_key = "SEA_AD::SECONDARY::D00"
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY"), ("SEA_AD", "SECONDARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, margin=0.10, per_unit={secondary_key: 0.90}),
        alpha=0.01,
    )
    assert out["stratum_status"]["SEA_AD::PRIMARY"] == "PASS"
    assert out["stratum_status"]["SEA_AD::SECONDARY"] == "FAIL"
    assert out["status"] == "FAIL"


def test_structural_or_blocked_support_abstains_instead_of_zero_fill():
    rows = _rows(donors=8)
    rows[0] = {**rows[0], "support_state": "UNSUPPORTED_STRUCTURAL"}
    rows[1] = {**rows[1], "support_state": "BLOCKED_EVIDENCE_CONTRACT"}
    ref = _reference(rows, margin=0.10)
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(),
        reference_artifact=ref,
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["supported_donor_count"] == 6
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["abstained_donor_count"] == 2


def test_missing_frozen_baseline_is_contract_error_not_cherry_pick():
    rows = _rows()
    rows[0] = {**rows[0], "baseline_scores": {"constant_train_mean": 0.2, "technical_operator_only": 0.2}}
    with pytest.raises(G.G2DecisionError, match="baseline"):
        G.adjudicate_g2(
            rows=rows,
            required_strata=[("SEA_AD", "PRIMARY")],
            frozen_baseline_ids=BASELINES,
            decision_qualification=_qual(),
            reference_artifact=_reference(_rows()),
            alpha=0.01,
        )


def test_reference_must_match_exact_deciding_realization_and_metric():
    rows = _rows()
    with pytest.raises(G.G2DecisionError, match="binding"):
        G.adjudicate_g2(
            rows=rows,
            required_strata=[("SEA_AD", "PRIMARY")],
            frozen_baseline_ids=BASELINES,
            decision_qualification=_qual(),
            reference_artifact=_reference(rows, binding="c" * 64),
            alpha=0.01,
        )


def test_unqualified_known_truth_decision_cannot_issue_human_fail():
    rows = _rows(candidate=0.0)
    out = G.adjudicate_g2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        frozen_baseline_ids=BASELINES,
        decision_qualification=_qual(False),
        reference_artifact=_reference(rows),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_KNOWN_TRUTH_NOT_QUALIFIED"


def test_known_truth_qualification_covers_signal_shortcut_margin_and_underpower():
    q = G.qualify_known_truth_g2()
    assert q["status"] == G.QUAL_PASS
    assert q["worlds"] == {
        "BIOLOGICAL_SIGNAL_BEYOND_BASELINES": "PASS",
        "SHORTCUT_ONLY": "FAIL",
        "TINY_ADVANTAGE_BELOW_MARGIN": "FAIL",
        "UNDERPOWERED_SUPPORTED_DONORS": "NOT_ESTIMABLE",
        "STRUCTURAL_SUPPORT_LOSS": "NOT_ESTIMABLE",
    }
    assert all(v is False for v in q["authority"].values())
