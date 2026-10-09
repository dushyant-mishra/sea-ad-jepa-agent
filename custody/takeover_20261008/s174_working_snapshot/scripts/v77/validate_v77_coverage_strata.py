#!/usr/bin/env python3
"""Are the detection-inferred coverage strata the real studies, and how is the cache weighted? (S149)

The coverage confound diagnostic and the within-cohort envelope infer each real cell's cohort from
its own detections. Two readings were open: the strata are the studies (a measurement-process
effect), or they partly sort cells by depth (shallow cells fitting the smaller HVS coverage).

This checks the inference against an independent fact. The FULL104 population authority records,
for every production donor, the operators that measured it, and every operator belongs to one
study. For every cache cell from a production donor, the inferred stratum is cross-tabulated
against that study. It also reports depth per stratum, and how the calibration cache weights the
studies compared with the production corpus, by cells and by donors.

Only donor identifiers, operator identities and detection patterns are used. Real TRAIN access is
pathology-blind, TRAIN-only and read-only through load_real; the per-class metadata CSVs in the
cache directory are never opened.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "v64"))
import build_v77_real_calibration as RC  # noqa: E402
import v77_address_universe as AU  # noqa: E402
import v73_full104_population_geometry as G  # noqa: E402

EXECUTOR_FILES = ("scripts/v77/validate_v77_coverage_strata.py", "scripts/v77/build_v77_real_calibration.py",
                  "scripts/v77/v77_address_universe.py", "scripts/v64/v73_full104_population_geometry.py")
ORDER = ("HVS", "NPH52", "SEA_AD")


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=str(RC.DEFAULT_CACHE),
                    help="real TRAIN cache; the default is the original (S174-affected) cache")
    a = ap.parse_args()
    for rel in EXECUTOR_FILES:
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True, cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} is not tracked")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} differs from HEAD")
    head = _git("rev-parse", "HEAD")
    digests = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in EXECUTOR_FILES}

    meta, trip = G.load_authority()
    dids = [str(x) for x in meta["donor_ids"]]
    osrc = meta["operator_sources"]
    per = {}
    for d_i, o_i, c in trip:
        per.setdefault(dids[int(d_i)], collections.Counter())[str(osrc[int(o_i)])] += int(c)
    multi_study_donors = sorted(d for d, c in per.items() if len(c) > 1)
    true_src = {d: c.most_common(1)[0][0] for d, c in per.items()}

    X, cls, don, src, dig = RC.load_real(Path(a.cache))
    X = X.tocsr(); X.eliminate_zeros()
    don = don.astype(str)
    uni = AU.AddressUniverse(7302)
    fits = {f: X[:, np.where(~uni.source_support[AU.SOURCE_FAMILIES.index(f)])[0]].getnnz(axis=1) == 0
            for f in ORDER}
    s = np.full(X.shape[0], "NONE", dtype=object)
    for f in reversed(ORDER):
        s[fits[f]] = f

    shared = np.array([d in true_src for d in don])
    tab = {t: {c: int(((s == c) & shared & np.array([true_src.get(d) == t for d in don])).sum())
               for c in (*ORDER, "NONE")} for t in ORDER}
    agree = sum(tab[t][t] for t in ORDER)
    nnz = X.getnnz(axis=1)
    cache_cells = {f: int((s == f).sum()) for f in ORDER}
    cache_donors = {}
    for d in np.unique(don):
        v, c = np.unique(s[don == d].astype(str), return_counts=True)
        cache_donors[str(v[np.argmax(c)])] = cache_donors.get(str(v[np.argmax(c)]), 0) + 1
    prod_cells = {k: int(v) for k, v in meta["source_counts"].items()}
    prod_donors = dict(collections.Counter(true_src.values()))
    tot_pc, tot_pd = sum(prod_cells.values()), sum(prod_donors.values())
    tot_cc, tot_cd = sum(cache_cells.values()), sum(cache_donors.values())

    rec = dict(
        schema="V77_COVERAGE_STRATA_VALIDATION_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        question="are the detection-inferred coverage strata the real studies, and how is the cache weighted?",
        inferred_vs_true_study_for_cells_of_production_donors=dict(
            rows="true study from the population authority's operators", cols="inferred stratum",
            table=tab, cells=int(shared.sum()), agreeing=int(agree),
            agreement=float(agree / max(int(shared.sum()), 1)),
            production_donors_measured_by_more_than_one_study=multi_study_donors),
        median_detected_per_cell_by_stratum={f: float(np.median(nnz[s == f])) for f in ORDER if (s == f).any()},
        weighting=dict(
            calibration_cache=dict(cells=cache_cells, donors_by_majority_stratum=cache_donors,
                                   cell_fraction={k: v / tot_cc for k, v in cache_cells.items()},
                                   donor_fraction={k: v / tot_cd for k, v in cache_donors.items()},
                                   cells_per_donor=dict(min=int(np.min(list(collections.Counter(don).values()))),
                                                        median=float(np.median(list(collections.Counter(don).values()))),
                                                        max=int(np.max(list(collections.Counter(don).values()))))),
            production_full104=dict(cells=prod_cells, donors=prod_donors,
                                    cell_fraction={k: v / tot_pc for k, v in prod_cells.items()},
                                    donor_fraction={k: v / tot_pd for k, v in prod_donors.items()}),
            donors_shared=int(len(set(don) & set(true_src))), cache_only_donors=int(len(set(don) - set(true_src)))),
        source=dict(cache=str(a.cache), n_shards=len(dig), shard_digests=dig,
                    population_authority=str(G.AUTHORITY), pathology_blind=True, train_only=True,
                    read_only=True, metadata_csvs_opened=False),
        command=f"python scripts/v77/validate_v77_coverage_strata.py --out {a.out} --cache {a.cache}",
        source_commit=head, provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256=digests, no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(agreement=rec["inferred_vs_true_study_for_cells_of_production_donors"]["agreement"],
                          table=tab, depth=rec["median_detected_per_cell_by_stratum"],
                          cache_cell_fraction=rec["weighting"]["calibration_cache"]["cell_fraction"],
                          production_cell_fraction=rec["weighting"]["production_full104"]["cell_fraction"],
                          production_donor_fraction=rec["weighting"]["production_full104"]["donor_fraction"]),
                     indent=1))


if __name__ == "__main__":
    main()
