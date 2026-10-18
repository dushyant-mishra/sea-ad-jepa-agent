from __future__ import annotations

import json
from pathlib import Path

from scripts.v5.td_unified import challenge_custody_v1 as c


SCHEMA_DIR = Path("schemas/target_discovery/unified_v1")


def _deps():
    return {
        "task2_manifest_sha": "1" * 64,
        "task3_registry_sha": "2" * 64,
        "registry_unit_identities": (("G8", "3" * 64),),
        "producer_actor_identity": "4" * 64,
        "executor_actor_identity": "5" * 64,
        "controller_actor_identity": "6" * 64,
        "adjudicator_actor_identity": "7" * 64,
        "challenge_generator_code_sha": "8" * 40,
        "challenge_generator_policy_sha": "9" * 64,
        "realization_schema_sha": "a" * 64,
        "rng_policy_sha": "b" * 64,
        "challenge_family_sha": "c" * 64,
        "adjudication_contract_sha": "d" * 64,
        "multiplicity_policy_sha": "e" * 64,
        "publication_policy_sha": "f" * 64,
        "genesis_ledger_identity": "0" * 64,
        "authority_scope": "UNIT:G8",
        "authority_restrictions": ("NO_TRAINING_AUTHORITY",),
        "qualification_budget": 1,
    }


def test_qualification_campaign_payload_keys_match_declared_schema():
    campaign = c.create_campaign("schema", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    payload = campaign.to_payload()
    schema = json.loads((SCHEMA_DIR / "qualification_campaign_v1.json").read_text(encoding="utf-8"))
    assert set(payload) == set(schema["properties"])
    assert set(schema["required"]) == set(payload)


def test_task4_terminal_schema_files_are_strict_objects():
    names = (
        "task4_actor_action_attestation_v1.json",
        "task4_persistent_custody_head_v1.json",
        "exposure_ledger_v1.json",
        "method_output_freeze_receipt_v1.json",
        "sealed_qualification_reveal_v1.json",
        "sealed_custody_receipt_v1.json",
        "qualification_evidence_package_v1.json",
    )
    for name in names:
        schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
