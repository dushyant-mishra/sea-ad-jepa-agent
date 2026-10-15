"""Independent B2 RED: HUMAN_EXECUTED requires authenticated execution evidence."""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair


def test_h2_human_executed_requires_authenticated_execution_receipt():
    dep, ref, dependencies = verified_pair(r, dep_stage=Q.HUMAN_EXECUTABLE)
    registry = r.TDQualificationRegistry((dep, ref), (), (), ())
    controller_obj = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "C1"}
    reviewer_obj = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "R1"}
    controller = r.canonical_sha256(controller_obj)
    reviewer = r.canonical_sha256(reviewer_obj)
    authority_objects = {controller: controller_obj, reviewer: reviewer_obj}

    with pytest.raises(r.RegistryError, match="HUMAN_EXECUTED|execution|receipt|evidence|closed"):
        r.promote_unit(
            registry,
            "G8",
            Q.HUMAN_EXECUTED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=authority_objects.get,
            dependency_verifier=dependencies.get,
        )
