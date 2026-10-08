#!/usr/bin/env python3
"""S174 synthetic replay: the V77 synthetic results whose statistics were computed on a cache-derived
universe, rerun on the corrected universe with nothing else changed, old beside corrected.

Each replay reran the committed runner with the receipt's original arguments; only --universe (and,
where the runner takes it, the --universe-name of the corrected within-cohort file) and --out differ.
Before a corrected receipt is used, the same runner on the OLD universe must reproduce the committed
receipt exactly, every numeric leaf; that proof is recorded here and the reproduced receipts are
committed beside the corrected ones.

STATISTICAL RULING (owner, 2026-10-07). The corrected pooled p05-p95 envelopes are NOT qualification
targets: S159 shows the corrected real point can lie outside its own donor-bootstrap interval, so a
candidate identical to the real point could fail a gate built on them. Corrected real point estimates
are descriptive reference values; the donor-resampled distributions are uncertainty diagnostics; no
binary "inside every envelope" decision is made until S159 is resolved, and no interval is re-centred.
Accordingly each arm is described, per corrected invariant, by its ratio to the real point, its
position relative to the donor-bootstrap interval (below, inside, above) and its distance from the point
in donor-bootstrap standard deviations. These are descriptions; nothing passes, fails or is selected.

The runners write the universe label TRAIN_PREVALENCE05_19569, the builder's fixed name for the frozen
universe; in s174_replay it denotes the corrected 14,417-address universe, whose path and digest each
receipt records. The isolation runner's console table prints the old real detection row as a fixed
display; no receipt carries real values.

Usage: python summarize_s174_synthetic_replay.py --repro-dir DIR --out JSON --md MD
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

NL = chr(10)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "results" / "v77"
NEW = ROOT / "results" / "v77" / "s174_replay"
REPLAYS = {
    "V77_REALIZATION_ISOLATION_RECEIPT_V2.json": "ISO_V2_OLD_UNIVERSE.json",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2.json": "DR_V2_OLD_UNIVERSE.json",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_HVS_EXPLORATORY.json": "DR_V2_HVS_OLD_UNIVERSE.json",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V2__WITHIN_SEA_AD_EXPLORATORY.json": "DR_V2_SEAAD_OLD_UNIVERSE.json",
}
SUPERSEDED_BEFORE_S174 = {
    "V77_REALIZATION_ISOLATION_RECEIPT_V1.json": "superseded by V2 (S139/S140 scorer mismatch); not replayed",
    "V77_DYNAMIC_RANGE_TOURNAMENT_V1.json": "superseded by V2 (S129/S138 DR5, S139/S140 scorer mismatch); not replayed",
}
STATISTICAL_RULING = dict(
    pooled_envelopes="not qualification targets until S159 is resolved",
    real_point_estimates="descriptive reference values",
    donor_resampled_distributions="uncertainty diagnostics",
    binary_inside_every_envelope_decision="not made",
    recentring="not done; an interval is never moved to make the point fit",
    why="S159: the corrected real point lies outside its own donor-bootstrap p05-p95 interval for some statistics, so a "
        "candidate identical to the real point could fail a gate built on these intervals")
# (layer, statistic, envelope or None). Envelope keys: cal = expression, det = detection, ab = abundance.
INVARIANTS = [("expression", "median_abs_corr", "cal"), ("expression", "frac_abs_gt_0p3", "cal"),
              ("expression", "var_top10_pc", "cal"),
              ("detection", "median_abs_corr", "det"), ("detection", "frac_abs_gt_0p3", "det"),
              ("detection", "mean_degree", "det"), ("detection", "transitivity", "det"),
              ("detection", "largest_community_frac", "det"),
              ("class_separation", "t5_within_over_pooled", None),
              ("abundance", "abundance_max_over_median_nonzero", "ab"), ("abundance", "top1pct_count_share", "ab"),
              ("depth", "median_detected_per_cell", None)]
SHORT = {"expression.median_abs_corr": "expr med|r|", "expression.frac_abs_gt_0p3": "expr |r|>0.3",
         "expression.var_top10_pc": "expr top10 var", "detection.median_abs_corr": "det med|r|",
         "detection.frac_abs_gt_0p3": "det |r|>0.3", "detection.mean_degree": "det degree",
         "detection.transitivity": "det transitivity", "detection.largest_community_frac": "det community",
         "class_separation.t5_within_over_pooled": "T5", "abundance.abundance_max_over_median_nonzero": "max/median",
         "abundance.top1pct_count_share": "top1%", "depth.median_detected_per_cell": "detected/cell"}
TWELVE_FOLD_ARM = "DR2_scale_2p50"
GRADED = ("DR1_scale_1p20_baseline", "DR2_scale_2p50", "DR3_scale_4p00", "DR4_scale_5p50")
TIMING = ("seconds", "wall_seconds", "elapsed", "runtime")

_spec = importlib.util.spec_from_file_location("s174_compare", HERE / "compare_s174_rebuild.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)


def load(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def finite(x) -> bool:
    return x is not None and math.isfinite(float(x))


def r4(x):
    return round(float(x), 4) if finite(x) else None


def reproduction(committed: Path, reproduced: Path) -> dict:
    """Every numeric leaf of the committed receipt equals the reproduced one (timing leaves aside)."""
    a, b = C.numeric_leaves(load(committed)), C.numeric_leaves(load(reproduced))
    keep = lambda p: not any(t in p.split(".")[-1] for t in TIMING)
    a = {k: v for k, v in a.items() if keep(k)}
    b = {k: v for k, v in b.items() if keep(k)}
    differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return dict(exact=not differing, numeric_leaves=len(a), differing=differing[:20],
                reproduced_sha256=sha(reproduced))


def _median_detected(rec):
    hits = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "median_detected" and isinstance(v, (int, float)):
                    hits.append(float(v))
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(rec)
    assert len(set(hits)) == 1, hits
    return hits[0]


def references() -> dict:
    """Per invariant and era: the real point, and the donor-bootstrap interval and SD where one exists."""
    env = {}
    for tag, name in (("cal", "V77_REAL_CALIBRATION_ENVELOPE_V1.json"), ("det", "V77_REAL_DETECTION_ENVELOPE_V1.json"),
                      ("ab", "V77_REAL_ABUNDANCE_ENVELOPE_V1.json")):
        env[("old", tag)] = load(OLD / name)["ACCEPTANCE_ENVELOPES"]
        env[("corrected", tag)] = load(NEW / name)["ACCEPTANCE_ENVELOPES"]
    other = {}
    for era, d in (("old", OLD), ("corrected", NEW)):
        other[(era, "t5_within_over_pooled")] = load(d / "V77_REAL_TRAIN_TOPOLOGY_CALIBRATION_V1.json")[
            "T5_class_conditional_structure"]["within_over_pooled_ratio"]
        other[(era, "median_detected_per_cell")] = _median_detected(load(d / "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1.json"))
    R = {}
    for layer, stat, tag in INVARIANTS:
        key = f"{layer}.{stat}"
        R[key] = {}
        for era in ("old", "corrected"):
            if tag is None:
                R[key][era] = dict(point=other[(era, stat)], interval=None, boot_sd=None, point_inside_own_interval=None)
            else:
                e = env[(era, tag)][stat]
                lo, hi = e["accept_low"], e["accept_high"]
                R[key][era] = dict(point=e["point"], interval=[lo, hi], boot_sd=e.get("boot_sd"),
                                   point_inside_own_interval=lo <= e["point"] <= hi)
    return R


def value(m: dict, layer: str, stat: str):
    """An arm's value for one invariant, read from its matched scoring."""
    if layer in ("expression", "detection"):
        return m[layer][stat]
    if layer == "class_separation":
        return m["t5"]["within_over_pooled"]
    if layer == "abundance":
        return m["abundance"][stat]
    return m["median_detected_per_cell"]


def describe(x, ref: dict) -> dict:
    p, iv, sd = ref["point"], ref["interval"], ref["boot_sd"]
    pos = None
    if iv is not None and finite(x):
        pos = "below" if x < iv[0] else ("above" if x > iv[1] else "inside")
    return dict(value=r4(x), point=r4(p), over_point=r4(x / p) if finite(x) and p else None,
                position=pos, sd_from_point=r4((x - p) / sd) if finite(x) and sd else None)


def arm_profile(arm: str, old: dict, new: dict, R: dict) -> dict:
    mo, mn = old["matched_to_real_envelopes"], new["matched_to_real_envelopes"]
    inv = {}
    for layer, stat, _ in INVARIANTS:
        key = f"{layer}.{stat}"
        inv[key] = dict(old_universe=describe(value(mo, layer, stat), R[key]["old"]),
                        corrected_universe=describe(value(mn, layer, stat), R[key]["corrected"]))
    pos = lambda era, want: [k for k, v in inv.items() if v[era]["position"] == want]
    return dict(arm=arm, invariants=inv,
                corrected_inside=pos("corrected_universe", "inside"), corrected_below=pos("corrected_universe", "below"),
                corrected_above=pos("corrected_universe", "above"),
                old_inside=pos("old_universe", "inside"),
                canonical_genes_lost=dict(old_universe=mo["canonical_genes_lost"],
                                          corrected_universe=mn["canonical_genes_lost"]))


def isolation(R) -> dict:
    name = "V77_REALIZATION_ISOLATION_RECEIPT_V2.json"
    o, n = load(OLD / name)["arms"], load(NEW / name)["arms"]
    arms = [arm_profile(a, o[a], n[a], R) for a in o]
    A, B = arms[0]["invariants"], arms[1]["invariants"]
    t, d = "detection.transitivity", "detection.mean_degree"
    persists = all(B[k]["corrected_universe"]["value"] < A[k]["corrected_universe"]["value"] for k in (t, d))
    binary = {a: {k: r4(o[a]["topology_v1_binary_hvg__NOT_COMPARABLE_TO_REAL"][k])
                  for k in ("frac_abs_gt_0p3", "transitivity", "mean_degree")} for a in o}
    return dict(
        arms=arms, collapse_from_counting_alone_persists_on_the_corrected_universe=persists,
        audit_correction_figures_came_from=dict(
            scorer="topology_v1_binary_hvg__NOT_COMPARABLE_TO_REAL (S139/S140), old universe", values=binary),
        reading=(f"between arms identical except realization, Poisson counting lowers detection transitivity from "
                 f"{A[t]['corrected_universe']['value']} to {B[t]['corrected_universe']['value']} and mean degree from "
                 f"{A[d]['corrected_universe']['value']} to {B[d]['corrected_universe']['value']} on the corrected "
                 f"universe (old universe: {A[t]['old_universe']['value']} to {B[t]['old_universe']['value']}, "
                 f"{A[d]['old_universe']['value']} to {B[d]['old_universe']['value']}); the collapse "
                 f"{'persists' if persists else 'does not persist'}. Relative to the corrected real points the "
                 f"deterministic arm is {A[t]['corrected_universe']['over_point']} and "
                 f"{A[d]['corrected_universe']['over_point']} times, the Poisson arm "
                 f"{B[t]['corrected_universe']['over_point']} and {B[d]['corrected_universe']['over_point']} times"))


def twelve_fold(arm: dict, verdict_recorded: dict) -> dict:
    """The 12-fold arm is recorded as an observation. It is not a winner and is not selected."""
    v = arm["invariants"]
    c = lambda k: v[k]["corrected_universe"]
    dens, deg, tr = c("detection.frac_abs_gt_0p3"), c("detection.mean_degree"), c("detection.transitivity")
    ab, dp = c("abundance.abundance_max_over_median_nonzero"), c("depth.median_detected_per_cell")
    facts = dict(density_inside=dens["position"] == "inside", degree_inside=deg["position"] == "inside",
                 transitivity_overshoots=tr["value"] > tr["point"],
                 abundance_outside_interval=ab["position"] != "inside", depth_below_real=dp["value"] < dp["point"])
    rec = verdict_recorded.get(TWELVE_FOLD_ARM, {})
    return dict(
        arm=TWELVE_FOLD_ARM, status="OBSERVATION; NOT A WINNER; NOT SELECTED", facts=facts,
        detection_density=dens, detection_mean_degree=deg, detection_transitivity=tr,
        abundance_max_over_median=ab, median_detected_per_cell=dp,
        verdict_recorded_objections=rec.get("rejection_reasons"),
        reading=(f"on the corrected universe the 12-fold arm lands close to the corrected real detection density "
                 f"({dens['value']} against {dens['point']}, {dens['over_point']} times, {dens['position']} the "
                 f"interval) and mean degree ({deg['value']} against {deg['point']}, {deg['over_point']} times, "
                 f"{deg['position']}). Its transitivity "
                 f"{'overshoots' if facts['transitivity_overshoots'] else 'does not overshoot'} "
                 f"({tr['value']} against {tr['point']}, {tr['over_point']} times); its abundance max/median is "
                 f"{ab['over_point']} times the real point ({ab['position']} the interval) and its median detected per "
                 f"cell {dp['over_point']} times the real value, so the abundance and depth objections the verdict "
                 f"recorded {'still apply' if facts['abundance_outside_interval'] and facts['depth_below_real'] else 'need re-reading'}. "
                 f"It is recorded as an observation, not as a winner or a selected model"))


def tournament(R) -> dict:
    name = "V77_DYNAMIC_RANGE_TOURNAMENT_V2.json"
    o, n = load(OLD / name)["arms"], load(NEW / name)["arms"]
    arms = [arm_profile(a, o[a], n[a], R) for a in o]
    by = {a["arm"]: a["invariants"] for a in arms}
    t = "detection.transitivity"

    def monotone(era, k):
        v = [by[a][k][era]["value"] for a in GRADED]
        return all(x < y for x, y in zip(v, v[1:]))
    above_old = [a for a in by if by[a][t]["old_universe"]["value"] > by[a][t]["old_universe"]["point"]]
    above_new = [a for a in by if by[a][t]["corrected_universe"]["value"] > by[a][t]["corrected_universe"]["point"]]
    verdict = load(OLD / "V77_DYNAMIC_RANGE_VERDICT_V1.json")
    ab = "abundance.abundance_max_over_median_nonzero"
    ab_out = [a for a in by if by[a][ab]["corrected_universe"]["position"] != "inside"]
    depth = [by[a]["depth.median_detected_per_cell"]["corrected_universe"]["over_point"] for a in by]
    return dict(
        arms=arms,
        recorded_verdict=verdict["VERDICT"], verdict_cites=verdict["tournament_receipt"]["path"],
        verdict_note=("the verdict was written on tournament V1, whose DR5 values the register withdrew (S129) and "
                      "whose scorer was not comparable to the real envelopes (S139/S140); its claims are restated here "
                      "with the V2 matched numbers"),
        transitivity_rises_monotonically_over_graded_arms=dict(old_universe=monotone("old_universe", t),
                                                               corrected_universe=monotone("corrected_universe", t)),
        mean_degree_rises_monotonically_over_graded_arms=dict(
            old_universe=monotone("old_universe", "detection.mean_degree"),
            corrected_universe=monotone("corrected_universe", "detection.mean_degree")),
        arms_above_the_real_transitivity_point=dict(old_universe=above_old, corrected_universe=above_new),
        verdict_recorded_grounds_against_corrected_references=dict(
            abundance_max_over_median_outside_the_corrected_interval=ab_out, of=len(arms),
            median_detected_per_cell_over_corrected_real=[min(depth), max(depth)]),
        twelve_fold_arm=twelve_fold(next(a for a in arms if a["arm"] == TWELVE_FOLD_ARM),
                                    verdict["BUT_EVERY_ARM_IS_REJECTED"]["per_arm"]),
        reading=(f"detection transitivity above the real point: {', '.join(above_old) or 'none'} on the old universe "
                 f"against the old point; {', '.join(above_new) or 'none'} on the corrected universe against the "
                 f"corrected point, so the verdict's 'the mechanism overshoots the real transitivity' was measured "
                 f"against the old point. The grounds the verdict recorded for rejecting every arm remain against the "
                 f"corrected references: abundance max/median lies outside the corrected interval for {len(ab_out)} of "
                 f"{len(arms)} arms, and the median detected per cell is {min(depth)} to {max(depth)} times the corrected "
                 f"real value"))


def coverage(arms: list) -> dict:
    """Per corrected invariant: the range of the replayed arms' ratios to the real point, and whether that range
    brackets the real value. It describes what this family spans by its varied parameter; it ranks nothing."""
    out = {}
    for layer, stat, _ in INVARIANTS:
        k = f"{layer}.{stat}"
        r = [a["invariants"][k]["corrected_universe"]["over_point"] for a in arms]
        r = [x for x in r if x is not None]
        out[k] = dict(min_over_point=min(r), max_over_point=max(r), real_point_bracketed=min(r) <= 1 <= max(r))
    return out


def class_separation(arms: list) -> dict:
    sd = load(OLD / "V77_SUBSTATE_FAMILY_DECISION_V1.json")["T5_HARD_GUARD_HELD_THROUGHOUT"]["why_it_is_structural_here"]
    k = "class_separation.t5_within_over_pooled"
    t5 = [a["invariants"][k]["corrected_universe"]["value"] for a in arms]
    real = arms[0]["invariants"][k]["corrected_universe"]["point"]
    return dict(corrected_real=real, replayed_arm_range=[min(t5), max(t5)], every_arm_above_the_real_ratio=min(t5) > real,
                recorded_generator_design=sd,
                reading=(f"every replayed arm has a within-class over pooled ratio of {min(t5)} to {max(t5)}, against a "
                         f"corrected real {real}: none reproduces the part of the real pooled dependence that comes from "
                         f"broad cell-class separation. The substate decision records that its sub-states are drawn "
                         f"independently of annotated cell class by construction, which is consistent with this. "
                         f"Recorded as a constraint on the next design; it does not change this replay")
                if min(t5) > real else "a replayed arm reaches the corrected real ratio")


def exploratory() -> dict:
    out = {}
    for name in [n for n in REPLAYS if "EXPLORATORY" in n]:
        o, n = load(OLD / name), load(NEW / name)
        out[name] = dict(universe=dict(old=o["frozen"]["evaluation_universe"], corrected=n["frozen"]["evaluation_universe"]),
                         arms=[dict(arm=a, **{k: dict(old_universe=r4(o["arms"][a]["matched_to_real_envelopes"]["detection"][k]),
                                                      corrected_universe=r4(n["arms"][a]["matched_to_real_envelopes"]["detection"][k]))
                                               for k in ("median_abs_corr", "frac_abs_gt_0p3", "transitivity", "mean_degree")})
                               for a in o["arms"]])
    return dict(status="EXPLORATORY; within-cohort references are not authorized for synthetic pass or fail, and none "
                       "are applied", **out)


def build(repro_dir: Path, out: Path) -> dict:
    R = references()
    repro = {name: reproduction(OLD / name, repro_dir / rp) for name, rp in REPLAYS.items()}
    corrected = {}
    for name in REPLAYS:
        n = load(NEW / name)
        corrected[name] = dict(sha256=sha(NEW / name), command=n.get("command"), source_commit=n.get("source_commit"),
                               provenance_status=n.get("provenance_status"))
    try:
        rp = out.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rp = out.as_posix()
    iso, dr = isolation(R), tournament(R)
    same = {era: load(d / "V77_REALIZATION_ISOLATION_RECEIPT_V2.json")["arms"]["B_poisson"]["matched_to_real_envelopes"]
            == load(d / "V77_DYNAMIC_RANGE_TOURNAMENT_V2.json")["arms"]["DR1_scale_1p20_baseline"]["matched_to_real_envelopes"]
            for era, d in (("old", OLD), ("corrected", NEW))}
    assert all(same.values()), same
    all_arms = iso["arms"] + [a for a in dr["arms"] if a["arm"] != "DR1_scale_1p20_baseline"]
    refs = {k: {era: dict(point=r4(v[era]["point"]), interval=[r4(x) for x in v[era]["interval"]] if v[era]["interval"]
                          else None, boot_sd=r4(v[era]["boot_sd"]),
                          point_inside_own_interval=v[era]["point_inside_own_interval"])
                for era in ("old", "corrected")} for k, v in R.items()}
    return dict(
        schema="S174_SYNTHETIC_REPLAY_V1", record_path=rp,
        rule=("each replay reran the committed runner with the receipt's original arguments; only the universe (and "
              "--out) changed; a rerun on the old universe reproduced each committed receipt first; no seed, arm, "
              "preprocessing or scoring rule changed and no arm was tuned after the corrected target was seen"),
        statistical_ruling=STATISTICAL_RULING,
        universe_label_note=("the runners write TRAIN_PREVALENCE05_19569, the builder's fixed name for the frozen universe; "
                             "in s174_replay it denotes the corrected 14,417-address universe"),
        abundance_note=("S130: abundance max/median on the frozen universe divides by the median of nonzero gene means "
                        "and so also penalises detection coverage; read it that way"),
        reproduction_on_the_old_universe=repro, corrected_receipts=corrected,
        superseded_before_s174=SUPERSEDED_BEFORE_S174,
        references=refs,
        s159_points_outside_their_own_interval=[k for k, v in refs.items()
                                                if v["corrected"]["point_inside_own_interval"] is False],
        realization_isolation=iso, dynamic_range_tournament=dr, exploratory=exploratory(),
        dr1_identical_to_b_poisson=same,
        distinct_replayed_arms=[a["arm"] for a in all_arms],
        invariant_coverage_across_replayed_arms=coverage(all_arms),
        class_separation_across_replayed_arms=class_separation(all_arms),
        inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in
                [OLD / n for n in REPLAYS] + [NEW / n for n in REPLAYS] + [OLD / "V77_DYNAMIC_RANGE_VERDICT_V1.json"]},
        code_sha256=sha(Path(__file__)))


def _band_table(arms: list, era: str) -> list[str]:
    keys = [f"{layer}.{stat}" for layer, stat, _ in INVARIANTS]
    mark = {"inside": "in", "below": "below", "above": "above", None: "point only"}
    out = ["| arm | " + " | ".join(SHORT[k] for k in keys) + " |", "|---|" + "---|" * len(keys)]
    for a in arms:
        cells = []
        for k in keys:
            d = a["invariants"][k][era]
            cells.append(f"{d['over_point']} ({mark[d['position']]})")
        out.append(f"| {a['arm']} | " + " | ".join(cells) + " |")
    return out


def markdown(rec: dict) -> str:
    iso, dr = rec["realization_isolation"], rec["dynamic_range_tournament"]
    L = ["# S174 synthetic replay", "",
         "V77 synthetic results whose statistics were computed on the cache-derived evaluation universe, rerun on the "
         f"corrected universe with nothing else changed. JSON record: `{rec['record_path']}`.", "",
         f"Rule: {rec['rule']}.", "",
         "## Statistical ruling", ""]
    for k, v in rec["statistical_ruling"].items():
        L.append(f"- {k.replace('_', ' ')}: {v}")
    L += ["", "Every cell below is a description: the ratio to the real point, and in brackets the position relative to "
              "the donor-bootstrap interval (`point only` where the reference has no interval). Nothing passes, fails "
              "or is selected.", "",
          f"S159: the corrected real point lies outside its own interval for {', '.join(rec['s159_points_outside_their_own_interval'])}.",
          "", f"Universe label: {rec['universe_label_note']}. {rec['abundance_note']}.", "",
          "## Reproduction on the old universe", "", "| receipt | exact | numeric leaves |", "|---|---|---|"]
    for k, v in rec["reproduction_on_the_old_universe"].items():
        L.append(f"| {k} | {v['exact']} | {v['numeric_leaves']} |")
    L += ["", "Superseded before S174, not replayed:", ""]
    for k, v in rec["superseded_before_s174"].items():
        L.append(f"- `{k}`: {v}")
    L += ["", "## Reference values", "", "| invariant | old point | corrected point | corrected interval | "
          "corrected point inside its own interval |", "|---|---|---|---|---|"]
    for k, v in rec["references"].items():
        L.append(f"| {k} | {v['old']['point']} | {v['corrected']['point']} | {v['corrected']['interval'] or '-'} | "
                 f"{v['corrected']['point_inside_own_interval'] if v['corrected']['interval'] else '-'} |")
    arms = iso["arms"] + dr["arms"]
    L += ["", "## Per-arm description against the corrected real values (corrected universe)", ""] + \
        _band_table(arms, "corrected_universe") + \
        ["", "## The same arms against the old real values (old universe), for comparison", ""] + \
        _band_table(arms, "old_universe")
    cov = rec["invariant_coverage_across_replayed_arms"]
    L += ["", "## Which corrected invariants the replayed arms span", "",
          f"Distinct arms: {', '.join(rec['distinct_replayed_arms'])} (DR1 is the same arm as B_poisson and is counted "
          "once). A bracketed invariant is one whose real value lies between the lowest and highest arm; this describes "
          "what the family spans and ranks nothing.", "",
          "| invariant | lowest arm / point | highest arm / point | real value bracketed |", "|---|---|---|---|"]
    for k, v in cov.items():
        L.append(f"| {k} | {v['min_over_point']} | {v['max_over_point']} | {v['real_point_bracketed']} |")
    L += ["", f"Class separation: {rec['class_separation_across_replayed_arms']['reading']}.", ""]
    L += ["", "## Realization isolation (V2)", "", f"Reading: {iso['reading']}.", "",
          f"The audit correction's headline figures came from {iso['audit_correction_figures_came_from']['scorer']}: "
          f"{json.dumps(iso['audit_correction_figures_came_from']['values'])}.", "",
          "## Dynamic-range tournament (V2)", "",
          f"Recorded verdict: `{dr['recorded_verdict']}` (cites `{dr['verdict_cites']}`). {dr['verdict_note']}.", "",
          f"Transitivity rises monotonically over the graded arms: {dr['transitivity_rises_monotonically_over_graded_arms']}; "
          f"mean degree: {dr['mean_degree_rises_monotonically_over_graded_arms']}.", "", f"Reading: {dr['reading']}.", "",
          f"### The 12-fold arm ({dr['twelve_fold_arm']['arm']}): {dr['twelve_fold_arm']['status']}", "",
          dr["twelve_fold_arm"]["reading"] + ".", "",
          f"Objections the verdict recorded for this arm: {'; '.join(dr['twelve_fold_arm']['verdict_recorded_objections'] or [])}.",
          "", "## Exploratory within-cohort variants", "", rec["exploratory"]["status"] + ".", ""]
    for name, v in rec["exploratory"].items():
        if name == "status":
            continue
        L += [f"`{name}` (universe {v['universe']['old']} to {v['universe']['corrected']}):", "",
              "| arm | median abs corr | frac > 0.3 | transitivity | mean degree |", "|---|---|---|---|---|"]
        for a in v["arms"]:
            L.append(f"| {a['arm']} | " + " | ".join(f"{a[k]['old_universe']} / {a[k]['corrected_universe']}"
                                                   for k in ("median_abs_corr", "frac_abs_gt_0p3", "transitivity",
                                                             "mean_degree")) + " |")
        L.append("")
    L += ["Exploratory cells give old universe / corrected universe."]
    return NL.join(L) + NL


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repro-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    rec = build(Path(a.repro_dir), out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    with open(Path(a.md), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(markdown(rec))
    print({k: v["exact"] for k, v in rec["reproduction_on_the_old_universe"].items()})
    print(rec["realization_isolation"]["reading"])
    print(rec["dynamic_range_tournament"]["reading"])
    print(rec["dynamic_range_tournament"]["twelve_fold_arm"]["reading"])


if __name__ == "__main__":
    main()
