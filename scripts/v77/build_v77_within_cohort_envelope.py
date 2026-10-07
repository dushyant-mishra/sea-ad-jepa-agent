#!/usr/bin/env python3
"""Within-cohort real measurements: a CANDIDATE CALIBRATION DIAGNOSTIC, for review (S149).

AUTHORITY. This executor produces scientific evidence, not a target. The pooled real envelopes
pool cells from studies measured by different processes, and a null with no biological dependence
reproduces 89% of the pooled detection correlation density (V77_REAL_COVERAGE_CONFOUND_DIAGNOSTIC_V1).
The measurements below show what the dependence looks like inside one measurement process.
Whether and how they become a calibration target, estimand or weighting is decided by the
real-data scientific lane, not here, and no synthetic pass/fail decision may use them until it
does. Earlier wording in this file called them a "replacement target" and a "material pivot";
that language is withdrawn (results/v77/V77_WITHIN_COHORT_AUTHORITY_CORRECTION_V1.json).

THE MEASUREMENT RULE. Every constant below is inherited from the frozen pooled builders; nothing
is chosen from outcomes.

 1. Stratum. A cell's measured coverage is evidenced by its detections: its cell-level stratum is
    the smallest cohort coverage containing every one of its detections, over all 41,238
    addresses. A donor comes from one study, so the stratum used is the donor-level majority;
    disagreement between cells and their donor's stratum is reported, never hidden.
 2. Eligibility. A stratum is enveloped only if at least two broad cell classes reach the frozen
    T5 floor of MIN_CLASS_CELLS cells, so that every statistic, T5 included, is defined.
 3. Within a stratum, the frozen pooled rules applied unchanged: universe = addresses detected in
    more than 5% of the stratum's cells; 3,000 genes by CPM-log1p expression variance; the
    detection layer (binarised) and the expression layer on that one gene set; T5 by the shared
    class_conditional_t5; abundance by abundance_stats; and depth.
 4. Envelope. Donor bootstrap within the stratum, 24 replicates, seed 20261006, gene set held at
    the point estimate's, and the inherited 5%-95% percentile range, as frozen (see S159).

Gene selection is redone inside each stratum, which removes the caveat on the coverage
diagnostic, whose within-stratum rows reused the pooled gene set.

S159, OPEN METHODOLOGICAL DEFECT. The inherited percentile rule puts the real point estimate
OUTSIDE its own range for 2 of 30 metrics in HVS and 5 of 30 in SEA_AD, every one shifted upward
and every one a correlation-magnitude statistic (median |corr|, community size, variance share,
T5). A with-replacement donor resample keeps only about 63% distinct cells, and correlation
magnitudes rise as distinct cells fall, which is the likely mechanism. The pooled envelopes show
no such case. A CANDIDATE repair, recorded for review and NOT authoritative, keeps the resampled
spread and removes its location bias: [point - (median - q05), point + (q95 - median)]. Both
ranges and every replicate are stored; neither is an acceptance rule.

CANDIDATE COMPARISON PROTOCOL, for review. The same n-dependence suggests a synthetic world is
comparable with a stratum only when scored on the same number of cells, so each stratum records
its cell count and class sizes.

Real TRAIN access is pathology-blind, TRAIN-only and read-only, through load_real.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import build_v77_real_calibration as RC  # noqa: E402
import build_v77_calibration_envelope as ENV  # noqa: E402
import build_v77_topology_calibration as TC  # noqa: E402
import v77_address_universe as AU  # noqa: E402

EXECUTOR_FILES = ("build_v77_within_cohort_envelope.py", "build_v77_real_calibration.py",
                  "build_v77_calibration_envelope.py", "build_v77_topology_calibration.py",
                  "v77_address_universe.py")
STRATUM_ORDER = ("HVS", "NPH52", "SEA_AD")          # smallest coverage first
DET_FLOOR = 0.05                                     # frozen pooled universe floor
N_HVG = 3000                                         # frozen pooled gene count
N_BOOT = 24                                          # frozen pooled replicate count
SEED = 20261006                                      # frozen pooled seed
QUANTILES = (0.05, 0.95)                             # inherited percentile rule (S159 open)


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def _require_committed_executors():
    for f in EXECUTOR_FILES:
        rel = f"scripts/v77/{f}"
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True,
                          cwd=ROOT).returncode != 0:
            sys.exit(f"refusing: {rel} is not tracked; a receipt must describe committed code")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode != 0:
            sys.exit(f"refusing: {rel} differs from HEAD")
    if _git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("refusing: tracked files are modified")
    return _git("rev-parse", "HEAD"), {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest()
                                       for f in EXECUTOR_FILES}


def cell_strata(X, uni):
    fits = {}
    for f in STRATUM_ORDER:
        cov = uni.source_support[AU.SOURCE_FAMILIES.index(f)]
        fits[f] = X[:, np.where(~cov)[0]].getnnz(axis=1) == 0
    s = np.full(X.shape[0], "NONE", dtype=object)
    for f in reversed(STRATUM_ORDER):
        s[fits[f]] = f
    return s, fits


def donor_strata(cell_s, don):
    by = {}
    for d in np.unique(don):
        vals, cnt = np.unique(cell_s[don == d].astype(str), return_counts=True)
        by[str(d)] = str(vals[np.argmax(cnt)])
    return np.array([by[str(d)] for d in don], dtype=object), by


def _flat(prefix, d, out):
    for k, v in d.items():
        if isinstance(v, (int, float, np.floating, np.integer)) and not isinstance(v, bool):
            out[f"{prefix}.{k}"] = float(v)


def measure(Ld, det, sub, lib, nnz_all, cls, sel, rows):
    Ld_r, det_r = Ld[rows], det[rows]
    H = Ld_r[:, sel]
    H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    C_r = (H.T @ H) / len(H)
    per_class, pooled, within = TC.class_conditional_t5(Ld_r, sel, C_r, cls[rows])
    flat = {}
    _flat("detection", ENV.stats_from_logmatrix(det_r, sel, len(sel)), flat)
    _flat("expression", ENV.stats_from_logmatrix(Ld_r, sel, len(sel)), flat)
    flat["t5.within_over_pooled"] = float(within / pooled) if pooled > 0 else float("nan")
    flat["t5.n_classes_used"] = float(len(per_class))
    _flat("abundance", ENV.abundance_stats(sub[rows], lib[rows][:, None]), flat)
    flat["depth.median_library"] = float(np.median(lib[rows]))
    flat["depth.median_detected_all_addresses"] = float(np.median(nnz_all[rows]))
    flat["depth.median_detected_in_universe"] = float(np.median((sub[rows] > 0).sum(1)))
    return flat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--universe-dir", required=True,
                    help="where per-stratum universe npz files are written (custody, not git)")
    a = ap.parse_args()
    head, digests = _require_committed_executors()

    X, cls, don, src, dig = RC.load_real(RC.DEFAULT_CACHE)
    X = X.tocsr(); X.eliminate_zeros()
    uni = AU.AddressUniverse(7302)
    cs, fits = cell_strata(X, uni)
    ds, by_donor = donor_strata(cs, don)
    violators = np.array([not fits[s][i] if s in fits else True for i, s in enumerate(ds)])
    mixed_donors = sorted(d for d in by_donor if len(set(cs[don == d].astype(str))) > 1)

    frozen = {
        "detection": json.loads((ROOT / "results/v77/V77_REAL_DETECTION_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"],
        "expression": json.loads((ROOT / "results/v77/V77_REAL_CALIBRATION_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"],
        "abundance": json.loads((ROOT / "results/v77/V77_REAL_ABUNDANCE_ENVELOPE_V1.json").read_text())["ACCEPTANCE_ENVELOPES"],
    }
    pooled_t5 = json.loads((ROOT / "results/v77/V77_REAL_TRAIN_TOPOLOGY_CALIBRATION_V1.json").read_text())[
        "T5_class_conditional_structure"]["within_over_pooled_ratio"]

    # the pooled gene set, to report how much the within-stratum selection departs from it
    lib_all = np.asarray(X.sum(1)).ravel()
    keep_all = np.where(np.asarray((X > 0).sum(0)).ravel() / X.shape[0] > DET_FLOOR)[0]
    _, pooled_hvg, _, _ = TC.hvg_correlation(X, lib_all, keep_all, N_HVG)
    pooled_hvg = set(int(x) for x in pooled_hvg)

    udir = Path(a.universe_dir); udir.mkdir(parents=True, exist_ok=True)
    strata = {}
    for si, f in enumerate(STRATUM_ORDER):
        m = ds == f
        n = int(m.sum())
        cls_s = cls[m]
        uc, cc = np.unique(cls_s, return_counts=True)
        big = int((cc >= TC.MIN_CLASS_CELLS).sum())
        info = dict(n_cells=n, n_donors=int(len(np.unique(don[m]))), classes_at_t5_floor=big,
                    class_sizes={str(c): int(k) for c, k in zip(uc, cc)})
        if big < 2:
            strata[f] = dict(info, ELIGIBLE=False,
                             reason=f"fewer than two classes with >= {TC.MIN_CLASS_CELLS} cells")
            print(f"{f}: not eligible ({n} cells, {big} classes at the floor)")
            continue
        Xs = X[m]
        lib = np.asarray(Xs.sum(1)).ravel()
        nnz_all = Xs.getnnz(axis=1)
        gdet = np.asarray((Xs > 0).sum(0)).ravel() / n
        uni_s = np.where(gdet > DET_FLOOR)[0].astype(np.int64)
        C, hvg_addr, Ld, sel = TC.hvg_correlation(Xs, lib, uni_s, N_HVG)
        sub = np.asarray(Xs[:, uni_s].todense(), dtype=np.float64)
        det = (sub > 0).astype(np.float64)
        rows_all = np.arange(n)
        point = measure(Ld, det, sub, lib, nnz_all, cls_s, sel, rows_all)

        don_s = don[m]
        donors = np.unique(don_s)
        rng = np.random.default_rng([SEED, si])
        boots = []
        for b in range(N_BOOT):
            pick = rng.choice(donors, size=len(donors), replace=True)
            idx = np.concatenate([np.where(don_s == d)[0] for d in pick])
            boots.append(measure(Ld, det, sub, lib, nnz_all, cls_s, sel, idx))
            print(f"  {f} bootstrap {b + 1}/{N_BOOT}", flush=True)
        env = {}
        for k in point:
            v = np.array([bb[k] for bb in boots], dtype=float)
            q05, q50, q95 = (float(np.nanquantile(v, q)) for q in (QUANTILES[0], 0.5, QUANTILES[1]))
            env[k] = dict(point=point[k], boot_sd=float(np.nanstd(v, ddof=1)),
                          candidate_recentered_range_S159=[point[k] - (q50 - q05), point[k] + (q95 - q50)],
                          inherited_percentile_range=[q05, q95],
                          inherited_range_excludes_point=bool(not (q05 <= point[k] <= q95)),
                          resample_median_minus_point=q50 - point[k],
                          replicates=[float(x) for x in v])

        mask = np.zeros(AU.N_ADDRESSES, dtype=bool); mask[uni_s] = True
        name = f"TRAIN_WITHIN_{f}_PREVALENCE05_{len(uni_s)}"
        upath = udir / f"{name}.npz"
        np.savez_compressed(upath, evaluation_universe=uni_s, name=np.array(name))
        hv = set(int(x) for x in hvg_addr)
        strata[f] = dict(
            info, ELIGIBLE=True,
            universe=dict(name=name, n_genes=int(len(uni_s)),
                          index_sha256=hashlib.sha256(uni_s.tobytes()).hexdigest(),
                          npz=str(upath), npz_sha256=hashlib.sha256(upath.read_bytes()).hexdigest(),
                          mask_packbits_b64=base64.b64encode(np.packbits(mask)).decode()),
            genes=dict(n=int(len(sel)),
                       address_sha256=hashlib.sha256(np.sort(hvg_addr).astype(np.int64).tobytes()).hexdigest(),
                       jaccard_with_pooled_gene_set=float(len(hv & pooled_hvg) / len(hv | pooled_hvg))),
            DIAGNOSTIC_RANGES=env)
        print(f"{f}: {n} cells, {info['n_donors']} donors, universe {len(uni_s)}; "
              f"det frac>.3 {point['detection.frac_abs_gt_0p3']:.4f} trans {point['detection.transitivity']:.4f} "
              f"deg {point['detection.mean_degree']:.1f} | T5 {point['t5.within_over_pooled']:.4f}")

    pooled_reference = {f"{layer}.{k}": v["point"] for layer, envs in frozen.items()
                        for k, v in envs.items()}
    pooled_reference["t5.within_over_pooled"] = pooled_t5
    rec = dict(
        schema="V77_REAL_WITHIN_COHORT_DIAGNOSTIC_V3",
        relabels=dict(receipts=["results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json",
                                "results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V2.json"],
                      why="authority language corrected; the computation is unchanged"),
        inherited_rule="5%-95% percentile of the donor resamples; OPEN defect S159: it can exclude the point",
        candidate_repair_S159=("[point - (median - q05), point + (q95 - median)]; recorded for review, "
                               "NOT authoritative"),
        candidate_comparison_protocol=("score a synthetic world on the stratum's own universe and own number "
                                       "of cells; for review"),
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        status="CANDIDATE_CALIBRATION_DIAGNOSTIC__FOR_REVIEW__NOT_FOR_SYNTHETIC_PASS_FAIL",
        authority=dict(
            decides_target_estimand_and_weighting="the real-data scientific lane",
            synthetic_pass_fail_use="NOT AUTHORIZED",
            evidence="results/v77/V77_REAL_COVERAGE_CONFOUND_DIAGNOSTIC_V1.json",
            pooled_envelopes="unchanged; composition-inclusive references"),
        rule=dict(stratum="smallest cohort coverage containing every detection of the cell, over all "
                          "addresses; donor-level majority used",
                  eligibility=f"at least two classes with >= {TC.MIN_CLASS_CELLS} cells (frozen T5 floor)",
                  universe=f"detected in more than {DET_FLOOR:.0%} of the stratum's cells (frozen floor)",
                  genes=f"{N_HVG} by CPM-log1p expression variance within the stratum (frozen rule)",
                  envelope=f"donor bootstrap within stratum, {N_BOOT} replicates, seed {SEED}, "
                           f"gene set held at the point estimate's, range = quantiles {QUANTILES}"),
        stratum_assignment=dict(
            cell_level={s: int((cs == s).sum()) for s in (*STRATUM_ORDER, "NONE")},
            donor_level_cells={s: int((ds == s).sum()) for s in STRATUM_ORDER},
            donor_level_donors={s: int(sum(1 for v in by_donor.values() if v == s)) for s in STRATUM_ORDER},
            donors_with_mixed_cell_strata=len(mixed_donors),
            cells_whose_detections_violate_their_donor_stratum_coverage=int(violators.sum())),
        strata=strata,
        pooled_reference_points=pooled_reference,
        source=dict(cache=str(RC.DEFAULT_CACHE), n_shards=len(dig), shard_digests=dig,
                    pathology_blind=True, train_only=True, read_only=True),
        command=f"python scripts/v77/build_v77_within_cohort_envelope.py --out {a.out} "
                f"--universe-dir {a.universe_dir}",
        source_commit=head,
        provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256=digests,
        no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print("assignment:", rec["stratum_assignment"])


if __name__ == "__main__":
    main()
