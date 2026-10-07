"""Canonical export surface for V5 prefreeze checkpoint binding.

The audited checkpoint implementation is preserved under a private module. This
wrapper extends its explicit transitive runtime-source manifest so both private
implementation blobs are cryptographically covered by every checkpoint/runtime
source digest, then re-exports the implementation API unchanged.
"""
from __future__ import annotations

from . import _inactive_checkpoint_binding_impl_v1 as _impl

_REQUIRED_PRIVATE_RUNTIME_SOURCES = (
    "_inactive_checkpoint_binding_impl_v1.py",
    "_ema_bound_runtime_proof_impl_v1.py",
)

_sources = tuple(_impl.CANONICAL_RUNTIME_SOURCE_FILES)
for _name in _REQUIRED_PRIVATE_RUNTIME_SOURCES:
    if _name not in _sources:
        _sources = _sources + (_name,)
_impl.CANONICAL_RUNTIME_SOURCE_FILES = _sources

for _name in dir(_impl):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_impl, _name)

CANONICAL_RUNTIME_SOURCE_FILES = _impl.CANONICAL_RUNTIME_SOURCE_FILES
