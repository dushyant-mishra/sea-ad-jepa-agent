from __future__ import annotations

import hashlib
import importlib
import inspect
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.contracts import MECHANICS_CONTRACT  # noqa: E402
from sea_ad_jepa.v4.full_transcriptome_synthetic import generate_full_transcriptome_fixture  # noqa: E402
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder  # noqa: E402
from sea_ad_jepa.v4.successor_candidate import (  # noqa: E402
    CandidateMolecularLedger, SuccessorCandidateContract, biological_evidence_curve,
    contiguous_supported_prefix, fit_reproducibility_weighted_basis, masked_project,
    measurement_quality_curve, one_standard_error_dimension, oracle_module_graph,
    validate_encoder_inputs, zero_fill_project,
)


def small_basis():
    expression = np.asarray([[1., 9., 2., 0.], [2., 8., 1., 1.], [3., 7., 0., 2.], [4., 6., 1., 3.]])
    support = np.ones_like(expression, dtype=bool)
    return expression, support, fit_reproducibility_weighted_basis(expression, support, np.ones(4), np.asarray(["a", "a", "b", "b"]), 2)


def test_historical_mechanics_contract_is_unchanged() -> None:
    assert (MECHANICS_CONTRACT.vocabulary_size, MECHANICS_CONTRACT.gene_identity_dim, MECHANICS_CONTRACT.model_width, MECHANICS_CONTRACT.latent_slots) == (4096, 48, 160, 24)


def test_candidate_dimensions_are_independent() -> None:
    contract = SuccessorCandidateContract(37346, 160, 96)
    assert (contract.gene_count, contract.d_gene, contract.global_audit_max_dim) == (37346, 160, 96)


def test_measured_zero_differs_from_unmeasured() -> None:
    ids = torch.tensor([[0, 1]]); expression = torch.zeros(1, 2); support = torch.tensor([[True, False]])
    ledger = CandidateMolecularLedger(ids, expression, support, torch.zeros(1, 2, 3))
    assert ledger.normalized_expression[0, 0] == ledger.normalized_expression[0, 1] == 0
    assert ledger.measurement_support.tolist() == [[True, False]]


def test_candidate_encoder_accepts_gene_ids_above_4095() -> None:
    model = IPBEncoder(vocabulary_size=5001, width=8, heads=2, blocks=1, ffn_width=16, dropout=0)
    output = model(torch.tensor([[4999, 5000]]), torch.ones(1, 2), torch.ones(1, 2, dtype=torch.bool), torch.zeros(1, 2, dtype=torch.bool), "target")
    assert output.gene_states.shape == (1, 2, 8)


def test_historical_encoder_default_remains_4096() -> None:
    assert IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16).tokenizer.vocabulary_size == 4096


def test_candidate_package_retains_all_molecular_evidence() -> None:
    fields = set(CandidateMolecularLedger.__dataclass_fields__)
    assert fields == {"canonical_gene_ids", "normalized_expression", "measurement_support", "contextual_gene_states"}


def test_oracle_graph_path_has_no_pearson_builder() -> None:
    source = inspect.getsource(oracle_module_graph)
    runner = importlib.import_module("scripts.v4.stage81a3r_full_transcriptome_microqual")
    assert "build_train_pearson_graph(" not in source
    assert "build_train_pearson_graph(" not in inspect.getsource(runner.full_g_mechanics)
    assert oracle_module_graph(np.arange(500) // 10).genes == 500


def test_masked_projection_ignores_unmeasured_values() -> None:
    expression, support, basis = small_basis(); support[0, 1] = False
    first = masked_project(expression[:1], support[:1], basis, 2)
    changed = expression[:1].copy(); changed[0, 1] = 1e9
    np.testing.assert_allclose(first, masked_project(changed, support[:1], basis, 2))


def test_zero_fill_and_masked_projection_differ() -> None:
    expression, support, basis = small_basis(); support[0, 1:] = False
    assert not np.allclose(masked_project(expression[:1], support[:1], basis, 2), zero_fill_project(expression[:1], support[:1], basis, 2))


def test_same_cell_cross_operator_fixture_is_paired() -> None:
    fixture = generate_full_transcriptome_fixture(512, cells=64, seed=4)
    assert fixture.counts_view1.shape == fixture.counts_view2.shape == (64, 512)
    assert not np.array_equal(fixture.counts_view1, fixture.counts_view2)


def test_one_se_selector_is_deterministic() -> None:
    errors = np.asarray([[3., 2., 2.01], [3.1, 2.1, 2.0], [2.9, 1.9, 2.02]])
    assert one_standard_error_dimension([16, 32, 48], errors) == one_standard_error_dimension([16, 32, 48], errors)
    assert one_standard_error_dimension([16, 32, 48], errors)[0] == 32


def test_residual_inclusion_is_contiguous() -> None:
    assert contiguous_supported_prefix([(1, 16, True), (17, 32, True), (33, 48, False)])[0] == 32


def test_supported_block_after_gap_is_ordering_failure() -> None:
    prefix, status = contiguous_supported_prefix([(1, 16, True), (17, 32, False), (33, 48, True)])
    assert prefix == 16 and status == "ORDERING FAILURE / REPRESENTATION-DESIGN CONCERN"


def test_donor_refits_recompute_preprocessing() -> None:
    expression, support, _ = small_basis()
    first = fit_reproducibility_weighted_basis(expression[:2], support[:2], np.ones(4), np.asarray(["a", "a"]), 1)
    second = fit_reproducibility_weighted_basis(expression[2:], support[2:], np.ones(4), np.asarray(["b", "b"]), 1)
    assert not np.array_equal(first.mean, second.mean)


def test_hidden_labels_are_not_basis_inputs() -> None:
    assert set(inspect.signature(fit_reproducibility_weighted_basis).parameters) == {"expression", "measurement_support", "reproducibility", "donors", "max_dim"}


@pytest.mark.parametrize("name", ["donor_id", "dataset_id", "matrix_id", "pathology", "diagnosis", "cell_type", "rare_state"])
def test_forbidden_unrestricted_encoder_inputs(name: str) -> None:
    with pytest.raises(ValueError): validate_encoder_inputs(["expression", name])


def test_global_basis_has_no_ledger_parameter_path() -> None:
    assert "torch" not in inspect.getsource(fit_reproducibility_weighted_basis)


def test_u_bio_and_u_meas_are_separate_paths() -> None:
    assert biological_evidence_curve is not measurement_quality_curve
    assert "support" in inspect.signature(biological_evidence_curve).parameters
    assert "noise_scales" in inspect.signature(measurement_quality_curve).parameters


def test_protected_historical_hashes() -> None:
    expected = {
        "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
        "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
        "results/v4/stage81a3_foundation_biological_state_domain_qualification.json": "912bf050f1091575bf141295ccb06bbce648614cd5991cf660c33f8951cff4b3",
        "results/v4/stage81a3_reproducible_state_basis.pt": "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest() == digest


def test_new_manifest_contract_excludes_forbidden_inputs() -> None:
    text = (PROJECT / "configs/v4/stage81a2r_a3r_microqual.yaml").read_text().lower()
    input_block = text.split("inputs:", 1)[1].split("outputs:", 1)[0]
    assert "pathology" not in input_block and "development" not in input_block and "sealed" not in input_block


def test_localization_control_refits_both_bases_independently() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_full_transcriptome_microqual")
    source = inspect.getsource(runner.audit_fixture)
    assert "ordinary_fits.append(fit_reproducibility_weighted_basis" in source
    assert "fits.append(fit_reproducibility_weighted_basis" in source
    assert "fixture.normalized_view1[train][rows]" in source


def test_heldout_raw_upper_bound_respects_heldout_support() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_full_transcriptome_microqual")
    source = inspect.getsource(runner.audit_fixture)
    assert "np.where(fixture.heldout_support, fixture.normalized_view2, 0.0)" in source
    assert "heldout_panel_raw_informative_mean_factor_r2" in source


def test_stability_repair_changes_sample_size_only_for_hard_fixtures() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_stability_audit_repair")
    source = inspect.getsource(runner.main)
    assert 'seed=int(fixture_item["seed"]), name=fixture_item["name"]' in source
    assert 'repair["hard_fixture_cell_levels"]' in source


def test_stability_repair_refits_ordinary_and_weighted_preprocessing() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_stability_audit_repair")
    source = inspect.getsource(runner.evaluate_fixture)
    assert "weighted.append(fit_reproducibility_weighted_basis" in source
    assert "ordinary.append(fit_reproducibility_weighted_basis" in source
    assert "fixture.normalized_view1[train][rows]" in source


def test_stability_repair_cannot_promote_unstable_global_or_rerun_heldout() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_stability_audit_repair")
    source = inspect.getsource(runner.main)
    assert '"global_resolution_decision": "UNADJUDICATED"' in source
    assert '"heldout_family_rerun_on_supported_prefix": False' in source


def test_eigenspace_diagnostic_is_fixed_hard_fixture_only() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_eigenspace_band_diagnostic")
    source = inspect.getsource(runner.main)
    assert 'config["cells"]' in source
    assert 'root["synthetic"]["fixtures"]' in source
    assert "stability_calibration" not in source


def test_eigenspace_diagnostic_never_promotes_band() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3r_eigenspace_band_diagnostic")
    source = inspect.getsource(runner.main)
    assert '"dimension_or_band_promoted": False' in source
    assert '"global_resolution_decision": "UNADJUDICATED"' in source
