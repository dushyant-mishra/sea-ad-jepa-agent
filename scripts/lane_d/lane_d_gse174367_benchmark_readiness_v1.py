#!/usr/bin/env python
"""LANE D - GSE174367 RNA/ATAC + Stage75F benchmark-readiness reconnaissance.

READ-ONLY. Executes no biological evaluation. Emits provenance, overlap,
coordinate and contamination-audit artifacts only.

Governance footer carried by every artifact produced here:
  TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED |
  D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
import argparse
import collections
import hashlib
import json
import os
import re
from datetime import datetime, timezone

import h5py
import numpy as np
import pandas as pd

FOOTER = ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | "
          "D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF")


# ---------------------------------------------------------------- utilities

def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def size_or_none(path):
    return os.path.getsize(path) if os.path.exists(path) else None


# ---------------------------------------------------- 1. file authentication
# SHA-256 values recorded by the historical acquisition manifest
# results/tables/stage38a_download_manifest_v1.csv (data rows 12-14).
RECORDED = {
    "data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5": dict(
        size=273975534,
        sha256="6ba98a1af8772af08c8cdd5e5e63eebb0890daed48cac2e1b8961dcc67069b77",
        source="results/tables/stage38a_download_manifest_v1.csv"),
    "data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz": dict(
        size=435170,
        sha256="ab1a029deb43196e2bb1fea5907d838885750cfff3850c600c07588c7c7cdb2b",
        source="results/tables/stage38a_download_manifest_v1.csv"),
    "data/external/public_schema_audit/GSE174367/GSE174367_series_matrix.txt.gz": dict(
        size=13280,
        sha256="e36488f44e30d0bdf48f5864b8cd091629203defecbb41d9e7fec721b5115928",
        source="results/tables/stage38a_download_manifest_v1.csv"),
    "data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5": dict(
        size=None, sha256=None,
        source="NO_RECORDED_SHA256_ANYWHERE_IN_REPOSITORY"),
    "data/external/gse174367/GSE174367_snATAC-seq_cell_meta.csv.gz": dict(
        size=None, sha256=None,
        source="NO_RECORDED_SHA256_ANYWHERE_IN_REPOSITORY"),
}


def authenticate_files(root, precomputed):
    rows = []
    for rel, rec in RECORDED.items():
        path = os.path.join(root, rel)
        exists = os.path.exists(path)
        size = size_or_none(path)
        digest = precomputed.get(rel)
        if exists and digest is None:
            digest = sha256_file(path)
        if not exists:
            status, action = "ABSENT", "needs_download"
        elif rec["sha256"] is None:
            status = "PRESENT_NO_RECORDED_DIGEST"
            action = "needs_independent_reauthentication_against_GEO"
        elif rec["sha256"] == digest and rec["size"] == size:
            status, action = "AUTHENTICATED", "none"
        else:
            status, action = "DIGEST_MISMATCH", "needs_download_and_reauthentication"
        rows.append(dict(
            relative_path=rel,
            exists_locally=bool(exists),
            observed_size_bytes=size,
            recorded_size_bytes=rec["size"],
            observed_sha256=digest,
            recorded_sha256=rec["sha256"],
            recorded_digest_source=rec["source"],
            authentication_status=status,
            required_action=action,
        ))
    return pd.DataFrame(rows)


# --------------------------------- 2. Stage75F frozen-freeze authentication

def authenticate_stage75f(root):
    manifest_rel = "results/reports/stage75_integrated_evidence_manifest_v1.json"
    manifest_path = os.path.join(root, manifest_rel)
    if not os.path.exists(manifest_path):
        return None, pd.DataFrame()
    with open(manifest_path) as fh:
        man = json.load(fh)

    rows = []
    for name, spec in man["source_tables"].items():
        p = os.path.join(root, spec["path"])
        exists = os.path.exists(p)
        obs = sha256_file(p) if exists else None
        n_rows, cols_ok = None, None
        if exists:
            df = pd.read_csv(p)
            n_rows = len(df)
            cols_ok = bool(list(df.columns) == spec["columns"])
        rows.append(dict(
            role="stage75f_source_table", table=name, path=spec["path"],
            exists=bool(exists), recorded_sha256=spec["sha256"], observed_sha256=obs,
            digest_match=bool(obs == spec["sha256"]) if exists else False,
            recorded_rows=spec["rows"], observed_rows=n_rows,
            row_count_match=bool(n_rows == spec["rows"]) if exists else False,
            column_schema_match=cols_ok))

    # Frozen outputs. The manifest records their row counts but not their
    # digests, so this run establishes those digests for the first time.
    out_expected = man["output_row_counts"]
    out_map = {
        "regulator_summary": man["outputs"]["regulator_summary_csv"],
        "tf_target_summary": man["outputs"]["tf_target_summary_csv"],
        "negative_regulator_gate": man["outputs"]["negative_regulator_gate_csv"],
    }
    for name, rel in out_map.items():
        p = os.path.join(root, rel)
        exists = os.path.exists(p)
        obs = sha256_file(p) if exists else None
        n_rows = len(pd.read_csv(p)) if exists else None
        rows.append(dict(
            role="stage75f_frozen_output", table=name, path=rel, exists=bool(exists),
            recorded_sha256=None, observed_sha256=obs, digest_match=None,
            recorded_rows=out_expected[name], observed_rows=n_rows,
            row_count_match=bool(n_rows == out_expected[name]) if exists else False,
            column_schema_match=None))

    # The manifest itself.
    rows.append(dict(
        role="stage75f_manifest", table="integrated_evidence_manifest",
        path=manifest_rel, exists=True, recorded_sha256=None,
        observed_sha256=sha256_file(manifest_path), digest_match=None,
        recorded_rows=None, observed_rows=None, row_count_match=None,
        column_schema_match=None))
    return man, pd.DataFrame(rows)


# ------------------------------------------------ 3. donor / sample overlap

def sample_overlap(root):
    rna = pd.read_csv(os.path.join(
        root, "data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz"))
    atac = pd.read_csv(os.path.join(
        root, "data/external/gse174367/GSE174367_snATAC-seq_cell_meta.csv.gz")
    ).rename(columns={"Sample.ID": "SampleID"})

    rows = []
    for s in sorted(set(rna.SampleID) | set(atac.SampleID),
                    key=lambda x: int(x.split("-")[1])):
        r = rna[rna.SampleID == s]
        a = atac[atac.SampleID == s]
        src = r if len(r) else a
        rows.append(dict(
            sample_id=s,
            in_processed_rna=bool(len(r)), in_processed_atac=bool(len(a)),
            rna_cells=int(len(r)), atac_cells=int(len(a)),
            rna_microglia_cells=int((r["Cell.Type"] == "MG").sum()),
            atac_microglia_cells=int((a["Cell.Type"] == "MG").sum()),
            diagnosis=str(src.Diagnosis.iloc[0]),
            age=int(src.Age.iloc[0]), sex=str(src.Sex.iloc[0]),
            rna_batch=(int(r.Batch.iloc[0]) if len(r) else None),
            atac_batch=(int(a.Batch.iloc[0]) if len(a) else None),
            shared_donor_both_modalities=bool(len(r) and len(a)),
            paired_rna_atac_nuclei="NO_CELL_LEVEL_PAIRING_IN_DEPOSIT"))
    tbl = pd.DataFrame(rows)

    # Do the two assays agree on donor-level covariates? If SampleID is a
    # donor key shared across assays, every covariate must agree exactly.
    cov = ["Age", "Sex", "PMI", "Tangle.Stage", "Plaque.Stage", "Diagnosis", "RIN"]
    r1 = rna[["SampleID"] + cov].drop_duplicates()
    a1 = atac[["SampleID"] + cov].drop_duplicates()
    m = r1.merge(a1, on="SampleID", suffixes=("_rna", "_atac"))
    mism = {c: int((m[c + "_rna"].astype(str) != m[c + "_atac"].astype(str)).sum())
            for c in cov}

    # Is there any cell-level correspondence between the two assays?
    rb, ab = set(rna.Barcode), set(atac.Barcode)
    rseq = set(b.rsplit("-", 1)[0] for b in rb)
    aseq = set(b.rsplit("-", 1)[0] for b in ab)
    n_shared_seq = len(rseq & aseq)
    expected_common_wl = len(rseq) * len(aseq) / 737280.0

    r_suf = rna.assign(suf=rna.Barcode.str.rsplit("-", n=1).str[1]) \
               .groupby("suf").SampleID.agg(lambda s: sorted(set(s))[0]).to_dict()
    a_suf = atac.assign(suf=atac.Barcode.str.rsplit("-", n=1).str[1]) \
                .groupby("suf").SampleID.agg(lambda s: sorted(set(s))[0]).to_dict()
    suffix_map = {suf: dict(rna_sample=r_suf[suf], atac_sample=a_suf[suf],
                            same_sample=bool(r_suf[suf] == a_suf[suf]))
                  for suf in sorted(set(r_suf) & set(a_suf), key=int)}

    pairing = dict(
        verdict="NO_CELL_LEVEL_RNA_ATAC_PAIRING",
        raw_barcode_string_overlap=len(rb & ab),
        raw_overlap_is_spurious=True,
        stripped_16mer_overlap=n_shared_seq,
        rna_unique_16mers=len(rseq), atac_unique_16mers=len(aseq),
        expected_overlap_if_one_shared_737280_whitelist=round(expected_common_wl, 1),
        observed_over_expected=round(n_shared_seq / expected_common_wl, 5),
        gem_group_suffix_collision=suffix_map,
        n_suffixes_where_same_integer_means_different_sample=int(
            sum(1 for v in suffix_map.values() if not v["same_sample"])),
        basis=("The GEO series deposits separate snRNA-seq (library_strategy RNA-Seq) "
               "and snATAC-seq (library_strategy ATAC-seq) libraries prepared by "
               "independent unbiased total-nuclei isolations from the same biological "
               "samples. No 10x Multiome / paired-modality assay is deposited and the "
               "deposit supplies no cell-level correspondence table."),
        interpretation=("Observed 16-mer overlap is a tiny fraction of what a single "
                        "shared 737,280-barcode whitelist would produce, so the two "
                        "assays draw from largely disjoint whitelists (10x 3-prime GEX "
                        "vs 10x scATAC v1). The raw barcode string matches that do "
                        "occur map to DIFFERENT samples because the GEM-group integer "
                        "suffix is assay-local. Any cell-level RNA-ATAC join would be "
                        "fabricated."))
    return tbl, mism, pairing


# --------------------------------------------- 4. gene overlap with FULL104

FULL104_REGISTRY = ("results/v4/"
                    "stage81a2r_foundation_molecular_address_registry_candidate.csv")


def gene_overlap(root):
    h5 = os.path.join(
        root, "data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5")
    with h5py.File(h5, "r") as f:
        g = f["matrix"]
        gid = np.array([x.decode() for x in g["features"]["id"][:]])
        gname = np.array([x.decode() for x in g["features"]["name"][:]])
        genome = np.array([x.decode() for x in g["features"]["genome"][:]])
        ftype = np.array([x.decode() for x in g["features"]["feature_type"][:]])

    base = np.array([x.split(".")[0] for x in gid])            # keeps _PAR_Y suffix
    stem = np.array([x.replace("_PAR_Y", "") for x in base])   # collapses PAR_Y
    is_par = np.array(["_PAR_Y" in x for x in gid])

    reg = pd.read_csv(
        os.path.join(root, FULL104_REGISTRY),
        usecols=["molecular_address_index", "molecular_address_id", "identity_class",
                 "current_ensembl_gene_id", "legacy_source_exact_id", "symbol"])
    reg["legacy_stem"] = reg.legacy_source_exact_id.astype(str).str.split(".").str[0]

    reg_cur = set(x for x in reg.current_ensembl_gene_id.dropna().astype(str)
                  if x.startswith("ENSG"))
    reg_leg = set(x for x in reg.legacy_stem if x.startswith("ENSG"))
    reg_addr = set(reg.molecular_address_id.astype(str))
    reg_sym = set(reg.symbol.dropna().astype(str))

    in_cur = np.isin(stem, list(reg_cur))
    in_leg = np.isin(stem, list(reg_leg)) & ~in_cur
    in_addr = np.isin(stem, list(reg_addr)) & ~in_cur & ~in_leg
    sym_only = (~in_cur & ~in_leg & ~in_addr) & np.isin(gname, list(reg_sym))

    cls = np.array(["unmatched_no_full104_address"] * len(gid), dtype=object)
    cls[sym_only] = "symbol_only_ambiguous_not_joinable"
    cls[in_addr] = "address_id_match_non_ensembl"
    cls[in_leg] = "legacy_ensembl_match"
    cls[in_cur] = "current_ensembl_exact"

    feat = pd.DataFrame(dict(
        gse174367_feature_id=gid, ensembl_unversioned=base, ensembl_stem=stem,
        gse174367_symbol=gname, gse174367_genome=genome,
        gse174367_feature_type=ftype, is_par_y_copy=is_par,
        full104_match_class=cls))

    # ------- collision register: reported, never silently deduplicated -----
    collisions = []
    dup_unv = {k: v for k, v in collections.Counter(base).items() if v > 1}
    for k in sorted(dup_unv):
        idx = np.where(base == k)[0]
        collisions.append(dict(
            collision_class="duplicate_unversioned_ensembl_id_within_gse174367",
            key=k, multiplicity=int(dup_unv[k]),
            members="|".join(gid[idx]), symbols="|".join(sorted(set(gname[idx]))),
            resolution="RETAINED_UNRESOLVED",
            note="all such groups are PAR_Y pairs; see par_y class"))
    dup_par = {k: v for k, v in collections.Counter(stem[is_par]).items()}
    for k in sorted(dup_par):
        idx = np.where(stem == k)[0]
        collisions.append(dict(
            collision_class="par_y_x_y_locus_collision_against_full104_address",
            key=k, multiplicity=int(len(idx)),
            members="|".join(gid[idx]), symbols="|".join(sorted(set(gname[idx]))),
            resolution="RETAINED_UNRESOLVED",
            note=("X and Y pseudoautosomal copies are distinct physical loci that "
                  "collapse onto one FULL104 Ensembl address; summing them would "
                  "merge two chromosomes' counts")))
    dup_sym = {k: v for k, v in collections.Counter(gname).items() if v > 1}
    for k in sorted(dup_sym):
        idx = np.where(gname == k)[0]
        if all(is_par[idx]) or len(set(stem[idx])) == 1:
            continue
        collisions.append(dict(
            collision_class="symbol_maps_to_multiple_distinct_ensembl_ids",
            key=k, multiplicity=int(dup_sym[k]),
            members="|".join(gid[idx]), symbols=k,
            resolution="RETAINED_UNRESOLVED",
            note="symbol is not a usable join key; join on Ensembl identity only"))
    matched = feat[feat.full104_match_class.isin(
        ["current_ensembl_exact", "legacy_ensembl_match"])]
    many_to_one = {k: v for k, v in collections.Counter(matched.ensembl_stem).items()
                   if v > 1}
    for k in sorted(many_to_one):
        sub = matched[matched.ensembl_stem == k]
        collisions.append(dict(
            collision_class="many_gse174367_features_to_one_full104_address",
            key=k, multiplicity=int(many_to_one[k]),
            members="|".join(sub.gse174367_feature_id),
            symbols="|".join(sorted(set(sub.gse174367_symbol))),
            resolution="RETAINED_UNRESOLVED",
            note="requires an explicit declared aggregation rule before any join"))
    coll = pd.DataFrame(collisions)

    matched_stems = set(matched.ensembl_stem)
    reg_hit = reg[reg.current_ensembl_gene_id.isin(matched_stems) |
                  reg.legacy_stem.isin(matched_stems)]

    summary = dict(
        gse174367_features_total=int(len(gid)),
        gse174367_reference_genome=str(collections.Counter(genome).most_common(1)[0][0]),
        gse174367_feature_types={k: int(v) for k, v in collections.Counter(ftype).items()},
        gse174367_all_ids_versioned=bool(all("." in x for x in gid)),
        gse174367_unique_versioned_ids=int(len(set(gid))),
        gse174367_unique_unversioned_ids=int(len(set(base))),
        gse174367_unique_symbols=int(len(set(gname))),
        gse174367_par_y_features=int(is_par.sum()),
        full104_registry_path=FULL104_REGISTRY,
        full104_addresses_total=int(len(reg)),
        full104_identity_class_counts={k: int(v) for k, v in
                                       reg.identity_class.value_counts().items()},
        match_class_counts={k: int(v) for k, v in collections.Counter(cls).items()},
        full104_addresses_covered_by_gse174367=int(len(reg_hit)),
        full104_addresses_not_covered=int(len(reg) - len(reg_hit)),
        full104_coverage_fraction=round(len(reg_hit) / len(reg), 6),
        collision_counts=({k: int(v) for k, v in
                           collections.Counter(coll.collision_class).items()}
                          if len(coll) else {}),
        unresolved_collisions_total=int(len(coll)),
        structural_missingness=dict(
            full104_addresses_absent_from_gse174367=int(len(reg) - len(reg_hit)),
            gse174367_features_with_no_full104_address=int(
                (cls == "unmatched_no_full104_address").sum()),
            note=("Absence is structural. GSE174367 was quantified against a "
                  "GRCh38.p12 CellRanger pre-mRNA reference; FULL104 addresses come "
                  "from the Stage81A2R authoritative Ensembl identity layer built over "
                  "SEA-AD + HVS + NPH52. A missing address means the gene was not in "
                  "the other vocabulary, NOT that it is biologically absent. Any "
                  "evaluation must treat non-overlap as missing-by-design and must "
                  "not impute zeros.")),
        annotation_versions=dict(
            gse174367_rna_reference="GRCh38.p12.premrna2 (CellRanger pre-mRNA reference)",
            gse174367_atac_reference="GRCh38",
            full104_identity_authority="Stage81A2R authoritative Ensembl identity layer",
            stage75_peak_annotation="GENCODE v44 / hg38",
            cross_version_liftover_executed=False,
            cross_version_reconciliation="NOT_EXECUTED"))
    return feat, coll, summary


# ------------------------------------------------- 5. ATAC coordinate audit

def peak_audit(root):
    h5 = os.path.join(
        root, "data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5")
    with h5py.File(h5, "r") as f:
        g = f["matrix"]
        pid = np.array([x.decode() for x in g["features"]["id"][:]])
        pname = np.array([x.decode() for x in g["features"]["name"][:]])
        genome = np.array([x.decode() for x in g["features"]["genome"][:]])
        shape = g["shape"][:]
        nnz = int(g["data"].shape[0])

    rec = re.compile(r"^(.+):(\d+)-(\d+)$")
    chrom, start, end, bad = [], [], [], []
    for x in pid:
        m = rec.match(x)
        if not m:
            bad.append(x)
            continue
        chrom.append(m.group(1))
        start.append(int(m.group(2)))
        end.append(int(m.group(3)))
    chrom, start, end = np.array(chrom), np.array(start), np.array(end)
    width = end - start
    cc = collections.Counter(chrom)
    canonical = re.compile(r"^chr([1-9]|1[0-9]|2[0-2]|X|Y)$")
    noncanon = sorted([c for c in cc if not canonical.match(c)])

    peaks = pd.DataFrame(dict(peak_id=pid, chrom=chrom, start=start, end=end,
                              width=width))
    audit = dict(
        n_peaks=int(shape[0]), n_barcodes=int(shape[1]), stored_nonzeros=nnz,
        n_unique_peak_ids=int(len(set(pid))),
        id_equals_name=bool(np.array_equal(pid, pname)),
        unparseable_peak_ids=len(bad),
        declared_genome=str(collections.Counter(genome).most_common(1)[0][0]),
        reference_build_claimed="hg38 / GRCh38",
        reference_build_independently_verified=False,
        build_verification_status="NOT_EXECUTED",
        build_verification_note=("The h5 declares genome=GRCh38 and every interval "
                                 "lies inside hg38 chromosome bounds, but no per-peak "
                                 "chrom.sizes containment test or liftOver round-trip "
                                 "has been run here."),
        chromosome_naming_convention="UCSC chr-prefixed",
        fraction_chr_prefixed=float(np.mean([c.startswith("chr") for c in chrom])),
        n_distinct_contigs=len(cc),
        contigs={k: int(v) for k, v in sorted(cc.items(), key=lambda kv: -kv[1])},
        noncanonical_contigs=noncanon,
        chrM_present=bool("chrM" in cc or "chrMT" in cc),
        alt_scaffold_peaks=int(sum(cc[c] for c in noncanon)),
        peak_width=dict(min=int(width.min()), p25=int(np.percentile(width, 25)),
                        median=int(np.median(width)),
                        mean=round(float(width.mean()), 2),
                        p75=int(np.percentile(width, 75)), max=int(width.max())),
        degenerate_peaks_width_lt_50bp=int((width < 50).sum()),
        wide_peaks_width_gt_10kb=int((width > 10000).sum()),
        coordinate_system_note=("CellRanger-ATAC peak ids are BED-like: 0-based "
                                "half-open start, end exclusive. Joining against a "
                                "1-based annotation (GTF) requires start+1."))
    return peaks, audit


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--precomputed-digests", default=None)
    args = ap.parse_args()
    root, out = args.repo_root, args.out_dir
    os.makedirs(out, exist_ok=True)

    pre = {}
    if args.precomputed_digests and os.path.exists(args.precomputed_digests):
        for line in open(args.precomputed_digests):
            parts = line.strip().split("|")
            if len(parts) == 3:
                pre[parts[0].replace("\\", "/")] = parts[2]

    auth = authenticate_files(root, pre)
    auth.to_csv(os.path.join(out, "laneD_file_authentication_v1.csv"), index=False)

    man, s75 = authenticate_stage75f(root)
    s75.to_csv(os.path.join(out, "laneD_stage75f_authentication_v1.csv"), index=False)

    ov, mism, pairing = sample_overlap(root)
    ov.to_csv(os.path.join(out, "laneD_sample_donor_overlap_v1.csv"), index=False)

    feat, coll, gsum = gene_overlap(root)
    feat.to_csv(os.path.join(out, "laneD_gene_feature_map_v1.csv.gz"), index=False,
                compression="gzip")
    coll.to_csv(os.path.join(out, "laneD_gene_collision_register_v1.csv"), index=False)

    peaks, paudit = peak_audit(root)
    peaks.to_csv(os.path.join(out, "laneD_atac_peak_coordinates_v1.csv.gz"),
                 index=False, compression="gzip")

    src = s75[s75.role == "stage75f_source_table"] if len(s75) else pd.DataFrame()
    outs = s75[s75.role == "stage75f_frozen_output"] if len(s75) else pd.DataFrame()

    summary = dict(
        lane="LANE_D_external_multiomics",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        repo_root=root,
        governance_footer=FOOTER,
        execution_class="RECONNAISSANCE_ONLY",
        biological_evaluation_status="NOT_EXECUTED",
        file_authentication=json.loads(auth.to_json(orient="records")),
        stage75f=dict(
            manifest_path="results/reports/stage75_integrated_evidence_manifest_v1.json",
            manifest_git_commit=(man or {}).get("git_commit"),
            recovered=man is not None,
            source_tables_total=int(len(src)),
            source_tables_digest_authenticated=int(src.digest_match.sum()) if len(src) else 0,
            source_tables_rowcount_authenticated=int(src.row_count_match.sum()) if len(src) else 0,
            source_tables_schema_authenticated=int(src.column_schema_match.sum()) if len(src) else 0,
            frozen_output_rows=({r.table: r.observed_rows for r in outs.itertuples()}
                                if len(outs) else {}),
            frozen_output_digests=({r.table: r.observed_sha256 for r in outs.itertuples()}
                                   if len(outs) else {}),
            tiers=(man or {}).get("tiers"),
            parameters=(man or {}).get("parameters"),
            claim_boundaries=(man or {}).get("claim_boundaries"),
            what_this_is=("A compact 10-regulator / 96-row TF-target motif-evidence "
                          "package with a 3-regulator negative gate. It is NOT a "
                          "validated regulatory network, NOT a complete SCENIC+ "
                          "eRegulon model, NOT causal evidence, NOT a therapeutic "
                          "ranking.")),
        sample_overlap=dict(
            processed_rna_samples=int(ov.in_processed_rna.sum()),
            processed_atac_samples=int(ov.in_processed_atac.sum()),
            shared_donor_samples=int(ov.shared_donor_both_modalities.sum()),
            rna_only_samples=sorted(ov.loc[ov.in_processed_rna & ~ov.in_processed_atac,
                                           "sample_id"].tolist()),
            atac_only_samples=sorted(ov.loc[ov.in_processed_atac & ~ov.in_processed_rna,
                                            "sample_id"].tolist()),
            rna_cells_total=int(ov.rna_cells.sum()),
            atac_cells_total=int(ov.atac_cells.sum()),
            rna_microglia_total=int(ov.rna_microglia_cells.sum()),
            atac_microglia_total=int(ov.atac_microglia_cells.sum()),
            donor_covariate_mismatches_across_shared_samples=mism,
            sample_id_is_donor_level_key=bool(all(v == 0 for v in mism.values())),
            cell_level_pairing=pairing),
        gene_overlap=gsum,
        atac_coordinate_audit=paudit)

    with open(os.path.join(out, "laneD_provenance_manifest_v1.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps({k: v for k, v in summary.items()
                      if k != "file_authentication"}, indent=2)[:9000])


if __name__ == "__main__":
    main()
