from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import build_td_relational_synthetic_package_v2 as G
import finalize_td_relational_synthetic_package_v2 as F


TD_SHA = "2397ab83d8ae9d0c762a8fd5f3919edc350d137f"
INTERFACE_HASHES = {
    "package_validator_sha256": "1" * 64,
    "synthetic_adapter_sha256": "2" * 64,
    "disk_preflight_sha256": "3" * 64,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_transport_archive_is_deterministic_and_bound_to_exact_td_interface(tmp_path):
    package = tmp_path / "pkg"
    G.main(str(package))
    archive_a = tmp_path / "a.tar.xz"
    archive_b = tmp_path / "b.tar.xz"
    receipt_a = F.build_transport_archive(
        package_dir=package,
        archive_path=archive_a,
        td_commit_sha=TD_SHA,
        td_interface_hashes=INTERFACE_HASHES,
    )
    receipt_b = F.build_transport_archive(
        package_dir=package,
        archive_path=archive_b,
        td_commit_sha=TD_SHA,
        td_interface_hashes=INTERFACE_HASHES,
    )
    assert sha(archive_a) == sha(archive_b) == receipt_a["archive_sha256"] == receipt_b["archive_sha256"]
    assert receipt_a["td_pr316_commit_sha"] == TD_SHA
    assert receipt_a["td_interface_hashes"] == INTERFACE_HASHES


def test_transport_layout_separates_prefit_and_controller_material(tmp_path):
    package = tmp_path / "pkg"
    G.main(str(package))
    archive = tmp_path / "pkg.tar.xz"
    F.build_transport_archive(
        package_dir=package,
        archive_path=archive,
        td_commit_sha=TD_SHA,
        td_interface_hashes=INTERFACE_HASHES,
    )
    with tarfile.open(archive, "r:xz") as tf:
        names = set(tf.getnames())
        assert "pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json" in names
        assert "pre_fit/fit_package_root.json" in names
        assert "controller/controller_manifest.json" in names
        assert "metadata/td_interface_identity.json" in names
        fit_names = sorted(name for name in names if name.startswith("pre_fit/fit_views/") and name.endswith(".npz"))
        assert len(fit_names) == 9
        controller = json.loads(tf.extractfile("controller/controller_manifest.json").read().decode("utf-8"))
        identity = json.loads(tf.extractfile("metadata/td_interface_identity.json").read().decode("utf-8"))
        assert controller["schema"] == "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V2"
        assert identity["td_pr316_commit_sha"] == TD_SHA
        assert identity["td_interface_hashes"] == INTERFACE_HASHES
        assert identity["authority"]["td_biological_execution_authorized"] is False


def test_transport_receipt_binds_binding_controller_package_and_nine_fit_hashes(tmp_path):
    package = tmp_path / "pkg"
    G.main(str(package))
    archive = tmp_path / "pkg.tar.xz"
    receipt = F.build_transport_archive(
        package_dir=package,
        archive_path=archive,
        td_commit_sha=TD_SHA,
        td_interface_hashes=INTERFACE_HASHES,
    )
    binding = json.loads((package / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json").read_text())
    assert receipt["package_sha256"] == binding["package_sha256"]
    assert receipt["binding_sha256"] == sha(package / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json")
    assert receipt["controller_manifest_canonical_sha256"] == binding["controller_truth_sha256"]
    assert len(receipt["fit_view_sha256"]) == 9
    assert set(receipt["fit_view_sha256"]) == {record["sha256"] for record in binding["fit_views"]}


def test_transport_freeze_rejects_unbound_or_malformed_td_identity(tmp_path):
    package = tmp_path / "pkg"
    G.main(str(package))
    with pytest.raises(ValueError, match="TD commit"):
        F.build_transport_archive(
            package_dir=package,
            archive_path=tmp_path / "bad.tar.xz",
            td_commit_sha="not-a-sha",
            td_interface_hashes=INTERFACE_HASHES,
        )
    with pytest.raises(ValueError, match="interface hash"):
        F.build_transport_archive(
            package_dir=package,
            archive_path=tmp_path / "bad2.tar.xz",
            td_commit_sha=TD_SHA,
            td_interface_hashes={"package_validator_sha256": "x"},
        )
