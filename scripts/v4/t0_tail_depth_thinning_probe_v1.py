#!/usr/bin/env python3
"""Same-cell depth intervention on the frozen rare tail. Step 2, diagnostic only.

The cross-cell QC test asks whether tail-labelled cells differ from their
donor's other cells in Q_DEPTH or Q_DETECT. That is association. It cannot say
whether the dependence is technical, because a genuine biological state may also
differ on those axes.

This asks the counterfactual instead. Holding cell identity fixed, thin
molecules from the exact confirmation cells to prospectively fixed lower depths,
recompute the frozen target score with the frozen scorer and the frozen fit,
re-centre per donor as the frozen builder does, and re-apply the frozen tail
threshold. Then measure how far scores move, whether within-donor rank order
survives, and how often the tail label flips.

Every design choice -- levels, draws, seed derivation, metrics and the
acceptance checks -- is fixed in `configs/v4/t0_tail_depth_thinning_contract_v1.json`,
which was committed before this module ran.

One structural fact about the scorer is worth stating, because it explains why
depth can move the score at all. `score_raw_counts` computes
`sum over nonzero entries of log1p(10000*count/library) * w` and then subtracts
`mu . w` taken over **all** genes. A gene that drops to zero loses its
contribution while the offset stays fixed, so the score is not invariant to
detection by construction. That is a property of the frozen estimator, not a
defect this probe introduces, and it is the reason a depth intervention is the
right instrument here.

Interpretation limits, frozen in the contract and repeated because they bound
every number below: thinning moves Q_DEPTH and Q_DETECT together, so this does
not separate them as causes; a high flip rate says the label is fragile to
measurement depth, not that the tail is artefactual; and no p-value or gate is
defined. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is untouched.

Pathology-blind: no AT8 value is read.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import hashlib
import io
import json
import struct
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

STOP = "STOP_T0_TAIL_DEPTH_THINNING_REFUSED"
CONTRACT = "configs/v4/t0_tail_depth_thinning_contract_v1.json"
REPORT = "T0_TAIL_DEPTH_THINNING_PROBE.json"
CELL_CSV = "T0_TAIL_DEPTH_THINNING_CELLS.csv"
LEVEL_CSV = "T0_TAIL_DEPTH_THINNING_LEVELS.csv"

NAMESPACE = b"T0-TAIL-DEPTH-THINNING-V1"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _cell_seed(draw: int, level: float, donor: str, stable_key: str) -> int:
    """Deterministic per-cell seed, as frozen in the contract."""
    level_text = repr(float(level)).encode()
    donor_bytes = str(donor).encode()
    key_bytes = str(stable_key).encode()
    digest = hashlib.sha256(
        NAMESPACE + b"\x00" + struct.pack(">I", draw)
        + struct.pack(">H", len(level_text)) + level_text
        + struct.pack(">H", len(donor_bytes)) + donor_bytes
        + struct.pack(">H", len(key_bytes)) + key_bytes).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def thin_cell(counts: np.ndarray, library: float, retention: float,
              seed: int) -> tuple[np.ndarray, float]:
    """Binomial molecule retention on both halves of the cell's library.

    The scalar-measured molecules and the unmeasured remainder are thinned at
    the same rate, so the CP10K denominator stays consistent with its numerator.
    """
    generator = np.random.default_rng(seed)
    scalar_total = float(np.sum(counts, dtype=np.float64))
    remainder = library - scalar_total
    if remainder < -1e-9:
        _fail("scalar counts %.6f exceed source_library %.6f"
              % (scalar_total, library))
    remainder = max(0.0, remainder)

    if retention >= 1.0:
        # The control level must not perturb the cell at all.
        return counts.astype(np.int64, copy=True), float(library)

    thinned = generator.binomial(counts.astype(np.int64), retention)
    thinned_remainder = float(generator.binomial(int(round(remainder)),
                                                 retention))
    thinned_library = float(np.sum(thinned, dtype=np.float64)) + thinned_remainder
    return thinned, thinned_library


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def probe(*, summaries: dict[str, Any], matrix, feature_positions: np.ndarray,
          fit: dict[str, Any], threshold: float, scorer, contract: dict[str, Any],
          log=print) -> dict[str, Any]:
    donors = [d for d in summaries["donor_table"]["donor_id"].tolist()
              if d in summaries["tail_masks_by_donor"]]
    indices = summaries["cell_indices_by_donor"]
    keys = summaries["stable_keys_by_donor"]
    masks = summaries["tail_masks_by_donor"]

    scalar = matrix[:, feature_positions] if not hasattr(matrix, "tocsr") \
        else matrix.tocsr()[:, feature_positions]
    library_all = np.asarray(summaries["_source_library"], dtype=np.float64)

    # Unthinned reference, recomputed here so displacement is measured against a
    # baseline produced by the same code path as the thinned values.
    baseline: dict[str, dict[str, np.ndarray]] = {}
    for donor in donors:
        ix = indices[donor]
        rows = scalar[ix]
        scores = scorer(rows, library_all[ix], fit)
        centered = scores - float(np.sum(scores, dtype=np.float64) / len(scores))
        baseline[donor] = {
            "centered": centered,
            "tail": centered > threshold,
            "sd": float(np.std(centered, ddof=1)),
        }
        if not np.array_equal(baseline[donor]["tail"], np.asarray(masks[donor])):
            _fail("recomputed baseline tail mask differs from the frozen mask "
                  "for donor %s; the probe is not reproducing the frozen "
                  "classification" % donor)
    log("baseline reproduces the frozen tail mask for all %d donors"
        % len(donors))

    cell_rows: list[dict[str, Any]] = []
    level_rows: list[dict[str, Any]] = []

    for level in contract["retention_levels"]:
        for draw in range(contract["draws_per_level"]):
            displacement = []
            standardised = []
            spearmans = []
            tail_to_rest = 0
            rest_to_tail = 0
            original_tail = 0
            thinned_tail = 0
            detect_before = []
            detect_after = []
            depth_before = []
            depth_after = []

            for donor in donors:
                ix = indices[donor]
                rows = scalar[ix]
                dense = np.asarray(rows.todense()) if hasattr(rows, "todense") \
                    else np.asarray(rows)
                thinned = np.empty_like(dense, dtype=np.int64)
                libraries = np.empty(len(ix), dtype=np.float64)
                for position in range(len(ix)):
                    seed = _cell_seed(draw, level, donor,
                                      keys[donor][position])
                    t, lib = thin_cell(dense[position].astype(np.int64),
                                       float(library_all[ix][position]),
                                       float(level), seed)
                    if np.any(t > dense[position]):
                        _fail("thinning increased a count for donor %s" % donor)
                    if lib > float(library_all[ix][position]) + 1e-9:
                        _fail("thinning increased the library for donor %s"
                              % donor)
                    thinned[position] = t
                    libraries[position] = lib

                scores = scorer(thinned, libraries, fit)
                centered = scores - float(np.sum(scores, dtype=np.float64)
                                          / len(scores))
                tail = centered > threshold

                base = baseline[donor]
                delta = centered - base["centered"]
                displacement.extend(np.abs(delta).tolist())
                if base["sd"] > 0:
                    standardised.extend((np.abs(delta) / base["sd"]).tolist())
                spearmans.append(_spearman(base["centered"], centered))

                tail_to_rest += int(np.sum(base["tail"] & ~tail))
                rest_to_tail += int(np.sum(~base["tail"] & tail))
                original_tail += int(np.sum(base["tail"]))
                thinned_tail += int(np.sum(tail))

                detect_before.append(float(np.mean(
                    np.count_nonzero(dense, axis=1) / dense.shape[1])))
                detect_after.append(float(np.mean(
                    np.count_nonzero(thinned, axis=1) / thinned.shape[1])))
                depth_before.append(float(np.mean(np.log1p(library_all[ix]))))
                depth_after.append(float(np.mean(np.log1p(libraries))))

                if draw == 0:
                    for position in range(len(ix)):
                        cell_rows.append({
                            "retention": level, "draw": draw,
                            "donor_id": str(donor),
                            "stable_key": str(keys[donor][position]),
                            # Cast before storing: numpy 2.x reprs a float64
                            # as "np.float64(...)", which is not parseable as a
                            # CSV float, so an uncast value would publish a
                            # machine-readable file that no reader can read.
                            "baseline_centered":
                                float(base["centered"][position]),
                            "thinned_centered": float(centered[position]),
                            "signed_displacement": float(delta[position]),
                            "baseline_tail": bool(base["tail"][position]),
                            "thinned_tail": bool(tail[position]),
                        })

            displacement = np.asarray(displacement)
            standardised = np.asarray(standardised)
            level_rows.append({
                "retention": level, "draw": draw,
                "cells": int(len(displacement)),
                "mean_abs_displacement": float(displacement.mean()),
                "median_abs_displacement": float(np.median(displacement)),
                "p95_abs_displacement": float(np.quantile(displacement, 0.95)),
                "mean_abs_displacement_in_donor_sd":
                    float(standardised.mean()) if len(standardised) else None,
                "mean_within_donor_spearman":
                    float(np.nanmean(spearmans)),
                "min_within_donor_spearman":
                    float(np.nanmin(spearmans)),
                "original_tail_cells": original_tail,
                "thinned_tail_cells": thinned_tail,
                "tail_to_rest_flips": tail_to_rest,
                "rest_to_tail_flips": rest_to_tail,
                "tail_to_rest_flip_rate":
                    tail_to_rest / original_tail if original_tail else None,
                "rest_to_tail_flip_rate":
                    rest_to_tail / (int(len(displacement)) - original_tail)
                    if len(displacement) > original_tail else None,
                "net_tail_change": thinned_tail - original_tail,
                "mean_q_detect_before": float(np.mean(detect_before)),
                "mean_q_detect_after": float(np.mean(detect_after)),
                "mean_q_depth_before": float(np.mean(depth_before)),
                "mean_q_depth_after": float(np.mean(depth_after)),
            })
            log("  retention %-5s draw %d: mean|d| %.4f  spearman %.4f  "
                "tail %d->%d  flips %d/%d"
                % (level, draw, level_rows[-1]["mean_abs_displacement"],
                   level_rows[-1]["mean_within_donor_spearman"],
                   original_tail, thinned_tail, tail_to_rest, rest_to_tail))

    # The frozen acceptance check: the control level must not perturb anything.
    controls = [r for r in level_rows if r["retention"] == 1.0]
    if not controls:
        _fail("the contract's control level 1.0 was not executed")
    for row in controls:
        if row["mean_abs_displacement"] != 0.0 or row["p95_abs_displacement"] != 0.0:
            _fail("retention 1.0 displaced the score by %.17g; a harness that "
                  "perturbs the cell when asked not to cannot measure what "
                  "perturbation does" % row["mean_abs_displacement"])
        if row["tail_to_rest_flips"] or row["rest_to_tail_flips"]:
            _fail("retention 1.0 flipped tail labels")
    log("control level 1.0 reproduced scores and labels exactly")

    return {"levels": level_rows, "cells": cell_rows, "donors": len(donors)}


def write_csvs(outdir: Path, cell_rows, level_rows) -> dict[str, str]:
    cell_path = outdir / CELL_CSV
    with io.open(cell_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["retention", "draw", "donor_id", "stable_key",
                         "baseline_centered", "thinned_centered",
                         "signed_displacement", "baseline_tail",
                         "thinned_tail"])
        for row in cell_rows:
            writer.writerow([row["retention"], row["draw"], row["donor_id"],
                             row["stable_key"], repr(row["baseline_centered"]),
                             repr(row["thinned_centered"]),
                             repr(row["signed_displacement"]),
                             row["baseline_tail"], row["thinned_tail"]])

    level_path = outdir / LEVEL_CSV
    fields = list(level_rows[0].keys())
    with io.open(level_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.DictWriter(handle, fieldnames=fields,
                                   lineterminator="\n")
        writer.writeheader()
        for row in level_rows:
            writer.writerow(row)
    return {"cell_csv": cell_path.name, "level_csv": level_path.name}


def run(*, confirmation_pkg: Path, discovery_pkg: Path, tail_dir: Path,
        membership: Path, feature_split: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        _fail("the thinning contract is not frozen")

    summary = json.loads(
        (confirmation_pkg / "T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))
    decision = json.loads(
        (confirmation_pkg / "T0_V20_ADJUDICATION_DECISION.json"
         ).read_text(encoding="utf-8"))
    if decision.get("tail_terminal") != "RARE_TAIL_UNDERDETERMINED_MEASUREMENT":
        _fail("expected the QC-vetoed tail terminal, found %r"
              % decision.get("tail_terminal"))

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
    tail_mod = stage2a._frozen("t0_tail_authority_v1")
    fit_mod = stage2a._frozen("t0_discovery_fit_v2")
    feature_mod = stage2a._frozen("t0_feature_authority_v1")

    summaries = raw.confirmation_summaries_from_raw(
        target_dir=str(discovery_pkg / "target"), tail_dir=str(tail_dir),
        scalar_raw_counts=cached["matrix"],
        scalar_feature_ids=cached["feature_ids"],
        matrix_id=cached["matrix_id"], local_row=cached["local_row"],
        cell_id=cached["cell_id"], donor_id=cached["donor_id"],
        stable_key=cached["stable_key"],
        source_library=cached["source_library"],
        feature_split_csv=str(feature_split), membership_csv=str(membership))
    summaries["_source_library"] = cached["source_library"]

    feature = feature_mod.load_feature_authority(str(feature_split))
    scoring_positions = np.flatnonzero(
        feature.feature_role.to_numpy() == "SCORING")
    target = fit_mod.load_target_v2(str(discovery_pkg / "target"),
                                    str(feature_split))
    log("%d SCORING addresses, tail threshold %r"
        % (len(scoring_positions), float(summaries["threshold"])))

    result = probe(summaries=summaries, matrix=cached["matrix"],
                   feature_positions=scoring_positions, fit=target["fit"],
                   threshold=float(summaries["threshold"]),
                   scorer=tail_mod.score_raw_counts, contract=contract,
                   log=log)

    outdir.mkdir(parents=True, exist_ok=True)
    csv_names = write_csvs(outdir, result["cells"], result["levels"])

    report = {
        "schema": "JEPA_T0_TAIL_DEPTH_THINNING_PROBE_V1",
        "what": "Same-cell measurement intervention: thin molecules to fixed "
                "lower depths, recompute the frozen score and tail label, and "
                "measure displacement, rank stability and label flips.",
        "step": "2 of the QC methodology investigation",
        "diagnostic_only": True,
        "contract": CONTRACT,
        "contract_status": contract["status"],
        "retention_levels": contract["retention_levels"],
        "draws_per_level": contract["draws_per_level"],
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "training_authorized": False,
        "t0_v20_modified": False,
        "frozen_qc_gate_modified": False,
        "qc_alpha_modified": False,
        "tail_definition_modified": False,
        "tail_rule_or_threshold_modified": False,
        "remediation_designed_or_tested": False,
        "pathology_blind": True,
        "reads_at8": False,
        "control_level_reproduced_exactly": True,
        "baseline_reproduced_the_frozen_tail_mask": True,
        "scorer_detection_sensitivity_note":
            "score_raw_counts sums log1p(10000*count/library)*w over nonzero "
            "entries and subtracts mu.w over all genes, so a gene dropping to "
            "zero loses its contribution while the offset is unchanged. The "
            "frozen estimator is therefore not detection-invariant by "
            "construction; this probe measures the consequence rather than "
            "introducing it.",
        "interpretation_limits": contract["interpretation_limits"],
        "donors": result["donors"],
        "per_level": result["levels"],
        "machine_readable": csv_names,
        "provenance": {
            "confirmation_matrix_sha256":
                summary["confirmation_matrix_sha256"],
            "target_package_root_sha256":
                summaries["target_package_root_sha256"],
            "tail_package_root_sha256": summaries["tail_package_root_sha256"],
            "tail_threshold": float(summaries["threshold"]),
            "seed_namespace": NAMESPACE.decode(),
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }

    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s, %s, %s" % (out.name, csv_names["cell_csv"],
                              csv_names["level_csv"]))
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
    print("%-10s %5s %14s %12s %10s %10s %9s"
          % ("retention", "draw", "mean|displ|", "in donor sd", "spearman",
             "tail n", "flips"))
    for row in report["per_level"]:
        print("%-10s %5d %14.5f %12.4f %10.4f %5d->%-4d %4d/%-4d"
              % (row["retention"], row["draw"], row["mean_abs_displacement"],
                 row["mean_abs_displacement_in_donor_sd"] or 0.0,
                 row["mean_within_donor_spearman"],
                 row["original_tail_cells"], row["thinned_tail_cells"],
                 row["tail_to_rest_flips"], row["rest_to_tail_flips"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
