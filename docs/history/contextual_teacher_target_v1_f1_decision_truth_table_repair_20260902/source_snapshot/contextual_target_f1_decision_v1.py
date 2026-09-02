"""Prospective F1 conclusion-bearing arithmetic; no project outcomes are loaded."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t

ALPHA=.05
PROGRAMS=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail')

def cosine(a,b):
 a=np.asarray(a,np.float64);b=np.asarray(b,np.float64);return np.sum(a*b,axis=-1)/(np.linalg.norm(a,axis=-1)*np.linalg.norm(b,axis=-1))
def advantages(sc,sn,tt,dc,dn,dt):return cosine(sc,tt)-cosine(sn,tt),cosine(dc,dt)-cosine(dn,dt)
def program_mean(a,w2):
 w=np.asarray(w2,np.float64);return float(np.dot(a,w)/w.sum())
def hierarchy(values,donor,operator):
 vals=np.asarray(values,np.float64);d=np.asarray(donor);o=np.asarray(operator);out=[]
 for dd in sorted(set(d)):
  opmeans=[vals[(d==dd)&(o==oo)].mean() for oo in sorted(set(o[d==dd]))];out.append(float(np.mean(opmeans)))
 return np.asarray(out)
def t_interval(x,alpha=ALPHA):
 x=np.asarray(x,np.float64);n=len(x);m=float(np.mean(x)) if n else None
 if n<2 or not np.isfinite(x).all() or np.var(x,ddof=1)==0:return {'estimable':False,'n':n,'mean':m,'lower':None,'upper':None,'lower_one_sided':None,'p_positive':None,'p_negative':None}
 se=float(x.std(ddof=1)/np.sqrt(n));crit=float(student_t.ppf(1-alpha/2,n-1));stat=m/se
 return {'estimable':True,'n':n,'mean':m,'lower':m-crit*se,'upper':m+crit*se,'lower_one_sided':m-float(student_t.ppf(1-alpha,n-1))*se,'p_positive':float(student_t.sf(stat,n-1)),'p_negative':float(student_t.cdf(stat,n-1))}
def holm(p):
 p=np.asarray(p,np.float64);order=np.argsort(p,kind='stable');adj=np.empty(len(p));running=0.
 for rank,idx in enumerate(order):running=max(running,(len(p)-rank)*p[idx]);adj[idx]=min(1.,running)
 return adj
def evidence_slopes(a_by_donor_e,evidence=(.2,.4,.6,.8,1.)):
 y=np.asarray(a_by_donor_e,np.float64);x=np.asarray(evidence,np.float64)-np.mean(evidence);return (y@x)/np.dot(x,x)
def frozen_rank(x):
 x=np.asarray(x,np.float64)
 if x.size==0:return 0
 s=np.linalg.svd(x,compute_uv=False);tol=max(x.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.);return int(np.sum(s>tol))
def nuisance_design(columns,n):
 """Intercept plus centered columns, lexicographically retained only on rank increase."""
 X=np.ones((n,1),np.float64);kept=[]
 for name in sorted(columns):
  if name.startswith('protected_'):raise ValueError('protected-source leakage')
  v=np.asarray(columns[name],np.float64)
  if v.shape!=(n,) or not np.isfinite(v).all():raise ValueError('invalid nuisance column')
  candidate=np.column_stack([X,v-v.mean()])
  if frozen_rank(candidate)>frozen_rank(X):X=candidate;kept.append(name)
 return X,kept
def hc3_intercept(y,columns,alpha=ALPHA):
 y=np.asarray(y,np.float64);n=len(y);X,kept=nuisance_design(columns,n);rank=frozen_rank(X);df=n-rank
 if n<2 or not np.isfinite(y).all() or rank!=X.shape[1] or df<=0:return {'estimable':False,'kept':kept,'rank':rank,'df':df,'beta0':None,'lower':None,'upper':None,'p_positive':None}
 xtxi=np.linalg.inv(X.T@X);beta=xtxi@X.T@y;res=y-X@beta;h=np.einsum('ij,jk,ik->i',X,xtxi,X);den=1-h
 if np.any(den<=np.sqrt(np.finfo(np.float64).eps)):return {'estimable':False,'kept':kept,'rank':rank,'df':df,'beta0':float(beta[0]),'lower':None,'upper':None,'p_positive':None}
 u=res/den;cov=xtxi@(X.T@(X*(u*u)[:,None]))@xtxi;se=float(np.sqrt(max(0.,cov[0,0])))
 if not np.isfinite(se) or se==0:return {'estimable':False,'kept':kept,'rank':rank,'df':df,'beta0':float(beta[0]),'lower':None,'upper':None,'p_positive':None}
 crit=float(student_t.ppf(1-alpha/2,df));stat=float(beta[0]/se)
 return {'estimable':True,'kept':kept,'rank':rank,'df':df,'beta0':float(beta[0]),'lower':float(beta[0]-crit*se),'upper':float(beta[0]+crit*se),'p_positive':float(student_t.sf(stat,df))}
def group_intervals(y,groups):
 y=np.asarray(y,np.float64);g=np.asarray(groups);return {str(k):t_interval(y[g==k]) for k in sorted(set(g.astype(str)))}
def qualify(payload):
 if set(map(str,payload['source_group']))!={'HVS','NPH52','SEA_AD'}:raise ValueError('source-group authority mismatch')
 if set(payload['program_A'])!=set(PROGRAMS) or set(payload['program_delta'])!=set(PROGRAMS):raise ValueError('protected-program family mismatch')
 overall=t_interval(payload['overall_A']);program={p:t_interval(payload['program_A'][p]) for p in PROGRAMS};direct={p:t_interval(payload['program_delta'][p]) for p in PROGRAMS}
 ppos=[program[p]['p_positive'] if program[p]['estimable'] else 1. for p in PROGRAMS];pneg=[direct[p]['p_negative'] if direct[p]['estimable'] else 1. for p in PROGRAMS]
 pos_adj=holm(ppos);neg_adj=holm(pneg);slope=t_interval(evidence_slopes(payload['evidence_A']));qid={k:t_interval(payload[k]) for k in ('query_margin','query_structure')}
 nuisance=hc3_intercept(payload['nuisance_y'],payload['nuisance_columns']);source=group_intervals(payload['nuisance_y'],payload['source_group']);source_rep=all(v['estimable'] and v['lower']>0 for v in source.values())
 gates={'legal':bool(payload['legal']),'overall_positive':bool(overall['estimable'] and overall['lower']>0),'all_programs_reported_and_estimable':bool(all(program[p]['estimable'] for p in PROGRAMS)),'all_direct_deltas_estimable':bool(all(direct[p]['estimable'] for p in PROGRAMS)),'no_adjusted_direct_degradation':bool(all(direct[p]['estimable'] for p in PROGRAMS) and np.all(neg_adj>=ALPHA)),'evidence_slope_positive':bool(slope['estimable'] and slope['lower_one_sided']>0),'query_identity_positive':bool(all(qid[k]['estimable'] and qid[k]['lower']>0 for k in qid)),'nuisance_positive':bool(nuisance['estimable'] and nuisance['lower']>0 and source_rep)}
 return {'qualified':bool(all(gates.values())),'gates':gates,'overall':overall,'program_positive_holm':dict(zip(PROGRAMS,pos_adj.tolist())),'direct_negative_holm':dict(zip(PROGRAMS,neg_adj.tolist())),'evidence_slope':slope,'query_identity':qid,'nuisance':nuisance,'source_replication':source,'claim_scope':'PANEL_CONDITIONED_QUERY_SAMPLE'}
def synthetic():
 rng=np.random.default_rng(1701);n=24;base=np.linspace(.22,.42,n)+rng.normal(0,.015,n);prog={p:(base+.01*i).tolist() for i,p in enumerate(PROGRAMS)};delta={p:(np.linspace(.02,.08,n)+.002*i).tolist() for i,p in enumerate(PROGRAMS)};e=np.stack([base+.08*j for j in range(5)],1)
 payload={'overall_A':base.tolist(),'program_A':prog,'program_delta':delta,'evidence_A':e.tolist(),'query_margin':(base*.4).tolist(),'query_structure':(base*.3).tolist(),'nuisance_y':base.tolist(),'source_group':np.tile(['HVS','NPH52','SEA_AD'],8).tolist(),'nuisance_columns':{'operator_mix':np.tile([0.,1.],n//2).tolist(),'support_depth':np.linspace(-1,1,n).tolist(),'duplicate_support':np.linspace(-2,2,n).tolist()},'legal':True}
 decision=qualify(payload);bad=dict(payload);bad['program_delta']=dict(delta);bad['program_delta']['local_core']=(-np.linspace(.2,.4,n)).tolist();bad_decision=qualify(bad)
 rank_bad=nuisance_design({'a':np.arange(n),'b':2*np.arange(n)},n)[1];shortcut=dict(payload);shortcut['nuisance_y']=np.tile([.6,0.,0.],8).tolist();shortcut['overall_A']=shortcut['nuisance_y'];shortcut_decision=qualify(shortcut)
 constant=dict(payload);constant['program_delta']=dict(delta);constant['program_delta']['local_core']=np.full(n,-.25).tolist();constant_decision=qualify(constant)
 nan_attack=dict(payload);nan_attack['program_delta']=dict(delta);x=np.asarray(nan_attack['program_delta']['local_core']);x[0]=np.nan;nan_attack['program_delta']['local_core']=x.tolist();nan_rejected=not qualify(nan_attack)['gates']['no_adjusted_direct_degradation']
 missing=dict(payload);missing['program_delta']=dict(delta);del missing['program_delta']['local_core']
 try:qualify(missing);missing_rejected=False
 except ValueError:missing_rejected=True
 zero=t_interval(np.ones(n));return {'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'decision':decision,'negative_direct_attack':bad_decision,'constant_negative_direct_attack':constant_decision,'nan_direct_rejected':nan_rejected,'missing_program_rejected':missing_rejected,'nuisance_source_attack':shortcut_decision,'rank_deficient_kept':rank_bad,'zero_variance_estimable':zero['estimable'],'holm_boundary':holm([.00625,.02,.2,.4,.8,.9,.95,1.]).tolist()}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--synthetic-out',type=Path,required=True);args=ap.parse_args();args.synthetic_out.write_text(json.dumps(synthetic(),indent=2)+'\n')
if __name__=='__main__':main()
