from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import string

from .canonical import canonical_digest
from .lifecycle import ExperimentRunV1, RunState


def _digest(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


class ChallengeStatus(str, Enum):
    PROSPECTIVE_SEALED_CHALLENGE = "PROSPECTIVE_SEALED_CHALLENGE"
    DEVELOPMENT_CALIBRATION = "DEVELOPMENT_CALIBRATION"


@dataclass(frozen=True)
class SyntheticOracleTruthV1:
    realization_id: str
    truth_payload: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.realization_id, str) or not self.realization_id.strip():
            raise ValueError("oracle realization_id must be explicit")
        if not isinstance(self.truth_payload, tuple):
            raise ValueError("oracle truth payload must be an immutable tuple")
        if not all(
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            and item[0]
            for item in self.truth_payload
        ):
            raise ValueError("oracle truth payload entries must be named pairs")
        canonical_digest(self.truth_payload)

    def digest(self) -> str:
        return canonical_digest(
            {"realization_id": self.realization_id, "truth_payload": self.truth_payload}
        )


@dataclass(frozen=True)
class FrozenQualificationOutputsV1:
    run_id: str
    output_digest: str
    provenance_receipt_digest: str
    synthetic_realization_id: str | None = None
    challenge_partition: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be explicit")
        _digest(self.output_digest, "output_digest")
        _digest(self.provenance_receipt_digest, "provenance_receipt_digest")
        if self.synthetic_realization_id is not None and (
            not isinstance(self.synthetic_realization_id, str)
            or not self.synthetic_realization_id.strip()
        ):
            raise ValueError("synthetic_realization_id must be explicit when supplied")
        if self.synthetic_realization_id is None:
            if self.challenge_partition is not None:
                raise ValueError("challenge_partition requires synthetic realization identity")
        elif self.challenge_partition not in {status.value for status in ChallengeStatus}:
            raise ValueError("synthetic frozen outputs require a recognized challenge_partition")


@dataclass(frozen=True)
class OracleUnblindingReceiptV1:
    run_id: str
    output_digest: str
    oracle_digest: str
    challenge_status: ChallengeStatus
    retune_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be explicit")
        _digest(self.output_digest, "output_digest")
        _digest(self.oracle_digest, "oracle_digest")
        if not isinstance(self.challenge_status, ChallengeStatus):
            raise ValueError("challenge_status must be explicit")
        if self.retune_reason is not None and (
            not isinstance(self.retune_reason, str) or not self.retune_reason.strip()
        ):
            raise ValueError("retune_reason must be explicit when supplied")
        if self.challenge_status is ChallengeStatus.PROSPECTIVE_SEALED_CHALLENGE and self.retune_reason is not None:
            raise ValueError("prospective sealed challenge cannot carry a retune reason")


def unblind_oracle(
    run: ExperimentRunV1,
    frozen_outputs: FrozenQualificationOutputsV1,
    oracle: SyntheticOracleTruthV1,
) -> OracleUnblindingReceiptV1:
    if run.state is not RunState.QUALIFICATION_OUTPUTS_FROZEN:
        raise ValueError("ordinary qualification outputs must be frozen before oracle unblinding")
    if frozen_outputs.run_id != run.experiment_run_id:
        raise ValueError("oracle unblinding run identity does not match frozen outputs")
    if frozen_outputs.synthetic_realization_id is None:
        raise ValueError("oracle unblinding requires frozen synthetic realization identity")
    if frozen_outputs.synthetic_realization_id != oracle.realization_id:
        raise ValueError("oracle realization does not match frozen output realization")
    if frozen_outputs.challenge_partition is None:
        raise ValueError("oracle unblinding requires frozen challenge partition identity")
    challenge_status = ChallengeStatus(frozen_outputs.challenge_partition)
    run.record_oracle_unblinded(event_run_id=frozen_outputs.run_id)
    return OracleUnblindingReceiptV1(
        run_id=run.experiment_run_id,
        output_digest=frozen_outputs.output_digest,
        oracle_digest=oracle.digest(),
        challenge_status=challenge_status,
    )


def mark_post_unblinding_retune(
    receipt: OracleUnblindingReceiptV1,
    *,
    reason: str,
) -> OracleUnblindingReceiptV1:
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("retune reason must be explicit")
    return replace(
        receipt,
        challenge_status=ChallengeStatus.DEVELOPMENT_CALIBRATION,
        retune_reason=reason,
    )
