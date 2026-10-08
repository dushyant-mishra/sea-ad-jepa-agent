"""Canonical export surface for presentation-normalized V5 EMA runtime proof.

The audited implementation is preserved under a private module. This public
surface is the only normal import route, retires the legacy dictionary
persistence route, and requires noninitial continuation to use the canonical V2
physical continuation manifest.
"""
from __future__ import annotations

import sea_ad_jepa.v5 as _package

_PRIVATE_FULLNAME = __package__ + "._ema_bound_runtime_proof_impl_v1"
_package._permit_private_runtime_import(_PRIVATE_FULLNAME)
try:
    from . import _ema_bound_runtime_proof_impl_v1 as _impl
finally:
    _package._revoke_private_runtime_import(_PRIVATE_FULLNAME)

_BLOCKED = {"persist_and_verify_presentation_ema_checkpoint"}

for _name in dir(_impl):
    if _name.startswith("__") or _name in _BLOCKED:
        continue
    globals()[_name] = getattr(_impl, _name)

for _name in _BLOCKED:
    if hasattr(_impl, _name):
        delattr(_impl, _name)


def issue_presentation_ema_bound_authority_from_checkpoint(
    modules,
    parent,
    *,
    premise_state_path,
    half_life_presentations,
    presentation_unit_id=PRESENTATION_UNIT_SUCCESSFUL_BASE_CELLS,
    scaler=None,
    persisted_ema_proof=None,
):
    """Genesis-only issuer; noninitial continuation must use the V2 manifest path."""
    if parent.reference_checkpoint.next_update_index > 0:
        raise RuntimeError(
            "noninitial presentation EMA continuation requires "
            "ema_persisted_continuation_v2"
        )
    if persisted_ema_proof is not None:
        raise RuntimeError(
            "legacy dictionary EMA persistence is retired; use "
            "ema_persisted_continuation_v2"
        )
    return _impl.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=premise_state_path,
        half_life_presentations=half_life_presentations,
        presentation_unit_id=presentation_unit_id,
        scaler=scaler,
        persisted_ema_proof=None,
    )

assert "persist_and_verify_presentation_ema_checkpoint" not in globals()
