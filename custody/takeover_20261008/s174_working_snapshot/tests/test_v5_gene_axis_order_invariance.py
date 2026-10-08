"""The mapping must depend on gene IDENTITY, never on column ORDER.

THE DEFECT THIS ENCODES

  Every FULL104 count materializer maps source columns to molecular addresses
  through `source_feature_index`, used as a position in the source matrix. That
  is correct only when the index enumerates that matrix's own feature order. For
  the HVS_COMMON and SEA_AD_COMMON families it enumerates the harmonized feature
  universe in Ensembl order instead, so counts land at the addresses of other
  genes.

  The observable signature is simple: a POSITIONAL mapping gives different
  answers for the same data presented in a different column order. An
  IDENTITY-based mapping gives the same answer. That is what these tests assert.

  The fixture holds the gene→count content fixed and permutes only the column
  order, so any difference in the result is attributable to the ordering alone.

BOTH DIRECTIONS ARE ASSERTED

  A test that only checks the corrected mapping would pass even if the
  positional mapping were also order-invariant — which would mean the fixture
  was not exercising the defect at all. So the positional mapping is asserted to
  FAIL. A fixture that cannot distinguish the two is a fixture that proves
  nothing.
"""
from __future__ import annotations

import numpy as np
import pytest

ADDRESS_N = 64


def _fixture(rng, n_genes=24, n_cells=40):
    """Gene IDs, their per-cell counts, and an address for each gene."""
    genes = [f"ENSG{i:011d}" for i in range(n_genes)]
    counts = rng.poisson(3.0, size=(n_cells, n_genes)).astype(np.int64)
    # the authoritative address of each gene, deliberately unrelated to order
    addresses = rng.permutation(ADDRESS_N)[:n_genes]
    return genes, counts, {g: int(a) for g, a in zip(genes, addresses)}


def _permute_columns(genes, counts, rng):
    """Same genes, same counts per gene, different column order."""
    order = rng.permutation(len(genes))
    return [genes[i] for i in order], counts[:, order]


def _materialize_positional(counts, source_to_address):
    """The defective rule: column POSITION indexes the mapping table."""
    out = np.zeros((counts.shape[0], ADDRESS_N), dtype=np.int64)
    for col in range(counts.shape[1]):
        target = source_to_address.get(col)
        if target is None:
            continue
        out[:, target] += counts[:, col]
    return out


def _materialize_by_identity(genes, counts, gene_to_address):
    """The corrected rule: the gene's own identity indexes the mapping."""
    out = np.zeros((counts.shape[0], ADDRESS_N), dtype=np.int64)
    for col, g in enumerate(genes):
        target = gene_to_address.get(g)
        if target is None:
            continue
        out[:, target] += counts[:, col]
    return out


def test_identity_mapping_is_invariant_to_column_order():
    rng = np.random.default_rng(20260927)
    genes, counts, gene_to_address = _fixture(rng)
    g2, c2 = _permute_columns(genes, counts, rng)

    a = _materialize_by_identity(genes, counts, gene_to_address)
    b = _materialize_by_identity(g2, c2, gene_to_address)
    assert np.array_equal(a, b), (
        "the identity-based mapping produced different gene-addressed counts "
        "for the same data in a different column order; it is not "
        "order-invariant and therefore does not fix the defect")


def test_positional_mapping_FAILS_under_column_reordering():
    """The old rule must break here, or the fixture is not exercising anything."""
    rng = np.random.default_rng(20260927)
    genes, counts, gene_to_address = _fixture(rng)
    # the mapping table as the defective path builds it: keyed by the position a
    # gene occupies in the ORIGINAL ordering
    source_to_address = {i: gene_to_address[g] for i, g in enumerate(genes)}

    g2, c2 = _permute_columns(genes, counts, rng)
    a = _materialize_positional(counts, source_to_address)
    b = _materialize_positional(c2, source_to_address)

    assert not np.array_equal(a, b), (
        "the positional mapping was order-invariant on this fixture, so the "
        "fixture does not exercise the defect and the companion test proves "
        "nothing")


def test_positional_mapping_matches_identity_only_in_the_original_order():
    """Where the two agree, and precisely where they stop agreeing."""
    rng = np.random.default_rng(20260927)
    genes, counts, gene_to_address = _fixture(rng)
    source_to_address = {i: gene_to_address[g] for i, g in enumerate(genes)}

    same_order_positional = _materialize_positional(counts, source_to_address)
    same_order_identity = _materialize_by_identity(genes, counts, gene_to_address)
    assert np.array_equal(same_order_positional, same_order_identity), (
        "in the ORIGINAL order the two rules must agree; if they do not, the "
        "fixture is malformed rather than the rule being wrong")

    g2, c2 = _permute_columns(genes, counts, rng)
    reordered_positional = _materialize_positional(c2, source_to_address)
    reordered_identity = _materialize_by_identity(g2, c2, gene_to_address)
    assert not np.array_equal(reordered_positional, reordered_identity), (
        "after reordering the positional rule must diverge from identity; that "
        "divergence IS the FULL104 defect")


@pytest.mark.parametrize("n_genes", [8, 24, 100])
def test_order_invariance_holds_at_several_sizes(n_genes):
    rng = np.random.default_rng(1000 + n_genes)
    genes = [f"ENSG{i:011d}" for i in range(n_genes)]
    counts = rng.poisson(2.0, size=(30, n_genes)).astype(np.int64)
    addr = {g: i for i, g in enumerate(rng.permutation(genes))}
    g2, c2 = _permute_columns(genes, counts, rng)
    big = max(addr.values()) + 1

    def mat(gs, cs):
        out = np.zeros((cs.shape[0], big), dtype=np.int64)
        for col, g in enumerate(gs):
            out[:, addr[g]] += cs[:, col]
        return out

    assert np.array_equal(mat(genes, counts), mat(g2, c2))


def test_a_deliberately_wrong_mapping_is_rejected():
    """A mapping that sends two genes to one address must not pass as correct."""
    rng = np.random.default_rng(7)
    genes, counts, gene_to_address = _fixture(rng, n_genes=10)
    broken = dict(gene_to_address)
    broken[genes[1]] = broken[genes[0]]          # collide two genes

    good = _materialize_by_identity(genes, counts, gene_to_address)
    bad = _materialize_by_identity(genes, counts, broken)
    assert not np.array_equal(good, bad), (
        "a mapping that collides two distinct genes onto one address produced "
        "the same result as the correct mapping; the comparison is insensitive "
        "to exactly the error class it must catch")
    assert bad.sum() == good.sum(), (
        "the collision should relocate counts, not lose them; if the totals "
        "differ the fixture is testing something else")
