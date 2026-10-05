#!/usr/bin/env python3
"""Fail-closed consistency check for JEPA's canonical current-authority surface."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CURRENT_DATE = "2026-10-05"
CURRENT_FILES = (
    "START_HERE.md",
    "README.md",
    "docs/agent/CURRENT_AUTHORITY_INDEX.md",
    "docs/agent/CURRENT_SUPERSESSION_MAP.md",
    "docs/agent/memory-os/ACTIVE_STATE.md",
)
POINTER = "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json"
LEGACY_ACTIVE_ALIAS = "docs/agent/ACTIVE_STATE.md"
LEGACY_CHECKPOINT_ALIAS = "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json"
NEXT_ACTION_ALIAS = "docs/agent/memory-os/NEXT_ALLOWED_ACTION.json"
CHAT_BOOTSTRAP = "docs/agent/memory-os/START_EVERY_JEPA_CHAT.txt"
MEMORY_OS = "docs/agent/memory-os/JEPA_PROJECT_MEMORY_OS.md"


def audit_authority_surface(root: Path) -> list[str]:
    root = Path(root)
    failures: list[str] = []

    pointer_path = root / POINTER
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"pointer invalid: {exc}")
        pointer = {}

    if pointer.get("date") != CURRENT_DATE:
        failures.append(f"pointer stale date: {pointer.get('date')!r}")
    if "TARGET_AUTHORITY" not in str(pointer.get("status", "")):
        failures.append("pointer status is not target-authority reset/reconciliation")
    handoff_value = str(pointer.get("handoff_path", pointer.get("handoff", pointer.get("current_handoff", ""))))
    if "20261005_TARGET_AUTHORITY_RESET" not in handoff_value:
        failures.append("pointer handoff is not Oct-5 target-authority reset")

    texts: dict[str, str] = {}
    for rel in CURRENT_FILES:
        path = root / rel
        if not path.exists():
            failures.append(f"missing current file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[rel] = text
        if rel == "README.md":
            if "October 5, 2026" not in text and CURRENT_DATE not in text:
                failures.append(f"{rel} stale date")
        else:
            match = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", text)
            if not match or match.group(1) != CURRENT_DATE:
                failures.append(f"{rel} stale date")

    active_alias = root / LEGACY_ACTIVE_ALIAS
    if not active_alias.exists():
        failures.append(f"missing legacy current-looking alias: {LEGACY_ACTIVE_ALIAS}")
    else:
        active_text = active_alias.read_text(encoding="utf-8")
        if "SUPERSEDED_ALIAS_ROUTER" not in active_text or "docs/agent/memory-os/ACTIVE_STATE.md" not in active_text:
            failures.append(f"legacy current-looking alias is not superseded: {LEGACY_ACTIVE_ALIAS}")

    checkpoint_alias = root / LEGACY_CHECKPOINT_ALIAS
    if not checkpoint_alias.exists():
        failures.append(f"missing legacy current-looking alias: {LEGACY_CHECKPOINT_ALIAS}")
    else:
        try:
            checkpoint = json.loads(checkpoint_alias.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"legacy current-looking alias invalid: {LEGACY_CHECKPOINT_ALIAS}: {exc}")
            checkpoint = {}
        if checkpoint.get("status") != "SUPERSEDED_ALIAS_ROUTER" or checkpoint.get("date") != CURRENT_DATE:
            failures.append(f"legacy current-looking alias is not superseded: {LEGACY_CHECKPOINT_ALIAS}")
        if checkpoint.get("canonical_current_state") != "docs/agent/JEPA_HANDOFF_STATE_20261005_TARGET_AUTHORITY_RESET.json":
            failures.append(f"legacy current-looking alias has wrong canonical route: {LEGACY_CHECKPOINT_ALIAS}")

    next_action_path = root / NEXT_ACTION_ALIAS
    try:
        next_action = json.loads(next_action_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"memory-os bootstrap invalid: {NEXT_ACTION_ALIAS}: {exc}")
        next_action = {}
    if next_action.get("status") != "SUPERSEDED_ALIAS_ROUTER" or next_action.get("date") != CURRENT_DATE:
        failures.append(f"memory-os bootstrap alias is stale: {NEXT_ACTION_ALIAS}")
    if next_action.get("canonical_current_state") != "docs/agent/JEPA_HANDOFF_STATE_20261005_TARGET_AUTHORITY_RESET.json":
        failures.append(f"memory-os bootstrap alias has wrong canonical route: {NEXT_ACTION_ALIAS}")

    bootstrap_path = root / CHAT_BOOTSTRAP
    if not bootstrap_path.exists():
        failures.append(f"memory-os bootstrap missing: {CHAT_BOOTSTRAP}")
    else:
        bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
        if "Date: 2026-10-05" not in bootstrap_text or "CURRENT_BOOTSTRAP_ROUTER" not in bootstrap_text or "START_HERE.md" not in bootstrap_text:
            failures.append(f"memory-os bootstrap is stale: {CHAT_BOOTSTRAP}")

    memory_os_path = root / MEMORY_OS
    if not memory_os_path.exists():
        failures.append(f"memory-os bootstrap missing: {MEMORY_OS}")
    else:
        memory_os_text = memory_os_path.read_text(encoding="utf-8")
        if "Date: 2026-10-05" not in memory_os_text or "CURRENT_BOOTSTRAP_FRAMEWORK" not in memory_os_text or "START_HERE.md" not in memory_os_text:
            failures.append(f"memory-os bootstrap is stale: {MEMORY_OS}")

    joined = "\n".join(texts.values()).lower()
    if any(claim in joined for claim in ("training is authorized", "training authorized", "training = on", "training: on")):
        failures.append("training contradiction: an authority surface authorizes training")

    off_phrases = ("training = off", "training: off", "training remains off", "training and multimodal training are off")
    if texts and not any(any(p in text.lower() for p in off_phrases) for text in texts.values()):
        failures.append("training boundary missing: no current file states training OFF")

    if "500k" not in joined or "not authorized" not in joined:
        failures.append("missing current boundary: 500K")

    target_boundary_phrases = (
        "no qualified production target",
        "no production teacher target is currently qualified",
        "production target winner: **none qualified**",
        "production target winner | **none qualified**",
        "production target winner = none qualified",
    )
    if not any(phrase in joined for phrase in target_boundary_phrases):
        failures.append("missing current boundary: target winner")

    if "160" not in joined or "not biological" not in joined:
        failures.append("missing current boundary: width 160")

    return failures


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(".")
    failures = audit_authority_surface(root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS_AUTHORITY_SURFACE_CONSISTENCY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
