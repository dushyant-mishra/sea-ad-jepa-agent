#!/usr/bin/env python3
"""Stream exact address-resolved T1 H and fit recovery centroids on reader_fit only."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
T1 = ROOT / "exports" / "prod41k_teacher_t1_20260823"
RUN = T1 / "t1_run"
OUT = ROOT / "exports" / "prod41k_t1_contextual_recovery_v1"
sys.path.insert(0, str(ROOT / "scripts" / "v4"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
import stage81a3_prod41k_teacher_t1 as t1  # noqa: E402
from production_train_loader import ProductionTrainLoader  # noqa: E402


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def checkpoint(update: int, device: torch.device):
    manifest = json.loads((RUN / "checkpoint_manifest.json").read_text())
    row = next(x for x in manifest["checkpoints"] if int(x["update"]) == update)
    path = ROOT / row["path"]
    if sha(path) != row["sha256"] or path.stat().st_size != int(row["bytes"]):
        raise RuntimeError(f"checkpoint identity mismatch u{update}")
    state = torch.load(path, map_location=device, weights_only=False)
    online, target = t1.phase_e.build_components(t1.SEED, device)[:2]
    online.load_state_dict(state["online_encoder"]); target.load_state_dict(state["target_encoder"])
    online.eval(); target.eval()
    return online, target, row


def stream_mode(update, mode, encoder, role, meta, values, measured, weights, panel, partial_masks, frozen_raw, device):
    n, genes, width = len(meta), t1.phase_e.VOCABULARY_SIZE, t1.phase_e.WIDTH
    fit = meta.reader_partition.astype(str).eq("reader_fit").to_numpy()
    operators = meta.operator_index.to_numpy(np.int64)
    sources, source_names = pd.factorize(meta.study_id.astype(str), sort=True)
    if fit.sum() != 3163 or meta.loc[fit, "donor_id"].nunique() != 104:
        raise RuntimeError("fit-donor firewall mismatch")
    op_names = sorted(meta.loc[fit, "operator_index"].astype(int).unique())
    if op_names != list(range(42)):
        raise RuntimeError("fit partition does not contain all 42 operators")
    op_count = np.bincount(operators[fit], minlength=42).astype(np.int64)
    source_count = np.bincount(sources[fit], minlength=len(source_names)).astype(np.int64)
    if np.any(op_count == 0) or np.any(source_count == 0):
        raise RuntimeError("unexpected centroid fallback in current cohort")

    address_sum = np.zeros((genes, width), np.float64)
    operator_sum = np.zeros((42, genes, width), np.float64)
    source_sum = np.zeros((len(source_names), genes, width), np.float64)
    address_sumsq = np.zeros(genes, np.float64)
    dim_sumsq = np.zeros(width, np.float64)
    pooled = np.empty((n, len(t1.CONTINUOUS), width), np.float32)
    weight_tensor = torch.from_numpy(weights).to(device)
    started = time.time()
    with torch.inference_mode():
        for begin in range(0, n, t1.EVAL_BATCH):
            end = min(begin + t1.EVAL_BATCH, n); batch = end - begin
            expression = torch.from_numpy(values[begin:end]).to(device)
            mask = torch.from_numpy(measured[begin:end]).to(device)
            hidden = torch.zeros_like(mask)
            if mode == "partial_H":
                hidden_cpu = torch.from_numpy(partial_masks[begin:end])
                hidden = hidden_cpu.to(device)
                for local in range(batch):
                    digest = hashlib.sha256(hidden_cpu[local].numpy().tobytes()).hexdigest()
                    if digest != str(panel.iloc[begin + local].mask_sha256):
                        raise RuntimeError("partial mask hash drift")
            gene_ids = torch.arange(genes, device=device).expand(batch, -1)
            with torch.autocast("cuda", dtype=torch.float16):
                output = encoder(gene_ids, expression, mask, hidden, role)
            pooled[begin:end] = torch.einsum("kg,bgd->bkd", weight_tensor, output.gene_states.float()).cpu().numpy()
            local_fit = np.flatnonzero(fit[begin:end])
            if len(local_fit):
                x = output.gene_states[local_fit].float().cpu().numpy()
                address_sum += x.sum(axis=0, dtype=np.float64)
                address_sumsq += np.einsum("bgd,bgd->g", x, x, dtype=np.float64, optimize=True)
                dim_sumsq += np.einsum("bgd,bgd->d", x, x, dtype=np.float64, optimize=True)
                global_rows = begin + local_fit
                for op in np.unique(operators[global_rows]):
                    operator_sum[op] += x[operators[global_rows] == op].sum(axis=0, dtype=np.float64)
                for source in np.unique(sources[global_rows]):
                    source_sum[source] += x[sources[global_rows] == source].sum(axis=0, dtype=np.float64)
            if end % 512 == 0 or end == n:
                print(f"u{update} {mode} {end}/{n}", flush=True)
    raw_max_abs = float(np.max(np.abs(pooled - frozen_raw))) if frozen_raw is not None else np.nan
    if frozen_raw is not None and raw_max_abs != 0.0:
        raise RuntimeError(f"streamed raw-H differs from frozen evaluator u{update} {mode}: {raw_max_abs}")

    fit_n = int(fit.sum()); grand_sum = address_sum.sum(axis=0); grand_mean = grand_sum / (fit_n * genes)
    address_mean = address_sum / fit_n
    operator_mean = operator_sum / op_count[:, None, None]
    source_mean = source_sum / source_count[:, None, None]
    b_program = np.einsum("kg,gd->kd", weights, address_mean, optimize=True)
    op_program = np.einsum("kg,ogd->okd", weights, operator_mean, optimize=True)
    source_program = np.einsum("kg,sgd->skd", weights, source_mean, optimize=True)
    address_residual = pooled - b_program.astype(np.float32)[None]
    operator_residual = pooled - op_program.astype(np.float32)[operators]
    source_residual = pooled - source_program.astype(np.float32)[sources]

    total_sumsq = float(address_sumsq.sum())
    total_sst = total_sumsq - float(np.square(grand_sum).sum()) / (fit_n * genes)
    address_sse_by_address = address_sumsq - np.square(address_sum).sum(axis=1) / fit_n
    op_sse_by_address = address_sumsq.copy()
    source_sse_by_address = address_sumsq.copy()
    op_explained = np.zeros(genes, np.float64); source_explained = np.zeros(genes, np.float64)
    for op in range(42): op_explained += np.square(operator_sum[op]).sum(axis=1) / op_count[op]
    for source in range(len(source_names)): source_explained += np.square(source_sum[source]).sum(axis=1) / source_count[source]
    op_sse_by_address -= op_explained; source_sse_by_address -= source_explained
    address_sse = float(address_sse_by_address.sum()); op_sse = float(op_sse_by_address.sum()); source_sse = float(source_sse_by_address.sum())

    rows = [
        {"update": update, "evidence_mode": mode, "scope": "aggregate", "index": "all", "fit_cells": fit_n,
         "fit_donors": 104, "total_variance_sst": total_sst, "address_residual_sse": address_sse,
         "source_residual_sse": source_sse, "operator_residual_sse": op_sse,
         "address_variance_fraction": 1-address_sse/total_sst, "source_incremental_fraction": (address_sse-source_sse)/total_sst,
         "operator_incremental_fraction": (address_sse-op_sse)/total_sst, "remaining_operator_fraction": op_sse/total_sst,
         "raw_frozen_max_abs_difference": raw_max_abs},
    ]
    overall_by_address = address_sumsq - 2 * (address_sum * grand_mean).sum(axis=1) + fit_n * np.square(grand_mean).sum()
    between_by_address = fit_n * np.square(address_mean - grand_mean).sum(axis=1)
    for g in range(genes):
        denominator = overall_by_address[g]
        rows.append({"update": update, "evidence_mode": mode, "scope": "address", "index": g, "fit_cells": fit_n,
                     "fit_donors": 104, "total_variance_sst": denominator, "address_residual_sse": address_sse_by_address[g],
                     "source_residual_sse": source_sse_by_address[g], "operator_residual_sse": op_sse_by_address[g],
                     "address_variance_fraction": between_by_address[g]/denominator if denominator > 0 else np.nan,
                     "source_incremental_fraction": (address_sse_by_address[g]-source_sse_by_address[g])/denominator if denominator > 0 else np.nan,
                     "operator_incremental_fraction": (address_sse_by_address[g]-op_sse_by_address[g])/denominator if denominator > 0 else np.nan,
                     "remaining_operator_fraction": op_sse_by_address[g]/denominator if denominator > 0 else np.nan,
                     "raw_frozen_max_abs_difference": raw_max_abs})
    for d in range(width):
        dim_total = dim_sumsq[d] - grand_sum[d]**2/(fit_n*genes)
        addr_sse_d = dim_sumsq[d] - np.square(address_sum[:,d]).sum()/fit_n
        op_sse_d = dim_sumsq[d] - sum(np.square(operator_sum[o,:,d]).sum()/op_count[o] for o in range(42))
        src_sse_d = dim_sumsq[d] - sum(np.square(source_sum[s,:,d]).sum()/source_count[s] for s in range(len(source_names)))
        rows.append({"update": update, "evidence_mode": mode, "scope": "dimension", "index": d, "fit_cells": fit_n,
                     "fit_donors": 104, "total_variance_sst": dim_total, "address_residual_sse": addr_sse_d,
                     "source_residual_sse": src_sse_d, "operator_residual_sse": op_sse_d,
                     "address_variance_fraction": 1-addr_sse_d/dim_total, "source_incremental_fraction": (addr_sse_d-src_sse_d)/dim_total,
                     "operator_incremental_fraction": (addr_sse_d-op_sse_d)/dim_total, "remaining_operator_fraction": op_sse_d/dim_total,
                     "raw_frozen_max_abs_difference": raw_max_abs})

    centroids = None
    if mode == "rich_H":
        centroids = {"address_mean": address_mean.astype(np.float32),
                     "operator_deviation": (operator_mean-address_mean[None]).astype(np.float32),
                     "source_deviation": (source_mean-address_mean[None]).astype(np.float32),
                     "operator_count": op_count, "source_count": source_count,
                     "source_name": np.asarray(source_names, dtype="U32")}
    features = {"raw": pooled, "address_residual": address_residual.astype(np.float32),
                "source_residual": source_residual.astype(np.float32), "operator_residual": operator_residual.astype(np.float32)}
    audit = {"update": update, "evidence_mode": mode, "fit_cells": fit_n, "fit_donors": 104,
             "operators": 42, "sources": source_names.tolist(), "address_component_fitted_on": "reader_fit only; every address token is lawfully evaluated, including explicit structural/collision states",
             "fallback_rule": "operator/source mean when fit count>0 else address mean", "fallbacks_used": 0,
             "raw_frozen_max_abs_difference": raw_max_abs, "wall_seconds": time.time()-started}
    return rows, features, centroids, audit


def main():
    OUT.mkdir(parents=True, exist_ok=True); t1.validate_contract()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda": raise RuntimeError("qualified CUDA path required")
    evaluation = t1.load_evaluation(ProductionTrainLoader())
    meta, values, measured, weights, _, _, _, _, panel, partial_masks = evaluation
    if set(meta.reader_partition.astype(str)) != {"reader_fit","reader_validation","reader_oracle"}: raise RuntimeError("donor partition drift")
    with np.load(RUN/"u0_evaluation_features.npz",allow_pickle=False) as z:
        u0={k:z[k] for k in z.files}
    all_rows=[]; all_features={}; audits=[]
    for update in (0,205):
        online,target,row=checkpoint(update,device)
        for mode,encoder,role in (("rich_H",target,"target"),("partial_H",online,"student")):
            frozen=u0[mode] if update==0 else None
            rows,features,centroids,audit=stream_mode(update,mode,encoder,role,meta,values,measured,weights,panel,partial_masks,frozen,device)
            all_rows.extend(rows); audits.append(audit)
            for variant,array in features.items(): all_features[f"u{update:04d}__{mode}__{variant}"]=array
            if centroids is not None:
                path=OUT/f"T1_RECOVERY_RICH_CENTROIDS_u{update:04d}.npz"; np.savez_compressed(path,**centroids); audit["centroid_path"]=str(path.relative_to(ROOT));audit["centroid_sha256"]=sha(path)
    frame=pd.DataFrame(all_rows)
    frame.to_csv(OUT/"T1_RECOVERY_ADDRESS_OPERATOR_DECOMPOSITION.csv",index=False,lineterminator="\n")
    frame[[c for c in frame if c not in ("source_residual_sse","source_incremental_fraction")]].to_csv(OUT/"T1_RECOVERY_ADDRESS_DECOMPOSITION.csv",index=False,lineterminator="\n")
    np.savez_compressed(OUT/"T1_RECOVERY_RESIDUAL_FEATURES.npz",**all_features)
    payload={"schema":"prod41k-t1-recovery-address-decomposition-v1","neural_updates":0,"fit_partition":"reader_fit","fit_cells":3163,"fit_donors":104,
             "representation_semantics":"exact streamed [cell,41238,160] gene/address states; pooled outputs are only downstream frozen-program readout tensors",
             "audits":audits,"residual_features_sha256":sha(OUT/"T1_RECOVERY_RESIDUAL_FEATURES.npz")}
    (OUT/"T1_RECOVERY_ADDRESS_OPERATOR_DECOMPOSITION.json").write_text(json.dumps(payload,indent=2)+"\n")
    (OUT/"T1_RECOVERY_ADDRESS_DECOMPOSITION.json").write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))

if __name__=="__main__": main()
