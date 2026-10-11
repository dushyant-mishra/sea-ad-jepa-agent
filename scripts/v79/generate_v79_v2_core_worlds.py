#!/usr/bin/env python3
"""Deterministic V79 V2_CORE synthetic-world generator primitives.

Engineering only until a separate controller realization-authorization receipt exists.
The final Contract V2 plus the prospective Q10/Q11 pairing amendment define the
world semantics. Neither authority alone permits realized world bytes.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

FINAL_CONTRACT_SHA256 = "8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d"
QUALIFICATION_PAYLOAD_SHA256 = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
PAIRING_AMENDMENT_REL = "results/v79/v2_core_qualification/V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1.json"
PAIRING_AMENDMENT_SHA256 = "09f60d91817a041badaa4fc5108125f02a02d1ebbe8242a0f012aa6978d56f7c"
REALIZATION_AUTH_SCHEMA = "V79_V2_CORE_WORLD_REALIZATION_AUTHORIZATION_V1"


def seed_for(*, world_index: int, gene_index: int, stream: int, root: int) -> int:
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(int(world_index), int(gene_index), int(stream)))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def load_pairing_amendment(root: Path) -> dict:
    path = root / PAIRING_AMENDMENT_REL
    if not path.exists():
        raise SystemExit("STOP: Q10/Q11 pairing amendment is required")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PAIRING_AMENDMENT_SHA256:
        raise SystemExit("STOP: Q10/Q11 pairing amendment SHA mismatch")
    sidecar = path.with_suffix(".sha256")
    if not sidecar.exists() or sidecar.read_text(encoding="utf-8").strip() != f"{digest}  {path.name}":
        raise SystemExit("STOP: Q10/Q11 pairing amendment sidecar mismatch")
    a = json.loads(raw)
    if a.get("schema") != "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1":
        raise SystemExit("STOP: wrong pairing amendment schema")
    if a.get("controller_comment") != 6114906562:
        raise SystemExit("STOP: pairing amendment controller binding mismatch")
    if a.get("final_contract_sha256") != FINAL_CONTRACT_SHA256 or a.get("qualification_payload_sha256") != QUALIFICATION_PAYLOAD_SHA256:
        raise SystemExit("STOP: pairing amendment authority binding mismatch")
    if a.get("worlds_generated_at_freeze") != 0 or a.get("qualification_fits_at_freeze") != 0:
        raise SystemExit("STOP: pairing amendment was not frozen pre-outcome")
    if a.get("authorization", {}).get("world_realization") is not False:
        raise SystemExit("STOP: pairing amendment may not itself authorize realization")
    return a


def effective_seed_world_index(world_index: int, stream: int, amendment: dict) -> int:
    pair = amendment["paired_counterfactual"]
    q10 = int(pair["parent_world"]["world_index"])
    q11 = int(pair["child_world"]["world_index"])
    new_streams = {int(v) for v in pair["q11_new_randomness_only"].values()}
    if int(world_index) == q11 and int(stream) not in new_streams:
        return q10
    return int(world_index)


def validate_q10_q11_pairing(q10: dict, q11: dict, amendment: dict) -> None:
    allowed = {"operator_offsets_detection_sha", "operator_offsets_positive_sha"}
    for key in (set(q10) | set(q11)) - allowed:
        if q10.get(key) != q11.get(key):
            raise SystemExit(f"STOP: Q10/Q11 non-operator truth differs: {key}")
    if q10.get("operator_offsets_detection_sha") not in (None, "") or q10.get("operator_offsets_positive_sha") not in (None, ""):
        raise SystemExit("STOP: Q10 must not contain operator perturbation")
    if not q11.get("operator_offsets_detection_sha") or not q11.get("operator_offsets_positive_sha"):
        raise SystemExit("STOP: Q11 must contain both frozen operator perturbations")
    if amendment["paired_counterfactual"].get("all_q11_gates_remain") != "HARD_FAIL":
        raise SystemExit("STOP: Q11 hard-gate authority changed")


def _arr_record(a: np.ndarray) -> dict[str, Any]:
    c = np.ascontiguousarray(a)
    return {"dtype": c.dtype.str, "shape": list(c.shape), "sha256": hashlib.sha256(c.tobytes(order="C")).hexdigest()}


def array_bundle_sha(bundle: dict[str, np.ndarray]) -> str:
    rec = {k: _arr_record(np.asarray(bundle[k])) for k in sorted(bundle)}
    raw = json.dumps(rec, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def scientific_truth_sha(obj: Any) -> str:
    def canon(x: Any) -> Any:
        if isinstance(x, np.ndarray):
            return {"__array__": _arr_record(x)}
        if isinstance(x, np.generic):
            return x.item()
        if isinstance(x, dict):
            return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
        if isinstance(x, (list, tuple)):
            return [canon(v) for v in x]
        if isinstance(x, (str, int, float, bool)) or x is None:
            return x
        raise TypeError(f"unsupported truth type: {type(x)!r}")
    raw = json.dumps(canon(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_designs(payload: dict, *, base_design: dict[str, np.ndarray], s174_design: dict[str, np.ndarray]) -> dict[str, dict[str, np.ndarray]]:
    out: dict[str, dict[str, np.ndarray]] = {}
    for w in payload["worlds"]["world_list"]:
        src = base_design if w["design"] == "BASE" else s174_design
        out[w["name"]] = {k: np.asarray(v).copy() for k, v in src.items()}
    return out


def build_structural_support(payload: dict, design: dict[str, np.ndarray], *, world_index: int,
                             genes: int | None = None, amendment: dict | None = None) -> np.ndarray:
    """Build the frozen cell×gene structural support truth.

    For the real G=44 qualification this is exactly five genes with composition
    1 single-source-measured / 3 one-source-absent / 1 partial NPH52 (3 of 7
    NPH52 matrices unmeasured). Tiny fixtures use a proportional fallback.
    """
    G = int(genes if genes is not None else payload["worlds"]["genes_per_world"])
    op = np.asarray(design["op"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    support = np.ones((len(src), G), dtype=bool)
    rule = payload["worlds"]["structural_support_rule"]
    n_struct = int(rule["genes_with_structural_absence_per_world"]) if G == int(payload["worlds"]["genes_per_world"]) else min(G, max(1, round(59.0 / 500.0 * G)))
    wi = effective_seed_world_index(world_index, 1, amendment) if amendment is not None else int(world_index)
    rng = np.random.default_rng(seed_for(world_index=wi, gene_index=9999, stream=1, root=int(payload["seeds"]["root"])))
    structural_genes = np.sort(rng.choice(G, size=n_struct, replace=False))
    sources = np.sort(np.unique(src))

    if n_struct == 5:
        # 1) one gene measured in exactly one source, source selected uniformly.
        g = structural_genes[0]
        keep = int(rng.choice(sources))
        support[:, g] = src == keep

        # 2) three genes each fully absent in one source, weighted 38:20:10 (HVS:NPH52:SEA_AD).
        weights = np.asarray([38.0, 20.0, 10.0], dtype=float)
        if len(sources) != 3:
            raise SystemExit("STOP: frozen support rule requires three sources")
        weights /= weights.sum()
        for g in structural_genes[1:4]:
            absent = int(rng.choice(sources, p=weights))
            support[:, g] = src != absent

        # 3) one partial gene: exactly floor(7/2)=3 of NPH52's 7 matrices absent.
        nph52 = int(sources[1])
        nph_ops = np.unique(op[src == nph52])
        if len(nph_ops) != 7:
            raise SystemExit(f"STOP: frozen partial-support rule requires 7 NPH52 matrices, got {len(nph_ops)}")
        g = structural_genes[4]
        drop = set(int(x) for x in rng.choice(nph_ops, size=3, replace=False))
        support[:, g] = np.array([not (int(s) == nph52 and int(o) in drop) for s, o in zip(src, op)], dtype=bool)
        return support

    # Tiny-fixture fallback: preserve the measured-vs-unmeasured code path without pretending 1/3/1 composition fits.
    for g in structural_genes:
        absent = int(rng.choice(sources))
        support[:, g] = src != absent
    return support


def _rescale_donor_effects(part: dict, new_sd: np.ndarray) -> None:
    part["donor_sd"] = np.asarray(new_sd, dtype=float)
    if "donor_z" in part:
        part["donor_effects"] = np.asarray(part["donor_z"], dtype=float) * part["donor_sd"][None, :]
    elif np.all(part["donor_sd"] == 0):
        part["donor_effects"] = np.zeros_like(np.asarray(part["donor_effects"], dtype=float))


def _sparse_prevalence(G: int, world_index: int, payload: dict) -> np.ndarray:
    root = int(payload["seeds"]["root"])
    perm_rng = np.random.default_rng(seed_for(world_index=world_index, gene_index=9999, stream=50, root=root))
    perm = perm_rng.permutation(G)
    out = np.empty(G, dtype=float)
    lo, hi = np.log(0.005), np.log(0.05)
    for g in range(G):
        jitter = np.random.default_rng(seed_for(world_index=world_index, gene_index=g, stream=10, root=root)).uniform()
        level = (perm[g] + jitter) / G
        out[g] = np.exp(lo + level * (hi - lo))
    return out


def apply_world_modifications(base_truth: dict, world_def: dict, payload: dict) -> dict:
    """Apply only the prospectively frozen Q01-Q09 modification semantics."""
    out = copy.deepcopy(base_truth)
    mods = world_def.get("modifications", {})
    fixed = payload["worlds"]["planting_magnitudes"]["fixed_magnitudes"]
    G = len(out["detection"]["donor_sd"])

    donor_mod = mods.get("donor_sd")
    if donor_mod in ("weak", "strong"):
        key = f"{donor_mod}_donor_sd"
        _rescale_donor_effects(out["detection"], np.full(G, float(fixed[key]["detection"])))
        _rescale_donor_effects(out["positive"], np.full(G, float(fixed[key]["positive"])))
    elif donor_mod == "absent":
        _rescale_donor_effects(out["detection"], np.zeros(G))
        _rescale_donor_effects(out["positive"], np.zeros(G))

    if mods.get("source") == "weak":
        for part_name in ("detection", "positive"):
            arr = np.asarray(out[part_name]["source_contrasts"], dtype=float)
            signs = np.where(arr < 0, -1.0, 1.0)
            out[part_name]["source_contrasts"] = signs * float(fixed["weak_abs_source"][part_name])
    elif mods.get("source") == "absent":
        for p in ("detection", "positive"):
            out[p]["source_contrasts"] = np.zeros_like(out[p]["source_contrasts"], dtype=float)

    if mods.get("class") == "absent":
        for p in ("detection", "positive"):
            out[p]["class_contrasts"] = np.zeros_like(out[p]["class_contrasts"], dtype=float)

    if mods.get("depth2") == "absent":
        for p in ("detection", "positive"):
            out[p]["depth2"] = np.zeros_like(out[p]["depth2"], dtype=float)

    if mods.get("prevalence") == "sparse":
        out["detection"]["prevalence"] = _sparse_prevalence(G, int(world_def["index"]), payload)

    if mods.get("sigma") == "tail":
        out["positive"]["sigma"] = np.full(G, float(fixed["tail_sigma"]))

    return out


def generate_operator_offsets(design: dict[str, np.ndarray], *, donor_sd: float, world_index: int,
                              gene_index: int, part: str, payload: dict, amendment: dict) -> np.ndarray:
    """Generate Q11 operator offsets and centre them unweighted within source."""
    if part not in ("detection", "positive"):
        raise ValueError("part must be detection or positive")
    stream = 22 if part == "detection" else 23
    wi = effective_seed_world_index(world_index, stream, amendment)
    root = int(payload["seeds"]["root"])
    rng = np.random.default_rng(seed_for(world_index=wi, gene_index=gene_index, stream=stream, root=root))
    op = np.asarray(design["op"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    if np.min(op) < 0:
        raise SystemExit("STOP: operator IDs must be nonnegative integer codes")
    out = np.zeros(int(np.max(op)) + 1, dtype=float)
    scale = 0.5 * float(donor_sd)
    for s in np.unique(src):
        ops = np.unique(op[src == s])
        for o in ops:
            if len(np.unique(src[op == o])) != 1:
                raise SystemExit("STOP: operator maps to multiple sources")
        raw = rng.normal(0.0, scale, size=len(ops))
        raw -= raw.mean()
        out[ops] = raw
    return out


def apply_poison(counts: np.ndarray, support: np.ndarray, *, poison: int = -1) -> np.ndarray:
    counts = np.asarray(counts)
    support = np.asarray(support, dtype=bool)
    if counts.shape != support.shape:
        raise ValueError("counts/support shape mismatch")
    out = counts.copy()
    out[~support] = poison
    return out


def opaque_world_id(name: str) -> str:
    return hashlib.sha256(("V2CORE|" + name).encode("utf-8")).hexdigest()[:12]


def build_manifest(*, world_name: str, world_index: int, truth: dict, final_contract_sha: str,
                   payload_sha: str, generated_files: dict[str, str]) -> dict:
    if final_contract_sha != FINAL_CONTRACT_SHA256:
        raise SystemExit("STOP: wrong final Contract V2 SHA")
    if payload_sha != QUALIFICATION_PAYLOAD_SHA256:
        raise SystemExit("STOP: wrong qualification payload SHA")
    return {
        "schema": "V79_V2_CORE_WORLD_MANIFEST_V1",
        "world_name": world_name,
        "world_index": int(world_index),
        "opaque_world_id": opaque_world_id(world_name),
        "final_contract_sha256": final_contract_sha,
        "qualification_payload_sha256": payload_sha,
        "pairing_amendment_sha256": PAIRING_AMENDMENT_SHA256,
        "scientific_truth_sha256": scientific_truth_sha(truth),
        "generated_outputs": dict(sorted(generated_files.items())),
        "qualification_fits_run": 0,
        "benchmark_run": False,
        "training_authorized": False,
    }


def validate_realization_authorization(authorization: dict | None) -> dict:
    if not authorization:
        raise SystemExit("STOP: realized world generation requires separate controller authorization receipt")
    if authorization.get("schema") != REALIZATION_AUTH_SCHEMA:
        raise SystemExit("STOP: wrong realization authorization schema")
    if authorization.get("final_contract_sha256") != FINAL_CONTRACT_SHA256:
        raise SystemExit("STOP: authorization does not bind final Contract V2")
    if authorization.get("pairing_amendment_sha256") != PAIRING_AMENDMENT_SHA256:
        raise SystemExit("STOP: authorization does not bind Q10/Q11 pairing amendment")
    if authorization.get("world_generation_authorized") is not True:
        raise SystemExit("STOP: world generation is not authorized")
    if authorization.get("qualification_fitting_authorized") is not False:
        raise SystemExit("STOP: realization authorization may not authorize fitting")
    head = authorization.get("generator_code_head")
    ci = authorization.get("generator_green_ci")
    if not isinstance(head, str) or len(head) < 7 or not isinstance(ci, dict) or not ci.get("passed"):
        raise SystemExit("STOP: authorization must bind audited generator head and green CI")
    return authorization


def realize_worlds(payload: dict, design: dict[str, np.ndarray], out_dir: Path, authorization: dict | None) -> None:
    validate_realization_authorization(authorization)
    raise SystemExit("STOP: realization engine not yet controller-audited for physical Q00-Q11 emission")
