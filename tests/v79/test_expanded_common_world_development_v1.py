"""Red/green development-only safeguards for the expanded PR328 fit fixture.

No synthetic target/learner PASS or model training may be reported from these tests.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from scripts.v79 import expanded_common_world_development_v1 as dev
from scripts.v79.unified_synthetic_integration_v1 import (
    UnifiedBiologyConfig, build_unified_biology,
)
from scripts.v79.unified_synthetic_fit_view_v1 import (
    UnifiedObservationConfig, fit_view_sha256, observe_unified_world,
)


@pytest.fixture(scope="module")
def fixture():
    return dev.build_development_fixture()


def test_existing_pr328_world_fit_receipts_unchanged():
    """Original immutable 480x48 source hash equivalence, not new benchmark."""
    world = build_unified_biology(UnifiedBiologyConfig(), seed=20261013)
    fit = observe_unified_world(world, UnifiedObservationConfig(), seed=20261014)
    assert world.world_hash == "dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66"
    assert fit_view_sha256(fit) == "fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a"


def test_three_genuinely_disjoint_complete_512_gene_views(fixture):
    files, report = fixture
    roles = report["frozen_preoutcome_address_roles"]
    panels = [np.asarray(p, dtype=int) for p in roles["relational_views_3x512"]]
    assert len(panels) == 3
    assert all(p.shape == (512,) for p in panels)
    assert len(set(np.concatenate(panels).tolist())) == 1536
    teacher = files["teacher_measured.npz"]
    assert teacher["rna_counts"].shape == (1440, 2048)
    assert teacher["rna_support"].shape == (1440, 2048)
    # All 3x512 addresses have structural support across all synthetic sources.
    assert all(teacher["rna_support"][:, p].all() for p in panels)
    # This is *view feasibility*, not R1 relation/gate qualification.
    assert report["all_six_candidate_recoverability"] == "UNASSESSED"


def test_real_structural_support_not_detection(fixture):
    files, report = fixture
    t = files["teacher_measured.npz"]
    roster = files["roster_evaluation_only.npz"]
    masks = dev.prospective_support()
    for i, source in enumerate(dev.SOURCES):
        rows = roster["synthetic_source"] == source
        assert rows.any()
        assert np.array_equal(t["rna_support"][rows], np.broadcast_to(masks[i], t["rna_support"][rows].shape))
    # Both structurally unavailable genes and measured zero counts must occur.
    assert np.any(~t["rna_support"])
    assert np.any((t["rna_counts"] == 0) & t["rna_support"])
    assert np.all(t["rna_counts"][~t["rna_support"]] == 0)
    assert report["support"]["independent_of_count_detection"] is True


def test_query_panels_and_q_exclusion_under_adversarial_count_mutation(fixture):
    files, report = fixture
    t = files["teacher_measured.npz"]
    student = files["student_qexcluded.npz"]
    roles = report["frozen_preoutcome_address_roles"]
    queries = roles["query_addresses"]
    panels = roles["query_other8_panels"]
    assert len(queries) == 4 and len(panels) == 4
    assert all(len(p) == 8 for p in panels)
    assert not set(queries).intersection(set(sum(panels, [])))
    assert len(set(sum(panels, []))) == 32
    assert not set(queries).intersection(student["rna_base_address_ids"].tolist())
    assert student["rna_base_counts"].shape == (1440, 2044)
    assert student["rna_base_support"].shape == (1440, 2044)
    assert np.array_equal(
        student["projected_base_depth"],
        student["rna_base_counts"].sum(axis=1, dtype=np.int64),
    )
    attacked = t["rna_counts"].copy()
    attacked[:, queries] += 987654
    projection = dev.student_projection(attacked, t["rna_support"], queries)
    for key in projection:
        assert np.array_equal(projection[key], student[key]), key


def test_same_and_other_nucleus_atac_distinct(fixture):
    files, _ = fixture
    paired = files["teacher_measured.npz"]["atac_same_nucleus"]
    unpaired = files["atac_separate_nucleus_negative.npz"]["atac_separate_nucleus"]
    assert paired.shape == unpaired.shape == (1440, 2048)
    assert paired.dtype == np.float32 and unpaired.dtype == np.float32
    assert not np.array_equal(paired, unpaired)
    # A biological C5 regulatory PASS would need held-donor and matched-null
    # learning/scoring; neither is run here.


def test_donor_primary_split_and_role_separation(fixture):
    files, report = fixture
    roster = files["roster_evaluation_only.npz"]
    split = roster["split"]
    donors = roster["donor_id"]
    assert set(split) == {"train", "val", "test"}
    assert set(roster["synthetic_source"]) == set(dev.SOURCES)
    assert np.unique(donors).size == 36
    for donor in np.unique(donors):
        assert np.unique(split[donors == donor]).size == 1
        assert np.unique(roster["synthetic_source"][donors == donor]).size == 1
    # Donor and source metadata are held in evaluator-only file, not student.
    assert set(files["student_qexcluded.npz"]) == {
        "rna_base_counts", "rna_base_support",
        "rna_base_address_ids", "projected_base_depth",
    }
    assert "synthetic_source" not in files["student_qexcluded.npz"]
    assert "atac_separate_nucleus" not in files["teacher_measured.npz"]
    assert report["synthetic_fit_role_separation"].startswith("FILE_LEVEL_DEVELOPMENT_ONLY")


def test_no_controller_truth_or_learned_authority_in_any_fit_output(fixture):
    files, report = fixture
    forbidden = {
        "expected_molecular_state", "rare_activity", "rare_program_activity",
        "continuous_factors", "latent_abundance", "context_niche",
        "perturbation_state", "candidate_mapping", "counterfactual_truth",
        "cell_score_mean", "ordering_truth", "conditional_signal_mean",
    }
    assert set(files) == set(dev.FIT_NAMES)
    assert all(not set(payload).intersection(forbidden) for payload in files.values())
    assert report["controller_truth_exported"] is False
    assert report["model_training_or_controller_scoring_executed"] is False
    assert report["real_biology_or_production_authority"] is False
    assert report["C4_C6_nonadditive_increment"] == "NOT_ADJUDICATED"


def test_report_is_original_source_bound_and_roles_unchanged_by_counts(fixture):
    _, report = fixture
    assert report["source_parent_pr328_exact_head"] == dev.PARENT_PR328_HEAD
    assert report["original_pr328_480x48_untouched"] is True
    assert report["frozen_preoutcome_address_roles"] == dev.frozen_address_roles(dev.prospective_support())
    assert report["frozen_dimensions"] == {"cells": 1440, "genes": 2048, "donors": 36}


def test_fail_closed_projection_and_no_overwrite(tmp_path: Path, fixture):
    with pytest.raises(ValueError, match="invalid frozen queries"):
        dev.student_projection(
            fixture[0]["teacher_measured.npz"]["rna_counts"],
            fixture[0]["teacher_measured.npz"]["rna_support"],
            [0, 0, 1, 2],
        )
    receipt = dev.write_development_fixture(tmp_path / "first")
    assert set(receipt["fit_file_sha256"]) == set(dev.FIT_NAMES)
    for name in dev.FIT_NAMES:
        path = tmp_path / "first" / name
        assert sha256(path.read_bytes()).hexdigest() == receipt["fit_file_sha256"][name]
        with np.load(path, allow_pickle=False) as f:
            assert all(f[key].dtype.kind != "O" for key in f.files)
    assert (tmp_path / "first" / "DEVELOPMENT_RECEIPT.json").is_file()
    with pytest.raises(FileExistsError):
        dev.write_development_fixture(tmp_path / "first")
