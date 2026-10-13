from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import td_test_qualification_package_v1 as P


class RelationalAdapterError(ValueError):
    pass


MANDATORY_RELATIONAL_CAPABILITIES = (
    'REL_BROAD_MESO_POSITIVE',
    'REL_FINE_RECURRENT_POSITIVE',
    'REL_RARE_LOCAL_ISLAND_POSITIVE',
    'REL_MULTI_ISLAND_POSITIVE',
    'REL_DONOR_RESTRICTED_POSITIVE',
    'REL_SOURCE_VISIBILITY_STRESS',
    'REL_TECHNICAL_TWIN_NEGATIVE',
    'REL_NULL_NEGATIVE',
    'REL_UNDERPOWERED_POSITIVE',
)

_EXECUTOR_INPUT_FIELDS = frozenset({
    'source','panel_id','z_distances','x_distances','y_distances','donor_ids','operator_ids','global_rows',
    'focal_mask','neighbor_pool_mask','null_y_identity_maps','min_focal_anchors_per_donor',
})
_PAYLOAD_FIELDS = frozenset({'authenticated_fit_view_sha256','executor_input'})
_AUTHORITY = {
    'synthetic_world_generation_authorized': False,
    'synthetic_world_regeneration_authorized': False,
    'real_execution_authorized': False,
    'target_selection_authorized': False,
    'td60_authorized': False,
    'stage4_authorized': False,
    'training_authorized': False,
}


@dataclass(frozen=True)
class RelationalQualificationAdapterReceipt:
    status: str
    package_id: str
    package_sha256: str
    fit_inputs: dict[str, dict]
    controller_challenges: dict[str, dict]
    missing_capabilities: tuple[str, ...]
    authority: dict[str, bool]


def build_relational_qualification_adapter(
    package: P.ValidatedExternalPackage,
    challenge_payloads: Mapping[str, Mapping],
) -> RelationalQualificationAdapterReceipt:
    if not isinstance(package, P.ValidatedExternalPackage):
        raise RelationalAdapterError('package must be a ValidatedExternalPackage')
    if not isinstance(challenge_payloads, Mapping):
        raise RelationalAdapterError('challenge_payloads must be a mapping')

    missing=tuple(cap for cap in MANDATORY_RELATIONAL_CAPABILITIES if cap not in package.capabilities)
    if missing:
        return RelationalQualificationAdapterReceipt(
            status='INCOMPLETE', package_id=package.package_id, package_sha256=package.package_sha256,
            fit_inputs={}, controller_challenges={}, missing_capabilities=missing, authority=dict(_AUTHORITY),
        )

    challenge_ids=[]
    for cap in MANDATORY_RELATIONAL_CAPABILITIES:
        rec=package.capabilities[cap]
        if not isinstance(rec, Mapping):
            raise RelationalAdapterError(f'invalid capability record: {cap}')
        if rec.get('capability_id') != cap:
            raise RelationalAdapterError(f'capability_id mismatch: {cap}')
        cid=rec.get('challenge_id')
        if not isinstance(cid,str) or not cid:
            raise RelationalAdapterError(f'challenge_id missing: {cap}')
        challenge_ids.append(cid)
    if len(challenge_ids) != len(set(challenge_ids)):
        raise RelationalAdapterError('mandatory capabilities must bind distinct opaque challenge IDs')
    if set(challenge_payloads) != set(challenge_ids):
        raise RelationalAdapterError('challenge_payloads must cover the exact mandatory challenge set')

    fit_inputs={}
    controller={}
    for cap,cid in zip(MANDATORY_RELATIONAL_CAPABILITIES,challenge_ids):
        payload=challenge_payloads[cid]
        if not isinstance(payload, Mapping) or set(payload) != _PAYLOAD_FIELDS:
            raise RelationalAdapterError('each challenge payload must contain exactly authenticated_fit_view_sha256 and executor_input')
        expected_sha=package.fit_views.get(cid)
        actual_sha=payload.get('authenticated_fit_view_sha256')
        if actual_sha != expected_sha:
            raise RelationalAdapterError(f'fit-view SHA-256 mismatch: {cid}')
        inp=payload.get('executor_input')
        if not isinstance(inp, Mapping) or set(inp) != _EXECUTOR_INPUT_FIELDS:
            raise RelationalAdapterError(f'executor_input fields must exactly match the blinded TD gate schema: {cid}')
        fit=dict(inp)
        fit['profile_id']=cid
        fit_inputs[cid]=fit
        controller[cid]={
            'capability_id': cap,
            'semantic_class': package.capabilities[cap].get('semantic_class'),
            'challenge_id': cid,
            'fit_view_sha256': expected_sha,
        }

    return RelationalQualificationAdapterReceipt(
        status='READY', package_id=package.package_id, package_sha256=package.package_sha256,
        fit_inputs=fit_inputs, controller_challenges=controller, missing_capabilities=tuple(), authority=dict(_AUTHORITY),
    )
