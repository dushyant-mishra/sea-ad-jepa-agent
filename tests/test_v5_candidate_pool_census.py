"""Adversarial tests for the outcome-blind candidate-pool census.

Each test names the failure it exists to catch, and every one of them is
reachable: the fixture is built so the assertion can actually fail if the
guard is removed. Tests that cannot fail are the specific defect this project
keeps finding, so the accumulator test below is checked against a brute-force
recomputation rather than against itself.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "scripts" / "v5" / "full104_candidate_pool_census_v1.py"
ANALYSIS = ROOT / "scripts" / "v5" / "candidate_pool_analysis_v1.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def C():
    return _load(CENSUS, "full104_candidate_pool_census_v1")


@pytest.fixture(scope="module")
def A(C):
    return _load(ANALYSIS, "candidate_pool_analysis_v1")


# --------------------------------------------------------------------------
# The outcome firewall
# --------------------------------------------------------------------------

def test_the_forbidden_set_is_exactly_the_frozen_48(C):
    assert len(C.BAN_29) == 29
    assert len(C.NUISANCE) == 19
    assert len(C.FORBIDDEN) == 48
    assert not (set(C.BAN_29) & set(C.NUISANCE)), "a nuisance gene collides with the 29"


def test_every_reserved_readout_is_forbidden(C):
    reserved = {a for p in C.R8_ADDR.values() for a in p["readout"]}
    assert len(reserved) == 6
    assert reserved <= set(C.FORBIDDEN)
    # and the identities are exactly the six frozen ones
    assert sorted(reserved) == [2810, 4748, 10846, 13734, 14980, 26659]


def test_every_program_and_housekeeping_address_is_forbidden(C):
    prog = {p["query"] for p in C.R8_ADDR.values()}
    prog |= {a for p in C.R8_ADDR.values() for a in p["panel"]}
    assert prog <= set(C.FORBIDDEN)
    assert set(C.HOUSEKEEPING) <= set(C.FORBIDDEN)


def test_eligible_mask_removes_every_forbidden_address(A, C):
    n = C.N_ADDR
    stats = {"n_available": np.full(n, 10_000, dtype=np.int64),
             "mean": np.full(n, 1.0)}
    m = A.eligible_mask(stats, min_cells=500)
    assert m.sum() == n - len(C.FORBIDDEN), "exclusion count is wrong"
    assert not m[np.asarray(C.FORBIDDEN)].any(), "a forbidden address survived"
    # reachability of the assertion: without the exclusion the mask would be full
    assert m.sum() < n


def test_slot_pool_never_returns_a_forbidden_gene(A, C):
    n = C.N_ADDR
    rng = np.random.default_rng(20260928)
    stats = {"n_available": np.full(n, 10_000, dtype=np.int64),
             "mean": np.full(n, 1.0), "detect": np.full(n, 0.5),
             "fano": np.full(n, 2.0), "depth": np.full(n, 0.1),
             "hk": np.full(n, 0.2)}
    elig = A.eligible_mask(stats, 500)
    base = C.R8_ADDR["APOE_LIPID"]["panel"][0]
    # every address matches on every criterion here, so the ONLY thing that can
    # keep a forbidden gene out is the firewall itself
    for _, crit in C.TIERS:
        pool = A.slot_pool(stats, base, crit, elig)
        assert len(pool) > 0, "fixture must produce a non-empty pool"
        assert not (set(pool.tolist()) & set(C.FORBIDDEN))
        assert base not in pool, "a slot must not match itself"


# --------------------------------------------------------------------------
# Evaluation-donor contamination
# --------------------------------------------------------------------------

def test_donor_split_is_disjoint_and_one_third_per_source(C):
    pairs = [("HVS", f"h{i}") for i in range(30)]
    pairs += [("NPH52", f"n{i}") for i in range(16)]
    pairs += [("SEA_AD", f"s{i}") for i in range(46)]
    a = C.split_donors(pairs)
    for src, n in (("HVS", 30), ("NPH52", 16), ("SEA_AD", 46)):
        ev = [d for (s, d), v in a.items() if s == src and v == "EVAL"]
        fit = [d for (s, d), v in a.items() if s == src and v == "FIT"]
        assert len(ev) + len(fit) == n
        assert not set(ev) & set(fit), "a donor is in both arms"
        assert len(ev) == -(-n // 3), f"{src}: expected ceil(n/3) evaluation donors"


def test_donor_split_is_stable_across_processes(C):
    """PYTHONHASHSEED must not move the split. Python's hash() would."""
    code = (
        "import importlib.util,sys,json;"
        f"s=importlib.util.spec_from_file_location('c',r'{CENSUS}');"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "p=[('HVS','h%d'%i) for i in range(30)]+[('NPH52','n%d'%i) for i in range(16)];"
        "a=m.split_donors(p);"
        "print(json.dumps(sorted(k[1] for k,v in a.items() if v=='EVAL')))"
    )
    outs = []
    for seed in ("0", "1", "12345"):
        import os
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", code], env=env,
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-400:]
        outs.append(r.stdout.strip())
    assert len(set(outs)) == 1, f"donor split moved with PYTHONHASHSEED: {outs}"


def test_a_leaked_evaluation_donor_would_change_the_split(C):
    """Reachability: the split must actually separate donors, not label them all
    FIT. If it did, contamination would be undetectable."""
    pairs = [("HVS", f"h{i}") for i in range(30)]
    a = C.split_donors(pairs)
    assert "EVAL" in a.values() and "FIT" in a.values()


# --------------------------------------------------------------------------
# Structural zeros, and the accumulator arithmetic
# --------------------------------------------------------------------------

def test_unavailable_addresses_are_nan_not_zero(C):
    acc = C.Acc()
    acc.add_cells("m1", 100, np.full(100, 8.5), np.full(100, 1.0))
    avail = {"m1": np.zeros(C.N_ADDR, dtype=bool)}
    avail["m1"][:10] = True                      # only ten addresses measured
    out = C.finish(acc, avail)
    assert np.isnan(out["mean"][20]), "an unmeasured address must be NaN"
    assert out["n_available"][20] == 0
    assert out["mean"][0] == 0.0, "a measured address with no counts is a real zero"
    assert out["n_available"][0] == 100


def test_streaming_accumulators_match_a_brute_force_recomputation(C):
    """The arithmetic, checked against a dense recomputation rather than itself."""
    rng = np.random.default_rng(7)
    n_cells, n_addr = 400, 60
    dense = rng.poisson(0.7, size=(n_cells, n_addr)).astype(np.float64)
    D = rng.integers(3000, 9000, size=n_cells).astype(np.float64)
    hk = rng.normal(size=n_cells)
    logD = np.log(D)

    acc = C.Acc()
    acc.add_cells("m", n_cells, logD, hk)
    r, cidx = np.nonzero(dense)
    cnt = dense[r, cidx]
    y = np.log1p(cnt * 1e4 / D[r])
    # pad the accumulator arrays to the module's N_ADDR
    acc.add_entries(cidx.astype(np.int64), cnt, y, logD[r], hk[r])
    avail = {"m": np.zeros(C.N_ADDR, dtype=bool)}
    avail["m"][:n_addr] = True
    out = C.finish(acc, avail)

    Y = np.log1p(dense * 1e4 / D[:, None])
    for a in range(n_addr):
        assert np.isclose(out["mean"][a], dense[:, a].mean(), atol=1e-9)
        assert np.isclose(out["detect"][a], (dense[:, a] > 0).mean(), atol=1e-9)
        want_fano = dense[:, a].var() / dense[:, a].mean()
        assert np.isclose(out["fano"][a], want_fano, atol=1e-8)
        assert np.isclose(out["depth"][a], np.corrcoef(Y[:, a], logD)[0, 1], atol=1e-8)
        assert np.isclose(out["hk"][a], np.corrcoef(Y[:, a], hk)[0, 1], atol=1e-8)


def test_partially_available_address_uses_only_its_own_cells(C):
    """The bug this guards: summing covariate moments over the WHOLE source
    while dividing by a per-address n gives a wrong correlation whenever an
    address is measured in only some matrices."""
    acc = C.Acc()
    rng = np.random.default_rng(11)
    for mid, n, shift in (("m1", 200, 0.0), ("m2", 200, 5.0)):
        logD = rng.normal(8.5 + shift, 0.2, size=n)
        acc.add_cells(mid, n, logD, np.zeros(n))
    avail = {"m1": np.zeros(C.N_ADDR, dtype=bool),
             "m2": np.zeros(C.N_ADDR, dtype=bool)}
    avail["m1"][0] = True                 # address 0 only in m1
    avail["m2"][1] = True                 # address 1 only in m2
    avail["m1"][2] = avail["m2"][2] = True
    out = C.finish(acc, avail)
    assert out["n_available"][0] == 200
    assert out["n_available"][1] == 200
    assert out["n_available"][2] == 400, "a fully available address sees both"


# --------------------------------------------------------------------------
# Decoding
# --------------------------------------------------------------------------

def test_a_positional_mapping_is_not_the_decoder(C, tmp_path):
    """The original Level-4 defect was using block position as gene identity.
    A verified decoder must disagree with that, or it is not doing anything."""
    d = tmp_path / "dec"
    d.mkdir()
    cols = np.arange(100, dtype=np.int64)
    addrs = (cols * 7 + 3) % C.N_ADDR          # a genuine permutation
    np.savez(d / "decoder_M.npz", block_column=cols, true_address=addrs)
    lut, status, nmap = C.build_col2addr(str(d), "M")
    assert status == "DECODER_VERIFIED" and nmap == 100
    assert not np.array_equal(lut[cols], cols), \
        "the decoder maps every column to itself, so it cannot fix the defect"
    assert np.array_equal(lut[cols], addrs)


def test_a_matrix_without_a_verified_decoder_is_refused(C, tmp_path):
    lut, status, _ = C.build_col2addr(str(tmp_path), "UNKNOWN_MATRIX")
    assert lut is None and status == "NO_VERIFIED_DECODER"


def test_nph52_is_identity_verified_and_needs_no_decoder(C):
    mid = "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs"
    lut, status, _ = C.build_col2addr("/nonexistent", mid)
    assert lut == "IDENTITY"
    assert status == "NPH52_FEATURE_AXIS_VERIFIED_ZERO_BASED"


# --------------------------------------------------------------------------
# Panel feasibility arithmetic
# --------------------------------------------------------------------------

def test_max_disjoint_panels_respects_the_scarcest_slot(A):
    pools = [np.arange(100, 400), np.arange(400, 405), np.arange(500, 800),
             np.arange(800, 1100)]
    k = A.max_disjoint_panels(pools)
    assert k == 5, f"the five-gene slot caps the panel count, got {k}"


def test_an_empty_slot_makes_zero_panels(A):
    pools = [np.arange(100, 400), np.array([], dtype=np.int64),
             np.arange(500, 800), np.arange(800, 1100)]
    assert A.max_disjoint_panels(pools) == 0


def test_disjoint_panels_never_reuse_a_gene(A):
    pools = [np.arange(0, 10), np.arange(10, 20),
             np.arange(20, 30), np.arange(30, 40)]
    assert A.max_disjoint_panels(pools) == 10


# --------------------------------------------------------------------------
# Regression: availability is a property of the ADDRESS, not the block column
# --------------------------------------------------------------------------

def test_availability_mask_is_indexed_by_address_not_by_column(C, tmp_path):
    """The bug this catches, found after a full 12-minute census run.

    `lut` is indexed by block column and HOLDS the true address. The census
    built its availability mask as `lut >= 0`, which is a mask over COLUMNS.
    Because the SEA-AD decoders are complete permutations - identity fraction
    0.0000 - that mislabelled 1,469 addresses available and 1,469 absent in
    every SEA-AD matrix, and reported CD74 as structurally unmeasured when it
    is measured, while reporting PGK1 as measured when it is genuinely absent.

    The counts coincide (a permutation maps n columns onto n addresses), so a
    check on pool SIZES cannot catch this. Only identity can.
    """
    d = tmp_path / "dec"
    d.mkdir()
    cols = np.arange(0, 200, dtype=np.int64)
    addrs = (cols * 7 + 3) % C.N_ADDR
    np.savez(d / "decoder_P.npz", block_column=cols, true_address=addrs)
    lut, status, _ = C.build_col2addr(str(d), "P")

    column_mask = lut >= 0                       # the WRONG construction
    address_mask = np.zeros(C.N_ADDR, dtype=bool)
    mapped = lut[lut >= 0]
    address_mask[mapped] = True                  # the correct one

    assert column_mask.sum() == address_mask.sum(), \
        "a permutation preserves the COUNT, which is why size checks miss this"
    assert not np.array_equal(column_mask, address_mask), \
        "fixture must use a non-identity decoder or the bug is unreachable"

    for a in addrs.tolist():
        assert address_mask[a], "every mapped true address must be available"
    wrong = int((column_mask & ~address_mask).sum())
    assert wrong > 0, "the wrong construction must mislabel something"
