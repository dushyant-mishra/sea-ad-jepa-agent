from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .unified_synthetic_integration_v1 import UnifiedBiologyWorld
from .unified_synthetic_fit_view_v1 import UnifiedFitView, fit_view_sha256
from .unified_synthetic_controller_truth_v1 import UnifiedControllerTruth, controller_truth_sha256


_AUTHORITY = {
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
    "real_data_authorized": False,
    "synthetic_training_authorized": False,
}
_SOURCE_COMMITS = {
    "stage81a3": "f5a8ebeddbcd52a94274a7f72ecda1f71b82d777",
    "v79_pr253": "1a0ab6e1108af924ca13e81caa3c70f3101d251c",
    "pr311": "2b6d3439105e087acdab53a318c57bbb468eae26",
    "pr315": "af03ef67d52651463944a6de3a08e101ad00e0ea",
}
_INTEGRATION_SOURCE_FILES = (
    "scripts/v79/unified_synthetic_integration_v1.py",
    "scripts/v79/unified_synthetic_fit_view_v1.py",
    "scripts/v79/unified_synthetic_controller_truth_v1.py",
    "scripts/v79/finalize_unified_synthetic_integration_v1.py",
)


def _canon(value: Mapping[str, object]) -> bytes:
    return (json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _sha_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required custody file missing or symlinked: {path}")
    h=sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _integration_source_identity(repo_root: Path) -> dict[str, str]:
    root=repo_root.resolve()
    identity={}
    for rel in _INTEGRATION_SOURCE_FILES:
        path=(root/rel)
        try:
            path.resolve(strict=True).relative_to(root)
        except Exception as exc:
            raise ValueError(f"integration source escapes repository: {rel}") from exc
        identity[rel]=_sha_file(path)
    return identity


def build_integration_receipt(*, world: UnifiedBiologyWorld, fit_view: UnifiedFitView,
                              controller_truth: UnifiedControllerTruth, repo_root: Path,
                              integration_manifest_path: Path) -> dict[str, object]:
    if fit_view.world_hash != world.world_hash:
        raise ValueError("fit view is not bound to supplied world")
    if controller_truth.world_sha256 != world.world_hash:
        raise ValueError("controller truth is not bound to supplied world")
    root=Path(repo_root).resolve()
    manifest_path=Path(integration_manifest_path)
    if not manifest_path.is_absolute():
        manifest_path=root/manifest_path
    try:
        manifest_path.resolve(strict=True).relative_to(root)
    except Exception as exc:
        raise ValueError("integration manifest must be inside repository") from exc
    manifest_sha=_sha_file(manifest_path)
    source_identity=_integration_source_identity(root)
    fit_sha = fit_view_sha256(fit_view)
    controller_sha = controller_truth_sha256(controller_truth)
    package_identity = {
        "schema": "UNIFIED_SYNTHETIC_FIT_PACKAGE_IDENTITY_V1",
        "world_sha256": world.world_hash,
        "fit_view_sha256": fit_sha,
        "source_commits": _SOURCE_COMMITS,
        "integration_manifest_sha256": manifest_sha,
        "integration_source_sha256": source_identity,
    }
    package_sha = sha256(_canon(package_identity)).hexdigest()
    return {
        "schema": "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V1",
        "source_commits": dict(_SOURCE_COMMITS),
        "integration_manifest_sha256": manifest_sha,
        "integration_source_sha256": source_identity,
        "world_sha256": world.world_hash,
        "fit_view_sha256": fit_sha,
        "controller_truth_sha256": controller_sha,
        "synthetic_package_sha256": package_sha,
        "controller_in_fit_package": False,
        "calibration": {"stat1_50k_physical_row_status": "QUARANTINED_NOT_HARD_AUTHORITY"},
        "authority": dict(_AUTHORITY),
    }


def write_integration_receipt_once(path: Path, receipt: Mapping[str, object]) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise ValueError(f"integration receipt already exists: {target}")
    if not isinstance(receipt, Mapping) or receipt.get("schema") != "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V1":
        raise ValueError("invalid integration receipt")
    authority = receipt.get("authority")
    if not isinstance(authority, Mapping) or any(value is not False for value in authority.values()):
        raise ValueError("authority escalation refused")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canon(receipt))
