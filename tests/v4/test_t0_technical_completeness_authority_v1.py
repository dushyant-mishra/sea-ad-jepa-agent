"""Adversarial cases for the T0 technical-completeness authority.

Two properties carry the weight.

The formulas must be the recovered ones, not paraphrases. So the cases check
`log1p(source_library)` and `count_nonzero(A) / 35076` against independently
computed values, and check that Q_DETECT is refused when taken over any universe
other than the full 35,076-address projection.

The predicate must stay threshold-free. The realistic failure is drift -- a
plausible quality floor added later -- so the guard is tested by attempting to
introduce one. And an authority or provenance failure must raise rather than
appear as `technical_complete=False`, because laundering a provenance failure into
an eligibility outcome would turn eligibility into a way to drop inconvenient
donors.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_technical_completeness_authority_v1 as tc  # noqa: E402

CODE_SHA = "c" * 64
SUBSTRATE = {
    "population_closure_root_sha256": "1" * 64,
    "logical_row_authority_root_sha256": "2" * 64,
    "physical_read_plan_root_sha256": "3" * 64,
    "feature_authority_root_sha256": "4" * 64,
    "projection_root_sha256": "5" * 64,
}


# --- the exact recovered formulas -------------------------------------------

@pytest.mark.parametrize("library", [1, 67, 9470, 638150])
def test_q_depth_is_log1p_of_the_source_library(library) -> None:
    assert tc.cell_q_depth(library) == math.log1p(library)


def test_q_detect_is_nonzero_over_the_full_projection() -> None:
    row = [1, 0, 2, 0, 3] + [0] * (tc.SCALAR_FEATURES - 5)
    assert tc.cell_q_detect(row) == 3 / tc.SCALAR_FEATURES


def test_the_q_detect_denominator_is_35076_not_the_scoring_subset() -> None:
    """Q_DETECT covers the measurement universe, not the 28,061 SCORING subset."""
    assert tc.SCALAR_FEATURES == 35_076
    assert "28,061" in tc.Q_DETECT_UNIVERSE or "28061" in tc.Q_DETECT_UNIVERSE
    assert tc.Q_DETECT_CELL_FORMULA == "count_nonzero(A) / 35076"
    assert tc.Q_DEPTH_CELL_FORMULA == "log1p(source_library)"


@pytest.mark.parametrize("width", [41_238, 28_061, 35_075, 35_077, 0])
def test_a_projection_of_the_wrong_width_is_refused(width) -> None:
    """A rate over the wrong denominator is not Q_DETECT."""
    with pytest.raises(AssertionError) as excinfo:
        tc.cell_q_detect([0] * width)
    assert tc.STOP_PROJECTION_WIDTH in str(excinfo.value)


def test_a_nonzero_count_outside_the_projection_range_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc.cell_q_detect_from_nonzero_count(tc.SCALAR_FEATURES + 1)
    assert tc.STOP_PROJECTION_WIDTH in str(excinfo.value)


def test_the_precomputed_count_agrees_with_the_row_form() -> None:
    row = [1, 0, 2] + [0] * (tc.SCALAR_FEATURES - 3)
    assert tc.cell_q_detect(row) == tc.cell_q_detect_from_nonzero_count(2)


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "2.0", "", None])
def test_an_unusable_source_library_stops(bad) -> None:
    """log1p of a non-positive or non-integral library would be wrong or undefined."""
    with pytest.raises(AssertionError) as excinfo:
        tc.cell_q_depth(bad)
    assert tc.STOP_LIBRARY in str(excinfo.value)


@pytest.mark.parametrize("bad", [-1, 1.5, float("nan")])
def test_non_integral_or_negative_projected_counts_stop(bad) -> None:
    row = [bad] + [0] * (tc.SCALAR_FEATURES - 1)
    with pytest.raises(AssertionError) as excinfo:
        tc.cell_q_detect(row)
    assert tc.STOP_COUNTS in str(excinfo.value)


def test_donor_summaries_are_arithmetic_means() -> None:
    summary = tc.donor_summaries([(1.0, 0.1), (3.0, 0.3)], donor_id="D1")
    assert summary["Q_DEPTH"] == pytest.approx(2.0)
    assert summary["Q_DETECT"] == pytest.approx(0.2)


def test_a_donor_with_no_authenticated_cell_stops() -> None:
    """At least one cell is a conjunct of the frozen predicate."""
    with pytest.raises(AssertionError) as excinfo:
        tc.donor_summaries([], donor_id="D1")
    assert tc.STOP_NO_CELLS in str(excinfo.value)


# --- the predicate stays threshold-free -------------------------------------

def test_the_predicate_is_threshold_free() -> None:
    assert tc.assert_predicate_is_threshold_free() is True
    assert tc.SEMANTICS == "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY"


def test_a_low_but_defined_donor_is_technically_complete() -> None:
    """This is the whole point of a definedness predicate.

    A donor with a tiny library and a single detected address has poor data and
    is still technically complete, because its summaries are defined. Removing it
    would require a quality cutoff that V18 never froze.
    """
    summary = tc.donor_summaries([(tc.cell_q_depth(1),
                                   tc.cell_q_detect_from_nonzero_count(1))],
                                 donor_id="POOR")
    assert tc.technical_complete(summary, donor_id="POOR") is True


def test_a_sub_tail_floor_donor_is_technically_complete() -> None:
    """The 80-cell floor is tail-only and must not reach this predicate."""
    cells = [(9470, 3000)] * 67
    rows = tc.build_rows(cells_by_donor={"H20.33.037": cells})
    assert rows[0]["cells"] == 67
    assert rows[0]["technical_complete"] is True


def test_an_undefined_summary_is_not_complete() -> None:
    assert tc.technical_complete({"Q_DEPTH": float("nan"), "Q_DETECT": 0.5},
                                 donor_id="D1") is False
    assert tc.technical_complete({"Q_DEPTH": 1.0, "Q_DETECT": float("inf")},
                                 donor_id="D1") is False
    assert tc.technical_complete({"Q_DEPTH": 1.0}, donor_id="D1") is False


def test_a_q_detect_outside_the_unit_range_is_not_complete() -> None:
    """Out of [0,1] means the wrong universe, not a low value."""
    assert tc.technical_complete({"Q_DEPTH": 1.0, "Q_DETECT": 1.5},
                                 donor_id="D1") is False
    assert tc.technical_complete({"Q_DEPTH": 1.0, "Q_DETECT": -0.1},
                                 donor_id="D1") is False


def test_changing_the_semantics_label_is_refused() -> None:
    original = tc.SEMANTICS
    try:
        tc.SEMANTICS = "QUALITY_FILTER"
        with pytest.raises(AssertionError) as excinfo:
            tc.assert_predicate_is_threshold_free()
        assert tc.STOP_THRESHOLD in str(excinfo.value)
    finally:
        tc.SEMANTICS = original


def test_editing_the_forbidden_cutoff_list_is_refused() -> None:
    original = tc.FORBIDDEN_CUTOFFS
    try:
        tc.FORBIDDEN_CUTOFFS = ("SOMETHING_ELSE",)
        with pytest.raises(AssertionError) as excinfo:
            tc.assert_predicate_is_threshold_free()
        assert tc.STOP_THRESHOLD in str(excinfo.value)
    finally:
        tc.FORBIDDEN_CUTOFFS = original


def test_downgrading_the_global_stop_rule_is_refused() -> None:
    original = tc.AUTHORITY_FAILURE_IS_A_GLOBAL_STOP
    try:
        tc.AUTHORITY_FAILURE_IS_A_GLOBAL_STOP = False
        with pytest.raises(AssertionError) as excinfo:
            tc.assert_predicate_is_threshold_free()
        assert tc.STOP_THRESHOLD in str(excinfo.value)
    finally:
        tc.AUTHORITY_FAILURE_IS_A_GLOBAL_STOP = original


# --- fail-closed: provenance failures raise, never record False -------------

@pytest.mark.parametrize("missing", [
    "population_closure_root_sha256",
    "logical_row_authority_root_sha256",
    "physical_read_plan_root_sha256",
    "feature_authority_root_sha256",
    "projection_root_sha256",
])
def test_a_missing_parent_identity_is_a_global_stop(missing) -> None:
    """It must raise, not silently mark donors technically incomplete."""
    substrate = dict(SUBSTRATE)
    substrate.pop(missing)
    with pytest.raises(AssertionError) as excinfo:
        tc.assert_substrate_lawful(substrate=substrate)
    assert tc.STOP_SUBSTRATE in str(excinfo.value)
    assert missing in str(excinfo.value)


def test_a_malformed_parent_identity_is_a_global_stop() -> None:
    substrate = dict(SUBSTRATE)
    substrate["projection_root_sha256"] = "not-a-digest"
    with pytest.raises(AssertionError) as excinfo:
        tc.assert_substrate_lawful(substrate=substrate)
    assert tc.STOP_SUBSTRATE in str(excinfo.value)


def test_an_unlawful_substrate_prevents_the_authority_being_built(tmp_path) -> None:
    substrate = dict(SUBSTRATE)
    substrate.pop("projection_root_sha256")
    with pytest.raises(AssertionError) as excinfo:
        tc._build_authority_from_precomputed_cells_fixture(tmp_path / "pkg",
                           cells_by_donor={"D1": [(9470, 3000)]},
                           substrate=substrate,
                           derivation_code_sha256=CODE_SHA,
                           candidate_donors=["D1"])
    assert tc.STOP_SUBSTRATE in str(excinfo.value)


def test_the_candidate_donor_set_must_match_exactly() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc.build_rows(cells_by_donor={"D1": [(9470, 3000)]},
                      candidate_donors=["D1", "D2"])
    assert tc.STOP_DONOR_SET in str(excinfo.value)


# --- roots and package ------------------------------------------------------

def test_the_root_is_deterministic_and_binds_the_formulas() -> None:
    rows = tc.build_rows(cells_by_donor={"D1": [(9470, 3000)]})
    before = tc.completeness_root(rows)
    assert before == tc.completeness_root(rows)
    original = tc.Q_DETECT_CELL_FORMULA
    try:
        tc.Q_DETECT_CELL_FORMULA = "count_nonzero(A) / 28061"
        assert tc.completeness_root(rows) != before
    finally:
        tc.Q_DETECT_CELL_FORMULA = original


def test_the_root_moves_when_a_summary_moves() -> None:
    a = tc.build_rows(cells_by_donor={"D1": [(9470, 3000)]})
    b = tc.build_rows(cells_by_donor={"D1": [(9470, 3001)]})
    assert tc.completeness_root(a) != tc.completeness_root(b)


def test_donor_identity_collisions_do_not_share_a_root() -> None:
    a = tc.build_rows(cells_by_donor={"a|b": [(100, 10)]})
    b = tc.build_rows(cells_by_donor={"a": [(100, 10)], "b": [(100, 10)]})
    assert tc.completeness_root(a) != tc.completeness_root(b)


def test_the_typed_float_framing_refuses_a_nonfinite_value() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc._typed_float(float("nan"))
    assert tc.STOP_FIELD_SCHEMA in str(excinfo.value)


def test_the_package_round_trips_with_external_parent_binding(tmp_path) -> None:
    summary = tc._build_authority_from_precomputed_cells_fixture(
        tmp_path / "pkg",
        cells_by_donor={"D1": [(9470, 3000), (8123, 2500)],
                        "D2": [(7777, 1000)]},
        substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
        candidate_donors=["D1", "D2"])
    assert summary["donor_count"] == 2
    assert summary["technically_complete_donors"] == 2
    loaded = tc.load_authority(
        tmp_path / "pkg",
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_completeness_root_sha256=summary["completeness_root_sha256"],
        expected_parent_contract_root_sha256=summary["parent_contract_root_sha256"])
    assert len(loaded["records"]) == 2
    assert loaded["metadata"]["real_execution_ready"] is False


def test_the_loader_refuses_a_wrong_parent_contract_root(tmp_path) -> None:
    summary = tc._build_authority_from_precomputed_cells_fixture(
        tmp_path / "pkg", cells_by_donor={"D1": [(9470, 3000)]},
        substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
        candidate_donors=["D1"])
    with pytest.raises(AssertionError) as excinfo:
        tc.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_completeness_root_sha256=summary["completeness_root_sha256"],
            expected_parent_contract_root_sha256="f" * 64)
    assert tc.STOP_PARENT_IDENTITY in str(excinfo.value)


def test_the_parent_contract_root_moves_with_any_parent(tmp_path) -> None:
    a = tc.parent_contract_root(substrate=SUBSTRATE,
                                derivation_code_sha256=CODE_SHA)
    other = dict(SUBSTRATE)
    other["projection_root_sha256"] = "6" * 64
    b = tc.parent_contract_root(substrate=other, derivation_code_sha256=CODE_SHA)
    c = tc.parent_contract_root(substrate=SUBSTRATE,
                                derivation_code_sha256="d" * 64)
    assert len({a, b, c}) == 3


def test_the_metadata_declares_its_synthetic_status_and_formulas(tmp_path) -> None:
    tc._build_authority_from_precomputed_cells_fixture(tmp_path / "pkg", cells_by_donor={"D1": [(9470, 3000)]},
                       substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
                       candidate_donors=["D1"])
    meta = json.loads((tmp_path / "pkg" / tc.METADATA).read_text(encoding="utf-8"))
    assert meta["semantics"] == tc.SEMANTICS
    assert meta["thresholds_introduced"] is False
    assert meta["authority_failure_is_a_global_stop"] is True
    assert meta["q_depth_cell_formula"] == "log1p(source_library)"
    assert meta["q_detect_cell_formula"] == "count_nonzero(A) / 35076"
    assert "Recovered verbatim" in meta["formula_provenance"]
    assert meta["production_run_status"] == "SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN"
    assert meta["pathology_values_read"] is False
    assert meta["real_execution_ready"] is False


def test_a_stored_authority_declaring_a_threshold_is_refused(tmp_path) -> None:
    """Guards against a later package asserting a cutoff was applied."""
    summary = tc._build_authority_from_precomputed_cells_fixture(
        tmp_path / "pkg", cells_by_donor={"D1": [(9470, 3000)]},
        substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
        candidate_donors=["D1"])
    path = tmp_path / "pkg" / tc.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["thresholds_introduced"] = True
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError):
        tc.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_completeness_root_sha256=summary["completeness_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])


def test_writing_into_a_nonempty_directory_is_refused(tmp_path) -> None:
    out = tmp_path / "pkg"
    out.mkdir()
    (out / "stray.txt").write_text("x", encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        tc._build_authority_from_precomputed_cells_fixture(out, cells_by_donor={"D1": [(9470, 3000)]},
                           substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
                           candidate_donors=["D1"])
    assert tc.STOP_PACKAGE_MEMBER in str(excinfo.value)



# R4 dataset-bound production-input attacks ---------------------------------

def _tiny_csr_npz(rows: int, width: int, entries) -> bytes:
    import numpy as np

    by_row = [[] for _ in range(rows)]
    for row, column, value in entries:
        by_row[int(row)].append((int(column), int(value)))
    data, indices, indptr = [], [], [0]
    for record in by_row:
        for column, value in sorted(record):
            indices.append(column)
            data.append(value)
        indptr.append(len(data))
    buffer = io.BytesIO()
    np.savez(
        buffer,
        data=np.asarray(data, dtype=np.int32),
        indices=np.asarray(indices, dtype=np.int32),
        indptr=np.asarray(indptr, dtype=np.int32),
        shape=np.asarray([rows, width], dtype=np.int32),
        format=np.array(b"csr"),
    )
    return buffer.getvalue()


def test_dataset_bound_builder_does_not_accept_detached_cells_by_donor(
        tmp_path: Path) -> None:
    """Genuine-looking parent roots cannot carry arbitrary technical values."""
    with pytest.raises(TypeError):
        tc.build_authority(
            tmp_path / "pkg",
            cells_by_donor={"D1": [(9470, 3000)]},
            substrate=SUBSTRATE,
            derivation_code_sha256=CODE_SHA,
            candidate_donors=["D1"],
        )


def test_q_detect_numerator_is_derived_from_authenticated_phase2_block(
        tmp_path: Path) -> None:
    """The production helper reads the bound NPZ and the exact 35,076 B1 indices."""
    relative = Path("op31") / "block-00000.counts.npz"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    payload = _tiny_csr_npz(
        1, 41_238,
        [(0, 0, 5), (0, 35_075, 3), (0, 40_000, 9)],
    )
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    logical = {"rows": [{
        "counts_path": relative.as_posix(),
        "counts_sha256": digest,
        "row_index": 0,
    }]}
    feature_authority = {
        "projection": [
            {"molecular_address_index": index}
            for index in range(tc.SCALAR_FEATURES)
        ]
    }
    result = tc._projected_nonzero_counts_from_authenticated_blocks(
        logical=logical,
        feature_authority=feature_authority,
        phase2_expression_root=tmp_path,
    )
    assert result == {0: 2}


def test_q_detect_helper_refuses_same_path_with_wrong_bound_digest(
        tmp_path: Path) -> None:
    relative = Path("op31") / "block-00000.counts.npz"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(_tiny_csr_npz(1, 41_238, [(0, 0, 5)]))
    logical = {"rows": [{
        "counts_path": relative.as_posix(),
        "counts_sha256": "0" * 64,
        "row_index": 0,
    }]}
    feature_authority = {
        "projection": [
            {"molecular_address_index": index}
            for index in range(tc.SCALAR_FEATURES)
        ]
    }
    with pytest.raises(AssertionError, match="SUBSTRATE_NOT_LAWFUL"):
        tc._projected_nonzero_counts_from_authenticated_blocks(
            logical=logical,
            feature_authority=feature_authority,
            phase2_expression_root=tmp_path,
        )
