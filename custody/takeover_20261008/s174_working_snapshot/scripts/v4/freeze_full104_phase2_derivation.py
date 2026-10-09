#!/usr/bin/env python3
"""Create the metadata-only prospective freeze for FULL104 Phase-2 derivation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "exports/jepa_codex_adaptive_handoff_v014_20260826/JEPA_CODEX_ADAPTIVE_HANDOFF_V014_20260826"
META = ROOT / "outputs/full104_v014_20260826/01_full104_metadata_adapter"
V8_ENV = ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified"
V8 = V8_ENV / "FULL104_EXPRESSION_INTERFACE_V8"
DISCOVERY = ROOT / "exports/foundation_corpus_discovery_v1"
READER = ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"
CONTRACT = HANDOFF / "prior_v013/full104/FULL104_ADAPTIVE_CALIBRATION_CONTRACT_V1.md"
INTERFACES = HANDOFF / "codex/contracts/FULL104_DERIVED_ARTIFACT_INTERFACES_V014.md"
PLAN = ROOT / "docs/exec-plans/active/FULL104_PHASE2_STATE_DERIVATION.md"
COUNCIL = ROOT / "outputs/full104_v014_20260826/PHASE2_PREFLIGHT_COUNCIL_20260827.md"
SCRIPT = Path(__file__).resolve()

EXPECTED = {
    "contract": "83f7a1912c857d14d20fbe6d1ebeefbf8e2b6b0786e82c2f0536a44a2442231b",
    "v8_manifest": "28d544e8cc34408d27d0682fc853770b0bdddcaa56a4099f9d58630367b1a127",
    "reader_split": "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    "metadata_manifest": "54e4ba5b60e9c5d3ff23a307df03576f45ac725f3b71642888500a469ebdbc74",
}

FROZEN = {
    "addresses": 41238,
    "reader_fit_donors": 104,
    "views": 4,
    "visible_fraction_numerator": 3,
    "visible_fraction_denominator": 5,
    "d_gene": 160,
    "fold_min_donors_per_source": 3,
    "fold_maximum": 8,
    "sample_quantiles": [0.05, 0.10, 0.25, 0.50],
    "source_sensitivities": ["equal_source", "leave_each_source_out"],
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def hash_key(*parts: object) -> int:
    value = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big") & ((1 << 63) - 1)


def authenticate() -> dict[str, Path]:
    inputs = {
        "controlling_contract": CONTRACT,
        "derived_interfaces": INTERFACES,
        "v8_package_manifest": V8 / "FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv",
        "v8_external_anchor": V8_ENV / "FULL104_EXPRESSION_INTERFACE_V8.PACKAGE_ROOT_SHA256.txt",
        "v8_terminal_status": V8 / "FULL104_EXPRESSION_INTERFACE_V8_STATUS.json",
        "metadata_manifest": META / "FULL104_ADAPTER_SHA256_MANIFEST.csv",
        "metadata_status": META / "FULL104_METADATA_SCOPE_STATUS.json",
        "metadata_lineage_index": META / "FULL104_ROW_LINEAGE.csv",
        "reader_split": READER,
        "source_donor_authority": DISCOVERY / "FOUNDATION_METADATA_SOURCE_X_DONOR.csv",
        "donor_operator_authority": DISCOVERY / "FOUNDATION_METADATA_DONOR_X_OPERATOR.csv",
        "operator_state_authority": ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
        "address_registry": ROOT / "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv",
        "source_asset_pins": V8 / "interface_check_v8r1/FULL104_EXPRESSION_ASSET_PINS.csv",
        "nph_fit_derivative_manifest": V8 / "NPH_READER_FIT_DERIVATIVE_MANIFEST.csv",
        "original_nph_denylist": V8 / "ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv",
        "active_plan": PLAN,
        "preflight_council": COUNCIL,
        "freeze_code": SCRIPT,
    }
    for name, path in inputs.items():
        if not path.is_file():
            raise RuntimeError(f"missing controlling input: {name}: {path}")
    if sha(CONTRACT) != EXPECTED["contract"]:
        raise RuntimeError("controlling contract hash mismatch")
    if sha(inputs["v8_package_manifest"]) != EXPECTED["v8_manifest"]:
        raise RuntimeError("V8 manifest hash mismatch")
    if inputs["v8_external_anchor"].read_text(encoding="ascii").strip() != EXPECTED["v8_manifest"]:
        raise RuntimeError("V8 external anchor mismatch")
    if sha(READER) != EXPECTED["reader_split"] or sha(inputs["metadata_manifest"]) != EXPECTED["metadata_manifest"]:
        raise RuntimeError("reader/metadata authority hash mismatch")
    v8_status = json.loads(inputs["v8_terminal_status"].read_text(encoding="utf-8"))
    if v8_status.get("status") != "PASS_FULL104_EXPRESSION_INTERFACE_VERIFIED" or v8_status.get("phase2_started"):
        raise RuntimeError("V8 gate unavailable")
    metadata_status = json.loads(inputs["metadata_status"].read_text(encoding="utf-8"))
    if metadata_status.get("status") != "PASS_FULL104_PRODUCTION_SCOPE_RECONCILED" or metadata_status.get("phase2_started"):
        raise RuntimeError("metadata gate unavailable")
    return inputs


def build_inventory() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    reader = pd.read_csv(READER, dtype=str)
    fit = set(reader.loc[reader.reader_partition.eq("reader_fit"), "donor_id"])
    if len(fit) != FROZEN["reader_fit_donors"]:
        raise RuntimeError("reader-fit donor count mismatch")
    sd = pd.read_csv(DISCOVERY / "FOUNDATION_METADATA_SOURCE_X_DONOR.csv")
    sd = sd[sd.donor_id.astype(str).isin(fit)].copy()
    if len(sd) != len(fit) or sd.donor_id.nunique() != len(fit) or sd.groupby("donor_id").source.nunique().max() != 1:
        raise RuntimeError("one-source-per-fit-donor authority mismatch")
    op = pd.read_csv(DISCOVERY / "FOUNDATION_METADATA_DONOR_X_OPERATOR.csv")
    op = op[op.donor_id.astype(str).isin(fit)].copy()
    totals = op.groupby("donor_id", as_index=False).cell_count.sum().rename(columns={"cell_count": "operator_sum"})
    inv = sd[["source", "donor_id", "cell_count"]].merge(totals, on="donor_id", validate="one_to_one")
    if not np.array_equal(inv.cell_count.to_numpy(np.int64), inv.operator_sum.to_numpy(np.int64)):
        raise RuntimeError("donor total mismatch")
    inv = inv.drop(columns="operator_sum").sort_values(["source", "donor_id"]).reset_index(drop=True)
    if int(inv.cell_count.sum()) != 4_553_407 or set(inv.source) != {"HVS", "NPH52", "SEA_AD"}:
        raise RuntimeError("fit104 corpus geometry mismatch")
    inv["primary_donor_weight"] = 1.0 / len(inv)
    inv["natural_cell_weight_within_donor"] = 1.0 / inv.cell_count
    inv["primary_row_weight"] = inv.primary_donor_weight * inv.natural_cell_weight_within_donor

    minimum = int(inv.groupby("source").size().min())
    folds = min(FROZEN["fold_maximum"], minimum // FROZEN["fold_min_donors_per_source"])
    if folds < 2:
        raise RuntimeError("insufficient grouped donor folds")
    assignment = []
    for source, group in inv.groupby("source", sort=True):
        ordered = group.assign(tie=group.donor_id.map(lambda d: hash_key("PHASE2_FOLD", source, d)))
        ordered = ordered.sort_values(["cell_count", "tie", "donor_id"], ascending=[False, True, True]).reset_index(drop=True)
        snake = list(range(folds)) + list(range(folds - 1, -1, -1))
        for i, row in ordered.iterrows():
            assignment.append({"donor_id": row.donor_id, "source": source, "outer_fold": snake[i % len(snake)]})
    fold = pd.DataFrame(assignment).sort_values(["outer_fold", "source", "donor_id"]).reset_index(drop=True)
    if fold.donor_id.nunique() != len(inv) or fold.groupby(["outer_fold", "source"]).size().min() < FROZEN["fold_min_donors_per_source"]:
        raise RuntimeError("fold source coverage mismatch")
    op = op.merge(fold[["donor_id", "outer_fold"]], on="donor_id", validate="many_to_one")
    return inv, fold, op


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        raise RuntimeError("prospective freeze output already exists")
    out.mkdir(parents=True)
    inputs = authenticate()
    inv, folds, donor_operator = build_inventory()
    inv_path = out / "PHASE2_DONOR_INVENTORY.csv"
    fold_path = out / "PHASE2_DONOR_FOLDS.csv"
    coverage_path = out / "PHASE2_FOLD_OPERATOR_COVERAGE.csv"
    inv.to_csv(inv_path, index=False, lineterminator="\n")
    folds.to_csv(fold_path, index=False, lineterminator="\n")
    donor_operator.groupby(["outer_fold", "matrix_id"], as_index=False).agg(
        donors=("donor_id", "nunique"), cells=("cell_count", "sum")
    ).to_csv(coverage_path, index=False, lineterminator="\n")

    donor_counts = inv.set_index("donor_id").cell_count.astype(np.int64)
    ladder = []
    for level, quantile in enumerate(FROZEN["sample_quantiles"]):
        cap = int(np.quantile(donor_counts.to_numpy(), quantile, method="lower"))
        ladder.append({
            "level": level,
            "donor_capacity_quantile": quantile,
            "per_donor_cap": cap,
            "selected_cells": int(np.minimum(donor_counts, cap).sum()),
            "selection": "nested deterministic donor-global hash order; all cells when donor capacity is below cap",
        })
    ladder.append({
        "level": len(ladder), "donor_capacity_quantile": "FULL", "per_donor_cap": "FULL",
        "selected_cells": int(donor_counts.sum()),
        "selection": "fallback full authenticated fit104 stream if sample-ladder geometry is unsaturated",
    })
    ladder_path = out / "PHASE2_SAMPLE_LADDER.csv"
    pd.DataFrame(ladder).to_csv(ladder_path, index=False, lineterminator="\n")

    search_rank = 2 * FROZEN["d_gene"]
    sketch_dim = 1 << math.ceil(math.log2(math.ceil(1.5 * search_rank)))
    mask_blocks = FROZEN["visible_fraction_denominator"] * FROZEN["views"]
    visible_blocks = FROZEN["visible_fraction_numerator"] * FROZEN["views"]
    prefix_block = 2 * FROZEN["views"]
    prefix_grid = list(range(prefix_block, search_rank + 1, prefix_block))
    resamples = 1 << math.ceil(math.log2(max(2, search_rank // 2)))
    seeds = {
        name: hashlib.sha256(("FULL104_PHASE2_V1|" + name).encode()).hexdigest()
        for name in ["cell_order", "four_views", "feature_sketch_A", "feature_sketch_B", "donor_bootstrap", "matched_null", "fold_ties", "direct_basis_cv"]
    }
    rng_path = out / "PHASE2_RNG_KEYS.json"
    write_json(rng_path, {"schema": "full104-phase2-rng-v1", "keys": seeds, "derivation": "SHA256(FULL104_PHASE2_V1|purpose)"})
    descriptors = {
        "allowed": [
            "log1p_source_library", "scalar_measured_fraction", "structurally_unmeasured_fraction",
            "collision_unresolved_fraction", "scalar_nonzero_fraction", "visible_scalar_fraction",
        ],
        "forbidden": [
            "donor_id", "source", "dataset_id", "matrix_id", "operator_id", "file_or_shard_id",
            "native_annotation", "cell_type", "biology_or_program_label", "pathology", "diagnosis",
        ],
        "rule": "allowed descriptors are continuous physical evidence/depth summaries only; identity remains audit sidecar",
    }
    descriptor_path = out / "PHASE2_PHYSICAL_DESCRIPTOR_ALLOWLIST.json"
    write_json(descriptor_path, descriptors)
    dag = {
        "ordered_nodes": ["shared_state", "private_state", "capacity_gate", "teacher_standardization", "direct_basis_ridge"],
        "dependencies": {
            "shared_state": ["preexpression_freeze", "metadata_selection_manifest"],
            "private_state": ["shared_state_hash", "physical_descriptor_allowlist"],
            "capacity_gate": ["shared_state_hash", "private_state_hash"],
            "teacher_standardization": ["dimension_selection_hash", "fit104_only_teacher_coordinates"],
            "direct_basis_ridge": ["dimension_selection_hash", "standardization_hash", "nested_donor_cv"],
        },
        "prohibited_nodes": ["query_geometry", "schedule", "gpu_mechanics", "optimizer", "ema", "lambda", "u0_u205_training"],
    }
    dag_path = out / "PHASE2_ARTIFACT_DAG.json"
    write_json(dag_path, dag)

    input_rows = []
    for name, path in inputs.items():
        input_rows.append({"name": name, "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "bytes": path.stat().st_size, "sha256": sha(path), "authority_tag": "FROZEN_AUTHORITY"})
    input_path = out / "PHASE2_INPUT_HASHES.csv"
    pd.DataFrame(input_rows).to_csv(input_path, index=False, lineterminator="\n")

    freeze = {
        "schema": "full104-phase2-derivation-freeze-v1",
        "status": "FROZEN_BEFORE_PHASE2_EXPRESSION",
        "authority": "FROZEN_AUTHORITY",
        "scope": ["shared_state", "private_state", "capacity_gate", "teacher_standardization", "direct_basis_ridge"],
        "primary_estimand": {
            "rule": "equal influence for every reader-fit donor; equal cell influence within donor",
            "source_weights_derived_from_fit_donor_composition": {k: int(v) / len(inv) for k, v in inv.groupby("source").size().items()},
            "raw_cell_count_weighting_prohibited": True,
            "forced_equal_thirds_prohibited": True,
            "sensitivities_nonselecting": FROZEN["source_sensitivities"],
        },
        "sampling": {
            "ladder_path": ladder_path.name,
            "selection_order": "SHA256(cell_order_key|source|donor|operator|canonical_cell_id|row_locator)",
            "stopping": "smallest nested level within one donor-bootstrap SE of the largest evaluated level for held-donor predictability, with no material donor-resampled subspace loss; otherwise advance; full stream is fail-safe final level",
            "operator_role": "natural within-donor composition; coverage reported, never pooled-cell reweighting",
        },
        "shared": {
            "views": FROZEN["views"],
            "visible_fraction": FROZEN["visible_fraction_numerator"] / FROZEN["visible_fraction_denominator"],
            "mask_blocks": mask_blocks,
            "selected_blocks": visible_blocks,
            "exact_count_repair": "deterministic trim/add within boundary blocks to floor(0.60*MEASURED_SCALAR)",
            "feature_sketch_dimension": sketch_dim,
            "feature_channels": {"value_signed_countsketch": sketch_dim // 2, "visibility_signed_countsketch": sketch_dim // 2},
            "independent_sketches": 2,
            "candidate_search_rank": search_rank,
            "candidate_prefix_grid": prefix_grid,
            "donor_resamples": resamples,
            "matched_null_replicates": resamples,
            "outer_folds": int(folds.outer_fold.nunique()),
            "null": "independent view derangements within donor×operator; preserve source/operator/support/depth/view marginals; report unbroken singleton fraction",
            "selection": "contiguous observed prefix above selection-aware matched null and stable under donor resampling; smallest prefix within one donor-level SE of best held-donor cross-view predictability",
            "boundary": "stable unsaturated signal at maximum search rank => STUDENT_CAPACITY_LIMIT; no forced boundary selection",
            "numerics": "canonical shard/operator order; float64 compensated donor sufficient statistics; two deterministic sketches; eigensolver residual/orthogonality/conditioning and principal-angle agreement",
        },
        "private": {
            "starts_only_after_shared_hash_freeze": True,
            "target": "full-rich molecular sketch residual after cross-fitted shared state and allowlisted physical descriptors",
            "selection": "contiguous residual prefix above matched null with nonzero donor-heldout partial-view predictability; smallest within one donor-level SE",
            "zero_is_lawful": True,
        },
        "capacity": {
            "historical_96_is_not_authority": True,
            "d_gene_160_is_not_assumed_state_ceiling": True,
            "test": "selected D_total against hash-pinned parameterized production tensor interfaces, serialization, forward shape, direct-route rank and contextual residual bottleneck; no inward dimension movement",
        },
        "standardization": "mergeable float64 equal-donor moments on fit104 teacher coordinates only; separate hash artifact; deterministic near-zero-scale rule",
        "direct_basis_ridge": {
            "eligible_universe": FROZEN["addresses"],
            "historical_4096_filter_prohibited": True,
            "ranking": "donor-reproducible cross-fitted association with standardized frozen teacher state across full address universe, with physical availability explicit",
            "basis_grid": "D_total-scaled geometric prefixes through every eligible address, including full-universe candidate",
            "ridge_grid": "trace-scaled log grid frozen by procedure before fold outcomes",
            "selection": "nested grouped donor CV on standardized per-coordinate/block teacher-state error; smallest basis/ridge within one donor-level SE",
        },
        "resume": {
            "atomic_state": ["input hashes", "canonical cursor", "processed row counts and weights", "float64 donor sufficient statistics", "fold/resample/null maps", "RNG states", "solver state", "code/environment hashes"],
            "restart_fixture_required": True,
            "failure_status": "STOP_NUMERICAL_GEOMETRY_UNSTABLE",
        },
        "stop_conditions": [
            "authority/firewall/namespace/observation mismatch", "protected expression access", "TEACHER_BIOLOGY_LIMIT",
            "STUDENT_CAPACITY_LIMIT", "STOP_NUMERICAL_GEOMETRY_UNSTABLE", "unstable direct-basis donor-CV solution",
            "missing authority tag or artifact dependency",
        ],
        "no_expression_opened": True,
        "no_validation_or_oracle": True,
        "no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": True,
    }
    freeze_path = out / "PHASE2_DERIVATION_FREEZE.json"
    write_json(freeze_path, freeze)

    derived_files = [inv_path, fold_path, coverage_path, ladder_path, rng_path, descriptor_path, dag_path, input_path, freeze_path]
    ledger_rows = []
    for name, value, tag, procedure, artifact in [
        ("molecular_addresses", FROZEN["addresses"], "FROZEN_AUTHORITY", "controlling Molecular Ledger", inputs["address_registry"]),
        ("fit_donors", len(inv), "DERIVE_ON_104_FIT", "authenticated reader split intersect source×donor authority", inv_path),
        ("fit_cells", int(inv.cell_count.sum()), "DERIVE_ON_104_FIT", "sum authenticated donor×operator counts", inv_path),
        ("outer_donor_folds", int(folds.outer_fold.nunique()), "DERIVE_ON_104_FIT", "largest K<=8 with >=3 donors/source/fold; deterministic source-stratified snake", fold_path),
        ("four_views", FROZEN["views"], "FROZEN_AUTHORITY", "controlling four-view teacher family", freeze_path),
        ("visible_fraction", 0.6, "FROZEN_AUTHORITY", "controlling primary evidence fraction", freeze_path),
        ("candidate_search_rank", search_rank, "FROZEN_AUTHORITY", "prospective overcomplete rank=2*d_gene; boundary is a STOP, not selection", freeze_path),
        ("feature_sketch_dimension", sketch_dim, "FROZEN_AUTHORITY", "next power of two >=1.5*candidate rank", freeze_path),
        ("donor_resamples", resamples, "FROZEN_AUTHORITY", "next power of two >=candidate_rank/2", freeze_path),
        ("matched_null_replicates", resamples, "FROZEN_AUTHORITY", "same Monte Carlo resolution as donor resamples", freeze_path),
    ]:
        ledger_rows.append({
            "field": name, "value": value, "authority_tag": tag, "input_hashes": sha(input_path),
            "derivation_procedure": procedure, "procedure_hash": sha(SCRIPT), "result_artifact": artifact.name,
            "result_hash": sha(artifact),
        })
    ledger_path = out / "PHASE2_NUMERIC_AUTHORITY_LEDGER.csv"
    pd.DataFrame(ledger_rows).to_csv(ledger_path, index=False, lineterminator="\n")
    derived_files.append(ledger_path)

    manifest_path = out / "PHASE2_PREEXPRESSION_MANIFEST.csv"
    rows = []
    for path in sorted(derived_files):
        rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)})
    pd.DataFrame(rows).to_csv(manifest_path, index=False, lineterminator="\n")
    anchor_path = out.parent / "PHASE2_PREEXPRESSION_MANIFEST_SHA256.txt"
    anchor_path.write_text(sha(manifest_path) + "\n", encoding="ascii")
    print(json.dumps({
        "status": freeze["status"], "fit_donors": len(inv), "fit_cells": int(inv.cell_count.sum()),
        "outer_folds": int(folds.outer_fold.nunique()), "sample_ladder": ladder,
        "manifest_sha256": sha(manifest_path), "expression_opened": False,
    }, indent=2))


if __name__ == "__main__":
    main()
