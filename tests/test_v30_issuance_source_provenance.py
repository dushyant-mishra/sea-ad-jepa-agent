"""V30 synthetic negative control: SHA integrity is not source provenance.

No reader_fit expression, no GPU, no actual teacher, and NO production issuance.
Demonstrates whether the final issuance API accepts a *self-consistent invented*
closure mapping without executing the real graph validator.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from sea_ad_jepa.v5.current_authority_roots_v2 import (
    CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2,
)
from sea_ad_jepa.v5.current_teacher_target_receipt_v2 import (
    seal_current_teacher_target_receipt_v2,
)
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v2 import (
    CurrentTrainerPreexecutionAuthorityV2,
)
from sea_ad_jepa.v5.current_training_authority_v1 import issue_training_authority_v1
from sea_ad_jepa.v5.current_runtime_source_authority_v1 import (
    CurrentRuntimeSourceAuthorityV1,
)


def digest(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def canonical_digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


class SyntheticCritical:
    """Only implements the issuer's actual dynamic interface, not real evidence."""
    training_authorized = False

    def validate(self):
        pass

    def canonical_digest(self):
        return digest("UNVERIFIED_SCIENTIFIC_CRITICAL_TEST")


def synthetic_runtime():
    return CurrentRuntimeSourceAuthorityV1(
        authority_id="SYNTHETIC_ONLY_NEVER_APPROVED",
        source_manifest_sha256=digest("unverified-source-manifest"),
        source_root_sha256=digest("unverified-source-root"),
        runtime_environment_artifact_sha256=digest("unverified-environment"),
        entrypoint_source_sha256=digest("unverified-entrypoint"),
        source_packaging_policy_id="MULTIFILE_SOURCE_MANIFEST_AND_ROOT_V1",
        entrypoint_policy_id="CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1",
        runtime_abi_id="CPYTHON_RUNTIME_ABI_EXACTLY_RECORDED_V1",
    )


def fabricated_envelope():
    critical = SyntheticCritical()
    runtime = synthetic_runtime()
    # No actual representation/support/masking/teacher/schedule/geometry objects
    # exist. Each digest is an invented, syntactically valid SHA value.
    roots = {
        role: digest("V30_NO_PARENT_BYTES_" + role)
        for role in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
    }
    roots["critical_test_authority_sha256"] = critical.canonical_digest()
    roots["runtime_source_authority_sha256"] = runtime.canonical_digest()
    closure_core = {
        "schema": "V5_CURRENT_AUTHORITY_CLOSURE_V2",
        "authority_roots": roots,
        "training_authorized": False,
    }
    closure = {**closure_core, "closure_digest": canonical_digest(closure_core)}
    pre = CurrentTrainerPreexecutionAuthorityV2(
        authority_roots=roots,
        closure_v2_sha256=closure["closure_digest"],
        protected_registry_authority_sha256=roots["protected_registry_authority_sha256"],
        critical_test_authority_sha256=roots["critical_test_authority_sha256"],
        relational_training_active=False,
        optimizer_started=False,
    )
    receipt_roots = {**roots, "preexecution_authority_sha256": pre.canonical_digest()}
    target_package_root = digest("V30_NOT_A_REAL_TEACHER_TARGET")
    receipt = seal_current_teacher_target_receipt_v2(
        target_package_root=target_package_root,
        authority_roots=receipt_roots,
        closure_v2_sha256=closure["closure_digest"],
    )
    return critical, runtime, closure, pre, receipt, target_package_root


def test_synthetic_envelope_accepted_without_live_closure_validation():
    critical, runtime, closure, pre, receipt, target = fabricated_envelope()
    # This test calls the *real* issuer but NEVER runs the actual closure graph
    # validator, never builds a teacher, and never invokes an optimizer.
    issued = issue_training_authority_v1(
        closure_v2=closure,
        preexecution=pre,
        receipt_v2=receipt,
        expected_target_package_root=target,
        critical_test=critical,
        runtime_source=runtime,
    )
    assert issued.training_authorized is True
    assert issued.closure_v2_sha256 == closure["closure_digest"]
    assert issued.target_package_root == target
    # Reaching here proves an issuance-source provenance gap, NOT actual B1
    # population permission or successful execution.
    print("V30_FINDING_SELF_CONSISTENT_INVENTED_CLOSURE_ACCEPTED__B1_STILL_OFF")


def test_mutated_hash_is_still_rejected_positive_safety_control():
    critical, runtime, closure, pre, receipt, target = fabricated_envelope()
    bad = copy.deepcopy(receipt)
    bad["receipt_digest"] = digest("corrupted-receipt")
    with pytest.raises(ValueError, match="receipt digest mismatch"):
        issue_training_authority_v1(
            closure_v2=closure, preexecution=pre, receipt_v2=bad,
            expected_target_package_root=target,
            critical_test=critical, runtime_source=runtime,
        )


def test_inconsistent_closure_digest_is_rejected_positive_safety_control():
    critical, runtime, closure, pre, receipt, target = fabricated_envelope()
    bad = copy.deepcopy(closure)
    bad["closure_digest"] = digest("corrupted-closure")
    with pytest.raises(ValueError, match="closure_v2 digest"):
        issue_training_authority_v1(
            closure_v2=bad, preexecution=pre, receipt_v2=receipt,
            expected_target_package_root=target,
            critical_test=critical, runtime_source=runtime,
        )
