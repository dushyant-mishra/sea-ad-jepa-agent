import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "build_td_relational_replay_manifest.py"
EXPECTED_MANIFEST_SHA = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"


def load_module():
    spec = importlib.util.spec_from_file_location("td_replay_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_pair_hash_is_deterministic():
    module = load_module()
    genes = np.arange(512, dtype=np.int32)
    assert module.pair_hash(genes, "TD59", 0, "Z") == (
        "023ac869614eac50ea1359ba1af61f2935264d0d894e66357cf4399abdb20d56"
    )


def test_manifest_writer_persists_exact_lf_bytes(tmp_path):
    module = load_module()
    out = tmp_path / "manifest.csv"
    text = "a,b\n1,2\n"
    module.write_lf_bytes(out, text)
    assert out.read_bytes() == text.encode("utf-8")
    assert b"\r\n" not in out.read_bytes()


def test_rebuild_manifest_against_external_authorities(tmp_path):
    cal = os.environ.get("TD_CALIBRATION_ZIP")
    td = os.environ.get("TD_ARTIFACTS_ZIP")
    if not cal or not td:
        pytest.skip("external replay authorities not supplied")

    out_csv = tmp_path / "manifest.csv"
    out_json = tmp_path / "receipt.json"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--calibration-zip",
            cal,
            "--td-artifacts-zip",
            td,
            "--manifest-out",
            str(out_csv),
            "--receipt-out",
            str(out_json),
        ],
        check=True,
    )
    receipt = json.loads(out_json.read_text())
    assert receipt["status"] == "PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST"
    assert receipt["common_core_rows"] == 17186
    assert receipt["replay_addresses"] == 9216
    assert receipt["manifest_sha256"] == EXPECTED_MANIFEST_SHA
    assert all(receipt["validation"].values())
