#!/usr/bin/env python3
"""Deterministic V79 V2_CORE synthetic-world generator primitives.

Engineering only until a separate controller realization-authorization receipt exists.
The canonical final Contract V2 (PR #290, SHA-256 57e19295...) plus the prospective Q10/Q11 pairing amendment
define the world semantics. Neither authority alone permits realized world bytes.

Authority (controller rebind ruling 6115340528): the contract is obtained only through PR #290's
v79_v2_core_launch.require_launch_authority(). This module keeps no competing contract validator. The
non-canonical PR #289 contract is named once, as OBSOLETE_CONTRACT_SHA256, and only so that it can be refused.

Pre-realization repairs (controller audit at PR #291 312bb302):
- donor-strength worlds rescale the realized donor-effect arrays from one canonical latent field
  (donor_raw_centered); a truth object without it is refused;
- the detection intercept is solved per world after modifications and the structural-support mask, over
  measured cells only (build_world_truth);
- source codes follow canonical metadata (SOURCE_CODES, verified by source_code_mapping).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v79_v2_core_launch as L  # noqa: E402  (PR #290: the single launch-authority gate)
import v79_v2_core_observation as O  # noqa: E402
import v79_v2_core_planting as P  # noqa: E402

FINAL_CONTRACT_SHA256 = L.FINAL_CONTRACT_SHA256
OBSOLETE_CONTRACT_SHA256 = "8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d"  # refused, never authority
QUALIFICATION_PAYLOAD_SHA256 = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
PAIRING_AMENDMENT_REL = ("results/v79/v2_core_qualification_amendments/"
                         "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1.json")
PAIRING_AMENDMENT_SHA256 = "57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5"
PAIRING_CONTROLLER_COMMENT = 6114906562
REBIND_CONTROLLER_COMMENT = 6115340528
REALIZATION_AUTH_SCHEMA = "V79_V2_CORE_WORLD_REALIZATION_AUTHORIZATION_V1"
SOURCE_CODES = {"HVS": 0, "NPH52": 1, "SEA_AD": 2}
CONTRACT_DIR = "results/v79/v2_core_qualification"


def seed_for(*, world_index: int, gene_index: int, stream: int, root: int) -> int:
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(int(world_index), int(gene_index), int(stream)))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def load_launch_contract(root: Path) -> tuple[dict, dict]:
    """Canonical Contract V2 through the PR #290 gate, plus its immutable scientific payload (the accepted draft).

    The payload's worlds/seeds/gates/priors/model must equal the contract's; any difference STOPs."""
    root = Path(root)
    contract = L.require_launch_authority(root / CONTRACT_DIR / L.FINAL_CONTRACT_NAME, root=root)
    if contract.get("finalization", {}).get("from_accepted_draft_sha256") != QUALIFICATION_PAYLOAD_SHA256:
        raise SystemExit("STOP: canonical contract does not derive from the immutable payload")
    draft = contract["accepted_evidence"]["contract_v2_draft"]
    raw = (root / draft["path"]).read_bytes()
    if draft["sha256"] != QUALIFICATION_PAYLOAD_SHA256 or hashlib.sha256(raw).hexdigest() != QUALIFICATION_PAYLOAD_SHA256:
        raise SystemExit("STOP: immutable qualification payload hash mismatch")
    payload = json.loads(raw)
    for key in ("worlds", "seeds", "gates", "priors", "model"):
        if payload.get(key) != contract.get(key):
            raise SystemExit(f"STOP: payload and canonical contract disagree on {key}")
    return contract, payload


def validate_pairing_amendment_content(a: dict) -> dict:
    if a.get("schema") != "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1":
        raise SystemExit("STOP: wrong pairing amendment schema")
    if a.get("controller_comment") != PAIRING_CONTROLLER_COMMENT or a.get("rebind_controller_comment") != REBIND_CONTROLLER_COMMENT:
        raise SystemExit("STOP: pairing amendment controller binding mismatch")
    if a.get("final_contract_sha256") == OBSOLETE_CONTRACT_SHA256:
        raise SystemExit("STOP: pairing amendment is bound to the obsolete non-canonical contract")
    if a.get("final_contract_sha256") != FINAL_CONTRACT_SHA256 or a.get("qualification_payload_sha256") != QUALIFICATION_PAYLOAD_SHA256:
        raise SystemExit("STOP: pairing amendment authority binding mismatch")
    if a.get("worlds_generated_at_freeze") != 0 or a.get("qualification_fits_at_freeze") != 0:
        raise SystemExit("STOP: pairing amendment was not frozen pre-outcome")
    if a.get("authorization", {}).get("world_realization") is not False:
        raise SystemExit("STOP: pairing amendment may not itself authorize realization")
    pair = a.get("paired_counterfactual", {})
    if pair.get("all_q11_gates_remain") != "HARD_FAIL" or \
            {int(v) for v in pair.get("q11_new_randomness_only", {}).values()} != {22, 23}:
        raise SystemExit("STOP: pairing amendment semantics changed")
    return a


def load_pairing_amendment(root: Path) -> dict:
    path = Path(root) / PAIRING_AMENDMENT_REL
    if not path.exists():
        raise SystemExit("STOP: Q10/Q11 pairing amendment is required")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PAIRING_AMENDMENT_SHA256:
        raise SystemExit("STOP: Q10/Q11 pairing amendment SHA mismatch")
    sidecar = path.with_suffix(".sha256")
    if not sidecar.exists() or sidecar.read_text(encoding="utf-8").strip() != f"{digest}  {path.name}":
        raise SystemExit("STOP: Q10/Q11 pairing amendment sidecar mismatch")
    return validate_pairing_amendment_content(json.loads(raw))


def source_code_mapping(root: Path) -> dict[str, int]:
    """Source name -> design code, from canonical metadata: the S174 operator bridge (operator -> source name)
    joined to the authenticated S174 design-only arrays (operator -> source code)."""
    root = Path(root)
    bridge = L.ACCEPTED_EVIDENCE["s174_operator_bridge"]
    braw = (root / bridge["path"]).read_bytes()
    if hashlib.sha256(braw).hexdigest() != bridge["sha256"]:
        raise SystemExit("STOP: S174 operator bridge hash mismatch")
    op_source = {}
    for r in json.loads(braw)["rows"]:
        op_source.setdefault(int(r["operator_index"]), set()).add(str(r["source"]))
    design = load_s174_design(root)
    mapping: dict[str, set] = {}
    for o in np.unique(design["op"]):
        names = op_source.get(int(o), set())
        if len(names) != 1:
            raise SystemExit(f"STOP: operator {int(o)} has no unique bridge source")
        mapping.setdefault(next(iter(names)), set()).update(int(c) for c in np.unique(design["src"][design["op"] == o]))
    if any(len(v) != 1 for v in mapping.values()) or len({next(iter(v)) for v in mapping.values()}) != len(mapping):
        raise SystemExit(f"STOP: source names and codes are not a bijection: {mapping}")
    return {k: next(iter(v)) for k, v in sorted(mapping.items(), key=lambda kv: next(iter(kv[1])))}


def load_s174_design(root: Path) -> dict[str, np.ndarray]:
    """The authenticated value-blind S174 design (contract input s174_design_only)."""
    rec = L.ACCEPTED_EVIDENCE["s174_design_only"]
    path = Path(root) / "results/v79/v2_core_qualification/inputs/V79_S174_DESIGN_ONLY_V1.npz"
    if hashlib.sha256(path.read_bytes()).hexdigest() != rec["sha256"]:
        raise SystemExit("STOP: S174 design-only hash mismatch")
    with np.load(path, allow_pickle=False) as z:
        return {"src": np.asarray(z["src"], np.int64), "donor": np.asarray(z["donor"], np.int64),
                "cls": np.asarray(z["cls"], np.int64), "op": np.asarray(z["op"], np.int64),
                "log_lib": np.asarray(z["log_lib_centered"], np.float64)}


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
        if sorted(int(s) for s in sources) != sorted(SOURCE_CODES.values()):
            raise SystemExit("STOP: frozen support rule requires the three canonical source codes")
        name_of = {code: name for name, code in SOURCE_CODES.items()}
        g = structural_genes[0]
        keep = int(rng.choice(sources))
        support[:, g] = src == keep

        weights = np.asarray([float(rule["one_source_absent_probabilities"][name_of[int(s)]]) for s in sources],
                             dtype=float)
        weights /= weights.sum()
        for g in structural_genes[1:4]:
            absent = int(rng.choice(sources, p=weights))
            support[:, g] = src != absent

        nph52 = int(SOURCE_CODES["NPH52"])
        nph_ops = np.unique(op[src == nph52])
        if len(nph_ops) != 7:
            raise SystemExit(f"STOP: frozen partial-support rule requires 7 NPH52 matrices, got {len(nph_ops)}")
        g = int(structural_genes[4])
        wi24 = effective_seed_world_index(world_index, 24, amendment) if amendment is not None else int(world_index)
        rng24 = np.random.default_rng(seed_for(world_index=wi24, gene_index=g, stream=24,
                                                root=int(payload["seeds"]["root"])))
        drop = set(int(x) for x in rng24.choice(nph_ops, size=3, replace=False))
        support[:, g] = np.array([not (int(s) == nph52 and int(o) in drop) for s, o in zip(src, op)], dtype=bool)
        return support

    for g in structural_genes:
        absent = int(rng.choice(sources))
        support[:, g] = src != absent
    return support


def _rescale_donor_effects(part: dict, new_sd: np.ndarray) -> None:
    """Realized donor effects = canonical latent field x donor SD, for every gene."""
    if "donor_raw_centered" not in part:
        raise SystemExit("STOP: donor rescale requires the canonical latent field donor_raw_centered")
    part["donor_sd"] = np.asarray(new_sd, dtype=float)
    part["donor_effects"] = np.asarray(part["donor_raw_centered"], dtype=float) * part["donor_sd"][None, :]


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
        for part in ("detection", "positive"):
            out[part]["donor_raw_centered"] = np.zeros_like(np.asarray(out[part]["donor_raw_centered"], dtype=float))
            if "factor_loading" in out[part]:
                out[part]["factor_loading"] = np.zeros_like(np.asarray(out[part]["factor_loading"], dtype=float))

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


def build_world_designs(root: Path, payload: dict) -> dict[str, dict[str, np.ndarray]]:
    """BASE (shared key [100,0,0], S174 sizes) for Q00-Q09 and the exact S174 arrays for Q10/Q11."""
    actual_mapping = source_code_mapping(root)
    if actual_mapping != SOURCE_CODES:
        raise SystemExit(f"STOP: SOURCE_CODES disagree with authenticated source mapping: {actual_mapping}")
    s174 = load_s174_design(root)
    donors_per_source = tuple(int(len(np.unique(s174["donor"][s174["src"] == c]))) for c in sorted(SOURCE_CODES.values()))
    if donors_per_source != (62, 19, 68):
        raise SystemExit(f"STOP: S174 donors per source {donors_per_source} differ from the contract (62, 19, 68)")
    base = P.build_base_design(s174, donors_per_source=donors_per_source, root=int(payload["seeds"]["root"]))
    return build_designs(payload, base_design=base, s174_design=s174)


def detection_nonintercept_predictor(design: dict[str, np.ndarray], det: dict) -> np.ndarray:
    z, q = O.depth_basis(design["log_lib"])
    cls = np.asarray(design["cls"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    Hc = O.normalized_helmert(3)
    Hs = O.normalized_helmert(3)
    eta = z[:, None] * np.asarray(det["depth1"], float)[None, :] + q[:, None] * np.asarray(det["depth2"], float)[None, :]
    eta = eta + Hc[cls] @ np.asarray(det["class_contrasts"], float).T + Hs[src] @ np.asarray(det["source_contrasts"], float).T
    return eta


def solve_detection_intercept_for_gene(nonintercept: np.ndarray, measured: np.ndarray, target: float) -> float:
    return P.solve_detection_intercept(np.asarray(nonintercept, float), np.asarray(measured, bool),
                                       target_prevalence=float(target))


def _src_by_donor(design: dict[str, np.ndarray]) -> np.ndarray:
    donor = np.asarray(design["donor"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    out = np.full(int(donor.max()) + 1, -1, dtype=np.int64)
    for d in range(len(out)):
        s = np.unique(src[donor == d])
        if len(s) != 1:
            raise SystemExit(f"STOP: donor {d} does not belong to exactly one source")
        out[d] = int(s[0])
    return out


def build_world_truth(payload: dict, cal: dict, designs: dict[str, dict[str, np.ndarray]], world_def: dict,
                      amendment: dict) -> dict:
    """In-memory planted truth for one world (no disk emission)."""
    wi = int(world_def["index"])
    name = str(world_def["name"])
    root = int(payload["seeds"]["root"])
    G = int(payload["worlds"]["genes_per_world"])
    design = designs[name]
    parent = effective_seed_world_index(wi, 50, amendment)
    plant = P.build_q00_planting(cal, payload, world_index=parent, G=G)
    sbd = _src_by_donor(design)
    truth = {}
    for part in ("detection", "positive"):
        don = P.build_donor_effects(sbd, plant[part]["donor_sd"], world_index=parent, part=part, root=root)
        truth[part] = {**{k: np.asarray(v) for k, v in plant[part].items()},
                       "donor_raw_centered": don["raw_centered"], "donor_effects": don["effects"],
                       "factor_loading": don["lambda"]}
    truth = apply_world_modifications(truth, world_def, payload)
    support = build_structural_support(payload, design, world_index=wi, amendment=amendment)
    nonint = detection_nonintercept_predictor(design, truth["detection"])
    truth["detection"]["intercept"] = np.asarray(
        [solve_detection_intercept_for_gene(nonint[:, g], support[:, g], truth["detection"]["prevalence"][g])
         for g in range(G)], dtype=float)
    offsets = None
    if world_def.get("modifications", {}).get("operator") == "omitted_perturbation":
        offsets = {part: np.column_stack([
            generate_operator_offsets(design, donor_sd=float(truth[part]["donor_sd"][g]), world_index=wi, gene_index=g,
                                      part=part, payload=payload, amendment=amendment) for g in range(G)])
            for part in ("detection", "positive")}
    return {"world": name, "world_index": wi, "seed_parent_world_index": parent, "detection": truth["detection"],
            "positive": truth["positive"], "support": support, "operator_offsets": offsets}


def non_operator_truth_sha(world_truth: dict) -> str:
    return scientific_truth_sha({"detection": world_truth["detection"], "positive": world_truth["positive"],
                                 "support": world_truth["support"]})


def generate_operator_offsets(design: dict[str, np.ndarray], *, donor_sd: float, world_index: int,
                              gene_index: int, part: str, payload: dict, amendment: dict) -> np.ndarray:
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


def validate_poison_integrity(observed: np.ndarray, support: np.ndarray, *, poison: float = -1.0) -> None:
    observed = np.asarray(observed)
    support = np.asarray(support, dtype=bool)
    if observed.shape != support.shape:
        raise SystemExit("STOP: observed/support shape mismatch")
    if np.any(observed[support] == poison):
        raise SystemExit("STOP: poison sentinel appears in a structurally measured entry")
    if np.any(observed[~support] != poison):
        raise SystemExit("STOP: structurally unmeasured entry is not poisoned")


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
