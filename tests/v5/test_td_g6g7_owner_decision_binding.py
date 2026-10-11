"""Item 1: the runtime-authorization gate refuses any authorization that is not bound to a verified, immutable
owner-decision record. Synthetic owner-decision fixtures only: no real owner decision is created or read."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_gate_fixtures as F  # noqa: E402

FLAGS = F.OWNER_DECISION_FLAGS
synthetic_owner_decision = F.synthetic_owner_decision


def build(tmp_path, monkeypatch, **decision_overrides):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    b.owner_decision = Path(tmp_path) / "owner_decision.json"
    decision = synthetic_owner_decision(m)
    decision.update(decision_overrides)
    for key in [k for k, v in decision.items() if v is None]:
        del decision[key]
    F.write_json(b.owner_decision, decision)
    F.rewrite_authorization(m, b, owner_decision_sha256=F.sha(b.owner_decision))
    return m, b


def gate(m, b, **overrides):
    overrides.setdefault("owner_decision_path", b.owner_decision)
    return F.call_gate(m, b, **overrides)


def test_constants_are_the_exact_owner_decision_contract():
    m = F.load_common()
    assert m.OWNER_DECISION_SCHEMA == "JEPA_TD_RELATIONAL_G6_G7_OWNER_DECISION_V1"
    assert m.OWNER_DECISION == "AUTHORIZE_G6_G7_INTEGRITY_ONLY"


def test_valid_synthetic_owner_decision_is_accepted_and_bound(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch)
    rec = gate(m, b)
    assert rec["owner_decision_sha256"] == F.sha(b.owner_decision)


def test_authorization_without_an_owner_decision_record_is_refused(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="owner-decision"):
        gate(m, b, owner_decision_path=None)


def test_missing_owner_decision_file_is_refused(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="owner-decision"):
        gate(m, b, owner_decision_path=Path(tmp_path) / "absent.json")


@pytest.mark.parametrize("field,value", [
    ("schema", "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2"),
    ("schema", None),
    ("decision", "AUTHORIZE_G6_G7_INTEGRITY_ONLY "),
    ("decision", "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY"),
    ("decision", None),
    ("authorized_pr259_preflight_driver_sha256", "0" * 64),
    ("authorized_pr259_preflight_driver_sha256", None),
    ("authorized_pr259_mapping_receipt_sha256", "0" * 64),
    ("authorized_pr259_mapping_receipt_sha256", None),
    ("qualified_implementation_commit_sha", "b" * 40),
    ("qualified_implementation_commit_sha", None),
])
def test_owner_decision_contract_fields_are_exact(tmp_path, monkeypatch, field, value):
    m, b = build(tmp_path, monkeypatch, **{field: value})
    with pytest.raises(RuntimeError, match="owner-decision"):
        gate(m, b)


@pytest.mark.parametrize("flag", FLAGS)
@pytest.mark.parametrize("value", [True, None, "false", 0])
def test_owner_decision_must_keep_each_flag_explicitly_false(tmp_path, monkeypatch, flag, value):
    m, b = build(tmp_path, monkeypatch, **{flag: value})
    with pytest.raises(RuntimeError, match="owner-decision"):
        gate(m, b)


def test_owner_decision_may_not_authorize_anything_else(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch, td56_corrected_replay_authorized=True)
    with pytest.raises(RuntimeError, match="owner-decision"):
        gate(m, b)


def test_owner_decision_edited_after_authorization_is_refused(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch)
    original = json.loads(b.owner_decision.read_text(encoding="utf-8"))
    F.write_json(b.owner_decision, original, indent=4)  # same semantics, different physical bytes
    with pytest.raises(RuntimeError, match="owner_decision_sha256"):
        gate(m, b)


def test_authorization_must_bind_the_owner_decision_sha(tmp_path, monkeypatch):
    m, b = build(tmp_path, monkeypatch)
    F.rewrite_authorization(m, b, owner_decision_sha256=None)  # authorization without owner_decision_sha256
    with pytest.raises(RuntimeError, match="owner_decision_sha256"):
        gate(m, b)


def _load_entrypoint(name):
    import importlib.util

    path = F.ROOT / "scripts" / "v5" / name
    spec = importlib.util.spec_from_file_location(f"entry_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("script", ["materialize_td_relational_corrected_sampleA_v2.py",
                                    "audit_td_relational_g7_s174_overlap_v2.py"])
def test_g6_and_g7_pass_the_owner_decision_to_the_gate_and_trace_its_sha(tmp_path, monkeypatch, script):
    from types import SimpleNamespace

    mod = _load_entrypoint(script)
    seen = {}

    def fake_gate(path, **kwargs):
        seen.update(kwargs)
        raise RuntimeError("stop after gate call")

    monkeypatch.setattr(mod.common, "load_runtime_authorization", fake_gate)
    args = SimpleNamespace(value_authorization="auth.json", preflight_result="p.json", mapping_receipt="m.json",
                           replay_manifest="r.csv", owner_decision="owner_decision.json")
    with pytest.raises(RuntimeError, match="stop after gate call"):
        mod.bind_execution(args)
    assert Path(seen["owner_decision_path"]) == Path("owner_decision.json")

    od = Path(tmp_path) / "od.json"
    od.write_text("{}\n", encoding="utf-8")
    files = {}
    for key in ("preflight_result", "mapping_receipt", "value_authorization"):
        files[key] = Path(tmp_path) / f"{key}.json"
        files[key].write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(mod.common, "code_identity", lambda a, b: {"implementation_commit_sha": "a" * 40})
    trace_args = SimpleNamespace(owner_decision=str(od), **{k: str(v) for k, v in files.items()})
    trace_fn = getattr(mod, "_authority_trace", None) or getattr(mod, "expected_authority_trace")
    trace = trace_fn(trace_args, {"schema": "s", "authorization": "t"}, Path("g6.py"), Path("g7.py"))
    assert trace["owner_decision_sha256"] == F.sha(od)
