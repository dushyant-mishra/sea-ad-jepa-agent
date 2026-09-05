#!/usr/bin/env python3
"""Independent outcome-blind verifier attacks for F1-B v1.

This verifier is expected to STOP the current v1 implementation. It reads only source,
contract and published synthetic result files from the checked-out branch plus synthetic
in-memory tensors. It does not read expression, DEV/SEALED/pathology, or F1 outcomes.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[2]
EXEC=ROOT/"scripts/v4/run_f1b_minimal_bridge_v1.py"
CONTRACT=ROOT/"docs/agent/F1B_MINIMAL_BRIDGE_CONTRACT_20260905.md"
RESULT=ROOT/"docs/agent/F1B_DUAL_ROUTING_RESULT_20260905.json"

def load_module():
    spec=importlib.util.spec_from_file_location("f1b_v1_verify",EXEC)
    mod=importlib.util.module_from_spec(spec);sys.modules["f1b_v1_verify"]=mod;spec.loader.exec_module(mod)
    return mod

class Fake:
    def __init__(self):
        self.params=[]
        for b in range(6):
            for leaf in ("attention_norm.weight","attention_norm.bias",
                         "attention.query.weight","attention.query.bias",
                         "attention.key.weight","attention.key.bias",
                         "attention.value.weight","attention.value.bias"):
                p=torch.nn.Parameter(torch.ones(2));p.grad=torch.ones(2)
                self.params.append((f"blocks.{b}.{leaf}",p))
    def named_parameters(self): return self.params

def attack_g1_nonfinite(mod):
    enc=Fake();enc.params[0][1].grad=torch.tensor([float("nan"),1.0])
    report=mod.gradient_coverage(enc)
    gates=mod.evaluate_gates(report,{"tensors":48,"zero_moments":0,"zero_tensors":[]},
        {"ratio_over_decay":10.0,"pure_decay_prediction":1e-6,"mean_relative_movement":1e-3,"min_relative_movement":1e-3},
        {"min_per_query_routing_spread":1e-3,"mean_n_eff_over_n":0.99},{},{},mod.Frozen(),
        {"mean_n_eff_over_n":0.99},False)
    return {"vulnerable":bool(gates["G1_gradient_coverage"]),"grad_min_norm":report["min_norm"]}

def attack_g2_one_moment_zero(mod):
    enc=Fake()
    class Opt: pass
    opt=Opt();opt.state={}
    for _,p in enc.params:
        opt.state[p]={"exp_avg":torch.ones_like(p),"exp_avg_sq":torch.zeros_like(p),"step":torch.tensor(1.)}
    rep=mod.optimizer_moments(enc,opt)
    return {"vulnerable":rep["zero_moments"]==0,"report":rep}

def attack_g3_mean_masking(mod):
    enc=Fake();base={}
    lr=mod.Frozen().learning_rate;wd=mod.Frozen().weight_decay;steps=40
    decay=1-(1-lr*wd)**steps
    for i,(name,p) in enumerate(enc.params):
        base[name]=torch.ones_like(p)
        if i==0:
            p.data.fill_(1-decay)  # pure decay only
        else:
            p.data.fill_(1.1)
    rep=mod.movement_report(enc,base,mod.Frozen(),steps)
    return {"vulnerable":rep["ratio_over_decay"]>=mod.Frozen().movement_over_decay_margin,
            "mean_ratio_over_decay":rep["ratio_over_decay"],"min_relative_movement":rep["min_relative_movement"],
            "pure_decay_prediction":rep["pure_decay_prediction"]}

def static_findings():
    src=EXEC.read_text(encoding="utf-8")
    contract=CONTRACT.read_text(encoding="utf-8")
    result=json.loads(RESULT.read_text(encoding="utf-8"))
    return {
      "predictor_mechanics_gate_missing": "predictor_gradient_coverage" not in src and "predictor_optimizer_moments" not in src,
      "backbone_cell0_support_literal_present": 'visible[0].sum()' in src,
      "backbone_cell0_query_literal_present": 'pop["queries"][0, :4]' in src,
      "predictor_cell0_support_literal_present": 'valid[0].sum()' in src,
      "entropy_perplexity_used": '(-(p * (p + 1e-30).log()).sum(-1)).exp()' in src or '(-(w * (w + 1e-30).log()).sum(-1)).exp()' in src,
      "participation_ratio_reported": '1.0 /' in src and 'sum(p * p)' in src,
      "movement_family_includes_attention_norm": 'PRE_ATTENTION_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")' in src,
      "movement_skips_near_zero_baseline": 'if norm <= 1e-8:' in src,
      "update_override_exposed": 'add_argument("--updates"' in src,
      "contract_default_updates":40,
      "published_result_updates":result.get("frozen_parameters",{}).get("updates"),
      "directional_structural_impossibility_claim_present":"structurally unable to be solved through the CELL token or a global mean" in contract,
      "published_mode":result.get("mode"),
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    mod=load_module()
    attacks={"G1_nonfinite":attack_g1_nonfinite(mod),"G2_one_moment_zero":attack_g2_one_moment_zero(mod),
             "G3_mean_movement_masking":attack_g3_mean_masking(mod),"static":static_findings()}
    vulnerabilities=[]
    if attacks["G1_nonfinite"]["vulnerable"]:vulnerabilities.append("G1_ACCEPTS_NONFINITE_GRADIENT")
    if attacks["G2_one_moment_zero"]["vulnerable"]:vulnerabilities.append("G2_ACCEPTS_ZERO_SECOND_MOMENT")
    if attacks["G3_mean_movement_masking"]["vulnerable"]:vulnerabilities.append("G3_MEAN_MASKS_DECAY_ONLY_TENSOR")
    s=attacks["static"]
    for key in ("predictor_mechanics_gate_missing","backbone_cell0_support_literal_present","backbone_cell0_query_literal_present",
                "predictor_cell0_support_literal_present","movement_family_includes_attention_norm","movement_skips_near_zero_baseline"):
        if s.get(key):vulnerabilities.append(key.upper())
    if s["published_result_updates"]!=s["contract_default_updates"]:vulnerabilities.append("PUBLISHED_300U_EXCEEDS_FROZEN_40U_HORIZON")
    doc={"schema":"F1B_INDEPENDENT_VERIFIER_ATTACKS_V1",
         "terminal":"STOP_F1B_INDEPENDENT_VERIFICATION_REPAIR_REQUIRED" if vulnerabilities else "PASS_F1B_INDEPENDENT_VERIFIER",
         "vulnerabilities":vulnerabilities,"attacks":attacks,
         "explicit_correction":"The backbone G4 expression uses dim=1 on [heads,queries,keys], so it does compare query addresses. The remaining routing defect is first-cell-only coverage/normalization, not a head/query-axis error.",
         "firewall":{"expression_read":False,"f1_outcome_read":False,"dev_sealed_pathology":False}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"terminal":doc["terminal"],"vulnerabilities":vulnerabilities},indent=2))
if __name__=="__main__":main()
