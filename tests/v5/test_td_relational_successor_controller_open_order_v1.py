from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_relational_successor_disk_runner_v1 as D
import td_test_qualification_package_v1 as P


def test_controller_truth_is_opened_only_after_all_blinded_fit_execution(monkeypatch,tmp_path):
    events=[]
    binding_path=tmp_path/'binding.json'
    controller_path=tmp_path/'controller.json'
    output_path=tmp_path/'receipt.json'
    binding_path.write_text('{}',encoding='utf-8')
    controller_path.write_text('{}',encoding='utf-8')

    def fake_read_json(path):
        p=Path(path)
        if p==binding_path:
            events.append('binding_open')
            return {'binding':'stub'}
        if p==controller_path:
            events.append('controller_open')
            return {'controller':'stub'}
        raise AssertionError(p)

    package=P.ValidatedExternalPackage('pkg','a'*64,{},'b'*64,{})
    adapter=SimpleNamespace(status='READY')
    fit_receipt=SimpleNamespace()
    qualification=SimpleNamespace(status='QUALIFIED')
    readiness=SimpleNamespace(status='READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY')

    monkeypatch.setattr(D,'_read_json',fake_read_json)
    monkeypatch.setattr(D.P,'validate_external_package_binding',lambda *a,**k: package)
    monkeypatch.setattr(D,'load_authenticated_fit_payloads',lambda *a,**k: {})
    monkeypatch.setattr(D.A,'build_relational_qualification_adapter',lambda *a,**k: adapter)
    def fake_fit(_adapter):
        events.append('fit_complete')
        assert 'controller_open' not in events
        return fit_receipt
    monkeypatch.setattr(D.Q,'execute_blinded_fit',fake_fit)
    monkeypatch.setattr(D.R,'build_relational_gate_binding',lambda *a,**k: {'gate':'binding'})
    def fake_adjudicate(**kwargs):
        events.append('adjudicate')
        assert events.index('fit_complete') < events.index('controller_open') < events.index('adjudicate')
        return qualification
    monkeypatch.setattr(D.Q,'adjudicate_blinded_qualification',fake_adjudicate)
    monkeypatch.setattr(D.R,'assess_relational_successor_readiness',lambda **k: readiness)
    monkeypatch.setattr(D,'_write_json_atomic',lambda *a,**k: events.append('receipt_write'))

    receipt=D.run_disk_qualification(
        repo_root=ROOT,
        binding_path=binding_path,
        fit_dir=tmp_path,
        controller_manifest_path=controller_path,
        authenticated_package_sha256='a'*64,
        output_path=output_path,
    )
    assert receipt['qualification'] is qualification
    assert events == ['binding_open','fit_complete','controller_open','adjudicate','receipt_write']
