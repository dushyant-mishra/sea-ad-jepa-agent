from __future__ import annotations

import inspect

import pytest
import torch

from sea_ad_jepa.v5.data_first_support import (
    CANONICAL_VOCABULARY_SIZE,
    combined_teacher_student_token_cost,
    contribution_weighted_mean,
    evidence_dose,
    evidence_dose_from_fraction,
    fine_matched_null_permutation_partial,
    fine_null_estimability,
    plan_contiguous_token_budget_microbatches,
    ragged_donor_operator_groups,
    sample_ragged_anchored_triplets,
    support_stratified_evidence_counts,
)


def test_evidence_reports_within_support_and_universe_semantics() -> None:
    hvs = evidence_dose_from_fraction(18_736, 0.40)
    sea = evidence_dose_from_fraction(35_076, 0.40)
    assert hvs.visible_addresses == 11_242
    assert sea.visible_addresses == 21_046
    assert hvs.visible_fraction_of_measured == pytest.approx(1 - 7_494 / 18_736)
    assert sea.visible_fraction_of_measured == pytest.approx(1 - 14_030 / 35_076)
    assert hvs.visible_fraction_of_universe == pytest.approx(11_242 / CANONICAL_VOCABULARY_SIZE)
    assert sea.visible_fraction_of_universe == pytest.approx(21_046 / CANONICAL_VOCABULARY_SIZE)
    assert hvs.visible_fraction_of_universe < sea.visible_fraction_of_universe


def test_evidence_support_is_fail_closed_but_not_equalized() -> None:
    with pytest.raises(ValueError, match="exceeds measured"):
        evidence_dose(10, 11)
    with pytest.raises(ValueError, match="exact integer"):
        evidence_dose(10.0, 4)  # type: ignore[arg-type]


def test_ragged_groups_keep_nonestimable_cells_in_batch() -> None:
    donors = ["d0", "d0", "d1", "d1", "d1", "d2"]
    operators = ["o", "o", "o", "o", "o", "o"]
    plan = ragged_donor_operator_groups(donors, operators)
    assert plan.group_counts.tolist() == [2, 3, 1]
    assert plan.total_cells == 6
    assert plan.total_groups == 3
    assert plan.estimable_groups == 1
    assert plan.estimable_cells == 3
    assert plan.relationally_estimable_cell_mask.tolist() == [False, False, True, True, True, False]


def test_ragged_group_order_does_not_require_equal_sizes() -> None:
    donors = ["b", "a", "a", "a", "c", "c", "c", "c"]
    operators = ["z", "x", "x", "y", "q", "q", "q", "q"]
    plan = ragged_donor_operator_groups(donors, operators)
    assert sorted(plan.group_counts.tolist()) == [1, 1, 2, 4]
    assert plan.estimable_groups == 1


def test_singleton_null_stratum_becomes_not_estimable_not_exception() -> None:
    strata = torch.tensor([0, 0, 1, 2, 2, 2], dtype=torch.int64)
    report = fine_null_estimability(strata)
    assert report.stratum_counts.tolist() == [2, 1, 3]
    assert report.nonestimable_strata == 1
    assert report.nonestimable_cell_mask.tolist() == [False, False, True, False, False, False]
    perm, mask = fine_matched_null_permutation_partial(strata, seed=19)
    assert perm[2].item() == -1
    assert not mask[2]
    eligible = torch.nonzero(mask, as_tuple=False).flatten()
    assert torch.all(perm[eligible] != eligible)
    assert torch.equal(strata[perm[eligible]], strata[eligible])


def test_partial_null_is_deterministic_and_seeded() -> None:
    strata = torch.tensor([0, 0, 0, 1, 1, 1, 1, 2], dtype=torch.int64)
    a, ma = fine_matched_null_permutation_partial(strata, seed=7)
    b, mb = fine_matched_null_permutation_partial(strata, seed=7)
    assert torch.equal(a, b) and torch.equal(ma, mb)
    assert a[-1].item() == -1
    assert not ma[-1]
    variants = {
        tuple(fine_matched_null_permutation_partial(strata, seed=seed)[0].tolist())
        for seed in range(32)
    }
    assert len(variants) > 1


def test_token_budget_packer_never_reorders_and_requires_external_budget() -> None:
    costs = torch.tensor([9, 7, 5, 11, 4], dtype=torch.int64)
    plan = plan_contiguous_token_budget_microbatches(costs, maximum_token_budget=16)
    assert plan.microbatch_ranges == ((0, 2), (2, 4), (4, 5))
    assert plan.microbatch_token_costs == (16, 16, 4)
    with pytest.raises(TypeError):
        plan_contiguous_token_budget_microbatches(costs)  # type: ignore[call-arg]


def test_token_budget_packer_fails_if_one_cell_cannot_fit() -> None:
    with pytest.raises(ValueError, match="one cell exceeds"):
        plan_contiguous_token_budget_microbatches(
            torch.tensor([3, 20, 4], dtype=torch.int64), maximum_token_budget=19
        )


def test_combined_token_cost_uses_actual_support_per_cell_and_view() -> None:
    measured = torch.tensor([10, 20], dtype=torch.int64)
    visible = torch.tensor([[6, 7], [11, 12]], dtype=torch.int64)
    assert combined_teacher_student_token_cost(measured, visible).tolist() == [26, 46]


def test_v5_support_module_has_no_production_geometry_defaults() -> None:
    from sea_ad_jepa.v5 import data_first_support as module

    sig = inspect.signature(module.plan_contiguous_token_budget_microbatches)
    assert sig.parameters["maximum_token_budget"].default is inspect.Parameter.empty
    source = inspect.getsource(module)
    forbidden = [
        "effective_batch = 128",
        "microbatch = 8",
        "target_blocks = 16",
        "group_size=16",
        "groups_per_batch=8",
        "nearest-half",
        "nearest-third",
        "relational_loss_weight",
    ]
    for token in forbidden:
        assert token not in source


def test_v5_is_not_wired_into_v4_production_runtime() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    runtime = (root / "src/sea_ad_jepa/v4/teacher_student_runtime.py").read_text()
    assert "sea_ad_jepa.v5" not in runtime
    assert "data_first_support" not in runtime


def test_frozen_data_geometry_profile_separates_full_reader_from_historical_joint() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    profile = json.loads((root / "docs/agent/TEACHER_STUDENT_DATA_GEOMETRY_PROFILE_V1.json").read_text())
    full = profile["full_reader_fit_marginals"]
    hist = profile["historical_3292_mechanics_only"]
    assert full["cells"] == 4_553_407
    assert full["donors"] == 104
    assert full["operators"] == 42
    assert full["source_support"]["HVS"]["measured_scalar_addresses_min"] == 18_736
    assert full["source_support"]["SEA_AD"]["measured_scalar_addresses_max"] == 35_076
    assert full["diagnostic_theoretical_token_work_reduction_factor"] == pytest.approx(1.7695896057406355)
    assert hist["cells"] == 3_292
    assert hist["donor_operator_groups"] == 1_400
    assert hist["groups_below_triplet_minimum_3"] == 1_021
    assert "MUST NOT" in hist["boundary"]


def test_v5_authority_leaves_dataset_shaped_production_values_unset() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    authority = json.loads((root / "docs/agent/TEACHER_STUDENT_DATA_FIRST_V5_AUTHORITY_V1.json").read_text())
    unset = set(authority["production_values_explicitly_unset"])
    required = {
        "effective_batch_cells",
        "microbatch_cells",
        "maximum_token_budget",
        "mask_or_evidence_fraction",
        "target_block_count_or_address_budget",
        "donor_operator_group_size_schedule",
        "relational_triplet_cap",
        "fine_null_fallback_hierarchy",
        "relational_loss_weight",
        "collapse_thresholds",
        "locality_fraction_or_k",
        "update_count_or_replay_cap",
    }
    assert required <= unset
    assert authority["execution_authorized"] is False
    assert authority["successor_u0_materialization_authorized"] is False
    assert authority["u0_u40_authorized"] is False
    assert authority["td60_authorized"] is False
    assert authority["v4_review_package_unchanged"] is True


def test_hidden_fraction_authority_does_not_accept_strings_or_bools() -> None:
    with pytest.raises(ValueError, match="explicit numeric authority"):
        evidence_dose_from_fraction(100, "0.4")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="explicit numeric authority"):
        evidence_dose_from_fraction(100, True)  # type: ignore[arg-type]


def test_batch_with_zero_relational_support_remains_structurally_valid() -> None:
    plan = ragged_donor_operator_groups(
        ["d0", "d0", "d1", "d2"], ["o", "o", "o", "o"]
    )
    assert plan.total_cells == 4
    assert plan.estimable_groups == 0
    assert plan.estimable_cells == 0
    assert not bool(plan.relationally_estimable_cell_mask.any())


def test_group_keys_are_explicit_and_stable_not_inferred_from_count() -> None:
    plan = ragged_donor_operator_groups(
        ["d2", "d1", "d1", "d2", "d2"], ["oB", "oA", "oA", "oB", "oB"]
    )
    assert plan.group_keys == (("d1", "oA"), ("d2", "oB"))
    assert plan.group_counts.tolist() == [2, 3]


def test_loss_aggregation_is_invariant_to_compute_chunking() -> None:
    a = contribution_weighted_mean(
        torch.tensor([3.0, 9.0]), torch.tensor([2, 4], dtype=torch.int64)
    )
    b = contribution_weighted_mean(
        torch.tensor([1.0, 2.0, 9.0]), torch.tensor([1, 1, 4], dtype=torch.int64)
    )
    assert a.item() == pytest.approx(2.0)
    assert b.item() == pytest.approx(2.0)


def test_loss_aggregation_rejects_zero_estimable_contribution() -> None:
    with pytest.raises(ValueError, match="no estimable contributions"):
        contribution_weighted_mean(
            torch.tensor([0.0]), torch.tensor([0], dtype=torch.int64)
        )


def test_support_stratified_evidence_separates_universal_core_from_extension() -> None:
    measured = torch.tensor([
        [1,1,1,0,0],
        [1,1,1,1,1],
    ], dtype=torch.bool)
    hidden = torch.tensor([
        [1,0,0,0,0],
        [0,1,0,1,0],
    ], dtype=torch.bool)
    core = torch.tensor([1,1,1,0,0], dtype=torch.bool)
    r = support_stratified_evidence_counts(measured, hidden, core)
    assert r.core_measured.tolist() == [3,3]
    assert r.core_hidden.tolist() == [1,1]
    assert r.core_visible.tolist() == [2,2]
    assert r.extension_measured.tolist() == [0,2]
    assert r.extension_hidden.tolist() == [0,1]
    assert r.extension_visible.tolist() == [0,1]


def test_support_stratified_evidence_rejects_fake_universal_core() -> None:
    measured = torch.tensor([[1,1,0],[1,1,1]], dtype=torch.bool)
    hidden = torch.zeros_like(measured)
    fake_core = torch.tensor([1,1,1], dtype=torch.bool)
    with pytest.raises(ValueError, match="universal core is not measured"):
        support_stratified_evidence_counts(measured, hidden, fake_core)


def test_exact_reader_fit_joint_support_closes_and_corrects_historical_proxy() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    summary = json.loads((root / "docs/agent/TEACHER_STUDENT_READER_FIT_DONOR_OPERATOR_SUPPORT_V1.json").read_text())
    assert summary["donor_operator_groups"] == 1_400
    assert summary["reader_fit_cells"] == 4_553_407
    assert summary["group_size"]["min"] == 1
    assert summary["group_size"]["max"] == 42_209
    assert summary["triplet_estimability"]["nonestimable_groups"] == 39
    assert summary["triplet_estimability"]["nonestimable_cells"] == 59
    assert summary["generated_joint_csv"]["rows"] == 1_400
    assert summary["generated_joint_csv"]["sha256"] == "a9cb16bb2c475db6624f1f16405dcc53650003e030fc75c88dfe7d15a5c14e5e"
    assert summary["partition_queried"] == "reader_fit"
    assert summary["protected_partitions_queried"] is False
    assert summary["input_files"]["foundation_metadata_rows_sqlite"]["sha256"] == "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
    assert summary["triplet_estimability"]["estimable_groups"] == 1_361
    assert summary["triplet_estimability"]["estimable_cells"] == 4_553_348
    assert summary["source_summary"]["HVS"]["groups_below_triplet_minimum_3"] == 39
    assert summary["source_summary"]["NPH52"]["groups_below_triplet_minimum_3"] == 0
    assert summary["source_summary"]["SEA_AD"]["groups_below_triplet_minimum_3"] == 0
    assert summary["all_possible_anchored_triplet_capacity_diagnostic"]["source_shares"]["SEA_AD"] == pytest.approx(0.991888481096704)


def test_universal_core_profile_is_support_derived_and_does_not_choose_mask_budget() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    p = json.loads((root / "docs/agent/TEACHER_STUDENT_SUPPORT_RECURRENCE_PROFILE_V1.json").read_text())
    s = p["measured_scalar_support"]
    assert s["measured_by_all_42_operators_universal_core"] == 17_186
    assert s["measured_by_all_operators_within_HVS"] == 18_736
    assert s["measured_by_all_operators_within_NPH52"] == 29_136
    assert s["measured_by_all_operators_within_SEA_AD"] == 35_076
    assert "No hidden/visible budgets are selected" in p["prospective_use"]
    assert p["execution_authorized"] is False


def test_v5_authority_leaves_scientific_sampling_weights_unset() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    a = json.loads((root / "docs/agent/TEACHER_STUDENT_DATA_FIRST_V5_AUTHORITY_V1.json").read_text())
    unset = set(a["production_values_explicitly_unset"])
    assert {
        "scientific_group_sampling_weights",
        "scientific_source_weights",
        "scientific_donor_weights",
        "relational_contribution_unit",
    } <= unset
    assert a["full_reader_joint_recovered"] is True
    assert a["full_reader_joint_facts"]["universal_measured_core_addresses"] == 17_186
    assert a["commitments"]["uniform_all_triplet_sampling_not_authorized"] is True
    assert a["commitments"]["ragged_triplet_sampler_does_not_enumerate_full_reservoir"] is True
    assert a["commitments"]["ragged_triplet_draws_per_group_require_external_authority"] is True
    assert "relational_triplet_draws_per_group" in a["production_values_explicitly_unset"]
    assert "relational_triplet_sampling_seed_policy" in a["production_values_explicitly_unset"]


def test_sampling_measure_diagnostic_exposes_bias_without_selecting_policy() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    d = json.loads((root / "docs/agent/TEACHER_STUDENT_READER_FIT_SAMPLING_MEASURE_DIAGNOSTICS_V1.json").read_text())
    assert d["active_policy"] is None
    assert d["execution_authorized"] is False
    shares = d["source_shares_if_sampled_uniformly_over"]
    assert shares["cells"]["SEA_AD"] == pytest.approx(0.9044245331023562)
    assert shares["donor_operator_groups"]["HVS"] == pytest.approx(0.6771428571428572)
    assert shares["donors"]["SEA_AD"] == pytest.approx(46/104)
    assert shares["all_possible_anchored_triplets"]["SEA_AD"] == pytest.approx(0.991888481096704)
    assert shares["source_then_donor_equal"]["NPH52"] == pytest.approx(1/3)


def test_ragged_triplet_sampler_requires_explicit_group_draws_and_skips_small_groups() -> None:
    plan = ragged_donor_operator_groups(
        ["d0","d0","d1","d1","d1","d1","d2"],
        ["o","o","o","o","o","o","o"],
    )
    sample = sample_ragged_anchored_triplets(
        plan, torch.tensor([0, 5, 0], dtype=torch.int64), seed=17
    )
    assert sample.group_capacities.tolist() == [0, 12, 0]
    assert sample.triplets.shape == (5,3)
    assert len(torch.unique(sample.triplets, dim=0)) == 5
    assert sample.triplet_group_ids.tolist() == [1]*5
    for i,j,k in sample.triplets.tolist():
        assert len({i,j,k}) == 3
        assert j < k
        assert plan.group_ids[i] == plan.group_ids[j] == plan.group_ids[k] == 1


def test_ragged_triplet_sampler_is_deterministic_and_group_key_bound() -> None:
    plan = ragged_donor_operator_groups(
        ["dA"]*6 + ["dB"]*5,
        ["o1"]*6 + ["o2"]*5,
    )
    draws = torch.tensor([8,7], dtype=torch.int64)
    a = sample_ragged_anchored_triplets(plan, draws, seed=99)
    b = sample_ragged_anchored_triplets(plan, draws, seed=99)
    c = sample_ragged_anchored_triplets(plan, draws, seed=100)
    assert torch.equal(a.triplets,b.triplets)
    assert torch.equal(a.triplet_group_ids,b.triplet_group_ids)
    assert not torch.equal(a.triplets,c.triplets)


def test_ragged_triplet_sampler_fails_closed_on_unauthorized_draws() -> None:
    plan = ragged_donor_operator_groups(["d"]*3 + ["x"]*2, ["o"]*5)
    with pytest.raises(ValueError, match="non-estimable"):
        sample_ragged_anchored_triplets(plan, torch.tensor([1,1], dtype=torch.int64), seed=1)
    with pytest.raises(ValueError, match="exceed"):
        sample_ragged_anchored_triplets(plan, torch.tensor([4,0], dtype=torch.int64), seed=1)
    with pytest.raises(TypeError):
        sample_ragged_anchored_triplets(plan, torch.tensor([1,0], dtype=torch.int64))  # type: ignore[call-arg]


def test_ragged_triplet_unranking_matches_complete_small_group_relation_set() -> None:
    plan = ragged_donor_operator_groups(["d"]*4, ["o"]*4)
    sample = sample_ragged_anchored_triplets(plan, torch.tensor([12], dtype=torch.int64), seed=123)
    expected=[]
    for i in range(4):
        others=[x for x in range(4) if x!=i]
        for a in range(len(others)):
            for b in range(a+1,len(others)):
                expected.append((i,others[a],others[b]))
    assert set(map(tuple,sample.triplets.tolist())) == set(expected)
