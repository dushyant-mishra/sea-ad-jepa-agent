"""TD60/V5 checkpoint *readiness* preflight; never an execution authority.

The September TD60 u40 clause is historical and remains unchanged. V5 Q40 is
mechanical qualification, not a biological-learning exposure milestone. This
source-only checker reads the unfrozen V5 authority candidate and reports why
it cannot be used to start the 48-case TD60 learned-teacher evaluation.

Do not use this script to choose a new milestone, issue a checkpoint, validate
checkpoint authenticity, open outcomes or authorize any optimizer step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "TD60_V5_CHECKPOINT_READINESS_PREFLIGHT_V1"
V5_SCHEMA = "TEACHER_STUDENT_V5_DATA_FIRST_AUTHORITY_CANDIDATE_V2"
STOP = "HOLD_NO_LAWFUL_V5_BIOLOGICAL_CHECKPOINT__TD60_NOT_AUTHORIZED"
UNAUTHORIZED = {
    "training_authorized": False,
    "execution_authorized": False,
    "successor_u0_materialization_authorized": False,
    "td60_execution_authorized": False,
}
NEEDED = (
    ("proposal_policy_frozen", True),
    ("evidence_schedule_frozen", True),
    ("production_compute_kernel_frozen", True),
    ("production_training_presentations", "POSITIVE_INTEGER"),
    ("production_ema_half_life_presentations", "POSITIVE_INTEGER"),
)


def assess_v5_candidate(payload: Any, *, source_sha256: str) -> dict[str, Any]:
    """Assess source-candidate JSON, never a self-declared biological PASS token.

    The only output status is HOLD: a self-supplied manifest can describe a
    candidate, but cannot authenticate an independent exposure/teacher issuer.
    """
    if type(payload) is not dict or payload.get("schema") != V5_SCHEMA:
        raise ValueError("refuse missing or unknown V5 source-candidate schema")
    if type(source_sha256) is not str or len(source_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_sha256):
        raise ValueError("source SHA-256 must be exact 64-character lowercase hex")
    for field, val in UNAUTHORIZED.items():
        if payload.get(field) is not val:
            raise ValueError(f"source candidate unexpectedly claims authority: {field}")
    blockers = ["V5_Q40_IS_MECHANICS_ONLY__NOT_TD60_LEARNED_BIOLOGY"]
    if payload.get("scientific_target_frozen") is not True:
        blockers.append("NO_FROZEN_SCIENTIFIC_TARGET")
    for field, required in NEEDED:
        val = payload.get(field)
        ok = val is True if required is True else type(val) is int and val > 0
        if not ok:
            blockers.append("UNFROZEN_" + field.upper())
    blockers.append("NO_INDEPENDENTLY_AUTHENTICATED_V5_EXPOSURE_CHECKPOINT_OR_TD60_RELEASE")
    return {
        "schema": SCHEMA,
        "status": STOP,
        "source_candidate_sha256": source_sha256,
        "source_schema": V5_SCHEMA,
        "td60_evaluable_cases_if_separately_authorized": 48,
        "td60_frozen_design_preserved": True,
        "checkpoint_selected": None,
        "checkpoint_bytes_opened": False,
        "teacher_or_student_ran": False,
        "biological_outcomes_opened": False,
        "external_issuer_authenticated": False,
        "unresolved": blockers,
        "authority": {
            "real_training": False,
            "td60_execution": False,
            "representation_selection": False,
            "target_selection": False,
            "stage4": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-dir", type=Path, default=Path("."))
    args = ap.parse_args()
    source = args.project_dir / "docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_AUTHORITY_CANDIDATE.json"
    raw = source.read_bytes()
    result = assess_v5_candidate(json.loads(raw), source_sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
