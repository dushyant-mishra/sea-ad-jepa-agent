from pathlib import Path


RUNTIME = Path("src/sea_ad_jepa/v5/inactive_update_reference.py")
ALTERNATE_REHEARSAL = Path("src/sea_ad_jepa/v5/prefreeze_guarded_rehearsal.py")


def test_canonical_consumer_does_not_mutate_teacher_ema_directly():
    """EMA must be owned by the mutation guard, not the V5 consumer body."""
    source = RUNTIME.read_text(encoding="utf-8")
    forbidden = (
        "teacher.mul_(m).add_(online,alpha=1.0-m)",
        "teacher.mul_(m).add_(online, alpha=1.0-m)",
    )
    assert not any(fragment in source for fragment in forbidden), (
        "inactive_update_reference.py still has a directly reachable EMA mutation path; "
        "the canonical successor must route EMA through the guarded completion boundary"
    )


def test_canonical_successor_has_no_alternate_generic_rehearsal_runtime():
    assert not ALTERNATE_REHEARSAL.exists(), (
        "prefreeze_guarded_rehearsal.py remains as a second executable mutation/checkpoint path; "
        "the canonical successor must expose only the actual V5 guarded consumer"
    )
