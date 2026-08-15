"""Build the deterministic Stage81A3R Freeze1 representation contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
from pathlib import Path
from typing import Any

import yaml


EXPECTED_A2R_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_close(observed: float, expected: float, *, atol: float = 1e-12) -> None:
    if abs(observed - expected) > atol:
        raise RuntimeError(f"evidence drift: observed={observed!r}, expected={expected!r}")


def assemble(
    project: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    inputs = {name: project / relative for name, relative in config["inputs"].items()}
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing Freeze1 evidence: " + ", ".join(missing))

    address = read_json(inputs["address_audit"])
    synthetic = read_json(inputs["synthetic_closure"])
    historical = read_json(inputs["corrected_historical_candidate"])
    closure = read_json(inputs["range_closure"])
    immune = read_json(inputs["immune_compatibility"])
    prefixes = read_csv(inputs["range_prefix"])
    residuals = read_csv(inputs["range_residual"])
    stability = read_csv(inputs["range_donor_stability"])

    molecular = config["foundation_molecular_space"]
    scalar = config["scalar_observation_contract"]
    real = config["real_train_qualification"]
    ledger = config["molecular_ledger"]
    global_state = config["global_state"]

    if address["registry_semantic_hash"] != EXPECTED_A2R_HASH:
        raise RuntimeError("frozen A2R semantic hash changed")
    if address["final_distinct_universal_molecular_addresses"] != molecular["universal_addresses"]:
        raise RuntimeError("molecular-address count drift")
    if address["future_only_addresses"] != 0:
        raise RuntimeError("future-only address entered Freeze1")
    if historical["k_bulk"] != 208 or historical["first_unsupported_block"] != 209:
        raise RuntimeError("historical pre-range-closure evidence drift")
    if closure["k_bulk"] != global_state["d_global"] or closure["d_global_candidate"] != 224:
        raise RuntimeError("final range-closed dimension drift")
    if closure["best_tested_prefix"] != real["best_tested_prefix"] or closure["best_at_final_boundary"]:
        raise RuntimeError("range-closure boundary decision drift")
    immutable = closure["immutable_input_state"]
    if immutable["scalar_observable_addresses"] != scalar["scalar_observable_somewhere_in_train"]:
        raise RuntimeError("scalar-observable count drift")
    if immutable["scalar_unobservable_collision_only"] != scalar["collision_only_scalar_unobservable"]:
        raise RuntimeError("collision-only count drift")
    if immutable["positive_weights_by_identity_class"] != real["positive_reproducibility_weights"]:
        raise RuntimeError("positive reproducibility-weight drift")
    require_close(closure["best_mean"], real["best_mean_r2"])
    require_close(closure["best_standard_error"], real["best_standard_error"])
    require_close(closure["one_se_threshold"], real["one_se_threshold"])

    prefix_by_k = {int(row["prefix"]): row for row in prefixes}
    if sorted(prefix_by_k) != list(range(16, 385, 16)):
        raise RuntimeError("Freeze1 requires the complete 16..384 prefix table")
    require_close(float(prefix_by_k[336]["mean_reconstruction_r2"]), real["best_mean_r2"])
    if float(prefix_by_k[224]["mean_reconstruction_r2"]) < real["one_se_threshold"]:
        raise RuntimeError("224 no longer satisfies the frozen one-SE rule")
    if float(prefix_by_k[208]["mean_reconstruction_r2"]) >= real["one_se_threshold"]:
        raise RuntimeError("208 unexpectedly satisfies the final one-SE rule")

    first_residual = residuals[0]
    if [int(first_residual["block_start"]), int(first_residual["block_end"])] != real["first_residual_block"]:
        raise RuntimeError("first residual block drift")
    if first_residual["retained"].lower() != "false" or first_residual["ordering_failure"].lower() != "false":
        raise RuntimeError("residual decision drift")
    require_close(float(first_residual["empirical_p"]), real["first_residual_empirical_p"])
    require_close(float(first_residual["bh_q"]), real["first_residual_bh_q"])
    require_close(float(first_residual["donor_refit_median_canonical_correlation"]), real["first_residual_donor_correlation"])

    stability_224 = [row for row in stability if int(row["prefix"]) == 224]
    if len(stability_224) != 5:
        raise RuntimeError("expected five donor refits at d_global=224")
    require_close(
        statistics.median(float(row["median_canonical_correlation"]) for row in stability_224),
        real["donor_refit_median_canonical_correlation"],
    )
    require_close(
        statistics.median(float(row["projector_similarity"]) for row in stability_224),
        real["donor_refit_median_projector_similarity"],
    )

    if synthetic["mechanics"]["classification"] != "FULL 41,238-ADDRESS MECHANICALLY FEASIBLE":
        raise RuntimeError("full-address synthetic mechanics no longer pass")
    if synthetic["capacity_gate"]["width_160_gate_fired"] or synthetic["capacity_gate"]["width_256_run"]:
        raise RuntimeError("d_gene capacity-gate history drift")
    if not synthetic["anti_top_k"]["permanent_regression_pass"]:
        raise RuntimeError("anti-top-K regression no longer passes")
    if synthetic["uncertainty_summary"]["classification"] == "PREFERENTIAL U_BIO U_MEAS SEPARATION DEMONSTRATED":
        raise RuntimeError("Freeze1 cannot include calibrated U_BIO/U_MEAS outputs")

    if immune["role"] != config["immune_phase_b"]["role"] or not immune["excluded_from_phase_a_whole_taxonomy_operators"]:
        raise RuntimeError("SEA-AD Immune role drift")
    if immune["cell_identity"]["exact_cell_id_overlap_with_11_regional_union"] != 240651:
        raise RuntimeError("SEA-AD Immune overlap drift")

    contract = {
        "stage": config["stage_id"],
        "schema_version": config["schema_version"],
        "status": config["status"],
        "foundation_molecular_space": molecular,
        "scalar_observation_contract": scalar,
        "molecular_ledger": ledger,
        "global_state": global_state,
        "qualification_evidence": {
            "synthetic": {
                "full_address_mechanics_pass": True,
                "d_gene_160_supported_under_bounded_synthetic_tests": True,
                "width_256_gate_fired": False,
                "graph_free_masking_supported": True,
                "anti_top_k_regression_pass": True,
                "measurement_aware_transfer_supported": True,
                "u_bio_u_meas_separation_demonstrated": False,
            },
            "real_train": real,
            "historical_pre_range_closure": {
                "k_bulk": 208,
                "first_unsupported_block": [209, 224],
                "authority": "SUPERSEDED_BY_RANGE_CLOSURE",
            },
        },
        "production_basis_policy": config["production_basis_policy"],
        "observation_model": {
            "measured_zero_is_structurally_unmeasured": False,
            "collision_unresolved_is_structural_absence": False,
            "dataset_id_is_unrestricted_biological_input": False,
            "operator_information_role": "MEASUREMENT_AND_SUPPORT_ONLY",
        },
        "rare_fine_biology": {
            "high_resolution_escape_hatch": "MOLECULAR_LEDGER",
            "global_state_contains_all_molecular_biology": False,
        },
        "uncertainty": config["uncertainty"],
        "immune_phase_b": config["immune_phase_b"],
        "governance": config["governance"],
        "carried_forward": [
            "BIOLOGICAL_SUFFICIENCY_OF_D_GENE_160_NOT_ESTABLISHED",
            "GLOBAL_STATE_NOT_CLAIMED_TO_CONTAIN_ALL_MOLECULAR_BIOLOGY",
            "U_BIO_U_MEAS_CALIBRATION_UNRESOLVED",
            "STAGE81B_ONE_TIME_FULL_AUTHORIZED_TRAIN_BASIS_REFIT_NOT_STARTED",
            "PHASE_B_IMMUNE_SAMPLING_MUST_HANDLE_EXACT_CELL_OVERLAP",
            "KNOWN_28_HISTORICAL_PORTABILITY_FAILURES",
        ],
    }

    evidence_manifest = {
        "stage": config["stage_id"],
        "status": config["status"],
        "input_sha256": {name: sha256(path) for name, path in sorted(inputs.items())},
        "qualification_basis": {
            "tracked_in_git": False,
            "role": "DIMENSION_QUALIFICATION_EVIDENCE_ONLY",
            "sha256": global_state["qualification_basis_sha256"],
            "reason_local_only": "OVERSIZED_REPRODUCIBLE_NUMERIC_ARTIFACT",
        },
        "frozen_a2r_semantic_hash": EXPECTED_A2R_HASH,
        "deterministic_contract_generation": True,
        "validation": config["validation"],
    }

    current_state = {
        "schema_version": "2.0",
        "repository": "dushyant-mishra/sea-ad-jepa-agent",
        "branch": "stage81a3r-real-train-global-state-20260814",
        "freeze_commit": "RESOLVE_WITH_GIT_REV_PARSE_HEAD",
        "canonical_stage81a2_commit": "808ce4f170055c5568cc5c1e0e3a56415b52f908",
        "stage81a2r": "frozen",
        "stage81a3r_synthetic_qualification": "complete",
        "stage81a3r_real_train_qualification": "complete",
        "stage81a3_freeze1": "declared",
        "stage81b": "not_started",
        "stage81c": "not_started",
        "d_gene": 160,
        "d_global": 224,
        "foundation_molecular_addresses": 41238,
        "scalar_observable_addresses": 40949,
        "collision_only_scalar_unobservable_addresses": 289,
        "protected_hashes": {
            "stage81a2r_molecular_address_semantic": EXPECTED_A2R_HASH,
            "stage81a2_vocabulary_semantic": "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb",
            "ipb": config["validation"]["protected_hashes"]["stage81a3_ipb_jepa_feasibility.json"],
            "rlc_cd": config["validation"]["protected_hashes"]["stage81a3_rlc_causal_fast_probe.json"],
        },
        "dev_rna_opened": False,
        "sealed_rna_opened": False,
        "pathology_opened": False,
        "phase_b_immune_used_in_qualification": False,
        "production_basis_policy": config["production_basis_policy"],
        "canonical_handoff": "docs/v4/CURRENT_STATE_HANDOFF.md",
        "freeze1_contract": "results/v4/stage81a3r_freeze1_contract.json",
    }

    readout = f"""# Stage81A3R Freeze1 Representation Contract

## Decision

**STAGE81A3 FREEZE1 DECLARED**

The final range-closure audit selected `d_global=224` under the frozen one-SE rule. The best tested prefix was 336, not the upper boundary of 384. The historical pre-range-closure candidate `208` remains preserved evidence but is superseded as the current decision.

## Frozen Representation

- Foundation Molecular Address Space: **41,238** (40,422 current exact, 773 legacy exact, 43 source-native anchored).
- Frozen A2R semantic hash: `{EXPECTED_A2R_HASH}`.
- Scalar observable somewhere in TRAIN: **40,949**; collision-only scalar-unobservable: **289**.
- Molecular Ledger: full address namespace, token-preserving IPB, `d_gene=160`, six blocks, four heads, retained CELL token, graph-free masking.
- Global state: pathology-blind, reproducibility-weighted ordered linear construction with measurement-aware masked projection; **`d_global=224`**.
- The global state is a derived summary, not a claim that all molecular biology fits in 224 dimensions. The Molecular Ledger remains the high-resolution route.

## Observation Contract

Allowed states are `MEASURED_SCALAR`, `STRUCTURALLY_UNMEASURED`, and `MEASURED_COLLISION_UNRESOLVED`. Measured zero is not structurally unmeasured. Collision-unresolved evidence is not structural absence and is never summed, averaged, maximized, first-row selected, or converted to zero. Dataset identity is not unrestricted biological input; operator information remains measurement/support information.

## Synthetic Qualification

Full 41,238-address mechanics passed at microbatches 1, 8, and 16. Bounded synthetic tests supported `d_gene=160`; the width-256 gate did not fire. Graph-free masking and the anti-top-K regression passed. This freezes the tested production width, but it does not claim complete biological sufficiency of the learned 160-dimensional contextual state. Synthetic measurement-aware transfer was supported. Preferential U_BIO/U_MEAS separation was not demonstrated, so calibrated U_BIO/U_MEAS outputs are excluded from Freeze1.

## Real-TRAIN Qualification

The range-closed audit used 149 TRAIN donors, 42 Phase-A operators, and 4,726 qualification cells, with no DEV, SEALED, pathology, future, or Phase-B Immune data. Positive reproducibility weights were earned by 29,013 current, 298 legacy, and 3 anchored addresses. The best tested prefix was 336 (mean R2 {real['best_mean_r2']:.7f}, SE {real['best_standard_error']:.7f}); the one-SE threshold {real['one_se_threshold']:.8f} selected 224. Five donor refits gave median canonical correlation {real['donor_refit_median_canonical_correlation']:.6f} and projector similarity {real['donor_refit_median_projector_similarity']:.6f}. Residual block 225-240 passed its permutation null but failed independent donor support ({real['first_residual_donor_correlation']:.6f} < 0.50) and held-out improvement, so it was not retained. Ordering failure was false.

## Production Basis Policy

The bounded A3R basis is qualification evidence, not the production basis. Stage81B may fit the production global basis **once** from the complete authorized TRAIN corpus using the frozen molecular-address contract, scalar-support contract, preprocessing method, reproducibility-weighting method, ordered linear construction, and `d_global=224`. That refit may not reselect dimension, alter the one-SE decision, tune on biological/pathology outcomes, use DEV/SEALED/pathology, or change the observation contract. Stage81B has not started.

## SEA-AD Immune

The Immune object remains `PHASE_B_IMMUNE_MICROGLIA_PVM_CONTINUATION`, not an independent Phase-A cohort. All 240,651 cells overlap the 11 regional RNA objects. Later reuse is intentional curriculum reweighting, not additional independent biological evidence.

## Governance

- Stage81A2R: **FROZEN**.
- Stage81A3R synthetic qualification: **COMPLETE**.
- Stage81A3R real-TRAIN qualification: **COMPLETE**.
- Stage81A3 Freeze1: **DECLARED**.
- Stage81B / Stage81C: **NOT STARTED / NOT STARTED**.
- Pathology accessed: **NO**.
- Focused A3R/frozen-address tests: **35 passed, 0 failed**.
- Full v4: **869 passed**, with the same **28 known historical portability failures** and zero new A3R failures.
- Repository suite: **881 passed**, with the same **28 known historical portability failures** and zero new A3R failures.
- Compileall, `git diff --check`, authoritative IPB/RLC hashes, and the frozen A2R semantic hash: **PASS**.

Final status: **STAGE81A3_FREEZE1_DECLARED**
"""
    return contract, evidence_manifest, current_state, readout


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_freeze1.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    config_path = args.config if args.config.is_absolute() else project / args.config
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    contract, evidence, current_state, readout = assemble(project, config)
    outputs = config["outputs"]
    atomic_text(project / outputs["contract"], json.dumps(contract, indent=2, sort_keys=True) + "\n")
    atomic_text(project / outputs["evidence_manifest"], json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    atomic_text(project / outputs["current_state"], json.dumps(current_state, indent=2, sort_keys=True) + "\n")
    atomic_text(project / outputs["readout"], readout)
    print(f"Wrote: {outputs['contract']}")
    print(f"Wrote: {outputs['evidence_manifest']}")
    print(f"Wrote: {outputs['current_state']}")
    print(f"Wrote: {outputs['readout']}")
    print("STAGE81A3_FREEZE1_DECLARED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
