from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import string

from .protocol import ExecutionMode


class LifecycleError(ValueError):
    pass


class RunMode(str, Enum):
    ZERO_UPDATE_QUALIFICATION = ExecutionMode.ZERO_UPDATE_QUALIFICATION.value
    BOUNDED_MUTATION_REHEARSAL = ExecutionMode.BOUNDED_MUTATION_REHEARSAL.value


class RunState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PREPARED = "PREPARED"
    MUTATED = "MUTATED"
    EMA_APPLIED = "EMA_APPLIED"
    CHECKPOINTED = "CHECKPOINTED"
    QUALIFICATION_OUTPUTS_FROZEN = "QUALIFICATION_OUTPUTS_FROZEN"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RunFailureV1:
    experiment_run_id: str
    last_proven_state: RunState
    reason: str


@dataclass
class ExperimentRunV1:
    experiment_run_id: str
    protocol_digest: str
    mode: RunMode
    state: RunState = RunState.NOT_STARTED
    parent_run_id: str | None = None
    retry_reason: str | None = None
    _event_names: list[str] = field(default_factory=list, repr=False)
    _failure: RunFailureV1 | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.experiment_run_id, str) or not self.experiment_run_id.strip():
            raise LifecycleError("experiment_run_id must be explicit")
        if (
            not isinstance(self.protocol_digest, str)
            or len(self.protocol_digest) != 64
            or any(ch not in string.hexdigits for ch in self.protocol_digest)
        ):
            raise LifecycleError("protocol_digest must be a 64-character hexadecimal digest")
        if not isinstance(self.mode, RunMode):
            raise LifecycleError("run mode must be explicit")
        if self.state is not RunState.NOT_STARTED:
            raise LifecycleError("new runs must start at NOT_STARTED")
        if self.parent_run_id is not None and (
            not isinstance(self.parent_run_id, str) or not self.parent_run_id.strip()
        ):
            raise LifecycleError("parent_run_id must be explicit when supplied")
        if self.parent_run_id == self.experiment_run_id:
            raise LifecycleError("child run identity must be distinct from parent run identity")
        if self.parent_run_id is not None and (
            not isinstance(self.retry_reason, str) or not self.retry_reason.strip()
        ):
            raise LifecycleError("retry_reason is required for child runs")

    @property
    def event_names(self) -> tuple[str, ...]:
        return tuple(self._event_names)

    @property
    def failure(self) -> RunFailureV1 | None:
        return self._failure

    def _require_live(self) -> None:
        if self.state in {RunState.FAILED, RunState.VERIFIED}:
            raise LifecycleError(f"run is terminal at {self.state.value}")

    def _check_run_id(self, event_run_id: str | None) -> None:
        if event_run_id is not None and event_run_id != self.experiment_run_id:
            raise LifecycleError("event run identity does not match experiment_run_id")

    def _advance(self, expected: RunState, target: RunState, event: str, event_run_id: str | None = None) -> None:
        self._require_live()
        self._check_run_id(event_run_id)
        if self.state is not expected:
            raise LifecycleError(f"cannot record {event} from {self.state.value}")
        self.state = target
        self._event_names.append(event)

    def prepare(self, *, event_run_id: str | None = None) -> None:
        self._advance(RunState.NOT_STARTED, RunState.PREPARED, "PREPARED", event_run_id)

    def record_mutation(self, *, event_run_id: str | None = None) -> None:
        self._require_live()
        self._check_run_id(event_run_id)
        if self.mode is RunMode.ZERO_UPDATE_QUALIFICATION:
            raise LifecycleError("zero-update qualification cannot record mutation")
        self._advance(RunState.PREPARED, RunState.MUTATED, "MUTATED", event_run_id)

    def record_ema_applied(self, *, event_run_id: str | None = None) -> None:
        if self.mode is RunMode.ZERO_UPDATE_QUALIFICATION:
            raise LifecycleError("EMA is forbidden in zero-update qualification")
        try:
            self._advance(RunState.MUTATED, RunState.EMA_APPLIED, "EMA_APPLIED", event_run_id)
        except LifecycleError as exc:
            if "EMA" not in str(exc):
                raise LifecycleError(f"EMA cannot be applied: {exc}") from exc
            raise

    def record_checkpointed(self, *, event_run_id: str | None = None) -> None:
        if self.mode is RunMode.ZERO_UPDATE_QUALIFICATION:
            raise LifecycleError("mutation checkpoint is forbidden in zero-update qualification")
        self._advance(RunState.EMA_APPLIED, RunState.CHECKPOINTED, "CHECKPOINTED", event_run_id)

    def freeze_outputs(self, *, event_run_id: str | None = None) -> None:
        expected = (
            RunState.PREPARED
            if self.mode is RunMode.ZERO_UPDATE_QUALIFICATION
            else RunState.CHECKPOINTED
        )
        self._advance(
            expected,
            RunState.QUALIFICATION_OUTPUTS_FROZEN,
            "QUALIFICATION_OUTPUTS_FROZEN",
            event_run_id,
        )

    def record_oracle_unblinded(self, *, event_run_id: str | None = None) -> None:
        self._require_live()
        self._check_run_id(event_run_id)
        if self.state is not RunState.QUALIFICATION_OUTPUTS_FROZEN:
            raise LifecycleError("oracle may unblind only after qualification outputs are frozen")
        if "ORACLE_UNBLINDED" in self._event_names:
            raise LifecycleError("oracle unblinding is one-shot for a run")
        self._event_names.append("ORACLE_UNBLINDED")

    def verify(self, *, event_run_id: str | None = None) -> None:
        self._advance(
            RunState.QUALIFICATION_OUTPUTS_FROZEN,
            RunState.VERIFIED,
            "VERIFIED",
            event_run_id,
        )

    def fail(self, reason: str, *, event_run_id: str | None = None) -> RunFailureV1:
        self._require_live()
        self._check_run_id(event_run_id)
        if not isinstance(reason, str) or not reason.strip():
            raise LifecycleError("failure reason must be explicit")
        last = self.state
        failure = RunFailureV1(self.experiment_run_id, last, reason)
        self._failure = failure
        self.state = RunState.FAILED
        self._event_names.append("FAILED")
        return failure

    def retry_as_child(self, child_run_id: str, *, reason: str) -> "ExperimentRunV1":
        if self.state is not RunState.FAILED:
            raise LifecycleError("retry requires a terminal failed parent run")
        if child_run_id == self.experiment_run_id:
            raise LifecycleError("retry child run identity must be distinct from parent run identity")
        return ExperimentRunV1(
            experiment_run_id=child_run_id,
            protocol_digest=self.protocol_digest,
            mode=self.mode,
            parent_run_id=self.experiment_run_id,
            retry_reason=reason,
        )
