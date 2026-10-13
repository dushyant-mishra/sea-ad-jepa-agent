from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Mapping

import numpy as np

from .unified_synthetic_integration_v1 import UnifiedBiologyWorld


@dataclass(frozen=True)
class UnifiedControllerTruth:
    world_sha256: str
    candidate_mapping: dict[str, dict[str, object]]
    recoverability: dict[str, str]
    counterfactual_truth: dict[str, object]


def derive_controller_truth(world: UnifiedBiologyWorld) -> UnifiedControllerTruth:
    expected = np.asarray(world.expected_molecular_state, dtype=np.float64)
    shared = expected.mean(axis=1)
    rare = np.asarray(world.rare_activity, dtype=bool)
    programs = np.asarray(world.rare_program_activity, dtype=bool)
    context = np.asarray(world.context_niche, dtype=bool)
    perturb = np.asarray(world.perturbation_state, dtype=bool)
    arms = np.asarray(world.perturbation_arm, dtype=np.int8)

    # Candidate-specific semantics are derived only here, after the neutral world exists.
    mapping = {
        "C1": {
            "kind": "shared_state",
            "cell_score_mean": float(shared.mean()),
            "cell_score_sd": float(shared.std()),
        },
        "C2": {
            "kind": "relational_shared",
            "ordering": np.argsort(shared).astype(int).tolist(),
        },
        "C3": {
            "kind": "query_conditioned",
            "query_address": 0,
            "conditional_signal_mean": float(expected[:, 0].mean()),
        },
        "C4": {
            "kind": "structured_composite",
            "components": ["C1", "C2", "C3"],
        },
        "C5": {
            "kind": "regulatory_specialist",
            "rare_cell_count": int(rare.sum()),
            "program_regimes": list(world.rare_regime_ids),
            "program_positive_counts": programs.sum(axis=0).astype(int).tolist(),
        },
        "C6": {
            "kind": "shared_query_composite",
            "components": ["C1", "C3"],
        },
    }
    recoverability = {
        "C1": "POINT_IDENTIFIABLE",
        "C2": "POINT_IDENTIFIABLE",
        "C3": "STOCHASTIC_IDENTIFIABLE",
        "C4": "STOCHASTIC_IDENTIFIABLE",
        "C5": "TEACHER_PRIVATE" if int(rare.sum()) < max(2, len(rare) // 100) else "POINT_IDENTIFIABLE",
        "C6": "STOCHASTIC_IDENTIFIABLE",
    }
    rare_by_regime = {
        regime: {
            "cell_positive_count": int(programs[:, p].sum()),
            "donor_active_count": int(world.rare_donor_active[:, p].sum()),
            "donor_prevalence_mean": float(world.rare_donor_prevalence[:, p].mean()),
        }
        for p, regime in enumerate(world.rare_regime_ids)
    }
    counterfactual = {
        "rare_activity_count": int(rare.sum()),
        "rare_by_regime": rare_by_regime,
        "context_niche_count": int(context.sum()),
        "context_rare_prevalence": float(rare[context].mean()) if context.any() else 0.0,
        "noncontext_rare_prevalence": float(rare[~context].mean()) if (~context).any() else 0.0,
        "perturbed_count": int(perturb.sum()),
        "perturbation_arm_counts": {str(a): int((arms == a).sum()) for a in (0, 1, 2)},
        "rare_expected_shift": float(expected[rare].mean() - expected[~rare].mean()) if rare.any() and (~rare).any() else 0.0,
    }
    return UnifiedControllerTruth(
        world_sha256=world.world_hash,
        candidate_mapping=mapping,
        recoverability=recoverability,
        counterfactual_truth=counterfactual,
    )


def controller_truth_sha256(truth: UnifiedControllerTruth) -> str:
    raw = json.dumps(asdict(truth), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()


_FORBIDDEN = {
    "rare_activity",
    "rare_eligible",
    "rare_program_activity",
    "rare_donor_active",
    "rare_donor_prevalence",
    "context_niche",
    "perturbation_state",
    "expected_molecular_state",
    "candidate_mapping",
    "recoverability",
    "controller_truth",
    "controller_truth_sha256",
    "counterfactual_truth",
    "latent_abundance",
    "pseudo_rare",
}


def assert_fit_view_is_controller_free(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("fit payload must be a mapping")
    leaked = sorted(set(payload) & _FORBIDDEN)
    if leaked:
        raise ValueError(f"controller-only fields leaked into fit view: {leaked}")
