#!/usr/bin/env python3
"""Fit-side runtime-environment validation without importing world/truth code."""
from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import re
import sys
from pathlib import Path
from typing import Mapping

ENV_LOCK_REL = "results/v79/v2_core_qualification/inputs/V79_BAYES_ENV_PIP_FREEZE.txt"
ENV_LOCK_SHA256 = "5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782"


class RuntimeLockRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise RuntimeLockRefused(f"REFUSED V2_CORE runtime: {msg}")


def _canon_pkg(name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(name).strip().lower())


def load_locked_versions(root: Path) -> dict[str, str]:
    path = Path(root) / ENV_LOCK_REL
    if not path.is_file():
        _refuse("environment lock missing")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ENV_LOCK_SHA256:
        _refuse("environment lock hash mismatch")
    out: dict[str, str] = {}
    for raw_line in raw.decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "==" not in line:
            _refuse(f"unsupported lock line {line!r}")
        name, version = line.split("==", 1)
        key = _canon_pkg(name)
        if not key or not version or key in out:
            _refuse(f"malformed/duplicate package {line!r}")
        out[key] = version
    if not out:
        _refuse("environment lock is empty")
    return out


def installed_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for d in importlib.metadata.distributions():
        name = d.metadata.get("Name")
        if name:
            out[_canon_pkg(name)] = str(d.version)
    return out


def validate_runtime(root: Path, *, observed: Mapping[str, str] | None = None,
                     require_windows: bool = True, required_cpu_devices: int | None = None) -> dict:
    locked = load_locked_versions(root)
    got_raw = dict(observed) if observed is not None else installed_versions()
    got = {_canon_pkg(k): str(v) for k, v in got_raw.items()}
    missing = sorted(k for k in locked if k not in got)
    mismatch = sorted((k, locked[k], got.get(k)) for k in locked if k in got and got[k] != locked[k])
    if missing or mismatch:
        _refuse(f"package lock mismatch; missing={missing}, mismatch={mismatch}")
    system = platform.system()
    if require_windows and system.lower() != "windows":
        _refuse(f"locked qualification/benchmark execution is Windows-only; host={system}")
    jax_devices = []
    if required_cpu_devices is not None:
        try:
            import jax
            jax_devices = [str(x) for x in jax.devices("cpu")]
        except Exception as exc:
            _refuse(f"cannot enumerate JAX CPU devices: {exc}")
        if len(jax_devices) != int(required_cpu_devices):
            _refuse(f"expected {int(required_cpu_devices)} JAX CPU devices, observed {len(jax_devices)}")
    return {
        "schema": "V79_V2_CORE_FIT_RUNTIME_RECEIPT_V1",
        "environment_lock_sha256": ENV_LOCK_SHA256,
        "matched_packages": len(locked),
        "platform_system": system,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "jax_cpu_devices": jax_devices,
    }
