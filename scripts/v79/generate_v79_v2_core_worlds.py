#!/usr/bin/env python3
"""Deterministic V79 V2_CORE synthetic-world generator primitives.

Engineering only until a separate controller realization-authorization receipt exists.
The final Contract V2 plus the prospective Q10/Q11 pairing amendment define the
world semantics. Neither authority alone permits realized world bytes.
"""
from __future__ import annotations

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
    """Stable uint32 seed keyed only by effective scientific identity."""
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
    """Apply the frozen paired-counterfactual seed identity.

    Q11 inherits Q10 for every base stream. Only operator offset streams 22/23
    retain Q11 world identity and therefore add new randomness.
    """
    pair = amendment["paired_counterfactual"]
    q10 = int(pair["parent_world"]["world_index"])
    q11 = int(pair["child_world"]["world_index"])
    new_streams = {int(v) for v in pair["q11_new_randomness_only"].values()}
    if int(world_index) == q11 and int(stream) not in new_streams:
        return q10
    return int(world_index)


def validate_q10_q11_pairing(q10: dict, q11: dict, amendment: dict) -> None:
    """Fail closed unless Q10/Q11 truth differs only in operator-offset fields."""
    allowed = {"operator_offsets_detection_sha", "operator_offsets_positive_sha"}
    keys = set(q10) | set(q11)
    for key in keys - allowed:
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
    """Hash scientific truth canonically; poison/storage bytes are not implicit truth."""
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


def _matrix_levels(design: dict[str, np.ndarray]) -> np.ndarray:
    return np.unique(np.asarray(design["op"], dtype=np.int64))


def build_structural_support(payload: dict, design: dict[str, np.ndarray], *, world_index: int, genes: int | None = None,
                             amendment: dict | None = None) -> np.ndarray:
    G = int(genes if genes is not None else payload["worlds"]["genes_per_world"])
    n_cell = len(np.asarray(design["src"]))
    op = np.asarray(design["op"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    support = np.ones((n_cell, G), dtype=bool)
    frac = 59.0 / 500.0
    n_struct = min(G, max(1, round(frac * G)))
    wi = effective_seed_world_index(world_index, 1, amendment) if amendment is not None else int(world_index)
    rng = np.random.default_rng(seed_for(world_index=wi, gene_index=9999, stream=1, root=int(payload["seeds"]["root"])))
    structural_genes = np.sort(rng.choice(G, size=n_struct, replace=False))
    for j, g in enumerate(structural_genes):
        if j == 0 and n_struct >= 3:
            keep_source = int(rng.choice(np.unique(src)))
            support[:, g] = src == keep_source
        elif j == n_struct - 1 and n_struct >= 2:
            candidate_sources = [int(s) for s in np.unique(src) if len(np.unique(op[src == s])) >= 2]
            if candidate_sources:
                s = int(rng.choice(candidate_sources))
                ops = np.unique(op[src == s])
                n_drop = max(1, len(ops) // 2)
                drop = set(int(x) for x in rng.choice(ops, size=n_drop, replace=False))
                support[:, g] = np.array([not (int(ss) == s and int(oo) in drop) for ss, oo in zip(src, op)], dtype=bool)
            else:
                absent_source = int(rng.choice(np.unique(src)))
                support[:, g] = src != absent_source
        else:
            absent_source = int(rng.choice(np.unique(src)))
            support[:, g] = src != absent_source
    return support


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
