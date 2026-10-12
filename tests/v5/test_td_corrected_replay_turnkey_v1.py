"""Corrected TD replay turnkey package: contract, predecessors, outcome-blind QUALIFY, replay-only authority,
one-shot marker, orchestrator (stubbed executors), evidence validator, launcher text and adapter mechanics.

Synthetic fixtures only. No corrected value is opened and no replay kernel runs. Tests that need the local TD41-TD58
archive are skipped when it is absent; the real-file QUALIFY covers them.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import re
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
def authority_world(tmp_path, contract):
    code = {"implementation_commit_sha": "c" * 40, "code_sha256": "d" * 64}
    base = {"scope": "CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY", "contract_sha256": sha(CONTRACT),
            "implementation_commit_sha": code["implementation_commit_sha"], **{k: False for k in G.DOWNSTREAM}}
    owner = wjson(tmp_path / "owner.json", {"schema": G.AUTH_SCHEMAS["owner"], **base})
    runtime = wjson(tmp_path / "runtime.json", {"schema": G.AUTH_SCHEMAS["runtime"], **base, "owner_decision_sha256": sha(owner),
                                                 "code_sha256": code["code_sha256"]})
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
                                code=code)


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
    with pytest.raises(G.GateError, match="already exists"):
        G.begin_attempt(tmp_path / "ns", {})


# ------------------------------------------------------------------------------------------- orchestrator (stubbed)
def test_outcome_classes_follow_the_frozen_mapping(tmp_path, contract):
    def td56(obs, p95):
        p = tmp_path / f"r{obs}_{p95}.npz"
        np.savez(p, obs=obs, p95=p95)
        return X.classify_td56(p)
    assert (td56(0.8, 0.5), td56(0.4, 0.5), td56(float("nan"), 0.5), td56(0.8, float("nan"))) == ("PASS", "FAIL", "NOT_ESTIMABLE", "NOT_ESTIMABLE")
    assert X.classify_td56(tmp_path / "absent.npz") == "IMPLEMENTATION_FAILURE"
    pats = contract["invocation_outcome_mapping"]["support_patterns"]
    err = tmp_path / "e.txt"
    err.write_text("Traceback\nRuntimeError: observed split 0 half 1 has <4 measurable donors\n")
    assert X.classify_module(1, err, pats) == "NOT_ESTIMABLE"
    err.write_text("RuntimeError: array SHA mismatch data.npy\n")
    assert X.classify_module(1, err, pats) == "IMPLEMENTATION_FAILURE"
    assert (X.classify_module(0, err, pats), X.classify_module(2, err, pats)) == ("PASS", "FAIL")


def _stage(invs, per_source):
    return {"status": X.stage_status([i["outcome"] for i in invs]), "invocations": invs, "invocations_per_source": per_source}


def test_universal_source_rule():
    p = lambda s, o: {"source": s, "outcome": o}  # noqa: E731
    agree = {"TD56": _stage([p("HVS", "PASS"), p("NPH52", "PASS"), p("SEA_AD", "PASS")], 1)}
    assert X.universal_source(agree) == "PASS"
    disagree = {"TD56": _stage([p("HVS", "PASS"), p("NPH52", "PASS"), p("SEA_AD", "FAIL")], 1)}
    assert X.universal_source(disagree) == "FAIL"
    first_fail = {"TD57C": _stage([p("HVS", "FAIL")], 2)}
    assert X.universal_source(first_fail) == "PASS"
    ne = {"TD59": _stage([p("HVS", "NOT_ESTIMABLE")], 2)}
    assert X.universal_source(ne) == "NOT_ESTIMABLE"


def run_stubbed(tmp_path, monkeypatch, plan: dict, *, ratified=True):
    """plan: (stage, source, panel) -> outcome; TD56 entries as (obs, p95) or 'crash'."""
    calls = []
    ns = tmp_path / "ns"
    monkeypatch.setattr(A, "corrected_cache", lambda *a, **k: (calls.append(("corrected_cache", (ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json").exists())), {"meta": {}})[1])
    def write_inputs(cache, archive, bundle, mnt):
        mnt.mkdir(parents=True)
        (mnt / "x.bin").write_bytes(b"x")
        return {"x.bin": sha(mnt / "x.bin")}
    monkeypatch.setattr(A, "write_inputs", write_inputs)
    monkeypatch.setattr(A, "archive_member", lambda archive, name, sha_=None: b"#exec\n")
    def run_executor(*, kind, executor, executor_sha, mnt, input_sha, python, source=None, panel=None, output=None, stdout, stderr, timeout=None):
        stage = "TD56" if kind == "td56" else Path(output).name.split("_")[0]
        key = (stage, source if stage != "TD56" else Path(stdout).name[len("TD56_"):-len(".stdout.txt")], panel)
        calls.append(("run", key))
        Path(stdout).write_text("")
        o = plan.get(key, "PASS" if stage != "TD56" else (0.8, 0.5))
        if stage == "TD56":
            if o == "crash":
                Path(stderr).write_text("Error\n"); return 1
            np.savez(Path(mnt) / f"td56_{key[1]}_result.npz", obs=o[0], p95=o[1]); Path(stderr).write_text(""); return 0
        Path(output).write_text(json.dumps({"status": o, "cases": [{"split": 0, "half": 0, "observed_median_donor_local_triplet_agreement": 0.6,
                                                                     "null_p95_index60": 0.5}]}))
        if o == "NOT_ESTIMABLE":
            Path(stderr).write_text("RuntimeError: null vector is not exactly 64 finite values\n"); return 1
        Path(stderr).write_text("")
        return 0 if o == "PASS" else 2
    monkeypatch.setattr(A, "run_executor", run_executor)
    qr = wjson(tmp_path / "q.json", {"q": 1})
    args = type("Args", (), dict(namespace=str(ns), archive="a", support_bundle="b", g6_values="v", g6_meta="m",
                                  sample_freeze="f", python="py", implementation_commit="c" * 40, qualify_receipt=str(qr),
                                  authority_sha_json='{"owner": "o"}', detected_field="detected_corrected", ratified=ratified))
    X.run(args)
    return ns, calls


def test_marker_precedes_corrected_values_and_every_stage_runs_in_frozen_order(tmp_path, monkeypatch):
    ns, calls = run_stubbed(tmp_path, monkeypatch, {("TD57C", "HVS", 0): "FAIL"})
    assert calls[0] == ("corrected_cache", True)                     # marker existed before values were opened
    runs = [c[1] for c in calls if c[0] == "run"]
    assert [r[0] for r in runs] == ["TD56"] * 3 + ["TD57B"] * 6 + ["TD57C"] + ["TD59"] * 6
    bundle = json.loads((ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").read_text())
    assert {k: v["status"] for k, v in bundle["stages"].items()} == {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}
    assert bundle["frozen_interpretation"]["label"] == "CORRECTED_RELATIONAL_PROGRAM_CONSISTENT_WITH_HISTORICAL_SCALE_BRACKET"
    assert bundle["routing"]["biological_state"] == "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
    assert all(bundle[k] is False for k in G.DOWNSTREAM)
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


def test_not_estimable_and_failures_are_preserved_and_stop_only_their_own_stage(tmp_path, monkeypatch):
    ns, calls = run_stubbed(tmp_path, monkeypatch, {("TD56", "NPH52", None): (float("nan"), 0.5), ("TD57B", "HVS", 0): "FAIL",
                                                    ("TD59", "SEA_AD", 0): "NOT_ESTIMABLE"})
    bundle = json.loads((ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").read_text())
    assert {k: v["status"] for k, v in bundle["stages"].items()} == {"TD56": "NOT_ESTIMABLE", "TD57B": "FAIL", "TD57C": "PASS", "TD59": "NOT_ESTIMABLE"}
    td56 = json.loads((ns / "TD56" / "TD56_STAGE_RECEIPT.json").read_text())
    assert [i["source"] for i in td56["invocations"]] == ["HVS", "NPH52"]            # stopped at NPH52
    assert bundle["routing"]["biological_state"].startswith("NOT_ESTIMABLE")       # never a biological PASS
    assert bundle["frozen_interpretation"]["label"] == "NOT_ESTIMABLE__NO_BIOLOGICAL_PASS"
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_VALID__COMPLETE"


def test_an_implementation_failure_is_preserved_and_never_routed(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {("TD56", "HVS", None): "crash"})
    bundle = json.loads((ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").read_text())
    assert bundle["stages"]["TD56"]["status"] == "IMPLEMENTATION_FAILURE"
    assert bundle["routing"] == "NOT_PROJECTED__IMPLEMENTATION_FAILURE_OR_UNRATIFIED_RULE"
    assert not (ns / "CORRECTED_REPLAY_ROUTING_INPUT_V2.json").exists()


def test_unratified_rules_are_never_projected(tmp_path, monkeypatch):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {}, ratified=False)
    assert json.loads((ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json").read_text())["routing"].startswith("NOT_PROJECTED")


def test_second_attempt_is_refused(tmp_path, monkeypatch):
    run_stubbed(tmp_path, monkeypatch, {})
    with pytest.raises(G.GateError, match="already exists"):
        run_stubbed(tmp_path, monkeypatch, {})


def test_frozen_interpretation_patterns():
    st = lambda a, b, c, d: {"TD56": a, "TD57B": b, "TD57C": c, "TD59": d}  # noqa: E731
    assert X.frozen_interpretation(st("FAIL", "PASS", "FAIL", "PASS"), "PASS")["pattern"] == "D"
    assert X.frozen_interpretation(st("PASS", "FAIL", "FAIL", "PASS"), "PASS")["pattern"] == "C"
    assert X.frozen_interpretation(st("PASS", "PASS", "PASS", "PASS"), "PASS")["pattern"] == "E"
    assert X.frozen_interpretation(st("PASS", "PASS", "FAIL", "FAIL"), "PASS")["pattern"] == "B"
    assert X.frozen_interpretation(st("PASS", "PASS", "NOT_ESTIMABLE", "PASS"), "PASS")["pattern"] == "H"
    g = X.frozen_interpretation(st("PASS", "PASS", "FAIL", "PASS"), "FAIL")
    assert g["pattern"] == "A" and g["source_qualifier"]["label"] == "NO_UNIVERSAL_SOURCE_REPLICATION"
    assert X.frozen_interpretation(st("IMPLEMENTATION_FAILURE", "PASS", "FAIL", "PASS"), None)["pattern"] is None


@pytest.mark.parametrize("attack", ["output", "status", "routing", "flag", "order"])
def test_evidence_tampering_is_detected(tmp_path, monkeypatch, attack):
    ns, _ = run_stubbed(tmp_path, monkeypatch, {})
    st = ns / "TD57B" / "TD57B_STAGE_RECEIPT.json"
    rec = json.loads(st.read_text())
    if attack == "output":
        (ns / rec["invocations"][0]["output"]).write_text('{"status": "FAIL"}')
    elif attack == "status":
        rec["status"] = "FAIL"; st.write_text(json.dumps(rec))
    elif attack == "routing":
        ri = ns / "CORRECTED_REPLAY_ROUTING_INPUT_V2.json"
        r = json.loads(ri.read_text()); r["td57b"] = "IMPLEMENTATION_FAILURE"; ri.write_text(json.dumps(r))
    elif attack == "flag":
        b = ns / "TD_CORRECTED_REPLAY_RECEIPT_V1.json"
        r = json.loads(b.read_text()); r["training_authorized"] = True; b.write_text(json.dumps(r))
    elif attack == "order":
        rec["invocations"] = list(reversed(rec["invocations"])); st.write_text(json.dumps(rec))
    assert EV.validate_evidence(ns)["verdict"] == "EVIDENCE_INVALID"


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
                r'blob_sha "\$ACC_COMMIT" "\$ACC_REL"', r'replay namespace already exists', r'WSL replay environment is not the pinned one'):
        assert first(pat) < mk, pat
    execute = first(r"wpy td_corrected_replay_execute_v1\.py")
    assert first(r"wpy td_corrected_replay_gate_v1\.py qualify") < first(r"wpy td_corrected_replay_gate_v1\.py authority") < execute
    assert first(r'if \[ "\$MODE" = "QUALIFY" \]; then') < execute
    assert first(r'EXECUTE_ONCE requires a ratified QUALIFY PASS') < execute


# --------------------------------------------------------------------------------------------- adapter mechanics
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
