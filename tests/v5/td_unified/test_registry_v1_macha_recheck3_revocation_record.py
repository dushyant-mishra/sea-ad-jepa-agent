"""Focused B5-F regression: every revocation must hit the process-local anchor."""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import registry_v1 as r
from tests.v5.td_unified.test_registry_v1_macha_recheck3 import _genesis, _revoke


def test_b5_f_low_stage_revocation_without_custody_is_still_anchored():
    registry, controller, _, objects = _genesis("F5")

    # A low-stage, history-free revocation may still be executed without a
    # custody object under the labelled R4 stopgap. It must nevertheless be
    # remembered for the lifetime of this qualification process.
    _revoke(registry, "F5_G8", controller, objects)

    with pytest.raises(r.RegistryError, match="revok|anchor|custody|history"):
        r.RegistryHistoryCustody(registry, attestation_key=b"fresh")
