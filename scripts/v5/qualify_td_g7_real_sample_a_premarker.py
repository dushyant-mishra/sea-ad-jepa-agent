#!/usr/bin/env python3
"""Read-only real-file qualification of the successor G7's pre-marker path. THIS FILE DOES NOT RUN G7.

The successor G7's own pre-marker path is exercised against the authenticated real inputs:
  1. The real Sample-A freeze (79eb005c) has no physical global_row column. G7's own select_sample_a() derives it
     from the freeze-file row position (0..24999), and the result is identical to the accepted G6 selector's.
  2. G7's own load_inputs() runs with every pinned real metadata input (no count values).
  3. Producer-code continuity: this tree's common and G6 are byte-identical to the accepted G6 producer at ff4a21f9.
  4. G7's load_accepted_g6_predecessor() runs on the real accepted G6 namespace and the real external acceptance.
     This is the full G6 prerequisite: pinned hashes, authority linkage, coverage, and structural validation of the
     values and metadata NPZ against the real Sample-A rows.
The one pre-marker step not exercised is bind_execution(): it needs the owner's fresh successor authority, which does
not exist and is never created here.

Read-only negative probes:
  N1. The old ff4a21f9 runtime authorization and owner decision, with the real PR #259 receipts, cannot authorize
      this successor code.
  N2. The old fafd4309 G6 namespace (start marker only) is refused as a predecessor.
  N3. The old G7 at ff4a21f9 reproduces the real-run failure on the same real freeze: no global_row, and the shared
      metadata validator raises AttributeError.
  N4. The spent ff4a21f9 G7 operational authorization binds the old G7 code and cannot release this successor.

No G7 start marker, receipt or output is created. No H5AD file is opened, and h5py is never imported. No S174 count
cache, TD56/57B/57C/59/TD60 or training. Nothing is written; the result is printed as JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
V5 = ROOT / "scripts" / "v5"
G6_PATH = V5 / "materialize_td_relational_corrected_sampleA_v2.py"
G7_PATH = V5 / "audit_td_relational_g7_s174_overlap_v2.py"
COMMON_PATH = V5 / "td_relational_value_read_v2_common.py"

REAL_SAMPLE_FREEZE_SHA = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
OLD_COMMIT = "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
OLD_G7_SHA = "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe"
OLD_OWNER_DECISION_SHA = "3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a"
OLD_RUNTIME_AUTHORIZATION_SHA = "28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7"
OLD_G7_OPERATIONAL_AUTHORIZATION = ("eba777767928d27032fc23a23b185ebdeb1c881a",
                                    "custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json",
                                    "19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee")
OLD_G6_START_MARKER_SHA = "ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894"
TERMINAL = "PASS_TD_G7_SUCCESSOR_REAL_SAMPLE_A_PREMARKER_GATE__NO_G7_MARKER__NO_H5AD__NO_AUTHORITY_CREATED"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"STOP: {message}")


def refusal(fn) -> str:
    """Run a probe that must refuse; return the refusal, fail the gate if it is accepted."""
    try:
        fn()
    except (RuntimeError, AttributeError, KeyError) as exc:
        return f"{type(exc).__name__}: {exc}"
    raise SystemExit("STOP: a negative probe was accepted")


def git_blob(rev: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{rev}:{path}"])


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("sample-freeze", "replay-manifest", "provenance", "collision-ledger", "macha-freeze", "g6-receipt",
                 "g6-acceptance", "preflight-result", "mapping-receipt", "old-owner-decision",
                 "old-runtime-authorization", "old-g6-namespace"):
        p.add_argument(f"--{name}", required=True)
    args = p.parse_args()
    out: dict = {"schema": "JEPA_TD_G7_SUCCESSOR_REAL_PREMARKER_GATE_V1"}

    g7 = load(G7_PATH, "td_g7_successor_real_gate")
    common = g7.common
    g6 = load(G6_PATH, "td_g6_reference_real_gate")

    # 1. real freeze: no physical global_row; G7 derives it; identical to the accepted G6 selector
    freeze_path = Path(args.sample_freeze)
    require(sha(freeze_path) == REAL_SAMPLE_FREEZE_SHA, "real Sample-A freeze SHA mismatch")
    frame = pd.read_csv(freeze_path, dtype=str)
    require("global_row" not in frame.columns, "the real freeze unexpectedly carries a physical global_row")
    selected = g7.select_sample_a(frame)
    require(selected["global_row"].astype(int).tolist() == list(range(25_000)), "G7 global_row is not 0..24999")
    require(selected["sample_row"].astype(int).tolist() == list(range(25_000)), "G7 sample_row is not 0..24999")
    reference = g6.select_sample_a(frame, enforce_geometry=True)
    for col in ("global_row", "sample_row", "cell_id", "source", "matrix_id", "local_row", "donor_id", "operator_index"):
        require(selected[col].astype(str).tolist() == reference[col].astype(str).tolist(), f"G7 and G6 selectors differ: {col}")
    out["1_real_freeze"] = {"sha256": REAL_SAMPLE_FREEZE_SHA, "rows": int(len(frame)),
                            "physical_global_row_column": False, "columns": list(frame.columns),
                            "g7_sample_a_rows": int(len(selected)),
                            "g7_global_row_first_last": [int(selected.global_row.iloc[0]), int(selected.global_row.iloc[-1])],
                            "g7_source_counts": {k: int(v) for k, v in sorted(selected.source.value_counts().items())},
                            "g7_equals_accepted_g6_selector": True}

    # 2. G7's own load_inputs with every pinned real metadata input
    replay, sample_a, _, _, _ = g7.load_inputs(argparse.Namespace(
        replay_manifest=args.replay_manifest, sample_freeze=args.sample_freeze, provenance=args.provenance,
        collision_ledger=args.collision_ledger, macha_freeze=args.macha_freeze))
    require(sample_a["global_row"].astype(int).tolist() == list(range(25_000)), "load_inputs global_row mismatch")
    replay_addresses = set(replay.molecular_address_index.astype(int))
    out["2_g7_load_inputs"] = {"replay_addresses": len(replay_addresses), "sample_a_rows": int(len(sample_a)),
                               "input_sha256": {k: sha(getattr(args, k)) for k in
                                                ("replay_manifest", "sample_freeze", "provenance",
                                                 "collision_ledger", "macha_freeze")}}

    # 3. producer-code continuity of the exact clean committed tree
    identity = common.code_identity(G6_PATH, G7_PATH)
    g7.require_g6_producer_code_continuity(identity)
    out["3_successor_code_identity"] = identity

    # 4. the accepted G6 predecessor, through G7's own bridge and full prerequisite
    pred = g7.load_accepted_g6_predecessor(Path(args.g6_receipt), Path(args.g6_acceptance),
                                           replay_addresses=replay_addresses, sample_a=sample_a)
    out["4_accepted_g6_predecessor"] = {
        "status": pred["status"], "verified_sha256": pred["g7_verified_g6_execution_sha256"],
        "external_acceptance_sha256": pred["g7_g6_predecessor"]["external_acceptance_sha256"],
        "producer_commit": pred["g7_g6_predecessor"]["implementation_commit_sha"],
        "receipt_flags": {k: pred[k] for k in g7.FALSE_FLAGS}}

    # N1. old authority cannot authorize the successor code (real PR #259 receipts, real code identity)
    require(sha(args.old_owner_decision) == OLD_OWNER_DECISION_SHA, "old owner decision SHA mismatch")
    require(sha(args.old_runtime_authorization) == OLD_RUNTIME_AUTHORIZATION_SHA, "old runtime authorization SHA mismatch")
    n1 = refusal(lambda: common.load_runtime_authorization(
        Path(args.old_runtime_authorization), preflight_path=Path(args.preflight_result),
        mapping_path=Path(args.mapping_receipt), g6_path=G6_PATH, g7_path=G7_PATH,
        replay_manifest_path=Path(args.replay_manifest), owner_decision_path=Path(args.old_owner_decision)))
    require("qualified implementation commit" in n1, f"old authority refused for an unexpected reason: {n1}")
    old_auth = json.loads(Path(args.old_runtime_authorization).read_text(encoding="utf-8"))
    out["N1_old_authority_refused"] = {"refusal": n1,
                                       "old_authorization_binds": {k: old_auth.get(k) for k in
                                                                   ("implementation_commit_sha", "g7_script_sha256")},
                                       "successor_binds": {k: identity[k] for k in
                                                           ("implementation_commit_sha", "g7_script_sha256")}}

    # N2. the old fafd4309 G6 namespace is not the accepted predecessor
    old_ns = Path(args.old_g6_namespace)
    require(sorted(x.name for x in old_ns.iterdir()) == ["G6_EXECUTION_START.json"] and
            sha(old_ns / "G6_EXECUTION_START.json") == OLD_G6_START_MARKER_SHA, "old G6 namespace changed")
    out["N2_old_g6_namespace_refused"] = refusal(lambda: g7.load_accepted_g6_predecessor(
        old_ns / "G6_RECEIPT.json", Path(args.g6_acceptance), replay_addresses=replay_addresses, sample_a=sample_a))

    # N3. the old G7 reproduces the real-run failure on the same real freeze and accepted G6 metadata
    with tempfile.TemporaryDirectory() as tmp:
        for rel in ("scripts/v5/td_relational_value_read_v2_common.py", "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"):
            (Path(tmp) / Path(rel).name).write_bytes(git_blob(OLD_COMMIT, rel))
        old_g7 = load(Path(tmp) / G7_PATH.name, "td_g7_ff4a21f9_old_real_gate")
        require(old_g7.common.canonical_text_sha256(Path(tmp) / G7_PATH.name) == OLD_G7_SHA, "old G7 blob SHA mismatch")
        old_selected = old_g7.select_sample_a(frame)
        meta_raw = (Path(args.g6_receipt).parent / common.G6_META_NAME).read_bytes()
        n3 = refusal(lambda: old_g7.common.validate_g6_meta_artifact(meta_raw, sample_a=old_selected,
                                                                     source_counts=old_g7.SOURCE_COUNTS))
    require("global_row" in n3 and "global_row" not in old_selected.columns, f"old G7 did not reproduce: {n3}")
    out["N3_old_g7_real_failure_reproduced"] = n3

    # N4. the spent ff4a21f9 G7 operational authorization binds the old G7 code
    rev, rel, want = OLD_G7_OPERATIONAL_AUTHORIZATION
    raw = git_blob(rev, rel)
    require(hashlib.sha256(raw).hexdigest() == want, "old G7 operational authorization SHA mismatch")
    op = json.loads(raw.decode("utf-8"))
    require(op.get("implementation_commit_sha") == OLD_COMMIT and op.get("g7_script_sha256") == OLD_G7_SHA,
            "old G7 operational authorization does not bind the old G7")
    require(identity["implementation_commit_sha"] != OLD_COMMIT and identity["g7_script_sha256"] != OLD_G7_SHA,
            "successor identity equals the old G7")
    out["N4_old_g7_operational_authorization_cannot_release_successor"] = {
        "sha256": want, "authorization": op.get("authorization"),
        "binds": {"implementation_commit_sha": OLD_COMMIT, "g7_script_sha256": OLD_G7_SHA}}

    require("h5py" not in sys.modules, "h5py was imported: an H5AD reader was reachable")
    out["no_h5py_imported"] = True
    out["g7_marker_or_receipt_created"] = False
    out["authority_created"] = False
    out["terminal"] = TERMINAL
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
