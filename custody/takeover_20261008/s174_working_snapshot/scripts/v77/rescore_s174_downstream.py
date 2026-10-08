#!/usr/bin/env python3
"""S174 downstream re-score, item 6 of the authorized dependency order: do the V77 synthetic-lane
conclusions that were judged against the old real targets survive the corrected ones?

It re-scores RECORDED synthetic statistics against the old and the corrected real envelopes. It generates
nothing, tunes nothing and selects nothing. That is valid only where the synthetic statistics themselves do
not depend on the corrupted cache: the background search and the Observer-V2 roster draw their priors from
the registry (v77_address_universe) and score genes chosen inside each synthetic world, so only their
targets moved. Records that score synthetic counts on the cache-derived evaluation universe cannot be
settled this way and are listed as pending a synthetic replay.

  background rounds  every recorded candidate, under each round's own rule (inside the donor-resampled
                     p05-p95 envelope on every target). The old re-score must reproduce every recorded
                     count exactly before anything new is said
  step 3             the record's three premises: the latent mechanism matched real geometry; observation
                     attenuates correlation below the real target; correlation and rank cannot both be met
  factor family      the falsifying invariant (transitivity out of reach), the second structural tension and
                     the two-layer findings, each against the corrected values
  observer V2        the evidence the decision cited (the realization isolation rows), the frozen roster,
                     the diagnosed residual and the retained abundance, against the corrected envelopes
  substate family    the two search rounds (same faithfulness check) and the family decision: its headline
                     setting, the change it credits, its abundance dial and its two named issues
  T5 guard           the within-class over pooled ratio every one of these records cites as its real reference
S159 is open: the corrected envelope's own point falls outside its p05-p95 band on some targets, so a
candidate identical to the real point would fail the recorded rule there. Rule counts are reported beside
ratios to the corrected point; no new threshold is introduced and no verdict is computed by one.

Usage: python rescore_s174_downstream.py --out results/v77/s174_replay/S174_DOWNSTREAM_RESCORE_V1.json \
           --md docs/agent/S174_DOWNSTREAM_RESCORE.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

NL = chr(10)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "results" / "v77"
NEW = ROOT / "results" / "v77" / "s174_replay"
TARGETS = ["median_abs_corr", "frac_abs_gt_0p3", "var_top10_pc", "mean_degree", "largest_community_frac",
           "transitivity", "substitute_frac", "frac_pos_gt_0p3", "frac_neg_lt_m0p3", "pos_over_neg_ratio",
           "mean_signed_corr"]
KEY = ("median_abs_corr", "frac_abs_gt_0p3", "var_top10_pc", "mean_degree", "transitivity")
ROUNDS = [f"V77_BG_SEARCH_ROUND{i}" for i in range(1, 8)]
# Step 3 states its post-observation shortfall as figures, not as candidate ids, and the round files that
# precede it (rounds 1 and 2) are the runs made before the abundance prior was added, so its premises are
# re-scored on its own figures. Each is bound to the recorded text by the literal it is quoted from.
STEP3_FIGURES = dict(median_abs_corr=("0.22", "0.33"), mean_degree=("950", "1686"),
                     transitivity=("0.55", "0.86"), var_top10_pc=("0.68", "0.509"))
DUPLICATES = {"V77_BG_CANDIDATE_SEARCH_ROUND1": "V77_BG_SEARCH_ROUND1",
              "V77_BG_CANDIDATE_SEARCH_ROUND2": "V77_BG_SEARCH_ROUND2"}
ENVELOPES = dict(cal="V77_REAL_CALIBRATION_ENVELOPE_V1.json", det="V77_REAL_DETECTION_ENVELOPE_V1.json",
                 ab="V77_REAL_ABUNDANCE_ENVELOPE_V1.json")
RECORDS = dict(step3="V77_STEP3_BACKGROUND_CALIBRATION_RESULT_V1.json",
               factor="V77_STEP3_FACTOR_FAMILY_FALSIFICATION_V1.json",
               observer="V77_OBSERVER_V2_DECISION_RECEIPT_V1.json",
               substate="V77_SUBSTATE_FAMILY_DECISION_V1.json")
SUBSTATE_ROUNDS = ["V77_SUBSTATE_SEARCH_ROUND1", "V77_SUBSTATE_SEARCH_ROUND2"]
TOPOLOGY = "V77_REAL_TRAIN_TOPOLOGY_CALIBRATION_V1.json"
DET5 = ("median_abs_corr", "frac_abs_gt_0p3", "transitivity", "mean_degree", "largest_community_frac")
# the substate decision states its abundance dial in prose; each value is bound to the literal it is quoted from
SUBSTATE_DIAL = {"x0.5": "0.8220", "x0.3": "0.8844", "x0.2": "0.9410"}
PENDING_REPLAY = {
    "V77_REALIZATION_ISOLATION_RECEIPT_V1.json": "scores synthetic counts on the cache-derived evaluation universe",
    "V77_REALIZATION_ISOLATION_RECEIPT_V2.json": "scores synthetic counts on the cache-derived evaluation universe",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V1.json": "scores synthetic counts on the cache-derived evaluation universe",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2.json": "scores synthetic counts on the cache-derived evaluation universe",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_HVS_EXPLORATORY.json": "exploratory; same universe dependence",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_SEA_AD_EXPLORATORY.json": "exploratory; same universe dependence",
    "V77_OBSERVER_V2_AUDIT_CORRECTION_V1.json": "its canonical-universe numbers come from the realization isolation",
    "V77_DYNAMIC_RANGE_VERDICT_V1.json": "the verdict on the dynamic-range tournament; it also quotes the old detection "
                                         "points",
}
NOT_MATERIAL = {
    "V77_S157_PAIRED_CHALLENGE_SCORE_ARM1_V1.json / _ARMS_V1.json / _PREREGISTRATION_V1.json":
        "the universe is only the address set of synthetic twin worlds; the identifiability conclusions do not "
        "depend on which genes it holds (as recorded when S174 was registered)",
    "V77_CONTEXT_SHORTCUT_AUDIT_V1.json": "DIAGNOSTIC_ONLY; study recoverability from support and depth does not "
                                          "depend on gene identity",
    "REHEARSAL_* and V77_RUNTIME_HANDOFF_*": "plumbing and runtime lane (kept separate from this repair by the "
                                            "owner); the universe is an index set there; flagged, not replayed",
}


# Classified before this re-score (register addendum 6) or superseded before S174; each keeps its reason.
CLASSIFIED_ELSEWHERE = {
    "V77_REPRODUCTION_ABUNDANCE_ENVELOPE_V1.json": "superseded by the replay itself (addendum 6)",
    "V77_REPRODUCTION_REAL_TOPOLOGY_AFTER_T5_EXTRACTION_V1.json": "superseded by the replay itself (addendum 6)",
    "V77_SUPERSEDED_REBUILD_CUSTODY_V1.json": "not material (addendum 6)",
    "V77_WITHIN_COHORT_AUTHORITY_CORRECTION_V1.json": "not material (addendum 6)",
    "V77_S157_LINEAGE_CROSSWALK_V1.json": "not material; its S149 row is superseded by the S149 update (addendum 6)",
    "V77_S157_TERMINAL_RECEIPT_V1.json": "not material (addendum 6)",
    "V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json": "superseded by V2 before S174 (S159); V2 is replayed",
}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def finite(x) -> bool:
    return x is not None and math.isfinite(float(x))


def r4(x):
    return round(float(x), 4) if finite(x) else None


def in_band(x, e, k) -> bool:
    return e[k]["accept_low"] <= x <= e[k]["accept_high"]


def inside(stats: dict, e: dict, keys) -> list[str]:
    return [k for k in keys if k in stats and k in e and in_band(stats[k], e, k)]


def ratio(x, e, k):
    p = e[k]["point"]
    return round(float(x) / p, 4) if finite(x) and p else None


def matches_recorded(x, rec) -> bool:
    """x equals a recorded figure at the precision the record printed it with."""
    s_ = repr(float(rec))
    return round(float(x), len(s_.split(".")[1]) if "." in s_ else 0) == float(rec)


def point_band(e, k) -> dict:
    return dict(point=r4(e[k]["point"]), band=[r4(e[k]["accept_low"]), r4(e[k]["accept_high"])],
                point_inside_own_band=in_band(e[k]["point"], e, k))


def envelopes() -> dict:
    E = {}
    for tag, name in ENVELOPES.items():
        E[f"{tag}_old"] = load(OLD / name)["ACCEPTANCE_ENVELOPES"]
        E[f"{tag}_new"] = load(NEW / name)["ACCEPTANCE_ENVELOPES"]
    return E


def s159(E) -> dict:
    out = {}
    for tag in ENVELOPES:
        for era in ("old", "new"):
            e = E[f"{tag}_{era}"]
            out[f"{ENVELOPES[tag]}::{'corrected' if era == 'new' else 'old'}"] = [
                k for k, v in e.items() if not v["accept_low"] <= v["point"] <= v["accept_high"]]
    res = load(NEW / ENVELOPES["det"])["resampling"]
    return dict(points_outside_their_own_band=out, resampling=dict(unit=res["unit"], n_bootstrap=res["n_bootstrap"]),
                consequence=("under the recorded rule a candidate identical to the corrected real point would fail on "
                             "these targets; a count of targets inside the band is therefore capped below the number "
                             "of targets and is read beside the ratio to the point"))


# ------------------------------------------------------------------------------------ background rounds

def background(E) -> tuple[dict, list]:
    out, faithful, entries = [], True, []
    rule = None
    for name in ROUNDS:
        d = load(OLD / f"{name}.json")
        rule = rule or d["acceptance_rule"]
        same_rule = d["acceptance_rule"] == rule
        rows = []
        for cid, c in d["candidates"].items():
            obs = c["observed"]
            n_old, n_new = len(inside(obs, E["cal_old"], TARGETS)), len(inside(obs, E["cal_new"], TARGETS))
            faithful &= c.get("n_targets_inside") == n_old and same_rule
            rows.append(dict(candidate=cid, recorded_verdict=c.get("verdict"),
                             recorded_n_inside=c.get("n_targets_inside"), old_n_inside_recomputed=n_old,
                             corrected_n_inside=n_new, of=len(TARGETS),
                             inside_corrected=inside(obs, E["cal_new"], TARGETS),
                             observed={k: r4(obs[k]) for k in KEY},
                             observed_over_corrected_point={k: ratio(obs[k], E["cal_new"], k) for k in KEY}))
            entries.append((name, cid, c))
        out.append(dict(round=name, envelope_source=d["envelope_source"]["path"], rows=rows,
                        best_old=max(r["old_n_inside_recomputed"] for r in rows),
                        best_corrected=max(r["corrected_n_inside"] for r in rows)))
    dup = {}
    for a, b in DUPLICATES.items():
        ca, cb = load(OLD / f"{a}.json")["candidates"], load(OLD / f"{b}.json")["candidates"]
        dup[a] = dict(same_as=b, same_candidates=set(ca) == set(cb),
                      same_recorded_statistics=all(ca[k]["observed"] == cb[k]["observed"] for k in ca))
    allrows = [r for rd in out for r in rd["rows"]]
    position = {}
    for k in KEY:
        vals = [c["observed"][k] for _, _, c in entries if finite(c["observed"][k])]
        po, pn = E["cal_old"][k]["point"], E["cal_new"][k]["point"]
        position[k] = dict(finite_entries=len(vals), old_point=r4(po), corrected_point=r4(pn),
                           observed_range=[r4(min(vals)), r4(max(vals))],
                           below_old_point=sum(v < po for v in vals), above_old_point=sum(v > po for v in vals),
                           below_corrected_point=sum(v < pn for v in vals),
                           above_corrected_point=sum(v > pn for v in vals))
    return dict(recorded_rule=rule, faithful_to_recorded_counts=faithful, duplicates_counted_once=dup,
                entries=len(allrows), distinct_candidates=len({r["candidate"] for r in allrows}),
                accepted_under_old=sum(r["old_n_inside_recomputed"] == len(TARGETS) for r in allrows),
                accepted_under_corrected=sum(r["corrected_n_inside"] == len(TARGETS) for r in allrows),
                max_inside_old=max(r["old_n_inside_recomputed"] for r in allrows),
                max_inside_corrected=max(r["corrected_n_inside"] for r in allrows),
                position_of_recorded_entries=position, rounds=out), entries


# ------------------------------------------------------------------------------------------------ step 3

def step3(E, entries) -> dict:
    s3 = load(OLD / RECORDS["step3"])
    lat = s3["THE_LATENT_MECHANISM_IS_SOLVED"]
    cid = lat["best_latent_candidate"]
    c6 = next(c["latent"] for _, i, c in entries if i == cid)
    six = list(lat["latent_versus_real"])
    for k in six:
        rec = lat["latent_versus_real"][k][0]
        assert round(c6[k], len(repr(float(rec)).split(".")[1])) == rec, k
    p1_rows = [dict(statistic=k, latent=r4(c6[k]), old_real=r4(E["cal_old"][k]["point"]),
                    corrected_real=r4(E["cal_new"][k]["point"]), latent_over_old=ratio(c6[k], E["cal_old"], k),
                    latent_over_corrected=ratio(c6[k], E["cal_new"], k)) for k in six]
    missed = max(p1_rows, key=lambda r: abs(math.log(r["latent_over_old"])))
    close = [r["latent_over_corrected"] for r in p1_rows if r is not missed]
    why = s3["WHY_STEP_3_IS_NOT_CLOSED"]
    text = why["systematic_failure"]
    fig = {}
    for k, (val, tgt) in STEP3_FIGURES.items():
        assert val in text and tgt in text, k
        v = float(val)
        fig[k] = dict(recorded_post_observation=v, recorded_target=float(tgt),
                      old_point=r4(E["cal_old"][k]["point"]), corrected_point=r4(E["cal_new"][k]["point"]),
                      over_old_point=ratio(v, E["cal_old"], k), over_corrected_point=ratio(v, E["cal_new"], k))
    over = [k for k, f in fig.items() if f["over_corrected_point"] > 1]
    short = [k for k, f in fig.items() if f["recorded_post_observation"] < f["recorded_target"]]
    both = fig["median_abs_corr"]["over_corrected_point"] > 1 and fig["var_top10_pc"]["over_corrected_point"] > 1
    flipped = [k for k in short if k in over]
    rest = [f"{k} ({fig[k]['over_corrected_point']} times)" for k in fig if k not in short]
    return dict(
        recorded_verdict=s3["VERDICT"],
        premise_1_latent_mechanism_matched_real=dict(
            recorded_claim=lat["reading"], candidate=cid, rows=p1_rows,
            latent_inside_old_band=len(inside(c6, E["cal_old"], six)),
            latent_inside_corrected_band=len(inside(c6, E["cal_new"], six)), of=len(six),
            reading=(f"the {len(close)} statistics the record called close are {min(close)} to {max(close)} times the "
                     f"corrected points; {missed['statistic']}, the one it missed, is {missed['latent_over_corrected']} "
                     f"times")),
        premise_2_observation_attenuates_correlation=dict(
            recorded_claim=text, recorded_binding_constraint=why["binding_constraint"], recorded_figures=fig,
            reading=(f"the recorded figures fell short of the old target on {', '.join(short)}; {len(flipped)} of those "
                     f"{len(short)} are above the corrected point ({', '.join(flipped)}), so there the shortfall the "
                     f"record attributed to the observation model exists only against the old target; the figure it "
                     f"recorded as running high stays high against the corrected point: {', '.join(rest)}")),
        premise_3_correlation_and_rank_cannot_both_be_met=dict(
            recorded_claim=why["the_structural_trap"],
            recorded_figures_above_corrected_point=dict(
                median_abs_corr=fig["median_abs_corr"]["over_corrected_point"] > 1,
                var_top10_pc=fig["var_top10_pc"]["over_corrected_point"] > 1),
            reading=(("the trap was stated for raising correlation toward the old target without pushing the rank "
                      "too low; against the corrected targets the recorded figures are above the real value on both, "
                      "so meeting them would need lower correlation and a less dominant top-10 rank together, which "
                      "is not the trade-off recorded") if both else
                     "the recorded figures are not above the corrected point on both statistics")))


# ----------------------------------------------------------------------------------------- factor family

def factor_family(E) -> dict:
    ff = load(OLD / RECORDS["factor"])
    inv = ff["THE_INVARIANT_THAT_FALSIFIES_THE_FAMILY"]
    xs = inv["observed_across_every_configuration"]
    lo, hi = min(xs), max(xs)
    det_o, det_n, cal_n = E["det_old"], E["det_new"], E["cal_new"]
    n_hvg = load(NEW / ENVELOPES["det"])["resampling"]["n_hvg"]
    ten = ff["THE_SECOND_STRUCTURAL_TENSION"]
    tension = [dict(candidate=e["candidate"], median_abs_corr=e["median_abs_corr"], var_top10_pc=e["var_top10_pc"],
                    largest_community=e["largest_community"], recorded_inside=e["inside"],
                    over_corrected_point=dict(
                        median_abs_corr=ratio(e["median_abs_corr"], cal_n, "median_abs_corr"),
                        var_top10_pc=ratio(e["var_top10_pc"], cal_n, "var_top10_pc"),
                        largest_community_frac=ratio(e["largest_community"], cal_n, "largest_community_frac")))
               for e in ten["evidence"]]
    two = ff["WHAT_THE_TWO_LAYER_MODEL_DID_ACHIEVE"]
    real_side = {}
    for k in ("median_abs_corr", "pos_over_neg_ratio", "mean_signed_corr", "largest_community_frac", "var_top10_pc"):
        real_side[k] = dict(detection_old=r4(det_o[k]["point"]), detection_corrected=r4(det_n[k]["point"]),
                            expression_old=r4(E["cal_old"][k]["point"]), expression_corrected=r4(cal_n[k]["point"]))
    in_range = dict(detection=lo <= det_n["transitivity"]["point"] <= hi,
                    expression=lo <= cal_n["transitivity"]["point"] <= hi)
    # the layer the record's invariant was stated on: its recorded real value is that layer's old point
    layer = next(name for name, e in (("detection", det_o), ("expression", E["cal_old"]))
                 if round(e["transitivity"]["point"], 4) == inv["real"])
    pt = (det_n if layer == "detection" else cal_n)["transitivity"]["point"]
    other = "expression" if layer == "detection" else "detection"
    opt = (cal_n if layer == "detection" else det_n)["transitivity"]["point"]

    def where(x):
        return "inside" if lo <= x <= hi else (f"below the lowest recorded value {lo}" if x < lo else
                                               f"above the highest recorded value {hi}")
    det_more = det_n["median_abs_corr"]["point"] > cal_n["median_abs_corr"]["point"]
    det_skew = (det_n["pos_over_neg_ratio"]["point"] > cal_n["pos_over_neg_ratio"]["point"]
                and det_n["mean_signed_corr"]["point"] > cal_n["mean_signed_corr"]["point"])
    return dict(
        recorded_verdict=ff["VERDICT"],
        invariant=dict(
            recorded_statistic=inv["statistic"], recorded_real=inv["real"], recorded_envelope=inv["envelope"],
            recorded_reading=inv["range"],
            old_detection=point_band(det_o, "transitivity"),
            corrected_detection=point_band(det_n, "transitivity"),
            corrected_expression=point_band(cal_n, "transitivity"),
            recorded_configurations=xs, family_range=[lo, hi],
            corrected_points_inside_family_range=in_range,
            configurations_inside_corrected_detection_band=sum(in_band(x, det_n, "transitivity") for x in xs),
            configurations_inside_corrected_expression_band=sum(in_band(x, cal_n, "transitivity") for x in xs),
            edge_density=dict(n_hvg=n_hvg,
                              old_detection=r4(det_o["mean_degree"]["point"] / (n_hvg - 1)),
                              corrected_detection=r4(det_n["mean_degree"]["point"] / (n_hvg - 1))),
            recorded_layer=layer,
            reading=(f"the record's invariant is on the {layer} layer (its recorded real {inv['real']} is the old "
                     f"{layer} point) and falsified the family because transitivity never approached it at an edge "
                     f"density of {r4(det_o['mean_degree']['point'] / (n_hvg - 1))}. The corrected {layer} value "
                     f"{r4(pt)} is {where(pt)} the range the family produced [{lo}, {hi}], at an edge density of "
                     f"{r4(det_n['mean_degree']['point'] / (n_hvg - 1))}, so the stated reason "
                     f"{'no longer holds' if lo <= pt <= hi else 'still holds'}. The corrected {other} value {r4(opt)} "
                     f"is {where(opt)}. This does not show that the family fits the corrected targets: that was "
                     f"never scored")),
        second_structural_tension=dict(recorded_claim=ten["statement"], evidence=tension,
                                       corrected_points=dict(median_abs_corr=r4(cal_n["median_abs_corr"]["point"]),
                                                             var_top10_pc=r4(cal_n["var_top10_pc"]["point"]),
                                                             largest_community_frac=r4(
                                                                 cal_n["largest_community_frac"]["point"]))),
        two_layer_findings=dict(recorded=two, real_side_old_and_corrected=real_side,
                                detection_carries_more_dependence_than_expression=det_more,
                                detection_more_positively_skewed_than_expression=det_skew,
                                reading=((f"detection still carries more dependence than expression (corrected "
                                          f"{r4(det_n['median_abs_corr']['point'])} against "
                                          f"{r4(cal_n['median_abs_corr']['point'])}) and is still more positively "
                                          f"skewed, so the direction of the two-layer findings survives; their "
                                          f"magnitudes, and every synthetic value the record placed inside an old "
                                          f"envelope, were measured against the inflated targets")
                                         if det_more and det_skew else
                                         "the direction of the two-layer findings does not survive in full; see the "
                                         "two flags")))


# ------------------------------------------------------------------------------------------- observer V2

def observer(E) -> dict:
    ob = load(OLD / RECORDS["observer"])
    det_keys = ("median_abs_corr", "frac_abs_gt_0p3", "transitivity", "mean_degree")
    ab_pairs = (("abundance_max_over_median", "abundance_max_over_median_nonzero"),
                ("top1pct", "top1pct_count_share"))
    cited = []
    for r in ob["THE_CONFOUND_I_INTRODUCED_AND_REMOVED"]["isolation_run"]:
        row = dict(variant=r["variant"])
        for k in det_keys:
            row[k] = dict(value=r[k], old_point=r4(E["det_old"][k]["point"]),
                          corrected_point=r4(E["det_new"][k]["point"]), over_old=ratio(r[k], E["det_old"], k),
                          over_corrected=ratio(r[k], E["det_new"], k))
        for kr, ke in ab_pairs:
            row[ke] = dict(value=r[kr], old_point=r4(E["ab_old"][ke]["point"]),
                           corrected_point=r4(E["ab_new"][ke]["point"]), over_old=ratio(r[kr], E["ab_old"], ke),
                           over_corrected=ratio(r[kr], E["ab_new"], ke))
        cited.append(row)
    span = {}
    for r in cited:
        v = [r[k]["over_corrected"] for k in det_keys]
        span[r["variant"]] = [min(v), max(v)]
    det_v = next(k for k in span if "DETERMINISTIC" in k)
    poi_v = next(k for k in span if "POISSON" in k)
    allc = ob["ALL_CANDIDATES_INCLUDING_FAILURES"]
    topo = ("median_abs_corr", "frac_abs_gt_0p3", "transitivity", "mean_degree", "largest_community_frac")
    roster = []
    for cid, m in allc["results"].items():
        row = dict(candidate=cid,
                   topology_inside_old=len(inside(m, E["det_old"], topo)),
                   topology_inside_corrected=len(inside(m, E["det_new"], topo)),
                   topology_inside_corrected_targets=inside(m, E["det_new"], topo), of=len(topo),
                   over_corrected_point={k: ratio(m[k], E["det_new"], k) for k in topo})
        for kr, ke in (("max_over_median", "abundance_max_over_median_nonzero"), ("top1", "top1pct_count_share")):
            row[f"{ke}_inside_old"] = in_band(m[kr], E["ab_old"], ke)
            row[f"{ke}_inside_corrected"] = in_band(m[kr], E["ab_new"], ke)
            row[f"{ke}_over_corrected_point"] = ratio(m[kr], E["ab_new"], ke)
        roster.append(row)
    med = [m["median_abs_corr"] for m in allc["results"].values()]
    tail = {cid: ratio(m["frac_abs_gt_0p3"], E["det_new"], "frac_abs_gt_0p3") for cid, m in allc["results"].items()}
    frac = [m["frac_abs_gt_0p3"] for m in allc["results"].values()]
    frac_pt = E["det_new"]["frac_abs_gt_0p3"]["point"]
    tail_side = "inside" if min(frac) <= frac_pt <= max(frac) else ("above" if frac_pt > max(frac) else "below")
    res = ob["THE_DIAGNOSED_RESIDUAL_AND_WHERE_IT_BELONGS"]
    det_pt = E["det_new"]["median_abs_corr"]["point"]
    return dict(
        recorded_decision=ob["DECISION"], recorded_answer=ob["ANSWER"],
        cited_evidence_realization_isolation=dict(
            rows=cited,
            ratio_span_to_corrected_points=span,
            reading=(f"the decision cited the deterministic-threshold variant reproducing the real fraction above 0.3 "
                     f"and mean degree essentially exactly; those real values are the old detection points. Against "
                     f"the corrected points, on the four topology statistics, the deterministic variant is "
                     f"{span[det_v][0]} to {span[det_v][1]} times the real value and the Poisson variant, recorded as "
                     f"destroying detection correlation, {span[poi_v][0]} to {span[poi_v][1]} times")),
        roster=dict(recorded_every_candidate_failed_on_topology=allc["every_candidate_failed_on_topology"],
                    recorded_best=allc["best_of_roster"], rows=roster),
        diagnosed_residual=dict(recorded_claim=res["real_data_implication"], recorded_handoff=res["handoff"],
                                old_real_detection_median_abs_corr=r4(E["det_old"]["median_abs_corr"]["point"]),
                                corrected_real_detection_median_abs_corr=r4(det_pt),
                                roster_median_abs_corr_range=[r4(min(med)), r4(max(med))],
                                corrected_point_inside_roster_range=min(med) <= det_pt <= max(med),
                                roster_frac_abs_gt_0p3_over_corrected_point=tail,
                                reading=(f"the median the residual was quantified on now lies "
                                         f"{'inside' if min(med) <= det_pt <= max(med) else 'outside'} the roster's own "
                                         f"range; the corrected real fraction above 0.3 ({r4(frac_pt)}) lies "
                                         f"{tail_side} the roster's range [{r4(min(frac))}, {r4(max(frac))}], which is "
                                         f"{min(tail.values())} to {max(tail.values())} times the real value")),
        abundance_retained=dict(recorded_claim=allc["abundance_was_however_retained"],
                                old_real=r4(E["ab_old"]["abundance_max_over_median_nonzero"]["point"]),
                                corrected_real=r4(E["ab_new"]["abundance_max_over_median_nonzero"]["point"])),
        caveat=("roster and isolation statistics were computed with each arm's own prevalence filter, which the audit "
                "correction showed to be material; the audit correction's canonical-universe numbers were computed on "
                "the old cache-derived universe and are pending a synthetic replay"))


# ---------------------------------------------------------------------------------------- substate family

def substate_search(E) -> dict:
    out, faithful = [], True
    for name in SUBSTATE_ROUNDS:
        d = load(OLD / f"{name}.json")
        rows = []
        for cid, c in d["candidates"].items():
            ne, nd = len(inside(c["observed"], E["cal_old"], TARGETS)), len(inside(c["detection"], E["det_old"], TARGETS))
            faithful &= ne == c["n_expression_inside"] and nd == c["n_detection_inside"]
            rows.append(dict(candidate=cid, recorded_expression_inside=c["n_expression_inside"],
                             recorded_detection_inside=c["n_detection_inside"], expression_inside_old=ne,
                             detection_inside_old=nd,
                             expression_inside_corrected=len(inside(c["observed"], E["cal_new"], TARGETS)),
                             detection_inside_corrected=len(inside(c["detection"], E["det_new"], TARGETS)),
                             detection_inside_corrected_targets=inside(c["detection"], E["det_new"], TARGETS),
                             detection_over_corrected_point={k: ratio(c["detection"][k], E["det_new"], k)
                                                             for k in DET5}))
        out.append(dict(round=name, recorded_headline_target=d["headline_target"], rows=rows))
    return dict(faithful_to_recorded_counts=faithful, of=len(TARGETS), rounds=out)


def substate_decision(E) -> dict:
    d = load(OLD / RECORDS["substate"])
    best = d["BEST_SETTING_AND_WHY_IT_REVEALS_THE_MECHANISM"]
    for k in DET5:
        assert matches_recorded(E["det_old"][k]["point"], best["real"][k]), k
    m = best["measured"]
    best_rows = [dict(statistic=k, measured=m[k], recorded_real=best["real"][k],
                      corrected_point=r4(E["det_new"][k]["point"]), over_corrected=ratio(m[k], E["det_new"], k),
                      inside_old_band=in_band(m[k], E["det_old"], k), inside_corrected_band=in_band(m[k], E["det_new"], k))
                 for k in DET5]
    en = d["THE_ENABLING_CHANGE_WAS_THE_OBSERVATION_MODEL_NOT_THE_GENERATOR"]
    keymap = dict(median="median_abs_corr", frac_gt_0p3="frac_abs_gt_0p3", transitivity="transitivity",
                  degree="mean_degree", largest_community="largest_community_frac")
    models = []
    for r in en["measured_effect_of_removing_it"]:
        models.append(dict(model=r["model"], over_corrected={keymap[k]: ratio(r[k], E["det_new"], keymap[k])
                                                             for k in keymap}))
    a = next(x for x in models if x["model"].startswith("A "))
    c = next(x for x in models if x["model"].startswith("C "))
    further = [k for k in keymap.values()
               if abs(math.log(c["over_corrected"][k])) > abs(math.log(a["over_corrected"][k]))]
    dial_text = best["why_abundance_scale_is_the_dial"]
    dial = {}
    for scale, val in SUBSTATE_DIAL.items():
        assert val in dial_text and scale.replace("x", "x") in dial_text, scale
        dial[scale] = dict(transitivity=float(val), over_corrected=ratio(float(val), E["det_new"], "transitivity"),
                           inside_old_band=in_band(float(val), E["det_old"], "transitivity"),
                           inside_corrected_band=in_band(float(val), E["det_new"], "transitivity"))
    i2 = d["UNRESOLVED_ISSUE_2_SIGN_BALANCE_AND_COMMUNITY_SIZE"]
    return dict(
        recorded_decision=d["FAMILY_DECISION"], recorded_headline=d["HEADLINE"],
        headline_setting=dict(generator=best["generator"], observation=best["observation"],
                              abundance_prior_scale=best["abundance_prior_scale"], rows=best_rows,
                              inside_old_band=sum(r["inside_old_band"] for r in best_rows),
                              inside_corrected_band=sum(r["inside_corrected_band"] for r in best_rows), of=len(DET5)),
        credited_change=dict(
            recorded_claim=en["finding"], recorded_culprit=en["the_culprit"], models=models,
            statistics_where_C_is_further_from_the_corrected_point_than_A=further, of=len(keymap),
            reading=(f"against the corrected points the free-threshold model the record moved to (C) is further from "
                     f"the real value than the exact top-k default it replaced (A) on {len(further)} of {len(keymap)} "
                     f"statistics ({', '.join(further)})")),
        abundance_dial=dict(recorded_claim=dial_text, settings=dial,
                            reading=(f"the dial brackets the old target; none of the {len(dial)} recorded settings is "
                                     f"inside the corrected band" if not any(v["inside_corrected_band"]
                                                                            for v in dial.values())
                                     else "a recorded setting lies inside the corrected band")),
        issue_2_sign_balance_and_community=dict(
            recorded=i2, real_detection_pos_over_neg=dict(old=r4(E["det_old"]["pos_over_neg_ratio"]["point"]),
                                                          corrected=r4(E["det_new"]["pos_over_neg_ratio"]["point"])),
            real_detection_largest_community=dict(old=r4(E["det_old"]["largest_community_frac"]["point"]),
                                                  corrected=r4(E["det_new"]["largest_community_frac"]["point"]))),
        issue_1_note=("the abundance figures this issue quotes (6685, 0.322) were computed over all 41,238 addresses of "
                      "the old cache and are not recomputed here; on the filtered universe the corrected abundance "
                      "points are in the observer V2 section"))


def t5_guard(E) -> dict:
    to = load(OLD / TOPOLOGY)["T5_class_conditional_structure"]
    tn = load(NEW / TOPOLOGY)["T5_class_conditional_structure"]
    ff, ob, sd = load(OLD / RECORDS["factor"]), load(OLD / RECORDS["observer"]), load(OLD / RECORDS["substate"])
    bg = [c["t5_observed"] for n in ROUNDS for c in load(OLD / f"{n}.json")["candidates"].values()
          if finite(c.get("t5_observed"))]
    ss = [c["t5_observed"] for n in SUBSTATE_ROUNDS for c in load(OLD / f"{n}.json")["candidates"].values()
          if finite(c.get("t5_observed"))]
    ranges = {"background rounds": [r4(min(bg)), r4(max(bg))],
              "factor family": ff["T5_GUARD_NEVER_VIOLATED"]["range_across_all_candidates"],
              "observer V2 roster": ob["GUARDS"]["T5"]["range_across_roster"],
              "substate search rounds": [r4(min(ss)), r4(max(ss))],
              "substate family": sd["T5_HARD_GUARD_HELD_THROUGHOUT"]["range_across_all_substate_candidates"]}
    old, new = to["within_over_pooled_ratio"], tn["within_over_pooled_ratio"]
    lowest = min(v[0] for v in ranges.values())
    above = all(v[0] > new for v in ranges.values())
    return dict(
        recorded_real_reference=1.012, old_real=r4(old), corrected_real=r4(new),
        corrected_pooled_median_abs_corr=r4(tn["pooled_median_abs_corr"]),
        corrected_mean_within_class_median_abs_corr=r4(tn["mean_within_class_median_abs_corr"]),
        recorded_guard=to["GUARD"], recorded_synthetic_ranges=ranges,
        lowest_recorded_synthetic=lowest, every_recorded_range_above_corrected_real=above,
        successor_requirement_recorded=ff["WHAT_A_SUCCESSOR_FAMILY_MUST_HAVE"]["why_discrete_states_are_the_leading_candidate"],
        substate_structural_argument_recorded=sd["T5_HARD_GUARD_HELD_THROUGHOUT"]["why_it_is_structural_here"],
        reading=(f"the guard fails a candidate whose ratio collapses toward zero, and no recorded candidate did (lowest "
                 f"{lowest}). But the real ratio is {r4(new)}, not {r4(old)}: within-class dependence is about "
                 f"{round(100 * new)}% of pooled, so part of the real pooled dependence is class separation. "
                 + ("Every recorded synthetic range lies above the corrected real ratio. " if above else "")
                 + "The inferences built on a ratio of about 1, that real dependence carries essentially no class "
                   "separation and that a successor's states cannot simply be the broad cell classes, rested on the "
                   "old input"))


# --------------------------------------------------------------------------------------------- markdown

def markdown(rec: dict) -> str:
    bg, s3, ff, ob = rec["background_rounds"], rec["step3"], rec["factor_family"], rec["observer_v2"]
    L = ["# S174 downstream re-score", "",
         "Old and corrected numbers side by side for the V77 synthetic-lane records judged against the real "
         "targets. Recorded synthetic statistics are re-scored under each record's own rule; nothing is "
         f"generated, tuned or selected. JSON record: `{rec['record_path']}`.", "", "## S159 (open)", ""]
    for k, v in rec["S159"]["points_outside_their_own_band"].items():
        if v:
            L.append(f"- `{k}`: point outside its own p05-p95 band on {', '.join(v)}")
    L += ["", f"Resampling: {rec['S159']['resampling']}. {rec['S159']['consequence']}.", "",
          "## Background search rounds", "",
          f"Recorded rule: {bg['recorded_rule']}.", "",
          f"Re-scorer faithful to every recorded count: **{bg['faithful_to_recorded_counts']}**. "
          f"{bg['entries']} recorded entries, {bg['distinct_candidates']} distinct candidates (the two candidate-search "
          f"files duplicate rounds 1 and 2 and are counted once). Accepted under the old envelope: "
          f"{bg['accepted_under_old']}; under the corrected: {bg['accepted_under_corrected']}. Most targets inside: "
          f"{bg['max_inside_old']}/11 old, {bg['max_inside_corrected']}/11 corrected.", "",
          "| round | candidate | recorded | old (recomputed) | corrected | median abs corr / corrected point |",
          "|---|---|---|---|---|---|"]
    for rd in bg["rounds"]:
        for r in rd["rows"]:
            L.append(f"| {rd['round'].replace('V77_BG_SEARCH_', '')} | {r['candidate']} | {r['recorded_n_inside']}/11 | "
                     f"{r['old_n_inside_recomputed']}/11 | {r['corrected_n_inside']}/11 | "
                     f"{r['observed_over_corrected_point']['median_abs_corr']} |")
    L += ["", "Where the recorded entries sit (finite values only):", "",
          "| statistic | old point | corrected point | recorded range | below old | above old | below corrected | "
          "above corrected |", "|---|---|---|---|---|---|---|---|"]
    for k, v in bg["position_of_recorded_entries"].items():
        L.append(f"| {k} | {v['old_point']} | {v['corrected_point']} | {v['observed_range'][0]} to "
                 f"{v['observed_range'][1]} | {v['below_old_point']} | {v['above_old_point']} | "
                 f"{v['below_corrected_point']} | {v['above_corrected_point']} |")
    p1, p2, p3 = (s3["premise_1_latent_mechanism_matched_real"], s3["premise_2_observation_attenuates_correlation"],
                  s3["premise_3_correlation_and_rank_cannot_both_be_met"])
    L += ["", "## Step 3 background calibration", "", f"Recorded verdict: `{s3['recorded_verdict']}`.", "",
          f"**Premise 1, latent mechanism matched real geometry** ({p1['candidate']}). Recorded: {p1['recorded_claim']}. "
          f"Corrected: {p1['reading']}.", "",
          "| statistic | latent | old real | corrected real | latent / old | latent / corrected |",
          "|---|---|---|---|---|---|"]
    for r in p1["rows"]:
        L.append(f"| {r['statistic']} | {r['latent']} | {r['old_real']} | {r['corrected_real']} | "
                 f"{r['latent_over_old']} | {r['latent_over_corrected']} |")
    L += ["", f"**Premise 2, observation attenuates correlation.** Recorded: {p2['recorded_claim']}. "
              f"Corrected: {p2['reading']}.", "",
          "| statistic | recorded after observation | recorded target | corrected point | recorded / corrected |",
          "|---|---|---|---|---|"]
    for k, f in p2["recorded_figures"].items():
        L.append(f"| {k} | {f['recorded_post_observation']} | {f['recorded_target']} | {f['corrected_point']} | "
                 f"{f['over_corrected_point']} |")
    L += ["", f"**Premise 3, correlation and rank cannot both be met.** Recorded: {p3['recorded_claim']} "
              f"Corrected: {p3['reading']}.", ""]
    inv = ff["invariant"]
    L += ["## Factor-family falsification", "", f"Recorded verdict: `{ff['recorded_verdict']}`.", "",
          f"- Invariant: {inv['recorded_statistic']}, recorded real {inv['recorded_real']} "
          f"(band {inv['recorded_envelope']}), family range {inv['family_range']} over "
          f"{len(inv['recorded_configurations'])} recorded configurations.",
          f"- Corrected detection {inv['corrected_detection']['point']} (band {inv['corrected_detection']['band']}, "
          f"point inside own band: {inv['corrected_detection']['point_inside_own_band']}); corrected expression "
          f"{inv['corrected_expression']['point']} (band {inv['corrected_expression']['band']}).",
          f"- Recorded configurations inside the corrected detection band: "
          f"{inv['configurations_inside_corrected_detection_band']}; inside the corrected expression band: "
          f"{inv['configurations_inside_corrected_expression_band']}.",
          f"- Edge density at the real point (mean degree over {inv['edge_density']['n_hvg'] - 1}): old "
          f"{inv['edge_density']['old_detection']}, corrected {inv['edge_density']['corrected_detection']}.",
          f"- Corrected: {inv['reading']}.", "",
          f"Second structural tension, recorded: {ff['second_structural_tension']['recorded_claim']}. "
          f"Corrected points: {json.dumps(ff['second_structural_tension']['corrected_points'])}.", ""]
    for e in ff["second_structural_tension"]["evidence"]:
        L.append(f"- {e['candidate']}: recorded inside {e['recorded_inside']}; over the corrected point "
                 f"{json.dumps(e['over_corrected_point'])}")
    L += ["", f"Two-layer findings, corrected: {ff['two_layer_findings']['reading']}.", "",
          "| statistic | detection old | detection corrected | expression old | expression corrected |",
          "|---|---|---|---|---|"]
    for k, v in ff["two_layer_findings"]["real_side_old_and_corrected"].items():
        L.append(f"| {k} | {v['detection_old']} | {v['detection_corrected']} | {v['expression_old']} | "
                 f"{v['expression_corrected']} |")
    L += ["", "## Observer-V2 decision", "", f"Recorded decision: `{ob['recorded_decision']}`. "
                                              f"Recorded answer: {ob['recorded_answer']}", "",
          f"Corrected: {ob['cited_evidence_realization_isolation']['reading']}.", "",
          "| variant | frac abs corr > 0.3 (/ corrected) | mean degree (/ corrected) | transitivity (/ corrected) | "
          "median abs corr (/ corrected) |", "|---|---|---|---|---|"]
    for r in ob["cited_evidence_realization_isolation"]["rows"]:
        L.append(f"| {r['variant']} | {r['frac_abs_gt_0p3']['value']} ({r['frac_abs_gt_0p3']['over_corrected']}) | "
                 f"{r['mean_degree']['value']} ({r['mean_degree']['over_corrected']}) | "
                 f"{r['transitivity']['value']} ({r['transitivity']['over_corrected']}) | "
                 f"{r['median_abs_corr']['value']} ({r['median_abs_corr']['over_corrected']}) |")
    L += ["", f"Roster, recorded: every candidate failed on topology = "
              f"{ob['roster']['recorded_every_candidate_failed_on_topology']}; best {ob['roster']['recorded_best']}.", "",
          "| candidate | topology inside old | inside corrected | median abs corr | frac > 0.3 | transitivity | "
          "mean degree | largest community | max/median | top1% |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in ob["roster"]["rows"]:
        o = r["over_corrected_point"]
        L.append(f"| {r['candidate']} | {r['topology_inside_old']}/{r['of']} | {r['topology_inside_corrected']}/{r['of']} | "
                 f"{o['median_abs_corr']} | {o['frac_abs_gt_0p3']} | {o['transitivity']} | {o['mean_degree']} | "
                 f"{o['largest_community_frac']} | {r['abundance_max_over_median_nonzero_over_corrected_point']} | "
                 f"{r['top1pct_count_share_over_corrected_point']} |")
    L += ["", "Roster columns after the counts are ratios to the corrected real point.", ""]
    dr, ar = ob["diagnosed_residual"], ob["abundance_retained"]
    L += [f"Diagnosed residual, recorded: {dr['recorded_claim']} Corrected: real detection median abs corr "
          f"{dr['old_real_detection_median_abs_corr']} becomes {dr['corrected_real_detection_median_abs_corr']} "
          f"(roster range {dr['roster_median_abs_corr_range']}); {dr['reading']}.", "",
          f"Abundance retained, recorded: {ar['recorded_claim']}. Corrected: real max/median {ar['old_real']} becomes "
          f"{ar['corrected_real']}.", "", f"Caveat: {ob['caveat']}.", ""]
    ss, sd, t5 = rec["substate_search"], rec["substate_family_decision"], rec["t5_guard"]
    L += ["## Substate family", "",
          f"Search rounds: re-scorer faithful to every recorded count: **{ss['faithful_to_recorded_counts']}**.", "",
          "| round | candidate | expression inside (recorded / corrected) | detection inside (recorded / corrected) | "
          "which (corrected detection) |", "|---|---|---|---|---|"]
    for rd in ss["rounds"]:
        for r in rd["rows"]:
            L.append(f"| {rd['round'].replace('V77_SUBSTATE_SEARCH_', '')} | {r['candidate']} | "
                     f"{r['recorded_expression_inside']} / {r['expression_inside_corrected']} | "
                     f"{r['recorded_detection_inside']} / {r['detection_inside_corrected']} | "
                     f"{', '.join(r['detection_inside_corrected_targets']) or '-'} |")
    hs = sd["headline_setting"]
    L += ["", f"Recorded decision: `{sd['recorded_decision']}`. Recorded headline: {sd['recorded_headline']}", "",
          f"Headline setting ({hs['generator']}; abundance prior x{hs['abundance_prior_scale']}): inside the old band "
          f"on {hs['inside_old_band']} of {hs['of']}, inside the corrected band on {hs['inside_corrected_band']}.", "",
          "| statistic | measured | recorded real (old) | corrected point | measured / corrected |",
          "|---|---|---|---|---|"]
    for r in hs["rows"]:
        L.append(f"| {r['statistic']} | {r['measured']} | {r['recorded_real']} | {r['corrected_point']} | "
                 f"{r['over_corrected']} |")
    cc = sd["credited_change"]
    L += ["", f"The change the decision credits, recorded: {cc['recorded_culprit']} Corrected: {cc['reading']}.", "",
          "| model | " + " | ".join(DET5) + " |", "|---|" + "---|" * len(DET5)]
    for mm in cc["models"]:
        L.append(f"| {mm['model']} | " + " | ".join(str(mm["over_corrected"][k]) for k in DET5) + " |")
    L += ["", "Model columns are ratios to the corrected real point.", "",
          f"Abundance dial, recorded: {sd['abundance_dial']['recorded_claim']} Corrected: {sd['abundance_dial']['reading']}.",
          "", f"Issue 2, real detection positive-over-negative ratio: old "
              f"{sd['issue_2_sign_balance_and_community']['real_detection_pos_over_neg']['old']}, corrected "
              f"{sd['issue_2_sign_balance_and_community']['real_detection_pos_over_neg']['corrected']}; largest "
              f"community: old {sd['issue_2_sign_balance_and_community']['real_detection_largest_community']['old']}, "
              f"corrected {sd['issue_2_sign_balance_and_community']['real_detection_largest_community']['corrected']}.",
          "", f"Issue 1: {sd['issue_1_note']}.", "",
          "## T5 guard", "",
          f"Real within-class over pooled ratio: old {t5['old_real']} (recorded {t5['recorded_real_reference']}), "
          f"corrected {t5['corrected_real']} (pooled {t5['corrected_pooled_median_abs_corr']}, mean within-class "
          f"{t5['corrected_mean_within_class_median_abs_corr']}).", ""]
    for k, v in t5["recorded_synthetic_ranges"].items():
        L.append(f"- {k}: recorded synthetic range {v}")
    L += ["", f"Corrected: {t5['reading']}.", "", "## Pending a synthetic replay", ""]
    for k, v in rec["pending_synthetic_replay"].items():
        L.append(f"- `{k}`: {v}")
    L += ["", "## Not replayed (not material)", ""]
    for k, v in rec["not_material"].items():
        L.append(f"- `{k}`: {v}")
    L += ["", "## Classified before this re-score", ""]
    for k, v in rec["classified_elsewhere"].items():
        L.append(f"- `{k}`: {v}")
    return NL.join(L) + NL


def record_path(out: Path) -> str:
    try:
        return out.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return out.as_posix()


def build(out: Path) -> dict:
    E = envelopes()
    bg, entries = background(E)
    files = [OLD / n for n in ENVELOPES.values()] + [NEW / n for n in ENVELOPES.values()] + \
            [OLD / n for n in RECORDS.values()] + [OLD / f"{n}.json" for n in ROUNDS + list(DUPLICATES)] + \
            [OLD / f"{n}.json" for n in SUBSTATE_ROUNDS] + [OLD / TOPOLOGY, NEW / TOPOLOGY]
    return dict(schema="S174_DOWNSTREAM_RESCORE_V1",
                scope=("item 6 of the authorized dependency order (the background-search rounds, both Step 3 "
                       "verdicts and the Observer-V2 decision), plus the records found to depend on the same targets: "
                       "the substate search rounds, the substate family decision and the T5 reference they all cite"),
                rule=("each record's own recorded rule and premises are applied unchanged; nothing is generated, "
                      "tuned or selected; no new threshold is introduced and no verdict is computed by one. The "
                      "corrected envelopes are the corrected form of the references those records used: pooled, "
                      "composition-inclusive references, not endorsed here as biological targets. Whether S149's "
                      "correction changes their standing is for the owner and the real-data lane"),
                record_path=record_path(out),
                S159=s159(E), background_rounds=bg, step3=step3(E, entries), factor_family=factor_family(E),
                observer_v2=observer(E), substate_search=substate_search(E),
                substate_family_decision=substate_decision(E), t5_guard=t5_guard(E),
                pending_synthetic_replay=PENDING_REPLAY, not_material=NOT_MATERIAL,
                classified_elsewhere=CLASSIFIED_ELSEWHERE,
                inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in files},
                code_sha256=sha(Path(__file__)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    rec = build(out)
    bg = rec["background_rounds"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    md = Path(a.md)
    md.parent.mkdir(parents=True, exist_ok=True)
    with open(md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(markdown(rec))
    print("faithful:", bg["faithful_to_recorded_counts"], "| entries", bg["entries"], "| accepted old/corrected",
          bg["accepted_under_old"], bg["accepted_under_corrected"], "| max inside old/corrected",
          bg["max_inside_old"], bg["max_inside_corrected"])


if __name__ == "__main__":
    main()
