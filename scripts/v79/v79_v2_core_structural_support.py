#!/usr/bin/env python3
"""Authoritative structural-support construction for V79 V2_CORE worlds.

Source identity is bound through the frozen operator/source bridge, never inferred
from whichever matrix levels happen to appear in a resampled synthetic design.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import generate_v79_v2_core_worlds as G

REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")
SOURCE_ABSENCE_WEIGHTS = {"HVS": 38.0, "NPH52": 20.0, "SEA_AD": 10.0}


def load_source_code_map_from_bridge(bridge_path: Path, design: dict[str, np.ndarray]) -> dict[str, int]:
    """Resolve synthetic integer source codes against the frozen operator/source bridge.

    Only operators actually present in ``design`` are needed for the mapping, but
    every present operator must agree with the bridge. This remains valid when a
    resampled BASE world happens not to contain all 42 matrix levels.
    """
    bridge = json.loads(Path(bridge_path).read_text(encoding="utf-8"))
    rows = bridge.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("STOP: operator/source bridge lacks rows")
    op = np.asarray(design["op"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    if len(op) != len(src) or len(op) == 0:
        raise SystemExit("STOP: invalid design for source mapping")

    by_op = {}
    for r in rows:
        oi = int(r["operator_index"])
        source = str(r["source"])
        if source not in REQUIRED_SOURCES:
            raise SystemExit(f"STOP: unexpected bridge source {source}")
        if oi in by_op and by_op[oi] != source:
            raise SystemExit("STOP: bridge operator has conflicting sources")
        by_op[oi] = source

    mapping: dict[str, int] = {}
    for oi in np.unique(op):
        if int(oi) not in by_op:
            raise SystemExit(f"STOP: design operator {int(oi)} absent from frozen bridge")
        source_name = by_op[int(oi)]
        codes = np.unique(src[op == oi])
        if len(codes) != 1:
            raise SystemExit("STOP: design operator spans source codes")
        code = int(codes[0])
        old = mapping.get(source_name)
        if old is not None and old != code:
            raise SystemExit(f"STOP: {source_name} maps to multiple source codes")
        mapping[source_name] = code

    if set(mapping) != set(REQUIRED_SOURCES):
        raise SystemExit(f"STOP: source mapping incomplete: {sorted(mapping)}")
    if len(set(mapping.values())) != 3:
        raise SystemExit("STOP: source names do not map one-to-one to source codes")
    return mapping


def validate_source_code_map(source_code_map: dict[str, int], design: dict[str, np.ndarray]) -> dict[str, int]:
    if set(source_code_map) != set(REQUIRED_SOURCES):
        raise SystemExit("STOP: source-code map must contain exactly HVS/NPH52/SEA_AD")
    out = {k: int(source_code_map[k]) for k in REQUIRED_SOURCES}
    if len(set(out.values())) != 3:
        raise SystemExit("STOP: source-code map is not one-to-one")
    observed = set(int(x) for x in np.unique(np.asarray(design["src"], dtype=np.int64)))
    if observed != set(out.values()):
        raise SystemExit(f"STOP: source-code map does not match design codes: {sorted(observed)}")
    return out


def build_structural_support(payload: dict, design: dict[str, np.ndarray], *, world_index: int,
                             source_code_map: dict[str, int], genes: int | None = None,
                             amendment: dict | None = None) -> np.ndarray:
    """Build frozen measurement support using explicit biological/source identity."""
    codes = validate_source_code_map(source_code_map, design)
    GENE_COUNT = int(genes if genes is not None else payload["worlds"]["genes_per_world"])
    op = np.asarray(design["op"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    support = np.ones((len(src), GENE_COUNT), dtype=bool)
    rule = payload["worlds"]["structural_support_rule"]
    n_struct = (int(rule["genes_with_structural_absence_per_world"])
                if GENE_COUNT == int(payload["worlds"]["genes_per_world"])
                else min(GENE_COUNT, max(1, round(59.0 / 500.0 * GENE_COUNT))))
    root = int(payload["seeds"]["root"])
    wi1 = G.effective_seed_world_index(world_index, 1, amendment) if amendment is not None else int(world_index)
    rng = np.random.default_rng(G.seed_for(world_index=wi1, gene_index=9999, stream=1, root=root))
    structural_genes = np.sort(rng.choice(GENE_COUNT, size=n_struct, replace=False))
    source_codes = np.asarray([codes[s] for s in REQUIRED_SOURCES], dtype=np.int64)

    if n_struct == 5:
        # One gene measured in exactly one uniformly selected source.
        g = int(structural_genes[0])
        keep = int(rng.choice(source_codes))
        support[:, g] = src == keep

        # Three genes fully absent in one source using frozen HVS:NPH52:SEA_AD weights.
        weights = np.asarray([SOURCE_ABSENCE_WEIGHTS[s] for s in REQUIRED_SOURCES], dtype=float)
        weights /= weights.sum()
        for g0 in structural_genes[1:4]:
            absent = int(rng.choice(source_codes, p=weights))
            support[:, int(g0)] = src != absent

        # One partial NPH52 gene: exactly 3 of the 7 canonical NPH52 operators.
        g = int(structural_genes[4])
        nph = int(codes["NPH52"])
        nph_ops = np.unique(op[src == nph])
        if len(nph_ops) != 7:
            raise SystemExit(f"STOP: NPH52 design must expose all 7 operators for partial-support truth, got {len(nph_ops)}")
        wi24 = G.effective_seed_world_index(world_index, 24, amendment) if amendment is not None else int(world_index)
        matrix_rng = np.random.default_rng(G.seed_for(world_index=wi24, gene_index=g, stream=24, root=root))
        drop = set(int(x) for x in matrix_rng.choice(nph_ops, size=3, replace=False))
        support[:, g] = np.asarray([not (int(s) == nph and int(o) in drop) for s, o in zip(src, op)], dtype=bool)
        return support

    # Tiny fixtures only: retain the measured/unmeasured path without claiming 1/3/1 composition.
    for g0 in structural_genes:
        absent = int(rng.choice(source_codes))
        support[:, int(g0)] = src != absent
    return support
