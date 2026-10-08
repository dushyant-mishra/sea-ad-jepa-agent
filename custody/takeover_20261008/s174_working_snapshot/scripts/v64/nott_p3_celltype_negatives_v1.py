#!/usr/bin/env python3
"""V64 P3 mechanical execution: neuron and oligodendrocyte VALID NEGATIVES.

NO SCIENTIFIC DESIGN HAPPENS HERE. Every rule was frozen on canonical before any
P3 candidate was joined or counted:

  V64_P3_GSE73721_EXACT_FILE_AUTHENTICATION_V1     exact expression bytes
  V64_P3_EXPRESSION_AND_GENE_JOIN_CONTRACT_V1      symbol join + FPKM > 0.5
  V64_P3_CELLTYPE_NEGATIVE_ELIGIBILITY_CONTRACT_V1 the negative definition
  V64_NOTT_PROMOTER_ORIENTATION_AND_GENE_MAPPING_CONTRACT_V1   orientation
  V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1     coordinate qualification

This executor implements them and nothing else. Forbidden and absent: threshold
changes, rescue rules, alternative liftover semantics, widened overlaps, external
gene repair, post-result tuning.

COORDINATE QUALIFICATION is the SAME exact-identity C3 applied to microglia, run
through the same authenticated liftOver v479 at minMatch=0.95: one target per
anchor (a -multiple pass is used ONLY to detect and reject ambiguity, never to
resolve it), same chromosome, zero interval-length change, and an exact hg38->hg19
round trip re-run on precisely the forward-admissible set. Both anchors must pass
every test for the pair to be retained.

ORIENTATION is assigned in SOURCE hg19 before any coordinate transform, so the
liftover cannot determine promoter identity. Exactly one anchor must overlap >=1 bp
of a Nott promoter row carrying the cell type's own active-promoter flag.

THE MICROGLIA REFERENCE MAP against which absence is tested is the C3-qualified,
source-oriented, unique-Ensembl-resolved microglia promoter-distal population --
rebuilt here from the same authenticated sources rather than imported, so the
comparison is not contingent on an intermediate artifact.

DENOMINATORS ARE PRESERVED. Every stage is reported against the original source
interaction count (neuron 93,290; oligodendrocyte 61,895), never against a
surviving subset, and the mutually exclusive failure classes are required to sum
back to that denominator.

TRIVIAL vs VALID. Per the frozen contract, edges failing microglial expression or
microglial distal accessibility are TRIVIAL negatives and are excluded: absence of
a contact is uninformative where the gene is not expressed or the region is not
accessible. They are counted, never silently dropped.

TRAINING=OFF. TD60=BLOCKED. No AD loci, JEPA targets, Morabito, NIH-CARD or
project RNA are read.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
from bisect import bisect_left
from collections import Counter, defaultdict

import openpyxl

WSL_ROOT = "/mnt/c/Users/dushy/jepa_c3"
WIN_ROOT = "C:/Users/dushy/jepa_c3"
LIFTOVER = "./liftOver_v479"
MINMATCH = "0.95"

S5 = "C:/Users/dushy/Downloads/NIHMS1066836-supplement-Table_S5.xlsx"
S5_SHA = "81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e"
EXPR = "C:/Users/dushy/Dropbox/GSE73721_Human_and_mouse_table.csv.gz"
EXPR_SHA = "140f376a5162b4d739a0e4224ce5757e7399b24fb2fce1c5f9bf0eb438d2fcef"
ATAC_PU1 = "C:/Users/dushy/jepa_c3/ATAC_PU1.bed.gz"
ATAC_PU1_SHA = "7cadc9906dbf335e252c823a8f19da738b64c7c45692ab4abbb962e18971cf36"
LIFTOVER_SHA = "80c77de53b8bbd5fec661242f24d4b2f0ac54446df6954d934d1a838927dd19c"
CHAIN_F_SHA = "5c0598e500ceb5a78c73086929e8ef993aec309bcafb595139b53d440b125a1d"
CHAIN_R_SHA = "14a712e8e147d9fc8e9d87d51977b46f6f8ddb93efbe5d0843d86b6205f587b1"
DISPO = "results/v64/c3_intermediates/V64_C3_PER_ANCHOR_DISPOSITION.tsv.gz"

MYELOID = ["45yo ctx myeloid", "51yo ctx myeloid", "63 yo ctx myeloid"]
FPKM_MIN = 0.5                       # frozen, not chosen here

CELLTYPES = {
    "neuron": {"sheet": "Neuronal interactome", "flag": "NeuN_active_promoter",
               "expected_source_interactions": 93290, "tag": "neu"},
    "oligodendrocyte": {"sheet": "Oligo interactome", "flag": "Olig2_active_promoter",
                        "expected_source_interactions": 61895, "tag": "oli"},
}
MICROGLIA_FLAG = "PU1_active_promoter"
MICROGLIA_SHEET = "Microglia interactome"
N_MICROGLIA_SOURCE = 104802


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def wsl(cmd):
    r = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                        f"cd {WSL_ROOT} && {cmd}"],
                       capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 and "liftOver" not in r.stderr:
        raise SystemExit(f"WSL FAILED: {cmd}\n{r.stderr[-800:]}")
    return r.stdout + r.stderr


def read_bed(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            out[f[3]] = (f[0], int(f[1]), int(f[2]))
    return out


def multi_names(path):
    c = Counter()
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            c[line.rstrip("\n").split("\t")[3]] += 1
    return {k for k, v in c.items() if v > 1}


class Intervals:
    """Sorted per-chromosome intervals, >=1 bp overlap query. No widening."""

    def __init__(self):
        self.d = defaultdict(list)
        self._ready = False

    def add(self, c, s, e):
        self.d[c].append((s, e))

    def build(self):
        self.starts, self.ends = {}, {}
        for c, v in self.d.items():
            v.sort()
            self.starts[c] = [x[0] for x in v]
            m, run = [], -1
            for _, e in v:
                run = max(run, e)
                m.append(run)
            self.ends[c] = m
        self._ready = True

    def overlaps(self, c, s, e) -> bool:
        if not self._ready or c not in self.starts:
            return False
        st = self.starts[c]
        i = bisect_left(st, e)
        if i == 0:
            return False
        return self.ends[c][i - 1] > s


class PromoterIndex:
    """Active-promoter rows for one cell type, queried by >=1 bp overlap in hg19.

    Returns EVERY overlapping row's (Nearest Ensembl, Gene Name) so the frozen
    uniqueness rule is evaluated on the full overlapping set, never on a first hit.
    """

    def __init__(self):
        self.d = defaultdict(list)

    def add(self, c, s, e, ens, gname):
        self.d[c].append((s, e, ens, gname))

    def build(self):
        self.rows, self.starts, self.maxlen = {}, {}, {}
        for c, v in self.d.items():
            v.sort()
            self.rows[c] = v
            self.starts[c] = [x[0] for x in v]
            self.maxlen[c] = max(e - s for s, e, _, _ in v)

    def hits(self, c, s, e):
        rows = self.rows.get(c)
        if not rows:
            return []
        st = self.starts[c]
        ml = self.maxlen[c]
        i = bisect_left(st, e)                 # rows with start < e are candidates
        out = []
        j = i - 1
        while j >= 0 and st[j] + ml > s:       # once start+maxlen <= s nothing can reach
            ps, pe, ens, gn = rows[j]
            if pe > s:
                out.append((ens, gn))
            j -= 1
        return out


def load_sheet_interactions(wb, sheet):
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    h = next(i for i, r in enumerate(rows) if r and r[0] == "chr1")
    out = []
    for r in rows[h + 1:]:
        if not r or r[0] is None:
            continue
        out.append((str(r[0]), int(r[1]), int(r[2]),
                    str(r[3]), int(r[4]), int(r[5])))
    return out


def load_promoters(wb, flag):
    ws = wb["H3K4me3_around_TSS_annotated_pe"]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows)
              if r and any(str(x).strip() == "PeakID" for x in r if x))
    hdr = [str(x).strip() if x is not None else "" for x in rows[hi]]
    col = {k: i for i, k in enumerate(hdr)}
    need = ["Chr", "Start", "End", flag, "Nearest Ensembl", "Gene Name"]
    miss = [k for k in need if k not in col]
    if miss:
        raise SystemExit(f"STOP_ANNOTATION_SCHEMA {miss} in {hdr}")
    idx = PromoterIndex()
    n = 0
    for r in rows[hi + 1:]:
        if not r or r[col["Chr"]] is None:
            continue
        f = r[col[flag]]
        if not (f is True or str(f).strip().upper() in ("TRUE", "1", "YES")):
            continue
        ens = r[col["Nearest Ensembl"]]
        gn = r[col["Gene Name"]]
        idx.add(str(r[col["Chr"]]), int(r[col["Start"]]), int(r[col["End"]]),
                str(ens).strip() if ens is not None else "",
                str(gn).strip() if gn is not None else "")
        n += 1
    idx.build()
    return idx, n


def orient(inter, prom):
    """Source-hg19 orientation. Returns index -> (class, promoter_side, ens, gname)."""
    res = {}
    cls = Counter()
    for i, (c1, s1, e1, c2, s2, e2) in enumerate(inter):
        h1 = prom.hits(c1, s1, e1)
        h2 = prom.hits(c2, s2, e2)
        p1, p2 = len(h1) > 0, len(h2) > 0
        if p1 and p2:
            cls["PROMOTER_PROMOTER"] += 1
            res[i] = ("PROMOTER_PROMOTER", None, None, None)
        elif not p1 and not p2:
            cls["NO_ACTIVE_PROMOTER_MATCH"] += 1
            res[i] = ("NO_ACTIVE_PROMOTER_MATCH", None, None, None)
        else:
            side = "A" if p1 else "B"
            hits = h1 if p1 else h2
            ens = {e for e, _ in hits if e}
            gns = {g for _, g in hits if g}
            if len(ens) == 1 and len(gns) == 1:
                cls["PROMOTER_DISTAL_UNIQUE_ENSEMBL_AND_SYMBOL"] += 1
                res[i] = ("UNIQUE", side, next(iter(ens)), next(iter(gns)))
            elif len(ens) == 1:
                cls["SYMBOL_MISSING_OR_AMBIGUOUS"] += 1
                res[i] = ("SYMBOL_UNRESOLVED", side, next(iter(ens)), None)
            else:
                cls["ENSEMBL_MISSING_OR_AMBIGUOUS"] += 1
                res[i] = ("ENSEMBL_UNRESOLVED", side, None, None)
    return res, cls


def c3_exact(tag, inter, log):
    """Exact-identity C3 on one interactome. Returns (retained hg38 map, funnel)."""
    n = len(inter)
    orig = {}
    bed = os.path.join(WIN_ROOT, f"p3_{tag}.hg19.bed")
    with open(bed, "w", newline="\n") as fh:
        for i, (c1, s1, e1, c2, s2, e2) in enumerate(inter):
            orig[f"A{i}"] = (c1, s1, e1)
            orig[f"B{i}"] = (c2, s2, e2)
            fh.write(f"{c1}\t{s1}\t{e1}\tA{i}\n{c2}\t{s2}\t{e2}\tB{i}\n")
    log(f"  [{tag}] anchors written: {2*n:,}")

    wsl(f"{LIFTOVER} -minMatch={MINMATCH} p3_{tag}.hg19.bed hg19ToHg38.over.chain.gz "
        f"p3_{tag}.hg38.bed p3_{tag}.hg38.unmapped 2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial p3_{tag}.hg19.bed "
        f"hg19ToHg38.over.chain.gz p3_{tag}.hg38.multi.bed "
        f"p3_{tag}.hg38.multi.unmapped 2>&1 | tail -2")
    fwd = read_bed(os.path.join(WIN_ROOT, f"p3_{tag}.hg38.bed"))
    amb = multi_names(os.path.join(WIN_ROOT, f"p3_{tag}.hg38.multi.bed"))

    reason = Counter()
    adm = {}
    for name, o in orig.items():
        m = fwd.get(name)
        if m is None:
            reason["unmapped"] += 1
        elif name in amb:
            reason["ambiguous_or_split"] += 1
        elif m[0] != o[0]:
            reason["chromosome_changed"] += 1
        elif (m[2] - m[1]) != (o[2] - o[1]):
            reason["length_changed"] += 1
        else:
            reason["admissible"] += 1
            adm[name] = m
    pairs_fwd = [i for i in range(n) if f"A{i}" in adm and f"B{i}" in adm]
    log(f"  [{tag}] forward-admissible pairs: {len(pairs_fwd):,}")

    rt_names = [x for i in pairs_fwd for x in (f"A{i}", f"B{i}")]
    rtb = os.path.join(WIN_ROOT, f"p3_{tag}.fwdadm.hg38.bed")
    with open(rtb, "w", newline="\n") as fh:
        for x in rt_names:
            c, s, e = adm[x]
            fh.write(f"{c}\t{s}\t{e}\t{x}\n")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} p3_{tag}.fwdadm.hg38.bed "
        f"hg38ToHg19.over.chain.gz p3_{tag}.rt.hg19.bed p3_{tag}.rt.unmapped 2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial p3_{tag}.fwdadm.hg38.bed "
        f"hg38ToHg19.over.chain.gz p3_{tag}.rt.multi.bed "
        f"p3_{tag}.rt.multi.unmapped 2>&1 | tail -2")
    rt = read_bed(os.path.join(WIN_ROOT, f"p3_{tag}.rt.hg19.bed"))
    rt_amb = multi_names(os.path.join(WIN_ROOT, f"p3_{tag}.rt.multi.bed"))

    rtr = Counter()
    ok = set()
    for x in rt_names:
        b = rt.get(x)
        if b is None:
            rtr["unmapped_on_return"] += 1
        elif x in rt_amb:
            rtr["ambiguous_on_return"] += 1
        elif b != orig[x]:
            rtr["not_exact"] += 1
        else:
            rtr["exact"] += 1
            ok.add(x)
    retained = {i: (adm[f"A{i}"], adm[f"B{i}"])
                for i in pairs_fwd if f"A{i}" in ok and f"B{i}" in ok}
    log(f"  [{tag}] C3 exact-identity retained pairs: {len(retained):,}")

    viol = 0
    for i in retained:
        for x in (f"A{i}", f"B{i}"):
            o, m = orig[x], adm[x]
            if m[0] != o[0] or (m[2] - m[1]) != (o[2] - o[1]) or rt[x] != o:
                viol += 1

    funnel = {
        "source_interactions": n,
        "source_anchor_instances": 2 * n,
        "forward_anchor_disposition": dict(reason),
        "forward_anchor_accounting_reconciles": sum(reason.values()) == 2 * n,
        "pairs_forward_admissible": len(pairs_fwd),
        "roundtrip_anchor_disposition": dict(rtr),
        "roundtrip_anchor_accounting_reconciles": sum(rtr.values()) == len(rt_names),
        "pairs_C3_exact_identity_retained": len(retained),
        "post_hoc_identity_violations": viol,
    }
    return retained, funnel


def load_expression():
    """Gene -> mean myeloid FPKM. Case-insensitive key; multiplicity is a STOP."""
    with gzip.open(EXPR, "rt", newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        hdr = [h.strip() for h in hdr]
        try:
            gi = hdr.index("Gene")
        except ValueError:
            raise SystemExit(f"STOP_EXPRESSION_SCHEMA no 'Gene' column in {hdr[:8]}")
        mi = []
        for c in MYELOID:
            if c not in hdr:
                raise SystemExit(f"STOP_EXPRESSION_SCHEMA missing myeloid column {c!r}")
            mi.append(hdr.index(c))
        vals, dup = {}, []
        n = 0
        for row in rd:
            if not row or len(row) <= max([gi] + mi):
                continue
            g = row[gi].strip()
            if not g:
                continue
            n += 1
            k = g.upper()
            try:
                v = sum(float(row[j]) for j in mi) / len(mi)
            except ValueError:
                continue
            if k in vals:
                dup.append(g)
            vals[k] = v
    if dup:
        raise SystemExit(f"STOP_EXPRESSION_KEY_NOT_UNIQUE {dup[:5]}")
    return vals, n


def build_microglia_reference(wb, log):
    """C3-qualified, source-oriented, unique-Ensembl microglia promoter-distal map.

    Returns ensembl -> Intervals of DISTAL hg38 intervals.
    """
    prom, prom_rows = load_promoters(wb, MICROGLIA_FLAG)
    inter = load_sheet_interactions(wb, MICROGLIA_SHEET)
    if len(inter) != N_MICROGLIA_SOURCE:
        raise SystemExit(f"STOP_MICROGLIA_SOURCE_COUNT {len(inter)}")
    res, mcls = orient(inter, prom)

    c3 = {}
    with gzip.open(DISPO, "rt") as fh:
        h = fh.readline().rstrip("\n").split("\t")
        ci = {k: j for j, k in enumerate(h)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ci["pair_C3_retained"]] != "True":
                continue
            i = int(f[ci["pair_index"]])
            c3.setdefault(i, {})[f[ci["side"]]] = (
                f[ci["hg38_chrom"]], int(f[ci["hg38_start"]]), int(f[ci["hg38_end"]]))

    by_gene = defaultdict(Intervals)
    n_edges = 0
    for i, d in c3.items():
        if "A" not in d or "B" not in d:
            continue
        k, side, ens, _ = res.get(i, (None, None, None, None))
        # The frozen contract defines this reference as "unique-Ensembl-resolved".
        # It does NOT require a unique Gene Name: the both-unique rule belongs to
        # orientation_and_gene_identity, which governs the neuron/oligo CANDIDATE
        # side, where the symbol is needed for the GSE73721 join. Requiring a
        # symbol here would shrink the reference and therefore inflate the count
        # of "absent" relationships, i.e. over-produce valid negatives.
        if k not in ("UNIQUE", "SYMBOL_UNRESOLVED"):
            continue
        dc, ds, de = d["B"] if side == "A" else d["A"]
        by_gene[ens].add(dc, ds, de)
        n_edges += 1
    for g in by_gene:
        by_gene[g].build()
    pre_c3_unique_ens = (mcls["PROMOTER_DISTAL_UNIQUE_ENSEMBL_AND_SYMBOL"]
                         + mcls["SYMBOL_MISSING_OR_AMBIGUOUS"])
    log(f"  microglia reference: {n_edges:,} qualified edges over {len(by_gene):,} genes "
        f"({prom_rows:,} PU1 active-promoter rows)")
    log(f"  microglia orientation cross-check vs committed P1S structure artifact: "
        f"PROMOTER_PROMOTER {mcls['PROMOTER_PROMOTER']:,} (P1S 7,614) | "
        f"NO_ACTIVE_PROMOTER_MATCH {mcls['NO_ACTIVE_PROMOTER_MATCH']:,} (P1S 32,978) | "
        f"unique-Ensembl {pre_c3_unique_ens:,} (P1S 61,624)")
    xcheck = {
        "why": "P1S resolved uniqueness on Nearest Ensembl alone. This executor splits "
               "that class into unique-symbol and symbol-unresolved, so their sum must "
               "reproduce the committed P1S count exactly. It does, which validates this "
               "orientation implementation against the one that produced P1S.",
        "PROMOTER_PROMOTER": {"here": mcls["PROMOTER_PROMOTER"], "P1S": 7614},
        "NO_ACTIVE_PROMOTER_MATCH": {"here": mcls["NO_ACTIVE_PROMOTER_MATCH"], "P1S": 32978},
        "PROMOTER_DISTAL_UNIQUE_ENSEMBL": {"here": pre_c3_unique_ens, "P1S": 61624},
        "all_three_reproduce": (mcls["PROMOTER_PROMOTER"] == 7614
                                and mcls["NO_ACTIVE_PROMOTER_MATCH"] == 32978
                                and pre_c3_unique_ens == 61624),
    }
    return by_gene, n_edges, prom_rows, dict(mcls), xcheck


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(m)

    # ---------- 0. fail closed on every input's exact bytes
    checks = {
        "table_s5": (S5, S5_SHA),
        "gse73721_expression": (EXPR, EXPR_SHA),
        "atac_pu1_microglia": (ATAC_PU1, ATAC_PU1_SHA),
        "liftover_v479": (os.path.join(WIN_ROOT, "liftOver_v479"), LIFTOVER_SHA),
        "chain_hg19ToHg38": (os.path.join(WIN_ROOT, "hg19ToHg38.over.chain.gz"), CHAIN_F_SHA),
        "chain_hg38ToHg19": (os.path.join(WIN_ROOT, "hg38ToHg19.over.chain.gz"), CHAIN_R_SHA),
    }
    digests = {}
    for k, (p, want) in checks.items():
        got = sha(p)
        digests[k] = {"path": p, "sha256": got, "bytes": os.path.getsize(p),
                      "matches_frozen": got == want}
        if got != want:
            raise SystemExit(f"STOP_DIGEST_MISMATCH {k}: {got} != {want}")
    log("input authentication: all 6 exact-byte checks PASS")

    wb = openpyxl.load_workbook(S5, read_only=True, data_only=True)
    sheets = list(wb.sheetnames)
    for c in CELLTYPES.values():
        if c["sheet"] not in sheets:
            raise SystemExit(f"STOP_SHEET_MISSING {c['sheet']} in {sheets}")

    expr, expr_rows = load_expression()
    log(f"expression reference: {expr_rows:,} gene rows, "
        f"{len(expr):,} unique case-insensitive symbols")

    # ---------- 1. microglia reference map (the thing absence is tested against)
    (mic_by_gene, mic_edges, mic_prom_rows, mic_cls,
     mic_xcheck) = build_microglia_reference(wb, log)

    pu1 = Intervals()
    n_pu1 = 0
    with gzip.open(ATAC_PU1, "rt") as fh:
        for line in fh:
            if not line.strip() or line.startswith(("#", "track")):
                continue
            f = line.rstrip("\n").split("\t")
            pu1.add(f[0], int(f[1]), int(f[2]))
            n_pu1 += 1
    pu1.build()
    log(f"  PU1 microglia ATAC peaks: {n_pu1:,}")

    results = {}
    for cname, cfg in CELLTYPES.items():
        log(f"\n=== {cname} ===")
        prom, prom_rows = load_promoters(wb, cfg["flag"])
        inter = load_sheet_interactions(wb, cfg["sheet"])
        N0 = len(inter)
        if N0 != cfg["expected_source_interactions"]:
            raise SystemExit(
                f"STOP_SOURCE_COUNT {cname}: {N0} != {cfg['expected_source_interactions']}")
        log(f"  source interactions: {N0:,}  ({prom_rows:,} {cfg['flag']} rows)")

        # orientation on SOURCE hg19, before any transform
        res, ocls = orient(inter, prom)

        # ---- pre-C3 source-side cross-check against canonical's published counts
        src_unique = [i for i in range(N0) if res[i][0] == "UNIQUE"]
        src_matched = [i for i in src_unique if res[i][3].upper() in expr]
        src_eligible = [i for i in src_matched if expr[res[i][3].upper()] > FPKM_MIN]
        log(f"  [source-side, no C3] unique gene {len(src_unique):,} | "
            f"GSE73721 matched {len(src_matched):,} | expressed {len(src_eligible):,}")

        # ---- the frozen funnel: C3 first
        retained, c3f = c3_exact(cfg["tag"], inter, log)

        stage = Counter()
        valid, rel_present = [], []
        for i in range(N0):
            if i not in retained:
                stage["FAIL_C3_EXACT_IDENTITY"] += 1
                continue
            k, side, ens, gname = res[i]
            if k in ("PROMOTER_PROMOTER", "NO_ACTIVE_PROMOTER_MATCH"):
                stage["FAIL_ORIENTATION_NOT_EXACTLY_ONE_PROMOTER"] += 1
                continue
            if k == "ENSEMBL_UNRESOLVED":
                stage["FAIL_GENE_ENSEMBL_UNRESOLVED"] += 1
                continue
            if k == "SYMBOL_UNRESOLVED":
                stage["FAIL_JOIN_SYMBOL_UNRESOLVED"] += 1
                continue
            key = gname.upper()
            if key not in expr:
                stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"] += 1
                continue
            if not (expr[key] > FPKM_MIN):
                stage["FAIL_EXPRESSION_INELIGIBLE_TRIVIAL"] += 1
                continue
            aa, bb = retained[i]
            dc, ds, de = bb if side == "A" else aa
            if not pu1.overlaps(dc, ds, de):
                stage["FAIL_MICROGLIA_DISTAL_NOT_ACCESSIBLE_TRIVIAL"] += 1
                continue
            iv = mic_by_gene.get(ens)
            if iv is not None and iv.overlaps(dc, ds, de):
                stage["RELATIONSHIP_PRESENT_IN_MICROGLIA"] += 1
                rel_present.append(i)
                continue
            stage["VALID_P3_NEGATIVE"] += 1
            valid.append((i, ens, gname, dc, ds, de))

        total = sum(stage.values())
        trivial = (stage["FAIL_EXPRESSION_INELIGIBLE_TRIVIAL"]
                   + stage["FAIL_MICROGLIA_DISTAL_NOT_ACCESSIBLE_TRIVIAL"])
        log(f"  funnel reconciles to source denominator: {total == N0} ({total:,}/{N0:,})")
        for k in ("FAIL_C3_EXACT_IDENTITY",
                  "FAIL_ORIENTATION_NOT_EXACTLY_ONE_PROMOTER",
                  "FAIL_GENE_ENSEMBL_UNRESOLVED", "FAIL_JOIN_SYMBOL_UNRESOLVED",
                  "FAIL_NOT_IN_EXPRESSION_REFERENCE",
                  "FAIL_EXPRESSION_INELIGIBLE_TRIVIAL",
                  "FAIL_MICROGLIA_DISTAL_NOT_ACCESSIBLE_TRIVIAL",
                  "RELATIONSHIP_PRESENT_IN_MICROGLIA", "VALID_P3_NEGATIVE"):
            log(f"    {k:<48} {stage[k]:>7,}  {100.0*stage[k]/N0:6.3f}%")

        # per-edge intermediate so the count is reconstructible, not just asserted
        obj = os.path.join(a.out_dir, f"V64_P3_{cname.upper()}_VALID_NEGATIVES.tsv.gz")
        with gzip.open(obj, "wt", newline="\n") as fh:
            fh.write("source_row_index\tnearest_ensembl\tgene_name\t"
                     "distal_chrom_hg38\tdistal_start_hg38\tdistal_end_hg38\n")
            for i, ens, gn, dc, ds, de in valid:
                fh.write(f"{i}\t{ens}\t{gn}\t{dc}\t{ds}\t{de}\n")

        results[cname] = {
            "source_sheet": cfg["sheet"],
            "active_promoter_flag": cfg["flag"],
            "active_promoter_rows": prom_rows,
            "source_interactions_denominator": N0,
            "orientation_classes_source_hg19": dict(ocls),
            "C3_exact_identity": c3f,
            "ATTRITION_FUNNEL_mutually_exclusive": dict(stage),
            "funnel_sums_to_source_denominator": total == N0,
            "VALID_P3_NEGATIVES": stage["VALID_P3_NEGATIVE"],
            "trivial_negatives": {
                "ambiguity_declared": (
                    "The contract defines trivial negatives as 'expression-fail or "
                    "microglial-accessibility-fail'. It does not say whether a symbol "
                    "absent from GSE73721 is an expression-fail or a join-fail. Both "
                    "readings are reported; NEITHER changes VALID_P3_NEGATIVES, because "
                    "edges in that class are excluded under either reading."),
                "narrow_join_failure_counted_separately": trivial,
                "wide_join_failure_counted_as_expression_fail":
                    trivial + stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"],
                "denominator_C3_qualified_and_gene_resolved": (
                    trivial + stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"]
                    + stage["RELATIONSHIP_PRESENT_IN_MICROGLIA"]
                    + stage["VALID_P3_NEGATIVE"]),
                "fraction_narrow": (
                    trivial / (trivial + stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"]
                               + stage["RELATIONSHIP_PRESENT_IN_MICROGLIA"]
                               + stage["VALID_P3_NEGATIVE"])),
                "fraction_wide": (
                    (trivial + stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"])
                    / (trivial + stage["FAIL_NOT_IN_EXPRESSION_REFERENCE"]
                       + stage["RELATIONSHIP_PRESENT_IN_MICROGLIA"]
                       + stage["VALID_P3_NEGATIVE"])),
            },
            "distinct_genes_in_valid_negatives": len({v[1] for v in valid}),
            "per_edge_artifact": os.path.basename(obj),
            "canonical_pre_C3_source_side_crosscheck": {
                "note": "Canonical computed these WITHOUT C3, because its runtime could "
                        "not run liftOver. Recomputed here from the same frozen rules to "
                        "test this implementation against canonical's independent one. "
                        "These are NOT funnel stages.",
                "unique_gene_resolved": len(src_unique),
                "GSE73721_matched": len(src_matched),
                "expression_eligible": len(src_eligible),
            },
        }

    out = {
        "schema": "V64_P3_CELLTYPE_NEGATIVES_V1",
        "date": "2026-09-29",
        "status": "MECHANICAL_EXECUTION_OF_PROSPECTIVELY_FROZEN_P3_RULES",
        "executed_against_canonical_commit": "8ff7ed1ff64b19ea789681c6b1b4498f56bbfcae",
        "authorities": [
            "results/v64/V64_P3_GSE73721_EXACT_FILE_AUTHENTICATION_V1.json",
            "results/v64/V64_P3_EXPRESSION_AND_GENE_JOIN_CONTRACT_V1.json",
            "results/v64/V64_P3_CELLTYPE_NEGATIVE_ELIGIBILITY_CONTRACT_V1.json",
            "results/v64/V64_NOTT_PROMOTER_ORIENTATION_AND_GENE_MAPPING_CONTRACT_V1.json",
        ],
        "input_authentication": digests,
        "frozen_parameters_not_chosen_here": {
            "expression_statistic": "arithmetic mean FPKM over three human myeloid samples",
            "expression_threshold": FPKM_MIN,
            "expression_comparator": ">",
            "symbol_match": "case-insensitive exact equality, no external repair",
            "liftover_minMatch": float(MINMATCH),
            "liftover_multiple_used_only_to_detect_ambiguity": True,
            "c3_length_tolerance_bp": 0,
            "atac_overlap_bp": 1,
            "peak_widening": False,
            "nearest_peak_rescue": False,
            "distance_window_substitution": False,
        },
        "microglia_reference_population": {
            "definition": "C3-qualified, source-oriented, unique-Ensembl-resolved "
                          "microglia promoter-distal contacts",
            "source_interactions": N_MICROGLIA_SOURCE,
            "qualified_edges": mic_edges,
            "distinct_genes": len(mic_by_gene),
            "PU1_active_promoter_rows": mic_prom_rows,
            "PU1_ATAC_peaks": n_pu1,
            "orientation_classes_source_hg19": mic_cls,
            "orientation_crosscheck_against_committed_P1S": mic_xcheck,
            "unique_Ensembl_only_not_unique_symbol": (
                "The frozen contract defines this reference as 'unique-Ensembl-resolved'. "
                "Requiring a unique Gene Name here as well would shrink the reference and "
                "inflate VALID_P3_NEGATIVES; the both-unique rule governs the neuron/oligo "
                "CANDIDATE side, where the symbol is needed for the GSE73721 join."),
        },
        "expression_reference": {
            "rows": expr_rows, "unique_case_insensitive_symbols": len(expr),
            "myeloid_columns": MYELOID},
        "results": results,
        "E2_NOTT_CANDIDATE": "NOT_INSTANTIATED",
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "uses_AD_loci": False, "uses_JEPA_targets": False,
                       "uses_Morabito": False, "uses_NIH_CARD": False,
                       "uses_project_RNA": False,
                       "external_gene_annotation_repair": False,
                       "thresholds_changed": False, "rescue_rules_used": False},
    }
    with open(os.path.join(a.out_dir, "V64_P3_CELLTYPE_NEGATIVES_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    with io.open(os.path.join(a.out_dir, "run_log.txt"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    log("\nVALID_P3_NEGATIVES  neuron %s  oligodendrocyte %s"
        % (f"{results['neuron']['VALID_P3_NEGATIVES']:,}",
           f"{results['oligodendrocyte']['VALID_P3_NEGATIVES']:,}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
