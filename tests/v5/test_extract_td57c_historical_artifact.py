import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "extract_td57c_historical_artifact.py"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_td57c", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_td57c_member_is_preserved_byte_for_byte(tmp_path):
    m = load_module()
    archive = tmp_path / "historical.zip"
    payload = b'{"gene_views":{"X":[1],"Y":[2],"Z":[3]},"cases":[{"x":1}]}\n'
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("td57c_p0_hvs.json", payload)
        z.writestr("other.txt", b"x")
    out = tmp_path / "td57c_p0_hvs.json"
    receipt = m.extract_td57c_member(archive, sha256_file(archive), out)
    assert out.read_bytes() == payload
    assert receipt["status"] == "PASS_EXACT_TD57C_HISTORICAL_ARTIFACT_EXTRACTED"
    assert receipt["member"] == "td57c_p0_hvs.json"
    assert receipt["member_sha256"] == hashlib.sha256(payload).hexdigest()
    assert receipt["corrected_replay_ingested"] is False
    assert receipt["top_level_keys"] == ["cases", "gene_views"]


def test_archive_sha_mismatch_fails_closed(tmp_path):
    m = load_module()
    archive = tmp_path / "historical.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("td57c_p0_hvs.json", b"{}")
    with pytest.raises(RuntimeError, match="archive SHA mismatch"):
        m.extract_td57c_member(archive, "0" * 64, tmp_path / "out.json")


def test_missing_exact_member_fails_closed(tmp_path):
    m = load_module()
    archive = tmp_path / "historical.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("not_the_member.json", json.dumps({}).encode())
    with pytest.raises(RuntimeError, match="expected exactly one"):
        m.extract_td57c_member(archive, sha256_file(archive), tmp_path / "out.json")
