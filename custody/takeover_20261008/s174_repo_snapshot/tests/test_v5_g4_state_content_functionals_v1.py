import numpy as np
import pytest

from sea_ad_jepa.v5.g4_state_content_functionals_v1 import (
    compare_state_content_to_nuisance_baseline,
    donor_heldout_state_content,
    paired_same_cell_cosine_stability,
)


def clustered_fixture():
    rows = []
    # Four donors, two folds, every donor has both classes but donor-specific
    # composition differs so composition recovery is nontrivial.
    counts = {
        0: (8, 2),
        1: (2, 8),
        2: (7, 3),
        3: (3, 7),
    }
    rng = np.random.default_rng(3)
    for donor, (na, nb) in counts.items():
        for label, n, center in (
            ("A", na, np.array([2.0, 0.2])),
            ("B", nb, np.array([0.2, 2.0])),
        ):
            for _ in range(n):
                rows.append((donor, label, center + rng.normal(scale=0.03, size=2)))
    embedding = np.vstack([r[2] for r in rows])
    donor = np.array([r[0] for r in rows])
    label = [r[1] for r in rows]
    donor_fold = np.array([0, 1, 1, 0])
    return embedding, label, donor, donor_fold


def test_clean_state_embedding_has_high_heldout_content_and_composition_fidelity() -> None:
    emb, label, donor, folds = clustered_fixture()
    out = donor_heldout_state_content(emb, label, donor, folds)
    assert out.balanced_accuracy > 0.95
    assert out.mean_donor_composition_fidelity > 0.95
    assert np.all(out.donor_composition_fidelity > 0.9)


def test_constant_representation_is_stable_but_fails_content_limb() -> None:
    emb, label, donor, folds = clustered_fixture()
    constant = np.ones_like(emb)
    content = donor_heldout_state_content(constant, label, donor, folds)
    stability = paired_same_cell_cosine_stability(constant, constant.copy(), donor)
    assert stability.equal_donor_mean_stability == pytest.approx(1.0)
    assert content.balanced_accuracy <= 0.55
    assert content.mean_donor_composition_fidelity < 0.8


def test_same_cell_stability_detects_large_rotation() -> None:
    ref = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, -1.0]])
    alt = -ref
    out = paired_same_cell_cosine_stability(ref, alt, [0, 0, 1, 1])
    assert out.equal_donor_mean_stability == pytest.approx(0.0)


def test_zero_norm_representation_is_nonestimable_not_maximally_stable() -> None:
    with pytest.raises(ValueError, match="zero-norm"):
        paired_same_cell_cosine_stability(
            [[0.0, 0.0], [1.0, 0.0]],
            [[0.0, 0.0], [1.0, 0.0]],
            [0, 1],
        )


def test_content_probe_never_trains_on_heldout_donor_class_absence() -> None:
    # Fold 0 training contains only class B, so class A in the heldout fold is
    # not silently scored with a probe that never saw it.
    emb = np.array([[2.0, 0.0], [2.1, 0.0], [0.0, 2.0], [0.0, 2.1]])
    labels = ["A", "A", "B", "B"]
    donor = np.array([0, 0, 1, 1])
    donor_fold = np.array([0, 1])
    with pytest.raises(ValueError, match="absent from a training fold"):
        donor_heldout_state_content(emb, labels, donor, donor_fold)



def test_source_only_content_is_not_mislabeled_incremental_biology() -> None:
    # Two sources, two donors per source, each source perfectly determines the
    # state label. A representation that only encodes source has perfect content
    # recovery, but so does the lawful source-only nuisance baseline.
    donor = np.repeat(np.arange(4), 6)
    source_by_donor = np.array([0, 1, 0, 1])
    source = source_by_donor[donor]
    labels = np.where(source == 0, "A", "B").tolist()
    donor_fold = np.array([0, 0, 1, 1])
    rep = np.column_stack([source == 0, source == 1]).astype(float)
    nuisance = rep.copy()

    rep_content = donor_heldout_state_content(rep, labels, donor, donor_fold)
    nuisance_content = donor_heldout_state_content(nuisance, labels, donor, donor_fold)
    inc = compare_state_content_to_nuisance_baseline(rep_content, nuisance_content)

    assert rep_content.balanced_accuracy == pytest.approx(1.0)
    assert rep_content.mean_donor_composition_fidelity == pytest.approx(1.0)
    assert inc.balanced_accuracy_increment == pytest.approx(0.0)
    assert inc.composition_fidelity_increment == pytest.approx(0.0)
