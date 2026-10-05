"""Regressions for strict FULL104 support semantics.

Two properties are load-bearing for the masking design and are regressed here:

1. The 219 addresses admitted only by the loose "measured" reading can never
   enter the terminal common core.
2. Measured zero is never reclassified as structural missingness.

The fixture reproduces the real FULL104 support geometry (three source families,
one uniform panel for each of the two large families, a heterogeneous panel for
the small one, plus collision-unresolved addresses) rather than using an
arbitrary shape. The real-data checks run against the authenticated observation
state and fail closed if it is absent -- they never skip.
"""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_strict_support_selection_v1 import (
    MEASURED_COLLISION_UNRESOLVED,
    MEASURED_SCALAR,
    STRUCTURALLY_UNMEASURED,
    SUPPORT_SEMANTICS_ID,
    TERMINAL_UNIVERSE_SIZE,
    assert_terminal_universe_is_strict,
    classify_cell_addresses,
    eligible_masking_addresses,
    loose_only_addresses,
    select_loose_common_core,
    select_strict_common_core,
)

CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))
OBSERVATION_STATE_RELPATH = (
    "exports/foundation_calibration_bundle_20260824/support/"
    "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
)
OBSERVATION_STATE_SHA256 = (
    "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
)

# Census-established constants. These are evidence, not tunables.
STRICT_CORE = 17186
LOOSE_CORE = 17405
LOOSE_ONLY = 219
NEVER_MEASURED_ANYWHERE = 289
N_OPERATORS = 42
N_ADDRESSES = 41238


def resolve_observation_state() -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / OBSERVATION_STATE_RELPATH
        if candidate.is_file():
            return candidate
    raise AssertionError(
        "authenticated observation state not found under any canonical root "
        f"{[str(r) for r in CANONICAL_ROOTS]!r}. This check fails closed rather than "
        "skipping: an unrun support regression is not a pass."
    )


def build_fixture_states() -> np.ndarray:
    """Synthetic states reproducing the real FULL104 support geometry."""
    n_addr = 400
    states = np.zeros((N_OPERATORS, n_addr), dtype=np.uint8)
    hvs = list(range(0, 24))
    sea = list(range(24, 35))
    nph = list(range(35, 42))

    # 0-199 strictly measured everywhere -> the strict core
    for op in range(N_OPERATORS):
        states[op, 0:200] = MEASURED_SCALAR
    # 200-219 measured everywhere, but collision-unresolved in some operators
    # -> loose-only, must never enter the terminal universe
    for op in range(N_OPERATORS):
        states[op, 200:220] = MEASURED_SCALAR
    for op in sea[:3]:
        states[op, 200:210] = MEASURED_COLLISION_UNRESOLVED
    for op in nph[:2]:
        states[op, 210:220] = MEASURED_COLLISION_UNRESOLVED
    # 220-299 source-family specific
    for op in hvs:
        states[op, 220:260] = MEASURED_SCALAR
    for op in sea:
        states[op, 260:300] = MEASURED_SCALAR
    # 300-379 heterogeneous within the small family only
    for i, op in enumerate(nph):
        states[op, 300 + i * 10: 310 + i * 10] = MEASURED_SCALAR
    # 380-399 never measured anywhere
    return states


class StrictSupportFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.states = build_fixture_states()

    def test_strict_and_loose_cores_differ_by_the_collision_addresses(self) -> None:
        strict = select_strict_common_core(self.states)
        loose = select_loose_common_core(self.states)
        self.assertEqual(strict.size, 200)
        self.assertEqual(loose.size, 220)
        self.assertEqual(loose_only_addresses(self.states).tolist(), list(range(200, 220)))

    def test_loose_only_addresses_cannot_enter_terminal_universe(self) -> None:
        strict = select_strict_common_core(self.states)
        assert_terminal_universe_is_strict(self.states, strict)
        for intruder in (200, 209, 210, 219):
            polluted = np.sort(np.append(strict, intruder))
            with self.assertRaises(ValueError) as ctx:
                assert_terminal_universe_is_strict(self.states, polluted)
            self.assertIn("loose-only", str(ctx.exception))

    def test_whole_loose_core_is_rejected_as_terminal_universe(self) -> None:
        with self.assertRaises(ValueError):
            assert_terminal_universe_is_strict(
                self.states, select_loose_common_core(self.states)
            )

    def test_measured_zero_is_not_structural_missingness(self) -> None:
        """A cell with almost no detected transcripts still has zero missingness."""
        states = self.states
        op = 0
        supported = int((states[op] == MEASURED_SCALAR).sum())
        counts = classify_cell_addresses(states, op, np.array([0, 1, 2]))
        self.assertEqual(counts["measured_nonzero"], 3)
        self.assertEqual(counts["measured_zero"], supported - 3)
        self.assertGreater(counts["measured_zero"], 0)
        # the classes are exhaustive and disjoint
        self.assertEqual(sum(counts.values()), states.shape[1])
        # a fully undetected cell is all measured zero, never structurally missing
        empty = classify_cell_addresses(states, op, np.array([], dtype=np.int64))
        self.assertEqual(empty["measured_nonzero"], 0)
        self.assertEqual(empty["measured_zero"], supported)
        self.assertEqual(
            empty["structurally_unmeasured"],
            int((states[op] == STRUCTURALLY_UNMEASURED).sum()),
        )

    def test_structural_missingness_is_not_reported_as_measured_zero(self) -> None:
        states = self.states
        op = 35  # small-family operator with a narrow panel
        counts = classify_cell_addresses(states, op, np.array([0, 5]))
        self.assertGreater(counts["structurally_unmeasured"], 0)
        self.assertEqual(
            counts["structurally_unmeasured"],
            int((states[op] == STRUCTURALLY_UNMEASURED).sum()),
        )

    def test_nonzero_outside_declared_panel_is_rejected(self) -> None:
        states = self.states
        unsupported = int(np.flatnonzero(states[35] == STRUCTURALLY_UNMEASURED)[0])
        with self.assertRaises(ValueError) as ctx:
            classify_cell_addresses(states, 35, np.array([unsupported]))
        self.assertIn("outside the operator", str(ctx.exception))

    def test_nonzero_at_collision_address_is_rejected(self) -> None:
        states = self.states
        with self.assertRaises(ValueError):
            classify_cell_addresses(states, 24, np.array([200]))

    def test_eligibility_is_value_independent(self) -> None:
        """Eligible set depends only on support and target, never on values."""
        states = self.states
        strict = select_strict_common_core(states)
        target = int(strict[7])
        eligible = eligible_masking_addresses(states, strict, target)
        self.assertEqual(eligible.size, strict.size - 1)
        self.assertNotIn(target, eligible.tolist())
        # recomputing for any hypothetical cell gives an identical set, because
        # no expression value is consulted anywhere in the call
        again = eligible_masking_addresses(states, strict, target)
        self.assertTrue(np.array_equal(eligible, again))

    def test_unknown_state_code_is_rejected(self) -> None:
        states = self.states.copy()
        states[0, 0] = 7
        with self.assertRaises(ValueError):
            select_strict_common_core(states)

    def test_semantics_identifier_is_strict(self) -> None:
        self.assertEqual(
            SUPPORT_SEMANTICS_ID,
            "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        )
        self.assertEqual(TERMINAL_UNIVERSE_SIZE, STRICT_CORE)


class StrictSupportRealDataTests(unittest.TestCase):
    """Data-bound regressions. Fail closed when the asset is absent."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.path = resolve_observation_state()
        digest = hashlib.sha256()
        with cls.path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 22), b""):
                digest.update(chunk)
        cls.digest = digest.hexdigest()
        cls.states = np.load(cls.path, allow_pickle=False)["states"]

    def test_asset_identity(self) -> None:
        self.assertEqual(self.digest, OBSERVATION_STATE_SHA256)
        self.assertEqual(self.states.shape, (N_OPERATORS, N_ADDRESSES))

    def test_state_alphabet_is_ternary(self) -> None:
        self.assertEqual(
            sorted(int(v) for v in np.unique(self.states)),
            [STRUCTURALLY_UNMEASURED, MEASURED_SCALAR, MEASURED_COLLISION_UNRESOLVED],
        )

    def test_strict_core_is_exactly_17186(self) -> None:
        self.assertEqual(select_strict_common_core(self.states).size, STRICT_CORE)

    def test_loose_core_is_17405_and_is_not_the_terminal_universe(self) -> None:
        loose = select_loose_common_core(self.states)
        self.assertEqual(loose.size, LOOSE_CORE)
        self.assertEqual(loose_only_addresses(self.states).size, LOOSE_ONLY)
        with self.assertRaises(ValueError):
            assert_terminal_universe_is_strict(self.states, loose)

    def test_each_loose_only_address_is_individually_rejected(self) -> None:
        strict = select_strict_common_core(self.states)
        for address in loose_only_addresses(self.states)[:25]:
            polluted = np.sort(np.append(strict, int(address)))
            with self.assertRaises(ValueError):
                assert_terminal_universe_is_strict(self.states, polluted)

    def test_addresses_never_measured_anywhere(self) -> None:
        never = int(((self.states == MEASURED_SCALAR).sum(axis=0) == 0).sum())
        self.assertEqual(never, NEVER_MEASURED_ANYWHERE)

    def test_strict_core_has_no_structural_missingness(self) -> None:
        strict = select_strict_common_core(self.states)
        sub = self.states[:, strict]
        self.assertTrue((sub == MEASURED_SCALAR).all())
        self.assertEqual(int((sub == STRUCTURALLY_UNMEASURED).sum()), 0)
        self.assertEqual(int((sub == MEASURED_COLLISION_UNRESOLVED).sum()), 0)


if __name__ == "__main__":
    unittest.main()
