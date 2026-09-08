"""Parameter-free, provenance-bound query-local contextual state construction.

F0 scope only.  This module owns the encoder call so callers cannot supply
precomputed gene states or CELL/global tensors.
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import torch
import torch.nn.functional as F


STRUCTURALLY_UNMEASURED = 0
MEASURED_SCALAR = 1
MEASURED_COLLISION_UNRESOLVED = 2
ALLOWED_PHYSICAL_STATES = frozenset(
    {STRUCTURALLY_UNMEASURED, MEASURED_SCALAR, MEASURED_COLLISION_UNRESOLVED}
)

EXPECTED_ENCODER_SOURCE_SHA256 = (
    "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a"
)
EXPECTED_TOKENIZER_SOURCE_SHA256 = (
    "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4"
)
EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256 = (
    "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
)


def _tensor_sha256(value: torch.Tensor) -> str:
    array = value.detach().contiguous().cpu().numpy()
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _validate_sha(name: str, value: str, expected: str | None = None) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a full SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{name} must be hexadecimal") from error
    if expected is not None and value.lower() != expected:
        raise ValueError(f"{name} authority mismatch")


def _module_state_sha256(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in module.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().contiguous().cpu().numpy().tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class QueryLocalStateResult:
    row_identity: tuple[str, ...]
    query_index: torch.Tensor
    query_address: torch.Tensor
    query_physical_state: torch.Tensor
    physical_state: torch.Tensor
    evidence_visible: torch.Tensor
    hidden_mask: torch.Tensor
    physical_state_sha256: str
    evidence_sha256: str
    hidden_mask_sha256: str
    context_indices: tuple[tuple[int, ...], ...]
    context_counts: torch.Tensor
    context_state_sha256: tuple[str, ...]
    context_states: tuple[torch.Tensor, ...]
    h_query: torch.Tensor
    mu_context: torch.Tensor
    pre_layer_norm: torch.Tensor
    contextual_state: torch.Tensor
    encoder_source_sha256: str
    tokenizer_source_sha256: str
    model_state_sha256: str
    physical_state_authority_sha256: str
    role: str


def construct_query_local_contextual_state(
    *,
    encoder: torch.nn.Module,
    gene_ids: torch.Tensor,
    normalized_expression: torch.Tensor,
    physical_state: torch.Tensor,
    evidence_visible: torch.Tensor,
    query_index: torch.Tensor,
    row_provenance: Sequence[Mapping[str, object]],
    encoder_source_sha256: str,
    tokenizer_source_sha256: str,
    model_state_sha256: str,
    physical_state_authority_sha256: str,
    role: str,
) -> QueryLocalStateResult:
    """Run one safe q-specific encoder view per row and construct S_q/T_q."""
    if role not in {"student", "teacher"}:
        raise ValueError("role must be student or teacher")
    if encoder.training:
        raise ValueError("F0 query-local construction requires encoder.eval()")
    if gene_ids.dtype is not torch.long or gene_ids.ndim != 2:
        raise TypeError("gene_ids must be torch.long [B,V]")
    if not normalized_expression.is_floating_point() or normalized_expression.ndim != 2:
        raise TypeError("normalized_expression must be floating [B,V]")
    if physical_state.dtype is not torch.uint8 or physical_state.ndim != 2:
        raise TypeError("physical_state must be immutable-semantics uint8 [B,V]")
    if evidence_visible.dtype is not torch.bool or evidence_visible.ndim != 2:
        raise TypeError("evidence_visible must be bool [B,V]")
    if query_index.dtype is not torch.long or query_index.ndim != 1:
        raise TypeError("query_index must be torch.long [B]")
    shape = normalized_expression.shape
    if gene_ids.shape != shape or physical_state.shape != shape or evidence_visible.shape != shape:
        raise ValueError("all molecular tensors must share [B,V]")
    if query_index.shape[0] != shape[0] or len(row_provenance) != shape[0]:
        raise ValueError("one query and provenance record are required per row")
    if not torch.isfinite(normalized_expression).all():
        raise ValueError("normalized_expression contains non-finite values")
    if query_index.numel() and (
        int(query_index.min()) < 0 or int(query_index.max()) >= shape[1]
    ):
        raise ValueError("query_index outside molecular ledger")
    canonical_gene_ids = torch.arange(shape[1], dtype=torch.long, device=gene_ids.device).expand(
        shape[0], -1
    )
    if not torch.equal(gene_ids, canonical_gene_ids):
        raise ValueError("gene_ids do not match the canonical ordered molecular ledger")

    unique_states = {int(item) for item in torch.unique(physical_state).tolist()}
    if not unique_states.issubset(ALLOWED_PHYSICAL_STATES):
        raise ValueError("physical_state contains a non-authoritative code")
    physical_copy = physical_state.clone()
    physical_hash_before = _tensor_sha256(physical_copy)
    measurement_scalar = physical_state == MEASURED_SCALAR
    if torch.any(evidence_visible & ~measurement_scalar):
        raise ValueError("evidence_visible must be a subset of measured scalar")
    rows = torch.arange(shape[0], device=query_index.device)
    if not torch.all(measurement_scalar[rows, query_index]):
        raise ValueError("every q must be physically MEASURED_SCALAR")
    if torch.any(evidence_visible[rows, query_index]):
        raise ValueError("q scalar evidence must be withheld")
    hidden_mask = measurement_scalar & ~evidence_visible
    if torch.any(~evidence_visible.any(dim=1)):
        raise ValueError("eligible context is empty")

    identities: list[str] = []
    for row_number, record in enumerate(row_provenance):
        if record.get("reader_partition") != "reader_fit":
            raise PermissionError("protected reader partition rejected before forward")
        if record.get("foundation_split") != "foundation/train":
            raise PermissionError("non-TRAIN or protected split rejected before forward")
        if bool(record.get("pathology", False)) or bool(record.get("external", False)):
            raise PermissionError("pathology/external provenance rejected before forward")
        identity = str(record.get("canonical_cell_id", ""))
        if not identity:
            raise ValueError("canonical_cell_id is required")
        expected_state_hash = str(record.get("physical_state_row_sha256", ""))
        if expected_state_hash != _tensor_sha256(physical_state[row_number]):
            raise ValueError("physical-state row/provenance hash mismatch")
        expected_query = record.get("query_address")
        actual_query = int(gene_ids[row_number, query_index[row_number]])
        if expected_query is None or int(expected_query) != actual_query:
            raise ValueError("query index/address provenance mismatch")
        identities.append(identity)

    _validate_sha("encoder_source_sha256", encoder_source_sha256, EXPECTED_ENCODER_SOURCE_SHA256)
    _validate_sha("tokenizer_source_sha256", tokenizer_source_sha256, EXPECTED_TOKENIZER_SOURCE_SHA256)
    _validate_sha("model_state_sha256", model_state_sha256)
    if _module_state_sha256(encoder) != model_state_sha256:
        raise ValueError("model_state_sha256 does not bind the supplied encoder")
    _validate_sha(
        "physical_state_authority_sha256",
        physical_state_authority_sha256,
        EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
    )

    context = torch.no_grad() if role == "teacher" else nullcontext()
    with context:
        encoded = encoder(
            gene_ids=gene_ids,
            expression=normalized_expression,
            measurement_mask=measurement_scalar,
            hidden_target_mask=hidden_mask,
            view="student",
        )
        gene_states = encoded.gene_states
        h_query = gene_states[rows, query_index]
        context_indices: list[tuple[int, ...]] = []
        context_hashes: list[str] = []
        context_states: list[torch.Tensor] = []
        means: list[torch.Tensor] = []
        for row in range(shape[0]):
            indices = torch.nonzero(evidence_visible[row], as_tuple=False).flatten()
            indices = indices[indices != query_index[row]]
            if indices.numel() == 0:
                raise ValueError("eligible context is empty")
            selected = gene_states[row, indices]
            context_indices.append(tuple(int(item) for item in indices.tolist()))
            context_hashes.append(_tensor_sha256(selected))
            context_states.append(selected)
            means.append(selected.sum(dim=0) / int(indices.numel()))
        mu_context = torch.stack(means)
        pre_layer_norm = h_query - mu_context
        contextual_state = F.layer_norm(pre_layer_norm, (pre_layer_norm.shape[-1],))

    if _tensor_sha256(physical_state) != physical_hash_before or not torch.equal(
        physical_state, physical_copy
    ):
        raise RuntimeError("physical_state was mutated")
    if role == "teacher":
        h_query = h_query.detach()
        mu_context = mu_context.detach()
        pre_layer_norm = pre_layer_norm.detach()
        contextual_state = contextual_state.detach()

    return QueryLocalStateResult(
        row_identity=tuple(identities),
        query_index=query_index.detach().clone(),
        query_address=gene_ids[rows, query_index].detach().clone(),
        query_physical_state=physical_state[rows, query_index].detach().clone(),
        physical_state=physical_state.detach().clone(),
        evidence_visible=evidence_visible.detach().clone(),
        hidden_mask=hidden_mask.detach().clone(),
        physical_state_sha256=physical_hash_before,
        evidence_sha256=_tensor_sha256(evidence_visible),
        hidden_mask_sha256=_tensor_sha256(hidden_mask),
        context_indices=tuple(context_indices),
        context_counts=torch.tensor(
            [len(item) for item in context_indices], dtype=torch.long, device=query_index.device
        ),
        context_state_sha256=tuple(context_hashes),
        context_states=tuple(item.detach() if role == "teacher" else item for item in context_states),
        h_query=h_query,
        mu_context=mu_context,
        pre_layer_norm=pre_layer_norm,
        contextual_state=contextual_state,
        encoder_source_sha256=encoder_source_sha256,
        tokenizer_source_sha256=tokenizer_source_sha256,
        model_state_sha256=model_state_sha256,
        physical_state_authority_sha256=physical_state_authority_sha256,
        role=role,
    )
