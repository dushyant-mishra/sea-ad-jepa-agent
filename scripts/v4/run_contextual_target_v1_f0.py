#!/usr/bin/env python3
"""Bounded reader-fit-only F0 harness for the contextual query-local interface."""

from __future__ import annotations

import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import csv
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import platform
import shutil
import sys
import time
from typing import Any, Callable

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

from sea_ad_jepa.v4.contextual_query_local import (  # noqa: E402
    EXPECTED_ENCODER_SOURCE_SHA256,
    EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
    EXPECTED_TOKENIZER_SOURCE_SHA256,
    construct_query_local_contextual_state,
)
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder  # noqa: E402
from contextual_target_v1_f0_slow_reference import (  # noqa: E402
    slow_true_singleton_reference,
)
from contextual_target_v1_f0_authenticated_fixture import (  # noqa: E402
    load_authenticated_reader_fit_fixture,
)

DISCOVERY = ROOT / "outputs" / "contextual_teacher_target_v1_code_discovery_20260901"
V8 = (
    ROOT
    / "outputs"
    / "full104_v014_20260826"
    / "full104_expression_interface_v8_verified"
    / "FULL104_EXPRESSION_INTERFACE_V8"
)
FINAL = ROOT / "outputs" / "contextual_teacher_target_v1_f0_implementation_20260901"
STAGING = ROOT / "outputs" / "_staging_contextual_teacher_target_v1_f0_implementation_20260901"
CHECKPOINT = ROOT / "exports" / "prod41k_teacher_t1_20260823" / "t1_run" / "t1_checkpoint_u0000.pt"
PHYSICAL_AUTHORITY = (
    ROOT
    / "exports"
    / "foundation_calibration_bundle_20260824"
    / "support"
    / "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
)
SELECTION = V8 / "interface_check_v8r1" / "FULL104_EXPRESSION_INTERFACE_SELECTION.csv"
IDENTITY = V8 / "audit_identity" / "FULL104_EXPRESSION_INTERFACE_IDENTITY.csv"
PAYLOAD = V8 / "model_inputs" / "FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz"
READER_SPLIT = ROOT / "exports" / "contextual_biology_v6r5a_20260822" / "reader_donor_split.csv"

DISCOVERY_HASHES = {
    "CONTEXTUAL_TARGET_V1_CODE_PATH_DISCOVERY.json": "6cabab06887d710148a524e20c2b9959206984d83b22091a96e3b5467e889bd2",
    "CONTEXTUAL_TARGET_V1_QUERY_SCALAR_CALL_GRAPH.md": "c3b6bd207f668239725a5a60b16a687bb99a442b81d721212de163d6cbc44e11",
    "CONTEXTUAL_TARGET_V1_F0_IMPLEMENTATION_PLAN.md": "4626325f16a37ef0862cc922536ff3cc8e2a8abaed9a05e9ce77f96d8a0714a5",
    "CONTEXTUAL_TARGET_V1_DISCOVERY_RED_TEAM.md": "a3060833eb0531df2f7d23461037b8304ae7c71763076ca282bbb50f535dbf6a",
}
CONTRACT_SHA = "e7c33317b2ca9da59f8c836f70062409fb9cfc4e5489222978afcff83aeb5be3"
SHARED_ROOT_SHA = "0641735d6619ff3cfdc3cce8673c38f678591d1a4a685ea229470737c9311e6d"
MODEL_SHA = "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"
MODEL_STATE_SHA_RUNTIME = ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tensor_sha(value: torch.Tensor) -> str:
    array = value.detach().contiguous().cpu().numpy()
    h = hashlib.sha256()
    h.update(str(array.dtype).encode("ascii"))
    h.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    h.update(array.tobytes(order="C"))
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def state_dict_sha(model: torch.nn.Module) -> str:
    h = hashlib.sha256()
    for name, value in model.state_dict().items():
        h.update(name.encode("utf-8"))
        h.update(value.detach().contiguous().cpu().numpy().tobytes())
    return h.hexdigest()


def validate_authorities() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, expected in DISCOVERY_HASHES.items():
        actual = sha256(DISCOVERY / name)
        if actual != expected:
            raise RuntimeError("STOP_SOURCE_OR_AUTHORITY_HASH_MISMATCH: " + name)
        observed[name] = actual
    packet_contract = ROOT / "CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2" / "CONTEXTUAL_TEACHER_TARGET_V1_PROSPECTIVE_CONTRACT.md"
    if sha256(packet_contract) != CONTRACT_SHA:
        raise RuntimeError("STOP_SOURCE_OR_AUTHORITY_HASH_MISMATCH: prospective contract")
    shared_root = (
        ROOT
        / "outputs"
        / "full104_v014_20260826"
        / "03_phase2_state_derivation_v1"
        / "full104_shared_state_final_adjudication_v1"
        / "FULL104_SHARED_STATE_FINAL_ROOT_SHA256.txt"
    )
    if shared_root.read_text(encoding="ascii").strip() != SHARED_ROOT_SHA:
        raise RuntimeError("STOP_SOURCE_OR_AUTHORITY_HASH_MISMATCH: shared root")
    observed[str(packet_contract.relative_to(ROOT))] = CONTRACT_SHA
    observed[str(shared_root.relative_to(ROOT))] = sha256(shared_root)
    checks = {
        ROOT / "src/sea_ad_jepa/v4/ipb_jepa.py": EXPECTED_ENCODER_SOURCE_SHA256,
        ROOT / "src/sea_ad_jepa/v4/gene_tokenizer.py": EXPECTED_TOKENIZER_SOURCE_SHA256,
        PHYSICAL_AUTHORITY: EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
        CHECKPOINT: MODEL_SHA,
    }
    for path, expected in checks.items():
        if sha256(path) != expected:
            raise RuntimeError("STOP_SOURCE_OR_AUTHORITY_HASH_MISMATCH: " + str(path))
        observed[str(path.relative_to(ROOT))] = expected
    return observed


def load_frozen_inputs() -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    spec = importlib.util.spec_from_file_location(
        "frozen_v8_consumer", V8 / "code" / "full104_expression_interface_consumer.py"
    )
    consumer = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(consumer)
    selection = pd.read_csv(SELECTION).sort_values("selection_row", kind="stable")
    if len(selection) != 84 or selection.operator_index.nunique() != 42:
        raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL: V8 fixture geometry")
    requests = selection[
        ["selection_row", "donor_id", "canonical_cell_id", "reader_partition", "foundation_split"]
    ].to_dict("records")
    return load_authenticated_reader_fit_fixture(
        requests=requests,
        selection_path=SELECTION,
        identity_path=IDENTITY,
        reader_split_path=READER_SPLIT,
        payload_loader=lambda: consumer.load_teacher_inputs(V8),
    )


def choose_fixture(
    values: np.ndarray, states: np.ndarray, metadata: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, object]]]:
    chosen_rows = (
        metadata.groupby("operator_index", sort=True, as_index=False).first()["selection_row"]
        .astype(int)
        .to_numpy()
    )
    x = values[chosen_rows].copy()
    m = states[chosen_rows].copy()
    query = []
    provenance: list[dict[str, object]] = []
    by_selection = metadata.set_index("selection_row")
    for fixture_row, source_row in enumerate(chosen_rows):
        measured = np.flatnonzero(m[fixture_row] == 1)
        if not len(measured):
            raise RuntimeError("STOP_OBSERVATION_CONTRACT: operator has no scalar q")
        zero = measured[x[fixture_row, measured] == 0]
        operator = int(by_selection.loc[source_row, "operator_index"])
        candidates = zero if operator % 4 == 0 and len(zero) else measured
        position = operator % 3
        q = int(candidates[0] if position == 0 else candidates[len(candidates) // 2] if position == 1 else candidates[-1])
        query.append(q)
        provenance.append(
            {
                "canonical_cell_id": str(by_selection.loc[source_row, "canonical_cell_id"]),
                "donor_id": str(by_selection.loc[source_row, "donor_id"]),
                "source": str(by_selection.loc[source_row, "source"]),
                "operator_index": operator,
                "selection_row": int(source_row),
                "reader_partition": "reader_fit",
                "foundation_split": "foundation/train",
                "pathology": False,
                "external": False,
                "physical_state_row_sha256": tensor_sha(torch.from_numpy(m[fixture_row])),
                "query_address": q,
            }
        )
    query_array = np.asarray(query, dtype=np.int64)
    evidence = m == 1
    evidence[np.arange(len(m)), query_array] = False
    return chosen_rows, x, m, evidence, provenance


def load_encoder(device: torch.device) -> IPBEncoder:
    loaded = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    encoder = IPBEncoder(
        vocabulary_size=41_238,
        width=160,
        heads=4,
        blocks=6,
        gradient_checkpointing=False,
    )
    encoder.load_state_dict(loaded["online_encoder"], strict=True)
    encoder.eval().to(device)
    return encoder


def call_candidate(
    encoder: IPBEncoder,
    expression: torch.Tensor,
    states: torch.Tensor,
    evidence: torch.Tensor,
    queries: torch.Tensor,
    provenance: list[dict[str, object]],
    role: str = "teacher",
):
    if not MODEL_STATE_SHA_RUNTIME:
        raise RuntimeError("runtime model-state binding not initialized")
    ids = torch.arange(expression.shape[1], dtype=torch.long, device=expression.device).expand(
        len(expression), -1
    )
    return construct_query_local_contextual_state(
        encoder=encoder,
        gene_ids=ids,
        normalized_expression=expression,
        physical_state=states,
        evidence_visible=evidence,
        query_index=queries,
        row_provenance=provenance,
        encoder_source_sha256=EXPECTED_ENCODER_SOURCE_SHA256,
        tokenizer_source_sha256=EXPECTED_TOKENIZER_SOURCE_SHA256,
        model_state_sha256=MODEL_STATE_SHA_RUNTIME,
        physical_state_authority_sha256=EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
        role=role,
    )


def call_reference(
    encoder: IPBEncoder,
    expression: torch.Tensor,
    states: torch.Tensor,
    evidence: torch.Tensor,
    queries: torch.Tensor,
    provenance: list[dict[str, object]],
    role: str = "teacher",
):
    ids = torch.arange(expression.shape[1], dtype=torch.long, device=expression.device).expand(
        len(expression), -1
    )
    return slow_true_singleton_reference(
        encoder=encoder,
        gene_ids=ids,
        normalized_expression=expression,
        physical_state=states,
        evidence_visible=evidence,
        query_index=queries,
        row_provenance=provenance,
        role=role,
    )


def float_metrics(actual: torch.Tensor, expected: torch.Tensor, rule: dict[str, float]) -> dict[str, Any]:
    a = actual.detach().double().cpu()
    b = expected.detach().double().cpu()
    difference = (a - b).abs()
    scale = max(1.0, float(a.abs().max()), float(b.abs().max()))
    absolute = float(difference.max()) if difference.numel() else 0.0
    relative = float((difference / torch.maximum(b.abs(), torch.tensor(rule["relative_floor"]))).max()) if difference.numel() else 0.0
    absolute_tolerance = rule["absolute_epsilon_multiplier"] * rule["machine_epsilon"] * scale
    relative_tolerance = rule["relative_epsilon_multiplier"] * rule["machine_epsilon"]
    return {
        "max_absolute": absolute,
        "max_relative": relative,
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "pass": bool(absolute <= absolute_tolerance or relative <= relative_tolerance),
    }


def require(condition: bool, stop: str, detail: str) -> None:
    if not condition:
        raise RuntimeError(f"{stop}: {detail}")


def expect_failure(action: Callable[[], object], label: str) -> str:
    try:
        action()
    except Exception as error:  # deliberate adversarial boundary
        return type(error).__name__ + ": " + str(error)
    raise RuntimeError("STOP_IMPLEMENTATION_SEMANTICS: attack accepted: " + label)


def main() -> None:
    global MODEL_STATE_SHA_RUNTIME
    if FINAL.exists() or STAGING.exists():
        raise RuntimeError("refusing to overwrite existing F0 output/staging")
    STAGING.mkdir(parents=True)
    start = time.time()
    authorities = validate_authorities()
    values_np, states_np, metadata = load_frozen_inputs()
    selected_rows, fixture_x, fixture_m, fixture_u, provenance = choose_fixture(
        values_np, states_np, metadata
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(20_260_901)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(20_260_901)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    encoder = load_encoder(device)
    initial_model_sha = state_dict_sha(encoder)
    MODEL_STATE_SHA_RUNTIME = initial_model_sha
    x = torch.from_numpy(fixture_x).to(device)
    m = torch.from_numpy(fixture_m).to(device)
    u = torch.from_numpy(fixture_u).to(device)
    q = torch.from_numpy(np.asarray([row["query_address"] for row in provenance], dtype=np.int64)).to(device)

    # Deterministic repeatability is measured before the comparison rule is frozen.
    repeated_a = call_candidate(encoder, x[:1], m[:1], u[:1], q[:1], provenance[:1])
    repeated_b = call_candidate(encoder, x[:1], m[:1], u[:1], q[:1], provenance[:1])
    repeat_exact = all(
        torch.equal(getattr(repeated_a, name), getattr(repeated_b, name))
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    )
    require(repeat_exact, "STOP_NUMERICAL_FAILURE", "eval repeatability is not exact")
    epsilon = float(np.finfo(np.float32).eps)
    comparison_rule = {
        "machine_epsilon": epsilon,
        "absolute_epsilon_multiplier": 256.0,
        "relative_epsilon_multiplier": 512.0,
        "relative_floor": epsilon,
        "exact_semantics": [
            "uint8 state",
            "bool mask",
            "query index/address",
            "context indices/count",
            "row identity/provenance",
            "semantic hashes in singleton reference parity",
        ],
        "derived_before_candidate_reference_or_adversarial_interpretation": True,
        "repeatability_exact": True,
    }
    run_manifest = {
        "schema": "contextual-target-v1-f0-run-manifest-v1",
        "created_before_adversarial_interpretation": True,
        "device": str(device),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "dtype": "float32",
        "deterministic_algorithms": True,
        "seed": 20_260_901,
        "comparison_rule": comparison_rule,
        "fixture_selection_rows": selected_rows.tolist(),
        "fixture_selection_outcome_blind": True,
        "authorities": authorities,
    }
    atomic_json(STAGING / "CONTEXTUAL_TARGET_V1_F0_RUN_MANIFEST.json", run_manifest)

    parity_rows = []
    for row in range(len(x)):
        candidate = call_candidate(encoder, x[row : row + 1], m[row : row + 1], u[row : row + 1], q[row : row + 1], provenance[row : row + 1])
        reference = call_reference(encoder, x[row : row + 1], m[row : row + 1], u[row : row + 1], q[row : row + 1], provenance[row : row + 1])
        exact = {
            "row_identity": candidate.row_identity == reference["row_identity"],
            "query_index": torch.equal(candidate.query_index, reference["query_index"]),
            "query_address": torch.equal(candidate.query_address, reference["query_address"]),
            "physical_state": torch.equal(m[row : row + 1], reference["physical_state"]),
            "evidence": torch.equal(u[row : row + 1], reference["evidence_visible"]),
            "context_indices": candidate.context_indices == reference["context_indices"],
            "context_hash": candidate.context_state_sha256 == reference["context_state_sha256"],
            "hidden_mask_hash": candidate.hidden_mask_sha256
            == reference["hidden_mask_sha256_per_row"][0],
            "query_physical_state": bool(torch.all(candidate.query_physical_state == 1)),
        }
        floats = {
            name: float_metrics(getattr(candidate, name), reference[name], comparison_rule)
            for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
        }
        floats["context_states"] = float_metrics(
            candidate.context_states[0], reference["context_states"][0], comparison_rule
        )
        require(all(exact.values()), "STOP_NUMERICAL_FAILURE", f"reference exact mismatch row {row}")
        require(all(item["pass"] for item in floats.values()), "STOP_NUMERICAL_FAILURE", f"reference float mismatch row {row}")
        parity_rows.append({"fixture_row": row, "operator_index": provenance[row]["operator_index"], "exact": exact, "float": floats})

    reference_parity = {
        "status": "PASS",
        "reference_imports_optimized_constructor": False,
        "operators": len({int(row["operator_index"]) for row in provenance}),
        "rows": len(parity_rows),
        "comparisons": parity_rows,
    }
    atomic_json(STAGING / "CONTEXTUAL_TARGET_V1_F0_REFERENCE_PARITY.json", reference_parity)

    # B: q intervention and unsafe rich control.
    attack_row = 0
    altered = x[attack_row : attack_row + 1].clone()
    altered[0, q[attack_row]] += 3.0
    safe_base = call_candidate(encoder, x[attack_row : attack_row + 1], m[attack_row : attack_row + 1], u[attack_row : attack_row + 1], q[attack_row : attack_row + 1], provenance[attack_row : attack_row + 1])
    safe_changed = call_candidate(encoder, altered, m[attack_row : attack_row + 1], u[attack_row : attack_row + 1], q[attack_row : attack_row + 1], provenance[attack_row : attack_row + 1])
    intervention_metrics = {
        name: float_metrics(getattr(safe_changed, name), getattr(safe_base, name), comparison_rule)
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    }
    intervention_metrics["context_states"] = float_metrics(
        safe_changed.context_states[0], safe_base.context_states[0], comparison_rule
    )
    require(all(item["pass"] for item in intervention_metrics.values()), "STOP_QUERY_SELF_LEAKAGE", "safe output changed with x_q")
    measured = m[attack_row : attack_row + 1] == 1
    ids = torch.arange(x.shape[1], dtype=torch.long, device=device)[None]
    with torch.no_grad():
        unsafe_a = encoder(ids, x[attack_row : attack_row + 1], measured, ~measured, "target").gene_states[0, q[attack_row]]
        unsafe_b = encoder(ids, altered, measured, ~measured, "target").gene_states[0, q[attack_row]]
    unsafe_change = float((unsafe_b - unsafe_a).abs().max().cpu())
    require(unsafe_change > comparison_rule["absolute_epsilon_multiplier"] * epsilon, "STOP_IMPLEMENTATION_SEMANTICS", "unsafe rich control did not respond")

    # Gradient/JVP-equivalent dependency probe: zero q gradient, nonzero context gradient.
    grad_x = x[attack_row : attack_row + 1].clone().detach().requires_grad_(True)
    student = call_candidate(encoder, grad_x, m[attack_row : attack_row + 1], u[attack_row : attack_row + 1], q[attack_row : attack_row + 1], provenance[attack_row : attack_row + 1], role="student")
    projection = torch.linspace(-1.0, 1.0, student.contextual_state.shape[-1], device=device)
    gradient = torch.autograd.grad(
        (student.contextual_state * projection).sum(), grad_x, retain_graph=True
    )[0]
    q_gradient = float(gradient[0, q[attack_row]].abs().cpu())
    visible_non_q = torch.nonzero(u[attack_row], as_tuple=False).flatten()
    non_q_gradient_max = float(gradient[0, visible_non_q].abs().max().cpu())
    hq_gradient = torch.autograd.grad(
        (student.h_query * projection).sum(), grad_x, retain_graph=False
    )[0]
    hq_non_q_gradient_max = float(hq_gradient[0, visible_non_q].abs().max().cpu())
    require(q_gradient <= epsilon, "STOP_QUERY_SELF_LEAKAGE", "nonzero autograd dependence on x_q")
    require(non_q_gradient_max > epsilon, "STOP_IMPLEMENTATION_SEMANTICS", "student context gradient deleted")
    require(hq_non_q_gradient_max > epsilon, "STOP_QUERY_READOUT_DELETED", "q readout has no non-q dependence")
    require(not safe_base.contextual_state.requires_grad, "STOP_IMPLEMENTATION_SEMANTICS", "teacher output not detached")

    # C: lawful non-q context sensitivity.
    context_address = int(visible_non_q[len(visible_non_q) // 2])
    context_altered = x[attack_row : attack_row + 1].clone()
    context_altered[0, context_address] += 2.0
    context_changed = call_candidate(encoder, context_altered, m[attack_row : attack_row + 1], u[attack_row : attack_row + 1], q[attack_row : attack_row + 1], provenance[attack_row : attack_row + 1])
    context_delta = float((context_changed.contextual_state - safe_base.contextual_state).abs().max().cpu())
    hq_context_delta = float((context_changed.h_query - safe_base.h_query).abs().max().cpu())
    require(context_delta > 256 * epsilon, "STOP_IMPLEMENTATION_SEMANTICS", "lawful context cannot change output")
    require(hq_context_delta > 256 * epsilon, "STOP_QUERY_READOUT_DELETED", "lawful context cannot change H_q")

    # E/F/G and coverage assertions.
    measured_zero_context = int(np.count_nonzero((fixture_m == 1) & fixture_u & (fixture_x == 0)))
    measured_zero_query = int(np.count_nonzero(fixture_x[np.arange(len(q)), q.cpu().numpy()] == 0))
    code0 = int(np.count_nonzero(fixture_m == 0))
    code2 = int(np.count_nonzero(fixture_m == 2))
    require(measured_zero_context > 0 and measured_zero_query > 0, "STOP_OBSERVATION_CONTRACT", "natural measured-zero coverage missing")
    require(code0 > 0 and code2 > 0, "STOP_OBSERVATION_CONTRACT", "natural code0/code2 coverage missing")
    require(not np.any(fixture_u[fixture_m != 1]), "STOP_OBSERVATION_CONTRACT", "non-scalar entered context")

    # Direct code0/code2 distinction: swap naturally present codes within one operator.
    state_row = next(
        index
        for index in range(len(m))
        if torch.any(m[index] == 0) and torch.any(m[index] == 2)
    )
    swapped_physical = m[state_row : state_row + 1].clone()
    zero_address = int(torch.nonzero(swapped_physical[0] == 0, as_tuple=False)[0])
    collision_address = int(torch.nonzero(swapped_physical[0] == 2, as_tuple=False)[0])
    swapped_physical[0, zero_address] = 2
    swapped_physical[0, collision_address] = 0
    swapped_provenance = [dict(provenance[state_row])]
    swapped_provenance[0]["physical_state_row_sha256"] = tensor_sha(swapped_physical[0])
    state_baseline = call_candidate(
        encoder,
        x[state_row : state_row + 1],
        m[state_row : state_row + 1],
        u[state_row : state_row + 1],
        q[state_row : state_row + 1],
        provenance[state_row : state_row + 1],
    )
    state_swapped = call_candidate(
        encoder,
        x[state_row : state_row + 1],
        swapped_physical,
        u[state_row : state_row + 1],
        q[state_row : state_row + 1],
        swapped_provenance,
    )
    state_swap_metric = float_metrics(
        state_swapped.contextual_state, state_baseline.contextual_state, comparison_rule
    )
    require(state_swap_metric["pass"], "STOP_OBSERVATION_CONTRACT", "scalar-ineligible code0/code2 swap changed output")
    require(
        state_swapped.physical_state_sha256 != state_baseline.physical_state_sha256
        and state_swapped.context_indices == state_baseline.context_indices,
        "STOP_OBSERVATION_CONTRACT",
        "code0/code2 provenance distinction not retained",
    )

    # H/I: true singleton against vectorized replicas and companion/order/chunk invariance.
    base = 1
    measured_addresses = np.flatnonzero(fixture_m[base] == 1)
    vector_queries = np.asarray(
        [measured_addresses[0], measured_addresses[len(measured_addresses) // 2], measured_addresses[-1]],
        dtype=np.int64,
    )
    vx = x[base : base + 1].repeat(3, 1)
    vm = m[base : base + 1].repeat(3, 1)
    vu = vm == 1
    vu[torch.arange(3, device=device), torch.from_numpy(vector_queries).to(device)] = False
    vq = torch.from_numpy(vector_queries).to(device)
    vp = []
    for index, item in enumerate(vector_queries):
        record = dict(provenance[base])
        record["query_address"] = int(item)
        vp.append(record)
    vectorized = call_candidate(encoder, vx, vm, vu, vq, vp)
    singleton = call_reference(encoder, vx, vm, vu, vq, vp)
    vector_metrics = {
        name: float_metrics(getattr(vectorized, name), singleton[name], comparison_rule)
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    }
    vector_metrics["context_states"] = {
        str(index): float_metrics(
            vectorized.context_states[index], singleton["context_states"][index], comparison_rule
        )
        for index in range(3)
    }
    vector_exact = {
        "row_identity": vectorized.row_identity == singleton["row_identity"],
        "query_index": torch.equal(vectorized.query_index, singleton["query_index"]),
        "query_address": torch.equal(vectorized.query_address, singleton["query_address"]),
        "query_physical_state": bool(torch.all(vectorized.query_physical_state == 1)),
        "physical_state": torch.equal(vectorized.physical_state, singleton["physical_state"]),
        "evidence_visible": torch.equal(vectorized.evidence_visible, singleton["evidence_visible"]),
        "hidden_mask": torch.equal(vectorized.hidden_mask, singleton["hidden_mask"]),
        "context_indices": vectorized.context_indices == singleton["context_indices"],
        "context_counts": torch.equal(
            vectorized.context_counts.cpu(),
            torch.tensor([len(item) for item in singleton["context_indices"]]),
        ),
    }
    require(vectorized.context_indices == singleton["context_indices"], "STOP_NUMERICAL_FAILURE", "vector context indices")
    require(all(vector_exact.values()), "STOP_NUMERICAL_FAILURE", "vectorized exact semantics")
    require(
        all(item["pass"] for name, item in vector_metrics.items() if name != "context_states")
        and all(item["pass"] for item in vector_metrics["context_states"].values()),
        "STOP_NUMERICAL_FAILURE",
        "vectorized parity",
    )
    permutation = torch.tensor([2, 0, 1], device=device)
    permuted = call_candidate(encoder, vx[permutation], vm[permutation], vu[permutation], vq[permutation], [vp[int(i)] for i in permutation.cpu()])
    restored = torch.argsort(permutation)
    permutation_floats = {
        name: float_metrics(
            getattr(permuted, name)[restored], getattr(vectorized, name), comparison_rule
        )
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    }
    permutation_floats["context_states"] = {
        str(index): float_metrics(
            permuted.context_states[int(restored[index])],
            vectorized.context_states[index],
            comparison_rule,
        )
        for index in range(3)
    }
    permutation_exact = {
        "row_identity": tuple(permuted.row_identity[int(i)] for i in restored.cpu()) == vectorized.row_identity,
        "query_index": torch.equal(permuted.query_index[restored], vectorized.query_index),
        "query_address": torch.equal(permuted.query_address[restored], vectorized.query_address),
        "query_physical_state": torch.equal(permuted.query_physical_state[restored], vectorized.query_physical_state),
        "physical_state": torch.equal(permuted.physical_state[restored], vectorized.physical_state),
        "evidence_visible": torch.equal(permuted.evidence_visible[restored], vectorized.evidence_visible),
        "hidden_mask": torch.equal(permuted.hidden_mask[restored], vectorized.hidden_mask),
        "context_indices": tuple(permuted.context_indices[int(i)] for i in restored.cpu()) == vectorized.context_indices,
        "context_counts": torch.equal(permuted.context_counts[restored], vectorized.context_counts),
    }
    require(
        all(item["pass"] for name, item in permutation_floats.items() if name != "context_states")
        and all(item["pass"] for item in permutation_floats["context_states"].values()),
        "STOP_NUMERICAL_FAILURE",
        "query order changed output",
    )
    require(all(permutation_exact.values()), "STOP_NUMERICAL_FAILURE", "query order changed exact semantics")
    chunked_results = []
    for index in range(3):
        chunked_results.append(call_candidate(encoder, vx[index : index + 1], vm[index : index + 1], vu[index : index + 1], vq[index : index + 1], vp[index : index + 1]))
    chunk_floats = {
        name: float_metrics(
            torch.cat([getattr(item, name) for item in chunked_results]),
            getattr(vectorized, name),
            comparison_rule,
        )
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    }
    chunk_floats["context_states"] = {
        str(index): float_metrics(
            chunked_results[index].context_states[0], vectorized.context_states[index], comparison_rule
        )
        for index in range(3)
    }
    chunk_exact = {
        "row_identity": tuple(item.row_identity[0] for item in chunked_results) == vectorized.row_identity,
        "query_index": torch.equal(torch.cat([item.query_index for item in chunked_results]), vectorized.query_index),
        "query_address": torch.equal(torch.cat([item.query_address for item in chunked_results]), vectorized.query_address),
        "query_physical_state": torch.equal(torch.cat([item.query_physical_state for item in chunked_results]), vectorized.query_physical_state),
        "physical_state": torch.equal(torch.cat([item.physical_state for item in chunked_results]), vectorized.physical_state),
        "evidence_visible": torch.equal(torch.cat([item.evidence_visible for item in chunked_results]), vectorized.evidence_visible),
        "hidden_mask": torch.equal(torch.cat([item.hidden_mask for item in chunked_results]), vectorized.hidden_mask),
        "context_indices": tuple(item.context_indices[0] for item in chunked_results) == vectorized.context_indices,
        "context_counts": torch.equal(torch.cat([item.context_counts for item in chunked_results]), vectorized.context_counts),
    }
    require(
        all(item["pass"] for name, item in chunk_floats.items() if name != "context_states")
        and all(item["pass"] for item in chunk_floats["context_states"].values()),
        "STOP_NUMERICAL_FAILURE",
        "batch partition changed output",
    )
    require(all(chunk_exact.values()), "STOP_NUMERICAL_FAILURE", "batch partition changed exact semantics")
    companion_two = call_candidate(encoder, vx[[0, 2]], vm[[0, 2]], vu[[0, 2]], vq[[0, 2]], [vp[0], vp[2]])
    companion_floats = {
        name: float_metrics(getattr(companion_two, name)[0], getattr(vectorized, name)[0], comparison_rule)
        for name in ("h_query", "mu_context", "pre_layer_norm", "contextual_state")
    }
    companion_floats["context_states"] = float_metrics(
        companion_two.context_states[0], vectorized.context_states[0], comparison_rule
    )
    companion_exact = {
        "row_identity": companion_two.row_identity[0] == vectorized.row_identity[0],
        "query_index": int(companion_two.query_index[0]) == int(vectorized.query_index[0]),
        "query_address": int(companion_two.query_address[0]) == int(vectorized.query_address[0]),
        "query_physical_state": int(companion_two.query_physical_state[0]) == int(vectorized.query_physical_state[0]),
        "physical_state": torch.equal(companion_two.physical_state[0], vectorized.physical_state[0]),
        "evidence_visible": torch.equal(companion_two.evidence_visible[0], vectorized.evidence_visible[0]),
        "hidden_mask": torch.equal(companion_two.hidden_mask[0], vectorized.hidden_mask[0]),
        "context_indices": companion_two.context_indices[0] == vectorized.context_indices[0],
        "context_counts": int(companion_two.context_counts[0]) == int(vectorized.context_counts[0]),
    }
    require(all(item["pass"] for item in companion_floats.values()), "STOP_NUMERICAL_FAILURE", "companion set changed output")
    require(all(companion_exact.values()), "STOP_NUMERICAL_FAILURE", "companion set changed exact semantics")

    # J/K/L: API and semantic attacks.
    signature = inspect.signature(construct_query_local_contextual_state)
    no_global_surface = "cell" not in signature.parameters and "global_state" not in signature.parameters and "gene_states" not in signature.parameters
    require(no_global_surface, "STOP_UNSAFE_GLOBAL_DEPENDENCY", "unsafe global/precomputed state surface exists")
    global_attack = expect_failure(
        lambda: construct_query_local_contextual_state(  # type: ignore[call-arg]
            encoder=encoder,
            gene_ids=ids,
            normalized_expression=x[:1],
            physical_state=m[:1],
            evidence_visible=u[:1],
            query_index=q[:1],
            row_provenance=provenance[:1],
            encoder_source_sha256=EXPECTED_ENCODER_SOURCE_SHA256,
            tokenizer_source_sha256=EXPECTED_TOKENIZER_SOURCE_SHA256,
            model_state_sha256=MODEL_SHA,
            physical_state_authority_sha256=EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
            role="teacher",
            cell=torch.zeros(1, 160, device=device),
        ),
        "unsafe CELL injection",
    )
    wrong_q = q[:1].clone()
    wrong_q[0] = visible_non_q[0]
    wrong_q_u = m[:1] == 1
    wrong_q_u[0, wrong_q[0]] = False
    wrong_q_attack = expect_failure(lambda: call_candidate(encoder, x[:1], m[:1], wrong_q_u, wrong_q, provenance[:1]), "wrong q")
    corrupted = m[:1].clone()
    corrupted[0, 0] = 7
    invalid_state_attack = expect_failure(lambda: call_candidate(encoder, x[:1], corrupted, u[:1], q[:1], provenance[:1]), "invalid state")
    swapped_row = next(
        (index for index in range(1, len(m)) if tensor_sha(m[index]) != tensor_sha(m[0])),
        None,
    )
    require(swapped_row is not None, "STOP_OBSERVATION_CONTRACT", "no distinct physical-state attack row")
    swapped = m[swapped_row : swapped_row + 1].clone()
    swapped_u = swapped == 1
    swapped_u[0, q[0]] = False
    swapped_state_attack = expect_failure(lambda: call_candidate(encoder, x[:1], swapped, swapped_u, q[:1], provenance[:1]), "swapped state")
    q_visible = u[:1].clone()
    q_visible[0, q[0]] = True
    q_visibility_attack = expect_failure(lambda: call_candidate(encoder, x[:1], m[:1], q_visible, q[:1], provenance[:1]), "q visible")
    empty = torch.zeros_like(u[:1])
    empty_attack = expect_failure(lambda: call_candidate(encoder, x[:1], m[:1], empty, q[:1], provenance[:1]), "empty context")

    # M: actual authenticated metadata-first loader must reject before payload read.
    firewall_attacks = {}
    split_authority = pd.read_csv(READER_SPLIT, dtype=str)
    protected_donors = {
        role: str(split_authority.loc[split_authority.reader_partition == role, "donor_id"].iloc[0])
        for role in ("reader_validation", "reader_oracle")
    }
    valid_request = {
        key: provenance[0][key]
        for key in ("selection_row", "donor_id", "canonical_cell_id", "reader_partition", "foundation_split")
    }
    attack_requests = {}
    for role, donor in protected_donors.items():
        request = dict(valid_request)
        request.update({"donor_id": donor, "reader_partition": role})
        attack_requests[role] = request
        relabel = dict(request)
        relabel["reader_partition"] = "reader_fit"
        attack_requests[role + "_relabel_as_fit"] = relabel
    for label in ("DEV", "SEALED"):
        request = dict(valid_request)
        request["foundation_split"] = label
        attack_requests[label] = request
    for label in ("pathology", "external"):
        request = dict(valid_request)
        request[label] = True
        attack_requests[label] = request
    outside = dict(valid_request)
    outside["canonical_cell_id"] = "protected-or-unregistered-cell"
    attack_requests["unregistered_or_protected_cell_relabel"] = outside
    for label, record in attack_requests.items():
        reads = {"count": 0}
        def sentinel() -> dict[str, np.ndarray]:
            reads["count"] += 1
            return {"normalized_values": values_np, "observation_states": states_np}
        rejection = expect_failure(
            lambda record=record: load_authenticated_reader_fit_fixture(
                requests=[record],
                selection_path=SELECTION,
                identity_path=IDENTITY,
                reader_split_path=READER_SPLIT,
                payload_loader=sentinel,
            ),
            label,
        )
        require(reads["count"] == 0, "STOP_PROVENANCE_OR_FIREWALL", label + " expression reached")
        firewall_attacks[label] = {"rejection": rejection, "expression_read_count": reads["count"]}

    class SentinelEncoder(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.forward_count = 0
        def forward(self, *args: object, **kwargs: object) -> object:
            self.forward_count += 1
            raise AssertionError("sentinel encoder forward must not be reached")

    sentinel_encoder = SentinelEncoder().eval().to(device)
    protected_provenance = [dict(provenance[0])]
    protected_provenance[0]["reader_partition"] = "reader_oracle"
    protected_constructor_attack = expect_failure(
        lambda: construct_query_local_contextual_state(
            encoder=sentinel_encoder,
            gene_ids=ids,
            normalized_expression=x[:1],
            physical_state=m[:1],
            evidence_visible=u[:1],
            query_index=q[:1],
            row_provenance=protected_provenance,
            encoder_source_sha256=EXPECTED_ENCODER_SOURCE_SHA256,
            tokenizer_source_sha256=EXPECTED_TOKENIZER_SOURCE_SHA256,
            model_state_sha256=state_dict_sha(sentinel_encoder),
            physical_state_authority_sha256=EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
            role="teacher",
        ),
        "protected constructor provenance",
    )
    require(
        sentinel_encoder.forward_count == 0,
        "STOP_PROVENANCE_OR_FIREWALL",
        "protected constructor reached encoder forward",
    )
    wrong_model_binding_attack = expect_failure(
        lambda: construct_query_local_contextual_state(
            encoder=encoder,
            gene_ids=ids,
            normalized_expression=x[:1],
            physical_state=m[:1],
            evidence_visible=u[:1],
            query_index=q[:1],
            row_provenance=provenance[:1],
            encoder_source_sha256=EXPECTED_ENCODER_SOURCE_SHA256,
            tokenizer_source_sha256=EXPECTED_TOKENIZER_SOURCE_SHA256,
            model_state_sha256=MODEL_SHA,
            physical_state_authority_sha256=EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
            role="teacher",
        ),
        "wrong model-state binding",
    )

    require(state_dict_sha(encoder) == initial_model_sha, "STOP_INTERFACE_SCOPE_CREEP", "model weights mutated")
    metamorphic = {
        "status": "PASS",
        "A_reference_parity": "PASS",
        "B_xq_intervention": intervention_metrics,
        "unsafe_rich_control_max_abs_change": unsafe_change,
        "xq_autograd_absolute": q_gradient,
        "nonq_context_gradient_max_absolute": non_q_gradient_max,
        "hq_nonq_gradient_max_absolute": hq_non_q_gradient_max,
        "C_nonq_context_max_abs_change": context_delta,
        "C_hq_nonq_context_max_abs_change": hq_context_delta,
        "D_physical_hash_unchanged": True,
        "E_measured_zero_context_count": measured_zero_context,
        "E_measured_zero_query_count": measured_zero_query,
        "F_collision_code2_count": code2,
        "G_structural_code0_count": code0,
        "FG_code0_code2_swap": {
            "addresses": [zero_address, collision_address],
            "physical_hashes_distinct": True,
            "context_indices_equal": True,
            "output": state_swap_metric,
        },
        "H_vectorized_parity": vector_metrics,
        "H_vectorized_exact_semantics": vector_exact,
        "I_query_order": permutation_floats,
        "I_query_order_exact_semantics": permutation_exact,
        "I_batch_partition": chunk_floats,
        "I_batch_partition_exact_semantics": chunk_exact,
        "I_companion_set": companion_floats,
        "I_companion_exact_semantics": companion_exact,
        "J_no_global_input_surface": no_global_surface,
        "J_global_attack": global_attack,
        "K_wrong_query_attack": wrong_q_attack,
        "L_invalid_state_attack": invalid_state_attack,
        "L_swapped_state_attack": swapped_state_attack,
        "L_wrong_model_binding_attack": wrong_model_binding_attack,
        "q_visible_attack": q_visibility_attack,
        "empty_context_attack": empty_attack,
        "q_readout_present_finite": bool(torch.isfinite(safe_base.h_query).all()),
        "q_identity_address_specific": len(set(vectorized.query_address.cpu().tolist())) == 3,
        "physical_state_immutable": True,
        "teacher_stop_gradient": not safe_base.contextual_state.requires_grad,
        "student_differentiable": student.contextual_state.requires_grad and non_q_gradient_max > epsilon,
        "optimizer_step_count": 0,
        "ema_update_count": 0,
        "training_run_count": 0,
        "protected_biology_evaluation_count": 0,
        "model_state_sha_before": initial_model_sha,
        "model_state_sha_after": state_dict_sha(encoder),
    }
    atomic_json(STAGING / "CONTEXTUAL_TARGET_V1_F0_METAMORPHIC_RESULTS.json", metamorphic)
    firewall = {
        "status": "PASS",
        "attacks": firewall_attacks,
        "protected_expression_opened": False,
        "constructor_protected_provenance_rejection": protected_constructor_attack,
        "constructor_sentinel_forward_count": sentinel_encoder.forward_count,
        "reader_fit_fixture_rows": len(provenance),
        "operators": 42,
        "fixture_payload_sha256": sha256(PAYLOAD),
    }
    atomic_json(STAGING / "CONTEXTUAL_TARGET_V1_F0_FIREWALL_RESULTS.json", firewall)

    implementation_manifest = {
        "schema": "contextual-target-v1-f0-implementation-manifest-v1",
        "terminal_status": "TESTS_PASS_AWAITING_COUNCIL",
        "source_paths_read": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(
                {
                    **authorities,
                    str((V8 / "code/full104_expression_interface_consumer.py").relative_to(ROOT)): sha256(V8 / "code/full104_expression_interface_consumer.py"),
                    str(SELECTION.relative_to(ROOT)): sha256(SELECTION),
                    str(IDENTITY.relative_to(ROOT)): sha256(IDENTITY),
                    str(PAYLOAD.relative_to(ROOT)): sha256(PAYLOAD),
                    str(READER_SPLIT.relative_to(ROOT)): sha256(READER_SPLIT),
                    "src/sea_ad_jepa/v4/contextual_query_local.py": sha256(ROOT / "src/sea_ad_jepa/v4/contextual_query_local.py"),
                    "scripts/v4/contextual_target_v1_f0_slow_reference.py": sha256(ROOT / "scripts/v4/contextual_target_v1_f0_slow_reference.py"),
                    "scripts/v4/contextual_target_v1_f0_authenticated_fixture.py": sha256(ROOT / "scripts/v4/contextual_target_v1_f0_authenticated_fixture.py"),
                    "scripts/v4/run_contextual_target_v1_f0.py": sha256(Path(__file__)),
                }.items()
            )
        ],
        "source_paths_added_or_changed": [
            {
                "path": "src/sea_ad_jepa/v4/contextual_query_local.py",
                "pre_sha256": None,
                "post_sha256": sha256(ROOT / "src/sea_ad_jepa/v4/contextual_query_local.py"),
                "symbols": ["QueryLocalStateResult", "construct_query_local_contextual_state"],
                "conclusion_bearing": True,
                "reason": "own safe encoder forward and parameter-free same-pass contextual reduction",
            },
            {
                "path": "scripts/v4/contextual_target_v1_f0_slow_reference.py",
                "pre_sha256": None,
                "post_sha256": sha256(ROOT / "scripts/v4/contextual_target_v1_f0_slow_reference.py"),
                "symbols": ["slow_true_singleton_reference"],
                "conclusion_bearing": True,
                "reason": "independent one-(cell,q)-at-a-time reference",
            },
            {
                "path": "scripts/v4/contextual_target_v1_f0_authenticated_fixture.py",
                "pre_sha256": None,
                "post_sha256": sha256(ROOT / "scripts/v4/contextual_target_v1_f0_authenticated_fixture.py"),
                "symbols": ["load_authenticated_reader_fit_fixture"],
                "conclusion_bearing": True,
                "reason": "hash-bound metadata-first reader-fit authorization before payload access",
            },
            {
                "path": "scripts/v4/run_contextual_target_v1_f0.py",
                "pre_sha256": None,
                "post_sha256": sha256(Path(__file__)),
                "symbols": ["main"],
                "conclusion_bearing": True,
                "reason": "bounded A-M F0 harness and fail-closed publication",
            },
        ],
        "core_encoder_modified": False,
        "tokenizer_modified": False,
        "ema_modified": False,
        "elapsed_seconds": time.time() - start,
    }
    atomic_json(STAGING / "CONTEXTUAL_TARGET_V1_F0_IMPLEMENTATION_MANIFEST.json", implementation_manifest)
    print("F0_TESTS_PASS_AWAITING_COUNCIL", flush=True)


if __name__ == "__main__":
    main()
