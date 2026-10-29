"""Hostile fixture-only tests for segregated physical-total / visible depth V2.

No tests authenticate real molecules, donors, q-issuers, or biology.
"""
from copy import deepcopy
import json

import pytest

from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.casebundle_v1 import validate_casebundle, CaseBundleError
from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    QExcludedDepthNotEstimable, QExcludedObservationError,
)

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"


def world():
    return {
        "cells": [
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
             "library_total": 12, "counts": {"B1": 2, "B2": 0, "Q1": 10}}
        ],
        "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "B3": "RNA:BASE",
                           "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
        "operator_states": {"OP": {"B1": MS, "B2": MS, "B3": SU, "E1": MS, "Q1": MS}},
        "ladder": [
            {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
            {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
            {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
        ],
        "query_address_id": "Q1",
    }


def student(w=None):
    return V2.produce_fixture_student_view_v2(**(world() if w is None else w))


def teacher(w=None):
    return V2.produce_fixture_teacher_view_v2(**(world() if w is None else w))


def row(view, address):
    return next(r for r in view["rows"] if r["address_id"] == address)


def assert_view_law(v, kind):
    assert v["schema"] == "TD_OBSERVATION_NORMALIZATION_VIEW_V2_FIXTURE"
    assert v["view_kind"] == kind
    assert v["authority_scope"] == "FIXTURE_ONLY"
    assert v["depth_semantics"] == "BASE_RIGHTS_INVARIANT_NORMALIZATION_DEPTH_NOT_PHYSICAL_TOTAL"
    assert v["reader_partition"] == "reader_fit"
    assert v["authority_effect"] == "NONE"
    assert v["source_authenticated"] is False
    assert v["q_rights_issuer_authenticated"] is False
    assert v["source_feature_mapping_authenticated"] is False
    assert v["physical_measurement_identity_authenticated"] is False
    assert v["donor_identity_authenticated"] is False
    assert v["same_code_path_authorized"] is False
    assert v["real_training_authorized"] is False
    assert v["external_truth_access_authorized"] is False
    assert v["observable_sha256"] == canonical_sha256({k: x for k, x in v.items() if k != "observable_sha256"})
    assert all("library_total" not in r and "physical_library_total" not in r
               and "library_size" not in r for r in v["rows"])
    assert "library_total" not in v and "physical_library_total" not in v
    assert V2.validate_fixture_observation_view_v2(v)["externally_authenticated"] is False


def test_student_base_rights_view_hides_query_count_and_does_not_include_teacher_rows():
    v = student()
    assert_view_law(v, "STUDENT_BASE_RIGHTS")
    assert row(v, "B1")["count"] == 2
    assert row(v, "B1")["base_rights_normalization_depth"] == 2
    assert row(v, "B2")["state"] == MS and row(v, "B2")["count"] == 0
    assert row(v, "B3")["state"] == SU and row(v, "B3")["count"] is None
    assert row(v, "Q1")["state"] == "WITHHELD_BY_EVIDENCE_RIGHTS"
    assert row(v, "Q1")["count"] is None
    assert row(v, "Q1")["base_rights_normalization_depth"] is None
    assert "teacher_rows" not in v
    assert "latent_truth" not in json.dumps(v)


def test_teacher_count_greater_than_base_depth_is_lawful_in_separate_v2_schema():
    v = teacher()
    assert_view_law(v, "TEACHER_RICHER_RIGHTS")
    assert row(v, "Q1")["count"] == 10
    assert row(v, "Q1")["base_rights_normalization_depth"] == 2
    assert 10 > 2
    with pytest.raises(CaseBundleError):
        validate_casebundle(v)  # V1 remains unchanged and cannot silently import V2


@pytest.mark.parametrize("delta", [1, 7, 99, 4096])
def test_mapped_query_mass_cannot_change_student_view_or_hash(delta):
    original = student()
    w = world()
    w["cells"][0]["counts"]["Q1"] += delta
    w["cells"][0]["library_total"] += delta
    perturbed = student(w)
    assert perturbed == original
    assert row(teacher(w), "Q1")["count"] == 10 + delta


def test_offledger_mass_cannot_be_silently_treated_as_legitimate_depth():
    w = world()
    w["cells"][0]["library_total"] += 4  # potential unrepresented q alias
    with pytest.raises(QExcludedDepthNotEstimable, match="unmapped or unresolved"):
        student(w)
    with pytest.raises(QExcludedDepthNotEstimable):
        teacher(w)


def test_query_assigned_base_rights_is_not_allowed():
    w = world()
    w["address_rights"]["Q1"] = "RNA:BASE"
    with pytest.raises(QExcludedDepthNotEstimable, match="queried address"):
        student(w)
    with pytest.raises(QExcludedDepthNotEstimable):
        teacher(w)


def test_unknown_query_address_cannot_be_assumed_structurally_absent():
    w = world()
    w["query_address_id"] = "MISSING"
    with pytest.raises(QExcludedDepthNotEstimable, match="source-mapped"):
        student(w)


def test_collision_outside_base_is_not_estimable_even_if_other_mass_balanced():
    w = world()
    w["operator_states"]["OP"]["E1"] = MCU
    with pytest.raises(QExcludedDepthNotEstimable):
        student(w)


def test_duplicate_cells_are_refused_by_original_producer():
    w = world()
    w["cells"].append(deepcopy(w["cells"][0]))
    with pytest.raises(QExcludedObservationError, match="duplicate cell"):
        student(w)


def test_altered_issuer_authentication_claim_even_with_recomputed_digest_is_refused():
    v = student()
    v["source_authenticated"] = True
    v["observable_sha256"] = canonical_sha256({k: x for k, x in v.items() if k != "observable_sha256"})
    with pytest.raises(QExcludedObservationError, match="forbidden issuer"):
        V2.validate_fixture_observation_view_v2(v)


def test_malicious_physical_total_field_is_not_valid_in_the_v2_consumer():
    v = teacher()
    v["rows"][0]["physical_library_total"] = 12
    v["observable_sha256"] = canonical_sha256({k: x for k, x in v.items() if k != "observable_sha256"})
    with pytest.raises(QExcludedObservationError, match="physical total"):
        V2.validate_fixture_observation_view_v2(v)


def test_malformed_count_depth_states_and_q_reveal_cannot_be_signed_through():
    kinds = [
        ("count", 999, "MEASURED_SCALAR"),
        ("base_rights_normalization_depth", 0, "MEASURED_SCALAR"),
        ("state", "NONSENSE", "NONSENSE"),
    ]
    for key, value, _ in kinds:
        v = student()
        v["rows"][0][key] = value
        v["observable_sha256"] = canonical_sha256({k: x for k, x in v.items() if k != "observable_sha256"})
        # A1 repair: type-valid count tampering is now rejected whenever it
        # breaks the exact base-visible depth equality law.
        with pytest.raises(QExcludedObservationError):
            V2.validate_fixture_observation_view_v2(v)
    v = student()
    row(v, "Q1")["state"] = MS
    row(v, "Q1")["count"] = 5
    row(v, "Q1")["base_rights_normalization_depth"] = 2
    v["observable_sha256"] = canonical_sha256({k: x for k, x in v.items() if k != "observable_sha256"})
    with pytest.raises(QExcludedObservationError, match="queried scalar"):
        V2.validate_fixture_observation_view_v2(v)


def test_caller_mutation_after_view_issue_does_not_modify_frozen_observable():
    w = world()
    v = student(w)
    w["cells"][0]["counts"]["B1"] = 400
    w["ladder"][0]["evidence_rights"].append("RNA:QUERY")
    assert row(v, "B1")["count"] == 2
    assert V2.validate_fixture_observation_view_v2(v)["authority_effect"] == "NONE"


def test_nested_hostile_str_subclass_refused_before_comparison():
    class Bomb(str):
        def __eq__(self, other):
            raise RuntimeError("caller comparison executed")
        def __hash__(self):
            return hash(str(self))
    w = world()
    w["query_address_id"] = Bomb("Q1")
    with pytest.raises(QExcludedObservationError):
        student(w)


def test_bad_digest_is_not_a_credible_issuer():
    v = student()
    v["observable_sha256"] = "f"*64
    with pytest.raises(QExcludedObservationError, match="digest"):
        V2.validate_fixture_observation_view_v2(v)


def test_v2_does_not_change_v1_casebundle_validation_of_real_physical_total():
    w = world()
    physical_rows = [{
        "cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
        "address_id": a, "state": MS, "count": k, "library_size": 12,
        "evidence_right": w["address_rights"][a]
    } for a, k in w["cells"][0]["counts"].items()]
    p = {
        "schema": "KNOWN_TRUTH_CASEBUNDLE_V1", "case_id": "OLDER_FIXTURE",
        "authority_scope": "FIXTURE_ONLY", "manifest_sha256": "a"*64,
        "population_access_policy_sha256": "b"*64,
        "address_universe_sha256": "c"*64, "reader_partition": "reader_fit",
        "observations": physical_rows,
    }
    assert validate_casebundle(p)["status"] == "CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY"
