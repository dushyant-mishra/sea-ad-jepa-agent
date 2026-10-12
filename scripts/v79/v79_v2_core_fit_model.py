#!/usr/bin/env python3
"""Contract-driven, truth-blind V79 V2_CORE NumPyro models."""
from __future__ import annotations

import hashlib
import json
from typing import Mapping

import numpy as np

try:
    import jax
    jax.config.update("jax_enable_x64", True)
    jax.config.update("jax_default_matmul_precision", "highest")
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
except Exception:  # structural helpers remain importable for audit tooling
    jax = jnp = numpyro = dist = None


class FitModelRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitModelRefused(f"REFUSED V2_CORE fit model: {msg}")


def model_fingerprint(contract: Mapping) -> dict:
    model = contract.get("model", {})
    if model.get("name") != "V2_CORE":
        _refuse("model.name is not V2_CORE")
    excluded = tuple(model.get("excluded_terms", ()))
    required_excluded = {"operator / matrix", "donor x class", "source x class", "dataset or matrix ID"}
    if set(excluded) != required_excluded:
        _refuse("excluded-term authority differs")
    priors = contract.get("priors", {})
    if set(priors) != {"detection", "positive"}:
        _refuse("detection/positive priors missing")
    stable = {
        "name": "V2_CORE",
        "parts": ["detection", "positive"],
        "terms": ["depth1", "depth2", "class", "source", "donor_within_source"],
        "positive_family": model.get("positive_family"),
        "parameterization": contract.get("parameterization"),
        "priors": priors,
    }
    stable["sha256"] = hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return stable


def _helmert(n: int) -> np.ndarray:
    if n < 1:
        _refuse("empty factor")
    if n == 1:
        return np.zeros((1, 0), dtype=np.float64)
    h = np.zeros((n, n - 1), dtype=np.float64)
    for j in range(n - 1):
        den = np.sqrt((j + 1) * (j + 2))
        h[: j + 1, j] = 1.0 / den
        h[j + 1, j] = -(j + 1) / den
    return h


def _codes(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    levels, inv = np.unique(np.asarray(values), return_inverse=True)
    return levels, inv.astype(np.int32)


def prepare_design(design: Mapping[str, np.ndarray]) -> dict:
    required = {"src", "donor", "cls", "log_lib"}
    if set(design) != required:
        _refuse(f"fit design keys must be exactly {sorted(required)}")
    n = len(np.asarray(design["src"]))
    if n == 0 or any(np.asarray(design[k]).ndim != 1 or len(np.asarray(design[k])) != n for k in required):
        _refuse("unaligned 1-D design vectors")
    src_levels, src = _codes(np.asarray(design["src"]))
    cls_levels, cls = _codes(np.asarray(design["cls"]))
    donor_levels, donor = _codes(np.asarray(design["donor"]))
    if len(src_levels) != 3 or len(cls_levels) != 3:
        _refuse("V2_CORE requires exactly three sources and three broad classes")
    donor_source = np.full(len(donor_levels), -1, dtype=np.int32)
    blocks = []
    for s in range(3):
        ds = np.unique(donor[src == s])
        if len(ds) < 1:
            _refuse("source with no donor")
        for d in ds:
            seen = np.unique(src[donor == d])
            if seen.size != 1 or int(seen[0]) != s:
                _refuse("donor crosses source; within-source basis undefined")
            donor_source[d] = s
        hb = _helmert(len(ds))
        block = np.zeros((len(donor_levels), hb.shape[1]), dtype=np.float64)
        if hb.shape[1]:
            block[ds, :] = hb
        blocks.append(block)
    if np.any(donor_source < 0):
        _refuse("donor source assignment incomplete")
    W = np.concatenate(blocks, axis=1) if blocks else np.zeros((len(donor_levels), 0), dtype=np.float64)
    log_lib = np.asarray(design["log_lib"], dtype=np.float64)
    sd = float(np.std(log_lib, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        _refuse("log_lib has zero/nonfinite population SD")
    z = (log_lib - float(np.mean(log_lib))) / sd
    q = z * z - 1.0
    cb = _helmert(3)
    sb = _helmert(3)
    return {
        "z": z, "q": q,
        "class_basis": cb, "source_basis": sb,
        "class_rows": cb[cls], "source_rows": sb[src],
        "donor_basis_by_donor": W, "donor_rows": W[donor],
        "donor_source": donor_source,
        "src_code": src, "cls_code": cls, "donor_code": donor,
    }


def _subset(d: dict, mask: np.ndarray) -> dict:
    cell_keys = ("z", "q", "class_rows", "source_rows", "donor_rows", "src_code", "cls_code", "donor_code")
    out = {k: np.asarray(v)[mask] for k, v in d.items() if k in cell_keys}
    out["donor_basis_by_donor"] = d["donor_basis_by_donor"]
    out["donor_source"] = d["donor_source"]
    return out


def prepare_detection_data(gene_inputs) -> dict:
    d = prepare_design(gene_inputs.design)
    mask = np.asarray(gene_inputs.detection_mask, dtype=bool)
    if mask.ndim != 1 or len(mask) != len(d["z"]):
        _refuse("detection mask shape mismatch")
    out = _subset(d, mask)
    out["y"] = np.asarray(gene_inputs.detected, dtype=np.int8)[mask]
    return out


def prepare_positive_data(gene_inputs) -> dict:
    d = prepare_design(gene_inputs.design)
    mask = np.asarray(gene_inputs.positive_mask, dtype=bool)
    if mask.ndim != 1 or len(mask) != len(d["z"]):
        _refuse("positive mask shape mismatch")
    observed = np.asarray(gene_inputs.observed, dtype=np.float64)
    if np.any(observed[mask] <= 0):
        _refuse("positive likelihood received non-positive observation")
    out = _subset(d, mask)
    out["y_log"] = np.log(observed[mask])
    return out


def _prior(spec: Mapping, *, shape=()):
    if dist is None:
        _refuse("NumPyro is unavailable")
    name = spec.get("dist")
    if name == "Normal":
        d = dist.Normal(float(spec["loc"]), float(spec["scale"]))
    elif name == "HalfNormal":
        d = dist.HalfNormal(float(spec["scale"]))
    else:
        _refuse(f"unsupported frozen prior {name!r}")
    return d.expand(shape).to_event(len(shape)) if shape else d


def _linear_terms(part: str, priors: Mapping, data: Mapping):
    p = priors[part]
    if part == "detection":
        b1n, b2n = "beta_depth1", "beta_depth2"
    else:
        b1n, b2n = "gamma_depth1", "gamma_depth2"
    alpha = numpyro.sample("alpha", _prior(p["alpha"]))
    b1 = numpyro.sample(b1n, _prior(p[b1n]))
    b2 = numpyro.sample(b2n, _prior(p[b2n]))
    cc = numpyro.sample("class_contrasts", _prior(p["class_contrasts"], shape=(2,)))
    sc = numpyro.sample("source_contrasts", _prior(p["source_contrasts"], shape=(2,)))
    donor_sd = numpyro.sample("donor_sd", _prior(p["donor_sd"]))
    nb = int(np.asarray(data["donor_basis_by_donor"]).shape[1])
    raw_spec = p["donor_raw"]
    donor_raw = numpyro.sample("donor_raw", _prior(raw_spec, shape=(nb,))) if nb else jnp.zeros((0,))
    eta = alpha + b1*jnp.asarray(data["z"]) + b2*jnp.asarray(data["q"])
    eta = eta + jnp.asarray(data["class_rows"]) @ cc + jnp.asarray(data["source_rows"]) @ sc
    if nb:
        eta = eta + jnp.asarray(data["donor_rows"]) @ (donor_sd * donor_raw)
    return eta


def build_detection_model(contract: Mapping, gene_inputs):
    model_fingerprint(contract)
    data = prepare_detection_data(gene_inputs)
    priors = contract["priors"]
    def model():
        eta = _linear_terms("detection", priors, data)
        numpyro.sample("obs", dist.Bernoulli(logits=eta), obs=jnp.asarray(data["y"]))
    model.v79_part = "detection"
    model.v79_data = data
    return model


def build_positive_model(contract: Mapping, gene_inputs):
    model_fingerprint(contract)
    data = prepare_positive_data(gene_inputs)
    priors = contract["priors"]
    def model():
        mu = _linear_terms("positive", priors, data)
        sigma = numpyro.sample("sigma", _prior(priors["positive"]["sigma"]))
        numpyro.sample("obs", dist.Normal(mu, sigma), obs=jnp.asarray(data["y_log"]))
    model.v79_part = "positive"
    model.v79_data = data
    return model
