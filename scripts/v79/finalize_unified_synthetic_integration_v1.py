from __future__ import annotations

from hashlib import sha1, sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys
from typing import Mapping

from .unified_synthetic_integration_v1 import (
    CALIBRATION_BOUNDARY,
    PERTURBATION_ARM_SEMANTICS,
    UnifiedBiologyWorld,
    validate_integration_manifest,
)
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
    "scripts/v79/v79_hierarchical_biology.py",
    "scripts/v79/v79_observation_operator.py",
    "scripts/v79/v79_rare_biology_generator_v1.py",
)
_FROZEN_IMPORTED_BLOB_SHA1 = {
    "scripts/v79/v79_hierarchical_biology.py": "08d74b02fb609a1e923f2adc906c2bf68b821b26",
    "scripts/v79/v79_observation_operator.py": "6ed165d33ea31616875064f0c7d95554a6a6abe8",
    "scripts/v79/v79_rare_biology_generator_v1.py": "2a2f0b2f5b48ed7b9cfd81a74ab7ec514053309f",
}
_RUNTIME_ENVIRONMENT = {
    "python": "3.11.9",
    "numpy": "2.3.5",
    "pandas": "2.2.3",
    "scipy": "1.17.0",
    "pytest": "9.0.2",
}


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


def _git_blob_sha1(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required custody file missing or symlinked: {path}")
    raw=path.read_bytes()
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _runtime_environment() -> dict[str, str]:
    observed = {
        "python": ".".join(str(x) for x in sys.version_info[:3]),
        "numpy": version("numpy"),
        "pandas": version("pandas"),
        "scipy": version("scipy"),
        "pytest": version("pytest"),
    }
    if observed != _RUNTIME_ENVIRONMENT:
        raise ValueError(f"runtime environment drift detected: {observed}")
    return observed


def _integration_source_identity(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    root=repo_root.resolve()
    identity={}
    frozen_blob_identity={}
    for rel in _INTEGRATION_SOURCE_FILES:
        path=(root/rel)
        try:
            path.resolve(strict=True).relative_to(root)
        except Exception as exc:
            raise ValueError(f"integration source escapes repository: {rel}") from exc
        identity[rel]=_sha_file(path)
        if rel in _FROZEN_IMPORTED_BLOB_SHA1:
            observed=_git_blob_sha1(path)
            expected=_FROZEN_IMPORTED_BLOB_SHA1[rel]
            if observed != expected:
                raise ValueError(f"frozen imported dependency drift detected: {rel}")
            frozen_blob_identity[rel]=observed
    if frozen_blob_identity != _FROZEN_IMPORTED_BLOB_SHA1:
        raise ValueError("frozen imported dependency coverage differs")
    return identity, frozen_blob_identity


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
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_integration_manifest(manifest)
    manifest_sha=_sha_file(manifest_path)
    source_identity, frozen_blob_identity=_integration_source_identity(root)
    runtime_environment=_runtime_environment()
    fit_sha = fit_view_sha256(fit_view)
    controller_sha = controller_truth_sha256(controller_truth)
    package_identity = {
        "schema": "UNIFIED_SYNTHETIC_FIT_PACKAGE_IDENTITY_V2",
        "world_sha256": world.world_hash,
        "fit_view_sha256": fit_sha,
        "source_commits": _SOURCE_COMMITS,
        "integration_manifest_sha256": manifest_sha,
        "integration_source_sha256": source_identity,
        "frozen_import_git_blob_sha1": frozen_blob_identity,
        "runtime_environment": runtime_environment,
        "perturbation_arm_semantics": PERTURBATION_ARM_SEMANTICS,
        "calibration": CALIBRATION_BOUNDARY,
    }
    package_sha = sha256(_canon(package_identity)).hexdigest()
    return {
        "schema": "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2",
        "source_commits": dict(_SOURCE_COMMITS),
        "integration_manifest_sha256": manifest_sha,
        "integration_source_sha256": source_identity,
        "frozen_import_git_blob_sha1": frozen_blob_identity,
        "runtime_environment": runtime_environment,
        "perturbation_arm_semantics": dict(PERTURBATION_ARM_SEMANTICS),
        "world_sha256": world.world_hash,
        "fit_view_sha256": fit_sha,
        "controller_truth_sha256": controller_sha,
        "synthetic_package_sha256": package_sha,
        "controller_in_fit_package": False,
        "calibration": dict(CALIBRATION_BOUNDARY),
        "authority": dict(_AUTHORITY),
    }


def write_integration_receipt_once(path: Path, receipt: Mapping[str, object]) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise ValueError(f"integration receipt already exists: {target}")
    if not isinstance(receipt, Mapping) or receipt.get("schema") != "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2":
        raise ValueError("invalid integration receipt")
    authority = receipt.get("authority")
    if not isinstance(authority, Mapping) or any(value is not False for value in authority.values()):
        raise ValueError("authority escalation refused")
    if receipt.get("calibration") != CALIBRATION_BOUNDARY:
        raise ValueError("receipt calibration boundary differs")
    if receipt.get("perturbation_arm_semantics") != PERTURBATION_ARM_SEMANTICS:
        raise ValueError("receipt perturbation semantics differ")
    if receipt.get("runtime_environment") != _RUNTIME_ENVIRONMENT:
        raise ValueError("receipt runtime environment differs")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canon(receipt))
