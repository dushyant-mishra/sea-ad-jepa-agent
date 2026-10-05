#!/usr/bin/env python3
"""Bulk disease-context ETL: GSE241858 (TREM2 R47H x cytokine) and GSE240609 (APOE3ch).

A third assay schema, separate from the single-cell CRISPR and the drug-treatment
pipelines. These are **genotype-by-context** experiments, not CRISPR perturbations,
and their effects keep that interpretation.

The experimental unit, which is where these designs are easiest to overstate
--------------------------------------------------------------------------
GSE241858 edited two independent iPSC **clones** per genotype (A and B) and then
took technical/passage replicates within each. The clone is the biological
replicate: there are **two per genotype**, not six. Effects are therefore
estimated with the clone as the unit, and the within-clone replicates are averaged
first rather than counted as independent.

GSE240609 is a 2x2 of neuron genotype (WT vs PSEN) by microglia genotype (APOE3 vs
APOE3-Christchurch) with **one sample per cell**. Differences are computable;
uncertainty is not. That is recorded rather than papered over with a within-sample
standard error that would describe sequencing noise, not biology.

Coculture, in GSE240609, is also not a cell-autonomous perturbation: the measured
material is a neuron-microglia coculture, so a difference between APOE3ch and
APOE3 conditions is a property of the coculture and is labelled as such.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path: Path) -> tuple[list[str], list[str], list[str], np.ndarray]:
    with gzip.open(path, "rt") as fh:
        sep = "\t"
        header = fh.readline().rstrip("\n")
        if "\t" not in header:
            sep = ","
        cols = header.split(sep)
        genes, syms, rows = [], [], []
        for line in fh:
            parts = line.rstrip("\n").split(sep)
            genes.append(parts[0])
            syms.append(parts[1])
            rows.append([float(x) for x in parts[2:]])
    X = np.asarray(rows, dtype=np.float64)
    if np.any(X < 0):
        raise SystemExit(f"{path.name}: negative count")
    return cols[2:], genes, syms, X.T    # samples x genes


def parse_241858(sample: str) -> dict:
    """CTRL_A_1 / R47H_B_2_IFN -> structured fields."""
    m = re.match(r"^(CTRL|R47H)_([AB])_(\d+)(?:_(UNTR|IFN|LPS))?$", sample)
    if not m:
        raise SystemExit(f"unparsed GSE241858 sample id: {sample}")
    g, clone, rep, treat = m.groups()
    return {"sample_id": sample, "genotype": g, "clone": f"{g}_{clone}",
            "replicate": int(rep), "treatment": treat or "BASELINE"}


def cpm_log(X: np.ndarray) -> np.ndarray:
    lib = np.maximum(X.sum(axis=1, keepdims=True), 1.0)
    return np.log2(X / lib * 1e6 + 1.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gse241858-baseline", type=Path, required=True)
    ap.add_argument("--gse241858-cytokine", type=Path, required=True)
    ap.add_argument("--gse240609-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    summary: dict = {"schema": "BULK_DISEASE_CONTEXT_EFFECTS_V1"}

    # ================= GSE241858 =================
    eff_rows, sample_rows = [], []
    for arm, path in (("baseline", args.gse241858_baseline),
                      ("cytokine", args.gse241858_cytokine)):
        samples, genes, syms, X = read_table(path)
        meta = [parse_241858(s) for s in samples]
        for m, tot in zip(meta, X.sum(axis=1)):
            sample_rows.append({"study": "GSE241858", "arm": arm, **m,
                                "total_counts": int(tot),
                                "file": path.name, "file_sha256": sha256_file(path)})
        lg = cpm_log(X)
        detected = X.sum(axis=0) > 0

        # Average within clone x treatment FIRST: replicates inside a clone are not
        # independent biology.
        key = [(m["clone"], m["treatment"]) for m in meta]
        uniq = sorted(set(key))
        C = np.vstack([lg[[i for i, k in enumerate(key) if k == u]].mean(axis=0)
                       for u in uniq])
        cmeta = [{"clone": c, "treatment": t,
                  "genotype": "R47H" if c.startswith("R47H") else "CTRL",
                  "n_within_clone_replicates": sum(1 for k in key if k == (c, t))}
                 for c, t in uniq]

        def contrast(name, num_fn, den_fn, note):
            i = [j for j, m in enumerate(cmeta) if num_fn(m)]
            j_ = [j for j, m in enumerate(cmeta) if den_fn(m)]
            if not i or not j_:
                return
            d = C[i].mean(axis=0) - C[j_].mean(axis=0)
            # clone-level SE; with two clones per genotype this is a 2-unit estimate
            se = (np.sqrt(C[i].var(axis=0, ddof=1) / len(i) + C[j_].var(axis=0, ddof=1) / len(j_))
                  if len(i) > 1 and len(j_) > 1 else np.full(d.shape, np.nan))
            for k in np.flatnonzero(detected):
                eff_rows.append({
                    "study": "GSE241858", "arm": arm, "assay": "bulk_RNAseq",
                    "system": "iPSC-derived microglia", "contrast": name,
                    # GSE241858 is a THIRD identifier namespace: ENTREZID plus SYMBOL.
                    # Both are carried; neither is silently dropped or resolved.
                    "gene_id_namespace": "ENTREZID",
                    "gene_id": genes[k], "gene_symbol": syms[k],
                    "log2fc": round(float(d[k]), 6),
                    "se_clone_level": "" if not np.isfinite(se[k]) else round(float(se[k]), 6),
                    "n_numerator_clone_units": len(i), "n_denominator_clone_units": len(j_),
                    "experimental_unit": "iPSC clone",
                    "note": note})

        if arm == "baseline":
            contrast("R47H_vs_CTRL_baseline",
                     lambda m: m["genotype"] == "R47H", lambda m: m["genotype"] == "CTRL",
                     "genotype effect at baseline; 2 clones per genotype")
        else:
            for t in ("IFN", "LPS"):
                contrast(f"{t}_vs_UNTR_in_CTRL",
                         lambda m, t=t: m["treatment"] == t and m["genotype"] == "CTRL",
                         lambda m: m["treatment"] == "UNTR" and m["genotype"] == "CTRL",
                         f"{t} stimulation response in control genotype")
                contrast(f"{t}_vs_UNTR_in_R47H",
                         lambda m, t=t: m["treatment"] == t and m["genotype"] == "R47H",
                         lambda m: m["treatment"] == "UNTR" and m["genotype"] == "R47H",
                         f"{t} stimulation response in R47H genotype")
            contrast("R47H_vs_CTRL_untreated",
                     lambda m: m["genotype"] == "R47H" and m["treatment"] == "UNTR",
                     lambda m: m["genotype"] == "CTRL" and m["treatment"] == "UNTR",
                     "genotype effect, untreated arm of the cytokine experiment")

        summary.setdefault("GSE241858", {})[arm] = {
            "samples": len(samples), "genes": len(genes),
            "genes_detected": int(detected.sum()),
            "clone_treatment_units": len(uniq),
            "clones_per_genotype": 2,
            "design_note": ("clone is the biological replicate; within-clone replicates "
                            "are averaged before contrast estimation"),
            "unbalanced": sorted({f"{c}:{t}:{n}" for (c, t), n in
                                  ((u, sum(1 for k in key if k == u)) for u in uniq)}),
        }

    with (out / "GSE241858_sample_identity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sample_rows[0]))
        w.writeheader(); w.writerows(sample_rows)
    with (out / "GSE241858_genotype_context_effects.csv").open("w", newline="",
                                                               encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(eff_rows[0]))
        w.writeheader(); w.writerows(eff_rows)

    # ================= GSE240609 =================
    files = sorted(args.gse240609_dir.glob("*gene_counts.txt.gz"))
    if not files:
        raise SystemExit("no GSE240609 count files found")
    g609, X609, meta609 = None, [], []
    for p in files:
        with gzip.open(p, "rt") as fh:
            first = fh.readline().rstrip("\n")
            sep = "\t" if "\t" in first else ","
            rows = [first] + fh.read().splitlines()
        gene, val = [], []
        start = 1 if not rows[0].split(sep)[-1].lstrip("-").replace(".", "").isdigit() else 0
        for line in rows[start:]:
            parts = line.split(sep)
            gene.append(parts[0])
            val.append(float(parts[-1]))
        if g609 is None:
            g609 = gene
        elif gene != g609:
            raise SystemExit(f"{p.name}: gene order differs; refusing to merge")
        X609.append(val)
        nm = p.name
        meta609.append({
            "study": "GSE240609", "file": nm, "file_sha256": sha256_file(p),
            "neuron_genotype": "PSEN" if "PSEN" in nm else "WT",
            "microglia_genotype": "APOE3ch" if "Church" in nm or "CHurch" in nm else "APOE3",
            "material": "neuron_microglia_coculture",
        })
    X609 = np.asarray(X609, dtype=np.float64)
    lg609 = cpm_log(X609)
    det609 = X609.sum(axis=0) > 0
    with (out / "GSE240609_sample_identity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(meta609[0]))
        w.writeheader(); w.writerows(meta609)

    cells = {(m["neuron_genotype"], m["microglia_genotype"]): i
             for i, m in enumerate(meta609)}
    rows609 = []
    for neuron in sorted({m["neuron_genotype"] for m in meta609}):
        a = cells.get((neuron, "APOE3ch"))
        b = cells.get((neuron, "APOE3"))
        if a is None or b is None:
            continue
        d = lg609[a] - lg609[b]
        for k in np.flatnonzero(det609):
            rows609.append({
                "study": "GSE240609", "assay": "bulk_RNAseq",
                "material": "neuron_microglia_coculture",
                "contrast": f"APOE3ch_vs_APOE3_microglia_in_{neuron}_neurons",
                "neuron_genotype": neuron,
                "gene_id_namespace": "SYMBOL", "gene_id": g609[k], "log2fc": round(float(d[k]), 6),
                "se": "", "n_numerator": 1, "n_denominator": 1,
                "uncertainty_estimable": False,
                "note": ("one sample per design cell: the difference is computable but no "
                         "uncertainty is estimable, and this is a coculture-level effect, "
                         "not a cell-autonomous microglial perturbation"),
            })
    if rows609:
        with (out / "GSE240609_coculture_effects.csv").open("w", newline="",
                                                            encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows609[0]))
            w.writeheader(); w.writerows(rows609)

    summary["GSE240609"] = {
        "samples": len(meta609), "genes": len(g609),
        "genes_detected": int(det609.sum()),
        "design": "2x2 neuron genotype (WT/PSEN) x microglia genotype (APOE3/APOE3ch)",
        "replicates_per_design_cell": 1,
        "uncertainty_estimable": False,
        "interpretation_limit": ("measured material is a neuron-microglia coculture; a "
                                 "genotype difference is a coculture-level effect and must "
                                 "not be read as cell-autonomous"),
        "contrast_rows": len(rows609),
    }
    summary["assay_schema"] = "bulk RNA-seq, genotype-by-context; NOT CRISPR perturbation"
    summary["jepa_prediction_used"] = False
    summary["therapeutic_ranking"] = False
    (out / "BULK_DISEASE_CONTEXT_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
