from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

import finalize_td_relational_synthetic_package_v2_1 as V21


REQUIRED_INTERFACE_HASHES = V21.REQUIRED_INTERFACE_HASHES


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_separated_transport_archives(
    *, package_dir: Path | str, prefit_archive_path: Path | str, controller_archive_path: Path | str,
    td_commit_sha: str, td_interface_hashes: Mapping[str, str],
) -> dict:
    """Freeze V2.1 transports while keeping byte identity and semantic commitment distinct."""
    receipt = V21.build_separated_transport_archives(
        package_dir=package_dir,
        prefit_archive_path=prefit_archive_path,
        controller_archive_path=controller_archive_path,
        td_commit_sha=td_commit_sha,
        td_interface_hashes=td_interface_hashes,
    )
    package = Path(package_dir)
    binding_path = package / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json"
    controller_path = package / "controller" / "controller_manifest.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))

    semantic_commitment = receipt["controller_manifest_sha256"]
    if semantic_commitment != binding.get("controller_truth_sha256"):
        raise ValueError("legacy receipt controller commitment does not match blinded binding")
    raw_manifest_sha = _sha_file(controller_path)

    corrected = dict(receipt)
    corrected["schema"] = "JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_SEPARATED_TRANSPORT_RECEIPT_V2"
    corrected["controller_commitment_sha256"] = semantic_commitment
    corrected["controller_manifest_sha256"] = raw_manifest_sha
    return corrected


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Freeze V2.1 transports with unambiguous controller identities")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--prefit-archive", required=True)
    parser.add_argument("--controller-archive", required=True)
    parser.add_argument("--td-commit", required=True)
    for key in REQUIRED_INTERFACE_HASHES:
        parser.add_argument("--" + key.replace("_", "-"), required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    hashes = {key: getattr(args, key) for key in REQUIRED_INTERFACE_HASHES}
    value = build_separated_transport_archives(
        package_dir=args.package_dir,
        prefit_archive_path=args.prefit_archive,
        controller_archive_path=args.controller_archive,
        td_commit_sha=args.td_commit,
        td_interface_hashes=hashes,
    )
    Path(args.receipt).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
