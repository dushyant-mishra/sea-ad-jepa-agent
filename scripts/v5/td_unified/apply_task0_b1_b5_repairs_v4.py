from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / "scripts" / "v5" / "td_unified" / "apply_task0_b1_b5_repairs_v3.py"), run_name="__main__")

path = ROOT / "results" / "target_discovery" / "unified_qualification_v1" / "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"
payload = json.loads(path.read_text(encoding="utf-8"))
entry = next(x for x in payload["decompositions"] if x["parent_artifact_id"] == "PR356_SYNTH_PLAN")
paths = {
    "OLD_TASK1_IMPLEMENTATION": "scripts/production_synthetic/canonical_v1.py",
    "OLD_TASK2_IMPLEMENTATION": "scripts/production_synthetic/custody_v1.py",
    "OLD_TASK3_REQUIREMENTS": "docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md",
    "OLD_TASK4_REQUIREMENTS": "docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md",
    "OLD_TASKS5_12": "docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md",
}
for child in entry["children"]:
    child["artifact_path"] = paths[child["child_artifact_id"]]
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
