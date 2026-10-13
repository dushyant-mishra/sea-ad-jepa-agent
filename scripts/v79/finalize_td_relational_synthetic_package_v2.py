from __future__ import annotations

import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path
from typing import Mapping


REQUIRED_INTERFACE_HASHES = (
    "package_validator_sha256",
    "synthetic_adapter_sha256",
    "disk_preflight_sha256",
)


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _load_json(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _validate_identity(td_commit_sha: str, td_interface_hashes: Mapping[str, str]) -> dict[str, str]:
    if not _is_sha256(td_commit_sha):
        raise ValueError("TD commit must be a lowercase 40/64-hex commit identity")
    if not isinstance(td_interface_hashes, Mapping) or set(td_interface_hashes) != set(REQUIRED_INTERFACE_HASHES):
        raise ValueError("interface hash keys must exactly match the frozen certification contract")
    out = {}
    for key in REQUIRED_INTERFACE_HASHES:
        value = td_interface_hashes.get(key)
        if not _is_sha256(value):
            raise ValueError(f"interface hash must be lowercase SHA-256: {key}")
        out[key] = value
    return out


def _tar_entry(name: str, data: bytes) -> tuple[tarfile.TarInfo, bytes]:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mode = 0o600
    return info, data


def _build_uncompressed_tar(entries: list[tuple[str, bytes]]) -> bytes:
    handle = io.BytesIO()
    with tarfile.open(fileobj=handle, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name, data in sorted(entries, key=lambda item: item[0]):
            info, payload = _tar_entry(name, data)
            tf.addfile(info, io.BytesIO(payload))
    return handle.getvalue()


def build_transport_archive(
    *,
    package_dir: Path | str,
    archive_path: Path | str,
    td_commit_sha: str,
    td_interface_hashes: Mapping[str, str],
) -> dict:
    package = Path(package_dir)
    archive = Path(archive_path)
    if not package.is_dir():
        raise ValueError("package_dir must exist")
    interface_hashes = _validate_identity(td_commit_sha, td_interface_hashes)

    binding_path = package / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json"
    fit_root_path = package / "fit_package_root.json"
    controller_path = package / "controller_manifest.json"
    binding = _load_json(binding_path)
    fit_root = _load_json(fit_root_path)
    controller = _load_json(controller_path)

    if binding.get("schema") != "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2":
        raise ValueError("wrong V2 binding schema")
    if controller.get("schema") != "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V2":
        raise ValueError("wrong V2 controller schema")
    package_sha = _sha_bytes(_canonical(fit_root))
    if binding.get("package_sha256") != package_sha or controller.get("package_sha256") != package_sha:
        raise ValueError("package SHA binding mismatch")
    controller_canonical_sha = _sha_bytes(_canonical(controller))
    if binding.get("controller_truth_sha256") != controller_canonical_sha:
        raise ValueError("controller canonical SHA mismatch")

    fit_hashes = [record.get("sha256") for record in binding.get("fit_views", [])]
    if len(fit_hashes) != 9 or any(not _is_sha256(value) for value in fit_hashes):
        raise ValueError("binding must contain exactly nine fit-view hashes")
    if len(set(fit_hashes)) != 9:
        raise ValueError("fit-view hashes must be distinct")

    entries: list[tuple[str, bytes]] = [
        ("pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json", binding_path.read_bytes()),
        ("pre_fit/fit_package_root.json", fit_root_path.read_bytes()),
        ("controller/controller_manifest.json", controller_path.read_bytes()),
    ]
    for digest in fit_hashes:
        path = package / "fit_views" / f"{digest}.npz"
        if not path.is_file() or _sha_file(path) != digest:
            raise ValueError(f"fit-view authentication failed: {digest}")
        entries.append((f"pre_fit/fit_views/{digest}.npz", path.read_bytes()))

    identity = {
        "schema": "JEPA_TD_RELATIONAL_SYNTHETIC_V2_TD_INTERFACE_IDENTITY_V1",
        "td_pr316_commit_sha": td_commit_sha,
        "package_binding_schema": binding["schema"],
        "controller_schema": controller["schema"],
        "td_interface_hashes": interface_hashes,
        "authority": {
            "td_biological_execution_authorized": False,
            "real_td_execution_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    entries.append(("metadata/td_interface_identity.json", _canonical(identity)))

    tar_bytes = _build_uncompressed_tar(entries)
    xz_bytes = lzma.compress(tar_bytes, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME)
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(xz_bytes)

    return {
        "schema": "JEPA_TD_RELATIONAL_SYNTHETIC_V2_TRANSPORT_RECEIPT_V1",
        "package_id": binding["package_id"],
        "package_sha256": package_sha,
        "binding_sha256": _sha_file(binding_path),
        "controller_manifest_file_sha256": _sha_file(controller_path),
        "controller_manifest_canonical_sha256": controller_canonical_sha,
        "fit_view_sha256": sorted(fit_hashes),
        "td_pr316_commit_sha": td_commit_sha,
        "td_interface_hashes": interface_hashes,
        "archive_sha256": _sha_file(archive),
        "archive_size_bytes": archive.stat().st_size,
        "authority": identity["authority"],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Freeze a deterministic synthetic V2 transport archive")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--td-commit", required=True)
    parser.add_argument("--package-validator-sha256", required=True)
    parser.add_argument("--synthetic-adapter-sha256", required=True)
    parser.add_argument("--disk-preflight-sha256", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    receipt = build_transport_archive(
        package_dir=args.package_dir,
        archive_path=args.archive,
        td_commit_sha=args.td_commit,
        td_interface_hashes={
            "package_validator_sha256": args.package_validator_sha256,
            "synthetic_adapter_sha256": args.synthetic_adapter_sha256,
            "disk_preflight_sha256": args.disk_preflight_sha256,
        },
    )
    Path(args.receipt).write_bytes(_canonical(receipt))
