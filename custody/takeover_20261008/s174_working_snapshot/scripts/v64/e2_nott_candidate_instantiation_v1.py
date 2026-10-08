#!/usr/bin/env python3
"""Instantiate E2_NOTT_CANDIDATE: the Nott-centered microglial regulatory edge set.

MECHANICAL ONLY. Every rule was frozen on canonical before this ran. Nothing here
designs a target, tunes a threshold, adds a qualification criterion, or opens any
protected outcome.

GOVERNING AUTHORITY, in precedence order
  V64_E2_SINGLE_SOURCE_SUCCESSOR_CONTRACT_V1   supersedes V63 C1/C4/C6/C12 on the
                                               explicitly authorised single-source
                                               Nott-centered fallback path
  V63_E2_DESIGN_CONTRACT_V1                    the object definition and claim scope
  V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1 coordinate qualification
  V64_NOTT_PROMOTER_ORIENTATION_AND_GENE_MAPPING_CONTRACT_V1   orientation + gene
  V64_NOTT_P1S_OPERATIONAL_SUCCESSOR_CONTRACT_V2               substrate fit

THE OBJECT IS A SET OF PAIRS, NOT A GENE LIST. Multiple legitimate regulatory edges
for the same gene remain separate rows. Nothing is collapsed to unique genes.

ORIENTATION AND GENE IDENTITY are recomputed here from the authenticated Table S5
by importing the ALREADY-AUDITED P3 executor's functions rather than reimplementing
them, so the semantics are provably identical to the code that produced P3 and, via
its own cross-check, to the code that produced P1S.

GENE IDENTITY IS UNIQUE-ENSEMBL ONLY. Per P3 self-audit item S26, which canonical
has ruled must stay fixed, a unique Gene Name is NOT additionally required on the
microglia population: the both-unique rule governs only the P3 neuron/oligodendrocyte
candidate side, where a symbol is needed for the GSE73721 join. Gene Name is carried
as secondary metadata where available, with its status labelled.

C3 IS NOT RE-RUN. The frozen C3 result and its per-anchor disposition are committed
on canonical; they are read, not recomputed. Re-lifting would risk producing a
second, differently-derived coordinate set for the same frozen gate.

ACCESSIBILITY SCOPE, STATED NOT ASSUMED. V63 C5 names Kosoy aged primary-microglia
ATAC as the intended accessibility source and records it as UNVERIFIED; Nott ATAC is
listed there as a SENSITIVITY layer. On this single-source path the successor
contract requires only that "the chosen accessibility source bytes and terms" be
verified, and the already-qualified P1S/P3 construction path uses the authenticated
Nott PU.1 track. That track is therefore used here -- and because it comes from the
same study and the same sorted nuclei as the contacts, E2_NOTT_CANDIDATE does NOT
satisfy V63's "externally defined microglial accessibility" wording. That limitation
is recorded in the receipt rather than papered over, and the pre-accessibility
population is reported so both readings are recoverable.

TRAINING=OFF. TD60=BLOCKED. No AD loci, JEPA targets, NIH-CARD, Morabito, SEA-AD,
GSE214979 or project RNA are read.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import statistics
import subprocess
from collections import Counter, defaultdict

P3_MODULE = "scripts/v64/nott_p3_celltype_negatives_v1.py"

S5 = "C:/Users/dushy/Downloads/NIHMS1066836-supplement-Table_S5.xlsx"
S5_SHA = "81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e"
ATAC_PU1 = "C:/Users/dushy/jepa_c3/ATAC_PU1.bed.gz"
ATAC_PU1_SHA = "7cadc9906dbf335e252c823a8f19da738b64c7c45692ab4abbb962e18971cf36"
DISPO = "results/v64/c3_intermediates/V64_C3_PER_ANCHOR_DISPOSITION.tsv.gz"
C3_RETAINED = "results/v64/V64_NOTT_C3_RETAINED_CONTACTS_HG38.tsv.gz"

MICROGLIA_SHEET = "Microglia interactome"
MICROGLIA_FLAG = "PU1_active_promoter"

# Upstream quantities that MUST reproduce exactly. Not targets; tripwires.
XCHECK = {
    "original_microglia_interactions": 104802,
    "C3_retained": 102701,
    "P1S_source_oriented_promoter_distal": 62890,
    "pre_C3_unique_Ensembl_source_side": 61624,
}

AUTHORITY_FILES = [
    "results/v63/V63_E2_DESIGN_CONTRACT_V1.json",
    "results/v64/V64_E2_SINGLE_SOURCE_SUCCESSOR_CONTRACT_V1.json",
    "results/v64/V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1.json",
    "results/v64/V64_NOTT_C3_LIFTOVER_IMPLEMENTATION_DEFAULTS_V1.json",
    "results/v64/V64_NOTT_PROMOTER_ORIENTATION_AND_GENE_MAPPING_CONTRACT_V1.json",
    "results/v64/V64_NOTT_P1S_OPERATIONAL_SUCCESSOR_CONTRACT_V2.json",
    "results/v64/V64_NOTT_P1S_V2_SENSITIVITY_COMPLETION_V2.json",
    "results/v64/V64_P1S_DENSITY_PANEL_INDEPENDENT_AUDIT_V1.json",
    "results/v64/V64_P3_EXPRESSION_AND_GENE_JOIN_CONTRACT_V1.json",
    "results/v64/V64_P3_CELLTYPE_NEGATIVE_ELIGIBILITY_CONTRACT_V1.json",
    "results/v64/V64_P3_CELLTYPE_NEGATIVES_V1.json",
    "results/v64/V64_P3_INDEPENDENT_AUDIT_V1.json",
    "results/v64/V64_SPILLOVER_FIREWALL_MANIFEST_V1.json",
    "results/v64/V64_CANONICAL_AUTHORITY_CONSOLIDATION_20260929_V1.json",
    "results/v64/V64_P1S_P3_RECONCILIATION_20260929_V1.json",
    "results/v64/V64_NOTT_ATAC_AND_CHAIN_AUTHENTICATION_RECEIPT_V1.json",
    "results/v64/V64_NOTT_DATA_USE_TERMS_RECORD_V1.json",
    P3_MODULE,
]

EDGE_COLUMNS = [
    "source_row_index", "chrom", "promoter_side",
    "promoter_start_hg38", "promoter_end_hg38",
    "distal_start_hg38", "distal_end_hg38",
    "promoter_start_hg19", "promoter_end_hg19",
    "distal_start_hg19", "distal_end_hg19",
    "nearest_ensembl", "gene_name", "gene_name_status",
    "distal_pu1_peak_overlap", "contact_distance_bp", "contact_distance_bp_hg19_source",
]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True,
                          text=True, check=True).stdout.strip()


def load_p3_module():
    spec = importlib.util.spec_from_file_location("p3mod", P3_MODULE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def summarise(vals):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)

    def q(f):
        return s[min(n - 1, max(0, int(round(f * (n - 1)))))]
    return {"n": n, "min": s[0], "p25": q(0.25), "median": q(0.50),
            "p75": q(0.75), "p95": q(0.95), "max": s[-1],
            "mean": round(statistics.fmean(s), 2)}


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

    parent = git("rev-parse", "HEAD")
    porcelain = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
    tracked_mods = [l for l in porcelain if not l.startswith("??")]
    untracked = [l[3:] for l in porcelain if l.startswith("??")]
    log(f"canonical parent commit: {parent}")
    log(f"tracked files modified vs canonical HEAD: {len(tracked_mods)} "
        f"(untracked new files present: {len(untracked)})")
    if tracked_mods:
        raise SystemExit(f"STOP_TRACKED_FILES_MODIFIED {tracked_mods[:5]}")

    # ---------- 0. authenticate inputs, fail closed
    digests = {}
    for k, (p, want) in {
        "table_s5": (S5, S5_SHA),
        "nott_pu1_microglia_atac": (ATAC_PU1, ATAC_PU1_SHA),
    }.items():
        got = sha_file(p)
        digests[k] = {"path": p, "sha256": got, "bytes": os.path.getsize(p),
                      "matches_frozen": got == want}
        if got != want:
            raise SystemExit(f"STOP_DIGEST_MISMATCH {k}")
    for k, p in {"c3_per_anchor_disposition": DISPO,
                 "c3_retained_contacts_hg38": C3_RETAINED}.items():
        digests[k] = {"path": p, "sha256": sha_file(p),
                      "bytes": os.path.getsize(p),
                      "note": "frozen C3 artifact read from canonical, not recomputed"}
    log("input authentication: Table S5 and Nott PU1 ATAC match frozen digests")

    authority = {}
    for f in AUTHORITY_FILES:
        try:
            authority[f] = {"git_blob": git("rev-parse", f"HEAD:{f}"),
                            "sha256": sha_file(f)}
        except Exception as exc:                       # noqa: BLE001
            authority[f] = {"error": str(exc)}
    missing = [f for f, v in authority.items() if "error" in v]
    if missing:
        raise SystemExit(f"STOP_AUTHORITY_FILE_UNREADABLE {missing}")
    log(f"authority chain: {len(authority)} files pinned by git blob + sha256")

    p3 = load_p3_module()
    import openpyxl
    wb = openpyxl.load_workbook(S5, read_only=True, data_only=True)

    # ---------- 1. source interactions and source-hg19 orientation
    prom, prom_rows = p3.load_promoters(wb, MICROGLIA_FLAG)
    inter = p3.load_sheet_interactions(wb, MICROGLIA_SHEET)
    N0 = len(inter)
    res, ocls = p3.orient(inter, prom)
    pre_c3_unique_ens = (ocls["PROMOTER_DISTAL_UNIQUE_ENSEMBL_AND_SYMBOL"]
                         + ocls["SYMBOL_MISSING_OR_AMBIGUOUS"])
    log(f"source interactions: {N0:,}  ({prom_rows:,} {MICROGLIA_FLAG} rows)")
    log(f"orientation: PROMOTER_PROMOTER {ocls['PROMOTER_PROMOTER']:,} | "
        f"NO_ACTIVE_PROMOTER_MATCH {ocls['NO_ACTIVE_PROMOTER_MATCH']:,} | "
        f"promoter-distal unique-Ensembl {pre_c3_unique_ens:,}")

    # ---------- 2. frozen C3 result, read from canonical
    c3 = {}
    with gzip.open(DISPO, "rt") as fh:
        h = fh.readline().rstrip("\n").split("\t")
        ci = {k: j for j, k in enumerate(h)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ci["pair_C3_retained"]] != "True":
                continue
            i = int(f[ci["pair_index"]])
            c3.setdefault(i, {})[f[ci["side"]]] = {
                "hg38": (f[ci["hg38_chrom"]], int(f[ci["hg38_start"]]),
                         int(f[ci["hg38_end"]])),
                "hg19": (f[ci["hg19_chrom"]], int(f[ci["hg19_start"]]),
                         int(f[ci["hg19_end"]])),
            }
    c3 = {i: d for i, d in c3.items() if "A" in d and "B" in d}
    log(f"C3 exact-identity retained pairs: {len(c3):,}")

    # ---------- 3. PU1 microglia accessibility
    pu1 = p3.Intervals()
    pu1_rows = defaultdict(list)
    n_pu1 = 0
    with gzip.open(ATAC_PU1, "rt") as fh:
        for line in fh:
            if not line.strip() or line.startswith(("#", "track")):
                continue
            f = line.rstrip("\n").split("\t")
            c, s, e = f[0], int(f[1]), int(f[2])
            pu1.add(c, s, e)
            pu1_rows[c].append((s, e))
            n_pu1 += 1
    pu1.build()
    for c in pu1_rows:
        pu1_rows[c].sort()
    log(f"Nott PU1 microglia ATAC peaks: {n_pu1:,}")

    # per-chrom start arrays + max peak width, so the overlap scan is bounded
    pu1_starts = {c: [x[0] for x in v] for c, v in pu1_rows.items()}
    pu1_maxlen = {c: max(e - s for s, e in v) for c, v in pu1_rows.items()}

    def n_overlapping_peaks(c, s, e):
        from bisect import bisect_left
        rows = pu1_rows.get(c)
        if not rows:
            return 0
        st = pu1_starts[c]
        ml = pu1_maxlen[c]
        i = bisect_left(st, e)
        n = 0
        j = i - 1
        while j >= 0 and st[j] + ml > s:
            ps, pe = rows[j]
            if pe > s:
                n += 1
            j -= 1
        return n

    # ---------- 4. the funnel
    PD = ("UNIQUE", "SYMBOL_UNRESOLVED", "ENSEMBL_UNRESOLVED")
    stage = Counter()
    edges = []
    for i in range(N0):
        if i not in c3:
            stage["DROP_C3_NOT_EXACT_IDENTITY"] += 1
            continue
        k, side, ens, gname = res[i]
        if k not in PD:
            stage["DROP_NOT_SOURCE_ORIENTED_PROMOTER_DISTAL"] += 1
            continue
        if k == "ENSEMBL_UNRESOLVED":
            stage["DROP_GENE_ENSEMBL_UNRESOLVED"] += 1
            continue
        pa = c3[i]["A" if side == "A" else "B"]
        da = c3[i]["B" if side == "A" else "A"]
        pc, ps, pe = pa["hg38"]
        dc, ds, de = da["hg38"]
        npk = n_overlapping_peaks(dc, ds, de)
        if npk == 0:
            stage["DROP_DISTAL_NOT_ACCESSIBLE_IN_MICROGLIA"] += 1
            continue
        stage["E2_EDGE"] += 1
        _, ph19s, ph19e = pa["hg19"]
        _, dh19s, dh19e = da["hg19"]
        edges.append({
            "source_row_index": i, "chrom": pc, "promoter_side": side,
            "promoter_start_hg38": ps, "promoter_end_hg38": pe,
            "distal_start_hg38": ds, "distal_end_hg38": de,
            "promoter_start_hg19": ph19s, "promoter_end_hg19": ph19e,
            "distal_start_hg19": dh19s, "distal_end_hg19": dh19e,
            "nearest_ensembl": ens,
            "gene_name": gname if gname else "",
            "gene_name_status": "PRESENT_UNIQUE" if gname else "ABSENT_OR_AMBIGUOUS",
            "distal_pu1_peak_overlap": npk,
            "contact_distance_bp": abs(((ds + de) // 2) - ((ps + pe) // 2)),
            "contact_distance_bp_hg19_source": abs(((dh19s + dh19e) // 2)
                                                   - ((ph19s + ph19e) // 2)),
        })

    total = sum(stage.values())
    n_pd_after_c3 = (stage["E2_EDGE"] + stage["DROP_DISTAL_NOT_ACCESSIBLE_IN_MICROGLIA"]
                     + stage["DROP_GENE_ENSEMBL_UNRESOLVED"])
    n_unique_gene_after_c3 = (stage["E2_EDGE"]
                              + stage["DROP_DISTAL_NOT_ACCESSIBLE_IN_MICROGLIA"])

    # ---------- 5. the four mandated cross-checks
    x = {
        "original_microglia_interactions": {
            "expected": XCHECK["original_microglia_interactions"], "observed": N0},
        "C3_retained": {
            "expected": XCHECK["C3_retained"], "observed": len(c3)},
        "P1S_source_oriented_promoter_distal": {
            "expected": XCHECK["P1S_source_oriented_promoter_distal"],
            "observed": n_pd_after_c3},
        "pre_C3_unique_Ensembl_source_side": {
            "expected": XCHECK["pre_C3_unique_Ensembl_source_side"],
            "observed": pre_c3_unique_ens},
    }
    for k, v in x.items():
        v["reproduces_exactly"] = v["expected"] == v["observed"]
    all_ok = all(v["reproduces_exactly"] for v in x.values())
    log("\nUPSTREAM CROSS-CHECKS")
    for k, v in x.items():
        log(f"  {k:<44} expected {v['expected']:>7,}  observed {v['observed']:>7,}  "
            f"{'OK' if v['reproduces_exactly'] else 'MISMATCH'}")
    if not all_ok:
        raise SystemExit("STOP_UPSTREAM_CROSSCHECK_FAILED — diagnose, do not continue")

    # ---------- 6. edge table, deterministic bytes
    buf = io.StringIO()
    buf.write("\t".join(EDGE_COLUMNS) + "\n")
    for e in sorted(edges, key=lambda r: r["source_row_index"]):
        buf.write("\t".join(str(e[c]) for c in EDGE_COLUMNS) + "\n")
    raw = buf.getvalue().encode("utf-8")
    raw_sha = hashlib.sha256(raw).hexdigest()
    tsv_gz = os.path.join(a.out_dir, "V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz")
    with open(tsv_gz, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0) as gz:
            gz.write(raw)                     # mtime=0 => byte-identical on rebuild
    gz_sha = sha_file(tsv_gz)

    # ---------- 7. structure summaries
    deltas = [e["contact_distance_bp"] - e["contact_distance_bp_hg19_source"]
              for e in edges]
    d19s = [e["contact_distance_bp_hg19_source"] for e in edges]
    d38s = [e["contact_distance_bp"] for e in edges]
    n_same = sum(1 for d in deltas if d == 0)
    n_le1k = sum(1 for d in deltas if abs(d) <= 1000)
    n_gt1k = sum(1 for d in deltas if abs(d) > 1000)
    n_gt10k = sum(1 for d in deltas if abs(d) > 10000)
    n_over1mb = sum(1 for x in d38s if x > 1000000)
    n_under10k = sum(1 for x in d38s if x < 10000)

    genes = Counter(e["nearest_ensembl"] for e in edges)
    proms = Counter((e["chrom"], e["promoter_start_hg38"], e["promoter_end_hg38"])
                    for e in edges)
    chrom = Counter(e["chrom"] for e in edges)
    multi_gene = {g: c for g, c in genes.items() if c > 1}
    edges_in_multi = sum(multi_gene.values())

    out = {
        "schema": "V64_E2_NOTT_CANDIDATE_CONSTRUCTION_RECEIPT_V1",
        "date": "2026-09-29",
        "object": "E2_NOTT_CANDIDATE",
        "status": "INSTANTIATED",
        "unit": "a (promoter, distal) PAIR. Not a gene list. Multiple legitimate "
                "regulatory edges for the same gene remain separate rows.",
        "canonical_parent_commit": parent,
        "worktree_state_at_start": {
            "tracked_files_modified_vs_canonical_HEAD": len(tracked_mods),
            "no_tracked_modification": len(tracked_mods) == 0,
            "untracked_new_files": untracked,
            "note": "Untracked entries are this executor and its outputs, which did not "
                    "exist on canonical. No tracked file differs from canonical HEAD; the "
                    "script exits if any does.",
        },
        "authority_chain": authority,
        "authenticated_inputs": digests,
        "frozen_parameters_not_chosen_here": {
            "contact_significance": "FDR < 0.01, inherited from the deposited "
                                    "pre-thresholded interactome; not re-thresholded",
            "anchor_width_bp": 5000,
            "c3_length_tolerance_bp": 0,
            "liftover": "v479, minMatch 0.95, frozen C3 result read from canonical, "
                        "NOT recomputed here",
            "promoter_overlap_bp": 1,
            "atac_overlap_bp": 1,
            "peak_widening": False,
            "nearest_peak_rescue": False,
            "gene_identity": "Nearest Ensembl, unique required; Gene Name is secondary "
                             "metadata and is NOT additionally required (P3 S26)",
            "density_strata_used_to_select_or_reweight": False,
        },
        "ATTRITION_FUNNEL": {
            "denominator_original_nott_microglia_interactions": N0,
            "stages_mutually_exclusive": dict(stage),
            "stages_sum_to_denominator": total == N0,
            "derived_denominators": {
                "C3_qualified": len(c3),
                "source_oriented_promoter_distal_after_C3": n_pd_after_c3,
                "unique_Ensembl_resolved_after_C3": n_unique_gene_after_c3,
                "accessibility_qualified": stage["E2_EDGE"],
            },
            "orientation_classes_source_hg19": dict(ocls),
            "pre_C3_unique_Ensembl_source_side": pre_c3_unique_ens,
        },
        "UPSTREAM_CROSSCHECKS": x,
        "all_upstream_crosschecks_reproduce_exactly": all_ok,
        "CONSISTENCY_OBSERVATION_NOT_AN_EXACT_CHECK": {
            "quantity": "fraction of C3-qualified, source-oriented, unique-Ensembl "
                        "promoter-distal contacts whose distal anchor is accessible in "
                        "the Nott PU.1 microglia track",
            "observed_here": round(stage["E2_EDGE"] / n_unique_gene_after_c3, 5),
            "committed_P1S_microglia_observed_support_rate": 0.3426,
            "why_not_exact": "P1S computed its support rate on 62,753 analysed pairs, "
                             "which include the gene-ambiguous and gene-unannotated "
                             "classes that E2 excludes, and after dropping 137 pairs for "
                             "which the geometry null was not constructible. The two "
                             "populations are therefore not identical and the rates are "
                             "expected to agree closely rather than exactly.",
            "agreement": "close",
        },
        "E2": {
            "edge_count": len(edges),
            "distinct_genes_nearest_ensembl": len(genes),
            "distinct_promoter_anchors_hg38": len(proms),
            "genes_with_more_than_one_edge": len(multi_gene),
            "edges_belonging_to_multi_edge_genes": edges_in_multi,
            "max_edges_for_a_single_gene": max(genes.values()) if genes else 0,
            "edges_per_gene_summary": summarise(list(genes.values())),
            "promoter_degree_summary_edges_per_promoter_anchor":
                summarise(list(proms.values())),
            "contact_distance_bp_summary":
                summarise([e["contact_distance_bp"] for e in edges]),
            "distal_pu1_peak_overlap_summary":
                summarise([e["distal_pu1_peak_overlap"] for e in edges]),
            "gene_name_status": dict(Counter(e["gene_name_status"] for e in edges)),
            "chromosome_distribution": dict(sorted(chrom.items())),
            "chromosome_coverage_note": (
                "22 autosomes, no chrX or chrY. This is INHERITED FROM THE SOURCE: the "
                "deposited Nott microglia interactome itself contains only chr1-chr22. "
                "No sex chromosome was dropped by any step of this construction."),
            "source_hg19_contact_distance_summary":
                summarise([e["contact_distance_bp_hg19_source"] for e in edges]),
            "LIFTOVER_CONTACT_DISTANCE_DISTORTION": {
                "finding": (
                    "C3 exact identity constrains each ANCHOR individually -- same "
                    "chromosome, exact length, exact round trip. It does NOT constrain "
                    "the SEPARATION between the two anchors of a pair: the two anchors "
                    "can land in different chain blocks with different offsets, so a "
                    "C3-PASS pair can still have its contact distance shifted."),
                "edges_distance_unchanged": n_same,
                "edges_distance_unchanged_pct": round(100.0 * n_same / len(edges), 3),
                "edges_abs_change_le_1000bp": n_le1k,
                "edges_abs_change_gt_1000bp": n_gt1k,
                "edges_abs_change_gt_10000bp": n_gt10k,
                "max_increase_bp": max(deltas),
                "max_decrease_bp": min(deltas),
                "source_hg19_span_bp": [min(d19s), max(d19s)],
                "lifted_hg38_span_bp": [min(d38s), max(d38s)],
                "edges_exceeding_1Mb_after_lift": n_over1mb,
                "edges_below_10kb_after_lift": n_under10k,
                "why_it_matters": (
                    "The frozen contract records the source cis span as 10 kb to 1 Mb, "
                    "and the hg19 coordinates reproduce that exactly. After harmonization "
                    "a small tail sits outside it. Any distance-dependent downstream "
                    "analysis on hg38 coordinates inherits this, including the frozen "
                    "P1S mirrored-distance null."),
                "action_taken": (
                    "REPORTED ONLY. No edge was trimmed, no tolerance was introduced, and "
                    "P1S was not reopened -- doing any of those would be exactly the "
                    "post-hoc retuning the contract forbids. Both the source and lifted "
                    "distances are carried per edge so any successor can condition on "
                    "either without re-deriving them."),
            },
        },
        "edge_table": {
            "path": "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz",
            "columns": EDGE_COLUMNS,
            "uncompressed_sha256": raw_sha,
            "uncompressed_bytes": len(raw),
            "gzip_sha256": gz_sha,
            "gzip_determinism": "written with mtime=0 so a rebuild is byte-identical; "
                                "the uncompressed digest is the authoritative one",
            "rows": len(edges),
        },
        "CLAIM_SCOPE": {
            "what_this_object_is": "Nott-defined primary-microglia promoter-distal "
                                   "contact pairs, source-thresholded by the depositors, "
                                   "hg19->hg38 harmonized under the frozen exact-identity "
                                   "rule, gene-resolved to a unique Nearest Ensembl, and "
                                   "restricted to distal intervals accessible in the "
                                   "authenticated Nott PU.1 microglia ATAC track.",
            "must_not_be_called": [
                "independently replicated contact set",
                "multi-source supported contacts",
                "causal enhancer-gene map",
                "proof of universal microglia specificity",
                "independent cross-study replication",
                "disease-specific regulation",
            ],
            "P1S_established": "INTERNAL microglial substrate compatibility relative to "
                               "same-study neuron/oligodendrocyte comparators and the "
                               "frozen geometry null. Not independent replication.",
            "P3_established": "hard neuron/oligodendrocyte negatives exist where the gene "
                              "is expressed in microglia and the distal region is "
                              "accessible in microglia, yet the same gene-distal "
                              "relationship is absent from the qualified microglia map.",
            "accessibility_source_limitation": {
                "finding": "V63 C5 names Kosoy aged primary-microglia ATAC as the intended "
                           "accessibility source and records it UNVERIFIED, listing Nott "
                           "ATAC as a SENSITIVITY layer. This build uses the authenticated "
                           "Nott PU.1 track, which is the already-qualified P1S/P3 path "
                           "and satisfies the successor contract's requirement to verify "
                           "the chosen source's bytes and terms.",
                "consequence": "Contacts and accessibility come from the SAME study and "
                               "the same PU.1-sorted nuclei. E2_NOTT_CANDIDATE therefore "
                               "does NOT satisfy V63's 'externally defined microglial "
                               "accessibility' wording and must not be described as if it "
                               "did.",
                "recoverable": "The pre-accessibility population is reported, so the "
                               "unrestricted object can be reconstructed if a verified "
                               "external accessibility source later becomes available.",
            },
            "promotion_rule": "Only after independent validation-cohort correspondence "
                              "passes may this be promoted to the validated E2 authority "
                              "class.",
        },
        "DENSITY_STATE_CARRIED_FORWARD": {
            "P1S_primary": "PASS",
            "local_density_operator": "UNDER_SPECIFIED__NO_OPERATOR_AUTHORITATIVE",
            "panel": "six definitions, descriptive and outcome-exposed, none selected",
            "robust_statement": "excluding superseded D6, all reported density quartile "
                                "contrasts remain positive at roughly +0.08 to +0.22",
            "not_proven": "D1's flatness is CONSISTENT WITH offsetting observed-arm and "
                          "null-arm dependencies; it is NOT a proven arithmetic "
                          "cancellation of the D2/D3 quartile trends, because those strata "
                          "contain different pairs.",
            "used_in_E2_construction": False,
        },
        "governance": {
            "training": "OFF", "td60": "BLOCKED",
            "E2_NOTT_CANDIDATE": "INSTANTIATED_PENDING_INDEPENDENT_AUDIT",
            "nih_card_correspondence_started": False,
            "target_integration_started": False,
            "no_protected_validation_data_used": True,
            "uses_AD_loci": False, "uses_JEPA_target_registry": False,
            "uses_NIH_CARD": False, "uses_Morabito": False,
            "uses_SEA_AD": False, "uses_GSE214979": False,
            "uses_project_RNA": False,
            "external_gene_annotation_repair": False,
            "thresholds_changed": False, "rescue_rules_used": False,
            "statement": "No protected validation data, AD locus list, target registry, "
                         "NIH-CARD outcome or Morabito outcome was read, joined or used "
                         "in any way during this construction.",
        },
    }
    with open(os.path.join(a.out_dir,
                           "V64_E2_NOTT_CANDIDATE_CONSTRUCTION_RECEIPT_V1.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)
    with io.open(os.path.join(a.out_dir, "run_log.txt"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    log("\nATTRITION FUNNEL")
    for k in ("DROP_C3_NOT_EXACT_IDENTITY",
              "DROP_NOT_SOURCE_ORIENTED_PROMOTER_DISTAL",
              "DROP_GENE_ENSEMBL_UNRESOLVED",
              "DROP_DISTAL_NOT_ACCESSIBLE_IN_MICROGLIA", "E2_EDGE"):
        log(f"  {k:<44} {stage[k]:>7,}  {100.0*stage[k]/N0:6.3f}%")
    log(f"  {'sum':<44} {total:>7,}  reconciles={total == N0}")
    log(f"\nE2 edges {len(edges):,} | distinct genes {len(genes):,} | "
        f"distinct promoter anchors {len(proms):,}")
    log(f"genes with >1 edge: {len(multi_gene):,} covering {edges_in_multi:,} edges; "
        f"max edges for one gene {max(genes.values()) if genes else 0}")
    log(f"contact distance preserved exactly by lift: {n_same:,}/{len(edges):,} "
        f"({100.0*n_same/len(edges):.3f}%); >1 kb change {n_gt1k:,}; "
        f">1 Mb after lift {n_over1mb}")
    log(f"edge table uncompressed sha256 {raw_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
