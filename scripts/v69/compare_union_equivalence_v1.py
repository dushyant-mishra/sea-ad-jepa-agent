#!/usr/bin/env python3
"""V69: decide whether cisTarget SCORES are independent of the region set.

Compares an independently scored region set against the same regions selected out of a
larger UNION run. Alignment is by NAME on both axes, never by position, so a run that
happened to be position-dependent cannot pass by accident.

cisTarget feather layout, verified by inspection rather than assumed:
  <prefix>.motifs_vs_regions.scores.feather   rows = regions, columns = motifs,
                                              plus a trailing index column "regions"
  <prefix>.regions_vs_motifs.scores.feather   rows = motifs,  columns = regions,
                                              plus a trailing index column "motifs"

This producer reads the first form and fails closed if the expected index column is
absent, rather than guessing which column is the index.

SCOPE OF THE CLAIM. This decides SCORE independence only. Rankings are a cross-region
operation and are expected to be route-dependent; they are built per route and are
deliberately not covered here.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

INDEX_COLUMN = "regions"


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def matrix_digest(df: pd.DataFrame) -> str:
    """Digest of values plus both axis labels, in a canonical sorted order."""
    d = df.sort_index(axis=0).sort_index(axis=1)
    h = hashlib.sha256()
    h.update("\x1f".join(map(str, d.index)).encode())
    h.update(b"\x1e")
    h.update("\x1f".join(map(str, d.columns)).encode())
    h.update(b"\x1e")
    h.update(np.ascontiguousarray(d.to_numpy(dtype=np.float64)).tobytes())
    return h.hexdigest()


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def load_scores(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    if INDEX_COLUMN not in df.columns:
        raise FailClosed("FAIL__EXPECTED_INDEX_COLUMN_ABSENT",
                         path=str(path), expected=INDEX_COLUMN,
                         observed_last_columns=list(df.columns[-3:]))
    return df.set_index(INDEX_COLUMN).sort_index(axis=0).sort_index(axis=1)


def compare(independent: Path, union: Path, label: str) -> dict:
    ind = load_scores(independent)
    uni = load_scores(union)

    missing_regions = [r for r in ind.index if r not in uni.index]
    missing_motifs = [m for m in ind.columns if m not in uni.columns]
    if missing_regions or missing_motifs:
        return {"set": label, "status": "FAIL__AXIS_LABELS_MISSING_FROM_UNION",
                "n_missing_regions": len(missing_regions),
                "n_missing_motifs": len(missing_motifs),
                "example_missing_regions": missing_regions[:5],
                "example_missing_motifs": missing_motifs[:5]}

    sub = uni.loc[ind.index, ind.columns]
    a = ind.to_numpy(dtype=np.float64)
    b = sub.to_numpy(dtype=np.float64)
    identical = bool(np.array_equal(a, b))
    diff = np.abs(a - b)
    return {
        "set": label,
        "status": "PASS__BITWISE_IDENTICAL" if identical else "FAIL__SCORES_DIFFER",
        "bitwise_identical": identical,
        "n_regions_compared": int(ind.shape[0]),
        "n_motifs_compared": int(ind.shape[1]),
        "max_abs_difference": float(diff.max()),
        "n_cells_differing": int((diff > 0).sum()),
        "independent_matrix_digest": matrix_digest(ind),
        "union_subset_matrix_digest": matrix_digest(sub),
        "independent_file_sha256": sha256_file(independent),
        "union_file_sha256": sha256_file(union),
    }


def rankings_counter_control(d: Path) -> dict:
    """Prove the comparison CAN fail, using the same machinery on the rankings.

    A score-equality PASS is only meaningful if the comparison is capable of detecting
    a difference. Rankings are a cross-region operation, so subsetting the union's
    rankings back to one route's regions MUST disagree with that route's independently
    built rankings. If this control were to pass -- i.e. if rankings also matched --
    the whole comparison would be suspect, because it would mean the alignment is
    somehow reading the same bytes twice.
    """
    def load(name, idx):
        df = pd.read_feather(d / name)
        if idx not in df.columns:
            raise FailClosed("FAIL__EXPECTED_INDEX_COLUMN_ABSENT",
                             path=name, expected=idx)
        return df.set_index(idx).sort_index(axis=0).sort_index(axis=1)

    ra = load("DB_A.regions_vs_motifs.rankings.feather", "motifs")
    ru = load("DB_U.regions_vs_motifs.rankings.feather", "motifs")
    cols = [c for c in ra.columns if c in ru.columns]
    a = ra[cols].to_numpy(dtype=np.float64)
    b = ru.loc[ra.index, cols].to_numpy(dtype=np.float64)
    n_diff = int((a != b).sum())
    differ = n_diff > 0
    return {
        "control": "RANKINGS_MUST_DIFFER",
        "purpose": ("Demonstrates the comparison is capable of detecting a difference, "
                    "so the score-equality PASS is not a check that cannot fail."),
        "n_cells_compared": int(a.size),
        "n_cells_differing": n_diff,
        "max_abs_difference": float(np.abs(a - b).max()),
        "rankings_differ_as_required": differ,
        "status": ("PASS__CONTROL_DETECTED_A_DIFFERENCE" if differ
                   else "FAIL__CONTROL_FOUND_NO_DIFFERENCE_COMPARISON_IS_SUSPECT"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    suffix = ".motifs_vs_regions.scores.feather"
    try:
        results = [compare(d / f"DB_{s}{suffix}", d / f"DB_U{suffix}", s)
                   for s in ("A", "B")]
        control = rankings_counter_control(d)
        scores_equal = all(r.get("bitwise_identical") for r in results)
        # The optimisation is licensed ONLY if scores match AND the control proves the
        # comparison could have detected a mismatch.
        ok = scores_equal and control["rankings_differ_as_required"]
        out = {
            "schema": "V69_UNION_REGION_SCORE_EQUIVALENCE_V1",
            "run_utc": utcnow(),
            "question": ("Is a region's cisTarget CRM score for a motif independent of "
                         "which other regions are present in the same FASTA?"),
            "design": ("A and B are disjoint deterministic slices of the Route-A region "
                       "universe. U is their union in REVERSED order, so it matches the "
                       "order of neither. All three are scored with the identical motif "
                       "batch, FASTA, cbust binary and parameters. U is then subset back "
                       "to A and to B, aligned by NAME on both axes."),
            "pass_criterion_declared_in_advance": "exact bitwise equality of the score matrices",
            "per_set": results,
            "counter_control": control,
            "scores_bitwise_equal": scores_equal,
            "verdict": ("UNION_SCORING_IS_SAFE__SCORES_ARE_REGION_SET_INDEPENDENT" if ok
                        else ("UNION_SCORING_REJECTED__SCORES_DEPEND_ON_REGION_SET"
                              if not scores_equal
                              else "UNION_SCORING_REJECTED__COUNTER_CONTROL_FAILED")),
            "scope_of_claim": ("SCORE independence only. RANKINGS are a cross-region "
                               "operation, are expected to be route-dependent, and must "
                               "be built separately for each route. This result does NOT "
                               "license sharing a rankings database between routes."),
            "status": "PASS__EQUIVALENCE_DEMONSTRATED" if ok else "STOP__EQUIVALENCE_NOT_DEMONSTRATED",
        }
    except FailClosed as e:
        out = {"schema": "V69_UNION_REGION_SCORE_EQUIVALENCE_V1",
               "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0 if str(out["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
