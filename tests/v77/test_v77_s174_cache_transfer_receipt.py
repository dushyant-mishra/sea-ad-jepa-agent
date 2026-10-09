"""S174 cache transfer custody: the committed verification receipt is internally consistent and its
expectations come from the committed S174 authorities, not from the archive. The physical bytes are
local-only (data/ is not in git), so this test checks the receipt, not the files."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v77" / "verify_s174_cache_transfer.py"
REC = ROOT / "results" / "v77" / "s174_replay" / "S174_LOCAL_CACHE_TRANSFER_VERIFICATION_20261009.json"
spec = importlib.util.spec_from_file_location("s174_transfer", SCRIPT)
V = importlib.util.module_from_spec(spec)
sys.modules["s174_transfer"] = V
spec.loader.exec_module(V)


def _rec() -> dict:
    return json.loads(REC.read_text(encoding="utf-8"))


def test_receipt_comes_from_the_committed_verifier_and_passes_exactly():
    rec = _rec()
    assert rec["code_sha256"] == V.sha_file(SCRIPT)
    assert rec["terminal"] == V.PASS and rec["failure_reasons"] == []
    assert rec["expected"] == {"files": 84, "counts_meta_pairs": 42} and rec["exact_matches"] == "84/84"
    assert all(r["exact_match"] and r["bytes_equal"] for r in rec["members"]) and len(rec["members"]) == 84
    assert all(r["canonical_sha256"] == r["extracted_sha256"] == r["authority_sha256"] for r in rec["members"])


def test_expectations_are_the_committed_s174_authorities():
    rec = _rec()
    exp, prov = V.authorities()
    assert {r["relative_path"]: r["authority_sha256"] for r in rec["members"]} == exp
    assert rec["authority_chain"] == prov["chain"]
    chain = prov["chain"]
    assert chain["g1b_pass"] and chain["g1b_r7_bytes_identical"]
    assert chain["g1b_freeze_shards_equal_build_receipt"] and chain["g1b_freeze_cites_this_build_receipt"]


def test_archive_layout_is_the_cache_folder_and_its_84_files():
    lay = _rec()["archive"]["layout"]
    assert lay["file_members"] == 84 and lay["directory_records"] == ["s174_rebuilt_real_train_v1"]
    assert all(r["archive_path"] == f"s174_rebuilt_real_train_v1/{r['relative_path']}" for r in _rec()["members"])
