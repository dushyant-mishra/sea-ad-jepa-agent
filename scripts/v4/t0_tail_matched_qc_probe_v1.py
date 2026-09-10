#!/usr/bin/env python3
"""Matched-QC held-out validation of the frozen tail grouping. Step 4.

Implements `configs/v4/t0_tail_matched_qc_contract_v1.json` exactly, as frozen
by the owner in `bc60a921` before this module was written.

Diagnostic only. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`, and no balance threshold, caliper, alternative
matching method, donor subset or holdout feature subset is chosen from these
results.

The question: after tail and rest cells are compared only inside their
overlapping Q_DEPTH/Q_DETECT support **and** deterministically matched 1:1 on
those two axes, does the independent COHERENCE_HOLDOUT program remain
donor-consistent?

Why this is the step that matters. The common-support precursor showed
restriction alone does not equalise the comparison — it left the frozen QC
contrast higher than before, because that statistic divides by a standard
deviation the restriction shrinks. Matching equalises the two groups rather than
merely bounding their range, and the contract's eligibility rule makes it
workable: a minimum of five matched pairs and ten decision donors, the same
frozen numbers, applied to a design where the rest group equals the tail group
by construction, with the exact common-direction test applied directly to the
eligible donor vectors rather than through the adjudicator that enforces a rest
minimum that 1:1 matching cannot satisfy.

Everything frozen is reused unmodified: the tail grouping, the per-cell QC
metrics, the discovery-derived holdout scale and decision mask, the holdout
vector construction, and the exact sign-flip test. Matching uses no pathology
and no holdout expression — only the two QC axes — so the validation features
cannot have influenced which cells were compared.

Pathology-blind: no AT8 value is read.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linear_sum_assignment
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_discovery_scalar_matrix_v1 as dm  # noqa: E402
import t0_numeric_environment_v1 as numeric_environment  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

STOP = "STOP_T0_TAIL_MATCHED_QC_REFUSED"
CONTRACT = "configs/v4/t0_tail_matched_qc_contract_v1.json"
REPORT = "T0_TAIL_MATCHED_QC_PROBE.json"
DONOR_CSV = "T0_TAIL_MATCHED_QC_DONORS.csv"
PAIR_CSV = "T0_TAIL_MATCHED_QC_PAIRS.csv"

METRIC_NAMES = ("Q_DEPTH", "Q_DETECT")
MIN_MATCHED_PAIRS = 5
MIN_DECISION_DONORS = 10

# --- corrections to the frozen contract, applied under explicit authority ---
# Both are additive: every quantity the contract prescribes is still computed
# and published. See the module docstring and the findings document.
SIZE_CONTROL_NAMESPACE = b"T0-TAIL-MATCHED-QC-SIZE-CONTROL-V1"
SIZE_CONTROL_REPLICATES = 20
CORRECTIONS = [
    {
        "id": "FIXED_DENOMINATOR_BALANCE",
        "what": "Post-match standardized mean differences are additionally "
                "reported against the pre-match denominator, not only against "
                "the matched subset's own standard deviation.",
        "why": "The frozen _donor_delta divides by the SD of whatever subset it "
               "is handed, so a pre-match and a post-match SMD computed that "
               "way have different denominators and are not comparable. The "
               "common-support precursor demonstrated the artefact: the frozen "
               "contrast rose from 0.2947 to 0.3228 because restriction shrank "
               "the standardiser. A pre/post pair on shifting denominators "
               "would make the balance claim uninterpretable.",
        "contract_quantity_still_reported": True,
    },
    {
        "id": "SIZE_MATCHED_UNMATCHED_CONTROL",
        "what": "Coherence is additionally computed with the same matched tail "
                "cells against an equal number of rest cells drawn at random "
                "from common support instead of matched on QC, over %d "
                "deterministic replicates." % SIZE_CONTROL_REPLICATES,
        "why": "1:1 matching shrinks each donor's comparison group from "
               "hundreds of cells to the pair count, which adds noise to every "
               "donor vector and lowers a cross-donor coherence statistic for "
               "reasons of power alone. Without this control a drop in matched "
               "coherence cannot be attributed to removing the confound rather "
               "than to the smaller comparison group.",
        "contract_quantity_still_reported": True,
    },
]


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def common_support(qc: np.ndarray, tail: np.ndarray):
    """The contract's rectangular intersection, per donor, per metric."""
    values = np.asarray(qc, dtype=np.float64)
    mask = np.asarray(tail, dtype=bool)
    if mask.sum() == 0 or (~mask).sum() == 0:
        return None, None, "donor has no tail or no rest cells"
    low = np.maximum(values[mask].min(axis=0), values[~mask].min(axis=0))
    high = np.minimum(values[mask].max(axis=0), values[~mask].max(axis=0))
    if np.any(high < low):
        return None, None, "empty overlap on at least one QC metric"
    inside = np.all((values >= low) & (values <= high), axis=1)
    interval = {"low": [float(x) for x in low],
                "high": [float(x) for x in high]}
    return inside, interval, None


def pooled_rank_space(qc: np.ndarray) -> np.ndarray:
    """Pooled empirical midranks per metric, scaled to [0, 1].

    Pooled over the donor's common-support cells, tail and rest together, so the
    transform does not depend on the grouping. Midranks handle ties, which count
    data produces in quantity.
    """
    values = np.asarray(qc, dtype=np.float64)
    out = np.empty_like(values)
    for column in range(values.shape[1]):
        ranks = rankdata(values[:, column], method="average")
        span = ranks.max() - ranks.min()
        out[:, column] = (ranks - ranks.min()) / span if span > 0 else 0.0
    return out


def match_pairs(rank_space: np.ndarray, tail: np.ndarray,
                stable_keys: np.ndarray):
    """Minimum-total-distance 1:1 matching without replacement.

    Both groups are pre-sorted by canonical stable-key byte order before the
    assignment is solved, which is the contract's deterministic tie-break: the
    cost matrix is then a fixed function of the data, and the solver is
    deterministic on it.
    """
    mask = np.asarray(tail, dtype=bool)
    tail_index = np.flatnonzero(mask)
    rest_index = np.flatnonzero(~mask)
    tail_index = tail_index[np.argsort(
        [str(stable_keys[i]).encode() for i in tail_index], kind="stable")]
    rest_index = rest_index[np.argsort(
        [str(stable_keys[i]).encode() for i in rest_index], kind="stable")]

    expected = min(len(tail_index), len(rest_index))
    if expected == 0:
        return [], []
    difference = (rank_space[tail_index][:, None, :]
                  - rank_space[rest_index][None, :, :])
    cost = np.sum(difference ** 2, axis=2)
    rows, columns = linear_sum_assignment(cost)
    if len(rows) != expected:
        _fail("matched %d pairs, expected %d" % (len(rows), expected))
    pairs = [(int(tail_index[r]), int(rest_index[c])) for r, c in
             zip(rows, columns)]
    distances = [float(cost[r, c]) for r, c in zip(rows, columns)]
    # ONE_TO_ONE_NO_REPLACEMENT
    if len({p[0] for p in pairs}) != len(pairs) or \
            len({p[1] for p in pairs}) != len(pairs):
        _fail("a cell appeared in more than one pair")
    return pairs, distances


def standardized_difference(qc: np.ndarray, tail: np.ndarray,
                            frozen_qc) -> list[float]:
    """The frozen per-donor standardized contrast, unchanged."""
    return [float(x) for x in frozen_qc._donor_delta(qc, tail)]


def fixed_denominator_smd(qc: np.ndarray, tail: np.ndarray,
                          denominator: np.ndarray) -> list[float]:
    """Standardized mean difference against a denominator fixed in advance.

    The correction. `_donor_delta` restandardises on whatever subset it sees, so
    its pre-match and post-match values sit on different scales and a change
    between them says nothing about balance. Holding the denominator at the
    donor's pre-match spread makes the two comparable, which is the convention
    the matching literature uses for exactly this reason.
    """
    values = np.asarray(qc, dtype=np.float64)
    mask = np.asarray(tail, dtype=bool)
    difference = values[mask].mean(axis=0) - values[~mask].mean(axis=0)
    safe = np.where(denominator > 0, denominator, 1.0)
    return [float(x) for x in (difference / safe)]


def size_control_rest(rest_local: np.ndarray, count: int, donor: str,
                      replicate: int) -> np.ndarray:
    """`count` rest cells from common support, chosen at random not by QC.

    Deterministic per donor and replicate, so the control is reproducible and
    independent of iteration order.
    """
    digest = hashlib.sha256(
        SIZE_CONTROL_NAMESPACE + b"\x00" + str(replicate).encode() + b"\x00"
        + str(donor).encode()).digest()
    generator = np.random.default_rng(
        int.from_bytes(digest[:8], "little", signed=False))
    return generator.choice(rest_local, size=count, replace=False)


def run(*, confirmation_pkg: Path, discovery_pkg: Path, tail_dir: Path,
        membership: Path, feature_split: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    contract_bytes = (root / CONTRACT).read_bytes()
    contract = json.loads(contract_bytes.decode("utf-8"))
    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        _fail("the matched-QC contract is not frozen")
    eligibility = contract["donor_eligibility_for_holdout_test"]
    if int(eligibility["minimum_matched_pairs"]) != MIN_MATCHED_PAIRS or \
            int(eligibility["minimum_decision_donors"]) != MIN_DECISION_DONORS:
        _fail("eligibility minima differ from the frozen contract")

    conf_summary = json.loads(
        (confirmation_pkg / "T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))
    decision = json.loads(
        (confirmation_pkg / "T0_V20_ADJUDICATION_DECISION.json"
         ).read_text(encoding="utf-8"))
    if decision.get("tail_terminal") != "RARE_TAIL_UNDERDETERMINED_MEASUREMENT":
        _fail("expected the QC-vetoed tail terminal, found %r"
              % decision.get("tail_terminal"))
    frozen_preflight = decision["tail_preflight"]
    disc_summary = json.loads(
        (discovery_pkg / "T0_DISCOVERY_STAGE_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))

    conf = dm.load_cache(
        confirmation_pkg,
        expected_matrix_sha256=conf_summary["confirmation_matrix_sha256"],
        log=lambda m: None)
    disc = dm.load_cache(
        discovery_pkg,
        expected_matrix_sha256=disc_summary["discovery_scalar_matrix_sha256"],
        log=lambda m: None)
    if conf is None or disc is None:
        _fail("both digest-verified matrix caches are required")

    raw = stage2a._frozen("t0_confirmation_raw_v1")
    preflight = stage2a._frozen("t0_tail_preflight_raw_v1")
    exact_mod = stage2a._frozen("t0_coherence_exact_v1")
    loo_mod = stage2a._frozen("t0_coherence_statistic_v1")
    frozen_qc = stage2a._frozen("t0_tail_qc_randomization_v1")
    feature_mod = stage2a._frozen("t0_feature_authority_v1")

    feature = feature_mod.load_feature_authority(str(feature_split))
    roles = feature.feature_role.to_numpy()
    address_ids = feature.molecular_address_id.astype(str).to_numpy()
    scoring_pos = np.flatnonzero(roles == "SCORING")
    holdout_pos = np.flatnonzero(roles == "COHERENCE_HOLDOUT")
    if set(scoring_pos.tolist()) & set(holdout_pos.tolist()):
        _fail("SCORING and COHERENCE_HOLDOUT positions overlap")

    disc_csr = disc["matrix"].tocsr() if sp.issparse(disc["matrix"]) \
        else sp.csr_matrix(disc["matrix"])
    scale, decision_mask = preflight.discovery_holdout_scale(
        holdout_raw_counts=disc_csr[:, holdout_pos],
        donor_id=disc["donor_id"], stable_key=disc["stable_key"],
        source_library=disc["source_library"])
    features = int(decision_mask.sum())
    expected_features = int(
        contract["heldout_validation"]["decision_feature_count_expected"])
    if features != expected_features or \
            features != int(frozen_preflight["holdout_decision_features"]):
        _fail("holdout decision features %d do not match the contract's %d"
              % (features, expected_features))
    log("frozen holdout scale reproduces %d decision features" % features)

    summaries = raw.confirmation_summaries_from_raw(
        target_dir=str(discovery_pkg / "target"), tail_dir=str(tail_dir),
        scalar_raw_counts=conf["matrix"],
        scalar_feature_ids=conf["feature_ids"],
        matrix_id=conf["matrix_id"], local_row=conf["local_row"],
        cell_id=conf["cell_id"], donor_id=conf["donor_id"],
        stable_key=conf["stable_key"],
        source_library=conf["source_library"],
        feature_split_csv=str(feature_split), membership_csv=str(membership))

    frozen_masks = summaries["tail_masks_by_donor"]
    donors = [d for d in summaries["donor_table"]["donor_id"].tolist()
              if d in frozen_masks]
    indices = summaries["cell_indices_by_donor"]
    keys = summaries["stable_keys_by_donor"]
    qc_by_donor = summaries["qc_by_donor"]

    conf_csr = conf["matrix"].tocsr() if sp.issparse(conf["matrix"]) \
        else sp.csr_matrix(conf["matrix"])
    library = np.asarray(conf["source_library"], dtype=np.float64)

    donor_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    eligible: list[str] = []
    excluded: dict[str, str] = {}
    matched_selection: dict[str, dict[str, Any]] = {}

    for donor in donors:
        qc = np.asarray(qc_by_donor[donor], dtype=np.float64)
        mask = np.asarray(frozen_masks[donor], dtype=bool)
        donor_keys = np.asarray(keys[donor])
        inside, interval, reason = common_support(qc, mask)
        if inside is None:
            excluded[str(donor)] = reason
            log("  %-13s excluded: %s" % (donor, reason))
            continue

        pre = standardized_difference(qc, mask, frozen_qc)
        cs_qc = qc[inside]
        cs_mask = mask[inside]
        cs_keys = donor_keys[inside]
        cs_local = np.flatnonzero(inside)

        if cs_mask.sum() == 0 or (~cs_mask).sum() == 0:
            excluded[str(donor)] = "no tail or no rest cell inside common support"
            log("  %-13s excluded: %s" % (donor, excluded[str(donor)]))
            continue

        ranks = pooled_rank_space(cs_qc)
        pairs, distances = match_pairs(ranks, cs_mask, cs_keys)
        n_pairs = len(pairs)

        # PAIR_COUNT_EXACTLY_MIN_OF_COMMON_SUPPORT_GROUP_COUNTS
        if n_pairs != min(int(cs_mask.sum()), int((~cs_mask).sum())):
            _fail("donor %s matched %d pairs against the expected minimum"
                  % (donor, n_pairs))

        matched_tail = [cs_local[p[0]] for p in pairs]
        matched_rest = [cs_local[p[1]] for p in pairs]
        matched_local = np.asarray(matched_tail + matched_rest, dtype=np.int64)
        matched_mask = np.concatenate([np.ones(n_pairs, bool),
                                       np.zeros(n_pairs, bool)])
        # MATCHED_CELLS_INSIDE_COMMON_SUPPORT
        if not np.all(inside[matched_local]):
            _fail("a matched cell lies outside common support for %s" % donor)
        # FROZEN_TAIL_MASK_EXACT
        if not np.array_equal(mask[matched_local], matched_mask):
            _fail("matched labels differ from the frozen mask for %s" % donor)

        post = standardized_difference(qc[matched_local], matched_mask,
                                       frozen_qc) if n_pairs >= 2 else [None,
                                                                        None]
        # The correction: same denominator before and after, so the pair is
        # comparable and a fall genuinely means the groups became more alike.
        pre_denominator = np.std(qc, axis=0, ddof=1)
        pre_fixed = fixed_denominator_smd(qc, mask, pre_denominator)
        post_fixed = (fixed_denominator_smd(qc[matched_local], matched_mask,
                                            pre_denominator)
                      if n_pairs >= 1 else [None, None])
        row = {
            "donor_id": str(donor),
            "tail_total": int(mask.sum()),
            "rest_total": int((~mask).sum()),
            "tail_common_support": int(cs_mask.sum()),
            "rest_common_support": int((~cs_mask).sum()),
            "tail_retained_fraction": float(cs_mask.sum() / mask.sum()),
            "rest_retained_fraction": float((~cs_mask).sum() / (~mask).sum()),
            "matched_pairs": n_pairs,
            "eligible": bool(n_pairs >= MIN_MATCHED_PAIRS),
            "q_depth_interval": [interval["low"][0], interval["high"][0]],
            "q_detect_interval": [interval["low"][1], interval["high"][1]],
            "q_depth_smd_pre": pre[0], "q_detect_smd_pre": pre[1],
            "q_depth_smd_post": post[0], "q_detect_smd_post": post[1],
            "q_depth_smd_pre_fixed_denominator": pre_fixed[0],
            "q_detect_smd_pre_fixed_denominator": pre_fixed[1],
            "q_depth_smd_post_fixed_denominator": post_fixed[0],
            "q_detect_smd_post_fixed_denominator": post_fixed[1],
            "q_depth_mean_tail_pre": float(qc[mask][:, 0].mean()),
            "q_depth_mean_rest_pre": float(qc[~mask][:, 0].mean()),
            "q_detect_mean_tail_pre": float(qc[mask][:, 1].mean()),
            "q_detect_mean_rest_pre": float(qc[~mask][:, 1].mean()),
            "q_depth_mean_tail_post": float(qc[matched_tail][:, 0].mean()),
            "q_depth_mean_rest_post": float(qc[matched_rest][:, 0].mean()),
            "q_detect_mean_tail_post": float(qc[matched_tail][:, 1].mean()),
            "q_detect_mean_rest_post": float(qc[matched_rest][:, 1].mean()),
            "match_distance_mean": float(np.mean(distances)),
            "match_distance_median": float(np.median(distances)),
            "match_distance_max": float(np.max(distances)),
        }
        donor_rows.append(row)
        for (tail_local, rest_local), distance in zip(pairs, distances):
            pair_rows.append({
                "donor_id": str(donor),
                "tail_stable_key": str(cs_keys[tail_local]),
                "rest_stable_key": str(cs_keys[rest_local]),
                "rank_distance_squared": distance,
            })
        if row["eligible"]:
            eligible.append(str(donor))
            matched_selection[str(donor)] = {
                "rows": np.asarray(indices[donor])[matched_local],
                "mask": matched_mask,
                "keys": donor_keys[matched_local],
                "matched_tail_local": np.asarray(matched_tail, dtype=np.int64),
                "common_support_rest_local":
                    cs_local[np.flatnonzero(~cs_mask)],
                "pairs": n_pairs,
            }
        else:
            excluded[str(donor)] = "only %d matched pairs, minimum %d" % (
                n_pairs, MIN_MATCHED_PAIRS)
        log("  %-13s cs %3d/%4d  pairs %3d  eligible %-5s  smd detect "
            "%.4f -> %s"
            % (donor, cs_mask.sum(), (~cs_mask).sum(), n_pairs,
               row["eligible"], pre[1],
               "%.4f" % post[1] if post[1] is not None else "n/a"))

    log("%d eligible donors of %d" % (len(eligible), len(donors)))

    # MINIMUM_10_DECISION_DONORS_OR_STOP_DIAGNOSTIC
    decision_capable = len(eligible) >= MIN_DECISION_DONORS
    coherence: dict[str, Any] | None = None
    loo: dict[str, Any] | None = None
    size_control: dict[str, Any] | None = None
    donor_vectors: dict[str, Any] = {}

    if decision_capable:
        rows, ids, stable, libs, masks = [], [], [], [], {}
        for donor in eligible:
            selection = matched_selection[donor]
            rows.append(conf_csr[selection["rows"]])
            ids.append(np.asarray([donor] * len(selection["rows"])))
            stable.append(np.asarray(
                [str(k) for k in np.asarray(conf["stable_key"])[
                    selection["rows"]]]))
            libs.append(library[selection["rows"]])
            masks[donor] = selection["mask"]
        matrix = sp.vstack(rows, format="csr")
        donor_list, vectors, tail_counts, rest_counts = \
            preflight.confirmation_holdout_vectors(
                holdout_raw_counts=matrix[:, holdout_pos],
                donor_id=np.concatenate(ids),
                stable_key=np.concatenate(stable),
                source_library=np.concatenate(libs),
                tail_masks_by_donor=masks, scale=scale,
                decision_mask=decision_mask)
        usable = np.asarray([np.linalg.norm(v) > 0 for v in vectors])
        if int(usable.sum()) < MIN_DECISION_DONORS:
            decision_capable = False
        else:
            result = exact_mod.exact_common_direction_test(vectors[usable])
            coherence = {k: (float(v) if isinstance(v, float) else int(v))
                         for k, v in result.items()}
            loo_result = loo_mod.loo_coherence(vectors[usable])
            loo = {"loo_mean_cosine": float(loo_result["loo_mean_cosine"]),
                   "loo_median_cosine": float(loo_result["loo_median_cosine"]),
                   "loo_positive_fraction":
                       float(loo_result["loo_positive_fraction"])}
            for j, donor in enumerate(donor_list):
                donor_vectors[str(donor)] = {
                    "l2_norm_after_normalisation":
                        float(np.linalg.norm(vectors[j])),
                    "tail_cells": int(tail_counts[j]),
                    "rest_cells": int(rest_counts[j]),
                    "usable": bool(usable[j]),
                }
            log("matched coherence %.6f, exact p %.3e, null max %.6f"
                % (coherence["mean_pairwise_cosine"],
                   coherence["p_upper_exact"], coherence["null_max"]))

            # The second correction: the same tail cells against an equal
            # number of rest cells chosen at random rather than matched, so a
            # difference from the unmatched result can be attributed to the
            # matching rather than to the smaller comparison group.
            control_cosines = []
            control_p = []
            for replicate in range(SIZE_CONTROL_REPLICATES):
                rows_c, ids_c, stable_c, libs_c, masks_c = [], [], [], [], {}
                for donor in eligible:
                    selection = matched_selection[donor]
                    pairs_n = selection["pairs"]
                    chosen = size_control_rest(
                        selection["common_support_rest_local"], pairs_n,
                        donor, replicate)
                    local = np.concatenate([selection["matched_tail_local"],
                                            chosen])
                    donor_rows_index = np.asarray(indices[donor])[local]
                    rows_c.append(conf_csr[donor_rows_index])
                    ids_c.append(np.asarray([donor] * len(local)))
                    stable_c.append(np.asarray(
                        [str(k) for k in np.asarray(conf["stable_key"])[
                            donor_rows_index]]))
                    libs_c.append(library[donor_rows_index])
                    masks_c[donor] = np.concatenate(
                        [np.ones(pairs_n, bool), np.zeros(pairs_n, bool)])
                matrix_c = sp.vstack(rows_c, format="csr")
                _, vectors_c, _, _ = preflight.confirmation_holdout_vectors(
                    holdout_raw_counts=matrix_c[:, holdout_pos],
                    donor_id=np.concatenate(ids_c),
                    stable_key=np.concatenate(stable_c),
                    source_library=np.concatenate(libs_c),
                    tail_masks_by_donor=masks_c, scale=scale,
                    decision_mask=decision_mask)
                usable_c = np.asarray([np.linalg.norm(v) > 0
                                       for v in vectors_c])
                if int(usable_c.sum()) < MIN_DECISION_DONORS:
                    continue
                result_c = exact_mod.exact_common_direction_test(
                    vectors_c[usable_c])
                control_cosines.append(float(result_c["mean_pairwise_cosine"]))
                control_p.append(float(result_c["p_upper_exact"]))
            if control_cosines:
                array = np.asarray(control_cosines)
                observed = coherence["mean_pairwise_cosine"]
                size_control = {
                    "replicates": len(control_cosines),
                    "mean": float(array.mean()),
                    "sd": float(array.std(ddof=1)) if len(array) > 1 else None,
                    "min": float(array.min()), "max": float(array.max()),
                    "matched_observed": observed,
                    "matched_inside_control_range":
                        bool(array.min() <= observed <= array.max()),
                    "control_replicates_at_or_above_matched":
                        int(np.sum(array >= observed)),
                    "median_exact_p": float(np.median(control_p)),
                    "what_it_isolates":
                        "The same matched tail cells against an equal number of "
                        "rest cells drawn at random from common support rather "
                        "than matched on QC. A matched value inside this range "
                        "means matching changed nothing beyond the reduction in "
                        "comparison-group size.",
                }
                log("size-matched control: mean %.6f, range %.6f-%.6f, "
                    "matched %.6f inside range %s"
                    % (size_control["mean"], size_control["min"],
                       size_control["max"], observed,
                       size_control["matched_inside_control_range"]))

    outdir.mkdir(parents=True, exist_ok=True)
    donor_path = outdir / DONOR_CSV
    columns = [c for c in donor_rows[0].keys()
               if c not in ("q_depth_interval", "q_detect_interval")]
    with io.open(donor_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(columns + ["q_depth_low", "q_depth_high",
                                   "q_detect_low", "q_detect_high"])
        for row in donor_rows:
            writer.writerow(
                [repr(float(row[c])) if isinstance(row[c], float) else row[c]
                 for c in columns]
                + [repr(row["q_depth_interval"][0]),
                   repr(row["q_depth_interval"][1]),
                   repr(row["q_detect_interval"][0]),
                   repr(row["q_detect_interval"][1])])

    pair_path = outdir / PAIR_CSV
    with io.open(pair_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["donor_id", "tail_stable_key", "rest_stable_key",
                         "rank_distance_squared"])
        for row in pair_rows:
            writer.writerow([row["donor_id"], row["tail_stable_key"],
                             row["rest_stable_key"],
                             repr(float(row["rank_distance_squared"]))])

    report = {
        "schema": "JEPA_T0_TAIL_MATCHED_QC_PROBE_V1",
        "contract_corrections_applied": CORRECTIONS,
        "contract_prescribed_quantities_all_reported": True,
        "size_matched_control": size_control,
        "step": "4 of the QC methodology investigation",
        "implements_contract": CONTRACT,
        "contract_sha256": _sha256_bytes(contract_bytes),
        "diagnostic_only": True,
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "training_authorized": False,
        "t0_v20_modified": False,
        "frozen_tail_mask_modified": False,
        "tail_labels_recomputed": False,
        "frozen_qc_veto_modified": False,
        "qc_alpha_modified": False,
        "frozen_target_modified": False,
        "tail_threshold_modified": False,
        "scoring_features_entering_validation": 0,
        "holdout_decision_features": features,
        "caliper_used": False,
        "balance_gate_defined": False,
        "successor_estimator_designed": False,
        "pathology_blind": True,
        "reads_at8": False,
        "decision_capable": decision_capable,
        "minimum_matched_pairs": MIN_MATCHED_PAIRS,
        "minimum_decision_donors": MIN_DECISION_DONORS,
        "eligible_donors": eligible,
        "excluded_donors": excluded,
        "matched_coherence": coherence,
        "leave_one_donor_out": loo,
        "per_donor_vector_summary": donor_vectors,
        "per_donor": donor_rows,
        "committed_coherence": frozen_preflight["support"]["coherence"],
        "committed_qc": frozen_preflight["qc"],
        "interpretation_limits": contract["interpretation_limits"],
        "machine_readable": {"donor_csv": donor_path.name,
                             "pair_csv": pair_path.name},
        "provenance": {
            "confirmation_matrix_sha256":
                conf_summary["confirmation_matrix_sha256"],
            "discovery_matrix_sha256":
                disc_summary["discovery_scalar_matrix_sha256"],
            "target_package_root_sha256":
                summaries["target_package_root_sha256"],
            "tail_package_root_sha256": summaries["tail_package_root_sha256"],
            "tail_threshold": float(summaries["threshold"]),
            "feature_role_authority_sha256":
                _sha256_bytes(Path(feature_split).read_bytes()),
            "holdout_address_ids_sha256":
                _sha256_bytes("|".join(address_ids[holdout_pos]
                                       ).encode("utf-8")),
            "holdout_decision_mask_sha256":
                _sha256_bytes(np.asarray(decision_mask,
                                         dtype=np.bool_).tobytes()),
            "holdout_scale_sha256":
                _sha256_bytes(np.asarray(scale, dtype=np.float64).tobytes()),
            "donor_set": [str(d) for d in donors],
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s, %s, %s" % (out.name, donor_path.name, pair_path.name))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("confirmation-pkg", "discovery-pkg", "tail-dir", "membership",
                 "feature-split", "outdir"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    report = run(confirmation_pkg=a.confirmation_pkg,
                 discovery_pkg=a.discovery_pkg, tail_dir=a.tail_dir,
                 membership=a.membership, feature_split=a.feature_split,
                 outdir=a.outdir)
    print()
    print("%-13s %8s %8s %7s %8s %11s %11s"
          % ("donor", "cs tail", "cs rest", "pairs", "eligible",
             "smd detect", "-> post"))
    for row in report["per_donor"]:
        print("%-13s %8d %8d %7d %8s %11.4f %11s"
              % (row["donor_id"], row["tail_common_support"],
                 row["rest_common_support"], row["matched_pairs"],
                 row["eligible"], row["q_detect_smd_pre"],
                 "%.4f" % row["q_detect_smd_post"]
                 if row["q_detect_smd_post"] is not None else "n/a"))
    print()
    print("eligible donors: %d (minimum %d) -> decision capable %s"
          % (len(report["eligible_donors"]), report["minimum_decision_donors"],
             report["decision_capable"]))
    coherence = report["matched_coherence"]
    if coherence:
        print("matched held-out coherence %.6f  exact p %.3e  null max %.6f  "
              "donors %d"
              % (coherence["mean_pairwise_cosine"],
                 coherence["p_upper_exact"], coherence["null_max"],
                 coherence["donors"]))
        print("committed unmatched coherence %.6f  exact p %.3e"
              % (report["committed_coherence"]["mean_pairwise_cosine"],
                 report["committed_coherence"]["p_upper_exact"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
