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

import io as _io  # noqa: E402

import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as _rc  # noqa: E402

ADDRESS_SPACE = _rc.ADDRESS_SPACE_SIZE

CODE_SHA = "c" * 64
SUBSTRATE = {
    "population_closure_root_sha256": "1" * 64,
    "logical_row_authority_root_sha256": "2" * 64,
    "physical_read_plan_root_sha256": "3" * 64,
    "feature_authority_root_sha256": "4" * 64,
    "projection_root_sha256": "5" * 64,
    "population_raw_source_root_sha256": "6" * 64,
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
    rows = tc._build_rows_from_values(cells_by_donor={"H20.33.037": cells})
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
        tc._build_authority_from_values(tmp_path / "pkg",
                           cells_by_donor={"D1": [(9470, 3000)]},
                           substrate=substrate,
                           derivation_code_sha256=CODE_SHA,
                           candidate_donors=["D1"])
    assert tc.STOP_SUBSTRATE in str(excinfo.value)


def test_the_candidate_donor_set_must_match_exactly() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc._build_rows_from_values(cells_by_donor={"D1": [(9470, 3000)]},
                      candidate_donors=["D1", "D2"])
    assert tc.STOP_DONOR_SET in str(excinfo.value)


# --- roots and package ------------------------------------------------------

def test_the_root_is_deterministic_and_binds_the_formulas() -> None:
    rows = tc._build_rows_from_values(cells_by_donor={"D1": [(9470, 3000)]})
    before = tc.completeness_root(rows)
    assert before == tc.completeness_root(rows)
    original = tc.Q_DETECT_CELL_FORMULA
    try:
        tc.Q_DETECT_CELL_FORMULA = "count_nonzero(A) / 28061"
        assert tc.completeness_root(rows) != before
    finally:
        tc.Q_DETECT_CELL_FORMULA = original


def test_the_root_moves_when_a_summary_moves() -> None:
    a = tc._build_rows_from_values(cells_by_donor={"D1": [(9470, 3000)]})
    b = tc._build_rows_from_values(cells_by_donor={"D1": [(9470, 3001)]})
    assert tc.completeness_root(a) != tc.completeness_root(b)


def test_donor_identity_collisions_do_not_share_a_root() -> None:
    a = tc._build_rows_from_values(cells_by_donor={"a|b": [(100, 10)]})
    b = tc._build_rows_from_values(cells_by_donor={"a": [(100, 10)], "b": [(100, 10)]})
    assert tc.completeness_root(a) != tc.completeness_root(b)


def test_the_typed_float_framing_refuses_a_nonfinite_value() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc._typed_float(float("nan"))
    assert tc.STOP_FIELD_SCHEMA in str(excinfo.value)


def test_the_package_round_trips_with_external_parent_binding(tmp_path) -> None:
    summary = tc._build_authority_from_values(
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
    summary = tc._build_authority_from_values(
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
    tc._build_authority_from_values(tmp_path / "pkg", cells_by_donor={"D1": [(9470, 3000)]},
                       substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
                       candidate_donors=["D1"])
    meta = json.loads((tmp_path / "pkg" / tc.METADATA).read_text(encoding="utf-8"))
    assert meta["semantics"] == tc.SEMANTICS
    assert meta["thresholds_introduced"] is False
    assert meta["authority_failure_is_a_global_stop"] is True
    assert meta["q_depth_cell_formula"] == "log1p(source_library)"
    assert meta["q_detect_cell_formula"] == "count_nonzero(A) / 35076"
    assert "Recovered verbatim" in meta["formula_provenance"]
    assert meta["production_run_status"] == tc.PRODUCTION_RUN_STATUS_FIXTURE
    assert meta["pathology_values_read"] is False
    assert meta["real_execution_ready"] is False


def test_a_stored_authority_declaring_a_threshold_is_refused(tmp_path) -> None:
    """Guards against a later package asserting a cutoff was applied."""
    summary = tc._build_authority_from_values(
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
        tc._build_authority_from_values(out, cells_by_donor={"D1": [(9470, 3000)]},
                           substrate=SUBSTRATE, derivation_code_sha256=CODE_SHA,
                           candidate_donors=["D1"])
    assert tc.STOP_PACKAGE_MEMBER in str(excinfo.value)


# ---------------------------------------------------------------------------
# The decision-bearing values must come from authenticated parents.
#
# External review found the residual gap: build_authority accepted
# `cells_by_donor=[(source_library, projected_nonzero_count), ...]` while
# `substrate` was only a collection of parent-root STRINGS. So genuine roots
# could accompany entirely forged values, and Q_DEPTH and Q_DETECT would be
# computed from numbers no authority had ever produced. Root strings named the
# parents; they did not bind the values.
#
# The production path must therefore derive both summaries from authenticated
# objects: `source_library` out of the B2 logical row authority, and the
# 35,076-projection non-zero count out of authenticated counts payload bytes
# through the B1 projection.
# ---------------------------------------------------------------------------

import csv as _csv  # noqa: E402
import hashlib as _hashlib  # noqa: E402
import io as _io  # noqa: E402

if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))
import t0_v20_row_count_authority_v1 as _rc  # noqa: E402

ADDRESS_SPACE = _rc.ADDRESS_SPACE_SIZE


def _csr_npz(rows: int, width: int, entries) -> bytes:
    """A CSR payload shaped like a real Phase2 counts block."""
    import numpy as np

    per_row = {r: [] for r in range(rows)}
    for row_index, column, value in entries:
        per_row[row_index].append((column, value))
    data, indices, indptr = [], [], [0]
    for r in range(rows):
        for column, value in sorted(per_row[r]):
            indices.append(column)
            data.append(value)
        indptr.append(len(data))
    buffer = _io.BytesIO()
    np.savez(buffer,
             data=np.asarray(data, dtype=np.int32),
             indices=np.asarray(indices, dtype=np.int32),
             indptr=np.asarray(indptr, dtype=np.int32),
             shape=np.asarray([rows, width], dtype=np.int32),
             format=np.array(b"csr"))
    return buffer.getvalue()


# Two donors, two cells each. Columns are chosen so some fall inside the
# projected address set and some outside it, which is what makes the projection
# actually matter to Q_DETECT.
PROJECTED_POSITIONS = tuple(range(0, 200))
CELL_SPEC = [
    ("C1", "D1", 0, 9470, [(0, 3), (5, 1), (250, 7)]),
    ("C2", "D1", 1, 8123, [(1, 2), (300, 9)]),
    ("C3", "D2", 0, 7777, [(2, 4), (7, 6), (9, 1)]),
    ("C4", "D2", 1, 6000, [(400, 5)]),
]


def _payloads():
    """One block per (cell, row) pair, keyed by counts path."""
    blocks = {}
    for cell, _donor, row_index, _library, entries in CELL_SPEC:
        key = "op31/block-%s" % cell
        rows = row_index + 1
        blocks[key] = _csr_npz(
            rows, ADDRESS_SPACE,
            [(row_index, column, value) for column, value in entries])
    return blocks


def _authentic_logical():
    """A logical authority shaped like the B2 output, with real counts digests."""
    blocks = _payloads()
    rows = []
    payload_by_path = {}
    for index, (cell, donor, row_index, library, _entries) in enumerate(CELL_SPEC):
        key = "op31/block-%s" % cell
        payload = blocks[key]
        path = "%s.counts.npz" % key
        payload_by_path[path] = payload
        rows.append({
            "logical_index": index,
            "canonical_cell_id": cell,
            "donor_id": donor,
            "block_key": key,
            "row_index": row_index,
            "meta_path": "%s.meta.csv" % key,
            "meta_sha256": _hashlib.sha256(("meta-%s" % key).encode()).hexdigest(),
            "counts_path": path,
            "counts_sha256": _hashlib.sha256(payload).hexdigest(),
            "selection_row": 10 + index,
            "expression_row": 100 + index,
            "primary_row_weight": "8.06e-08",
            "source_library": library,
        })
    logical = {
        "rows": rows, "row_count": len(rows),
        "feature_authority_root_sha256": "4" * 64,
        "population_closure_root_sha256": "1" * 64,
        "logical_row_authority_root_sha256": None,
        "real_execution_ready": False,
    }
    logical["logical_row_authority_root_sha256"] = _rc._logical_root(
        rows, logical["feature_authority_root_sha256"],
        logical["population_closure_root_sha256"])
    return logical, payload_by_path


def _projection():
    return {"positions": list(PROJECTED_POSITIONS),
            "feature_authority_root_sha256": "4" * 64}


def _expected_detect(entries) -> float:
    inside = sum(1 for column, value in entries
                 if column in PROJECTED_POSITIONS and value != 0)
    return inside / float(tc.SCALAR_FEATURES)


def test_genuine_parent_roots_with_forged_values_cannot_produce_an_authority(
        tmp_path) -> None:
    """The exact defect. Real roots, invented numbers.

    The forged pair (9470, 3000) is the shape the old entrypoint accepted: a
    plausible library and a plausible projected non-zero count, accompanied by
    parent-root strings that are entirely genuine. There must be no parameter
    through which it can enter the production path.
    """
    logical, _payloads = _authentic_logical()
    forged = {"D1": [(9470, 3000)], "D2": [(7777, 2500)]}
    with pytest.raises(TypeError):
        tc.build_production_authority(
            tmp_path / "pkg",
            cells_by_donor=forged,
            substrate={
                "population_closure_root_sha256": logical[
                    "population_closure_root_sha256"],
                "logical_row_authority_root_sha256": logical[
                    "logical_row_authority_root_sha256"],
                "physical_read_plan_root_sha256": "3" * 64,
                "feature_authority_root_sha256": logical[
                    "feature_authority_root_sha256"],
                "projection_root_sha256": "5" * 64,
            },
            derivation_code_sha256=CODE_SHA,
            candidate_donors=["D1", "D2"])

    with pytest.raises(AssertionError) as excinfo:
        tc.refuse_detached_values(cells_by_donor=forged)
    assert tc.STOP_DETACHED_VALUES in str(excinfo.value)


def test_the_row_primitive_is_private(tmp_path) -> None:
    """It may remain for tests, but production must not be able to call it."""
    assert hasattr(tc, "_build_rows_from_values")
    assert not hasattr(tc, "build_rows")


def test_a_wrong_logical_root_expectation_stops(tmp_path) -> None:
    logical, payloads = _authentic_logical()
    projection = _projection()
    with pytest.raises(AssertionError):
        tc.build_production_authority(
            tmp_path / "pkg", logical=logical,
            expected_logical_root_sha256="f" * 64,
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=payloads, projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
            expected_projection_positions=len(projection["positions"]),
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])


def test_a_wrong_closure_root_expectation_stops(tmp_path) -> None:
    logical, payloads = _authentic_logical()
    projection = _projection()
    with pytest.raises(AssertionError):
        tc.build_production_authority(
            tmp_path / "pkg", logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256="f" * 64,
            counts_payload_bytes_by_path=payloads, projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
            expected_projection_positions=len(projection["positions"]),
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])


def test_a_tampered_counts_payload_stops(tmp_path) -> None:
    """The non-zero count must come from the bytes the logical row binds."""
    logical, payloads = _authentic_logical()
    projection = _projection()
    tampered = dict(payloads)
    victim = sorted(tampered)[0]
    tampered[victim] = _csr_npz(2, ADDRESS_SPACE, [(0, 0, 99)])
    with pytest.raises(AssertionError):
        tc.build_production_authority(
            tmp_path / "pkg", logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=tampered, projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])


def test_an_absent_counts_payload_stops(tmp_path) -> None:
    logical, payloads = _authentic_logical()
    projection = _projection()
    partial = dict(payloads)
    partial.pop(sorted(partial)[0])
    with pytest.raises(AssertionError):
        tc.build_production_authority(
            tmp_path / "pkg", logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=partial, projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])


def test_the_projection_root_is_injective_over_position_sets() -> None:
    a = tc.projection_root({"positions": [1, 2], "feature_authority_root_sha256": "4" * 64})
    b = tc.projection_root({"positions": [12], "feature_authority_root_sha256": "4" * 64})
    c = tc.projection_root({"positions": [1, 2], "feature_authority_root_sha256": "5" * 64})
    assert len({a, b, c}) == 3


# ---------------------------------------------------------------------------
# A fully lawful production fixture.
#
# The R5 contract requires the authenticated B2 closure (for its rows/nnz
# geometry), the logical authority, a verified physical read plan, the B1
# projection at its real 35,076 size, and a population byte-to-row raw-source
# proof covering every accepted row. Building all of that is the point: a
# production call cannot be assembled out of root strings any more.
# ---------------------------------------------------------------------------

MATRIX_ID = "sea_ad_mtg_rna_final_2026"
OPERATOR = 31

# expression_row == index here, so the synthetic H5AD rows line up with the
# logical rows the population proof must cover.
LAWFUL_CELLS = [
    ("C1", "D1", 0, 0, {0: 3, 5: 1, 250: 7}, {1: 6, 4: 5}),
    ("C2", "D1", 0, 1, {1: 2, 300: 9}, {2: 11}),
    ("C3", "D2", 0, 2, {2: 4, 7: 6, 9: 1}, {3: 11}),
]


def _csv_bytes(columns, rows) -> bytes:
    import csv as _csv
    buffer = _io.StringIO()
    writer = _csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _csr_payload(rows: int, width: int, entries) -> bytes:
    import numpy as np

    per_row = {r: [] for r in range(rows)}
    for row_index, column, value in entries:
        per_row[row_index].append((column, value))
    data, indices, indptr = [], [], [0]
    for r in range(rows):
        for column, value in sorted(per_row[r]):
            indices.append(column)
            data.append(value)
        indptr.append(len(data))
    buffer = _io.BytesIO()
    np.savez(buffer,
             data=np.asarray(data, dtype=np.int32),
             indices=np.asarray(indices, dtype=np.int32),
             indptr=np.asarray(indptr, dtype=np.int32),
             shape=np.asarray([rows, ADDRESS_SPACE], dtype=np.int32),
             format=np.array(b"csr"))
    return buffer.getvalue()


def _write_source_h5ad(path):
    """A synthetic MTG-shaped H5AD whose row sums are the bound libraries."""
    import h5py
    import numpy as np
    import t0_raw_source_row_authority_v1 as rs

    data, indices, indptr = [], [], [0]
    for _cell, _donor, _blk, _row, _addr, source_entries in LAWFUL_CELLS:
        for column in sorted(source_entries):
            indices.append(column)
            data.append(source_entries[column])
        indptr.append(len(data))

    with h5py.File(str(path), "w") as handle:
        layer = handle.create_group("layers").create_group("UMIs")
        layer.attrs["encoding-type"] = "csr_matrix"
        layer.attrs["encoding-version"] = "0.1.0"
        layer.attrs["shape"] = np.asarray(
            [len(LAWFUL_CELLS), rs.SOURCE_FEATURE_COUNT], dtype=np.int64)
        layer.create_dataset("data", data=np.asarray(data, dtype=np.float64))
        layer.create_dataset("indices", data=np.asarray(indices, dtype=np.int32))
        layer.create_dataset("indptr", data=np.asarray(indptr, dtype=np.int64))
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "exp_component_name"
        obs.create_dataset("exp_component_name", data=np.asarray(
            [c for c, _, _, _, _, _ in LAWFUL_CELLS], dtype=h5py.string_dtype()))
        donors = sorted({d for _, d, _, _, _, _ in LAWFUL_CELLS})
        node = obs.create_group("Donor ID")
        node.create_dataset("categories",
                            data=np.asarray(donors, dtype=h5py.string_dtype()))
        node.create_dataset("codes", data=np.asarray(
            [donors.index(d) for _, d, _, _, _, _ in LAWFUL_CELLS], dtype=np.int8))
        obs.create_dataset("Braak", data=np.asarray([5] * len(LAWFUL_CELLS),
                                                    dtype=np.int64))
    return path


def _lawful_inputs(tmp_path):
    """Every authenticated parent the R5 production contract requires."""
    import hashlib as _h
    import t0_raw_source_row_authority_v1 as rs

    # One op31 block holding all three cells.
    block = "op31/block-00000"
    meta = _csv_bytes(
        ["selection_row", "canonical_cell_id", "donor_id", "expression_row",
         "primary_row_weight", "source_library"],
        [[10 + i, cell, donor, row, "8.06e-08", sum(src.values())]
         for i, (cell, donor, _blk, row, _addr, src) in enumerate(LAWFUL_CELLS)])
    payload = _csr_payload(
        len(LAWFUL_CELLS), ADDRESS_SPACE,
        [(i, column, value)
         for i, (_c, _d, _b, _r, addr, _s) in enumerate(LAWFUL_CELLS)
         for column, value in addr.items()])
    nnz = sum(len(addr) for _c, _d, _b, _r, addr, _s in LAWFUL_CELLS)

    membership = _csv_bytes(
        ["source", "matrix_id", "operator_index", "local_row", "donor_id",
         "partition", "cell_id", "native_class", "broad_class", "stable_key"],
        [["SEA_AD", MATRIX_ID, OPERATOR, i, donor, "reader_fit", cell,
          "Immune", "Non-neuronal and Non-neural", 1000 + i]
         for i, (cell, donor, _b, _r, _a, _s) in enumerate(LAWFUL_CELLS)])
    manifest = _csv_bytes(
        ["block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
         "counts_path", "counts_sha256", "meta_path", "meta_sha256"],
        [[block, "SEA_AD", OPERATOR, MATRIX_ID, len(LAWFUL_CELLS), nnz,
          "%s.counts.npz" % block, _h.sha256(payload).hexdigest(),
          "%s.meta.csv" % block, _h.sha256(meta).hexdigest()]])

    closure = _rc.build_population_closure(
        membership_bytes=membership,
        expected_membership_sha256=_h.sha256(membership).hexdigest(),
        block_manifest_bytes=manifest,
        expected_block_manifest_sha256=_h.sha256(manifest).hexdigest(),
        meta_bytes_by_path={"%s.meta.csv" % block: meta},
        operator_index=OPERATOR, matrix_id=MATRIX_ID)
    logical = _rc.build_logical_row_authority(
        closure=closure, membership_bytes=membership,
        feature_authority_root_sha256="4" * 64)
    plan = _rc.build_physical_read_plan(logical=logical)

    asset = _write_source_h5ad(tmp_path / "source.h5ad")
    population = rs.prove_population_from_source_path(
        source_path=asset, logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_source_sha256=_h.sha256(asset.read_bytes()).hexdigest())

    # The projection at its real size, so the production default is satisfied.
    positions = list(range(tc.SCALAR_FEATURES))
    projection = {"positions": positions,
                  "feature_authority_root_sha256": "4" * 64}

    return {
        "closure": closure,
        "expected_closure_root_sha256": closure["population_closure_root_sha256"],
        "expected_membership_sha256": _h.sha256(membership).hexdigest(),
        "expected_block_manifest_sha256": _h.sha256(manifest).hexdigest(),
        "logical": logical,
        "expected_logical_root_sha256": logical["logical_row_authority_root_sha256"],
        "physical_plan": plan,
        "expected_physical_plan_root_sha256": plan["physical_read_plan_root_sha256"],
        "counts_payload_bytes_by_path": {"%s.counts.npz" % block: payload},
        "projection": projection,
        "expected_projection_root_sha256": tc.projection_root(projection),
        "population_raw_source": population,
        "expected_population_raw_source_root_sha256": population[
            "population_raw_source_root_sha256"],
        "expected_source_sha256": _h.sha256(asset.read_bytes()).hexdigest(),
        "derivation_code_sha256": CODE_SHA,
        "candidate_donors": ["D1", "D2"],
    }


def test_the_pre_r5_detached_value_derivation_cases_are_retired() -> None:
    """Six earlier derivation cases were written against the removed contract.

    They called `derive_rows_from_authenticated_parents` with a logical
    authority and a projection but no population raw-source proof and no
    closure-bound geometry, because the contract of the day did not require
    them. Under the R5 contract that call is refused by name, so those cases
    could only be kept by weakening the very requirement the external review
    asked for.

    Their properties -- projection-root binding, Q_DETECT counting only
    projected addresses, Q_DEPTH from the library, consumed cell identities in
    the root -- are all exercised against the lawful production fixture below,
    which additionally binds the closure, the physical plan and the population
    byte-to-row proof.
    """
    import inspect

    signature = inspect.signature(tc.derive_rows_from_authenticated_parents)
    for required in ("population_raw_source", "block_geometry",
                     "expected_projection_positions"):
        assert required in signature.parameters
    assert signature.parameters["expected_projection_positions"].default ==         tc.SCALAR_FEATURES


def test_the_lawful_production_path_succeeds(tmp_path) -> None:
    inputs = _lawful_inputs(tmp_path)
    summary = tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert summary["donor_count"] == 2
    assert summary["cells_consumed"] == len(LAWFUL_CELLS)
    assert summary["projection_positions"] == tc.SCALAR_FEATURES
    assert summary["real_execution_ready"] is False


def test_the_physical_plan_parent_is_the_verified_plan_not_the_logical_root(
        tmp_path) -> None:
    """Preserves the intent of the external review's physical-plan case.

    That case asserted the substrate must not record the logical root under the
    name `physical_read_plan_root_sha256`. It could not be run as written,
    because it also required the call to succeed with no raw-source proof and a
    one-position projection, which the same review's other two cases require to
    be refused. The intent is preserved here under the lawful contract.
    """
    inputs = _lawful_inputs(tmp_path)
    summary = tc.build_production_authority(tmp_path / "pkg", **inputs)
    meta = json.loads((tmp_path / "pkg" / tc.METADATA).read_text(encoding="utf-8"))
    recorded = meta["substrate"]["physical_read_plan_root_sha256"]
    assert recorded == inputs["expected_physical_plan_root_sha256"]
    assert recorded != inputs["expected_logical_root_sha256"]
    assert summary["real_execution_ready"] is False


def test_q_depth_uses_the_proven_library_not_the_stored_one(tmp_path) -> None:
    """The stored value is bound; only the proof shows it came from the H5 row."""
    import math

    inputs = _lawful_inputs(tmp_path)
    rows = tc.derive_rows_from_authenticated_parents(
        logical=inputs["logical"],
        expected_logical_root_sha256=inputs["expected_logical_root_sha256"],
        expected_closure_root_sha256=inputs["expected_closure_root_sha256"],
        counts_payload_bytes_by_path=inputs["counts_payload_bytes_by_path"],
        projection=inputs["projection"],
        expected_projection_root_sha256=inputs["expected_projection_root_sha256"],
        population_raw_source=inputs["population_raw_source"],
        expected_population_raw_source_root_sha256=inputs[
            "expected_population_raw_source_root_sha256"],
        block_geometry=inputs["closure"]["block_geometry"],
        expected_source_sha256=inputs["expected_source_sha256"])
    by_donor = {row["donor_id"]: row for row in rows}
    expected = (math.log1p(sum(LAWFUL_CELLS[0][5].values()))
                + math.log1p(sum(LAWFUL_CELLS[1][5].values()))) / 2.0
    assert by_donor["D1"]["Q_DEPTH"] == pytest.approx(expected)


def test_a_population_proof_for_a_different_logical_set_is_refused(
        tmp_path) -> None:
    """A proof set that does not cover this population must not be accepted."""
    inputs = _lawful_inputs(tmp_path)
    short = dict(inputs["population_raw_source"])
    short["proofs"] = inputs["population_raw_source"]["proofs"][:1]
    inputs["population_raw_source"] = short
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert "POPULATION_ROW_CARDINALITY" in str(excinfo.value)


def test_a_missing_population_proof_is_refused_by_name(tmp_path) -> None:
    inputs = _lawful_inputs(tmp_path)
    inputs["population_raw_source"] = None
    inputs["expected_population_raw_source_root_sha256"] = None
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert tc.STOP_RAW_SOURCE_PROOF in str(excinfo.value)


def test_a_missing_physical_plan_is_refused_by_name(tmp_path) -> None:
    inputs = _lawful_inputs(tmp_path)
    inputs["physical_plan"] = None
    inputs["expected_physical_plan_root_sha256"] = None
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert tc.STOP_PHYSICAL_PLAN in str(excinfo.value)


def test_a_missing_closure_is_refused_by_name(tmp_path) -> None:
    inputs = _lawful_inputs(tmp_path)
    inputs["closure"] = None
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert tc.STOP_GEOMETRY_NOT_CLOSED in str(excinfo.value)


def test_a_short_projection_is_refused_on_the_production_default(
        tmp_path) -> None:
    """35,076 unique in-range positions are mandatory; small ones are fixtures."""
    inputs = _lawful_inputs(tmp_path)
    small = {"positions": [0], "feature_authority_root_sha256": "4" * 64}
    inputs["projection"] = small
    inputs["expected_projection_root_sha256"] = tc.projection_root(small)
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(tmp_path / "pkg", **inputs)
    assert tc.STOP_PROJECTION_POSITIONS in str(excinfo.value)


def test_a_tampered_manifest_geometry_is_reconciled_against_the_payload(
        tmp_path) -> None:
    """Item 8: the reconciliation is mandatory, not an optional argument."""
    inputs = _lawful_inputs(tmp_path)
    geometry = {key: dict(value)
                for key, value in inputs["closure"]["block_geometry"].items()}
    geometry["op31/block-00000"]["nnz"] += 1
    closure = dict(inputs["closure"])
    closure["block_geometry"] = geometry
    with pytest.raises(AssertionError) as excinfo:
        tc.derive_rows_from_authenticated_parents(
            logical=inputs["logical"],
            expected_logical_root_sha256=inputs["expected_logical_root_sha256"],
            expected_closure_root_sha256=inputs["expected_closure_root_sha256"],
            counts_payload_bytes_by_path=inputs["counts_payload_bytes_by_path"],
            projection=inputs["projection"],
            expected_projection_root_sha256=inputs[
                "expected_projection_root_sha256"],
            population_raw_source=inputs["population_raw_source"],
            expected_population_raw_source_root_sha256=inputs[
                "expected_population_raw_source_root_sha256"],
            block_geometry=geometry,
            expected_source_sha256=inputs["expected_source_sha256"])
    assert "COUNTS_MATRIX_GEOMETRY" in str(excinfo.value)


def test_omitting_the_block_geometry_is_refused_by_name(tmp_path) -> None:
    inputs = _lawful_inputs(tmp_path)
    with pytest.raises(AssertionError) as excinfo:
        tc.derive_rows_from_authenticated_parents(
            logical=inputs["logical"],
            expected_logical_root_sha256=inputs["expected_logical_root_sha256"],
            expected_closure_root_sha256=inputs["expected_closure_root_sha256"],
            counts_payload_bytes_by_path=inputs["counts_payload_bytes_by_path"],
            projection=inputs["projection"],
            expected_projection_root_sha256=inputs[
                "expected_projection_root_sha256"],
            population_raw_source=inputs["population_raw_source"],
            expected_population_raw_source_root_sha256=inputs[
                "expected_population_raw_source_root_sha256"])
    assert tc.STOP_GEOMETRY_NOT_CLOSED in str(excinfo.value)


# ---------------------------------------------------------------------------
# The retired production terminal.
#
# `SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN` was true until the production B2 run
# executed and replayed. Leaving it in the writer would have stamped a false
# terminal into the first real package, so it is retired and refused. A stale
# status string that contradicts the artifact carrying it is the same class of
# error as any other unverified claim.
# ---------------------------------------------------------------------------

def test_the_retired_production_terminal_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        tc.assert_production_run_status_not_retired(
            tc.RETIRED_PRODUCTION_RUN_STATUS)
    assert tc.STOP_FIELD_SCHEMA in str(excinfo.value)
    assert "retired" in str(excinfo.value)


def test_only_the_two_lawful_production_statuses_are_accepted() -> None:
    for status in (tc.PRODUCTION_RUN_STATUS_POPULATION,
                   tc.PRODUCTION_RUN_STATUS_FIXTURE):
        assert tc.assert_production_run_status_not_retired(status) is True
    for status in ("", None, "SOMETHING_ELSE",
                   tc.RETIRED_PRODUCTION_RUN_STATUS):
        with pytest.raises(AssertionError):
            tc.assert_production_run_status_not_retired(status)


def test_a_package_recording_the_retired_terminal_is_refused_on_load(
        tmp_path) -> None:
    """The regression the external review asked for."""
    import json as _json

    inputs = _lawful_inputs(tmp_path)
    summary = tc.build_production_authority(tmp_path / "pkg", **inputs)
    path = tmp_path / "pkg" / tc.METADATA
    meta = _json.loads(path.read_text(encoding="utf-8"))
    meta["production_run_status"] = tc.RETIRED_PRODUCTION_RUN_STATUS
    path.write_text(_json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    # Mutating a member moves the package root, so the root check would fire
    # first. Recompute it so the load actually reaches the status guard and the
    # test exercises what it claims to.
    members = {name: (tmp_path / "pkg" / name).read_bytes()
               for name in tc.MEMBERS}
    with pytest.raises(AssertionError) as excinfo:
        tc.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=tc.package_root(members),
            expected_completeness_root_sha256=summary[
                "completeness_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert tc.STOP_FIELD_SCHEMA in str(excinfo.value)
    assert "retired" in str(excinfo.value)


def test_the_module_docstring_no_longer_says_production_b2_is_unauthorized() -> None:
    doc = tc.__doc__ or ""
    assert "the production B2 run is not authorized" not in doc
    assert "synthetic fixtures only" not in doc
    assert "executed and replayed" in doc


def test_a_fixture_sized_run_does_not_claim_the_real_population(
        tmp_path) -> None:
    """The status is decided by what was covered, not by a caller flag."""
    inputs = _lawful_inputs(tmp_path)
    summary = tc.build_production_authority(tmp_path / "pkg", **inputs)
    # The lawful fixture covers three cells and two donors, not 20,804 and 46.
    assert summary["derived_over_the_real_population"] is False
    assert summary["production_run_status"] == tc.PRODUCTION_RUN_STATUS_FIXTURE


def test_the_population_claim_requires_the_frozen_geometry() -> None:
    """All three of donors, rows and projection size must be the real ones."""
    assert tc.PRODUCTION_DONOR_COUNT == 46
    assert tc.PRODUCTION_POPULATION_ROWS == 20_804
    assert tc.SCALAR_FEATURES == 35_076
