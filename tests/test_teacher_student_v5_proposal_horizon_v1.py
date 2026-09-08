from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load():
    counts_path = ROOT / "docs/agent/READER_FIT_DONOR_OPERATOR_COUNTS_V1.csv.gz.b64"
    horizon_path = ROOT / "docs/agent/TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1.json"
    proposal_path = ROOT / "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3.json"
    decoded_csv = gzip.decompress(base64.b64decode(counts_path.read_bytes()))
    g = pd.read_csv(io.BytesIO(decoded_csv))
    g["donor_cells"] = g.groupby("donor_id").cells.transform("sum")
    g["groups_per_donor"] = g.groupby("donor_id").operator_index.transform("count")
    source_cells = g.groupby("source").cells.sum().to_dict()
    g["source_cells"] = g.source.map(source_cells)
    horizon = json.loads(horizon_path.read_text())
    proposal = json.loads(proposal_path.read_text())
    return counts_path, horizon_path, proposal_path, g, horizon, proposal


def _coeff(entry: dict[str, object]) -> Fraction:
    return Fraction(int(entry["numerator"]), int(entry["denominator"]))


def _probabilities(g: pd.DataFrame, proposal: dict):
    D = int(g.donor_id.nunique())
    S = int(g.source.nunique())
    counts = g.cells.to_numpy(float)
    p = 1.0 / (D * g.donor_cells.to_numpy(float))
    q_source = 1.0 / (S * g.source_cells.to_numpy(float))
    q_group = 1.0 / (D * g.groups_per_donor.to_numpy(float) * counts)
    c = proposal["base"]["coefficients"]
    a = float(_coeff(c["alpha_target"]))
    b = float(_coeff(c["beta_operator_coverage"]))
    s = float(_coeff(c["gamma_source_uniform"]))
    q = a * p + b * q_group + s * q_source
    return counts, p, q_source, q_group, q, (a, b, s)


def test_horizon_authority_freezes_constraints_but_does_not_authorize_training():
    counts_path, horizon_path, proposal_path, g, horizon, proposal = _load()
    assert horizon["schema"] == "TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1"
    assert horizon["total_presentations"] == 4_553_407 == int(g.cells.sum())
    assert horizon["horizon_definition"] == "EXACTLY_ONE_READER_FIT_POPULATION_EQUIVALENT__NO_AUTOMATIC_EXTENSION"
    c = horizon["constraints_frozen_before_q_selection"]
    assert c == {
        "max_expected_per_cell_exposure": 32,
        "max_importance_weight_max_to_min_ratio": 64.0,
        "min_expected_donor_operator_group_presentations": 16,
        "min_importance_ess_fraction": 0.5,
    }
    assert horizon["training_authorized"] is False
    assert horizon["execution_authorized"] is False
    assert proposal["training_authorized"] is False
    assert proposal["execution_authorized"] is False


def test_compact_reader_fit_group_ledger_is_hash_bound_and_complete():
    counts_path, horizon_path, proposal_path, g, horizon, proposal = _load()
    decoded_csv = gzip.decompress(base64.b64decode(counts_path.read_bytes()))
    raw = pd.read_csv(io.BytesIO(decoded_csv))
    assert list(raw.columns) == ["source", "donor_id", "operator_index", "cells"]
    assert len(g) == 1400
    assert int(g.cells.sum()) == 4_553_407
    assert g.donor_id.nunique() == 104
    assert g.source.nunique() == 3
    assert _sha(counts_path) == proposal["reader_fit_group_counts"]["transport_sha256"]
    assert hashlib.sha256(base64.b64decode(counts_path.read_bytes())).hexdigest() == proposal["reader_fit_group_counts"]["decoded_gzip_sha256"]
    assert hashlib.sha256(decoded_csv).hexdigest() == proposal["reader_fit_group_counts"]["decoded_csv_sha256"] == "e79c03765b8c88a8755d37313b76fd384d8a3f1221c2ee79af0a2b7af0a86d28"
    assert _sha(horizon_path) == proposal["presentation_horizon_authority"]["sha256"] == "5969202b44d4c56bd5d3701b1b84eab2a251ea76b5a9e8bb7fa4732a971c1fc7"


def test_base_q_exact_coefficients_probability_mass_and_p_over_q_metrics():
    _, _, _, g, horizon, proposal = _load()
    counts, p, q_source, q_group, q, (a, b, s) = _probabilities(g, proposal)
    coeff = proposal["base"]["coefficients"]
    assert _coeff(coeff["alpha_target"]) == Fraction(50747095471185150, 1173046947290933909)
    assert _coeff(coeff["beta_operator_coverage"]) == Fraction(5436880721882508, 1173046947290933909)
    assert _coeff(coeff["gamma_source_uniform"]) == Fraction(253256277841, 265996376719)
    assert _coeff(coeff["alpha_target"]) + _coeff(coeff["beta_operator_coverage"]) + _coeff(coeff["gamma_source_uniform"]) == 1
    assert np.sum(counts * q) == pytest.approx(1.0, rel=1e-13, abs=1e-13)

    H = horizon["total_presentations"]
    w = p / q
    ess = 1.0 / np.sum(counts * p * p / q)
    exp = H * q
    group_exp = H * counts * q
    m = proposal["base"]["derived_metrics"]
    assert float(exp.max()) == pytest.approx(32.0, abs=2e-12)
    assert float(group_exp.min()) == pytest.approx(16.0, abs=2e-12)
    assert float(ess) == pytest.approx(m["importance_ess_fraction"], rel=1e-13)
    assert float(w.min()) == pytest.approx(m["importance_weight_min"], rel=1e-13)
    assert float(w.max()) == pytest.approx(m["importance_weight_max"], rel=1e-13)
    assert float(w.max() / w.min()) == pytest.approx(m["importance_weight_max_to_min_ratio"], rel=1e-13)
    assert ess >= 0.5
    assert w.max() / w.min() <= 64.0

    # q != p, so exact importance correction is mandatory rather than optional.
    assert not np.allclose(q, p)
    assert proposal["base"]["importance_correction"].startswith("w_i = p_target_i / q_i")


def test_declared_extrema_are_the_actual_repeat_and_group_coverage_boundaries():
    _, _, _, g, horizon, proposal = _load()
    counts, p, q_source, q_group, q, _ = _probabilities(g, proposal)
    H = horizon["total_presentations"]
    max_i = int(np.argmax(H * q))
    min_i = int(np.argmin(H * counts * q))
    max_row = g.iloc[max_i]
    min_row = g.iloc[min_i]
    declared = proposal["base"]["active_extrema"]
    assert (max_row.source, max_row.donor_id, int(max_row.operator_index), int(max_row.cells), int(max_row.donor_cells), int(max_row.groups_per_donor)) == (
        declared["repeat_ceiling_cell"]["source"], declared["repeat_ceiling_cell"]["donor_id"], declared["repeat_ceiling_cell"]["operator_index"],
        declared["repeat_ceiling_cell"]["group_cells"], declared["repeat_ceiling_cell"]["donor_cells"], declared["repeat_ceiling_cell"]["groups_per_donor"],
    )
    assert (min_row.source, min_row.donor_id, int(min_row.operator_index), int(min_row.cells), int(min_row.donor_cells), int(min_row.groups_per_donor)) == (
        declared["coverage_floor_group"]["source"], declared["coverage_floor_group"]["donor_id"], declared["coverage_floor_group"]["operator_index"],
        declared["coverage_floor_group"]["group_cells"], declared["coverage_floor_group"]["donor_cells"], declared["coverage_floor_group"]["groups_per_donor"],
    )


def test_selected_q_maximizes_target_component_under_frozen_linear_guardrails():
    _, _, _, g, horizon, proposal = _load()
    counts, p, q_source, q_group, q, (a, b, s) = _probabilities(g, proposal)
    H = float(horizon["total_presentations"])
    c = horizon["constraints_frozen_before_q_selection"]
    A, B = [], []
    for i in range(len(g)):
        A.append([H * (p[i] - q_source[i]), H * (q_group[i] - q_source[i])])
        B.append(c["max_expected_per_cell_exposure"] - H * q_source[i])
    for i in range(len(g)):
        n = counts[i]
        A.append([-H * n * (p[i] - q_source[i]), -H * n * (q_group[i] - q_source[i])])
        B.append(-(c["min_expected_donor_operator_group_presentations"] - H * n * q_source[i]))
    A.append([1.0, 1.0]); B.append(1.0)
    lp = linprog(c=[-1.0, 0.0], A_ub=np.asarray(A), b_ub=np.asarray(B), bounds=[(0, 1), (0, 1)], method="highs")
    assert lp.success
    assert float(lp.x[0]) == pytest.approx(a, abs=2e-12)
    assert float(lp.x[1]) == pytest.approx(b, abs=2e-12)
    assert 1.0 - float(lp.x[0]) - float(lp.x[1]) == pytest.approx(s, abs=2e-12)


def test_group_coverage_floor_has_explicit_zero_hit_union_bound():
    _, _, _, g, horizon, proposal = _load()
    coverage = horizon["coverage_interpretation"]
    expected = len(g) * math.exp(-16)
    assert coverage["per_group_zero_hit_upper_bound"] == pytest.approx(math.exp(-16), rel=1e-15)
    assert coverage["all_1400_group_zero_hit_union_bound"] == pytest.approx(expected, rel=1e-15)
    assert expected < 2e-4


def test_relational_v2_proposal_is_preserved_unchanged_and_triplet_budget_stays_unfrozen():
    _, _, _, g, horizon, proposal = _load()
    rel = proposal["relational"]
    assert rel["proposal_policy_id"] == "DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2"
    assert rel["proposal_equals_target"] is True
    assert rel["importance_correction_required"] is False
    assert rel["operator_role"] == "ADMISSIBILITY_BOUNDARY_ONLY"
    assert rel["triplet_budget"] is None
    assert rel["triplet_budget_is_scientific_weight"] is False
