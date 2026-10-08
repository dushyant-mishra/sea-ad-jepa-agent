"""S157 paired challenge: the latent behind the biological arm, its exact twin and the
operator-linked twin. Written before the observer hook existed (RED first).

The exact twin is defined by identical observables, so its latent must equal the biological
arm's exactly; the operator twin shares the same noise but groups cells by operator instead of
by biological state. Each test states the value that would make it fail.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v64"))

import build_v77_fullscale_rna_observer_v2 as OBS  # noqa: E402

Z = dict(state_index=np.array([0, 2, 2, 1, 2, 5, 2, 3]),
         operator_index=np.array([0, 1, 2, 3, 4, 5, 6, 7]))
IDS = np.arange(8, dtype=np.int64) * 11 + 5
BASE = dict(k_star=2, delta=2.0, beta=0.6, module_addresses=[1, 2, 3], operator_set=[1, 4])


def _spec(kind):
    return dict(BASE, kind=kind)


def test_bio_and_exact_twin_latents_are_identical():
    a = OBS.challenge_latent(_spec("BIO"), Z, IDS, 7302)
    b = OBS.challenge_latent(_spec("TWIN_EXACT"), Z, IDS, 7302)
    assert a.std() > 0, "a constant latent would make this test vacuous"
    assert np.array_equal(a, b), "the exact twin's latent differs from the biological arm's"


def test_bio_tracks_state_and_operator_twin_tracks_operators_with_the_same_noise():
    bio = OBS.challenge_latent(_spec("BIO"), Z, IDS, 7302)
    op = OBS.challenge_latent(_spec("TWIN_OPERATOR"), Z, IDS, 7302)
    noise_bio = bio - 2.0 * (Z["state_index"] == 2)
    noise_op = op - 2.0 * np.isin(Z["operator_index"], [1, 4])
    assert np.allclose(noise_bio, noise_op), "the twins must differ only in grouping"
    assert not np.array_equal(bio, op), "the operator twin must not reproduce the state grouping"


def test_latent_follows_cell_identity_not_row_order():
    perm = np.arange(8)[::-1]
    a = OBS.challenge_latent(_spec("BIO"), Z, IDS, 7302)
    b = OBS.challenge_latent(_spec("BIO"), {k: v[perm] for k, v in Z.items()}, IDS[perm], 7302)
    assert np.array_equal(b, a[perm])


def test_unknown_kind_is_refused(tmp_path):
    (tmp_path / "CHALLENGE_SPEC.json").write_text('{"kind": "SOMETHING_ELSE"}')
    with pytest.raises(RuntimeError):
        OBS.load_challenge(tmp_path)


def test_no_spec_means_no_challenge(tmp_path):
    assert OBS.load_challenge(tmp_path) is None
