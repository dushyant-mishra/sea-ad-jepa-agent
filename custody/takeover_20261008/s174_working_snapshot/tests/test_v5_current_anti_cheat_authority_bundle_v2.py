from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.anti_cheat_authority_bundle_v2 import AntiCheatAuthorityBundleV2


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2",
        target_identity_gate_authority_sha256=h("identity"),
        masking_authority_sha256=h("masking"),
        masking_qualification_execution_authority_sha256=h("masking-execution"),
        remaining_rna_execution_authority_sha256=h("remaining-rna-execution"),
        measurement_robustness_authority_sha256=h("measurement"),
        observation_gradient_firewall_authority_sha256=h("firewall"),
        critical_test_authority_sha256=h("critical"),
    )
    values.update(updates)
    return AntiCheatAuthorityBundleV2(**values)


class Stub:
    training_authorized = False
    def __init__(self, digest: str, *, passed: bool = True):
        self._digest = digest
        self.passed = passed
    def validate(self): return None
    def canonical_digest(self): return self._digest


def test_valid_v2_bundle_is_deterministic_and_hash_bound() -> None:
    a = authority()
    a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_all_anti_cheat_roles_must_be_distinct() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(
            masking_qualification_execution_authority_sha256=same,
            remaining_rna_execution_authority_sha256=same,
        ).validate()


def test_execution_evidence_must_be_live_bound_and_passed() -> None:
    a = authority()
    a.bind_execution_evidence(
        masking_qualification_execution=Stub(a.masking_qualification_execution_authority_sha256, passed=True),
        remaining_rna_execution=Stub(a.remaining_rna_execution_authority_sha256, passed=True),
    )
    with pytest.raises(ValueError, match="masking qualification execution must be EXECUTED_PASS"):
        a.bind_execution_evidence(
            masking_qualification_execution=Stub(a.masking_qualification_execution_authority_sha256, passed=False),
            remaining_rna_execution=Stub(a.remaining_rna_execution_authority_sha256, passed=True),
        )
    with pytest.raises(ValueError, match="remaining-RNA execution must be EXECUTED_PASS"):
        a.bind_execution_evidence(
            masking_qualification_execution=Stub(a.masking_qualification_execution_authority_sha256, passed=True),
            remaining_rna_execution=Stub(a.remaining_rna_execution_authority_sha256, passed=False),
        )


def test_execution_role_splicing_is_rejected() -> None:
    a = authority()
    with pytest.raises(ValueError, match="masking qualification execution authority root mismatch"):
        a.bind_execution_evidence(
            masking_qualification_execution=Stub(h("wrong-mask-execution"), passed=True),
            remaining_rna_execution=Stub(a.remaining_rna_execution_authority_sha256, passed=True),
        )
    with pytest.raises(ValueError, match="remaining-RNA execution authority root mismatch"):
        a.bind_execution_evidence(
            masking_qualification_execution=Stub(a.masking_qualification_execution_authority_sha256, passed=True),
            remaining_rna_execution=Stub(h("wrong-rna-execution"), passed=True),
        )


def test_v2_bundle_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
