from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = ROOT / "results" / "target_discovery" / "unified_qualification_v1"
MATRIX = RESULT_DIR / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"
DECOMP = RESULT_DIR / "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"
STREAMS = RESULT_DIR / "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"
UNRESOLVED = RESULT_DIR / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"
TAXONOMY = RESULT_DIR / "TASK0_MIGRATION_TAXONOMY_V1.json"
COMPLETENESS = RESULT_DIR / "PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json"

OLD_TASK12_HEAD = "ff597faf2182522a320ec5322f8db9b67c9c6094"
CHECKPOINT_HEAD = "f53c13e6eed329651b1088775782fea399ba1bf6"
PLAN_HEAD = "5b6bf07e7d8b69b286ea430b09765a5ee4743325"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _by_id(rows, key="artifact_id"):
    return {row[key]: row for row in rows}


def test_b1_pr356_primary_surfaces_bind_implemented_tasks_and_migrate_task4():
    matrix = _load(MATRIX)
    decomp = _load(DECOMP)
    text = json.dumps(matrix, sort_keys=True) + json.dumps(decomp, sort_keys=True)
    assert OLD_TASK12_HEAD in text
    assert "OLD_TASK1_IMPLEMENTATION" in text
    assert "OLD_TASK2_IMPLEMENTATION" in text
    assert "OLD_TASK3_REQUIREMENTS" in text
    assert "OLD_TASK4_REQUIREMENTS" in text
    assert "OLD_TASKS5_12" in text
    pr356 = next(x for x in decomp["decompositions"] if x["parent_artifact_id"] == "PR356_SYNTH_PLAN")
    children = _by_id(pr356["children"], "child_artifact_id")
    assert children["OLD_TASK1_IMPLEMENTATION"]["source_commit"] == OLD_TASK12_HEAD
    assert children["OLD_TASK2_IMPLEMENTATION"]["source_commit"] == OLD_TASK12_HEAD
    assert children["OLD_TASK4_REQUIREMENTS"]["continue_stop_or_redirect"] == "REDIRECT"
    assert "CaseBundle" in children["OLD_TASK4_REQUIREMENTS"]["destination_in_unified_architecture"]


def test_b2_known_available_identities_are_full_and_bound():
    matrix = _by_id(_load(MATRIX)["artifacts"])
    streams_payload = _load(STREAMS)
    stream_rows = [a for s in streams_payload["streams"] for a in s["artifacts"]]
    streams = _by_id(stream_rows)
    for artifact_id in ["REAL_SUPPORT_PROFILE", "REAL_GEOMETRY_PROFILE", "MACHA_REAL_DATA_AUDIT", "PR356_SYNTH_PLAN"]:
        row = matrix[artifact_id]
        assert row["exact_identity_available"] is True
        assert HEX40.match(row["source_commit"])
        assert row.get("artifact_digest") and HEX64.match(row["artifact_digest"])
        assert row.get("byte_custody")
    for artifact_id in ["MACHA_PR314_CORRECTED_REPLAY", "MACHA_REAL_DATA_AUDIT", "MACHA_V79_TERMINAL_NOT_QUALIFIED", "MACHA_V79_Q00_Q11_REALIZATION_CUSTODY"]:
        row = streams[artifact_id]
        assert row["exact_identity_available"] is True
        assert HEX40.match(row["source_commit"])
        assert row.get("artifact_digest") and HEX64.match(row["artifact_digest"])
        assert row.get("byte_custody")


def test_b3_protected_partition_facts_are_stress_only_and_authority_is_unique():
    matrix = _by_id(_load(MATRIX)["artifacts"])
    streams_payload = _load(STREAMS)
    stream_rows = [a for s in streams_payload["streams"] for a in s["artifacts"]]
    streams = _by_id(stream_rows)
    m = matrix["MACHA_REAL_DATA_AUDIT"]
    s = streams["MACHA_REAL_DATA_AUDIT"]
    assert m["current_authority"] == s["current_authority"]
    protected = m.get("protected_partition_facts", [])
    assert protected
    assert all(x["use_class"] == "PROSPECTIVE_CONVENTION_STRESS_ONLY" for x in protected)
    assert all(x.get("calibration_authorized") is False for x in protected)
    assert "protected partition facts" not in " ".join(m.get("reusable_components", [])).lower()


def test_b4_task12_checkpoint_and_external_obligations_are_in_task0_custody():
    completeness = _load(COMPLETENESS)
    unresolved = _load(UNRESOLVED)
    text = json.dumps(completeness, sort_keys=True) + json.dumps(unresolved, sort_keys=True)
    assert CHECKPOINT_HEAD in text
    ids = {x["item_id"] for x in unresolved["items"]}
    required = {*(f"U_TASK2_REUSE_O{i}" for i in range(1, 9)), "U_TASK2_REUSE_D1_EXCEPTION_WRAPPING", "U_TASK2_E2_PRECOMMITMENT_ERRATUM", "U_TASK2_POST_REVEAL_FRESH_FAMILY", "U_TASK3_READER_FIT_CALIBRATION_STATUS"}
    assert required.issubset(ids)
    by_id = _by_id(unresolved["items"], "item_id")
    for item_id in [f"U_TASK2_REUSE_O{i}" for i in range(1, 9)]:
        assert by_id[item_id]["blocks_same_code_path"] is True


def test_b5_taxonomy_records_retrospective_ratification_and_exact_plan_binding():
    taxonomy = _load(TAXONOMY)
    assert taxonomy["controlling_plan_amendment_head"] == PLAN_HEAD
    assert taxonomy["historical_biological_evidence_authority"] == "RETROSPECTIVELY_RATIFIED_20261014"
    chronology = taxonomy["historical_biological_evidence_chronology"]
    assert chronology["validator_first_commit"] == "f98f0041"
    assert chronology["plan_ratification_commit"] == PLAN_HEAD
    assert chronology["taxonomy_binding_commit"] == "4417949b"
    assert taxonomy.get("controlling_plan_amendment_path")
    assert taxonomy.get("controlling_plan_amendment_blob_sha")
