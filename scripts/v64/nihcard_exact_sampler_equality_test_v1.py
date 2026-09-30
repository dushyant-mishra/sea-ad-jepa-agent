"""Exact set-equality test: interval algebra vs brute-force liftOver enumeration."""
import gzip, importlib.util, os, subprocess, sys
from collections import defaultdict
from bisect import bisect_left
import numpy as np

spec = importlib.util.spec_from_file_location(
    "ex", "scripts/v64/nihcard_exact_control_sampler_v1.py")
X = importlib.util.module_from_spec(spec); spec.loader.exec_module(X)
W = 5000
WIN = "C:/Users/dushy/jepa_c3"


def load_bed(p):
    d = defaultdict(list)
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as fh:
        for l in fh:
            if l.strip() and not l.startswith(("#", "track")):
                f = l.rstrip().split("\t")
                d[f[0]].append((int(f[1]), int(f[2])))
    for c in d:
        d[c].sort()
    return d


def overlaps(rows, starts, maxlen, c, s, e):
    v = rows.get(c)
    if not v:
        return False
    j = bisect_left(starts[c], e) - 1
    while j >= 0 and starts[c][j] + maxlen[c] > s:
        ps, pe = v[j]
        if pe > s:
            return True
        j -= 1
    return False


def main(n_edges):
    fwd = X.ChainIndex(X.parse_chain(f"{WIN}/hg19ToHg38.over.chain.gz"))
    rev = X.ChainIndex(X.parse_chain(f"{WIN}/hg38ToHg19.over.chain.gz"))
    pu1 = load_bed(f"{WIN}/ATAC_PU1.bed.gz")
    nih = defaultdict(list)
    import anndata
    at = anndata.read_h5ad("D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad",
                           backed="r")
    for p in at.var_names:
        c, se = str(p).split(":"); s_, e_ = se.split("-")
        nih[c].append((int(s_), int(e_)))
    for c in nih:
        nih[c].sort()
    pu_s = {c: [x[0] for x in v] for c, v in pu1.items()}
    pu_m = {c: max(e - s for s, e in v) for c, v in pu1.items()}
    nh_s = {c: [x[0] for x in v] for c, v in nih.items()}
    nh_m = {c: max(e - s for s, e in v) for c, v in nih.items()}

    rows = []
    with gzip.open("results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz",
                   "rt") as fh:
        h = fh.readline().rstrip().split("\t"); ix = {k: i for i, k in enumerate(h)}
        rows = [l.rstrip().split("\t") for l in fh]
    by_prom = defaultdict(list)
    for r in rows:
        pk = f"{r[ix['chrom']]}:{r[ix['promoter_start_hg38']]}-{r[ix['promoter_end_hg38']]}"
        by_prom[pk].append((int(r[ix['distal_start_hg19']]), int(r[ix['distal_end_hg19']])))

    rng = np.random.default_rng(20260929)
    sel = rng.choice(len(rows), n_edges, replace=False)
    allok = True
    nonempty = 0
    tested = 0
    for n, i in enumerate(sel):
        r = rows[i]; c = r[ix["chrom"]]
        P = (int(r[ix["promoter_start_hg19"]]) + int(r[ix["promoter_end_hg19"]])) // 2
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        tol = max(int(0.10 * d0), 10000)
        pk = f"{c}:{r[ix['promoter_start_hg38']]}-{r[ix['promoter_end_hg38']]}"
        excl = by_prom[pk]
        for side in (1, -1):
            A = X.admissible_starts(c, P, d0, tol, side, fwd, rev, pu1, nih, excl)
            algebra = set()
            for a, b in A:
                algebra.update(range(a, b + 1))
            lo = (P + d0 - tol - W // 2) if side > 0 else (P - d0 - tol - W // 2)
            hi = (P + d0 + tol - W // 2) if side > 0 else (P - d0 + tol - W // 2)
            lo = max(0, lo)
            if hi < lo:
                brute = set()
            else:
                ex = X.norm([(x - W + 1, y - 1) for x, y in excl])
                cand = [s for s in range(lo, hi + 1)
                        if not any(a <= s <= b for a, b in ex)]
                bed = f"{WIN}/eqtest.bed"
                with open(bed, "w", newline="\n") as fh:
                    for s in cand:
                        fh.write(f"{c}\t{s}\t{s+W}\tS{s}\n")
                subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                                "cd /mnt/c/Users/dushy/jepa_c3 && "
                                "./liftOver_v479 -minMatch=0.95 eqtest.bed "
                                "hg19ToHg38.over.chain.gz eqtest.hg38.bed eqtest.un "
                                "2>/dev/null; "
                                "./liftOver_v479 -minMatch=0.95 -multiple -noSerial "
                                "eqtest.bed hg19ToHg38.over.chain.gz eqtest.multi.bed "
                                "eqtest.mun 2>/dev/null"],
                               capture_output=True, text=True, timeout=7200)
                f38 = {}
                for l in open(f"{WIN}/eqtest.hg38.bed"):
                    if l.strip() and not l.startswith("#"):
                        f = l.rstrip().split("\t")
                        f38[f[3]] = (f[0], int(f[1]), int(f[2]))
                mc = defaultdict(int)
                for l in open(f"{WIN}/eqtest.multi.bed"):
                    if l.strip() and not l.startswith("#"):
                        mc[l.rstrip().split("\t")[3]] += 1
                keep = {k: v for k, v in f38.items()
                        if mc[k] <= 1 and v[0] == c and v[2] - v[1] == W}
                with open(f"{WIN}/eqtest.rt.bed", "w", newline="\n") as fh:
                    for k, v in keep.items():
                        fh.write(f"{v[0]}\t{v[1]}\t{v[2]}\t{k}\n")
                subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                                "cd /mnt/c/Users/dushy/jepa_c3 && "
                                "./liftOver_v479 -minMatch=0.95 eqtest.rt.bed "
                                "hg38ToHg19.over.chain.gz eqtest.rt19.bed eqtest.rtun "
                                "2>/dev/null"],
                               capture_output=True, text=True, timeout=7200)
                brute = set()
                for l in open(f"{WIN}/eqtest.rt19.bed"):
                    if not l.strip() or l.startswith("#"):
                        continue
                    f = l.rstrip().split("\t")
                    s0 = int(f[3][1:])
                    if f[0] != c or int(f[1]) != s0 or int(f[2]) != s0 + W:
                        continue
                    h38 = keep[f[3]]
                    if not overlaps(pu1, pu_s, pu_m, c, h38[1], h38[2]):
                        continue
                    if not overlaps(nih, nh_s, nh_m, c, h38[1], h38[2]):
                        continue
                    brute.add(s0)
            same = algebra == brute
            allok &= same
            tested += 1
            if len(brute) > 0:
                nonempty += 1
            print(f"  edge {n:>2} side {side:+d}  algebra {len(algebra):>6}  "
                  f"brute {len(brute):>6}  EQUAL {same}")
            if not same:
                print("    only-algebra:", sorted(algebra - brute)[:5])
                print("    only-brute  :", sorted(brute - algebra)[:5])
    print("\nEXACT SET EQUALITY ON ALL TESTED EDGES/SIDES:", allok)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2))
