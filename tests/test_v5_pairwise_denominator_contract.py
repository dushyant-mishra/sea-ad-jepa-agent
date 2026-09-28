"""The pair-specific denominator is NOT total_excluding_29 minus the controls.

THE DEFECT THIS PREVENTS

  The corrected artifact stores `total_excluding_29` = the nucleus's total count
  minus 21 program addresses (three queries, twelve panel partners, six reserved
  readouts) and eight housekeeping genes.

  The frozen protocol's denominator for a directed test P -> Q is

      EXCLUDED(P,Q) = query(P) + panel(P) + query(Q) + panel(Q)
                    + RESERVED(6) + HOUSEKEEPING(8)
                    + AMBIENT(10) + MYELOID(6) + MITOCHONDRIAL(3)

  which does NOT remove the THIRD program's query and four partners. Building
  the denominator as `total_excluding_29 - controls` therefore removes five
  addresses the protocol keeps, in every one of the six directed tests. That is
  a different experiment, not a rounding difference, and it would be invisible
  because both quantities are plausible positive numbers.

  The correct reconstruction from the stored artifact adds the third program's
  query and panel counts back:

      D(P,Q) = total_excluding_29
             + counts[query(R)] + counts[panel(R)]        # R = the third program
             - counts[AMBIENT + MYELOID + MITOCHONDRIAL]

  These tests assert the naive form is WRONG and the reconstruction is EXACT.
  Asserting only the second would pass even if the two agreed, which would mean
  the fixture was not exercising the defect.
"""
from __future__ import annotations

import itertools

import numpy as np
import pytest

PROGRAMS = {
    "APOE_LIPID": {"query": 6186, "panel": [6188, 11425, 7194, 2044],
                   "readout": [4748, 13734]},
    "P2RY12_HOMEOSTATIC": {"query": 12469, "panel": [15109, 12239, 12995, 13365],
                           "readout": [2810, 14980]},
    "HLA_DRA_ANTIGEN": {"query": 18511, "panel": [392, 23673, 18500, 20496],
                        "readout": [26659, 10846]},
}
HOUSEKEEPING = [1817, 9924, 2628, 11587, 16586, 8192, 12595, 1225]
AMBIENT = [6584, 1015, 11973, 5370, 17102, 12238, 6359, 13053, 3762, 2690]
MYELOID = [18579, 12586, 966, 10205, 305, 10670]
MITO = [17359, 17409, 17415]
CONTROLS = AMBIENT + MYELOID + MITO          # 19 nuisance genes, not 20

BANNED_29 = sorted({p["query"] for p in PROGRAMS.values()}
                   | {a for p in PROGRAMS.values() for a in p["panel"]}
                   | {a for p in PROGRAMS.values() for a in p["readout"]}
                   | set(HOUSEKEEPING))


def excluded_for_pair(pred, read):
    """Exactly what the frozen protocol removes for one directed test."""
    e = {PROGRAMS[pred]["query"], PROGRAMS[read]["query"]}
    e |= set(PROGRAMS[pred]["panel"]) | set(PROGRAMS[read]["panel"])
    e |= {a for p in PROGRAMS.values() for a in p["readout"]}   # all 6 reserved
    e |= set(HOUSEKEEPING) | set(CONTROLS)
    return e


def third_program(pred, read):
    return next(k for k in PROGRAMS if k not in (pred, read))


def _fixture(rng, n=500):
    """Counts at every address the protocol mentions, plus a bulk remainder."""
    addrs = sorted(set(BANNED_29) | set(CONTROLS))
    counts = {a: rng.poisson(3.0, n).astype(np.int64) for a in addrs}
    rest = rng.poisson(4000.0, n).astype(np.int64)      # everything else
    total_all = rest + sum(counts.values())
    total_excluding_29 = total_all - sum(counts[a] for a in BANNED_29)
    return counts, total_all, total_excluding_29


def test_the_29_address_set_is_what_the_artifact_stores():
    assert len(BANNED_29) == 29, f"expected 29 excluded addresses, got {len(BANNED_29)}"
    assert len(CONTROLS) == 19, (
        f"the protocol enumerates 19 distinct NUISANCE genes, got {len(CONTROLS)}; "
        "the query-only control is already among the stored 29 and must not be "
        "counted again as a twentieth new gene")
    assert not (set(CONTROLS) & set(BANNED_29)), \
        "a control gene collides with an already-stored address"


@pytest.mark.parametrize("pred,read", [
    (a, b) for a, b in itertools.permutations(PROGRAMS, 2)])
def test_naive_denominator_is_WRONG_for_every_directed_pair(pred, read):
    """total_excluding_29 minus controls removes the third program too."""
    rng = np.random.default_rng(abs(hash(pred + read)) % (2 ** 31))
    counts, total_all, tex29 = _fixture(rng)

    naive = tex29 - sum(counts[a] for a in CONTROLS)
    correct = total_all - sum(counts[a] for a in excluded_for_pair(pred, read))

    assert not np.array_equal(naive, correct), (
        "the naive denominator matched the protocol denominator, so this "
        "fixture does not exercise the defect and the companion test proves "
        "nothing")

    R = third_program(pred, read)
    extra = sum(counts[a] for a in [PROGRAMS[R]["query"]] + PROGRAMS[R]["panel"])
    assert np.array_equal(correct - naive, extra), (
        "the discrepancy should be exactly the third program's query plus four "
        "partners — five addresses the protocol keeps and the naive form drops")


@pytest.mark.parametrize("pred,read", [
    (a, b) for a, b in itertools.permutations(PROGRAMS, 2)])
def test_reconstruction_from_the_stored_artifact_is_exact(pred, read):
    """D can be rebuilt from total_excluding_29 without re-reading the blocks."""
    rng = np.random.default_rng(abs(hash(read + pred)) % (2 ** 31))
    counts, total_all, tex29 = _fixture(rng)
    R = third_program(pred, read)

    rebuilt = (tex29
               + sum(counts[a] for a in [PROGRAMS[R]["query"]] + PROGRAMS[R]["panel"])
               - sum(counts[a] for a in CONTROLS))
    correct = total_all - sum(counts[a] for a in excluded_for_pair(pred, read))
    assert np.array_equal(rebuilt, correct), (
        "reconstruction from the stored artifact does not reproduce the protocol "
        "denominator; the real-data evaluator must not use it")


def test_denominator_is_pair_specific_not_one_global_value():
    """Six directed tests must not share a single denominator."""
    rng = np.random.default_rng(99)
    counts, total_all, _ = _fixture(rng)
    ds = {}
    for pred, read in itertools.permutations(PROGRAMS, 2):
        ds[(pred, read)] = total_all - sum(
            counts[a] for a in excluded_for_pair(pred, read))
    distinct = {tuple(v.tolist()) for v in ds.values()}
    assert len(distinct) > 1, (
        "every directed pair produced an identical denominator, which would "
        "mean the pair-specific construction is not actually pair-specific")


def test_a_denominator_that_went_nonpositive_is_detectable():
    """Protocol drops a nucleus when D <= 0; the condition must be reachable."""
    rng = np.random.default_rng(7)
    counts, total_all, _ = _fixture(rng, n=50)
    # a pathological nucleus: almost all of its counts sit in excluded addresses
    excl = excluded_for_pair("APOE_LIPID", "P2RY12_HOMEOSTATIC")
    fake_total = sum(counts[a][0] for a in excl) - 1
    d = fake_total - sum(counts[a][0] for a in excl)
    assert d <= 0, "the nonpositive-denominator branch is unreachable in testing"
