from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from scripts.v5.td_unified import manifest_v1 as m
from scripts.v5.td_unified.canonical_v1 import canonical_sha256

ROOT = Path(__file__).resolve().parents[3]
LEDGER_SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "observed_access_ledger_v1.json"


def _policy():
    donors = ["D1", "D2", "D3", "D4", "D5"]
    return m.build_current_td_access_policy(
        fit_donors=donors,
        donor_source={d: "S1" for d in donors},
    )


def test_access_session_generates_ledger_from_actual_reads_and_receipt_binds_it():
    assert hasattr(m, "PopulationAccessSession")
    policy = _policy()
    fold = policy.crossfit_folds[0]
    donor = fold.train_donors[0]
    values = {d: {"value": index} for index, d in enumerate(policy.assignment_basis["fit_donors"])}
    session = m.PopulationAccessSession(policy=policy, producer_id="G8", reader_fit_values=values)

    result = session.read_fit(
        fold_index=0,
        phase="TRAIN",
        donor_ids=(donor,),
        access_class="BIOLOGICAL_VALUES",
    )
    assert result == (values[donor],)

    receipt, ledger = session.finalize()
    assert receipt.access_ledger_sha == canonical_sha256(ledger)
    assert ledger["object_role"] == "OBSERVED_ACCESS_LEDGER"
    assert ledger["producer_id"] == "G8"
    assert ledger["access_policy_sha"] == policy.canonical_sha256()
    assert ledger["observed_access"][0]["donor_ids"] == [donor]
    assert m.validate_producer_access(policy, receipt, ledger_resolver={receipt.access_ledger_sha: ledger}.get) is None


def test_hand_authored_receipt_cannot_claim_actual_observed_access_without_ledger():
    params = inspect.signature(m.ProducerAccessReceipt).parameters
    assert "access_ledger_sha" in params
    policy = _policy()
    fold = policy.crossfit_folds[0]
    event = m.ObservedAccess("reader_fit", "BIOLOGICAL_VALUES", 0, "TRAIN", (fold.train_donors[0],))
    receipt = m.ProducerAccessReceipt(
        producer_id="G8",
        access_policy_sha=policy.canonical_sha256(),
        access_ledger_sha="0" * 64,
        observed_access=(event,),
    )
    with pytest.raises(m.ManifestError, match="ledger|observed|access"):
        m.validate_producer_access(policy, receipt, ledger_resolver=lambda _: None)


def test_access_ledger_must_match_receipt_events_exactly():
    policy = _policy()
    fold = policy.crossfit_folds[0]
    donor = fold.train_donors[0]
    values = {d: d for d in policy.assignment_basis["fit_donors"]}
    session = m.PopulationAccessSession(policy=policy, producer_id="G8", reader_fit_values=values)
    session.read_fit(0, "TRAIN", (donor,), "BIOLOGICAL_VALUES")
    receipt, ledger = session.finalize()

    mutated = dict(ledger)
    mutated["observed_access"] = []
    with pytest.raises(m.ManifestError, match="ledger|digest|events|observed"):
        m.validate_producer_access(
            policy,
            receipt,
            ledger_resolver={receipt.access_ledger_sha: mutated}.get,
        )


def test_forbidden_read_invalidates_session_before_data_can_be_used():
    policy = _policy()
    fold = policy.crossfit_folds[0]
    held = fold.held_out_donors[0]
    values = {d: d for d in policy.assignment_basis["fit_donors"]}
    session = m.PopulationAccessSession(policy=policy, producer_id="G8", reader_fit_values=values)
    with pytest.raises(m.ManifestError, match="held|leak|forbidden|train"):
        session.read_fit(0, "TRAIN", (held,), "BIOLOGICAL_VALUES")
    with pytest.raises(m.ManifestError, match="invalid|forbidden|session"):
        session.finalize()


def test_protected_partition_interface_exposes_identity_not_values():
    policy = _policy()
    values = {d: d for d in policy.assignment_basis["fit_donors"]}
    session = m.PopulationAccessSession(policy=policy, producer_id="G8", reader_fit_values=values)
    assert not hasattr(session, "read_reader_validation_values")
    assert not hasattr(session, "read_reader_oracle_values")
    session.observe_protected_partition_identity("reader_validation")
    receipt, ledger = session.finalize()
    event = ledger["observed_access"][0]
    assert event == {
        "partition": "reader_validation",
        "access_class": "PARTITION_IDENTITY",
        "fold_index": None,
        "phase": "CUSTODY",
        "donor_ids": [],
    }
    assert m.validate_producer_access(policy, receipt, ledger_resolver={receipt.access_ledger_sha: ledger}.get) is None


def test_observed_access_ledger_has_closed_machine_schema():
    assert LEDGER_SCHEMA.exists()
    schema = json.loads(LEDGER_SCHEMA.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "object_role",
        "ledger_schema",
        "producer_id",
        "access_policy_sha",
        "observed_access",
    }
