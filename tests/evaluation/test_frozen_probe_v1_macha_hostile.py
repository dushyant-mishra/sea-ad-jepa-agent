"""Hostile first-pass review tests for PR #438 head 034cb8ab (frozen_probe_v1).

Synthetic planted fixtures only; no real, protected or human data.
Tests named ``test_red_*`` are expected to FAIL against 034cb8ab and each
assertion message states the defect. Tests named ``test_green_*`` are
confirmatory checks of properties the evaluator does have.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.evaluation import frozen_probe_v1 as fp
from sea_ad_jepa.evaluation.frozen_probe_v1 import FrozenProbeError, evaluate_frozen_probe

LABELS = dict(
    source_role="PLANTED_SYNTHETIC_FIXED",
    target_semantics="CONTINUOUS_SYNTHETIC",
    query_leakage_provenance="EXCLUDED_BY_FIXTURE_CONSTRUCTION",
)


def _folds(n_donors: int = 20):
    return [([int(d) for d in range(n_donors) if d % 5 != k],
             [int(d) for d in range(n_donors) if d % 5 == k]) for k in range(5)]


def _core(seed: int = 20261026, *, unspanned_nuisance: float = 0.0,
          donor_sd: float = 0.0, rare_prevalence: float = 0.13):
    """Same generative recipe as the PR fixture (tests/evaluation/test_frozen_probe_v1.py
    lines 15-27) with two optional, separately controlled additions: a nuisance
    term outside the baseline span and a donor random effect."""
    rng = np.random.default_rng(seed)
    donors = np.repeat(np.arange(20), 80)
    n = donors.size
    source = 2 * (donors % 2) - 1
    depth = rng.normal(size=n) + .6 * source
    broad, local, _unused = rng.normal(size=(3, n))
    rare = (rng.random(n) < rare_prevalence).astype(np.float64)
    baseline = np.column_stack((source, depth, depth ** 2, source * depth,
                                broad + .15 * rng.normal(size=n)))
    donor_effect = rng.normal(size=20) * donor_sd
    nuisance_extra = np.cos(2. * depth)  # function of depth only; not in baseline span
    y = (1.4 * local + 3. * rare + .2 * broad + 2. * source + 1.2 * depth
         + unspanned_nuisance * nuisance_extra + donor_effect[donors]
         + .45 * rng.normal(size=n))
    return dict(rng=rng, donors=donors, n=n, source=source, depth=depth,
                local=local, rare=rare, baseline=baseline, y=y,
                nuisance_extra=nuisance_extra)


def _kwargs(c, z, **extra):
    out = dict(donor_ids=c["donors"].copy(), baseline=c["baseline"].copy(),
               embeddings=np.asarray(z, dtype=np.float64).copy(), target=c["y"].copy(),
               folds=_folds(), **LABELS)
    out.update(extra)
    return out


def _compact(c):
    return np.column_stack((c["local"], c["rare"]))


# ---------------------------------------------------------------------------
# RED: scientific scope of the biology-versus-nuisance discriminator
# ---------------------------------------------------------------------------

def test_red_nuisance_only_representation_earns_donor_replicated_increment():
    """In the PR NUISANCE world the embedding columns 0-3 are byte-identical to
    baseline columns 0-3 and Y's nuisance dependence lies inside the baseline
    span, so no nuisance-only embedding can earn increment by construction.
    Here a depth-only term outside the baseline span (3.7% of Y variance) is
    added; an embedding carrying ONLY that depth function and noise receives a
    positive held-donor increment in every held donor, and the receipt has no
    field that distinguishes it from biological gain."""
    c = _core(unspanned_nuisance=1.0)
    z = np.column_stack((c["nuisance_extra"], c["rng"].normal(size=c["n"])))
    r = evaluate_frozen_probe(**_kwargs(c, z))
    positive = sum(row["delta_nll"] > 0 for row in r["donor_rows"])
    # One-sided donor sign test: >=15/20 positive has p~0.021 under no increment.
    assert positive < 15, (
        "nuisance-only representation (no biological coordinate) earned a donor-"
        f"replicated increment: {positive}/20 held donors positive, mean_delta_nll="
        f"{r['mean_delta_nll']:.4f}; biology-vs-nuisance separation rests entirely on "
        "the caller baseline spanning all nuisance")


# ---------------------------------------------------------------------------
# RED: leakage guard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("transform", [
    "negated", "plus_1e-9", "float32_roundtrip", "affine_2y_plus_3",
])
def test_red_trivially_equivalent_target_copy_rejected(transform):
    """frozen_probe_v1.py:146-147 rejects only bit-exact copies of Y. After the
    train-only standardization at line 81 each transform below is the SAME
    feature as Y, yet it is accepted and inflates mean_delta_nll."""
    c = _core()
    y = c["y"]
    leaked = {
        "negated": -y,
        "plus_1e-9": y + 1e-9,
        "float32_roundtrip": y.astype(np.float32).astype(np.float64),
        "affine_2y_plus_3": 2. * y + 3.,
    }[transform]
    z = _compact(c)
    z = np.column_stack((leaked, z))
    with pytest.raises(FrozenProbeError):
        r = evaluate_frozen_probe(**_kwargs(c, z))
        clean = evaluate_frozen_probe(**_kwargs(c, _compact(c)))
        pytest.fail(f"{transform} copy of Y accepted: mean_delta_nll {r['mean_delta_nll']:.4f} "
                    f"versus {clean['mean_delta_nll']:.4f} without the leaked column")


# ---------------------------------------------------------------------------
# RED: numerical fail-open / unit dependence
# ---------------------------------------------------------------------------

def test_red_delta_nll_invariant_to_target_units():
    """A difference of Gaussian log densities is invariant to rescaling Y. The
    absolute floor sigma2>=1e-12 at line 92 breaks this: identical fixture in
    different units gives a different increment."""
    c = _core()
    z = _compact(c)
    ref = evaluate_frozen_probe(**_kwargs(c, z))["mean_delta_nll"]
    scaled = evaluate_frozen_probe(**_kwargs(c, z, target=c["y"] * 1e-6))["mean_delta_nll"]
    assert scaled == pytest.approx(ref, rel=1e-6), (
        f"unit change of Y altered mean_delta_nll: {ref:.6f} -> {scaled:.6f}")


@pytest.mark.parametrize("scale", [1e-12, 1e160])
def test_red_rescaled_informative_embedding_not_silently_scored_as_collapsed(scale):
    """Finite inputs pass line 29, but the absolute sd threshold (line 80) zeroes a
    small-unit embedding and std overflow zeroes a large-unit one; both are
    scored as if collapsed instead of failing closed."""
    c = _core()
    z = _compact(c)
    ref = evaluate_frozen_probe(**_kwargs(c, z))["mean_delta_nll"]
    try:
        with np.errstate(all="ignore"):
            got = evaluate_frozen_probe(**_kwargs(c, z * scale))
    except FrozenProbeError:
        return  # failing closed is acceptable
    assert got["mean_delta_nll"] == pytest.approx(ref, rel=1e-6), (
        f"embedding x{scale:g} scored {got['mean_delta_nll']:.3g} vs {ref:.4f}; "
        f"geometry constant={got['geometry']['constant']}")


def test_red_zero_variance_target_fails_closed():
    """A constant planted target carries no information; it returns
    mean_delta_nll == 0, the same receipt as a collapsed embedding."""
    c = _core()
    with pytest.raises(FrozenProbeError):
        evaluate_frozen_probe(**_kwargs(c, _compact(c), target=np.full(c["n"], 3.)))


# ---------------------------------------------------------------------------
# RED: identity / pseudo-replication
# ---------------------------------------------------------------------------

def test_red_same_biological_donor_under_two_ids_rejected():
    """Donor 19 is an exact row-level copy of donor 0 under a new integer ID.
    _donors/_validate_folds (lines 31-68) check only integer labels, so donor 0
    is scored while its duplicate sits in the training donors."""
    c = _core(donor_sd=1.0)
    d = c["donors"]
    m0, m19 = d == 0, d == 19
    z = np.random.default_rng(5).normal(size=(20, 8))[d]  # donor fingerprint
    c["baseline"][m19] = c["baseline"][m0]
    c["y"][m19] = c["y"][m0]
    z[m19] = z[m0]
    with pytest.raises(FrozenProbeError):
        r = evaluate_frozen_probe(**_kwargs(c, z))
        rows = {row["donor"]: row["delta_nll"] for row in r["donor_rows"]}
        others = np.median([v for k, v in rows.items() if k not in (0, 19)])
        pytest.fail(f"duplicated donor accepted: donor0 delta {rows[0]:.3f}, donor19 "
                    f"{rows[19]:.3f}, median other donors {others:.3f}")


def test_red_fixture_identity_binds_folds_and_penalty():
    """fixture_content_sha256 (lines 152-159) hashes arrays only; the folds and
    ridge penalty that determine the result are outside it."""
    c = _core()
    a = evaluate_frozen_probe(**_kwargs(c, _compact(c)))
    b = evaluate_frozen_probe(**_kwargs(c, _compact(c), ridge_penalty=5000.))
    assert a["mean_delta_nll"] != pytest.approx(b["mean_delta_nll"])
    assert a["fixture_content_sha256"] != b["fixture_content_sha256"], (
        "different decision-relevant inputs share one fixture identity: "
        f"{a['mean_delta_nll']:.4f} vs {b['mean_delta_nll']:.4f}")


# ---------------------------------------------------------------------------
# RED: score semantics and width fairness
# ---------------------------------------------------------------------------

def test_red_count_valued_target_refused_for_gaussian_score():
    """Gaussian scoring is gated only by the caller string (line 128). An
    integer-valued, non-negative Poisson target in a float array is accepted."""
    c = _core()
    counts = np.random.default_rng(3).poisson(np.exp(.5 * c["local"])).astype(np.float64)
    with pytest.raises(FrozenProbeError):
        evaluate_frozen_probe(**_kwargs(c, _compact(c), target=counts))


def test_red_wide_embedding_with_informative_coordinate_not_scored_harmful():
    """Fixed penalty 2.0 on ~1280 standardized training cells is effectively
    OLS; the in-sample sigma2 (line 92) plus overfit costs ~p/(2n) nats, so a
    representation that strictly contains a genuinely informative coordinate
    is reported as harmful once it is wide. Width, not information, decides."""
    c = _core()
    z = np.random.default_rng(99).normal(size=(c["n"], 500))
    z[:, 0] = c["local"]
    alone = evaluate_frozen_probe(**_kwargs(c, c["local"][:, None]))["mean_delta_nll"]
    wide = evaluate_frozen_probe(**_kwargs(c, z))["mean_delta_nll"]
    assert wide > 0, (f"local coordinate alone {alone:.4f}; same coordinate + 499 noise "
                      f"columns {wide:.4f}")


# ---------------------------------------------------------------------------
# GREEN: confirmatory properties
# ---------------------------------------------------------------------------

def _independent_donor_rows(kw, lam=2.):
    """Augmented least-squares ridge (no normal equations), train-only moments."""
    donors, y = kw["donor_ids"], kw["target"]
    B, Z = kw["baseline"], kw["embeddings"]
    out = {}
    for train_ids, held_ids in kw["folds"]:
        tr, te = np.isin(donors, train_ids), np.isin(donors, held_ids)

        def score(X):
            m, s = X[tr].mean(0), X[tr].std(0)
            s[s <= 1e-10] = 1.
            A = np.hstack([np.ones((tr.sum(), 1)), (X[tr] - m) / s])
            At = np.hstack([np.ones((te.sum(), 1)), (X[te] - m) / s])
            P = (np.sqrt(lam) * np.eye(A.shape[1]))[1:]
            w = np.linalg.lstsq(np.vstack([A, P]),
                                np.concatenate([y[tr], np.zeros(len(P))]), rcond=None)[0]
            s2 = max(np.mean((y[tr] - A @ w) ** 2), 1e-12)
            return .5 * (np.log(2 * np.pi * s2) + (y[te] - At @ w) ** 2 / s2)

        nb, na = score(B), score(np.hstack([B, Z]))
        for dd in held_ids:
            mk = donors[te] == dd
            out[dd] = (nb[mk].mean(), na[mk].mean(), (nb - na)[mk].mean())
    return out


@pytest.mark.parametrize("kind", ["MULTIPROGRAM", "COLLAPSED", "NUISANCE", "COMPACT",
                                  "COMPACT_RARE_DROPPED"])
def test_green_independent_reproduction_of_donor_rows(kind):
    from test_frozen_probe_v1 import _world  # sibling module (rootdir-insert import mode)
    kw = _world(kind)
    got = evaluate_frozen_probe(**kw)
    mine = _independent_donor_rows(kw)
    for row in got["donor_rows"]:
        b, a, dl = mine[row["donor"]]
        assert abs(b - row["baseline_nll"]) < 1e-10
        assert abs(a - row["augmented_nll"]) < 1e-10
        assert abs(dl - row["delta_nll"]) < 1e-10
    assert abs(np.mean([v[2] for v in mine.values()]) - got["mean_delta_nll"]) < 1e-10


def test_green_donor_fingerprint_shortcut_does_not_transfer():
    c = _core(donor_sd=1.0)
    z = np.random.default_rng(5).normal(size=(20, 8))[c["donors"]]
    assert evaluate_frozen_probe(**_kwargs(c, z))["mean_delta_nll"] < 0


@pytest.mark.parametrize("variant", ["str_ids", "bool_fold", "np_int_fold"])
def test_green_identity_type_tricks_fail_closed(variant):
    c = _core()
    kw = _kwargs(c, _compact(c))
    if variant == "str_ids":
        kw["donor_ids"] = np.array([f" {d}" for d in c["donors"]])
    elif variant == "bool_fold":
        kw["folds"][0][1][0] = bool(kw["folds"][0][1][0])
    else:
        kw["folds"][0][1][0] = np.int64(kw["folds"][0][1][0])
    with pytest.raises(FrozenProbeError):
        evaluate_frozen_probe(**kw)


def test_green_module_imports_no_trainable_framework():
    tree = ast.parse(Path(fp.__file__).read_text(encoding="utf-8"))
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
             for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree)
              if isinstance(n, ast.ImportFrom) and n.module}
    assert names <= {"__future__", "collections", "hashlib", "math", "numpy"}, names
