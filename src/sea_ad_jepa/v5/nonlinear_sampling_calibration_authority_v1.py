"""Control-only calibration of the FULL104 nonlinear donor sampling cap."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Tuple

CAP_LADDER: Tuple[int, ...] = (64, 128, 256, 512, 1024)
LADDER_ID = "FULL104_NONLINEAR_DONOR_CAP_CONTROL_LADDER_V1"
SELECTION_RULE_ID = "LOWEST_PLANTED_CONTROL_QUALIFYING_NONLINEAR_CAP_V1"
OUTCOME_FIREWALL_ID = "REAL_MASKING_POLICY_OUTCOMES_FORBIDDEN_DURING_NONLINEAR_CAP_CALIBRATION_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(value,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload) -> str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class NonlinearCapControlVerdictV1:
    max_cells_per_donor: int
    planted_detected: bool
    planted_suppressed: bool
    negative_contains_zero: bool
    replay_exact: bool
    all_donors_represented: bool

    @property
    def qualified(self) -> bool:
        return all((
            self.planted_detected,
            self.planted_suppressed,
            self.negative_contains_zero,
            self.replay_exact,
            self.all_donors_represented,
        ))


@dataclass(frozen=True)
class NonlinearSamplingCalibrationPlanV1:
    authority_id: str
    target_panel_authority_sha256: str
    outer_split_authority_sha256: str
    primary_parameters_authority_sha256: str
    ladder_id: str = LADDER_ID
    selection_rule_id: str = SELECTION_RULE_ID
    outcome_firewall_policy_id: str = OUTCOME_FIREWALL_ID
    cap_ladder: Tuple[int,...] = CAP_LADDER
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        roots=(
            _sha(self.target_panel_authority_sha256,"target_panel_authority_sha256"),
            _sha(self.outer_split_authority_sha256,"outer_split_authority_sha256"),
            _sha(self.primary_parameters_authority_sha256,"primary_parameters_authority_sha256"),
        )
        if len(set(roots)) != len(roots): raise ValueError("nonlinear calibration roots must be role-distinct")
        if self.ladder_id != LADDER_ID: raise ValueError("ladder_id mismatch")
        if self.selection_rule_id != SELECTION_RULE_ID: raise ValueError("selection_rule_id mismatch")
        if self.outcome_firewall_policy_id != OUTCOME_FIREWALL_ID: raise ValueError("outcome_firewall_policy_id mismatch")
        if tuple(self.cap_ladder) != CAP_LADDER: raise ValueError("nonlinear cap ladder is frozen")
        if self.terminal_outcomes_inspected_before_freeze is not False: raise ValueError("nonlinear cap plan must freeze before terminal outcomes")
        if self.training_authorized is not False: raise ValueError("nonlinear cap plan cannot authorize training")

    def select(self, verdicts: Mapping[int, NonlinearCapControlVerdictV1]) -> int | None:
        self.validate()
        keys=tuple(verdicts.keys())
        expected=self.cap_ladder[:len(keys)]
        if keys != expected: raise ValueError("nonlinear cap verdicts must form an exact ladder prefix")
        first=None
        for i,cap in enumerate(keys):
            v=verdicts[cap]
            if v.max_cells_per_donor != cap: raise ValueError("nonlinear cap verdict mismatch")
            if v.qualified:
                first=i; break
        if first is not None:
            if first != len(keys)-1: raise ValueError("higher nonlinear cap opened after lower cap already qualified")
            return keys[first]
        if len(keys)==len(self.cap_ladder): raise ValueError("FAIL_CLOSED_NO_CONTROL_QUALIFYING_NONLINEAR_CAP")
        return None

    def next_cap(self, verdicts: Mapping[int, NonlinearCapControlVerdictV1]) -> int:
        selected=self.select(verdicts)
        if selected is not None: raise ValueError("nonlinear cap already qualified; do not open higher cap")
        return self.cap_ladder[len(verdicts)]

    def canonical_digest(self) -> str:
        self.validate()
        payload=dict(asdict(self)); payload["cap_ladder"]=list(self.cap_ladder)
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V1",**payload})


@dataclass(frozen=True)
class NonlinearSamplingCalibrationReceiptV1:
    plan_authority_sha256: str
    selected_max_cells_per_donor: int
    evaluated_caps: Tuple[int,...]
    verdict_digest_by_cap: Mapping[int,str]
    real_masking_policy_outcomes_inspected: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        _sha(self.plan_authority_sha256,"plan_authority_sha256")
        if self.selected_max_cells_per_donor not in CAP_LADDER: raise ValueError("selected nonlinear cap is not approved")
        if tuple(self.evaluated_caps) != CAP_LADDER[:len(self.evaluated_caps)]: raise ValueError("evaluated nonlinear caps must form exact ladder prefix")
        if not self.evaluated_caps or self.evaluated_caps[-1] != self.selected_max_cells_per_donor: raise ValueError("selected nonlinear cap must be final evaluated rung")
        if set(self.verdict_digest_by_cap) != set(self.evaluated_caps): raise ValueError("receipt must bind every evaluated nonlinear cap")
        for cap,digest in self.verdict_digest_by_cap.items():
            _sha(digest,f"verdict_digest_by_cap[{cap}]")
        if self.real_masking_policy_outcomes_inspected is not False: raise ValueError("nonlinear cap calibration cannot use real policy outcomes")
        if self.training_authorized is not False: raise ValueError("nonlinear calibration receipt cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload=dict(asdict(self)); payload["evaluated_caps"]=list(self.evaluated_caps); payload["verdict_digest_by_cap"]={str(k):v for k,v in sorted(self.verdict_digest_by_cap.items())}
        return _digest({"schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V1",**payload})
