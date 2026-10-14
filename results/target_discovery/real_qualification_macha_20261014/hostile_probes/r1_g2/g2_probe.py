"""Hostile synthetic probes for G2 (PR #357 head c174d052) through adjudicate_g2. No real data."""
from __future__ import annotations

import json
import sys

G2_WT = "D:/jepa_rq_g2_20261014"
sys.path.insert(0, G2_WT)
import scripts.v5.td_real_g2_content_decision_v1 as G  # noqa: E402

B = "a" * 64
FULL_C1 = ("constant_train_mean", "technical_operator_only", "address_support_operator",
           "matched_wrong_cell", "identity_support_only")  # contract 206167a1 C1 mandatory_falsifiers
OUT = {}


def rows(cands, baselines, source="SEA_AD", endpoint="PRIMARY", support=None):
    out = []
    for i, c in enumerate(cands):
        out.append({"source": source, "endpoint": endpoint, "donor_id": f"{source}_D{i:02d}",
                    "candidate_score": c, "baseline_scores": dict(baselines),
                    "support_state": (support[i] if support else "SUPPORTED"), "input_binding_sha256": B})
    return out


def ref(rs, margin=0.10):
    return {"schema": G.REFERENCE_SCHEMA, "frozen": True, "qualified": True, "metric": G.METRIC,
            "orientation": G.ORIENTATION, "input_binding_sha256": B, "reference_namespace_disjoint": True,
            "reference_receipt_sha256": "0" * 64,
            "margins": {f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}': margin for r in rs
                        if r["support_state"] == "SUPPORTED"}}


FORGED_QUAL = {"schema": G.QUAL_SCHEMA, "status": G.QUAL_PASS, "known_truth_power_qualified": True}


def adj(rs, strata, baselines, margin=0.10, alpha=0.01, qual=FORGED_QUAL):
    return G.adjudicate_g2(rows=rs, required_strata=strata, frozen_baseline_ids=baselines,
                           decision_qualification=qual, reference_artifact=ref(rs, margin), alpha=alpha)


S = [("SEA_AD", "PRIMARY")]
# GA: hand-written qualification dict accepted (not bound to qualify_known_truth_g2 output / hash)
r = rows([0.8] * 8, {k: 0.2 for k in FULL_C1})
OUT["GA_forged_qualification_dict_accepted"] = adj(r, S, FULL_C1)["status"]

# GB: caller-chosen baseline family; contract C1 needs 5 falsifiers. Strong technical baseline 0.48.
bl_full = {"constant_train_mean": 0.10, "technical_operator_only": 0.48, "address_support_operator": 0.30,
           "matched_wrong_cell": 0.30, "identity_support_only": 0.30}
r_full = rows([0.50] * 8, bl_full)
r_weak = rows([0.50] * 8, {"constant_train_mean": 0.10})
OUT["GB_baseline_family_caller_supplied"] = {
    "full_C1_family": adj(r_full, S, FULL_C1)["status"],
    "caller_passes_only_constant_train_mean": adj(r_weak, S, ("constant_train_mean",))["status"],
}

# GC: zero margin reference accepted -> raw direction test; tiny 0.001 advantage passes
r = rows([0.201] * 8, {k: 0.20 for k in FULL_C1})
OUT["GC_zero_margin_reference_accepted_tiny_advantage"] = adj(r, S, FULL_C1, margin=0.0)["status"]

# GD: candidate identical to strongest baseline (e.g. the candidate IS the technical shortcut), margin 0
r = rows([0.20] * 10, {k: 0.20 for k in FULL_C1})
d = adj(r, S, FULL_C1, margin=0.0)
OUT["GD_candidate_equal_to_baseline_zero_margin"] = {
    "status": d["status"], "n_tied": d["stratum_details"]["SEA_AD::PRIMARY"]["raw_sufficient_statistics"]["n_tied_donors"]}
r = rows([0.30] * 10, {k: 0.20 for k in FULL_C1})  # advantage exactly == margin 0.10
d = adj(r, S, FULL_C1, margin=0.10)
OUT["GD2_advantage_exactly_equal_margin"] = d["status"]

# GE: value-dependent abstention: 10 donors, 3 losing; relabel losers UNSUPPORTED_STRUCTURAL
c = [0.8] * 7 + [0.1] * 3
honest = rows(c, {k: 0.2 for k in FULL_C1})
gamed = rows(c, {k: 0.2 for k in FULL_C1}, support=["SUPPORTED"] * 7 + ["UNSUPPORTED_STRUCTURAL"] * 3)
c8 = [0.8] * 8 + [0.1] * 3
gamed8 = rows(c8, {k: 0.2 for k in FULL_C1}, support=["SUPPORTED"] * 8 + ["UNSUPPORTED_STRUCTURAL"] * 3)
OUT["GE_value_dependent_support_relabel"] = {
    "honest_10_donors_7pos_3neg": adj(honest, S, FULL_C1)["status"],
    "losers_relabelled_unsupported_7": adj(gamed, S, FULL_C1)["status"],
    "honest_11_donors_8pos_3neg": adj(rows(c8, {k: 0.2 for k in FULL_C1}), S, FULL_C1)["status"],
    "losers_relabelled_unsupported_8": adj(gamed8, S, FULL_C1)["status"],
}

# GF: required_strata caller-supplied: omit failing HVS stratum
good = rows([0.8] * 8, {k: 0.2 for k in FULL_C1}, source="SEA_AD")
bad = rows([0.1] * 8, {k: 0.2 for k in FULL_C1}, source="HVS")
all_rows = good + bad
OUT["GF_required_strata_caller_supplied"] = {
    "both_required": G.adjudicate_g2(rows=all_rows, required_strata=[("SEA_AD", "PRIMARY"), ("HVS", "PRIMARY")],
                                     frozen_baseline_ids=FULL_C1, decision_qualification=FORGED_QUAL,
                                     reference_artifact=ref(all_rows), alpha=0.01)["status"],
    "HVS_omitted": G.adjudicate_g2(rows=all_rows, required_strata=[("SEA_AD", "PRIMARY")],
                                   frozen_baseline_ids=FULL_C1, decision_qualification=FORGED_QUAL,
                                   reference_artifact=ref(all_rows), alpha=0.01)["status"],
}

# GG: alpha caller-supplied
r = rows([0.8] * 2, {k: 0.2 for k in FULL_C1})
OUT["GG_alpha_0.5_two_donors"] = adj(r, S, FULL_C1, alpha=0.5)["status"]

# GH: 'not demonstrated' converted to FAIL: 9 of 10 donors clear the margin
r = rows([0.8] * 9 + [0.1], {k: 0.2 for k in FULL_C1})
d = adj(r, S, FULL_C1)
OUT["GH_9of10_donors_beat_margin"] = {"status": d["status"],
                                      "p_two_sided": d["stratum_details"]["SEA_AD::PRIMARY"]["raw_sufficient_statistics"]["two_sided_p"]}
r = rows([0.8] * 7, {k: 0.2 for k in FULL_C1})
OUT["GH2_7of7_positive_two_sided_vs_one_sided"] = adj(r, S, FULL_C1)["status"]

# GI: structurally unsupported row must still carry a finite numeric candidate score (forced fill)
r = rows([0.8] * 8, {k: 0.2 for k in FULL_C1}) + [{
    "source": "SEA_AD", "endpoint": "PRIMARY", "donor_id": "SEA_AD_UNSUP", "candidate_score": None,
    "baseline_scores": {}, "support_state": "UNSUPPORTED_STRUCTURAL", "input_binding_sha256": B}]
try:
    OUT["GI_unsupported_row_with_null_score"] = adj(r, S, FULL_C1)["status"]
except G.G2DecisionError as e:
    OUT["GI_unsupported_row_with_null_score"] = f"REFUSED: {e}"

# GJ: NaN in one supported donor -> exception (no distinct NUMERICAL_FAILURE status)
r = rows([0.8] * 7 + [float("nan")], {k: 0.2 for k in FULL_C1})
try:
    OUT["GJ_nan_one_donor"] = adj(r, S, FULL_C1)["status"]
except G.G2DecisionError as e:
    OUT["GJ_nan_one_donor"] = f"RAISES: {e}"

# GK: reference metric literal is generic; same reference object accepted for any endpoint/candidate
r = rows([0.8] * 8, {k: 0.2 for k in FULL_C1}, endpoint="ANY_OTHER_ENDPOINT_METRIC")
OUT["GK_generic_metric_reference_accepted_other_endpoint"] = adj(r, [("SEA_AD", "ANY_OTHER_ENDPOINT_METRIC")], FULL_C1)["status"]
OUT["GK_reference_fields"] = sorted(ref(r).keys())

print(json.dumps(OUT, indent=1))
