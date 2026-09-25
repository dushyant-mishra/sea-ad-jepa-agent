#!/usr/bin/env python3
"""GSE254205 GNE-317 drug-response ETL V2 — a BULK schema, deliberately not Perturb-seq.

Design recovered from the authenticated archive and series record:

    NT      rep1..3    untreated APOE4/4 iPSC-derived microglia
    AB      rep1..3    + fibrillar amyloid-beta
    AB_GNE  rep1..3    + fibrillar amyloid-beta + GNE-317

Bulk STAR ``ReadsPerGene`` counts over Ensembl gene IDs. Three replicates per
condition, one cell model, one timepoint. This is a **measured drug-induced
expression response**, not a compound annotation and not a computational
hypothesis.

Contrasts, each reported separately
-----------------------------------
* ``AB_vs_NT``      — what amyloid does
* ``AB_GNE_vs_AB``  — what the drug does *in the amyloid context* (the
  therapeutically relevant contrast)
* ``AB_GNE_vs_NT``  — net state versus untreated

They are not combined, and no rescue or reversal claim is computed here: showing
that a drug moves expression is not showing that it restores a healthy state, and
this ETL stops before that inference.

Replicates are preserved before aggregation, so every effect carries n and a
replicate-level standard error.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

CONDITIONS = {
    "NT": dict(amyloid=False, compound=None,
               description="untreated APOE4/4 iPSC-derived microglia"),
    "AB": dict(amyloid=True, compound=None,
               description="fibrillar amyloid-beta"),
    "AB_GNE": dict(amyloid=True, compound="GNE-317",
                   description="fibrillar amyloid-beta plus GNE-317"),
}
REPLICATES = ("rep1", "rep2", "rep3")
CONTRASTS = (("AB_vs_NT", "AB", "NT"),
             ("AB_GNE_vs_AB", "AB_GNE", "AB"),
             ("AB_GNE_vs_NT", "AB_GNE", "NT"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_counts(path: Path) -> tuple[list[str], np.ndarray]:
    genes, vals = [], []
    with path.open(encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        if header[:2] != ["Gene", "Counts"]:
            raise SystemExit(f"unexpected header in {path.name}: {header[:2]}")
        for line in fh:
            g, v = line.rstrip("\n").split("\t")[:2]
            genes.append(g)
            vals.append(int(v))
    a = np.asarray(vals, dtype=np.int64)
    if np.any(a < 0):
        raise SystemExit(f"negative count in {path.name}")
    return genes, a


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--counts-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.out_dir
    if out.exists() and any(out.iterdir()):
        raise SystemExit("V2 outputs require a NEW EMPTY directory; never overwrite V1 evidence")
    out.mkdir(parents=True, exist_ok=True)

    samples, mats, ref_genes = [], [], None
    for cond in CONDITIONS:
        for rep in REPLICATES:
            p = args.counts_dir / f"{cond}_{rep}ReadsPerGene.out.tab"
            if not p.is_file():
                raise SystemExit(f"missing sample file: {p.name}")
            genes, a = read_counts(p)
            if ref_genes is None:
                ref_genes = genes
            elif genes != ref_genes:
                raise SystemExit(f"{p.name} has a different gene order/universe")
            samples.append(dict(sample_id=f"{cond}_{rep}", condition=cond, replicate=rep,
                                amyloid=CONDITIONS[cond]["amyloid"],
                                compound=CONDITIONS[cond]["compound"] or "",
                                file=p.name, file_sha256=sha256_file(p),
                                total_counts=int(a.sum()),
                                genes_detected=int((a > 0).sum())))
            mats.append(a)
    X = np.vstack(mats)                      # 9 samples x genes
    n_genes = X.shape[1]
    if len(set(ref_genes)) != n_genes:
        raise SystemExit("duplicate Ensembl gene IDs in the count files")
    print(f"samples {X.shape[0]} | genes {n_genes:,} | "
          f"library sizes {X.sum(axis=1).min():,}..{X.sum(axis=1).max():,}", flush=True)

    with (out / "GSE254205_sample_identity_v2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(samples[0]))
        w.writeheader(); w.writerows(samples)

    # All reference-table genes were ASSAYED (present in all 9 STAR files).
    # Zero counts in every sample mean ASSAYED_BUT_UNDETECTED, not unmeasured.
    # The effect table retains the V1 detectable-anywhere analytical filter;
    # no earlier effect values/contrasts are silently changed.
    detected_any = X.sum(axis=0) > 0
    detected_samples = (X > 0).sum(axis=0)
    n_undetected = int((~detected_any).sum())
    print(f"assayed genes {n_genes:,}; detected in >=1 sample "
          f"{int(detected_any.sum()):,}; assayed but undetected {n_undetected:,}",
          flush=True)
    with (out / "GSE254205_feature_assay_status_v2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=[
            "gene_id", "assayed", "detected_anywhere", "n_samples_detected",
            "assay_status", "included_in_v1_compatible_effects",
        ])
        w.writeheader()
        for k, gene in enumerate(ref_genes):
            w.writerow({
                "gene_id": gene, "assayed": True,
                "detected_anywhere": bool(detected_any[k]),
                "n_samples_detected": int(detected_samples[k]),
                "assay_status": (
                    "ASSAYED_AND_DETECTED" if detected_any[k]
                    else "ASSAYED_BUT_UNDETECTED"
                ),
                "included_in_v1_compatible_effects": bool(detected_any[k]),
            })

    cpm = X / np.maximum(X.sum(axis=1, keepdims=True), 1) * 1e6
    lg = np.log2(cpm + 1.0)
    cond_of = np.array([s["condition"] for s in samples])

    rows = []
    for name, num, den in CONTRASTS:
        i = np.flatnonzero(cond_of == num)
        j = np.flatnonzero(cond_of == den)
        d = lg[i].mean(axis=0) - lg[j].mean(axis=0)
        # replicate-level SE of the difference of means
        se = np.sqrt(lg[i].var(axis=0, ddof=1) / len(i) + lg[j].var(axis=0, ddof=1) / len(j))
        for k in np.flatnonzero(detected_any):
            rows.append({
                "study": "GSE254205", "assay": "bulk_RNAseq",
                "system": "APOE4/4 iPSC-derived microglia",
                "contrast": name, "numerator_condition": num, "denominator_condition": den,
                "compound": CONDITIONS[num]["compound"] or "",
                "gene_id": ref_genes[k],
                "log2fc": round(float(d[k]), 6),
                "se": round(float(se[k]), 6),
                "n_numerator": int(len(i)), "n_denominator": int(len(j)),
                "measured": True,
                "assayed": True,
                "detected_anywhere": True,
                "effect_inclusion_rule": "DETECTED_ANYWHERE_ACROSS_NINE_SAMPLES",
            })
    with (out / "GSE254205_drug_response_effects_v2.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    per_contrast = {}
    for name, num, den in CONTRASTS:
        sub = [r for r in rows if r["contrast"] == name]
        fc = np.asarray([r["log2fc"] for r in sub])
        per_contrast[name] = {
            "genes_scored": len(sub),
            "median_log2fc": round(float(np.median(fc)), 4),
            "n_abs_gt_1": int((np.abs(fc) > 1).sum()),
            "n_abs_gt_2": int((np.abs(fc) > 2).sum()),
        }

    summary = {
        "schema": "GSE254205_BULK_DRUG_RESPONSE_V2",
        "study": "GSE254205",
        "assay": "bulk_RNAseq_STAR_ReadsPerGene",
        "system": "APOE4/4 iPSC-derived microglia",
        "compound": "GNE-317",
        "design": "3 conditions x 3 replicates; one cell model; one timepoint",
        "conditions": {k: v["description"] for k, v in CONDITIONS.items()},
        "samples": len(samples),
        "genes_in_annotation": n_genes,
        "genes_detected_anywhere": int(detected_any.sum()),
        "genes_assayed": n_genes,
        "genes_assayed_but_undetected": n_undetected,
        "genes_structurally_unmeasured_within_reference": 0,
        "genes_excluded_from_effects_by_detection_filter": n_undetected,
        "detection_filter": "DETECTED_ANYWHERE_ACROSS_NINE_SAMPLES",
        "v1_scientific_contrasts_preserved": True,
        "v1_result_replaced": False,
        "feature_namespace": "Ensembl gene ID",
        "contrasts": per_contrast,
        "replicates_preserved_before_aggregation": True,
        "measured_drug_induced_expression": True,
        "annotation_or_hypothesis_only": False,
        "rescue_or_reversal_claim_computed": False,
        "therapeutic_ranking": False,
        "jepa_prediction_used": False,
    }
    (out / "GSE254205_drug_response_summary_v2.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
