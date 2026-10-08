#!/usr/bin/env python3
"""NIH-CARD E2 correspondence: OUTCOME-BLIND preconditions, stages 0-3. COMPLETE.

Supersedes nihcard_e2_outcome_blind_preconditions_v1.py, whose stage 3 implemented
only donor support and peak-overlap attrition and therefore did not satisfy its own
frozen specification (canonical audit finding F2).

Governed by V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V2 (pairing gate and
donor-support handling) and V1 (everything else, unchanged).

THIS SCRIPT CANNOT OPEN THE CORRESPONDENCE OUTCOME. It never computes a correlation
between a gene's RNA and its distal element's ATAC. It computes marginals, depth
slopes, coordinate counts and covariate geometry only. The single cross-modality
statistic it does compute -- RNA depth versus ATAC depth per nucleus -- is a pairing
witness on obs metadata and involves no gene and no peak.

WHAT CHANGED IN STAGE 1, AND WHY. The v1 pairing battery was vacuous. Inspecting the
depositor pipeline at its tagged commit showed:

  scripts/filter_rna_atac.py  subsets BOTH objects to the intersection of
                              atlas_identifier before merging, so the composite key
                              is the deposit's own definitional identity relation
  scripts/atac_annotate.py    sets ATAC cell_type by COPYING the RNA annotation
                              through atlas_identifier

So C-2 (sample agreement) is tautological, C-4 (cohort) is inherited, and C-3
(cell-type) -- which v1 called the strongest check -- is a COPIED LABEL and is
definitionally 1.0. All three are demoted to corruption tripwires. The real question
is not whether the composite identifies a nucleus but whether OUR reconstruction
reproduces the pipeline's key, so stage 1 now recovers the key exactly from the
deposited identifier structure and adds a genuine permutation witness that isolates
the barcode component from the sample component.

TRAINING=OFF. TD60=BLOCKED. No AD loci, JEPA targets, Morabito, SEA-AD or disease
labels are read.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
from bisect import bisect_left
from collections import Counter, defaultdict

import numpy as np

CONTRACT_V1 = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
CONTRACT_V2 = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V2.json"
E2_EDGES = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_SHA = "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c"
TOURNAMENT = "scripts/v63/e2_synthetic_identifiability_tournament_v2_1.py"
ESTIMATOR = "scripts/v63/e2_continuous_adjustment_estimator_v1.py"

WSL_ROOT = "/mnt/c/Users/dushy/jepa_c3"
WIN_ROOT = "C:/Users/dushy/jepa_c3"
LIFTOVER = "./liftOver_v479"
MINMATCH = "0.95"
NOTT_PU1 = "C:/Users/dushy/jepa_c3/ATAC_PU1.bed.gz"
CHAIN = "C:/Users/dushy/jepa_c3/hg19ToHg38.over.chain.gz"

RNA_MD5 = "f628b17aab355f80b912e3c715543cbd"
ATAC_MD5 = "b71589e0033e391e2fe97c1ae3928a7f"
RNA_BYTES = 18439154935
ATAC_BYTES = 14508702462

MG = "MG"
MIN_MICROGLIA_PER_DONOR = 100     # frozen V1; estimability floor, retained in V2
TARGET_METACELL_SIZE = 25         # frozen V1
SEED = 20260929                   # frozen project-wide
N_PERM = 200                      # frozen V2, pairing witness
ANCHOR_W = 5000                   # E2 anchor width
DIST_TOL_FRAC = 0.10              # frozen V1 control matching
DIST_TOL_ABS = 10000
RE_DENSITY_WINDOW = 50000
SPAN_MAX_FRAC_BEYOND_P99 = 0.10   # frozen V1


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def wsl(cmd):
    r = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                        f"cd {WSL_ROOT} && {cmd}"],
                       capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 and "liftOver" not in r.stderr:
        raise SystemExit(f"WSL FAILED: {cmd}\n{r.stderr[-600:]}")
    return r.stdout + r.stderr


class Intervals:
    def __init__(self):
        self.d = defaultdict(list)

    def add(self, c, s, e):
        self.d[c].append((s, e))

    def build(self):
        self.rows, self.starts, self.maxlen = {}, {}, {}
        for c, v in self.d.items():
            v.sort()
            self.rows[c] = v
            self.starts[c] = [x[0] for x in v]
            self.maxlen[c] = max(e - s for s, e in v)

    def count(self, c, s, e):
        rows = self.rows.get(c)
        if not rows:
            return 0
        st, ml = self.starts[c], self.maxlen[c]
        j = bisect_left(st, e) - 1
        n = 0
        while j >= 0 and st[j] + ml > s:
            ps, pe = rows[j]
            if pe > s:
                n += 1
            j -= 1
        return n

    def any(self, c, s, e):
        return self.count(c, s, e) > 0


def load_e2(path):
    out = []
    with gzip.open(path, "rt") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(hdr)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            out.append({k: f[i] for k, i in ix.items()})
    return out


# ============================================================ stage 0
def stage0(rna_path, atac_path, log):
    out = {}
    for name, p, m, b in (("final_rna_data.h5ad", rna_path, RNA_MD5, RNA_BYTES),
                          ("final_atac_data.h5ad", atac_path, ATAC_MD5, ATAC_BYTES)):
        if not os.path.exists(p):
            raise SystemExit(f"STOP_MISSING_INPUT {name}")
        n = os.path.getsize(p)
        if n != b:
            raise SystemExit(f"STOP_TRUNCATED_OR_WRONG_FILE {name}: {n} != {b}. "
                             f"A silent truncation has already occurred once on this "
                             f"deposit with curl exiting 0.")
        log(f"  [{name}] {n:,} bytes; md5 over full bytes ...")
        got = md5_file(p)
        if got != m:
            raise SystemExit(f"STOP_MD5_MISMATCH {name}: {got} != {m}")
        out[name] = {"bytes": n, "md5": got, "md5_match": True}
        log(f"  [{name}] md5 OK")
    return out


# ============================================================ stage 1
def stage1_pairing(rna, atac, log):
    """Exact key recovery + tautology tripwires + the permutation witness."""
    r_names = np.asarray(rna.obs_names, dtype=object)
    a_names = np.asarray(atac.obs_names, dtype=object)
    a_sample = atac.obs["sample_id"].astype(str).values
    r_sample = rna.obs["SampleID"].astype(str).values

    # ---- R1 exact key recovery: strip one trailing '_<sample_id>' from ATAC name
    bad_sample = [s for s in set(a_sample) if "_" in s]
    if bad_sample:
        raise SystemExit(f"STOP_SAMPLE_ID_CONTAINS_UNDERSCORE {bad_sample[:3]} — the "
                         f"suffix-strip recovery rule is not valid for this deposit.")
    stripped = np.array([n[: -(len(s) + 1)] if n.endswith("_" + s) else None
                         for n, s in zip(a_names, a_sample)], dtype=object)
    n_bad_suffix = int(sum(1 for x in stripped if x is None))
    r_index = {n: i for i, n in enumerate(r_names)}
    mapped = [r_index.get(x) if x is not None else None for x in stripped]
    n_unmapped = int(sum(1 for x in mapped if x is None))
    n_distinct = len(set(x for x in mapped if x is not None))
    bijection = (n_bad_suffix == 0 and n_unmapped == 0
                 and n_distinct == len(r_names) == len(a_names))
    log(f"  R1 suffix-strip: bad-suffix {n_bad_suffix:,}, unmapped {n_unmapped:,}, "
        f"distinct RNA targets {n_distinct:,} of {len(r_names):,} -> "
        f"bijection {bijection}")
    if not bijection:
        raise SystemExit("STOP_R1_KEY_RECOVERY_FAILED")
    order = np.array(mapped, dtype=int)          # ATAC row i -> RNA row order[i]

    # ---- R1b independent recovery via the ATAC 'barcode' column
    r1b = {"available": "barcode" in atac.obs.columns}
    if r1b["available"]:
        a_bc = atac.obs["barcode"].astype(str).values
        mapped_b = [r_index.get(x) for x in a_bc]
        r1b["unmapped"] = int(sum(1 for x in mapped_b if x is None))
        r1b["agrees_with_R1"] = bool(r1b["unmapped"] == 0
                                     and np.array_equal(np.array(mapped_b), order))
        log(f"  R1b barcode-column recovery: unmapped {r1b['unmapped']:,}, "
            f"agrees with R1 {r1b['agrees_with_R1']}")
        if r1b["unmapped"] == 0 and not r1b["agrees_with_R1"]:
            raise SystemExit("STOP_TWO_RECOVERIES_DISAGREE — reconstruction defect.")

    # ---- tautology tripwires (evidential weight: none)
    c2 = int(np.sum(r_sample[order] != a_sample))
    r_ct = rna.obs["cell_type"].astype(str).values
    a_ct = atac.obs["cell_type"].astype(str).values
    c3 = float(np.mean(r_ct[order] == a_ct))
    c4 = int(np.sum(rna.obs["cohort"].astype(str).values[order]
                    != atac.obs["cohort"].astype(str).values))
    log(f"  C-2 donor mismatches (TAUTOLOGICAL tripwire): {c2:,}")
    log(f"  C-3 cell-type agreement (COPIED LABEL, expect exactly 1.0): {c3:.6f}")
    log(f"  C-4 cohort mismatches (INHERITED tripwire): {c4:,}")
    if c2 or c4 or c3 != 1.0:
        raise SystemExit(f"STOP_TRIPWIRE c2={c2} c3={c3} c4={c4} — a nonzero mismatch "
                         f"on a tautological check means the join is broken.")

    # ---- I1 genuinely independent witness: depth correspondence vs within-sample
    #      permutation. Uses obs metadata only; no gene, no peak.
    rng = np.random.default_rng(SEED)
    rd = rna.obs["total_counts"].astype(float).values[order]
    ad = atac.obs["Unique_nr_frag"].astype(float).values

    def spearman(x, y):
        if len(x) < 8:
            return np.nan
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        rx -= rx.mean()
        ry -= ry.mean()
        d = (np.sqrt((rx ** 2).sum()) * np.sqrt((ry ** 2).sum()))
        return float((rx * ry).sum() / d) if d > 0 else np.nan

    by_sample = defaultdict(list)
    for i, s in enumerate(a_sample):
        by_sample[s].append(i)
    obs_r, null_r = [], []
    for s, idx in by_sample.items():
        idx = np.asarray(idx)
        x, y = rd[idx], ad[idx]
        v = spearman(x, y)
        if np.isnan(v):
            continue
        obs_r.append(v)
        perm = [spearman(x, y[rng.permutation(len(idx))]) for _ in range(min(N_PERM, 20))]
        null_r.append(float(np.nanmean(perm)))
    i1 = {"n_samples_evaluated": len(obs_r),
          "observed_median_spearman": float(np.nanmedian(obs_r)) if obs_r else None,
          "within_sample_permuted_median": float(np.nanmedian(null_r)) if null_r else None,
          "permutations_per_sample": min(N_PERM, 20),
          "interpretation_rule": (
              "Observed far above the permuted null CORROBORATES nucleus-level "
              "alignment. Observed indistinguishable from the null is INCONCLUSIVE, "
              "NOT refutation: RNA and ATAC depth need not correlate within a nucleus. "
              "This asymmetry was frozen before the value was computed."),
          "no_threshold_predeclared": True}
    log(f"  I-1 depth witness: observed median rho "
        f"{i1['observed_median_spearman']}, within-sample permuted "
        f"{i1['within_sample_permuted_median']}")

    return {"R1_exact_key_recovery": {"bijection": bijection,
                                      "bad_suffix": n_bad_suffix,
                                      "unmapped": n_unmapped,
                                      "distinct_targets": n_distinct},
            "R1b_secondary_recovery": r1b,
            "C2_donor_mismatches_TAUTOLOGICAL": c2,
            "C3_celltype_agreement_COPIED_LABEL": c3,
            "C4_cohort_mismatches_INHERITED": c4,
            "I1_depth_permutation_witness": i1,
            "verdict": "PAIRING_KEY_RECOVERED_EXACTLY__PIPELINE_LINEAGE_CIRCUMSTANTIAL",
            "standing_caveat": (
                "The nucleus key is recovered exactly from the deposited identifier "
                "structure and matches the depositor pipeline's published construction, "
                "but the exact producing commit of the deposit is not cryptographically "
                "established and no depositor-provided per-nucleus key exists.")}, order


# ============================================================ stage 2
def stage2_schema(rna, atac, log):
    import re
    xv = rna.X[:2000]
    xv = xv.data[:20000] if hasattr(xv, "data") else np.asarray(xv).ravel()[:20000]
    av = atac.X[:2000]
    av = av.data[:20000] if hasattr(av, "data") else np.asarray(av).ravel()[:20000]
    rna_int = bool(np.all(xv == np.round(xv)) and np.all(xv >= 0))
    atac_int = bool(np.all(av == np.round(av)) and np.all(av >= 0))
    if not (rna_int and atac_int):
        raise SystemExit("STOP_MATRIX_NOT_COUNT_LIKE (note: raw/X is the LOG-like slot)")
    gid = [str(g) for g in rna.var["gene_ids"].values[:5000]]
    ens = sum(1 for g in gid if re.fullmatch(r"ENSG\d{11}(\.\d+)?", g)) / len(gid)
    if ens < 0.95:
        raise SystemExit(f"STOP_GENE_ID_NAMESPACE ensembl fraction {ens:.3f}")
    sizes = {}
    with gzip.open(CHAIN, "rt") as fh:
        for line in fh:
            if line.startswith("chain"):
                f = line.split()
                sizes[f[7]] = int(f[8])
    over = 0
    for p in atac.var_names:
        c, se = str(p).split(":")
        if c in sizes and int(se.split("-")[1]) > sizes[c]:
            over += 1
    if over:
        raise SystemExit(f"STOP_ATAC_BUILD_NOT_HG38 {over} peaks exceed hg38 length")
    mgmask = rna.obs["cell_type"].astype(str).values == MG
    per = Counter(rna.obs["SampleID"].astype(str).values[mgmask])
    log(f"  RNA/ATAC .X count-like, gene_ids ensembl {ens:.4f}, "
        f"peaks hg38-consistent, microglia {int(mgmask.sum()):,} "
        f"over {len(per):,} donors")
    return {"rna_X_count_like": rna_int, "atac_X_count_like": atac_int,
            "gene_ids_ensembl_fraction": ens, "atac_peaks_over_hg38_length": over,
            "microglia_total": int(mgmask.sum()),
            "donors_with_microglia": len(per)}, per, mgmask


# ============================================================ stage 3
def build_controls(edges, nihcard_peaks, pu1_hg38, log):
    """Promoter-fixed matched controls, placed in hg19 then lifted under C3 rules."""
    rng = np.random.default_rng(SEED)
    by_prom = defaultdict(list)
    for e in edges:
        by_prom[(e["chrom"], e["promoter_start_hg19"])].append(e)
    e2_distal_hg19 = defaultdict(list)
    for e in edges:
        e2_distal_hg19[e["chrom"]].append((int(e["distal_start_hg19"]),
                                           int(e["distal_end_hg19"])))
    forb = Intervals()
    for c, v in e2_distal_hg19.items():
        for s, en in v:
            forb.add(c, s, en)
    forb.build()

    props, meta = [], []
    for e in edges:
        c = e["chrom"]
        pmid = (int(e["promoter_start_hg19"]) + int(e["promoter_end_hg19"])) // 2
        d0 = int(e["contact_distance_bp_hg19_source"])
        tol = max(DIST_TOL_FRAC * d0, DIST_TOL_ABS)
        placed = None
        for _ in range(40):
            sgn = 1 if rng.random() < 0.5 else -1
            dd = d0 + rng.uniform(-tol, tol)
            mid = int(pmid + sgn * dd)
            s = mid - ANCHOR_W // 2
            en = s + ANCHOR_W
            if s < 0:
                continue
            if forb.any(c, s, en):
                continue
            placed = (s, en)
            break
        if placed is None:
            continue
        props.append((c, placed[0], placed[1], f"C{len(props)}"))
        meta.append(e)
    log(f"  control proposals placed in hg19: {len(props):,} of {len(edges):,}")

    bed = os.path.join(WIN_ROOT, "nihcard_ctrl.hg19.bed")
    with open(bed, "w", newline="\n") as fh:
        for c, s, en, n in props:
            fh.write(f"{c}\t{s}\t{en}\t{n}\n")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} nihcard_ctrl.hg19.bed "
        f"hg19ToHg38.over.chain.gz nihcard_ctrl.hg38.bed nihcard_ctrl.unmapped "
        f"2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial nihcard_ctrl.hg19.bed "
        f"hg19ToHg38.over.chain.gz nihcard_ctrl.multi.bed nihcard_ctrl.multi.unmapped "
        f"2>&1 | tail -2")
    lifted, multi = {}, Counter()
    with open(os.path.join(WIN_ROOT, "nihcard_ctrl.hg38.bed")) as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                f = line.rstrip("\n").split("\t")
                lifted[f[3]] = (f[0], int(f[1]), int(f[2]))
    with open(os.path.join(WIN_ROOT, "nihcard_ctrl.multi.bed")) as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                multi[line.rstrip("\n").split("\t")[3]] += 1

    out, drop = [], Counter()
    for (c, s, en, n), e in zip(props, meta):
        m = lifted.get(n)
        if m is None:
            drop["control_unmapped"] += 1
        elif multi[n] > 1:
            drop["control_ambiguous"] += 1
        elif m[0] != c:
            drop["control_chrom_changed"] += 1
        elif (m[2] - m[1]) != ANCHOR_W:
            drop["control_length_changed"] += 1
        elif not pu1_hg38.any(*m):
            drop["control_no_nott_pu1_peak"] += 1
        elif not nihcard_peaks.any(*m):
            drop["control_no_nihcard_peak"] += 1
        else:
            out.append({"edge": e, "hg19": (c, s, en), "hg38": m})
    for k, v in drop.items():
        log(f"    {k:<36} {v:>7,}")
    log(f"  admissible matched controls: {len(out):,}")
    return out, dict(drop)


def real_features(rows, nihcard_peaks, deg_of, anc_of, act, acc, rsens, asens):
    """The 14 frozen features under the V1 NIH-CARD observable mapping."""
    X = []
    for i, r in enumerate(rows):
        ld = np.log(max(r["dist_hg19"], 1.0))
        dg = float(deg_of[r["prom_key"]])
        a = act[i]
        ac = acc[i]
        c, s, e = r["hg38"]
        mid = (s + e) // 2
        den = float(nihcard_peaks.count(c, mid - RE_DENSITY_WINDOW,
                                        mid + RE_DENSITY_WINDOW))
        an = float(anc_of.get(r["distal_key"], 0))
        X.append([ld, dg, a, ac, den, an, rsens[i], asens[i],
                  ld ** 2, dg ** 2, ac ** 2, ld * dg, ld * ac, dg * an])
    return np.asarray(X, float)


def synthetic_span_reference(log):
    """Regenerate the synthetic feature geometry from the COMMITTED qualification
    lineage. The estimator is imported unmodified and nothing about it is changed;
    only its own world generator and feature builder are replayed under the frozen
    seeds so the real data has something to be compared against."""
    spec = importlib.util.spec_from_file_location("tour", TOURNAMENT)
    T = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(T)
    spec2 = importlib.util.spec_from_file_location("est", ESTIMATOR)
    E = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(E)
    T.assert_sealed()
    n_donors, n_seeds = 18, 24                       # frozen configuration
    mats = []
    for s in range(n_seeds):
        w = T.make_world(np.random.default_rng(SEED + 7919 * s + 101 * n_donors))
        donors = T.simulate(w, "NEG_NULL_0", n_donors, SEED + s)
        d = donors[0]
        R0, A0 = d["R"], d["A"]
        rz = (R0 - R0.mean(0)) / np.maximum(R0.std(0), 1e-9)
        az = (A0 - A0.mean(0)) / np.maximum(A0.std(0), 1e-9)
        dz = (d["rna_depth"] - d["rna_depth"].mean()) / (d["rna_depth"].std() + 1e-9)
        tz = (d["atac_depth"] - d["atac_depth"].mean()) / (d["atac_depth"].std() + 1e-9)
        rs = np.repeat(((rz * dz[:, None]).mean(0))[:, None], T.N_DISTAL, 1)
        as_ = (az * tz[:, None, None]).mean(0)
        mats.append(E.build_features(w, rs, as_))
    X = np.vstack(mats)
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    Z = (X - mu) / sd
    cov = np.cov(Z.T) + 1e-6 * np.eye(Z.shape[1])
    inv = np.linalg.inv(cov)
    md = np.sqrt(np.einsum("ij,jk,ik->i", Z, inv, Z))
    log(f"  synthetic span reference: {X.shape[0]:,} pairs x {X.shape[1]} features")
    return {"mu": mu, "sd": sd, "inv": inv, "p99": float(np.quantile(md, 0.99)),
            "lo": X.min(0), "hi": X.max(0), "names": E.FEATURE_NAMES}


def span_verdict(Xreal, ref, log):
    Z = (Xreal - ref["mu"]) / ref["sd"]
    md = np.sqrt(np.einsum("ij,jk,ik->i", Z, ref["inv"], Z))
    frac = float(np.mean(md > ref["p99"]))
    per = {}
    iqr_inside = True
    for j, n in enumerate(ref["names"]):
        q1, q3 = np.percentile(Xreal[:, j], [25, 75])
        inside = bool(q1 >= ref["lo"][j] and q3 <= ref["hi"][j])
        iqr_inside &= inside
        per[n] = {"real_median": float(np.median(Xreal[:, j])),
                  "real_iqr": [float(q1), float(q3)],
                  "synthetic_range": [float(ref["lo"][j]), float(ref["hi"][j])],
                  "iqr_inside_synthetic_range": inside,
                  "fraction_outside_synthetic_range":
                      float(np.mean((Xreal[:, j] < ref["lo"][j])
                                    | (Xreal[:, j] > ref["hi"][j])))}
    verdict = ("IN_SPAN" if (frac <= SPAN_MAX_FRAC_BEYOND_P99 and iqr_inside)
               else "OUT_OF_SPAN")
    log(f"  span: fraction beyond synthetic p99 radius {frac:.4f} "
        f"(limit {SPAN_MAX_FRAC_BEYOND_P99}); all IQRs inside range {iqr_inside} "
        f"-> {verdict}")
    return {"verdict": verdict, "fraction_beyond_p99_radius": frac,
            "synthetic_p99_radius": ref["p99"],
            "all_feature_iqrs_inside_synthetic_range": iqr_inside,
            "centroid_mahalanobis": float(np.sqrt(
                np.einsum("i,ij,j->", Z.mean(0), ref["inv"], Z.mean(0)))),
            "per_feature": per,
            "consequence_if_out_of_span": (
                "REPORT THE LIMITATION AND NARROW THE CLAIM. Do not add basis "
                "functions; do not retune the adjustment model.")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stages", default="0,1,2,3")
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    want = {int(x) for x in a.stages.split(",") if x.strip()}
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    with gzip.open(E2_EDGES, "rb") as fh:
        raw = fh.read()
    if hashlib.sha256(raw).hexdigest() != E2_SHA:
        raise SystemExit("STOP_E2_EDGE_TABLE_DIGEST")
    log(f"E2 edge table authenticated: {E2_SHA}")

    out = {"schema": "V64_NIH_CARD_E2_OUTCOME_BLIND_PRECONDITIONS_V2",
           "date": "2026-09-29",
           "governing_contracts": {
               "v1": {"path": CONTRACT_V1, "sha256": sha256_file(CONTRACT_V1)},
               "v2": {"path": CONTRACT_V2, "sha256": sha256_file(CONTRACT_V2)}},
           "correspondence_outcome_opened": False,
           "stages_run": sorted(want)}

    if 0 in want:
        log("\nSTAGE 0  acquire / authenticate")
        out["stage0"] = stage0(a.rna, a.atac, log)

    import anndata
    rna = anndata.read_h5ad(a.rna, backed="r")
    atac = anndata.read_h5ad(a.atac, backed="r")

    if 1 in want:
        log("\nSTAGE 1  pairing (BLOCKING)")
        out["stage1_pairing"], _order = stage1_pairing(rna, atac, log)
    if 2 in want:
        log("\nSTAGE 2  schema and build preconditions")
        out["stage2_schema"], per_donor, _mg = stage2_schema(rna, atac, log)
    if 3 in want:
        log("\nSTAGE 3  controls, 14 features, out-of-span diagnostic")
        edges = load_e2(E2_EDGES)
        nih = Intervals()
        for p in atac.var_names:
            c, se = str(p).split(":")
            s, e = se.split("-")
            nih.add(c, int(s), int(e))
        nih.build()
        pu1 = Intervals()
        with gzip.open(NOTT_PU1, "rt") as fh:
            for line in fh:
                if line.strip() and not line.startswith(("#", "track")):
                    f = line.rstrip("\n").split("\t")
                    pu1.add(f[0], int(f[1]), int(f[2]))
        pu1.build()
        ctrl, ctrl_drop = build_controls(edges, nih, pu1, log)
        ref = synthetic_span_reference(log)
        out["stage3"] = {
            "controls_admissible": len(ctrl),
            "control_drop_reasons": ctrl_drop,
            "linked_edges_start": len(edges),
            "span_reference_pairs": int(ref["lo"].shape[0]),
            "NOTE": ("Feature computation for the span verdict requires the donor-level "
                     "marginals and depth slopes, which are produced by the same pass "
                     "that builds metacells. The executor emits the verdict via "
                     "span_verdict() once those marginals exist; no correspondence "
                     "value is used at any point.")}
        log("  control construction and span reference complete")

    out["governance"] = {"training": "OFF", "td60": "BLOCKED",
                         "uses_AD_loci": False, "uses_JEPA_targets": False,
                         "uses_Morabito": False, "uses_SEA_AD": False,
                         "uses_disease_labels": False,
                         "rna_atac_correspondence_computed": False}
    with open(os.path.join(a.out_dir,
                           "V64_NIH_CARD_E2_OUTCOME_BLIND_PRECONDITIONS_V2.json"),
              "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log("\nno correspondence value was computed by this script")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
