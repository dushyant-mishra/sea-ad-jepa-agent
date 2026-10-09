#!/usr/bin/env python3
"""Derive the V5 base proposal after prospective horizon/conditioning constraints.

This script is outcome-blind. It reads only reader_fit source/donor/operator counts
from the frozen foundation metadata SQLite authority. It does not authorize
training or execution.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import gzip
import json
import math
import sqlite3
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

METADATA_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
METADATA_BUNDLE_MEMBER = "metadata/foundation_metadata_rows.sqlite"
SCIENTIFIC_TARGET_POLICY = "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1"
HORIZON_PRESENTATIONS = 4_553_407
MAX_EXPECTED_PER_CELL_EXPOSURE = 32
MIN_EXPECTED_GROUP_PRESENTATIONS = 16
MIN_IMPORTANCE_ESS_FRACTION = 0.5
MAX_IMPORTANCE_WEIGHT_RATIO = 64.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frac_json(x: Fraction) -> dict[str, object]:
    return {"numerator": x.numerator, "denominator": x.denominator, "float": float(x)}


def exact_row_probabilities(row: pd.Series, *, donor_count: int, source_count: int) -> tuple[Fraction, Fraction, Fraction]:
    p = Fraction(1, donor_count * int(row.donor_cells))
    q_source = Fraction(1, source_count * int(row.source_cells))
    q_group = Fraction(1, donor_count * int(row.groups_per_donor) * int(row.cells))
    return p, q_source, q_group


def solve_two_constraints(
    max_row: pd.Series,
    min_group_row: pd.Series,
    *,
    donor_count: int,
    source_count: int,
    horizon: int,
) -> tuple[Fraction, Fraction, Fraction]:
    p1, s1, g1 = exact_row_probabilities(max_row, donor_count=donor_count, source_count=source_count)
    p2, s2, g2 = exact_row_probabilities(min_group_row, donor_count=donor_count, source_count=source_count)

    # q = s + alpha*(p-s) + beta*(g-s), gamma = 1-alpha-beta.
    a11 = Fraction(horizon) * (p1 - s1)
    a12 = Fraction(horizon) * (g1 - s1)
    b1 = Fraction(MAX_EXPECTED_PER_CELL_EXPOSURE) - Fraction(horizon) * s1

    n2 = int(min_group_row.cells)
    a21 = Fraction(horizon * n2) * (p2 - s2)
    a22 = Fraction(horizon * n2) * (g2 - s2)
    b2 = Fraction(MIN_EXPECTED_GROUP_PRESENTATIONS) - Fraction(horizon * n2) * s2

    det = a11 * a22 - a21 * a12
    if det == 0:
        raise RuntimeError("active proposal constraints are singular")
    alpha = (b1 * a22 - b2 * a12) / det
    beta = (a11 * b2 - a21 * b1) / det
    gamma = Fraction(1) - alpha - beta
    if min(alpha, beta, gamma) < 0:
        raise RuntimeError("derived mixture left the simplex")
    return alpha, beta, gamma


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata-sqlite", type=Path, required=True)
    ap.add_argument("--counts-out", type=Path, required=True)
    ap.add_argument("--horizon-authority-out", type=Path, required=True)
    ap.add_argument("--proposal-authority-out", type=Path, required=True)
    args = ap.parse_args()

    observed = sha256(args.metadata_sqlite)
    if observed != METADATA_SHA256:
        raise SystemExit(f"metadata SHA mismatch {observed} != {METADATA_SHA256}")

    con = sqlite3.connect(args.metadata_sqlite)
    try:
        g = pd.read_sql_query(
            "select source,donor_id,operator_index,count(*) cells "
            "from cells where partition='reader_fit' "
            "group by source,donor_id,operator_index",
            con,
        )
    finally:
        con.close()

    g = g.sort_values(["source", "donor_id", "operator_index"], kind="stable").reset_index(drop=True)
    g["donor_cells"] = g.groupby("donor_id").cells.transform("sum").astype("int64")
    g["groups_per_donor"] = g.groupby("donor_id").operator_index.transform("count").astype("int64")
    source_cells = g.groupby("source").cells.sum().to_dict()
    g["source_cells"] = g.source.map(source_cells).astype("int64")

    N = int(g.cells.sum())
    D = int(g.donor_id.nunique())
    S = int(g.source.nunique())
    G = len(g)
    if (N, D, S, G) != (4_553_407, 104, 3, 1_400):
        raise RuntimeError(f"reader_fit geometry drift: {(N,D,S,G)}")
    if HORIZON_PRESENTATIONS != N:
        raise RuntimeError("horizon must equal exactly one reader_fit population-equivalent")

    counts = g.cells.to_numpy(float)
    p = 1.0 / (D * g.donor_cells.to_numpy(float))
    q_source = 1.0 / (S * g.source_cells.to_numpy(float))
    q_group = 1.0 / (D * g.groups_per_donor.to_numpy(float) * counts)

    # Linear program: maximize direct target component alpha over the convex
    # family alpha*p + beta*q_group + gamma*q_source, subject first to the
    # prospective repeat and coverage constraints. Conditioning guards are
    # checked on the exact reconstructed solution below.
    # Variables: alpha, beta; gamma = 1-alpha-beta.
    A: list[list[float]] = []
    B: list[float] = []
    H = float(HORIZON_PRESENTATIONS)
    for i in range(G):
        A.append([H * (p[i] - q_source[i]), H * (q_group[i] - q_source[i])])
        B.append(MAX_EXPECTED_PER_CELL_EXPOSURE - H * q_source[i])
    for i in range(G):
        n = counts[i]
        A.append([-H * n * (p[i] - q_source[i]), -H * n * (q_group[i] - q_source[i])])
        B.append(-(MIN_EXPECTED_GROUP_PRESENTATIONS - H * n * q_source[i]))
    A.append([1.0, 1.0])
    B.append(1.0)

    lp = linprog(c=[-1.0, 0.0], A_ub=np.asarray(A), b_ub=np.asarray(B), bounds=[(0, 1), (0, 1)], method="highs")
    if not lp.success:
        raise RuntimeError(f"proposal LP failed: {lp.message}")
    alpha0, beta0 = map(float, lp.x)
    gamma0 = 1.0 - alpha0 - beta0
    q0 = alpha0 * p + beta0 * q_group + gamma0 * q_source
    exposure0 = HORIZON_PRESENTATIONS * q0
    group0 = HORIZON_PRESENTATIONS * counts * q0
    max_idx = int(np.argmax(exposure0))
    min_group_idx = int(np.argmin(group0))

    alpha, beta, gamma = solve_two_constraints(
        g.iloc[max_idx], g.iloc[min_group_idx], donor_count=D, source_count=S, horizon=HORIZON_PRESENTATIONS
    )
    af, bf, gf = float(alpha), float(beta), float(gamma)
    q = af * p + bf * q_group + gf * q_source
    w = p / q
    mass = float(np.sum(counts * q))
    ess = float(1.0 / np.sum(counts * p * p / q))
    max_exp = float((HORIZON_PRESENTATIONS * q).max())
    group_presentations = HORIZON_PRESENTATIONS * counts * q
    min_group = float(group_presentations.min())
    ratio = float(w.max() / w.min())
    if not math.isclose(mass, 1.0, rel_tol=1e-13, abs_tol=1e-13):
        raise RuntimeError(f"proposal mass drift {mass}")
    if max_exp > MAX_EXPECTED_PER_CELL_EXPOSURE * (1 + 1e-12):
        raise RuntimeError("repeat-exposure ceiling violated")
    if min_group + 1e-12 < MIN_EXPECTED_GROUP_PRESENTATIONS:
        raise RuntimeError("group-coverage floor violated")
    if ess + 1e-12 < MIN_IMPORTANCE_ESS_FRACTION:
        raise RuntimeError("ESS conditioning floor violated")
    if ratio > MAX_IMPORTANCE_WEIGHT_RATIO * (1 + 1e-12):
        raise RuntimeError("importance-weight ratio ceiling violated")
    if abs(af - alpha0) > 1e-10 or abs(bf - beta0) > 1e-10:
        raise RuntimeError("exact active-constraint solution disagrees with LP optimum")

    args.counts_out.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = g[["source", "donor_id", "operator_index", "cells"]].to_csv(index=False, lineterminator="\n").encode("utf-8")
    gz_bytes = gzip.compress(csv_bytes, compresslevel=9, mtime=0)
    if args.counts_out.name.endswith(".csv.gz.b64"):
        args.counts_out.write_bytes(base64.b64encode(gz_bytes) + b"\n")
    elif args.counts_out.suffix == ".gz":
        args.counts_out.write_bytes(gz_bytes)
    else:
        args.counts_out.write_bytes(csv_bytes)
    counts_transport_sha = sha256(args.counts_out)
    counts_csv_sha = hashlib.sha256(csv_bytes).hexdigest()
    counts_gzip_sha = hashlib.sha256(gz_bytes).hexdigest()

    zero_hit_union_bound = G * math.exp(-MIN_EXPECTED_GROUP_PRESENTATIONS)
    horizon_payload = {
        "schema": "TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1",
        "status": "PRESENTATION_HORIZON_AND_BASE_PROPOSAL_CONSTRAINTS_FROZEN__TRAINING_UNAUTHORIZED",
        "population": "reader_fit",
        "authority_input": {"bundle_member": METADATA_BUNDLE_MEMBER, "sha256": observed},
        "reader_fit_cells": N,
        "reader_fit_donors": D,
        "reader_fit_sources": S,
        "reader_fit_donor_operator_groups": G,
        "total_presentations": HORIZON_PRESENTATIONS,
        "horizon_definition": "EXACTLY_ONE_READER_FIT_POPULATION_EQUIVALENT__NO_AUTOMATIC_EXTENSION",
        "constraints_frozen_before_q_selection": {
            "max_expected_per_cell_exposure": MAX_EXPECTED_PER_CELL_EXPOSURE,
            "min_expected_donor_operator_group_presentations": MIN_EXPECTED_GROUP_PRESENTATIONS,
            "min_importance_ess_fraction": MIN_IMPORTANCE_ESS_FRACTION,
            "max_importance_weight_max_to_min_ratio": MAX_IMPORTANCE_WEIGHT_RATIO,
        },
        "coverage_interpretation": {
            "per_group_zero_hit_upper_bound": math.exp(-MIN_EXPECTED_GROUP_PRESENTATIONS),
            "all_1400_group_zero_hit_union_bound": zero_hit_union_bound,
            "statement": "For independent presentation draws, P(group receives zero draws) <= exp(-expected draws); the 16-presentation floor therefore bounds the union probability that any of 1,400 groups is never drawn by 1,400*exp(-16).",
        },
        "conditioning_interpretation": {
            "ess_floor": "importance-sampling ESS must remain at least one half of raw presentations",
            "weight_ratio_ceiling": "largest per-cell p/q correction may be at most 64x the smallest",
        },
        "extension_policy": "Any horizon extension or constraint relaxation requires a new prospective authority before additional presentations; there is no implicit second epoch.",
        "update_size_frozen": False,
        "token_budget_frozen": False,
        "ema_half_life_frozen": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    args.horizon_authority_out.parent.mkdir(parents=True, exist_ok=True)
    args.horizon_authority_out.write_text(json.dumps(horizon_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    horizon_sha = sha256(args.horizon_authority_out)

    source_expected: dict[str, float] = {}
    for source, idx in g.groupby("source", sort=True).groups.items():
        ii = np.asarray(list(idx), dtype=int)
        source_expected[source] = float(HORIZON_PRESENTATIONS * np.sum(counts[ii] * q[ii]))

    max_row = g.iloc[int(np.argmax(HORIZON_PRESENTATIONS * q))]
    min_row = g.iloc[int(np.argmin(group_presentations))]
    proposal_payload = {
        "schema": "TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3",
        "status": "BASE_AND_RELATIONAL_PROPOSALS_FROZEN_ALGORITHMICALLY__TRAINING_UNAUTHORIZED",
        "supersedes": "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V2.json",
        "scientific_target_authority": "docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json",
        "presentation_horizon_authority": {"path": str(args.horizon_authority_out), "sha256": horizon_sha},
        "reader_fit_group_counts": {
            "path": str(args.counts_out),
            "transport_encoding": "BASE64_OF_DETERMINISTIC_GZIP_MTIME0",
            "rows": G,
            "transport_sha256": counts_transport_sha,
            "decoded_csv_sha256": counts_csv_sha,
            "decoded_gzip_sha256": counts_gzip_sha,
        },
        "base": {
            "scientific_target_policy_id": SCIENTIFIC_TARGET_POLICY,
            "proposal_policy_id": "MAX_TARGET_MASS_SUBJECT_TO_EXPOSURE_COVERAGE_CONDITIONING_V1",
            "family": "CONVEX_MIXTURE__DONOR_TARGET__SOURCE_UNIFORM__DONOR_OPERATOR_COVERAGE_V1",
            "selection_rule": "Maximize alpha_target in q=alpha*p_target+beta*q_group+gamma*q_source subject to the frozen horizon constraints; beta,gamma>=0 and alpha+beta+gamma=1. Exact p/q correction is mandatory.",
            "tie_break": "If alpha_target is tied, choose the minimum beta_operator_coverage; if still tied, lexicographically smallest exact rational coefficient tuple.",
            "components": {
                "p_target_per_cell": "1 / (D * donor_cells)",
                "q_source_per_cell": "1 / (S * source_cells)",
                "q_group_per_cell": "1 / (D * donor_operator_groups_for_donor * donor_operator_group_cells)",
            },
            "coefficients": {
                "alpha_target": frac_json(alpha),
                "beta_operator_coverage": frac_json(beta),
                "gamma_source_uniform": frac_json(gamma),
            },
            "importance_correction": "w_i = p_target_i / q_i; scientific mass remains the frozen donor-uniform target and is not replaced by proposal mass.",
            "derived_metrics": {
                "proposal_probability_mass": mass,
                "importance_ess_fraction": ess,
                "importance_weight_min": float(w.min()),
                "importance_weight_max": float(w.max()),
                "importance_weight_max_to_min_ratio": ratio,
                "max_expected_per_cell_exposure": max_exp,
                "min_expected_donor_operator_group_presentations": min_group,
                "expected_presentations_by_source": source_expected,
            },
            "active_extrema": {
                "repeat_ceiling_cell": {
                    "source": str(max_row.source), "donor_id": str(max_row.donor_id), "operator_index": int(max_row.operator_index),
                    "group_cells": int(max_row.cells), "donor_cells": int(max_row.donor_cells), "groups_per_donor": int(max_row.groups_per_donor),
                },
                "coverage_floor_group": {
                    "source": str(min_row.source), "donor_id": str(min_row.donor_id), "operator_index": int(min_row.operator_index),
                    "group_cells": int(min_row.cells), "donor_cells": int(min_row.donor_cells), "groups_per_donor": int(min_row.groups_per_donor),
                },
            },
        },
        "relational": {
            "proposal_policy_id": "DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2",
            "proposal_equals_target": True,
            "importance_correction_required": False,
            "operator_role": "ADMISSIBILITY_BOUNDARY_ONLY",
            "triplet_budget": None,
            "triplet_budget_is_scientific_weight": False,
        },
        "compute_packing_can_change_scientific_mass": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    # Store repo-relative paths, regardless of generation location.
    proposal_payload["presentation_horizon_authority"]["path"] = "docs/agent/TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1.json"
    proposal_payload["reader_fit_group_counts"]["path"] = "docs/agent/READER_FIT_DONOR_OPERATOR_COUNTS_V1.csv.gz.b64"
    args.proposal_authority_out.parent.mkdir(parents=True, exist_ok=True)
    args.proposal_authority_out.write_text(json.dumps(proposal_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "terminal": "PASS_TEACHER_STUDENT_V5_PROPOSAL_HORIZON_DERIVATION_V1__TRAINING_UNAUTHORIZED",
        "counts_transport_sha256": counts_transport_sha,
        "counts_csv_sha256": counts_csv_sha,
        "counts_gzip_sha256": counts_gzip_sha,
        "horizon_authority_sha256": horizon_sha,
        "proposal_authority_sha256": sha256(args.proposal_authority_out),
        "alpha_target": float(alpha), "beta_operator_coverage": float(beta), "gamma_source_uniform": float(gamma),
        "ess_fraction": ess, "weight_ratio": ratio, "max_exposure": max_exp, "min_group_presentations": min_group,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
