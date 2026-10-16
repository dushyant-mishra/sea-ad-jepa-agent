"""Test isolation for the explicitly process-local Task 3 revocation stopgap.

Production semantics intentionally keep revocations for the lifetime of one
qualification process. Synthetic tests repeatedly construct the same execution
identities, so each pytest test represents a fresh qualification process.
Within a test the anchor is never reset; fork/restart attacks therefore retain
the exact process-local behavior under review.
"""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import registry_v1 as registry


@pytest.fixture(autouse=True)
def _fresh_task3_process_revocation_anchor():
    registry._PROCESS_REVOCATION_ANCHOR.clear()
    try:
        yield
    finally:
        registry._PROCESS_REVOCATION_ANCHOR.clear()
