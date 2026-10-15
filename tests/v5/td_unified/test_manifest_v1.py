from __future__ import annotations

import hashlib
import importlib

import pytest


def _manifest_module():
    try:
        return importlib.import_module("scripts.v5.td_unified.manifest_v1")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Unified Task 2 manifest_v1 is not implemented yet: {exc}")


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
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    receipt = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("reader_validation", "BIOLOGICAL_VALUES"),),
    )
    with pytest.raises(m.ManifestError, match="validation|forbidden|access"):
        m.validate_producer_access(policy, receipt)


def test_reader_oracle_access_is_protected_until_later_authority_transition():
    m = _manifest_module()
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    receipt = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("reader_oracle", "CALIBRATION_STATISTICS"),),
    )
    with pytest.raises(m.ManifestError, match="oracle|forbidden|access"):
        m.validate_producer_access(policy, receipt)


def test_producer_receipt_must_enumerate_actual_partitions_and_access_classes():
    m = _manifest_module()
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    lawful = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("reader_fit", "BIOLOGICAL_VALUES"),),
    )
    assert m.validate_producer_access(policy, lawful) is None
    forged = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("reader_fit", "UNKNOWN_CLASS"),),
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, forged)


def test_numeric_success_with_forbidden_partition_access_is_invalid():
    m = _manifest_module()
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    receipt = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("reader_validation", "BIOLOGICAL_VALUES"),),
        numeric_result_digest="0" * 64,
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, receipt)


def test_manifest_binds_exact_objects_not_branch_or_pr_labels():
    m = _manifest_module()
    resolver_map = {
        "a" * 64: {"object_role": "REGISTRY", "version": 1},
        "b" * 64: {"object_role": "MANIFEST", "version": 1},
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
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    receipt = m.ProducerAccessReceipt(
        producer_id="G8",
        observed_access=(("mystery_partition", "METADATA"),),
    )
    with pytest.raises(m.ManifestError):
        m.validate_producer_access(policy, receipt)
