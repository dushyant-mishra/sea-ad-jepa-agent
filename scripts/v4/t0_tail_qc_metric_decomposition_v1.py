#!/usr/bin/env python3
"""Which QC metric drives the rare-tail veto? Diagnostic only.

The frozen veto statistic is a maximum across the two QC metrics:

    t_obs = max over metrics of ( mean over donors of |standardized contrast| )

and the committed record stores only that maximum, 0.2947, with p = 0.018. It
does not say whether Q_DEPTH or Q_DETECT attained it. That matters for anything
built to remediate the confound: depth-matched tail calling and
detection-residualised tail calling are different designs, and the two metrics
are strongly associated (Pearson r = 0.9232 on discovery donors) so which one
carries the signal is not guessable.

This decomposes the frozen statistic. It does not re-adjudicate anything.

**The frozen decision is untouched and is not recomputed here as an
alternative.** The per-metric p-values below carry no multiplicity control --
the frozen test applies the maximum precisely to control it -- so they are
descriptive quantities, not tests, and cannot license a different tail terminal.
The frozen terminal remains `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` on the
authority of the max statistic at p = 0.018.

Faithfulness is a precondition rather than an assumption. The frozen per-donor
contrast function and the frozen hash-seeded permutation key are imported and
used directly, and the run refuses to report a decomposition unless it first
reproduces the recorded maximum statistic and the recorded p exactly. A
decomposition of a statistic this module failed to reproduce would describe
something other than the veto.

Pathology-blind: nothing here reads AT8. The QC metrics and the tail mask are
properties of the expression data and the frozen target.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_discovery_scalar_matrix_v1 as dm  # noqa: E402
import t0_numeric_environment_v1 as numeric_environment  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

STOP = "STOP_T0_TAIL_QC_DECOMPOSITION_REFUSED"
REPORT = "T0_TAIL_QC_METRIC_DECOMPOSITION.json"

# Column order is fixed by the frozen builder: qc_by[u] = np.c_[qdepth, detect].
METRIC_NAMES = ("Q_DEPTH", "Q_DETECT")


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def observed_contrasts(qc_by_donor, tail_masks, donor_ids, frozen_qc):
    """Per-donor standardized tail-vs-rest contrast, via the frozen function."""
    rows = []
    for donor in donor_ids:
        rows.append(frozen_qc._donor_delta(qc_by_donor[donor],
                                           tail_masks[donor]))
    return np.vstack(rows)


def null_contrasts(qc_by_donor, tail_masks, keys_by_donor, donor_ids,
                   frozen_qc, log=print):
    """The frozen null, reproduced, keeping the per-metric vector each replicate.

    The frozen test collapses each replicate to a maximum and keeps only that.
    The permutation itself is rebuilt with the frozen `_key` and the frozen
    ordering rule, so the null being decomposed is the null the veto used.
    """
    replicates = frozen_qc.QC_REPLICATES
    out = np.empty((replicates, frozen_qc.QC_METRICS), dtype=np.float64)
    for r in range(replicates):
        values = []
        for donor in donor_ids:
            qc = qc_by_donor[donor]
            mask = frozen_qc._as_bool_mask(tail_masks[donor], len(qc))
            keys = keys_by_donor[donor]
            n_tail = int(np.sum(mask))
            order = sorted(
                range(len(keys)),
                key=lambda i: (frozen_qc._key(frozen_qc.NAMESPACE, r,
                                              str(donor), str(keys[i])),
                               str(keys[i]).encode()))
            permuted = np.zeros(len(keys), bool)
            permuted[order[:n_tail]] = True
            values.append(frozen_qc._donor_delta(qc, permuted))
        out[r] = np.mean(np.abs(np.vstack(values)), axis=0)
        if log and (r + 1) % 200 == 0:
            log("    %d/%d replicates" % (r + 1, replicates))
    return out


def decompose(*, qc_by_donor, tail_masks, keys_by_donor, donor_ids,
              recorded_statistic: float, recorded_p_upper: float,
              log=print) -> dict[str, Any]:
    frozen_qc = stage2a._frozen("t0_tail_qc_randomization_v1")

    observed = observed_contrasts(qc_by_donor, tail_masks, donor_ids, frozen_qc)
    per_metric_observed = np.mean(np.abs(observed), axis=0)
    statistic = float(np.max(per_metric_observed))
    log("observed max statistic %.16g" % statistic)

    if statistic != float(recorded_statistic):
        _fail("reproduced statistic %.17g does not equal the recorded %.17g; "
              "a decomposition of a statistic this module cannot reproduce "
              "would describe something other than the veto"
              % (statistic, recorded_statistic))

    log("reproducing the frozen null (%d replicates)" % frozen_qc.QC_REPLICATES)
    null = null_contrasts(qc_by_donor, tail_masks, keys_by_donor, donor_ids,
                          frozen_qc, log=log)

    # The frozen decision statistic and its p, recomputed exactly as frozen.
    null_max = null.max(axis=1)
    tolerance = 1e-15 * max(1.0, abs(statistic))
    ge = int(np.sum(null_max >= statistic - tolerance))
    p_upper = (1 + ge) / (frozen_qc.QC_REPLICATES + 1)
    log("reproduced max-statistic p_upper %.6g (ge=%d)" % (p_upper, ge))
    if abs(p_upper - float(recorded_p_upper)) > 1e-12:
        _fail("reproduced p_upper %.17g does not equal the recorded %.17g"
              % (p_upper, recorded_p_upper))

    metrics = []
    for index, name in enumerate(METRIC_NAMES):
        value = float(per_metric_observed[index])
        column = null[:, index]
        metric_tolerance = 1e-15 * max(1.0, abs(value))
        metric_ge = int(np.sum(column >= value - metric_tolerance))
        metrics.append({
            "metric": name,
            "column": index,
            "mean_abs_standardized_contrast": value,
            "attained_the_frozen_maximum": bool(value == statistic),
            "share_of_the_frozen_maximum": value / statistic if statistic else None,
            "null_mean": float(column.mean()),
            "null_p95": float(np.quantile(column, 0.95)),
            "null_max": float(column.max()),
            "descriptive_p_upper": (1 + metric_ge) / (frozen_qc.QC_REPLICATES + 1),
            "descriptive_p_upper_is_not_a_test": (
                "No multiplicity control. The frozen veto applies the maximum "
                "across metrics precisely to control it. This number describes "
                "where one metric sits in its own null and cannot license a "
                "different tail terminal."),
        })

    # Which donors carry it, signed, so a remediation knows where to look.
    donors = []
    for position, donor in enumerate(donor_ids):
        donors.append({
            "donor_id": str(donor),
            "cells": int(len(qc_by_donor[donor])),
            "tail_cells": int(np.sum(tail_masks[donor])),
            "q_depth_signed_contrast": float(observed[position, 0]),
            "q_detect_signed_contrast": float(observed[position, 1]),
        })

    return {
        "schema": "JEPA_T0_TAIL_QC_METRIC_DECOMPOSITION_V1",
        "what": "Decomposition of the frozen rare-tail QC veto statistic across "
                "its two metrics. Diagnostic only.",
        "frozen_decision_untouched": True,
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "frozen_statistic_reproduced": True,
        "frozen_max_statistic": statistic,
        "frozen_max_statistic_p_upper": p_upper,
        "frozen_qc_alpha": frozen_qc.QC_ALPHA,
        "frozen_replicates": frozen_qc.QC_REPLICATES,
        "veto": bool(p_upper <= frozen_qc.QC_ALPHA),
        "pathology_blind": True,
        "reads_at8": False,
        "changes_no_t0_result": True,
        "per_metric": metrics,
        "per_donor": donors,
        "numeric_environment": numeric_environment.numeric_environment(),
    }


def run(*, confirmation_pkg: Path, discovery_pkg: Path, tail_dir: Path,
        membership: Path, feature_split: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    summary = json.loads(
        (confirmation_pkg / "T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))
    decision = json.loads(
        (confirmation_pkg / "T0_V20_ADJUDICATION_DECISION.json"
         ).read_text(encoding="utf-8"))
    qc_record = decision["tail_preflight"]["qc"]

    cached = dm.load_cache(
        confirmation_pkg,
        expected_matrix_sha256=summary["confirmation_matrix_sha256"],
        log=lambda m: None)
    if cached is None:
        _fail("no digest-verified confirmation matrix cache under %s"
              % confirmation_pkg)
    log("confirmation matrix %s, shape %s"
        % (summary["confirmation_matrix_sha256"][:16], cached["matrix"].shape))

    raw = stage2a._frozen("t0_confirmation_raw_v1")
    summaries = raw.confirmation_summaries_from_raw(
        target_dir=str(discovery_pkg / "target"),
        tail_dir=str(tail_dir),
        scalar_raw_counts=cached["matrix"],
        scalar_feature_ids=cached["feature_ids"],
        matrix_id=cached["matrix_id"], local_row=cached["local_row"],
        cell_id=cached["cell_id"], donor_id=cached["donor_id"],
        stable_key=cached["stable_key"],
        source_library=cached["source_library"],
        feature_split_csv=str(feature_split),
        membership_csv=str(membership))

    masks = summaries["tail_masks_by_donor"]
    donor_ids = [u for u in summaries["donor_table"]["donor_id"].tolist()
                 if u in masks]
    log("%d tail-measurable confirmation donors" % len(donor_ids))
    if len(donor_ids) != int(qc_record["donors"]):
        _fail("decomposing %d donors but the record vetoed on %d"
              % (len(donor_ids), qc_record["donors"]))

    report = decompose(
        qc_by_donor=summaries["qc_by_donor"], tail_masks=masks,
        keys_by_donor=summaries["stable_keys_by_donor"],
        donor_ids=donor_ids,
        recorded_statistic=qc_record["max_mean_abs_standardized_qc_contrast"],
        recorded_p_upper=qc_record["p_upper"], log=log)

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s" % out)
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
    print("frozen max statistic %.10f  p_upper %.4f  veto %s"
          % (report["frozen_max_statistic"],
             report["frozen_max_statistic_p_upper"], report["veto"]))
    print()
    print("%-10s %28s %10s %10s %12s"
          % ("metric", "mean|std contrast|", "share", "null p95", "descr. p"))
    for entry in report["per_metric"]:
        print("%-10s %28.10f %10.4f %10.4f %12.4f"
              % (entry["metric"], entry["mean_abs_standardized_contrast"],
                 entry["share_of_the_frozen_maximum"], entry["null_p95"],
                 entry["descriptive_p_upper"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
