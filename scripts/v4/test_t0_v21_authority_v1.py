import copy
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t0_v21_authority_v1 as a

H="a"*64; B="b"*64; C="c"*64; D="d"*64; E="e"*64; F="f"*64; ZERO="0"*64; ONE="1"*64; TWO="2"*64

def authority():
    return {"expression_root_digest":H,"donor_role_ledger_digest":B,"donor_order_digest":C,"molecular_address_digest":D,"transformation_digest":E,"nuisance_spec_digest":F,"estimator_id":"S2@v21","target_code_sha":ZERO,"contract_sha":ONE}

def old_crossfit():
    ids=tuple(f"D{i:02d}" for i in range(28)); scores=np.arange(28,dtype=float)/10.0; folds=[]
    for i in range(28):
        folds.append({"held_out_index":i,"n_train":27,"train_indices":tuple(j for j in range(28) if j!=i),"out_of_fold_prediction":float(scores[i]),"fold_ridge_exponent":-4.0})
    return {"kind":"t0_v21_cross_fit_artifact_v1","n_donors":28,"donor_ids":ids,"y":np.linspace(0,1,28),"age":np.linspace(55,90,28),"sex":np.tile([0.,1.],14),"oof_scores":scores,"folds":folds,"artifact_digest":"legacy"}

def fold_prov(cf):
    ids=tuple(cf["donor_ids"]); out=[]
    for i,d in enumerate(ids):
        out.append({"held_out_donor_id":d,"train_donor_ids":tuple(x for x in ids if x!=d),"training_data_digest":hashlib.sha256(f"data-{i}".encode()).hexdigest(),"ridge_trace_digest":hashlib.sha256(f"ridge-{i}".encode()).hexdigest(),"fitted_target_digest":hashlib.sha256(f"fit-{i}".encode()).hexdigest(),"prediction":float(cf["oof_scores"][i])})
    return out

def sealed():
    cf=old_crossfit(); return a.seal_authoritative_crossfit(cross_fit_artifact=cf,source_authority=authority(),fold_provenance=fold_prov(cf))

def test_self_consistent_but_wrong_external_authority_fails():
    art=sealed(); expected=authority(); expected["expression_root_digest"]=TWO
    with pytest.raises(RuntimeError,match="expression_root_digest"): a.validate_authoritative_crossfit(art,expected_source_authority=expected)

def test_fold_training_data_digest_is_bound():
    art=copy.deepcopy(sealed()); art["fold_provenance"][0]["training_data_digest"]=TWO
    with pytest.raises(RuntimeError,match="digest does not recompute"): a.validate_authoritative_crossfit(art,expected_source_authority=authority())

def test_illegal_train_donor_set_cannot_be_sealed():
    cf=old_crossfit(); fp=fold_prov(cf); fp[0]["train_donor_ids"]=fp[0]["train_donor_ids"][:-1]+("D00",)
    with pytest.raises(RuntimeError,match="exact 27-donor complement"): a.seal_authoritative_crossfit(cross_fit_artifact=cf,source_authority=authority(),fold_provenance=fp)

def test_prediction_mismatch_cannot_be_sealed():
    cf=old_crossfit(); fp=fold_prov(cf); fp[4]["prediction"]+=1
    with pytest.raises(RuntimeError,match="prediction mismatch"): a.seal_authoritative_crossfit(cross_fit_artifact=cf,source_authority=authority(),fold_provenance=fp)

def test_protected_confirmation_design_is_forbidden():
    with pytest.raises(RuntimeError,match="protected role"): a.seal_confirmation_design_receipt(age=np.linspace(55,90,12),sex=np.tile([0.,1.],6),source_role="reader_validation",source_digest=H,contract_sha=ONE)

def test_nested_permutation_evidence_must_match_artifact_and_reject():
    art=sealed(); v=a.validate_authoritative_crossfit(art,expected_source_authority=authority())
    ev=a.seal_nested_permutation_evidence(authoritative_crossfit_digest=v["artifact_digest"],source_authority_digest=v["source_authority_digest"],nested_pipeline_code_sha=ZERO,contract_sha=ONE,n_permutations=9999,seed=7,p_upper=0.02,null_digest=H)
    assert a.validate_nested_permutation_evidence(ev,artifact_digest=v["artifact_digest"],source_authority_digest=v["source_authority_digest"],expected_pipeline_code_sha=ZERO,expected_contract_sha=ONE)["verified"]
    ev2=a.seal_nested_permutation_evidence(authoritative_crossfit_digest=v["artifact_digest"],source_authority_digest=v["source_authority_digest"],nested_pipeline_code_sha=ZERO,contract_sha=ONE,n_permutations=9999,seed=7,p_upper=0.20,null_digest=H)
    with pytest.raises(RuntimeError,match="does not reject"): a.validate_nested_permutation_evidence(ev2,artifact_digest=v["artifact_digest"],source_authority_digest=v["source_authority_digest"],expected_pipeline_code_sha=ZERO,expected_contract_sha=ONE)

def test_frozen_B_is_enforced():
    with pytest.raises(RuntimeError,match="B=9999"): a.seal_nested_permutation_evidence(authoritative_crossfit_digest=H,source_authority_digest=B,nested_pipeline_code_sha=ZERO,contract_sha=ONE,n_permutations=99,seed=1,p_upper=.01,null_digest=C)
