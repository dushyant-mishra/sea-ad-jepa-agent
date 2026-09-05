#!/usr/bin/env python3
"""F1-B minimal mechanism bridge.

Governed by docs/agent/F1B_MINIMAL_BRIDGE_CONTRACT_20260905.md.

Qualifies whether the planned production mechanism can learn a query-local contextual
target without routing collapse: IPBEncoder + SingletonQueryPredictor +
directional_pair_context_loss, EMA teacher on rich evidence, student on partial evidence.

`synthetic` mode is self-contained and needs no expression. `technical-fixture` and `real`
fail closed without an external launch authority. This file must not create one.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

STOP_UNAUTHORIZED = "STOP_F1B_REAL_RUN_NOT_EXTERNALLY_AUTHORIZED"
LAUNCH_SCHEMA = "f1b-minimal-bridge-external-authority-v1"
CONTRACT_RELATIVE = Path("docs/agent/F1B_MINIMAL_BRIDGE_CONTRACT_20260905.md")

V, WIDTH, HEADS, BLOCKS, IDENTITY_DIM = 41238, 160, 4, 6, 48

# Frozen byte authorities. Tracked python sources are LF-normalised before hashing
# because .gitattributes forces eol=lf only for *.sh; data artifacts are raw-byte hashed.
FROZEN = {
    "ipb_jepa.py": "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a",
    "gene_tokenizer.py": "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4",
    "full104_model_components_v2.py": "c69ed6abb68f31e6177170ebafa1b412b0780d47d83e00776707a4c8cd4ae342",
    "u0_checkpoint": "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4",
    "program_weights": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
}
RELATIVE = {
    "ipb_jepa.py": Path("src/sea_ad_jepa/v4/ipb_jepa.py"),
    "gene_tokenizer.py": Path("src/sea_ad_jepa/v4/gene_tokenizer.py"),
    "full104_model_components_v2.py": Path(
        "exports/jepa_codex_adaptive_handoff_v014_20260826/"
        "JEPA_CODEX_ADAPTIVE_HANDOFF_V014_20260826/codex/code/full104_model_components_v2.py"),
    "u0_checkpoint": Path("exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt"),
    "program_weights": Path("exports/contextual_biology_v6r5a_20260822/program_weights.npz"),
}
LF_NORMALISED = {"ipb_jepa.py", "gene_tokenizer.py"}
RAW_BYTES = {"full104_model_components_v2.py", "u0_checkpoint", "program_weights"}

# The 48 tensors that were exactly gradient-dead for the whole of T1.
PRE_ATTENTION_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
EXPECTED_PRE_ATTENTION_TENSORS = 48


@dataclass(frozen=True)
class Frozen:
    """Every conclusion-bearing constant, fixed before any result exists."""
    cells: int = 4
    queries_per_cell: int = 8
    evidence_level: int = 60
    updates: int = 40
    telemetry_every: int = 5
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    ema_decay: float = 0.996
    seed: int = 20260905
    # G3: movement must exceed pure decoupled decay by this factor. T1 sat at 1.017x.
    movement_over_decay_margin: float = 2.0
    # G4: routing must differ across query addresses by at least this relative spread.
    routing_diversity_floor: float = 1e-6
    # G5: a frozen endpoint may not lose more than this fraction of its baseline.
    rare_degradation_tolerance: float = 0.05
    # An endpoint whose baseline spread is below this is saturated, not decision-bearing.
    saturation_floor: float = 1e-4
    # Routing is called sharpened only if N_eff/N drops below this fraction of baseline.
    sharpening_threshold: float = 0.95


def sha256_source(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def authenticate(canonical_root: Path) -> dict[str, str]:
    """Verify every frozen byte authority before anything else runs."""
    root = Path(canonical_root).resolve()
    actual = {}
    for name, relative in RELATIVE.items():
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"STOP_F1B_AUTHORITY_MISSING:{name}")
        actual[name] = sha256_source(path) if name in LF_NORMALISED else sha256_file(path)
        if actual[name] != FROZEN[name]:
            raise RuntimeError(f"STOP_F1B_AUTHORITY_MISMATCH:{name}")
    return actual


def load_recovered_components(canonical_root: Path):
    """Import the recovered planned components from their exact historical bytes."""
    path = Path(canonical_root).resolve() / RELATIVE["full104_model_components_v2.py"]
    if sha256_file(path) != FROZEN["full104_model_components_v2.py"]:
        raise RuntimeError("STOP_F1B_AUTHORITY_MISMATCH:full104_model_components_v2.py")
    spec = importlib.util.spec_from_file_location("full104_model_components_v2", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["full104_model_components_v2"] = module
    spec.loader.exec_module(module)
    for required in ("SingletonQueryPredictor", "directional_pair_context_loss", "center_queries"):
        if not hasattr(module, required):
            raise RuntimeError(f"STOP_F1B_RECOVERED_COMPONENT_MISSING:{required}")
    return module


def validate_launch_authority(path: Path | None, mode: str, output_root: Path,
                              expected: dict[str, str], worktree_root: Path) -> dict[str, Any]:
    """Fail closed. This file must never synthesise its own authority."""
    try:
        if path is None:
            raise ValueError("missing")
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema") != LAUNCH_SCHEMA:
            raise ValueError("schema")
        if payload.get("f1b_execution_authorized") is not True or \
                type(payload.get("f1b_execution_authorized")) is not bool:
            raise ValueError("boolean")
        if payload.get("mode") != mode:
            raise ValueError("mode")
        if Path(str(payload.get("output_root"))).resolve() != Path(output_root).resolve():
            raise ValueError("output")
        if payload.get("executor_sha256") != sha256_source(Path(__file__)):
            raise ValueError("executor bytes")
        if payload.get("contract_sha256") != sha256_source(worktree_root / CONTRACT_RELATIVE):
            raise ValueError("contract bytes")
        for field, value in expected.items():
            if payload.get("frozen_authorities", {}).get(field) != value:
                raise ValueError(field)
        if mode == "real":
            if payload.get("population_disjoint_from_f1a") is not True:
                raise ValueError("f1a disjointness")
            if payload.get("reader_partition") != "reader_fit":
                raise ValueError("reader partition")
        return payload
    except Exception as error:
        raise RuntimeError(f"{STOP_UNAUTHORIZED}: {type(error).__name__}") from error


# --------------------------------------------------------------------------------------
# Synthetic population
# --------------------------------------------------------------------------------------

def synthetic_population(frozen: Frozen, device: torch.device) -> dict[str, torch.Tensor]:
    """Self-contained cells with realistic sparsity. Carries no biology by construction."""
    rng = np.random.default_rng(frozen.seed)
    n, measured_n, detected_n = frozen.cells, 18736, 5200
    expression = np.zeros((n, V), np.float32)
    measured = np.zeros((n, V), bool)
    for i in range(n):
        m = rng.choice(V, measured_n, replace=False)
        measured[i, m] = True
        det = rng.choice(m, detected_n, replace=False)
        expression[i, det] = np.log1p(rng.gamma(1.5, 2.0, detected_n) * 10.0)
    queries = np.zeros((n, frozen.queries_per_cell), np.int64)
    student_visible = np.zeros((n, V), bool)
    teacher_visible = np.zeros((n, V), bool)
    for i in range(n):
        m = np.flatnonzero(measured[i])
        queries[i] = rng.choice(m, frozen.queries_per_cell, replace=False)
        # Every query is ablated from BOTH roles: strictly stronger than per-query masking.
        eligible = np.setdiff1d(m, queries[i], assume_unique=False)
        teacher_visible[i, eligible] = True
        keep = len(eligible) * frozen.evidence_level // 100
        student_visible[i, rng.permutation(eligible)[:keep]] = True
    return {
        "expression": torch.from_numpy(expression).to(device),
        "measured": torch.from_numpy(measured).to(device),
        "teacher_visible": torch.from_numpy(teacher_visible).to(device),
        "student_visible": torch.from_numpy(student_visible).to(device),
        "queries": torch.from_numpy(queries).to(device),
    }


def assert_no_query_leakage(pop: dict[str, torch.Tensor]) -> None:
    """The query scalar must be invisible to both roles, for every query, in every cell."""
    rows = torch.arange(len(pop["queries"]), device=pop["queries"].device)[:, None]
    for role in ("teacher_visible", "student_visible"):
        if bool(pop[role][rows, pop["queries"]].any()):
            raise RuntimeError(f"STOP_F1B_QUERY_SELF_LEAKAGE:{role}")
    if not bool(pop["measured"][rows, pop["queries"]].all()):
        raise RuntimeError("STOP_F1B_QUERY_NOT_MEASURED")
    if bool((pop["student_visible"] & ~pop["teacher_visible"]).any()):
        raise RuntimeError("STOP_F1B_STUDENT_EVIDENCE_NOT_LAWFUL_SUBSET")


# --------------------------------------------------------------------------------------
# Target construction
# --------------------------------------------------------------------------------------

def contextual_target(encoder, pop: dict[str, torch.Tensor], visible: torch.Tensor,
                      queries: torch.Tensor) -> torch.Tensor:
    """LayerNorm(h_q - mean(h over visible)) at each query. Stop-gradient by caller."""
    ids = torch.arange(V, device=visible.device).expand(len(visible), -1)
    hidden = pop["measured"] & ~visible
    encoded = encoder(gene_ids=ids, expression=pop["expression"],
                      measurement_mask=pop["measured"], hidden_target_mask=hidden, view="student")
    states = encoded.gene_states
    rows = torch.arange(len(states), device=states.device)[:, None]
    h_query = states[rows, queries]
    counts = visible.sum(dim=1).clamp_min(1).to(states.dtype)
    mu = (states * visible[..., None].to(states.dtype)).sum(dim=1) / counts[:, None]
    return F.layer_norm(h_query - mu[:, None, :], (states.shape[-1],)), encoded


def encode_student(encoder, pop: dict[str, torch.Tensor]):
    ids = torch.arange(V, device=pop["expression"].device).expand(len(pop["expression"]), -1)
    hidden = pop["measured"] & ~pop["student_visible"]
    return encoder(gene_ids=ids, expression=pop["expression"], measurement_mask=pop["measured"],
                   hidden_target_mask=hidden, view="student")


# --------------------------------------------------------------------------------------
# Telemetry
# --------------------------------------------------------------------------------------

def pre_attention_tensors(encoder) -> list[tuple[str, torch.nn.Parameter]]:
    out = []
    for name, parameter in encoder.named_parameters():
        if any(role in name for role in PRE_ATTENTION_ROLES):
            out.append((name, parameter))
    return out


def gradient_coverage(encoder) -> dict[str, Any]:
    """Per tensor. Never pooled: T1's pooled IPB_shared read 2.43 while 48 tensors were dead."""
    rows = []
    for name, parameter in pre_attention_tensors(encoder):
        g = parameter.grad
        rows.append({"tensor": name,
                     "grad_norm": 0.0 if g is None else float(g.detach().float().norm()),
                     "grad_is_none": g is None})
    zero = [r["tensor"] for r in rows if r["grad_norm"] == 0.0]
    return {"tensors": len(rows), "zero_norm": len(zero), "zero_tensors": zero[:8],
            "min_norm": min((r["grad_norm"] for r in rows), default=0.0),
            "max_norm": max((r["grad_norm"] for r in rows), default=0.0), "rows": rows}


def optimizer_moments(encoder, optimizer) -> dict[str, Any]:
    zero, total = [], 0
    for name, parameter in pre_attention_tensors(encoder):
        state = optimizer.state.get(parameter, {})
        if "exp_avg" not in state:
            continue
        total += 1
        dead = float(state["exp_avg"].abs().max()) == 0.0 and \
               float(state["exp_avg_sq"].abs().max()) == 0.0
        if dead:
            zero.append(name)
    return {"tensors": total, "zero_moments": len(zero), "zero_tensors": zero[:8]}


def movement_report(encoder, baseline: dict[str, torch.Tensor], frozen: Frozen,
                    steps: int) -> dict[str, Any]:
    """Relative movement against the pure decoupled-decay floor."""
    decay = 1.0 - (1.0 - frozen.learning_rate * frozen.weight_decay) ** max(steps, 1)
    rel = {}
    for name, parameter in pre_attention_tensors(encoder):
        base = baseline[name]
        norm = float(base.norm())
        if norm <= 1e-8:
            continue
        rel[name] = float((parameter.detach().float() - base).norm()) / norm
    values = list(rel.values())
    mean = float(np.mean(values)) if values else 0.0
    return {"pure_decay_prediction": decay, "mean_relative_movement": mean,
            "ratio_over_decay": (mean / decay) if decay > 0 else None,
            "min_relative_movement": float(np.min(values)) if values else 0.0}


def routing_report(encoder, pop: dict[str, torch.Tensor]) -> dict[str, Any]:
    """Effective attended tokens and per-query routing diversity in the encoder."""
    visible = pop["student_visible"]
    n_visible = int(visible[0].sum())
    with torch.no_grad():
        hidden = pop["measured"] & ~visible
        gene_valid = pop["measured"] & ~hidden
        safe = pop["expression"].masked_fill(~gene_valid, 0.0)
        ids = torch.arange(V, device=visible.device).expand(len(visible), -1)
        tokens = torch.cat((encoder.cell_token.expand(len(safe), -1, -1),
                            encoder.tokenizer(ids, safe)), dim=1)
        vmask = torch.cat((torch.ones(len(safe), 1, dtype=torch.bool, device=safe.device),
                           gene_valid), dim=1)
        probes = pop["queries"][0, :4] + 1  # +1 for the CELL token offset
        blocks = []
        for index, block in enumerate(encoder.blocks):
            attention = block.attention
            t = block.attention_norm(tokens)
            shape = (len(safe), tokens.shape[1], HEADS, WIDTH // HEADS)
            q = (F.elu(attention.query(t).reshape(shape).float()) + 1.0).transpose(1, 2)
            k = (F.elu(attention.key(t).reshape(shape).float()) + 1.0).transpose(1, 2)
            k = k * vmask[:, None, :, None]
            scores = torch.einsum("hqd,hnd->hqn", q[0, :, probes, :], k[0]).clamp_min(0)
            p = scores / scores.sum(-1, keepdim=True).clamp_min(1e-30)
            neff = (-(p * (p + 1e-30).log()).sum(-1)).exp()
            # G4: do different query addresses route differently at all?
            spread = float((p.max(dim=1).values - p.min(dim=1).values).max())
            blocks.append({"block": index,
                           "n_eff_over_n": float(neff.mean()) / max(n_visible, 1),
                           "max_weight_over_uniform": float(p.max()) * max(n_visible, 1),
                           "per_query_routing_spread": spread})
            tokens, _ = block(tokens, vmask)
    return {"visible_tokens": n_visible, "blocks": blocks,
            "mean_n_eff_over_n": float(np.mean([b["n_eff_over_n"] for b in blocks])),
            "min_per_query_routing_spread": float(np.min([b["per_query_routing_spread"] for b in blocks]))}


def program_projection(states: torch.Tensor, weights: dict[str, np.ndarray]) -> dict[str, torch.Tensor]:
    """w-weighted projection of the per-cell gene-state field onto each program direction."""
    out = {}
    with torch.no_grad():
        for name, w in weights.items():
            wt = torch.from_numpy(w).to(states.device).float()
            wt = wt / wt.norm().clamp_min(1e-12)
            out[name] = torch.einsum("bvd,v->bd", states.float(), wt)
    return out


def predictor_routing_report(head, encoder, student, pop: dict[str, torch.Tensor]) -> dict[str, Any]:
    """Routing inside the predictor's softmax cross-attention.

    A JEPA predictor is *allowed* to perform the conditional computation. Requiring the
    ELU+1 backbone to sharpen may therefore be the wrong test: selective retrieval can
    legitimately live in the predictor's softmax router. This is measured independently of
    the backbone so the two cannot be confused.

    The recovered component bytes are never modified; the diagnostic re-runs the same
    cross-attention with need_weights=True in a separate no-grad pass.
    """
    with torch.no_grad():
        queries = head.queries(encoder.tokenizer.gene_identity, pop["queries"])
        memory = torch.cat((student.cell_state[:, None], student.gene_states), dim=1)
        valid = torch.cat((torch.ones(len(memory), 1, dtype=torch.bool, device=memory.device),
                           pop["student_visible"]), dim=1)
        _, weights = head.cross_attention(queries, memory, memory, key_padding_mask=~valid,
                                          need_weights=True, average_attn_weights=False)
        # weights: [batch, heads, queries, keys]
        w = weights.float().clamp_min(0)
        w = w / w.sum(-1, keepdim=True).clamp_min(1e-30)
        n_keys = int(valid[0].sum())
        neff = (-(w * (w + 1e-30).log()).sum(-1)).exp()
        # Do different query addresses retrieve different evidence?
        flat = F.normalize(w.mean(dim=1).reshape(len(w), w.shape[2], -1), dim=-1)
        cos = torch.einsum("bqk,bpk->bqp", flat, flat)
        off = ~torch.eye(cos.shape[-1], dtype=torch.bool, device=cos.device)
        return {"keys": n_keys,
                "mean_n_eff_over_n": float(neff.mean()) / max(n_keys, 1),
                "max_weight_over_uniform": float(w.max()) * max(n_keys, 1),
                "query_map_cosine": float(cos[:, off].mean())}


def endpoint_report(states: torch.Tensor, weights: dict[str, np.ndarray], frozen: Frozen,
                    baseline_projection: dict[str, torch.Tensor] | None = None) -> dict[str, Any]:
    """Scale-invariant retention of each program direction, plus a dynamic-range check.

    `retention` is the mean per-cell cosine between the current program projection and the
    frozen baseline projection. Cosine is used deliberately: a magnitude-based endpoint
    drifts with any global rescaling of the representation and would fire on every run.

    `spread` guards against the T1 failure mode where headline R2 endpoints sat at 0.9999,
    saturated at ceiling and structurally unable to register damage. Any endpoint below the
    saturation floor is reported as not decision-bearing.
    """
    projection = program_projection(states, weights)
    out = {}
    for name, current in projection.items():
        spread = float(current.norm(dim=-1).std()) if len(states) > 1 else 0.0
        if baseline_projection is None:
            retention = 1.0
        else:
            retention = float(F.cosine_similarity(current, baseline_projection[name], dim=-1).mean())
        out[name] = {"retention": retention,
                     "magnitude": float(current.norm(dim=-1).mean()),
                     "spread": spread,
                     "saturated": bool(spread < frozen.saturation_floor)}
    return out, projection


# --------------------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------------------

def evaluate_gates(coverage, moments, movement, routing, endpoints, baseline_endpoints,
                   frozen: Frozen, baseline_routing, biology_evaluable: bool) -> dict[str, Any]:
    """G1-G4 are always terminal. G5 is terminal only where biology is evaluable.

    A fixed-projection retention confounds coordinate rotation with information loss.
    Closed v4 finding #4 records that much apparent partial-H loss was rotation, not
    destruction. Synthetic expression carries no biology and no probe can be refit on it,
    so G5 is reported but never terminal in synthetic mode. Real mode must measure
    retention through a refit held-out probe, which is rotation-invariant.
    """
    g1 = coverage["tensors"] == EXPECTED_PRE_ATTENTION_TENSORS and coverage["zero_norm"] == 0
    g2 = moments["tensors"] == EXPECTED_PRE_ATTENTION_TENSORS and moments["zero_moments"] == 0
    g3 = bool(movement["ratio_over_decay"] is not None and
              movement["ratio_over_decay"] >= frozen.movement_over_decay_margin)
    g4 = bool(routing["min_per_query_routing_spread"] > frozen.routing_diversity_floor)
    degraded = []
    if biology_evaluable:
        for name, current in endpoints.items():
            base = baseline_endpoints.get(name)
            if base is None or base["saturated"]:
                continue
            if (1.0 - current["retention"]) > frozen.rare_degradation_tolerance:
                degraded.append(name)
    g5 = not degraded
    ratio = routing["mean_n_eff_over_n"] / max(baseline_routing["mean_n_eff_over_n"], 1e-12)
    outcome = ("ROUTING_SHARPENED" if ratio < frozen.sharpening_threshold
               else "ROUTING_DIFFUSE_WITH_HEALTHY_GRADIENTS" if (g1 and g2 and g3)
               else "ROUTING_UNRESOLVED")
    return {
        "G1_gradient_coverage": bool(g1),
        "G2_optimizer_moments": bool(g2),
        "G3_movement_beyond_decay": g3,
        "G4_routing_diversity": g4,
        "G5_rare_non_degradation": bool(g5) if biology_evaluable else "NOT_EVALUABLE_SYNTHETIC",
        "G5_terminal": bool(biology_evaluable),
        "degraded_endpoints": degraded,
        "all_mechanics_pass": bool(g1 and g2 and g3 and g4 and g5),
        "routing_outcome": outcome,
        "routing_ratio_vs_baseline": ratio,
    }


# --------------------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------------------

def run(mode: str, output_root: Path, canonical_root: Path, worktree_root: Path,
        launch_authority: Path | None, frozen: Frozen) -> dict[str, Any]:
    authorities = authenticate(canonical_root)
    if mode != "synthetic":
        validate_launch_authority(launch_authority, mode, output_root, authorities, worktree_root)
        raise RuntimeError(f"{STOP_UNAUTHORIZED}: mode {mode} has no authorized data path in this contract")

    components = load_recovered_components(canonical_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(frozen.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(frozen.seed)

    sys.path.insert(0, str(Path(canonical_root).resolve() / "src"))
    from sea_ad_jepa.v4.ipb_jepa import IPBEncoder

    payload = torch.load(Path(canonical_root).resolve() / RELATIVE["u0_checkpoint"],
                         map_location="cpu", weights_only=False)
    online = IPBEncoder(vocabulary_size=V, width=WIDTH, heads=HEADS, blocks=BLOCKS,
                        gradient_checkpointing=True).to(device)
    online.load_state_dict(payload["online_encoder"])
    teacher = IPBEncoder(vocabulary_size=V, width=WIDTH, heads=HEADS, blocks=BLOCKS,
                         gradient_checkpointing=False).to(device)
    teacher.load_state_dict(payload["online_encoder"])
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad_(False)
    head = components.SingletonQueryPredictor(identity_dim=IDENTITY_DIM, width=WIDTH,
                                              heads=HEADS).to(device)
    online.train(); head.train()

    parameters = list(online.parameters()) + list(head.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=frozen.learning_rate,
                                  weight_decay=frozen.weight_decay)

    pop = synthetic_population(frozen, device)
    assert_no_query_leakage(pop)
    pairs = torch.tensor([[i, j] for i in range(frozen.cells) for j in range(i + 1, frozen.cells)],
                         dtype=torch.long, device=device)

    zdata = np.load(Path(canonical_root).resolve() / RELATIVE["program_weights"], allow_pickle=True)
    programs = {k[4:]: np.asarray(zdata["l2__" + k[4:]], np.float32)
                for k in zdata.keys() if k.startswith("l2__")}

    baseline_state = {n: p.detach().float().clone() for n, p in pre_attention_tensors(online)}
    baseline_routing = routing_report(online, pop)
    with torch.no_grad():
        base_enc = encode_student(online, pop)
        baseline_predictor_routing = predictor_routing_report(head, online, base_enc, pop)
        baseline_endpoints, baseline_projection = endpoint_report(
            base_enc.gene_states, programs, frozen)
    del base_enc

    history, aborted, abort_reason = [], False, None
    for step in range(1, frozen.updates + 1):
        optimizer.zero_grad(set_to_none=True)
        with torch.no_grad():
            target, _ = contextual_target(teacher, pop, pop["teacher_visible"], pop["queries"])
            target = target.detach()
        student = encode_student(online, pop)
        predicted = head(online.tokenizer.gene_identity, pop["queries"],
                         student.gene_states, student.cell_state, pop["student_visible"])
        loss, stats = components.directional_pair_context_loss(predicted, target, pairs)
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("STOP_F1B_NONFINITE_LOSS")
        loss.backward()
        coverage = gradient_coverage(online)
        optimizer.step()
        with torch.no_grad():
            for tp, op in zip(teacher.parameters(), online.parameters()):
                tp.mul_(frozen.ema_decay).add_(op.detach(), alpha=1.0 - frozen.ema_decay)
        moments = optimizer_moments(online, optimizer)

        if step == 1 or step % frozen.telemetry_every == 0 or step == frozen.updates:
            movement = movement_report(online, baseline_state, frozen, step)
            routing = routing_report(online, pop)
            with torch.no_grad():
                probe = encode_student(online, pop)
                endpoints, _ = endpoint_report(probe.gene_states, programs, frozen,
                                               baseline_projection)
                predictor_routing = predictor_routing_report(head, online, probe, pop)
                del probe
            gates = evaluate_gates(coverage, moments, movement, routing, endpoints,
                                   baseline_endpoints, frozen, baseline_routing,
                                   biology_evaluable=(mode != "synthetic"))
            record = {"update": step, "loss": float(loss.detach()),
                      "mean_cosine": stats["mean_cosine"], "valid_fraction": stats["valid_fraction"],
                      "gradient_coverage": {k: v for k, v in coverage.items() if k != "rows"},
                      "optimizer_moments": moments, "movement": movement,
                      "routing_backbone": {k: v for k, v in routing.items() if k != "blocks"},
                      "routing_predictor": predictor_routing,
                      "endpoints": endpoints, "gates": gates}
            history.append(record)
            print("u%-4d loss=%.6f cos=%+.4f | G1=%s G2=%s G3=%s G4=%s G5=%s | "
                  "grad_dead=%d/%d moments_dead=%d/%d | move/decay=%s | N_eff/N=%.5f"
                  % (step, record["loss"], stats["mean_cosine"],
                     gates["G1_gradient_coverage"], gates["G2_optimizer_moments"],
                     gates["G3_movement_beyond_decay"], gates["G4_routing_diversity"],
                     gates["G5_rare_non_degradation"],
                     coverage["zero_norm"], coverage["tensors"],
                     moments["zero_moments"], moments["tensors"],
                     ("%.2f" % movement["ratio_over_decay"]) if movement["ratio_over_decay"] else "n/a",
                     routing["mean_n_eff_over_n"]), flush=True)
            print("        backbone N_eff/N=%.5f | PREDICTOR N_eff/N=%.5f max/unif=%.3f "
                  "query_map_cos=%.5f"
                  % (routing["mean_n_eff_over_n"], predictor_routing["mean_n_eff_over_n"],
                     predictor_routing["max_weight_over_uniform"],
                     predictor_routing["query_map_cosine"]), flush=True)
            if not gates["G1_gradient_coverage"] or not gates["G2_optimizer_moments"]:
                aborted, abort_reason = True, "STOP_F1B_ATTENTION_PATH_DEAD"
                break
            if gates["G5_terminal"] and not gates["G5_rare_non_degradation"]:
                aborted, abort_reason = True, "STOP_F1B_ENDPOINT_DEGRADATION"
                break
        del student, predicted, target, loss

    final = history[-1] if history else {}
    terminal = (abort_reason if aborted else
                "PASS_F1B_MINIMAL_BRIDGE_IMPLEMENTATION_AWAITING_INDEPENDENT_VERIFICATION"
                if final.get("gates", {}).get("all_mechanics_pass") else
                "STOP_F1B_MECHANICS_GATES_NOT_MET")
    document = {
        "schema": "f1b-minimal-bridge-v1",
        "terminal": terminal,
        "mode": mode,
        "implementer_may_not_issue_verifier_pass": True,
        "contract": str(CONTRACT_RELATIVE.as_posix()),
        "contract_sha256": sha256_source(worktree_root / CONTRACT_RELATIVE),
        "executor_sha256": sha256_source(Path(__file__)),
        "frozen_parameters": asdict(frozen),
        "frozen_authorities": authorities,
        "device": device.type,
        "torch_version": torch.__version__,
        "components": {"encoder": "IPBEncoder", "head": "SingletonQueryPredictor",
                       "loss": "directional_pair_context_loss",
                       "excluded": ["DirectResidualStateHead", "BlockPredictor", "block_mean_target"]},
        "baseline_routing_backbone": {k: v for k, v in baseline_routing.items() if k != "blocks"},
        "baseline_routing_predictor": baseline_predictor_routing,
        "baseline_endpoints": baseline_endpoints,
        "endpoint_semantics": ("retention = mean per-cell cosine against the frozen baseline "
                               "program projection; scale-invariant by construction. In "
                               "synthetic mode this measures representation retention, NOT "
                               "biology, because synthetic expression carries no biology."),
        "routing_outcome": final.get("gates", {}).get("routing_outcome"),
        "history": history,
        "firewall": {"expression_read": False, "dev_sealed_or_pathology": False,
                     "f1_candidate_outcome_read": False, "f1a_artifacts_modified": False,
                     "protected_program_selection": False},
    }
    document["semantic_root_sha256"] = canonical_sha(document)
    out = Path(output_root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "F1B_MINIMAL_BRIDGE_RESULT.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("synthetic", "technical-fixture", "real"), required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--canonical-root", type=Path, default=Path("D:/Jepa project"))
    p.add_argument("--worktree-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--launch-authority", type=Path, default=None)
    p.add_argument("--updates", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    frozen = Frozen() if args.updates is None else Frozen(updates=args.updates)
    document = run(args.mode, args.output_root, args.canonical_root, args.worktree_root,
                   args.launch_authority, frozen)
    print(json.dumps({"terminal": document["terminal"],
                      "routing_outcome": document["routing_outcome"],
                      "semantic_root_sha256": document["semantic_root_sha256"]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
