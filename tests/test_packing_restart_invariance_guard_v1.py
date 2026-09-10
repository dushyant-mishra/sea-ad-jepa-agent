import pytest

from sea_ad_jepa.v5.packing_restart_invariance_guard_v1 import (
    FORBIDDEN_RNG_COORDINATES,
    PackingRestartInvarianceAuthorityV1,
    qualify_packing_restart_invariance,
)


def authority(**kw):
    base = dict(
        authority_id="packing-restart-v1",
        scientific_schedule_authority_id="schedule-v1",
        scientific_schedule_artifact_sha256="a" * 64,
        keyed_rng_contract_sha256="b" * 64,
        proposal_weight_artifact_sha256="c" * 64,
        dimension_authority_artifact_sha256="d" * 64,
        forbidden_rng_coordinates=FORBIDDEN_RNG_COORDINATES,
        rules_frozen_before_optimizer_start=True,
    )
    base.update(kw)
    return PackingRestartInvarianceAuthorityV1(**base)


def reference():
    return [["p0", "p1", "p2", "p3"], ["p4", "p5", "p6"], ["p7", "p8"]]


def packed():
    return [[["p0"], ["p1", "p2"], ["p3"]], [["p4", "p5"], ["p6"]], [["p7"], ["p8"]]]


def resumed():
    return [[["p4"], ["p5", "p6"]], [["p7", "p8"]]]


def test_hardware_repacking_preserves_scientific_updates_and_restart_suffix():
    out = qualify_packing_restart_invariance(
        reference_updates=reference(), packed_updates=packed(), restart_update_cursor=1,
        resumed_packed_updates=resumed(), authority=authority(),
    )
    assert out["packing_changes_scientific_membership"] is False
    assert out["packing_changes_scientific_order"] is False
    assert out["restart_replays_or_skips_updates"] is False
    assert out["training_authorized"] is False


def test_repacking_cannot_move_presentation_between_scientific_updates():
    bad = packed(); bad[0][-1] = ["p3", "p4"]; bad[1][0] = ["p5"]
    with pytest.raises(RuntimeError, match="PACKING_CHANGED"):
        qualify_packing_restart_invariance(
            reference_updates=reference(), packed_updates=bad, restart_update_cursor=1,
            resumed_packed_updates=resumed(), authority=authority(),
        )


def test_repacking_cannot_reorder_within_scientific_update():
    bad = packed(); bad[0] = [["p1", "p0"], ["p2", "p3"]]
    with pytest.raises(RuntimeError, match="PACKING_CHANGED"):
        qualify_packing_restart_invariance(
            reference_updates=reference(), packed_updates=bad, restart_update_cursor=1,
            resumed_packed_updates=resumed(), authority=authority(),
        )


def test_restart_cannot_replay_previous_update():
    bad = [packed()[0], *resumed()]
    with pytest.raises(RuntimeError, match="RESTART_CURSOR_OR_SUFFIX_MISMATCH"):
        qualify_packing_restart_invariance(
            reference_updates=reference(), packed_updates=packed(), restart_update_cursor=1,
            resumed_packed_updates=bad, authority=authority(),
        )


def test_restart_cannot_skip_next_update():
    bad = [resumed()[-1]]
    with pytest.raises(RuntimeError, match="RESTART_CURSOR_OR_SUFFIX_MISMATCH"):
        qualify_packing_restart_invariance(
            reference_updates=reference(), packed_updates=packed(), restart_update_cursor=1,
            resumed_packed_updates=bad, authority=authority(),
        )


def test_rng_may_not_depend_on_packing_coordinates():
    wrong = tuple(x for x in FORBIDDEN_RNG_COORDINATES if x != "microbatch_ordinal")
    with pytest.raises(ValueError, match="canonical packing/device exclusion"):
        qualify_packing_restart_invariance(
            reference_updates=reference(), packed_updates=packed(), restart_update_cursor=1,
            resumed_packed_updates=resumed(), authority=authority(forbidden_rng_coordinates=wrong),
        )
