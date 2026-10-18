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
from scripts.v5.td_unified import challenge_custody_v1 as task4


@pytest.fixture(autouse=True)
def _fresh_task3_process_revocation_anchor():
    registry._PROCESS_REVOCATION_ANCHOR.clear()
    # Each pytest test is an independent synthetic qualification process.
    # Keep Task 4 identity leases intact *within* each test so duplicate
    # campaign remint attempts still fail; reset only at test boundaries.
    task4._CAMPAIGN_IDENTITY_LEASES.clear()
    try:
        yield
    finally:
        registry._PROCESS_REVOCATION_ANCHOR.clear()
        task4._CAMPAIGN_IDENTITY_LEASES.clear()
