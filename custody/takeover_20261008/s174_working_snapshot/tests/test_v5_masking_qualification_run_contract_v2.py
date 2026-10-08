"""Tests for the run contract V2 execution-source role split.

V1 carried one generic ``runner_source_sha256``. Two different files are actually
involved: the canonical in-memory reference, and the streaming executor that
performs the real FULL104 run. Freezing the reference digest into the execution
role would name code that never ran. These tests prove the misbinding fails.
"""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from sea_ad_jepa.v5.masking_qualification_run_contract_v2 import (
    CANONICAL_REFERENCE_RELPATH,
    FULL104_STREAMING_EXECUTION_RELPATH,
    MaskingQualificationRunContractV2,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

FREEZE_POLICY_ID = "FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1"
STRICT_SUPPORT_POLICY_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


CANONICAL_LIVE = sha256_file(REPO_ROOT / CANONICAL_REFERENCE_RELPATH)
STREAMING_LIVE = sha256_file(REPO_ROOT / FULL104_STREAMING_EXECUTION_RELPATH)


def distinct(prefix: str, count: int):
    return [f"{prefix}{index:02d}".ljust(64, "0") for index in range(count)]


def contract(**overrides) -> MaskingQualificationRunContractV2:
    roots = distinct("c", 13)
    base = dict(
        authority_id="TEST_RUN_CONTRACT_V2",
        qualification_design_authority_sha256=roots[0],
        qualification_parameters_authority_sha256=roots[1],
        full104_block_manifest_sha256=roots[2],
        observation_state_sha256=roots[3],
        support_estimability_authority_sha256=roots[4],
        census_authority_sha256=roots[5],
        target_evidence_budget_template_sha256=roots[6],
        burden_ladder_authority_sha256=roots[7],
        outer_split_authority_sha256=roots[8],
        target_panel_authority_sha256=roots[9],
        precision_authority_sha256=roots[10],
        rng_replay_authority_sha256=roots[11],
        machine_worktree_checkpoint_sha256=roots[12],
        canonical_reference_source_sha256=CANONICAL_LIVE,
        full104_streaming_execution_source_sha256=STREAMING_LIVE,
        execution_source_role_id="FULL104_STREAMING_EXECUTION_V1",
        freeze_policy_id=FREEZE_POLICY_ID,
        support_state_policy_id=STRICT_SUPPORT_POLICY_ID,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
    )
    base.update(overrides)
    return MaskingQualificationRunContractV2(**base)


class ExecutionSourceRoleTests(unittest.TestCase):
    def test_the_two_source_files_are_different_files(self) -> None:
        self.assertNotEqual(CANONICAL_REFERENCE_RELPATH, FULL104_STREAMING_EXECUTION_RELPATH)
        self.assertNotEqual(CANONICAL_LIVE, STREAMING_LIVE)

    def test_correctly_bound_contract_validates(self) -> None:
        run = contract()
        run.validate()
        run.bind_execution_sources(
            canonical_reference_live_sha256=CANONICAL_LIVE,
            full104_streaming_execution_live_sha256=STREAMING_LIVE,
        )

    def test_canonical_reference_hash_in_execution_role_fails(self) -> None:
        """The specific misbinding this repair exists to prevent."""
        run = contract(full104_streaming_execution_source_sha256=CANONICAL_LIVE)
        # both roles now hold the same digest, so distinctness already rejects it
        with self.assertRaises(ValueError) as ctx:
            run.validate()
        self.assertIn("distinct", str(ctx.exception))

    def test_canonical_reference_hash_in_execution_role_fails_on_binding(self) -> None:
        """Even with a distinct-looking canonical root, the binding still fails."""
        run = contract(
            canonical_reference_source_sha256="d" * 64,
            full104_streaming_execution_source_sha256=CANONICAL_LIVE,
        )
        run.validate()
        with self.assertRaises(ValueError) as ctx:
            run.bind_execution_sources(
                canonical_reference_live_sha256=CANONICAL_LIVE,
                full104_streaming_execution_live_sha256=STREAMING_LIVE,
            )
        self.assertIn("canonical_reference_source_sha256 does not match", str(ctx.exception))

    def test_execution_role_misbinding_is_named_explicitly(self) -> None:
        run = contract(
            canonical_reference_source_sha256=CANONICAL_LIVE,
            full104_streaming_execution_source_sha256="e" * 64,
        )
        run.validate()
        with self.assertRaises(ValueError) as ctx:
            run.bind_execution_sources(
                canonical_reference_live_sha256=CANONICAL_LIVE,
                full104_streaming_execution_live_sha256=CANONICAL_LIVE,
            )
        self.assertIn("cannot share a digest", str(ctx.exception))

    def test_swapped_roles_fail(self) -> None:
        run = contract(
            canonical_reference_source_sha256=STREAMING_LIVE,
            full104_streaming_execution_source_sha256=CANONICAL_LIVE,
        )
        run.validate()
        with self.assertRaises(ValueError):
            run.bind_execution_sources(
                canonical_reference_live_sha256=CANONICAL_LIVE,
                full104_streaming_execution_live_sha256=STREAMING_LIVE,
            )

    def test_stale_streaming_digest_fails(self) -> None:
        run = contract(full104_streaming_execution_source_sha256="f" * 64)
        run.validate()
        with self.assertRaises(ValueError) as ctx:
            run.bind_execution_sources(
                canonical_reference_live_sha256=CANONICAL_LIVE,
                full104_streaming_execution_live_sha256=STREAMING_LIVE,
            )
        self.assertIn(
            "full104_streaming_execution_source_sha256 does not match", str(ctx.exception)
        )

    def test_execution_source_role_id_is_enumerated(self) -> None:
        run = contract(execution_source_role_id="SOME_OTHER_ROLE")
        with self.assertRaises(ValueError):
            run.validate()


class RunContractRootTests(unittest.TestCase):
    def test_all_roots_must_be_distinct(self) -> None:
        shared = "9" * 64
        run = contract(
            census_authority_sha256=shared,
            target_evidence_budget_template_sha256=shared,
        )
        with self.assertRaises(ValueError) as ctx:
            run.validate()
        self.assertIn("distinct", str(ctx.exception))

    def test_loose_support_policy_is_rejected(self) -> None:
        run = contract(support_state_policy_id="MEASURED_ANY_V1")
        with self.assertRaises(ValueError):
            run.validate()

    def test_loose_terminal_universe_is_rejected(self) -> None:
        run = contract(terminal_universe_id="FULL_COMMON_CORE_17405_V1")
        with self.assertRaises(ValueError):
            run.validate()

    def test_freeze_policy_is_fixed(self) -> None:
        run = contract(freeze_policy_id="FROZEN_AFTER_OUTCOMES_V1")
        with self.assertRaises(ValueError):
            run.validate()

    def test_cannot_authorize_training_or_protected_outcomes(self) -> None:
        run = contract()
        object.__setattr__(run, "training_authorized", True)
        with self.assertRaises(ValueError):
            run.validate()
        run = contract()
        object.__setattr__(run, "protected_outcomes_authorized", True)
        with self.assertRaises(ValueError):
            run.validate()

    def test_malformed_digest_is_rejected(self) -> None:
        run = contract(census_authority_sha256="NOTAHASH")
        with self.assertRaises(ValueError):
            run.validate()

    def test_uppercase_digest_is_rejected(self) -> None:
        run = contract(census_authority_sha256="A" * 64)
        with self.assertRaises(ValueError):
            run.validate()

    def test_digest_is_deterministic_and_discriminating(self) -> None:
        self.assertEqual(contract().canonical_digest(), contract().canonical_digest())
        self.assertNotEqual(
            contract().canonical_digest(),
            contract(census_authority_sha256="7" * 64).canonical_digest(),
        )


if __name__ == "__main__":
    unittest.main()
