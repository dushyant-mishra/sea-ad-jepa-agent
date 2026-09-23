"""Synthetic-only guarded molecular entrypoint tests. NEVER invokes the real executor."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/agent/run_full104_rare_tail_molecular_guarded_v1_20260922.py"


def module():
    spec = importlib.util.spec_from_file_location("guarded_molecular_entrypoint", GATE)
    assert spec is not None and spec.loader is not None
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def preflight(m):
    return {
        "schema": m.PREFLIGHT_SCHEMA,
        "state": m.EXPECTED_PREFLIGHT_STATE,
        "molecular_authority_sha256": "a" * 64,
        "sample_receipt_sha256": "b" * 64,
        "full104_manifest_sha256": "c" * 64,
        "outer_split_receipt_sha256": "d" * 64,
        "execution_contract_sha256": "e" * 64,
        "structural_receipt_file_sha256": "f" * 64,
        "source_hashes": {"runner_normalized_text_sha256": "1" * 64},
        "expression_opened": False,
        "count_matrices_opened": False,
        "training_authorized": False,
    }


def published(m, path):
    data = preflight(m)
    data["receipt_sha256"] = m.canonical_digest(data)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    return m.sha256_file(path)


def cases():
    return [
        {"panel": p, "source_code": s, "fold_index": f, "state": "PASS"}
        for p in (0, 1) for s in range(3) for f in range(4)
    ]


def result(m):
    x = preflight(m)
    return {
        "schema": "V5_FULL104_RARE_TAIL_MOLECULAR_RESULT_V1",
        "authority_sha256": x["molecular_authority_sha256"],
        "sample_receipt_sha256": x["sample_receipt_sha256"],
        "full104_manifest_sha256": x["full104_manifest_sha256"],
        "outer_split_receipt_sha256": x["outer_split_receipt_sha256"],
        "case_count": 24,
        "cases": cases(),
        "panel_results": [{}, {}],
        "terminal": m.PASS_TERMINAL,
        "molecular_prequalification_passed": True,
        "teacher_tail_evaluation_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
        "pathology_labels_used": False,
        "disease_labels_used": False,
        "native_class_labels_used": False,
        "rare_state_labels_used": False,
    }


def test_reviewed_receipt_exact_bytes_and_self_digest_recomputed(tmp_path, monkeypatch):
    m = module()
    p = tmp_path / "review.json"
    approved = published(m, p)
    body = json.loads(p.read_text(encoding="utf-8"))
    monkeypatch.setattr(m, "run_preflight_v2", lambda **_: body)
    assert m.verify_reviewed_preflight(
        reviewed_receipt=p, approved_file_sha256=approved, physical_inputs={}
    ) == body
    with pytest.raises(ValueError, match="externally reviewed immutable SHA"):
        m.verify_reviewed_preflight(
            reviewed_receipt=p, approved_file_sha256="0" * 64, physical_inputs={}
        )
    monkeypatch.setattr(m, "run_preflight_v2", lambda **_: {**body, "state": "DRIFTED"})
    with pytest.raises(ValueError, match="today's authenticated physical inputs"):
        m.verify_reviewed_preflight(
            reviewed_receipt=p, approved_file_sha256=approved, physical_inputs={}
        )


def test_v2_review_gateway_defaults_to_no_expression_access(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, "verify_reviewed_preflight", lambda **_: preflight(m))
    monkeypatch.setattr(m.subprocess, "run",
                        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected molecular run")))
    out = m.run_guarded(
        inputs={"repo_root": ROOT}, reviewed_receipt=tmp_path / "receipt",
        approved_file_sha256="0" * 64, out=tmp_path / "result",
        out_receipt=tmp_path / "result-receipt",
        execute_after_independent_review=False,
    )
    # A mocked verifier must supply an actual V2 self digest for the dry-run summary.
    # The positive full receipt verification is tested independently above.
    assert out["state"] == "GATE_VERIFIED__EXPRESSION_NOT_OPENED"
    assert not (tmp_path / "result").exists()
    assert not (tmp_path / "result.intent.json").exists()


def test_result_validator_rejects_missing_duplicate_wrong_terminal_and_promotion():
    m = module()
    baseline = result(m)
    assert m.validate_scientific_result(baseline, preflight=preflight(m), exit_code=0) == m.PASS_TERMINAL
    bad = {**baseline, "cases": baseline["cases"][:-1], "case_count": 23}
    with pytest.raises(ValueError, match="24"):
        m.validate_scientific_result(bad, preflight=preflight(m), exit_code=0)
    bad = {**baseline, "cases": baseline["cases"][:-1] + [baseline["cases"][0]]}
    with pytest.raises(ValueError, match="duplicate"):
        m.validate_scientific_result(bad, preflight=preflight(m), exit_code=0)
    bad = {**baseline, "terminal": m.FAIL_TERMINAL}
    with pytest.raises(ValueError, match="disagrees"):
        m.validate_scientific_result(bad, preflight=preflight(m), exit_code=0)
    bad = {**baseline, "training_authorized": True}
    with pytest.raises(ValueError, match="protected flag"):
        m.validate_scientific_result(bad, preflight=preflight(m), exit_code=0)


def test_atomic_synthetic_success_creates_one_result_one_receipt_and_intent(tmp_path, monkeypatch):
    m = module()
    payload = preflight(m)
    payload["receipt_sha256"] = m.canonical_digest(payload)
    monkeypatch.setattr(m, "verify_reviewed_preflight", lambda **_: payload)
    real_hash = m.normalized_text_sha256
    monkeypatch.setattr(
        m, "normalized_text_sha256",
        lambda p: payload["source_hashes"]["runner_normalized_text_sha256"]
        if p.name == "run_full104_rare_tail_molecular_prequalification_v1_20260922.py"
        else real_hash(p),
    )
    called = []

    def fake_runner(command, **kwargs):
        assert command[:3] == [m.sys.executable, "-m", m.RUNNER_MODULE]
        assert kwargs["check"] is False
        stage = Path(command[command.index("--out") + 1])
        stage.write_text(json.dumps(result(m)), encoding="utf-8")
        called.append(stage)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(m.subprocess, "run", fake_runner)
    dest = tmp_path / "synthetic-result.json"
    receipt = tmp_path / "synthetic-evidence.json"
    actual = m.run_guarded(
        inputs={"repo_root": ROOT, "authority_path": ROOT / "not-used-authority",
                "sample_dir": tmp_path, "split_receipt_path": tmp_path,
                "level4_root": tmp_path, "target_eligibility_path": tmp_path},
        reviewed_receipt=tmp_path / "reviewed.json",
        approved_file_sha256="2" * 64, out=dest, out_receipt=receipt,
        execute_after_independent_review=True,
    )
    assert len(called) == 1
    assert dest.is_file() and receipt.is_file()
    assert (tmp_path / "synthetic-result.json.intent.json").is_file()
    assert actual["molecular_result_file_sha256"] == m.sha256_file(dest)
    assert actual["receipt_sha256"] == m.canonical_digest({
        k: v for k, v in actual.items() if k != "receipt_sha256"
    })
    assert actual["training_authorized"] is False


def test_crash_creates_exclusive_intent_and_cannot_repeat(tmp_path, monkeypatch):
    m = module()
    payload = preflight(m)
    payload["receipt_sha256"] = m.canonical_digest(payload)
    monkeypatch.setattr(m, "verify_reviewed_preflight", lambda **_: payload)
    monkeypatch.setattr(
        m, "normalized_text_sha256", lambda _: payload["source_hashes"]["runner_normalized_text_sha256"],
    )
    calls = []
    def fail_runner(*args, **kwargs):
        calls.append(True)
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(m.subprocess, "run", fail_runner)
    kwargs = dict(
        inputs={"repo_root": ROOT, "authority_path": ROOT, "sample_dir": ROOT,
                "split_receipt_path": ROOT, "level4_root": ROOT,
                "target_eligibility_path": ROOT},
        reviewed_receipt=ROOT, approved_file_sha256="a" * 64,
        out=tmp_path / "result.json", out_receipt=tmp_path / "receipt.json",
        execute_after_independent_review=True,
    )
    with pytest.raises(RuntimeError, match="failed mechanically"):
        m.run_guarded(**kwargs)
    assert (tmp_path / "result.json.intent.json").is_file()
    with pytest.raises(FileExistsError):
        m.run_guarded(**kwargs)
    assert len(calls) == 1
