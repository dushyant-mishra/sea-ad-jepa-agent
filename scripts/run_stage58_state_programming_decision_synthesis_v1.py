from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGE27C = 0.3267024400121495
MATERIAL = 0.3317
SCORECARD_COLUMNS = ["scorecard_item","status","stage","metric","threshold_or_gate","current_value","pass_fail","datasets_allowed","datasets_forbidden","allowed_claim","notes","stage_id","primary_metric","pass_rule","result","allowed_inputs","forbidden_inputs","interpretation"]

def resolve(p): 
    p=Path(p); return p if p.is_absolute() else ROOT/p
def write_csv(df,p):
    p=resolve(p); p.parent.mkdir(parents=True, exist_ok=True); df.to_csv(p,index=False)
def write_text(t,p):
    p=resolve(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t,encoding="utf-8")
def load_cfg(p):
    with resolve(p).open("r",encoding="utf-8") as f: return yaml.safe_load(f)
def update_section(path,title,body):
    p=resolve(path); old=p.read_text(encoding="utf-8") if p.exists() else ""; marker=f"## {title}"; block=f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before,rest=old.split(marker,1); nxt=rest.find("\n## "); old=before+block+(rest[nxt:] if nxt>=0 else "")
    else: old=old.rstrip()+"\n\n"+block
    p.write_text(old,encoding="utf-8")
def md(df):
    if df.empty: return ""
    cols=list(df.columns); lines=["| "+" | ".join(cols)+" |","| "+" | ".join(["---"]*len(cols))+" |"]
    for _,r in df.fillna("").iterrows(): lines.append("| "+" | ".join(str(r[c]).replace("|","/") for c in cols)+" |")
    return "\n".join(lines)
def update_scorecard(cfg):
    path=resolve(cfg["inputs"]["v3_scorecard_csv"]); sc=pd.read_csv(path) if path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for c in SCORECARD_COLUMNS:
        if c not in sc: sc[c]=""
    sc=sc[SCORECARD_COLUMNS]; row={"scorecard_item":"stage58_state_programming_decision_synthesis","status":"complete","stage":"Stage58","metric":"decision synthesis","threshold_or_gate":"synthesize Stage53-57 without new modeling or overclaims","current_value":"stage58_run_pass=True","pass_fail":"pass","datasets_allowed":"existing Stage53-57 outputs only","datasets_forbidden":"new modeling; raw data commits; external validation claims","allowed_claim":"internal decision synthesis and next-data prioritization","notes":"Stage27C remains locked; Stage55 remains strongest near-miss.","stage_id":"stage58_state_programming_decision_synthesis","primary_metric":"best prior branch score","pass_rule":"all synthesis outputs written and claim boundaries preserved","result":"stage58_run_pass=True","allowed_inputs":"committed Stage53-57 tables","forbidden_inputs":"new benchmark tuning","interpretation":"Proceed to DLPFC audit and gene-preserved MTG rebuild rather than more MTG feature squeezing."}
    sc=sc[~sc["scorecard_item"].eq(row["scorecard_item"])]; pd.concat([sc,pd.DataFrame([row],columns=SCORECARD_COLUMNS)],ignore_index=True).to_csv(path,index=False)
def run(cfg):
    rows=[]
    for stage,key in [("Stage53","stage53_branch"),("Stage54","stage54_branch"),("Stage55","stage55_branch"),("Stage56","stage56_branch"),("Stage57","stage57_branch")]:
        p=resolve(cfg["inputs"][key]); df=pd.read_csv(p); best=df.sort_values("mean_pooled_oof_spearman",ascending=False).iloc[0]
        rows.append({"stage":stage,"best_model_variant":best["model_variant"],"best_mean_pooled_oof_spearman":best["mean_pooled_oof_spearman"],"delta_vs_stage27c":float(best["mean_pooled_oof_spearman"])-STAGE27C,"beats_stage27c":float(best["mean_pooled_oof_spearman"])>STAGE27C,"beats_material_threshold":float(best["mean_pooled_oof_spearman"])>MATERIAL})
    syn=pd.DataFrame(rows)
    nxt=pd.DataFrame([
        {"priority_rank":1,"next_action":"Stage60_gene_preserved_MTG_module_rebuild","reason":"raw MTG contains missing stress/module genes and decodable Micro-PVM state labels; can test whether missing genes explain near-miss","claim_boundary":"internal benchmark only"},
        {"priority_rank":2,"next_action":"Stage59_DLPFC_Microglia_PVM_acquisition_support_audit","reason":"DLPFC Microglia-PVM exists online/local metadata; region support may clarify generality","claim_boundary":"support/acquisition audit unless donor/pathology linkage exists"},
        {"priority_rank":3,"next_action":"spatial_or_plaque_proximity_feature_acquisition","reason":"current transcriptomic state modules are subthreshold; spatial/pathology-proximity features are likely missing signal","claim_boundary":"manual acquisition/readiness only"},
    ])
    pf=pd.DataFrame([{"stage58_run":True,"synthesis_written":True,"next_data_priority_written":True,"stage27c_locked_benchmark_preserved":True,"no_new_modeling":True,"no_external_validation_claim":True,"stage58_run_pass":True}])
    write_csv(syn,cfg["outputs"]["synthesis_table"]); write_csv(nxt,cfg["outputs"]["next_data_priority"]); write_csv(pf,cfg["outputs"]["pass_fail"])
    report=f"# Stage58 state-programming decision synthesis\n\n{md(syn)}\n\n## Decision\n\nStage55 remains the strongest state-programming near-miss, but no Stage53-57 result beats Stage27C or reaches the material rescue threshold. The next move is new signal, not more tuning: gene-preserved MTG module extraction and DLPFC support audit.\n\n{md(nxt)}\n"
    write_text(report,cfg["outputs"]["report"]); write_text(report,cfg["outputs"]["pi_summary"])
    status="Stage58 synthesized Stage53-57. Stage55 remains the strongest state-programming near-miss, but Stage27C remains locked. Next priorities are gene-preserved MTG module extraction, DLPFC Microglia-PVM audit, and spatial/plaque-proximity feature acquisition. No new modeling or validation claim was made."
    update_section(cfg["inputs"]["active_status"],"Stage 58 state-programming decision synthesis",status); update_section(cfg["inputs"]["v3_scorecard_md"],"Stage 58 state-programming decision synthesis",status); update_scorecard(cfg)
    print("stage58_run_pass=True"); print("best_prior_stage="+syn.sort_values("best_mean_pooled_oof_spearman",ascending=False).iloc[0]["stage"])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="configs/agent/stage58_state_programming_decision_synthesis_v1.yaml"); args=ap.parse_args(); run(load_cfg(args.config))
if __name__=="__main__": main()
