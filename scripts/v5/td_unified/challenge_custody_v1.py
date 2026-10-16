"""Unified Task 4 sealed campaign lifecycle.

This module implements custody mechanics only.  It does not interpret biology,
select targets/representations, promote registry stages, or authorize training.
Final campaigns require a current GREEN preauthority barrier; development
campaigns are permanently non-authorizing.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping

from .task4_authority_barrier_v1 import Task4BarrierStatus, Task4BarrierError, require_task4_preauthority_barrier_green


class Task4ChallengeCustodyError(ValueError):
    pass


def _canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


class CampaignState(str, Enum):
    CAMPAIGN_CREATED = "CAMPAIGN_CREATED"
    DEFINITION_SEALED = "DEFINITION_SEALED"
    REALIZATION_SET_SEALED = "REALIZATION_SET_SEALED"
    EXPOSURE_ACTIVE = "EXPOSURE_ACTIVE"
    ALL_REQUIRED_OUTPUTS_FROZEN = "ALL_REQUIRED_OUTPUTS_FROZEN"
    HIDDEN_MATERIAL_REVEALED = "HIDDEN_MATERIAL_REVEALED"
    REGENERATION_VERIFIED = "REGENERATION_VERIFIED"
    CUSTODY_COMPLETE = "CUSTODY_COMPLETE"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True)
class QualificationCampaign:
    campaign_id: str
    dependencies: Mapping[str, object]
    namespace: str
    promotion_authority: str
    state: CampaignState
    campaign_identity: str
    exposures_consumed: int = 0

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "QUALIFICATION_CAMPAIGN",
            "campaign_id": self.campaign_id,
            "dependencies": dict(self.dependencies),
            "namespace": self.namespace,
            "promotion_authority": self.promotion_authority,
            "state": self.state.value,
            "campaign_identity": self.campaign_identity,
            "exposures_consumed": self.exposures_consumed,
        }


@dataclass(frozen=True)
class SealedChallengeDefinition:
    campaign_identity: str
    family: str
    hidden_spec_commitment: str
    namespace: str

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "SEALED_CHALLENGE_DEFINITION",
            "campaign_identity": self.campaign_identity,
            "family": self.family,
            "hidden_spec_commitment": self.hidden_spec_commitment,
            "namespace": self.namespace,
        }


@dataclass(frozen=True)
class SealedRealizationSet:
    campaign_identity: str
    definition_sha256: str
    realization_ids: tuple[str, ...]
    content_sha256s: tuple[str, ...]
    challenge_classes: tuple[str, ...]
    budget: int
    sealed_root: str

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "SEALED_REALIZATION_SET",
            "campaign_identity": self.campaign_identity,
            "definition_sha256": self.definition_sha256,
            "realization_ids": list(self.realization_ids),
            "content_sha256s": list(self.content_sha256s),
            "challenge_classes": list(self.challenge_classes),
            "budget": self.budget,
            "sealed_root": self.sealed_root,
        }


def _campaign_identity(campaign_id: str, dependencies: Mapping[str, object], namespace: str) -> str:
    return _sha({"campaign_id": campaign_id, "dependencies": dict(dependencies), "namespace": namespace})


def create_campaign(campaign_id: str, dependencies: Mapping[str, object], *, barrier_status: Task4BarrierStatus | None, namespace: str) -> QualificationCampaign:
    if type(campaign_id) is not str or not campaign_id:
        raise Task4ChallengeCustodyError("campaign_id must be non-empty")
    if namespace not in {"DEVELOPMENT", "FINAL"}:
        raise Task4ChallengeCustodyError("unknown campaign namespace")
    if namespace == "FINAL":
        if barrier_status is None:
            raise Task4ChallengeCustodyError("final campaign requires GREEN C1-C9 barrier")
        try:
            require_task4_preauthority_barrier_green(barrier_status)
        except Task4BarrierError as exc:
            raise Task4ChallengeCustodyError(str(exc)) from exc
        promotion_authority = "CUSTODY_ONLY"
    else:
        promotion_authority = "NONE"
    identity = _campaign_identity(campaign_id, dependencies, namespace)
    return QualificationCampaign(campaign_id, dict(dependencies), namespace, promotion_authority, CampaignState.CAMPAIGN_CREATED, identity)


def assert_same_campaign_identity(campaign: QualificationCampaign, campaign_id: str, dependencies: Mapping[str, object]) -> None:
    expected = _campaign_identity(campaign_id, dependencies, campaign.namespace)
    if expected != campaign.campaign_identity:
        raise Task4ChallengeCustodyError("campaign ID/dependency mutation creates a new campaign identity")


def seal_definition(campaign: QualificationCampaign, *, family: str, hidden_spec: bytes):
    if campaign.state is not CampaignState.CAMPAIGN_CREATED:
        raise Task4ChallengeCustodyError("challenge definition can seal only from CAMPAIGN_CREATED")
    if type(hidden_spec) is not bytes or not hidden_spec:
        raise Task4ChallengeCustodyError("hidden specification must be non-empty bytes")
    if type(family) is not str or not family:
        raise Task4ChallengeCustodyError("challenge family must be non-empty")
    commitment = hashlib.sha256(hidden_spec).hexdigest()
    definition = SealedChallengeDefinition(campaign.campaign_identity, family, commitment, campaign.namespace)
    return replace(campaign, state=CampaignState.DEFINITION_SEALED), definition


def _validated_rows(rows: Iterable[Mapping[str, object]], budget: int):
    seq = list(rows)
    if type(budget) is not int or budget <= 0 or len(seq) != budget:
        raise Task4ChallengeCustodyError("realization inventory must exactly equal frozen budget")
    ids, digests, classes = [], [], []
    for row in seq:
        if set(row) != {"realization_id", "content_sha256", "challenge_class"}:
            raise Task4ChallengeCustodyError("realization row has unknown or missing fields")
        rid, digest, cls = row["realization_id"], row["content_sha256"], row["challenge_class"]
        if type(rid) is not str or not rid or rid in ids:
            raise Task4ChallengeCustodyError("realization IDs must be unique non-empty strings")
        if type(digest) is not str or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise Task4ChallengeCustodyError("realization content digest must be exact lowercase SHA-256")
        if digest in digests:
            raise Task4ChallengeCustodyError("duplicate realization content digest forbidden")
        if type(cls) is not str or not cls:
            raise Task4ChallengeCustodyError("challenge class must be non-empty")
        ids.append(rid); digests.append(digest); classes.append(cls)
    return tuple(ids), tuple(digests), tuple(classes)


def seal_realization_set(campaign: QualificationCampaign, definition: SealedChallengeDefinition, rows: Iterable[Mapping[str, object]], *, budget: int):
    if campaign.state is not CampaignState.DEFINITION_SEALED:
        raise Task4ChallengeCustodyError("realization set can seal only after definition")
    if definition.campaign_identity != campaign.campaign_identity:
        raise Task4ChallengeCustodyError("challenge definition belongs to another campaign")
    ids, digests, classes = _validated_rows(rows, budget)
    definition_sha = _sha(definition.to_payload())
    root = _sha({"campaign_identity": campaign.campaign_identity, "definition_sha256": definition_sha, "realization_ids": ids, "content_sha256s": digests, "challenge_classes": classes, "budget": budget})
    sealed = SealedRealizationSet(campaign.campaign_identity, definition_sha, ids, digests, classes, budget, root)
    return replace(campaign, state=CampaignState.REALIZATION_SET_SEALED), sealed
