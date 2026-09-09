#!/usr/bin/env python3
"""Q_DEPTH against Q_DETECT, as a diagnostic. It changes no T0 result.

The two QC metrics enter T0 only as one reduced model. The measurement
sensitivity is a single fit with both added at once —
`measurements=[_run(y,np.c_[z,qdepth,qdetect],state,P)]`, named
`Q_DEPTH+Q_DETECT` — so if they are close to collinear the design carries two
columns of nearly the same information, and the sensitivity has less independent
purchase on measurement confounding than its name suggests. That is worth
knowing and is not a reason to change anything: the design is frozen, the
adjudication rule is frozen, and the result stands as adjudicated.

What each measures:

    Q_DEPTH  = mean over the donor's cells of log1p(source_library)
    Q_DETECT = mean over the donor's cells of nonzero(A) / n_addresses

Both summarise sequencing effort per donor. Depth is the library size on a log
scale; detection is the fraction of the address space observed at all. They are
mechanically linked — deeper libraries detect more addresses — with the link
saturating as detection approaches one, so a strong association is expected and
the question is how strong, and whether the pair is jointly estimable.

This is computed on the **discovery** donors from the frozen scalar matrix. That
keeps it pathology-blind: nothing here reads AT8, and no gated endpoint is
touched. The QC metrics are properties of the expression data alone.

Reported: the association between the two, the conditioning of the nuisance
design once both are appended, and the variance each retains after the other and
the frozen nuisance columns are projected out. The last is the one that matters,
because it is what the sensitivity fit actually has to work with.
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

REPORT = "T0_QC_METRIC_DIAGNOSTIC.json"


def donor_qc_metrics(matrix, donor_id, source_library) -> dict[str, Any]:
    """Q_DEPTH and Q_DETECT per donor, by the frozen definitions."""
    donors = sorted(set(map(str, donor_id)), key=lambda d: d.encode("utf-8"))
    index = {d: i for i, d in enumerate(donors)}
    rows = np.asarray([index[str(d)] for d in donor_id], dtype=np.int64)

    n_addresses = matrix.shape[1]
    nonzero_per_cell = np.asarray(
        (matrix != 0).sum(axis=1)).ravel().astype(float)
    depth_per_cell = np.log1p(np.asarray(source_library, dtype=float))

    counts = np.bincount(rows, minlength=len(donors)).astype(float)
    depth = np.bincount(rows, weights=depth_per_cell,
                        minlength=len(donors)) / counts
    detect = (np.bincount(rows, weights=nonzero_per_cell / n_addresses,
                          minlength=len(donors)) / counts)
    return {"donors": donors, "cells_per_donor": counts,
            "q_depth": depth, "q_detect": detect,
            "n_addresses": int(n_addresses)}


def _residual_fraction(target: np.ndarray, design: np.ndarray) -> float:
    """Fraction of a column's centred variance left after projecting out `design`.

    This is the quantity the sensitivity fit depends on. A value near zero means
    the column adds almost nothing the other columns did not already carry, so
    the reduced model is barely reduced.
    """
    centred = target - target.mean()
    coefficients, *_ = np.linalg.lstsq(design, centred, rcond=None)
    residual = centred - design @ coefficients
    denominator = float(centred @ centred)
    if denominator == 0.0:
        return 0.0
    return float(residual @ residual) / denominator


def diagnose(metrics: dict[str, Any], age: np.ndarray,
             sex: np.ndarray) -> dict[str, Any]:
    depth = metrics["q_depth"]
    detect = metrics["q_detect"]
    n = len(depth)

    pearson = float(np.corrcoef(depth, detect)[0, 1])
    ranks = (np.argsort(np.argsort(depth)).astype(float),
             np.argsort(np.argsort(detect)).astype(float))
    spearman = float(np.corrcoef(*ranks)[0, 1])

    # The frozen nuisance design: intercept, centred age, its square, sex.
    age_c = age - age.mean()
    nuisance = np.c_[np.ones(n), age_c, age_c ** 2, sex]
    with_qc = np.c_[nuisance, depth, detect]

    def condition(matrix: np.ndarray) -> float:
        singular = np.linalg.svd(matrix, compute_uv=False)
        return float(singular[0] / singular[-1]) if singular[-1] > 0 else float("inf")

    return {
        "donors": n,
        "pearson_r": pearson,
        "pearson_r_squared": pearson ** 2,
        "spearman_r": spearman,
        "q_depth_mean": float(depth.mean()), "q_depth_sd": float(depth.std(ddof=1)),
        "q_detect_mean": float(detect.mean()),
        "q_detect_sd": float(detect.std(ddof=1)),
        "nuisance_condition_number": condition(nuisance),
        "nuisance_plus_qc_condition_number": condition(with_qc),
        # What each metric still carries once the nuisance design and the other
        # metric are removed. This is the sensitivity's actual leverage.
        "q_depth_residual_variance_fraction_given_nuisance_and_q_detect":
            _residual_fraction(depth, np.c_[nuisance, detect]),
        "q_detect_residual_variance_fraction_given_nuisance_and_q_depth":
            _residual_fraction(detect, np.c_[nuisance, depth]),
        "q_depth_residual_variance_fraction_given_nuisance_only":
            _residual_fraction(depth, nuisance),
        "q_detect_residual_variance_fraction_given_nuisance_only":
            _residual_fraction(detect, nuisance),
    }


def run(*, discovery_pkg: Path, age_sex_pkg: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    summary = json.loads((discovery_pkg / "T0_DISCOVERY_STAGE_RUN_SUMMARY.json"
                          ).read_text(encoding="utf-8"))
    cached = dm.load_cache(
        discovery_pkg,
        expected_matrix_sha256=summary["discovery_scalar_matrix_sha256"],
        log=lambda m: None)
    if cached is None:
        raise SystemExit("no cached discovery matrix under %s" % discovery_pkg)
    log("discovery matrix %s, shape %s"
        % (summary["discovery_scalar_matrix_sha256"][:16],
           cached["matrix"].shape))

    metrics = donor_qc_metrics(cached["matrix"], cached["donor_id"],
                               cached["source_library"])
    log("%d discovery donors, %d addresses"
        % (len(metrics["donors"]), metrics["n_addresses"]))

    # The same replayed age/sex authority the frozen metadata builder uses,
    # loaded through its own expectation checks rather than read as a CSV.
    import t0_eligible_donor_production_run_v1 as ed
    import t0_stage2a_pre_at8_gate_v1 as stage2a
    ages_mod = stage2a._frozen("t0_age_sex_authority_v1")
    replayed = ages_mod.load_authority(
        age_sex_pkg,
        expected_package_root_sha256=ed.AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256=ed.AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256=ed.AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256=(
            ed.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET))
    table = {str(row["donor_id"]): row for row in replayed["rows"]}
    age = np.asarray([float(table[d]["age"]) for d in metrics["donors"]])
    sex = np.asarray([1.0 if str(table[d]["sex"]).strip().lower().startswith("m")
                      else 0.0 for d in metrics["donors"]])

    report = diagnose(metrics, age, sex)
    report["schema"] = "JEPA_T0_QC_METRIC_DIAGNOSTIC_V1"
    report["role"] = "DISCOVERY"
    report["pathology_blind"] = True
    report["changes_no_t0_result"] = True
    report["note"] = (
        "Diagnostic only. The T0 V20 design, thresholds, nuisance columns and "
        "adjudication rule are frozen and unchanged by this. Computed on "
        "discovery donors from the frozen scalar matrix; no AT8 value is read.")

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    log("wrote %s" % out)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--discovery-pkg", required=True, type=Path)
    p.add_argument("--age-sex-pkg", required=True, type=Path)
    p.add_argument("--outdir", required=True, type=Path)
    a = p.parse_args(argv)
    report = run(discovery_pkg=a.discovery_pkg, age_sex_pkg=a.age_sex_pkg,
                 outdir=a.outdir)
    print()
    for key in ("donors", "pearson_r", "pearson_r_squared", "spearman_r",
                "nuisance_condition_number",
                "nuisance_plus_qc_condition_number",
                "q_depth_residual_variance_fraction_given_nuisance_and_q_detect",
                "q_detect_residual_variance_fraction_given_nuisance_and_q_depth"):
        print("%-64s %s" % (key, report[key]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
