"""Outcome-blind static evidence-ladder contract for real-TD G7.

This module freezes only the lawful nested evidence-rights ladder. It does not
read biological candidate outcomes, compute G7, or authorize real TD.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


class EvidenceLadderError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1"
OPERATOR_FAMILY = "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION"
_ALLOWED_TOP = {"schema", "frozen", "candidate_id", "full_evidence_rights", "levels"}
_ALLOWED_LEVEL = {"level_id", "operator_family", "evidence_rights"}
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _nonempty_string(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise EvidenceLadderError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _rights(value, label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise EvidenceLadderError(f"{label} must be a nonempty sequence of nonempty strings")
    out = []
    for item in value:
        if not isinstance(item, str) or not item or item != item.strip() or "\0" in item:
            raise EvidenceLadderError(f"{label} values must be nonempty strings")
        out.append(item)
    if len(set(out)) != len(out):
        raise EvidenceLadderError(f"{label} values must be unique")
    return tuple(out)


def _validate_level(raw: Mapping, index: int) -> dict:
    if not isinstance(raw, Mapping) or set(raw) != _ALLOWED_LEVEL:
        raise EvidenceLadderError(f"level {index} must contain exact level fields")
    level_id = _nonempty_string(raw["level_id"], f"levels[{index}].level_id")
    operator = _nonempty_string(raw["operator_family"], f"levels[{index}].operator_family")
    if operator != OPERATOR_FAMILY:
        if "COUNT" in operator.upper() or "THIN" in operator.upper() or "DEPTH" in operator.upper():
            raise EvidenceLadderError("count thinning is forbidden in G7 biological-evidence convergence")
        raise EvidenceLadderError("G7 requires BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION operator family")
    rights = _rights(raw["evidence_rights"], f"levels[{index}].evidence_rights")
    return {"level_id": level_id, "operator_family": operator, "evidence_rights": rights}


def derive_evidence_ladder(manifest: Mapping) -> dict:
    if not isinstance(manifest, Mapping) or set(manifest) != _ALLOWED_TOP:
        raise EvidenceLadderError("evidence ladder manifest fields differ from frozen schema")
    if manifest.get("schema") != SCHEMA:
        raise EvidenceLadderError("evidence ladder schema mismatch")
    if manifest.get("frozen") is not True:
        raise EvidenceLadderError("evidence ladder manifest must be explicitly frozen")

    candidate_id = _nonempty_string(manifest["candidate_id"], "candidate_id")
    full_rights = _rights(manifest["full_evidence_rights"], "full_evidence_rights")
    raw_levels = manifest["levels"]
    if isinstance(raw_levels, (str, bytes)) or not isinstance(raw_levels, Sequence) or not raw_levels:
        raise EvidenceLadderError("levels must be a nonempty sequence")

    levels = [_validate_level(raw, i) for i, raw in enumerate(raw_levels)]
    level_ids = [level["level_id"] for level in levels]
    if len(set(level_ids)) != len(level_ids):
        raise EvidenceLadderError("level_id values must be unique")

    for previous, current in zip(levels, levels[1:]):
        previous_set = set(previous["evidence_rights"])
        current_set = set(current["evidence_rights"])
        if not previous_set < current_set:
            raise EvidenceLadderError("evidence rights must form a strictly nested ladder")

    if tuple(levels[-1]["evidence_rights"]) != tuple(full_rights):
        raise EvidenceLadderError("terminal level must equal declared full evidence rights exactly")

    base = {
        "schema": "JEPA_TD_REAL_EVIDENCE_LADDER_CONTRACT_V1",
        "candidate_id": candidate_id,
        "level_ids": level_ids,
        "levels": [
            {
                "level_id": level["level_id"],
                "operator_family": level["operator_family"],
                "evidence_rights": list(level["evidence_rights"]),
            }
            for level in levels
        ],
        "full_evidence_rights": list(full_rights),
        "strict_adjacent_monotonicity_required": False,
        "count_thinning_authorized": False,
        "claim_boundary": "STATIC_EVIDENCE_LADDER_ONLY__NO_G7_BIOLOGICAL_OUTCOME",
        "authority": dict(NO_AUTHORITY),
    }

    if len(levels) < 3:
        return {
            **base,
            "status": "NOT_ESTIMABLE_FEWER_THAN_THREE_LAWFUL_LEVELS",
            "terminal_contrast": None,
        }

    return {
        **base,
        "status": "EVIDENCE_LADDER_FROZEN",
        "terminal_contrast": {
            "reference_level": levels[-2]["level_id"],
            "full_level": levels[-1]["level_id"],
        },
    }
