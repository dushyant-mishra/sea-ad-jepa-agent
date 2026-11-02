"""D1 -> standalone V2C fixture integration; no real issuer or deployment.

Original #507/#512 independent RED and #511/#514 author tests are untouched.
Tests deliberately distinguish view-content commitment from physical authenticity.
"""
import ast
from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from scripts.v5.td_unified import observation_d1_base_only_student_v2c_fixture_v1 as P
from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C

MS, SU, MCU, W = C._MS, C._SU, C._MCU, C._W


def policy():
    return {
        "query_address_id": "ENSG_Q",
        "base_evidence_rights": ["RNA_BASE"],
        "address_rights": {
            "ENSG_A": "RNA_BASE", "ENSG_B": "RNA_BASE",
            "ENSG_Q": "RNA_QUERY", "ENSG_E": "RNA_EXT",
            "ENSG_U": "RNA_EXT", "ENSG_Z": "RNA_QUERY",
        },
        "operator_states": {
            "OP_A": {a: (MCU if a=="ENSG_U" else SU if a=="ENSG_Z" else MS)
                     for a in ("ENSG_A","ENSG_B","ENSG_Q","ENSG_E","ENSG_U","ENSG_Z")},
            "OP_B": {a: (SU if a in ("ENSG_B","ENSG_Z") else
                         MCU if a=="ENSG_U" else MS)
                     for a in ("ENSG_A","ENSG_B","ENSG_Q","ENSG_E","ENSG_U","ENSG_Z")},
        },
        "cell_roster": [
            {"cell_id":"C_A0","donor_id":"D_A","source_id":"S_A","operator_id":"OP_A"},
            {"cell_id":"C_A1","donor_id":"D_B","source_id":"S_A","operator_id":"OP_A"},
            {"cell_id":"C_B0","donor_id":"D_C","source_id":"S_B","operator_id":"OP_B"},
        ],
    }


def observations():
    return [
        {"cell_id":"C_A0","base_counts":{"ENSG_A":3,"ENSG_B":2}},
        {"cell_id":"C_A1","base_counts":{"ENSG_A":4}},  # omitted measured zero
        {"cell_id":"C_B0","base_counts":{"ENSG_A":6}},  # second operator B structurally unmeasured
    ]


def build(p=None, o=None):
    return P.produce_d1_base_only_student_v2c_fixture(
        expected_policy=policy() if p is None else p,
        base_observations=observations() if o is None else o,
    )


def receipt(view=None, p=None):
    return C.validate_student_v2c(
        student_view=build() if view is None else view,
        expected_policy=policy() if p is None else p,
    )


def test_v2c_direct_fixture_and_complete_policy_digest():
    v=build()
    r=receipt(v)
    assert v["view_kind"]=="STUDENT_BASE_RIGHTS"
    assert v["observable_sha256"]==C._sha({k:x for k,x in v.items() if k!="observable_sha256"})
    assert r["validated_student_view_sha256"]==v["observable_sha256"]
    assert r["complete_policy_sha256"]==C._sha(policy())
    assert r["receipt_sha256"]==C._sha({k:x for k,x in r.items() if k!="receipt_sha256"})
    assert r["status"]=="STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY"
    assert r["real_training_authorized"] is False
    assert r["source_rights_issuer_authenticated"] is False
    assert r["authority_effect"]=="NONE"
    rows={(x["cell_id"],x["address_id"]):x for x in v["rows"]}
    assert rows["C_A0","ENSG_A"]["base_rights_normalization_depth"]==5
    assert rows["C_A1","ENSG_B"]["count"]==0
    assert rows["C_B0","ENSG_B"]["state"]==SU
    assert rows["C_A0","ENSG_U"]["state"]==MCU
    assert rows["C_A0","ENSG_Q"]["state"]==W
    assert rows["C_A0","ENSG_Q"]["count"] is None


def test_producer_accepts_only_redacted_base_values():
    assert set(inspect.signature(P.produce_d1_base_only_student_v2c_fixture).parameters)=={
        "expected_policy","base_observations"
    }
    with pytest.raises(TypeError):
        P.produce_d1_base_only_student_v2c_fixture(
            base_observations=observations(),expected_policy=policy(),library_total=100
        )
    assert "library_total" not in str(build())
    assert "teacher_digest" not in str(build())


@pytest.mark.parametrize("q",[0,1,7,23,2**20])
@pytest.mark.parametrize("offledger",[0,10,99999])
@pytest.mark.parametrize("collision",[0,8,101])
def test_hidden_q_and_residual_worlds_have_identical_student_output(q,offledger,collision):
    # Not in the producer's input; does not test external upstream roster selection.
    world={"q":q,"offledger":offledger,"collision":collision}
    assert all(isinstance(v,int) for v in world.values())
    assert build()==build()
    assert receipt()==receipt()


@pytest.mark.parametrize("fault",[
    "unknown_count","query_value","collision_value","structural_value",
    "negative","bool","float","zero","missing_cell","extra_cell",
    "query_promoted","query_unmeasured","wrong_operator","missing_state",
    "malformed_roster","malformed_right","unhashable_base",
])
def test_corrupted_policy_and_values_refuse_in_domain(fault):
    p,o=policy(),observations()
    if fault=="unknown_count": o[0]["base_counts"]["FAKE"]=1
    elif fault=="query_value": o[0]["base_counts"]["ENSG_Q"]=7
    elif fault=="collision_value": o[0]["base_counts"]["ENSG_U"]=7
    elif fault=="structural_value": o[0]["base_counts"]["ENSG_Z"]=7
    elif fault=="negative": o[0]["base_counts"]["ENSG_A"]=-1
    elif fault=="bool": o[0]["base_counts"]["ENSG_A"]=True
    elif fault=="float": o[0]["base_counts"]["ENSG_A"]=1.5
    elif fault=="zero": o[0]["base_counts"]={}
    elif fault=="missing_cell": o.pop()
    elif fault=="extra_cell": o.append(deepcopy(o[0]))
    elif fault=="query_promoted": p["address_rights"]["ENSG_Q"]="RNA_BASE"
    elif fault=="query_unmeasured": p["operator_states"]["OP_B"]["ENSG_Q"]=SU
    elif fault=="wrong_operator": p["cell_roster"][2]["operator_id"]="UNKNOWN"
    elif fault=="missing_state": del p["operator_states"]["OP_A"]["ENSG_U"]
    elif fault=="malformed_roster": p["cell_roster"][0]["cell_id"]=True
    elif fault=="malformed_right": p["address_rights"]["ENSG_A"]=" "
    elif fault=="unhashable_base": p["base_evidence_rights"]=[{"wrong":"right"}]
    with pytest.raises(C.StudentV2CRefusal):
        build(p,o)


def test_zero_base_refusal_is_hidden_query_invariant():
    o=observations()
    for row in o: row["base_counts"]={}
    outcomes=[]
    for secret in (0,7,23,10000):
        assert secret>=0
        with pytest.raises(C.StudentV2CRefusal) as exc:
            build(o=o)
        outcomes.append((type(exc.value),exc.value.args,exc.value.__cause__))
    assert len(set(outcomes))==1


@pytest.mark.parametrize("fault",["donor","source","roster","operator","query","content_swap"])
def test_composition_receipts_bind_view_and_entire_policy(fault):
    original=receipt()
    p,o=policy(),observations()
    if fault=="donor": p["cell_roster"][0]["donor_id"]="OTHER"
    elif fault=="source": p["cell_roster"][0]["source_id"]="OTHER"
    elif fault=="roster":
        p["cell_roster"]=p["cell_roster"][:2];o=o[:2]
    elif fault=="operator": p["operator_states"]["OP_A"]["ENSG_E"]=SU
    elif fault=="query":
        p["query_address_id"]="ENSG_E"
        p["address_rights"]["ENSG_E"]="RNA_QUERY"
        p["address_rights"]["ENSG_Q"]="RNA_EXT"
    elif fault=="content_swap":
        o[0]["base_counts"]["ENSG_A"]=4
        o[0]["base_counts"]["ENSG_B"]=1
    changed=receipt(build(p,o),p)
    assert changed["receipt_sha256"]!=original["receipt_sha256"]
    if fault=="content_swap":
        assert changed["complete_policy_sha256"]==original["complete_policy_sha256"]
        assert changed["validated_student_view_sha256"]!=original["validated_student_view_sha256"]
    else:
        assert changed["complete_policy_sha256"]!=original["complete_policy_sha256"]


def test_self_issued_consistent_forgery_remains_unauthenticated():
    o=observations();o[0]["base_counts"]={"ENSG_A":1,"ENSG_B":4}
    r=receipt(build(o=o))
    assert r["validated_student_view_sha256"]!=receipt()["validated_student_view_sha256"]
    assert all(r[key] is False for key in (
        "source_rights_issuer_authenticated","physical_measurement_identity_authenticated",
        "source_feature_alias_closure_authenticated","depositor_qc_selection_authenticated",
        "real_training_authorized",
    ))


def test_alias_contamination_is_a_positive_known_limitation():
    o=observations()
    o[0]["base_counts"]["ENSG_A"]+=23
    assert build(o=o)!=build()
    assert receipt(build(o=o))["source_feature_alias_closure_authenticated"] is False


def test_imports_only_v2c_not_v2b_or_teacher_aware_502():
    source=inspect.getsource(P)
    tree=ast.parse(source)
    imported=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            imported.extend((node.module,name.name) for name in node.names)
        if isinstance(node,ast.Import):
            imported.extend((name.name,"") for name in node.names)
    assert imported==[("__future__","annotations"),
                      ("scripts.v5.td_unified","observation_v2c_standalone_student_gate_v1")]
    assert "observation_v2b_public_student_gate_v1" not in source
    assert "observation_normalization_view_v2_bound_content_v1" not in source


def test_v2c_verifier_runs_from_only_its_own_file_in_isolated_python_launch():
    # Not OS isolation or physical source authentication: only a packaging
    # proof that the verifier itself needs no legacy Python source tree.
    source=Path(inspect.getsourcefile(C))
    v=build();p=policy()
    payload=json.dumps({"view":v,"policy":p})
    code="""
import importlib.util, json, sys
spec=importlib.util.spec_from_file_location("student_only_v2c",sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    import scripts.v5.td_unified.observation_normalization_view_v2_bound_content_v1
except ImportError:
    pass
else:
    raise RuntimeError("LEGACY_IMPORT_REACHABLE")
request=json.loads(sys.stdin.read())
out=module.validate_student_v2c(student_view=request["view"],expected_policy=request["policy"])
print(json.dumps(out,sort_keys=True))
"""
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td)/"student_v2c.py"
        dest.write_bytes(source.read_bytes())
        env={**os.environ,"PYTHONPATH":str(Path.cwd())}
        result=subprocess.run(
            [sys.executable,"-I","-S","-B","-c",code,str(dest)],
            input=payload,text=True,capture_output=True,cwd=td,env=env,check=True,
        )
    assert json.loads(result.stdout)==receipt()
