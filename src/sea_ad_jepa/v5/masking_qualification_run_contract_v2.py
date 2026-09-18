"""Prospective canonical masking-qualification run contract, successor to V1.

V1 carried a single generic ``runner_source_sha256``. In practice two different
pieces of code are involved and they are not interchangeable:

``canonical_reference_source_sha256``
    ``full104_masking_qualification_runner_v1.py`` -- the in-memory canonical
    reference implementation. It defines correct behaviour and is what parity
    tests compare against. It does not execute FULL104.

``full104_streaming_execution_source_sha256``
    ``full104_masking_streaming_executor_v1.py`` -- the code that actually
    performs the FULL104 run, because a dense 17,186-address core over 4,553,407
    cells is ~313 GB and cannot be materialized.

Binding the canonical reference digest into the execution role would freeze a
contract that names code which never ran. V2 makes the two roles explicit,
requires every root to be distinct, and provides
:meth:`bind_execution_sources`, which compares each stored digest against the
live digest of the file that actually occupies that role -- so a swap fails
rather than silently freezing the wrong provenance.

This is a provenance repair. The scientific runner is unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

FREEZE_POLICY_ID = "FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1"
STRICT_SUPPORT_POLICY_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"

APPROVED_EXECUTION_SOURCE_ROLE_IDS: Tuple[str, ...] = (
    "FULL104_STREAMING_EXECUTION_V1",
)
APPROVED_TERMINAL_UNIVERSE_IDS: Tuple[str, ...] = (
    "FULL_COMMON_CORE_17186_V1",
)

#: Repository-relative paths that define each execution-source role.
CANONICAL_REFERENCE_RELPATH = (
    "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py"
)
FULL104_STREAMING_EXECUTION_RELPATH = (
    "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationRunContractV2:
    authority_id: str

    # scientific design and parameters
    qualification_design_authority_sha256: str
    qualification_parameters_authority_sha256: str

    # substrate and support
    full104_block_manifest_sha256: str
    observation_state_sha256: str
    support_estimability_authority_sha256: str
    census_authority_sha256: str

    # budget and burden
    target_evidence_budget_authority_sha256: str
    burden_ladder_authority_sha256: str

    # population geometry
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    precision_authority_sha256: str
    rng_replay_authority_sha256: str

    # machine binding
    machine_worktree_checkpoint_sha256: str

    # execution sources -- distinct roles, never interchangeable
    canonical_reference_source_sha256: str
    full104_streaming_execution_source_sha256: str
    execution_source_role_id: str

    freeze_policy_id: str
    support_state_policy_id: str
    terminal_universe_id: str
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def _roots(self) -> Tuple[Tuple[str, str], ...]:
        return (
            ("qualification_design_authority_sha256", self.qualification_design_authority_sha256),
            ("qualification_parameters_authority_sha256", self.qualification_parameters_authority_sha256),
            ("full104_block_manifest_sha256", self.full104_block_manifest_sha256),
            ("observation_state_sha256", self.observation_state_sha256),
            ("support_estimability_authority_sha256", self.support_estimability_authority_sha256),
            ("census_authority_sha256", self.census_authority_sha256),
            ("target_evidence_budget_authority_sha256", self.target_evidence_budget_authority_sha256),
            ("burden_ladder_authority_sha256", self.burden_ladder_authority_sha256),
            ("outer_split_authority_sha256", self.outer_split_authority_sha256),
            ("target_panel_authority_sha256", self.target_panel_authority_sha256),
            ("precision_authority_sha256", self.precision_authority_sha256),
            ("rng_replay_authority_sha256", self.rng_replay_authority_sha256),
            ("machine_worktree_checkpoint_sha256", self.machine_worktree_checkpoint_sha256),
            ("canonical_reference_source_sha256", self.canonical_reference_source_sha256),
            ("full104_streaming_execution_source_sha256", self.full104_streaming_execution_source_sha256),
        )

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name, value in self._roots():
            _sha(value, name)
        seen: dict[str, str] = {}
        for name, value in self._roots():
            if value in seen:
                raise ValueError(
                    "run-contract roots must be distinct; "
                    f"{name} duplicates {seen[value]}. Two roles bound to the same "
                    "digest means one of them names code or evidence that did not "
                    "occupy that role."
                )
            seen[value] = name
        if self.execution_source_role_id not in APPROVED_EXECUTION_SOURCE_ROLE_IDS:
            raise ValueError(
                "execution_source_role_id must be one of "
                f"{APPROVED_EXECUTION_SOURCE_ROLE_IDS!r}"
            )
        if self.terminal_universe_id not in APPROVED_TERMINAL_UNIVERSE_IDS:
            raise ValueError(
                f"terminal_universe_id must be one of {APPROVED_TERMINAL_UNIVERSE_IDS!r}"
            )
        if self.freeze_policy_id != FREEZE_POLICY_ID:
            raise ValueError(f"freeze_policy_id must equal {FREEZE_POLICY_ID}")
        if self.support_state_policy_id != STRICT_SUPPORT_POLICY_ID:
            raise ValueError(
                f"support_state_policy_id must equal {STRICT_SUPPORT_POLICY_ID}"
            )
        if self.protected_outcomes_authorized is not False:
            raise ValueError("run contract cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("run contract cannot authorize training")

    # ---- role-explicit execution-source binding -------------------------------

    def bind_execution_sources(
        self,
        *,
        canonical_reference_live_sha256: str,
        full104_streaming_execution_live_sha256: str,
    ) -> None:
        """Verify each execution-source root against the file that fills that role.

        ``canonical_reference_live_sha256`` must be the live digest of
        :data:`CANONICAL_REFERENCE_RELPATH`, and
        ``full104_streaming_execution_live_sha256`` the live digest of
        :data:`FULL104_STREAMING_EXECUTION_RELPATH`. Passing them the wrong way
        round, or freezing the canonical reference digest in the execution role,
        fails here.
        """
        self.validate()
        canonical = _sha(canonical_reference_live_sha256, "canonical_reference_live_sha256")
        streaming = _sha(
            full104_streaming_execution_live_sha256,
            "full104_streaming_execution_live_sha256",
        )
        if canonical == streaming:
            raise ValueError(
                "canonical reference and streaming executor cannot share a digest; "
                "they are different files filling different roles"
            )
        if self.canonical_reference_source_sha256 != canonical:
            raise ValueError(
                "canonical_reference_source_sha256 does not match the live digest of "
                f"{CANONICAL_REFERENCE_RELPATH}"
            )
        if self.full104_streaming_execution_source_sha256 != streaming:
            if self.full104_streaming_execution_source_sha256 == canonical:
                raise ValueError(
                    "EXECUTION_SOURCE_ROLE_MISBINDING: the canonical reference digest is "
                    "bound in the FULL104 streaming-execution role. The canonical "
                    "reference does not execute FULL104; bind the digest of "
                    f"{FULL104_STREAMING_EXECUTION_RELPATH} instead."
                )
            raise ValueError(
                "full104_streaming_execution_source_sha256 does not match the live "
                f"digest of {FULL104_STREAMING_EXECUTION_RELPATH}"
            )

    # ---- authority binding ----------------------------------------------------

    def bind_parameters(self, parameters: Any) -> None:
        self.validate()
        if _live_digest(parameters, "parameters") != self.qualification_parameters_authority_sha256:
            raise ValueError("parameters authority root mismatch")

    def bind_design(self, design: Any) -> None:
        self.validate()
        if _live_digest(design, "qualification design") != self.qualification_design_authority_sha256:
            raise ValueError("qualification design authority root mismatch")

    def bind_evidence_budget(self, budget: Any) -> None:
        self.validate()
        if _live_digest(budget, "evidence budget") != self.target_evidence_budget_authority_sha256:
            raise ValueError("evidence-budget authority root mismatch")

    def bind_burden_ladder(self, ladder: Any) -> None:
        self.validate()
        if _live_digest(ladder, "burden ladder") != self.burden_ladder_authority_sha256:
            raise ValueError("burden-ladder authority root mismatch")
        if ladder.census_authority_sha256 != self.census_authority_sha256:
            raise ValueError(
                "burden ladder is bound to a different census authority than the run contract"
            )

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V2",
                **asdict(self),
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )
