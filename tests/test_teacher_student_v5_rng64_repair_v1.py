from __future__ import annotations

import torch

from sea_ad_jepa.v5.keyed_rng_v1 import (
    keyed_dropout_mask,
    philox4x32_10_scalar,
    scientific_counter_words,
)


def test_philox4x32_10_random123_known_answer():
    assert philox4x32_10_scalar((0, 0, 0, 0), (0, 0)) == (
        0x6627E8D5,
        0xE169C58D,
        0xBC57AC4C,
        0x9B00DBD8,
    )


def test_actual_reader_fit_stable_key_extrema_fit_counter_without_aliasing():
    lo = 257_865_466_610
    hi = 9_223_371_444_004_343_451
    a = scientific_counter_words(lo, 41_237, 159)
    b = scientific_counter_words(hi, 41_237, 159)
    assert a != b
    assert a[0] == (lo & 0xFFFFFFFF)
    assert a[1] == ((lo >> 32) & 0xFFFFFFFF)
    assert b[0] == (hi & 0xFFFFFFFF)
    assert b[1] == ((hi >> 32) & 0xFFFFFFFF)
    assert a[2] == b[2] == 41_238
    assert a[3] == b[3] == 159


def test_two_real_cells_that_collided_under_old_modulus_now_have_distinct_addresses_and_streams():
    # These exact stable keys shared old keyed_rng_v1 residue 157675334 mod 2^31-1.
    left = 3_563_565_154_610_006_020
    right = 4_946_309_937_675_127_272
    assert left % 2_147_483_647 == right % 2_147_483_647
    assert scientific_counter_words(left, 17, 9) != scientific_counter_words(right, 17, 9)
    ids = torch.tensor([[-1, 17]], dtype=torch.int64)
    ml = keyed_dropout_mask(ids, torch.tensor([left], dtype=torch.int64), width=160, training_seed=77, update_index=5, view_index=2, site_id=19)
    mr = keyed_dropout_mask(ids, torch.tensor([right], dtype=torch.int64), width=160, training_seed=77, update_index=5, view_index=2, site_id=19)
    assert not torch.equal(ml, mr)


def test_packing_and_row_order_invariance_survives_uint64_repair():
    ids = torch.tensor([[-1, 0, 4, 9, 11], [-1, 0, 4, 9, 11]], dtype=torch.int64)
    keys = torch.tensor([257_865_466_610, 9_223_371_444_004_343_451], dtype=torch.int64)
    full = keyed_dropout_mask(ids, keys, width=32, training_seed=77, update_index=5, view_index=2, site_id=19)
    select = torch.tensor([4, 0, 2])
    packed = keyed_dropout_mask(ids[:, select], keys, width=32, training_seed=77, update_index=5, view_index=2, site_id=19)
    assert torch.equal(packed, full[:, select])
    rerow = keyed_dropout_mask(ids.flip(0), keys.flip(0), width=32, training_seed=77, update_index=5, view_index=2, site_id=19)
    assert torch.equal(rerow, full.flip(0))


def test_frequency_and_local_correlation_sanity_after_philox_repair():
    batch, tokens, width = 128, 64, 32
    ids = torch.arange(tokens, dtype=torch.int64).repeat(batch, 1)
    keys = torch.arange(1000, 1000 + batch, dtype=torch.int64)
    mask = keyed_dropout_mask(ids, keys, width=width, training_seed=8_113_002, update_index=91, view_index=3, site_id=17)
    keep = float(mask.float().mean())
    assert abs(keep - .9) < .004
    x = mask[:, :, :-1].float().reshape(-1)
    y = mask[:, :, 1:].float().reshape(-1)
    corr = float(torch.corrcoef(torch.stack([x, y]))[0, 1])
    assert abs(corr) < .02
