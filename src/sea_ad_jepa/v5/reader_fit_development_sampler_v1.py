"""Deterministic reader-fit donor-uniform proposal for a bounded V5 diagnostic.

No training authority. Source gate reuses the frozen pass1/calibration bridge.
No expression, masks, protected labels or historical V4 defaults are loaded.
The proposal is EXACTLY the scientific p=1/(D*n_d), so p/q=1.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from numbers import Integral
from pathlib import Path
from typing import Mapping

import numpy as np

from .frozen_pass1_reader_fit_count_bridge_v1 import (
    FROZEN_PASS1_SHA256,
    _compare_structural,
    _sha256_open_file,
    verify_frozen_pass1_reader_fit_count_bridge,
)
from .reader_fit_population_preflight_v1 import (
    ARCHIVE_SHA256,
    EXPECTED_TOTAL_FIT_CELLS,
    load_frozen_reader_fit_from_bundle,
)

SCHEMA = "V26_READER_FIT_DEVELOPMENT_PROPOSAL_V1"
POLICY = "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR__WITH_REPLACEMENT_V1"


def _positive_exact(value: object, name: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    n = int(value)
    if n < (0 if allow_zero else 1):
        raise ValueError(f"{name} is outside its nonnegative/positive bound")
    return n


@dataclass(frozen=True)
class ProposedDevelopmentUpdate:
    """Selection rows are identities only; source still needs raw-cell attestation."""
    selection_rows: np.ndarray
    donor_codes: np.ndarray
    proposal_probabilities: np.ndarray
    importance_weights: np.ndarray
    seed_sha256: str
    update_index: int
    proposal_policy_id: str = POLICY
    training_authorized: bool = False

    def nontraining_report(self) -> dict[str, object]:
        rows = np.ascontiguousarray(self.selection_rows.astype("<i8", copy=False))
        donors = np.ascontiguousarray(self.donor_codes.astype("<i8", copy=False))
        return {
            "schema": SCHEMA,
            "status": "DETERMINISTIC_PROPOSAL_ONLY",
            "policy": self.proposal_policy_id,
            "seed_sha256": self.seed_sha256,
            "update_index": self.update_index,
            "presentations": len(rows),
            "selection_rows_sha256": hashlib.sha256(rows.tobytes()).hexdigest(),
            "donor_codes_sha256": hashlib.sha256(donors.tobytes()).hexdigest(),
            "sampling_with_replacement": True,
            "importance_weights_all_one": bool(np.all(self.importance_weights == 1.0)),
            "raw_level4_lineage_verified_here": False,
            "target_mask_model_qualified_here": False,
            "training_authorized": False,
            "protected_outcomes_opened": False,
        }


def _propose_structural(
    *,
    cell_donor: np.ndarray,
    donor_ids: np.ndarray,
    expected_counts: Mapping[str, int],
    run_seed: int,
    update_index: int,
    presentations: int,
    source_digest: str,
) -> ProposedDevelopmentUpdate:
    """Pure structural mechanics for synthetic tests; NO frozen-source authority."""
    seed = _positive_exact(run_seed, "run_seed", allow_zero=True)
    index = _positive_exact(update_index, "update_index", allow_zero=True)
    n = _positive_exact(presentations, "presentations")
    if not isinstance(source_digest, str) or len(source_digest) != 64:
        raise ValueError("source_digest must be an explicit SHA-256")
    try:
        bytes.fromhex(source_digest)
    except ValueError as exc:
        raise ValueError("source_digest must be an explicit SHA-256") from exc
    _compare_structural(cell_donor, donor_ids, expected_counts)
    codes = np.asarray(cell_donor)
    names = np.asarray(donor_ids).astype(str)
    counts = np.asarray([expected_counts[d] for d in names], dtype=np.int64)
    # One stable sort, one prefix-sum: O(N log N), not 104 full-dataset scans.
    ranked_rows = np.argsort(codes, kind="stable").astype(np.int64, copy=False)
    offsets = np.concatenate(([0], np.cumsum(counts)))
    if len(ranked_rows) != int(offsets[-1]):
        raise RuntimeError("donor offsets do not close over frozen cell count")
    material = f"{SCHEMA}|{POLICY}|{source_digest}|{seed}|{index}".encode("ascii")
    seed_digest = hashlib.sha256(material).hexdigest()
    rng = np.random.Generator(np.random.PCG64(int.from_bytes(bytes.fromhex(seed_digest), "big")))
    # Every presentation samples a donor uniformly, then one of its frozen rows
    # uniformly. Nothing uses source/operator or a cell's measured value.
    draw_donors = rng.integers(0, len(names), size=n, dtype=np.int64)
    # Per-presentation integer rejection sampling avoids floating-point endpoint
    # effects and implements exact discrete uniform choice within each donor.
    within = rng.integers(low=0, high=counts[draw_donors], dtype=np.int64)
    rows = ranked_rows[offsets[draw_donors] + within]
    if not np.array_equal(codes[rows].astype(np.int64), draw_donors):
        raise RuntimeError("sampled selection_row donor mismatch")
    q = 1.0 / (len(names) * counts[draw_donors].astype(np.float64))
    if not bool(np.isfinite(q).all()) or not bool((q > 0).all()):
        raise RuntimeError("invalid explicit proposal probability")
    weights = np.ones(n, dtype=np.float64)  # p/q = 1 by design
    return ProposedDevelopmentUpdate(rows, draw_donors, q, weights, seed_digest, index)


def propose_from_frozen_pass1(
    *,
    pass1_path: Path | str,
    calibration_zip: Path | str,
    run_seed: int,
    update_index: int,
    presentations: int,
) -> tuple[ProposedDevelopmentUpdate, dict[str, object]]:
    """Byte-authenticate frozen inputs; never claim raw Level-4 or V5 authority."""
    # The existing audited bridge validates exact population and input identities.
    bridge = verify_frozen_pass1_reader_fit_count_bridge(
        pass1_path=pass1_path, calibration_zip=calibration_zip,
    )
    if bridge.get("status") != "BYTE_BOUND_PASS1_AND_METADATA_COUNTS_ONLY" or bridge.get("training_authorized") is not False:
        raise ValueError("frozen pass1 bridge is not the exact nontraining receipt")
    # Reauthenticate this second read through one descriptor. A concurrent
    # pathname replacement cannot splice unverified bytes into the proposal.
    with Path(pass1_path).open("rb") as stream:
        if _sha256_open_file(stream) != FROZEN_PASS1_SHA256:
            raise ValueError("frozen pass1 changed before sampler read")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as data:
            codes = np.asarray(data["cell_donor"])
            ids = np.asarray(data["duniq"])
    population = load_frozen_reader_fit_from_bundle(calibration_zip)
    if len(population.donor_counts) != 104 or len(codes) != EXPECTED_TOTAL_FIT_CELLS:
        raise ValueError("reader-fit physical scope changed")
    selection = _propose_structural(
        cell_donor=codes, donor_ids=ids,
        expected_counts=population.donor_counts,
        run_seed=run_seed, update_index=update_index,
        presentations=presentations, source_digest=FROZEN_PASS1_SHA256,
    )
    report = {
        **selection.nontraining_report(),
        "frozen_pass1_sha256": FROZEN_PASS1_SHA256,
        "frozen_calibration_zip_sha256": ARCHIVE_SHA256,
        "frozen_count_bridge_status": bridge["status"],
        "reader_fit_donors": len(population.donor_counts),
        "reader_fit_cells": len(codes),
        "scientific_estimand_id": "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1",
        "proposal_q_equals_p_by_construction": True,
        "raw_level4_lineage_verified_here": False,
        "training_authorized": False,
    }
    return selection, report
