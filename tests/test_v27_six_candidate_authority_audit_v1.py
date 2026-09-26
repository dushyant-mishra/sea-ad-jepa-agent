"""Adversarial six-candidate role audits; no real expression or protected data."""
from __future__ import annotations
import copy, json, pathlib, shutil
import pytest
from scripts.v5.v27_six_candidate_authority_audit_v1 import CANDIDATES, audit, run

REPO = pathlib.Path(__file__).resolve().parents[1]
def setup(tmp_path):
    for rel, _, _ in CANDIDATES.values():
        p=tmp_path/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/rel,p)
    return tmp_path
def corrupt(tmp_path,root,edit):
    rel,_,_=CANDIDATES[root]
    p=tmp_path/rel
    v=json.loads(p.read_text())
    edit(v)
    p.write_text(json.dumps(v,sort_keys=True)+"\n")
def expect_reject(tmp_path,root):
    with pytest.raises((AssertionError,ValueError,TypeError,KeyError)):
        audit(root,tmp_path)

def test_all_six_original_candidate_validators_pass_and_none_close():
    r=run(REPO)
    assert r["candidate_valid"] == 6 and r["closed_roots"] == 0
    assert all(v["training_authorized"] is False and
               v["qualification"]=="CANDIDATE_SCHEMA_VALID__NOT_CLOSED" for v in r["rows"])

def test_wrong_schema_rejected(tmp_path):
    setup(tmp_path)
    k="representation_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(schema="V5_WRONG_ROLE"))
    expect_reject(tmp_path,k)

def test_prohibited_training_authorization_rejected(tmp_path):
    setup(tmp_path)
    k="support_estimability_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(training_authorized=True))
    expect_reject(tmp_path,k)

def test_registry_observation_role_splicing_rejected(tmp_path):
    setup(tmp_path)
    k="canonical_address_registry_authority_sha256"
    corrupt(tmp_path,k,lambda v:v["OPERATOR_ADDRESS_OBSERVATION_STATE"].update(sha256=v["ADDRESS_REGISTRY"]["sha256"]))
    expect_reject(tmp_path,k)

def test_registry_model_field_leakage_rejected(tmp_path):
    setup(tmp_path)
    k="canonical_address_registry_authority_sha256"
    corrupt(tmp_path,k,lambda v:v["field_safety"]["model_facing"].append("donor_id"))
    expect_reject(tmp_path,k)

def test_base_estimand_substituted_metadata_source_fails(tmp_path):
    setup(tmp_path)
    k="base_training_estimand_sha256"
    corrupt(tmp_path,k,lambda v:v.update(population_authority_sha256="f"*64))
    expect_reject(tmp_path,k)

def test_rng_false_self_digest_rejected(tmp_path):
    setup(tmp_path)
    k="masking_rng_replay_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(authority_sha256="a"*64))
    expect_reject(tmp_path,k)

def test_rng_seed_tamper_rejected(tmp_path):
    setup(tmp_path)
    k="masking_rng_replay_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(global_seed=v["global_seed"]+1))
    expect_reject(tmp_path,k)

def test_mask_parameter_wrong_role_digest_rejected(tmp_path):
    setup(tmp_path)
    k="masking_qualification_parameters_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(support_estimability_authority_sha256="1"*64))
    expect_reject(tmp_path,k)

def test_mask_parameters_cannot_assert_terminal_exposure(tmp_path):
    setup(tmp_path)
    k="masking_qualification_parameters_authority_sha256"
    corrupt(tmp_path,k,lambda v:v.update(terminal_full104_masking_outcomes_inspected=True))
    expect_reject(tmp_path,k)

def test_missing_candidate_cannot_be_reported_valid(tmp_path):
    setup(tmp_path)
    (tmp_path/CANDIDATES["representation_authority_sha256"][0]).unlink()
    r=run(tmp_path)
    assert r["candidate_valid"]==5 and r["closed_roots"]==0
