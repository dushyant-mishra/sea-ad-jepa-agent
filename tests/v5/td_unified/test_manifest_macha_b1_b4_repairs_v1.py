from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified import manifest_v1 as m
from scripts.v5.td_unified.canonical_v1 import canonical_sha256


def _reader_split() -> bytes:
    rows = ["donor_id,reader_partition"]
    rows += [f"F{i:03d},reader_fit" for i in range(104)]
    rows += [f"V{i:03d},reader_validation" for i in range(22)]
    rows += [f"O{i:03d},reader_oracle" for i in range(23)]
    return ("\n".join(rows) + "\n").encode()


def _authoritative_policy(monkeypatch):
    raw = _reader_split()
    sha = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(m, "FROZEN_READER_SPLIT_SHA256", sha)
    policy = m.build_current_td_access_policy_from_reader_split(reader_split_raw=raw)
    return raw, sha, policy


def test_t2_b1_authority_re_resolves_split_bytes_and_recomputes_donors(monkeypatch):
    raw, sha, real = _authoritative_policy(monkeypatch)
    fake = sorted(f"FAKE_{i:03d}" for i in range(104))
    basis = {
        "fit_donors": fake,
        "fold_count": 5,
        "assignment_law": m.CURRENT_TD_ASSIGNMENT_LAW,
        "reader_split_raw_sha256": sha,
        "population_registry_sha256": m.FROZEN_POPULATION_REGISTRY_SHA256,
    }
    folds = tuple(
        m.CrossFitFold(k, tuple(d for d in fake if d not in fake[k::5]), tuple(fake[k::5]))
        for k in range(5)
    )
    forged = m.PopulationAccessPolicy(
        "ACCESS_POLICY", "POPULATION_ACCESS_POLICY_V1", "AUTHENTICATED_READER_SPLIT",
        sha, m.FROZEN_POPULATION_REGISTRY_SHA256, basis, canonical_sha256(basis), 5,
        folds, ("reader_fit",), ("reader_validation", "reader_oracle"),
    )
    resolver = {sha: raw}.get
    with pytest.raises(m.ManifestError, match="donor|split|fold|authority"):
        m.require_current_td_population_authority(forged, raw_resolver=resolver)
    with pytest.raises(m.ManifestError, match="donor|split|fold|authority"):
        m.validate_population_access_policy_payload(forged.to_payload(), raw_resolver=resolver)


def test_t2_b1_authority_recomputes_exact_folds_not_just_partition_validity(monkeypatch):
    raw, sha, real = _authoritative_policy(monkeypatch)
    donors = real.assignment_basis["fit_donors"]
    wrong = tuple(
        m.CrossFitFold(k, tuple(d for d in donors if d not in donors[k::5]), tuple(donors[k::5]))
        for k in range(5)
    )
    altered = m.PopulationAccessPolicy(
        real.object_role, real.policy_schema, real.population_authority,
        real.reader_split_raw_sha256, real.population_registry_sha256,
        dict(real.assignment_basis), real.assignment_basis_sha, real.fold_count,
        wrong, real.allowed_outcome_partitions, real.protected_partitions,
    )
    with pytest.raises(m.ManifestError, match="fold|assignment|law"):
        m.require_current_td_population_authority(altered, raw_resolver={sha: raw}.get)


def test_t2_b2_handmade_ledger_is_not_harness_attested(monkeypatch):
    raw, sha, policy = _authoritative_policy(monkeypatch)
    assert hasattr(m, "HarnessAccessRegistry")
    registry = m.HarnessAccessRegistry(attestation_key=b"task2-test-harness-key")
    fold = policy.crossfit_folds[0]
    event = m.ObservedAccess("reader_fit", "BIOLOGICAL_VALUES", 0, "EVAL", fold.held_out_donors[:1])
    ledger = {
        "object_role": "OBSERVED_ACCESS_LEDGER", "ledger_schema": "OBSERVED_ACCESS_LEDGER_V1",
        "producer_id": "evil", "access_policy_sha": policy.canonical_sha256(),
        "observed_access": [event.to_payload()],
    }
    receipt = m.ProducerAccessReceipt("evil", policy.canonical_sha256(), canonical_sha256(ledger), (event,))
    with pytest.raises(m.ManifestError, match="harness|session|attest|issued"):
        m.validate_producer_access(policy, receipt, session_registry=registry)


def test_t2_b3_redundant_subpolicies_must_equal_access_policy_derivations(monkeypatch):
    raw, sha, policy = _authoritative_policy(monkeypatch)
    assert hasattr(m, "derive_crossfit_policy_payload")
    assert hasattr(m, "derive_protected_partition_policy_payload")
    assert hasattr(m, "derive_reader_partition_policy_payload")
    good = m.derive_protected_partition_policy_payload(policy)
    bad = dict(good)
    bad["reader_validation_access_classes"] = ["BIOLOGICAL_VALUES"]
    with pytest.raises(m.ManifestError, match="sub-policy|protected|consisten|derive"):
        m.validate_manifest_subpolicy_consistency(
            access_policy=policy.to_payload(),
            crossfit_policy=m.derive_crossfit_policy_payload(policy),
            protected_partition_policy=bad,
            reader_fit_policy=m.derive_reader_partition_policy_payload(policy, "reader_fit"),
            reader_validation_policy=m.derive_reader_partition_policy_payload(policy, "reader_validation"),
            reader_oracle_policy=m.derive_reader_partition_policy_payload(policy, "reader_oracle"),
            raw_resolver={sha: raw}.get,
        )


def test_t2_b4_manifest_explicitly_binds_missing_contract_identity_surface():
    required = {
        "normalization_library_contract_sha": "NORMALIZATION_LIBRARY_CONTRACT",
        "target_portfolio_code_identity_sha": "TARGET_PORTFOLIO_CODE_IDENTITY",
        "target_portfolio_policy_sha": "TARGET_PORTFOLIO_POLICY",
        "unit_execution_identity_table_sha": "UNIT_EXECUTION_IDENTITY_TABLE",
    }
    for field, role in required.items():
        assert m._MANIFEST_ROLE_BY_FIELD.get(field) == role
    assert hasattr(m, "validate_unit_execution_identity_table")
