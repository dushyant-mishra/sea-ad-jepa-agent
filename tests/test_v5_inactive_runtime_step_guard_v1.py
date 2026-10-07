from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "src/sea_ad_jepa/v5"


def test_superseded_inactive_guard_no_longer_exists_as_active_source():
    """A single canonical mutation lock means the #221 donor guard is not executable source."""
    legacy = V5 / "inactive_runtime_step_guard_v1.py"
    assert not legacy.exists(), (
        "superseded #221 guard remains discoverable as active source; "
        "canonical runtime must have exactly one mutation guard"
    )


def test_canonical_consumer_has_no_direct_optimizer_or_ema_mutation():
    source = (V5 / "inactive_update_reference.py").read_text(encoding="utf-8")
    assert ".optimizer.step(" not in source
    forbidden_ema = (
        "teacher.mul_(m).add_(online,alpha=1.0-m)",
        "teacher.mul_(m).add_(online, alpha=1.0-m)",
    )
    assert not any(fragment in source for fragment in forbidden_ema)


def test_canonical_wrapper_uses_prefreeze_guard_and_guard_owned_ema():
    source = (V5 / "inactive_guarded_update_v1.py").read_text(encoding="utf-8")
    assert "PrefreezeOptimizerGuardV1" in source
    assert "guard.run_optimizer_step(token)" in source
    assert "guard.assert_step_complete(token)" in source
    assert "guard.run_ema(token, apply_ema)" in source
    assert "InactiveReferenceOptimizerStepGuardV1" not in source
