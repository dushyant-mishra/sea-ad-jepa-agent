#!/usr/bin/env python3
"""Versioned DEVELOPMENT-ONLY 2048-address extension of original PR328 biology.

This is NOT production synthetic Task4, an independently sealed realization, a
JEPA training experiment, or a candidate C1-C6 qualification. The original PR328
480x48 world and its receipts are never modified. All observations here are
synthetic and the fit outputs contain NO latent/controller-truth arrays.

Structural assay availability is prospectively defined independently from
observed detection, correcting the known PR328 *interpretation* defect without
mutating its original biology or fit-side implementation.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

import numpy as np

from scripts.v79.unified_synthetic_integration_v1 import (
    UnifiedBiologyConfig, build_unified_biology, world_as_latent_biology,
)
from scripts.v79.unified_synthetic_fit_view_v1 import (
    _atac_realization, _donor_splits,
)
from scripts.v79.v79_observation_operator import observe_latent_biology

SCHEMA = "JEPA_EXPANDED_COMMON_WORLD_DEVELOPMENT_FIT_ONLY_V1"
PARENT_PR328_HEAD = "25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec"
N_CELLS = 1440
N_GENES = 2048
N_DONORS = 36
WORLD_SEED = 20261104
OBS_SEED = 20261105
SOURCES = ("SYNTH_A", "SYNTH_B", "SYNTH_C")
CAPTURE_MEAN = (-0.25, -0.45, -0.65)  # PR328 development stress convention
CAPTURE_SD = (0.15, 0.18, 0.20)       # PR328 development stress convention
SUPPORT_PERIOD = 37                  # new prospective fixture-only convention
SOURCE_OFFSETS = (0, 5, 11)          # new prospective fixture-only convention
VIEW_SIZE = 512
N_QUERIES = 4
OTHER_GENES_PER_QUERY = 8
FIT_NAMES = (
    "teacher_measured.npz",
    "student_qexcluded.npz",
    "roster_evaluation_only.npz",
    "atac_separate_nucleus_negative.npz",
)


def prospective_support() -> np.ndarray:
    """Synthetic assay *structural* support, not expression>0 or detection rate."""
    idx = np.arange(N_GENES, dtype=np.int64)
    return np.stack([
        ((idx + offset) % SUPPORT_PERIOD) != 0 for offset in SOURCE_OFFSETS
    ]).astype(bool)


def frozen_address_roles(support_table: np.ndarray) -> dict[str, object]:
    """Choose disjoint views using support ONLY, before any biological outcome."""
    s = np.asarray(support_table)
    if s.shape != (len(SOURCES), N_GENES) or s.dtype != np.bool_:
        raise ValueError("invalid prospective support table")
    common = np.flatnonzero(np.all(s, axis=0))
    required = 3 * VIEW_SIZE + N_QUERIES * (1 + OTHER_GENES_PER_QUERY)
    if len(common) < required:
        raise ValueError("insufficient physically shared structural addresses")
    views = [
        common[i * VIEW_SIZE:(i + 1) * VIEW_SIZE].astype(np.int64)
        for i in range(3)
    ]
    tail = common[3 * VIEW_SIZE:]
    queries = tail[:N_QUERIES].astype(np.int64)
    panels = [
        tail[N_QUERIES + i * OTHER_GENES_PER_QUERY:
             N_QUERIES + (i + 1) * OTHER_GENES_PER_QUERY].astype(np.int64)
        for i in range(N_QUERIES)
    ]
    all_assigned = np.concatenate([*views, queries, *panels])
    if len(set(all_assigned.tolist())) != len(all_assigned):
        raise AssertionError("view/query/panel overlap")
    return {
        "relational_views_3x512": [v.tolist() for v in views],
        "query_addresses": queries.tolist(),
        "query_other8_panels": [p.tolist() for p in panels],
        "common_measured_count": int(common.size),
    }


def source_and_partition(donor_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    donors = np.asarray(donor_ids)
    if donors.ndim != 1:
        raise ValueError("donor roster must be 1D")
    source = np.asarray(SOURCES, dtype="U8")[donors % len(SOURCES)]
    return source, _donor_splits(donors)


def student_projection(
    full_counts: np.ndarray, full_support: np.ndarray,
    query_addresses: list[int],
) -> dict[str, np.ndarray]:
    """No q value or q-containing physical total enters the student artifact."""
    counts = np.asarray(full_counts)
    support = np.asarray(full_support)
    if counts.ndim != 2 or counts.shape[1] != N_GENES:
        raise ValueError("unexpected full count shape")
    if support.shape != counts.shape or support.dtype != np.bool_:
        raise ValueError("support shape/type mismatch")
    if len(query_addresses) != N_QUERIES or len(set(query_addresses)) != N_QUERIES:
        raise ValueError("invalid frozen queries")
    if any(type(i) is not int or not 0 <= i < N_GENES for i in query_addresses):
        raise ValueError("invalid query address")
    base_ids = np.setdiff1d(np.arange(N_GENES), np.asarray(query_addresses), assume_unique=True)
    base_counts = counts[:, base_ids].copy()
    base_support = support[:, base_ids].copy()
    base_depth = base_counts.sum(axis=1, dtype=np.int64)
    if np.any(base_counts[~base_support] != 0):
        raise ValueError("unsupported addresses contain observed counts")
    return {
        "rna_base_counts": base_counts.astype(np.int32),
        "rna_base_support": base_support,
        "rna_base_address_ids": base_ids.astype(np.int32),
        "projected_base_depth": base_depth,
    }


def build_development_fixture() -> tuple[dict[str, dict[str, np.ndarray]], dict[str, object]]:
    """Reuse PR328 biological generator and V79 *actual* observation operator."""
    world = build_unified_biology(
        UnifiedBiologyConfig(n_cells=N_CELLS, n_genes=N_GENES, n_donors=N_DONORS),
        seed=WORLD_SEED,
    )
    source, partition = source_and_partition(world.donor_id)
    support_table = prospective_support()
    roles = frozen_address_roles(support_table)
    authority: Mapping[str, object] = {
        "regime_ids": list(SOURCES),
        "structural_support": support_table.tolist(),
        "capture_log_mean": list(CAPTURE_MEAN),
        "capture_log_sd": list(CAPTURE_SD),
        "gene_propensity_constant": 1.0,
        "realization_family": "independent_thinning",
        "molecule_scale": 3.0,  # original PR328 development convention
    }
    observed = observe_latent_biology(
        world_as_latent_biology(world), authority, source, OBS_SEED,
    )
    counts64 = observed.counts.toarray()
    if np.any(counts64 > np.iinfo(np.int32).max) or np.any(counts64 < 0):
        raise ValueError("count representation is not exact int32")
    counts = counts64.astype(np.int32)
    support = np.asarray(observed.structural_support, dtype=bool)
    if not np.array_equal(support, support_table[world.donor_id % len(SOURCES)]):
        raise AssertionError("structural support differs from frozen assay rule")

    # Reuse original PR328 same- vs separate-nucleus ATAC observation component.
    # These are observed simulated signals, not hidden program or causal truth.
    atac_same = _atac_realization(
        world, "same_nucleus", np.random.default_rng(OBS_SEED + 9091),
        N_GENES, 0.35,
    )
    atac_separate = _atac_realization(
        world, "separate_nucleus", np.random.default_rng(OBS_SEED + 9092),
        N_GENES, 0.35,
    )
    donor_ids = np.asarray(world.donor_id, dtype=np.int32)
    ids = np.array([
        f"DEV_D{int(d):03d}_CELL{i:05d}" for i, d in enumerate(donor_ids)
    ], dtype="U32")
    teacher = {
        "rna_counts": counts,
        "rna_support": support,
        "rna_address_ids": np.arange(N_GENES, dtype=np.int32),
        "atac_same_nucleus": atac_same,
    }
    student = student_projection(counts, support, roles["query_addresses"])
    roster = {
        "donor_id": donor_ids,
        "synthetic_source": source.astype("U8"),
        "split": partition.astype("U8"),
        "rna_entity_id": ids,
        "atac_same_entity_id": ids.copy(),
        "atac_separate_entity_id": np.char.add(ids, "_ATAC_OTHER"),
        # Experimental arm assignment is permitted evaluation metadata, never
        # controller-derived actual program activation or inferred causal truth.
        "perturbation_arm": np.asarray(world.perturbation_arm, dtype=np.int8),
    }
    negative = {
        "atac_separate_nucleus": atac_separate,
    }
    payload = {
        "teacher_measured.npz": teacher,
        "student_qexcluded.npz": student,
        "roster_evaluation_only.npz": roster,
        "atac_separate_nucleus_negative.npz": negative,
    }
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "source_parent_pr328_exact_head": PARENT_PR328_HEAD,
        "status": "DEVELOPMENT_FIXTURE_ONLY__NO_MODEL_OR_CANDIDATE_QUALIFICATION",
        "original_pr328_480x48_untouched": True,
        "frozen_dimensions": {
            "cells": N_CELLS, "genes": N_GENES, "donors": N_DONORS,
        },
        "seeds": {"neutral_biology": WORLD_SEED, "rna_observer": OBS_SEED},
        "biological_generator": "original PR328 build_unified_biology unchanged",
        "rna_observation_code": "original PR328 v79_observation_operator.observe_latent_biology unchanged",
        "atac_observation_code": "original PR328 _atac_realization unchanged",
        "support": {
            "class": "PROSPECTIVE_CONVENTION__NOT_EMPIRICAL_ASSAY_CALIBRATION",
            "formula": "(gene_address + source_offset) % 37 != 0",
            "source_offsets": list(SOURCE_OFFSETS),
            "source_names": list(SOURCES),
            "independent_of_count_detection": True,
            "structural_support_sha256": sha256(support_table.astype(np.uint8).tobytes()).hexdigest(),
        },
        "capture": {
            "class": "PR328_DEVELOPMENT_STRESS_CONVENTION__NOT_REALISTIC_CALIBRATION",
            "log_means": list(CAPTURE_MEAN), "log_sds": list(CAPTURE_SD),
        },
        "frozen_preoutcome_address_roles": roles,
        "world_identity_sha256": world.world_hash,
        "observed_csr_sha256": observed.counts_hash,
        "synthetic_fit_role_separation": "FILE_LEVEL_DEVELOPMENT_ONLY__NOT_AUTHENTICATED",
        "controller_truth_exported": False,
        "model_training_or_controller_scoring_executed": False,
        "all_six_candidate_recoverability": "UNASSESSED",
        "C4_C6_nonadditive_increment": "NOT_ADJUDICATED",
        "real_biology_or_production_authority": False,
        "known_limitations": [
            "2048 synthetic addresses are NOT canonical repaired human 41238-gene identities",
            "fixed source support is a prospective convention, not empirical support",
            "original PR328 conditional/perturbation biology not recalibrated to expanded size",
            "C2 3x512 view *availability* is not donor-recurrent relation PASS",
            "C3 other8 panels are fixed without checking biological recoverability",
            "C4/C6 extra nonlinear information and learned teacher/student are untested",
            "development process sees latent world to simulate observations; no physical sealed controller firewall",
            "the production V3.1.1 Task4 generator and STOP_A/B/C are NOT implemented or crossed",
        ],
    }
    return payload, manifest


def write_development_fixture(output_dir: Path) -> dict[str, object]:
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refusing to overwrite development fixture output")
    files, manifest = build_development_fixture()
    out.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}
    for name, values in files.items():
        destination = out / name
        np.savez_compressed(destination, **values)
        checksums[name] = sha256(destination.read_bytes()).hexdigest()
    manifest["fit_file_sha256"] = checksums
    receipt = out / "DEVELOPMENT_RECEIPT.json"
    receipt.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = write_development_fixture(args.output_dir)
    print(json.dumps({
        "status": result["status"],
        "world_sha256": result["world_identity_sha256"],
        "files": result["fit_file_sha256"],
        "candidate_recoverability": result["all_six_candidate_recoverability"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
