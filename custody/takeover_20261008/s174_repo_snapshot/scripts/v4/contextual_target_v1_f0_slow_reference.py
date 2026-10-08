"""Independent slow true-singleton reference for contextual target F0.

This file intentionally does not import the optimized constructor or any of its
helpers.  Each row is forwarded independently through the frozen encoder.
"""

from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from typing import Mapping, Sequence

import torch
import torch.nn.functional as F


def _own_hash(value: torch.Tensor) -> str:
    array = value.detach().contiguous().cpu().numpy()
    h = hashlib.sha256()
    h.update(str(array.dtype).encode("ascii"))
    h.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    h.update(array.tobytes(order="C"))
    return h.hexdigest()


def slow_true_singleton_reference(
    *,
    encoder: torch.nn.Module,
    gene_ids: torch.Tensor,
    normalized_expression: torch.Tensor,
    physical_state: torch.Tensor,
    evidence_visible: torch.Tensor,
    query_index: torch.Tensor,
    row_provenance: Sequence[Mapping[str, object]],
    role: str,
) -> dict[str, object]:
    if role not in {"student", "teacher"}:
        raise ValueError("bad role")
    if encoder.training:
        raise ValueError("reference encoder must be eval")
    if physical_state.dtype is not torch.uint8 or evidence_visible.dtype is not torch.bool:
        raise TypeError("reference state/evidence dtype failure")
    if gene_ids.dtype is not torch.long or query_index.dtype is not torch.long:
        raise TypeError("reference identity dtype failure")
    if not normalized_expression.is_floating_point() or not torch.isfinite(normalized_expression).all():
        raise TypeError("reference expression failure")
    if not (
        gene_ids.shape == normalized_expression.shape == physical_state.shape == evidence_visible.shape
    ):
        raise ValueError("reference shape failure")
    if query_index.shape != (len(gene_ids),) or len(row_provenance) != len(gene_ids):
        raise ValueError("reference row geometry failure")

    all_hq, all_mu, all_pre, all_final, all_context_states = [], [], [], [], []
    all_indices, all_context_hashes, all_hidden_hashes, all_hidden = [], [], [], []
    physical_before = physical_state.clone()
    guard = torch.no_grad() if role == "teacher" else nullcontext()
    for row in range(len(gene_ids)):
        provenance = row_provenance[row]
        if provenance.get("reader_partition") != "reader_fit" or provenance.get(
            "foundation_split"
        ) != "foundation/train":
            raise PermissionError("reference protected provenance")
        if bool(provenance.get("pathology", False)) or bool(provenance.get("external", False)):
            raise PermissionError("reference pathology/external provenance")
        codes = {int(item) for item in torch.unique(physical_state[row]).tolist()}
        if not codes.issubset({0, 1, 2}):
            raise ValueError("reference invalid state")
        measured = physical_state[row : row + 1] == 1
        visible = evidence_visible[row : row + 1]
        if torch.any(visible & ~measured):
            raise ValueError("reference evidence not measured")
        q = int(query_index[row])
        if q < 0 or q >= physical_state.shape[1] or not bool(measured[0, q]):
            raise ValueError("reference q not measured")
        if str(provenance.get("physical_state_row_sha256", "")) != _own_hash(
            physical_state[row]
        ):
            raise ValueError("reference physical-state provenance mismatch")
        if int(provenance.get("query_address", -1)) != int(gene_ids[row, q]):
            raise ValueError("reference query identity mismatch")
        if bool(visible[0, q]):
            raise ValueError("reference q visible")
        hidden = measured & ~visible
        all_hidden_hashes.append(_own_hash(hidden))
        all_hidden.append(hidden[0].detach().clone())
        with guard:
            output = encoder(
                gene_ids=gene_ids[row : row + 1],
                expression=normalized_expression[row : row + 1],
                measurement_mask=measured,
                hidden_target_mask=hidden,
                view="student",
            )
            hq = output.gene_states[0, q]
            indices = torch.nonzero(visible[0], as_tuple=False).flatten()
            indices = indices[indices != q]
            if indices.numel() == 0:
                raise ValueError("reference empty context")
            chosen = output.gene_states[0, indices]
            mu = chosen.sum(dim=0) / int(indices.numel())
            pre = hq - mu
            final = F.layer_norm(pre, (pre.shape[-1],))
        all_hq.append(hq)
        all_mu.append(mu)
        all_pre.append(pre)
        all_final.append(final)
        all_indices.append(tuple(int(item) for item in indices.tolist()))
        all_context_hashes.append(_own_hash(chosen))
        all_context_states.append(chosen.detach() if role == "teacher" else chosen)
    if not torch.equal(physical_state, physical_before):
        raise RuntimeError("reference mutated physical state")
    return {
        "row_identity": tuple(str(row["canonical_cell_id"]) for row in row_provenance),
        "query_index": query_index.detach().clone(),
        "query_address": gene_ids[torch.arange(len(gene_ids), device=query_index.device), query_index]
        .detach()
        .clone(),
        "physical_state": physical_state.detach().clone(),
        "evidence_visible": evidence_visible.detach().clone(),
        "hidden_mask_sha256_per_row": tuple(all_hidden_hashes),
        "hidden_mask": torch.stack(all_hidden),
        "context_indices": tuple(all_indices),
        "context_state_sha256": tuple(all_context_hashes),
        "context_states": tuple(all_context_states),
        "h_query": torch.stack(all_hq),
        "mu_context": torch.stack(all_mu),
        "pre_layer_norm": torch.stack(all_pre),
        "contextual_state": torch.stack(all_final),
    }
