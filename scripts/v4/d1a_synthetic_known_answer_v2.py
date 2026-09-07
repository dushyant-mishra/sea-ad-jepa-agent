"""Deterministic known-answer fixtures for the frozen D1-A V2 contract."""

from __future__ import annotations

from dataclasses import dataclass
import json

import numpy as np
import pandas as pd

from sea_ad_jepa.v4.d1a_estimation_atlas import build_d1a_atlas


@dataclass(frozen=True)
class SyntheticFixture:
    states: np.ndarray
    metadata: pd.DataFrame
    molecular_values: np.ndarray
    measured_mask: np.ndarray
    feature_ids: list[str]
    known_refs: dict[str, np.ndarray]
    biological_direction: np.ndarray
    artifact_direction: np.ndarray
    biological_score: np.ndarray
    artifact_score: np.ndarray


def make_synthetic_fixture(seed: int = 20260907) -> SyntheticFixture:
    rng = np.random.default_rng(seed)
    n_donors = 12
    cells_per_donor = 8
    n_cells = n_donors * cells_per_donor
    n_features = 24

    basis, _ = np.linalg.qr(rng.normal(size=(160, 2)))
    biological_direction = basis[:, 0]
    artifact_direction = basis[:, 1]

    donors = np.repeat([f"D{i:02d}" for i in range(n_donors)], cells_per_donor)
    source_names = np.asarray(["HVS", "NPH52", "SEA_AD"], dtype=object)
    operator_names = np.asarray([f"OP{i:02d}" for i in range(6)], dtype=object)
    donor_source = {f"D{i:02d}": source_names[i % 3] for i in range(n_donors)}
    donor_operator = {f"D{i:02d}": operator_names[i % 6] for i in range(n_donors)}
    sources = np.asarray([donor_source[d] for d in donors], dtype=object)
    operators = np.asarray([donor_operator[d] for d in donors], dtype=object)

    biological_score = rng.normal(0.0, 1.0, size=n_cells)
    source_effect = {"HVS": 1.4, "NPH52": 0.0, "SEA_AD": -1.4}
    artifact_score = np.asarray([source_effect[str(s)] for s in sources]) + rng.normal(0.0, 0.35, size=n_cells)

    states = (
        3.2 * biological_score[:, None] * biological_direction[None, :]
        + 4.6 * artifact_score[:, None] * artifact_direction[None, :]
        + rng.normal(0.0, 0.30, size=(n_cells, 160))
    )

    support_probability = np.clip(0.52 + 0.20 * artifact_score, 0.10, 0.92)
    measured_mask = rng.random((n_cells, n_features)) < support_probability[:, None]

    molecular = rng.normal(0.0, 0.45, size=(n_cells, n_features))
    molecular[:, 0:5] += 2.2 * biological_score[:, None]
    molecular[:, 5:10] -= 2.2 * biological_score[:, None]
    molecular_values = molecular.copy()
    molecular_values[~measured_mask] = np.nan

    feature_ids = [f"G{i:02d}" for i in range(n_features)]
    known = np.zeros(n_features, dtype=np.float64)
    known[0:5] = 1.0
    known[5:10] = -1.0

    metadata = pd.DataFrame({
        "canonical_cell_id": [f"CELL_{i:04d}" for i in range(n_cells)],
        "donor": donors,
        "source": sources.astype(str),
        "operator": operators.astype(str),
    })

    return SyntheticFixture(
        states=states,
        metadata=metadata,
        molecular_values=molecular_values,
        measured_mask=measured_mask,
        feature_ids=feature_ids,
        known_refs={"KNOWN_BIO_MODULE": known},
        biological_direction=biological_direction,
        artifact_direction=artifact_direction,
        biological_score=biological_score,
        artifact_score=artifact_score,
    )


def make_measurement_only_fixture(seed: int = 20260908) -> SyntheticFixture:
    fixture = make_synthetic_fixture(seed)
    rng = np.random.default_rng(seed + 1)
    states = (
        4.6 * fixture.artifact_score[:, None] * fixture.artifact_direction[None, :]
        + rng.normal(0.0, 0.45, size=fixture.states.shape)
    )
    molecular = rng.normal(0.0, 0.5, size=fixture.molecular_values.shape)
    molecular[~fixture.measured_mask] = np.nan
    return SyntheticFixture(
        states=states,
        metadata=fixture.metadata,
        molecular_values=molecular,
        measured_mask=fixture.measured_mask,
        feature_ids=fixture.feature_ids,
        known_refs=fixture.known_refs,
        biological_direction=fixture.biological_direction,
        artifact_direction=fixture.artifact_direction,
        biological_score=fixture.biological_score,
        artifact_score=fixture.artifact_score,
    )


def _directions(result) -> dict[str, np.ndarray]:
    rows = result.state_loading_table
    output = {}
    for pid, frame in rows.groupby("program_id", sort=True):
        frame = frame.sort_values("state_dimension")
        output[str(pid)] = frame["loading"].to_numpy(dtype=float)
    return output


def known_answer_diagnostic() -> dict[str, object]:
    fixture = make_synthetic_fixture()
    result = build_d1a_atlas(
        fixture.states,
        fixture.metadata,
        fixture.molecular_values,
        fixture.measured_mask,
        fixture.feature_ids,
        n_components=3,
        mode="synthetic",
        known_molecular_reference_programs=fixture.known_refs,
    )
    directions = _directions(result)
    bio_alignment = {
        pid: abs(float(np.dot(direction, fixture.biological_direction)))
        for pid, direction in directions.items()
    }
    artifact_alignment = {
        pid: abs(float(np.dot(direction, fixture.artifact_direction)))
        for pid, direction in directions.items()
    }
    bio_pid = max(bio_alignment, key=bio_alignment.get)
    artifact_pid = max(artifact_alignment, key=artifact_alignment.get)

    cells = result.cell_ranking_table
    bio_cells = cells[cells["program_id"] == bio_pid].sort_values("canonical_cell_id")
    metadata_order = fixture.metadata.sort_values("canonical_cell_id").index.to_numpy()
    cell_correlation = float(
        np.corrcoef(
            bio_cells["raw_score"].to_numpy(dtype=float),
            fixture.biological_score[metadata_order],
        )[0, 1]
    )

    molecular = result.molecular_table[result.molecular_table["program_id"] == bio_pid].copy()
    top10 = set(
        molecular.sort_values(["effect_rank", "feature_id"]).head(10)["feature_id"].astype(str)
    )
    expected_module = {f"G{i:02d}" for i in range(10)}
    module_overlap = len(top10 & expected_module)

    programs = result.program_table.set_index("program_id")
    hypotheses = result.hypothesis_catalog.set_index("program_id")

    negative = make_measurement_only_fixture()
    negative_result = build_d1a_atlas(
        negative.states,
        negative.metadata,
        negative.molecular_values,
        negative.measured_mask,
        negative.feature_ids,
        n_components=3,
        mode="synthetic",
        known_molecular_reference_programs=negative.known_refs,
    )
    negative_directions = _directions(negative_result)
    absent_bio_max_alignment = max(
        abs(float(np.dot(direction, negative.biological_direction)))
        for direction in negative_directions.values()
    )

    return {
        "schema": "d1a-v2-synthetic-known-answer-diagnostic",
        "bio_program_id": bio_pid,
        "artifact_program_id": artifact_pid,
        "bio_alignment": bio_alignment[bio_pid],
        "artifact_alignment": artifact_alignment[artifact_pid],
        "bio_cell_score_abs_correlation": abs(cell_correlation),
        "bio_module_top10_overlap": module_overlap,
        "bio_priority_score": float(hypotheses.loc[bio_pid, "priority_score"]),
        "artifact_priority_score": float(hypotheses.loc[artifact_pid, "priority_score"]),
        "bio_measurement_support_r2": float(programs.loc[bio_pid, "measurement_support_r2"]),
        "artifact_measurement_support_r2": float(programs.loc[artifact_pid, "measurement_support_r2"]),
        "bio_source_eta_squared": float(programs.loc[bio_pid, "source_eta_squared"]),
        "artifact_source_eta_squared": float(programs.loc[artifact_pid, "source_eta_squared"]),
        "negative_absent_bio_max_alignment": float(absent_bio_max_alignment),
        "n_program_rows": int(len(result.program_table)),
        "n_state_loading_rows": int(len(result.state_loading_table)),
        "n_cell_ranking_rows": int(len(result.cell_ranking_table)),
        "n_molecular_rows": int(len(result.molecular_table)),
        "n_donor_rows": int(len(result.donor_table)),
        "n_source_rows": int(len(result.source_table)),
        "n_operator_rows": int(len(result.operator_table)),
        "n_hypothesis_rows": int(len(result.hypothesis_catalog)),
        "claim_status_values": sorted(set(result.hypothesis_catalog["claim_status"].astype(str))),
        "optimizer_steps": result.diagnostics["optimizer_steps"],
        "ema_updates": result.diagnostics["ema_updates"],
        "confirmatory_terminal": result.diagnostics["confirmatory_terminal"],
    }


def main() -> int:
    print(json.dumps(known_answer_diagnostic(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
