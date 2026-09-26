"""Prepared, CPU-only V26 development sampler; nontraining and source-bounded.

The PR135 single-update API rehashes the whole Aug24 ZIP and sorts 4.55M
pass1 donor codes on EACH invocation. A long diagnostic must never multiply
these whole-file operations by its update count. This module authenticates once,
snapshots donor codes/row order in memory and prepares a one-time donor index.
It exactly replays PR135's frozen proposal for every requested cursor.

An in-memory snapshot does NOT attest Level-4 cell lineage and cannot authorize
training. A future optimizer-facing adapter must independently bind its
source/target/parameter and checkpoint authority before consuming selections.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from numbers import Integral
from pathlib import Path
from typing import Mapping

import numpy as np

from .frozen_pass1_reader_fit_count_bridge_v1 import (
    FROZEN_PASS1_SHA256, _compare_structural, _sha256_open_file,
    verify_frozen_pass1_reader_fit_count_bridge,
)
from .reader_fit_population_preflight_v1 import (
    ARCHIVE_SHA256, EXPECTED_TOTAL_FIT_CELLS, load_frozen_reader_fit_from_bundle,
)
from .reader_fit_development_sampler_v1 import (
    POLICY, SCHEMA, ProposedDevelopmentUpdate, _positive_exact,
)

PREPARED_SCHEMA = "V26_PREPARED_READER_FIT_PROPOSAL_V1"


@dataclass(frozen=True)
class PreparedReaderFitProposal:
    """Synthetic constructor is NOT authenticated: physical factory is separate."""
    donor_codes: np.ndarray
    donor_names: tuple[str, ...]
    donor_counts: np.ndarray
    ordered_rows: np.ndarray
    offsets: np.ndarray
    source_digest: str
    # No public flag can promote a synthetic snapshot to byte authority.
    training_authorized: bool = False

    @classmethod
    def structural_only(
        cls, *, cell_donor: np.ndarray, donor_ids: np.ndarray,
        expected_counts: Mapping[str, int], source_digest: str,
    ) -> "PreparedReaderFitProposal":
        """Construct synthetic fixture without any possibility of byte authority."""
        _compare_structural(cell_donor, donor_ids, expected_counts)
        if (not isinstance(source_digest, str) or len(source_digest) != 64
                or any(c not in "0123456789abcdef" for c in source_digest)):
            raise ValueError("source digest must be canonical lowercase SHA-256")
        # Arrays with read-only flags but OWNING memory can be made writable
        # again by a caller. Back with immutable bytes so cached source/index
        # snapshots cannot be silently changed between trajectory updates.
        codes = np.frombuffer(np.asarray(cell_donor, dtype="<i8").tobytes(), dtype="<i8")
        names = tuple(str(x) for x in np.asarray(donor_ids).astype(str))
        counts = np.frombuffer(
            np.asarray([expected_counts[d] for d in names], dtype="<i8").tobytes(),
            dtype="<i8",
        )
        ordered = np.frombuffer(
            np.argsort(codes, kind="stable").astype("<i8", copy=False).tobytes(),
            dtype="<i8",
        )
        offsets = np.frombuffer(
            np.concatenate(([0], np.cumsum(counts, dtype=np.int64))).astype("<i8").tobytes(),
            dtype="<i8",
        )
        if len(ordered) != int(offsets[-1]):
            raise ValueError("prepared donor offsets fail to cover source")
        return cls(codes, names, counts, ordered, offsets, source_digest)

    def proposal(self, *, run_seed: int, update_index: int,
                 presentations: int) -> ProposedDevelopmentUpdate:
        """O(presentations + donor_count), no per-update FULL104 data scan."""
        seed = _positive_exact(run_seed, "run_seed", allow_zero=True)
        index = _positive_exact(update_index, "update_index", allow_zero=True)
        n = _positive_exact(presentations, "presentations")
        if n > int(self.donor_counts.min()):
            raise ValueError("update presentations exceed smallest donor; cannot certify exact q=p")
        if len(self.donor_codes) != int(self.offsets[-1]) or len(self.donor_names) != len(self.donor_counts):
            raise ValueError("invalid prepared population geometry")
        material = f"{SCHEMA}|{POLICY}|{self.source_digest}|{seed}|{index}".encode("ascii")
        seed_digest = hashlib.sha256(material).hexdigest()
        rng = np.random.Generator(np.random.PCG64(int.from_bytes(bytes.fromhex(seed_digest), "big")))
        draw_donors = rng.integers(0, len(self.donor_names), size=n, dtype=np.int64)
        requested = np.bincount(draw_donors, minlength=len(self.donor_names))
        if np.any(requested > self.donor_counts):
            raise RuntimeError("impossible donor oversubscription after prospective capacity gate")
        rows = np.empty(n, dtype=np.int64)
        for donor in np.flatnonzero(requested):
            slots = np.flatnonzero(draw_donors == donor)
            within = rng.choice(int(self.donor_counts[donor]), size=len(slots), replace=False)
            rows[slots] = self.ordered_rows[self.offsets[donor] + within]
        if len(np.unique(rows)) != n or not np.array_equal(self.donor_codes[rows], draw_donors):
            raise RuntimeError("prepared selection duplicate or donor identity mismatch")
        q = 1.0 / (len(self.donor_names) * self.donor_counts[draw_donors].astype(np.float64))
        if not bool(np.isfinite(q).all()) or not bool((q > 0).all()):
            raise RuntimeError("nonfinite or nonpositive scientific proposal")
        return ProposedDevelopmentUpdate(
            rows, draw_donors, q, np.ones(n, dtype=np.float64),
            seed_digest, index,
        )

    def plan(self, *, run_seed: int, first_update_index: int,
             update_count: int, presentations_per_update: int,
             maximum_declared_presentations: int,
             ) -> tuple[ProposedDevelopmentUpdate, ...]:
        """Materialize only an explicitly bounded trajectory; no guessed defaults."""
        start = _positive_exact(first_update_index, "first_update_index", allow_zero=True)
        n_updates = _positive_exact(update_count, "update_count")
        n_presentations = _positive_exact(presentations_per_update, "presentations_per_update")
        cap = _positive_exact(maximum_declared_presentations, "maximum_declared_presentations")
        if n_updates * n_presentations > cap:
            raise ValueError("planned presentations exceed explicit declared materialization limit")
        if n_presentations > int(self.donor_counts.min()):
            raise ValueError("scheduled presentations exceed smallest frozen donor")
        if start + n_updates > (1 << 63) - 1:
            raise ValueError("schedule cursor would exceed signed 64-bit range")
        return tuple(self.proposal(
            run_seed=run_seed, update_index=i, presentations=n_presentations,
        ) for i in range(start, start + n_updates))

    def nontraining_report(self) -> dict[str, object]:
        return {
            "schema": PREPARED_SCHEMA,
            "status": "PREPARED_SNAPSHOT_NONTRAINING",
            "source_digest": self.source_digest,
            "population_donors": len(self.donor_names),
            "population_cells": len(self.donor_codes),
            "minimum_donor_cells": int(self.donor_counts.min()),
            "proposal_policy_id": POLICY,
            "numpy_version": np.__version__,
            "rng_bit_generator": "PCG64",
            # No editable object flag or caller-supplied constructor argument
            # can issue a physical source receipt. The separately archived PR132
            # byte-authority evidence MUST be carried into any later adapter.
            "input_authentication": "STRUCTURAL_SNAPSHOT_NO_BYTE_AUTHORITY_RECEIPT",
            "source_mutations_after_snapshot_detected_here": False,
            "raw_level4_per_cell_binding_here": False,
            "training_authorized": False,
            "protected_outcomes_opened": False,
        }


def prepare_from_frozen_pass1(
    *, pass1_path: Path | str, calibration_zip: Path | str,
) -> PreparedReaderFitProposal:
    """Only byte-bound factory; reads/hash-validates source ONCE per trajectory."""
    bridge = verify_frozen_pass1_reader_fit_count_bridge(
        pass1_path=pass1_path, calibration_zip=calibration_zip,
    )
    if (bridge.get("status") != "BYTE_BOUND_PASS1_AND_METADATA_COUNTS_ONLY"
            or bridge.get("training_authorized") is not False):
        raise ValueError("physical pass1 bridge did not produce exact scoped proof")
    with Path(pass1_path).open("rb") as stream:
        if _sha256_open_file(stream) != FROZEN_PASS1_SHA256:
            raise ValueError("frozen pass1 changed before prepared snapshot")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as payload:
            codes = np.asarray(payload["cell_donor"])
            ids = np.asarray(payload["duniq"])
    frozen = load_frozen_reader_fit_from_bundle(calibration_zip)
    if len(frozen.donor_counts) != 104 or len(codes) != EXPECTED_TOTAL_FIT_CELLS:
        raise ValueError("not genuine frozen 104-donor population")
    prepared = PreparedReaderFitProposal.structural_only(
        cell_donor=codes, donor_ids=ids,
        expected_counts=frozen.donor_counts,
        source_digest=FROZEN_PASS1_SHA256,
    )
    if len(prepared.donor_names) != bridge["donor_count"] or len(prepared.donor_codes) != bridge["cell_count"]:
        raise ValueError("prepared population contradicts frozen bridge")
    return PreparedReaderFitProposal(
        prepared.donor_codes, prepared.donor_names, prepared.donor_counts,
        prepared.ordered_rows, prepared.offsets, prepared.source_digest,
        training_authorized=False,
    )
