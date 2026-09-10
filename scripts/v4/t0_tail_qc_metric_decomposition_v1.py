#!/usr/bin/env python3
"""Which recorded QC axis carries more of the frozen rare-tail contrast.

Diagnostic only, and deliberately narrow. The frozen veto statistic is a maximum
across the two QC metrics, and the committed record stores only that maximum --
0.2946862124155104 at p_upper 0.018 -- without saying which metric attained it.
This decomposes that statistic into its two components and describes how
donor-distributed and how stable the answer is.

It does not modify T0 V20, the frozen QC gate, `QC_ALPHA`, the tail definition,
the terminal, or training authority. It designs and tests no remediation.

**What the result may and may not be read as.** Q_DEPTH and Q_DETECT are highly
correlated -- Pearson r = 0.9232 across discovery donors -- so the larger
component is not evidence of a unique causal mechanism, and nothing here
attributes the contrast to one physical cause. The claim available from this
decomposition is narrower: which recorded QC axis carries more of the frozen
contrast, and how broadly across donors and how stably across the frozen null
that holds.

Faithfulness is a precondition, not an assumption. The frozen per-donor contrast
function, the frozen permutation key and the frozen constants are imported and
used directly; the already-materialised confirmation cells, masks and decision
donors are reused with no recalculation of the tail mask; and the run refuses to
report anything unless it first reproduces the recorded maximum statistic, its
exceedance count and its p_upper exactly. A decomposition of a statistic this
module could not reproduce would be describing something else.

Pathology-blind: no AT8 value is read. The QC metrics and the tail mask are
properties of the expression data and the frozen target.
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

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_discovery_scalar_matrix_v1 as dm  # noqa: E402
import t0_numeric_environment_v1 as numeric_environment  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

STOP = "STOP_T0_TAIL_QC_DECOMPOSITION_REFUSED"
REPORT = "T0_TAIL_QC_METRIC_DECOMPOSITION.json"
DONOR_CSV = "T0_TAIL_QC_DONOR_COMPONENTS.csv"
REPLICATE_CSV = "T0_TAIL_QC_REPLICATE_COMPONENTS.csv"

# Column order is fixed by the frozen builder: qc_by[u] = np.c_[qdepth, detect].
METRIC_NAMES = ("Q_DEPTH", "Q_DETECT")

NON_AUTHORITATIVE = (
    "Diagnostic, non-authoritative. Not a p-value gate. The frozen veto applies "
    "the maximum across metrics precisely to control multiplicity, so a single "
    "component's position in its own null is descriptive and cannot license a "
    "different tail terminal.")


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> dict[str, str]:
    raw = Path(path).read_bytes()
    return {"path": str(path).replace("\\", "/"),
            "sha256_raw_bytes": _sha256_bytes(raw),
            "sha256_lf_normalized": _sha256_bytes(raw.replace(b"\r\n", b"\n"))}


# --- the two component statistics -----------------------------------------

def observed_components(qc_by_donor, tail_masks, donor_ids, frozen_qc):
    """Per-donor standardized tail-vs-rest contrast, via the frozen function.

    Returns the (donors x metrics) matrix of signed contrasts and the frozen
    per-metric aggregate, which is the mean across donors of the absolute value.
    """
    rows = [frozen_qc._donor_delta(qc_by_donor[d], tail_masks[d])
            for d in donor_ids]
    signed = np.vstack(rows)
    per_metric = np.mean(np.abs(signed), axis=0)
    return signed, per_metric


def null_components(qc_by_donor, tail_masks, keys_by_donor, donor_ids,
                    frozen_qc, log=print) -> np.ndarray:
    """T_depth[r] and T_detect[r] for every frozen replicate.

    The frozen test collapses each replicate to its maximum and keeps only that.
    The permutation is rebuilt with the frozen `_key` and the frozen ordering
    rule, so the null being decomposed is the null the veto used.
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


# --- the regression check against the frozen record -----------------------

def frozen_max_regression(per_metric: np.ndarray, null: np.ndarray,
                          *, recorded_statistic: float, recorded_ge: Any,
                          recorded_p_upper: float, frozen_qc) -> dict[str, Any]:
    """Reproduce the frozen max statistic, its exceedance count and its p.

    Any mismatch is a STOP. This is the check that makes the decomposition below
    a decomposition of the veto rather than of a lookalike.
    """
    statistic = float(np.max(per_metric))
    null_max = null.max(axis=1)
    tolerance = 1e-15 * max(1.0, abs(statistic))
    ge = int(np.sum(null_max >= statistic - tolerance))
    p_upper = (1 + ge) / (frozen_qc.QC_REPLICATES + 1)
    veto = bool(p_upper <= frozen_qc.QC_ALPHA)

    problems = []
    if statistic != float(recorded_statistic):
        problems.append("observed max %.17g != recorded %.17g"
                        % (statistic, recorded_statistic))
    if abs(p_upper - float(recorded_p_upper)) > 1e-12:
        problems.append("p_upper %.17g != recorded %.17g"
                        % (p_upper, recorded_p_upper))
    if recorded_ge is not None and ge != int(recorded_ge):
        problems.append("ge %d != recorded %d" % (ge, int(recorded_ge)))
    if not veto:
        problems.append("veto did not reproduce")
    if problems:
        _fail("frozen max-statistic regression failed: " + "; ".join(problems))

    return {
        "observed_max_statistic": statistic,
        "observed_max_statistic_repr": repr(statistic),
        "ge": ge,
        "replicates": frozen_qc.QC_REPLICATES,
        "p_upper": p_upper,
        "qc_alpha": frozen_qc.QC_ALPHA,
        "veto": veto,
        "reproduces_frozen_record_exactly": True,
        "recorded_statistic": float(recorded_statistic),
        "recorded_p_upper": float(recorded_p_upper),
        "recorded_ge": None if recorded_ge is None else int(recorded_ge),
    }


# --- descriptive component quantities -------------------------------------

def component_descriptives(per_metric: np.ndarray, null: np.ndarray,
                           statistic: float, frozen_qc) -> list[dict[str, Any]]:
    entries = []
    for index, name in enumerate(METRIC_NAMES):
        value = float(per_metric[index])
        column = null[:, index]
        tolerance = 1e-15 * max(1.0, abs(value))
        exceedances = int(np.sum(column >= value - tolerance))
        entries.append({
            "metric": name,
            "column": index,
            "observed_mean_abs_standardized_contrast": value,
            "observed_repr": repr(value),
            "attains_frozen_maximum": bool(value == statistic),
            "share_of_frozen_maximum": value / statistic if statistic else None,
            "null_mean": float(column.mean()),
            "null_sd": float(column.std(ddof=1)),
            "null_median": float(np.median(column)),
            "null_p95": float(np.quantile(column, 0.95)),
            "null_max": float(column.max()),
            "observed_percentile_in_own_null":
                float(100.0 * np.mean(column < value)),
            "component_exceedance_count": exceedances,
            "component_descriptive_p_upper":
                (1 + exceedances) / (frozen_qc.QC_REPLICATES + 1),
            "caveat": NON_AUTHORITATIVE,
        })
    return entries


def argmax_stability(null: np.ndarray, observed_winner: str) -> dict[str, Any]:
    """Does the same axis win the maximum across the frozen null replicates?

    If the two components largely substitute for each other, the winner will be
    split near evenly; if one axis dominates the statistic, it will win most
    replicates. Either way this is descriptive.
    """
    winners = np.argmax(null, axis=1)
    counts = {name: int(np.sum(winners == index))
              for index, name in enumerate(METRIC_NAMES)}
    ties = int(np.sum(null[:, 0] == null[:, 1]))
    modal = max(counts, key=lambda k: counts[k])
    total = int(null.shape[0])
    return {
        "replicates": total,
        "null_argmax_counts": counts,
        "null_argmax_fractions": {k: v / total for k, v in counts.items()},
        "exact_ties": ties,
        "modal_null_winner": modal,
        "observed_winner": observed_winner,
        "observed_winner_is_modal_null_winner": modal == observed_winner,
        "interpretation_note":
            "A near-even split indicates the two axes largely substitute for "
            "each other in the maximum; a lopsided split indicates one axis "
            "dominates the statistic. Descriptive either way.",
        "caveat": NON_AUTHORITATIVE,
    }


def leave_one_donor_out(signed: np.ndarray, donor_ids) -> dict[str, Any]:
    """Does the identity of the larger component depend on any single donor?

    Descriptive only, and it recomputes only the observed components -- the
    frozen null is not re-derived for the held-out subsets.
    """
    absolute = np.abs(signed)
    rows = []
    flips = []
    full_winner = METRIC_NAMES[int(np.argmax(absolute.mean(axis=0)))]
    for position, donor in enumerate(donor_ids):
        keep = np.ones(len(donor_ids), bool)
        keep[position] = False
        component = absolute[keep].mean(axis=0)
        winner = METRIC_NAMES[int(np.argmax(component))]
        rows.append({
            "held_out_donor": str(donor),
            "q_depth_component": float(component[0]),
            "q_detect_component": float(component[1]),
            "larger_component": winner,
            "margin": float(abs(component[1] - component[0])),
        })
        if winner != full_winner:
            flips.append(str(donor))
    return {
        "full_cohort_larger_component": full_winner,
        "donors_whose_removal_flips_the_larger_component": flips,
        "larger_component_is_stable_to_single_donor_removal": not flips,
        "per_held_out_donor": rows,
        "caveat": "Descriptive. The frozen null is not recomputed for these "
                  "subsets, so no p-value attaches to any of them.",
    }


# --- provenance ------------------------------------------------------------

def provenance(*, summaries: dict[str, Any], confirmation_matrix_sha256: str,
               membership: Path, feature_split: Path,
               frozen_qc_module: Path) -> dict[str, Any]:
    return {
        "confirmation_matrix_sha256": confirmation_matrix_sha256,
        "target_package_root_sha256": summaries["target_package_root_sha256"],
        "tail_package_root_sha256": summaries["tail_package_root_sha256"],
        "tail_threshold": float(summaries["threshold"]),
        "canonical_confirmation_donors":
            [str(d) for d in summaries["canonical_confirmation_donors"]],
        "tail_measurable_donors":
            [str(d) for d in summaries["tail_measurable_donors"]],
        "membership": _sha256_file(membership),
        "feature_split": _sha256_file(feature_split),
        "frozen_qc_randomization_module": _sha256_file(frozen_qc_module),
        "decomposition_module": _sha256_file(Path(__file__)),
    }


def write_csvs(outdir: Path, donor_rows: list[dict[str, Any]],
               null: np.ndarray) -> dict[str, str]:
    donor_path = outdir / DONOR_CSV
    with io.open(donor_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["donor_id", "cells", "tail_cells", "rest_cells",
                         "q_depth_signed", "q_depth_abs",
                         "q_detect_signed", "q_detect_abs"])
        for row in donor_rows:
            writer.writerow([
                row["donor_id"], row["cells"], row["tail_cells"],
                row["rest_cells"],
                repr(row["q_depth_signed_contrast"]),
                repr(row["q_depth_abs_contrast"]),
                repr(row["q_detect_signed_contrast"]),
                repr(row["q_detect_abs_contrast"])])

    replicate_path = outdir / REPLICATE_CSV
    with io.open(replicate_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["replicate", "t_depth", "t_detect", "t_max",
                         "argmax_metric"])
        for r in range(null.shape[0]):
            depth = float(null[r, 0])
            detect = float(null[r, 1])
            writer.writerow([r, repr(depth), repr(detect),
                             repr(max(depth, detect)),
                             METRIC_NAMES[int(np.argmax(null[r]))]])
    return {"donor_components_csv": str(donor_path.name),
            "replicate_components_csv": str(replicate_path.name)}


# --- driver ----------------------------------------------------------------

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
    if decision.get("tail_terminal") != "RARE_TAIL_UNDERDETERMINED_MEASUREMENT":
        _fail("this decomposition targets the QC-vetoed tail terminal; the "
              "record carries %r" % decision.get("tail_terminal"))

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
    frozen_qc = stage2a._frozen("t0_tail_qc_randomization_v1")

    # The already-materialised cells, masks and decision donors, reused. The
    # tail mask is not recalculated here under any different rule.
    summaries = raw.confirmation_summaries_from_raw(
        target_dir=str(discovery_pkg / "target"), tail_dir=str(tail_dir),
        scalar_raw_counts=cached["matrix"],
        scalar_feature_ids=cached["feature_ids"],
        matrix_id=cached["matrix_id"], local_row=cached["local_row"],
        cell_id=cached["cell_id"], donor_id=cached["donor_id"],
        stable_key=cached["stable_key"],
        source_library=cached["source_library"],
        feature_split_csv=str(feature_split), membership_csv=str(membership))

    masks = summaries["tail_masks_by_donor"]
    donor_ids = [u for u in summaries["donor_table"]["donor_id"].tolist()
                 if u in masks]
    log("%d decision donors" % len(donor_ids))
    if len(donor_ids) != int(qc_record["donors"]):
        _fail("decomposing %d donors but the record vetoed on %d"
              % (len(donor_ids), qc_record["donors"]))

    signed, per_metric = observed_components(
        summaries["qc_by_donor"], masks, donor_ids, frozen_qc)
    log("observed components: Q_DEPTH %r  Q_DETECT %r"
        % (float(per_metric[0]), float(per_metric[1])))

    log("reproducing the frozen null (%d replicates)" % frozen_qc.QC_REPLICATES)
    null = null_components(summaries["qc_by_donor"], masks,
                           summaries["stable_keys_by_donor"], donor_ids,
                           frozen_qc, log=log)

    regression = frozen_max_regression(
        per_metric, null,
        recorded_statistic=qc_record["max_mean_abs_standardized_qc_contrast"],
        recorded_ge=qc_record.get("ge"),
        recorded_p_upper=qc_record["p_upper"], frozen_qc=frozen_qc)
    log("frozen regression reproduced: max %r ge %d p_upper %r"
        % (regression["observed_max_statistic"], regression["ge"],
           regression["p_upper"]))

    statistic = regression["observed_max_statistic"]
    components = component_descriptives(per_metric, null, statistic, frozen_qc)
    winner = next(c["metric"] for c in components if c["attains_frozen_maximum"])

    donor_rows = []
    for position, donor in enumerate(donor_ids):
        qc = summaries["qc_by_donor"][donor]
        mask = np.asarray(masks[donor])
        donor_rows.append({
            "donor_id": str(donor),
            "cells": int(len(qc)),
            "tail_cells": int(np.sum(mask)),
            "rest_cells": int(np.sum(~mask)),
            "q_depth_signed_contrast": float(signed[position, 0]),
            "q_depth_abs_contrast": float(abs(signed[position, 0])),
            "q_detect_signed_contrast": float(signed[position, 1]),
            "q_detect_abs_contrast": float(abs(signed[position, 1])),
        })

    outdir.mkdir(parents=True, exist_ok=True)
    csv_names = write_csvs(outdir, donor_rows, null)

    report = {
        "schema": "JEPA_T0_TAIL_QC_METRIC_DECOMPOSITION_V1",
        "what": "Decomposition of the frozen rare-tail QC veto statistic into "
                "its two recorded QC components, with donor-level and "
                "replicate-level detail.",
        "diagnostic_only": True,
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "training_authorized": False,
        "t0_v20_modified": False,
        "frozen_qc_gate_modified": False,
        "qc_alpha_modified": False,
        "tail_definition_modified": False,
        "tail_mask_recalculated": False,
        "remediation_designed_or_tested": False,
        "pathology_blind": True,
        "reads_at8": False,
        "correlated_components_caveat":
            "Q_DEPTH and Q_DETECT are highly correlated (Pearson r = 0.9232 "
            "across discovery donors). The larger component is not evidence of "
            "a unique causal mechanism and no physical cause is attributed "
            "here. The available claim is only which recorded QC axis carries "
            "more of the frozen contrast, and how donor-distributed and stable "
            "that observation is.",
        "frozen_max_statistic_regression": regression,
        "larger_component": winner,
        "per_metric": components,
        "null_argmax_stability": argmax_stability(null, winner),
        "leave_one_donor_out": leave_one_donor_out(signed, donor_ids),
        "per_donor": donor_rows,
        "machine_readable": csv_names,
        "provenance": provenance(
            summaries=summaries,
            confirmation_matrix_sha256=summary["confirmation_matrix_sha256"],
            membership=membership, feature_split=feature_split,
            frozen_qc_module=Path(frozen_qc.__file__)),
        "numeric_environment": numeric_environment.numeric_environment(),
    }

    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s, %s, %s" % (out.name, csv_names["donor_components_csv"],
                              csv_names["replicate_components_csv"]))
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
    r = report["frozen_max_statistic_regression"]
    print()
    print("frozen regression: max %s  ge %d  p_upper %s  veto %s"
          % (r["observed_max_statistic_repr"], r["ge"], r["p_upper"],
             r["veto"]))
    print()
    print("%-9s %24s %9s %11s %9s %9s"
          % ("metric", "observed", "share", "pct in null", "exceed", "descr p"))
    for c in report["per_metric"]:
        print("%-9s %24s %9.4f %10.2f%% %9d %9.4f"
              % (c["metric"], c["observed_repr"],
                 c["share_of_frozen_maximum"],
                 c["observed_percentile_in_own_null"],
                 c["component_exceedance_count"],
                 c["component_descriptive_p_upper"]))
    s = report["null_argmax_stability"]
    print()
    print("null argmax: %s   modal %s   observed winner %s   agree %s"
          % (s["null_argmax_counts"], s["modal_null_winner"],
             s["observed_winner"], s["observed_winner_is_modal_null_winner"]))
    loo = report["leave_one_donor_out"]
    print("leave-one-donor-out: larger component stable = %s   flips on %s"
          % (loo["larger_component_is_stable_to_single_donor_removal"],
             loo["donors_whose_removal_flips_the_larger_component"] or "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
