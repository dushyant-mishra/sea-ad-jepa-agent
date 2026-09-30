#!/usr/bin/env python3
"""Stage-3 outcome-blind ETL: Part-4 support funnel + hierarchical feature artifact.

Satisfies V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V1.

PHASE A (this script) builds the STRUCTURAL layer: gene resolution, consensus-peak
support, frozen matched-control construction, the full 20,709-edge attrition funnel,
and the hierarchical promoter/edge tables. Every quantity here is a coordinate, a
count, or an identifier.

PHASE B (separate pass) fills promoter_activity and distal_accessibility, which are
the only columns requiring matrix reads.

MATRIX ACCESS DECLARATION. Phase A reads NO matrix values at all. It touches
`var_names` (ATAC peak coordinates), `var['gene_ids']` (RNA Ensembl IDs) and
`obs['cell_type']`/`obs['SampleID']` for the microglia donor census. That is metadata
only, and is strictly narrower than the bounded integrity reads already performed.

HIERARCHY IS BUILT, NEVER INFERRED. promoter_key comes from the E2 table's hg38
promoter anchor. Every edge row carries its promoter_index explicitly. Nothing is
reconstructed later from feature equality.

TOPOLOGY WARNING HONOURED. promoter_degree is the real count of E2 linked edges on a
promoter. It is a NUISANCE COVARIATE. It is NOT the number of synthetic candidate
slots, which the frozen tournament fixes at 24 with 4 linked. This script does not
touch the simulator.

CONTROLS use the frozen rules verbatim: promoter fixed, same chromosome, 5 kb, source
hg19 separation matched within +/-10% or 10 kb, not overlapping any E2 distal partner
of that promoter, requiring >=1 Nott PU.1 peak AND >=1 NIH-CARD consensus peak, lifted
hg19->hg38 through the same C3 semantics. No nearest rescue. Identical support rules
are applied to linked and control rows.

FIREWALL. No E2 gene RNA is paired with its linked distal ATAC. No correspondence, no
Delta, no per-edge biological quantity. TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
from bisect import bisect_left
from collections import Counter, defaultdict

import numpy as np

E2 = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_SHA = "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c"
N_E2 = 20709
NOTT_PU1 = "C:/Users/dushy/jepa_c3/ATAC_PU1.bed.gz"
WSL_ROOT = "/mnt/c/Users/dushy/jepa_c3"
WIN_ROOT = "C:/Users/dushy/jepa_c3"
LIFTOVER = "./liftOver_v479"
MINMATCH = "0.95"

RNA_MD5 = "f628b17aab355f80b912e3c715543cbd"
ATAC_MD5 = "b71589e0033e391e2fe97c1ae3928a7f"
RNA_BYTES = 18439154935
ATAC_BYTES = 14508702462

ANCHOR_W = 5000
DIST_TOL_FRAC = 0.10
DIST_TOL_ABS = 10000
RE_WINDOW = 50000
MG = "MG"
MIN_MICROGLIA_PER_DONOR = 100     # frozen V1
TARGET_METACELL = 25              # frozen V1
SEED = 20260929


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True, check=True).stdout.strip()


def wsl(cmd):
    r = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                        f"cd {WSL_ROOT} && {cmd}"], capture_output=True,
                       text=True, timeout=7200)
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
        return self

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


def load_e2():
    with gzip.open(E2, "rb") as fh:
        raw = fh.read()
    if hashlib.sha256(raw).hexdigest() != E2_SHA:
        raise SystemExit("STOP_E2_DIGEST")
    lines = raw.decode().rstrip("\n").split("\n")
    hdr = lines[0].split("\t")
    ix = {k: i for i, k in enumerate(hdr)}
    rows = [{k: f[i] for k, i in ix.items()} for f in (l.split("\t") for l in lines[1:])]
    if len(rows) != N_E2:
        raise SystemExit(f"STOP_E2_COUNT {len(rows)}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    for nm, p, b in (("rna", a.rna, RNA_BYTES), ("atac", a.atac, ATAC_BYTES)):
        if os.path.getsize(p) != b:
            raise SystemExit(f"STOP_BYTES {nm}")
    log("input byte lengths match the authenticated receipt")

    edges = load_e2()
    log(f"E2 edges loaded and digest-verified: {len(edges):,}")

    import anndata
    rna = anndata.read_h5ad(a.rna, backed="r")
    atac = anndata.read_h5ad(a.atac, backed="r")

    # ---- NIH-CARD consensus peaks (coordinates only)
    nih = Intervals()
    for p in atac.var_names:
        c, se = str(p).split(":")
        s, e = se.split("-")
        nih.add(c, int(s), int(e))
    nih.build()
    log(f"NIH-CARD consensus peaks indexed: {atac.n_vars:,}")

    pu1 = Intervals()
    with gzip.open(NOTT_PU1, "rt") as fh:
        for line in fh:
            if line.strip() and not line.startswith(("#", "track")):
                f = line.rstrip("\n").split("\t")
                pu1.add(f[0], int(f[1]), int(f[2]))
    pu1.build()

    # ---- gene universe (identifiers only, no expression)
    gid = [str(g) for g in rna.var["gene_ids"].values]
    gid_count = Counter(gid)
    gset = set(gid)
    log(f"RNA gene_ids indexed: {len(gid):,} ({len(gset):,} unique)")

    # ---- donor census for support reporting (metadata only)
    ct = rna.obs["cell_type"].astype(str).values
    don = rna.obs["SampleID"].astype(str).values
    per_donor = Counter(don[i] for i in np.flatnonzero(ct == MG))
    qual = {d: n for d, n in per_donor.items() if n >= MIN_MICROGLIA_PER_DONOR}
    metacells = {d: n // TARGET_METACELL for d, n in qual.items()}
    log(f"microglia {sum(per_donor.values()):,} over {len(per_donor):,} donors; "
        f"{len(qual):,} donors with >= {MIN_MICROGLIA_PER_DONOR}")

    # ---- FUNNEL over all 20,709 E2 edges
    stage = Counter()
    admissible = []
    for i, e in enumerate(edges):
        ens = e["nearest_ensembl"]
        if ens not in gset:
            stage["DROP_GENE_NOT_IN_NIHCARD"] += 1
            continue
        if gid_count[ens] != 1:
            stage["DROP_GENE_AMBIGUOUS_IN_NIHCARD"] += 1
            continue
        c = e["chrom"]
        ds, de = int(e["distal_start_hg38"]), int(e["distal_end_hg38"])
        npk = nih.count(c, ds, de)
        if npk == 0:
            stage["DROP_NO_CONSENSUS_PEAK_OVER_DISTAL"] += 1
            continue
        stage["LINKED_STRUCTURALLY_SUPPORTED"] += 1
        admissible.append({"i": i, "e": e, "n_peaks": npk})
    log(f"linked structurally supported: {stage['LINKED_STRUCTURALLY_SUPPORTED']:,}")
    for k, v in stage.items():
        log(f"    {k:<42} {v:>7,}")

    # ---- matched controls, frozen rules, hg19 placement then C3 lift
    rng = np.random.default_rng(SEED)
    forb = Intervals()
    for e in edges:
        forb.add(e["chrom"], int(e["distal_start_hg19"]), int(e["distal_end_hg19"]))
    forb.build()
    cand_bed, cand_owner, n_cand_hist = [], [], []
    for rec in admissible:
        e = rec["e"]
        c = e["chrom"]
        pmid = (int(e["promoter_start_hg19"]) + int(e["promoter_end_hg19"])) // 2
        d0 = int(e["contact_distance_bp_hg19_source"])
        tol = max(DIST_TOL_FRAC * d0, DIST_TOL_ABS)
        # C-S45: enumerate candidate windows in hg19 WITHOUT any biological filter,
        # lift them all, and apply every biological constraint in hg38 -- the only
        # coordinate space the PU.1 and consensus-peak tracks live in.
        # C-S44 (superseded) used a 40-draw uniform rejection sampler.
        # C-S45 is the real bug it masked: the hg19 pre-filter tested hg19 windows
        # against the hg38 PU.1 track, so it selected essentially at random and the
        # apparent scarcity was a coordinate-space error, not a data property.
        band = []
        for sgn in (1, -1):
            lo, hi = int(d0 - tol), int(d0 + tol)
            step = max(1000, (hi - lo) // 60 or 1000)
            for dd in range(lo, hi + 1, step):
                st_ = pmid + sgn * dd - ANCHOR_W // 2
                if st_ < 0:
                    continue
                if forb.any(c, st_, st_ + ANCHOR_W):
                    continue
                band.append(st_)
        if not band:
            stage["DROP_NO_CANDIDATE_WINDOW_IN_BAND"] += 1
            continue
        for st_ in band:
            cand_bed.append((c, st_, st_ + ANCHOR_W, f"K{len(cand_bed)}"))
            cand_owner.append(rec)
        continue
    from collections import Counter as _C
    _per = _C(id(o) for o in cand_owner)
    log(f"candidate windows enumerated in hg19: {len(cand_bed):,} over "
        f"{len(_per):,} edges (median {int(np.median(list(_per.values()))) if _per else 0} "
        f"per edge)")

    bed = os.path.join(WIN_ROOT, "stage3_ctrl.hg19.bed")
    with open(bed, "w", newline="\n") as fh:
        for c, s_, e2_, n in cand_bed:
            fh.write(f"{c}\t{s_}\t{e2_}\t{n}\n")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} stage3_ctrl.hg19.bed hg19ToHg38.over.chain.gz "
        f"stage3_ctrl.hg38.bed stage3_ctrl.unmapped 2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial stage3_ctrl.hg19.bed "
        f"hg19ToHg38.over.chain.gz stage3_ctrl.multi.bed stage3_ctrl.multi.unmapped "
        f"2>&1 | tail -2")
    lifted, multi = {}, Counter()
    with open(os.path.join(WIN_ROOT, "stage3_ctrl.hg38.bed")) as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                f = line.rstrip("\n").split("\t")
                lifted[f[3]] = (f[0], int(f[1]), int(f[2]))
    with open(os.path.join(WIN_ROOT, "stage3_ctrl.multi.bed")) as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                multi[line.rstrip("\n").split("\t")[3]] += 1

    cstage = Counter()
    by_edge = defaultdict(list)
    for (c, s19, e19, n), rec in zip(cand_bed, cand_owner):
        m = lifted.get(n)
        if m is None:
            cstage["CAND_UNMAPPED"] += 1
        elif multi[n] > 1:
            cstage["CAND_AMBIGUOUS"] += 1
        elif m[0] != c:
            cstage["CAND_CHROM_CHANGED"] += 1
        elif (m[2] - m[1]) != ANCHOR_W:
            cstage["CAND_LENGTH_CHANGED"] += 1
        elif not pu1.any(*m):
            cstage["CAND_NO_NOTT_PU1_PEAK_HG38"] += 1
        elif nih.count(*m) == 0:
            cstage["CAND_NO_CONSENSUS_PEAK_HG38"] += 1
        else:
            cstage["CAND_ADMISSIBLE"] += 1
            by_edge[id(rec)].append({"rec": rec, "hg19": (c, s19, e19), "hg38": m,
                                     "n_peaks": nih.count(*m)})
    paired = []
    for rec in admissible:
        opts = by_edge.get(id(rec))
        if not opts:
            continue
        n_cand_hist.append(len(opts))
        paired.append(opts[int(rng.integers(0, len(opts)))])
    stage["DROP_NO_ADMISSIBLE_CONTROL_AFTER_LIFT"] = (
        stage["LINKED_STRUCTURALLY_SUPPORTED"]
        - stage.get("DROP_NO_CANDIDATE_WINDOW_IN_BAND", 0) - len(paired))
    for k, v in cstage.items():
        log(f"    {k:<42} {v:>7,}")
    log(f"    edges with >=1 admissible control: {len(paired):,} "
        f"(median options {int(np.median(n_cand_hist)) if n_cand_hist else 0})")

    ok_ids = {id(p["rec"]) for p in paired}
    final = [r for r in admissible if id(r) in ok_ids]
    stage["LINKED_STRUCTURALLY_SUPPORTED"] = len(final)
    total = sum(v for k, v in stage.items() if k.startswith("DROP_")) + len(final)
    log(f"\nfinal admissible linked rows: {len(final):,}; funnel reconciles to "
        f"{N_E2:,}: {total == N_E2}")

    # ---- hierarchical tables
    prom_key_of = {}
    prom_rows = []
    for r in final:
        e = r["e"]
        pk = f"{e['chrom']}:{e['promoter_start_hg38']}-{e['promoter_end_hg38']}"
        if pk not in prom_key_of:
            prom_key_of[pk] = len(prom_rows)
            prom_rows.append({"promoter_key": pk, "promoter_index": prom_key_of[pk],
                              "nearest_ensembl": e["nearest_ensembl"],
                              "promoter_start_hg19": int(e["promoter_start_hg19"]),
                              "promoter_end_hg19": int(e["promoter_end_hg19"])})
    deg_all = Counter()
    for e in edges:
        deg_all[f"{e['chrom']}:{e['promoter_start_hg38']}-{e['promoter_end_hg38']}"] += 1
    for p in prom_rows:
        p["promoter_degree"] = deg_all[p["promoter_key"]]
    anc = Counter()
    for e in edges:
        anc[f"{e['chrom']}:{e['distal_start_hg38']}"] += 1

    edge_rows = []
    for r, pr in zip(final, [None] * len(final)):
        e = r["e"]
        pk = f"{e['chrom']}:{e['promoter_start_hg38']}-{e['promoter_end_hg38']}"
        pidx = prom_key_of[pk]
        c = e["chrom"]
        ds, de = int(e["distal_start_hg38"]), int(e["distal_end_hg38"])
        mid = (ds + de) // 2
        edge_rows.append({
            "pair_key": f"L{r['i']}", "promoter_index": pidx, "promoter_key": pk,
            "population": "LINKED",
            "source_hg19_distance_bp": int(e["contact_distance_bp_hg19_source"]),
            "log_distance": float(np.log(max(1, int(e["contact_distance_bp_hg19_source"])))),
            "re_density": float(nih.count(c, mid - RE_WINDOW, mid + RE_WINDOW)),
            "anchor_frequency": float(anc[f"{c}:{ds}"]),
            "nihcard_peaks_over_distal": int(r["n_peaks"]),
            "distal_chrom": c, "distal_start_hg38": ds, "distal_end_hg38": de,
        })
    for p in paired:
        r = p["rec"]
        e = r["e"]
        pk = f"{e['chrom']}:{e['promoter_start_hg38']}-{e['promoter_end_hg38']}"
        if pk not in prom_key_of:
            continue
        c, ds, de = p["hg38"]
        mid = (ds + de) // 2
        d19 = abs(((p["hg19"][1] + p["hg19"][2]) // 2)
                  - ((int(e["promoter_start_hg19"]) + int(e["promoter_end_hg19"])) // 2))
        edge_rows.append({
            "pair_key": f"C{r['i']}", "promoter_index": prom_key_of[pk],
            "promoter_key": pk, "population": "CONTROL",
            "source_hg19_distance_bp": int(d19),
            "log_distance": float(np.log(max(1, d19))),
            "re_density": float(nih.count(c, mid - RE_WINDOW, mid + RE_WINDOW)),
            "anchor_frequency": float(anc.get(f"{c}:{ds}", 0)),
            "nihcard_peaks_over_distal": int(p["n_peaks"]),
            "distal_chrom": c, "distal_start_hg38": ds, "distal_end_hg38": de,
        })

    # ---- validation
    pk_all = [r["pair_key"] for r in edge_rows]
    if len(set(pk_all)) != len(pk_all):
        raise SystemExit("STOP_PAIR_KEY_NOT_UNIQUE")
    byp = defaultdict(set)
    for r in edge_rows:
        byp[r["promoter_index"]].add(prom_rows[r["promoter_index"]]["promoter_degree"])
    if any(len(v) != 1 for v in byp.values()):
        raise SystemExit("STOP_PROMOTER_DEGREE_NOT_CONSTANT")
    nL = sum(1 for r in edge_rows if r["population"] == "LINKED")
    nC = len(edge_rows) - nL
    blocks = Counter(r["promoter_index"] for r in edge_rows)
    log(f"\nhierarchy: {len(prom_rows):,} promoters | {nL:,} LINKED | {nC:,} CONTROL")
    log(f"block sizes: min {min(blocks.values())} median "
        f"{int(np.median(list(blocks.values())))} max {max(blocks.values())}")
    log(f"real promoter_degree: min {min(p['promoter_degree'] for p in prom_rows)} "
        f"max {max(p['promoter_degree'] for p in prom_rows)}")

    ekeys = sorted(edge_rows[0].keys())
    pkeys = sorted(prom_rows[0].keys())
    np.savez_compressed(
        os.path.join(a.out_dir, "V64_NIH_CARD_STAGE3_STRUCTURAL_V1.npz"),
        edge_table=np.array([[str(r[k]) for k in ekeys] for r in edge_rows], dtype=object),
        edge_columns=np.array(ekeys, dtype=object),
        promoter_table=np.array([[str(p[k]) for k in pkeys] for p in prom_rows], dtype=object),
        promoter_columns=np.array(pkeys, dtype=object),
        promoter_index=np.array([r["promoter_index"] for r in edge_rows], dtype=int))

    out = {
        "schema": "V64_NIH_CARD_STAGE3_STRUCTURAL_RECEIPT_V1",
        "date": "2026-09-30", "phase": "A_STRUCTURAL_NO_MATRIX_VALUES",
        "contract": "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V1.json",
        "producer": {"path": __file__.replace("\\", "/").split("/")[-1],
                     "git_blob": None, "sha256": sha256_file(__file__)},
        "inputs": {
            "e2_edge_table_sha256": E2_SHA,
            "rna": {"bytes": RNA_BYTES, "md5": RNA_MD5},
            "atac": {"bytes": ATAC_BYTES, "md5": ATAC_MD5},
            "authentication_receipt": "results/v64/V64_NIH_CARD_LOCAL_BYTE_AUTHENTICATION_V1.json",
            "pairing_closeout": "results/v64/V64_NIH_CARD_PAIRING_EXECUTION_RECEIPT_V1.json"},
        "MATRIX_ACCESS_DECLARATION": {
            "matrix_values_read": "NONE",
            "metadata_read": ["atac.var_names", "rna.var['gene_ids']",
                              "rna.obs['cell_type']", "rna.obs['SampleID']"],
            "why_outcome_blind": "coordinates, identifiers and a cell-type/donor census "
                                 "only; no expression or accessibility value is read in "
                                 "this phase"},
        "ATTRITION_FUNNEL": {"denominator": N_E2, "stages": dict(stage),
                             "control_stages": dict(cstage),
                             "admissible_control_windows_per_edge": {
                                 "median": float(np.median(n_cand_hist)) if n_cand_hist else None,
                                 "max": int(max(n_cand_hist)) if n_cand_hist else None},
                             "reconciles": bool(total == N_E2)},
        "donor_support": {
            "microglia_total": int(sum(per_donor.values())),
            "donors_with_microglia": len(per_donor),
            "donors_meeting_min_microglia": len(qual),
            "min_microglia_per_donor": MIN_MICROGLIA_PER_DONOR,
            "target_metacell_size": TARGET_METACELL,
            "metacells_per_qualifying_donor": {
                "min": int(min(metacells.values())) if metacells else None,
                "median": float(np.median(list(metacells.values()))) if metacells else None,
                "max": int(max(metacells.values())) if metacells else None}},
        "hierarchy": {
            "promoters": len(prom_rows), "linked_rows": nL, "control_rows": nC,
            "edge_rows": len(edge_rows),
            "block_size": {"min": int(min(blocks.values())),
                           "median": float(np.median(list(blocks.values()))),
                           "max": int(max(blocks.values()))},
            "real_promoter_degree": {
                "min": int(min(p["promoter_degree"] for p in prom_rows)),
                "max": int(max(p["promoter_degree"] for p in prom_rows))},
            "TOPOLOGY_NOTE": "real promoter_degree is a NUISANCE COVARIATE. It is NOT "
                             "the synthetic candidate-slot count, which the frozen "
                             "tournament fixes at 24 with 4 linked."},
        "pending_phase_B": ["promoter_activity", "distal_accessibility"],
        "feature_definitions": {
            "source_hg19_distance_bp": "midpoint-to-midpoint separation in hg19 source coordinates",
            "log_distance": "natural log of source_hg19_distance_bp",
            "promoter_degree": "count of E2 linked edges sharing the hg38 promoter anchor",
            "re_density": f"NIH-CARD consensus peaks whose interval overlaps a +/-{RE_WINDOW} bp window around the distal midpoint",
            "anchor_frequency": "count of E2 edges sharing the distal hg38 start coordinate"},
        "no_correspondence_computed": True,
        "governance": {"training": "OFF", "td60": "BLOCKED", "Morabito": "PROTECTED",
                       "stage_4": "NOT_AUTHORISED"},
    }
    p = os.path.join(a.out_dir, "V64_NIH_CARD_STAGE3_STRUCTURAL_RECEIPT_V1.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2)
    with open(os.path.join(a.out_dir, "run_log.txt"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log(f"\nwritten {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
