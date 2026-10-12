#!/usr/bin/env python3
"""Frozen sampler policy, recovery state machine and fit custody for V79 V2_CORE."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np


class FitRunnerRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitRunnerRefused(f"REFUSED V2_CORE fit runner: {msg}")


@dataclass(frozen=True)
class SamplerPolicy:
    chains: int
    warmup: int
    draws: int
    max_tree_depth: int
    target_accept_primary: float
    target_accept_escalation: float
    rhat_max: float
    ess_min: int


def _first_float(text: str) -> float:
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(text))
    if not m:
        _refuse(f"cannot parse numeric policy from {text!r}")
    return float(m.group(1))


def sampler_policy(contract: Mapping) -> SamplerPolicy:
    inf = contract.get("inference", {})
    rec = inf.get("recovery_path", {})
    diag = inf.get("diagnostics", {})
    if rec.get("version") != "V2_CORE_ONE_ESCALATION_ONE_EXTENSION_V1":
        _refuse("unexpected recovery-path version")
    if "no reparameterization" not in str(rec.get("no_other_changes", "")):
        _refuse("recovery no-change lock missing")
    return SamplerPolicy(
        chains=int(inf["chains"]), warmup=int(inf["warmup"]), draws=int(inf["draws"]),
        max_tree_depth=int(inf["max_tree_depth"]),
        target_accept_primary=_first_float(rec["primary"]),
        target_accept_escalation=_first_float(rec["escalation"]),
        rhat_max=_first_float(diag.get("rhat", "")), ess_min=int(_first_float(diag.get("ess", ""))),
    )


def evaluate_sampler_diagnostics(contract: Mapping, diagnostics: Mapping) -> bool:
    p = sampler_policy(contract)
    return (int(diagnostics.get("divergences", -1)) == 0 and
            float(diagnostics.get("worst_rhat", float("inf"))) <= p.rhat_max and
            float(diagnostics.get("worst_ess_bulk", -1)) >= p.ess_min and
            float(diagnostics.get("worst_ess_tail", -1)) >= p.ess_min)


def next_recovery_action(contract: Mapping, attempts: list[Mapping], diagnostics: Mapping) -> str:
    if evaluate_sampler_diagnostics(contract, diagnostics):
        return "COMPLETE"
    stages = [str(a.get("stage")) for a in attempts]
    if int(diagnostics.get("divergences", 0)) > 0:
        return "ESCALATE" if "ESCALATION" not in stages else "NOT_DIAGNOSED"
    return "EXTEND" if "EXTENSION" not in stages else "NOT_DIAGNOSED"


def fit_identity(opaque_world_id: str, world_manifest_sha: str, part: str, gene_index: int) -> str:
    if not re.fullmatch(r"[0-9a-f]{12}", opaque_world_id):
        _refuse("opaque world id required")
    if part not in {"detection", "positive"} or gene_index < 0:
        _refuse("invalid fit scientific identity")
    return hashlib.sha256(f"{opaque_world_id}|{world_manifest_sha}|{part}|{int(gene_index)}".encode()).hexdigest()


def new_fit_receipt(*, execution_mode: str, fit_id: str, opaque_world_id: str, gene_index: int, part: str,
                    input_manifest_sha: str, contract_sha: str, code_sha: str) -> dict:
    if execution_mode not in {"ENGINEERING_BENCHMARK", "QUALIFICATION"}:
        _refuse(f"unknown execution mode {execution_mode!r}")
    if part not in {"detection", "positive"}:
        _refuse("unknown model part")
    return {
        "schema": "V79_V2_CORE_FIT_RECORD_V1", "execution_mode": execution_mode,
        "fit_id": fit_id, "opaque_world_id": opaque_world_id, "gene_index": int(gene_index), "part": part,
        "input_manifest_sha256": input_manifest_sha, "contract_sha256": contract_sha, "code_sha": code_sha,
        "attempts": [], "final_diagnosis": None, "posterior_artifacts": {},
        "benchmark_run": execution_mode == "ENGINEERING_BENCHMARK",
        "qualification_fits_run": 1 if execution_mode == "QUALIFICATION" else 0,
        "scoring_run": False, "truth_accessed": False, "training_authorized": False,
    }


def write_receipt_atomic(path: Path, receipt: Mapping) -> str:
    path = Path(path)
    raw = (json.dumps(dict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    digest = hashlib.sha256(raw).hexdigest()
    if path.exists():
        old = path.read_bytes()
        if old != raw:
            _refuse(f"existing fit receipt differs: {path}")
        return hashlib.sha256(old).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    if tmp.exists():
        _refuse(f"stale partial receipt exists: {tmp}")
    tmp.write_bytes(raw); os.replace(tmp, path)
    return digest


def planned_attempt(contract: Mapping, *, stage: str, previous_target_accept: float | None = None) -> dict:
    p = sampler_policy(contract)
    if stage == "PRIMARY": ta, warm, ext = p.target_accept_primary, p.warmup, False
    elif stage == "ESCALATION": ta, warm, ext = p.target_accept_escalation, p.warmup, False
    elif stage == "EXTENSION":
        if previous_target_accept is None:
            _refuse("extension must inherit previous target_accept")
        ta, warm, ext = float(previous_target_accept), 0, True
    else:
        _refuse(f"unknown sampler stage {stage}")
    return {"stage":stage, "chains":p.chains, "warmup":warm, "draws_per_chain":p.draws,
            "target_accept":ta, "max_tree_depth":p.max_tree_depth, "extended":ext}


def diagnostics_from_samples(samples_by_chain: Mapping[str, np.ndarray], *, divergences: int, mean_tree_steps: float) -> dict:
    import arviz as az
    if not samples_by_chain:
        _refuse("no sampled sites for diagnostics")
    idata = az.from_dict(posterior={k: np.asarray(v) for k, v in samples_by_chain.items()})
    tab = az.summary(idata, kind="diagnostics", round_to=None)
    if not {"r_hat", "ess_bulk", "ess_tail"}.issubset(tab.columns):
        _refuse("ArviZ diagnostics missing required columns")
    return {
        "divergences": int(divergences),
        "worst_rhat": float(np.nanmax(tab["r_hat"].to_numpy())),
        "worst_ess_bulk": float(np.nanmin(tab["ess_bulk"].to_numpy())),
        "worst_ess_tail": float(np.nanmin(tab["ess_tail"].to_numpy())),
        "mean_tree_steps": float(mean_tree_steps),
    }


def combine_samples(a: Mapping[str, np.ndarray], b: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    if set(a) != set(b):
        _refuse("extension sampled-site set changed")
    out = {}
    for k in a:
        x, y = np.asarray(a[k]), np.asarray(b[k])
        if x.ndim < 2 or y.ndim < 2 or x.shape[0] != y.shape[0] or x.shape[2:] != y.shape[2:]:
            _refuse(f"extension sample shape mismatch at {k}")
        out[k] = np.concatenate([x, y], axis=1)
    return out


def posterior_summary(samples_by_chain: Mapping[str, np.ndarray]) -> dict:
    out = {}
    for k, v in samples_by_chain.items():
        a = np.asarray(v); flat = a.reshape((-1,) + a.shape[2:])
        out[k] = {"mean":np.mean(flat,0).tolist(), "sd":np.std(flat,0,ddof=1).tolist(),
                  "q05":np.quantile(flat,.05,axis=0).tolist(), "q50":np.quantile(flat,.50,axis=0).tolist(),
                  "q95":np.quantile(flat,.95,axis=0).tolist()}
    return out


def run_nuts_attempt(*, contract: Mapping, model, seed: int, stage: str,
                     post_warmup_state=None, previous_target_accept: float | None = None):
    import jax
    from numpyro.infer import MCMC, NUTS
    spec = planned_attempt(contract, stage=stage, previous_target_accept=previous_target_accept)
    kernel = NUTS(model, target_accept_prob=spec["target_accept"], max_tree_depth=spec["max_tree_depth"])
    mcmc = MCMC(kernel, num_warmup=spec["warmup"], num_samples=spec["draws_per_chain"],
                num_chains=spec["chains"], chain_method="parallel", progress_bar=False)
    if stage == "EXTENSION":
        if post_warmup_state is None:
            _refuse("extension requires prior chain state")
        mcmc.post_warmup_state = post_warmup_state
    t0 = time.perf_counter()
    mcmc.run(jax.random.PRNGKey(int(seed)), extra_fields=("diverging", "num_steps"))
    return {"mcmc":mcmc, "wall_seconds":time.perf_counter()-t0, "spec":spec}


def attempt_diagnostics(run: Mapping) -> tuple[dict, dict[str, np.ndarray]]:
    m = run["mcmc"]
    samples = {k: np.asarray(v) for k, v in m.get_samples(group_by_chain=True).items()}
    extra = m.get_extra_fields(group_by_chain=True)
    divergences = int(np.asarray(extra["diverging"]).sum())
    mean_steps = float(np.asarray(extra["num_steps"]).mean())
    return diagnostics_from_samples(samples, divergences=divergences, mean_tree_steps=mean_steps), samples
