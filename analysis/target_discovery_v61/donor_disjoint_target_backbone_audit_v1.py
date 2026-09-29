#!/usr/bin/env python3
"""Donor-disjoint stress test for the V61 source-balanced target backbone.

Discovery-only. Does not authorize training or biological specificity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import subspace_angles

SOURCES = ("HVS", "NPH52", "SEA_AD")


def stable_split(donors):
    ordered = sorted(map(str, donors), key=lambda x: hashlib.sha256(x.encode()).hexdigest())
    return set(ordered[::2]), set(ordered[1::2])


def residualize_group_means(y, groups):
    out = np.asarray(y, float).copy()
    groups = np.asarray(groups)
    for value in pd.unique(groups):
        mask = groups == value
        if mask.any():
            out[mask] -= out[mask].mean(0)
    return out


def eta_trace(y, groups):
    y = np.asarray(y, float)
    groups = np.asarray(groups)
    mean = y.mean(0)
    denominator = ((y - mean) ** 2).sum()
    numerator = 0.0
    for value in pd.unique(groups):
        mask = groups == value
        if mask.any():
            delta = y[mask].mean(0) - mean
            numerator += int(mask.sum()) * float(delta @ delta)
    return float(numerator / denominator) if denominator else 0.0


def canonical_class(meta):
    c = meta.broad_class.astype(object).copy()
    nph = meta.source.eq("NPH52")
    c.loc[nph & meta.native_class.eq("ExN")] = "Neuronal: Glutamatergic"
    c.loc[nph & meta.native_class.eq("InN")] = "Neuronal: GABAergic"
    c.loc[nph & ~meta.native_class.isin(["ExN", "InN"])] = "Non-neuronal and Non-neural"
    allowed = {"Neuronal: Glutamatergic", "Neuronal: GABAergic", "Non-neuronal and Non-neural"}
    c.loc[~c.isin(allowed)] = "Non-neuronal and Non-neural"
    return c.astype(str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--array-dir", required=True, help="directory containing data.npy, indices.npy, indptr.npy, shape.npy")
    ap.add_argument("--sample-freeze", required=True)
    ap.add_argument("--address-namespace", required=True)
    ap.add_argument("--measurement-support", required=True)
    ap.add_argument("--feature-width", type=int, default=400)
    ap.add_argument("--max-rank", type=int, default=12)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    array_dir = Path(args.array_dir)
    data = np.load(array_dir / "data.npy", mmap_mode="r")
    indices = np.load(array_dir / "indices.npy", mmap_mode="r")
    indptr = np.load(array_dir / "indptr.npy", mmap_mode="r")
    shape = tuple(np.load(array_dir / "shape.npy").tolist())
    x = sparse.csr_matrix((data, indices, indptr), shape=shape, copy=False)

    meta = pd.read_csv(args.sample_freeze)
    meta["donor_id"] = meta.donor_id.astype(str)
    meta["eval_class"] = canonical_class(meta)
    namespace = pd.read_csv(args.address_namespace, usecols=["molecular_address_index", "biotype"])
    support = pd.read_csv(args.measurement_support, usecols=["matrix_id", "molecular_address_index", "measured_address"])
    n_measured = support[support.measured_address].groupby("molecular_address_index").matrix_id.nunique()
    universe = np.sort(
        namespace[
            namespace.biotype.eq("protein_coding")
            & namespace.molecular_address_index.isin(n_measured[n_measured.eq(42)].index)
        ].molecular_address_index.to_numpy()
    )
    qc = np.diff(x.indptr).astype(float)
    qc = (qc - qc.mean()) / (qc.std() + 1e-12)

    donor_sets = {}
    for source in SOURCES:
        donor_sets[source] = stable_split(meta.loc[meta.source.eq(source), "donor_id"].unique())
    rows1 = np.array([i for i, row in meta.iterrows() if row.donor_id in donor_sets[row.source][0]], dtype=int)
    rows2 = np.array([i for i, row in meta.iterrows() if row.donor_id in donor_sets[row.source][1]], dtype=int)
    assert set(meta.iloc[rows1].donor_id).isdisjoint(set(meta.iloc[rows2].donor_id))

    def variance(rows, cols):
        block = x[rows][:, cols]
        mean = np.asarray(block.mean(0)).ravel()
        mean2 = np.asarray(block.multiply(block).mean(0)).ravel()
        return np.maximum(mean2 - mean * mean, 0)

    selection_score = np.mean(
        np.vstack([variance(rows1[meta.iloc[rows1].source.to_numpy() == source], universe) for source in SOURCES]),
        axis=0,
    )
    features = universe[np.argsort(selection_score)[::-1][: args.feature_width]]

    def fit(rows):
        covariance = np.zeros((len(features), len(features)))
        params = {}
        for source in SOURCES:
            source_rows = rows[meta.iloc[rows].source.to_numpy() == source]
            dense = x[source_rows][:, features].toarray().astype(float)
            q = qc[source_rows]
            mean = dense.mean(0)
            centered = dense - mean
            beta = (q @ centered) / (q @ q + 1e-12)
            residual = centered - q[:, None] * beta
            sd = residual.std(0, ddof=1)
            sd[sd < 1e-8] = 1.0
            residual /= sd
            covariance += (residual.T @ residual) / (3 * max(len(source_rows) - 1, 1))
            params[source] = (mean, beta, sd)
        values, vectors = np.linalg.eigh(covariance)
        order = np.argsort(values)[::-1]
        return values[order], vectors[:, order], params

    def project(rows, vectors, params):
        out = np.empty((len(rows), vectors.shape[1]))
        positions = {row: i for i, row in enumerate(rows)}
        for source in SOURCES:
            source_rows = rows[meta.iloc[rows].source.to_numpy() == source]
            dense = x[source_rows][:, features].toarray().astype(float)
            q = qc[source_rows]
            mean, beta, sd = params[source]
            scores = ((dense - mean - q[:, None] * beta) / sd) @ vectors
            for j, row in enumerate(source_rows):
                out[positions[row]] = scores[j]
        return out

    def audit(scores, rows, rank):
        mm = meta.iloc[rows].reset_index(drop=True)
        y = scores[:, :rank]
        source_residual = residualize_group_means(y, mm.source)
        biology = eta_trace(source_residual, mm.source.astype(str) + "|" + mm.eval_class.astype(str))
        source = eta_trace(y, mm.source)
        residual = residualize_group_means(y, mm.source.astype(str) + "|" + mm.eval_class.astype(str))
        donor = eta_trace(residual, mm.donor_id)
        sea = mm.source.eq("SEA_AD").to_numpy()
        sea_residual = residualize_group_means(y[sea], mm.loc[sea, "eval_class"])
        operator = eta_trace(sea_residual, mm.loc[sea, "operator_index"])
        return {
            "biology_within_source_eta2": biology,
            "source_eta2": source,
            "donor_after_source_class_eta2": donor,
            "seaad_operator_after_class_eta2": operator,
        }

    _, vectors1, params1 = fit(rows1)
    _, vectors2, _ = fit(rows2)
    scores11 = project(rows1, vectors1, params1)
    scores21 = project(rows2, vectors1, params1)

    result = {
        "schema": "V61_DONOR_DISJOINT_TARGET_BACKBONE_V1",
        "status": "DISCOVERY_STRESS_TEST_ONLY",
        "donor_disjoint": True,
        "split": {s: {"half1": len(donor_sets[s][0]), "half2": len(donor_sets[s][1])} for s in SOURCES},
        "cells": {"half1": len(rows1), "half2": len(rows2)},
        "feature_width": args.feature_width,
        "universe_n": len(universe),
        "ranks": {},
    }
    for rank in range(1, args.max_rank + 1):
        cosines = np.cos(subspace_angles(vectors1[:, :rank], vectors2[:, :rank]))
        result["ranks"][str(rank)] = {
            "mean_cos": float(cosines.mean()),
            "min_cos": float(cosines.min()),
            "fit_half1": audit(scores11, rows1, rank),
            "heldout_half2_projected_on_half1_basis": audit(scores21, rows2, rank),
        }
    result["producer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(args.out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
