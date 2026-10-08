#!/usr/bin/env python3
"""Adapter exposing F1-B/C3 successor v2 to the frozen behavioural attacks."""
from __future__ import annotations

from scripts.v4.f1b_successor_attack_suite_v1 import Candidate
from scripts.v4.f1b_c3_training_successor_v2 import (
    ATTACK_AUTHORITY_PACKAGE_ROOT,
    directional_claim,
    enforce_frozen_horizon,
    gate_mandatory_gradients,
    movement_gate,
    production_amp_smoke,
    protected_update,
    refit_g5_probe,
    routing_metrics,
    routing_report,
    select_g5_endpoints,
    target_equivalence,
)


def successor_candidate() -> Candidate:
    return Candidate(
        name="F1BC3TrainingSuccessorV2",
        gate_mandatory_gradients=gate_mandatory_gradients,
        movement_gate=movement_gate,
        routing_report=routing_report,
        routing_metrics=routing_metrics,
        refit=refit_g5_probe,
        frozen_horizon=enforce_frozen_horizon,
        directional_claim=directional_claim,
        target_equivalence=target_equivalence,
        amp_smoke=production_amp_smoke,
        protected_update=protected_update,
        select_endpoints=select_g5_endpoints,
        metadata={
            "generation": "v2",
            "attack_authority_package_root": ATTACK_AUTHORITY_PACKAGE_ROOT,
            "real_execution_authorized": False,
        },
    )
