from __future__ import annotations

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r


def _unit(unit_id: str = "G8", *, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED):
    return r.RegistryUnit(
        unit_id=unit_id,
        qualification_stage=stage,
        active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope=f"UNIT:{unit_id}",
        authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha="1" * 64,
        access_policy_sha="2" * 64,
        producer_code_sha="a" * 40,
        executor_code_sha="b" * 40,
        producer_policy_sha="3" * 64,
        executor_policy_sha="4" * 64,
        schema_sha="5" * 64,
        metric_sha="6" * 64,
        reference_producer_sha="7" * 64,
        falsifier_sha="8" * 64,
        population_authority="AUTHENTICATED_READER_SPLIT",
        claim_scope="POOLED_DONOR_LEVEL",
    )


def _unit_prereq(dep: r.RegistryUnit, ref: r.RegistryUnit):
    return r.PrerequisiteRecord(
        prerequisite_id="P1",
        dependent_unit_id=dep.unit_id,
        dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=ref.unit_id,
        prerequisite_unit_sha=ref.canonical_sha256(),
        required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=dep.manifest_sha,
        access_policy_sha=dep.access_policy_sha,
        gate="REAL_REFERENCE_READY",
        content_required=False,
        content_validated=True,
        content_validation_receipt_sha=None,
        requirement_class="UNIT",
        external_state="SATISFIED",
        evidence_receipt_sha="9" * 64,
    )


def _registry(*units, prerequisites=(), promotions=()):
    return r.TDQualificationRegistry(tuple(units), tuple(prerequisites), tuple(promotions), ())


def _actor(role: str, actor_id: str, nonce: str = ""):
    obj = {"object_role": role, "actor_id": actor_id, "nonce": nonce}
    sha = canonical_sha256(obj)
    return sha, obj


def _evidence(requirement_class: str, **claims):
    obj = {"object_role": "PREREQUISITE_EVIDENCE", "requirement_class": requirement_class, **claims}
    sha = canonical_sha256(obj)
    return sha, obj


def test_ready_requires_actual_dependency_authentication_not_consistent_hash_strings():
    dep = _unit("G8")
    ref = _unit("REF")
    reg = _registry(dep, ref, prerequisites=(_unit_prereq(dep, ref),))
    result = r.derive_real_reference_ready("G8", reg)
    assert not result.ready
    assert any("verif" in b.lower() or "resolver" in b.lower() or "authentic" in b.lower() for b in result.blockers)


def test_two_distinct_reviewer_objects_with_same_actor_id_are_not_independent():
    unit = _unit("G8", stage=QualificationStage.REAL_REFERENCE_READY)
    csha, cobj = _actor("QUALIFICATION_CONTROLLER", "same-human", "controller-object")
    rsha, robj = _actor("INDEPENDENT_REVIEWER", "same-human", "reviewer-object")
    process_sha, process_obj = _evidence(
        "PROCESS_ISOLATION",
        producer_process_isolated=True,
        harness_drives_finalization=True,
        reader_fit_values_out_of_process=True,
        protected_partitions_physically_absent=True,
    )
    custody_sha, custody_obj = _evidence(
        "CROSS_PROCESS_LEDGER_CUSTODY",
        persistent_ledger=True,
        signing_key_out_of_process=True,
        key_custodian="HARNESS",
    )
    def p(pid, klass, sha):
        return r.PrerequisiteRecord(
            prerequisite_id=pid,
            dependent_unit_id="G8",
            dependent_unit_sha=unit.canonical_sha256(),
            prerequisite_unit_id=pid,
            prerequisite_unit_sha="c" * 64,
            required_stage=QualificationStage.SEMANTICS_ONLY,
            required_lineage_status=ActiveLineageStatus.ACTIVE,
            manifest_sha=unit.manifest_sha,
            access_policy_sha=unit.access_policy_sha,
            gate="HUMAN_EXECUTABLE",
            content_required=False,
            content_validated=True,
            content_validation_receipt_sha=None,
            requirement_class=klass,
            external_state="SATISFIED",
            evidence_receipt_sha=sha,
        )
    reg = _registry(unit, prerequisites=(p("R1", "PROCESS_ISOLATION", process_sha), p("R4", "CROSS_PROCESS_LEDGER_CUSTODY", custody_sha)))
    objects = {csha: cobj, rsha: robj, process_sha: process_obj, custody_sha: custody_obj}
    with pytest.raises(r.RegistryError, match="actor|independent|same"):
        r.promote_unit(reg, "G8", QualificationStage.HUMAN_EXECUTABLE,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get)


def test_vacuous_process_isolation_label_cannot_satisfy_R1():
    unit = _unit("G8", stage=QualificationStage.REAL_REFERENCE_READY)
    csha, cobj = _actor("QUALIFICATION_CONTROLLER", "C")
    rsha, robj = _actor("INDEPENDENT_REVIEWER", "R")
    bad = {"object_role": "PREREQUISITE_EVIDENCE"}
    bad_sha = canonical_sha256(bad)
    good_sha, good = _evidence(
        "CROSS_PROCESS_LEDGER_CUSTODY",
        persistent_ledger=True,
        signing_key_out_of_process=True,
        key_custodian="HARNESS",
    )
    def p(pid, klass, sha):
        return r.PrerequisiteRecord(
            prerequisite_id=pid,
            dependent_unit_id="G8",
            dependent_unit_sha=unit.canonical_sha256(),
            prerequisite_unit_id=pid,
            prerequisite_unit_sha="c" * 64,
            required_stage=QualificationStage.SEMANTICS_ONLY,
            required_lineage_status=ActiveLineageStatus.ACTIVE,
            manifest_sha=unit.manifest_sha,
            access_policy_sha=unit.access_policy_sha,
            gate="HUMAN_EXECUTABLE",
            content_required=False,
            content_validated=True,
            content_validation_receipt_sha=None,
            requirement_class=klass,
            external_state="SATISFIED",
            evidence_receipt_sha=sha,
        )
    reg = _registry(unit, prerequisites=(p("R1", "PROCESS_ISOLATION", bad_sha), p("R4", "CROSS_PROCESS_LEDGER_CUSTODY", good_sha)))
    objects = {csha: cobj, rsha: robj, bad_sha: bad, good_sha: good}
    with pytest.raises(r.RegistryError, match="PROCESS_ISOLATION|process isolation|evidence"):
        r.promote_unit(reg, "G8", QualificationStage.HUMAN_EXECUTABLE,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get)


def test_vacuous_cross_process_custody_label_cannot_satisfy_R4():
    unit = _unit("G8", stage=QualificationStage.REAL_REFERENCE_READY)
    csha, cobj = _actor("QUALIFICATION_CONTROLLER", "C")
    rsha, robj = _actor("INDEPENDENT_REVIEWER", "R")
    good_sha, good = _evidence(
        "PROCESS_ISOLATION",
        producer_process_isolated=True,
        harness_drives_finalization=True,
        reader_fit_values_out_of_process=True,
        protected_partitions_physically_absent=True,
    )
    bad = {"object_role": "PREREQUISITE_EVIDENCE"}
    bad_sha = canonical_sha256(bad)
    def p(pid, klass, sha):
        return r.PrerequisiteRecord(
            prerequisite_id=pid,
            dependent_unit_id="G8",
            dependent_unit_sha=unit.canonical_sha256(),
            prerequisite_unit_id=pid,
            prerequisite_unit_sha="c" * 64,
            required_stage=QualificationStage.SEMANTICS_ONLY,
            required_lineage_status=ActiveLineageStatus.ACTIVE,
            manifest_sha=unit.manifest_sha,
            access_policy_sha=unit.access_policy_sha,
            gate="HUMAN_EXECUTABLE",
            content_required=False,
            content_validated=True,
            content_validation_receipt_sha=None,
            requirement_class=klass,
            external_state="SATISFIED",
            evidence_receipt_sha=sha,
        )
    reg = _registry(unit, prerequisites=(p("R1", "PROCESS_ISOLATION", good_sha), p("R4", "CROSS_PROCESS_LEDGER_CUSTODY", bad_sha)))
    objects = {csha: cobj, rsha: robj, good_sha: good, bad_sha: bad}
    with pytest.raises(r.RegistryError, match="custody|persistence|key|R4"):
        r.promote_unit(reg, "G8", QualificationStage.HUMAN_EXECUTABLE,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get)


def test_hand_constructed_real_reference_ready_stage_without_promotion_history_cannot_advance():
    unit = _unit("G8", stage=QualificationStage.REAL_REFERENCE_READY)
    csha, cobj = _actor("QUALIFICATION_CONTROLLER", "C")
    rsha, robj = _actor("INDEPENDENT_REVIEWER", "R")
    psha, pobj = _evidence(
        "PROCESS_ISOLATION",
        producer_process_isolated=True,
        harness_drives_finalization=True,
        reader_fit_values_out_of_process=True,
        protected_partitions_physically_absent=True,
    )
    ksha, kobj = _evidence(
        "CROSS_PROCESS_LEDGER_CUSTODY",
        persistent_ledger=True,
        signing_key_out_of_process=True,
        key_custodian="HARNESS",
    )
    def p(pid, klass, sha):
        return r.PrerequisiteRecord(
            prerequisite_id=pid,
            dependent_unit_id="G8",
            dependent_unit_sha=unit.canonical_sha256(),
            prerequisite_unit_id=pid,
            prerequisite_unit_sha="c" * 64,
            required_stage=QualificationStage.SEMANTICS_ONLY,
            required_lineage_status=ActiveLineageStatus.ACTIVE,
            manifest_sha=unit.manifest_sha,
            access_policy_sha=unit.access_policy_sha,
            gate="HUMAN_EXECUTABLE",
            content_required=False,
            content_validated=True,
            content_validation_receipt_sha=None,
            requirement_class=klass,
            external_state="SATISFIED",
            evidence_receipt_sha=sha,
        )
    reg = _registry(unit, prerequisites=(p("R1", "PROCESS_ISOLATION", psha), p("R4", "CROSS_PROCESS_LEDGER_CUSTODY", ksha)))
    objects = {csha: cobj, rsha: robj, psha: pobj, ksha: kobj}
    with pytest.raises(r.RegistryError, match="promotion history|provenance|prior promotion"):
        r.promote_unit(reg, "G8", QualificationStage.HUMAN_EXECUTABLE,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get)
