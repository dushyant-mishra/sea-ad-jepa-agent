#!/usr/bin/env python3
"""Read-only V29 exact-class compatibility audit of V27 six OWN-schema candidates.

This is deliberately NOT authority issuance: a matching Python class cannot
authenticate parent bytes, a separate training contract, or executed science.
Never auto-upcast V3 evidence to the V1 current closure merely to make tests green.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ROOTS = (
    "representation_authority_sha256",
    "support_estimability_authority_sha256",
    "canonical_address_registry_authority_sha256",
    "base_training_estimand_sha256",
    "masking_rng_replay_authority_sha256",
    "masking_qualification_parameters_authority_sha256",
)
PARAMS = {
    "representation_authority_sha256": "representation",
    "support_estimability_authority_sha256": "support_estimability",
    "canonical_address_registry_authority_sha256": "canonical_address_registry",
    "base_training_estimand_sha256": "base_training_estimand",
    "masking_rng_replay_authority_sha256": "masking_rng_replay",
    "masking_qualification_parameters_authority_sha256": "masking_qualification_parameters",
}
KNOWN_CLASS_CONFLICTS = {
    "masking_rng_replay_authority_sha256": ("MaskingRngReplayAuthorityV3", "MaskingRngReplayAuthorityV1"),
    "masking_qualification_parameters_authority_sha256": ("MaskingQualificationParametersAuthorityV3", "MaskingQualificationParametersAuthorityV1"),
}
RAW_ROLE_ARGUMENTS = ("full104_substrate_sha256", "observation_gradient_firewall_authority_sha256")
LEDGER = "docs/agent/JEPA_V27_33_ROOT_VALIDATION_LEDGER_20260926.json"
VALIDATOR = "scripts/v5/v27_six_candidate_authority_audit_v1.py"
CLOSURE = "src/sea_ad_jepa/v5/current_authority_closure_v2.py"
ROOT_VOCAB = "src/sea_ad_jepa/v5/current_authority_roots_v2.py"


def _imports(tree: ast.AST) -> dict[str, str]:
    result = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.ImportFrom) and node.module and
                (node.level == 1 or node.module.startswith('sea_ad_jepa.v5.'))):
            for item in node.names:
                result[item.asname or item.name] = node.module + "." + item.name
    return result


def _candidate_classes(source: str) -> dict[str, tuple[str, str, str]]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CANDIDATES" for t in node.targets):
            if not isinstance(node.value, ast.Dict):
                raise ValueError("STOP_NON_LITERAL_V27_CANDIDATES")
            result = {}
            for key, val in zip(node.value.keys, node.value.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    raise ValueError("STOP_DYNAMIC_CANDIDATE_ROOT")
                if not isinstance(val, ast.Tuple) or len(val.elts) != 3:
                    raise ValueError("STOP_CANDIDATE_TUPLE_SHAPE")
                path, schema, cls = val.elts
                if not (isinstance(path, ast.Constant) and isinstance(schema, ast.Constant) and isinstance(cls, ast.Name)):
                    raise ValueError("STOP_DYNAMIC_CANDIDATE_BINDING")
                result[key.value] = (path.value, schema.value, cls.id)
            if set(result) != set(ROOTS):
                raise ValueError("STOP_SIX_ROOT_ROLE_INVENTORY_DRIFT")
            imports = _imports(tree)
            for root, (_, _, cls) in result.items():
                if cls not in imports:
                    raise ValueError("STOP_CANDIDATE_CLASS_IMPORT_MISSING_" + root)
            return result
    raise ValueError("STOP_V27_CANDIDATES_MISSING")


def _closure_types(source: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    tree = ast.parse(source)
    imported = _imports(tree)
    fn = next((x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "validate_current_v5_authority_closure_v2"), None)
    if fn is None:
        raise ValueError("STOP_CURRENT_CLOSURE_MISSING")
    ann = {}
    for arg in fn.args.kwonlyargs:
        ann[arg.arg] = arg.annotation.id if isinstance(arg.annotation, ast.Name) else ast.unparse(arg.annotation)
    for raw in RAW_ROLE_ARGUMENTS:
        if ann.get(raw) != "str":
            raise ValueError("STOP_RAW_SHA_ROLE_CHANGED_" + raw)
    typed = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "typed" for t in node.targets):
            if not isinstance(node.value, ast.Tuple):
                raise ValueError("STOP_TYPED_CLOSURE_TABLE_CHANGED")
            for entry in node.value.elts:
                if isinstance(entry, ast.Tuple) and len(entry.elts) >= 2:
                    arg, cls = entry.elts[:2]
                    if isinstance(arg, ast.Name) and isinstance(cls, ast.Name):
                        typed[arg.id] = cls.id
    if not typed:
        raise ValueError("STOP_CLOSURE_TYPED_GUARD_NOT_RECOVERED")
    return ann, typed, imported


def _root_names(source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2" for t in node.targets):
            roots = ast.literal_eval(node.value)
            if not isinstance(roots, tuple):
                raise ValueError("STOP_ROOT_VOCABULARY_CHANGED")
            return roots, roots + ("preexecution_authority_sha256",)
    raise ValueError("STOP_ROOT_VOCABULARY_MISSING")


def audit(repo: Path, *, validator_source: str | None = None,
          closure_source: str | None = None, ledger_data: dict | None = None) -> dict[str, Any]:
    validator_source = validator_source if validator_source is not None else (repo / VALIDATOR).read_text()
    closure_source = closure_source if closure_source is not None else (repo / CLOSURE).read_text()
    ledger = ledger_data if ledger_data is not None else json.loads((repo / LEDGER).read_text())
    candidates = _candidate_classes(validator_source)
    annotated, typed, closure_imports = _closure_types(closure_source)
    upstream, receipt = _root_names((repo / ROOT_VOCAB).read_text())

    if len(upstream) != 32 or len(receipt) != 33 or len(set(receipt)) != 33:
        raise ValueError("STOP_32_PLUS_ONE_VOCABULARY_DRIFT")
    if ledger.get("upstream_root_count") != 32 or ledger.get("receipt_root_count") != 33:
        raise ValueError("STOP_LEDGER_ROOT_COUNTS_DRIFT")
    if ledger.get("validated_schema_candidates") != 6 or ledger.get("fully_closed_roots") != 0:
        raise ValueError("STOP_FALSE_V27_CLOSURE_OR_COUNT")
    if ledger.get("not_matched_on_reviewed_head") != 25 or ledger.get("unresolved_module") != 2:
        raise ValueError("STOP_LEDGER_SCOPE_CHANGED_REAUDIT_REQUIRED")
    if ledger.get("status") != "SIX_OWN_SCHEMA_CANDIDATES_VALIDATED__ZERO_CLOSED__NO_TRAINING_AUTHORITY":
        raise ValueError("STOP_LEDGER_FALSE_STATUS")
    rows = ledger.get("rows")
    if not isinstance(rows, list) or tuple(r.get("root") for r in rows) != receipt:
        raise ValueError("STOP_LEDGER_ROOT_ORDER_OR_MEMBERSHIP_DRIFT")
    raw = {r["root"]: r for r in rows if r["root"] in RAW_ROLE_ARGUMENTS}
    if set(raw) != set(RAW_ROLE_ARGUMENTS) or any("NO_SINGLE_DEFINING_MODULE" not in r["classification"] for r in raw.values()):
        raise ValueError("STOP_RAW_ROLE_CLASS_FORGERY")
    # A branch can add evidence later; this is deliberately an exact-head snapshot.
    output = []
    for role in ROOTS:
        path, schema, own_class = candidates[role]
        row = next(r for r in rows if r["root"] == role)
        if row.get("candidate_path") != path or row.get("current_closure_validated") is not False:
            raise ValueError("STOP_CANDIDATE_PATH_OR_PREMATURE_CLOSURE_" + role)
        if "CANDIDATE_VALIDATED_BY_CURRENT_OWN_CLASS" not in row.get("classification", ""):
            raise ValueError("STOP_CANDIDATE_VALIDATION_SCOPE_CHANGED_" + role)
        if not (repo / path).is_file():
            raise ValueError("STOP_CANDIDATE_FILE_ABSENT_" + role)
        obj = json.loads((repo / path).read_text())
        if obj.get("schema") != schema:
            raise ValueError("STOP_CANDIDATE_SCHEMA_SPILLOVER_" + role)
        if obj.get("training_authorized") is not False:
            raise ValueError("STOP_CANDIDATE_TRAINING_AUTHORIZATION_" + role)
        param = PARAMS[role]
        closure_class = typed.get(param, annotated.get(param))
        if closure_class is None:
            raise ValueError("STOP_CLOSURE_ROLE_UNMAPPED_" + role)
        if closure_class not in ("Any", own_class) and closure_class not in closure_imports:
            raise ValueError("STOP_CLOSURE_CLASS_IMPORT_MISSING_" + role)
        mismatch = closure_class not in ("Any", own_class)
        output.append({
            "root": role, "candidate_schema": schema, "candidate_class": own_class,
            "closure_parameter": param, "closure_required_class": closure_class,
            "class_compatible": not mismatch,
            "status": ("EXACT_CLASS_CONFLICT__REQUIRES_PROSPECTIVE_VERSIONED_RECONCILIATION"
                       if mismatch else "OWN_SCHEMA_CANDIDATE__CLOSURE_PARENTS_NOT_YET_ATTESTED"),
            "fully_closed": False, "training_authorized": False,
        })
    observed = {x["root"]: (x["candidate_class"], x["closure_required_class"]) for x in output if not x["class_compatible"]}
    if observed != KNOWN_CLASS_CONFLICTS:
        raise ValueError("STOP_UNEXPECTED_CLASS_CONFLICT_CHANGE__INDEPENDENT_REVIEW_REQUIRED")
    return {
        "schema": "V29_SIX_CANDIDATE_CLASS_COMPATIBILITY_AUDIT_V1",
        "reviewed_v27_head": "938fe5d3a7288826fef86b2650fb3a9a21fd3794",
        "current_main_governance": "V25_UNMERGED",
        "upstream_roots": 32, "receipt_roots": 33, "own_schema_candidates": 6,
        "class_conflicts": len(observed), "fully_closed_roots": 0,
        "raw_sha_arguments": list(RAW_ROLE_ARGUMENTS),
        "full104_substrate_physically_rehashed_by_this_audit": False,
        "upstream_parent_bytes_authenticated_by_this_audit": False,
        "reader_fit_training_contract_issued": False, "training_authorized": False,
        "closure_ready": False,
        "rows": output,
    }


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("repo", type=Path)
    cli.add_argument("--out", type=Path)
    cli.add_argument("--require-closure", action="store_true")
    args = cli.parse_args()
    result = audit(args.repo)
    if args.out is not None:
        if args.out.exists():
            raise SystemExit("STOP_REFUSE_OVERWRITE_V29_AUDIT")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if args.require_closure:
        raise SystemExit("STOP_V29_CLASS_CONFLICTS_AND_MISSING_PARENT_VALIDATION__NO_TRAINING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
