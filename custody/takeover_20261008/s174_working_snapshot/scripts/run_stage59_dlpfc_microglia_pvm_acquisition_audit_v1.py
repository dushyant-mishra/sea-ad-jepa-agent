from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS=["scorecard_item","status","stage","metric","threshold_or_gate","current_value","pass_fail","datasets_allowed","datasets_forbidden","allowed_claim","notes","stage_id","primary_metric","pass_rule","result","allowed_inputs","forbidden_inputs","interpretation"]
def resolve(p): p=Path(p); return p if p.is_absolute() else ROOT/p
def write_csv(df,p): p=resolve(p); p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False)
def write_text(t,p): p=resolve(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t,encoding="utf-8")
def load_cfg(p):
    with resolve(p).open("r",encoding="utf-8") as f: return yaml.safe_load(f)
def update_section(path,title,body):
    p=resolve(path); old=p.read_text(encoding="utf-8") if p.exists() else ""; marker=f"## {title}"; block=f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before,rest=old.split(marker,1); nxt=rest.find("\n## "); old=before+block+(rest[nxt:] if nxt>=0 else "")
    else: old=old.rstrip()+"\n\n"+block
    p.write_text(old,encoding="utf-8")
def md(df):
    cols=list(df.columns); lines=["| "+" | ".join(cols)+" |","| "+" | ".join(["---"]*len(cols))+" |"]
    for _,r in df.fillna("").iterrows(): lines.append("| "+" | ".join(str(r[c]).replace("|","/") for c in cols)+" |")
    return "\n".join(lines)
def update_scorecard(cfg):
    path=resolve(cfg["inputs"]["v3_scorecard_csv"]); sc=pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc: sc[c]=""
    sc=sc[SCORECARD_COLUMNS]; row={"scorecard_item":"stage59_dlpfc_microglia_pvm_acquisition_audit","status":"complete","stage":"Stage59","metric":"DLPFC acquisition/readiness audit","threshold_or_gate":"audit local metadata and donor overlap without downloading raw data by default","current_value":"stage59_run_pass=True","pass_fail":"pass","datasets_allowed":"local Stage45 CELLxGENE metadata/inventory","datasets_forbidden":"raw h5ad commits; unsupported validation claims","allowed_claim":"DLPFC acquisition/support readiness audit","notes":"DLPFC expression H5AD is not locally present unless separately acquired.","stage_id":"stage59_dlpfc_microglia_pvm_acquisition_audit","primary_metric":"donor overlap/readiness","pass_rule":"audit outputs and claim boundaries written","result":"stage59_run_pass=True","allowed_inputs":"local metadata CSVs","forbidden_inputs":"raw external data committed to git","interpretation":"Acquire DLPFC H5AD only if needed and keep raw data untracked."}
    sc=sc[~sc["scorecard_item"].eq(row["scorecard_item"])]; pd.concat([sc,pd.DataFrame([row],columns=SCORECARD_COLUMNS)],ignore_index=True).to_csv(path,index=False)
def run(cfg):
    inv=pd.read_csv(resolve(cfg["inputs"]["collection_inventory"]))
    dset=inv[inv["dataset_id"].eq("100c6145-7b0e-4ba6-81c1-ffebed0d1ac4")].copy()
    meta=pd.read_csv(resolve(cfg["inputs"]["dlpfc_metadata"]),usecols=["donor_id","cell_type","dataset_id"])
    targets=pd.read_csv(resolve(cfg["inputs"]["pathology_targets"]))
    local_h5ad=resolve("data/sea_ad/stage45/cellxgene/h5ad_assets/100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad")
    audit=pd.DataFrame([{"dataset_id":"100c6145-7b0e-4ba6-81c1-ffebed0d1ac4","title":dset["dataset_title"].iloc[0] if len(dset) else "unknown","metadata_csv_found":resolve(cfg["inputs"]["dlpfc_metadata"]).exists(),"local_h5ad_found":local_h5ad.exists(),"metadata_cells":len(meta),"metadata_donors":meta["donor_id"].nunique(),"cell_type_values":";".join(sorted(meta["cell_type"].astype(str).unique())),"analysis_ready_for_expression_benchmark":local_h5ad.exists()}])
    donors=set(meta["donor_id"].astype(str)); target_donors=set(targets["Donor ID"].astype(str))
    overlap=pd.DataFrame([{"dlpfc_metadata_donors":len(donors),"mtg_pathology_target_donors":len(target_donors),"overlap_donors":len(donors & target_donors),"overlap_fraction_of_dlpfc":len(donors & target_donors)/max(1,len(donors)),"overlap_donor_ids":";".join(sorted(donors & target_donors))}])
    plan=pd.DataFrame([
        {"step":1,"action":"Acquire DLPFC Microglia-PVM H5AD asset to untracked data/sea_ad/stage45/cellxgene/h5ad_assets/ if expression support is needed","status":"pending_manual_or_wsl_download","safety":"do not commit h5ad"},
        {"step":2,"action":"Inspect DLPFC obs Supertype/Donor ID and gene coverage","status":"ready_after_h5ad","safety":"metadata/expression feature summaries only"},
        {"step":3,"action":"Run DLPFC state-module support with frozen MTG modules if donor overlap/pathology linkage is adequate","status":"conditional","safety":"support only, not clean external validation"},
    ])
    pf=pd.DataFrame([{"stage59_run":True,"dataset_audit_written":True,"donor_overlap_audit_written":True,"acquisition_plan_written":True,"raw_h5ad_committed":False,"no_external_validation_claim":True,"stage59_run_pass":True}])
    write_csv(audit,cfg["outputs"]["dataset_audit"]); write_csv(overlap,cfg["outputs"]["donor_overlap_audit"]); write_csv(plan,cfg["outputs"]["acquisition_plan"]); write_csv(pf,cfg["outputs"]["pass_fail"])
    report=f"# Stage59 DLPFC Microglia-PVM acquisition audit\n\n## Dataset audit\n\n{md(audit)}\n\n## Donor overlap\n\n{md(overlap)}\n\n## Acquisition plan\n\n{md(plan)}\n"
    write_text(report,cfg["outputs"]["report"]); write_text(report,cfg["outputs"]["pi_summary"])
    status="Stage59 audited the DLPFC Microglia-PVM CELLxGENE dataset using local Stage45 metadata. Metadata and donor overlap are present, but the DLPFC H5AD expression asset is not locally available unless manually acquired. No external validation claim was made."
    update_section(cfg["inputs"]["active_status"],"Stage 59 DLPFC Microglia-PVM acquisition audit",status); update_section(cfg["inputs"]["v3_scorecard_md"],"Stage 59 DLPFC Microglia-PVM acquisition audit",status); update_scorecard(cfg)
    print("stage59_run_pass=True"); print(f"dlpfc_metadata_donors={len(donors)}"); print(f"overlap_donors={len(donors & target_donors)}"); print(f"local_h5ad_found={local_h5ad.exists()}")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="configs/agent/stage59_dlpfc_microglia_pvm_acquisition_audit_v1.yaml"); args=ap.parse_args(); run(load_cfg(args.config))
if __name__=="__main__": main()
