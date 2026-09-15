import numpy as np, json
from pathlib import Path

NF=5; LAM=1e-2

def ridge_predict(Xtr,Ytr,Xte):
    mu=Xtr.mean(0); sd=np.maximum(Xtr.std(0),1e-9)
    A=(Xtr-mu)/sd; ym=Ytr.mean(0)
    G=A.T@A+(LAM*len(A))*np.eye(A.shape[1])
    W=np.linalg.solve(G,A.T@(Ytr-ym))
    return ((Xte-mu)/sd)@W+ym

def make_synth(seed=0, scenario='operator_only', n_donors=100, cells_per=100, d=16, n_ops=20, n_src=3):
    rng=np.random.default_rng(seed)
    donor=np.repeat(np.arange(n_donors), cells_per)
    donor_src=np.arange(n_donors)%n_src
    op_src=np.arange(n_ops)%n_src
    op=np.empty(len(donor),dtype=int); src=np.empty(len(donor),dtype=int)
    idx=0
    for dd in range(n_donors):
        s=donor_src[dd]; candidates=np.where(op_src==s)[0]
        chosen=rng.choice(candidates,size=min(3,len(candidates)),replace=False)
        vals=np.resize(chosen,cells_per); rng.shuffle(vals)
        op[idx:idx+cells_per]=vals; src[idx:idx+cells_per]=s; idx+=cells_per
    kbio=5
    A0=rng.normal(size=(kbio,d))/np.sqrt(kbio); A1=rng.normal(size=(kbio,d))/np.sqrt(kbio)
    shared_op=rng.normal(scale=2.0,size=(n_ops,6))
    B0=rng.normal(size=(6,d))/np.sqrt(6); B1=rng.normal(size=(6,d))/np.sqrt(6)
    cell_bio=rng.normal(size=(len(donor),kbio))
    if scenario=='operator_only':
        bio0=np.zeros((len(donor),d)); bio1=np.zeros((len(donor),d))
        tech0=shared_op[op]@B0; tech1=shared_op[op]@B1
    elif scenario=='bio_plus_operator':
        bio0=cell_bio@A0; bio1=cell_bio@A1
        tech0=shared_op[op]@B0; tech1=shared_op[op]@B1
    elif scenario=='bio_confounded_operator':
        op_bio=rng.normal(scale=2.0,size=(n_ops,kbio)); z=cell_bio+op_bio[op]
        bio0=z@A0; bio1=z@A1
        tech0=np.zeros_like(bio0); tech1=np.zeros_like(bio1)
    else: raise ValueError(scenario)
    V0=bio0+tech0+rng.normal(scale=.7,size=(len(donor),d))
    V1=bio1+tech1+rng.normal(scale=.7,size=(len(donor),d))
    return V0,V1,donor,op,src

def correct_within_group_r2(X,Y,donor,group):
    fold=donor%NF; sse_model=sse_base=0.0
    groups=np.unique(group)
    for f in range(NF):
        te=fold==f; tr=~te
        gx=X[tr].mean(0); gy=Y[tr].mean(0)
        mx={}; my={}
        for g in groups:
            m=tr&(group==g)
            if m.any(): mx[g]=X[m].mean(0); my[g]=Y[m].mean(0)
        tri=np.where(tr)[0]; tei=np.where(te)[0]
        Xtr=np.stack([X[i]-mx.get(group[i],gx) for i in tri])
        Ytr=np.stack([Y[i]-my.get(group[i],gy) for i in tri])
        Xte=np.stack([X[i]-mx.get(group[i],gx) for i in tei])
        Yte=np.stack([Y[i]-my.get(group[i],gy) for i in tei])
        pred=ridge_predict(Xtr,Ytr,Xte)
        sse_model += float(np.square(Yte-pred).sum())
        sse_base += float(np.square(Yte).sum())
    return 1-sse_model/sse_base

def claude_x4_style_r2(X0,Y0,donor,group):
    fold=(donor%NF).astype(np.int8); pv=group
    V0=X0.astype(float).copy(); V1=Y0.astype(float).copy(); K=int(pv.max())+1
    for f in range(NF):
        tr=fold!=f
        for Vx in (V0,V1):
            m0=np.zeros((K,Vx.shape[1])); c0=np.zeros(K)
            np.add.at(m0,pv[tr],Vx[tr]); np.add.at(c0,pv[tr],1)
            gm=Vx[tr].mean(0); mm=np.where(c0[:,None]>0,m0/np.maximum(c0,1)[:,None],gm)
            if Vx is V0: V0[fold==f]-=mm[pv[fold==f]]
            else: V1[fold==f]-=mm[pv[fold==f]]
    gm=V1.mean(0); sse=sst=0.0
    for f in range(NF):
        m=fold==f; tr=~m; At=V0[tr].copy(); Yt=V1[tr].copy()
        for Vx,kind in ((At,'a'),(Yt,'b')):
            s=np.zeros((K,Vx.shape[1])); c=np.zeros(K)
            np.add.at(s,pv[tr],Vx); np.add.at(c,pv[tr],1)
            g=Vx.mean(0); mm=np.where(c[:,None]>0,s/np.maximum(c,1)[:,None],g)
            if kind=='a': At=At-mm[pv[tr]]
            else: Yt=Yt-mm[pv[tr]]
        pred=ridge_predict(At,Yt,V0[m])
        sse += float(np.square(V1[m]-pred).sum())
        sst += float(np.square(V1[m]-gm).sum())
    return 1-sse/sst

rows=[]
for scenario in ['operator_only','bio_plus_operator','bio_confounded_operator']:
    V0,V1,don,op,src=make_synth(scenario=scenario)
    rows.append({
        'scenario':scenario,
        'correct_within_operator_incremental_R2':correct_within_group_r2(V0,V1,don,op),
        'claude_x4_style_R2':claude_x4_style_r2(V0,V1,don,op)
    })
print(json.dumps({'authority':'LOCAL_SYNTHETIC_METHOD_REDTEAM_ONLY','seed':0,'rows':rows},indent=2,sort_keys=True))
