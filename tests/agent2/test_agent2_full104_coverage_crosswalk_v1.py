#!/usr/bin/env python
"""Adversarial tests for the AGENT 2 FULL104 coverage crosswalk.

Each test plants a specific defect and requires the builder to DETECT it. A
check that cannot fail is not evidence, so every adversarial test is paired
with a demonstration that the same machinery passes on clean input (the
positive control, test 01) and several tests assert the *negative* case too --
i.e. that the detector does not fire when the defect is absent.

Planted defects required by the assignment:
  * an unmapped identifier                      -> test 03
  * a version-suffixed Ensembl ID               -> test 04, 05
  * a symbol collision                          -> test 06
  * a deprecated symbol                         -> test 07
  * a missing-vs-zero confusion                 -> test 08, 09
  * a duplicated address                        -> test 10

Run:  python tests/agent2/test_agent2_full104_coverage_crosswalk_v1.py
"""
import csv
import gzip
import json
import os
import shutil
import sys
import tempfile
import traceback

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts", "agent2"))

import agent2_full104_coverage_crosswalk_v1 as X  # noqa: E402

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    print("%-58s %s %s" % (name, "PASS" if condition else "FAIL", detail))
    return bool(condition)


# ---------------------------------------------------------------------------
# Synthetic fixture: a miniature but structurally faithful world.
# Real geometry is preserved in kind -- versioned Ensembl ids, PAR_Y copies,
# duplicate symbols, HGNC alias routes, a sparse CSC matrix with true zeros.
# ---------------------------------------------------------------------------
def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def build_fixture(tmp, registry_rows, rna_features, rna_counts,
                  gtf_genes=None, hgnc_rows=None):
    """Create a complete on-disk input set. Returns a paths dict."""
    import h5py

    os.makedirs(tmp, exist_ok=True)
    reg = os.path.join(tmp, "registry.csv")
    write_csv(reg,
              ["molecular_address_index", "molecular_address_id",
               "identity_class", "symbol", "biotype"],
              registry_rows)

    man = os.path.join(tmp, "manifest.csv")
    with open(man, "w", encoding="utf-8") as fh:
        fh.write("block_id,path\n0,x\n")

    # Ensembl 116 style GTF
    gtf = os.path.join(tmp, "ens.gtf.gz")
    genes = gtf_genes if gtf_genes is not None else [
        (g[1], g[3], "1", 1000 + 5000 * i, 2000 + 5000 * i, "+",
         "protein_coding", "7")
        for i, g in enumerate(registry_rows)
        if str(g[1]).startswith("ENSG")
    ]
    with gzip.open(gtf, "wt", encoding="utf-8") as fh:
        fh.write("#!genome-build GRCh38.p14\n")
        for gid, sym, chrom, start, end, strand, bt, ver in genes:
            attrs = ('gene_id "%s"; gene_version "%s"; gene_name "%s"; '
                     'gene_biotype "%s";' % (gid, ver, sym, bt))
            fh.write("\t".join([chrom, "ensembl", "gene", str(start),
                                str(end), ".", strand, ".", attrs]) + "\n")

    # HGNC complete set
    hg = os.path.join(tmp, "hgnc.txt")
    cols = ["hgnc_id", "symbol", "ensembl_gene_id", "status", "locus_group",
            "prev_symbol", "alias_symbol"]
    rows = hgnc_rows if hgnc_rows is not None else []
    with open(hg, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(cols)
        for r in rows:
            w.writerow(r)
    wd = os.path.join(tmp, "withdrawn.txt")
    with open(wd, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["HGNC_ID", "STATUS", "WITHDRAWN_SYMBOL"])
        w.writerow(["HGNC:99999", "Entry Withdrawn", "GONEGENE"])

    # snRNA h5: CSC over cells, counts[f][c]
    n_feat = len(rna_features)
    n_cells = len(rna_counts[0]) if n_feat else 0
    rna = os.path.join(tmp, "rna.h5")
    data, indices, indptr = [], [], [0]
    for c in range(n_cells):
        for f in range(n_feat):
            v = rna_counts[f][c]
            if v:
                indices.append(f)
                data.append(v)
        indptr.append(len(data))
    with h5py.File(rna, "w") as fh:
        g = fh.create_group("matrix")
        g.create_dataset("data", data=np.array(data, dtype=np.int32))
        g.create_dataset("indices", data=np.array(indices, dtype=np.int64))
        g.create_dataset("indptr", data=np.array(indptr, dtype=np.int64))
        g.create_dataset("shape", data=np.array([n_feat, n_cells],
                                                dtype=np.int32))
        g.create_dataset("barcodes",
                         data=np.array([("BC%d-1" % i).encode()
                                        for i in range(n_cells)]))
        ff = g.create_group("features")
        ff.create_dataset("id", data=np.array([f[0].encode()
                                               for f in rna_features]))
        ff.create_dataset("name", data=np.array([f[1].encode()
                                                 for f in rna_features]))
        ff.create_dataset("genome",
                          data=np.array([b"GRCh38.p12.premrna2"] * n_feat))
        ff.create_dataset("feature_type",
                          data=np.array([b"Gene Expression"] * n_feat))

    # snATAC h5: one accessible peak at the TSS of the first gene
    atac = os.path.join(tmp, "atac.h5")
    peak_ids = ["chr1:900-3000", "chr1:500000-501000"]
    a_data, a_idx, a_ptr = [1, 1], [0, 1], [0, 2]
    with h5py.File(atac, "w") as fh:
        g = fh.create_group("matrix")
        g.create_dataset("data", data=np.array(a_data, dtype=np.int32))
        g.create_dataset("indices", data=np.array(a_idx, dtype=np.int64))
        g.create_dataset("indptr", data=np.array(a_ptr, dtype=np.int64))
        g.create_dataset("shape", data=np.array([len(peak_ids), 1],
                                                dtype=np.int32))
        g.create_dataset("barcodes", data=np.array([b"ABC-1"]))
        ff = g.create_group("features")
        ff.create_dataset("id", data=np.array([p.encode() for p in peak_ids]))
        ff.create_dataset("name", data=np.array([p.encode()
                                                 for p in peak_ids]))
        ff.create_dataset("genome", data=np.array([b"GRCh38"] * len(peak_ids)))
        ff.create_dataset("feature_type", data=np.array([b"Peaks"] *
                                                        len(peak_ids)))

    rmeta = os.path.join(tmp, "rna_meta.csv.gz")
    with gzip.open(rmeta, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Barcode", "Cell.Type"])
        for i in range(n_cells):
            w.writerow(["BC%d-1" % i, "MG" if i % 2 == 0 else "ODC"])
    ameta = os.path.join(tmp, "atac_meta.csv.gz")
    with gzip.open(ameta, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Barcode", "Cell.Type"])
        w.writerow(["ABC-1", "MG"])

    s75c = os.path.join(tmp, "s75c.csv")
    write_csv(s75c, ["peak_index", "peak_id", "nearest_gene_id",
                     "peak_gene_class"], [])
    s75fp = os.path.join(tmp, "s75f_p.csv")
    write_csv(s75fp, ["tf", "target_gene"], [])
    s75fs = os.path.join(tmp, "s75f_s.csv")
    write_csv(s75fs, ["tf", "target_gene"], [])
    s75fpm = os.path.join(tmp, "s75f_pm.csv")
    write_csv(s75fpm, ["batch_id", "tf"], [])
    s75fsm = os.path.join(tmp, "s75f_sm.csv")
    write_csv(s75fsm, ["batch_id", "tf"], [])
    qp = os.path.join(tmp, "panel.csv")
    write_csv(qp, ["gene", "audit_groups"], [])

    return {
        "registry": reg, "block_manifest": man, "gtf": gtf, "hgnc": hg,
        "hgnc_withdrawn": wd, "rna_h5": rna, "atac_h5": atac,
        "rna_meta": rmeta, "atac_meta": ameta, "stage75c": s75c,
        "s75f_primary": s75fp, "s75f_secondary": s75fs,
        "s75f_primary_motif": s75fpm, "s75f_secondary_motif": s75fsm,
        "query_panel": qp,
    }


def read_rows(out_dir):
    p = os.path.join(out_dir, "agent2_full104_feature_crosswalk_v1.csv")
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run_build(paths, out_dir):
    return X.build(paths, out_dir, enforce_digests=False)


# ---------------------------------------------------------------------------
BASE_REGISTRY = [
    [0, "ENSG00000000001", "current_exact", "AAA", "protein_coding"],
    [1, "ENSG00000000002", "current_exact", "BBB", "protein_coding"],
    [2, "ENSG00000000003", "current_exact", "CCC", "protein_coding"],
]
BASE_FEATURES = [
    ("ENSG00000000001.7", "AAA"),
    ("ENSG00000000002.3", "BBB"),
    ("ENSG00000000003.9", "CCC"),
]
# AAA detected, BBB structurally present but all-zero, CCC detected.
BASE_COUNTS = [[1, 0, 2, 0], [0, 0, 0, 0], [3, 1, 0, 0]]


def t01_positive_control(tmp):
    """POSITIVE CONTROL: clean input must build and must NOT raise."""
    p = build_fixture(os.path.join(tmp, "t01"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t01_out")
    prov = run_build(p, out)
    rows = read_rows(out)
    ok = (prov["counts"]["rows_written"] == 3
          and prov["counts"]["one_row_per_address_verified"] is True
          and len(rows) == 3
          and {r["molecular_address_id"] for r in rows} ==
          {"ENSG00000000001", "ENSG00000000002", "ENSG00000000003"})
    check("01 positive_control_clean_build_succeeds", ok,
          "rows=%d" % len(rows))
    # and the clean case must NOT report ambiguity or collisions
    check("01b positive_control_reports_no_false_ambiguity",
          prov["counts"]["addresses_ambiguously_mapped"] == 0
          and prov["counts"]["collision_rows"] == 0)
    return prov, rows


def t02_registry_digest_enforced(tmp):
    """Fail-closed: a registry whose digest is not the canonical one."""
    p = build_fixture(os.path.join(tmp, "t02"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t02_out")
    raised = False
    try:
        X.build(p, out, enforce_digests=True)
    except SystemExit as e:
        raised = "canonical registry digest mismatch" in str(e)
    check("02 wrong_registry_digest_is_rejected", raised)


def t03_unmapped_identifier(tmp):
    """PLANTED: an identifier with no counterpart in the assay."""
    reg = [r[:] for r in BASE_REGISTRY]
    reg.append([3, "ENSG00000099999", "current_exact", "GHOST",
                "protein_coding"])
    p = build_fixture(os.path.join(tmp, "t03"), reg, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t03_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    g = rows["ENSG00000099999"]
    check("03 unmapped_identifier_is_UNMEASURED",
          g["rna_state"] == X.ST_UNMEASURED and g["rna_map_route"] == "none",
          "state=%s" % g["rna_state"])
    check("03b unmapped_identifier_has_no_fabricated_zero",
          g["rna_nnz_cells_all"] == "",
          "nnz=%r" % g["rna_nnz_cells_all"])


def t04_version_suffix_handled(tmp):
    """PLANTED: version-suffixed Ensembl IDs must still join on stable ID."""
    p = build_fixture(os.path.join(tmp, "t04"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t04_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    a = rows["ENSG00000000001"]
    check("04 version_suffixed_id_joins_on_stable_id",
          a["rna_map_route"] == "ensembl_stable_id"
          and a["rna_source_version"] == "7",
          "route=%s ver=%s" % (a["rna_map_route"], a["rna_source_version"]))
    # a raw string compare would have failed; prove the splitter is real
    check("04b split_ensembl_version_is_not_identity",
          X.split_ensembl_version("ENSG00000000001.7")[0]
          == "ENSG00000000001")


def t05_version_disagreement_reported(tmp):
    """PLANTED: assay version 3 vs annotation version 11 must be reported."""
    genes = [("ENSG00000000001", "AAA", "1", 1000, 2000, "+",
              "protein_coding", "11"),
             ("ENSG00000000002", "BBB", "1", 9000, 9500, "+",
              "protein_coding", "3"),
             ("ENSG00000000003", "CCC", "1", 20000, 21000, "+",
              "protein_coding", "9")]
    p = build_fixture(os.path.join(tmp, "t05"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS, gtf_genes=genes)
    out = os.path.join(tmp, "t05_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    check("05 version_disagreement_is_flagged_false",
          rows["ENSG00000000001"]["rna_version_matches_ens116"] == "False",
          "AAA=%s" % rows["ENSG00000000001"]["rna_version_matches_ens116"])
    check("05b version_agreement_is_flagged_true",
          rows["ENSG00000000002"]["rna_version_matches_ens116"] == "True",
          "BBB=%s" % rows["ENSG00000000002"]["rna_version_matches_ens116"])


def t06_symbol_collision(tmp):
    """PLANTED: one symbol bound to two distinct assay features."""
    feats = BASE_FEATURES + [("ENSG00000000044.2", "AAA")]
    counts = [r[:] for r in BASE_COUNTS] + [[5, 0, 0, 1]]
    p = build_fixture(os.path.join(tmp, "t06"), BASE_REGISTRY, feats, counts)
    out = os.path.join(tmp, "t06_out")
    prov = run_build(p, out)
    coll = os.path.join(out, "agent2_collision_report_v1.csv")
    with open(coll, newline="", encoding="utf-8") as fh:
        crows = list(csv.DictReader(fh))
    hit = [c for c in crows if c["key"] == "AAA"
           and c["collision_type"] == "gene_symbol_multi_feature"]
    check("06 symbol_collision_is_reported_not_deduplicated",
          len(hit) == 1 and int(hit[0]["n_features"]) == 2,
          "rows=%d" % len(hit))
    check("06b collision_report_lists_every_colliding_feature",
          hit and "ENSG00000000001.7" in hit[0]["feature_ids"]
          and "ENSG00000000044.2" in hit[0]["feature_ids"])
    check("06c collision_count_is_nonzero_in_provenance",
          prov["counts"]["collisions_symbol"] >= 1,
          "n=%d" % prov["counts"]["collisions_symbol"])


def t07_deprecated_symbol(tmp):
    """PLANTED: registry carries a deprecated symbol; assay carries current."""
    reg = [[0, "HGNC:5", "source_native_anchored", "OLDNAME",
            "protein_coding"]]
    feats = [("ENSG00000000777.4", "NEWNAME")]
    counts = [[2, 0, 1, 0]]
    hg = [["HGNC:5", "NEWNAME", "", "Approved", "protein-coding gene",
           "OLDNAME", ""]]
    genes = [("ENSG00000000777", "NEWNAME", "1", 1000, 2000, "+",
              "protein_coding", "4")]
    p = build_fixture(os.path.join(tmp, "t07"), reg, feats, counts,
                      gtf_genes=genes, hgnc_rows=hg)
    out = os.path.join(tmp, "t07_out")
    run_build(p, out)
    r = read_rows(out)[0]
    check("07 deprecated_symbol_resolves_via_hgnc_alias_route",
          r["rna_map_route"] == "deprecated_alias_symbol",
          "route=%s" % r["rna_map_route"])
    check("07b deprecated_symbol_is_not_left_UNMEASURED",
          r["rna_state"] != X.ST_UNMEASURED, "state=%s" % r["rna_state"])


def t08_missing_is_not_zero(tmp):
    """PLANTED: missing-vs-zero confusion.

    BBB is present in the assay and observed zero. GHOST is absent entirely.
    They must land in DIFFERENT states, and GHOST must carry no count.
    """
    reg = [r[:] for r in BASE_REGISTRY]
    reg.append([3, "ENSG00000099999", "current_exact", "GHOST",
                "protein_coding"])
    p = build_fixture(os.path.join(tmp, "t08"), reg, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t08_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    bbb, ghost = rows["ENSG00000000002"], rows["ENSG00000099999"]
    check("08 measured_zero_is_MEASURED_BUT_UNDETECTED",
          bbb["rna_state"] == X.ST_UNDETECTED
          and bbb["rna_nnz_cells_all"] == "0",
          "BBB=%s nnz=%r" % (bbb["rna_state"], bbb["rna_nnz_cells_all"]))
    check("08b absent_feature_is_UNMEASURED_with_empty_count",
          ghost["rna_state"] == X.ST_UNMEASURED
          and ghost["rna_nnz_cells_all"] == "")
    check("08c missing_and_zero_are_never_the_same_state",
          bbb["rna_state"] != ghost["rna_state"])


def t09_microglia_missing_is_not_zero(tmp):
    """PLANTED: a gene detected overall but zero in microglia, vs absent."""
    # CCC has counts only in odd (ODC) cells -> zero in MG.
    counts = [[1, 0, 2, 0], [0, 0, 0, 0], [0, 4, 0, 6]]
    reg = [r[:] for r in BASE_REGISTRY]
    reg.append([3, "ENSG00000099999", "current_exact", "GHOST",
                "protein_coding"])
    p = build_fixture(os.path.join(tmp, "t09"), reg, BASE_FEATURES, counts)
    out = os.path.join(tmp, "t09_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    ccc, ghost = rows["ENSG00000000003"], rows["ENSG00000099999"]
    check("09 microglia_zero_is_MEASURED_BUT_UNDETECTED",
          ccc["rna_state"] == X.ST_DETECTED
          and ccc["rna_microglia_state"] == X.ST_UNDETECTED
          and ccc["rna_nnz_cells_microglia"] == "0",
          "all=%s mg=%s" % (ccc["rna_state"], ccc["rna_microglia_state"]))
    check("09b microglia_absent_feature_stays_UNMEASURED",
          ghost["rna_microglia_state"] == X.ST_UNMEASURED
          and ghost["rna_nnz_cells_microglia"] == "")


def t10_duplicated_address(tmp):
    """PLANTED: the same canonical address twice."""
    reg = [r[:] for r in BASE_REGISTRY]
    reg.append([3, "ENSG00000000002", "current_exact", "BBB",
                "protein_coding"])
    p = build_fixture(os.path.join(tmp, "t10"), reg, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t10_out")
    raised = False
    try:
        run_build(p, out)
    except SystemExit as e:
        raised = "closed bijection" in str(e)
    check("10 duplicated_address_is_rejected", raised)


def t11_duplicated_index(tmp):
    """PLANTED: a repeated molecular_address_index (row identity broken)."""
    reg = [r[:] for r in BASE_REGISTRY]
    reg.append([2, "ENSG00000000004", "current_exact", "DDD",
                "protein_coding"])
    p = build_fixture(os.path.join(tmp, "t11"), reg, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t11_out")
    raised = False
    try:
        run_build(p, out)
    except SystemExit as e:
        raised = "closed bijection" in str(e)
    check("11 duplicated_address_index_is_rejected", raised)


def t12_par_y_ambiguity(tmp):
    """PLANTED: a PAR_Y copy sharing a stable ID with its X copy."""
    feats = BASE_FEATURES + [("ENSG00000000001.7_PAR_Y", "AAA_PARY")]
    counts = [r[:] for r in BASE_COUNTS] + [[1, 1, 0, 0]]
    p = build_fixture(os.path.join(tmp, "t12"), BASE_REGISTRY, feats, counts)
    out = os.path.join(tmp, "t12_out")
    prov = run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    a = rows["ENSG00000000001"]
    check("12 par_y_duplicate_is_AMBIGUOUSLY_MAPPED",
          a["rna_state"] == X.ST_AMBIGUOUS and a["rna_n_features_mapped"]
          == "2", "state=%s n=%s" % (a["rna_state"],
                                     a["rna_n_features_mapped"]))
    check("12b par_y_ambiguity_carries_no_fabricated_count",
          a["rna_nnz_cells_all"] == "")
    amb = os.path.join(out, "agent2_ambiguous_address_report_v1.csv")
    with open(amb, newline="", encoding="utf-8") as fh:
        arows = list(csv.DictReader(fh))
    check("12c par_y_reason_is_recorded",
          any(r["reason"] == "par_y_x_copy_pair" for r in arows),
          "n_amb=%d" % len(arows))
    check("12d par_y_counted_in_provenance",
          prov["counts"]["morabito_rna_par_y_features"] == 1)


def t13_decoy_manifest_rejected(tmp):
    """Fail-closed: the known decoy block manifest must be refused."""
    p = build_fixture(os.path.join(tmp, "t13"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    with open(p["block_manifest"], "wb") as fh:
        fh.write(b"x" * X.DECOY_MANIFEST_BYTES)
    out = os.path.join(tmp, "t13_out")
    raised = False
    try:
        X.build(p, out, enforce_digests=False)
    except SystemExit as e:
        raised = "decoy" in str(e).lower()
    check("13 decoy_block_manifest_is_rejected", raised)


def t14_state_partition_is_total(tmp):
    """Every address lands in exactly one state of every state column."""
    p = build_fixture(os.path.join(tmp, "t14"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t14_out")
    prov = run_build(p, out)
    n = prov["counts"]["n_canonical_addresses"]
    bad = [k for k, v in prov["state_counts"].items() if sum(v.values()) != n]
    check("14 every_state_column_partitions_all_addresses",
          not bad, "bad=%s" % bad)


def t15_unresolvable_geometry_is_UNKNOWN(tmp):
    """A gene on a contig with no assayed peaks must be UNKNOWN, not zero."""
    genes = [("ENSG00000000001", "AAA", "KI270728.1", 1000, 2000, "+",
              "protein_coding", "7"),
             ("ENSG00000000002", "BBB", "1", 9000, 9500, "+",
              "protein_coding", "3"),
             ("ENSG00000000003", "CCC", "1", 20000, 21000, "+",
              "protein_coding", "9")]
    p = build_fixture(os.path.join(tmp, "t15"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS, gtf_genes=genes)
    out = os.path.join(tmp, "t15_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    a = rows["ENSG00000000001"]
    check("15 unassayed_contig_is_UNKNOWN_not_zero",
          a["annotation_regulatory_state"] == X.ST_UNKNOWN
          and a["n_peaks_promoter_window"] == "",
          "state=%s" % a["annotation_regulatory_state"])


def t16_promoter_overlap_is_real(tmp):
    """The interval detector must fire on a true overlap and not otherwise."""
    p = build_fixture(os.path.join(tmp, "t16"), BASE_REGISTRY, BASE_FEATURES,
                      BASE_COUNTS)
    out = os.path.join(tmp, "t16_out")
    run_build(p, out)
    rows = {r["molecular_address_id"]: r for r in read_rows(out)}
    # AAA TSS=999 (0-based start of 1000); peak chr1:900-3000 overlaps.
    a = rows["ENSG00000000001"]
    c = rows["ENSG00000000003"]
    check("16 true_promoter_overlap_is_detected",
          a["annotation_regulatory_state"] == "PROMOTER_SUPPORTED",
          "AAA=%s" % a["annotation_regulatory_state"])
    check("16b distant_gene_is_not_called_promoter_supported",
          c["annotation_regulatory_state"] != "PROMOTER_SUPPORTED",
          "CCC=%s" % c["annotation_regulatory_state"])


def t17_interval_search_unit(tmp):
    """Unit check on the overlap primitive itself, including boundaries."""
    packed, unparsed = X.build_peak_index(
        ["chr1:100-200", "chr1:150-400", "chr1:1000-1100", "bad_peak"])
    check("17 unparseable_peak_id_is_reported_not_dropped_silently",
          unparsed == ["bad_peak"], "unparsed=%s" % unparsed)
    a = X.peaks_in_window(packed, "chr1", 120, 160)
    check("17b overlap_returns_all_overlapping_peaks",
          sorted(a.tolist()) == [0, 1], "got=%s" % sorted(a.tolist()))
    b = X.peaks_in_window(packed, "chr1", 500, 900)
    check("17c non_overlapping_window_returns_empty",
          b.size == 0, "got=%s" % b.tolist())
    c = X.peaks_in_window(packed, "chr1", 200, 260)
    check("17d half_open_boundary_excludes_touching_peak",
          sorted(c.tolist()) == [1], "got=%s" % sorted(c.tolist()))
    d = X.peaks_in_window(packed, "chrZ", 0, 10**9)
    check("17e unknown_contig_returns_empty", d.size == 0)


def t18_par_y_parser_unit(tmp):
    check("18 par_y_parser_strips_suffix_to_stable_id",
          X.parse_assay_feature_id("ENSG00000182378.13_PAR_Y")
          == ("ENSG00000182378", "13", True))
    check("18b plain_id_is_not_flagged_par_y",
          X.parse_assay_feature_id("ENSG00000182378.13")
          == ("ENSG00000182378", "13", False))


def main():
    tmp = tempfile.mkdtemp(prefix="agent2_tests_")
    try:
        for fn in (t01_positive_control, t02_registry_digest_enforced,
                   t03_unmapped_identifier, t04_version_suffix_handled,
                   t05_version_disagreement_reported, t06_symbol_collision,
                   t07_deprecated_symbol, t08_missing_is_not_zero,
                   t09_microglia_missing_is_not_zero, t10_duplicated_address,
                   t11_duplicated_index, t12_par_y_ambiguity,
                   t13_decoy_manifest_rejected, t14_state_partition_is_total,
                   t15_unresolvable_geometry_is_UNKNOWN,
                   t16_promoter_overlap_is_real, t17_interval_search_unit,
                   t18_par_y_parser_unit):
            try:
                fn(tmp)
            except Exception:
                traceback.print_exc()
                check("%s RAISED" % fn.__name__, False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_pass = sum(1 for _, ok, _ in RESULTS if ok)
    n = len(RESULTS)
    print("\n%d/%d checks passed across %d adversarial scenarios"
          % (n_pass, n, 18))
    report = {"checks_total": n, "checks_passed": n_pass,
              "scenarios": 18,
              "results": [{"name": a, "passed": b, "detail": c}
                          for a, b, c in RESULTS]}
    out = os.environ.get("AGENT2_TEST_REPORT")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    return 0 if n_pass == n else 1


if __name__ == "__main__":
    sys.exit(main())
