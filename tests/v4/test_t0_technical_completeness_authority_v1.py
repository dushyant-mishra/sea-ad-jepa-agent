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
    assert meta["production_run_status"] == "SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN"
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


def test_the_production_path_derives_summaries_from_authenticated_parents(
        tmp_path) -> None:
    """Objects and bytes in, summaries out. No caller-supplied value tuples."""
    logical, payloads = _authentic_logical()
    projection = _projection()
    summary = tc.build_production_authority(
        tmp_path / "pkg",
        logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical["population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads,
        projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection),
        derivation_code_sha256=CODE_SHA,
        candidate_donors=["D1", "D2"])
    assert summary["donor_count"] == 2
    assert summary["cells_consumed"] == len(CELL_SPEC)
    assert summary["real_execution_ready"] is False


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
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])


def test_a_wrong_projection_root_expectation_stops(tmp_path) -> None:
    """The 35,076 projection is a decision-bearing parent, so it is bound."""
    logical, payloads = _authentic_logical()
    projection = _projection()
    with pytest.raises(AssertionError) as excinfo:
        tc.build_production_authority(
            tmp_path / "pkg", logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=payloads, projection=projection,
            expected_projection_root_sha256="f" * 64,
            derivation_code_sha256=CODE_SHA, candidate_donors=["D1", "D2"])
    assert tc.STOP_PROJECTION_ROOT in str(excinfo.value)


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


def test_q_detect_counts_only_projected_addresses(tmp_path) -> None:
    """A non-zero outside the projected set must not raise Q_DETECT.

    C1 has three stored values, only two of which lie inside the projected
    address set, so its detection rate is 2/35076 and not 3/35076. Counting the
    address-space non-zeros instead would be a rate over the wrong universe.
    """
    logical, payloads = _authentic_logical()
    projection = _projection()
    rows = tc.derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical["population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads, projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection))
    by_donor = {row["donor_id"]: row for row in rows}
    expected_d1 = (_expected_detect(CELL_SPEC[0][4])
                   + _expected_detect(CELL_SPEC[1][4])) / 2.0
    assert by_donor["D1"]["Q_DETECT"] == pytest.approx(expected_d1)
    # C4's only stored value is outside the projection, so its rate is zero.
    expected_d2 = (_expected_detect(CELL_SPEC[2][4]) + 0.0) / 2.0
    assert by_donor["D2"]["Q_DETECT"] == pytest.approx(expected_d2)


def test_q_depth_uses_the_bound_source_library(tmp_path) -> None:
    import math

    logical, payloads = _authentic_logical()
    projection = _projection()
    rows = tc.derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical["population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads, projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection))
    by_donor = {row["donor_id"]: row for row in rows}
    expected = (math.log1p(9470) + math.log1p(8123)) / 2.0
    assert by_donor["D1"]["Q_DEPTH"] == pytest.approx(expected)


def test_the_derived_rows_carry_the_cell_identities_they_consumed(
        tmp_path) -> None:
    """Binding cell identity is what ties a summary to a population."""
    logical, payloads = _authentic_logical()
    projection = _projection()
    rows = tc.derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical["population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads, projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection))
    by_donor = {row["donor_id"]: row for row in rows}
    assert by_donor["D1"]["cell_ids"] == ("C1", "C2")
    assert by_donor["D2"]["cell_ids"] == ("C3", "C4")


def test_the_completeness_root_binds_the_consumed_cell_identities() -> None:
    logical, payloads = _authentic_logical()
    projection = _projection()
    rows = tc.derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical["population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads, projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection))
    baseline = tc.completeness_root(rows)
    moved = [dict(row) for row in rows]
    moved[0] = dict(moved[0])
    moved[0]["cell_ids"] = ("C1", "C9")
    assert tc.completeness_root(moved) != baseline


def test_the_projection_root_is_injective_over_position_sets() -> None:
    a = tc.projection_root({"positions": [1, 2], "feature_authority_root_sha256": "4" * 64})
    b = tc.projection_root({"positions": [12], "feature_authority_root_sha256": "4" * 64})
    c = tc.projection_root({"positions": [1, 2], "feature_authority_root_sha256": "5" * 64})
    assert len({a, b, c}) == 3
