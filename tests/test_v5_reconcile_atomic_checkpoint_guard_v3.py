from __future__ import annotations


def test_current_authority_atomic_checkpoint_guard_exists():
    from sea_ad_jepa.v5.atomic_checkpoint_guard_v3 import (  # noqa: F401
        validate_atomic_checkpoint_transition_v3,
    )
