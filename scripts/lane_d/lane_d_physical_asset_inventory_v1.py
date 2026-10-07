#!/usr/bin/env python
"""LANE D scope A - physical asset inventory, authenticity, acquisition plan.

READ-ONLY. Covers every physical resource the GSE174367 / Stage75F chain
depends on: the GEO deposits, the GENCODE v44 annotation, the hg38 chromosome
definitions, the cisTarget motif-ranking databases and their vendor SHA-1
manifests, the motif-to-TF annotation table, and the execution container.

Before any download is proposed, duplicate local copies are searched for and
excluded, so the acquisition plan never asks for bytes that are already on
disk under another path.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone

import pandas as pd

# resource_id -> (relative path, class, vendor URL, digest algorithm, expected
# digest or None, where the expectation is recorded)
ASSETS = [
    ("gse174367_snrna_matrix",
     "data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5",
     "geo_primary",
     "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/"
     "GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5",
     "sha256", "6ba98a1af8772af08c8cdd5e5e63eebb0890daed48cac2e1b8961dcc67069b77",
     "stage72a_resource_inventory_v1.csv; stage38a_download_manifest_v1.csv"),
    ("gse174367_snrna_cell_meta",
     "data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz",
     "geo_primary",
     "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/"
     "GSE174367_snRNA-seq_cell_meta.csv.gz",
     "sha256", "ab1a029deb43196e2bb1fea5907d838885750cfff3850c600c07588c7c7cdb2b",
     "stage72a_resource_inventory_v1.csv; stage38a_download_manifest_v1.csv"),
    ("gse174367_snatac_matrix",
     "data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5",
     "geo_primary",
     "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/"
     "GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5",
     "sha256", "ff7c46e755ec0e3fecb319c5b3dd9ac0ada318525746ebe7dddb8e2c0dcab87f",
     "stage72a_resource_inventory_v1.csv"),
    ("gse174367_snatac_cell_meta",
     "data/external/gse174367/GSE174367_snATAC-seq_cell_meta.csv.gz",
     "geo_primary",
     "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/suppl/"
     "GSE174367_snATAC-seq_cell_meta.csv.gz",
     "sha256", "0657e92aa49eed953aae3b3c5f70aacebe86621c0a930356ec53ba0107c81767",
     "stage72a_resource_inventory_v1.csv"),
    ("gse174367_series_matrix",
     "data/external/public_schema_audit/GSE174367/GSE174367_series_matrix.txt.gz",
     "geo_metadata",
     "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174367/matrix/",
     "sha256", "e36488f44e30d0bdf48f5864b8cd091629203defecbb41d9e7fec721b5115928",
     "stage38a_download_manifest_v1.csv"),
    ("gencode_v44_gtf",
     "data/external_resources/stage75b/gencode.v44.annotation.gtf.gz",
     "annotation",
     "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/"
     "gencode.v44.annotation.gtf.gz",
     "sha256", None,
     "stage75b_acquisition_manifest_v1.csv records size 49721965 only"),
    ("hg38_chrom_sizes",
     "data/external_resources/stage75b/hg38.chrom.sizes",
     "annotation",
     "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes",
     "sha256", None,
     "stage75b_acquisition_manifest_v1.csv records size 11672 only"),
    ("cistarget_rankings",
     "data/external_resources/stage75b/"
     "hg38_screen_v10_clust.regions_vs_motifs.rankings.feather",
     "cistarget_database",
     "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/"
     "mc_v10_clust/region_based/"
     "hg38_screen_v10_clust.regions_vs_motifs.rankings.feather",
     "sha1", "1688a925f22d312769798258d990f13866bb4924",
     "vendor sha1sum.txt shipped by Aerts Lab alongside the database"),
    ("cistarget_scores",
     "data/external_resources/stage75b/"
     "hg38_screen_v10_clust.regions_vs_motifs.scores.feather",
     "cistarget_database",
     "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/"
     "mc_v10_clust/region_based/"
     "hg38_screen_v10_clust.regions_vs_motifs.scores.feather",
     "sha1", "07b5e527d2ed082e081e439e68dffa77b5f6129c",
     "vendor sha1sum.txt shipped by Aerts Lab alongside the database"),
    ("motif_annotation",
     "data/external_resources/stage75b/motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl",
     "motif_annotation",
     "https://resources.aertslab.org/cistarget/motif2tf/"
     "motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl",
     "sha256", None,
     "stage75e_input_inventory_v1.json records size 98718421 only"),
]

# Expensive assets whose digest must not be recomputed casually.
HEAVY = {"cistarget_rankings", "cistarget_scores"}


def digest(path, algo, chunk=1 << 22):
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def load_precomputed(path):
    out = {}
    if path and os.path.exists(path):
        for line in open(path):
            p = line.strip().split("|")
            if len(p) == 3:
                out[p[0].replace("\\", "/")] = p[2]
    return out


def find_duplicate_copies(root, basenames, search_roots):
    """Locate other copies of the same basenames on disk, before any download.

    Matching is by basename and byte size; a size match is then treated as a
    candidate duplicate whose digest can be checked cheaply if it is small.
    """
    found = {b: [] for b in basenames}
    for sr in search_roots:
        if not os.path.isdir(sr):
            continue
        for dirpath, dirnames, filenames in os.walk(sr):
            dirnames[:] = [d for d in dirnames
                           if d not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                if fn in found:
                    p = os.path.join(dirpath, fn)
                    try:
                        found[fn].append(dict(path=p.replace("\\", "/"),
                                              size_bytes=os.path.getsize(p)))
                    except OSError:
                        pass
    return found


def recover_environment(root):
    env = dict(execution_substrate="WSL2 + Docker on Windows",
               container_image=None, dockerfile=None,
               wsl_entrypoints=[], stage75f_scripts=[], python_runtime={})
    dfile = os.path.join(root, "docker", "scenicplus", "Dockerfile")
    if os.path.exists(dfile):
        env["dockerfile"] = "docker/scenicplus/Dockerfile"
        env["dockerfile_sha256"] = digest(dfile, "sha256")
        env["dockerfile_lines"] = open(dfile, errors="replace").read().splitlines()
    docs = os.path.join(root, "docs", "stage75f_f8_integrated_regulatory_evidence.md")
    if os.path.exists(docs):
        m = re.search(r"IMAGE=(\S+)", open(docs, errors="replace").read())
        if m:
            env["container_image"] = m.group(1)
    sdir = os.path.join(root, "scripts")
    if os.path.isdir(sdir):
        for fn in sorted(os.listdir(sdir)):
            p = os.path.join(sdir, fn)
            if not os.path.isfile(p):
                continue
            if fn.startswith("stage75") and fn.endswith(".sh"):
                env["wsl_entrypoints"].append(
                    dict(script="scripts/" + fn, sha256=digest(p, "sha256")))
            if fn.startswith("stage75f") and fn.endswith(".py"):
                env["stage75f_scripts"].append(
                    dict(script="scripts/" + fn, sha256=digest(p, "sha256")))
    for extra in ["scripts/run_stage75c_peak_gene_preflight_annotation_v1.py"]:
        p = os.path.join(root, extra)
        if os.path.exists(p):
            env["stage75f_scripts"].append(dict(script=extra,
                                                sha256=digest(p, "sha256")))
    try:
        import numpy
        import pandas as _pd
        import h5py as _h5
        import sys
        env["python_runtime"] = dict(python=sys.version.split()[0],
                                     numpy=numpy.__version__,
                                     pandas=_pd.__version__, h5py=_h5.__version__,
                                     note=("This is the LANE D audit runtime, which "
                                           "is NOT the Stage75F execution runtime; "
                                           "Stage75F ran inside the scenicplus "
                                           "container above."))
    except Exception as exc:  # pragma: no cover
        env["python_runtime"] = dict(error=str(exc))
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--precomputed-sha256", default=None)
    ap.add_argument("--precomputed-sha1", default=None)
    ap.add_argument("--duplicate-search-roots", default="")
    a = ap.parse_args()
    root, out = a.repo_root, a.out_dir
    os.makedirs(out, exist_ok=True)

    pre256 = load_precomputed(a.precomputed_sha256)
    pre1 = load_precomputed(a.precomputed_sha1)

    rows = []
    for rid, rel, cls, url, algo, expected, rec_src in ASSETS:
        p = os.path.join(root, rel)
        exists = os.path.exists(p)
        size = os.path.getsize(p) if exists else None
        obs = None
        if exists:
            pre = pre1 if algo == "sha1" else pre256
            obs = pre.get(rel)
            if obs is None and rid not in HEAVY:
                obs = digest(p, algo)
        if not exists:
            status, action = "ABSENT", "ACQUIRE"
        elif expected is None:
            status = "PRESENT_DIGEST_ESTABLISHED_HERE"
            action = ("NONE: vendor publishes no digest for this file; the digest "
                      "recorded by this lane becomes the local reference")
        elif obs is None:
            status, action = "PRESENT_DIGEST_NOT_COMPUTED", "VERIFY_DIGEST"
        elif obs == expected:
            status, action = "AUTHENTICATED", "NONE"
        else:
            status, action = "DIGEST_MISMATCH", "REACQUIRE"
        rows.append(dict(resource_id=rid, relative_path=rel, resource_class=cls,
                         exists_locally=bool(exists), size_bytes=size,
                         digest_algorithm=algo, expected_digest=expected,
                         observed_digest=obs, expectation_source=rec_src,
                         authenticity_status=status, required_action=action,
                         canonical_url=url))
    inv = pd.DataFrame(rows)
    inv.to_csv(os.path.join(out, "laneD_physical_asset_inventory_v1.csv"), index=False)

    search_roots = [s for s in a.duplicate_search_roots.split(";") if s]
    dupes = find_duplicate_copies(
        root, [os.path.basename(r[1]) for r in ASSETS], search_roots or [root])
    dup_rows = []
    for base, hits in dupes.items():
        canonical = [r for r in ASSETS if os.path.basename(r[1]) == base][0][1]
        canon_abs = os.path.join(root, canonical).replace("\\", "/")
        for h in hits:
            dup_rows.append(dict(basename=base, path=h["path"],
                                 size_bytes=h["size_bytes"],
                                 is_canonical_path=bool(
                                     os.path.normcase(h["path"]) ==
                                     os.path.normcase(canon_abs))))
    dup = pd.DataFrame(dup_rows)
    if len(dup):
        dup.to_csv(os.path.join(out, "laneD_duplicate_copy_scan_v1.csv"), index=False)

    # Acquisition plan: only what is genuinely absent AND has no duplicate copy.
    plan = []
    for r in inv.itertuples():
        if r.authenticity_status not in ("ABSENT", "DIGEST_MISMATCH"):
            continue
        base = os.path.basename(r.relative_path)
        alt = [d for d in dup_rows
               if d["basename"] == base and not d["is_canonical_path"]]
        plan.append(dict(
            resource_id=r.resource_id, relative_path=r.relative_path,
            reason=r.authenticity_status, canonical_url=r.canonical_url,
            duplicate_local_copies_found=len(alt),
            duplicate_paths="|".join(d["path"] for d in alt) or None,
            recommended_action=("COPY_FROM_LOCAL_DUPLICATE" if alt else "DOWNLOAD"),
            estimated_bytes=r.size_bytes))
    pd.DataFrame(plan).to_csv(
        os.path.join(out, "laneD_missing_resource_acquisition_plan_v1.csv"),
        index=False)

    env = recover_environment(root)
    manifest = dict(
        lane="LANE_D_external_multiomics", artifact="physical_asset_inventory",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        execution_class="RECONNAISSANCE_ONLY",
        biological_evaluation_status="NOT_EXECUTED",
        governance_footer=("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                           "PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | "
                           "RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF"),
        summary=dict(
            assets_total=int(len(inv)),
            authenticated=int((inv.authenticity_status == "AUTHENTICATED").sum()),
            digest_established_here=int(
                (inv.authenticity_status == "PRESENT_DIGEST_ESTABLISHED_HERE").sum()),
            digest_not_computed=int(
                (inv.authenticity_status == "PRESENT_DIGEST_NOT_COMPUTED").sum()),
            absent=int((inv.authenticity_status == "ABSENT").sum()),
            mismatched=int((inv.authenticity_status == "DIGEST_MISMATCH").sum()),
            total_bytes_on_disk=int(inv.size_bytes.fillna(0).sum()),
            downloads_required=int(sum(1 for p in plan
                                       if p["recommended_action"] == "DOWNLOAD"))),
        assets=json.loads(inv.to_json(orient="records")),
        duplicate_copy_scan=dict(
            search_roots=search_roots or [root],
            note=("Duplicate copies are searched for BEFORE any download is "
                  "proposed, so no acquisition asks for bytes already on disk."),
            hits=dup_rows),
        acquisition_plan=plan,
        environment=env)
    with open(os.path.join(out, "laneD_environment_and_asset_manifest_v1.json"),
              "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(json.dumps(manifest["summary"], indent=2))
    print(inv[["resource_id", "exists_locally", "size_bytes",
               "authenticity_status", "required_action"]].to_string())


if __name__ == "__main__":
    main()
