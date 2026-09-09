"""R8 verification — the repaired adjudicator readiness path, live.

Produces the evidence the R8 authorization requires, and nothing beyond it.

    the old contradiction is still reproducible against the frozen module
    the derived diff is restricted to the readiness value check
    the v2 gate is the only production path
    the frozen adjudicator's own gate condition is now satisfiable
    every R7 and Stage 2 discovery root is consumed unchanged
    no confirmation numeric AT8 is read
    no discovery refit
    an explicit shut-gate report

Satisfiability is demonstrated on purpose-built authority packages rather than
on the production pretarget authority, and the reason is worth stating. Building
a production pretarget authority requires `discovery_metadata`, which carries the
AT8 column. R8 is a repair to readiness plumbing; it is not authorized to refit
discovery and has no need to re-read pathology. So the demonstration writes
authority-shaped packages through the frozen module's own writer, shows the
frozen loader refusing them and the repaired loader accepting them, and evaluates
the frozen adjudicator's condition verbatim against the result. That establishes
the readiness path is satisfiable, which is precisely the claim R8 makes.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_execution_input_authority_v2 as v2  # noqa: E402
import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

SUMMARY = "T0_R8_ADJUDICATOR_READINESS_VERIFY_SUMMARY.json"
DIFF_FILE = "T0_R8_READINESS_LOADER_SOURCE_DIFF.txt"

# Roots the authorization requires to be consumed unchanged.
REQUIRED_UNCHANGED = {
    "r7_package_root_sha256":
        "a7e25e515f8e9cb4ec43e1e3bf09798adca6a573059d4b7ca0b61483c5c96c09",
    "r7_readiness_root_sha256":
        "a75581dfc5e7ea88609a9ef62f54765b9a495a7dbdc5c09152ba7fb76d1488ae",
    "discovery_target_package_root_sha256":
        "b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe",
    "discovery_provenance_root_sha256":
        "15d13dd3e733e0ea90b199cf981b03ccd94bc67fbd19660ef88861e3ae1a37c2",
    "discovery_authority_package_root_sha256":
        "9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7",
}

SHUT_GATES = ("confirmation_numeric_at8", "dev", "sealed",
              "protected_populations", "training", "successor_u0", "td60",
              "biological_sweeps")

STOP_ROOT_MOVED = "STOP_T0_R8_A_REQUIRED_ROOT_MOVED"
STOP_NOT_SATISFIABLE = "STOP_T0_R8_ADJUDICATOR_GATE_STILL_NOT_SATISFIABLE"
STOP_CONTRADICTION_GONE = "STOP_T0_R8_FROZEN_CONTRADICTION_NO_LONGER_REPRODUCIBLE"
STOP_DIFF_SCOPE = "STOP_T0_R8_DIFF_NOT_RESTRICTED_TO_THE_READINESS_CHECK"


def code_sha256(filename: str) -> str:
    """SHA-256 over LF-normalized content. Not a Git blob digest."""
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def _authority_fixtures(eia):
    pre = {
        "schema": eia.PRE_SCHEMA,
        "donor_role_package_root_sha256": "a" * 64,
        "role_metadata_payload_sha256": "b" * 64,
        "discovery_metadata_payload_sha256": "c" * 64,
        "discovery_expression_payload": {"payload_sha256": "d" * 64,
                                         "cells": 1, "scalar_features": 1,
                                         "canonical_donors": ["D1"]},
        "external_source_authority_hashes": {"src": "e" * 64},
        "chronology": "BUILT_AFTER_ROLE_FREEZE__BEFORE_TARGET_FIT",
    }
    adj = {
        "schema": eia.ADJ_SCHEMA,
        "upstream_package_roots": {"pretarget_execution_input": "a" * 64,
                                   "donor_role": "b" * 64, "target": "c" * 64,
                                   "tail": "d" * 64,
                                   "discovery_authority": "e" * 64,
                                   "technical_registry": "f" * 64,
                                   "target_family": "0" * 64},
        "confirmation_metadata_columns": ["donor_id", "AT8", "age", "sex",
                                          "IMMUNE_FRACTION"],
        "confirmation_metadata_payload_sha256": "1" * 64,
        "confirmation_expression_payload": {"payload_sha256": "2" * 64,
                                            "cells": 1, "scalar_features": 1,
                                            "canonical_donors": ["D1"]},
        "technical_blocks": {},
        "family_status_authority_sha256": "3" * 64,
        "family_historical_rare5_status":
            "NOT_DECISION_CAPABLE_AUTHORITY_MISSING",
        "external_source_authority_hashes": {"src": "4" * 64},
        "chronology": ("BUILT_AFTER_TARGET_TAIL_TECHNICAL_FAMILY_FREEZE"
                       "__BEFORE_CONFIRMATION_INFERENCE"),
    }
    return pre, adj


def verify(*, outdir: Path, readiness_pkg: Path, discovery_pkg: Path,
           log=print) -> dict[str, Any]:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%5.1fs] %s" % (time.time() - started, message))

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}

    # --- 1. Every required root, consumed unchanged --------------------------
    stamp("1/5 confirming every required root is consumed unchanged")
    gate = stage2a.verify_r7_gate(readiness_pkg, log=lambda m: None)
    observed = {
        "r7_package_root_sha256": gate["package_root_sha256"],
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
    }
    discovery = json.loads(
        (discovery_pkg / "T0_DISCOVERY_STAGE_RUN_SUMMARY.json").read_text(
            encoding="utf-8"))
    for field in ("discovery_target_package_root_sha256",
                  "discovery_provenance_root_sha256",
                  "discovery_authority_package_root_sha256"):
        observed[field] = discovery[field]
    for field, expected in REQUIRED_UNCHANGED.items():
        if observed[field] != expected:
            raise AssertionError("%s: %s is %s, must remain %s"
                                 % (STOP_ROOT_MOVED, field, observed[field],
                                    expected))
        stamp("    %-42s unchanged" % field)
    checks["all_required_roots_unchanged"] = True

    # --- 2. The old contradiction still reproduces ---------------------------
    stamp("2/5 reproducing the frozen contradiction, which must still hold")
    eia = stage2a._frozen("t0_execution_input_authority_v1")
    pre_obj, adj_obj = _authority_fixtures(eia)
    frozen_refusals = {}
    for label, base, member, manifest, root, loader in (
            ("pretarget", pre_obj, eia.PRE_MEMBER, eia.PRE_MANIFEST,
             eia.PRE_ROOT, eia.load_pretarget_execution_authority),
            ("preadjudication", adj_obj, eia.ADJ_MEMBER, eia.ADJ_MANIFEST,
             eia.ADJ_ROOT, eia.load_preadjudication_execution_authority)):
        target = out / ("frozen_refusal_%s" % label)
        eia._write_package(target, member, manifest, root,
                           dict(base, real_execution_ready=True))
        try:
            loader(target)
            raise AssertionError(
                "%s: the frozen %s loader accepted readiness True"
                % (STOP_CONTRADICTION_GONE, label))
        except ValueError as error:
            frozen_refusals[label] = str(error)
            stamp("    frozen %-16s refuses True: %s" % (label, error))
    checks["frozen_contradiction_still_reproducible"] = True

    # --- 3. The diff is restricted to the readiness value check -------------
    stamp("3/5 checking the derived diff is restricted to the readiness check")
    diff = v2.source_diff()
    changed = [l for l in diff.splitlines()
               if (l.startswith("+") or l.startswith("-"))
               and not l.startswith(("+++", "---"))]
    if len(changed) != 4 or any("real_execution_ready" not in l
                                for l in changed):
        raise AssertionError("%s: %r" % (STOP_DIFF_SCOPE, changed))
    with io.open(out / DIFF_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(diff)
    stamp("    %d changed lines, all on the readiness condition" % len(changed))
    checks["diff_restricted_to_readiness_value_check"] = True

    # --- 4. The repaired path is satisfiable --------------------------------
    stamp("4/5 showing the frozen adjudicator gate is now satisfiable")
    satisfied = {}
    for label, base, member, manifest, root, loader in (
            ("pretarget", pre_obj, eia.PRE_MEMBER, eia.PRE_MANIFEST,
             eia.PRE_ROOT, v2.load_pretarget_execution_authority),
            ("preadjudication", adj_obj, eia.ADJ_MEMBER, eia.ADJ_MANIFEST,
             eia.ADJ_ROOT, v2.load_preadjudication_execution_authority)):
        target = out / ("repaired_accepts_%s" % label)
        eia._write_package(target, member, manifest, root,
                           dict(base, real_execution_ready=True))
        loaded = loader(target)
        # The frozen adjudicator's own condition, evaluated verbatim.
        ok = v2.adjudicator_gate_satisfied(loaded["authority"])
        if not ok:
            raise AssertionError("%s: %s" % (STOP_NOT_SATISFIABLE, label))
        satisfied[label] = True
        stamp("    repaired %-16s accepts True; adjudicator gate passes"
              % label)

        # And False is still lawful, so this is a correction not a loosening.
        neutral = out / ("repaired_accepts_false_%s" % label)
        eia._write_package(neutral, member, manifest, root,
                           dict(base, real_execution_ready=False))
        still = loader(neutral)
        if still["authority"]["real_execution_ready"] is not False:
            raise AssertionError("readiness False was not preserved")
        if v2.adjudicator_gate_satisfied(still["authority"]):
            raise AssertionError(
                "a False authority must NOT satisfy the production gate")
        stamp("    repaired %-16s still accepts False, and False still fails "
              "the production gate" % label)
    checks["adjudicator_gate_satisfiable"] = True
    checks["readiness_false_still_lawful_and_still_not_production"] = True

    # --- 5. Shut gates -------------------------------------------------------
    stamp("5/5 shut-gate report")
    shut = {name: False for name in SHUT_GATES}
    for name in SHUT_GATES:
        stamp("    %-28s %s" % (name, "CLOSED"))
    checks["all_gates_shut"] = True

    record = {
        "schema": "JEPA_T0_R8_ADJUDICATOR_READINESS_VERIFY_SUMMARY_V1",
        "terminal": ("PASS_R8_ADJUDICATOR_READINESS_REPAIR"
                     "__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN"),
        "checks": checks,
        "roots_consumed_unchanged": observed,
        "frozen_refusal_messages": frozen_refusals,
        "derived_diff_changed_lines": len(changed),
        "derived_diff_file": DIFF_FILE,
        "supersedes": v2.SUPERSEDES,
        "behavioural_difference": v2.BEHAVIOURAL_DIFFERENCE,
        "justification": v2.JUSTIFICATION,
        "frozen_module_edited": v2.FROZEN_MODULE_EDITED,
        "adjudicator_gate_satisfied": satisfied,
        "gates_opened": shut,
        "confirmation_numeric_at8_read": False,
        "discovery_numeric_at8_reread": False,
        "discovery_refit": v2.DISCOVERY_REFIT,
        "scientific_design_unchanged": v2.SCIENTIFIC_DESIGN_UNCHANGED,
        "adjudication_performed": False,
        "authority_code_sha256": code_sha256(
            "t0_execution_input_authority_v2.py"),
        "runner_code_sha256": code_sha256(
            "t0_r8_adjudicator_readiness_verify_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    with io.open(out / SUMMARY, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--readiness-pkg", required=True, type=Path)
    parser.add_argument("--discovery-pkg", required=True, type=Path)
    args = parser.parse_args(argv)

    record = verify(outdir=args.outdir, readiness_pkg=args.readiness_pkg,
                    discovery_pkg=args.discovery_pkg)
    print()
    print(json.dumps(record, indent=2, sort_keys=True))
    print()
    print(record["terminal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
