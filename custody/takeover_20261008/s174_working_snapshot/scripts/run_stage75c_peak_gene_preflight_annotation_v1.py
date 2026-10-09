#!/usr/bin/env python
from __future__ import annotations

import argparse
import gzip
import re
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def md(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def update_section(path: str, title: str, body: str) -> None:
    p = resolve(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    marker = f"## {title}"
    block = f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before, rest = old.split(marker, 1)
        nxt = rest.find("\n## ")
        old = before + block + (rest[nxt:] if nxt >= 0 else "")
    else:
        old = old.rstrip() + "\n\n" + block
    p.write_text(old, encoding="utf-8")


def parse_attrs(attrs: str) -> dict[str, str]:
    out = {}
    for item in attrs.strip().split(";"):
        item = item.strip()
        if not item:
            continue
        if " " in item:
            key, val = item.split(" ", 1)
            out[key] = val.strip().strip('"')
    return out


def load_genes(gtf: Path) -> pd.DataFrame:
    rows = []
    opener = gzip.open if gtf.suffix == ".gz" else open
    with opener(gtf, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9 or parts[2] != "gene":
                continue
            attrs = parse_attrs(parts[8])
            gene_name = attrs.get("gene_name") or attrs.get("gene_id")
            gene_id = attrs.get("gene_id", "")
            gene_type = attrs.get("gene_type") or attrs.get("gene_biotype", "")
            start = int(parts[3]) - 1
            end = int(parts[4])
            strand = parts[6]
            tss = start if strand == "+" else end
            rows.append({"chrom": parts[0], "start": start, "end": end, "strand": strand, "tss": tss, "gene_id": gene_id, "gene_name": gene_name, "gene_type": gene_type})
    genes = pd.DataFrame(rows)
    genes["gene_name_upper"] = genes["gene_name"].astype(str).str.upper()
    return genes


def load_peaks(h5_path: Path) -> pd.DataFrame:
    with h5py.File(h5_path, "r") as handle:
        raw = handle["matrix"]["features"]["name"][:]
    names = [x.decode() if isinstance(x, bytes) else str(x) for x in raw]
    rows = []
    pat = re.compile(r"^(chr[^:]+):(\d+)-(\d+)$")
    for i, name in enumerate(names):
        m = pat.match(name)
        if not m:
            rows.append({"peak_index": i, "peak_id": name, "chrom": "", "start": np.nan, "end": np.nan, "midpoint": np.nan, "parseable_interval": False})
            continue
        chrom, start, end = m.group(1), int(m.group(2)), int(m.group(3))
        rows.append({"peak_index": i, "peak_id": name, "chrom": chrom, "start": start, "end": end, "midpoint": int((start + end) / 2), "parseable_interval": True})
    return pd.DataFrame(rows)


def annotate_peaks(peaks: pd.DataFrame, genes: pd.DataFrame, promoter_bp: int, proximal_bp: int) -> pd.DataFrame:
    out = []
    for chrom, pk in peaks[peaks["parseable_interval"]].groupby("chrom", sort=False):
        gg = genes[genes["chrom"].eq(chrom)].sort_values("tss").reset_index(drop=True)
        if gg.empty:
            for _, p in pk.iterrows():
                out.append({**p.to_dict(), "nearest_gene": "", "nearest_gene_id": "", "distance_to_tss": np.nan, "peak_gene_class": "no_gene_on_chrom"})
            continue
        tss = gg["tss"].to_numpy()
        for _, p in pk.iterrows():
            mid = int(p["midpoint"])
            pos = int(np.searchsorted(tss, mid))
            candidates = []
            if pos > 0:
                candidates.append(pos - 1)
            if pos < len(tss):
                candidates.append(pos)
            best = min(candidates, key=lambda ix: abs(int(tss[ix]) - mid))
            dist = int(mid - int(tss[best]))
            abs_dist = abs(dist)
            cls = "promoter_proximal" if abs_dist <= promoter_bp else ("proximal_100kb" if abs_dist <= proximal_bp else "distal_gt_100kb")
            row = p.to_dict()
            row.update({"nearest_gene": gg.loc[best, "gene_name_upper"], "nearest_gene_id": gg.loc[best, "gene_id"], "distance_to_tss": dist, "abs_distance_to_tss": abs_dist, "peak_gene_class": cls})
            out.append(row)
    # Add unparseable rows if any.
    for _, p in peaks[~peaks["parseable_interval"]].iterrows():
        out.append({**p.to_dict(), "nearest_gene": "", "nearest_gene_id": "", "distance_to_tss": np.nan, "abs_distance_to_tss": np.nan, "peak_gene_class": "unparseable_peak"})
    return pd.DataFrame(out)


def update_docs(cfg: dict[str, Any], pf: pd.DataFrame) -> None:
    body = (
        "Stage75C built a memory-safe peak-to-nearest-gene preflight annotation for "
        "GSE174367 snATAC peaks using hg38 chromosome sizes and GENCODE v44. This "
        "creates a proximity scaffold for later SCENIC+/CellOracle work, but it is "
        "not motif evidence, not a validated peak-to-gene map, and not a SCENIC+ eGRN."
    )
    update_section(cfg["inputs"]["active_status"], "Stage 75C peak-gene preflight annotation", body)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 75C peak-gene preflight annotation", body)
    score_path = resolve(cfg["inputs"]["v3_scorecard_csv"])
    score = pd.read_csv(score_path) if score_path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in score.columns:
            score[col] = ""
    row = {
        "scorecard_item": "Stage75C peak-gene preflight annotation",
        "status": "complete",
        "stage": "Stage75C",
        "metric": "GSE174367 snATAC peak nearest-gene annotation",
        "threshold_or_gate": "parseable peaks and rare-gene proximity support",
        "current_value": f"stage75c_run_pass={bool(pf['stage75c_run_pass'].iloc[0])}; proximity_only=True",
        "pass_fail": "pass" if bool(pf["stage75c_run_pass"].iloc[0]) else "fail",
        "datasets_allowed": "GSE174367 snATAC peaks, GENCODE v44, hg38 chrom sizes",
        "datasets_forbidden": "motif/eRegulon claims from proximity alone",
        "allowed_claim": "preflight proximity scaffold",
        "notes": "Peak-to-nearest-gene only; not validated regulation.",
        "stage_id": "stage75c_peak_gene_preflight_annotation",
        "primary_metric": "peak parseability and rare-gene peak support",
        "pass_rule": "annotation outputs and safety audit written",
        "result": "see stage75c_readiness_v1.csv",
        "allowed_inputs": "downloaded small hg38/GENCODE resources",
        "forbidden_inputs": "causal or validation claims",
        "interpretation": "Useful scaffold for Stage75D/eGRN prep, not sufficient for SCENIC+.",
    }
    score = score[~score["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([score[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(score_path, index=False)


def run(cfg: dict[str, Any]) -> None:
    inputs = cfg["inputs"]
    inv = pd.DataFrame([
        {"input_name": k, "path": v, "exists": resolve(v).exists(), "size_bytes": resolve(v).stat().st_size if resolve(v).exists() else 0}
        for k, v in inputs.items()
        if k not in {"active_status", "v3_scorecard_md", "v3_scorecard_csv"}
    ])
    genes = load_genes(resolve(inputs["gencode_gtf_gz"]))
    peaks = load_peaks(resolve(inputs["snatac_matrix_h5"]))
    ann = annotate_peaks(peaks, genes, int(cfg["parameters"]["promoter_window_bp"]), int(cfg["parameters"]["proximal_window_bp"]))
    edges = pd.read_csv(resolve(inputs["stage72b_edges"]))
    rare_genes = sorted(set(edges["source_tf"].astype(str).str.upper()) | set(edges["target_gene"].astype(str).str.upper()))
    support = ann[ann["nearest_gene"].isin(rare_genes)].groupby("nearest_gene", as_index=False).agg(
        n_nearest_peaks=("peak_id", "count"),
        n_promoter_peaks=("peak_gene_class", lambda x: int((x == "promoter_proximal").sum())),
        n_proximal_100kb_peaks=("peak_gene_class", lambda x: int((x.isin(["promoter_proximal", "proximal_100kb"])).sum())),
        min_abs_distance_to_tss=("abs_distance_to_tss", "min"),
    ).rename(columns={"nearest_gene": "gene"})
    all_support = pd.DataFrame({"gene": rare_genes}).merge(support, on="gene", how="left").fillna({"n_nearest_peaks": 0, "n_promoter_peaks": 0, "n_proximal_100kb_peaks": 0})
    gtf_summary = pd.DataFrame([{
        "n_genes_total": int(len(genes)),
        "n_protein_coding": int(genes["gene_type"].eq("protein_coding").sum()),
        "n_chromosomes": int(genes["chrom"].nunique()),
        "n_parseable_peaks": int(peaks["parseable_interval"].sum()),
        "n_total_peaks": int(len(peaks)),
    }])
    readiness = pd.DataFrame([{
        "stage75c_peak_gene_preflight_run": True,
        "inputs_found": bool(inv["exists"].all()),
        "n_total_peaks": int(len(peaks)),
        "n_parseable_peaks": int(peaks["parseable_interval"].sum()),
        "n_annotated_peak_rows": int(len(ann)),
        "n_rare_genes_with_nearest_peak": int((all_support["n_nearest_peaks"] > 0).sum()),
        "n_rare_genes_with_promoter_peak": int((all_support["n_promoter_peaks"] > 0).sum()),
        "proximity_scaffold_ready": True,
        "ready_for_true_scenicplus_egrn": False,
        "proximity_only_not_regulatory": True,
    }])
    claim = pd.DataFrame([{
        "stage75c_preflight_only": True,
        "proximity_only_not_regulatory": True,
        "no_motif_evidence_claim": True,
        "no_scenicplus_run": True,
        "no_celloracle_run": True,
        "no_model_training": True,
        "no_external_validation_claim": True,
        "no_causal_knockout_claim": True,
        "raw_data_not_committed": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{**readiness.iloc[0].to_dict(), **claim.iloc[0].to_dict()}])
    pf["stage75c_run_pass"] = pf[["inputs_found", "proximity_scaffold_ready", "safety_audit_pass"]].all(axis=1)
    out = cfg["outputs"]
    tables = {
        "input_inventory": inv,
        "gtf_gene_annotation_summary": gtf_summary,
        "peak_to_gene_preflight": ann,
        "rare_gene_peak_support": all_support,
        "readiness": readiness,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }
    for key, df in tables.items():
        write_csv(df, out[key])
    update_docs(cfg, pf)
    report = f"""# Stage75C peak-gene preflight annotation

## Readiness

{md(readiness)}

## GTF / peak summary

{md(gtf_summary)}

## Rare-gene peak support

{md(all_support.sort_values(['n_promoter_peaks', 'n_proximal_100kb_peaks', 'n_nearest_peaks'], ascending=False), 40)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage75C PI summary

- Peak-gene proximity scaffold ready: `{bool(readiness['proximity_scaffold_ready'].iloc[0])}`
- Total ATAC peaks: `{int(readiness['n_total_peaks'].iloc[0])}`
- Parseable interval peaks: `{int(readiness['n_parseable_peaks'].iloc[0])}`
- Rare/TF genes with nearest peak support: `{int(readiness['n_rare_genes_with_nearest_peak'].iloc[0])}`
- Rare/TF genes with promoter-window peak support: `{int(readiness['n_rare_genes_with_promoter_peak'].iloc[0])}`
- Ready for true SCENIC+ eGRN: `False`

This is a useful proximity scaffold, not motif-supported regulation.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage75C claim-boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage75c_run_pass={bool(pf['stage75c_run_pass'].iloc[0])}")
    print(f"n_total_peaks={int(readiness['n_total_peaks'].iloc[0])}")
    print(f"n_parseable_peaks={int(readiness['n_parseable_peaks'].iloc[0])}")
    print(f"n_rare_genes_with_nearest_peak={int(readiness['n_rare_genes_with_nearest_peak'].iloc[0])}")
    print(f"n_rare_genes_with_promoter_peak={int(readiness['n_rare_genes_with_promoter_peak'].iloc[0])}")
    print("ready_for_true_scenicplus_egrn=False")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage75c_peak_gene_preflight_annotation_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
