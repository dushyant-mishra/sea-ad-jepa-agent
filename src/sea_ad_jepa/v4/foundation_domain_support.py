"""Non-neural domain-support descriptors and leave-one-matrix distances."""

from __future__ import annotations

import numpy as np


def mixed_process_distance(
    first_numeric: np.ndarray,
    second_numeric: np.ndarray,
    first_categorical: tuple[str, ...],
    second_categorical: tuple[str, ...],
) -> float:
    """Fixed Gower-style mean distance over robust numeric and categorical fields."""
    first_numeric = np.asarray(first_numeric, dtype=np.float64)
    second_numeric = np.asarray(second_numeric, dtype=np.float64)
    numeric = np.minimum(np.abs(first_numeric - second_numeric), 10.0) / 10.0
    categorical = np.asarray([a != b for a, b in zip(first_categorical, second_categorical, strict=True)], dtype=float)
    return float(np.mean(np.concatenate([numeric, categorical])))


def domain_quadrant(measurement_distance: float, biological_distance: float, measurement_threshold: float, biological_threshold: float) -> str:
    measurement = measurement_distance > measurement_threshold
    biological = biological_distance > biological_threshold
    return {
        (False, False): "A_familiar_measurement_familiar_biology",
        (False, True): "B_familiar_measurement_unusual_biology",
        (True, False): "C_unfamiliar_measurement_familiar_biology",
        (True, True): "D_unfamiliar_measurement_unusual_biology",
    }[(measurement, biological)]


def descriptor_distance(first: dict[str, object], second: dict[str, object]) -> dict[str, float | bool]:
    numeric_names = ("library_median", "detected_median", "zero_fraction_median", "nonzero_median")
    numeric = []
    for name in numeric_names:
        a, b = float(first.get(name, 0.0)), float(second.get(name, 0.0))
        scale = max(abs(a), abs(b), 1.0)
        numeric.append(abs(a - b) / scale)
    mask_distance = 0.0 if first["mask_hash"] == second["mask_hash"] else 1.0
    technology_match = first.get("technology") == second.get("technology")
    tissue_match = first.get("tissue") == second.get("tissue")
    total = float(np.mean(numeric) + mask_distance + (0.0 if technology_match else 0.5) + (0.0 if tissue_match else 0.25))
    return {
        "total_distance": total,
        "qc_distance": float(np.mean(numeric)),
        "measurement_mask_distance": mask_distance,
        "technology_match": bool(technology_match),
        "tissue_match": bool(tissue_match),
    }


def nearest_domains(descriptors: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for name in sorted(descriptors):
        candidates = []
        for other in sorted(descriptors):
            if other == name:
                continue
            candidates.append((descriptor_distance(descriptors[name], descriptors[other])["total_distance"], other))
        _, nearest = min(candidates)
        rows.append({"matrix_id": name, "nearest_matrix_id": nearest, **descriptor_distance(descriptors[name], descriptors[nearest])})
    return rows
