#!/usr/bin/env python3
"""V44 tiny historical RNA tournament — fully non-authorizing research replay.

Requires ORIGINAL digest-authenticated historical discovery CSR already prepared
as indptr.npy, indices.npy, data.npy and ORIGINAL sample_freeze.csv. These
arrays are derived via np.load(original_npz) and np.save without sampling, so
the original discovery NPZ and sample metadata are still SHA-checked here.
The entire 600-MB original archive is NOT stored in this public Git branch.

This is a GitHub-readable reimplementation of the locally executed exact source
SHA256 1a3ee7ad900f9da71e287f47bed66850782a5cca0351e8c38390a519546dc342.
The physically executed exact source remains inside the 19KB V44 portable ZIP.
No neural JEPA, true current-V5 IPB or EMA training is run by this script.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, time, zipfile
from pathlib import Path
os.environ["OPENBLAS_NUM_THREADS"]="2"
os.environ["OMP_NUM_THREADS"]="2"
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

EXPR_SHA="4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92"
META_SHA="79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
CALIB_SHA="07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
N=2600;SEEDS=(7,11,17);LAT=48;ALPHA=50.0;QS=[6186,12469]

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def norm_view(z):
    r=np.expm1(z.astype(np.float64))
    total=r.sum(1,keepdims=True)
    if not np.all(total>0):raise ValueError("nonestimable zero-depth lawful view")
    return np.log1p(1e4*r/total).astype(np.float32)

def emb(train,test,dim,seed):
    n=min(dim,train.shape[1],len(train)-1)
    obj=PCA(n_components=n,svd_solver="randomized",random_state=seed,n_oversamples=8,iterated_power=2)
    return obj.fit_transform(train).astype(np.float32),obj.transform(test).astype(np.float32)

def whiten(train,test):
    mean=train.mean(0);std=train.std(0).clip(min=.1)
    return (train-mean)/std,(test-mean)/std

def head(train,test,dim,seed):
    return whiten(*emb(train,test,dim,seed))

def score(y,pred,trainvar,donors,rare):
    err=(pred-y)**2/trainvar
    frame=pd.DataFrame({"donor":donors,"mse":np.mean(err,axis=1),"rare":rare})
    per=frame.groupby("donor",sort=True).mse.mean()
    per_rare=frame[frame.rare].groupby("donor").mse.mean()
    return {"donor_equal_r2":float(1-per.mean()),
            "rare_subgroup_r2":float(1-per_rare.mean()) if len(per_rare)>=2 else None,
            "rare_test_donors":int(len(per_rare)),"per_donor_loss":per.to_dict()}

def run(root:Path,calibration:Path,out:Path):
    if sha(root/"discovery_original.npz")!=EXPR_SHA or sha(root/"sample_freeze.csv")!=META_SHA:
        raise ValueError("original discovery expression or original sample-freeze SHA mismatch")
    if sha(calibration)!=CALIB_SHA:raise ValueError("wrong original calibration bundle SHA")
    ptr=np.load(root/"indptr.npy",mmap_mode="r")
    idx=np.load(root/"indices.npy",mmap_mode="r")
    dat=np.load(root/"data.npy",mmap_mode="r")
    full=csr_matrix((np.array(dat[:ptr[N]],dtype=np.float32),np.array(idx[:ptr[N]],dtype=np.int32),
                     np.array(ptr[:N+1],dtype=np.int32)),shape=(N,41238))
    meta=pd.read_csv(root/"sample_freeze.csv").iloc[:N].reset_index(drop=True)
    assert meta["sample"].eq("A_NATURAL_MIXTURE").all() and meta["in_original_t1"].eq(0).all()
    with zipfile.ZipFile(calibration) as z:
        member=next(n for n in z.namelist() if n.endswith("/FOUNDATION_84_CELL_TRUTH_TABLE.npz"))
        with np.load(io.BytesIO(z.read(member)),allow_pickle=False) as truth:
            common=np.all(truth["measured_mask"],axis=0)
    assert int(common.sum())==17186
    allowed=np.setdiff1d(np.flatnonzero(common),np.array(QS))
    runs=[];splits=[];per_donor=[]
    for seed in SEEDS:
        start=time.monotonic()
        don=np.array(sorted(meta.donor_id.unique()))
        testdon=set(np.random.default_rng(seed).permutation(don)[:max(12,round(.20*len(don)))].tolist())
        tr=np.flatnonzero(~meta.donor_id.isin(testdon).to_numpy())
        te=np.flatnonzero(meta.donor_id.isin(testdon).to_numpy())
        X=full[:,allowed];mu=np.asarray(X[tr].mean(0)).ravel()
        sq=np.asarray(X[tr].power(2).mean(0)).ravel()
        chosen=allowed[np.argsort(-np.maximum(0,sq-mu**2),kind="stable")[:1600]]
        chosen=np.random.default_rng(20260926).permutation(chosen)
        cids,tids,yids=chosen[:640],chosen[640:1408],chosen[1408:1600]
        assert len(set(cids)&set(tids))==len(set(cids)&set(yids))==len(set(tids)&set(yids))==0
        C=norm_view(full[:,cids].toarray())
        T=norm_view(full[:,tids].toarray())
        Y=norm_view(full[:,yids].toarray())
        freq=meta.iloc[tr].native_class.value_counts()
        rare_labels=set(freq[(freq>=8)&(freq<=max(20,int(.018*len(tr))))].index)
        rare=meta.iloc[te].native_class.isin(rare_labels).to_numpy()
        pilot=PCA(n_components=8,svd_solver="randomized",random_state=seed)
        latent=pilot.fit_transform(C[tr])
        dist=np.linalg.norm(latent/(pilot.singular_values_/np.sqrt(max(1,len(tr)-1))).clip(min=1e-2),axis=1)
        tail=np.flatnonzero(dist>=np.quantile(dist,.9))
        arms={}
        arms["R_SINGLE_RICH_V5_LINEAR_PROXY"]=head(np.hstack([C[tr],T[tr]]),
            np.hstack([C[te],T[te]]),LAT,seed)
        arms["A_SINGLE_COMPLEMENTARY"]=head(T[tr],T[te],LAT,seed)
        trunk=PCA(n_components=64,svd_solver="randomized",random_state=seed)
        trunk_tr=trunk.fit_transform(T[tr]).astype(np.float32)
        trunk_te=trunk.transform(T[te]).astype(np.float32)
        btr=[];bte=[];ctr=[];cte=[]
        for i in range(3):
            group=T[:,i*256:(i+1)*256]
            basis=PCA(n_components=16,svd_solver="randomized",random_state=seed+i)
            target=basis.fit_transform(group[tr])
            testtarget=basis.transform(group[te])
            reg=Ridge(alpha=ALPHA).fit(trunk_tr,target)
            x,y=whiten(reg.predict(trunk_tr).astype(np.float32),
                       reg.predict(trunk_te).astype(np.float32))
            btr.append(x);bte.append(y)
            x,y=head(group[tr],group[te],16,seed+i)
            ctr.append(x);cte.append(y)
        arms["B_SHARED_TRUNK_THREE_HEADS"]=(np.hstack(btr),np.hstack(bte))
        arms["C_INDEPENDENT_CORE_FINE_RARE"]=(np.hstack(ctr),np.hstack(cte))
        tail_model=PCA(n_components=16,svd_solver="randomized",random_state=seed+99)
        tail_model.fit(T[tr[tail],512:768])
        tail_tr,tail_te=whiten(tail_model.transform(T[tr,512:768]),tail_model.transform(T[te,512:768]))
        arms["D_INDEPENDENT_WITH_TAIL_SPECIALIST"]=(np.hstack([ctr[0],ctr[1],tail_tr]),
                                                     np.hstack([cte[0],cte[1],tail_te]))
        ctrain,ctest=whiten(C[tr],C[te])
        yvar=Y[tr].var(0).clip(min=.1)
        control=Ridge(alpha=ALPHA).fit(ctrain,Y[tr])
        direct=score(Y[te],control.predict(ctest),yvar,meta.iloc[te].donor_id.to_numpy(),rare)
        for arm,(ztr,zte) in arms.items():
            student=Ridge(alpha=ALPHA).fit(ctrain,ztr)
            student_tr=student.predict(ctrain);student_te=student.predict(ctest)
            probe=Ridge(alpha=ALPHA).fit(student_tr,Y[tr])
            met=score(Y[te],probe.predict(student_te),yvar,meta.iloc[te].donor_id.to_numpy(),rare)
            oracle=Ridge(alpha=ALPHA).fit(ztr,Y[tr])
            omet=score(Y[te],oracle.predict(zte),yvar,meta.iloc[te].donor_id.to_numpy(),rare)
            runs.append({"seed":seed,"arm":arm,"holdout_donors":len(testdon),
                "test_cells":len(te),"train_cells":len(tr),"rare_labels_n":len(rare_labels),
                "rare_test_cells":int(rare.sum()),"rare_test_donors":met["rare_test_donors"],
                "independent_Y_donor_equal_R2":met["donor_equal_r2"],
                "independent_Y_rare_subgroup_R2":met["rare_subgroup_r2"],
                "teacher_oracle_independent_Y_R2":omet["donor_equal_r2"],
                "student_teacher_latent_R2":float(1-np.mean((student_te-zte)**2)/
                    np.maximum(np.mean(zte**2),1e-6)),
                "direct_C_to_Y_baseline_R2":direct["donor_equal_r2"]})
            per_donor.append({"seed":seed,"arm":arm,"per_donor_mse":met["per_donor_loss"]})
        splits.append({"seed":seed,"train_cells":len(tr),"test_cells":len(te),
            "train_donors":int(meta.iloc[tr].donor_id.nunique()),"test_donors":len(testdon),
            "rare_labels":len(rare_labels),"rare_test_cells":int(rare.sum()),
            "tail_train_rows":len(tail),"panel_C":640,"panel_T":768,"panel_Y":192,
            "seconds":round(time.monotonic()-start,2)})
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(runs).to_csv(out/"tournament_scores_v1.csv",index=False)
    (out/"per_donor_replay_v1.json").write_text(json.dumps(per_donor,sort_keys=True)+"\n")
    report={"schema":"JEPA_V44_HISTORICAL_DISCOVERY_TINY_TEACHER_TEAM_SCREEN_V1",
       "status":"EXPLORATORY_LINEAR_PROXY_NOT_CURRENT_V5_NEURAL_TRAINING",
       "originals":{"expression_npz_sha256":EXPR_SHA,"sample_freeze_csv_sha256":META_SHA},
       "population":"FIRST_2600_HISTORICAL_SAMPLE_A_NATURAL_MIXTURE__ORIGINAL_T1_EXCLUDED",
       "seeds":SEEDS,"q_ids_excluded_from_all_views":QS,"target_rank_each":LAT,
       "ridge_alpha":ALPHA,"train_only_variable_gene_selection":True,
       "teacher_C_T_denominator":"independent visible-only within-view normalization",
       "scientific_caveats":["R sees C+T while A/B/C/D see T only: R has unequal teacher information",
         "All five are PCA+ridge surrogates, not actual current V5 IPBEncoder or EMA JEPA",
         "Rare labels are RNA-derived native-class descriptive groups, not independent rare biology",
         "Output dimensions equal 48 but parameters/training compute unequal",
         "Independent Y is nonoverlapping RNA genes from same cell, NOT independent external biology",
         "Both q addresses excluded; query-specific fidelity is unmeasured",
         "Donors may recur across three random held-out splits; no confirmatory inference",
         "Historically frozen discovery sample; not present FULL104 execution"],
       "split_summary":splits,"runs":runs,"training_authorized":False,
       "audit_b_n1_opened":False,"protected_outcomes_opened":False}
    (out/"tournament_result_v1.json").write_text(json.dumps(report,indent=2)+"\n")
    print("V44_DONE_15_EXPLORATORY_HISTORICAL_CPU_ARMS_NO_CURRENT_TRAINING")
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--prepared-dir",type=Path,required=True)
    a.add_argument("--original-calibration-zip",type=Path,required=True)
    a.add_argument("--out-dir",type=Path,required=True)
    p=a.parse_args()
    run(p.prepared_dir,p.original_calibration_zip,p.out_dir)
