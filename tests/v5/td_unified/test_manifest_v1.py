from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "td_execution_manifest_v1.json"
POLICY_SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "population_access_policy_v1.json"
ACCESS_RECEIPT_SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "producer_access_receipt_v1.json"


def _manifest_module():
    try:
        return importlib.import_module("scripts.v5.td_unified.manifest_v1")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Unified Task 2 manifest_v1 is not implemented yet: {exc}")


def _small_policy(m):
    donors = ["D1", "D2", "D3", "D4", "D5"]
    return m.build_current_td_access_policy(
        fit_donors=donors,
        donor_source={d: "S1" for d in donors},
    )


def _access_receipt(m, policy, *, producer_id="G8", observed_access, numeric_result_digest=None):
    return m.ProducerAccessReceipt(
        producer_id=producer_id,
        access_policy_sha=policy.canonical_sha256(),
        observed_access=observed_access,
        numeric_result_digest=numeric_result_digest,
    )


def test_current_td_policy_crossfits_only_within_reader_fit():
    m = _manifest_module()
    policy = m.build_current_td_access_policy(
        fit_donors=[f"D{i:03d}" for i in range(104)],
        donor_source={f"D{i:03d}": f"S{i % 3}" for i in range(104)},
    )
    assert policy.fold_count == 5
    assert set(policy.allowed_outcome_partitions) == {"reader_fit"}
    all_held_out = []
    for fold in policy.crossfit_folds:
        train = set(fold.train_donors)
        held = set(fold.held_out_donors)
        assert train.isdisjoint(held)
        all_held_out.extend(fold.held_out_donors)
    assert sorted(all_held_out) == [f"D{i:03d}" for i in range(104)]


def test_crossfit_assignment_is_deterministic_and_outcome_blind():
    m = _manifest_module()
    donors = [f"D{i:03d}" for i in range(104)]
    sources = {d: f"S{int(d[1:]) % 3}" for d in donors}
    p1 = m.build_current_td_access_policy(fit_donors=donors, donor_source=sources)
    p2 = m.build_current_td_access_policy(fit_donors=list(reversed(donors)), donor_source=sources)
    assert p1 == p2


def test_reader_validation_access_cannot_rescue_estimability():
    m = _manifest_module()
    policy = _small_policy(m)
    receipt = _access_receipt(
        m,
        policy,
        observed_access=(("reader_validation", "BIOLOGICAL_VALUES"),),
    )
    with pytest.raises(m.ManifestError, match="validation|forbidden|access"):
        m.validate_producer_access(policy, receipt)


def test_reader_oracle_access_is_protected_until_later_authority_transition():
    m = _manifest_module()
    policy = _small_policy(m)
    receipt = _access_receipt(
        m,
        policy,
        observed_access=(("reader_oracle", "CALIBRATION_STATISTICS"),),
    )
    with pytest.raises(m.ManifestError, match="oracle|forbidden|access"):
        m.validate_producer_access(policy, receipt)


def test_producer_receipt_must_enumerate_actual_partitions_and_access_classes():
    m = _manifest_module()
    policy = _small_policy(m)
    lawful = _access_receipt(
        m,
        policy,
        observed_access=(("reader_fit", "BIOLOGICAL_VALUES"),),
    )
    assert m.validate_producer_access(policy, lawful) is None
    forged = _access_receipt(
        m,
        policy,
        observed_access=(("reader_fit", "UNKNOWN_CLASS"),),
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, forged)


def test_numeric_success_with_forbidden_partition_access_is_invalid():
    m = _manifest_module()
    policy = _small_policy(m)
    receipt = _access_receipt(
        m,
        policy,
        observed_access=(("reader_validation", "BIOLOGICAL_VALUES"),),
        numeric_result_digest="0" * 64,
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, receipt)


def test_manifest_binds_exact_objects_not_branch_or_pr_labels():
    m = _manifest_module()
    resolver_map = {
        "a" * 64: {"object_role": "REGISTRY", "version": 1},
        "b" * 64: {"object_role": "ACCESS_POLICY", "version": 1},
    }
    with pytest.raises(m.ManifestError):
        m.validate_manifest(
            {
                "schema": "TD_EXECUTION_MANIFEST_V1",
                "registry_sha": "PR #349",
                "access_policy_sha": "b" * 64,
            },
            resolver_map.get,
        )


def test_manifest_digest_rejects_mutated_policy_bytes():
    m = _manifest_module()
    policy = {"object_role": "ACCESS_POLICY", "version": 1, "fold_count": 5}
    from scripts.v5.td_unified.canonical_v1 import canonical_sha256

    claimed = canonical_sha256(policy)
    mutated = {"object_role": "ACCESS_POLICY", "version": 1, "fold_count": 4}
    with pytest.raises(m.ManifestError, match="digest|identity|policy"):
        m.verify_manifest_dependency(claimed, mutated, expected_role="ACCESS_POLICY")


def test_raw_file_sha256_is_recomputed_from_actual_bytes():
    m = _manifest_module()
    raw = b"exact raw bytes\x00\n"
    claimed = hashlib.sha256(raw).hexdigest()
    assert m.verify_raw_file_sha256(claimed, raw) is None
    with pytest.raises(m.ManifestError, match="raw|sha|digest"):
        m.verify_raw_file_sha256(claimed, raw + b"mutated")
    with pytest.raises(m.ManifestError):
        m.verify_raw_file_sha256(claimed, "not bytes")


def test_unknown_partition_fails_closed():
    m = _manifest_module()
    policy = _small_policy(m)
    receipt = _access_receipt(
        m,
        policy,
        observed_access=(("mystery_partition", "METADATA"),),
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, receipt)


# Hostile self-audit cycle 1 -------------------------------------------------

def test_access_receipt_binds_exact_access_policy_identity():
    m = _manifest_module()
    params = inspect.signature(m.ProducerAccessReceipt).parameters
    assert "access_policy_sha" in params
    policy = _small_policy(m)
    policy_sha = policy.canonical_sha256()
    lawful = m.ProducerAccessReceipt(
        producer_id="G8",
        access_policy_sha=policy_sha,
        observed_access=(("reader_fit", "BIOLOGICAL_VALUES"),),
    )
    assert m.validate_producer_access(policy, lawful) is None
    wrong = m.ProducerAccessReceipt(
        producer_id="G8",
        access_policy_sha="0" * 64,
        observed_access=(("reader_fit", "BIOLOGICAL_VALUES"),),
    )
    with pytest.raises(m.ManifestError, match="policy|identity|digest"):
        m.validate_producer_access(policy, wrong)


def test_crossfit_policy_binds_the_exact_assignment_inputs():
    m = _manifest_module()
    policy = _small_policy(m)
    assert isinstance(policy.assignment_basis_sha, str)
    assert len(policy.assignment_basis_sha) == 64
    payload = policy.to_payload()
    assert payload["assignment_basis_sha"] == policy.assignment_basis_sha
    assert payload["fold_count"] == 5
    assert len(payload["crossfit_folds"]) == 5


def test_manifest_schema_requires_the_full_task2_dependency_surface():
    schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    required_dependencies = {
        "registry_sha",
        "observation_contract_sha",
        "support_contract_sha",
        "controller_code_sha",
        "controller_policy_sha",
        "candidate_registry_sha",
        "endpoint_registry_sha",
        "source_registry_sha",
        "qualification_registry_sha",
        "population_split_registry_sha",
        "access_policy_sha",
        "reader_fit_policy_sha",
        "reader_validation_policy_sha",
        "reader_oracle_policy_sha",
        "crossfit_policy_sha",
        "protected_partition_policy_sha",
    }
    assert required_dependencies <= set(schema["required"])
    assert required_dependencies <= set(schema["properties"])
    assert schema["additionalProperties"] is False


def test_population_access_schema_closes_fold_structure_and_assignment_identity():
    schema = json.loads(POLICY_SCHEMA.read_text(encoding="utf-8"))
    assert "assignment_basis_sha" in schema["required"]
    assert "assignment_basis_sha" in schema["properties"]
    folds = schema["properties"]["crossfit_folds"]
    assert folds["items"]["additionalProperties"] is False
    assert set(folds["items"]["required"]) == {"fold_index", "train_donors", "held_out_donors"}


# Hostile self-audit cycle 2 -------------------------------------------------

def test_policy_inlines_assignment_basis_so_its_digest_is_not_a_trusted_string():
    m = _manifest_module()
    policy = _small_policy(m)
    payload = policy.to_payload()
    assert "assignment_basis" in payload
    from scripts.v5.td_unified.canonical_v1 import canonical_sha256

    assert canonical_sha256(payload["assignment_basis"]) == payload["assignment_basis_sha"]


def test_protected_partitions_allow_partition_identity_only_not_generic_metadata():
    m = _manifest_module()
    policy = _small_policy(m)
    receipt = _access_receipt(
        m,
        policy,
        observed_access=(("reader_validation", "METADATA"),),
    )
    with pytest.raises(m.ManifestError, match="validation|protected|forbidden"):
        m.validate_producer_access(policy, receipt)


def test_observed_access_binds_fold_phase_and_donor_ids_to_block_fit_leakage():
    m = _manifest_module()
    assert hasattr(m, "ObservedAccess")
    policy = _small_policy(m)
    fold = policy.crossfit_folds[0]
    held_out = fold.held_out_donors[0]
    lawful = m.ProducerAccessReceipt(
        producer_id="G8",
        access_policy_sha=policy.canonical_sha256(),
        observed_access=(
            m.ObservedAccess(
                partition="reader_fit",
                access_class="BIOLOGICAL_VALUES",
                fold_index=0,
                phase="TRAIN",
                donor_ids=(fold.train_donors[0],),
            ),
        ),
    )
    assert m.validate_producer_access(policy, lawful) is None
    leaked = m.ProducerAccessReceipt(
        producer_id="G8",
        access_policy_sha=policy.canonical_sha256(),
        observed_access=(
            m.ObservedAccess(
                partition="reader_fit",
                access_class="BIOLOGICAL_VALUES",
                fold_index=0,
                phase="TRAIN",
                donor_ids=(held_out,),
            ),
        ),
    )
    with pytest.raises(m.ManifestError, match="held|leak|train|donor"):
        m.validate_producer_access(policy, leaked)


def test_access_policy_role_tag_alone_cannot_pass_structural_validation():
    m = _manifest_module()
    assert hasattr(m, "validate_population_access_policy_payload")
    bad = {
        "object_role": "ACCESS_POLICY",
        "policy_schema": "POPULATION_ACCESS_POLICY_V1",
        "assignment_basis_sha": "0" * 64,
        "fold_count": 4,
        "crossfit_folds": [],
        "allowed_outcome_partitions": ["reader_fit"],
        "protected_partitions": ["reader_validation", "reader_oracle"],
    }
    with pytest.raises(m.ManifestError):
        m.validate_population_access_policy_payload(bad)


def test_producer_access_receipt_has_closed_machine_schema():
    assert ACCESS_RECEIPT_SCHEMA.exists()
    schema = json.loads(ACCESS_RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) >= {"receipt_schema", "producer_id", "access_policy_sha", "observed_access"}
    event = schema["properties"]["observed_access"]["items"]
    assert event["additionalProperties"] is False
    assert set(event["required"]) == {"partition", "access_class", "fold_index", "phase", "donor_ids"}
