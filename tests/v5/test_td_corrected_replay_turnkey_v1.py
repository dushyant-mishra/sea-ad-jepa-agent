"""Corrected TD replay turnkey package: contract, predecessors, outcome-blind QUALIFY, replay-only authority,
one-shot marker, orchestrator (stubbed executors), evidence validator, launcher text and adapter mechanics.

Synthetic fixtures only. No corrected value is opened and no replay kernel runs. Tests that need the local TD41-TD58
archive are skipped when it is absent; the real-file QUALIFY covers them.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))
import td_corrected_replay_adapter_v1 as A  # noqa: E402
import td_corrected_replay_evidence_v1 as EV  # noqa: E402
import td_corrected_replay_execute_v1 as X  # noqa: E402
import td_corrected_replay_gate_v1 as G  # noqa: E402

CONTRACT = ROOT / G.CONTRACT_REL
LAUNCHER = ROOT / "scripts" / "v5" / "run_td_corrected_replay_once.sh"
ARCHIVE = Path("D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip")
needs_archive = pytest.mark.skipif(not ARCHIVE.is_file(), reason="local TD41-TD58 archive not present (CI)")


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wjson(p: Path, rec: dict) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


@pytest.fixture()
def contract() -> dict:
    return G.load_contract(CONTRACT)


# ------------------------------------------------------------------------------------------------------- contract
def test_contract_keeps_g7_not_estimable_and_never_pass(contract, tmp_path):
    for change in ({"terminal": "PASS_TD_G7_S174_EXACT_OVERLAP"}, {"is_pass": True}):
        c = copy.deepcopy(contract)
        c["predecessors"]["g7"].update(change)
        with pytest.raises(G.GateError, match="NOT_ESTIMABLE and never PASS"):
            G.load_contract(wjson(tmp_path / "c.json", c))


@pytest.mark.parametrize("path,value,match", [
    (("predecessors", "g7_diagnostic", "classification"), "IDENTIFIER_NAMESPACE_MISMATCH", "diagnostic class"),
    (("predecessors", "g7_diagnostic", "claims_value_agreement"), True, "value agreement"),
    (("prerequisite", "g7_pass"), True, "G7 PASS"),
    (("downstream_authority", "td60_authorized"), True, "downstream authority"),
    (("downstream_authority", "training_authorized"), True, "downstream authority"),
    (("downstream_authority", "stage4_authorized"), True, "downstream authority"),
    (("downstream_authority", "target_selection_authorized"), True, "downstream authority"),
    (("stage_order",), ["TD56", "TD57C", "TD57B", "TD59"], "stage order"),
    (("replay_science_frozen",), False, "freeze replay science"),
])
def test_contract_refuses_any_weakening(contract, tmp_path, path, value, match):
    c = copy.deepcopy(contract)
    node = c
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    with pytest.raises(G.GateError, match=match):
        G.load_contract(wjson(tmp_path / "c.json", c))


def test_contract_binds_the_frozen_executors_and_the_amendment(contract):
    ex = contract["executors"]
    assert ex["TD57B"]["sha256"] == "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e"
    assert ex["TD57B"]["fast_wrapper_bound"] is False
    assert ex["TD57C"]["sha256"] == "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c"
    assert ex["TD59"]["sha256"] == "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085"
    assert {k: v["sha256"][:8] for k, v in ex["TD56"]["by_source"].items()} == {"HVS": "a1ea8653", "NPH52": "090134f0", "SEA_AD": "c77ceac2"}
    amend = contract["prerequisite_amendment"]
    assert sha(ROOT / amend["path"]) == amend["sha256"]
    assert contract["predecessors"]["g7_diagnostic"]["evidence_commit"].startswith("0b50938e")
    assert len(contract["predecessors"]["g7_diagnostic"]["evidence_commit"]) == 40


def test_validate_contract_refuses_altered_or_ambiguous_executor_bytes(contract, tmp_path):
    c = copy.deepcopy(contract)
    zpath = tmp_path / "arch.zip"
    members = {v["archive_path"]: b"exec-" + k.encode() for k, v in c["executors"]["TD56"]["by_source"].items()}
    members[c["executors"]["TD57B"]["archive_path"]] = b"td57b"
    members[c["executors"]["TD57C"]["archive_path"]] = b"td57c"
    with zipfile.ZipFile(zpath, "w") as z:
        for n, b in members.items():
            z.writestr(n, b)
    c["archive"]["sha256"] = sha(zpath)
    for v in c["executors"]["TD56"]["by_source"].values():
        v["sha256"] = hashlib.sha256(members[v["archive_path"]]).hexdigest()
    for s in ("TD57B", "TD57C"):
        c["executors"][s]["sha256"] = hashlib.sha256(members[c["executors"][s]["archive_path"]]).hexdigest()
    G.validate_contract(c, repo_root=ROOT, archive=zpath)                       # exact bytes resolve
    c2 = copy.deepcopy(c)
    c2["executors"]["TD57C"]["sha256"] = "0" * 64                                  # altered executor identity
    with pytest.raises(G.GateError, match="not the frozen executors"):
        G.validate_contract(c2, repo_root=ROOT, archive=zpath)
    with zipfile.ZipFile(zpath, "a") as z, pytest.warns(UserWarning):              # a second, ambiguous copy
        z.writestr(c["executors"]["TD57B"]["archive_path"], b"other")
    c["archive"]["sha256"] = sha(zpath)
    with pytest.raises(G.GateError, match="ambiguous"):
        G.validate_contract(c, repo_root=ROOT, archive=zpath)


def test_validate_contract_refuses_a_changed_environment_lock(contract):
    c = copy.deepcopy(contract)
    c["execution_environment"]["lock"]["sha256"] = "0" * 64
    with pytest.raises(G.GateError, match="environment lock file changed"):
        G.validate_contract(c, repo_root=ROOT, archive=Path("unused"))


@needs_archive
def test_contract_builder_regenerates_the_committed_contract_byte_for_byte():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/v5/build_td_corrected_replay_contract_v1.py"),
                        "--archive", str(ARCHIVE), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@needs_archive
def test_validate_contract_on_the_real_archive(contract):
    out = G.validate_contract(contract, repo_root=ROOT, archive=ARCHIVE)
    assert out["td59_successor_sha256"].startswith("870ddea0")


# ---------------------------------------------------------------------------------------------------- predecessors
def predecessor_world(tmp_path, contract):
    c = copy.deepcopy(contract)
    g6 = tmp_path / "g6"
    g6.mkdir()
    for name in c["predecessors"]["g6"]["artifact_sha256"]:
        (g6 / name).write_bytes(b"g6:" + name.encode())
    c["predecessors"]["g6"]["artifact_sha256"] = {n: sha(g6 / n) for n in c["predecessors"]["g6"]["artifact_sha256"]}
    acc = wjson(tmp_path / "acc.json", {"external_audit_disposition": G.G6_ACCEPT_DISPOSITION,
                                        "implementation_commit_sha": c["predecessors"]["g6"]["producer_commit"]})
    c["predecessors"]["g6"]["external_acceptance_sha256"] = sha(acc)
    g7 = tmp_path / "g7"
    marker = wjson(g7 / "G7_RECEIPT.json.STARTED_NOT_A_PASS.json", {"status": "STARTED_NOT_A_PASS"})
    receipt = wjson(g7 / "G7_RECEIPT.json", {
        "status": G.G7_TERMINAL, "natural_overlap_cells": 0, "checked_cell_address_entries": 0, "mismatches": 0,
        "no_overlap_is_not_pass": True, "authority_trace": {"implementation_commit_sha": c["predecessors"]["g7"]["implementation_commit"]},
        "biological_replay_authorized": False, "target_selection_authorized": False, "td60_authorized": False, "training_authorized": False})
    c["predecessors"]["g7"].update(marker_sha256=sha(marker), receipt_sha256=sha(receipt))
    tr = wjson(tmp_path / "transforms.json", {"classification": G.DIAGNOSTIC_CLASS, "spec_sha256": c["predecessors"]["g7_diagnostic"]["spec_sha256"],
                                               "g7_authority_created": False, "biological_replay_authorized": False})
    c["predecessors"]["g7_diagnostic"]["transforms_sha256"] = sha(tr)
    res = tmp_path / "result.md"
    res.write_text(f"Classification: {G.DIAGNOSTIC_CLASS}. It is not a G7 rerun. It is not evidence that any count disagrees.\n")
    c["predecessors"]["g7_diagnostic"]["result_sha256"] = sha(res)
    spent = wjson(tmp_path / "spent.json", {"spent_authority": [{"sha256": s} for s in c["predecessors"]["spent_authority_sha256"][3:]]})
    kw = dict(g6_namespace=g6, g6_acceptance=acc, g7_namespace=g7, diagnostic_transforms=tr, diagnostic_result=res, spent_record=spent)
    return c, kw


def test_exact_predecessors_close_the_prerequisite_without_a_g7_pass(contract, tmp_path):
    c, kw = predecessor_world(tmp_path, contract)
    r = G.authenticate_predecessors(c, **kw)
    assert r["technical_prerequisite_closed"] is True and r["g7_pass"] is False
    assert r["closure_reason"] == "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS"


def test_g7_relabelled_pass_is_refused_even_with_matching_hashes(contract, tmp_path):
    c, kw = predecessor_world(tmp_path, contract)
    rec = json.loads((kw["g7_namespace"] / "G7_RECEIPT.json").read_text())
    rec["status"] = "PASS_TD_G7_S174_EXACT_OVERLAP"
    c["predecessors"]["g7"]["receipt_sha256"] = sha(wjson(kw["g7_namespace"] / "G7_RECEIPT.json", rec))
    with pytest.raises(G.GateError, match="terminal is not"):
        G.authenticate_predecessors(c, **kw)


@pytest.mark.parametrize("attack,match", [
    ("g6_file", "accepted G6 artifact changed"), ("g6_extra", "accepted five files"), ("acceptance", "not 89932183"),
    ("g7_receipt", "marker/receipt changed"), ("missing_diagnostic", "missing diagnostic evidence"),
    ("wrong_class", "diagnostic class/spec"), ("diag_authority", "no authority"), ("spent", "spent-authority record"),
    ("diag_result", "diagnostic result document changed"),
])
def test_predecessor_attacks_fail_closed(contract, tmp_path, attack, match):
    c, kw = predecessor_world(tmp_path, contract)
    if attack == "g6_file":
        (kw["g6_namespace"] / "MANIFEST.json").write_bytes(b"tampered")
    elif attack == "g6_extra":
        (kw["g6_namespace"] / "EXTRA").write_bytes(b"x")
    elif attack == "acceptance":
        kw["g6_acceptance"].write_text("{}")
    elif attack == "g7_receipt":
        (kw["g7_namespace"] / "G7_RECEIPT.json").write_text("{}")
    elif attack == "missing_diagnostic":
        kw["diagnostic_transforms"] = tmp_path / "absent.json"
        c["predecessors"]["g7_diagnostic"]["transforms_sha256"] = "0" * 64
    elif attack in ("wrong_class", "diag_authority"):
        rec = json.loads(kw["diagnostic_transforms"].read_text())
        rec.update({"classification": "IDENTIFIER_NAMESPACE_MISMATCH"} if attack == "wrong_class" else {"g7_authority_created": True})
        c["predecessors"]["g7_diagnostic"]["transforms_sha256"] = sha(wjson(kw["diagnostic_transforms"], rec))
    elif attack == "spent":
        wjson(kw["spent_record"], {"spent_authority": [{"sha256": "f" * 64}]})
    elif attack == "diag_result":
        kw["diagnostic_result"].write_text(kw["diagnostic_result"].read_text() + "edited after the diagnostic\n")
    with pytest.raises((G.GateError, FileNotFoundError), match=match):
        G.authenticate_predecessors(c, **kw)


# --------------------------------------------------------------------------------- structural estimability (cheap)
def _structure(monkeypatch, *, donors_per_source=10, mutate=None):
    hist, view = {}, {"global_row": [], "source": [], "donor": [], "operator": []}
    g = 0
    for s in A.SOURCES:
        rows, dons, ops = [], [], []
        for d in range(donors_per_source):
            for _ in range(5):
                rows.append(g); dons.append(f"{s}_d{d}"); ops.append(d % 2); g += 1
        hist[s] = {"global_row": np.asarray(rows), "donor": np.asarray(dons, dtype=object), "operator": np.asarray(ops)}
        view["global_row"] += rows; view["source"] += [s] * len(rows); view["donor"] += dons; view["operator"] += ops
    view = {k: np.asarray(v) for k, v in view.items()}
    if mutate:
        mutate(view)
    monkeypatch.setattr(A, "historical_td50", lambda archive, s: hist[s])
    monkeypatch.setattr(A, "metadata_view", lambda meta, freeze: view)


def test_structural_estimability_requires_the_historical_comparison_populations(contract, monkeypatch):
    _structure(monkeypatch)
    out = G.structural_estimability(contract, g6_meta=Path("m"), sample_freeze=Path("f"), archive=Path("a"))
    assert all(v["structure_equals_historical_td50"] and v["donors_with_stratum_ge_4"] == 10 for v in out.values())


def test_a_changed_donor_identity_is_refused(contract, monkeypatch):
    _structure(monkeypatch, mutate=lambda v: v["donor"].__setitem__(0, "OTHER"))
    with pytest.raises(G.GateError, match="donor identities differ"):
        G.structural_estimability(contract, g6_meta=Path("m"), sample_freeze=Path("f"), archive=Path("a"))


def test_a_comparison_population_below_the_floor_stops_qualification(contract, monkeypatch):
    _structure(monkeypatch, donors_per_source=5)
    with pytest.raises(G.GateError, match="below"):
        G.structural_estimability(contract, g6_meta=Path("m"), sample_freeze=Path("f"), archive=Path("a"))


def test_decisions_stay_pending_until_ratified_exactly(contract, tmp_path):
    assert G.ratification_state(contract, None)["status"] == "PENDING_OWNER_RATIFICATION"
    d = contract["decisions_requiring_owner_ratification"]
    good = {"schema": G.RATIFICATION_SCHEMA, "contract_sha256": sha(CONTRACT),
            "ratified": {"detected_field": d["detected_field"]["proposed"], "routing_input_rule": d["routing_input_rule"]["proposed"]}}
    assert G.ratification_state(contract, wjson(tmp_path / "r.json", good))["status"] == "RATIFIED"
    bad = copy.deepcopy(good)
    bad["ratified"]["detected_field"] = "detected_historical"
    with pytest.raises(G.GateError, match="detected field differs"):
        G.ratification_state(contract, wjson(tmp_path / "b.json", bad))
    stale = copy.deepcopy(good)
    stale["contract_sha256"] = "0" * 64
    with pytest.raises(G.GateError, match="not bound to this contract"):
        G.ratification_state(contract, wjson(tmp_path / "s.json", stale))


# ------------------------------------------------------------------------------------------------------ authority
def authority_world(tmp_path, contract, code=None, equiv=None):
    code = code or {"implementation_commit_sha": "c" * 40, "code_sha256": "d" * 64}
    base = {"scope": "CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY", "contract_sha256": sha(CONTRACT),
            "implementation_commit_sha": code["implementation_commit_sha"], **{k: False for k in G.DOWNSTREAM}}
    owner = wjson(tmp_path / "owner.json", {"schema": G.AUTH_SCHEMAS["owner"], **base})
    equiv = equiv or wjson(tmp_path / "equiv_receipt.json", {"schema": "JEPA_TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1"})
    runtime = wjson(tmp_path / "runtime.json", {"schema": G.AUTH_SCHEMAS["runtime"], **base, "owner_decision_sha256": sha(owner),
                                                 "code_sha256": code["code_sha256"], "equivalence_receipt_sha256": sha(equiv),
                                                 "environment_lock_sha256": contract["execution_environment"]["lock"]["sha256"]})
    op = wjson(tmp_path / "op.json", {"schema": G.AUTH_SCHEMAS["operational"], **base, "owner_decision_sha256": sha(owner),
                                       "runtime_authorization_sha256": sha(runtime), "corrected_replay_execution_authorized": True,
                                       "single_attempt": True, "namespace": contract["namespace"]["root_windows"]})
    acc = wjson(tmp_path / "acc.json", {"schema": G.AUTH_SCHEMAS["acceptance"], **base, "operational_authorization_sha256": sha(op),
                                         "disposition": "ACCEPT_TD_CORRECTED_REPLAY_LAUNCH_PACKAGE__EXECUTE_ONCE",
                                         "code_sha256": code["code_sha256"], "corrected_replay_execution_authorized": True})
    return code, owner, runtime, op, acc


def _auth(contract, code, owner, runtime, op, acc=None, op_sha=None, acc_sha=None):
    return G.validate_authority(contract, owner=owner, runtime=runtime, operational=op, acceptance=acc,
                                expected_operational_sha=op_sha or sha(op), expected_acceptance_sha=acc_sha or (sha(acc) if acc else None),
                                code=code, equivalence_receipt=Path(owner).parent / "equiv_receipt.json")


def test_fresh_replay_only_authority_passes(contract, tmp_path):
    code, owner, runtime, op, acc = authority_world(tmp_path, contract)
    assert _auth(contract, code, owner, runtime, op, acc)["authority_check"] == "PASS"


@pytest.mark.parametrize("record,change,match", [
    ("op", {"td60_authorized": True}, "downstream flag"),
    ("owner", {"training_authorized": True}, "downstream flag"),
    ("runtime", {"g6_execution_authorized": True}, "downstream flag"),
    ("op", {"target_tournament_authorized": True}, "beyond the replay"),
    ("op", {"scope": "ANY"}, "replay-only"),
    ("owner", {"contract_sha256": "0" * 64}, "this contract"),
    ("runtime", {"implementation_commit_sha": "e" * 40}, "this implementation"),
    ("op", {"single_attempt": False}, "exactly one"),
    ("op", {"namespace": "D:/elsewhere"}, "namespace"),
    ("runtime", {"equivalence_receipt_sha256": "0" * 64}, "equivalence receipt"),      # review finding 4
    ("runtime", {"environment_lock_sha256": "0" * 64}, "environment lock"),            # review finding 4
])
def test_stale_or_widened_authority_is_refused(contract, tmp_path, record, change, match):
    code, owner, runtime, op, acc = authority_world(tmp_path, contract)
    path = {"owner": owner, "runtime": runtime, "op": op}[record]
    rec = json.loads(path.read_text())
    rec.update(change)
    wjson(path, rec)
    with pytest.raises(G.GateError, match=match):
        _auth(contract, code, owner, runtime, op)


def test_spent_authority_and_wrong_shas_are_refused(contract, tmp_path):
    code, owner, runtime, op, acc = authority_world(tmp_path, contract)
    c = copy.deepcopy(contract)
    c["predecessors"]["spent_authority_sha256"].append(sha(owner))
    with pytest.raises(G.GateError, match="spent authority"):
        _auth(c, code, owner, runtime, op)
    with pytest.raises(G.GateError, match="not the audited SHA"):
        _auth(contract, code, owner, runtime, op, op_sha="0" * 64)
    with pytest.raises(G.GateError, match="not the given SHA"):
        _auth(contract, code, owner, runtime, op, acc, acc_sha="0" * 64)
    with pytest.raises(G.GateError, match="exact code identity"):
        _auth(contract, {**code, "code_sha256": "9" * 64}, owner, runtime, op)


def test_begin_attempt_is_exclusive_and_spends_the_namespace(tmp_path):
    marker = G.begin_attempt(tmp_path / "ns", {"contract_sha256": "x"})
    rec = json.loads(marker.read_text())
    assert rec["status"] == "STARTED_NOT_A_RESULT" and all(rec[k] is False for k in G.DOWNSTREAM)
    assert json.loads(G.ledger_path(tmp_path / "ns").read_text())["status"] == "ATTEMPT_SPENT"
    with pytest.raises(G.GateError, match="already exists"):
        G.begin_attempt(tmp_path / "ns", {})
    os.chmod(marker, 0o666)
    shutil.rmtree(tmp_path / "ns")                      # review finding 5: deleting the namespace does not re-enable it
    with pytest.raises(G.GateError, match="already exists"):
        G.begin_attempt(tmp_path / "ns", {})
    assert not (tmp_path / "ns").exists()


def test_qualify_refuses_a_spent_attempt_ledger(contract, tmp_path, monkeypatch):
    for name in ("validate_contract", "validate_equivalence", "authenticate_predecessors", "structural_estimability"):
        monkeypatch.setattr(G, name, lambda *a, **k: {})
    monkeypatch.setattr(A, "check_support_bundle", lambda b: {})
    G.ledger_path(tmp_path / "ns").write_text("{}")
    args = type("Args", (), dict(archive="a", equivalence_receipt="e", implementation_commit="c" * 40, g6_namespace=str(tmp_path),
                                  g6_acceptance="x", g7_namespace="x", diagnostic_transforms="x", diagnostic_result="x",
                                  spent_record="x", sample_freeze="f", namespace=str(tmp_path / "ns"), support_bundle="b",
                                  ratification=None))
    with pytest.raises(G.GateError, match="attempt ledger exists"):
        G.qualify(contract, args=args)


# ------------------------------------------------------------------------------------------- orchestrator (stubbed)
def test_outcome_classes_follow_the_frozen_mapping(tmp_path, contract):
    def td56(obs, p95):
        p = tmp_path / f"r{obs}_{p95}.npz"
        np.savez(p, obs=obs, p95=p95)
        return X.classify_td56(p)
    assert (td56(0.8, 0.5), td56(0.4, 0.5), td56(float("nan"), 0.5), td56(0.8, float("nan"))) == ("PASS", "FAIL", "NOT_ESTIMABLE", "NOT_ESTIMABLE")
    assert X.classify_td56(tmp_path / "absent.npz") == "IMPLEMENTATION_FAILURE"
    pats = contract["invocation_outcome_mapping"]["support_patterns"]
    err, out = tmp_path / "e.txt", tmp_path / "o.json"
    cm = lambda rc: X.classify_module(rc, err, out, pats, source="HVS", panel=0)  # noqa: E731
    err.write_text("Traceback\nRuntimeError: observed split 0 half 1 has <4 measurable donors\n")
    assert cm(1) == "NOT_ESTIMABLE"
    err.write_text("RuntimeError: array SHA mismatch data.npy\n")
    assert cm(1) == "IMPLEMENTATION_FAILURE"
    # review finding 6: exit 0/2 counts only when the executor's own result agrees for this source and panel
    err.write_text("usage: td57b.py [-h]\ntd57b.py: error: unrecognized arguments\n")
    assert (cm(0), cm(2)) == ("IMPLEMENTATION_FAILURE", "IMPLEMENTATION_FAILURE")      # e.g. an argparse exit 2
    wjson(out, {"status": "PASS", "source": "HVS", "panel": 0})
    assert (cm(0), cm(2)) == ("PASS", "IMPLEMENTATION_FAILURE")
    wjson(out, {"status": "FAIL", "source": "HVS", "panel": 0})
    assert (cm(0), cm(2)) == ("IMPLEMENTATION_FAILURE", "FAIL")
    wjson(out, {"status": "FAIL", "source": "NPH52", "panel": 0})
    assert cm(2) == "IMPLEMENTATION_FAILURE"
    assert X.historical_comparison("TD56", "IMPLEMENTATION_FAILURE") == "NOT_COMPARABLE__IMPLEMENTATION_FAILURE"
    assert X.historical_comparison("TD57C", "FAIL") == "QUALITATIVE_HISTORICAL_CONCLUSION_REPRODUCED"


def _stage(invs):
    return {"status": X.stage_status([i["outcome"] for i in invs]), "invocations": invs}


ORDERS = {"TD56": [(None, s) for s in A.SOURCES], **{st: [(p, s) for p in (0, 1) for s in A.SOURCES] for st in ("TD57B", "TD57C", "TD59")}}
_p = lambda panel, s, o: {"panel": panel, "source": s, "outcome": o}  # noqa: E731
_P0 = [_p(0, "HVS", "PASS"), _p(0, "NPH52", "PASS"), _p(0, "SEA_AD", "PASS")]


def test_threshold_discordance_is_failure_to_establish_universality_not_source_heterogeneity():
    # audit of PR #307, item 8: a PASS/FAIL straddle is not automatically formal source heterogeneity
    rec = X.source_record(_stage([_p(0, "HVS", "PASS"), _p(0, "NPH52", "FAIL")]), ORDERS["TD57C"])
    assert rec["universal_qualification"] == "NOT_ESTABLISHED__AN_OBSERVED_EXECUTION_FAILED_ITS_FROZEN_GATE"
    assert rec["cross_source_pattern"] == "THRESHOLD_DISCORDANCE_OBSERVED__UNIVERSALITY_NOT_ESTABLISHED"
    assert rec["threshold_discordance"] == [{"panel": 0, "passed": ["HVS"], "failed": ["NPH52"]}]
    assert rec["source_heterogeneity"] == X.SOURCE_HETEROGENEITY == "UNRESOLVED__NO_PROSPECTIVELY_FROZEN_DIRECT_BETWEEN_SOURCE_TEST"
    straddles = ({"TD56": _stage([_p(None, "HVS", "PASS"), _p(None, "NPH52", "PASS"), _p(None, "SEA_AD", "FAIL")])},
                 {"TD57C": _stage([_p(0, "HVS", "PASS"), _p(0, "NPH52", "FAIL")])},
                 {"TD59": _stage(_P0 + [_p(1, "HVS", "PASS"), _p(1, "NPH52", "FAIL")])})
    assert all(X.routing_universal_source(st) == "PASS" for st in straddles)          # never FAIL
    assert X.routing_universal_source({"TD59": _stage([_p(0, "HVS", "PASS"), _p(0, "NPH52", "NOT_ESTIMABLE")])}) == "NOT_ESTIMABLE"


def test_source_order_censoring_is_missing_evidence_not_agreement():
    rec = X.source_record(_stage([_p(0, "HVS", "FAIL")]), ORDERS["TD57C"])
    assert [(u["panel"], u["source"]) for u in rec["unobserved"]] == [(0, "NPH52"), (0, "SEA_AD"), (1, "HVS"), (1, "NPH52"), (1, "SEA_AD")]
    assert all(u["evidence"] == X.UNOBSERVED for u in rec["unobserved"]) and not rec["threshold_discordance"]
    assert rec["cross_source_pattern"] == "NO_DISCORDANCE_OBSERVED__UNOBSERVED_SOURCES_ARE_MISSING_EVIDENCE"
    assert "AGREE" not in json.dumps(rec).upper()
    full = X.source_record(_stage(_P0 + [_p(1, s, "PASS") for s in A.SOURCES]), ORDERS["TD57C"])
    assert full["universal_qualification"] == "ESTABLISHED__EVERY_PLANNED_SOURCE_AND_PANEL_OBSERVED_PASS" and not full["unobserved"]


def _all_outcome_combinations():
    """The complete logical outcome space under the frozen sequential stop (7 x 13^3 = 15,379)."""
    seqs = {}
    for st, order in ORDERS.items():
        out = [[(pp, s, "PASS") for pp, s in order]]
        for k in range(len(order)):
            for bad in ("FAIL", "NOT_ESTIMABLE"):
                out.append([(pp, s, "PASS") for pp, s in order[:k]] + [(order[k][0], order[k][1], bad)])
        seqs[st] = out
    for combo in itertools.product(*(seqs[st] for st in ORDERS)):
        yield {st: _stage([_p(pp, s, o) for pp, s, o in seq]) for st, seq in zip(ORDERS, combo)}


def test_over_the_whole_outcome_space_the_route_follows_only_the_frozen_stage_hierarchy():
    import td_corrected_replay_routing_v2 as R
    by_status, n = {}, 0
    for stages in _all_outcome_combinations():
        n += 1
        ri = X.routing_inputs(stages)
        assert ri["universal_source"] != "FAIL"
        out = R.interpret_corrected_replay(**ri)
        assert all(out[k] is False for k in ("corrected_replay_authorized", "target_selected", "representation_selected",
                                             "td60_authorized", "stage4_authorized", "training_authorized"))
        st = {k: v["status"] for k, v in stages.items()}
        by_status.setdefault(tuple(st.values()), set()).add(out["biological_state"])
        # the decisive stage of the frozen hierarchy; an upstream NOT_ESTIMABLE is never strengthened by a later straddle
        decisive = next((st[k] for k, good in (("TD56", "PASS"), ("TD57B", "PASS"), ("TD57C", "FAIL")) if st[k] != good), st["TD59"])
        if decisive == "NOT_ESTIMABLE":
            assert out["v4_relational_status"] == "NOT_ESTIMABLE"
        assert out["candidate_routes"]["C6_SHARED_QUERY_COMPOSITE"] == "ACTIVE_SUBJECT_TO_C1_C3"
    assert n == 15379
    assert all(len(v) == 1 for v in by_status.values())          # a function of the four stage statuses only


PASS_TERMINAL = "PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED"


def preflight_world(tmp_path, ns, *, terminal=PASS_TERMINAL, with_acceptance=True, detected=None, compact=False,
                    forge_check=False):
    """The launch record and authority bytes the orchestrator requires."""
    c = G.load_contract(CONTRACT)
    rec_dir = tmp_path / "rec"
    rec_dir.mkdir(parents=True, exist_ok=True)
    d = c["decisions_requiring_owner_ratification"]
    rec = {"schema": G.RATIFICATION_SCHEMA, "contract_sha256": sha(CONTRACT),
           "ratified": {"detected_field": detected or d["detected_field"]["proposed"], "routing_input_rule": d["routing_input_rule"]["proposed"]}}
    rat = rec_dir / "ratification.json"
    rat.write_text(json.dumps(rec, separators=(",", ":")) if compact else json.dumps(rec, indent=2, sort_keys=True))
    q = wjson(rec_dir / "QUALIFY_RECEIPT.json", {
        "terminal": terminal, "contract_sha256": sha(CONTRACT), "implementation_commit_sha": "c" * 40,
        "namespace_fresh": str(ns), "ratification": {"status": "RATIFIED", "ratification_sha256": sha(rat)}})
    code = {"implementation_commit_sha": "c" * 40, "code_sha256": G.code_identity()["code_sha256"]}
    equiv = _equivalence(rec_dir, c)
    _, owner, runtime, op, acc = authority_world(rec_dir, c, code=code, equiv=equiv)
    shas = {"owner": sha(owner), "runtime": sha(runtime), "operational": sha(op), **({"acceptance": sha(acc)} if with_acceptance else {})}
    if forge_check:
        shas = {k: "1" * 64 for k in shas}
    au = wjson(rec_dir / "AUTHORITY_CHECK.json", {"authority_check": "PASS", "authority_sha256": shas,
                                                 "code_sha256": code["code_sha256"], "implementation_commit_sha": "c" * 40})
    return {"qualify_receipt": q, "authority_check": au, "ratification": rat, "owner": owner, "runtime": runtime,
            "operational": op, "acceptance": acc, "equivalence_receipt": equiv}


def run_stubbed(tmp_path, monkeypatch, plan: dict, *, support_ok=True, bad_input=None, **world):
    """plan: (stage, source, panel) -> outcome; TD56 entries as (obs, p95) or 'crash'; module entries may also be
    'ARGPARSE' (exit 2, no result written) or 'RAISE' (the orchestrator itself dies mid-attempt)."""
    calls = []
    ns = tmp_path / "ns"
    marker = ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    fake = hashlib.sha256(b"#exec\n").hexdigest()           # the stubbed archive members' bytes stand in for the executors
    real_load = G.load_contract
    def load_contract(path):
        c = real_load(path)
        for e in c["executors"]["TD56"]["by_source"].values():
            e["sha256"] = fake
        for st in ("TD57B", "TD57C"):
            c["executors"][st]["sha256"] = fake
        return c
    monkeypatch.setattr(G, "load_contract", load_contract)
    def require_sha(path, expected, label):
        calls.append(("sha", label, marker.exists()))
        if label == bad_input:
            raise A.AdapterError(f"{label} SHA mismatch")
    monkeypatch.setattr(A, "require_sha", require_sha)
    def support(bundle):
        calls.append(("support", marker.exists()))
        if not support_ok:
            raise A.AdapterError("support bundle SHA mismatch")
        return {"support_bundle_sha256": "s"}
    monkeypatch.setattr(A, "check_support_bundle", support)
    monkeypatch.setattr(A, "corrected_cache", lambda *a, **k: (calls.append(("corrected_cache", marker.exists(), k["detected_field"])), {"meta": {}})[1])
    def write_inputs(cache, archive, bundle, mnt):
        shas = {}
        for rel in sorted(EV.REQUIRED_INPUTS):
            f = mnt / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(rel.encode())
            shas[rel] = sha(f)
        return shas
    monkeypatch.setattr(A, "write_inputs", write_inputs)
    monkeypatch.setattr(A, "archive_member", lambda archive, name, sha_=None: b"#exec\n")
    def run_executor(*, kind, executor, executor_sha, mnt, input_sha, python, source=None, panel=None, output=None, stdout, stderr, timeout=None):
        stage = "TD56" if kind == "td56" else Path(output).name.split("_")[0]
        if stage == "TD56":
            source = Path(stdout).name[len("TD56_"):-len(".stdout.txt")]
        key = (stage, source, panel)
        calls.append(("run", key))
        Path(stdout).write_text("")
        o = plan.get(key, "PASS" if stage != "TD56" else (0.8, 0.5))
        if stage == "TD56":
            if o == "crash":
                Path(stderr).write_text("Error\n"); return 1
            np.savez(Path(mnt) / f"td56_{source}_result.npz", obs=o[0], p95=o[1]); Path(stderr).write_text("")
            Path(stdout).write_text(f"NULL finite 64 p95 {o[1]} PASS {bool(o[0] > o[1] and o[0] > 0)}\n"); return 0
        if o == "RAISE":
            raise RuntimeError("orchestrator died mid-attempt")
        if o == "NOT_ESTIMABLE":
            Path(stderr).write_text("RuntimeError: null vector is not exactly 64 finite values\n"); return 1
        if o == "ARGPARSE":
            Path(stderr).write_text("usage: x\nx: error: unrecognized arguments\n"); return 2
        text = json.dumps({"status": o, "source": source, "panel": panel, "cases": [
            {"split": 0, "half": 0, "observed_median_donor_local_triplet_agreement": 0.6, "null_p95_index60": 0.5,
             "pass": o == "PASS"}]}, indent=2, sort_keys=True) + "\n"
        Path(output).write_text(text); Path(stdout).write_text(text)              # the executors print their payload
        Path(stderr).write_text("")
        return 0 if o == "PASS" else 2
    monkeypatch.setattr(A, "run_executor", run_executor)
    paths = preflight_world(tmp_path, ns, **world)
    args = type("Args", (), dict(namespace=str(ns), archive="a", support_bundle="b", g6_values="v", g6_meta="m",
                                  sample_freeze="f", python="py", implementation_commit="c" * 40,
                                  **{k: str(v) for k, v in paths.items()}))
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        X.run(args)
    (tmp_path / "rec" / "execute.stdout.txt").write_text(printed.getvalue())      # what the launcher keeps outside the namespace
    (tmp_path / "rec" / "RUN_RECORD.txt").write_text("execute_exit=0\nattempt_spent=yes\n")
    return ns, calls


def bundle_of(ns):
    return json.loads((ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").read_text())


def test_marker_precedes_corrected_values_and_every_stage_runs_in_frozen_order(tmp_path, monkeypatch):
    ns, calls = run_stubbed(tmp_path, monkeypatch, {("TD57C", "HVS", 0): "FAIL"})
    first = next(i for i, c in enumerate(calls) if c[0] == "corrected_cache")
    assert [c[:2] for c in calls[:first]] == [("support", False), ("sha", "TD41-TD58 archive"), ("sha", "G6 values"),
                                              ("sha", "G6 metadata"), ("sha", "sample freeze")]
    assert not any(c[-1] for c in calls[:first])                                    # every pre-check ran before the marker
    assert calls[first] == ("corrected_cache", True, "detected_corrected")          # marker existed before values opened
    runs = [c[1] for c in calls if c[0] == "run"]
    assert [r[0] for r in runs] == ["TD56"] * 3 + ["TD57B"] * 6 + ["TD57C"] + ["TD59"] * 6
    bundle = bundle_of(ns)
    assert {k: v["status"] for k, v in bundle["stages"].items()} == {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}
    assert bundle["frozen_interpretation"]["label"] == "CORRECTED_RELATIONAL_PROGRAM_CONSISTENT_WITH_HISTORICAL_SCALE_BRACKET"
    assert bundle["routing_universal_source_input"] == "PASS" and bundle["source_heterogeneity"] == X.SOURCE_HETEROGENEITY
    assert bundle["routing"]["biological_state"] == "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
    assert all(bundle[k] is False for k in G.DOWNSTREAM)
    assert EV.validate_evidence(ns, tmp_path / "rec")["verdict"] == "EVIDENCE_VALID__COMPLETE"


@pytest.mark.parametrize("panel", [0, 1])
def test_td57c_threshold_discordance_routes_exactly_like_a_first_source_failure(tmp_path, monkeypatch, panel):
    ns, _ = run_stubbed(tmp_path / "discordant", monkeypatch, {("TD57C", "NPH52", panel): "FAIL"})  # HVS passes the panel first
    first, _ = run_stubbed(tmp_path / "first", monkeypatch, {("TD57C", "HVS", panel): "FAIL"})
    b, f = bundle_of(ns), bundle_of(first)
    assert b["stages"]["TD57C"]["status"] == f["stages"]["TD57C"]["status"] == "FAIL"
    assert b["routing"]["biological_state"] == f["routing"]["biological_state"] == "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
    assert b["routing_universal_source_input"] == "PASS" and b["source_heterogeneity"] == X.SOURCE_HETEROGENEITY
    assert b["universal_qualification"]["TD57C"]["threshold_discordance"] == [{"panel": panel, "passed": ["HVS"], "failed": ["NPH52"]}]
    q = b["frozen_interpretation"]
    assert q["pattern"] == "A" and q["universality_qualifier"]["label"] == X.UNIVERSALITY_QUALIFIER
    assert q["universality_qualifier"]["pattern_G_assigned"] is False and "universality_qualifier" not in f["frozen_interpretation"]
    assert "SOURCE_DISAGREEMENT" not in json.dumps(b)
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


def test_an_upstream_not_estimable_is_not_strengthened_by_a_later_straddle(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {("TD56", "HVS", None): (float("nan"), 0.5), ("TD59", "NPH52", 0): "FAIL"})
    b = bundle_of(ns)
    assert b["stages"]["TD56"]["status"] == "NOT_ESTIMABLE" and b["universal_qualification"]["TD59"]["threshold_discordance"]
    assert b["routing"]["biological_state"] == "NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS"
    assert b["routing"]["candidate_routes"]["C2_RELATIONAL_SHARED"] == "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


def test_no_source_averaging_rescues_a_failed_universal_qualification(tmp_path, monkeypatch):
    # five of six TD59 source-panels pass; the SEA_AD P1 failure alone still fails the stage
    ns, _ = run_stubbed(tmp_path, monkeypatch, {("TD57C", "HVS", 0): "FAIL", ("TD59", "SEA_AD", 1): "FAIL"})
    b = bundle_of(ns)
    rec = b["universal_qualification"]["TD59"]
    assert sum(o["outcome"] == "PASS" for o in rec["observed"]) == 5 and rec["universal_qualification"].startswith("NOT_ESTABLISHED")
    assert b["stages"]["TD59"]["status"] == "FAIL" and b["routing"]["biological_state"] == "BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED"
    assert b["routing"]["source_averaging_rescue_allowed"] is False and "pooled" not in json.dumps(b).lower()


def test_not_estimable_and_failures_are_preserved_and_stop_only_their_own_stage(tmp_path, monkeypatch):
    ns, calls = run_stubbed(tmp_path, monkeypatch, {("TD56", "NPH52", None): (float("nan"), 0.5), ("TD57B", "HVS", 0): "FAIL",
                                                    ("TD59", "SEA_AD", 0): "NOT_ESTIMABLE"})
    bundle = bundle_of(ns)
    assert {k: v["status"] for k, v in bundle["stages"].items()} == {"TD56": "NOT_ESTIMABLE", "TD57B": "FAIL", "TD57C": "PASS", "TD59": "NOT_ESTIMABLE"}
    td56 = json.loads((ns / "TD56" / "TD56_STAGE_RECEIPT.json").read_text())
    assert [i["source"] for i in td56["invocations"]] == ["HVS", "NPH52"]            # stopped at NPH52
    assert bundle["routing"]["biological_state"].startswith("NOT_ESTIMABLE")       # never a biological PASS
    assert bundle["frozen_interpretation"]["label"] == "NOT_ESTIMABLE__NO_BIOLOGICAL_PASS"
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


@pytest.mark.parametrize("plan", [{("TD56", "HVS", None): "crash"}, {("TD57B", "HVS", 0): "ARGPARSE"}])
def test_an_implementation_failure_is_preserved_and_never_routed(tmp_path, monkeypatch, plan):
    ns, _ = run_stubbed(tmp_path, monkeypatch, plan)
    bundle = bundle_of(ns)
    stage = next(iter(plan))[0]
    assert bundle["stages"][stage]["status"] == "IMPLEMENTATION_FAILURE"
    assert bundle["stages"][stage]["historical_comparison"] == "NOT_COMPARABLE__IMPLEMENTATION_FAILURE"
    assert bundle["routing"] == X.NOT_PROJECTED and bundle["routing_universal_source_input"] is None
    assert not (ns / X.ROUTING_INPUT).exists()
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


def test_ratification_is_parsed_not_scraped(tmp_path, monkeypatch):
    # review finding 3: a compact ratification JSON still yields the ratified field, before the marker
    _, calls = run_stubbed(tmp_path, monkeypatch, {}, compact=True)
    assert ("corrected_cache", True, "detected_corrected") in calls


@pytest.mark.parametrize("kw,match", [
    ({"terminal": "QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN"}, "ratified QUALIFY PASS"),
    ({"with_acceptance": False}, "launch-audit acceptance"),
    ({"detected": "detected_historical"}, "detected field differs"),
    ({"support_ok": False}, "support bundle"),
])
def test_the_orchestrator_cannot_be_run_around_its_gates_and_spends_nothing(tmp_path, monkeypatch, kw, match):
    # review findings 3 and 7: every pre-marker refusal leaves no namespace and no ledger
    with pytest.raises((G.GateError, A.AdapterError), match=match):
        run_stubbed(tmp_path, monkeypatch, {}, **kw)
    assert not (tmp_path / "ns").exists() and not G.ledger_path(tmp_path / "ns").exists()


def test_second_attempt_is_refused_even_after_the_namespace_is_removed(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    with pytest.raises(G.GateError, match="already exists"):
        run_stubbed(tmp_path, monkeypatch, {})
    os.chmod(ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json", 0o666)
    shutil.rmtree(ns)
    with pytest.raises(G.GateError, match="already exists"):
        run_stubbed(tmp_path, monkeypatch, {})
    assert not ns.exists()


def test_an_attempt_that_dies_midway_is_preserved_as_incomplete(tmp_path, monkeypatch):
    with pytest.raises(RuntimeError, match="died mid-attempt"):
        run_stubbed(tmp_path, monkeypatch, {("TD57B", "HVS", 0): "RAISE"})
    v = EV.validate_evidence(tmp_path / "ns")
    assert v["verdict"] == "EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED", v["problems"]
    assert v["incomplete"] == ["TD57B", "TD57C", "TD59", "bundle"] and v["stage_status"]["TD56"] == "PASS"


def test_preflight_revalidates_the_authority_bytes(tmp_path, monkeypatch):
    # re-review finding 7: made-up authority SHAs in the launcher's check record are refused before the marker
    with pytest.raises(G.GateError, match="not the audited SHA"):
        run_stubbed(tmp_path, monkeypatch, {}, forge_check=True)
    assert not (tmp_path / "ns").exists() and not G.ledger_path(tmp_path / "ns").exists()


def test_input_bytes_are_hashed_before_the_marker(tmp_path, monkeypatch):
    # re-review defect E: archive, G6 values/metadata and sample freeze are checked before anything is spent
    _, calls = run_stubbed(tmp_path, monkeypatch, {})
    hashed = [c for c in calls if c[0] == "sha"]
    assert [c[1] for c in hashed] == ["TD41-TD58 archive", "G6 values", "G6 metadata", "sample freeze"]
    assert not any(c[2] for c in hashed)
    with pytest.raises(A.AdapterError, match="G6 values"):
        run_stubbed(tmp_path / "second", monkeypatch, {}, bad_input="G6 values")
    assert not (tmp_path / "second" / "ns").exists() and not G.ledger_path(tmp_path / "second" / "ns").exists()


def test_a_spent_ledger_without_a_marker_is_reported_as_spent(tmp_path):
    # re-review defect C
    ns = tmp_path / "ns"
    G.ledger_path(ns).write_text("{}")
    v = EV.validate_evidence(ns)
    assert v["verdict"] == "EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED" and v["incomplete"] == ["start_marker"]
    ns.mkdir()
    (ns / "x.json").write_text("{}")
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_INVALID"


def test_a_completed_result_cannot_be_passed_off_as_a_crash_against_the_launch_record(tmp_path, monkeypatch):
    # re-review defect D: alone, a removed final receipt looks like a crash; the launch record shows exit 0
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    for p in (ns / "TD59" / "TD59_STAGE_RECEIPT.json", ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json", ns / X.ROUTING_INPUT):
        p.unlink()
    alone = EV.validate_evidence(ns)
    assert alone["verdict"] == "EVIDENCE_VALID__INCOMPLETE_ATTEMPT_PRESERVED" and alone["in_progress_stage"]["stage"] == "TD59"
    v = EV.validate_evidence(ns, tmp_path / "rec")
    assert v["verdict"] == "EVIDENCE_INVALID" and any("exited 0" in p for p in v["problems"])


def test_the_printed_stage_summary_is_checked_against_the_bundle(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    assert EV.validate_evidence(ns, tmp_path / "rec")["verdict"] == "EVIDENCE_VALID__COMPLETE"
    (tmp_path / "rec" / "execute.stdout.txt").write_text('{"TD56": {}}\n')
    v = EV.validate_evidence(ns, tmp_path / "rec")
    assert v["verdict"] == "EVIDENCE_INVALID" and any("printed at run time" in p for p in v["problems"])


def test_frozen_interpretation_patterns():
    st = lambda a, b, c, d: {"TD56": a, "TD57B": b, "TD57C": c, "TD59": d}  # noqa: E731
    assert X.frozen_interpretation(st("FAIL", "PASS", "FAIL", "PASS"), {})["pattern"] == "D"
    c = X.frozen_interpretation(st("PASS", "FAIL", "FAIL", "PASS"), {})
    assert c["pattern"] == "C" and c["pattern_F_requires_auditor_judgment"] is True    # any corrected TD59 PASS
    assert X.frozen_interpretation(st("PASS", "PASS", "PASS", "PASS"), {})["pattern"] == "E"
    b = X.frozen_interpretation(st("PASS", "PASS", "FAIL", "FAIL"), {})
    assert b["pattern"] == "B" and b["pattern_F_requires_auditor_judgment"] is False
    assert X.frozen_interpretation(st("PASS", "PASS", "NOT_ESTIMABLE", "PASS"), {})["pattern"] == "H"
    disc = {"TD57C": X.source_record(_stage([_p(0, "HVS", "PASS"), _p(0, "NPH52", "FAIL")]), ORDERS["TD57C"])}
    g = X.frozen_interpretation(st("PASS", "PASS", "FAIL", "PASS"), disc)
    assert g["pattern"] == "A" and g["universality_qualifier"]["stages"] == ["TD57C"]
    assert g["universality_qualifier"]["pattern_G_assigned"] is False and "G" not in X.PATTERNS
    assert X.frozen_interpretation(st("IMPLEMENTATION_FAILURE", "PASS", "FAIL", "PASS"), {})["pattern"] is None


def _writable(p: Path) -> Path:
    os.chmod(p, 0o666)
    return p


@pytest.mark.parametrize("attack", ["output", "status", "routing", "flag", "order", "relabel", "drop_inputs", "drop_routing",
                                    "universal", "heterogeneity", "qualification", "ledger", "truncate", "stderr", "printed",
                                    "cases", "td56_flag",
                                    "stray_stage", "stray_root", "executor_copy", "later_stage_dir"])
def test_evidence_tampering_is_detected(tmp_path, monkeypatch, attack):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    st = ns / "TD57B" / "TD57B_STAGE_RECEIPT.json"
    rec = json.loads(st.read_text())
    bpath = ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json"
    if attack == "output":
        (ns / rec["invocations"][0]["output"]).write_text('{"status": "FAIL"}')
    elif attack == "status":
        rec["status"] = "FAIL"; st.write_text(json.dumps(rec))
    elif attack == "routing":
        ri = ns / X.ROUTING_INPUT
        r = json.loads(ri.read_text()); r["td57b"] = "IMPLEMENTATION_FAILURE"; ri.write_text(json.dumps(r))
    elif attack == "flag":
        r = json.loads(bpath.read_text()); r["training_authorized"] = True; bpath.write_text(json.dumps(r))
    elif attack == "order":
        rec["invocations"] = list(reversed(rec["invocations"])); st.write_text(json.dumps(rec))
    elif attack == "relabel":
        # review finding 2: one invocation with exit 2 and a FAIL result, labelled PASS, with the input record and
        # the routing input removed
        inv = rec["invocations"][0]
        out = ns / inv["output"]
        out.write_text(json.dumps({**json.loads(out.read_text()), "status": "FAIL"}))
        inv.update(exit_code=2, output_sha256=sha(out))
        rec.update(invocations=[inv], invocations_run=1)
        st.write_text(json.dumps(rec))
        (ns / "ADAPTER_INPUT_SHA256.json").unlink()
        (ns / X.ROUTING_INPUT).unlink()
    elif attack == "drop_inputs":
        (ns / "ADAPTER_INPUT_SHA256.json").unlink()
    elif attack == "drop_routing":
        (ns / X.ROUTING_INPUT).unlink()
    elif attack == "universal":
        r = json.loads(bpath.read_text()); r["routing_universal_source_input"] = "FAIL"; bpath.write_text(json.dumps(r))
    elif attack == "heterogeneity":
        r = json.loads(bpath.read_text()); r["source_heterogeneity"] = "ESTABLISHED"; bpath.write_text(json.dumps(r))
    elif attack == "qualification":
        r = json.loads(bpath.read_text())
        r["universal_qualification"]["TD57B"]["universal_qualification"] = "NOT_ESTIMABLE"
        r["universal_qualification"]["TD57C"]["unobserved"] = [{"panel": 1, "source": "SEA_AD", "evidence": "UNOBSERVED"}]
        bpath.write_text(json.dumps(r))
    elif attack == "ledger":
        _writable(G.ledger_path(ns)).unlink()
    elif attack == "truncate":
        rec["invocations"] = rec["invocations"][:-1]; rec["invocations_run"] = 5; st.write_text(json.dumps(rec))
    elif attack == "stderr":
        (ns / rec["invocations"][0]["stderr"]).write_text("edited\n")
    elif attack in ("printed", "cases"):
        # re-review finding 2: SHAs kept consistent, so only the cross-checks can catch it
        inv = rec["invocations"][0]
        out, so = ns / inv["output"], ns / inv["stdout"]
        r = json.loads(out.read_text())
        if attack == "printed":
            so.write_text("something else\n")
        else:
            r["cases"][0]["pass"] = False
            text = json.dumps(r, indent=2, sort_keys=True) + "\n"
            out.write_text(text); so.write_text(text)
        inv.update(output_sha256=sha(out), stdout_sha256=sha(so))
        st.write_text(json.dumps(rec))
    elif attack == "td56_flag":
        t56 = ns / "TD56" / "TD56_STAGE_RECEIPT.json"
        r56 = json.loads(t56.read_text())
        so = ns / r56["invocations"][0]["stdout"]
        so.write_text("NULL finite 64 PASS False\n")
        r56["invocations"][0]["stdout_sha256"] = sha(so)
        t56.write_text(json.dumps(r56))
    elif attack == "stray_stage":
        (ns / "TD57B" / "extra.json").write_text("{}")
    elif attack == "stray_root":
        (ns / "extra.json").write_text("{}")
    elif attack == "executor_copy":
        next((ns / "executors").iterdir()).write_bytes(b"#altered\n")
    elif attack == "later_stage_dir":
        (ns / "TD57C" / "TD57C_STAGE_RECEIPT.json").unlink()
    v = EV.validate_evidence(ns)
    assert v["verdict"] == "EVIDENCE_INVALID", attack
    if attack == "relabel":
        text = "\n".join(v["problems"])
        for frag in ("without the adapter input record", "is not reproduced from its exit code", "PASS with 1 of 6",
                     "routing input missing"):
            assert frag in text, frag


def test_evidence_binds_the_launch_record(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    assert EV.validate_evidence(ns, tmp_path / "rec")["verdict"] == "EVIDENCE_VALID__COMPLETE"
    au = tmp_path / "rec" / "AUTHORITY_CHECK.json"
    r = json.loads(au.read_text()); r["authority_sha256"]["acceptance"] = "5" * 64; au.write_text(json.dumps(r))
    v = EV.validate_evidence(ns, tmp_path / "rec")
    assert v["verdict"] == "EVIDENCE_INVALID" and any("authority check" in p for p in v["problems"])


def test_no_marker_means_no_evidence(tmp_path):
    (tmp_path / "ns").mkdir()
    assert EV.validate_evidence(tmp_path / "ns")["verdict"] == "NO_ATTEMPT__NO_START_MARKER"


# ------------------------------------------------------------------------------------------------- launcher text
def _code_lines() -> list[str]:
    return [ln for ln in LAUNCHER.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def test_launcher_is_valid_bash():
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    subprocess.run([str(git_bash) if git_bash.is_file() else "bash", "-n", str(LAUNCHER)], check=True)


def test_launcher_invokes_only_the_replay_package_and_never_g6_or_g7():
    text = "\n".join(_code_lines())
    assert "materialize_td_relational_corrected_sampleA" not in text and "audit_td_relational_g7_s174_overlap" not in text
    called = set(re.findall(r"wpy (td_corrected_replay_[a-z_0-9]+\.py)", text))
    assert called == {"td_corrected_replay_gate_v1.py", "td_corrected_replay_execute_v1.py", "td_corrected_replay_evidence_v1.py"}
    assert "MSYS_NO_PATHCONV=1" in text


def test_launcher_orders_pure_checks_qualify_and_marker_correctly():
    lines = _code_lines()
    def first(pattern):
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))
    mk = first(r'mkdir -p "\$RUNROOT/authority"')
    for pat in (r'rev-parse HEAD\)" = "\$AUTH_COMMIT"', r'status --porcelain --ignored\)" \] \|\| fail', r'blob_sha "\$AUTH_COMMIT" "\$OP_REL"',
                r'blob_sha "\$ACC_COMMIT" "\$ACC_REL"', r'replay namespace already exists', r'WSL replay environment is not the pinned one',
                r'attempt ledger exists', r'an earlier EXECUTE_ONCE spent the attempt'):
        assert first(pat) < mk, pat
    execute = first(r"wpy td_corrected_replay_execute_v1\.py")
    assert first(r"wpy td_corrected_replay_gate_v1\.py qualify") < first(r"wpy td_corrected_replay_gate_v1\.py authority") < execute
    assert first(r'if \[ "\$MODE" = "QUALIFY" \]; then') < execute
    assert first(r'EXECUTE_ONCE requires a ratified QUALIFY PASS') < execute


def test_launcher_records_whether_the_attempt_was_spent_and_passes_the_authority_bytes():
    # re-review defect A: only a run that created the ledger blocks later launches
    text = "\n".join(_code_lines())
    assert "grep -q '^attempt_spent=yes'" in text and "launch_EXECUTE_ONCE_*/record/RUN_RECORD.txt; do" in text
    after = text[text.index("XRC=$?"):]
    assert "attempt_spent=yes" in after and "attempt_spent=no" in after
    assert after.index("attempt_spent=yes") < after.index("wpy td_corrected_replay_evidence_v1.py")
    execute = text[text.index("wpy td_corrected_replay_execute_v1.py"):text.index("XRC=$?")]
    for flag in ("--owner", "--runtime", "--operational", "--acceptance", "--equivalence-receipt", "--ratification", "--authority-check"):
        assert flag in execute, flag


def test_launcher_passes_parsed_decisions_and_binds_the_launch_record():
    text = "\n".join(_code_lines())
    assert "detected_field" not in text and "--detected-field" not in text          # review finding 3: no sed scraping
    execute = text[text.index("wpy td_corrected_replay_execute_v1.py"):]
    assert "--ratification" in execute and "--authority-check" in execute
    assert re.search(r'evidence_v1\.py .*\n?.*--launch-record "\$WREC"', text)
    assert re.search(r'gate_v1\.py qualify[\s\S]*--support-bundle', text) and re.search(r'gate_v1\.py authority[\s\S]*--equivalence-receipt', text)
    assert "208684bcca51680a107433cc22764cc2227a847da37a023d632ec1469bd04298" in text   # diagnostic result pinned


# --------------------------------------------------------------------------------------------- adapter mechanics
def _bundle(tmp_path, members):
    p = tmp_path / "bundle.zip"
    with zipfile.ZipFile(p, "w") as z:
        for name, data in members:
            z.writestr(name, data)
    return p


def test_support_bundle_is_checked_by_bundle_and_member_sha(tmp_path, monkeypatch):
    good = _bundle(tmp_path, [(A.SUPPORT_MEMBER, b"support")])
    monkeypatch.setattr(A, "SUPPORT_SHA", hashlib.sha256(b"support").hexdigest())
    with pytest.raises(A.AdapterError, match="support bundle SHA mismatch"):
        A.check_support_bundle(good)
    monkeypatch.setattr(A, "SUPPORT_BUNDLE_SHA", sha(good))
    assert A.check_support_bundle(good)["support_member_sha256"] == A.SUPPORT_SHA
    monkeypatch.setattr(A, "SUPPORT_SHA", "0" * 64)
    with pytest.raises(A.AdapterError, match="support member SHA mismatch"):
        A.check_support_bundle(good)


def test_support_bundle_constant_is_the_custody_value():
    assert A.SUPPORT_BUNDLE_SHA == "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
def test_write_inputs_places_rows_at_global_row_and_keeps_historical_order(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "N_GLOBAL", 10)
    monkeypatch.setattr(A, "N_ADDR", 5)
    meta = {"global_row": np.asarray([7, 2, 5]), "source": np.asarray(["HVS", "NPH52", "SEA_AD"]),
            "donor": np.asarray(["a", "b", "c"]), "operator": np.asarray([1, 2, 3]),
            "source_library": np.asarray([10, 20, 30]), "detected": np.asarray([1, 2, 3])}
    cache = {"indptr": np.asarray([0, 1, 3, 4]), "indices": np.asarray([4, 0, 2, 1], dtype=np.int32),
             "data": np.asarray([1.5, 2.5, 3.5, 4.5]), "meta": meta}
    monkeypatch.setattr(A, "historical_td50", lambda archive, s: {"global_row": meta["global_row"][meta["source"] == s]})
    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as z:
        z.writestr(A.SUPPORT_MEMBER, b"support")
    monkeypatch.setattr(A, "SUPPORT_SHA", hashlib.sha256(b"support").hexdigest())
    monkeypatch.setattr(A, "SUPPORT_BUNDLE_SHA", sha(bundle))
    shas = A.write_inputs(cache, Path("a"), bundle, tmp_path / "mnt")
    arr = tmp_path / "mnt" / "td_matrix_npz" / "arrays"
    indptr = np.load(arr / "indptr.npy")
    assert indptr.dtype == np.int32 and indptr[-1] == 4 and np.diff(indptr).tolist() == [0, 0, 2, 0, 0, 1, 0, 1, 0, 0]
    assert np.load(arr / "data.npy")[indptr[7]] == 1.5 and np.load(arr / "data.npy").dtype == np.float64
    t = np.load(tmp_path / "mnt" / "td50_NPH52.npz", allow_pickle=True)
    assert t["global_row"].tolist() == [2] and t["donor"].dtype == object
    assert shas["td50_NPH52.npz"] == sha(tmp_path / "mnt" / "td50_NPH52.npz")
    with pytest.raises(A.AdapterError, match="fresh"):
        A.write_inputs(cache, Path("a"), bundle, tmp_path / "mnt")


def test_bootstrap_refuses_altered_bytes_and_paths_outside_mnt_data(tmp_path):
    exe = tmp_path / "exe.py"
    exe.write_text("import numpy as np\nnp.load('/etc/passwd')\n")
    common = [sys.executable, str(A.BOOTSTRAP), "--kind", "td56", "--executor", str(exe), "--mnt", str(tmp_path), "--input-sha-json", "{}"]
    r = subprocess.run(common + ["--executor-sha256", "0" * 64], capture_output=True, text=True)
    assert r.returncode != 0 and "executor bytes" in (r.stdout + r.stderr)
    r = subprocess.run(common + ["--executor-sha256", sha(exe)], capture_output=True, text=True)
    assert r.returncode != 0 and "outside /mnt/data" in (r.stdout + r.stderr)


def test_bootstrap_redirects_only_the_input_constants(tmp_path):
    exe = tmp_path / "mod.py"
    exe.write_text(
        "import json, sys\nfrom pathlib import Path\nARRAY_ROOT = Path('/mnt/data/td_matrix_npz/arrays')\nSUPPORT_PATH = Path('/mnt/data/s.npz')\n"
        "META_PATHS = {'HVS': Path('/mnt/data/td50_HVS.npz')}\nARRAY_SHA256 = {'data.npy': 'h'}\nMETA_SHA256 = {'HVS': 'h'}\nSUPPORT_SHA256 = 'h'\n"
        "def main():\n    out = Path(sys.argv[sys.argv.index('--output') + 1])\n"
        "    out.write_text(json.dumps({'a': str(ARRAY_ROOT), 'm': ARRAY_SHA256['data.npy'], 's': SUPPORT_SHA256, 'meta': META_SHA256['HVS']}))\n    return 2\n")
    shas = {"support_rel": "sup.npz", "sup.npz": "S", "td_matrix_npz/arrays/data.npy": "D", "td50_HVS.npz": "M"}
    out = tmp_path / "o.json"
    r = subprocess.run([sys.executable, str(A.BOOTSTRAP), "--kind", "module", "--executor", str(exe), "--executor-sha256", sha(exe),
                        "--mnt", str(tmp_path / "mnt"), "--input-sha-json", json.dumps(shas), "--", "--source", "HVS",
                        "--panel", "0", "--output", str(out)], capture_output=True, text=True)
    assert r.returncode == 2, r.stderr
    got = json.loads(out.read_text())
    assert (got["m"], got["s"], got["meta"]) == ("D", "S", "M") and got["a"].replace("\\", "/").endswith("mnt/td_matrix_npz/arrays")


# ------------------------------------------------------------------------------------ historical-fixture equivalence
def _equivalence(tmp_path, contract, **override):
    env = {k: contract["execution_environment"][k] for k in ("python", "numpy", "scipy", "pandas")}
    rec = {"schema": "JEPA_TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1", "implementation_commit_sha": "c" * 40,
           "cases": [{"case": c, "equal": True, "exit_code": 2 if c == "TD57C_HVS_P0" else 0} for c in sorted(G.EQUIVALENCE_CASES)],
           "n_cases": 16, "all_equal": True, "td57c_historical_fail_reproduced": True, "corrected_values_read": False,
           "code_sha256": {"adapter": sha(A.__file__), "bootstrap": sha(A.BOOTSTRAP)}, "environment": {"platform": "Linux", **env}}
    rec.update(override)
    return wjson(tmp_path / "equiv.json", rec)


def test_equivalence_receipt_is_required_exactly(contract, tmp_path):
    assert G.validate_equivalence(contract, _equivalence(tmp_path, contract), implementation_commit="c" * 40)["cases_equal"] == 16
    bad_cases = [{"case": c, "equal": c != "TD57B_SEA_AD_P1"} for c in sorted(G.EQUIVALENCE_CASES)]
    for override, match in (({"implementation_commit_sha": "e" * 40}, "implementation commit"),
                            ({"cases": bad_cases, "all_equal": False}, "did not reproduce"),
                            ({"n_cases": 15}, "16 historical cases"),
                            ({"td57c_historical_fail_reproduced": False}, "TD57C historical failure"),
                            ({"code_sha256": {"adapter": "0" * 64, "bootstrap": sha(A.BOOTSTRAP)}}, "adapter/bootstrap bytes"),
                            ({"environment": {"platform": "Windows", "python": "3.13.5", "numpy": "2.3.5", "scipy": "1.17.0", "pandas": "2.2.3"}}, "pinned replay environment"),
                            ({"corrected_values_read": True}, "corrected values")):
        with pytest.raises(G.GateError, match=match):
            G.validate_equivalence(contract, _equivalence(tmp_path, contract, **override), implementation_commit="c" * 40)


def test_contract_binds_the_environment_lock_and_equivalence(contract):
    lock = contract["execution_environment"]["lock"]
    assert sha(ROOT / lock["path"]) == lock["sha256"]
    assert contract["historical_fixture_equivalence"]["required_cases"] == 16


def test_every_package_file_is_lf_only_so_code_identity_is_platform_stable():
    for rel in G.CODE_FILES + ("scripts/v5/td_corrected_replay_equivalence_v1.py", "tests/v5/test_td_corrected_replay_turnkey_v1.py"):
        assert b"\r" not in (ROOT / rel).read_bytes(), rel
