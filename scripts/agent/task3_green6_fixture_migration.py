#!/usr/bin/env python3
"""Historical one-shot migration of pre-RED6 Task 3 test units.

RED6 made producer/executor actor identities mandatory. Older hostile fixtures that
construct RegistryUnit directly must now bind actor identities too. This script only
migrates tests; it does not weaken the production contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "tests/v5/td_unified"

ACTOR_FIELDS = (
    'producer_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_PRODUCER","actor_id":f"producer:{unit_id}"}),\n'
    '        executor_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_EXECUTOR","actor_id":f"executor:{unit_id}"}),\n        '
)


def migrate(path: Path) -> bool:
    text = path.read_text()
    if "RegistryUnit(" not in text or "producer_actor_identity=" in text:
        return False
    # All historical direct-unit helpers put executor_code_sha before producer_policy_sha.
    pattern = re.compile(r'(executor_code_sha\s*=\s*[^,\n]+,\s*\n?\s*)producer_policy_sha=')
    new, n = pattern.subn(r'\1' + ACTOR_FIELDS + 'producer_policy_sha=', text)
    if n == 0:
        # Handle compact single-line constructor fragments.
        pattern2 = re.compile(r'(executor_code_sha\s*=\s*[^,]+,\s*)producer_policy_sha=')
        new, n = pattern2.subn(r'\1' + ACTOR_FIELDS + 'producer_policy_sha=', text)
    if n == 0:
        raise RuntimeError(f"could not migrate RegistryUnit helper in {path}")
    path.write_text(new)
    return True


if __name__ == "__main__":
    changed = []
    for path in sorted(TEST_DIR.glob("test_registry_v1*.py")):
        if path.name == "test_registry_v1_hostile_cycle6.py":
            continue
        if migrate(path):
            changed.append(str(path.relative_to(ROOT)))
    print("migrated", len(changed), "files")
    for item in changed:
        print(item)
