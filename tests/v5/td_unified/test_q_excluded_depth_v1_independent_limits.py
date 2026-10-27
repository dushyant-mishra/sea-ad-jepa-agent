"""Independent synthetic adversarial scope of Macha PR474.

These tests prove *limitations* of an otherwise useful fixture producer.
A passing test cannot certify source completeness, query-right separation,
physical donor identity, real calibration, or any human JEPA target.
"""
from copy import deepcopy
import pytest

from scripts.v5.td_unified.q_excluded_depth_v1 import produce_rights_ladder_observations
from scripts.v5.td_unified.casebundle_v1 import validate_casebundle, CaseBundleError

MS = "MEASURED_SCALAR"

def fixture():
    return {
        "cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC",
                   "operator_id": "OP", "library_total": 10,
                   "counts": {"B1": 2, "Q1": 3}}],
        "address_rights": {"B1": "RNA:BASE", "Q1": "RNA:QUERY"},
        "operator_states": {"OP": {"B1": MS, "Q1": MS}},
        "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                   {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:QUERY"]}],
    }

def value(result, level, address):
    return next(row for entry in result["levels"] if entry["level_id"] == level
                for row in entry["rows"] if row["address_id"] == address)

def cb(result, level):
    entry=next(v for v in result["levels"] if v["level_id"]==level)
    return {
        "schema": "KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id": "REVIEW_FIXTURE_ONLY",
        "authority_scope": "FIXTURE_ONLY",
        "manifest_sha256": "a"*64,
        "population_access_policy_sha256": "b"*64,
        "address_universe_sha256": "c"*64,
        "reader_partition": "reader_fit",
        "observations": entry["casebundle_observations"],
    }

def test_mapped_query_change_is_hidden_by_invariant_depth():
    world=fixture()
    base=produce_rights_ladder_observations(**world)
    altered=deepcopy(world)
    altered["cells"][0]["counts"]["Q1"]+=11
    altered["cells"][0]["library_total"]+=11
    other=produce_rights_ladder_observations(**altered)
    assert base["levels"][0]["rows_sha256"]==other["levels"][0]["rows_sha256"]
    assert value(base,"L0","B1")["library_size"]==7
    assert value(other,"L0","B1")["library_size"]==7

def test_unmapped_hidden_molecules_are_not_removed_without_an_external_coverage_proof():
    world=fixture()
    base=produce_rights_ladder_observations(**world)
    unrecorded=deepcopy(world)
    # The source total includes additional, unrepresented Q2 molecules. Q2
    # is outside address_rights/counts, so the producer cannot subtract it.
    unrecorded["cells"][0]["library_total"]+=4
    other=produce_rights_ladder_observations(**unrecorded)
    assert value(base,"L0","B1")["library_size"]==7
    assert value(other,"L0","B1")["library_size"]==11
    assert base["levels"][0]["rows_sha256"]!=other["levels"][0]["rows_sha256"]
    assert other["source_authenticated"] is False

def test_query_in_base_rights_is_not_identifiable_by_this_api():
    world=fixture()
    world["address_rights"]["Q1"]="RNA:BASE"
    base=produce_rights_ladder_observations(**world)
    changed=deepcopy(world)
    changed["cells"][0]["counts"]["Q1"]+=1
    changed["cells"][0]["library_total"]+=1
    next_result=produce_rights_ladder_observations(**changed)
    # The API has no separate q_id or per-query rights declaration, so it
    # cannot establish that a particular queried gene was excluded.
    assert value(base,"L0","Q1")["state"]==MS
    assert value(base,"L0","B1")["library_size"]==10
    assert value(next_result,"L0","B1")["library_size"]==11
    assert base["levels"][0]["rows_sha256"]!=next_result["levels"][0]["rows_sha256"]

def test_richer_teacher_level_must_not_relabel_depth_as_physical_library():
    world=fixture()
    world["cells"][0]["library_total"]=13
    world["cells"][0]["counts"]["Q1"]=10
    result=produce_rights_ladder_observations(**world)
    depth=value(result,"L1","Q1")["library_size"]
    count=value(result,"L1","Q1")["count"]
    assert (count, depth)==(10,3)
    assert validate_casebundle(cb(result,"L0"))["externally_authenticated"] is False
    # The existing CaseBundle assumes a physical denominator >= count.
    # Calling q-excluded depth 'library_size' is not interchangeable.
    with pytest.raises(CaseBundleError):
        validate_casebundle(cb(result,"L1"))

def test_no_fixture_output_can_promote_issuer_or_donor_identity():
    result=produce_rights_ladder_observations(**fixture())
    assert result["authority_scope"]=="FIXTURE_ONLY"
    assert result["source_authenticated"] is False
    assert result["physical_measurement_identity_authenticated"] is False
    assert result["donor_identity_authenticated"] is False
    assert result["authority_effect"]=="NONE"
