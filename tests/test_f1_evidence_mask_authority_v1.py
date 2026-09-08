"""The frozen F1 evidence-mask construction, checked against its own authority.

An independent review asked whether the producer's evidence mask was the frozen
construction. It was not. The previous implementation took the first measured
addresses in index order up to a rounded percentage, which is wrong in three
independent ways: it did not withhold the query's own scalar, it ordered by gene
address rather than by the seeded digest, and it used `round` where the
authority specifies `floor`. Each of those alone changes which addresses a
student sees, so every count would still have reconciled while the numbers were
wrong.

These tests bind the implementation to the controlling contract bytes and then
attack each of the three properties separately.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import f1_evidence_mask_authority_v1 as ev  # noqa: E402

CONTRACT_REL = ("outputs/contextual_teacher_target_v1_f1_preflight_20260901/"
                "CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md")
AUTHORITY_ROOT_ENV = "F1_PREFREEZE_AUTHORITY_ROOT"
_EXPLICIT = os.environ.get(AUTHORITY_ROOT_ENV)
CANONICAL_ROOTS = ((Path(_EXPLICIT),) if _EXPLICIT
                   else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), ROOT))
REQUIRE_AUTHORITIES = os.environ.get("F1_PREFREEZE_REQUIRE_AUTHORITIES") == "1"

AUTHORITY_DEPENDENT_TESTS = (
    "test_the_implementation_is_bound_to_the_controlling_contract_bytes",
)


def _authority(relative: str) -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    message = ("NOT_MEASURABLE (not a pass): evidence-mask contract not reachable: %s. "
               "Set %s, or F1_PREFREEZE_REQUIRE_AUTHORITIES=1 to fail instead."
               % (relative, AUTHORITY_ROOT_ENV))
    if REQUIRE_AUTHORITIES:
        pytest.fail(message)
    pytest.skip(message)


def _row(width: int = 20, query: int = 6) -> tuple[np.ndarray, int]:
    state = np.array([1, 1, 0, 1, 2, 1, 1, 1, 0, 1, 1, 2, 1, 1, 1, 0, 1, 1, 1, 1],
                     dtype=np.uint8)
    assert state.size == width
    assert int(state[query]) == ev.MEASURED_SCALAR
    return state, query


def test_the_implementation_is_bound_to_the_controlling_contract_bytes() -> None:
    """Digest plus the decisive sentences, so a same-length swap cannot pass."""
    contract = _authority(CONTRACT_REL)
    raw = contract.read_bytes()
    out = ev.verify_contract_authority(raw.decode("utf-8"),
                                       contract_sha256=hashlib.sha256(raw).hexdigest())
    assert out["contract_sha256"] == ev.EVIDENCE_MASK_CONTRACT_SHA256
    assert out["seed_sha256"] == ev.EVIDENCE_MASK_SEED_SHA256
    assert out["levels"] == [20, 40, 60, 80, 100]
    assert out["primary_level_percent"] == 60
    assert out["bound_phrases"] >= 7
    with pytest.raises(AssertionError, match="CONTRACT_DIGEST"):
        ev.verify_contract_authority(raw.decode("utf-8"), contract_sha256="0" * 64)
    with pytest.raises(AssertionError, match="CONTRACT_TEXT"):
        ev.verify_contract_authority("a different document of the same idea",
                                     contract_sha256=ev.EVIDENCE_MASK_CONTRACT_SHA256)


def test_eligible_context_is_measured_scalar_excluding_the_query() -> None:
    state, q = _row()
    eligible = ev.eligible_context(state, q)
    assert q not in set(eligible.tolist())
    assert set(eligible.tolist()) == set(np.flatnonzero(state == 1).tolist()) - {q}
    assert not any(int(state[j]) in (0, 2) for j in eligible.tolist())


def test_a_query_that_is_not_scalar_measured_is_rejected() -> None:
    state, _ = _row()
    for bad_query in (2, 4):            # state 0 and state 2
        with pytest.raises(ValueError, match="QUERY_NOT_SCALAR_MEASURED"):
            ev.eligible_context(state, bad_query)


def test_selected_count_is_floor_not_round() -> None:
    """`floor(p*|E|/100)`. With |E|=14, 20% is 2, not the rounded 3."""
    assert ev.selected_count(20, 14) == 2
    assert int(round(14 * 0.20)) == 3, "the rounded answer differs, which is the point"
    assert ev.selected_count(40, 14) == 5
    assert ev.selected_count(60, 14) == 8
    assert ev.selected_count(80, 14) == 11
    assert ev.selected_count(100, 14) == 14
    # 100% is always all of E for any size.
    for size in (1, 3, 7, 399, 4096):
        assert ev.selected_count(100, size) == size
    with pytest.raises(ValueError, match="LEVEL_NOT_AUTHORIZED"):
        ev.selected_count(50, 14)


def test_the_ordering_is_seeded_and_not_address_order() -> None:
    """Address order was the old bug; the authority orders by digest bytes."""
    state, q = _row()
    eligible = ev.eligible_context(state, q)
    ordering = ev.seeded_ordering(eligible, row_locator="HVS::abc#356", query_address=904)
    assert sorted(ordering.tolist()) == sorted(eligible.tolist())
    assert not np.array_equal(ordering, np.sort(ordering)), (
        "a seeded ordering that happened to be address order would not "
        "distinguish the implementations")
    # The ordering depends on the row locator and the query address.
    other_row = ev.seeded_ordering(eligible, row_locator="HVS::zzz#999", query_address=904)
    other_q = ev.seeded_ordering(eligible, row_locator="HVS::abc#356", query_address=17)
    assert not np.array_equal(ordering, other_row)
    assert not np.array_equal(ordering, other_q)
    # And it is deterministic.
    assert np.array_equal(
        ordering, ev.seeded_ordering(eligible, row_locator="HVS::abc#356",
                                     query_address=904))


def test_the_levels_are_nested_prefixes_of_one_ordering() -> None:
    state, q = _row()
    built = ev.build_row_evidence_masks(state, q, row_locator="HVS::abc#356",
                                        query_address=904)
    for lower, upper in zip(ev.EVIDENCE_LEVELS, ev.EVIDENCE_LEVELS[1:]):
        low = built["masks"][lower]
        high = built["masks"][upper]
        assert not np.any(low & ~high), (lower, upper)
    assert built["selected_counts"] == {20: 2, 40: 5, 60: 8, 80: 11, 100: 14}


def test_the_query_scalar_is_withheld_at_every_level() -> None:
    state, q = _row()
    built = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    for level in ev.EVIDENCE_LEVELS:
        assert not bool(built["masks"][level][q]), level
    assert not bool(built["teacher_rich_mask"][q])


def test_no_level_ever_selects_a_non_scalar_address() -> None:
    state, q = _row()
    built = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    measured = state == ev.MEASURED_SCALAR
    for level in ev.EVIDENCE_LEVELS:
        assert not np.any(built["masks"][level] & ~measured), level
    assert not np.any(built["teacher_rich_mask"] & ~measured)


def test_the_teacher_rich_target_is_all_eligible_context() -> None:
    """Why the teacher state is evidence-invariant and there are 43,108 of them."""
    state, q = _row()
    built = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    assert np.array_equal(built["masks"][100], built["teacher_rich_mask"])
    assert int(built["teacher_rich_mask"].sum()) == built["eligible_size"]


def test_selection_never_consults_an_expression_value() -> None:
    """A measured zero has the same eligibility and rank as a nonzero scalar.

    The authority is explicit about this, and it matters: a selection that
    depended on expression would leak the very signal F1 is estimating.
    """
    state, q = _row()
    first = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    # There is no expression argument to pass, which is the structural proof;
    # the behavioural proof is that the module's signature takes only state,
    # query and identity.
    import inspect
    parameters = set(inspect.signature(ev.build_row_evidence_masks).parameters)
    assert parameters == {"physical_state_row", "query_index", "row_locator",
                          "query_address", "seed"}
    assert "expression" not in " ".join(parameters)
    second = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    for level in ev.EVIDENCE_LEVELS:
        assert np.array_equal(first["masks"][level], second["masks"][level])


def test_lawfulness_assertions_actually_fire() -> None:
    """Guard the guards: each terminal condition must be detected."""
    state, q = _row()
    built = ev.build_row_evidence_masks(state, q, row_locator="r", query_address=1)
    masks = {level: built["masks"][level].copy() for level in ev.EVIDENCE_LEVELS}
    assert ev.assert_evidence_masks_lawful(masks, physical_state_row=state,
                                           query_index=q)["nested"] is True

    leaked = {level: m.copy() for level, m in masks.items()}
    leaked[60][q] = True
    with pytest.raises(AssertionError, match="QUERY_NOT_WITHHELD"):
        ev.assert_evidence_masks_lawful(leaked, physical_state_row=state, query_index=q)

    unmeasured = {level: m.copy() for level, m in masks.items()}
    unmeasured[60][2] = True                      # state 0
    with pytest.raises(AssertionError, match="NOT_SUBSET_OF_MEASURED_SCALAR"):
        ev.assert_evidence_masks_lawful(unmeasured, physical_state_row=state,
                                        query_index=q)

    broken = {level: m.copy() for level, m in masks.items()}
    broken[40][int(np.flatnonzero(broken[20])[0])] = False
    with pytest.raises(AssertionError, match="NOT_NESTED"):
        ev.assert_evidence_masks_lawful(broken, physical_state_row=state, query_index=q)


def test_an_empty_eligible_context_is_terminal() -> None:
    lone = np.zeros(8, dtype=np.uint8)
    lone[3] = ev.MEASURED_SCALAR
    with pytest.raises(ValueError, match="ELIGIBLE_CONTEXT_EMPTY"):
        ev.eligible_context(lone, 3)


def test_the_old_percentage_rule_disagrees_with_the_authority() -> None:
    """Make the corrected defect concrete rather than only described.

    This reproduces the previous implementation and requires it to differ, so
    the repair cannot be quietly reverted without a test failing.
    """
    state, q = _row()
    measurable = state == ev.MEASURED_SCALAR
    eligible_old = np.flatnonzero(measurable)          # includes q
    take = int(round(eligible_old.size * 0.60))
    old_mask = np.zeros(state.size, dtype=bool)
    old_mask[eligible_old[:max(take, 1)]] = True

    authorised = ev.build_row_evidence_masks(
        state, q, row_locator="HVS::abc#356", query_address=904)["masks"][60]
    assert not np.array_equal(old_mask, authorised)
    # The old rule could expose the query itself, which the authority forbids.
    assert bool(old_mask[q]) is True
    assert bool(authorised[q]) is False


def test_authority_dependent_declaration_matches_the_ast() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    actual = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
                        and inner.func.id == "_authority"):
                    actual.add(node.name)
    assert actual == set(AUTHORITY_DEPENDENT_TESTS), {
        "undeclared": sorted(actual - set(AUTHORITY_DEPENDENT_TESTS)),
        "declared_but_independent": sorted(set(AUTHORITY_DEPENDENT_TESTS) - actual),
    }
