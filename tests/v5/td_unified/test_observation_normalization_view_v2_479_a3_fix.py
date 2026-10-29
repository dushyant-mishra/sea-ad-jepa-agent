"""A3-only exact-type dispatch regression for PR479. Synthetic fixture, no authority.

The immutable Macha #481 review tests remain the external acceptance criterion.
A1/A2 and inherited #474 A4 are not repaired by this change.
"""
import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError


class HostileMeta(type):
    calls = 0

    def __eq__(cls, other):
        HostileMeta.calls += 1
        raise RuntimeError("hostile payload metaclass executed")

    __hash__ = type.__hash__


class Hostile(metaclass=HostileMeta):
    pass


@pytest.mark.parametrize("payload", [
    Hostile(), [Hostile()], {"key": Hostile()},
])
def test_snapshot_rejects_payload_without_executing_metaclass(payload):
    HostileMeta.calls = 0
    with pytest.raises(QExcludedObservationError):
        V2._view_snapshot(payload)
    assert HostileMeta.calls == 0


def test_snapshot_preserves_exact_primitive_types():
    assert V2._view_snapshot({"s": "ok", "n": 3, "b": False, "z": None}) == {
        "s": "ok", "n": 3, "b": False, "z": None,
    }
