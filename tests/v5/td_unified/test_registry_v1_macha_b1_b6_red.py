import dataclasses
from pathlib import Path

import pytest

import scripts.v5.td_unified.registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq, direct_fixture_actor_objects


def _authority_actors(*, controller_id="C1", reviewer_id="R1"):
    controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": controller_id}
    reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": reviewer_id}
    return r.canonical_sha256(controller), r.canonical_sha256(reviewer), {
        r.canonical_sha256(controller): controller,
        r.canonical_sha256(reviewer): reviewer,
    }


def _setup(dep_stage=Q.KNOWN_TRUTH_QUALIFIED):
    dep, ref, deps = verified_pair(r, dep_stage=dep_stage)
    prereq = verified_prereq(r, dep, ref)
    registry = r.TDQualificationRegistry((dep, ref), (prereq,), (), ())
    controller, reviewer, actors = _authority_actors()
    objects = dict(deps)
    objects.update(actors)
    return dep, ref, deps, registry, controller, reviewer, objects


def test_t3_b1_promote_unit_applies_task1_scope_stage_ceiling():
    dep, _, deps, _, controller, reviewer, objects = _setup()
    advanced = dataclasses.replace(dep, qualification_stage=Q.HUMAN_EXECUTED)
    registry = r.TDQualificationRegistry((advanced,), (), (), ())
    with pytest.raises(r.RegistryError, match="Task 1 authority|scope|stage|DOWNSTREAM|UNIT"):
        r.promote_unit(
            registry, "G8", Q.DOWNSTREAM_CERTIFIED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_t3_b2_fixed_stage_evidence_table_fails_closed_for_unimplemented_evidence():
    dep, ref, deps = verified_pair(r, dep_stage=Q.SAME_CODE_PATH)
    registry = r.TDQualificationRegistry((dep, ref), (), (), ())
    controller, reviewer, actors = _authority_actors()
    objects = dict(deps); objects.update(actors)
    with pytest.raises(r.RegistryError, match="KNOWN_TRUTH|sealed custody|adjudication|evidence"):
        r.promote_unit(
            registry, "G8", Q.KNOWN_TRUTH_QUALIFIED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )

    human = dataclasses.replace(dep, qualification_stage=Q.HUMAN_EXECUTABLE)
    registry2 = r.TDQualificationRegistry((human,), (), (), ())
    with pytest.raises(r.RegistryError, match="HUMAN_EXECUTED|execution receipt|evidence"):
        r.promote_unit(
            registry2, "G8", Q.HUMAN_EXECUTED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_t3_b3_registered_actor_table_refuses_aliases_and_newly_minted_controller():
    dep, _, deps, registry, _, reviewer, objects = _setup()
    producer_id = f"producer:{dep.unit_id}"
    bad_ids = [
        producer_id,
        producer_id + " ",
        " " + producer_id,
        producer_id.upper(),
        producer_id.replace(":", "\uff1a"),
        "minted-by-producer-1",
    ]
    for actor_id in bad_ids:
        controller_obj = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": actor_id}
        controller_sha = r.canonical_sha256(controller_obj)
        resolver = dict(objects); resolver[controller_sha] = controller_obj
        with pytest.raises(r.RegistryError, match="registered|ASCII|controller|producer|independent"):
            r.promote_unit(
                registry, "G8", Q.REAL_REFERENCE_READY,
                controller_identity=controller_sha,
                reviewer_identity=reviewer,
                authority_object_resolver=resolver.get,
                dependency_verifier=deps.get,
            )


def test_t3_b4_cache_is_internal_and_fresh_calls_reverify_against_current_resolver():
    _, _, deps, registry, _, _, objects = _setup()
    with pytest.raises(TypeError):
        r.derive_real_reference_ready(
            "G8", registry,
            dependency_verifier=deps.get,
            authority_object_resolver=objects.get,
            verification_cache={},
        )
    assert r.derive_real_reference_ready(
        "G8", registry,
        dependency_verifier=deps.get,
        authority_object_resolver=objects.get,
    ).ready
    assert not r.derive_real_reference_ready(
        "G8", registry,
        dependency_verifier=lambda _: None,
        authority_object_resolver=objects.get,
    ).ready


def test_t3_b5_revocation_erasure_and_rebuilt_advanced_history_are_refused():
    dep, _, deps, registry, controller, reviewer, objects = _setup()
    promoted = r.promote_unit(
        registry, "G8", Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    revoked = r.revoke_or_supersede(
        promoted, "G8", L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    forged_unit = dataclasses.replace(revoked.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
    forged = r.TDQualificationRegistry(
        tuple(forged_unit if u.unit_id == "G8" else u for u in revoked.units),
        revoked.prerequisites,
        revoked.promotions,
        (),
    )
    with pytest.raises(r.RegistryError, match="history|provenance|anchor|rollback"):
        r.promote_unit(
            forged, "G8", Q.HUMAN_EXECUTABLE,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_t3_b6_task3_ci_is_read_only_and_does_not_mutate_tests_or_production_code():
    workflows = list(Path(".github/workflows").glob("*task3*.yml"))
    assert workflows
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        assert "contents: write" not in text
        assert "git push" not in text
        assert "git commit" not in text
