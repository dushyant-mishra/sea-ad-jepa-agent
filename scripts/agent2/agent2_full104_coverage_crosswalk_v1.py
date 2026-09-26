#!/usr/bin/env python
"""AGENT 2 - FULL104 full gene-universe coverage crosswalk.

ONE ROW PER CANONICAL FULL104 MOLECULAR ADDRESS (41,238 rows).

Answers, per address and by individual resolution (never by comparing headline
totals), whether the address is:
  * present and structurally measured in Morabito GSE174367 snRNA;
  * absent / unresolved in Morabito snRNA;
  * associated with an annotation-supported promoter or candidate distal
    regulatory region (Ensembl 116 TSS geometry);
  * associated with an experimentally accessible ATAC region (observed
    accessibility measured from the GSE174367 peak x cell matrix);
  * represented in historical Stage75F evidence (HYPOTHESIS set, not a
    validated network);
  * eligible for an eventual matched RNA-ATAC comparison.

FOUR OBSERVATION STATES, NEVER CONFLATED
  UNMEASURED              - no feature for this address in the assay at all.
  MEASURED_BUT_UNDETECTED - a feature exists, zero counts observed.
  AMBIGUOUSLY_MAPPED      - identifier resolves to more than one target.
  MAPPED_WITHOUT_REGULATORY_EVIDENCE - RNA-resolved but no regulatory evidence.

A missing feature is NEVER turned into zero expression. UNMEASURED and
MEASURED_BUT_UNDETECTED are distinct columns and distinct states throughout.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF

Read-only with respect to every input. Writes only to --out-dir.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

import h5py
import numpy as np

# ---------------------------------------------------------------------------
# Frozen authorities and parameters. Declared before any measurement.
# ---------------------------------------------------------------------------
CANONICAL_REGISTRY_SHA256 = (
    "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
)
FULL104_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
FULL104_BLOCK_MANIFEST_BYTES = 2372002
# Decoy manifests of the same name that must never be used.
DECOY_MANIFEST_SHA256_PREFIX = "e482d9da21232bde"
DECOY_MANIFEST_BYTES = 2380918

ANNOTATION_RELEASE = "Ensembl 116 (GRCh38.p14)"
PROMOTER_BP = 2000       # Stage75C frozen parameter, reused unchanged
DISTAL_BP = 100000       # Stage75C frozen parameter, reused unchanged

CSV_FIELD_LIMIT = 10 * 1024 * 1024

# Observation-state vocabulary.
ST_UNMEASURED = "UNMEASURED"
ST_DETECTED = "MEASURED_DETECTED"
ST_UNDETECTED = "MEASURED_BUT_UNDETECTED"
ST_AMBIGUOUS = "AMBIGUOUSLY_MAPPED"
ST_NO_REG = "MAPPED_WITHOUT_REGULATORY_EVIDENCE"
ST_UNKNOWN = "UNKNOWN"


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def file_receipt(path):
    return {
        "path": os.path.abspath(path).replace("\\", "/"),
        "bytes": os.path.getsize(path),
        "sha256": sha256_of(path),
    }


def opener(path):
    return gzip.open(path, "rt", encoding="utf-8", newline="") \
        if path.endswith(".gz") else open(path, "r", encoding="utf-8", newline="")


# ---------------------------------------------------------------------------
# Identifier normalisation. Version handling is explicit and recorded.
# ---------------------------------------------------------------------------
ENSG_RE = re.compile(r"^(ENSG\d+)(?:\.(\d+))?$")


def split_ensembl_version(raw):
    """Return (unversioned_id, version_or_None, had_version).

    Documented version handling: an Ensembl gene stable ID carries an optional
    '.N' suffix. The stable ID (without .N) is the join key; the suffix is
    retained separately so a version disagreement is reportable rather than
    silently absorbed.
    """
    m = ENSG_RE.match(raw.strip())
    if not m:
        return raw.strip(), None, False
    return m.group(1), m.group(2), m.group(2) is not None


def norm_symbol(s):
    return (s or "").strip().upper()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_registry(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


def load_ensembl_gtf_genes(path):
    """Gene-level records from the frozen Ensembl 116 GTF.

    Returns dict unversioned_gene_id -> record. TSS is the strand-aware gene
    start; coordinates are converted to 0-based half-open like Stage75C.
    """
    gid_re = re.compile(r'gene_id "([^"]+)"')
    gname_re = re.compile(r'gene_name "([^"]+)"')
    gver_re = re.compile(r'gene_version "([^"]+)"')
    gbt_re = re.compile(r'gene_biotype "([^"]+)"')
    out = {}
    sym_index = collections.defaultdict(list)
    n_gene_lines = 0
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            n_gene_lines += 1
            attrs = p[8]
            m = gid_re.search(attrs)
            if not m:
                continue
            gid_raw = m.group(1)
            gid, inline_ver, _ = split_ensembl_version(gid_raw)
            mv = gver_re.search(attrs)
            version = mv.group(1) if mv else inline_ver
            mn = gname_re.search(attrs)
            mb = gbt_re.search(attrs)
            chrom, start, end, strand = p[0], int(p[3]) - 1, int(p[4]), p[6]
            tss = start if strand == "+" else end
            rec = {
                "gene_id": gid,
                "version": version,
                "symbol": mn.group(1) if mn else "",
                "biotype": mb.group(1) if mb else "",
                "chrom": chrom,
                "start": start,
                "end": end,
                "strand": strand,
                "tss": tss,
            }
            out[gid] = rec
            if rec["symbol"]:
                sym_index[norm_symbol(rec["symbol"])].append(gid)
    return out, dict(sym_index), n_gene_lines


def load_hgnc(complete_path, withdrawn_path):
    """HGNC symbol authority.

    Returns:
      hgnc_by_id       : 'HGNC:1234' -> record
      current_symbol   : SYMBOL -> [hgnc_id, ...]
      prev_or_alias    : SYMBOL -> [hgnc_id, ...]   (deprecated / alias routes)
      withdrawn_symbols: SYMBOL -> [raw withdrawn row ...]
      ens_by_hgnc      : 'HGNC:1234' -> ensembl_gene_id
    """
    hgnc_by_id = {}
    current_symbol = collections.defaultdict(list)
    prev_or_alias = collections.defaultdict(list)
    alias_by_hgnc = collections.defaultdict(list)
    ens_by_hgnc = {}
    with open(complete_path, "r", encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for row in rd:
            hid = (row.get("hgnc_id") or "").strip()
            if not hid:
                continue
            sym = norm_symbol(row.get("symbol"))
            ens = (row.get("ensembl_gene_id") or "").strip()
            hgnc_by_id[hid] = {
                "hgnc_id": hid,
                "symbol": row.get("symbol", ""),
                "ensembl_gene_id": ens,
                "status": row.get("status", ""),
                "locus_group": row.get("locus_group", ""),
            }
            if sym:
                current_symbol[sym].append(hid)
            if ens:
                ens_by_hgnc[hid] = ens
            for field in ("prev_symbol", "alias_symbol"):
                raw = row.get(field) or ""
                for tok in re.split(r"[|,]", raw):
                    t = norm_symbol(tok)
                    if t:
                        prev_or_alias[t].append(hid)
                        alias_by_hgnc[hid].append(t)
    withdrawn_symbols = collections.defaultdict(list)
    if withdrawn_path and os.path.exists(withdrawn_path):
        with open(withdrawn_path, "r", encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh, delimiter="\t")
            for row in rd:
                sym = norm_symbol(row.get("WITHDRAWN_SYMBOL")
                                  or row.get("withdrawn_symbol"))
                if sym:
                    withdrawn_symbols[sym].append(row)
    return (hgnc_by_id, dict(current_symbol), dict(prev_or_alias),
            dict(withdrawn_symbols), ens_by_hgnc, dict(alias_by_hgnc))


def load_h5_features(path):
    with h5py.File(path, "r") as f:
        ids = [x.decode() for x in f["matrix/features/id"][:]]
        names = [x.decode() for x in f["matrix/features/name"][:]]
        genome = [x.decode() for x in f["matrix/features/genome"][:]]
        shape = [int(x) for x in f["matrix/shape"][:]]
    return ids, names, genome, shape


def nnz_per_feature(path, subset_cols=None, chunk_cells=4096):
    """Per-feature count of cells with a nonzero entry.

    The 10x h5 is CSC over cells: indptr indexes cells, indices are feature
    rows. Streams cell-blocks so the 177M/210M nonzero arrays are never held
    whole. subset_cols, if given, is a boolean mask over cells.
    """
    with h5py.File(path, "r") as f:
        indptr = f["matrix/indptr"][:]
        n_feat = int(f["matrix/shape"][0])
        n_cells = int(f["matrix/shape"][1])
        idx_ds = f["matrix/indices"]
        total = np.zeros(n_feat, dtype=np.int64)
        sub = np.zeros(n_feat, dtype=np.int64) if subset_cols is not None else None
        n_sub_cells = 0
        for a in range(0, n_cells, chunk_cells):
            b = min(a + chunk_cells, n_cells)
            lo, hi = int(indptr[a]), int(indptr[b])
            if hi <= lo:
                continue
            block = idx_ds[lo:hi]
            total += np.bincount(block, minlength=n_feat)
            if subset_cols is not None:
                sel = np.nonzero(subset_cols[a:b])[0]
                if sel.size:
                    n_sub_cells += int(sel.size)
                    starts = indptr[a:b + 1]
                    parts = [block[int(starts[c]) - lo:int(starts[c + 1]) - lo]
                             for c in sel]
                    if parts:
                        sub += np.bincount(np.concatenate(parts),
                                           minlength=n_feat)
    return total, sub, n_sub_cells, n_feat, n_cells


def load_cell_meta_types(path, barcode_field="Barcode", type_field="Cell.Type"):
    out = {}
    with opener(path) as fh:
        rd = csv.DictReader(fh)
        if barcode_field not in rd.fieldnames:
            barcode_field = rd.fieldnames[0]
        tf = type_field if type_field in rd.fieldnames else None
        for row in rd:
            out[row[barcode_field]] = row.get(tf, "") if tf else ""
    return out


# ---------------------------------------------------------------------------
# Interval overlap: peaks against Ensembl 116 TSS geometry.
# ---------------------------------------------------------------------------
def build_peak_index(peak_ids):
    """Parse 'chr1:190849-191920' peak ids into per-chromosome sorted arrays."""
    per = collections.defaultdict(list)
    unparsed = []
    rx = re.compile(r"^(.+):(\d+)-(\d+)$")
    for i, pid in enumerate(peak_ids):
        m = rx.match(pid)
        if not m:
            unparsed.append(pid)
            continue
        per[m.group(1)].append((int(m.group(2)), int(m.group(3)), i))
    packed = {}
    for c, v in per.items():
        v.sort()
        packed[c] = {
            "start": np.array([t[0] for t in v], dtype=np.int64),
            "end": np.array([t[1] for t in v], dtype=np.int64),
            "idx": np.array([t[2] for t in v], dtype=np.int64),
            "maxend": np.maximum.accumulate(np.array([t[1] for t in v],
                                                     dtype=np.int64)),
        }
    return packed, unparsed


def peaks_in_window(packed, chrom, lo, hi):
    """Indices of peaks overlapping [lo, hi). Half-open, 0-based."""
    c = packed.get(chrom)
    if c is None:
        return np.empty(0, dtype=np.int64)
    # candidates: peaks whose start < hi
    j = int(np.searchsorted(c["start"], hi, side="left"))
    if j == 0:
        return np.empty(0, dtype=np.int64)
    # among those, keep peaks whose end > lo
    i = int(np.searchsorted(c["maxend"], lo, side="right"))
    if i >= j:
        return np.empty(0, dtype=np.int64)
    sl_end = c["end"][i:j]
    keep = np.nonzero(sl_end > lo)[0]
    if keep.size == 0:
        return np.empty(0, dtype=np.int64)
    return c["idx"][i:j][keep]


def ensembl_chrom_to_ucsc(chrom):
    if chrom == "MT":
        return "chrM"
    if re.match(r"^(\d+|X|Y)$", chrom):
        return "chr" + chrom
    return None  # scaffolds / patches: no UCSC-style equivalent in this peak set


# ---------------------------------------------------------------------------
# Stage75F historical evidence (HYPOTHESIS set, not a validated network)
# ---------------------------------------------------------------------------
def load_stage75f(primary_path, secondary_path):
    regulators, pairs = [], []
    for path, tier in ((primary_path, "primary"), (secondary_path, "secondary")):
        if not path or not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rd = csv.reader(fh)
            hdr = next(rd)
            ti = hdr.index("tf")
            gi = hdr.index("target_gene")
            for row in rd:
                if len(row) <= max(ti, gi):
                    continue
                pairs.append((row[ti].strip(), row[gi].strip(), tier))
                regulators.append(row[ti].strip())
    return sorted(set(regulators)), pairs


def load_stage75f_regulator_roster(primary_motif, secondary_motif):
    """All regulators TESTED, including any with no supported target."""
    tfs = []
    for path in (primary_motif, secondary_motif):
        if not path or not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rd = csv.reader(fh)
            hdr = next(rd)
            ti = hdr.index("tf")
            for row in rd:
                if len(row) > ti and row[ti].strip():
                    tfs.append(row[ti].strip())
    return sorted(set(tfs))


def load_query_panel(path, gene_field="gene"):
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        gf = gene_field if gene_field in rd.fieldnames else rd.fieldnames[0]
        for row in rd:
            g = (row.get(gf) or "").strip()
            if g:
                out.append(g)
    return out


# ---------------------------------------------------------------------------
# Resolution of one canonical address against the Morabito RNA feature space
# ---------------------------------------------------------------------------
def resolve_rna(addr_id, addr_symbol, mor_by_gid, mor_by_symbol,
                hgnc_by_id, current_symbol, prev_or_alias, withdrawn_symbols,
                ens_by_hgnc, alias_by_hgnc):
    """Return (feature_idx_list, route, notes).

    Routes are tried in a fixed precedence and the winning route is recorded.
    A route that returns more than one feature is NOT silently deduplicated;
    every feature is returned and the caller marks AMBIGUOUSLY_MAPPED.
    """
    notes = []
    # Route 1: Ensembl stable ID (version-insensitive join, version recorded).
    gid, _ver, _had = split_ensembl_version(addr_id)
    if gid.startswith("ENSG"):
        hits = mor_by_gid.get(gid)
        if hits:
            return list(hits), "ensembl_stable_id", notes
    # Route 2: HGNC-anchored address -> Ensembl ID via HGNC complete set.
    if addr_id.startswith("HGNC:"):
        ens = ens_by_hgnc.get(addr_id)
        if ens:
            notes.append("hgnc_to_ensembl=%s" % ens)
            hits = mor_by_gid.get(ens)
            if hits:
                return list(hits), "hgnc_id_to_ensembl", notes
    sym = norm_symbol(addr_symbol)
    if not sym:
        return [], "none", notes
    # Route 3: current symbol.
    hits = mor_by_symbol.get(sym)
    if hits:
        return list(hits), "current_symbol", notes
    # Route 4: deprecated / previous / alias symbol of the same HGNC record.
    hids = list(current_symbol.get(sym, []))
    # The address symbol may itself be a deprecated/alias spelling: follow it
    # to the HGNC record that owns it, then out to every spelling that record
    # has ever carried.
    hids += [h for h in prev_or_alias.get(sym, []) if h not in hids]
    alt = []
    for hid in hids:
        rec = hgnc_by_id.get(hid, {})
        alt.extend(alias_by_hgnc.get(hid, []))
        if rec.get("symbol"):
            alt.append(norm_symbol(rec["symbol"]))
    seen_feat = []
    for a in sorted(set(alt)):
        for fi in mor_by_symbol.get(a, []):
            if fi not in seen_feat:
                seen_feat.append(fi)
    if seen_feat:
        notes.append("deprecated_or_alias_symbol_route")
        return seen_feat, "deprecated_alias_symbol", notes
    if sym in withdrawn_symbols:
        notes.append("symbol_withdrawn_in_hgnc")
    return [], "none", notes

CROSSWALK_FIELDS = [
    "molecular_address_index", "molecular_address_id", "identity_class",
    "symbol", "biotype",
    "ens116_resolved", "ens116_gene_id", "ens116_version", "ens116_symbol",
    "ens116_biotype", "ens116_chrom", "ens116_tss", "ens116_strand",
    "rna_state", "rna_map_route", "rna_n_features_mapped",
    "rna_feature_ids", "rna_source_version", "rna_version_matches_ens116",
    "rna_nnz_cells_all",
    "rna_microglia_state", "rna_nnz_cells_microglia",
    "promoter_window", "n_peaks_promoter_window", "n_peaks_distal_window",
    "annotation_regulatory_state",
    "n_peaks_promoter_accessible", "n_peaks_distal_accessible",
    "atac_accessibility_state",
    "n_peaks_promoter_accessible_microglia",
    "n_peaks_distal_accessible_microglia",
    "atac_microglia_accessibility_state",
    "stage75c_n_peaks_nearest", "stage75c_peak_gene_classes",
    "stage75f_role", "stage75f_tf_partners", "stage75f_n_evidence_rows",
    "query_panel_member", "query_panel_groups",
    "regulatory_evidence_state",
    "matched_rna_atac_state",
]


def classify_annotation_regulatory(resolved, n_prom, n_dist):
    """Annotation-supported regulatory geometry, from Ensembl 116 TSS."""
    if not resolved:
        return ST_UNKNOWN
    if n_prom > 0:
        return "PROMOTER_SUPPORTED"
    if n_dist > 0:
        return "DISTAL_CANDIDATE_ONLY"
    return "NO_ANNOTATED_REGION_IN_ASSAYED_PEAK_SET"


def classify_atac_accessibility(resolved, n_prom_acc, n_dist_acc,
                                n_prom, n_dist):
    """Experimentally accessible ATAC region, measured from the peak matrix."""
    if not resolved:
        return ST_UNKNOWN
    if n_prom_acc > 0:
        return "ACCESSIBLE_PROMOTER"
    if n_dist_acc > 0:
        return "ACCESSIBLE_DISTAL_ONLY"
    if n_prom > 0 or n_dist > 0:
        # A peak was called in the window but observed in zero nuclei of this
        # population. Assayed and not accessible here: NOT the same as absent.
        return "REGION_PRESENT_BUT_NOT_ACCESSIBLE"
    return "NO_ASSAYED_REGION"


def resolve_default_paths(repo, args):
    def d(p, default):
        return p if p else os.path.join(repo, default)
    return {
        "registry": d(args.registry,
                      "results/v4/stage81a2r_foundation_molecular_address_"
                      "registry_candidate.csv"),
        "block_manifest": d(args.block_manifest,
                            "outputs/full104_v014_20260826/"
                            "03_phase2_state_derivation_v1/expression_level4/"
                            "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
        "gtf": d(args.gtf, "data/external/v4/gene_identity_authority/"
                           "ensembl_116/Homo_sapiens.GRCh38.116.gtf.gz"),
        "hgnc": d(args.hgnc, "data/external/v4/gene_identity_authority/"
                             "hgnc_2026-08/hgnc_complete_set_2026-08-07.txt"),
        "hgnc_withdrawn": d(args.hgnc_withdrawn,
                            "data/external/v4/gene_identity_authority/"
                            "hgnc_2026-08/withdrawn_2026-08-04.txt"),
        "rna_h5": d(args.rna_h5, "data/external/gse174367/GSE174367_snRNA-seq_"
                                 "filtered_feature_bc_matrix.h5"),
        "atac_h5": d(args.atac_h5, "data/external/gse174367/GSE174367_snATAC-"
                                   "seq_filtered_peak_bc_matrix.h5"),
        "rna_meta": d(args.rna_meta, "data/external/gse174367/GSE174367_snRNA-"
                                     "seq_cell_meta.csv.gz"),
        "atac_meta": d(args.atac_meta, "data/external/gse174367/GSE174367_"
                                       "snATAC-seq_cell_meta.csv.gz"),
        "stage75c": d(args.stage75c,
                      "results/tables/stage75c_peak_to_gene_preflight_v1.csv"),
        "s75f_primary": d(args.stage75f_primary,
                          "results/tables/stage75f_primary_tf_target_gene_"
                          "evidence_summary_v1.csv"),
        "s75f_secondary": d(args.stage75f_secondary,
                            "results/tables/stage75f_secondary_tf_target_gene_"
                            "evidence_summary_v1.csv"),
        "s75f_primary_motif": d(args.stage75f_primary_motif,
                                "results/tables/stage75f_primary_tf_motif_"
                                "support_summary_v1.csv"),
        "s75f_secondary_motif": d(args.stage75f_secondary_motif,
                                  "results/tables/stage75f_secondary_tf_motif_"
                                  "support_summary_v1.csv"),
        "query_panel": d(args.query_panel,
                         "results/tables/discovery_targeted_manifold_audit_"
                         "gene_list_v1.csv"),
    }


def authenticate(paths, prov, enforce=True):
    """Fail-closed authentication of the two anchor inputs."""
    reg = file_receipt(paths["registry"])
    prov["inputs"]["canonical_registry"] = reg
    if enforce and reg["sha256"] != CANONICAL_REGISTRY_SHA256:
        raise SystemExit(
            "FAIL-CLOSED: canonical registry digest mismatch.\n"
            "  expected %s\n  observed %s\n  path %s"
            % (CANONICAL_REGISTRY_SHA256, reg["sha256"], reg["path"]))
    prov["authentication"]["canonical_registry_sha256"] = reg["sha256"]
    prov["authentication"]["canonical_registry_verified"] = (
        reg["sha256"] == CANONICAL_REGISTRY_SHA256)

    man = file_receipt(paths["block_manifest"])
    prov["inputs"]["full104_block_manifest"] = man
    if man["bytes"] == DECOY_MANIFEST_BYTES or \
            man["sha256"].startswith(DECOY_MANIFEST_SHA256_PREFIX):
        raise SystemExit("FAIL-CLOSED: decoy FULL104 block manifest supplied "
                         "(%d bytes, sha256 %s)." % (man["bytes"],
                                                     man["sha256"]))
    if enforce and man["sha256"] != FULL104_BLOCK_MANIFEST_SHA256:
        raise SystemExit(
            "FAIL-CLOSED: FULL104 block manifest digest mismatch.\n"
            "  expected %s\n  observed %s\n  path %s"
            % (FULL104_BLOCK_MANIFEST_SHA256, man["sha256"], man["path"]))
    prov["authentication"]["full104_block_manifest_sha256"] = man["sha256"]
    prov["authentication"]["full104_block_manifest_verified"] = (
        man["sha256"] == FULL104_BLOCK_MANIFEST_SHA256)
    return prov


def build(paths, out_dir, microglia_label="MG", skip_matrix_scan=False,
          enforce_digests=True):
    os.makedirs(out_dir, exist_ok=True)
    prov = {
        "stage": "agent2_full104_full_gene_universe_coverage_crosswalk_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "annotation_release": ANNOTATION_RELEASE,
        "promoter_bp": PROMOTER_BP,
        "distal_bp": DISTAL_BP,
        "symbol_collision_policy": (
            "Symbol routes are used ONLY when the Ensembl stable-ID route "
            "fails. A symbol resolving to more than one assay feature is "
            "recorded as AMBIGUOUSLY_MAPPED with every candidate listed; it is "
            "never deduplicated to a single arbitrary winner and never "
            "silently dropped."),
        "missing_is_not_zero": (
            "UNMEASURED (no feature in the assay) and MEASURED_BUT_UNDETECTED "
            "(feature present, zero observed) are separate states in separate "
            "columns. No missing feature is ever assigned a zero count."),
        "governance": ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                       "PROTECTED_FULL104_OUTCOMES=UNOPENED | "
                       "D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | "
                       "THERAPEUTIC_RANKING=OFF"),
        "inputs": {}, "authentication": {}, "notes": [], "counts": {},
    }
    authenticate(paths, prov, enforce=enforce_digests)
    for key in ("gtf", "hgnc", "hgnc_withdrawn", "rna_h5", "atac_h5",
                "rna_meta", "atac_meta", "stage75c", "s75f_primary",
                "s75f_secondary", "s75f_primary_motif", "s75f_secondary_motif",
                "query_panel"):
        p = paths.get(key)
        if p and os.path.exists(p):
            prov["inputs"][key] = file_receipt(p)
        else:
            prov["inputs"][key] = {"path": p, "status": "MISSING"}
            prov["notes"].append("INPUT_MISSING:%s" % key)

    # ------------------------------------------------------------------
    # 1. Canonical registry, with closure over the identity space.
    # ------------------------------------------------------------------
    registry = load_registry(paths["registry"])
    n_addr = len(registry)
    idx_seen = collections.Counter()
    id_seen = collections.Counter()
    for r in registry:
        idx_seen[int(r["molecular_address_index"])] += 1
        id_seen[r["molecular_address_id"]] += 1
    dup_idx = sorted(i for i, c in idx_seen.items() if c > 1)
    dup_ids = sorted(i for i, c in id_seen.items() if c > 1)
    missing_idx = sorted(set(range(n_addr)) - set(idx_seen))
    if dup_idx or dup_ids or missing_idx:
        raise SystemExit(
            "FAIL-CLOSED: registry identity space is not a closed bijection. "
            "duplicate_index=%d duplicate_id=%d missing_index=%d"
            % (len(dup_idx), len(dup_ids), len(missing_idx)))
    prov["counts"]["n_canonical_addresses"] = n_addr
    prov["counts"]["registry_identity_closure_verified"] = True

    # ------------------------------------------------------------------
    # 2. Frozen annotation authorities.
    # ------------------------------------------------------------------
    ens, ens_sym_index, n_gtf_gene_lines = load_ensembl_gtf_genes(paths["gtf"])
    prov["counts"]["ensembl116_gene_records"] = len(ens)
    prov["counts"]["ensembl116_gene_lines_parsed"] = n_gtf_gene_lines
    (hgnc_by_id, current_symbol, prev_or_alias, withdrawn_symbols,
     ens_by_hgnc, alias_by_hgnc) = load_hgnc(paths["hgnc"],
                                             paths["hgnc_withdrawn"])
    prov["counts"]["hgnc_records"] = len(hgnc_by_id)
    prov["counts"]["hgnc_withdrawn_symbols"] = len(withdrawn_symbols)

    # ------------------------------------------------------------------
    # 3. Morabito snRNA feature space. Every feature individually resolved.
    # ------------------------------------------------------------------
    rna_ids, rna_names, rna_genome, rna_shape = load_h5_features(
        paths["rna_h5"])
    prov["counts"]["morabito_rna_n_features"] = len(rna_ids)
    prov["counts"]["morabito_rna_n_cells"] = int(rna_shape[1])
    prov["notes"].append(
        "GSE174367 snRNA matrix is %d features x %d CELLS. The figure 61,770 "
        "is a NUCLEUS count, not a feature count; it is never comparable to "
        "the 41,238 canonical addresses."
        % (int(rna_shape[0]), int(rna_shape[1])))
    prov["counts"]["morabito_rna_reference_genome"] = sorted(set(rna_genome))

    mor_by_gid = collections.defaultdict(list)
    mor_by_symbol = collections.defaultdict(list)
    rna_version_of = {}
    n_versioned = 0
    for i, fid in enumerate(rna_ids):
        gid, ver, had = split_ensembl_version(fid)
        if had:
            n_versioned += 1
        mor_by_gid[gid].append(i)
        rna_version_of[gid] = ver
        mor_by_symbol[norm_symbol(rna_names[i])].append(i)
    prov["counts"]["morabito_rna_features_with_version_suffix"] = n_versioned
    prov["counts"]["morabito_rna_unique_stable_ids"] = len(mor_by_gid)
    prov["counts"]["morabito_rna_unique_symbols"] = len(mor_by_symbol)

    # Collision report: identifiers that bind more than one assay feature.
    collisions = []
    for gid, feats in mor_by_gid.items():
        if len(feats) > 1:
            collisions.append({
                "collision_type": "ensembl_stable_id_multi_feature",
                "key": gid,
                "n_features": len(feats),
                "feature_ids": "|".join(rna_ids[f] for f in feats),
                "feature_symbols": "|".join(rna_names[f] for f in feats),
            })
    for sym, feats in mor_by_symbol.items():
        if len(feats) > 1:
            collisions.append({
                "collision_type": "gene_symbol_multi_feature",
                "key": sym,
                "n_features": len(feats),
                "feature_ids": "|".join(rna_ids[f] for f in feats),
                "feature_symbols": "|".join(rna_names[f] for f in feats),
            })
    prov["counts"]["collisions_ensembl_id"] = sum(
        1 for c in collisions if c["collision_type"].startswith("ensembl"))
    prov["counts"]["collisions_symbol"] = sum(
        1 for c in collisions if c["collision_type"].startswith("gene_symbol"))

    # ------------------------------------------------------------------
    # 4. Observed RNA detection. Missing is never zero.
    # ------------------------------------------------------------------
    n_rna_cells = int(rna_shape[1])
    mg_mask = None
    n_mg = 0
    n_rna_barcodes_without_meta = ST_UNKNOWN
    if os.path.exists(paths["rna_meta"]):
        types = load_cell_meta_types(paths["rna_meta"])
        with h5py.File(paths["rna_h5"], "r") as f:
            barcodes = [x.decode() for x in f["matrix/barcodes"][:]]
        mg_mask = np.zeros(n_rna_cells, dtype=bool)
        n_missing_meta = 0
        for i, bc in enumerate(barcodes):
            t = types.get(bc)
            if t is None:
                n_missing_meta += 1
            elif t == microglia_label:
                mg_mask[i] = True
        n_mg = int(mg_mask.sum())
        n_rna_barcodes_without_meta = n_missing_meta
        prov["notes"].append(
            "%d of %d snRNA barcodes carry no cell-type metadata row; they are "
            "held as UNKNOWN cell type and are NOT counted as non-microglia."
            % (n_missing_meta, n_rna_cells))
    prov["counts"]["morabito_rna_microglia_cells"] = n_mg
    prov["counts"]["morabito_rna_barcodes_without_metadata"] = \
        n_rna_barcodes_without_meta

    if skip_matrix_scan:
        rna_nnz_all = np.full(len(rna_ids), -1, dtype=np.int64)
        rna_nnz_mg = np.full(len(rna_ids), -1, dtype=np.int64)
        prov["notes"].append("MATRIX_SCAN_SKIPPED: detection states are "
                             "UNKNOWN in this run.")
    else:
        rna_nnz_all, rna_nnz_mg, n_mg_used, _, _ = nnz_per_feature(
            paths["rna_h5"], subset_cols=mg_mask)
        if rna_nnz_mg is None:
            rna_nnz_mg = np.full(len(rna_ids), -1, dtype=np.int64)
        prov["counts"]["morabito_rna_microglia_cells_scanned"] = n_mg_used
        prov["counts"]["morabito_rna_features_detected_any_cell"] = int(
            (rna_nnz_all > 0).sum())
        prov["counts"]["morabito_rna_features_zero_in_all_cells"] = int(
            (rna_nnz_all == 0).sum())
        prov["counts"]["morabito_rna_features_detected_in_microglia"] = int(
            (rna_nnz_mg > 0).sum())

    # ------------------------------------------------------------------
    # 5. ATAC peak universe and observed accessibility.
    # ------------------------------------------------------------------
    atac_ids, _, _, atac_shape = load_h5_features(paths["atac_h5"])
    prov["counts"]["morabito_atac_n_peaks"] = len(atac_ids)
    prov["counts"]["morabito_atac_n_cells"] = int(atac_shape[1])
    peak_index, unparsed_peaks = build_peak_index(atac_ids)
    prov["counts"]["morabito_atac_unparseable_peak_ids"] = len(unparsed_peaks)

    atac_mg_mask = None
    n_atac_mg = 0
    if os.path.exists(paths["atac_meta"]):
        atypes = load_cell_meta_types(paths["atac_meta"])
        with h5py.File(paths["atac_h5"], "r") as f:
            abars = [x.decode() for x in f["matrix/barcodes"][:]]
        atac_mg_mask = np.zeros(int(atac_shape[1]), dtype=bool)
        for i, bc in enumerate(abars):
            if atypes.get(bc) == microglia_label:
                atac_mg_mask[i] = True
        n_atac_mg = int(atac_mg_mask.sum())
    prov["counts"]["morabito_atac_microglia_cells"] = n_atac_mg

    if skip_matrix_scan:
        atac_nnz = np.full(len(atac_ids), -1, dtype=np.int64)
        atac_nnz_mg = np.full(len(atac_ids), -1, dtype=np.int64)
    else:
        atac_nnz, atac_nnz_mg, n_amg_used, _, _ = nnz_per_feature(
            paths["atac_h5"], subset_cols=atac_mg_mask)
        if atac_nnz_mg is None:
            atac_nnz_mg = np.full(len(atac_ids), -1, dtype=np.int64)
        prov["counts"]["morabito_atac_peaks_accessible_any_cell"] = int(
            (atac_nnz > 0).sum())
        prov["counts"]["morabito_atac_peaks_zero_in_all_cells"] = int(
            (atac_nnz == 0).sum())
        prov["counts"]["morabito_atac_peaks_accessible_in_microglia"] = int(
            (atac_nnz_mg > 0).sum())

    # ------------------------------------------------------------------
    # 6. Stage75C nearest-gene attribution (lane-d owns its authentication).
    # ------------------------------------------------------------------
    s75c_by_gene = collections.defaultdict(list)
    if os.path.exists(paths["stage75c"]):
        with open(paths["stage75c"], newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                gid_raw = (row.get("nearest_gene_id") or "").strip()
                if not gid_raw:
                    continue
                gid, _v, _h = split_ensembl_version(gid_raw)
                s75c_by_gene[gid].append(row.get("peak_gene_class", ""))
    prov["counts"]["stage75c_genes_with_nearest_peak"] = len(s75c_by_gene)
    prov["notes"].append(
        "Stage75C assigns each peak to exactly ONE nearest gene, so absence "
        "from that table is NOT evidence of no nearby peak. It is carried as a "
        "cross-check column only; the promoter/distal states in this crosswalk "
        "come from direct interval overlap against Ensembl 116 TSS geometry.")

    # ------------------------------------------------------------------
    # 7. Stage75F historical hypothesis evidence.
    # ------------------------------------------------------------------
    s75f_regs_with_targets, s75f_pairs = load_stage75f(
        paths["s75f_primary"], paths["s75f_secondary"])
    s75f_roster = load_stage75f_regulator_roster(
        paths["s75f_primary_motif"], paths["s75f_secondary_motif"])
    prov["counts"]["stage75f_regulators_tested"] = len(s75f_roster)
    prov["counts"]["stage75f_regulators_with_supported_targets"] = len(
        s75f_regs_with_targets)
    prov["counts"]["stage75f_tf_target_rows"] = len(s75f_pairs)
    prov["notes"].append(
        "Stage75F is a HYPOTHESIS set (motif-enrichment and coactivity "
        "evidence), not a validated regulatory network. No causal or "
        "therapeutic claim is carried by these columns.")
    s75f_targets = collections.defaultdict(list)
    for tf, tgt, _tier in s75f_pairs:
        s75f_targets[norm_symbol(tgt)].append(tf)
    s75f_reg_syms = {norm_symbol(t) for t in s75f_roster}

    # ------------------------------------------------------------------
    # 8. Query panel.
    # ------------------------------------------------------------------
    panel_genes = load_query_panel(paths["query_panel"])
    panel_groups = {}
    if os.path.exists(paths["query_panel"]):
        with open(paths["query_panel"], newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                g = norm_symbol(row.get("gene"))
                if g:
                    panel_groups[g] = row.get("audit_groups", "")
    panel_set = {norm_symbol(g) for g in panel_genes}
    prov["counts"]["query_panel_genes_declared"] = len(panel_genes)
    prov["counts"]["query_panel_unique_symbols"] = len(panel_set)

    # ------------------------------------------------------------------
    # 9. One row per canonical address.
    # ------------------------------------------------------------------
    out_csv = os.path.join(out_dir,
                           "agent2_full104_feature_crosswalk_v1.csv")
    written = 0
    written_idx = collections.Counter()
    tally = collections.Counter()
    state_by = {k: collections.Counter() for k in (
        "rna_state", "rna_microglia_state", "annotation_regulatory_state",
        "atac_accessibility_state", "atac_microglia_accessibility_state",
        "regulatory_evidence_state", "matched_rna_atac_state",
        "rna_map_route", "stage75f_role")}
    ambiguous_rows = []
    panel_hits = collections.Counter()
    tf_rows = []

    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CROSSWALK_FIELDS)
        w.writeheader()
        for r in registry:
            aidx = int(r["molecular_address_index"])
            aid = r["molecular_address_id"]
            asym = r.get("symbol", "")
            row = {k: "" for k in CROSSWALK_FIELDS}
            row["molecular_address_index"] = aidx
            row["molecular_address_id"] = aid
            row["identity_class"] = r.get("identity_class", "")
            row["symbol"] = asym
            row["biotype"] = r.get("biotype", "")

            # --- frozen annotation resolution ---
            gid, _v, _h = split_ensembl_version(aid)
            erec = ens.get(gid)
            if erec is None and aid.startswith("HGNC:"):
                alt = ens_by_hgnc.get(aid)
                if alt:
                    erec = ens.get(alt)
            if erec is None and asym:
                cand = ens_sym_index.get(norm_symbol(asym), [])
                if len(cand) == 1:
                    erec = ens.get(cand[0])
            row["ens116_resolved"] = bool(erec)
            if erec:
                row["ens116_gene_id"] = erec["gene_id"]
                row["ens116_version"] = erec["version"] or ""
                row["ens116_symbol"] = erec["symbol"]
                row["ens116_biotype"] = erec["biotype"]
                row["ens116_chrom"] = erec["chrom"]
                row["ens116_tss"] = erec["tss"]
                row["ens116_strand"] = erec["strand"]

            # --- Morabito RNA ---
            feats, route, _notes = resolve_rna(
                aid, asym, mor_by_gid, mor_by_symbol, hgnc_by_id,
                current_symbol, prev_or_alias, withdrawn_symbols,
                ens_by_hgnc, alias_by_hgnc)
            row["rna_map_route"] = route
            row["rna_n_features_mapped"] = len(feats)
            row["rna_feature_ids"] = "|".join(rna_ids[f] for f in feats)
            if len(feats) == 0:
                row["rna_state"] = ST_UNMEASURED
                row["rna_microglia_state"] = ST_UNMEASURED
                row["rna_nnz_cells_all"] = ""      # deliberately NOT 0
                row["rna_nnz_cells_microglia"] = ""
            elif len(feats) > 1:
                row["rna_state"] = ST_AMBIGUOUS
                row["rna_microglia_state"] = ST_AMBIGUOUS
                row["rna_nnz_cells_all"] = ""
                row["rna_nnz_cells_microglia"] = ""
                ambiguous_rows.append({
                    "molecular_address_index": aidx,
                    "molecular_address_id": aid,
                    "symbol": asym,
                    "route": route,
                    "n_features": len(feats),
                    "feature_ids": "|".join(rna_ids[f] for f in feats),
                    "feature_symbols": "|".join(rna_names[f] for f in feats),
                })
            else:
                f0 = feats[0]
                srcver = split_ensembl_version(rna_ids[f0])[1]
                row["rna_source_version"] = srcver or ""
                if erec and erec["version"] and srcver:
                    row["rna_version_matches_ens116"] = (
                        str(erec["version"]) == str(srcver))
                else:
                    row["rna_version_matches_ens116"] = ST_UNKNOWN
                nz = int(rna_nnz_all[f0])
                if nz < 0:
                    row["rna_state"] = ST_UNKNOWN
                    row["rna_nnz_cells_all"] = ""
                else:
                    row["rna_nnz_cells_all"] = nz
                    row["rna_state"] = (ST_DETECTED if nz > 0
                                        else ST_UNDETECTED)
                nzm = int(rna_nnz_mg[f0])
                if nzm < 0:
                    row["rna_microglia_state"] = ST_UNKNOWN
                    row["rna_nnz_cells_microglia"] = ""
                else:
                    row["rna_nnz_cells_microglia"] = nzm
                    row["rna_microglia_state"] = (ST_DETECTED if nzm > 0
                                                  else ST_UNDETECTED)

            # --- regulatory geometry from Ensembl 116 TSS ---
            n_prom = n_dist = 0
            n_prom_acc = n_dist_acc = 0
            n_prom_acc_mg = n_dist_acc_mg = 0
            resolved_geom = False
            if erec:
                uc = ensembl_chrom_to_ucsc(erec["chrom"])
                if uc is not None and uc in peak_index:
                    resolved_geom = True
                    tss = erec["tss"]
                    prom = peaks_in_window(peak_index, uc,
                                           tss - PROMOTER_BP,
                                           tss + PROMOTER_BP)
                    dist_all = peaks_in_window(peak_index, uc,
                                               tss - DISTAL_BP,
                                               tss + DISTAL_BP)
                    promset = set(prom.tolist())
                    dist = np.array([p for p in dist_all.tolist()
                                     if p not in promset], dtype=np.int64)
                    n_prom, n_dist = int(prom.size), int(dist.size)
                    row["promoter_window"] = "%s:%d-%d" % (
                        uc, max(0, tss - PROMOTER_BP), tss + PROMOTER_BP)
                    if atac_nnz[0] >= 0:
                        n_prom_acc = int((atac_nnz[prom] > 0).sum()) \
                            if prom.size else 0
                        n_dist_acc = int((atac_nnz[dist] > 0).sum()) \
                            if dist.size else 0
                    if atac_nnz_mg[0] >= 0:
                        n_prom_acc_mg = int((atac_nnz_mg[prom] > 0).sum()) \
                            if prom.size else 0
                        n_dist_acc_mg = int((atac_nnz_mg[dist] > 0).sum()) \
                            if dist.size else 0
            row["n_peaks_promoter_window"] = n_prom if resolved_geom else ""
            row["n_peaks_distal_window"] = n_dist if resolved_geom else ""
            row["annotation_regulatory_state"] = classify_annotation_regulatory(
                resolved_geom, n_prom, n_dist)
            scanned = atac_nnz[0] >= 0
            row["n_peaks_promoter_accessible"] = (
                n_prom_acc if (resolved_geom and scanned) else "")
            row["n_peaks_distal_accessible"] = (
                n_dist_acc if (resolved_geom and scanned) else "")
            row["atac_accessibility_state"] = (
                classify_atac_accessibility(resolved_geom, n_prom_acc,
                                            n_dist_acc, n_prom, n_dist)
                if scanned else ST_UNKNOWN)
            mg_scanned = atac_nnz_mg[0] >= 0
            row["n_peaks_promoter_accessible_microglia"] = (
                n_prom_acc_mg if (resolved_geom and mg_scanned) else "")
            row["n_peaks_distal_accessible_microglia"] = (
                n_dist_acc_mg if (resolved_geom and mg_scanned) else "")
            row["atac_microglia_accessibility_state"] = (
                classify_atac_accessibility(resolved_geom, n_prom_acc_mg,
                                            n_dist_acc_mg, n_prom, n_dist)
                if mg_scanned else ST_UNKNOWN)

            # --- Stage75C cross-check ---
            cls = s75c_by_gene.get(gid, [])
            row["stage75c_n_peaks_nearest"] = len(cls)
            row["stage75c_peak_gene_classes"] = "|".join(
                sorted(set(c for c in cls if c)))

            # --- Stage75F hypothesis evidence ---
            sym_n = norm_symbol(asym)
            is_reg = sym_n in s75f_reg_syms
            partners = s75f_targets.get(sym_n, [])
            if is_reg and partners:
                role = "REGULATOR_AND_TARGET"
            elif is_reg:
                role = "REGULATOR"
            elif partners:
                role = "TARGET"
            else:
                role = "NOT_IN_STAGE75F"
            row["stage75f_role"] = role
            row["stage75f_tf_partners"] = "|".join(sorted(set(partners)))
            row["stage75f_n_evidence_rows"] = len(partners)
            if is_reg:
                tf_rows.append((asym, aidx, row["rna_state"],
                                row["rna_microglia_state"],
                                row["atac_accessibility_state"]))

            # --- query panel ---
            in_panel = sym_n in panel_set
            row["query_panel_member"] = in_panel
            row["query_panel_groups"] = panel_groups.get(sym_n, "")
            if in_panel:
                panel_hits[sym_n] += 1

            # --- regulatory-evidence state (fourth named state) ---
            if row["rna_state"] in (ST_UNMEASURED, ST_AMBIGUOUS):
                row["regulatory_evidence_state"] = row["rna_state"]
            elif row["annotation_regulatory_state"] == ST_UNKNOWN:
                row["regulatory_evidence_state"] = ST_UNKNOWN
            elif row["annotation_regulatory_state"] in (
                    "PROMOTER_SUPPORTED", "DISTAL_CANDIDATE_ONLY"):
                row["regulatory_evidence_state"] = "REGULATORY_EVIDENCE_PRESENT"
            else:
                row["regulatory_evidence_state"] = ST_NO_REG

            # --- matched RNA-ATAC eligibility ---
            if row["rna_state"] in (ST_UNMEASURED, ST_AMBIGUOUS):
                row["matched_rna_atac_state"] = row["rna_state"]
            elif row["rna_state"] == ST_UNKNOWN or \
                    row["atac_accessibility_state"] == ST_UNKNOWN:
                row["matched_rna_atac_state"] = ST_UNKNOWN
            elif row["atac_accessibility_state"] in (
                    "ACCESSIBLE_PROMOTER", "ACCESSIBLE_DISTAL_ONLY"):
                row["matched_rna_atac_state"] = "ELIGIBLE_MATCHED_RNA_ATAC"
            else:
                row["matched_rna_atac_state"] = "NOT_ELIGIBLE_NO_ACCESSIBLE_REGION"

            w.writerow(row)
            written += 1
            written_idx[aidx] += 1
            for k in state_by:
                state_by[k][row[k]] += 1
            tally[row["rna_state"]] += 1

    # ------------------------------------------------------------------
    # 10. Closure: counts transcribed from what was WRITTEN, not intended.
    # ------------------------------------------------------------------
    if written != n_addr:
        raise SystemExit("FAIL-CLOSED: wrote %d rows for %d addresses."
                         % (written, n_addr))
    if set(written_idx) != set(range(n_addr)) or \
            any(c != 1 for c in written_idx.values()):
        raise SystemExit("FAIL-CLOSED: output is not exactly one row per "
                         "canonical address.")
    for k, ctr in state_by.items():
        tot = sum(ctr.values())
        if tot != n_addr:
            raise SystemExit("FAIL-CLOSED: %s states sum to %d, not %d"
                             % (k, tot, n_addr))
    prov["counts"]["rows_written"] = written
    prov["counts"]["one_row_per_address_verified"] = True
    prov["state_counts"] = {k: dict(v) for k, v in state_by.items()}

    # ------------------------------------------------------------------
    # 11. Side reports.
    # ------------------------------------------------------------------
    coll_csv = os.path.join(out_dir, "agent2_collision_report_v1.csv")
    with open(coll_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["collision_type", "key",
                                           "n_features", "feature_ids",
                                           "feature_symbols"])
        w.writeheader()
        for c in sorted(collisions, key=lambda x: (x["collision_type"],
                                                   x["key"])):
            w.writerow(c)
    amb_csv = os.path.join(out_dir, "agent2_ambiguous_address_report_v1.csv")
    with open(amb_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["molecular_address_index",
                                           "molecular_address_id", "symbol",
                                           "route", "n_features",
                                           "feature_ids", "feature_symbols"])
        w.writeheader()
        for a in ambiguous_rows:
            w.writerow(a)
    prov["counts"]["addresses_ambiguously_mapped"] = len(ambiguous_rows)
    prov["counts"]["collision_rows"] = len(collisions)

    tf_csv = os.path.join(out_dir, "agent2_tf_coverage_v1.csv")
    with open(tf_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tf", "in_canonical_registry", "molecular_address_index",
                    "rna_state", "rna_microglia_state",
                    "atac_accessibility_state"])
        found = {t[0].upper() for t in tf_rows}
        for tf in s75f_roster:
            hit = [t for t in tf_rows if t[0].upper() == tf.upper()]
            if hit:
                t = hit[0]
                w.writerow([tf, True, t[1], t[2], t[3], t[4]])
            else:
                w.writerow([tf, False, "", ST_UNMEASURED, ST_UNMEASURED,
                            ST_UNKNOWN])
        prov["counts"]["stage75f_regulators_in_registry"] = len(
            [t for t in s75f_roster if t.upper() in found])

    panel_csv = os.path.join(out_dir, "agent2_query_panel_coverage_v1.csv")
    missing_panel = sorted(panel_set - set(panel_hits))
    with open(panel_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["panel_gene", "in_canonical_registry",
                    "n_matching_addresses"])
        for g in sorted(panel_set):
            w.writerow([g, g in panel_hits, panel_hits.get(g, 0)])
    prov["counts"]["query_panel_genes_in_registry"] = len(panel_hits)
    prov["counts"]["query_panel_genes_absent_from_registry"] = len(
        missing_panel)
    prov["counts"]["query_panel_absent_symbols"] = missing_panel

    prov["outputs"] = {}
    for p in (out_csv, coll_csv, amb_csv, tf_csv, panel_csv):
        prov["outputs"][os.path.basename(p)] = file_receipt(p)
    prov_path = os.path.join(out_dir, "agent2_coverage_provenance_v1.json")
    with open(prov_path, "w", encoding="utf-8") as fh:
        json.dump(prov, fh, indent=2, sort_keys=True)
    return prov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out-dir", required=True)
    for opt in ("registry", "block-manifest", "gtf", "hgnc", "hgnc-withdrawn",
                "rna-h5", "atac-h5", "rna-meta", "atac-meta", "stage75c",
                "stage75f-primary", "stage75f-secondary",
                "stage75f-primary-motif", "stage75f-secondary-motif",
                "query-panel"):
        ap.add_argument("--" + opt, default=None)
    ap.add_argument("--microglia-label", default="MG")
    ap.add_argument("--skip-matrix-scan", action="store_true")
    ap.add_argument("--no-enforce-digests", action="store_true")
    a = ap.parse_args()
    paths = resolve_default_paths(a.repo.rstrip("/\\"), a)
    prov = build(paths, a.out_dir, microglia_label=a.microglia_label,
                 skip_matrix_scan=a.skip_matrix_scan,
                 enforce_digests=not a.no_enforce_digests)
    print(json.dumps({"counts": prov["counts"],
                      "state_counts": prov["state_counts"]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
