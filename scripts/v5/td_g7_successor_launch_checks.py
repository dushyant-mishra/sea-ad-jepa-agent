#!/usr/bin/env python3
"""Fail-closed launch checks for the one-shot TD G7 successor run at 8d41fb98. THIS FILE DOES NOT RUN G7.

External audit (PR #296, review 5486851355) accepted the qualification at 8d41fb98, with launch conditions:
  R1  Every successor authority record states g6_execution_authorized=false. The operational authorization is G7-only,
      and the launcher refuses without the explicit false flag and invokes only the G7 entrypoint. No G6 rerun.
  R2  Before the attempt marker can be reached, the launcher repeats and passes, independently: the G1b authority load,
      all 35 S174 shard hashes, coverage of all 34 HVS/SEA matrices, and the matrix->stem->shard join.
  The launch also uses the exact G6 acceptance bytes from immutable source, the accepted G6 receipt from
  G6_OUT_ff4a21f9, a fresh G7 namespace, and fresh authority bound to 8d41fb98 / 23be96f8 / 8e6504e0 / 275dad00.

Subcommands:
  acceptance Validate the external launch-audit acceptance (EXECUTE only): it must bind this exact authority commit,
             operational authorization, launcher and checks. The auditor creates it; this package never does.
  authority  Validate the three materialized authority records (R1, bindings, no reuse of spent ff4a21f9 authority).
  prestart   Run, read-only, everything G7's main() does before begin_g7_attempt, using G7's own functions from the
             exact execution worktree: bind_execution, expected_authority_trace, producer continuity, load_inputs and
             the accepted-G6 bridge. Then run the R2 replay of the post-marker metadata prerequisites. No marker,
             receipt, H5AD dataset read or S174 count read.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

IMPLEMENTATION_COMMIT = "8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27"
CODE_IDENTITY = {
    "implementation_commit_sha": IMPLEMENTATION_COMMIT,
    "common_script_sha256": "23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea",
    "g6_script_sha256": "8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d",
    "g7_script_sha256": "275dad00c6bd37ef11a34a376c703b4433ed40eae8d087c4d8f9535f88170412",
    "common_entrypoint": "scripts/v5/td_relational_value_read_v2_common.py",
    "g6_entrypoint": "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
    "g7_entrypoint": "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py",
}
PR259 = {"preflight_result_sha256": "62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae",
         "mapping_receipt_sha256": "6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0",
         "replay_manifest_sha256": "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"}
G6_PRODUCER_COMMIT = "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
G6_ACCEPTANCE_SHA = "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb"
G6_ACCEPTANCE_SOURCE = {"commit": "17a68667174ae8583305c546639dced7dded94d9",
                        "path": "docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json"}
G6_ARTIFACTS = {
    "G6_EXECUTION_START.json": "49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1",
    "G6_RECEIPT.json": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
    "MANIFEST.json": "4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf",
    "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz": "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9",
    "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz": "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74",
}
G6_RECEIPT_PATH = "D:/jepa_td_real_g6_20261011/G6_OUT_ff4a21f9/G6_RECEIPT.json"
G7_OUTPUT_NAMESPACE = "D:/jepa_td_real_g6_20261011/G7_OUT_8d41fb98"
SPENT_AUTHORITY_SHA = {  # ff4a21f9 authority: spent, must never be reused for the successor
    "3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a",
    "28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7",
    "19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee",
}
EXTERNAL_AUDIT = {"pr": 296, "review_id": 5486851355,
                  "classification": "ACCEPT_G7_SUCCESSOR_QUALIFICATION__8d41fb98__PREMARKER_DEFECT_REPAIRED__"
                                    "ACCEPTED_G6_PREDECESSOR_BRIDGE_CONFIRMED__NO_G7_EXECUTION_AUTHORITY_YET"}
OPERATIONAL_SCHEMA = "JEPA_TD_G7_OPERATIONAL_AUTHORIZATION_V2"
OPERATIONAL_AUTHORIZATION = ("EXECUTE_G7_SUCCESSOR_ONCE_AT_8d41fb98__G7_ENTRYPOINT_ONLY__NO_G6_RERUN__AGAINST_ACCEPTED_"
                             "G6_ff4a21f9__FRESH_OUTPUT__STOP_FOR_EXTERNAL_AUDIT")
PRESTART_REQUIREMENTS = ["G7_OWN_PREMARKER_PATH_INCLUDING_BIND_EXECUTION", "G1B_AUTHORITY_LOAD",
                         "ALL_35_S174_SHARD_HASHES", "ALL_34_HVS_SEA_MATRICES_COVERED", "MATRIX_STEM_SHARD_JOIN",
                         "PHYSICAL_SOURCES_PRESENT_AT_FROZEN_SIZES", "PROVENANCE_IDENTIFIERS_UNIQUE_PER_FAMILY"]
PYTHON_ENVIRONMENT = {"interpreter": "C:/Users/dushy/anaconda3/python.exe", "python": "3.9.7", "numpy": "1.24.2",
                      "pandas": "1.5.3", "scipy": "1.10.1", "h5py": "3.2.1"}   # the environment that qualified 8d41fb98
LAUNCH_ACCEPTANCE_PATH = "custody/owner_decisions/20261012/TD_G7_LAUNCH_AUDIT_ACCEPTANCE_8d41fb98.json"
LAUNCH_ACCEPTANCE_SCHEMA = "JEPA_TD_G7_LAUNCH_AUDIT_ACCEPTANCE_V1"
LAUNCH_ACCEPTANCE_DISPOSITION = "ACCEPT_G7_SUCCESSOR_LAUNCH_PACKAGE__EXECUTE_G7_ONCE"
FAMILY = {"HVS": "HVS_COMMON", "SEA_AD": "SEA_AD_COMMON"}
FALSE_FLAGS = ("biological_replay_authorized", "target_selection_authorized", "td60_authorized", "training_authorized")
N_S174_SHARDS = 35
N_HVS_SEA_MATRICES = 34


def stop(msg: str) -> None:
    raise SystemExit(f"STOP: {msg}")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    rec = json.loads(Path(path).read_bytes().decode("utf-8"))
    if not isinstance(rec, dict):
        stop(f"not a JSON object: {path}")
    return rec


def _require(rec: dict, want: dict, label: str) -> None:
    for key, value in want.items():
        if rec.get(key) != value:
            stop(f"{label}: {key} must be {value!r}, found {rec.get(key)!r}")


def _require_g6_scope_lock(rec: dict, label: str) -> None:
    """R1: the explicit false flag must be present. A missing key is a refusal."""
    if "g6_execution_authorized" not in rec or rec["g6_execution_authorized"] is not False:
        stop(f"{label}: R1 scope lock requires explicit g6_execution_authorized=false")
    _require(rec, {k: False for k in FALSE_FLAGS}, label)


def validate_owner_decision(rec: dict) -> None:
    _require(rec, {"schema": "JEPA_TD_RELATIONAL_G6_G7_OWNER_DECISION_V1", "decision": "AUTHORIZE_G6_G7_INTEGRITY_ONLY",
                   "authorized_pr259_preflight_driver_sha256": PR259["preflight_result_sha256"],
                   "authorized_pr259_mapping_receipt_sha256": PR259["mapping_receipt_sha256"],
                   "qualified_implementation_commit_sha": IMPLEMENTATION_COMMIT,
                   "external_audit_reference": EXTERNAL_AUDIT}, "owner decision")
    _require_g6_scope_lock(rec, "owner decision")


def validate_runtime_authorization(rec: dict, owner_sha: str) -> None:
    _require(rec, {"schema": "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2",
                   "authorization": "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY",
                   "owner_decision_sha256": owner_sha, **PR259, **CODE_IDENTITY,
                   "external_audit_reference": EXTERNAL_AUDIT}, "runtime authorization")
    _require_g6_scope_lock(rec, "runtime authorization")


def validate_operational_authorization(rec: dict, *, owner_sha: str, runtime_sha: str, launcher_sha: str,
                                       checks_sha: str) -> None:
    _require(rec, {"schema": OPERATIONAL_SCHEMA, "authorization": OPERATIONAL_AUTHORIZATION, **CODE_IDENTITY,
                   "g7_entrypoint_only": True, "g6_rerun_permitted": False,
                   "required_code_consumed_owner_decision_sha256": owner_sha,
                   "required_code_consumed_runtime_authorization_sha256": runtime_sha,
                   "g6_producer_commit_sha": G6_PRODUCER_COMMIT, "g6_external_acceptance_sha256": G6_ACCEPTANCE_SHA,
                   "g6_external_acceptance_source": G6_ACCEPTANCE_SOURCE, "g6_artifact_sha256": G6_ARTIFACTS,
                   "g6_receipt_path": G6_RECEIPT_PATH, "fresh_g7_output_namespace": G7_OUTPUT_NAMESPACE,
                   "launcher_sha256": launcher_sha, "launch_checks_sha256": checks_sha,
                   "prestart_requirements": PRESTART_REQUIREMENTS, "python_environment": PYTHON_ENVIRONMENT,
                   "launch_audit_acceptance_path": LAUNCH_ACCEPTANCE_PATH,
                   "launch_audit_acceptance_schema": LAUNCH_ACCEPTANCE_SCHEMA,
                   "launch_audit_acceptance_disposition": LAUNCH_ACCEPTANCE_DISPOSITION, "fresh_output_required": True,
                   "stop_after_g7": True, "requires_exact_launch_audit_before_execution": True,
                   "expected_g7_pass_terminal": "PASS_TD_G7_S174_EXACT_OVERLAP",
                   "corrected_biological_replay_authorized": False, "stage4_authorized": False,
                   "external_audit_reference": EXTERNAL_AUDIT}, "operational authorization")
    _require_g6_scope_lock(rec, "operational authorization")
    extra = sorted(k for k, v in rec.items() if k.endswith("_authorized") and v is not False)
    if extra:
        stop(f"operational authorization may not authorize anything beyond the G7 run: {extra}")


def validate_authority(owner: Path, runtime: Path, operational: Path, *, expected_operational_sha: str,
                       launcher: Path, checks: Path) -> dict:
    hashes = {"owner_decision": sha(owner), "runtime_authorization": sha(runtime), "operational_authorization": sha(operational)}
    if hashes["operational_authorization"] != expected_operational_sha:
        stop(f"operational authorization SHA {hashes['operational_authorization']} is not the audited "
             f"{expected_operational_sha}")
    reused = sorted(k for k, v in hashes.items() if v in SPENT_AUTHORITY_SHA)
    if reused:
        stop(f"spent ff4a21f9 authority reused: {reused}")
    validate_owner_decision(load_json(owner))
    validate_runtime_authorization(load_json(runtime), hashes["owner_decision"])
    validate_operational_authorization(load_json(operational), owner_sha=hashes["owner_decision"],
                                       runtime_sha=hashes["runtime_authorization"], launcher_sha=sha(launcher),
                                       checks_sha=sha(checks))
    return {**hashes, "launcher_sha256": sha(launcher), "launch_checks_sha256": sha(checks),
            "r1_scope_lock": "g6_execution_authorized=false in all three records; G7 entrypoint only"}


def validate_launch_acceptance(acceptance: Path, *, expected_sha: str, authority_commit: str, operational: Path,
                               launcher: Path, checks: Path) -> dict:
    """EXECUTE release: the external auditor's committed acceptance of this exact launch package."""
    actual = sha(acceptance)
    if actual != expected_sha:
        stop(f"launch-audit acceptance SHA {actual} is not {expected_sha}")
    rec = load_json(acceptance)
    _require(rec, {"schema": LAUNCH_ACCEPTANCE_SCHEMA, "disposition": LAUNCH_ACCEPTANCE_DISPOSITION,
                   "implementation_commit_sha": IMPLEMENTATION_COMMIT, "authority_commit_sha": authority_commit,
                   "operational_authorization_sha256": sha(operational), "launcher_sha256": sha(launcher),
                   "launch_checks_sha256": sha(checks), "fresh_g7_output_namespace": G7_OUTPUT_NAMESPACE,
                   "single_g7_attempt": True, "corrected_biological_replay_authorized": False,
                   "stage4_authorized": False}, "launch-audit acceptance")
    _require_g6_scope_lock(rec, "launch-audit acceptance")
    extra = sorted(k for k, v in rec.items() if k.endswith("_authorized") and v is not False)
    if extra:
        stop(f"launch-audit acceptance may not authorize anything beyond the G7 run: {extra}")
    return {"launch_audit_acceptance_sha256": actual, "launch_acceptance_check": "PASS"}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def prestart(exec_root: Path, args: argparse.Namespace) -> dict:
    """G7's own pre-marker path plus the R2 replay. Read-only: no marker, receipt, H5AD dataset or S174 counts."""
    g7_path = Path(exec_root) / CODE_IDENTITY["g7_entrypoint"]
    g7 = _load_module(g7_path, "td_g7_successor_prestart")
    if Path(g7.__file__).resolve() != g7_path.resolve():
        stop("G7 module did not load from the execution worktree")

    # the exact pre-marker sequence of g7.main(), stopping before begin_g7_attempt
    auth, _, _, g6_path, g7_resolved = g7.bind_execution(args)
    trace = g7.expected_authority_trace(args, auth, g6_path, g7_resolved)
    if {k: trace[k] for k in CODE_IDENTITY} != CODE_IDENTITY:
        stop(f"executing code identity is not the qualified successor: {trace}")
    g7.require_g6_producer_code_continuity(trace)
    replay, sample_a, provenance, _, macha = g7.load_inputs(args)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    pred = g7.load_accepted_g6_predecessor(Path(args.g6_receipt), Path(args.g6_acceptance),
                                           replay_addresses=replay_addresses, sample_a=sample_a)
    if pred["g7_verified_g6_execution_sha256"]["receipt"] != G6_ARTIFACTS["G6_RECEIPT.json"]:
        stop("accepted G6 receipt mismatch")

    # R2: post-marker metadata prerequisites, replayed before the marker with G7's own functions
    import h5py  # noqa: F401  G7 imports these lazily after its marker; they must resolve now
    from scipy import sparse  # noqa: F401
    _, g1b_freeze, g1b_result_sha, g1b_freeze_sha = g7.load_g1b_authority_from_pass_commit(g7_resolved)
    cache = Path(args.s174_cache_root)
    n_verified, _ = g7.verify_cache_hashes(cache, g1b_freeze)
    shards = g1b_freeze["rebuilt_cache"]["shards"]
    if n_verified != N_S174_SHARDS or len(shards) != N_S174_SHARDS:
        stop(f"S174 shard count {n_verified}/{len(shards)} != {N_S174_SHARDS}")
    for study in sorted(set(sample_a.source.astype(str)) - {"NPH52"}):   # G7 checks this after its marker
        fprov = provenance[provenance.source_dataset_id.astype(str).eq(FAMILY[study])]
        if fprov.empty or fprov.source_exact_ensembl_id.astype(str).duplicated().any():
            stop(f"provenance identifiers missing or nonunique for {study}")
    matrices = {str(m["matrix_id"]): m for m in macha["matrices"]}
    joined = {}
    for mid0, group in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        mid = str(mid0)
        rec = matrices.get(mid)
        if rec is None:
            stop(f"matrix absent from Macha freeze: {mid}")
        stem = str(rec["stem"])
        authority = shards.get(stem)
        if authority is None:
            stop(f"S174 shard absent from G1b authority: {mid} -> {stem}")
        cells, where, _ = g7.load_s174_cell_index(cache / f"{stem}.meta.npz", authority["meta"])
        if len(where) != len(cells):
            stop(f"duplicate S174 cell_id in shard {stem}")
        if not (cache / f"{stem}.counts.npz").is_file():
            stop(f"S174 counts shard missing: {stem}")
        src = Path(args.source_root) / str(rec["source"]["path"])
        if not src.is_file() or os.path.getsize(src) != int(rec["source"]["bytes"]):
            stop(f"physical source missing or resized: {mid}")
        joined[mid] = {"stem": stem, "study": str(group.source.iloc[0]), "sample_a_rows": int(len(group))}
    if len(joined) != N_HVS_SEA_MATRICES:
        stop(f"HVS/SEA matrix coverage {len(joined)} != {N_HVS_SEA_MATRICES}")
    return {"g7_premarker_path": "PASS", "successor_authority_trace": trace,
            "accepted_g6_receipt_sha256": pred["g7_verified_g6_execution_sha256"]["receipt"],
            "g1b_result_sha256": g1b_result_sha, "g1b_freeze_sha256": g1b_freeze_sha,
            "s174_verified_shards": n_verified, "hvs_sea_matrices_joined": len(joined),
            "sample_a_hvs_sea_rows": sum(v["sample_a_rows"] for v in joined.values()),
            "r2_prestart_replay": "PASS", "g7_marker_created": False}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    acc = sub.add_parser("acceptance")
    for name in ("acceptance", "expected-acceptance-sha256", "authority-commit", "operational-authorization", "launcher"):
        acc.add_argument(f"--{name}", required=True)
    a = sub.add_parser("authority")
    for name in ("owner-decision", "runtime-authorization", "operational-authorization", "expected-operational-sha256",
                 "launcher"):
        a.add_argument(f"--{name}", required=True)
    p = sub.add_parser("prestart")
    p.add_argument("--exec-root", required=True)
    for name in ("preflight-result", "mapping-receipt", "value-authorization", "owner-decision", "g6-receipt",
                 "g6-acceptance", "replay-manifest", "sample-freeze", "provenance", "collision-ledger", "macha-freeze",
                 "s174-cache-root", "source-root"):
        p.add_argument(f"--{name}", required=True)
    args = ap.parse_args()
    if args.cmd == "acceptance":
        print(json.dumps(validate_launch_acceptance(
            Path(args.acceptance), expected_sha=args.expected_acceptance_sha256, authority_commit=args.authority_commit,
            operational=Path(args.operational_authorization), launcher=Path(args.launcher), checks=Path(__file__)),
            indent=2, sort_keys=True))
    elif args.cmd == "authority":
        out = validate_authority(Path(args.owner_decision), Path(args.runtime_authorization),
                                 Path(args.operational_authorization),
                                 expected_operational_sha=args.expected_operational_sha256,
                                 launcher=Path(args.launcher), checks=Path(__file__))
        print(json.dumps({**out, "authority_check": "PASS"}, indent=2, sort_keys=True))
    else:
        print(json.dumps(prestart(Path(args.exec_root), args), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
