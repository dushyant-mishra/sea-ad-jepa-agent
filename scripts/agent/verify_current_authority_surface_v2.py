"""Validate the November-2026 current main startup, leaving the Oct-5 V1 tests historical.

This is a navigation/custody integrity guard, NOT a source-issuer, model
security or biological qualification validator. Future dates may advance only
if main routing and audit/handoff identity advance together.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import sys

ROUTER = "docs/agent/JEPA_MAIN_CURRENT_EXECUTION_MAP_20261102.md"
POINTER = "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json"
TERMINAL = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
CUTOFF = date(2026, 11, 2)
FRONT = (
    "START_HERE.md", "README.md", "docs/agent/CURRENT_AUTHORITY_INDEX.md",
    "docs/agent/CURRENT_SUPERSESSION_MAP.md", "docs/agent/memory-os/ACTIVE_STATE.md",
)


def check(root: Path) -> list[str]:
    root = Path(root)
    failures: list[str] = []
    try:
        p = json.loads((root / POINTER).read_text(encoding="utf8"))
    except (OSError, ValueError) as exc:
        return ["cannot read current pointer: " + type(exc).__name__]
    try:
        stamp = date.fromisoformat(p["date"])
    except (KeyError, TypeError, ValueError):
        stamp = date.min
    if stamp < CUTOFF:
        failures.append("current pointer backdated before November 2")
    if p.get("status") != TERMINAL:
        failures.append("current pointer must retain complete fail-closed terminal")
    if p.get("current_task_status") != "REPAIRED_V2C_D1_CONTAINER_AUTHOR_CI_GREEN__INDEPENDENT_MACHA_RECHECK_PENDING":
        failures.append("no current qualified repair/review state")
    if p.get("canonical_main_execution_map") != ROUTER:
        failures.append("main router drift")
    for fld, pr in (("canonical_audit", 322), ("active_handoff", 460)):
        ref = p.get(fld)
        if not isinstance(ref, dict) or type(ref.get("pr")) is not int or ref["pr"] != pr:
            failures.append("invalid " + fld + " PR")
            continue
        sha = ref.get("head_at_routing")
        if type(sha) is not str or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            failures.append("invalid " + fld + " exact-head field")
    impl = p.get("current_non_authorizing_implementation")
    if not isinstance(impl, dict):
        failures.append("current fixture pointer absent")
    else:
        if (impl.get("independent_recheck") != "PENDING" or
                impl.get("source_issuer") != "NOT_PROVISIONED" or
                impl.get("real_training_authorized") is not False):
            failures.append("fixture authority promoted without independently accepted change")
        for k in ("student_verifier_blob", "d1_producer_blob"):
            if not isinstance(impl.get(k), str) or re.fullmatch(r"[0-9a-f]{40}", impl[k]) is None:
                failures.append("fixture source blob identity malformed " + k)
    history = p.get("historical_20261006_router")
    if not isinstance(history, dict) or history.get("date") != "2026-10-06":
        failures.append("old October router not preserved as history")
    gover = p.get("governance")
    if not isinstance(gover, dict) or gover.get("training") != "OFF" or gover.get("stage4") != "NOT_AUTHORIZED":
        failures.append("main governance safety flags changed")
    try:
        m = (root / ROUTER).read_text(encoding="utf8")
    except OSError:
        m = ""
        failures.append("main execution map missing")
    for token in ("#322", "#460", "#514", "#515", "#521", "NOT_AUTHORIZED", "Macha", "source", "main"):
        if token not in m:
            failures.append("main router missing " + token)
    for rel in FRONT:
        try:
            text = (root / rel).read_text(encoding="utf8")[:1700]
        except OSError:
            failures.append("missing current startup file " + rel)
            continue
        if rel != "README.md" and not any(s in text for s in ("November 2, 2026", "November 2 2026", "November 2, 2026".lower())):
            failures.append("not current " + rel)
        if rel == "README.md" and "November 2, 2026" not in text:
            failures.append("README current date missing")
        if rel != "README.md" and ("20261005" in text or "October 5" in text) and "historical" not in text.lower():
            failures.append("stale startup claim " + rel)
        if rel == "START_HERE.md" and ("main execution map" not in text.lower() or "training" not in text.lower()):
            failures.append("START_HERE canonical guidance missing")
    # All canonical landing paths exist on the current checkout.
    if not (root / "scripts/v5/td_unified/observation_v2c_standalone_student_gate_v1.py").is_file():
        failures.append("main V2C fixture missing")
    if not (root / "deployment/student_v2c/Dockerfile.v1").is_file():
        failures.append("main isolated student fixture missing")
    return failures


if __name__ == "__main__":
    errs = check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("."))
    for err in errs:
        print("REFUSE_MAIN_CURRENT_ROUTE:", err)
    if errs:
        sys.exit(1)
    print("MAIN_CURRENT_ROUTE_CUSTODY_PASS__NO_SCIENTIFIC_OR_SECURITY_AUTHORITY")
