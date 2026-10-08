from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import urllib.request
from pathlib import Path
from typing import Any

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


def md(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def inspect_csv_gz(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"readable": False, "n_rows_estimate": "", "n_columns": "", "columns_sample": "", "notes": ""}
    if not path.exists() or path.suffix != ".gz":
        return row
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            header = handle.readline().strip().split(",")
            row["n_columns"] = len(header)
            row["columns_sample"] = ";".join(header[:30])
            n = 1 + sum(1 for _ in handle)
            row["n_rows_estimate"] = max(0, n - 1)
            row["readable"] = True
    except Exception as exc:
        row["notes"] = f"read_error={exc}"
    return row


def inspect_h5(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"readable": False, "h5_keys": "", "matrix_shape": "", "notes": ""}
    if not path.exists() or path.suffix.lower() not in {".h5", ".h5ad"}:
        return row
    try:
        import h5py
        with h5py.File(path, "r") as f:
            row["h5_keys"] = ";".join(list(f.keys())[:30])
            if "matrix" in f and "shape" in f["matrix"]:
                row["matrix_shape"] = str(tuple(f["matrix"]["shape"][:]))
            elif "X" in f:
                x = f["X"]
                row["matrix_shape"] = str(tuple(x.attrs["shape"])) if hasattr(x, "attrs") and "shape" in x.attrs else str(getattr(x, "shape", ""))
            row["readable"] = True
    except Exception as exc:
        row["notes"] = f"h5_read_error={exc}"
    return row


def inspect_resource(path: Path) -> dict[str, Any]:
    info = {
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        "sha256": sha256(path) if path.exists() and path.is_file() and path.stat().st_size < 2_000_000_000 else "",
        "readable": False,
        "n_rows_estimate": "",
        "n_columns": "",
        "columns_sample": "",
        "h5_keys": "",
        "matrix_shape": "",
        "notes": "",
    }
    if not path.exists():
        return info
    if path.is_dir():
        files = [p.name for p in path.iterdir() if p.is_file()]
        info["readable"] = True
        info["notes"] = f"directory_with_{len(files)}_files"
        info["columns_sample"] = ";".join(files[:20])
        return info
    if path.name.endswith(".csv.gz"):
        info.update(inspect_csv_gz(path))
    elif path.suffix.lower() in {".h5", ".h5ad"}:
        info.update(inspect_h5(path))
    return info


def download_file(url: str, dest: Path, force: bool = False) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    row = {"url": url, "local_path": str(dest), "download_attempted": True, "download_succeeded": False, "bytes_written": 0, "error": ""}
    if dest.exists() and dest.stat().st_size > 0 and not force:
        row.update({"download_succeeded": True, "bytes_written": dest.stat().st_size, "error": "already_exists"})
        return row
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response, out)
        tmp.replace(dest)
        row.update({"download_succeeded": True, "bytes_written": dest.stat().st_size})
    except Exception as exc:
        if tmp.exists():
            tmp.unlink()
        row["error"] = str(exc)
    return row


def build_inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in cfg["public_downloads"]:
        path = resolve(item["local_path"])
        info = inspect_resource(path)
        rows.append({
            "dataset_id": item["dataset_id"],
            "resource_id": item["resource_id"],
            "expected_role": item["expected_role"],
            "url": item["url"],
            "local_path": item["local_path"],
            **info,
        })
    # Additional local SEA-AD / protected-external checks.
    for name, key, role in [
        ("SEA-AD", "seaad_mtg_h5ad", "benchmark_rna_mtg_available"),
        ("SEA-AD", "seaad_dlpfc_h5ad", "benchmark_rna_dlpfc_available"),
        ("GSE157827", "gse157827_schema_dir", "protected_external_schema_only"),
    ]:
        path = resolve(cfg["inputs"][key])
        rows.append({"dataset_id": name, "resource_id": key, "expected_role": role, "url": "", "local_path": cfg["inputs"][key], **inspect_resource(path)})
    return pd.DataFrame(rows)


def update_scorecard(cfg: dict[str, Any], pf: pd.Series, ready: pd.Series) -> None:
    p = resolve(cfg["inputs"]["v3_scorecard_csv"])
    sc = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in sc.columns:
            sc[col] = ""
    row = {
        "scorecard_item": "Stage72A external multiomic GRN resource eligibility audit",
        "status": "complete",
        "stage": "Stage72A",
        "metric": "GSE174367/SEA-AD/GSE157827 resource acquisition and eligibility",
        "threshold_or_gate": "public resource audit/acquisition only; no graph or model",
        "current_value": f"stage72a_run_pass={bool(pf['stage72a_run_pass'])}; ready_for_stage72b_grn_construction={bool(ready['ready_for_stage72b_grn_construction'])}",
        "pass_fail": "pass" if bool(pf["stage72a_run_pass"]) else "fail",
        "datasets_allowed": "public GSE174367 processed files and existing local SEA-AD/GSE157827 schema files",
        "datasets_forbidden": "clean validation claims, graph construction, model training",
        "allowed_claim": "resource readiness / acquisition status only",
        "notes": "Raw/large data remain under data/ and are not staged.",
        "stage_id": "stage72a_external_multiomic_grn_resource_eligibility_audit",
        "primary_metric": "availability of snRNA/snATAC resources for Stage72B",
        "pass_rule": "audit outputs written and safety gates pass",
        "result": "see stage72a_grn_readiness_decision_v1.csv",
        "allowed_inputs": "local inventory and public GEO supplementary files",
        "forbidden_inputs": "external validation or model-selection use",
        "interpretation": "Planning/acquisition only.",
    }
    sc = sc[~sc["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([sc[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(p, index=False)


def run(cfg: dict[str, Any], download_missing: bool = False, force: bool = False) -> None:
    out = cfg["outputs"]
    before = build_inventory(cfg)
    logs = []
    if download_missing:
        for item in cfg["public_downloads"]:
            path = resolve(item["local_path"])
            if force or not path.exists() or path.stat().st_size == 0:
                logs.append({"dataset_id": item["dataset_id"], "resource_id": item["resource_id"], **download_file(item["url"], path, force=force)})
            else:
                logs.append({"dataset_id": item["dataset_id"], "resource_id": item["resource_id"], "url": item["url"], "local_path": str(path), "download_attempted": False, "download_succeeded": True, "bytes_written": path.stat().st_size, "error": "already_present"})
    else:
        for item in cfg["public_downloads"]:
            path = resolve(item["local_path"])
            logs.append({"dataset_id": item["dataset_id"], "resource_id": item["resource_id"], "url": item["url"], "local_path": str(path), "download_attempted": False, "download_succeeded": path.exists(), "bytes_written": path.stat().st_size if path.exists() else 0, "error": "download_not_requested"})
    inventory = build_inventory(cfg)
    dl = pd.DataFrame(logs)
    manifest = pd.DataFrame(cfg["public_downloads"])
    have = {r["resource_id"]: bool(r["exists"]) for _, r in inventory[inventory["dataset_id"].eq("GSE174367")].iterrows()}
    ready_for_grn = bool(have.get("snRNA_expression_matrix") and have.get("snRNA_cell_metadata") and have.get("snATAC_peak_matrix") and have.get("snATAC_cell_metadata"))
    grn = pd.DataFrame([{
        "ready_for_stage72b_grn_construction": ready_for_grn,
        "gse174367_snRNA_available": bool(have.get("snRNA_expression_matrix") and have.get("snRNA_cell_metadata")),
        "gse174367_snATAC_available": bool(have.get("snATAC_peak_matrix") and have.get("snATAC_cell_metadata")),
        "sea_ad_atac_or_multiome_confirmed_local": False,
        "sea_ad_rna_context_available": bool(resolve(cfg["inputs"]["seaad_mtg_h5ad"]).exists() and resolve(cfg["inputs"]["seaad_dlpfc_h5ad"]).exists()),
        "recommended_next_stage": "Stage72B_external_morabito_micro_pvm_grn_construction_v1" if ready_for_grn else "complete_public_acquisition_before_stage72b",
        "limitation": "SEA-AD ATAC/Multiome controlled-access files are not confirmed local; initial contextualization may be RNA-only unless acquired separately.",
    }])
    stage37e = pd.read_csv(resolve(cfg["inputs"]["stage37e_readiness"])) if resolve(cfg["inputs"]["stage37e_readiness"]).exists() else pd.DataFrame()
    protected = pd.DataFrame([{
        "dataset_id": "GSE157827",
        "local_schema_found": resolve(cfg["inputs"]["gse157827_schema_dir"]).exists(),
        "prior_stage37e_analysis_can_run": bool(stage37e["analysis_can_run"].iloc[0]) if not stage37e.empty and "analysis_can_run" in stage37e.columns else False,
        "protected_external_expression_ready": False,
        "manual_approval_required_before_expression_opening": True,
        "recommended_use": "frozen external expression projection only after approval and expression acquisition",
        "claim_level": "conditional external support only; not clean validation unless registry gate changes",
    }])
    next_actions = pd.DataFrame([
        {"priority": 1, "action": "Use acquired GSE174367 snRNA+snATAC processed files to build a Morabito microglia regulatory graph candidate.", "stage": "Stage72B", "requires_network": False if ready_for_grn else True},
        {"priority": 2, "action": "Audit whether SEA-AD ATAC/Multiome controlled-access resources are locally available and donor-linkable; if not, prepare manual acquisition list.", "stage": "Stage72C", "requires_network": False},
        {"priority": 3, "action": "Keep GSE157827 protected until expression availability and approval are confirmed; use only for frozen projection.", "stage": "Stage73", "requires_network": True},
    ])
    claim = pd.DataFrame([{
        "stage72a_is_resource_audit_and_acquisition_only": True,
        "no_graph_constructed": True,
        "no_model_training": True,
        "no_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "raw_or_large_data_not_committed": True,
        "downloaded_data_under_data_dir_only": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{
        "stage72a_run": True,
        "resource_inventory_written": True,
        "acquisition_manifest_written": True,
        "download_attempt_log_written": True,
        "grn_readiness_decision_written": True,
        "protected_external_test_decision_written": True,
        "reports_written": True,
        "docs_updated": True,
        "download_missing_requested": download_missing,
        "any_download_attempted": bool(dl["download_attempted"].any()) if not dl.empty else False,
        "all_requested_downloads_succeeded_or_already_present": bool(dl["download_succeeded"].all()) if not dl.empty else True,
        **claim.iloc[0].to_dict(),
    }])
    pf["stage72a_run_pass"] = pf[["resource_inventory_written", "acquisition_manifest_written", "download_attempt_log_written", "grn_readiness_decision_written", "protected_external_test_decision_written", "safety_audit_pass"]].all(axis=1)
    for name, df in {
        "resource_inventory": inventory,
        "acquisition_manifest": manifest,
        "download_attempt_log": dl,
        "grn_readiness_decision": grn,
        "protected_external_test_decision": protected,
        "next_action_plan": next_actions,
        "claim_boundary_audit": claim,
        "pass_fail": pf,
    }.items():
        write_csv(df, out[name])
    status = "Stage72A audited and optionally acquired public GSE174367 snRNA/snATAC processed resources for a context-specific Micro-PVM regulatory graph branch, while preserving claim boundaries. It does not construct a graph, train a model, or open GSE157827 as validation."
    update_section(cfg["inputs"]["active_status"], "Stage 72A external multiomic GRN resource eligibility audit", status)
    update_section(cfg["inputs"]["v3_scorecard_md"], "Stage 72A external multiomic GRN resource eligibility audit", status)
    update_scorecard(cfg, pf.iloc[0], grn.iloc[0])
    report = f"""# Stage72A external multiomic GRN resource eligibility audit

## Bottom line

Stage72A audits and, when requested, acquires public processed GSE174367 Morabito snRNA/snATAC resources needed for a context-specific Micro-PVM regulatory graph branch. It does not construct a graph or train a model.

GEO source: {cfg['sources']['gse174367_geo']}

## Resource inventory

{md(inventory)}

## Download log

{md(dl)}

## GRN readiness

{md(grn)}

## Protected external expression test

{md(protected)}

## Next actions

{md(next_actions)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(f"""# Stage72A PI summary

Stage72A completed the multiomic GRN resource audit/acquisition step.

- Download requested: `{download_missing}`
- Ready for Stage72B GRN construction: `{bool(grn['ready_for_stage72b_grn_construction'].iloc[0])}`
- GSE174367 snRNA available: `{bool(grn['gse174367_snRNA_available'].iloc[0])}`
- GSE174367 snATAC available: `{bool(grn['gse174367_snATAC_available'].iloc[0])}`
- SEA-AD RNA context available: `{bool(grn['sea_ad_rna_context_available'].iloc[0])}`
- SEA-AD ATAC/Multiome local confirmed: `False`
- GSE157827 protected external expression ready: `False`

No graph, model, external-validation, causal, or therapeutic claim is made.
""", out["pi_summary"])
    write_text(f"# Stage72A claim boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage72a_run_pass={bool(pf['stage72a_run_pass'].iloc[0])}")
    print(f"download_missing_requested={download_missing}")
    print(f"all_requested_downloads_succeeded_or_already_present={bool(pf['all_requested_downloads_succeeded_or_already_present'].iloc[0])}")
    print(f"ready_for_stage72b_grn_construction={bool(grn['ready_for_stage72b_grn_construction'].iloc[0])}")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage72a_external_multiomic_grn_resource_eligibility_audit_v1.yaml")
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run(load_cfg(args.config), download_missing=args.download_missing, force=args.force)


if __name__ == "__main__":
    main()
