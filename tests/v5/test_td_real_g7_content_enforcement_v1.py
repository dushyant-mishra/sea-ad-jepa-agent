"""Hostile G7 E3 real-validator content tests: synthetic fixture values only."""
from __future__ import annotations
from copy import deepcopy
import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E

RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]
def manifest():
    return {
        "schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
        "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(RIGHTS),
        "levels": [
            {"level_id": "L0", "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION", "evidence_rights": RIGHTS[:1]},
            {"level_id": "L1", "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION", "evidence_rights": RIGHTS[:2]},
            {"level_id": "L2", "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION", "evidence_rights": RIGHTS[:]},
        ],
    }

def full():
    return [
        {"atom_id":"cell:A","source":"SEA_AD","donor_id":"D1","right":"RNA:CORE",
         "state":"MEASURED_SCALAR","count":0,"library_size":31},
        {"atom_id":"cell:B","source":"SEA_AD","donor_id":"D1","right":"RNA:EXTENDED",
         "state":"MEASURED_SCALAR","count":5,"library_size":31},
        {"atom_id":"cell:C","source":"SEA_AD","donor_id":"D1","right":"CONTEXT:LAWFUL",
         "state":"MEASURED_SCALAR","count":3,"library_size":31},
        {"atom_id":"cell:D","source":"SEA_AD","donor_id":"D1","right":"CONTEXT:LAWFUL",
         "state":"STRUCTURALLY_UNMEASURED","count":None,"library_size":None},
        {"atom_id":"cell:E","source":"SEA_AD","donor_id":"D1","right":"RNA:EXTENDED",
         "state":"MEASURED_COLLISION_UNRESOLVED","count":None,"library_size":None},
    ]

def fixture():
    m=manifest()
    raw=full()
    mh=E.canonical_sha256(m)
    fh=E.canonical_sha256(raw)
    levels=[]
    expected_tokens={}
    expected_levels={}
    for id,rights in [("L0",RIGHTS[:1]),("L1",RIGHTS[:2]),("L2",RIGHTS[:])]:
        atoms=deepcopy(raw)
        for a in atoms:
            if a["state"]=="MEASURED_SCALAR" and a["right"] not in rights:
                a["state"]="WITHHELD_BY_EVIDENCE_RIGHTS"
                a["count"]=None
                a["library_size"]=None
        token={"schema":E.RIGHTS_TOKEN_SCHEMA,"candidate_id":m["candidate_id"],
               "level_id":id,"evidence_rights":list(rights),
               "manifest_sha256":mh,"full_atoms_sha256":fh}
        levels.append({"level_id":id,"rights_token":token,"atoms":atoms})
        expected_tokens[id]=E.canonical_sha256(token)
        expected_levels[id]=E.canonical_sha256(atoms)
    return m, raw, levels, dict(manifest_sha256=mh, full_atoms_sha256=fh,
                                token_sha256_by_level=expected_tokens,
                                atoms_sha256_by_level=expected_levels)

def check(m=None,raw=None,levels=None,pins=None):
    fm,fr,fl,fp=fixture()
    return E.validate_g7_e3_content(
        manifest=fm if m is None else m, full_atoms=fr if raw is None else raw,
        levels=fl if levels is None else levels, expected_pins=fp if pins is None else pins)

def test_valid_fixture_preserves_measured_zero_and_reports_no_human_authority():
    r=check()
    assert r["status"]=="E3_CONTENT_MECHANICS_VERIFIED_FIXTURE_ONLY"
    assert r["same_code_path_authorized"] is False
    assert r["human_g7_authorized"] is False
    assert r["visible_by_level"]=={"L0":1,"L1":2,"L2":3}

def test_visible_count_thinning_is_rejected_despite_rehashed_package():
    m,f,levels,pins=fixture()
    levels[1]["atoms"][1]["count"]=3
    pins["atoms_sha256_by_level"]["L1"]=E.canonical_sha256(levels[1]["atoms"])
    with pytest.raises(E.G7ContentError):
        check(m,f,levels,pins)

def test_visible_library_depth_thinning_is_rejected_even_if_count_unchanged():
    m,f,levels,pins=fixture()
    levels[1]["atoms"][0]["library_size"]=20
    pins["atoms_sha256_by_level"]["L1"]=E.canonical_sha256(levels[1]["atoms"])
    with pytest.raises(E.G7ContentError):
        check(m,f,levels,pins)

def test_already_visible_atom_must_remain_identical_at_all_levels():
    m,f,levels,pins=fixture()
    levels[2]["atoms"][0]["count"]=1
    pins["atoms_sha256_by_level"]["L2"]=E.canonical_sha256(levels[2]["atoms"])
    with pytest.raises(E.G7ContentError):
        check(m,f,levels,pins)

@pytest.mark.parametrize("mutation",["structural_to_withheld","collision_to_measured","hidden_as_zero",
                                     "omitted_atom","duplicate_atom","extra_atom","swapped_source"])
def test_states_roster_and_identity_are_content_bound(mutation):
    m,f,levels,pins=fixture()
    a=levels[0]["atoms"]
    if mutation=="structural_to_withheld": a[3]["state"]="WITHHELD_BY_EVIDENCE_RIGHTS"
    elif mutation=="collision_to_measured":
        a[4].update(state="MEASURED_SCALAR",count=0,library_size=31)
    elif mutation=="hidden_as_zero":
        a[1].update(state="MEASURED_SCALAR",count=0,library_size=31)
    elif mutation=="omitted_atom": a.pop()
    elif mutation=="duplicate_atom": a.append(deepcopy(a[0]))
    elif mutation=="extra_atom": a.append({**a[0], "atom_id":"rogue"})
    elif mutation=="swapped_source": a[0]["source"]="HVS"
    pins["atoms_sha256_by_level"]["L0"]=E.canonical_sha256(a)
    with pytest.raises(E.G7ContentError):
        check(m,f,levels,pins)

def test_tampered_rights_token_refused_even_if_rehashed():
    m,f,levels,pins=fixture()
    levels[1]["rights_token"]["evidence_rights"]=["RNA:CORE"]
    pins["token_sha256_by_level"]["L1"]=E.canonical_sha256(levels[1]["rights_token"])
    with pytest.raises(E.G7ContentError):
        check(m,f,levels,pins)

def test_forged_manifest_pins_or_full_observations_refused():
    m,f,levels,pins=fixture()
    pins["manifest_sha256"]="a"*64
    with pytest.raises(E.G7ContentError):check(m,f,levels,pins)
    m,f,levels,pins=fixture()
    f[0]["count"]=9
    with pytest.raises(E.G7ContentError):check(m,f,levels,pins)

def test_count_depth_operator_label_refused():
    m,f,levels,pins=fixture()
    m["levels"][0]["operator_family"]="COUNT_THINNING"
    with pytest.raises((E.G7ContentError,ValueError)):check(m,f,levels,pins)

def test_subclass_lookalike_rejected_without_calling_comparison():
    class AlwaysEqual(str):
        def __eq__(self,other):return True
        __hash__=str.__hash__
    m,f,levels,pins=fixture()
    levels[0]["atoms"][0]["count"]=AlwaysEqual("0")
    with pytest.raises(E.G7ContentError):check(m,f,levels,pins)

def test_relabelled_content_cannot_claim_independent_pin_issuer():
    m,f,levels,pins=fixture()
    r=check(m,f,levels,pins)
    assert "externally_authenticated" in r
    assert r["externally_authenticated"] is False

def _g7_typed_row(binding, *, pen=2, fin=3, added=1, source="SEA_AD", donor="D1"):
    return {"source":source,"donor_id":donor, "terminal_displacement":0.02,
            "penultimate_supported_evidence":pen, "full_supported_evidence":fin,
            "added_supported_evidence":added, "input_binding_sha256":binding}

def test_terminal_support_inputs_bind_to_actual_rights_content_not_caller_counts():
    m,f,levels,pins=fixture()
    binding=E.derive_fixture_g7_e3_input_binding(m,pins,required_sources=["SEA_AD"])
    receipt=E.bind_g7_terminal_inputs_e3(
        manifest=m,full_atoms=f,levels=levels,expected_pins=pins,
        required_sources=["SEA_AD"],rows=[_g7_typed_row(binding)],
        reference_input_binding_sha256=binding)
    assert receipt["status"]=="E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY"
    assert receipt["same_code_path_authorized"] is False
    assert receipt["human_g7_authorized"] is False
    assert receipt["bound_unit_count"]==1

@pytest.mark.parametrize("pen,fin,added",[(0,3,3),(2,2,0),(2,4,2),(2,3,0)])
def test_terminal_caller_supported_evidence_numbers_cannot_override_content(pen,fin,added):
    m,f,levels,pins=fixture()
    binding=E.derive_fixture_g7_e3_input_binding(m,pins,required_sources=["SEA_AD"])
    with pytest.raises(E.G7ContentError):
        E.bind_g7_terminal_inputs_e3(
            manifest=m,full_atoms=f,levels=levels,expected_pins=pins,
            required_sources=["SEA_AD"],rows=[_g7_typed_row(binding,pen=pen,fin=fin,added=added)],
            reference_input_binding_sha256=binding)

def test_terminal_binding_rejects_wrong_reference_or_row_hash():
    m,f,levels,pins=fixture()
    binding=E.derive_fixture_g7_e3_input_binding(m,pins,required_sources=["SEA_AD"])
    with pytest.raises(E.G7ContentError):
        E.bind_g7_terminal_inputs_e3(manifest=m,full_atoms=f,levels=levels,expected_pins=pins,
                                     required_sources=["SEA_AD"],rows=[_g7_typed_row(binding)],
                                     reference_input_binding_sha256="f"*64)
    with pytest.raises(E.G7ContentError):
        E.bind_g7_terminal_inputs_e3(manifest=m,full_atoms=f,levels=levels,expected_pins=pins,
                                     required_sources=["SEA_AD"],rows=[_g7_typed_row("f"*64)],
                                     reference_input_binding_sha256=binding)

def test_terminal_binding_rejects_source_donor_reassignment_and_unlisted_rows():
    m,f,levels,pins=fixture()
    binding=E.derive_fixture_g7_e3_input_binding(m,pins,required_sources=["SEA_AD"])
    for source,donor in [("HVS","D1"),("SEA_AD","D2")]:
        with pytest.raises(E.G7ContentError):
            E.bind_g7_terminal_inputs_e3(manifest=m,full_atoms=f,levels=levels,expected_pins=pins,
                                         required_sources=["SEA_AD"],rows=[
                                             _g7_typed_row(binding,source=source,donor=donor)],
                                         reference_input_binding_sha256=binding)
