from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402


def test_partial_structural_matrix_choice_uses_reserved_stream_24():
    payload = {
        "worlds": {"genes_per_world": 44, "structural_support_rule": {"genes_with_structural_absence_per_world": 5}},
        "seeds": {"root": 31000000},
    }
    src = np.concatenate([np.full(24, 0), np.full(7, 1), np.full(11, 2)]).astype(np.int64)
    op = np.arange(42, dtype=np.int64)
    design = {"src": src, "op": op}
    support = G.build_structural_support(payload, design, world_index=0, genes=44)

    partial_gene = None
    for g in np.where((~support).any(axis=0))[0]:
        nmiss = int((~support[src == 1, g]).sum())
        if 0 < nmiss < int((src == 1).sum()):
            partial_gene = int(g)
            break
    assert partial_gene is not None

    nph_ops = np.unique(op[src == 1])
    rng = np.random.default_rng(G.seed_for(world_index=0, gene_index=partial_gene, stream=24, root=31000000))
    expected = set(int(x) for x in rng.choice(nph_ops, size=3, replace=False))
    actual = set(int(x) for x in op[(src == 1) & (~support[:, partial_gene])])
    assert actual == expected
