"""Provisional pathology-blind Stage81A3R global-state audit on foundation TRAIN RNA."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.utils.extmath import randomized_svd

from sea_ad_jepa.v4.a3r_global_state import (
    contiguous_tail_decisions,
    masked_reconstruction_r2,
    one_standard_error_prefix,
    raw_paired_r2,
    stable_fold,
    subspace_metrics,
)

STATUS = "GLOBAL_STATE_PILOT_INPUT_CONTRACT_LIMITED"
FORBIDDEN = ("pathology", "diagnosis", "braak", "cerad", "amyloid", "disease")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n"); temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, frame: pd.DataFrame, *, compress: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".csv.gz" if compress else ".csv"
    descriptor, name = tempfile.mkstemp(dir=path.parent, suffix=suffix)
    os.close(descriptor)
    temporary = Path(name)
    if compress:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    frame.to_csv(text, index=False, lineterminator="\n")
    else:
        frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def h5_vector(group: h5py.Group, key: str) -> np.ndarray:
    node = group[key]
    if isinstance(node, h5py.Dataset):
        values = node[:]
    elif "categories" in node and "codes" in node:
        categories = node["categories"][:]
        values = categories[node["codes"][:]]
    else:
        raise RuntimeError(f"unsupported HDF5 vector: {group.name}/{key}")
    return np.asarray([item.decode() if isinstance(item, bytes) else str(item) for item in values])


def balanced_rows(donors: np.ndarray, cells: np.ndarray, cap: int, seed: int) -> np.ndarray:
    groups: dict[str, list[tuple[str, int]]] = {}
    for index, (donor, cell) in enumerate(zip(donors, cells, strict=True)):
        key = hashlib.sha256(f"{seed}|{donor}|{cell}".encode()).hexdigest()
        groups.setdefault(str(donor), []).append((key, index))
    for values in groups.values(): values.sort()
    selected: list[int] = []
    depth = 0
    while len(selected) < min(cap, len(donors)):
        added = False
        for donor in sorted(groups):
            if depth < len(groups[donor]):
                selected.append(groups[donor][depth][1]); added = True
                if len(selected) == min(cap, len(donors)): break
        if not added: break
        depth += 1
    return np.asarray(selected, dtype=np.int64)


def train_donors(split: pd.DataFrame) -> dict[str, set[str]]:
    subset = split[(split.split_domain == "foundation") & (split.split == "train")]
    result: dict[str, set[str]] = {}
    for study, group in subset.groupby("study_id"):
        result[str(study)] = {str(value).split("::", 1)[-1] for value in group.canonical_person_id}
    if {key: len(value) for key, value in result.items()} != {"HVS": 62, "NPH52": 19, "SEA_AD": 68}:
        raise RuntimeError("frozen TRAIN donor contract mismatch")
    return result


def extract_h5(
    source: Path, cache: Path, asset: Any, contract: Any, provenance: pd.DataFrame,
    donors_allowed: set[str], cap: int, seed: int,
) -> dict[str, Any]:
    matrix_id, study = str(asset.dataset_id), str(asset.study_id)
    stem = hashlib.sha256(matrix_id.encode()).hexdigest()[:16]
    counts_path, meta_path = cache / f"{stem}.counts.npz", cache / f"{stem}.meta.npz"
    if counts_path.exists() and meta_path.exists():
        meta = np.load(meta_path, allow_pickle=False)
        return {"matrix_id": matrix_id, "study_id": study, "counts": counts_path, "meta": meta_path,
                "rows": int(len(meta["donor_id"])), "reused": True, "logical_path": str(asset.matrix_path_or_object)}
    source_key = "HVS_COMMON" if study == "HVS" else "SEA_AD_COMMON"
    mapping = provenance[provenance.source_dataset_id.eq(source_key)].sort_values("source_feature_index")
    if mapping.source_feature_index.duplicated().any(): raise RuntimeError(f"noninjective source mapping: {source_key}")
    donor_key = "donor_id" if study == "HVS" else "Donor ID"
    cell_key = "exp_component_name"
    class_key, fallback = "Class", "Subclass"
    with h5py.File(source / str(asset.matrix_path_or_object), "r") as handle:
        donors = h5_vector(handle["obs"], donor_key); cells = h5_vector(handle["obs"], cell_key)
        eligible = np.where(np.isin(donors, sorted(donors_allowed)))[0]
        local = balanced_rows(donors[eligible], cells[eligible], cap, seed); rows = eligible[local]
        classes = h5_vector(handle["obs"], class_key) if class_key in handle["obs"] else h5_vector(handle["obs"], fallback)
        node = handle[str(contract.matrix_slot)]
        indptr, indices, data = node["indptr"], node["indices"], node["data"]
        source_to_address = dict(zip(mapping.source_feature_index.astype(int), mapping.molecular_address_index.astype(int)))
        out_rows: list[int] = []; out_cols: list[int] = []; out_data: list[int] = []; totals = []
        for output_row, source_row in enumerate(rows):
            start, end = int(indptr[source_row]), int(indptr[source_row + 1])
            columns = np.asarray(indices[start:end], dtype=np.int64); values = np.asarray(data[start:end])
            if np.any(values < 0) or not np.allclose(values, np.rint(values)): raise RuntimeError("noninteger count matrix")
            totals.append(int(np.rint(values).sum()))
            for column, value in zip(columns, values, strict=True):
                target = source_to_address.get(int(column))
                if target is not None and value:
                    out_rows.append(output_row); out_cols.append(target); out_data.append(int(round(float(value))))
    matrix = sparse.csr_matrix((out_data, (out_rows, out_cols)), shape=(len(rows), 41238), dtype=np.int32)
    sparse.save_npz(counts_path, matrix, compressed=True)
    np.savez_compressed(meta_path, donor_id=donors[rows].astype("U"), cell_id=cells[rows].astype("U"),
                        broad_cell_class=classes[rows].astype("U"), source_library=np.asarray(totals, dtype=np.int64))
    return {"matrix_id": matrix_id, "study_id": study, "counts": counts_path, "meta": meta_path,
            "rows": len(rows), "reused": False, "logical_path": str(asset.matrix_path_or_object)}


def extract_nph(source: Path, cache: Path, config: dict[str, Any], address_index: dict[str, int], train: set[str]) -> list[dict[str, Any]]:
    cells_path = source / config["inputs"]["nph_train_cells"]
    nonzero_path = source / config["inputs"]["nph_train_nonzero"]
    if not cells_path.exists() or not nonzero_path.exists():
        raise RuntimeError("pre-existing NPH TRAIN-only cache missing")
    cells = pd.read_csv(cells_path)
    if not set(cells.donor_id.astype(str)) <= train: raise RuntimeError("NPH cache contains non-TRAIN donor")
    nonzero = pd.read_csv(nonzero_path)
    results = []
    for source_id, group in cells.groupby("source_dataset_id", sort=True):
        source_id = str(source_id)
        matrix_id = "NPH52::matrix::" + source_id.split("::", 1)[1]
        stem = hashlib.sha256(matrix_id.encode()).hexdigest()[:16]
        counts_path, meta_path = cache / f"{stem}.counts.npz", cache / f"{stem}.meta.npz"
        order = group.reset_index(drop=True); row_map = {cell: i for i, cell in enumerate(order.cell_id.astype(str))}
        selected = nonzero[nonzero.cell_id.astype(str).isin(row_map)]
        rows = selected.cell_id.astype(str).map(row_map).to_numpy(int)
        columns = selected.canonical_ensembl_gene_id.astype(str).map(address_index)
        if columns.isna().any(): raise RuntimeError("NPH cache contains non-registry address")
        matrix = sparse.csr_matrix((selected.raw_count.to_numpy(np.int32), (rows, columns.to_numpy(int))), shape=(len(order), 41238))
        sparse.save_npz(counts_path, matrix, compressed=True)
        np.savez_compressed(meta_path, donor_id=order.donor_id.astype(str).to_numpy(dtype="U"),
                            cell_id=order.cell_id.astype(str).to_numpy(dtype="U"),
                            broad_cell_class=order.broad_cell_class.astype(str).to_numpy(dtype="U"),
                            source_library=order.raw_library_total.to_numpy(np.int64))
        results.append({"matrix_id": matrix_id, "study_id": "NPH52", "counts": counts_path, "meta": meta_path,
                        "rows": len(order), "reused": False, "logical_path": f"NPH52::{order.source_object.iloc[0]}"})
    return results


def count_views(counts: sparse.csr_matrix, totals: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed); first = counts.copy()
    first.data = rng.binomial(first.data.astype(np.int64), 0.5).astype(np.int32); first.eliminate_zeros()
    second = counts - first
    outside = totals - np.asarray(counts.sum(1)).ravel()
    if np.any(outside < 0): raise RuntimeError("address counts exceed source library")
    outside_first = rng.binomial(outside.astype(np.int64), 0.5)
    first_total = np.asarray(first.sum(1)).ravel() + outside_first
    second_total = np.asarray(second.sum(1)).ravel() + outside - outside_first
    def norm(matrix: sparse.csr_matrix, library: np.ndarray) -> np.ndarray:
        scaled = matrix.multiply((10_000.0 / np.maximum(library, 1))[:, None]).tocsr().astype(np.float32)
        scaled.data = np.log1p(scaled.data); return scaled.toarray()
    return norm(counts, totals), norm(first, first_total), norm(second, second_total)


def parameters(full: np.ndarray, a: np.ndarray, b: np.ndarray, measured: np.ndarray, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    support = measured[rows]; n = support.sum(0).astype(np.float64)
    total = full[rows].sum(0, dtype=np.float64); square = np.square(full[rows], dtype=np.float64).sum(0)
    mean = np.divide(total, n, out=np.zeros_like(total), where=n > 0)
    variance = np.divide(square, n, out=np.zeros_like(square), where=n > 0) - mean * mean
    std = np.sqrt(np.maximum(variance, 1e-6))
    aa, bb = a[rows], b[rows]; sa = aa.sum(0, dtype=np.float64); sb = bb.sum(0, dtype=np.float64)
    cross = (aa.astype(np.float64) * bb).sum(0); saa = np.square(aa, dtype=np.float64).sum(0); sbb = np.square(bb, dtype=np.float64).sum(0)
    covariance = cross - sa * sb / np.maximum(n, 1)
    denominator = np.sqrt(np.maximum(saa - sa * sa / np.maximum(n, 1), 0) * np.maximum(sbb - sb * sb / np.maximum(n, 1), 0))
    weight = np.clip(np.divide(covariance, denominator, out=np.zeros_like(covariance), where=denominator > 0), 0.0, 1.0)
    return mean.astype(np.float32), std.astype(np.float32), weight.astype(np.float32)


def transform(values: np.ndarray, measured: np.ndarray, mean: np.ndarray, std: np.ndarray, weight: np.ndarray) -> np.ndarray:
    return (((values - mean) / std) * measured * np.sqrt(weight)).astype(np.float32)


def fit_basis(x: np.ndarray, matrix_ids: np.ndarray, dimensions: int, seed: int, oversamples: int, iterations: int) -> tuple[np.ndarray, np.ndarray]:
    scaled = x.copy()
    for matrix in np.unique(matrix_ids):
        idx = matrix_ids == matrix; scaled[idx] *= np.sqrt(len(scaled) / (len(idx.nonzero()[0]) * len(np.unique(matrix_ids))))
    _, singular, vt = randomized_svd(scaled, n_components=dimensions, n_oversamples=oversamples,
                                      n_iter=iterations, random_state=seed, flip_sign=True)
    return vt.T.astype(np.float32), singular.astype(np.float64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_real_train_global_state.yaml"))
    args = parser.parse_args(); project = args.project_dir.resolve(); source = (args.source_project or project).resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8")); outputs = {k: project / v for k, v in config["outputs"].items()}
    if any(term in json.dumps(config).lower() for term in FORBIDDEN):
        # Governance labels are allowed; no input path or metadata field may contain them.
        if any(term in json.dumps(config["inputs"]).lower() for term in FORBIDDEN): raise RuntimeError("forbidden input configured")
    registry = pd.read_csv(source / config["inputs"]["address_registry"])
    audit = json.loads((source / config["inputs"]["injectivity_audit"]).read_text())
    if len(registry) != 41238 or audit["registry_semantic_hash"] != config["frozen_address_semantic_hash"]: raise RuntimeError("frozen address contract mismatch")
    split = pd.read_csv(source / config["inputs"]["split_registry"]); train = train_donors(split)
    assets = pd.read_csv(source / config["inputs"]["assets"]); semantics = pd.read_csv(source / config["inputs"]["matrix_semantics"])
    provenance = pd.read_csv(source / config["inputs"]["source_provenance"], low_memory=False)
    support_frame = pd.read_csv(source / config["inputs"]["measurement_support"])
    cache = source / config["cache_dir"]; cache.mkdir(parents=True, exist_ok=True)
    inventory = []
    for asset in assets[assets.study_id.isin(["HVS", "SEA_AD"]) & assets.foundation_eligible].sort_values("dataset_id").itertuples(index=False):
        contract = semantics[semantics.dataset_id.eq(asset.dataset_id)].iloc[0]
        inventory.append(extract_h5(source, cache, asset, contract, provenance, train[str(asset.study_id)],
                                    int(config["sampling"]["cells_per_h5_matrix"]), int(config["sampling"]["seed"])))
        print(f"cached {inventory[-1]['matrix_id']} rows={inventory[-1]['rows']}", flush=True)
    inventory.extend(extract_nph(source, cache, config, dict(zip(registry.molecular_address_id, registry.molecular_address_index)), train["NPH52"]))
    if len(inventory) != 42: raise RuntimeError(f"expected 42 matrix operators, found {len(inventory)}")
    support = {matrix: group.sort_values("molecular_address_index").measured_address.to_numpy(bool)
               for matrix, group in support_frame.groupby("matrix_id", sort=False)}
    nph_cache_addresses=set(pd.read_csv(source / config["inputs"]["nph_cache_vocabulary"]).canonical_ensembl_gene_id.astype(str))
    nph_available=registry.molecular_address_id.astype(str).isin(nph_cache_addresses).to_numpy()
    for matrix in list(support):
        if matrix.startswith("NPH52::matrix::"):
            support[matrix] = support[matrix] & nph_available
    full_parts=[]; a_parts=[]; b_parts=[]; measured_parts=[]; donor_parts=[]; matrix_parts=[]; study_parts=[]
    for item in inventory:
        counts = sparse.load_npz(item["counts"]); meta = np.load(item["meta"], allow_pickle=False)
        seed = int(hashlib.sha256(f"{config['sampling']['count_split_seed']}|{item['matrix_id']}".encode()).hexdigest()[:16], 16)
        full, a, b = count_views(counts, meta["source_library"], seed)
        mask = support[item["matrix_id"]]
        full_parts.append(full); a_parts.append(a); b_parts.append(b); measured_parts.append(np.repeat(mask[None, :], len(full), axis=0))
        donor_parts.append(meta["donor_id"].astype(str)); matrix_parts.append(np.repeat(item["matrix_id"], len(full))); study_parts.append(np.repeat(item["study_id"], len(full)))
    full=np.concatenate(full_parts); a=np.concatenate(a_parts); b=np.concatenate(b_parts); measured=np.concatenate(measured_parts)
    donors=np.concatenate(donor_parts); matrices=np.concatenate(matrix_parts); studies=np.concatenate(study_parts)
    folds=int(config["sampling"]["donor_folds"]); fold_ids=np.asarray([stable_fold(d, folds, int(config["sampling"]["seed"])) for d in donors])
    all_rows=np.arange(len(full)); mean,std,weight=parameters(full,a,b,measured,all_rows)
    x=transform(full,measured,mean,std,weight)
    maximum=int(config["basis"]["maximum_dimensions"]); basis,singular=fit_basis(x,matrices,maximum,int(config["sampling"]["seed"]),int(config["basis"]["randomized_oversamples"]),int(config["basis"]["randomized_iterations"]))
    np.savez_compressed(outputs["ordered_basis"], basis=basis, singular_values=singular, mean=mean, std=std, reproducibility_weight=weight,
                        molecular_address_id=registry.molecular_address_id.astype(str).to_numpy(dtype="U"), status=STATUS)
    eigenvalues=np.square(singular); relative_gap=np.full(maximum,np.nan,dtype=float)
    relative_gap[:-1]=np.divide(eigenvalues[:-1]-eigenvalues[1:],eigenvalues[:-1],out=np.zeros(maximum-1),where=eigenvalues[:-1]>0)
    spectrum=pd.DataFrame({"status":STATUS,"component":np.arange(1,maximum+1),"singular_value":singular,"eigenvalue":eigenvalues,
                           "relative_eigengap_to_next":relative_gap,"cumulative_fraction_of_audited_256_eigenvalue_sum":np.cumsum(eigenvalues)/eigenvalues.sum()})
    atomic_csv(outputs["eigenspectrum"],spectrum)
    weight_frame=pd.DataFrame({"status":STATUS,"molecular_address_index":registry.molecular_address_index,"molecular_address_id":registry.molecular_address_id,
                               "identity_class":registry.identity_class,"train_mean":mean,"train_std":std,"paired_view_reproducibility_weight":weight,
                               "operators_measuring_address_in_accepted_audit":np.stack(list(support.values())).sum(0)})
    atomic_csv(outputs["address_weights"],weight_frame,compress=True)
    prefixes=np.arange(int(config["basis"]["prefix_step"]),maximum+1,int(config["basis"]["prefix_step"])); scores=np.full((folds,len(prefixes)),np.nan)
    stability_rows=[]; block_rows=[]; block_null: dict[int,list[float]]={int(end):[] for end in prefixes}; operator_rows=[]; refit_bases=[]
    for fold in range(folds):
        fit=fold_ids!=fold; held=~fit; fmean,fstd,fweight=parameters(full,a,b,measured,np.where(fit)[0])
        fx=transform(full[fit],measured[fit],fmean,fstd,fweight)
        fbasis,fsingular=fit_basis(fx,matrices[fit],maximum,int(config["sampling"]["seed"])+fold+1,int(config["basis"]["randomized_oversamples"]),int(config["basis"]["randomized_iterations"])); refit_bases.append(fbasis)
        fa=transform(a[held],measured[held],fmean,fstd,fweight); fb=transform(b[held],measured[held],fmean,fstd,fweight)
        ffull=transform(full[held],measured[held],fmean,fstd,fweight)
        held_matrices=matrices[held]
        for j,prefix in enumerate(prefixes):
            values=[]
            for matrix in np.unique(held_matrices):
                idx=held_matrices==matrix; values.append(masked_reconstruction_r2(fa[idx],fb[idx],fbasis[:,:prefix],support[matrix]))
            scores[fold,j]=np.nanmean(values)
            canonical,projector=subspace_metrics(basis,fbasis,int(prefix))
            stability_rows.append({"status":STATUS,"donor_fold":fold,"prefix":int(prefix),"median_canonical_correlation":canonical,"projector_similarity":projector})
        step=int(config["basis"]["prefix_step"])
        for end in prefixes:
            start=int(end)-step; _,observed=subspace_metrics(basis[:,start:int(end)],fbasis[:,start:int(end)],step)
            block_rows.append({"status":STATUS,"donor_fold":fold,"block_start":start+1,"block_end":int(end),"matching_block_projector_similarity":observed})
            for null_end in prefixes:
                null_start=int(null_end)-step
                if int(null_end)==int(end): continue
                _,null_value=subspace_metrics(basis[:,null_start:int(null_end)],fbasis[:,start:int(end)],step)
                block_null[int(end)].append(null_value)
        for matrix in np.unique(held_matrices):
            idx=held_matrices==matrix
            paired_identity=raw_paired_r2(fa[idx],fb[idx],support[matrix])
            paired_projected=masked_reconstruction_r2(fa[idx],fb[idx],fbasis,support[matrix])
            projected_full=masked_reconstruction_r2(ffull[idx],ffull[idx],fbasis,support[matrix])
            operator_rows.append({"status":STATUS,"donor_fold":fold,"matrix_id":matrix,"study_id":studies[held][idx][0],"n_cells":int(idx.sum()),
                                  "raw_measured_evidence_upper_bound_r2":1.0,
                                  "projected_global_state_recovery_r2":projected_full,
                                  "gap_to_raw_measured_evidence":1.0-projected_full,
                                  "paired_view_identity_baseline_r2":paired_identity,
                                  "paired_view_projected_r2":paired_projected})
        print(f"donor refit fold {fold+1}/{folds} complete",flush=True)
    prefix_frame=pd.DataFrame({"status":STATUS,"prefix":prefixes,"mean_reconstruction_r2":np.nanmean(scores,axis=0),
                               "se_reconstruction_r2":np.nanstd(scores,axis=0,ddof=1)/np.sqrt(folds),"folds":folds})
    bulk=one_standard_error_prefix(prefixes,scores); bulk.update({"status":STATUS,"decision_rule":"smallest prefix within one SE of best held-out paired-view reconstruction"})
    block_frame=pd.DataFrame(block_rows); block_summary=[]
    for end in prefixes:
        observed=float(block_frame.loc[block_frame.block_end.eq(int(end)),"matching_block_projector_similarity"].median()); null=np.asarray(block_null[int(end)])
        empirical=float((1+np.sum(null>=observed))/(1+len(null)))
        block_summary.append({"block_end":int(end),"observed_median_projector_similarity":observed,"null_p95":float(np.quantile(null,0.95)),"empirical_p":empirical})
    order=np.argsort([row["empirical_p"] for row in block_summary]); m=len(block_summary); adjusted=np.empty(m); running=1.0
    for rank,index in reversed(list(enumerate(order,start=1))):
        running=min(running,float(block_summary[index]["empirical_p"])*m/rank); adjusted[index]=running
    recurrent={}
    for row,q in zip(block_summary,adjusted,strict=True):
        row["bh_q"]=float(q); row["recurrent_tail_supported"]=bool(q<=float(config["basis"]["residual_tail_fdr"]) and row["observed_median_projector_similarity"]>row["null_p95"]); recurrent[row["block_end"]]=row
    tails=contiguous_tail_decisions(prefix_frame,bulk["k_bulk"],int(config["basis"]["prefix_step"]),recurrent); final_dimension=bulk["k_bulk"]
    for index, tail in enumerate(tails):
        tail["recurrent_eigenspace_alignment_supported"] = tail.pop("recurrent_tail_supported")
        tail["recurrent_high_energy_tail_supported"] = False
        tail["energy_null_status"] = "UNRESOLVED_NO_PREDECLARED_HIGH_ENERGY_NULL"
        tail["retained"] = False
        tail["stop_triggered"] = index == 0
    for tail in tails:
        if tail["retained"]: final_dimension=int(tail["block_end"])
        else: break
    ordering_failure=any(row["ordering_failure"] for row in tails)
    stability=pd.DataFrame(stability_rows); operator=pd.DataFrame(operator_rows)
    paired=operator.groupby(["study_id","matrix_id"],as_index=False).agg(
        n_evaluations=("donor_fold","size"),
        raw_measured_evidence_upper_bound_r2=("raw_measured_evidence_upper_bound_r2","mean"),
        projected_global_state_recovery_r2=("projected_global_state_recovery_r2","mean"),
        paired_view_identity_baseline_r2=("paired_view_identity_baseline_r2","mean"),
        paired_view_projected_r2=("paired_view_projected_r2","mean"),
    )
    paired.insert(0,"status",STATUS)
    atomic_csv(outputs["paired_reproducibility"],paired); atomic_csv(outputs["prefix_qualification"],prefix_frame); atomic_csv(outputs["donor_stability"],stability)
    atomic_json(outputs["bulk_decision"],bulk); atomic_csv(outputs["residual_tail"],pd.DataFrame(tails)); atomic_csv(outputs["operator_qualification"],operator)
    atomic_json(outputs["ordering_audit"],{"status":STATUS,"ordering_failure":ordering_failure,"first_unsupported_block":next((row["block_start"] for row in tails if row["stop_triggered"]),None)})
    access={"status":STATUS,"train_donors":{k:len(v) for k,v in train.items()},"train_donors_total":sum(map(len,train.values())),"matrix_operators":len(inventory),
            "operators_by_study":pd.Series([item["study_id"] for item in inventory]).value_counts().sort_index().to_dict(),"cells_accessed":len(full),
            "real_rna_accessed":"TRAIN ONLY","development_rna_accessed":False,"sealed_rna_accessed":False,"pathology_accessed":False,"future_data_accessed":False,
            "metadata_fields_loaded":["donor_id","cell_id","broad_cell_class"],
            "nph_analysis_availability":"PREEXISTING TRAIN-ONLY 4096-ADDRESS CACHE; SOURCE MEASUREMENT SUPPORT OUTSIDE CACHE IS NOT ZERO-FILLED",
            "discarded_mixed_split_qs_extraction_used_by_accepted_analysis":False,
            "source_files":[{"matrix_id":i["matrix_id"],"study_id":i["study_id"],"logical_path":i["logical_path"],"selected_train_cells":i["rows"]} for i in inventory]}
    atomic_json(outputs["access_manifest"],access)
    median_canonical=float(stability.loc[stability.prefix.eq(final_dimension),"median_canonical_correlation"].median()); median_projector=float(stability.loc[stability.prefix.eq(final_dimension),"projector_similarity"].median())
    range_boundary = int(bulk["best_prefix"]) == maximum
    classification = "GLOBAL_RESOLUTION_LIMITATION_RESIDUAL_ENERGY_NULL_UNRESOLVED"
    supported_dimension = None
    candidate={"status":STATUS,"classification":classification,"k_bulk_within_audited_range":bulk["k_bulk"],
               "d_global_candidate":supported_dimension,"audited_range_endpoint":maximum,"best_prefix_at_audit_boundary":range_boundary,"ordering_failure":ordering_failure,
               "residual_eigenspace_alignment_audited":True,"residual_high_energy_null_adjudicated":False,
               "relative_eigengap_at_within_range_k_bulk":float(relative_gap[int(bulk["k_bulk"])-1]),
               "median_relative_eigengap_last_16_components":float(np.nanmedian(relative_gap[-17:-1])),
               "median_donor_refit_canonical_correlation":median_canonical,"median_donor_refit_projector_similarity":median_projector,
               "address_space":41238,"basis_method":"reproducibility-weighted standardized randomized linear SVD","freeze1_declared":False,
               "stage81b_started":False,"stage81c_started":False,"final_status":"STAGE81A3R_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN"}
    atomic_json(outputs["candidate"],candidate)
    readout=f"""# Stage81A3R Real-TRAIN Global-State Pilot Audit

**{STATUS}**

The accepted analytic lineage used foundation TRAIN RNA only, but NPH was restricted by the historical TRAIN-only 4,096-address cache. This is an analysis-induced observation restriction, not structural unmeasurement. No neural model was trained.

## Firewall

- TRAIN donors: **{access['train_donors_total']}** ({access['train_donors']}).
- Matrix operators: **{access['matrix_operators']}** ({access['operators_by_study']}).
- TRAIN cells sampled: **{access['cells_accessed']}**.
- Accepted-lineage DEV/SEALED/pathology use: **NO / NO / NO**.
- Execution history: a discarded NPH extraction attempt transiently materialized mixed-split `.qs` count containers before TRAIN-column selection.

## Candidate

- Basis: reproducibility-weighted standardized linear SVD with structural absence mean-imputed only in the fitting workspace.
- Projection/evaluation: measured-address masked least squares.
- One-SE bulk prefix within the audited range: **{bulk['k_bulk']}**; best prefix: **{bulk['best_prefix']}**.
- Best prefix reached the predeclared audit boundary: **{range_boundary}**.
- Supported production global dimension: **{supported_dimension}**.
- Ordering failure: **{ordering_failure}**.
- Donor-refit median canonical correlation/projector similarity at the within-range one-SE prefix: **{median_canonical:.4f} / {median_projector:.4f}**.
- Classification: **{classification}**.

Residual blocks are retained only contiguously. Unsupported gaps are not skipped. The raw measured-evidence upper bound is 1.0 by definition for recovering the measured standardized vector itself; projected full-view recovery and its gap are reported separately. Direct A-to-B count-split identity is retained as a noisy baseline and is not mislabeled as an upper bound.

## Governance

**GLOBAL_STATE_PILOT_INPUT_CONTRACT_LIMITED. NOT FROZEN.**

Final status: **STAGE81A3R_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN**
"""
    outputs["readout"].write_text(readout,encoding="utf-8",newline="\n")
    print(json.dumps(candidate,indent=2,sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
