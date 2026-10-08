#!/usr/bin/env python3
"""Deterministic SCENIC+-like regulatory ground truth: TF -> enhancer region -> target gene.

This module defines the GRAPH only. It is ground truth, not an inference pipeline: it builds
no cisTarget database, no motif ranking and no SCENIC+ software path. Both the truth
generator and the observers import it so that a single graph object is shared, and the truth
generator serialises it so the known positives and known negatives are auditable.

Design points that make the graph testable rather than decorative:

* every TF binds a SPARSE set of regions and regulates a SPARSE set of genes, so a dense
  linear loading matrix cannot imitate it;
* edges are SIGNED, so direction of effect is part of the truth;
* explicit DECOY regions are accessible and co-vary with TF activity but regulate nothing,
  which is the negative control an accessibility-only method will fail;
* explicit NEGATIVE gene sets are never regulated by a given TF, giving precision/recall a
  denominator that is not merely "everything else";
* regulons OVERLAP on a controlled number of genes, so a method must resolve shared targets
  rather than assuming disjoint modules.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v64"))
import build_v73_sharded_master_truth as T   # frozen World A primitives (stateless RNG)

S_GRAPH = 3100          # disjoint from World A (10-52) and from the truth extensions (2000-3001)

N_TF              = 4
REGIONS_PER_TF    = 12      # of 256 multiome ATAC regions
DECOY_REGIONS     = 24      # accessible, TF-correlated, regulate nothing
GENES_PER_TF      = 8       # of 96 FULL104 panel genes
SHARED_TARGETS    = 2       # genes deliberately shared between consecutive regulons
MULTIOME_GENES_PER_TF = 6   # of 64 multiome RNA genes


def _rank_pick(seed: int, n_items: int, k: int, stream: int, exclude=None) -> np.ndarray:
    """Deterministic stateless choice of k distinct items, optionally excluding a set."""
    ids = np.arange(n_items, dtype=np.uint64)
    score = T.u01(seed, ids, stream)
    if exclude is not None and len(exclude):
        score = score.copy()
        score[np.asarray(list(exclude), dtype=np.int64)] = np.inf
    return np.sort(np.argsort(score, kind="stable")[:k]).astype(np.int64)


def build_graph(seed: int, n_regions: int = 256, n_panel_genes: int = 96,
                n_multiome_genes: int = 64) -> dict:
    """Return the full regulatory ground-truth graph for a given seed."""
    g = {"seed": seed, "n_tf": N_TF, "n_regions": n_regions,
         "n_panel_genes": n_panel_genes, "n_multiome_genes": n_multiome_genes,
         "tf": []}
    used_regions: set[int] = set()
    used_genes: set[int] = set()
    prev_genes: np.ndarray | None = None

    for t in range(N_TF):
        regions = _rank_pick(seed + S_GRAPH, n_regions, REGIONS_PER_TF,
                             S_GRAPH + t, exclude=used_regions)
        used_regions.update(regions.tolist())

        genes = _rank_pick(seed + S_GRAPH + 40, n_panel_genes, GENES_PER_TF,
                           S_GRAPH + 40 + t, exclude=used_genes)
        # force a controlled overlap with the previous regulon so targets are not disjoint
        if prev_genes is not None and SHARED_TARGETS:
            genes = np.unique(np.concatenate([genes[:-SHARED_TARGETS],
                                              prev_genes[:SHARED_TARGETS]]))
        used_genes.update(genes[SHARED_TARGETS:].tolist() if prev_genes is not None
                          else genes.tolist())
        prev_genes = genes

        mgenes = _rank_pick(seed + S_GRAPH + 80, n_multiome_genes, MULTIOME_GENES_PER_TF,
                            S_GRAPH + 80 + t)

        # signed effects: direction of regulation is part of the truth
        rsign = np.where(T.u01(seed + S_GRAPH + 120, regions.astype(np.uint64),
                               S_GRAPH + 120 + t) < 0.5, -1.0, 1.0)
        gsign = np.where(T.u01(seed + S_GRAPH + 160, genes.astype(np.uint64),
                               S_GRAPH + 160 + t) < 0.35, -1.0, 1.0)
        mgsign = np.where(T.u01(seed + S_GRAPH + 200, mgenes.astype(np.uint64),
                                S_GRAPH + 200 + t) < 0.35, -1.0, 1.0)

        g["tf"].append(dict(
            tf=t,
            bound_regions=regions.tolist(),
            bound_region_signs=rsign.tolist(),
            target_panel_genes=genes.tolist(),
            target_panel_gene_signs=gsign.tolist(),
            target_multiome_genes=mgenes.tolist(),
            target_multiome_gene_signs=mgsign.tolist(),
        ))

    g["decoy_regions"] = _rank_pick(seed + S_GRAPH + 240, n_regions, DECOY_REGIONS,
                                    S_GRAPH + 240, exclude=used_regions).tolist()
    g["unbound_regions"] = sorted(set(range(n_regions))
                                  - used_regions - set(g["decoy_regions"]))
    g["never_targeted_panel_genes"] = sorted(set(range(n_panel_genes)) - used_genes)
    g["known_positive_region_gene_pairs"] = [
        [int(r), int(gg), int(s1 * s2)]
        for e in g["tf"]
        for r, s1 in zip(e["bound_regions"], e["bound_region_signs"])
        for gg, s2 in zip(e["target_panel_genes"], e["target_panel_gene_signs"])]
    g["known_negative_region_gene_pairs_are"] = (
        "every pair formed from decoy_regions or unbound_regions with any gene, and every "
        "pair formed from a bound region with a gene in never_targeted_panel_genes")
    g["semantics"] = dict(
        decoy_regions=("accessible and correlated with TF activity but regulating nothing; a "
                       "method that scores accessibility alone will call these positive"),
        shared_targets_per_adjacent_regulon=SHARED_TARGETS,
        signs="edge signs are ground truth; recovering magnitude without sign is a partial result")
    return g


def tf_region_matrix(graph: dict) -> np.ndarray:
    """(n_tf, n_regions) signed sparse binding matrix, plus zero rows for decoys."""
    M = np.zeros((graph["n_tf"], graph["n_regions"]), dtype=np.float32)
    for e in graph["tf"]:
        M[e["tf"], np.array(e["bound_regions"], dtype=np.int64)] = np.array(
            e["bound_region_signs"], dtype=np.float32)
    return M


def tf_gene_matrix(graph: dict, which: str = "panel") -> np.ndarray:
    """(n_tf, n_genes) signed sparse regulation matrix."""
    key_g = "target_panel_genes" if which == "panel" else "target_multiome_genes"
    key_s = "target_panel_gene_signs" if which == "panel" else "target_multiome_gene_signs"
    n = graph["n_panel_genes"] if which == "panel" else graph["n_multiome_genes"]
    M = np.zeros((graph["n_tf"], n), dtype=np.float32)
    for e in graph["tf"]:
        M[e["tf"], np.array(e[key_g], dtype=np.int64)] = np.array(e[key_s], dtype=np.float32)
    return M


def decoy_region_matrix(graph: dict) -> np.ndarray:
    """(n_tf, n_regions) loading that makes decoys TF-correlated but non-regulatory."""
    M = np.zeros((graph["n_tf"], graph["n_regions"]), dtype=np.float32)
    dec = np.array(graph["decoy_regions"], dtype=np.int64)
    if len(dec):
        per = max(1, len(dec) // graph["n_tf"])
        for t in range(graph["n_tf"]):
            sel = dec[t * per:(t + 1) * per]
            M[t, sel] = 1.0
    return M
