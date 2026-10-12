#!/usr/bin/env python3
"""Corrected TD replay gate: contract validation, predecessor authentication, outcome-blind QUALIFY, replay-only
authority, and the one-shot start marker. THIS FILE NEVER OPENS CORRECTED VALUES AND NEVER RUNS A REPLAY KERNEL.

  contract     validate the frozen contract against the bytes it binds
  qualify      authenticate the predecessors (G6 accepted; G7 NOT_ESTIMABLE, never PASS; the disjointness
               diagnostic as the only reason the old prerequisite is bypassed). Then, outcome-blind: resolve exactly
               one frozen executor per stage/source, run the cheap structural estimability checks on metadata, check
               owner ratification of the open decisions, and check the replay namespace is fresh. Writes only the
               QUALIFY receipt (under --record).
  authority    validate fresh replay-only owner/runtime/operational authority and, for EXECUTE, the committed
               external launch-audit acceptance.
`preflight_execute()` repeats the pure EXECUTE checks inside the orchestrator. `begin_attempt()` is the only function
that creates the attempt ledger and the start marker. Both use exclusive create; it must be called only after every
check has passed and before any protected (outcome-bearing) operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_corrected_replay_adapter_v1 as A  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REL = "target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json"
G7_TERMINAL = "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
DIAGNOSTIC_CLASS = "GENUINELY_DISJOINT_NATURAL_CELL_SETS"
G6_ACCEPT_DISPOSITION = "ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY"
DOWNSTREAM = ("g6_execution_authorized", "g7_execution_authorized", "target_selection_authorized", "td60_authorized",
              "stage4_authorized", "training_authorized")
STRUCTURAL_FLOORS = {"min_cells_per_stratum": 4, "td56_min_donors": 8, "td57b_min_donors_per_half": 4,
                     "td57c_td59_min_structural_donors": 8}
AUTH_SCHEMAS = {"owner": "JEPA_TD_CORRECTED_REPLAY_OWNER_DECISION_V1",
                "runtime": "JEPA_TD_CORRECTED_REPLAY_RUNTIME_AUTHORIZATION_V1",
                "operational": "JEPA_TD_CORRECTED_REPLAY_OPERATIONAL_AUTHORIZATION_V1",
                "acceptance": "JEPA_TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1"}
RATIFICATION_SCHEMA = "JEPA_TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1"
LEDGER_NAME = "TD_CORRECTED_REPLAY_ATTEMPT_LEDGER_V1.json"


def ledger_path(namespace: Path) -> Path:
    """The one-attempt ledger beside the namespace. Deleting the namespace does not re-enable an attempt."""
    return Path(namespace).parent / LEDGER_NAME


class GateError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return A.sha_file(Path(path))


def load_json(path: Path, label: str) -> dict:
    path = Path(path)
    if not path.is_file():
        raise GateError(f"missing {label}: {path}")
    rec = json.loads(path.read_bytes().decode("utf-8"))
    if not isinstance(rec, dict):
        raise GateError(f"{label} is not a JSON object")
    return rec


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise GateError(msg)


# --------------------------------------------------------------------------------------------------------- contract
def load_contract(path: Path) -> dict:
    c = load_json(path, "replay contract")
    require(c.get("schema") == "JEPA_TD_CORRECTED_REPLAY_CONTRACT_V1", "contract schema mismatch")
    require(c.get("replay_science_frozen") is True, "contract does not freeze replay science")
    g7 = c["predecessors"]["g7"]
    require(g7.get("terminal") == G7_TERMINAL and g7.get("is_pass") is False,
            "contract must keep G7 exactly NOT_ESTIMABLE and never PASS")
    require(c["predecessors"]["g7_diagnostic"].get("classification") == DIAGNOSTIC_CLASS, "diagnostic class mismatch")
    require(c["predecessors"]["g7_diagnostic"].get("claims_value_agreement") is False, "diagnostic may not claim value agreement")
    require(c["prerequisite"].get("g7_pass") is False and c["prerequisite"].get("claims_s174_sample_a_value_agreement") is False,
            "prerequisite amendment may not claim G7 PASS or value agreement")
    require(c.get("stage_order") == ["TD56", "TD57B", "TD57C", "TD59"], "stage order is not TD56 -> TD57B -> TD57C -> TD59")
    require(all(c["downstream_authority"].get(k) is False for k in DOWNSTREAM), "contract downstream authority must be false")
    return c


def validate_contract(c: dict, *, repo_root: Path, archive: Path) -> dict:
    for rel, want in c["science_references_sha256"].items():
        require(sha(repo_root / rel) == want, f"science reference changed: {rel}")
    amend = c["prerequisite_amendment"]
    require(sha(repo_root / amend["path"]) == amend["sha256"], "prerequisite amendment changed")
    lock = c["execution_environment"]["lock"]
    require(sha(repo_root / lock["path"]) == lock["sha256"], "environment lock file changed")
    require(sha(archive) == c["archive"]["sha256"], "TD41-TD58 archive SHA mismatch")
    ex = c["executors"]
    members = [v["archive_path"] for v in ex["TD56"]["by_source"].values()] + [ex[s]["archive_path"] for s in ("TD57B", "TD57C")]
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        for m in members:
            require(names.count(m) == 1, f"executor member ambiguous or missing: {m}")
        resolved = {m: hashlib.sha256(z.read(m)).hexdigest() for m in members}
    want = {v["archive_path"]: v["sha256"] for v in ex["TD56"]["by_source"].values()}
    want.update({ex[s]["archive_path"]: ex[s]["sha256"] for s in ("TD57B", "TD57C")})
    require(resolved == want, "executor archive bytes are not the frozen executors")
    require(ex["TD57B"]["fast_wrapper_bound"] is False, "TD57B fast wrapper may not replace the frozen executor")
    require(sha(repo_root / ex["TD59"]["repo_path"]) == ex["TD59"]["sha256"] ==
            "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085", "TD59 successor identity mismatch")
    return {"science_references": len(c["science_references_sha256"]), "executors_resolved": resolved,
            "td59_successor_sha256": ex["TD59"]["sha256"]}


# ------------------------------------------------------------------------------------------------------- predecessors
def authenticate_predecessors(c: dict, *, g6_namespace: Path, g6_acceptance: Path, g7_namespace: Path,
                              diagnostic_transforms: Path, diagnostic_result: Path, spent_record: Path) -> dict:
    p = c["predecessors"]
    g6 = p["g6"]
    present = {f.name for f in Path(g6_namespace).iterdir()}
    require(present == set(g6["artifact_sha256"]), f"G6 namespace is not the accepted five files: {sorted(present)}")
    for name, want in g6["artifact_sha256"].items():
        require(sha(Path(g6_namespace) / name) == want, f"accepted G6 artifact changed: {name}")
    require(sha(g6_acceptance) == g6["external_acceptance_sha256"], "G6 external acceptance is not 89932183")
    acc = load_json(g6_acceptance, "G6 acceptance")
    require(acc.get("external_audit_disposition") == G6_ACCEPT_DISPOSITION and acc.get("implementation_commit_sha") == g6["producer_commit"],
            "G6 acceptance does not accept the ff4a21f9 producer")

    g7 = p["g7"]
    marker = Path(g7_namespace) / "G7_RECEIPT.json.STARTED_NOT_A_PASS.json"
    receipt = Path(g7_namespace) / "G7_RECEIPT.json"
    require({f.name for f in Path(g7_namespace).iterdir()} == {marker.name, receipt.name}, "G7 namespace is not marker + receipt")
    require(sha(marker) == g7["marker_sha256"] and sha(receipt) == g7["receipt_sha256"], "G7 marker/receipt changed")
    r = load_json(receipt, "G7 receipt")
    require(r.get("status") == G7_TERMINAL, f"G7 receipt terminal is not {G7_TERMINAL}: {r.get('status')}")
    require(r.get("natural_overlap_cells") == 0 and r.get("checked_cell_address_entries") == 0 and r.get("mismatches") == 0
            and r.get("no_overlap_is_not_pass") is True, "G7 receipt is not the zero-overlap NOT_ESTIMABLE record")
    require(r["authority_trace"]["implementation_commit_sha"] == g7["implementation_commit"], "G7 implementation commit mismatch")
    require(all(r.get(k) is False for k in ("biological_replay_authorized", "target_selection_authorized", "td60_authorized",
                                            "training_authorized")), "G7 receipt grants downstream authority")

    d = p["g7_diagnostic"]
    require(Path(diagnostic_transforms).is_file() and Path(diagnostic_result).is_file(), "missing diagnostic evidence")
    require(sha(diagnostic_transforms) == d["transforms_sha256"], "diagnostic transforms output changed")
    require(sha(diagnostic_result) == d["result_sha256"], "diagnostic result document changed")
    t = load_json(diagnostic_transforms, "diagnostic transforms")
    require(t.get("classification") == DIAGNOSTIC_CLASS and t.get("spec_sha256") == d["spec_sha256"], "diagnostic class/spec mismatch")
    require(t.get("g7_authority_created") is False and t.get("biological_replay_authorized") is False,
            "diagnostic must create no authority")
    text = Path(diagnostic_result).read_text(encoding="utf-8")
    require(DIAGNOSTIC_CLASS in text and "not a G7 rerun" in text, "diagnostic result document does not state the classification")
    require("value agreement" not in text.lower() or "not evidence that any count disagrees" in text,
            "diagnostic result must not claim value agreement")

    spent = load_json(spent_record, "G7 spent-authority record")
    spent_shas = {x["sha256"] for x in spent.get("spent_authority", [])}
    require(spent_shas <= set(p["spent_authority_sha256"]) and len(spent_shas) == 4, "spent-authority record mismatch")
    return {"schema": "JEPA_TD_CORRECTED_REPLAY_PREDECESSOR_RECEIPT_V1", "g6_accepted": True, "g7_terminal": G7_TERMINAL,
            "g7_pass": False, "diagnostic_classification": DIAGNOSTIC_CLASS, "technical_prerequisite_closed": True,
            "closure_reason": "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS",
            "spent_authority_refused": sorted(p["spent_authority_sha256"])}


# ------------------------------------------------------------------------------------------ outcome-blind qualify
def structural_estimability(c: dict, *, g6_meta: Path, sample_freeze: Path, archive: Path) -> dict:
    """Metadata only: comparison populations must exist and equal the historical ones."""
    view = A.metadata_view(g6_meta, sample_freeze)
    out = {}
    for s in A.SOURCES:
        hist = A.historical_td50(archive, s)
        m = view["source"] == s
        rows = view["global_row"][m]
        order = np.argsort(rows)
        require(np.array_equal(rows[order], hist["global_row"]), f"{s}: G6 rows differ from the historical td50 rows")
        require(np.array_equal(view["donor"][m][order], hist["donor"].astype(str)), f"{s}: donor identities differ")
        require(np.array_equal(view["operator"][m][order], hist["operator"].astype(np.int64)), f"{s}: operator identities differ")
        donors = view["donor"][m]
        ops = view["operator"][m]
        strata = {}
        for d, o in zip(donors.tolist(), ops.tolist()):
            strata[(d, o)] = strata.get((d, o), 0) + 1
        big = {k: v for k, v in strata.items() if v >= STRUCTURAL_FLOORS["min_cells_per_stratum"]}
        donors_with_big = sorted({k[0] for k in big})
        out[s] = {"cells": int(m.sum()), "donors": int(len(set(donors.tolist()))), "strata": len(strata),
                  "strata_ge_4_cells": len(big), "donors_with_stratum_ge_4": len(donors_with_big),
                  "structure_equals_historical_td50": True}
        require(len(donors_with_big) >= STRUCTURAL_FLOORS["td56_min_donors"], f"{s}: comparison population below TD56 floor")
        require(len(donors_with_big) >= STRUCTURAL_FLOORS["td57c_td59_min_structural_donors"], f"{s}: below TD57C/TD59 floor")
        require(len(donors_with_big) >= 2 * STRUCTURAL_FLOORS["td57b_min_donors_per_half"], f"{s}: below TD57B half floor")
    return out


def ratification_state(c: dict, ratification: Path | None) -> dict:
    decisions = c["decisions_requiring_owner_ratification"]
    if ratification is None:
        return {"status": "PENDING_OWNER_RATIFICATION", "decisions": {k: v["status"] for k, v in decisions.items()}}
    r = load_json(ratification, "decision ratification")
    require(r.get("schema") == RATIFICATION_SCHEMA, "ratification schema mismatch")
    require(r.get("contract_sha256") == sha(ROOT / CONTRACT_REL), "ratification is not bound to this contract")
    got = r.get("ratified", {})
    require(got.get("detected_field") == decisions["detected_field"]["proposed"], "ratified detected field differs from the contract")
    require(got.get("routing_input_rule") == decisions["routing_input_rule"]["proposed"], "ratified routing rule differs from the contract")
    return {"status": "RATIFIED", "ratification_sha256": sha(ratification), "detected_field": got["detected_field"]}


EQUIVALENCE_CASES = ({f"TD56_{s}" for s in A.SOURCES} | {f"TD57B_{s}_P{p}" for s in A.SOURCES for p in (0, 1)}
                     | {"TD57C_HVS_P0"} | {f"TD59_{s}_P{p}" for s in A.SOURCES for p in (0, 1)})


def validate_equivalence(c: dict, receipt: Path, *, implementation_commit: str) -> dict:
    """The adapter-fed exact executors must have reproduced every historical case, with this exact adapter code."""
    r = load_json(receipt, "equivalence receipt")
    require(r.get("schema") == "JEPA_TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1", "equivalence receipt schema mismatch")
    require(r.get("implementation_commit_sha") == implementation_commit, "equivalence was not run at this implementation commit")
    require({x["case"] for x in r.get("cases", [])} == EQUIVALENCE_CASES and r.get("n_cases") == 16,
            "equivalence case set is not the 16 historical cases")
    require(r.get("all_equal") is True and all(x["equal"] for x in r["cases"]),
            "historical-fixture equivalence did not reproduce every case")
    require(r.get("td57c_historical_fail_reproduced") is True, "TD57C historical failure was not reproduced")
    require(r["code_sha256"]["adapter"] == sha(Path(A.__file__)) and r["code_sha256"]["bootstrap"] == sha(A.BOOTSTRAP),
            "equivalence was run with different adapter/bootstrap bytes")
    env, want = r["environment"], c["execution_environment"]
    require(env.get("platform") == "Linux" and all(env.get(k) == want[k] for k in ("python", "numpy", "scipy", "pandas")),
            "equivalence environment is not the pinned replay environment")
    require(r.get("corrected_values_read") is False, "equivalence may not read corrected values")
    return {"equivalence_receipt_sha256": sha(receipt), "cases_equal": 16, "td57c_historical_fail_reproduced": True}


def qualify(c: dict, *, args) -> dict:
    contract = validate_contract(c, repo_root=ROOT, archive=Path(args.archive))
    equivalence = validate_equivalence(c, Path(args.equivalence_receipt), implementation_commit=args.implementation_commit)
    pred = authenticate_predecessors(c, g6_namespace=Path(args.g6_namespace), g6_acceptance=Path(args.g6_acceptance),
                                     g7_namespace=Path(args.g7_namespace), diagnostic_transforms=Path(args.diagnostic_transforms),
                                     diagnostic_result=Path(args.diagnostic_result), spent_record=Path(args.spent_record))
    est = structural_estimability(c, g6_meta=Path(args.g6_namespace) / "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz",
                                  sample_freeze=Path(args.sample_freeze), archive=Path(args.archive))
    support = A.check_support_bundle(Path(args.support_bundle))
    ns = Path(args.namespace)
    require(not ns.exists(), f"replay namespace already exists (spent or occupied): {ns}")
    require(not ledger_path(ns).exists(), f"attempt ledger exists; the one corrected-replay attempt is spent: {ledger_path(ns)}")
    rat = ratification_state(c, Path(args.ratification) if args.ratification else None)
    ok = rat["status"] == "RATIFIED"
    return {"schema": "JEPA_TD_CORRECTED_REPLAY_QUALIFY_RECEIPT_V1",
            "terminal": ("PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED" if ok
                         else "QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN"),
            "contract_sha256": sha(ROOT / CONTRACT_REL), "contract": contract, "predecessors": pred,
            "structural_estimability": est, "historical_fixture_equivalence": equivalence, "ratification": rat,
            "support_bundle": support, "namespace_fresh": str(ns), "attempt_ledger_absent": True,
            "implementation_commit_sha": args.implementation_commit,
            "corrected_values_opened": False, "replay_kernels_run": False, "start_marker_created": False,
            **{k: False for k in DOWNSTREAM}}


# ------------------------------------------------------------------------------------------------------ authority
def validate_authority(c: dict, *, owner: Path, runtime: Path, operational: Path, acceptance: Path | None,
                       expected_operational_sha: str, expected_acceptance_sha: str | None, code: dict,
                       equivalence_receipt: Path) -> dict:
    spent = set(c["predecessors"]["spent_authority_sha256"])
    recs = {"owner": owner, "runtime": runtime, "operational": operational}
    if acceptance is not None:
        recs["acceptance"] = acceptance
    shas = {k: sha(v) for k, v in recs.items()}
    require(not (set(shas.values()) & spent), "spent authority may not be reused")
    require(shas["operational"] == expected_operational_sha, "operational authorization is not the audited SHA")
    if acceptance is not None:
        require(shas["acceptance"] == expected_acceptance_sha, "launch-audit acceptance is not the given SHA")
    contract_sha = sha(ROOT / CONTRACT_REL)
    for k, path in recs.items():
        r = load_json(path, k)
        require(r.get("schema") == AUTH_SCHEMAS[k], f"{k} schema mismatch")
        require(r.get("scope") == "CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY", f"{k} is not replay-only")
        require(all(r.get(f) is False for f in DOWNSTREAM), f"{k} must keep every downstream flag false")
        extra = sorted(f for f, v in r.items() if f.endswith("_authorized") and v is not False
                       and f != "corrected_replay_execution_authorized")
        require(not extra, f"{k} authorizes beyond the replay: {extra}")
        require(r.get("contract_sha256") == contract_sha, f"{k} is not bound to this contract")
        require(r.get("implementation_commit_sha") == code["implementation_commit_sha"], f"{k} is not bound to this implementation")
    rt = load_json(runtime, "runtime")
    require(rt.get("owner_decision_sha256") == shas["owner"], "runtime does not bind the owner decision")
    require(rt.get("code_sha256") == code["code_sha256"], "runtime does not bind the exact code identity")
    require(rt.get("equivalence_receipt_sha256") == sha(equivalence_receipt), "runtime does not bind this equivalence receipt")
    require(rt.get("environment_lock_sha256") == c["execution_environment"]["lock"]["sha256"],
            "runtime does not bind the contract environment lock")
    op = load_json(operational, "operational")
    require(op.get("owner_decision_sha256") == shas["owner"] and op.get("runtime_authorization_sha256") == shas["runtime"],
            "operational does not bind owner/runtime")
    require(op.get("corrected_replay_execution_authorized") is True and op.get("single_attempt") is True,
            "operational must authorize exactly one corrected replay attempt")
    require(op.get("namespace") == c["namespace"]["root_windows"], "operational namespace mismatch")
    if acceptance is not None:
        ac = load_json(acceptance, "acceptance")
        require(ac.get("disposition") == "ACCEPT_TD_CORRECTED_REPLAY_LAUNCH_PACKAGE__EXECUTE_ONCE", "acceptance disposition")
        require(ac.get("operational_authorization_sha256") == shas["operational"], "acceptance does not bind the operational authorization")
        require(ac.get("code_sha256") == code["code_sha256"], "acceptance does not bind the exact code identity")
    return {"authority_sha256": shas, "authority_check": "PASS"}


CODE_FILES = (
    "scripts/v5/td_corrected_replay_adapter_v1.py", "scripts/v5/td_corrected_replay_exec_bootstrap_v1.py",
    "scripts/v5/td_corrected_replay_gate_v1.py", "scripts/v5/td_corrected_replay_execute_v1.py",
    "scripts/v5/td_corrected_replay_evidence_v1.py", "scripts/v5/run_td_corrected_replay_once.sh",
    "scripts/v5/build_td_corrected_replay_contract_v1.py", "scripts/v5/td_corrected_replay_routing_v2.py",
    "scripts/v5/td_target_tournament_routing_v4.py", CONTRACT_REL,
    "target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_PREREQUISITE_AMENDMENT_20261012.json")


def code_identity(root: Path = ROOT) -> dict:
    """SHA-256 of every file that defines the replay package, plus one aggregate over sorted (path, SHA)."""
    files = {rel: sha(Path(root) / rel) for rel in CODE_FILES}
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode()); h.update(b"\0"); h.update(bytes.fromhex(files[rel])); h.update(b"\0")
    return {"files": files, "code_sha256": h.hexdigest()}


def preflight_execute(c: dict, *, qualify_receipt: Path, authority_check: Path, ratification: Path,
                      implementation_commit: str, namespace: Path) -> dict:
    """Pure checks the orchestrator repeats before the marker, so it cannot be run around the launcher's gates."""
    q = load_json(qualify_receipt, "QUALIFY receipt")
    require(str(q.get("terminal", "")).startswith("PASS_"), "EXECUTE requires a ratified QUALIFY PASS receipt")
    require(q.get("contract_sha256") == sha(ROOT / CONTRACT_REL) and q.get("implementation_commit_sha") == implementation_commit,
            "QUALIFY receipt is not for this contract and implementation")
    require(q.get("namespace_fresh") == str(Path(namespace)), "QUALIFY receipt is not for this namespace")
    rat = ratification_state(c, ratification)
    require((q.get("ratification") or {}).get("ratification_sha256") == rat["ratification_sha256"],
            "QUALIFY was not run with this ratification")
    au = load_json(authority_check, "authority check")
    require(au.get("authority_check") == "PASS" and "acceptance" in (au.get("authority_sha256") or {}),
            "EXECUTE requires an authority check that includes the launch-audit acceptance")
    require(au.get("code_sha256") == code_identity()["code_sha256"] and au.get("implementation_commit_sha") == implementation_commit,
            "authority check is not for this code and implementation")
    require(rat["detected_field"] in A.DETECTED_FIELDS, "ratified detected field is not a G6 metadata field")
    ns = Path(namespace)
    require(not ns.exists() and not ledger_path(ns).exists(), "replay namespace or attempt ledger already exists; attempt spent")
    return {"authority_sha256": au["authority_sha256"], "detected_field": rat["detected_field"],
            "ratification_sha256": rat["ratification_sha256"]}


def _exclusive_json(path: Path, rec: dict) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec, indent=2, sort_keys=True) + "\n")


def begin_attempt(namespace: Path, payload: dict) -> Path:
    """The only creator of the attempt ledger and the start marker. Exclusive create; the namespace and authority are
    spent from here on, and the ledger keeps them spent even if the namespace is later removed."""
    ns = Path(namespace)
    ledger = ledger_path(ns)
    if ns.exists() or ledger.exists():
        raise GateError(f"replay namespace or attempt ledger already exists; attempt spent or occupied: {ns}")
    rec = {"schema": "JEPA_TD_CORRECTED_REPLAY_EXECUTION_START_V1", "status": "STARTED_NOT_A_RESULT",
           **payload, **{k: False for k in DOWNSTREAM}}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    try:
        _exclusive_json(ledger, {**rec, "schema": "JEPA_TD_CORRECTED_REPLAY_ATTEMPT_LEDGER_V1", "status": "ATTEMPT_SPENT",
                                 "namespace": str(ns)})
        ns.mkdir()
    except FileExistsError as exc:
        raise GateError(f"replay namespace or attempt ledger already exists; attempt spent or occupied: {exc}") from exc
    marker = ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    _exclusive_json(marker, rec)
    return marker


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("qualify")
    for n in ("archive", "g6-namespace", "g6-acceptance", "g7-namespace", "diagnostic-transforms", "diagnostic-result",
              "spent-record", "sample-freeze", "namespace", "record", "equivalence-receipt", "implementation-commit",
              "support-bundle"):
        q.add_argument(f"--{n}", required=True)
    q.add_argument("--ratification")
    au = sub.add_parser("authority")
    for n in ("owner", "runtime", "operational", "expected-operational-sha256", "implementation-commit", "record",
              "equivalence-receipt"):
        au.add_argument(f"--{n}", required=True)
    au.add_argument("--acceptance")
    au.add_argument("--expected-acceptance-sha256")
    sub.add_parser("code-identity")
    a = ap.parse_args()
    c = load_contract(ROOT / CONTRACT_REL)
    if a.cmd == "code-identity":
        print(json.dumps(code_identity(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "authority":
        code = {**code_identity(), "implementation_commit_sha": a.implementation_commit}
        out = validate_authority(c, owner=Path(a.owner), runtime=Path(a.runtime), operational=Path(a.operational),
                                 acceptance=Path(a.acceptance) if a.acceptance else None,
                                 expected_operational_sha=a.expected_operational_sha256,
                                 expected_acceptance_sha=a.expected_acceptance_sha256, code=code,
                                 equivalence_receipt=Path(a.equivalence_receipt))
        out["code_sha256"] = code["code_sha256"]
        out["implementation_commit_sha"] = a.implementation_commit
        Path(a.record).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    if a.cmd == "qualify":
        out = qualify(c, args=a)
        rec = Path(a.record)
        rec.write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(json.dumps({"terminal": out["terminal"], "receipt_sha256": sha(rec)}, indent=2))
        return 0 if out["terminal"].startswith("PASS_") else 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
