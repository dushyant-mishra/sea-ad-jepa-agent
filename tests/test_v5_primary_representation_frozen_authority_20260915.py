from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.primary_representation_authority_v1 import (
    PrimaryRepresentationAuthorityV1,
)

DOCS = Path('docs/agent')
AUTH_PATH = DOCS / 'V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json'
PARENTS_PATH = DOCS / 'V5_PRIMARY_REPRESENTATION_FEATURE_PARENTS_20260915.json'
SELECTION_PATH = DOCS / 'V5_PRIMARY_REPRESENTATION_SELECTION_20260915.json'
RECEIPT_PATH = DOCS / 'V5_PRIMARY_REPRESENTATION_FREEZE_RECEIPT_20260915.json'

EXPECTED_AUTH_SHA = '92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1'
EXPECTED_PARENTS_SHA = '0ceec0884d8bb03b00046e9d57ffceadae0c2d389953e51b12c20ae3614a8eaa'
EXPECTED_SELECTION_SHA = '5802bd0b71d7ecccf3feddef6ba1edbf88f708f264b853b9596207d7568c68ce'
EXPECTED_RECEIPT_SHA = 'bc6f66c0b35c640caff80ee0922d0bc338f47fb1b562da07eb529348729c10a4'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_primary_representation_hash_chain_is_exact() -> None:
    assert sha(PARENTS_PATH) == EXPECTED_PARENTS_SHA
    assert sha(SELECTION_PATH) == EXPECTED_SELECTION_SHA
    assert sha(AUTH_PATH) == EXPECTED_AUTH_SHA
    assert sha(RECEIPT_PATH) == EXPECTED_RECEIPT_SHA

    authority_payload = json.loads(AUTH_PATH.read_text(encoding='utf-8'))
    authority = PrimaryRepresentationAuthorityV1(
        **{key: value for key, value in authority_payload.items() if key != 'schema'}
    )
    assert authority.canonical_digest() == EXPECTED_AUTH_SHA
    assert authority.training_authorized is False


def test_frozen_parent_hashes_and_column_roles_cannot_drift() -> None:
    parents = json.loads(PARENTS_PATH.read_text(encoding='utf-8'))
    selection = json.loads(SELECTION_PATH.read_text(encoding='utf-8'))

    assert parents['views']['V0']['full_array_sha256'] == '3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada'
    assert parents['views']['V1']['full_array_sha256'] == 'c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c'
    assert parents['column_layout']['value'] == {'start_inclusive': 0, 'stop_exclusive': 256}
    assert parents['column_layout']['visibility'] == {'start_inclusive': 256, 'stop_exclusive': 512}

    assert selection['primary_molecular_columns'] == {'start_inclusive': 0, 'stop_exclusive': 256}
    assert selection['excluded_from_primary_molecular_path']['visibility_columns'] == {
        'start_inclusive': 256,
        'stop_exclusive': 512,
    }
    assert selection['observation_channel_policy'] == 'VISIBILITY_OBSERVATION_QC_CONTROL_ONLY__NO_PRIMARY_MOLECULAR_INPUT'
    assert selection['training_authorized'] is False


def test_freeze_receipt_does_not_overclaim_scope() -> None:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding='utf-8'))
    assert receipt['scope'] == 'CHANNEL_ROLE_ONLY'
    assert receipt['d_shared_outcome_accessed'] is False
    assert receipt['protected_outcome_accessed'] is False
    assert receipt['training_authorized'] is False
    assert 'DEEP_MODEL_MEASUREMENT_ROBUSTNESS_GATE' in receipt['remaining_open']
    assert 'MODEL_GEOMETRY' in receipt['remaining_open']
