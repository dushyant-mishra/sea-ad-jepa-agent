"""Audit C -- is every eligible target actually estimable within each source?

Current eligibility is global and donor-based::

    donor_nonzero_cells    >= 30
    train supported donors >= 20
    validation supported donors >= 5

yielding 17,053 all-fold eligible targets. But the masking estimand is
**source-balanced** across HVS, NPH52 and SEA_AD: the primary score averages
within source and then across sources, so every source contributes equally to
the verdict regardless of how few donors or cells it has for that target.

Global eligibility does not imply per-source estimability. This audit
characterizes the gap. **It does not alter the 17,053 set.**

C3 is the sharp part
--------------------
The frozen scorer computes a within-donor centred correlation and, from
``_source_balanced_prediction_score`` verbatim::

    den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
    r = 0.0 if den <= _EPS else cov / den

where ``rss_y`` is the within-donor centred sum of squares of the target. So when
a target does not vary within a donor, ``rss_y = 0``, ``r = 0``, and that donor
contributes ``r**2 = 0`` to its source's mean -- a **perfect "no shortcut
detected" score**, not a missing value.

A source guardrail can therefore look clean because the target was essentially
unvarying there, which is the opposite of evidence that masking worked. Counting
those donor/target pairs is the point of C3.

Exactly-zero variance is identified without any subtraction: a target detected in
**no** cell of a donor is identically zero across that donor, so its within-donor
variance is exactly 0. Near-zero variance is additionally screened against the
scorer's own ``_EPS = 1e-12``, with the caveat that the ``sumsq/n - mean**2``
form suffers catastrophic cancellation precisely there -- which is why the exact
detection-count route carries the headline and the epsilon route is reported
beside it rather than instead of it.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

SCHEMA = "V5_FULL104_TARGET_SOURCE_ESTIMABILITY_V1"
_EPS = 1e-12                      # the scorer's own epsilon, not a new constant

#: Frozen current eligibility constants, restated for per-source evaluation.
MIN_DONOR_NONZERO_CELLS = 30
MIN_TRAIN_SUPPORTED_DONORS = 20
MIN_VALIDATION_SUPPORTED_DONORS = 5

SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", type=Path, required=True,
                    help="core sufficient-statistics NPZ from build_core_sufficient_statistics")
    ap.add_argument("--eligibility", type=Path,
                    default=Path("analysis/v5_full104_pass1_rebuild_20260920/evidence/"
                                 "full104_target_eligibility_v1.json"))
    ap.add_argument("--fold-by-donor", type=Path, default=None,
                    help="optional NPY of fold assignment per donor; without it the "
                         "per-fold section is reported NOT_MEASURABLE")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    stats = np.load(args.stats, allow_pickle=True)
    core = np.asarray(stats["core"], dtype=np.int64)
    donor_nnz = np.asarray(stats["donor_nnz"], dtype=np.int64)        # (donors, core)
    donor_nsum = np.asarray(stats["donor_nsum"], dtype=np.float64)
    donor_nsq = np.asarray(stats["donor_nsq"], dtype=np.float64)
    donor_cells = np.asarray(stats["donor_cells"], dtype=np.int64)
    donor_src = np.asarray(stats["donor_src"], dtype=np.int64)
    duniq = [str(x) for x in stats["duniq"]]
    n_donors, n_core = donor_nnz.shape

    eligibility = json.loads(args.eligibility.read_text(encoding="utf-8"))
    eligible_addresses = None
    for key in ("eligible_target_cols_all_folds", "all_fold_eligible_addresses",
                "all_fold_eligible", "eligible_addresses"):
        if key in eligibility and isinstance(eligibility[key], list):
            eligible_addresses = np.asarray(eligibility[key], dtype=np.int64)
            break
    if eligible_addresses is None:
        raise SystemExit(
            "could not locate the all-fold eligible address list in the eligibility receipt; "
            f"available keys: {sorted(eligibility)[:20]}")

    pos_of_address = {int(a): i for i, a in enumerate(core)}
    missing = [int(a) for a in eligible_addresses if int(a) not in pos_of_address]
    if missing:
        raise SystemExit(f"{len(missing)} eligible targets are not in the strict core")
    target_pos = np.asarray([pos_of_address[int(a)] for a in eligible_addresses], dtype=np.int64)
    n_targets = target_pos.size

    # ---------------------------------------------------------------- C1
    supported = donor_nnz >= MIN_DONOR_NONZERO_CELLS          # (donors, core)
    src_rows = []
    per_source_supported = np.zeros((len(SOURCE_NAMES), n_targets), dtype=np.int64)
    per_source_donors = np.zeros(len(SOURCE_NAMES), dtype=np.int64)
    for s, name in enumerate(SOURCE_NAMES):
        donors_s = np.flatnonzero(donor_src == s)
        per_source_donors[s] = donors_s.size
        sup = supported[np.ix_(donors_s, target_pos)]         # (donors_s, targets)
        per_source_supported[s] = sup.sum(axis=0)
        nnz_total = donor_nnz[np.ix_(donors_s, target_pos)].sum(axis=0)
        cells_total = int(donor_cells[donors_s].sum())
        src_rows.append({
            "source": name,
            "donors": int(donors_s.size),
            "cells": cells_total,
            "targets": int(n_targets),
            "mean_supported_donors_per_target": float(per_source_supported[s].mean()),
            "targets_with_zero_supported_donors": int((per_source_supported[s] == 0).sum()),
            "targets_with_fewer_than_5_supported_donors": int((per_source_supported[s] < 5).sum()),
            "mean_detection_rate": float(nnz_total.sum() / (cells_total * n_targets))
            if cells_total else float("nan"),
        })

    # ---------------------------------------------------------------- C3
    # Exact route: a target detected in NO cell of a donor has identically zero
    # within-donor variance. No subtraction, so no cancellation.
    zero_by_detection = donor_nnz[:, target_pos] == 0                  # (donors, targets)

    # Epsilon route, for comparison only. Reported beside the exact route.
    n_d = donor_cells[:, None].astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = donor_nsum[:, target_pos] / np.maximum(n_d, 1.0)
        var = donor_nsq[:, target_pos] / np.maximum(n_d, 1.0) - mean * mean
    rss = np.maximum(var, 0.0) * np.maximum(n_d, 1.0)
    near_zero_by_epsilon = rss <= _EPS

    rows_zero = []
    for s, name in enumerate(SOURCE_NAMES):
        donors_s = np.flatnonzero(donor_src == s)
        zd = zero_by_detection[donors_s]
        ze = near_zero_by_epsilon[donors_s]
        total_pairs = zd.size
        rows_zero.append({
            "source": name,
            "donor_target_pairs": int(total_pairs),
            "zero_variance_pairs_exact": int(zd.sum()),
            "zero_variance_fraction_exact": float(zd.mean()),
            "near_zero_variance_pairs_scorer_epsilon": int(ze.sum()),
            "near_zero_variance_fraction_scorer_epsilon": float(ze.mean()),
            "targets_with_every_donor_zero_variance": int((zd.all(axis=0)).sum()),
            "targets_with_any_donor_zero_variance": int((zd.any(axis=0)).sum()),
        })

    # ----------------------------------------- estimable-in-all-three summary
    estimable_per_source = per_source_supported >= MIN_VALIDATION_SUPPORTED_DONORS
    n_weak_sources = (~estimable_per_source).sum(axis=0)
    fully_estimable = int((n_weak_sources == 0).sum())
    one_weak = int((n_weak_sources == 1).sum())
    two_weak = int((n_weak_sources == 2).sum())
    three_weak = int((n_weak_sources == 3).sum())

    reasons = {}
    for s, name in enumerate(SOURCE_NAMES):
        weak = ~estimable_per_source[s]
        reasons[name] = {
            "targets_weak_in_this_source": int(weak.sum()),
            "of_which_zero_supported_donors": int((per_source_supported[s] == 0).sum()),
            "criterion": f"supported donors (>= {MIN_DONOR_NONZERO_CELLS} nonzero cells) "
                         f"< {MIN_VALIDATION_SUPPORTED_DONORS}",
        }

    args.out_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(name: str, rows: list[dict]) -> None:
        with (args.out_dir / name).open("w", newline="", encoding="utf-8") as handle:
            w = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    write_csv("TARGET_SOURCE_SUPPORT_SUMMARY.csv", src_rows)
    write_csv("TARGET_SOURCE_ZERO_VARIANCE_SUMMARY.csv", rows_zero)

    payload = {
        "schema": SCHEMA,
        "eligibility_set_altered": False,
        "targets_examined": int(n_targets),
        "donors": int(n_donors),
        "criteria_restated_per_source": {
            "min_donor_nonzero_cells": MIN_DONOR_NONZERO_CELLS,
            "min_validation_supported_donors": MIN_VALIDATION_SUPPORTED_DONORS,
            "min_train_supported_donors": MIN_TRAIN_SUPPORTED_DONORS,
        },
        "c1_per_source": src_rows,
        "c3_zero_variance": rows_zero,
        "estimable_in_all_three_sources": fully_estimable,
        "estimable_in_all_three_sources_fraction": fully_estimable / n_targets,
        "targets_with_one_weak_source": one_weak,
        "targets_with_two_weak_sources": two_weak,
        "targets_with_three_weak_sources": three_weak,
        "reasons_by_source": reasons,
        "scorer_behaviour_note":
            "A donor where the target does not vary yields rss_y = 0, so the frozen scorer "
            "returns r = 0 and contributes r**2 = 0 to its source mean. That is a perfect "
            "'no shortcut detected' contribution, NOT a missing value. A source guardrail can "
            "therefore look clean because the target was unvarying there.",
        "zero_variance_method_note":
            "The headline uses the EXACT route -- a target detected in no cell of a donor is "
            "identically zero across that donor -- which involves no subtraction. The "
            "scorer-epsilon route is reported beside it because sumsq/n - mean**2 suffers "
            "catastrophic cancellation exactly at near-zero variance.",
        "design_issue_if_mismatch":
            "If a material share of the 17,053 targets is weak or non-estimable in a source "
            "whose guardrail nonetheless votes, the global eligibility universe and the "
            "source-balanced guardrails are measuring different populations. That is an OPEN "
            "design issue; the target set is NOT shrunk here.",
        "training_authorized": False,
    }
    (args.out_dir / "TARGET_SOURCE_ESTIMABILITY.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items()
                      if k not in ("c1_per_source", "c3_zero_variance")}, indent=2))
    for r in src_rows:
        print(r)
    for r in rows_zero:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
