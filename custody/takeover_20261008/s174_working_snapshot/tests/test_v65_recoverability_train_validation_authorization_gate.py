from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/privileged_recoverability_train_validation_authorization_gate_v1.py"


def _load():
    spec=importlib.util.spec_from_file_location("authgate",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _valid(m,tmp_path):
    a={
        "authorized":True,
        "experiment":m.EXPERIMENT,
        "scope":m.SCOPE,
        "test_access":m.TEST_ACCESS,
        **m.expected_authority(ROOT),
    }
    p=tmp_path/"auth.json"; p.write_text(json.dumps(a))
    return p,a


def test_missing_authorization_fails_closed(tmp_path):
    m=_load()
    with pytest.raises(m.AuthorizationError,match="absent"):
        m.validate_authorization(tmp_path/"missing.json",ROOT)


def test_false_authorization_fails_closed(tmp_path):
    m=_load(); p,a=_valid(m,tmp_path)
    a["authorized"]=False; p.write_text(json.dumps(a))
    with pytest.raises(m.AuthorizationError,match="authorized=true"):
        m.validate_authorization(p,ROOT)


def test_test_access_can_never_be_authorized(tmp_path):
    m=_load(); p,a=_valid(m,tmp_path)
    a["test_access"]="ALLOWED"; p.write_text(json.dumps(a))
    with pytest.raises(m.AuthorizationError,match="TEST access"):
        m.validate_authorization(p,ROOT)


def test_digest_drift_fails_closed(tmp_path):
    m=_load(); p,a=_valid(m,tmp_path)
    a["decision_contract_sha256"]="0"*64; p.write_text(json.dumps(a))
    with pytest.raises(m.AuthorizationError,match="decision_contract_sha256"):
        m.validate_authorization(p,ROOT)


def test_forbidden_test_fields_fail_closed(tmp_path):
    m=_load(); p,a=_valid(m,tmp_path)
    a["test_metrics"]={}; p.write_text(json.dumps(a))
    with pytest.raises(m.AuthorizationError,match="forbidden TEST fields"):
        m.validate_authorization(p,ROOT)


def test_exact_valid_authorization_would_pass_gate(tmp_path):
    m=_load(); p,_=_valid(m,tmp_path)
    out=m.validate_authorization(p,ROOT)
    assert out["status"]=="AUTHORIZED_TRAIN_VALIDATION_ONLY"
    assert out["test_access"]=="FORBIDDEN"
