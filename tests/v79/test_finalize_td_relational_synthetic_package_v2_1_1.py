from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import build_td_relational_synthetic_package_v2_1 as G
import finalize_td_relational_synthetic_package_v2_1_1 as F


SEED = "43" * 32
NONCE = "b5" * 32
TD_SHA = "7" * 40
HASHES = {
    "package_validator_sha256": "1" * 64,
    "synthetic_adapter_sha256": "2" * 64,
    "disk_preflight_sha256": "3" * 64,
    "qualification_runner_v3_sha256": "4" * 64,
}


def test_receipt_separates_raw_controller_file_hash_from_semantic_commitment(tmp_path):
    package = tmp_path / "package"
    G.main(str(package), realization_seed_hex=SEED, blind_nonce=NONCE)
    prefit = tmp_path / "prefit.tar.xz"
    controller = tmp_path / "controller.tar.xz"
    receipt = F.build_separated_transport_archives(
        package_dir=package,
        prefit_archive_path=prefit,
        controller_archive_path=controller,
        td_commit_sha=TD_SHA,
        td_interface_hashes=HASHES,
    )
    controller_path = package / "controller" / "controller_manifest.json"
    binding = json.loads((package / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json").read_text(encoding="utf-8"))

    raw_sha = hashlib.sha256(controller_path.read_bytes()).hexdigest()
    assert receipt["schema"] == "JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_SEPARATED_TRANSPORT_RECEIPT_V2"
    assert receipt["controller_manifest_sha256"] == raw_sha
    assert receipt["controller_commitment_sha256"] == binding["controller_truth_sha256"]
    assert receipt["controller_manifest_sha256"] != receipt["controller_commitment_sha256"]

    with tarfile.open(controller, "r:xz") as tf:
        archived = tf.extractfile("controller/controller_manifest.json").read()
    assert hashlib.sha256(archived).hexdigest() == receipt["controller_manifest_sha256"]
