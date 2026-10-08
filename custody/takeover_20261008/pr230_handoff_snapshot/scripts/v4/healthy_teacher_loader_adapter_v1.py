"""Portable adapter around the exact hash-bound historical production loader source.

The healthy-teacher contract binds the historical loader source SHA.  Rather
than copy or edit that source to remove its Windows paths, this adapter verifies
the exact source bytes, imports them, and injects the current machine roots
before ProductionTrainLoader is instantiated.  The loader's own pinned manifest
verification remains active.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

FROZEN_LOADER_SOURCE_SHA256 = (
    "267fa42a5fa6f8b5f8199c68add1ffe0c8b49142095b7d980d1af27a8a31154a"
)
FROZEN_LOADER_MANIFEST_SHA256 = (
    "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"
)
FROZEN_LOADER_SEMANTIC_ROOT = (
    "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_production_loader(
    *,
    loader_source: Path,
    project_root: Path,
    authority_root: Path,
) -> Any:
    loader_source = Path(loader_source).resolve()
    if sha256(loader_source) != FROZEN_LOADER_SOURCE_SHA256:
        raise RuntimeError("production loader source SHA-256 mismatch")
    pinned = loader_source.with_name("production_loader_manifest.json")
    if not pinned.is_file() or sha256(pinned) != FROZEN_LOADER_MANIFEST_SHA256:
        raise RuntimeError("production loader pinned manifest missing or changed")

    spec = importlib.util.spec_from_file_location(
        "_jepa_frozen_production_train_loader", loader_source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen production loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    project_root = Path(project_root).resolve()
    authority_root = Path(authority_root).resolve()
    module.ROOT = project_root
    module.AUTH = authority_root
    module.CACHE = project_root / "data/cache/stage81a3r_corrected_real_train"
    module.RESULTS = project_root / "results/v4"
    module.AUTH_RESULTS = authority_root / "results/v4"

    loader = module.ProductionTrainLoader()
    manifest = loader.manifest()
    if manifest.get("semantic_hash") != FROZEN_LOADER_SEMANTIC_ROOT:
        raise RuntimeError("production loader semantic root mismatch")
    if int(manifest.get("address_count", -1)) != 41_238:
        raise RuntimeError("production loader address count mismatch")
    return loader
