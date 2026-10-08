"""Current F1 decision truth table: one authoritative gate per endpoint, no data access."""
from __future__ import annotations
import hashlib,importlib.util
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;V1=HERE/"contextual_target_f1_decision_v1.py";V1_SHA="204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34"
PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail");EVIDENCE=(.2,.4,.6,.8,1.);ALPHA=.05
CLAIM_SCOPE="FINITE_FROZEN_2781_DESIGN_SAMPLED_W2_EXPECTATION";PROGRAM_ESTIMAND="DESIGN_SAMPLED_W2_PROGRAM_ESTIMAND"
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def arithmetic():
 if sha(V1)!=V1_SHA:raise ValueError("frozen v1 arithmetic hash mismatch")
 s=importlib.util.spec_from_file_location("f1_v1_arithmetic",V1);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def exact_payload(payload):
 required={"overall_A","program_A","program_delta","evidence_A","qid_margin","qid_win_minus_half","program_qid_margin","draw0","draw1","nuisance_y","source_group","nuisance_columns","legal"}
 if set(payload)!=required:raise ValueError("current decision payload schema mismatch")
 if set(payload["program_A"])!=set(PROGRAMS) or set(payload["program_delta"])!=set(PROGRAMS) or set(payload["program_qid_margin"])!=set(PROGRAMS):raise ValueError("protected-program family mismatch")
 n=len(payload["overall_A"])
 if n!=104 or any(len(payload[k])!=n for k in ("qid_margin","qid_win_minus_half","draw0","draw1","nuisance_y","source_group")):raise ValueError("donor population mismatch")
 if not np.array_equal(np.asarray(payload["overall_A"],np.float64),np.asarray(payload["nuisance_y"],np.float64),equal_nan=True):raise ValueError("nuisance outcome must equal primary donor outcome")
 if np.asarray(payload["evidence_A"]).shape!=(n,5) or any(len(payload[f][p])!=n for f in ("program_A","program_delta","program_qid_margin") for p in PROGRAMS):raise ValueError("decision vector shape mismatch")
 if set(map(str,payload["source_group"]))!={"HVS","NPH52","SEA_AD"}:raise ValueError("source-group authority mismatch")
def qualify_current(payload):
 exact_payload(payload);v1=arithmetic();overall=v1.t_interval(payload["overall_A"]);program={p:v1.t_interval(payload["program_A"][p]) for p in PROGRAMS};direct={p:v1.t_interval(payload["program_delta"][p]) for p in PROGRAMS};qprog={p:v1.t_interval(payload["program_qid_margin"][p]) for p in PROGRAMS}
 pos=v1.holm([program[p]["p_positive"] if program[p]["estimable"] else 1. for p in PROGRAMS]);dneg=v1.holm([direct[p]["p_negative"] if direct[p]["estimable"] else 0. for p in PROGRAMS]);qneg=v1.holm([qprog[p]["p_negative"] if qprog[p]["estimable"] else 0. for p in PROGRAMS])
 slope=v1.t_interval(v1.evidence_slopes(payload["evidence_A"],EVIDENCE));qm=v1.t_interval(payload["qid_margin"]);qw=v1.t_interval(payload["qid_win_minus_half"]);nuisance=v1.hc3_intercept(payload["nuisance_y"],payload["nuisance_columns"]);sources=v1.group_intervals(payload["nuisance_y"],payload["source_group"])
 draw0=float(np.mean(np.asarray(payload["draw0"],np.float64)));draw1=float(np.mean(np.asarray(payload["draw1"],np.float64)));draw_finite=np.isfinite([draw0,draw1]).all()
 gates={"legal_provenance":bool(payload["legal"]),"overall_A_60_one_sided_positive":bool(overall["estimable"] and overall["lower_one_sided"]>0),"protected_program_family_estimable":bool(all(program[p]["estimable"] for p in PROGRAMS)),"no_contextual_minus_direct_degradation":bool(all(direct[p]["estimable"] for p in PROGRAMS) and np.all(dneg>=ALPHA)),"evidence_trend_one_sided_positive":bool(slope["estimable"] and slope["lower_one_sided"]>0),"qid_v2_margin_one_sided_positive":bool(qm["estimable"] and qm["lower_one_sided"]>0),"qid_v2_win_one_sided_positive":bool(qw["estimable"] and qw["lower_one_sided"]>0),"no_qid_v2_program_negative_margin":bool(all(qprog[p]["estimable"] for p in PROGRAMS) and np.all(qneg>=ALPHA)),"two_draw_sign_stable":bool(draw_finite and not ((draw0<0<draw1) or (draw1<0<draw0))),"hc3_nuisance_positive":bool(nuisance["estimable"] and nuisance["lower"]>0),"cross_source_replication":bool(all(x["estimable"] and x["lower"]>0 for x in sources.values()))}
 return {"qualified":bool(all(gates.values())),"gates":gates,"reports":{"overall":overall,"protected_program_positive_holm_report_only":dict(zip(PROGRAMS,pos.tolist())),"protected_program":program,"direct_negative_holm":dict(zip(PROGRAMS,dneg.tolist())),"evidence_slope":slope,"qid_margin":qm,"qid_win_minus_half":qw,"qid_program_negative_margin_holm":dict(zip(PROGRAMS,qneg.tolist())),"draw_means":[draw0,draw1],"nuisance":nuisance,"source_replication":sources},"claim_scope":CLAIM_SCOPE,"program_estimand":PROGRAM_ESTIMAND,"legacy_internal_scope_superseded":True,"frozen_v1_arithmetic_sha256":V1_SHA}
