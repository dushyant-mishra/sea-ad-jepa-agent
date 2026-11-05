"""Hostile gene-ID-aligned exact-collapse tests; no training or biological PASS."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.v5 import jepa_synth2048_collapse_sentinel_v1 as sentinel


def test_id_only_gene_tokens_stop_with_healthy_separate_cell_embeddings():
    rng = np.random.default_rng(501)
    template = rng.normal(size=(16, 8))
    states = np.broadcast_to(template[None], (8, 16, 8)).copy()
    ids = np.broadcast_to(np.arange(16)[None], (8, 16)).copy()
    cell_states = rng.normal(size=(8, 8))
    assert sentinel.geometry_diagnostic(cell_states).exactly_constant_across_cells is False
    with pytest.raises(sentinel.CollapseStop, match="identity-only"):
        sentinel.token_geometry_diagnostic(states, gene_ids=ids)


def test_reordered_and_missing_gene_support_still_catches_identity_only():
    rng = np.random.default_rng(502)
    per_gene = rng.normal(size=(32, 8))
    ids = np.array([
        [0, 1, 2, 3, 4, 5],
        [5, 3, 1, 7, 8, 9],
        [9, 4, 3, 2, 0, 5],
        [6, 9, 7, 5, 2, 0],
    ], dtype=np.int32)
    states = per_gene[ids].copy()
    with pytest.raises(sentinel.CollapseStop, match="identity-only"):
        sentinel.token_geometry_diagnostic(states, gene_ids=ids)


def test_cell_specific_gene_signal_breaks_exact_identity_collapse_only():
    rng = np.random.default_rng(503)
    p = rng.normal(size=(6, 12, 16))
    ids = np.broadcast_to(np.arange(12), (6, 12)).copy()
    z = sentinel.token_geometry_diagnostic(p, gene_ids=ids)
    assert z["gene_id_alignment"] == "EXPLICIT_CANONICAL_GENE_IDS"
    assert z["shared_gene_ids_compared_across_cells"] == 12
    assert z["shared_gene_ids_with_cell_specific_states"] == 12
    assert z["qualified_biological_representation"] is False


def test_most_gene_tokens_identity_only_is_unqualified_telemetry_not_false_pass():
    # Do not invent a threshold for partial near-collapse.
    rng = np.random.default_rng(504)
    shared = rng.normal(size=(8, 6))
    a = np.broadcast_to(shared[None], (6, 8, 6)).copy()
    a[4, 7, 1] += 0.1
    ids = np.broadcast_to(np.arange(8), (6, 8)).copy()
    r = sentinel.token_geometry_diagnostic(a, gene_ids=ids)
    assert r["shared_gene_ids_compared_across_cells"] == 8
    assert r["shared_gene_ids_with_cell_specific_states"] == 1
    assert r["shared_gene_ids_without_detected_cell_specific_states"] == 7
    assert r["qualified_biological_representation"] is False


def test_different_support_with_no_shared_genes_abstains():
    p = np.random.default_rng(505).normal(size=(3, 4, 5))
    ids = np.arange(12, dtype=np.int32).reshape(3, 4)
    r = sentinel.token_geometry_diagnostic(p, gene_ids=ids)
    assert r["status"] == "NOT_ESTIMABLE_NO_SHARED_GENE_IDS"
    assert r["shared_gene_ids_compared_across_cells"] == 0


@pytest.mark.parametrize("bad", [
    np.zeros((3, 4, 1), dtype=np.int32),
    np.zeros((3, 4), dtype=np.float32),
    -np.ones((3, 4), dtype=np.int32),
    np.broadcast_to(np.array([0, 0, 1, 2]), (3, 4)).copy(),
])
def test_invalid_gene_identity_alignment_refused(bad):
    p = np.random.default_rng(506).normal(size=(3, 4, 5))
    with pytest.raises(sentinel.CollapseStop):
        sentinel.token_geometry_diagnostic(p, gene_ids=bad)


def test_no_auto_pass_even_when_both_cell_and_tokens_vary():
    states = np.random.default_rng(507).normal(size=(9, 5, 8))
    ids = np.broadcast_to(np.arange(5), (9, 5)).copy()
    r = sentinel.token_geometry_diagnostic(states, gene_ids=ids)
    assert r["status"] == "UNQUALIFIED_TOKEN_GEOMETRY_TELEMETRY_ONLY"
    assert r["qualified_biological_representation"] is False
