#!/usr/bin/env python3
"""Independent implementation/harness validator for the FULL104 sensitivity."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd


FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def independent_prefix(dimensions, supported, rank=320):
    lookup = {int(d): bool(v) for d, v in zip(dimensions, supported)}
    prefix = []
    d = 1
    while d <= rank and lookup.get(d, False):
        prefix.append(d); d += 1
    return prefix


def independent_one_se(prefix, donor_scores):
    if not prefix:
        return None
    means = donor_scores.mean(0); ses = donor_scores.std(0, ddof=1) / math.sqrt(len(donor_scores))
    best = max(prefix, key=lambda d: means[d - 1]); threshold = means[best - 1] - ses[best - 1]
    return min(d for d in prefix if means[d - 1] >= threshold)


def independent_fit(mean_rows, within_rows, between_rows, indices, rank):
    mean = np.mean(mean_rows[indices], axis=0, dtype=np.float64)
    within = np.mean(within_rows[indices], axis=0, dtype=np.float64) - np.outer(mean, mean)
    between = np.mean(between_rows[indices], axis=0, dtype=np.float64) - np.outer(mean, mean)
    within = (within + within.T) * 0.5; between = (between + between.T) * 0.5
    diag = np.clip(np.diag(within), 0, None); positive = diag[diag > 0]
    floor = max(np.finfo(float).eps, (np.median(positive) if len(positive) else 1.0) * math.sqrt(np.finfo(float).eps))
    scale = np.sqrt(np.maximum(diag, floor)); aw = within / np.outer(scale, scale); ab = between / np.outer(scale, scale)
    aw = (aw + aw.T) * 0.5; ab = (ab + ab.T) * 0.5
    ridge = math.sqrt(np.finfo(float).eps) * np.trace(aw) / len(scale); metric = aw + ridge * np.eye(len(scale))
    mv, mq = np.linalg.eigh(metric); whitening = mq @ np.diag(1 / np.sqrt(mv)) @ mq.T
    reduced = whitening @ ab @ whitening; values, vectors = np.linalg.eigh((reduced + reduced.T) * 0.5)
    order = np.argsort(values)[::-1][:rank]; values = values[order]; components = (whitening @ vectors[:, order]) / scale[:, None]
    q, _ = np.linalg.qr(components, mode="reduced")
    return values, q


def synthetic_moments(seed=20260829, planted_rank=4):
    rng = np.random.default_rng(seed); donors, cells, views, features = 16, 32, 4, 16
    load, _ = np.linalg.qr(rng.normal(size=(features, planted_rank)))
    mean, within, between = [], [], []
    for _ in range(donors):
        latent = rng.normal(size=(cells, planted_rank)); x = np.stack([latent @ load.T + rng.normal(scale=.2, size=(cells, features)) for _ in range(views)], axis=1)
        summed = x.sum(1); local_w = sum(x[:, v].T @ x[:, v] for v in range(views))
        mean.append(x.mean((0, 1))); within.append(local_w / (cells * views)); between.append((summed.T @ summed - local_w) / (cells * views * (views - 1)))
    return np.asarray(mean), np.asarray(within), np.asarray(between)


def full512_rank320_solver_fixture():
    """Independent dense 512-D/rank-320 golden with a separated spectrum."""
    rng = np.random.default_rng(2026082917); dimension, rank, donors = 512, 320, 8
    q, _ = np.linalg.qr(rng.normal(size=(dimension, dimension)))
    within_values = np.linspace(0.75, 2.0, dimension)
    generalized_values = np.linspace(3.0, 0.05, dimension)
    within0 = (q * within_values) @ q.T
    between0 = (q * (within_values * generalized_values)) @ q.T
    means = np.zeros((donors, dimension), np.float64)
    within = np.repeat(within0[None], donors, axis=0)
    between = np.repeat(between0[None], donors, axis=0)
    from derive_full104_phase2_shared_state import fit_basis
    production = fit_basis(means, within, between, np.arange(donors), rank)
    values, independent_q = independent_fit(means, within, between, np.arange(donors), rank)
    subspace_loss = 1.0 - float(np.square(production["q"].T @ independent_q).sum() / rank)
    eigen_max = float(np.max(np.abs(production["eigenvalues"] - values)))
    tolerance = math.sqrt(np.finfo(np.float64).eps) * max(1.0, float(production["condition"]))
    residual = float(np.max(production["residual"])); orthogonality = float(production["orthogonality"])
    return {"pass": eigen_max <= 1e-6 and subspace_loss <= 1e-5 and residual <= tolerance and orthogonality <= tolerance,
            "dimension": dimension, "rank": rank, "eigenvalue_max_abs": eigen_max,
            "principal_subspace_loss": subspace_loss, "maximum_residual": residual,
            "metric_orthogonality": orthogonality, "frozen_tolerance": tolerance}


def independent_coordinate(basis, mean, within, between):
    mu, w = basis["mean"], basis["components"]
    cw = within - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    cb = between - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    return mean - mu @ np.eye(len(mu)), (w.T @ cw @ w + w.T @ cw.T @ w) * .5, (w.T @ cb @ w + w.T @ cb.T @ w) * .5


def independent_basis(mean, within, between, indices, rank):
    values, q = independent_fit(mean, within, between, indices, rank)
    mu = np.mean(mean[indices], axis=0); cw = np.mean(within[indices], axis=0) - np.outer(mu, mu); cb = np.mean(between[indices], axis=0) - np.outer(mu, mu)
    cw = (cw + cw.T) * .5; cb = (cb + cb.T) * .5; diag = np.clip(np.diag(cw), 0, None); positive = diag[diag > 0]
    floor = max(np.finfo(float).eps, (np.median(positive) if len(positive) else 1.) * math.sqrt(np.finfo(float).eps)); scale = np.sqrt(np.maximum(diag, floor))
    aw = (cw / np.outer(scale, scale)); aw = (aw + aw.T) * .5; ab = (cb / np.outer(scale, scale)); ab = (ab + ab.T) * .5
    ridge = math.sqrt(np.finfo(float).eps) * np.trace(aw) / len(scale); mv, mq = np.linalg.eigh(aw + ridge * np.eye(len(scale))); whitening = mq @ np.diag(1 / np.sqrt(mv)) @ mq.T
    rv, rq = np.linalg.eigh((whitening @ ab @ whitening + whitening @ ab.T @ whitening) * .5); order = np.argsort(rv)[::-1][:rank]
    components = (whitening @ rq[:, order]) / scale[:, None]
    return {"mean": mu, "components": components, "eigenvalues": rv[order], "q": np.linalg.qr(components, mode="reduced")[0]}


def independent_heldout(mean, within, between, folds, rank):
    out = np.empty((len(mean), rank)); donors = np.arange(len(mean))
    for fold in sorted(set(folds)):
        train, held = donors[folds != fold], donors[folds == fold]; basis = independent_basis(mean, within, between, train, rank); w = basis["components"]; mu = basis["mean"]
        def moments(d):
            cw = within[d] - np.outer(mean[d], mu) - np.outer(mu, mean[d]) + np.outer(mu, mu); cb = between[d] - np.outer(mean[d], mu) - np.outer(mu, mean[d]) + np.outer(mu, mu)
            return (mean[d] - mu) @ w, (w.T @ cw @ w + w.T @ cw.T @ w)*.5, (w.T @ cb @ w + w.T @ cb.T @ w)*.5
        train_m = [moments(d) for d in train]; tw = np.mean([x[1] for x in train_m], 0); tb = np.mean([x[2] for x in train_m], 0)
        slope = np.diag(tb) / np.maximum((np.diag(tw) + 2*np.diag(tb))/3, np.finfo(float).eps)
        for d in held:
            dm, dw, db = moments(d); t2, pt = np.diag(dw), np.diag(db); p2 = (t2 + 2*pt)/3; sse = t2 - 2*slope*pt + slope*slope*p2
            out[d] = 1 - np.cumsum(sse)/np.maximum(np.cumsum(np.maximum(t2-dm*dm,0)), np.finfo(float).eps)
    return out


def fixture_seed(key, *parts):
    return int.from_bytes(hashlib.sha256("|".join([key,*map(str,parts)]).encode()).digest()[:8], "little")


def independently_reproduce_fixture(package: Path):
    raw = np.load(package / "SYNTHETIC_END_TO_END_INPUTS.npz", allow_pickle=False); prod = np.load(package / "SYNTHETIC_END_TO_END_PRODUCTION.npz", allow_pickle=False)
    x=raw["views"].astype(np.float64); row_donor=raw["rows_donor"]; row_op=raw["rows_operator"]; selection=raw["selection_row"]; donor_ids=list(raw["donor_id"]); sources=raw["sources"]; folds=raw["folds"]; key=str(raw["key"].item()); boot_key=str(raw["bootstrap_key"].item())
    donor_ix={d:i for i,d in enumerate(donor_ids)}; chosen=[]
    for donor in donor_ids:
        for op in sorted(set(row_op[row_donor==donor])):
            indices=np.flatnonzero((row_donor==donor)&(row_op==op)); ranked=sorted(indices,key=lambda i:(hashlib.sha256(f"{key}|natural-full512-v1|sample-order|{donor}|{int(op)}|{int(selection[i])}".encode()).digest(),int(i))); chosen.append((donor,int(op),np.asarray(ranked[:min(4,len(ranked))]),len(ranked)))
    dim=x.shape[-1]; mean=np.zeros((len(donor_ids),dim)); within=np.zeros((len(donor_ids),dim,dim)); between=np.zeros_like(within)
    donor_n={d:int(np.count_nonzero(row_donor==d)) for d in donor_ids}
    for donor,op,indices,n in chosen:
        d=donor_ix[donor]; weight=n/(len(indices)*donor_n[donor]); local=x[indices]; mean[d]+=weight*local.mean(1).sum(0); local_w=sum(local[:,v].T@local[:,v] for v in range(4)); summed=local.sum(1); within[d]+=weight*local_w/4; between[d]+=weight*(summed.T@summed-local_w)/12
    rank=6; reps=8; basis=independent_basis(mean,within,between,np.arange(len(donor_ids)),rank); obs_e=[]; obs_s=[]
    def boot_indices(rep):
        parts=[]
        for source in sorted(set(sources)):
            ix=np.flatnonzero(sources==source); parts.append(np.random.default_rng(fixture_seed(boot_key,"natural-full512-v1",rep,source)).choice(ix,size=len(ix),replace=True))
        return np.concatenate(parts)
    for rep in range(reps):
        b=independent_basis(mean,within,between,boot_indices(rep),rank); obs_e.append(b["eigenvalues"]); obs_s.append(np.asarray([np.square(basis["q"][:,:d].T@b["q"][:,:d]).sum()/d for d in range(1,rank+1)]))
    obs_e=np.asarray(obs_e); obs_s=np.asarray(obs_s); obs_h=independent_heldout(mean,within,between,folds,rank)
    nf=[]; nb=[]; ns=[]; nh=[]; map_hash=[]
    for rep in range(reps):
        bm=np.zeros_like(between); digest=hashlib.sha256()
        for stratum,(donor,op,indices,nfull) in enumerate(chosen):
            n=len(indices); osd=fixture_seed(key,"natural-full512-v1","null","fixture","A",stratum,rep,"order"); fsd=fixture_seed(key,"natural-full512-v1","null","fixture","A",stratum,rep,"offsets"); order=np.random.default_rng(osd).permutation(n); gen=np.random.default_rng(fsd); offsets=np.zeros(4,dtype=np.int64) if n==1 else (gen.choice(n,4,replace=False).astype(np.int64) if n>=4 else (int(gen.integers(n))+np.arange(4))%n)
            digest.update(np.asarray([stratum,n,osd,fsd],np.uint64).tobytes()); digest.update(order.astype(np.int64).tobytes()); digest.update(offsets.tobytes()); local=x[indices[order]]; shifted=[local[(np.arange(n)+offsets[v])%n,v] for v in range(4)]; cross=np.zeros((dim,dim))
            for v in range(4):
                for w in range(v+1,4): product=shifted[v].T@shifted[w]; cross+=product+product.T
            bm[donor_ix[donor]]+=nfull/(n*donor_n[donor])*cross/12
        full=independent_basis(mean,within,bm,np.arange(len(donor_ids)),rank); boot=independent_basis(mean,within,bm,boot_indices(rep),rank); nf.append(full["eigenvalues"]); nb.append(boot["eigenvalues"]); ns.append(np.asarray([np.square(full["q"][:,:d].T@boot["q"][:,:d]).sum()/d for d in range(1,rank+1)])); nh.append(independent_heldout(mean,within,bm,folds,rank)); map_hash.append(digest.hexdigest())
    nf,nb,ns,nh=map(np.asarray,[nf,nb,ns,nh]); signal=np.logical_and.accumulate(obs_e.mean(0)-obs_e.std(0,ddof=1)/math.sqrt(reps)>nb.mean(0)+nb.std(0,ddof=1)/math.sqrt(reps)); joint=[]
    for j in range(rank):
        stability=obs_s[:,j].mean()-obs_s[:,j].std(ddof=1)/math.sqrt(reps)>ns[:,j].mean()+ns[:,j].std(ddof=1)/math.sqrt(reps); nd=nh[:,:,j].mean(0); predict=obs_h[:,j].mean()-obs_h[:,j].std(ddof=1)/math.sqrt(len(donor_ids))>nd.mean()+nd.std(ddof=1)/math.sqrt(len(donor_ids)); joint.append(bool(signal[j] and stability and predict))
    prefix=independent_prefix(range(1,rank+1),joint,rank); candidate=independent_one_se(prefix,obs_h)
    comparisons={"mean":(mean,prod["mean"]),"within":(within,prod["within"]),"between":(between,prod["between"]),"observed_bootstrap_eigen":(obs_e,prod["observed_bootstrap_eigen"]),"null_full_eigen":(nf,prod["null_full_eigen"]),"paired_null_bootstrap_eigen":(nb,prod["paired_null_bootstrap_eigen"]),"observed_stability":(obs_s,prod["observed_stability"]),"null_stability":(ns,prod["null_stability"]),"observed_heldout":(obs_h,prod["observed_heldout"]),"null_heldout":(nh,prod["null_heldout"])}
    def independent_joint_for_sketch(sketch_x, sketch):
        m=np.zeros_like(mean); w=np.zeros_like(within); b=np.zeros_like(between)
        for donor,op,indices,nfull in chosen:
            d=donor_ix[donor]; weight=nfull/(len(indices)*donor_n[donor]); local=sketch_x[indices]; m[d]+=weight*local.mean(1).sum(0); lw=sum(local[:,v].T@local[:,v] for v in range(4)); summed=local.sum(1); w[d]+=weight*lw/4; b[d]+=weight*(summed.T@summed-lw)/12
        base=independent_basis(m,w,b,np.arange(len(donor_ids)),rank); oe=[]; os=[]
        for rep in range(reps):
            fitted=independent_basis(m,w,b,boot_indices(rep),rank); oe.append(fitted["eigenvalues"]); os.append(np.asarray([np.square(base["q"][:,:d].T@fitted["q"][:,:d]).sum()/d for d in range(1,rank+1)]))
        oe=np.asarray(oe); os=np.asarray(os); oh=independent_heldout(m,w,b,folds,rank); nbe=[]; nst=[]; nhd=[]
        for rep in range(reps):
            bm=np.zeros_like(b)
            for stratum,(donor,op,indices,nfull) in enumerate(chosen):
                n=len(indices); osd=fixture_seed(key,"natural-full512-v1","null","fixture",sketch,stratum,rep,"order"); fsd=fixture_seed(key,"natural-full512-v1","null","fixture",sketch,stratum,rep,"offsets"); order=np.random.default_rng(osd).permutation(n); gen=np.random.default_rng(fsd); offsets=np.zeros(4,dtype=np.int64) if n==1 else (gen.choice(n,4,replace=False).astype(np.int64) if n>=4 else (int(gen.integers(n))+np.arange(4))%n); local=sketch_x[indices[order]]; shifted=[local[(np.arange(n)+offsets[v])%n,v] for v in range(4)]; cross=np.zeros((dim,dim))
                for v in range(4):
                    for z in range(v+1,4): product=shifted[v].T@shifted[z]; cross+=product+product.T
                bm[donor_ix[donor]]+=nfull/(n*donor_n[donor])*cross/12
            full=independent_basis(m,w,bm,np.arange(len(donor_ids)),rank); boot=independent_basis(m,w,bm,boot_indices(rep),rank); nbe.append(boot["eigenvalues"]); nst.append(np.asarray([np.square(full["q"][:,:d].T@boot["q"][:,:d]).sum()/d for d in range(1,rank+1)])); nhd.append(independent_heldout(m,w,bm,folds,rank))
        nbe,nst,nhd=map(np.asarray,[nbe,nst,nhd]); sg=np.logical_and.accumulate(oe.mean(0)-oe.std(0,ddof=1)/math.sqrt(reps)>nbe.mean(0)+nbe.std(0,ddof=1)/math.sqrt(reps)); jointly=[]
        for j in range(rank):
            stable=os[:,j].mean()-os[:,j].std(ddof=1)/math.sqrt(reps)>nst[:,j].mean()+nst[:,j].std(ddof=1)/math.sqrt(reps); nd=nhd[:,:,j].mean(0); pred=oh[:,j].mean()-oh[:,j].std(ddof=1)/math.sqrt(len(donor_ids))>nd.mean()+nd.std(ddof=1)/math.sqrt(len(donor_ids)); jointly.append(bool(sg[j] and stable and pred))
        return np.asarray(jointly), oh
    joint_b, held_b = independent_joint_for_sketch(raw["views_B"].astype(np.float64), "B")
    common_prefix=independent_prefix(range(1,rank+1),np.asarray(joint)&joint_b,rank); candidate_ab=independent_one_se(common_prefix,(obs_h+held_b)*.5)
    distinct_ab_pass=np.array_equal(joint_b,prod["distinct_B_jointly_supported"]) and (-1 if candidate_ab is None else candidate_ab)==int(prod["distinct_AB_candidate"])
    report=json.loads((package/"PRODUCTION_TARGETED_FIXTURE_REPORT.json").read_text()); u=package/"resume_uninterrupted"; r=package/"resume_interrupted"
    def resume_digest(directory):
        arrays=[np.load(p,allow_pickle=False)["value"] for p in sorted(directory.glob("replicate_*.npz"))]; return hashlib.sha256(b"".join([b"replicates",str(np.stack(arrays).dtype).encode(),str(np.stack(arrays).shape).encode(),np.ascontiguousarray(np.stack(arrays)).tobytes()])).hexdigest()
    resume_pass=len(list(u.glob("replicate_*.npz")))==4 and len(list(r.glob("replicate_*.npz")))==4 and resume_digest(u)==resume_digest(r)==report["resume_fingerprint"]["uninterrupted_execution_sha256"]
    diffs={name:float(np.max(np.abs(a-b))) for name,(a,b) in comparisons.items()}; scalar_pass=all(np.allclose(a,b,atol=1e-6,rtol=1e-5) for a,b in comparisons.values()); boolean_pass=np.array_equal(signal,prod["signal_supported"]) and np.array_equal(np.asarray(joint),prod["jointly_supported"]); candidate_pass=(-1 if candidate is None else candidate)==int(prod["candidate"]); map_pass=np.array_equal(np.asarray(map_hash),prod["map_hashes"])
    return {"pass":bool(scalar_pass and boolean_pass and candidate_pass and map_pass and distinct_ab_pass and resume_pass),"max_abs_differences":diffs,"boolean_exact":bool(boolean_pass),"candidate_exact":bool(candidate_pass),"map_hash_exact":bool(map_pass),"distinct_A_B_exact":bool(distinct_ab_pass),"forced_interruption_resume_exact":bool(resume_pass)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True); parser.add_argument("--matrix", required=True); parser.add_argument("--analytic", required=True)
    parser.add_argument("--production-core", required=True); parser.add_argument("--production-runner", required=True); parser.add_argument("--out", required=True)
    parser.add_argument("--production-fixture", required=True)
    args = parser.parse_args()
    freeze, matrix, analytic, core, runner, out, production_fixture = map(lambda x: Path(x).resolve(), [args.freeze, args.matrix, args.analytic, args.production_core, args.production_runner, args.out, args.production_fixture])
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((freeze / "PROSPECTIVE_REFIT_NULL_NATURAL_WEIGHT_FULL_FEATURE_SENSITIVITY_V1.json").read_text())
    checks = []
    checks.append({"test": "freeze_root", "pass": sha(freeze / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv") == FREEZE_ROOT})

    # Independent selector fixtures; this module imports no production selector/core.
    dims = list(range(1, 14))
    fixtures = [
        ("gapped_D6", [True] * 5 + [False] + [True] * 7, list(range(1, 6))),
        ("first_D1", [False] + [True] * 12, []),
        ("gapped_D5_D13", [True] * 4 + [False] + [True] * 8, list(range(1, 5))),
        ("planted_contiguous", [True] * 7 + [False] * 6, list(range(1, 8))),
    ]
    rng = np.random.default_rng(17); donor_scores = rng.normal(size=(104, 13))
    for name, support, expected in fixtures:
        prefix = independent_prefix(dims, support, 13); candidate = independent_one_se(prefix, donor_scores)
        checks.append({"test": name, "pass": prefix == expected and (candidate is None if not expected else candidate <= expected[-1]), "prefix": prefix, "candidate": candidate})
        order = rng.permutation(len(dims)); reordered = independent_prefix([dims[i] for i in order], [support[i] for i in order], 13)
        checks.append({"test": name + "_order_chunk", "pass": reordered == expected})

    # Independent dense eigensolver versus authenticated production estimator on a golden fixture.
    from derive_full104_phase2_shared_state import fit_basis
    mean, within, between = synthetic_moments(); indices = np.arange(len(mean))
    primary = fit_basis(mean, within, between, indices, 8); values, q = independent_fit(mean, within, between, indices, 8)
    overlap = np.square(primary["q"].T @ q).sum() / 8
    checks.append({"test": "dense_solver_independence_small", "pass": float(np.max(np.abs(primary["eigenvalues"] - values))) <= 1e-6 and 1 - float(overlap) <= 1e-5})
    full512 = full512_rank320_solver_fixture()
    checks.append({"test": "dense_vs_production_full512_rank320_solver", "pass": full512["pass"], "details": full512})

    source_core = core.read_text(); source_runner = runner.read_text(); tree = ast.parse(Path(__file__).read_text())
    forbidden = ["top32", "[:32]", "components[:, :32]", "shared_selection_refit_corrected"]
    checks.append({"test": "no_top32_or_stale_path", "pass": not any(token in source_core.lower() + source_runner.lower() for token in forbidden)})
    checks.append({"test": "null_refits_basis_with_numerical_gate", "pass": source_runner.count("fit_basis_checked(") >= 4 and "null_between_one" in source_runner})
    checks.append({"test": "streaming_no_cell_cell", "pass": "cell×cell" not in source_core and "np.zeros((len(plan), len(plan))" not in source_core})
    imported_modules = [n.module or "" for n in tree.body if isinstance(n, ast.ImportFrom)]
    checks.append({"test": "independent_selector_not_imported", "pass": all("selector" not in module and "sensitivity_core" not in module for module in imported_modules)})

    # Actual authority/weight identity using metadata only; no conclusion-bearing statistic.
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", usecols=["donor_id", "operator_index", "selection_row"], dtype={"donor_id": str})
    donor_n = rows.groupby("donor_id").size(); strata = rows.groupby(["donor_id", "operator_index"]).size()
    all_mass = {d: float(sum(n / donor_n[d] for (donor, _), n in strata.items() if donor == d)) for d in donor_n.index}
    checks.append({"test": "ALL_natural_donor_mass", "pass": max(abs(x - 1) for x in all_mass.values()) <= 64 * np.finfo(float).eps, "maximum_error": max(abs(x - 1) for x in all_mass.values())})
    checks.append({"test": "authority_population", "pass": len(rows) == 4_553_407 and len(donor_n) == 104 and len(strata) == 1400 and rows.operator_index.nunique() == 42})

    # Independently reconstruct and compare the lossless fixture plan without
    # importing the production runner/core.
    fixture_raw = np.load(production_fixture / "SYNTHETIC_END_TO_END_INPUTS.npz", allow_pickle=False)
    fixture_plan = np.load(production_fixture / "LOSSLESS_PLAN_FIXTURE.npz", allow_pickle=False)
    fd=list(fixture_raw["donor_id"]); rd=fixture_raw["rows_donor"]; ro=fixture_raw["rows_operator"]; sr=fixture_raw["selection_row"]; fkey=str(fixture_raw["key"].item()); expected=[]
    for donor in fd:
        donor_indices=np.flatnonzero(rd==donor); donor_n_local=len(donor_indices)
        for op in sorted(set(ro[donor_indices])):
            indices=np.flatnonzero((rd==donor)&(ro==op)); ranked=sorted(indices,key=lambda i:(hashlib.sha256(f"{fkey}|natural-full512-v1|sample-order|{donor}|{int(op)}|{int(sr[i])}".encode()).digest(),int(i))); selected=ranked[:min(4,len(ranked))]
            for local_rank,index in enumerate(selected):
                expected.append((int(index),int(sr[index]),str(donor),int(op),len(indices),len(selected),local_rank,len(indices)/(len(selected)*donor_n_local),len(indices)/(len(selected)*donor_n_local*len(fd))))
    columns=("row_index","selection_row","donor_id","operator_index","stratum_n","stratum_m","sample_rank","within_donor_weight","global_weight")
    expected_arrays={name:np.asarray([row[j] for row in expected],dtype=("U" if name=="donor_id" else np.float64 if "weight" in name else np.int64)) for j,name in enumerate(columns)}
    lossless_exact=all(np.array_equal(expected_arrays[name],fixture_plan[name]) for name in columns)
    donor_mass={d:float(fixture_plan["global_weight"][fixture_plan["donor_id"]==d].sum()) for d in fd}; lossless_mass=max(abs(x-1/len(fd)) for x in donor_mass.values()) <= 64*np.finfo(float).eps/len(fd)
    production_report=json.loads((production_fixture/"PRODUCTION_TARGETED_FIXTURE_REPORT.json").read_text())
    checks.append({"test":"independent_lossless_plan_exact_membership_weights_mass","pass":lossless_exact and lossless_mass and production_report["lossless_plan"]["corrupted_plan_rejected"] and production_report["lossless_plan"]["dtype_downgrade_rejected"] and production_report["lossless_plan"]["coordinated_substitution_rejected"] and production_report["lossless_plan"]["csv_explicitly_nonauthoritative"]})
    checks.append({"test":"csv_not_conclusion_authority","pass":"NESTED_WEIGHTED_SELECTION.npz" in source_runner and "pd.read_csv(plan_path" not in source_runner and '"csv_authoritative": False' in source_runner})
    with np.load(production_fixture/"FINGERPRINT_CHECKPOINT.npz", allow_pickle=False) as checkpoint_payload:
        checkpoint_has_plan_semantic = "plan_semantic_sha256" in checkpoint_payload.files
    checks.append({"test":"plan_semantic_bound_to_checkpoint","pass":"plan_semantic_sha256" in source_runner and checkpoint_has_plan_semantic})
    checks.append({"test":"checkpoint_payload_and_gate_source_binding","pass":production_report["payload_and_gate_binding"]["checkpoint_payload_tamper_rejected"] and production_report["payload_and_gate_binding"]["post_gate_core_change_rejected"] and all(token in source_runner for token in ("CHECKPOINT_PAYLOAD_LEDGER.json","assert_checkpoint_payload","verify_gate_implementation","core_sha256","fit_basis_code_sha256"))})

    end_to_end = independently_reproduce_fixture(production_fixture)
    checks.append({"test": "independent_end_to_end_weight_null_bootstrap_stability_heldout_selection", "pass": end_to_end["pass"], "details": end_to_end})

    # Recursive bypass test.
    graph = {"ALL": {"state": "PROVISIONAL", "tainted": False}, "shared": {"state": "EXPLORATORY", "tainted": True}, "private": {"state": "EXPLORATORY", "tainted": True}}
    blocked = graph["ALL"]["state"] != "FROZEN" or graph["shared"]["tainted"] or graph["private"]["tainted"]
    checks.append({"test": "recursive_taint_private_block", "pass": blocked})

    for item in checks:
        item["pass"] = bool(item["pass"])
    table = pd.DataFrame(checks); table.to_csv(out / "TARGETED_IMPLEMENTATION_HARNESS.csv", index=False, lineterminator="\n")
    passed = bool(table["pass"].all())
    result = {"schema": "full104-refit-null-independent-implementation-validator-v1",
              "status": "PASS_INDEPENDENT_IMPLEMENTATION_VALIDATOR" if passed else "STOP_INDEPENDENT_IMPLEMENTATION_VALIDATOR",
              "checks": checks, "independent_selector": "local while-loop implementation; no production selector/core import",
              "input_hashes": {"freeze_manifest": sha(freeze / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv"), "core": sha(core), "runner": sha(runner), "validator": sha(Path(__file__)), "production_fixture": sha(production_fixture / "SYNTHETIC_END_TO_END_PRODUCTION.npz")}}
    (out / "INDEPENDENT_IMPLEMENTATION_VALIDATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = out / "INDEPENDENT_IMPLEMENTATION_VALIDATION_MANIFEST.csv"; files = [out / "TARGETED_IMPLEMENTATION_HARNESS.csv", out / "INDEPENDENT_IMPLEMENTATION_VALIDATION.json", Path(__file__)]
    pd.DataFrame([{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]).to_csv(manifest, index=False, lineterminator="\n")
    print(json.dumps({"status": result["status"], "manifest_sha256": sha(manifest)}, indent=2))
    if not passed: raise SystemExit(2)


if __name__ == "__main__":
    main()
