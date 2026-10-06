from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


REQUIRED_Q_SAFETY_CHANNELS = (
    "QUERY_VALUE",
    "NORMALIZATION_DENOMINATOR",
    "LIBRARY_SIZE_SUMMARY",
    "DETECTED_FEATURE_SUMMARY",
    "QC_DESCENDANTS",
    "SUPPORT_OR_MISSINGNESS_SUMMARY",
    "MASK_CONSTRUCTION",
    "QUERY_DEPENDENT_PREPROCESSING",
    "TARGET_OR_TEACHER_PRE_CONTEXT",
)


@dataclass(frozen=True)
class QSafetyPolicyV1:
    forbidden_descendant_channels: tuple[str, ...]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.forbidden_descendant_channels, tuple):
            raise ValueError("q-safety channels must be an explicit tuple")
        supplied = self.forbidden_descendant_channels
        missing = [channel for channel in REQUIRED_Q_SAFETY_CHANNELS if channel not in supplied]
        if missing:
            raise ValueError(f"q-safety policy is missing required channels: {missing}")
        unknown = [channel for channel in supplied if channel not in REQUIRED_Q_SAFETY_CHANNELS]
        if unknown:
            raise ValueError(f"unknown q-safety channels require a successor contract: {unknown}")
        if len(supplied) != len(set(supplied)):
            raise ValueError("q-safety policy contains duplicate channels")


class NegativeControlArm(str, Enum):
    CLEAN_NEGATIVE = "CLEAN_NEGATIVE"
    TECHNICAL_OPERATOR_SHORTCUT = "TECHNICAL_OPERATOR_SHORTCUT"
    PLANTED_RECOVERABLE_BIOLOGICAL = "PLANTED_RECOVERABLE_BIOLOGICAL"
    PLANTED_INACCESSIBLE_PRIVATE_STATE = "PLANTED_INACCESSIBLE_PRIVATE_STATE"
    QUERY_LEAK = "QUERY_LEAK"


@dataclass(frozen=True)
class SyntheticControlRosterV1:
    arms: tuple[NegativeControlArm, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.arms, tuple) or not all(
            isinstance(arm, NegativeControlArm) for arm in self.arms
        ):
            raise ValueError("synthetic control arms must be an explicit tuple of NegativeControlArm")
        if len(self.arms) != len(set(self.arms)):
            raise ValueError("synthetic control roster contains duplicate arms")

    def validate(self, *, require_private_state: bool, require_query_leak: bool) -> None:
        required = {
            NegativeControlArm.CLEAN_NEGATIVE,
            NegativeControlArm.TECHNICAL_OPERATOR_SHORTCUT,
            NegativeControlArm.PLANTED_RECOVERABLE_BIOLOGICAL,
        }
        if require_private_state:
            required.add(NegativeControlArm.PLANTED_INACCESSIBLE_PRIVATE_STATE)
        if require_query_leak:
            required.add(NegativeControlArm.QUERY_LEAK)
        missing = required.difference(self.arms)
        if NegativeControlArm.PLANTED_INACCESSIBLE_PRIVATE_STATE in missing:
            raise ValueError("synthetic control roster is missing required private-state control")
        if NegativeControlArm.QUERY_LEAK in missing:
            raise ValueError("synthetic control roster is missing required query-leak control")
        if missing:
            raise ValueError(f"synthetic control roster is missing required controls: {sorted(x.value for x in missing)}")
