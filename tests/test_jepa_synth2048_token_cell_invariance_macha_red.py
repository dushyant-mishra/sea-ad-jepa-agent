"""Macha RED against #548 head cde03f73 (tests only; code UNCHANGED).

`token_geometry_diagnostic` STOPs only when all gene tokens WITHIN one cell are identical.
Distinct gene-identity embeddings make that impossible in a real encoder, so the check
cannot fire. The JEPA failure that produces a misleadingly falling loss is the opposite:
each gene's token state is the same in EVERY cell (a function of gene identity only,
blind to the cell's expression). Then hidden-block teacher targets are predictable from
gene identity alone and the loss can fall with no cell biology at all, while CELL states
still differ through another path. This test supplies exactly that case, aligned by gene,
and asks for a STOP. It uses only exact equality, consistent with the sentinel's own
no-tuned-threshold policy (it already STOPs on exactly constant CELL state).

Synthetic arrays only. No data, training, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from scripts.v5 import jepa_synth2048_collapse_sentinel_v1 as guard

CELLS, GENES, WIDTH = 6, 12, 16


def _call(tokens):
    gene_ids = np.broadcast_to(np.arange(GENES), (CELLS, GENES)).copy()
    params = inspect.signature(guard.token_geometry_diagnostic).parameters
    if "gene_ids" in params:  # tolerate a repair that requires per-token gene identity
        return guard.token_geometry_diagnostic(tokens, gene_ids=gene_ids)
    return guard.token_geometry_diagnostic(tokens)


def test_guard_cell_specific_tokens_are_not_stopped():
    tokens = np.random.default_rng(901).normal(size=(CELLS, GENES, WIDTH))
    assert _call(tokens)["qualified_biological_representation"] is False


def test_red_cell_invariant_identity_only_tokens_must_stop():
    identity_only = np.random.default_rng(902).normal(size=(GENES, WIDTH))
    tokens = np.broadcast_to(identity_only[None], (CELLS, GENES, WIDTH)).copy()
    cell_states = np.random.default_rng(903).normal(size=(CELLS, WIDTH))
    guard.geometry_diagnostic(cell_states)  # CELL still varies: no CELL STOP
    with pytest.raises(guard.CollapseStop):
        report = _call(tokens)
        pytest.fail(f"cell-invariant gene tokens reported as telemetry: {report}")
