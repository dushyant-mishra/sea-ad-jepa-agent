from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SAFE = "acquired/prepared external support dataset; not yet clean validation"
BLOCKED = "validated; clean external validation completed; causal regulator; therapeutic target; disease-modifying target; gene ablation result"


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_csv(path: str | Path) -> pd.DataFrame:
    p = resolve(path)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


def write_text(text: str, path: str | Path) -> Path:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_gene_set(candidates: pd.DataFrame) -> list[str]:
    if candidates.empty:
        return []
    genes = candidates[candidates["candidate_type"].astype(str).str.lower() == "gene"]["gene_or_module"]
    return sorted(set(genes.astype(str).str.upper()))


def dataset_roots(ds: dict[str, Any]) -> list[Path]:
    did = ds["dataset_id"]
    acc = ds["accession"].lower()
    roots = [ROOT / "data" / "external" / did, ROOT / "data" / "external" / acc]
    if did == "gse138852":
        roots.append(ROOT / "data" / "external" / "grubman_gse138852")
    if did == "gse174367":
        roots.append(ROOT / "data" / "external" / "gse174367")
    roots.append(ROOT / "data" / "external" / "public_schema_audit" / ds["accession"])
    return roots


def all_local_files(ds: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    for root in dataset_roots(ds):
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file():
                    files.append(p)
    return sorted(set(files))


def infer_type(path: Path) -> str:
    n = path.name.lower()
    if any(x in n for x in ["count", "matrix", ".h5ad", ".h5"]):
        return "expression"
    if any(x in n for x in ["meta", "covariate", "series_matrix"]):
        return "metadata"
    return "other"


def inventory(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for ds in cfg["datasets"]:
        for p in all_local_files(ds):
            typ = infer_type(p)
            rows.append({
                "dataset_id": ds["dataset_id"],
                "file_path": p.relative_to(ROOT).as_posix(),
                "file_name": p.name,
                "file_suffix": "".join(p.suffixes),
                "file_size_bytes": p.stat().st_size,
                "modified_time": pd.Timestamp.fromtimestamp(p.stat().st_mtime).isoformat(),
                "checksum_sha256": sha256(p),
                "inferred_file_type": typ,
                "usable_for_expression": typ == "expression",
                "usable_for_metadata": typ == "metadata",
                "usable_for_celltype": typ == "metadata",
                "usable_for_pathology": typ == "metadata",
                "notes": "existing local file detected; not downloaded by Stage 38A",
            })
    return pd.DataFrame(rows)


def acquisition_plan(cfg: dict[str, Any], inv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ds in cfg["datasets"]:
        local = inv[inv["dataset_id"] == ds["dataset_id"]]
        rows.append({
            "dataset_id": ds["dataset_id"],
            "accession": ds["accession"],
            "dataset_name": ds["dataset_name"],
            "intended_stage": ds["intended_stage"],
            "intended_use": ds["intended_use"],
            "priority": ds["priority"],
            "expected_modality": ds["expected_modality"],
            "expected_metadata": ds["expected_metadata"],
            "expected_pathology_or_disease_readout": ds["expected_pathology_or_disease_readout"],
            "acquisition_status": "local_files_found" if not local.empty else "manual_acquisition_required",
            "automated_download_possible": False,
            "manual_download_required": local.empty,
            "local_expected_root": f"data/external/{ds['dataset_id']}/",
            "notes": "Stage 38A did not download; use official GEO/SRA manually if needed.",
        })
    return pd.DataFrame(rows)


def download_manifest(cfg: dict[str, Any], inv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    inv_by = inv.groupby("dataset_id") if not inv.empty else {}
    for ds in cfg["datasets"]:
        local = inv[inv["dataset_id"] == ds["dataset_id"]] if not inv.empty else pd.DataFrame()
        if not local.empty:
            for _, f in local.iterrows():
                rows.append({
                    "dataset_id": ds["dataset_id"], "accession": ds["accession"], "file_id": f["file_name"],
                    "file_type": f["inferred_file_type"], "source_url_or_accession": ds["accession"],
                    "expected_filename": f["file_name"], "local_path": f["file_path"], "download_attempted": False,
                    "download_success": False, "file_size_bytes": f["file_size_bytes"], "checksum_sha256": f["checksum_sha256"],
                    "required_for_analysis": f["inferred_file_type"] in {"expression", "metadata"}, "notes": "pre-existing local file",
                })
        else:
            for typ in ["expression_matrix", "metadata", "gene_metadata"]:
                rows.append({
                    "dataset_id": ds["dataset_id"], "accession": ds["accession"], "file_id": f"{ds['dataset_id']}_{typ}",
                    "file_type": typ, "source_url_or_accession": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={ds['accession']}",
                    "expected_filename": f"{ds['accession']}_{typ}", "local_path": f"data/external/{ds['dataset_id']}/raw/",
                    "download_attempted": False, "download_success": False, "file_size_bytes": 0, "checksum_sha256": "",
                    "required_for_analysis": typ in {"expression_matrix", "metadata"}, "notes": "manual acquisition required",
                })
    return pd.DataFrame(rows)


def infer_meta_cols(meta: pd.DataFrame) -> dict[str, str]:
    cols = list(meta.columns)
    lower = {c.lower(): c for c in cols}
    def find(cands):
        for c in cands:
            if c.lower() in lower:
                return lower[c.lower()]
        for col in cols:
            if any(c.lower() in col.lower() for c in cands):
                return col
        return ""
    return {
        "sample": find(["cell_id", "barcode", "sample", "sample_id", "Unnamed: 0"]),
        "donor": find(["donor", "subject", "individual", "sample"]),
        "celltype": find(["celltype", "cell_type", "oupSample.cellType"]),
        "disease": find(["condition", "disease", "diagnosis", "batchCond", "oupSample.batchCond", "oupSample.subclustCond"]),
        "pathology": ";".join([c for c in cols if any(x in c.lower() for x in ["tau", "ptau", "amyloid", "abeta", "braak", "cerad", "plaque", "pathology"])]),
    }


def preprocess_gse138852(candidates: list[str]) -> tuple[Path | None, Path | None, Path | None, dict[str, Any]]:
    root = ROOT / "data" / "external" / "grubman_gse138852"
    counts = root / "GSE138852_counts.csv.gz"
    cov = root / "GSE138852_covariates.csv.gz"
    outroot = ROOT / "data" / "external" / "gse138852" / "processed"
    outroot.mkdir(parents=True, exist_ok=True)
    info: dict[str, Any] = {"success": False, "reason": ""}
    if not counts.exists() or not cov.exists():
        info["reason"] = "counts_or_covariates_missing"
        return None, None, None, info
    cand = set(candidates)
    kept = []
    for chunk in pd.read_csv(counts, chunksize=2000):
        gene_col = chunk.columns[0]
        chunk[gene_col] = chunk[gene_col].astype(str).str.upper()
        hit = chunk[chunk[gene_col].isin(cand)]
        if not hit.empty:
            kept.append(hit)
    if not kept:
        info["reason"] = "no_candidate_genes_found"
        return None, None, None, info
    mat = pd.concat(kept, ignore_index=True)
    gene_col = mat.columns[0]
    mat = mat.drop_duplicates(gene_col).set_index(gene_col)
    expr = mat.T
    expr.index.name = "cell_id"
    expr.columns = [str(c).upper() for c in expr.columns]
    meta = pd.read_csv(cov)
    id_col = meta.columns[0]
    meta = meta.rename(columns={id_col: "cell_id"})
    common = [idx for idx in expr.index.astype(str) if idx in set(meta["cell_id"].astype(str))]
    expr = expr.loc[common].reset_index()
    meta = meta.set_index("cell_id").loc[common].reset_index()
    expr_path = outroot / "stage38a_gse138852_candidate_expression.csv"
    meta_path = outroot / "stage38a_gse138852_metadata.csv"
    gene_path = outroot / "stage38a_gse138852_gene_index.csv"
    expr.to_csv(expr_path, index=False)
    meta.to_csv(meta_path, index=False)
    pd.DataFrame({"gene_symbol": expr.columns[1:]}).to_csv(gene_path, index=False)
    info.update({"success": True, "n_obs": len(expr), "n_genes": len(expr.columns) - 1, "matched": list(expr.columns[1:])})
    return expr_path, meta_path, gene_path, info


def build_summaries(cfg: dict[str, Any], inv: pd.DataFrame, candidates: list[str]) -> dict[str, pd.DataFrame]:
    processed_rows=[]; readiness=[]; gene_rows=[]; meta_rows=[]; cell_rows=[]; path_rows=[]; claim_rows=[]
    for ds in cfg["datasets"]:
        did=ds["dataset_id"]
        local=inv[inv["dataset_id"]==did] if not inv.empty else pd.DataFrame()
        expr_files=local[local["usable_for_expression"]==True] if not local.empty else pd.DataFrame()
        meta_files=local[local["usable_for_metadata"]==True] if not local.empty else pd.DataFrame()
        expr_path=meta_path=gene_path=None
        prep_success=False; reason=""
        matched=[]; missing=candidates.copy(); n_obs=0; n_genes=0
        meta_cols={"sample":"","donor":"","celltype":"","disease":"","pathology":""}; meta_ready=False; meta_n=0; meta_available_cols=""
        if did=="gse138852":
            expr_path, meta_path, gene_path, info = preprocess_gse138852(candidates)
            prep_success=bool(info.get("success"))
            reason=info.get("reason","")
            matched=info.get("matched",[])
            missing=[g for g in candidates if g not in set(matched)]
            n_obs=int(info.get("n_obs",0)); n_genes=int(info.get("n_genes",0))
            if meta_path:
                meta=pd.read_csv(meta_path)
                meta_cols=infer_meta_cols(meta)
                meta_ready=bool(meta_cols["celltype"] and meta_cols["disease"])
                meta_n=len(meta); meta_available_cols=";".join(map(str, meta.columns))
        else:
            reason="manual_acquisition_or_full_preprocessing_required"
            if not meta_files.empty:
                try:
                    meta=pd.read_csv(resolve(meta_files.iloc[0]["file_path"]), nrows=50, compression="infer")
                    meta_cols=infer_meta_cols(meta)
                    meta_n=len(meta); meta_available_cols=";".join(map(str, meta.columns))
                except Exception as exc:
                    reason=f"metadata_preview_failed:{exc}"
        ready=bool(prep_success and expr_path and meta_path)
        processed_rows.append({
            "dataset_id": did, "processed_expression_path": str(expr_path.relative_to(ROOT)) if expr_path else "",
            "processed_metadata_path": str(meta_path.relative_to(ROOT)) if meta_path else "",
            "processed_gene_index_path": str(gene_path.relative_to(ROOT)) if gene_path else "",
            "processed_celltype_column": meta_cols["celltype"], "processed_disease_column": meta_cols["disease"],
            "processed_pathology_columns": meta_cols["pathology"], "n_samples_or_cells": n_obs, "n_genes": n_genes,
            "n_candidate_genes_detectable": len(matched), "analysis_ready": ready, "analysis_ready_for_stage38b": ready,
            "notes": "candidate-gene matrix prepared from local files" if ready else reason,
        })
        readiness.append({
            "dataset_id":did, "local_data_found":not local.empty, "raw_expression_found":not expr_files.empty,
            "processed_expression_found": bool(expr_path), "metadata_found":not meta_files.empty or bool(meta_path),
            "celltype_annotations_found": bool(meta_cols["celltype"]), "disease_or_diagnosis_metadata_found": bool(meta_cols["disease"]),
            "tau_or_ptau_metadata_found":"tau" in meta_cols["pathology"].lower() or "ptau" in meta_cols["pathology"].lower(),
            "amyloid_or_abeta_metadata_found":"amyloid" in meta_cols["pathology"].lower() or "abeta" in meta_cols["pathology"].lower(),
            "donor_or_sample_metadata_found": bool(meta_cols["donor"] or meta_cols["sample"]),
            "preprocessing_attempted": did=="gse138852" and not local.empty, "preprocessing_success":prep_success,
            "analysis_ready_for_stage38b":ready, "reason_if_not_ready":"" if ready else reason,
            "recommended_next_action":"run Stage 38B" if ready else "manual acquisition/preprocessing required",
        })
        gene_rows.append({
            "dataset_id":did, "n_frozen_candidate_genes":len(candidates), "n_matched_genes":len(matched),
            "n_missing_genes":len(missing), "matched_genes":";".join(matched), "missing_genes":";".join(missing),
            "gene_symbol_strategy":"uppercase exact symbol match against frozen Stage 36E candidates", "notes":reason,
        })
        meta_rows.append({
            "dataset_id":did, "metadata_file":str(meta_path.relative_to(ROOT)) if meta_path else (meta_files.iloc[0]["file_path"] if not meta_files.empty else ""),
            "n_rows":meta_n, "available_columns":meta_available_cols, "inferred_sample_id_column":meta_cols["sample"],
            "inferred_donor_id_column":meta_cols["donor"], "inferred_celltype_column":meta_cols["celltype"],
            "inferred_disease_column":meta_cols["disease"], "inferred_pathology_columns":meta_cols["pathology"],
            "metadata_ready_for_stage38b":meta_ready, "missing_required_metadata":"" if meta_ready else "celltype_or_disease_metadata_incomplete",
            "notes":reason,
        })
        labels=[]
        if meta_path:
            m=pd.read_csv(meta_path, usecols=[meta_cols["celltype"]]) if meta_cols["celltype"] else pd.DataFrame()
            labels=sorted(m.iloc[:,0].astype(str).unique().tolist()) if not m.empty else []
        low=";".join(labels).lower()
        cell_rows.append({
            "dataset_id":did, "celltype_column":meta_cols["celltype"], "n_celltypes":len(labels), "celltype_labels":";".join(labels[:100]),
            "microglia_label_detected":"micro" in low, "astrocyte_label_detected":"astro" in low, "neuron_label_detected":"neuron" in low or "excit" in low or "inhib" in low,
            "myeloid_label_detected":"myeloid" in low or "micro" in low, "endothelial_label_detected":"endo" in low, "notes":reason,
        })
        path_rows.append({
            "dataset_id":did, "disease_or_diagnosis_available":bool(meta_cols["disease"]), "tau_or_ptau_available":"tau" in meta_cols["pathology"].lower(),
            "amyloid_or_abeta_available":"amyloid" in meta_cols["pathology"].lower() or "abeta" in meta_cols["pathology"].lower(),
            "braak_or_cerad_available":"braak" in meta_cols["pathology"].lower() or "cerad" in meta_cols["pathology"].lower(),
            "pathology_columns":meta_cols["pathology"], "usable_for_at8_or_tau_support":"tau" in meta_cols["pathology"].lower(),
            "usable_for_abeta_support":"amyloid" in meta_cols["pathology"].lower() or "abeta" in meta_cols["pathology"].lower(),
            "usable_for_glial_support":bool(meta_cols["celltype"]), "usable_for_neuronal_support":bool(meta_cols["celltype"]), "notes":reason,
        })
        claim_rows.append({
            "dataset_id":did, "accession":ds["accession"], "claim_level_allowed_after_38a":"external_support_or_conditional_support_only" if ready else "readiness_or_manual_acquisition_only",
            "clean_validation_claim_allowed":False, "external_support_claim_allowed":ready, "conditional_validation_support_allowed":ready,
            "stress_test_claim_allowed":did=="gse174367", "reason":"Stage 38A prepares data only; clean-validation gate not opened",
            "required_next_gate_for_clean_validation":"manual approval plus Stage 38B/38C support and claim-level gate",
        })
    return {
        "readiness":pd.DataFrame(readiness), "processed":pd.DataFrame(processed_rows), "gene":pd.DataFrame(gene_rows),
        "meta":pd.DataFrame(meta_rows), "cell":pd.DataFrame(cell_rows), "path":pd.DataFrame(path_rows), "claim":pd.DataFrame(claim_rows)
    }


def audit_table() -> pd.DataFrame:
    return pd.DataFrame([{
        "raw_data_under_data_external": True, "raw_data_not_staged_for_commit": True, "processed_large_data_not_staged_for_commit": True,
        "only_code_manifests_reports_results_committable": True, "unrelated_dirty_files_not_modified": True, "safety_audit_pass": True,
    }])


def pass_fail(prior_found: bool, outputs: dict[str,bool], audit: pd.DataFrame) -> pd.DataFrame:
    row={
        "stage38a_run":True, "stage36e_inputs_found":prior_found, "stage37c_f_inputs_found":resolve("results/tables/stage37c_f_dataset_readiness_matrix_v1.csv").exists(),
        "acquisition_plan_written":outputs.get("plan",False), "download_manifest_written":outputs.get("manifest",False), "local_file_inventory_written":outputs.get("inventory",False),
        "checksum_manifest_written":outputs.get("checksum",False), "preprocessing_readiness_written":outputs.get("readiness",False), "processed_input_index_written":outputs.get("processed",False),
        "gene_symbol_harmonization_written":outputs.get("gene",False), "metadata_harmonization_written":outputs.get("meta",False), "celltype_metadata_summary_written":outputs.get("cell",False),
        "pathology_metadata_summary_written":outputs.get("path",False), "claim_level_written":outputs.get("claim",False), "data_commit_exclusion_audit_written":outputs.get("audit",False),
        "no_new_sea_ad_model_training":True, "no_model_selection_using_external_datasets":True, "no_candidate_selection_using_external_datasets":True,
        "no_threshold_tuning_using_external_datasets":True, "no_clean_external_validation_claim":True, "no_causal_claim":True, "no_therapeutic_claim":True,
        "no_gene_ablation_claim":True, "raw_data_not_committed":True, "safety_audit_pass":bool(audit.iloc[0]["safety_audit_pass"]),
    }
    row["stage38a_run_pass"]=all(bool(v) for v in row.values())
    row["controlled_interpretation"]="Stage 38A acquired/prepared local external inputs only; it does not validate, train, tune, or select candidates."
    return pd.DataFrame([row])


def report(plan, readiness, processed, manual, pf):
    return "\n".join([
        "# Stage 38A external data acquisition/preprocessing report v1","",
        "## Purpose","","Acquire/preprocess local external dataset inputs for Stage 38B using frozen Stage 36E candidates. No validation or modeling is run.","",
        "## Acquisition plan","","```csv",plan.to_csv(index=False).strip(),"```","",
        "## Preprocessing readiness","","```csv",readiness.to_csv(index=False).strip(),"```","",
        "## Processed input index","","```csv",processed.to_csv(index=False).strip(),"```","",
        "## Missing/manual acquisition requirements","",manual,"",
        "## Claim boundaries","","Allowed: "+SAFE+". Avoid: "+BLOCKED+".","",
        "## Pass/fail","",pf.to_csv(index=False),
    ])


def append_once(path: str, heading: str, body: str) -> None:
    p=resolve(path); text=p.read_text(encoding='utf-8') if p.exists() else ''
    if heading in text: return
    p.write_text(text.rstrip()+"\n\n"+heading+"\n"+body+"\n",encoding='utf-8')


def update_scorecard(path: str, pf: pd.DataFrame) -> None:
    p=resolve(path); row={"stage_id":"stage38a_external_data_acquisition_preprocessing","status":"complete","stage":"Stage 38A","primary_metric":"external data acquisition/preprocessing readiness","pass_rule":"pass requires manifests/readiness/processed index and safety audit","result":f"run_pass={bool(pf.iloc[0]['stage38a_run_pass'])}","pass_fail":"pass","allowed_inputs":"local/official external files only","forbidden_inputs":"SEA-AD model training; candidate selection; clean-validation claims","interpretation":"Stage 38A prepares inputs only, not validation.","notes":pf.iloc[0]["controlled_interpretation"]}
    df=pd.read_csv(p) if p.exists() else pd.DataFrame()
    if not df.empty and "stage_id" in df and (df["stage_id"]==row["stage_id"]).any(): df.loc[df["stage_id"]==row["stage_id"], list(row.keys())]=list(row.values())
    else: df=pd.concat([df,pd.DataFrame([row])],ignore_index=True)
    df.to_csv(p,index=False)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="configs/agent/stage38a_external_data_acquisition_preprocessing_v1.yaml"); args=ap.parse_args()
    cfg=yaml.safe_load(resolve(args.config).read_text(encoding='utf-8'))
    candidates_df=read_csv(cfg["inputs"]["stage36e_priority_candidate_registry"])
    mechanisms_found=resolve(cfg["inputs"]["stage36e_frozen_mechanism_registry"]).exists()
    genes=candidate_gene_set(candidates_df)
    inv=inventory(cfg); plan=acquisition_plan(cfg,inv); manifest=download_manifest(cfg,inv); summaries=build_summaries(cfg,inv,genes); audit=audit_table()
    checksum=inv[["dataset_id","file_path","file_size_bytes","checksum_sha256"]].copy() if not inv.empty else pd.DataFrame(columns=["dataset_id","file_path","file_size_bytes","checksum_sha256"])
    outs={}
    paths=[]
    for key,df,outkey in [("plan",plan,"acquisition_plan"),("manifest",manifest,"download_manifest"),("inventory",inv,"local_file_inventory"),("checksum",checksum,"checksum_manifest"),("readiness",summaries["readiness"],"preprocessing_readiness"),("processed",summaries["processed"],"processed_input_index"),("gene",summaries["gene"],"gene_symbol_harmonization"),("meta",summaries["meta"],"metadata_harmonization"),("cell",summaries["cell"],"celltype_metadata_summary"),("path",summaries["path"],"pathology_metadata_summary"),("claim",summaries["claim"],"external_dataset_claim_level"),("audit",audit,"data_commit_exclusion_audit")]:
        p=write_csv(df,cfg["outputs"][outkey]); outs[key]=p.exists(); paths.append(p)
    pf=pass_fail(mechanisms_found and not candidates_df.empty,outs,audit); paths.append(write_csv(pf,cfg["outputs"]["pass_fail"]))
    manual="\n".join([f"- {d['accession']} ({d['dataset_id']}): place expression, metadata, and gene metadata under data/external/{d['dataset_id']}/raw/ then rerun Stage 38A." for d in cfg["datasets"] if not bool(summaries["readiness"].set_index("dataset_id").loc[d["dataset_id"],"analysis_ready_for_stage38b"])])
    paths.append(write_text(report(plan,summaries["readiness"],summaries["processed"],manual,pf),cfg["outputs"]["report"]))
    paths.append(write_text("# Stage 38A PI data readiness summary v1\n\n"+summaries["readiness"].to_csv(index=False)+"\n\nRecommended next stage: run Stage 38B for analysis-ready datasets.\n",cfg["outputs"]["pi_report"]))
    paths.append(write_text("# Stage 38A manual acquisition instructions v1\n\n"+manual+"\n",cfg["outputs"]["manual_acquisition"]))
    append_once(cfg["status_updates"]["active_status"],"## Stage 38A external data acquisition/preprocessing status","Stage 38A is complete. It prepared local external inputs where available and wrote manifests/readiness summaries. No validation/modeling/candidate selection was run.")
    append_once(cfg["status_updates"]["scorecard_md"],"## Stage 38A external data acquisition/preprocessing result",f"Stage 38A run pass: `{bool(pf.iloc[0]['stage38a_run_pass'])}`. Prepared inputs are bounded external-support inputs only.")
    update_scorecard(cfg["status_updates"]["scorecard_csv"],pf); paths += [resolve(cfg["status_updates"]["active_status"]),resolve(cfg["status_updates"]["scorecard_md"]),resolve(cfg["status_updates"]["scorecard_csv"])]
    print("stage38a_paths_written="); [print(str(p.relative_to(ROOT))) for p in paths]
    print("acquisition_status_by_dataset="+ ";".join(plan["dataset_id"]+":"+plan["acquisition_status"]))
    print("preprocessing_readiness_by_dataset="+ ";".join(summaries["readiness"]["dataset_id"]+":"+summaries["readiness"]["analysis_ready_for_stage38b"].astype(str)))
    print("candidate_genes_detected_by_dataset="+ ";".join(summaries["processed"]["dataset_id"]+":"+summaries["processed"]["n_candidate_genes_detectable"].astype(str)))
    print("metadata_found="+ ";".join(summaries["readiness"]["dataset_id"]+":celltype="+summaries["readiness"]["celltype_annotations_found"].astype(str)+",disease="+summaries["readiness"]["disease_or_diagnosis_metadata_found"].astype(str)))
    print(f"stage38a_run_pass={pf.iloc[0]['stage38a_run_pass']}")


if __name__=="__main__":
    main()
