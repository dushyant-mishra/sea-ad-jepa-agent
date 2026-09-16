"""Attack tests for the Stage-A authority reconciliation (REG-1, REG-2, REG-4, REG-5, wildcard).

Written RED against c02d43fb before any implementation existed.
"""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from sea_ad_jepa.v5.canonical_address_registry_authority_v1 import (  # noqa: E402
    CANONICAL_ADDRESS_REGISTRY_ROW_COUNT,
    CanonicalAddressRegistryAuthorityV1,
)
from sea_ad_jepa.v5.current_target_address_provider_authority_v1 import (  # noqa: E402
    APPROVED_GRADIENT_POLICY_IDS,
    APPROVED_PARAMETER_SHARING_POLICY_IDS,
    APPROVED_QUERY_PROVIDER_IDS,
    APPROVED_REPLAY_POLICY_IDS,
    CurrentTargetAddressProviderAuthorityV1,
)

REGISTRY = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
BLOCK_MANIFEST = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"


def make_registry(**over) -> CanonicalAddressRegistryAuthorityV1:
    base = dict(
        authority_id="V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916",
        registry_sha256=REGISTRY,
        registry_row_count=CANONICAL_ADDRESS_REGISTRY_ROW_COUNT,
        full104_block_manifest_sha256=BLOCK_MANIFEST,
        observation_state_sha256=OBSERVATION_STATE,
        recovery_provenance="stage81a2r foundation molecular address registry derivation",
        informative_path="results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv",
    )
    base.update(over)
    return CanonicalAddressRegistryAuthorityV1(**base)


def make_provider(**over) -> CurrentTargetAddressProviderAuthorityV1:
    base = dict(
        authority_id="V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_20260916",
        address_registry_authority_sha256=make_registry().canonical_digest(),
        query_provider_id="V5_SHARED_ADDRESS_QUERY_PROVIDER_V1",
        query_artifact_sha256="a" * 64,
        replay_policy_id="FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1",
        parameter_sharing_policy_id="SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1",
        gradient_policy_id="CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1",
    )
    base.update(over)
    return CurrentTargetAddressProviderAuthorityV1(**base)


# ---------------------------------------------------------------- REG-5 attacks
@pytest.mark.parametrize(
    "field,bad",
    [(f, v)
     for f in ("query_provider_id", "replay_policy_id", "parameter_sharing_policy_id", "gradient_policy_id")
     for v in ("anything", "TD60", "historical_provider", "trust_me_shared", "TD57", "TD59")],
)
def test_unauthorized_policy_ids_fail_closed(field: str, bad: str) -> None:
    with pytest.raises(ValueError, match=field):
        dataclasses.replace(make_provider(), **{field: bad}).validate()


def test_lawful_policy_ids_are_accepted() -> None:
    make_provider().validate()


def test_approved_vocabularies_are_nonempty_and_carry_no_historical_names() -> None:
    for vocab in (APPROVED_QUERY_PROVIDER_IDS, APPROVED_REPLAY_POLICY_IDS,
                  APPROVED_PARAMETER_SHARING_POLICY_IDS, APPROVED_GRADIENT_POLICY_IDS):
        assert vocab
        for value in vocab:
            assert not any(tag in value.upper() for tag in ("TD57", "TD59", "TD60"))


def test_per_address_biological_memory_is_not_an_approved_sharing_policy() -> None:
    assert not any("PER_ADDRESS" in v.upper() and "TABLE" in v.upper()
                   for v in APPROVED_PARAMETER_SHARING_POLICY_IDS)


# ---------------------------------------------------------------- REG-2 role-splicing
def test_observation_state_hash_cannot_be_spliced_in_as_the_registry() -> None:
    with pytest.raises(ValueError, match="registry_sha256"):
        make_registry(registry_sha256=OBSERVATION_STATE).validate()


def test_registry_hash_cannot_be_spliced_in_as_the_observation_state() -> None:
    with pytest.raises(ValueError, match="observation_state_sha256"):
        make_registry(observation_state_sha256=REGISTRY).validate()


def test_block_manifest_cannot_masquerade_as_the_registry() -> None:
    with pytest.raises(ValueError, match="registry_sha256"):
        make_registry(registry_sha256=BLOCK_MANIFEST).validate()


def test_provider_rejects_a_raw_registry_file_hash_where_an_AUTHORITY_digest_is_required() -> None:
    with pytest.raises(ValueError, match="address_registry_authority_sha256"):
        make_provider(address_registry_authority_sha256=REGISTRY).validate()


# ---------------------------------------------------------------- REG-4 custody / replay
def test_wrong_row_count_fails_closed() -> None:
    with pytest.raises(ValueError, match="registry_row_count"):
        make_registry(registry_row_count=41237).validate()


def test_wrong_registry_hash_is_rejected_by_the_verifier() -> None:
    auth = make_registry()
    assert auth.verify_artifact(sha256="b" * 64, row_count=41238, ordered=True, unique=True) is False
    assert auth.verify_artifact(sha256=REGISTRY, row_count=41238, ordered=True, unique=True) is True


@pytest.mark.parametrize("kw", [{"row_count": 41237}, {"ordered": False}, {"unique": False}])
def test_replay_invariants_fail_closed(kw: dict) -> None:
    args = dict(sha256=REGISTRY, row_count=41238, ordered=True, unique=True)
    args.update(kw)
    assert make_registry().verify_artifact(**args) is False


def test_absolute_path_is_informative_only_and_not_part_of_identity() -> None:
    a = make_registry().canonical_digest()
    b = make_registry(informative_path="X:/somewhere/else/registry.csv").canonical_digest()
    assert a == b, "a drive letter must not change authority identity"


# ---------------------------------------------------------------- field safety
def test_model_facing_fields_are_exactly_the_two_lawful_identity_columns() -> None:
    auth = make_registry()
    assert set(auth.model_facing_fields) == {"molecular_address_index", "molecular_address_id"}
    for forbidden in ("symbol", "biotype", "contributing_source_feature_count",
                      "contributing_source_families", "contributing_source_dataset_ids"):
        assert forbidden in auth.prohibited_fields
        assert forbidden not in auth.model_facing_fields


def test_cell_identity_columns_are_prohibited_as_model_input() -> None:
    # REG-3: the materialization contract's identity flag scopes per-cell identity metadata.
    auth = make_registry()
    for forbidden in ("canonical_cell_id", "selection_row", "donor_id"):
        assert forbidden in auth.prohibited_fields


# ---------------------------------------------------------------- training authority
@pytest.mark.parametrize("factory", [make_registry, make_provider])
def test_new_authorities_cannot_turn_training_on(factory) -> None:
    obj = factory()
    assert obj.training_authorized is False
    with pytest.raises(ValueError, match="training"):
        dataclasses.replace(obj, training_authorized=True).validate()


# ---------------------------------------------------------------- wildcard firewall
def _run(script: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def test_wildcard_import_does_not_load_quarantined_helpers() -> None:
    result = _run(
        "import sys, json\n"
        "exec('from sea_ad_jepa.v5 import *')\n"
        "print(json.dumps(sorted(n for n in sys.modules if n.startswith('sea_ad_jepa.v5.'))))\n"
    )
    assert result.returncode == 0, result.stdout
    loaded = json.loads(result.stdout.strip().splitlines()[-1])
    assert loaded == [], f"wildcard import bypassed the spillover firewall: {loaded}"
