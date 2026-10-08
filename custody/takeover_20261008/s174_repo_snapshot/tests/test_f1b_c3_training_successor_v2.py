from __future__ import annotations

import pytest

from scripts.v4.f1b_c3_training_successor_adapter_v2 import successor_candidate
from scripts.v4.f1b_c3_training_successor_v2 import (
    ATTACK_AUTHORITY_PACKAGE_ROOT,
    FROZEN_MANDATORY_BACKBONE,
    FROZEN_UPDATES,
    REGISTERED_G5_ENDPOINTS,
    directional_claim,
    enforce_frozen_horizon,
    refit_g5_probe,
    routing_metrics,
    select_g5_endpoints,
    target_equivalence,
)
from scripts.v4.f1b_reference_candidates_v1 import reference_vulnerable
from scripts.v4.f1b_successor_attack_suite_v1 import (
    DEFENDED,
    prove_polarity,
    registry_audit,
    run_suite,
)


def test_successor_defends_every_frozen_attack() -> None:
    report = run_suite(successor_candidate())
    assert report["terminal"] == "PASS_F1B_ATTACK_SUITE"
    assert report["not_applicable"] == []
    assert report["attack_defective"] == []
    assert len(report["defended"]) == 14
    assert all(row["verdict"] == DEFENDED for row in report["results"].values())


def test_successor_preserves_historical_vulnerable_pole_and_registry() -> None:
    polarity = prove_polarity(reference_vulnerable(), successor_candidate())
    assert polarity["terminal"] == "PASS_ATTACK_POLARITY"
    registry = registry_audit(reference_vulnerable(), successor_candidate())
    assert registry["terminal"] == "PASS_F1B_ATTACK_REGISTRY"


def test_attack_authority_binding_and_protected_registry_are_exact() -> None:
    assert ATTACK_AUTHORITY_PACKAGE_ROOT == (
        "daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b"
    )
    assert len(FROZEN_MANDATORY_BACKBONE) == 48
    assert len(set(FROZEN_MANDATORY_BACKBONE)) == 48
    assert all(
        any("." + role + "." in name for role in (
            "attention_norm", "attention.query", "attention.key", "attention.value"
        ))
        for name in FROZEN_MANDATORY_BACKBONE
    )


def test_horizon_is_an_enforced_constant_not_a_default() -> None:
    assert FROZEN_UPDATES == 40
    assert enforce_frozen_horizon(40) == {"updates": 40}
    with pytest.raises(RuntimeError):
        enforce_frozen_horizon(300)


def test_g5_refit_endpoint_and_directional_controls_are_behavioral() -> None:
    a = {
        "fit_donors": ["a1", "a2"], "fit_values": [0.0, 0.0],
        "eval_donors": ["e1"], "eval_values": [9.0],
    }
    b = {
        "fit_donors": ["b1", "b2"], "fit_values": [2.0, 4.0],
        "eval_donors": ["e1"], "eval_values": [9.0],
    }
    assert refit_g5_probe(a)["predictions"] == [0.0]
    assert refit_g5_probe(b)["predictions"] == [3.0]
    assert REGISTERED_G5_ENDPOINTS == ("l2__broad_common", "l2__local")
    assert select_g5_endpoints([
        "l2__broad_common", "l2__local", "l2__unregistered_experimental"
    ]) == ["l2__broad_common", "l2__local"]

    assert directional_claim({
        "observed": 1.0, "cell_only_control": 1.0, "identity_only_control": 0.0
    })["structural"] is False
    assert directional_claim({
        "observed": 1.0, "cell_only_control": 0.0, "identity_only_control": 1.0
    })["structural"] is False
    assert directional_claim({
        "observed": 1.0, "cell_only_control": 0.0, "identity_only_control": 0.0
    })["structural"] is True


def test_target_and_routing_semantics_keep_their_names() -> None:
    assert target_equivalence([1.0, 2.0], [1.0, 2.0])["equivalent"] is True
    assert target_equivalence([1.0, 2.0], [1.0, 2.1])["equivalent"] is False

    report = routing_metrics(
        [[0.5, 0.25, 0.25]],
        [[True, True, True]],
    )
    assert report["N_eff_entropy"][0] != report["N_eff_participation"][0]
    assert report["N_eff_entropy"][0] == pytest.approx(2.82842712474619)
    assert report["N_eff_participation"][0] == pytest.approx(2.6666666666666665)
