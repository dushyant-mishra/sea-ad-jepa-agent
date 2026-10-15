from __future__ import annotations

import hashlib
import inspect

import pytest

from scripts.v5.td_unified import manifest_v1 as m
from scripts.v5.td_unified.canonical_v1 import canonical_sha256

FROZEN_READER_SPLIT_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
FROZEN_POPULATION_REGISTRY_SHA256 = "50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d"


def _synthetic_reader_split() -> bytes:
    rows = ["donor_id,reader_partition"]
    rows += [f"F{i},reader_fit" for i in range(1, 6)]
    rows += ["V1,reader_validation", "O1,reader_oracle"]
    return ("\n".join(rows) + "\n").encode("utf-8")


def test_authoritative_reader_split_identity_is_a_frozen_lane_constant():
    assert hasattr(m, "FROZEN_READER_SPLIT_SHA256")
    assert m.FROZEN_READER_SPLIT_SHA256 == FROZEN_READER_SPLIT_SHA256
    assert hasattr(m, "FROZEN_POPULATION_REGISTRY_SHA256")
    assert m.FROZEN_POPULATION_REGISTRY_SHA256 == FROZEN_POPULATION_REGISTRY_SHA256


def test_current_td_authoritative_builder_requires_actual_frozen_reader_split_bytes():
    assert hasattr(m, "build_current_td_access_policy_from_reader_split")
    params = inspect.signature(m.build_current_td_access_policy_from_reader_split).parameters
    assert "reader_split_raw" in params
    bad = _synthetic_reader_split()
    assert hashlib.sha256(bad).hexdigest() != FROZEN_READER_SPLIT_SHA256
    with pytest.raises(m.ManifestError, match="reader split|raw|SHA|identity"):
        m.build_current_td_access_policy_from_reader_split(reader_split_raw=bad)


def test_fixture_builder_is_explicitly_non_authoritative_for_current_td():
    policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    payload = policy.to_payload()
    assert payload["population_authority"] == "FIXTURE_UNBOUND"
    assert payload["reader_split_raw_sha256"] is None
    with pytest.raises(m.ManifestError, match="authoritative|population|reader split"):
        m.require_current_td_population_authority(policy)


def test_authoritative_assignment_law_is_donor_identity_only_not_unbound_source_labels():
    assert hasattr(m, "CURRENT_TD_ASSIGNMENT_LAW")
    assert m.CURRENT_TD_ASSIGNMENT_LAW == "DONOR_SHA256_ORDER_ROUND_ROBIN_V1"
    # Source-stratified draft was pre-execution history, not authority.
    assert "SOURCE" not in m.CURRENT_TD_ASSIGNMENT_LAW


def test_manifest_access_policy_must_bind_frozen_population_split_custody():
    assert hasattr(m, "validate_manifest_population_binding")
    fixture_policy = m.build_current_td_access_policy(
        fit_donors=["D1", "D2", "D3", "D4", "D5"],
        donor_source={d: "S1" for d in ["D1", "D2", "D3", "D4", "D5"]},
    )
    split_obj = {
        "object_role": "POPULATION_SPLIT_REGISTRY",
        "reader_split_raw_sha256": FROZEN_READER_SPLIT_SHA256,
        "population_registry_sha256": FROZEN_POPULATION_REGISTRY_SHA256,
    }
    with pytest.raises(m.ManifestError, match="population|reader split|authority"):
        m.validate_manifest_population_binding(
            access_policy=fixture_policy.to_payload(),
            population_split_registry=split_obj,
        )


def test_wrong_reader_split_bytes_fail_even_if_partition_counts_look_plausible():
    raw = _synthetic_reader_split()
    assert b"reader_fit" in raw and b"reader_validation" in raw and b"reader_oracle" in raw
    with pytest.raises(m.ManifestError):
        m.build_current_td_access_policy_from_reader_split(reader_split_raw=raw)
