"""Non-authorizing TD→downstream readiness firewall.

This module exists before Unified Task 4 only to audit staging.  It cannot
accept Task 3, issue a Target Qualification Bundle, certify downstream
consumption, open Stage 4, or authorize training.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path


class DownstreamPreflightError(ValueError):
    pass


GLOBAL_STOP_STATE = (
    "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
)

ARCHITECTURE_V1_1_COMMIT = "3064ca545f0c94859ea989cd49a04fcbd5b9a303"
ARCHITECTURE_V1_1_PATH = (
    "docs/superpowers/specs/"
    "2026-10-14-unified-td-qualification-downstream-custody-architecture-v1-1-hostile-review-amendment.md"
)
IMPLEMENTATION_PLAN_COMMIT = "5b6bf07e7d8b69b286ea430b09765a5ee4743325"
IMPLEMENTATION_PLAN_PATH = (
    "docs/superpowers/plans/"
    "2026-10-14-unified-td-qualification-downstream-custody-v1-implementation.md"
)

LEGACY_POST_TD_HARNESS = "scripts/v5/jepa_post_td_harness_contract_v1.py"
TASK4_PRODUCTION_PATHS = (
    "scripts/v5/td_unified/target_bundle_v1.py",
    "scripts/v5/td_unified/downstream_contract_v1.py",
    "schemas/target_discovery/unified_v1/target_qualification_bundle_v1.json",
    "schemas/target_discovery/unified_v1/downstream_certification_contract_v1.json",
)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _git_object_exists(root: Path, commit: str, path: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def _legacy_authority(root: Path) -> dict[str, object]:
    path = root / LEGACY_POST_TD_HARNESS
    if not path.is_file():
        raise DownstreamPreflightError("legacy post-TD harness is missing; custody cannot be classified")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    authority = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == "_AUTHORITY_OFF" for t in node.targets):
            authority = ast.literal_eval(node.value)
            break
    if not isinstance(authority, dict):
        raise DownstreamPreflightError("legacy post-TD harness lacks explicit _AUTHORITY_OFF custody")
    required_off = {
        "target_selection_authorized",
        "representation_selection_authorized",
        "td60_authorized",
        "stage4_authorized",
        "training_authorized",
    }
    authority_all_false = required_off <= set(authority) and all(authority[key] is False for key in required_off)
    if not authority_all_false:
        raise DownstreamPreflightError("legacy post-TD harness is not explicitly authority-off")

    unified_dir = root / "scripts/v5/td_unified"
    legacy_token = "jepa_post_td_harness_contract_v1"
    imported_by_unified = False
    if unified_dir.is_dir():
        for candidate in unified_dir.glob("*.py"):
            if candidate.name == Path(__file__).name:
                continue
            if legacy_token in candidate.read_text(encoding="utf-8"):
                imported_by_unified = True
                break

    uses_registry = "TDQualificationRegistry" in source or "td_unified.registry_v1" in source or "registry_v1" in source
    return {
        "path": LEGACY_POST_TD_HARNESS,
        "classification": "LEGACY_NON_AUTHORIZING_MECHANICS_ONLY",
        "authority_all_false": authority_all_false,
        "uses_unified_registry_evidence": uses_registry,
        "imported_by_unified_package": imported_by_unified,
    }


def audit_downstream_preflight(
    root: str | Path,
    *,
    task3_candidate_sha: str,
    claimed_task3_accepted: bool = False,
    verify_git_custody: bool = True,
) -> dict[str, object]:
    """Audit staging only; never convert caller assertions into authority."""
    repo_root = Path(root).resolve()
    if not _HEX40.fullmatch(task3_candidate_sha):
        raise DownstreamPreflightError("task3_candidate_sha must be exact lowercase 40-hex")
    if claimed_task3_accepted:
        raise DownstreamPreflightError(
            "caller assertion of Task 3 acceptance is not authority; an independently frozen acceptance object is required"
        )

    present = [path for path in TASK4_PRODUCTION_PATHS if (repo_root / path).exists()]
    if present:
        raise DownstreamPreflightError(
            "premature Task 4 production surface exists before independent Task 3 acceptance: " + ", ".join(present)
        )

    if verify_git_custody:
        architecture_ok = _git_object_exists(repo_root, ARCHITECTURE_V1_1_COMMIT, ARCHITECTURE_V1_1_PATH)
        plan_ok = _git_object_exists(repo_root, IMPLEMENTATION_PLAN_COMMIT, IMPLEMENTATION_PLAN_PATH)
        if not architecture_ok or not plan_ok:
            raise DownstreamPreflightError("pinned downstream architecture/implementation-plan custody is not reachable")
    else:
        architecture_ok = False
        plan_ok = False

    legacy = _legacy_authority(repo_root)
    if legacy["imported_by_unified_package"]:
        raise DownstreamPreflightError("unified package imports the legacy post-TD harness")

    return {
        "schema": "JEPA_UNIFIED_DOWNSTREAM_PREFLIGHT_V1",
        "status": "DOWNSTREAM_STAGED__TASK3_ACCEPTANCE_REQUIRED__TASK4_BLOCKED",
        "task3_candidate_sha": task3_candidate_sha,
        "task3_independent_acceptance_verified": False,
        "task4_authorized": False,
        "stage4_authorized": False,
        "real_training_authorized": False,
        "global_authority": GLOBAL_STOP_STATE,
        "design_custody": {
            "architecture_v1_1_commit": ARCHITECTURE_V1_1_COMMIT,
            "architecture_v1_1_path": ARCHITECTURE_V1_1_PATH,
            "architecture_v1_1_reachable": architecture_ok,
            "implementation_plan_commit": IMPLEMENTATION_PLAN_COMMIT,
            "implementation_plan_path": IMPLEMENTATION_PLAN_PATH,
            "implementation_plan_reachable": plan_ok,
        },
        "task4_production_paths_present": present,
        "legacy_post_td_harness": legacy,
        "next_authority_gate": "INDEPENDENT_TASK3_ACCEPTANCE_AND_EXACT_FREEZE",
        "r4_cross_process_custody_closed": False,
    }
