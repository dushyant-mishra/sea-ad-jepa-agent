"""RED tests for the still-open blockers in Macha re-check 2 of d9e58a18.

Scope is intentionally narrow: N2, nested B3-V, and the four B5-F variants.
These tests must fail on d9e58a18 and must not be weakened to fit production code.
"""
from __future__ import annotations

import dataclasses
import hashlib

import pytest

from scripts.v5.td_unified import manifest_v1 as M
from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as csha
from tests.v5.td_unified import registry_v1_dependency_fixtures as fx
from tests.v5.td_unified.test_registry_v1_macha_rejection import _actors


ROWS = ["donor_id,reader_partition"] + [f"F{i:03d},reader_fit" for i in range(104)]
ROWS += [f"V{i:03d},reader_validation" for i in range(22)]
ROWS += [f"O{i:03d},reader_oracle" for i in range(23)]
RAW_BYTES = ("\n".join(ROWS) + "\n").encode()
RAW_SHA = hashlib.sha256(RAW_BYTES).hexdigest()
RAW = {RAW_SHA: RAW_BYTES}.get


def _world(monkeypatch, specs):
    monkeypatch.setattr(M, "FROZEN_READER_SPLIT_SHA256", RAW_SHA)
    policy = M.build_current_td_access_policy_from_reader_split(reader_split_raw=RAW_BYTES)
    store = {}

    def put(obj):
        sha = csha(obj)
        store[sha] = obj
        return sha

    def code(blob):
        sha = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
        store[sha] = blob
        return sha

    identities = {}
    table_rows = []
    for uid, _ in specs:
        ids, objects = fx._core(uid)
        store.update(objects)
        identities[uid] = ids
        table_rows.append(fx._row(uid, ids))

    fields = {
        "access_policy_sha": put(policy.to_payload()),
        "population_split_registry_sha": put({
            "object_role": "POPULATION_SPLIT_REGISTRY",
            "reader_split_raw_sha256": RAW_SHA,
            "population_registry_sha256": M.FROZEN_POPULATION_REGISTRY_SHA256,
        }),
        "crossfit_policy_sha": put(M.derive_crossfit_policy_payload(policy)),
        "protected_partition_policy_sha": put(M.derive_protected_partition_policy_payload(policy)),
    }
    for partition in ("reader_fit", "reader_validation", "reader_oracle"):
        fields[f"{partition}_policy_sha"] = put(
            M.derive_reader_partition_policy_payload(policy, partition)
        )
    normalization = put({"object_role": "NORMALIZATION_CONTRACT", "rule": "n"})
    library = put({"object_role": "LIBRARY_CONTRACT", "rule": "l"})
    fields["normalization_library_contract_sha"] = put({
        "object_role": "NORMALIZATION_LIBRARY_CONTRACT",
        "contract_schema": "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1",
        "normalization_contract_sha": normalization,
        "library_contract_sha": library,
    })
    fields["target_portfolio_code_identity_sha"] = put({
        "object_role": "TARGET_PORTFOLIO_CODE_IDENTITY",
        "identity_schema": "GIT_BLOB_IDENTITY_V1",
        "git_blob_sha1": code(b"def portfolio(): pass\n"),
    })
    fields["target_portfolio_policy_sha"] = put({
        "object_role": "TARGET_PORTFOLIO_POLICY",
        "policy_schema": "TARGET_PORTFOLIO_POLICY_IDENTITY_V1",
        "policy_contract_sha": put({
            "object_role": "TARGET_PORTFOLIO_POLICY_CONTRACT",
            "c": 1,
        }),
    })
    fields["unit_execution_identity_table_sha"] = put({
        "object_role": "UNIT_EXECUTION_IDENTITY_TABLE",
        "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1",
        "units": table_rows,
    })
    for field, role in M._MANIFEST_ROLE_BY_FIELD.items():
        if field not in fields:
            fields[field] = put({"object_role": role, "x": field})
    manifest = {
        "schema": "TD_EXECUTION_MANIFEST_V1",
        "controller_code_sha": code(b"controller = 1\n"),
        **fields,
    }
    manifest_sha = put(manifest)
    M.validate_manifest(dict(manifest), store.get, raw_resolver=RAW)

    units = [
        fx._build_unit(
            r,
            uid,
            identities[uid],
            manifest_sha=manifest_sha,
            access_sha=fields["access_policy_sha"],
            stage=stage,
            status=L.ACTIVE,
            population_authority="AUTHENTICATED_READER_SPLIT",
            claim_scope="POOLED_DONOR_LEVEL",
        )
        for uid, stage in specs
    ]
    return units, store


def _bind(units, prerequisites, store):
    controller, reviewer, actors = _actors()
    registry = r.TDQualificationRegistry(tuple(units), tuple(prerequisites), (), ())
    registry, objects = fx.bind_actor_registry(
        r,
        registry,
        {**store, **actors},
        trusted_actor_objects=tuple(actors.values()),
    )
    return registry, controller, reviewer, objects


def _rrr(registry, controller, reviewer, objects, *, uid="G8", custody=None):
    return r.promote_unit(
        registry,
        uid,
        Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=objects.get,
        raw_resolver=RAW,
        history_custody=custody,
    )


def _genesis(prefix):
    dep, ref, deps = fx.verified_pair(
        r,
        dep_id=f"{prefix}_G8",
        ref_id=f"{prefix}_REF",
        dep_stage=Q.SEMANTICS_ONLY,
        ref_stage=Q.SEMANTICS_ONLY,
    )
    registry = r.TDQualificationRegistry((dep, ref), (), (), ())
    controller, reviewer, actors = _actors()
    registry, objects = fx.bind_actor_registry(
        r,
        registry,
        {**deps, **actors},
        trusted_actor_objects=tuple(actors.values()),
    )
    return registry, controller, reviewer, objects


def _promote(registry, uid, stage, controller, reviewer, objects, custody=None):
    return r.promote_unit(
        registry,
        uid,
        stage,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=objects.get,
        history_custody=custody,
    )


def _revoke(registry, uid, controller, objects, custody=None):
    return r.revoke_or_supersede(
        registry,
        uid,
        L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=objects.get,
        dependency_verifier=objects.get,
        history_custody=custody,
    )


def test_n2_real_reference_ready_requires_matching_custody(monkeypatch):
    (g8, ref), store = _world(monkeypatch, [("G8", Q.KNOWN_TRUTH_QUALIFIED), ("REF", Q.KNOWN_TRUTH_QUALIFIED)])
    registry, controller, reviewer, objects = _bind(
        (g8, ref),
        (fx.verified_prereq(r, g8, ref),),
        store,
    )
    with pytest.raises(r.RegistryError, match="custody|history|REAL_REFERENCE_READY"):
        _rrr(registry, controller, reviewer, objects)


def test_b3_v_nested_prerequisite_actor_gate_rejects_unregistered_validator(monkeypatch):
    (g8, ref, ref2), store = _world(
        monkeypatch,
        [("G8", Q.KNOWN_TRUTH_QUALIFIED), ("REF", Q.KNOWN_TRUTH_QUALIFIED), ("REF2", Q.KNOWN_TRUTH_QUALIFIED)],
    )
    direct = fx.verified_prereq(r, g8, ref, pid="P1")
    nested = fx.verified_prereq(r, ref, ref2, pid="P2")
    validator = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}
    receipt = {
        "object_role": "CONTENT_VALIDATION_RECEIPT",
        "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
        "prerequisite_id": "P2",
        "content_identity_sha": nested.prerequisite_unit_sha,
        "validator_identity_sha": csha(validator),
        "status": "QUALIFIED",
    }
    store.update({csha(validator): validator, csha(receipt): receipt})
    nested = dataclasses.replace(
        nested,
        content_required=True,
        content_validated=True,
        content_validation_receipt_sha=csha(receipt),
    )
    registry, _, _, objects = _bind((g8, ref, ref2), (direct, nested), store)
    with pytest.raises(r.RegistryError, match="validator|registered|producer|independ"):
        r._require_registered_prerequisite_actors(
            registry,
            "G8",
            gate="REAL_REFERENCE_READY",
            authority_object_resolver=objects.get,
            dependency_verifier=objects.get,
        )


def test_b3_v_nested_prerequisite_cannot_promote_through_rrr(monkeypatch):
    (g8, ref, ref2), store = _world(
        monkeypatch,
        [("G8", Q.KNOWN_TRUTH_QUALIFIED), ("REF", Q.KNOWN_TRUTH_QUALIFIED), ("REF2", Q.KNOWN_TRUTH_QUALIFIED)],
    )
    direct = fx.verified_prereq(r, g8, ref, pid="P1")
    nested = fx.verified_prereq(r, ref, ref2, pid="P2")
    validator = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}
    receipt = {
        "object_role": "CONTENT_VALIDATION_RECEIPT",
        "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
        "prerequisite_id": "P2",
        "content_identity_sha": nested.prerequisite_unit_sha,
        "validator_identity_sha": csha(validator),
        "status": "QUALIFIED",
    }
    store.update({csha(validator): validator, csha(receipt): receipt})
    nested = dataclasses.replace(
        nested,
        content_required=True,
        content_validated=True,
        content_validation_receipt_sha=csha(receipt),
    )
    registry, controller, reviewer, objects = _bind((g8, ref, ref2), (direct, nested), store)
    with pytest.raises(r.RegistryError, match="validator|registered|producer|independ|custody"):
        _rrr(registry, controller, reviewer, objects)


def test_b5_f_forked_custody_created_before_revocation_cannot_promote_revoked_identity():
    registry, controller, reviewer, objects = _genesis("F2")
    custody_a = r.RegistryHistoryCustody(registry, attestation_key=b"a")
    custody_b = r.RegistryHistoryCustody(registry, attestation_key=b"b")
    _revoke(registry, "F2_G8", controller, objects, custody_a)
    with pytest.raises(r.RegistryError, match="revok|anchor|custody|history"):
        _promote(registry, "F2_G8", Q.FIXTURE_SAME_INTERFACE, controller, reviewer, objects, custody_b)


def test_b5_f_history_free_promotion_cannot_bypass_revocation_anchor():
    registry, controller, reviewer, objects = _genesis("F3")
    custody = r.RegistryHistoryCustody(registry, attestation_key=b"a")
    _revoke(registry, "F3_G8", controller, objects, custody)
    with pytest.raises(r.RegistryError, match="revok|anchor|custody|history"):
        _promote(registry, "F3_G8", Q.FIXTURE_SAME_INTERFACE, controller, reviewer, objects)


def test_b5_f_stage_shift_cannot_recreate_revoked_execution_identity():
    registry, controller, reviewer, objects = _genesis("F4")
    custody_a = r.RegistryHistoryCustody(registry, attestation_key=b"a")
    promoted = _promote(
        registry,
        "F4_G8",
        Q.FIXTURE_SAME_INTERFACE,
        controller,
        reviewer,
        objects,
        custody_a,
    )
    _revoke(promoted, "F4_G8", controller, objects, custody_a)

    with pytest.raises(r.RegistryError, match="revok|anchor|custody|history"):
        r.RegistryHistoryCustody(registry, attestation_key=b"b")


def test_b5_f_revoked_execution_identity_cannot_be_declared_ktq_then_reach_rrr(monkeypatch):
    (g8_low, ref_low), store_low = _world(
        monkeypatch,
        [("X_G8", Q.SEMANTICS_ONLY), ("X_REF", Q.SEMANTICS_ONLY)],
    )
    low, controller, _, low_objects = _bind((g8_low, ref_low), (), store_low)
    custody = r.RegistryHistoryCustody(low, attestation_key=b"a")
    _revoke(low, "X_G8", controller, low_objects, custody)

    (g8_ktq, ref_ktq), store_ktq = _world(
        monkeypatch,
        [("X_G8", Q.KNOWN_TRUTH_QUALIFIED), ("X_REF", Q.KNOWN_TRUTH_QUALIFIED)],
    )
    high, controller2, reviewer2, high_objects = _bind(
        (g8_ktq, ref_ktq),
        (fx.verified_prereq(r, g8_ktq, ref_ktq),),
        store_ktq,
    )
    with pytest.raises(r.RegistryError, match="revok|anchor|custody|history"):
        _rrr(high, controller2, reviewer2, high_objects, uid="X_G8")
