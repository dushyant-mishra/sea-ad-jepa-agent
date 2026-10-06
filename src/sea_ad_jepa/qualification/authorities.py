from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .protocol import ExecutionMode, QualificationProtocolV1


class MutationStatus(str, Enum):
    MUTATION_NOT_AUTHORIZED = "MUTATION_NOT_AUTHORIZED"


class ExperimentScope(str, Enum):
    SYNTHETIC_PIPELINE_VALIDITY = "SYNTHETIC_PIPELINE_VALIDITY"
    REAL_RNA_PREFREEZE_ONLY = "REAL_RNA_PREFREEZE_ONLY"


class ClaimLevel(str, Enum):
    NO_CLAIM = "NO_CLAIM"
    SYNTHETIC_PIPELINE_VALIDITY = "SYNTHETIC_PIPELINE_VALIDITY"
    RNA_REPRESENTATION = "RNA_REPRESENTATION"
    TRANSFERABLE_BIOLOGICAL_STATE = "TRANSFERABLE_BIOLOGICAL_STATE"
    REGULATORY_SUPPORT = "REGULATORY_SUPPORT"
    CAUSAL_PERTURBATIONAL_PREDICTION = "CAUSAL_PERTURBATIONAL_PREDICTION"


_CLAIM_RANK = {
    ClaimLevel.NO_CLAIM: 0,
    ClaimLevel.SYNTHETIC_PIPELINE_VALIDITY: 0,
    ClaimLevel.RNA_REPRESENTATION: 1,
    ClaimLevel.TRANSFERABLE_BIOLOGICAL_STATE: 2,
    ClaimLevel.REGULATORY_SUPPORT: 3,
    ClaimLevel.CAUSAL_PERTURBATIONAL_PREDICTION: 4,
}


@dataclass(frozen=True)
class ScientificExperimentAuthorityV1:
    protocol_digest: str
    scope: ExperimentScope
    evaluation_authorized: bool

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_digest, str) or len(self.protocol_digest) != 64:
            raise ValueError("protocol_digest must be a 64-character digest")
        if not isinstance(self.scope, ExperimentScope):
            raise ValueError("experiment scope must be explicit")
        if not isinstance(self.evaluation_authorized, bool):
            raise ValueError("evaluation_authorized must be explicit bool")
        if self.scope is ExperimentScope.REAL_RNA_PREFREEZE_ONLY and self.evaluation_authorized:
            raise ValueError("Stage A real-RNA execution is not authorized by this slice")


@dataclass(frozen=True)
class MutationAuthorityV1:
    status: MutationStatus

    def __post_init__(self) -> None:
        if not isinstance(self.status, MutationStatus):
            raise ValueError("mutation status is invalid; V1 supports only MUTATION_NOT_AUTHORIZED")
        if self.status is not MutationStatus.MUTATION_NOT_AUTHORIZED:
            raise ValueError("mutation is not authorized in shared qualification V1")


@dataclass(frozen=True)
class ClaimAuthorityV1:
    maximum_claim_level: ClaimLevel

    def __post_init__(self) -> None:
        if not isinstance(self.maximum_claim_level, ClaimLevel):
            raise ValueError("maximum claim level must be explicit")


@dataclass(frozen=True)
class AuthorityBundleV1:
    scientific: ScientificExperimentAuthorityV1
    mutation: MutationAuthorityV1
    claim: ClaimAuthorityV1

    def __post_init__(self) -> None:
        if not isinstance(self.scientific, ScientificExperimentAuthorityV1):
            raise ValueError("scientific authority is invalid")
        if not isinstance(self.mutation, MutationAuthorityV1):
            raise ValueError("mutation authority is invalid")
        if not isinstance(self.claim, ClaimAuthorityV1):
            raise ValueError("claim authority is invalid")

    def validate_against(self, protocol: QualificationProtocolV1) -> None:
        protocol.validate()
        if self.scientific.protocol_digest != protocol.digest():
            raise ValueError("scientific authority protocol digest mismatch")
        if self.mutation.status is not MutationStatus.MUTATION_NOT_AUTHORIZED:
            raise ValueError("mutation authority exceeds V1")
        if protocol.execution_mode is ExecutionMode.BOUNDED_MUTATION_REHEARSAL:
            raise ValueError("mutation rehearsal has no compatible mutation authority in V1")

        if self.scientific.scope is ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY:
            if self.claim.maximum_claim_level not in {
                ClaimLevel.NO_CLAIM,
                ClaimLevel.SYNTHETIC_PIPELINE_VALIDITY,
            }:
                raise ValueError("synthetic evidence cannot mint real biological claim authority")
        else:
            protocol_ceiling = ClaimLevel(protocol.claim_ceiling)
            if _CLAIM_RANK[self.claim.maximum_claim_level] > _CLAIM_RANK[protocol_ceiling]:
                raise ValueError("claim ceiling exceeds protocol claim ceiling")
