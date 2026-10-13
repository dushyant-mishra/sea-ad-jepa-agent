from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_relational_successor_readiness_v1 as R


def test_gate_binding_is_deterministic_and_hash_bound_to_exact_td_code():
    a=R.build_relational_gate_binding(ROOT)
    b=R.build_relational_gate_binding(ROOT)
    assert a==b
    assert len(a['qualified_gate_executor_sha256'])==64
    assert len(a['estimand_sha256'])==64
    assert len(a['decision_rule_sha256'])==64
    assert tuple(a['required_capabilities'])==R.MANDATORY_CAPABILITIES
    assert a['failure_scope']=='TEST_QUALIFICATION_ONLY'


def test_package_absent_is_explicitly_blocked_without_real_authority():
    binding=R.build_relational_gate_binding(ROOT)
    receipt=R.assess_relational_successor_readiness(binding=binding,external_package_present=False,qualification_receipt=None)
    assert receipt.status=='BLOCKED_EXTERNAL_SYNTHETIC_PACKAGE_NOT_DELIVERED'
    assert all(v is False for v in receipt.authority.values())


def test_package_present_without_qualification_is_blocked():
    binding=R.build_relational_gate_binding(ROOT)
    receipt=R.assess_relational_successor_readiness(binding=binding,external_package_present=True,qualification_receipt=None)
    assert receipt.status=='BLOCKED_TEST_OF_TEST_QUALIFICATION_NOT_EXECUTED'


def test_nonqualified_or_identity_drift_remains_blocked():
    binding=R.build_relational_gate_binding(ROOT)
    q=R.MinimalQualificationReference('NOT_QUALIFIED','a'*64,binding['qualified_gate_executor_sha256'],binding['estimand_sha256'],binding['decision_rule_sha256'])
    receipt=R.assess_relational_successor_readiness(binding=binding,external_package_present=True,qualification_receipt=q)
    assert receipt.status=='BLOCKED_TEST_OF_TEST_NOT_QUALIFIED'
    q2=replace(q,status='QUALIFIED',decision_rule_sha256='f'*64)
    receipt=R.assess_relational_successor_readiness(binding=binding,external_package_present=True,qualification_receipt=q2)
    assert receipt.status=='BLOCKED_QUALIFICATION_IDENTITY_MISMATCH'


def test_exact_qualified_receipt_only_reaches_independent_audit_not_execution():
    binding=R.build_relational_gate_binding(ROOT)
    q=R.MinimalQualificationReference('QUALIFIED','a'*64,binding['qualified_gate_executor_sha256'],binding['estimand_sha256'],binding['decision_rule_sha256'])
    receipt=R.assess_relational_successor_readiness(binding=binding,external_package_present=True,qualification_receipt=q)
    assert receipt.status=='READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY'
    assert receipt.real_execution_authorized is False
    assert all(v is False for v in receipt.authority.values())
