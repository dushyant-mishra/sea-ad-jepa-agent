from __future__ import annotations

import importlib
import importlib.util
import math

import numpy as np
import pytest

import scripts.v5.td_real_measurement_reference_v1 as LEGACY


def _load(name: str):
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    return importlib.import_module(name)


def test_conformal_resolution_never_rounds_anti_conservatively_at_boundary():
    alpha = math.nextafter(1.0 / 600.0, 0.0)
    assert 600.0 * alpha < 1.0
    assert LEGACY.minimum_calibration_size(alpha) == 600
    out = LEGACY.upper_prediction_bound([0.1] * 599, alpha=alpha)
    assert out["status"] == "NOT_ESTIMABLE_CALIBRATION_RESOLUTION"
    assert out["required_n"] == 600


def test_observation_aware_thinning_is_cell_and_address_identity_keyed_not_storage_order_keyed():
    T = _load("scripts.v5.td_real_measurement_thinning_v2")
    counts = np.asarray([[50, 0, 20], [10, 30, 0]], dtype=np.int64)
    measured = np.asarray([[True, True, True], [True, True, True]], dtype=bool)
    kwargs = dict(
        fraction=0.5,
        seed_namespace="g8/calibration",
        draw_index=7,
        row_ids=["cell-A", "cell-B"],
        address_ids=["addr-1", "addr-2", "addr-3"],
        measured_mask=measured,
        full_library=[100, 80],
    )
    a = T.thin_counts_and_library(counts, **kwargs)

    row_perm = [1, 0]
    col_perm = [2, 0, 1]
    b = T.thin_counts_and_library(
        counts[np.ix_(row_perm, col_perm)],
        fraction=0.5,
        seed_namespace="g8/calibration",
        draw_index=7,
        row_ids=[kwargs["row_ids"][i] for i in row_perm],
        address_ids=[kwargs["address_ids"][j] for j in col_perm],
        measured_mask=measured[np.ix_(row_perm, col_perm)],
        full_library=[kwargs["full_library"][i] for i in row_perm],
    )

    def canonical(out, row_ids, address_ids):
        result = {}
        for i, row_id in enumerate(row_ids):
            result[row_id] = {
                "counts": {address_ids[j]: out["counts"][i][j] for j in range(len(address_ids))},
                "library": out["library"][i],
                "unstored": out["unstored_library"][i],
            }
        return result

    assert canonical(a, kwargs["row_ids"], kwargs["address_ids"]) == canonical(
        b,
        [kwargs["row_ids"][i] for i in row_perm],
        [kwargs["address_ids"][j] for j in col_perm],
    )


def test_observation_aware_thinning_thins_unstored_library_mass_and_preserves_measurement_mask():
    T = _load("scripts.v5.td_real_measurement_thinning_v2")
    counts = [[40, 0], [12, 8]]
    measured = [[True, True], [True, True]]
    out = T.thin_counts_and_library(
        counts,
        fraction=0.25,
        seed_namespace="g8/calibration",
        draw_index=11,
        row_ids=["A", "B"],
        address_ids=["x", "y"],
        measured_mask=measured,
        full_library=[100, 20],
    )
    assert out["measured_mask"] == measured
    assert out["full_library"] == [100, 20]
    assert out["stored_library"] == [40, 20]
    assert out["unstored_library"] == [60, 0]
    for row_counts, thinned_library in zip(out["counts"], out["library"]):
        assert sum(row_counts) <= thinned_library
    assert out["library"][1] == sum(out["counts"][1])


def test_structurally_unmeasured_entries_cannot_carry_counts_into_thinning():
    T = _load("scripts.v5.td_real_measurement_thinning_v2")
    with pytest.raises(T.MeasurementThinningError, match="unmeasured"):
        T.thin_counts_and_library(
            [[5, 3]],
            fraction=0.5,
            seed_namespace="g8/calibration",
            draw_index=0,
            row_ids=["A"],
            address_ids=["x", "y"],
            measured_mask=[[True, False]],
            full_library=[8],
        )


def test_full_library_must_dominate_stored_counts_exactly():
    T = _load("scripts.v5.td_real_measurement_thinning_v2")
    with pytest.raises(T.MeasurementThinningError, match="full library"):
        T.thin_counts_and_library(
            [[5, 3]],
            fraction=0.5,
            seed_namespace="g8/calibration",
            draw_index=0,
            row_ids=["A"],
            address_ids=["x", "y"],
            measured_mask=[[True, True]],
            full_library=[7],
        )


def test_four_rng_namespaces_are_mandatory_and_disjoint():
    T = _load("scripts.v5.td_real_measurement_thinning_v2")
    T.validate_seed_namespaces(
        calibration_namespace="cal",
        deciding_namespace="decide",
        null_namespace="null",
        refit_namespace="refit",
    )
    with pytest.raises(T.MeasurementThinningError, match="disjoint"):
        T.validate_seed_namespaces(
            calibration_namespace="same",
            deciding_namespace="same",
            null_namespace="null",
            refit_namespace="refit",
        )


def test_g8_v3_fail_closes_reference_generation_until_statistical_estimand_is_qualified():
    G = _load("scripts.v5.td_real_g8_realization_contract_v3")
    out = G.reference_generation_readiness(
        observation_thinning_schema="JEPA_TD_REAL_MEASUREMENT_THINNING_V2",
        exact_input_bound=True,
        metric_contract_bound=True,
        support_contract_bound=True,
        technical_draws_available=599,
    )
    assert out["status"] == "BLOCKED_G8_STATISTICAL_CONTRACT_NOT_QUALIFIED"
    assert out["reference_generation_authorized"] is False
    assert out["human_g8_adjudication_authorized"] is False
    assert out["technical_draws_available"] == 599
    assert "599" not in out["blocking_reason"]


def test_repeated_thinnings_cannot_be_declared_independent_conformal_observations_for_full_vs_thinned_decision():
    G = _load("scripts.v5.td_real_g8_realization_contract_v3")
    with pytest.raises(G.G8V3ContractError, match="exchangeability"):
        G.validate_statistical_claim(
            calibration_observation="REPEATED_RNG_THINNING_OF_FIXED_REAL_UNIT",
            deciding_quantity="FULL_COUNT_TO_THINNED_DISPLACEMENT",
            claim="SPLIT_CONFORMAL_PREDICTION_BOUND",
        )


def test_g8_v3_does_not_promote_technical_draw_count_into_biological_sample_size():
    G = _load("scripts.v5.td_real_g8_realization_contract_v3")
    out = G.reference_generation_readiness(
        observation_thinning_schema="JEPA_TD_REAL_MEASUREMENT_THINNING_V2",
        exact_input_bound=True,
        metric_contract_bound=True,
        support_contract_bound=True,
        technical_draws_available=10_000,
    )
    assert out["biological_replication_unit"] == "DONOR"
    assert out["technical_draws_increase_biological_n"] is False
    assert out["reference_generation_authorized"] is False


def test_g8_v3_authority_remains_closed():
    G = _load("scripts.v5.td_real_g8_realization_contract_v3")
    out = G.reference_generation_readiness(
        observation_thinning_schema="JEPA_TD_REAL_MEASUREMENT_THINNING_V2",
        exact_input_bound=True,
        metric_contract_bound=True,
        support_contract_bound=True,
        technical_draws_available=599,
    )
    assert all(value is False for value in out["authority"].values())
