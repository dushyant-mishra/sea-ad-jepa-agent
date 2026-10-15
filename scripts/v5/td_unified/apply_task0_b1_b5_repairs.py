from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "results" / "target_discovery" / "unified_qualification_v1"
MATRIX = R / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"
DECOMP = R / "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"
STREAMS = R / "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"
UNRESOLVED = R / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"
TAXONOMY = R / "TASK0_MIGRATION_TAXONOMY_V1.json"
COMPLETENESS = R / "PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json"
VALIDATOR = ROOT / "scripts" / "v5" / "td_unified" / "premerger_migration_task0.py"

OLD_HEAD = "ff597faf2182522a320ec5322f8db9b67c9c6094"
CHECKPOINT_HEAD = "f53c13e6eed329651b1088775782fea399ba1bf6"
CHECKPOINT_SHA256 = "412473ac5075f03bcfc1390b93a0db1694d2b595165f74b9fc7c9c61598a94a6"
PLAN_HEAD = "5b6bf07e7d8b69b286ea430b09765a5ee4743325"
PLAN_PATH = "docs/superpowers/plans/2026-10-14-unified-td-qualification-downstream-custody-v1-task0-taxonomy-amendment.md"
PLAN_BLOB = "7f20050c2a8d0f80f0c6418c007bc12f7fc1083f"
PR356_PLAN_PATH = "docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md"
PR356_PLAN_HEAD = "2c2723a1a731e7a848196aef3f7c4ab965e9ff6a"
PR356_PLAN_BLOB = "ad81e3f2d5a7a0efded9b8b38c9060ebe676a48e"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def by_id(rows, key="artifact_id"):
    return {row[key]: row for row in rows}


def mark_false_identity(record):
    if record.get("exact_identity_available") is False:
        record.setdefault(
            "identity_unavailable_reason",
            "exact payload SHA-256 or repo blob is not frozen in current Task0 custody; retain only the narrower historical authority declared by this record",
        )
        record.setdefault("byte_custody", "HISTORICAL_WRAPPER_OR_NAVIGATION_ONLY")


def repair_matrix():
    p = load(MATRIX)
    active = by_id(p["active_or_partial_work"], "task_id")
    t13 = active["FORMER_SYNTH_TASKS_1_3_REQUIREMENTS"]
    t13.update({
        "exact_head_sha": OLD_HEAD,
        "current_status": "TASKS1_2_IMPLEMENTED_AND_CONTROLLER_VERIFIED__TASK3_STOPPED_REQUIREMENTS_MIGRATE_ONLY",
        "work_completed": ["Task1 canonical identity implementation", "Task2 sealed custody/RNG implementation", "controller verification PR #382: 332 passed"],
        "work_remaining": ["absorb Task1 primitives into unified Task1", "migrate Task2 custody substrate to sealed-challenge/finalizer infrastructure", "migrate old Task3 calibration/provenance requirements only"],
        "files_created": ["scripts/production_synthetic/canonical_v1.py", "scripts/production_synthetic/custody_v1.py", "historical PR #356 plan/handoff"],
        "tests_created": ["production_synthetic Task1/Task2 suites; independent Linux verification 332 passed"],
        "outputs_generated": ["reviewed Task1/Task2 reusable substrate", "Tasks1-2 checkpoint"],
        "continue_stop_or_redirect": "REDIRECT",
        "reason": "Tasks1-2 implementation survives as ADAPT_AND_WRAP substrate; old Task3 implementation stays stopped and requirements migrate",
    })
    t412 = active["FORMER_SYNTH_TASKS_4_12"]
    t412.update({
        "current_status": "TASK4_STOPPED_REQUIREMENTS_MIGRATE_ONLY__TASKS5_12_SUPERSEDED",
        "work_completed": ["Task4 candidate-neutral biology requirements designed"],
        "work_remaining": ["migrate Task4 requirements into unified CaseBundle/TruthBundle", "do not independently continue Tasks5-12"],
        "unified_destination": "Task4 requirements -> KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1; Tasks5-12 remain stopped",
        "reason": "Task4 requirements survive the merger; only independent Tasks5-12 authority path is superseded",
    })

    a = by_id(p["artifacts"])
    support = a["REAL_SUPPORT_PROFILE"]
    support.update({"source_commit": "f5a8ebeddbcd52a94274a7f72ecda1f71b82d777", "artifact_digest": "b78e65af8290245519bac7781f61793150592da9f542593dc0100df5cbdd395a", "artifact_blob_sha": "e816483b75116c06979b9fd1507e3e0ebfb281df", "exact_identity_available": True, "byte_custody": "REPO_BLOB_AND_SHA256"})
    geometry = a["REAL_GEOMETRY_PROFILE"]
    geometry.update({"source_commit": "f5a8ebeddbcd52a94274a7f72ecda1f71b82d777", "artifact_digest": "1ddf37827d548c84f533add702722e3015ea4abaedf258bf03a9c13e65d36f3a", "artifact_blob_sha": "1b50ceb4d28ea2b2e4ad0c88a3c34c816a908fd4", "exact_identity_available": True, "byte_custody": "REPO_BLOB_AND_SHA256"})
    audit = a["MACHA_REAL_DATA_AUDIT"]
    audit.update({
        "artifact_path": "results/target_discovery/real_qualification_macha_20261014/QUALIFICATION_RECEIPT_INDEX_V1.json",
        "artifact_digest": "2af2acc3bf29c51aa885626ddd4567e5b8d9b885b747c335031d1b932c0ba86c",
        "source_commit": "ccc3a08939694f5d35b3048c94ec44f44618eef4",
        "exact_identity_available": True,
        "byte_custody": "REPO_RECEIPT_INDEX_SHA256",
        "current_authority": "AUDIT_CUSTODY_AUTHORITY_ONLY",
        "reusable_components": ["289 addresses with no scalar-measuring operator", "17,186-address all-operator core", "source-only 730/4,894/4,710", "reader-fit Level-4 depth-retention census"],
        "destination_in_unified_architecture": "partition-independent operator/support facts may inform prospectively authorized calibration; protected-partition facts are stress-only; retain gate-blocker dependency ledger",
        "protected_partition_facts": [
            {"fact": "NPH52 has 0 reader-validation and 2 reader-oracle donors", "use_class": "PROSPECTIVE_CONVENTION_STRESS_ONLY", "calibration_authorized": False},
            {"fact": "4,894 NPH52-only addresses are never measured in reader-validation", "use_class": "PROSPECTIVE_CONVENTION_STRESS_ONLY", "calibration_authorized": False},
            {"fact": "SEA_AD held-out subclass donor counts", "use_class": "PROSPECTIVE_CONVENTION_STRESS_ONLY", "calibration_authorized": False},
        ],
    })
    plan = a["PR356_SYNTH_PLAN"]
    plan.update({"artifact_path": PR356_PLAN_PATH, "source_commit": PR356_PLAN_HEAD, "artifact_digest": None, "artifact_blob_sha": PR356_PLAN_BLOB, "exact_identity_available": True, "byte_custody": "REPO_BLOB", "reusable_components": ["Task1 implemented canonical identity substrate", "Task2 implemented custody/RNG substrate", "Task3 calibration/provenance requirements", "Task4 candidate-neutral biology requirements"], "superseded_components": ["independent synthetic Tasks5-12 authority path"], "destination_in_unified_architecture": "Tasks1-2 ADAPT_AND_WRAP; Tasks3-4 requirements migrate; Tasks5-12 independent continuation stopped", "decomposition_note": "Task1 and Task2 implemented at ff597faf; Task3 and Task4 requirements migrate only; Tasks5-12 stay stopped"})
    for row in p["artifacts"]:
        mark_false_identity(row)
    dump(MATRIX, p)


def child(child_id, role, migration_class, authority, destination, action, source_commit, blob, reusable, superseded=None):
    return {
        "child_artifact_id": child_id,
        "scientific_role": role,
        "migration_class": migration_class,
        "current_authority": authority,
        "destination_in_unified_architecture": destination,
        "continue_stop_or_redirect": action,
        "historical_evidence_retained": True,
        "requires_requalification": True,
        "requalification_reason": "must be rebound under the unified architecture before any current authority use",
        "reusable_components": reusable,
        "superseded_components": superseded or [],
        "source_commit": source_commit,
        "artifact_digest": None,
        "artifact_blob_sha": blob,
        "exact_identity_available": True,
        "byte_custody": "REPO_BLOB",
        "authority_basis": "EXACT_COMMIT_AND_REPO_BLOB",
    }


def repair_decomposition():
    p = load(DECOMP)
    entry = next(x for x in p["decompositions"] if x["parent_artifact_id"] == "PR356_SYNTH_PLAN")
    entry["children"] = [
        child("OLD_TASK1_IMPLEMENTATION", "implemented canonical identity/serialization substrate", "REUSABLE_SHARED_INFRASTRUCTURE", "CONTROLLER_VERIFIED_REUSE_SUBSTRATE_ONLY__NO_UNIFIED_PROMOTION", "unified Task1 canonical primitives via ADAPT_AND_WRAP", "REDIRECT", OLD_HEAD, "b8a34d8d47f618e7dcde1b3e5c53584701294561", ["canonical identity", "ordered registry digest", "semantic row-set digest"]),
        child("OLD_TASK2_IMPLEMENTATION", "implemented sealed custody/RNG substrate", "REUSABLE_SHARED_INFRASTRUCTURE", "CONTROLLER_VERIFIED_REUSE_SUBSTRATE_ONLY__NO_UNIFIED_PROMOTION", "unified sealed-challenge/finalizer custody via ADAPT_AND_WRAP; not unified Task2 manifest/access law", "REDIRECT", OLD_HEAD, "8efb7622eb2773305f9159cafdb19ccae8946fef", ["commit/reveal", "identity-keyed RNG", "exposure ledger", "withheld-family custody"]),
        child("OLD_TASK3_REQUIREMENTS", "calibration firewall, numeric provenance and realism requirements only", "PRODUCTION_INTERFACE_DEPENDENCY", "REQUIREMENTS_ONLY__NO_OLD_LANE_IMPLEMENTATION_AUTHORITY", "unified calibration/provenance/realism contracts after Task0 acceptance", "REDIRECT", PR356_PLAN_HEAD, PR356_PLAN_BLOB, ["calibration firewall", "number provenance", "realism contract"]),
        child("OLD_TASK4_REQUIREMENTS", "candidate-neutral known-truth biology requirements only", "KNOWN_TRUTH_SUBSTRATE", "REQUIREMENTS_ONLY__NO_OLD_LANE_IMPLEMENTATION_AUTHORITY", "KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1 substrate requirements", "REDIRECT", PR356_PLAN_HEAD, PR356_PLAN_BLOB, ["candidate-neutral hidden biology requirements"]),
        child("OLD_TASKS5_12", "former independent synthetic gate/controller/downstream authority path", "SUPERSEDED_PARALLEL_IMPLEMENTATION", "SUPERSEDED__NO_NEW_SCIENTIFIC_AUTHORITY", "historical requirements/challenge lessons only where explicitly migrated", "STOP_AND_FREEZE", PR356_PLAN_HEAD, PR356_PLAN_BLOB, [], ["independent synthetic Tasks5-12 authority path"]),
    ]
    for d in p["decompositions"]:
        for row in d["children"]:
            mark_false_identity(row)
    dump(DECOMP, p)


def repair_streams():
    p = load(STREAMS)
    rows = [a for s in p["streams"] for a in s["artifacts"]]
    a = by_id(rows)
    a["MACHA_PR314_CORRECTED_REPLAY"].update({"source_commit": "c6899a2910244a0352c0c57e7aea6e3026191da1", "artifact_path": "docs/agent/TD_CORRECTED_REPLAY_OUTCOME_7819aabd_20261012/TD_CORRECTED_REPLAY_OUTCOME.md", "artifact_blob_sha": "91fe2cb4e21e63991b7693365397d0168fb92ff6", "exact_identity_available": True, "byte_custody": "REPO_BLOB"})
    a["MACHA_REAL_DATA_AUDIT"].update({"artifact_path": "results/target_discovery/real_qualification_macha_20261014/QUALIFICATION_RECEIPT_INDEX_V1.json", "source_commit": "ccc3a08939694f5d35b3048c94ec44f44618eef4", "artifact_digest": "2af2acc3bf29c51aa885626ddd4567e5b8d9b885b747c335031d1b932c0ba86c", "exact_identity_available": True, "byte_custody": "REPO_RECEIPT_INDEX_SHA256", "current_authority": "AUDIT_CUSTODY_AUTHORITY_ONLY", "destination_in_unified_architecture": "partition-independent support/operator evidence plus prerequisite graph; protected-partition facts stress-only"})
    a["MACHA_V79_TERMINAL_NOT_QUALIFIED"].update({"artifact_path": "V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2.json", "source_commit": "ac1e73d79489438634aaeeca035d229875f3186a", "artifact_digest": "ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd", "exact_identity_available": True, "byte_custody": "LOCAL_ONLY:D:/jepa_v79_scoring_run_ac1e73d7_20261013/scoring_output/", "authorization_sha256": "4793d8f9024891a6572337246c76dea871b65ebde476d8f3983c483498b80337"})
    a["MACHA_V79_Q00_Q11_REALIZATION_CUSTODY"].update({"artifact_path": "scripts/v79/v79_v2_core_score_authority.py", "source_commit": "ac1e73d79489438634aaeeca035d229875f3186a", "artifact_blob_sha": "fa1fb78fdd2f93a095c6cb7cd5bc2c61a39fe29b", "exact_identity_available": True, "byte_custody": "REPO_BLOB_WITH_FROZEN_RESULT_AND_LEDGER_CONSTANTS"})
    for row in rows:
        mark_false_identity(row)
    dump(STREAMS, p)


def unresolved_item(item_id, missing, why, owner, *, same=True, kt=True, ref=True, human=True, real=False, finish=False):
    return {"item_id": item_id, "missing_dependency": missing, "why_missing": why, "who_owns_resolution": owner, "can_known_truth_lane_finish_now": finish, "requires_merged_lane_interface": True, "requires_real_data": real, "blocks_same_code_path": same, "blocks_known_truth_qualification": kt, "blocks_real_reference_ready": ref, "blocks_human_execution": human}


def repair_unresolved():
    p = load(UNRESOLVED)
    existing = {x["item_id"] for x in p["items"]}
    obligations = {
        "U_TASK2_REUSE_O1": ("one ledger per testbed from genesis", "fresh ledgers could bypass successor/exposure law"),
        "U_TASK2_REUSE_O2": ("publish ledger head after every entry and check expected_head", "re-chaining is detectable only against published heads"),
        "U_TASK2_REUSE_O3": ("report qualification draws per method and lineage with multiplicity", "sealed-draw reuse needs lineage-level accounting"),
        "U_TASK2_REUSE_O4": ("consult withheld_check_eligible only after the version's own reveal", "pre-reveal eligibility is not final"),
        "U_TASK2_REUSE_O5": ("regenerate realization content from sealed root at reveal", "same-ID content swaps are otherwise undetectable"),
        "U_TASK2_REUSE_O6": ("secret scan full git archive of each published commit", "sparse-worktree scans can miss leaked secrets"),
        "U_TASK2_REUSE_O7": ("emit withheld-family worlds inside SYNTH_QUALIFICATION budget", "withheld worlds must consume the sealed qualification budget"),
        "U_TASK2_REUSE_O8": ("independent audit of defect justifications", "defect records are attested declarations, not self-validating authority"),
    }
    for item_id, (missing, why) in obligations.items():
        if item_id not in existing:
            p["items"].append(unresolved_item(item_id, missing, why, "unified sealed-custody/finalizer implementation"))
    extra = [
        unresolved_item("U_TASK2_REUSE_D1_EXCEPTION_WRAPPING", "narrow catch-all exception wrapping and message-matched refusal tests", "internal bugs can currently be wrapped as generic custody refusals", "old Task2 substrate repair before unified reuse"),
        unresolved_item("U_TASK2_E2_PRECOMMITMENT_ERRATUM", "prospective spec erratum stating commitment binds a precommitment hash", "literal E2 is circular because generator hash contains the commitment", "owner/Sol plan authority"),
        unresolved_item("U_TASK2_POST_REVEAL_FRESH_FAMILY", "prospective design for a fresh withheld family after reveal", "current substrate correctly fails closed but does not define replacement-family issuance", "future sealed-challenge design"),
        unresolved_item("U_TASK3_READER_FIT_CALIBRATION_STATUS", "manifest-bound rule for reader_fit calibration versus held-out evidence", "calibration use spends independence for the same gate; reader_validation/oracle remain protected", "unified Task2/Task3 access-policy design", real=True),
    ]
    for item in extra:
        if item["item_id"] not in existing:
            p["items"].append(item)
    p["old_task1_2_checkpoint"] = {"commit": CHECKPOINT_HEAD, "path": "docs/agent/PRODUCTION_SYNTHETIC_TASKS_1_2_CHECKPOINT_MACHA_20261014.md", "sha256": CHECKPOINT_SHA256, "role": "AUTHOR_PROVENANCE_AND_REUSE_OBLIGATIONS__NOT_SELF_QUALIFICATION"}
    dump(UNRESOLVED, p)


def repair_completeness():
    p = load(COMPLETENESS)
    group = next(g for g in p["custody_groups"] if g["group_id"] == "ACTIVE_PR356_TASKS_1_4")
    rows = by_id(group["objects"], "object_id")
    checkpoint = {"commit": CHECKPOINT_HEAD, "path": "docs/agent/PRODUCTION_SYNTHETIC_TASKS_1_2_CHECKPOINT_MACHA_20261014.md", "sha256": CHECKPOINT_SHA256, "role": "AUTHOR_PROVENANCE_ONLY__PR382_IS_INDEPENDENT_VERIFICATION"}
    for object_id in ("PR356_TASK1", "PR356_TASK2"):
        rows[object_id]["macha_tasks1_2_checkpoint"] = checkpoint
        rows[object_id]["independent_verification"] = {"pr": 382, "run": 38644641042, "job": 116128364543, "result": "332 passed in 8.94s"}
    rows["PR356_TASK2"]["required_external_obligations"] = [f"U_TASK2_REUSE_O{i}" for i in range(1, 9)] + ["U_TASK2_REUSE_D1_EXCEPTION_WRAPPING", "U_TASK2_E2_PRECOMMITMENT_ERRATUM", "U_TASK2_POST_REVEAL_FRESH_FAMILY"]
    rows["PR356_TASK3"]["required_external_obligations"] = ["U_TASK3_READER_FIT_CALIBRATION_STATUS"]
    dump(COMPLETENESS, p)


def repair_taxonomy():
    p = load(TAXONOMY)
    p.update({
        "controlling_plan_amendment_head": PLAN_HEAD,
        "controlling_plan_amendment_path": PLAN_PATH,
        "controlling_plan_amendment_blob_sha": PLAN_BLOB,
        "historical_biological_evidence_authority": "RETROSPECTIVELY_RATIFIED_20261014",
        "historical_biological_evidence_chronology": {"validator_first_commit": "f98f0041", "validator_first_time_edt": "14:44:53", "plan_ratification_commit": PLAN_HEAD, "plan_ratification_time_edt": "15:43:21", "taxonomy_binding_commit": "4417949b", "taxonomy_binding_time_edt": "15:45:03", "interpretation": "class content retained; prospective-ordering claim withdrawn and replaced by explicit retrospective ratification"},
    })
    dump(TAXONOMY, p)


def repair_validator():
    text = VALIDATOR.read_text(encoding="utf-8")
    if "import re\n" not in text:
        text = text.replace("import json\n", "import json\nimport re\n")
    old = '''def _validate_exact_identity(record: dict[str, Any], label: str) -> None:\n    if "exact_identity_available" not in record:\n        raise ValueError(f"{label} missing required field: exact_identity_available")\n    if not isinstance(record["exact_identity_available"], bool):\n        raise ValueError(f"{label} exact_identity_available must be boolean")\n    if record["exact_identity_available"]:\n        if not record.get("source_commit") or not record.get("artifact_digest"):\n            raise ValueError(f"available exact identity omitted for {label}")\n\n\n'''
    new = '''def _validate_exact_identity(record: dict[str, Any], label: str) -> None:\n    if "exact_identity_available" not in record:\n        raise ValueError(f"{label} missing required field: exact_identity_available")\n    if not isinstance(record["exact_identity_available"], bool):\n        raise ValueError(f"{label} exact_identity_available must be boolean")\n    if record["exact_identity_available"]:\n        commit = record.get("source_commit")\n        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:\n            raise ValueError(f"available exact identity has invalid source_commit for {label}")\n        digest = record.get("artifact_digest")\n        blob = record.get("artifact_blob_sha")\n        digest_ok = isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None\n        blob_ok = isinstance(blob, str) and re.fullmatch(r"[0-9a-f]{40}", blob) is not None and bool(record.get("artifact_path"))\n        if not (digest_ok or blob_ok):\n            raise ValueError(f"available exact payload identity omitted for {label}")\n        if not record.get("byte_custody"):\n            raise ValueError(f"available exact identity missing byte_custody for {label}")\n    else:\n        if not record.get("identity_unavailable_reason"):\n            raise ValueError(f"unavailable exact identity missing reason for {label}")\n        authority = str(record.get("current_authority", ""))\n        basis = record.get("authority_basis")\n        if authority.startswith("AUTHENTICATED_CALIBRATION") or basis in {"EXACT_COMMIT_AND_AUTHENTICATED_AUDIT_OR_RECEIPT", "AUTHENTICATED_CALIBRATION_RECEIPT"}:\n            raise ValueError(f"authority-bearing identity cannot be unavailable for {label}")\n\n\n'''
    if old in text:
        text = text.replace(old, new)
    marker = "\ndef validate_migration_outputs(matrix_path: Path, unresolved_path: Path) -> dict[str, Any]:\n"
    if "def _validate_b1_b5_repair_guards" not in text:
        helper = '''\ndef _validate_b1_b5_repair_guards(matrix_path: Path, unresolved_ids: set[str], artifacts: list[dict[str, Any]]) -> None:\n    by_artifact = {a["artifact_id"]: a for a in artifacts}\n    decomp = _load(matrix_path.with_name("PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"))\n    pr356 = next((x for x in decomp.get("decompositions", []) if x.get("parent_artifact_id") == "PR356_SYNTH_PLAN"), None)\n    if pr356 is None:\n        raise ValueError("B1 PR356 decomposition missing")\n    children = {x["child_artifact_id"]: x for x in pr356.get("children", [])}\n    required_children = {"OLD_TASK1_IMPLEMENTATION", "OLD_TASK2_IMPLEMENTATION", "OLD_TASK3_REQUIREMENTS", "OLD_TASK4_REQUIREMENTS", "OLD_TASKS5_12"}\n    if set(children) != required_children:\n        raise ValueError("B1 PR356 decomposition does not match merged stop law")\n    old_head = "ff597faf2182522a320ec5322f8db9b67c9c6094"\n    if children["OLD_TASK1_IMPLEMENTATION"].get("source_commit") != old_head or children["OLD_TASK2_IMPLEMENTATION"].get("source_commit") != old_head:\n        raise ValueError("B1 old Tasks1-2 exact implementation head not bound")\n    if children["OLD_TASK4_REQUIREMENTS"].get("continue_stop_or_redirect") != "REDIRECT":\n        raise ValueError("B1 old Task4 requirements were dropped instead of migrated")\n\n    streams = _load(matrix_path.with_name("PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"))\n    stream_rows = {a["artifact_id"]: a for s in streams.get("streams", []) for a in s.get("artifacts", [])}\n    for artifact_id in set(by_artifact) & set(stream_rows):\n        if by_artifact[artifact_id].get("current_authority") != stream_rows[artifact_id].get("current_authority"):\n            raise ValueError(f"B3 conflicting authority across Task0 surfaces for {artifact_id}")\n    audit = by_artifact.get("MACHA_REAL_DATA_AUDIT", {})\n    for fact in audit.get("protected_partition_facts", []):\n        if fact.get("use_class") != "PROSPECTIVE_CONVENTION_STRESS_ONLY" or fact.get("calibration_authorized") is not False:\n            raise ValueError("B3 protected-partition fact routed into calibration")\n\n    required_unresolved = {*(f"U_TASK2_REUSE_O{i}" for i in range(1, 9)), "U_TASK2_REUSE_D1_EXCEPTION_WRAPPING", "U_TASK2_E2_PRECOMMITMENT_ERRATUM", "U_TASK2_POST_REVEAL_FRESH_FAMILY", "U_TASK3_READER_FIT_CALIBRATION_STATUS"}\n    missing = sorted(required_unresolved - unresolved_ids)\n    if missing:\n        raise ValueError("B4 Task1-2 reuse obligations missing: " + ", ".join(missing))\n\n    taxonomy = _load(matrix_path.with_name("TASK0_MIGRATION_TAXONOMY_V1.json"))\n    if set(taxonomy.get("allowed_migration_classes", [])) != set(MIGRATION_CLASSES):\n        raise ValueError("B5 taxonomy does not match validator enum")\n    if taxonomy.get("controlling_plan_amendment_head") != "5b6bf07e7d8b69b286ea430b09765a5ee4743325":\n        raise ValueError("B5 controlling taxonomy amendment head mismatch")\n    if taxonomy.get("controlling_plan_amendment_blob_sha") != "7f20050c2a8d0f80f0c6418c007bc12f7fc1083f":\n        raise ValueError("B5 controlling taxonomy amendment blob mismatch")\n    if taxonomy.get("historical_biological_evidence_authority") != "RETROSPECTIVELY_RATIFIED_20261014":\n        raise ValueError("B5 taxonomy chronology not truthfully classified")\n\n'''
        text = text.replace(marker, helper + marker)
    needle = "    macha_stream_artifact_count = _validate_macha_streams(matrix_path, unresolved_ids)\n"
    if "_validate_b1_b5_repair_guards(matrix_path, unresolved_ids, artifacts)" not in text:
        text = text.replace(needle, needle + "    _validate_b1_b5_repair_guards(matrix_path, unresolved_ids, artifacts)\n")
    VALIDATOR.write_text(text, encoding="utf-8")


def main():
    repair_matrix()
    repair_decomposition()
    repair_streams()
    repair_unresolved()
    repair_completeness()
    repair_taxonomy()
    repair_validator()


if __name__ == "__main__":
    main()
