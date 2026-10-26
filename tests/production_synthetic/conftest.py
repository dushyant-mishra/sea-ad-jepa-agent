"""Test isolation for the process-local realism custody in calibration_v1.

Each pytest test is an independent synthetic qualification process, so realism
family leases and issued states are reset only at test boundaries. Within a test
they are never reset, so reset/replay/re-contract attacks keep exact behavior.
"""
from __future__ import annotations

import pytest

from scripts.production_synthetic import calibration_v1 as calibration


def _clear():
    calibration._REALISM_FAMILY_LEASES.clear()
    calibration._REALISM_PUBLIC.clear()
    calibration._REALISM_PRIVATE.clear()


@pytest.fixture(autouse=True)
def _fresh_realism_process():
    _clear()
    try:
        yield
    finally:
        _clear()
