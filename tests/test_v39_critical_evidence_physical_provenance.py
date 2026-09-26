"""V39 non-authorizing red-team of the *real* V1 critical-test evidence class.

This does NOT simulate source-byte access or imply final graph closure. It
demonstrates that a caller-declared EXECUTED_PASS and synthetic SHA are allowed
by the current typed data class, and tests positive rejection controls.
"""
from __future__ import annotations

import hashlib
import pytest

from sea_ad_jepa.v5.critical_test_execution_authority_v1 import (
    CriticalTestExecutionAuthorityV1,
)
from sea_ad_jepa.v5.current_authority_closure_v2 import _auth


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def phantom(*, ids=("NEVER_EXECUTED_TEST",), statuses=None, source_sha=None):
    return CriticalTestExecutionAuthorityV1(
        authority_id="SYNTHETIC_TEST_FIXTURE_NO_CI",
        required_test_ids=ids,
        test_suite_source_sha256=source_sha or h("NEVER_READ_ANY_SOURCE_BYTES"),
        status_by_test=statuses or {name: "EXECUTED_PASS" for name in ids},
    )


def test_phantom_typed_critical_test_claim_is_locally_accepted():
    value = phantom()
    value.validate()
    assert value.normalized_status() == {"NEVER_EXECUTED_TEST": "EXECUTED_PASS"}
    assert len(value.canonical_digest()) == 64
    assert value.training_authorized is False
    print("V39_PHANTOM_EXECUTED_PASS_ACCEPTED_BY_CURRENT_TYPED_CLASS__NOT_B2")


def test_caller_selects_required_test_vocabulary_without_independent_manifest():
    hypothetical_full_scope = {"REQUIRED_A", "REQUIRED_B"}
    value = phantom(ids=("REQUIRED_A",))
    value.validate()
    assert hypothetical_full_scope - set(value.normalized_required()) == {"REQUIRED_B"}
    # This is a schema property, NOT evidence that project's actual fixed test
    # manifest includes REQUIRED_A or REQUIRED_B.


def test_source_sha_is_accepted_without_reading_any_original_source():
    bogus_source = h("NOT_A_REAL_VERIFIED_SOURCE_FILE")
    value = phantom(source_sha=bogus_source)
    value.validate()
    assert value.test_suite_source_sha256 == bogus_source
    assert value.canonical_digest() != phantom(
        source_sha=h("DIFFERENT_UNREAD_SOURCE")
    ).canonical_digest()


def test_closure_digest_helper_accepts_duck_typed_unverified_critical_object():
    class DuckCritical:
        training_authorized = False
        def validate(self):
            return None
        def canonical_digest(self):
            return h("NEVER_RAN_SUITE")
    assert _auth(DuckCritical(), "critical test") == h("NEVER_RAN_SUITE")
    # Does NOT test full V2 closure: other exact typed upstream roles are missing.


def test_nonpassing_status_still_fails_as_intended():
    value = phantom(statuses={"NEVER_EXECUTED_TEST": "FAILED"})
    with pytest.raises(ValueError, match="EXECUTED_PASS"):
        value.validate()


def test_missing_test_status_still_fails_as_intended():
    value = phantom(
        ids=("NEVER_EXECUTED_TEST", "ANOTHER_TEST"),
        statuses={"NEVER_EXECUTED_TEST": "EXECUTED_PASS"},
    )
    with pytest.raises(ValueError, match="exactly match"):
        value.validate()


def test_malformed_source_hash_still_fails_as_intended():
    value = phantom(source_sha="not-a-digest")
    with pytest.raises(ValueError, match="SHA-256"):
        value.validate()
