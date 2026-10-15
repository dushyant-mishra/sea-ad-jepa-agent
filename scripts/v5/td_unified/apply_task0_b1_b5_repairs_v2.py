from __future__ import annotations

import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = ROOT / "results" / "target_discovery" / "unified_qualification_v1"

# Apply the bounded B1-B5 repair first.
runpy.run_path(str(ROOT / "scripts" / "v5" / "td_unified" / "apply_task0_b1_b5_repairs.py"), run_name="__main__")

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_record(record: dict) -> None:
    if record.get("exact_identity_available") is True:
        digest = record.get("artifact_digest")
        blob = record.get("artifact_blob_sha")
        if isinstance(digest, str) and HEX40.fullmatch(digest) and not blob:
            record["artifact_blob_sha"] = digest
            record["artifact_digest"] = None
            blob = digest
        if isinstance(record.get("artifact_digest"), str) and HEX64.fullmatch(record["artifact_digest"]):
            record.setdefault("byte_custody", "SHA256_PAYLOAD")
        elif isinstance(record.get("artifact_blob_sha"), str) and HEX40.fullmatch(record["artifact_blob_sha"]):
            record.setdefault("byte_custody", "REPO_BLOB")
    else:
        record.setdefault("identity_unavailable_reason", "exact payload identity not frozen in current Task0 custody; retain only declared historical authority")
        record.setdefault("byte_custody", "HISTORICAL_WRAPPER_OR_NAVIGATION_ONLY")


def normalize_all() -> None:
    matrix_path = RESULT_DIR / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"
    p = load(matrix_path)
    for row in p["artifacts"]:
        normalize_record(row)
    dump(matrix_path, p)

    decomp_path = RESULT_DIR / "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"
    p = load(decomp_path)
    for entry in p["decompositions"]:
        for row in entry["children"]:
            normalize_record(row)
    dump(decomp_path, p)

    streams_path = RESULT_DIR / "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"
    p = load(streams_path)
    for stream in p["streams"]:
        for row in stream["artifacts"]:
            normalize_record(row)
    dump(streams_path, p)


def patch_tests() -> None:
    path = ROOT / "tests" / "v5" / "td_unified" / "test_premerger_migration_task0.py"
    text = path.read_text(encoding="utf-8")
    old = '''def test_available_exact_identity_is_not_omitted():\n    matrix = _load(MATRIX)\n    for artifact in matrix["artifacts"]:\n        assert "exact_identity_available" in artifact\n        if artifact["exact_identity_available"]:\n            assert artifact.get("source_commit")\n            assert artifact.get("artifact_digest")\n\n\n'''
    new = '''def test_available_exact_identity_is_not_omitted():\n    matrix = _load(MATRIX)\n    for artifact in matrix["artifacts"]:\n        assert "exact_identity_available" in artifact\n        if artifact["exact_identity_available"]:\n            assert re.fullmatch(r"[0-9a-f]{40}", artifact.get("source_commit", ""))\n            digest = artifact.get("artifact_digest")\n            blob = artifact.get("artifact_blob_sha")\n            assert (isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)) or (\n                isinstance(blob, str) and re.fullmatch(r"[0-9a-f]{40}", blob) and artifact.get("artifact_path")\n            )\n\n\ndef test_validator_rejects_truncated_exact_commit(tmp_path: Path):\n    matrix = _load(MATRIX)\n    unresolved = _load(UNRESOLVED)\n    target = next(a for a in matrix["artifacts"] if a.get("exact_identity_available"))\n    target["source_commit"] = target["source_commit"][:6]\n    bad_matrix = tmp_path / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"\n    ledger = tmp_path / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"\n    bad_matrix.write_text(json.dumps(matrix), encoding="utf-8")\n    ledger.write_text(json.dumps(unresolved), encoding="utf-8")\n    for name in ["PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json", "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json", "TASK0_MIGRATION_TAXONOMY_V1.json"]:\n        (tmp_path / name).write_text((RESULT_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")\n    with pytest.raises(ValueError, match="invalid source_commit"):\n        validate_migration_outputs(bad_matrix, ledger)\n\n\n'''
    if old not in text:
        raise RuntimeError("expected exact-identity test block not found")
    text = text.replace(old, new)
    if not text.startswith("import re\n") and "\nimport re\n" not in text[:300]:
        text = text.replace("import json\n", "import json\nimport re\n", 1)
    path.write_text(text, encoding="utf-8")

    b1 = ROOT / "tests" / "v5" / "td_unified" / "test_task0_b1_b5_regressions.py"
    text = b1.read_text(encoding="utf-8").replace('assert "CaseBundle" in children["OLD_TASK4_REQUIREMENTS"]["destination_in_unified_architecture"]', 'assert "KNOWN_TRUTH_CASEBUNDLE_V1" in children["OLD_TASK4_REQUIREMENTS"]["destination_in_unified_architecture"]')
    b1.write_text(text, encoding="utf-8")


normalize_all()
patch_tests()
