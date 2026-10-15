"""RED tests for Macha's second Unified Task 3 rejection at 68df3158.

These tests preserve only the still-open defects from the focused re-check:
N1, N2, B3-V, B3-E, B3-R, and B5-F.  Do not weaken them to fit current code.
"""
from __future__ import annotations

import dataclasses

import pytest

from scripts.v5.td_unified import manifest_v1 as task2
from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified import registry_v1_dependency_fixtures as fx
from tests.v5.td_unified.test_registry_v1_macha_rejection import (
    _actors,
    _human_execution_registry,
    _setup,
)


def _stage(registry, unit_id="G8"):
    return registry.units_by_id()[unit_id].qualification_stage


def test_n2_genesis_cannot_declare_known_truth_qualified_without_sealed_challenge_evidence():
    with pytest.raises(r.RegistryError, match="KNOWN_TRUTH|sealed|genesis|challenge|evidence"):
        _human_execution_registry()


def test_b3_v_content_validator_must_be_registered_and_independent_of_producer():
    dep, ref, deps, prereq, registry, controller, reviewer, legitimate = _setup()
    validator = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}
    receipt = {
        "object_role": "CONTENT_VALIDATION_RECEIPT",
        "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
        "prerequisite_id": prereq.prerequisite_id,
        "content_identity_sha": prereq.prerequisite_unit_sha,
        "validator_identity_sha": r.canonical_sha256(validator),
        "status": "QUALIFIED",
    }
    qualified = dataclasses.replace(
        prereq,
        content_required=True,
        content_validated=True,
        content_validation_receipt_sha=r.canonical_sha256(receipt),
    )
    attacked = r.TDQualificationRegistry(
        registry.units,
        (qualified,),
        registry.promotions,
        registry.revocations,
        actor_registry_sha=registry.actor_registry_sha,
    )
    objects = {
        **legitimate,
        r.canonical_sha256(validator): validator,
        r.canonical_sha256(receipt): receipt,
    }
    with pytest.raises(r.RegistryError, match="validator|actor|registered|producer|independ"):
        r.promote_unit(
            attacked,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_b3_e_human_execution_evidence_requires_registered_independent_issuer_without_n2_masking():
    dep, ref, deps, _, registry, controller, reviewer, objects = _setup()
    process_evidence = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "PROCESS_ISOLATION",
        "producer_process_isolated": True,
        "harness_drives_finalization": True,
        "reader_fit_values_out_of_process": True,
        "protected_partitions_physically_absent": True,
    }
    evidence_sha = r.canonical_sha256(process_evidence)
    human_prereq = dataclasses.replace(
        fx.verified_prereq(
            r,
            dep,
            ref,
            pid="ISO",
            gate="HUMAN_EXECUTABLE",
            requirement_class="PROCESS_ISOLATION",
        ),
        evidence_receipt_sha=evidence_sha,
    )
    attacked = r.TDQualificationRegistry(
        registry.units,
        registry.prerequisites + (human_prereq,),
        (),
        (),
        actor_registry_sha=registry.actor_registry_sha,
    )
    resolved = dict(objects)
    resolved[evidence_sha] = process_evidence
    with pytest.raises(r.RegistryError, match="issuer|actor|registered|evidence|independ"):
        r._require_registered_prerequisite_actors(
            attacked,
            "G8",
            gate="HUMAN_EXECUTABLE",
            authority_object_resolver=resolved.get,
            dependency_verifier=deps.get,
        )


def test_b3_r_actor_registry_must_be_pinned_not_producer_authored_without_n2_masking():
    dep, ref, deps = fx.verified_pair(r)
    prereq = fx.verified_prereq(r, dep, ref)
    minted_controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "minted-by-producer-1"}
    minted_reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "minted-by-producer-2"}
    registry = r.TDQualificationRegistry((dep, ref), (prereq,), (), ())
    registry, objects = fx.bind_actor_registry(
        r,
        registry,
        {
            **deps,
            r.canonical_sha256(minted_controller): minted_controller,
            r.canonical_sha256(minted_reviewer): minted_reviewer,
        },
        trusted_actor_objects=(minted_controller, minted_reviewer),
    )
    with pytest.raises(r.RegistryError, match="actor.registry|pinned|anchor|frozen|trusted"):
        r.promote_unit(
            registry,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=r.canonical_sha256(minted_controller),
            reviewer_identity=r.canonical_sha256(minted_reviewer),
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_b5_f_fresh_custody_cannot_erase_prior_revocation_of_same_prequalification_identity():
    dep, ref, deps = fx.verified_pair(
        r,
        dep_id="B5F_G8",
        ref_id="B5F_REF",
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
    original_identity = registry.units_by_id()["B5F_G8"].canonical_sha256()
    custody_a = r.RegistryHistoryCustody(registry, attestation_key=b"custody-a")
    revoked = r.revoke_or_supersede(
        registry,
        "B5F_G8",
        L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
        history_custody=custody_a,
    )
    assert revoked.revocations[-1].affected_unit_sha == original_identity
    assert revoked.units_by_id()["B5F_G8"].active_lineage_status is L.REVOKED_BY_DEFECT

    # Discard custody A and try to restart from the exact same original identity.
    assert registry.units_by_id()["B5F_G8"].canonical_sha256() == original_identity
    with pytest.raises(r.RegistryError, match="revok|history|anchor|genesis|custody"):
        r.RegistryHistoryCustody(registry, attestation_key=b"custody-b")


def test_n1_rrr_revalidates_manifest_and_population_with_frozen_task2_validators():
    ids, objs = fx._core("G8")
    rids, robjs = fx._core("REF")
    fake_access = {
        "object_role": "ACCESS_POLICY",
        "population_authority": "AUTHENTICATED_READER_SPLIT",
        "fit_donors": [f"FAKE_{i:03d}" for i in range(104)],
        "crossfit_folds": "CHOSEN_LATER",
    }
    with pytest.raises(task2.ManifestError):
        task2.validate_population_access_policy_payload(dict(fake_access))
    access_sha = r.canonical_sha256(fake_access)
    table = {
        "object_role": "UNIT_EXECUTION_IDENTITY_TABLE",
        "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1",
        "units": [fx._row("G8", ids), fx._row("REF", rids)],
    }
    table_sha = r.canonical_sha256(table)
    manifest = {
        "schema": "TD_EXECUTION_MANIFEST_V1",
        "access_policy_sha": access_sha,
        "unit_execution_identity_table_sha": table_sha,
    }
    manifest_sha = r.canonical_sha256(manifest)
    with pytest.raises(task2.ManifestError):
        task2.validate_manifest(dict(manifest), {**objs, access_sha: fake_access, table_sha: table}.get)

    g8 = fx._build_unit(
        r,
        "G8",
        ids,
        manifest_sha=manifest_sha,
        access_sha=access_sha,
        stage=Q.KNOWN_TRUTH_QUALIFIED,
        status=L.ACTIVE,
        population_authority="AUTHENTICATED_READER_SPLIT",
        claim_scope="POOLED_DONOR_LEVEL",
    )
    ref = fx._build_unit(
        r,
        "REF",
        rids,
        manifest_sha=manifest_sha,
        access_sha=access_sha,
        stage=Q.KNOWN_TRUTH_QUALIFIED,
        status=L.ACTIVE,
        population_authority="AUTHENTICATED_READER_SPLIT",
        claim_scope="POOLED_DONOR_LEVEL",
    )
    prereq = fx.verified_prereq(r, g8, ref)
    registry = r.TDQualificationRegistry((g8, ref), (prereq,), (), ())
    controller, reviewer, actors = _actors()
    all_objects = {**objs, **robjs, access_sha: fake_access, table_sha: table, manifest_sha: manifest, **actors}
    registry, all_objects = fx.bind_actor_registry(
        r,
        registry,
        all_objects,
        trusted_actor_objects=tuple(actors.values()),
    )
    with pytest.raises(r.RegistryError, match="manifest|population|reader.split|Task 2|authority"):
        r.promote_unit(
            registry,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=all_objects.get,
            dependency_verifier=all_objects.get,
        )
