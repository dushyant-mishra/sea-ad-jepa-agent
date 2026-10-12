#!/usr/bin/env python3
"""Pre-JAX runtime configuration for the frozen V79 V2_CORE fitter."""
from __future__ import annotations

import os
import re
import sys
from typing import Mapping


class RuntimeRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise RuntimeRefused(f"REFUSED V2_CORE runtime: {msg}")


def _require_or_set_env(name: str, expected: str) -> None:
    current = os.environ.get(name)
    if current is not None and current.strip().lower() != expected.lower():
        _refuse(f"{name} already conflicts with frozen authority: {current!r} != {expected!r}")
    os.environ[name] = expected


def configure_before_jax_import(contract: Mapping) -> int:
    """Set CPU/device/numeric controls from fit contract before any JAX import."""
    if "jax" in sys.modules or "jaxlib" in sys.modules:
        _refuse("JAX was imported before frozen runtime configuration")
    resources = contract.get("resources", {})
    devices = int(resources.get("xla_host_devices", -1))
    chains = int(contract.get("inference", {}).get("chains", -2))
    if devices <= 0 or devices != chains:
        _refuse(f"xla_host_devices={devices} does not equal chains={chains}")

    _require_or_set_env("JAX_PLATFORMS", "cpu")
    _require_or_set_env("JAX_ENABLE_X64", "true")
    _require_or_set_env("JAX_DEFAULT_MATMUL_PRECISION", "highest")

    flags = os.environ.get("XLA_FLAGS", "").strip()
    pat = re.compile(r"(?:^|\s)--xla_force_host_platform_device_count=(\d+)(?:\s|$)")
    found = pat.search(flags)
    if found and int(found.group(1)) != devices:
        _refuse(f"XLA_FLAGS already requests {found.group(1)} host devices, expected {devices}")
    if not found:
        flags = (flags + " " if flags else "") + f"--xla_force_host_platform_device_count={devices}"
    os.environ["XLA_FLAGS"] = flags
    return devices


def validate_imported_jax(contract: Mapping) -> dict:
    import jax

    devices = list(jax.devices())
    want = int(contract["resources"]["xla_host_devices"])
    if len(devices) != want:
        _refuse(f"observed {len(devices)} JAX devices, expected {want}")
    if any(str(d.platform).lower() != "cpu" for d in devices):
        _refuse(f"non-CPU JAX device observed: {[str(d) for d in devices]}")
    if not bool(jax.config.jax_enable_x64):
        _refuse("jax_enable_x64 is not true")
    precision = str(jax.config.jax_default_matmul_precision)
    if precision.lower() != "highest":
        _refuse(f"jax_default_matmul_precision={precision!r}, expected 'highest'")
    return {"jax_device_count": len(devices), "jax_devices": [str(d) for d in devices],
            "jax_platform": "cpu", "jax_enable_x64": True, "jax_default_matmul_precision": "highest"}
