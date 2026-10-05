"""Pathology-blind bounded candidate functionals for prospective G4.

These are candidates, not selected production authority:
- donor-held-out nearest-centroid cell-state recovery;
- donor state-composition fidelity based on those held-out predictions;
- paired same-cell cosine stability under measurement/masking intervention.

The content and stability limbs remain separate so a constant representation
cannot pass merely by being invariant.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class StateContentResultV1:
    oof_predicted_label: tuple[str, ...]
    classes: tuple[str, ...]
    balanced_accuracy: float
    donor_composition_fidelity: np.ndarray
    mean_donor_composition_fidelity: float

    def __post_init__(self) -> None:
        x = np.array(self.donor_composition_fidelity, dtype=np.float64, copy=True)
        if x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x)):
            raise ValueError("donor_composition_fidelity must be a finite vector")
        if np.any((x < 0.0) | (x > 1.0)):
            raise ValueError("composition fidelity must be bounded in [0,1]")
        if not 0.0 <= float(self.balanced_accuracy) <= 1.0:
            raise ValueError("balanced accuracy must be bounded in [0,1]")
        if not 0.0 <= float(self.mean_donor_composition_fidelity) <= 1.0:
            raise ValueError("mean composition fidelity must be bounded in [0,1]")
        x.flags.writeable = False
        object.__setattr__(self, "donor_composition_fidelity", x)


@dataclass(frozen=True)
class SameCellStabilityResultV1:
    per_row_stability: np.ndarray
    per_donor_stability: np.ndarray
    equal_donor_mean_stability: float

    def __post_init__(self) -> None:
        for name in ("per_row_stability", "per_donor_stability"):
            x = np.array(getattr(self, name), dtype=np.float64, copy=True)
            if x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x)):
                raise ValueError(f"{name} must be a finite vector")
            if np.any((x < 0.0) | (x > 1.0)):
                raise ValueError(f"{name} must be bounded in [0,1]")
            x.flags.writeable = False
            object.__setattr__(self, name, x)
        if not 0.0 <= float(self.equal_donor_mean_stability) <= 1.0:
            raise ValueError("equal_donor_mean_stability must be bounded in [0,1]")


@dataclass(frozen=True)
class StateContentIncrementOverNuisanceV1:
    representation_balanced_accuracy: float
    nuisance_balanced_accuracy: float
    balanced_accuracy_increment: float
    representation_mean_composition_fidelity: float
    nuisance_mean_composition_fidelity: float
    composition_fidelity_increment: float


def _embedding(value: Any, name: str) -> np.ndarray:
    x = np.asarray(value, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1 or not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be a finite row x latent matrix")
    norms = np.linalg.norm(x, axis=1)
    if np.any(norms <= 0):
        raise ValueError(f"{name} contains zero-norm rows; cosine content/stability is undefined")
    return x


def _labels(value: Any, name: str, n: int) -> np.ndarray:
    x = np.asarray([str(v) for v in value], dtype=object)
    if x.ndim != 1 or x.size != n or any(not str(v) for v in x):
        raise ValueError(f"{name} must contain {n} nonempty labels")
    return x


def _donor_fold_by_row(donor: np.ndarray, donor_fold: Any) -> np.ndarray:
    folds = np.asarray(donor_fold, dtype=np.int64)
    max_donor = int(donor.max())
    if donor.min() < 0 or folds.ndim != 1 or folds.size <= max_donor:
        raise ValueError("donor_fold must cover every nonnegative donor code")
    row_fold = folds[donor]
    if len(set(map(int, row_fold))) < 2:
        raise ValueError("content evaluation requires >=2 donor-held-out folds")
    return row_fold


def _unit_rows(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def donor_heldout_state_content(
    embedding: Any,
    state_label: Any,
    donor_code_by_row: Any,
    donor_fold: Any,
) -> StateContentResultV1:
    """Evaluate state content with no held-out-donor fitting.

    A cosine nearest-centroid probe is deliberately simple and deterministic.
    Its role is falsification: if a candidate representation cannot preserve
    even this bounded held-out state content, it cannot carry the G4 gate.
    """

    x = _embedding(embedding, "embedding")
    n = x.shape[0]
    label = _labels(state_label, "state_label", n)
    donor = np.asarray(donor_code_by_row, dtype=np.int64)
    if donor.ndim != 1 or donor.size != n:
        raise ValueError("donor_code_by_row must align embedding rows")
    row_fold = _donor_fold_by_row(donor, donor_fold)
    classes = tuple(sorted(set(label.tolist())))
    if len(classes) < 2:
        raise ValueError("state content requires at least two classes")

    z = _unit_rows(x)
    pred = np.empty(n, dtype=object)
    for fold in sorted(set(map(int, row_fold))):
        train = row_fold != fold
        test = row_fold == fold
        if not np.any(train) or not np.any(test):
            raise ValueError("each fold must contain train and held-out rows")
        centroids = []
        for cls in classes:
            ix = train & (label == cls)
            if not np.any(ix):
                raise ValueError(f"class {cls!r} absent from a training fold")
            centroid = z[ix].mean(axis=0)
            norm = float(np.linalg.norm(centroid))
            if norm <= 0:
                raise ValueError(f"class {cls!r} has zero-norm training centroid")
            centroids.append(centroid / norm)
        C = np.vstack(centroids)
        score = z[test] @ C.T
        winner = np.argmax(score, axis=1)
        pred[test] = [classes[int(i)] for i in winner]

    recalls = []
    for cls in classes:
        ix = label == cls
        if not np.any(ix):
            raise AssertionError("declared class has no rows")
        recalls.append(float(np.mean(pred[ix] == cls)))
    balanced = float(np.mean(recalls))

    donors = sorted(set(map(int, donor)))
    donor_fidelity = np.empty(len(donors), dtype=np.float64)
    for j, d in enumerate(donors):
        ix = donor == d
        true_p = np.asarray([np.mean(label[ix] == cls) for cls in classes], dtype=np.float64)
        pred_p = np.asarray([np.mean(pred[ix] == cls) for cls in classes], dtype=np.float64)
        tv = 0.5 * float(np.abs(true_p - pred_p).sum())
        donor_fidelity[j] = 1.0 - tv

    return StateContentResultV1(
        oof_predicted_label=tuple(map(str, pred.tolist())),
        classes=classes,
        balanced_accuracy=balanced,
        donor_composition_fidelity=donor_fidelity,
        mean_donor_composition_fidelity=float(donor_fidelity.mean()),
    )


def paired_same_cell_cosine_stability(
    reference_embedding: Any,
    intervened_embedding: Any,
    donor_code_by_row: Any,
) -> SameCellStabilityResultV1:
    ref = _embedding(reference_embedding, "reference_embedding")
    alt = _embedding(intervened_embedding, "intervened_embedding")
    if ref.shape != alt.shape:
        raise ValueError("reference and intervened embeddings must align exactly")
    donor = np.asarray(donor_code_by_row, dtype=np.int64)
    if donor.ndim != 1 or donor.size != ref.shape[0] or donor.min() < 0:
        raise ValueError("donor_code_by_row must align embedding rows")

    rn = _unit_rows(ref)
    an = _unit_rows(alt)
    cosine = np.sum(rn * an, axis=1)
    if np.any(np.abs(cosine) > 1.0 + 1e-10):
        raise ValueError("numeric cosine escaped [-1,1]")
    # Map [-1,1] to [0,1] so the rewarded direction is bounded.
    stability = (np.clip(cosine, -1.0, 1.0) + 1.0) / 2.0

    donors = sorted(set(map(int, donor)))
    per_donor = np.asarray([stability[donor == d].mean() for d in donors], dtype=np.float64)
    return SameCellStabilityResultV1(
        per_row_stability=stability,
        per_donor_stability=per_donor,
        equal_donor_mean_stability=float(per_donor.mean()),
    )



def compare_state_content_to_nuisance_baseline(
    representation_content: StateContentResultV1,
    nuisance_content: StateContentResultV1,
) -> StateContentIncrementOverNuisanceV1:
    """Report incremental content beyond a lawful nuisance-only baseline.

    No acceptance threshold is chosen here. A high absolute content score with
    near-zero increment is explicitly visible rather than being called biology.
    """

    if representation_content.classes != nuisance_content.classes:
        raise ValueError("representation and nuisance probes must use identical classes")
    if len(representation_content.oof_predicted_label) != len(nuisance_content.oof_predicted_label):
        raise ValueError("representation and nuisance probes must cover identical rows")
    if representation_content.donor_composition_fidelity.shape != nuisance_content.donor_composition_fidelity.shape:
        raise ValueError("representation and nuisance probes must cover identical donors")
    return StateContentIncrementOverNuisanceV1(
        representation_balanced_accuracy=float(representation_content.balanced_accuracy),
        nuisance_balanced_accuracy=float(nuisance_content.balanced_accuracy),
        balanced_accuracy_increment=float(
            representation_content.balanced_accuracy - nuisance_content.balanced_accuracy
        ),
        representation_mean_composition_fidelity=float(
            representation_content.mean_donor_composition_fidelity
        ),
        nuisance_mean_composition_fidelity=float(
            nuisance_content.mean_donor_composition_fidelity
        ),
        composition_fidelity_increment=float(
            representation_content.mean_donor_composition_fidelity
            - nuisance_content.mean_donor_composition_fidelity
        ),
    )
