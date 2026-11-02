"""Fail-closed memory/data-path planning for foundation qualification and later real fits."""
from __future__ import annotations


def dense_bytes(n_rows: int, n_columns: int, dtype_bytes: int) -> int:
    rows, cols, item = int(n_rows), int(n_columns), int(dtype_bytes)
    if rows <= 0 or cols <= 0 or item <= 0:
        raise ValueError("dense geometry and dtype bytes must be positive")
    return rows * cols * item


def compact_cache_plan(
    n_cells: int,
    registry_genes: int,
    selected_genes: int,
    dtype_bytes: int,
    dense_budget_bytes: int,
) -> dict[str, object]:
    """Plan an authenticated selected-gene cache without authorizing registry-wide dense materialization."""
    n_cells = int(n_cells)
    registry_genes = int(registry_genes)
    selected_genes = int(selected_genes)
    budget = int(dense_budget_bytes)
    if not (0 < selected_genes < registry_genes):
        raise ValueError("selected_genes must be positive and strictly smaller than registry_genes")
    if budget <= 0:
        raise ValueError("dense memory budget must be positive")
    full = dense_bytes(n_cells, registry_genes, dtype_bytes)
    selected = dense_bytes(n_cells, selected_genes, dtype_bytes)
    if selected > budget:
        raise MemoryError(f"selected dense cache would require {selected} bytes, above budget {budget}")
    return {
        "schema": "FOUNDATION_COMPACT_ANALYSIS_CACHE_PLAN_V1",
        "n_cells": n_cells,
        "registry_genes": registry_genes,
        "selected_genes": selected_genes,
        "full_registry_dense_bytes": full,
        "selected_dense_bytes": selected,
        "dense_budget_bytes": budget,
        "full_registry_dense_authorized": False,
        "selected_dense_authorized": True,
        "required_fields": ["selected_counts", "library_size", "detected_features", "design_indices"],
        "source_binding_required": True,
        "selected_column_identity_hash_required": True,
        "training_authorized": False,
    }
