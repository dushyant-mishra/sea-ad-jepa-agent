"""Shared engineering core for the pre-result F1 executor preflight."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import resource
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable

import numpy as np
import torch
import torch.nn.functional as F
from scipy.sparse import csr_matrix


EVIDENCE_SEED = "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f"
CHECKPOINT_SHA = "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"
STATE_SHA = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
ENCODER_SHA = "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a"
TOKENIZER_SHA = "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4"
CONSTRUCTOR_SHA = "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa"
NAMESPACE_SEMANTIC_ROOT = "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f"
BLOCK_MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
FLOAT32_RULE = MappingProxyType({
    "machine_epsilon": float(np.finfo(np.float32).eps),
    "absolute_epsilon_multiplier": 256.0,
    "relative_epsilon_multiplier": 512.0,
    "relative_floor": float(np.finfo(np.float32).eps),
})
F1_ARCHITECTURE = MappingProxyType({
    "vocabulary_size": 41238, "width": 160, "heads": 4, "blocks": 6,
    "identity_dim": 48, "gradient_checkpointing": False, "eval": True,
})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json_sha(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_authority_file(path: Path, expected_sha256: str) -> bool:
    if not path.is_file() or sha256_file(path) != expected_sha256:
        raise RuntimeError(f"authority hash mismatch: {path}")
    return True


def validate_fixture_binding(fixture: dict) -> bool:
    if canonical_json_sha(fixture.get("selected")) != fixture.get("membership_root_sha256"):
        raise RuntimeError("fixture membership root mismatch")
    return True


def validate_semantic_root(record: dict, root_key: str) -> bool:
    body = dict(record)
    stored = body.pop(root_key, None)
    if not isinstance(stored, str) or canonical_json_sha(body) != stored:
        raise RuntimeError(f"{root_key} semantic root mismatch")
    return True


def validate_runtime_facts(facts: dict) -> bool:
    required = (
        facts.get("is_wsl") is True,
        str(facts.get("canonical_mount", "")).startswith("/mnt/d/"),
        facts.get("cuda_available") is True,
        int(facts.get("cuda_device_count", 0)) >= 1,
        facts.get("nvidia_smi_ok") is True,
        facts.get("source_hashes_match") is True,
    )
    if not all(required):
        raise RuntimeError("WSL/CUDA/runtime authority mismatch")
    return True


def validate_encoder_architecture(encoder) -> bool:
    actual = {
        "vocabulary_size": int(encoder.tokenizer.vocabulary_size),
        "width": int(encoder.tokenizer.width),
        "heads": int(encoder.blocks[0].attention.heads),
        "blocks": len(encoder.blocks),
        "identity_dim": int(encoder.tokenizer.gene_identity.embedding_dim),
        "gradient_checkpointing": bool(encoder.gradient_checkpointing),
        "eval": not bool(encoder.training),
    }
    if actual != dict(F1_ARCHITECTURE):
        raise RuntimeError(f"production architecture mismatch: {actual}")
    return True


def tensor_sha(tensor: torch.Tensor) -> str:
    array = tensor.detach().contiguous().cpu().numpy()
    h = hashlib.sha256()
    h.update(str(array.dtype).encode("ascii"))
    h.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    h.update(array.tobytes(order="C"))
    return h.hexdigest()


def meminfo() -> dict[str, int]:
    result: dict[str, int] = {}
    with Path("/proc/meminfo").open("r", encoding="ascii") as handle:
        for line in handle:
            key, rest = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree", "SwapCached"}:
                result[key] = int(rest.strip().split()[0]) * 1024
    return result


def swap_used(info: dict[str, int]) -> int:
    return info["SwapTotal"] - info["SwapFree"]


def peak_rss_bytes() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def evidence_mask(state: np.ndarray, row_locator: str, query: int, level: int) -> np.ndarray:
    if int(state[query]) != 1:
        raise RuntimeError("query is not MEASURED_SCALAR")
    eligible = np.flatnonzero(state == 1)
    eligible = eligible[eligible != query]
    ranked = sorted(
        eligible.tolist(),
        key=lambda address: (
            hashlib.sha256(f"{EVIDENCE_SEED}|{row_locator}|{query}|{address}".encode("utf-8")).digest(),
            address,
        ),
    )
    keep = len(ranked) * int(level) // 100
    result = np.zeros(len(state), dtype=np.bool_)
    result[np.asarray(ranked[:keep], dtype=np.int64)] = True
    return result


@dataclass(frozen=True)
class ReaderRow:
    canonical_cell_id: str
    row_locator: str
    operator: int
    counts_path: str
    counts_sha256: str
    row_index: int
    source_library: float


class MaterializedFixtureReader:
    """Hash-bound reader returning values/states only to the model boundary."""

    def __init__(self, canonical_root: Path, worktree_root: Path):
        self.root = canonical_root.resolve()
        frozen = worktree_root.resolve() / "docs/agent/f1_real_reader_forward_executor_preflight_20260903"
        self.fixture = json.loads((frozen / "F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json").read_text(encoding="utf-8"))
        self.plan = json.loads((frozen / "F1_PREFLIGHT_READER_PLAN_BINDING.json").read_text(encoding="utf-8"))
        validate_fixture_binding(self.fixture)
        validate_semantic_root(self.plan, "reader_plan_root_sha256")
        if self.plan["fixture_membership_root_sha256"] != self.fixture["membership_root_sha256"]:
            raise RuntimeError("reader/fixture membership mismatch")
        if self.plan["block_manifest"]["sha256"] != BLOCK_MANIFEST_SHA:
            raise RuntimeError("block manifest authority mismatch")
        self.expression_root = self.root / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
        block_manifest = self.expression_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        if sha256_file(block_manifest) != BLOCK_MANIFEST_SHA:
            raise RuntimeError("live block manifest mismatch")
        state_path = self.root / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
        validate_authority_file(state_path, STATE_SHA)
        packed = np.load(state_path, allow_pickle=False)
        self.states = {int(op): packed["states"][index].astype(np.uint8) for index, op in enumerate(packed["operator_index"].astype(int))}
        self.rows = {
            row["canonical_cell_id"]: ReaderRow(
                canonical_cell_id=row["canonical_cell_id"],
                row_locator=row["row_locator"],
                operator=int(row["operator"]),
                counts_path=row["counts_path"],
                counts_sha256=row["counts_sha256"],
                row_index=int(row["row_index_within_block"]),
                source_library=float.fromhex(row["source_library_hex"]),
            )
            for row in self.plan["reader_rows"]
        }
        if len(self.rows) != self.plan["unique_rows"]:
            raise RuntimeError("reader plan duplicate rows")

    def _load_group(self, path_key: str, requests: list[ReaderRow]) -> dict[str, np.ndarray]:
        path = self.expression_root / path_key
        expected = {row.counts_sha256 for row in requests}
        if len(expected) != 1 or sha256_file(path) != next(iter(expected)):
            raise RuntimeError("counts block hash mismatch")
        with np.load(path, allow_pickle=False) as packed:
            matrix = csr_matrix((packed["data"], packed["indices"], packed["indptr"]), shape=tuple(packed["shape"]))
        result = {}
        for row in requests:
            dense = matrix.getrow(row.row_index).toarray().ravel().astype(np.float32)
            result[row.canonical_cell_id] = np.log1p(dense * (10000.0 / row.source_library)).astype(np.float32)
        return result

    def read(self, cell_ids: Iterable[str], workers: int = 0, reverse_physical: bool = False) -> tuple[MappingProxyType, list[dict[str, object]], dict[str, float]]:
        ids = list(cell_ids)
        if len(ids) != len(set(ids)) or any(cell not in self.rows for cell in ids):
            raise RuntimeError("reader request identity mismatch")
        grouped: dict[str, list[ReaderRow]] = {}
        for cell in ids:
            row = self.rows[cell]
            grouped.setdefault(row.counts_path, []).append(row)
        keys = sorted(grouped, reverse=reverse_physical)
        start = time.perf_counter()
        loaded: dict[str, np.ndarray] = {}
        if workers <= 1:
            for key in keys:
                loaded.update(self._load_group(key, grouped[key]))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {key: pool.submit(self._load_group, key, grouped[key]) for key in keys}
                for key in keys:
                    loaded.update(futures[key].result())
        elapsed = time.perf_counter() - start
        values = np.stack([loaded[cell] for cell in ids]).astype(np.float32, copy=False)
        states = np.stack([self.states[self.rows[cell].operator] for cell in ids]).astype(np.uint8, copy=False)
        if values.shape != states.shape or values.shape[1] != 41238 or not np.isfinite(values).all():
            raise RuntimeError("reader payload geometry/numerical mismatch")
        model_input = MappingProxyType({"normalized_values": values, "observation_states": states})
        if set(model_input) != {"normalized_values", "observation_states"}:
            raise AssertionError("model input boundary changed")
        sidecar = [
            {"canonical_cell_id": cell, "row_locator": self.rows[cell].row_locator, "operator": self.rows[cell].operator}
            for cell in ids
        ]
        return model_input, sidecar, {"reader_seconds": elapsed, "physical_blocks": len(keys),
                                      "physical_read_bytes": sum((self.expression_root / key).stat().st_size for key in keys)}


def load_encoder(canonical_root: Path, device: torch.device):
    from sea_ad_jepa.v4.ipb_jepa import IPBEncoder

    checkpoint = canonical_root / "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt"
    if sha256_file(checkpoint) != CHECKPOINT_SHA:
        raise RuntimeError("checkpoint authority mismatch")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    encoder = IPBEncoder(vocabulary_size=41238, width=160, heads=4, blocks=6, gradient_checkpointing=False)
    encoder.load_state_dict(payload["online_encoder"])
    encoder.eval().to(device)
    validate_encoder_architecture(encoder)
    return encoder


def lean_query_local(
    encoder,
    normalized_values: torch.Tensor,
    physical_state: torch.Tensor,
    evidence_visible: torch.Tensor,
    query_index: torch.Tensor,
    role: str,
) -> tuple[dict[str, torch.Tensor], dict[str, float]]:
    if role not in {"teacher", "student"}:
        raise ValueError("role")
    measurement = physical_state.eq(1)
    if not torch.all(measurement.gather(1, query_index[:, None])):
        raise RuntimeError("query physical state")
    if torch.any(evidence_visible.gather(1, query_index[:, None])):
        raise RuntimeError("query scalar leakage")
    hidden = measurement & ~evidence_visible
    ids = torch.arange(normalized_values.shape[1], device=normalized_values.device).expand(len(normalized_values), -1)
    if normalized_values.is_cuda:
        torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.no_grad():
        encoded = encoder(
            gene_ids=ids,
            expression=normalized_values,
            measurement_mask=measurement,
            hidden_target_mask=hidden,
            # Reviewed F0 uses the online encoder's student view for both roles;
            # teacher changes no-grad/detach semantics only.
            view="student",
        )
    if normalized_values.is_cuda:
        torch.cuda.synchronize()
    model_seconds = time.perf_counter() - start
    start = time.perf_counter()
    rows = torch.arange(len(normalized_values), device=normalized_values.device)
    h_query = encoded.gene_states[rows, query_index]
    means = []
    counts = []
    for index in range(len(normalized_values)):
        context = torch.nonzero(evidence_visible[index], as_tuple=False).flatten()
        context = context[context != query_index[index]]
        if context.numel() == 0:
            raise RuntimeError("empty context")
        means.append(encoded.gene_states[index, context].sum(dim=0) / int(context.numel()))
        counts.append(int(context.numel()))
    mu_context = torch.stack(means)
    pre = h_query - mu_context
    contextual = F.layer_norm(pre, (pre.shape[-1],))
    direct = F.layer_norm(h_query, (h_query.shape[-1],))
    if normalized_values.is_cuda:
        torch.cuda.synchronize()
    reduction_seconds = time.perf_counter() - start
    result = {
        "h_query": h_query.detach(),
        "mu_context": mu_context.detach(),
        "pre_layer_norm": pre.detach(),
        "contextual_state": contextual.detach(),
        "direct_state": direct.detach(),
        "hidden_mask": hidden.detach(),
        "context_counts": torch.tensor(counts, dtype=torch.int64, device=normalized_values.device),
    }
    return result, {"model_forward_seconds": model_seconds, "target_context_reduction_seconds": reduction_seconds}


def comparison(left: torch.Tensor, right: torch.Tensor) -> dict[str, float | bool]:
    a = left.detach().float().cpu().numpy().astype(np.float64)
    b = right.detach().float().cpu().numpy().astype(np.float64)
    delta = np.abs(a - b)
    absolute = float(delta.max(initial=0.0))
    scale = max(1.0, float(np.abs(b).max(initial=0.0)))
    relative = float((delta / np.maximum(np.abs(b), FLOAT32_RULE["relative_floor"])).max(initial=0.0))
    atol = FLOAT32_RULE["absolute_epsilon_multiplier"] * FLOAT32_RULE["machine_epsilon"] * scale
    rtol = FLOAT32_RULE["relative_epsilon_multiplier"] * FLOAT32_RULE["machine_epsilon"]
    return {"max_abs": absolute, "max_rel": relative, "absolute_tolerance": atol, "relative_tolerance": rtol, "pass": bool(absolute <= atol or relative <= rtol)}


def forward_identity(authority: dict[str, object], record: dict[str, object], role: str, run_id: str, shard_id: str) -> str:
    body = {
        "repository_commit": authority["repository_commit"],
        "checkpoint_sha256": CHECKPOINT_SHA,
        "encoder_sha256": ENCODER_SHA,
        "encoder_executed_bytes_sha256": authority["encoder_executed_bytes_sha256"],
        "tokenizer_sha256": TOKENIZER_SHA,
        "tokenizer_executed_bytes_sha256": authority["tokenizer_executed_bytes_sha256"],
        "namespace_semantic_root": NAMESPACE_SEMANTIC_ROOT,
        "observation_state_sha256": STATE_SHA,
        "reader_split_sha256": authority["reader_split_sha256"],
        "row_lineage_sha256": authority["row_lineage_sha256"],
        "evidence_mask_sha256": authority["evidence_mask_sha256"],
        "assignment_sha256": authority["assignment_sha256"],
        "dedup_sha256": authority["dedup_sha256"],
        "matched_null_sha256": authority["matched_null_sha256"],
        "constructor_sha256": CONSTRUCTOR_SHA,
        "constructor_executed_bytes_sha256": authority["constructor_executed_bytes_sha256"],
        "query_safe_target_sha256": authority["query_safe_target_sha256"],
        "role": role,
        "recipient": record["canonical_cell_id"],
        "null_source": record.get("null_source_cell") if role == "matched_null_student" else None,
        "query": int(record["q"]),
        "evidence_level": int(record["evidence_level"]),
        "dtype": "float32",
        "autocast": False,
        "run_id": run_id,
        "logical_shard_id": shard_id,
        "physical_read_plan": "FULL104_LEVEL4_SORTED_BLOCK_V1",
    }
    return canonical_json_sha(body)


def reader_source_sha() -> str:
    return sha256_file(Path(__file__))
