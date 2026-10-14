"""Canonical export surface for V5 prefreeze checkpoint binding.

The audited checkpoint implementation is preserved under a private module. This
wrapper is the only normal import route to that implementation and extends its
explicit transitive runtime-source manifest so the package import gate and both
private implementation blobs are cryptographically covered by every checkpoint
runtime-source digest.
"""
from __future__ import annotations

import sea_ad_jepa.v5 as _package

_PRIVATE_FULLNAME = __package__ + "._inactive_checkpoint_binding_impl_v1"
_package._permit_private_runtime_import(_PRIVATE_FULLNAME)
try:
    from . import _inactive_checkpoint_binding_impl_v1 as _impl
finally:
    _package._revoke_private_runtime_import(_PRIVATE_FULLNAME)

_REQUIRED_PRIVATE_RUNTIME_SOURCES = (
    "__init__.py",
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
