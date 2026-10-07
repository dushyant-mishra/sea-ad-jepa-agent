"""Physical V77-adapter binding for canonical V5 ZERO_UPDATE execution.

This module owns no model, optimizer, EMA, checkpoint, or mutation mechanics. It
binds the joined V77 batch to the exact adapter source file and then delegates to
``v77_zero_update`` unchanged.
"""
from __future__ import annotations

import hashlib
from importlib import import_module
from pathlib import Path

from .physical_binding_v2 import PhysicalRowValueBindingV2
from .pipeline import QualificationBatchV1
from .receipts import BoundAdapterQSafetyProofV1
from . import v77_zero_update as _canonical


V77_ADAPTER_MODULE = "scripts.v77.v77_synthetic_batch_adapter"


def canonical_v77_adapter_source_sha256() -> str:
    """Hash the exact physical V77 adapter source imported by this execution."""
    module = import_module(V77_ADAPTER_MODULE)
    filename = getattr(module, "__file__", None)
    if not isinstance(filename, str) or not filename:
        raise RuntimeError("canonical V77 adapter has no physical source file")
    path = Path(filename)
    if path.suffix == ".pyc":
        source = path.with_suffix(".py")
        if source.exists():
            path = source
    if not path.is_file():
        raise RuntimeError("canonical V77 adapter source is not a physical file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_v5_runtime_source_sha256() -> str:
    return _canonical.canonical_v5_runtime_source_sha256()


def canonical_v5_runtime_source_manifest() -> tuple[tuple[str, str], ...]:
    return _canonical.canonical_v5_runtime_source_manifest()


def run_canonical_v5_zero_update(
    batch: QualificationBatchV1,
    *,
    physical_bindings: tuple[PhysicalRowValueBindingV2, ...],
    q_safety_proof: BoundAdapterQSafetyProofV1,
    runtime_source_sha256: str,
    init_seed: int,
) -> dict[str, object]:
    """Bind adapter source identity and physical provenance, then execute ZERO_UPDATE."""
    actual_adapter_digest = canonical_v77_adapter_source_sha256()
    if batch.adapter_digest != actual_adapter_digest:
        raise ValueError("adapter source digest does not match the canonical V77 adapter source")

    receipt = _canonical.run_canonical_v5_zero_update(
        batch,
        physical_bindings=physical_bindings,
        q_safety_proof=q_safety_proof,
        runtime_source_sha256=runtime_source_sha256,
        init_seed=init_seed,
    )
    if receipt.get("training_authorized") is not False:
        raise RuntimeError("canonical ZERO_UPDATE unexpectedly authorized training")
    if receipt.get("optimizer_step_performed") is not False or receipt.get("ema_performed") is not False:
        raise RuntimeError("canonical ZERO_UPDATE unexpectedly mutated runtime state")
    return {**receipt, "adapter_source_sha256": actual_adapter_digest}
