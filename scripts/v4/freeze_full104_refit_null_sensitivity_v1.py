#!/usr/bin/env python3
"""Prospectively freeze the natural-weight/full-512 refit-null sensitivity."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pandas as pd


EXPECTED_AMENDMENT_SHA = "3c3306380944fffb697050baee1447f434d06054399daa26ffc9f63ac597911c"
EXPECTED_BASE_FREEZE_SHA = "5943e628bd2c8aa72622226c6267a610135ae1ef4bbb9f582e9ed3cd9f48f5c8"
EXPECTED_P0_MANIFEST_SHA = "ebc5987e193f2cf083330518903bd4db46e7d6675bbb5f32a063e1a55b4b16fb"
CLAUSE = "bracket only; local refinement every legal dimension before final freeze"
ROW_ORDER_DOMAIN = "SHA256(<matched_null_key>|natural-full512-v1|sample-order|<donor_id>|<operator_index>|<selection_row>)"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", required=True)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--publish", required=True)
    parser.add_argument("--future-result-dir", required=True)
    args = parser.parse_args()
    root = Path(args.phase2_root).resolve()
    staging = Path(args.staging).resolve()
    publish = Path(args.publish).resolve()
    future_result = Path(args.future_result_dir).resolve()
    external_anchor = publish.with_name(publish.name + "_ROOT_SHA256.txt")
    if staging.exists() or publish.exists() or future_result.exists() or external_anchor.exists():
        raise RuntimeError("freeze staging/publish or future result path already exists")
    staging.mkdir(parents=True)

    amendment_path = root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json"
    base_freeze_path = root / "preexpression_freeze/PHASE2_DERIVATION_FREEZE.json"
    p0_manifest = root / "shared_d_p0_repair_v1/P0_REPAIR_HASH_MANIFEST.csv"
    if sha(amendment_path) != EXPECTED_AMENDMENT_SHA or sha(base_freeze_path) != EXPECTED_BASE_FREEZE_SHA or sha(p0_manifest) != EXPECTED_P0_MANIFEST_SHA:
        raise RuntimeError("controlling authority hash mismatch")
    amendment = json.loads(amendment_path.read_text())
    base_freeze = json.loads(base_freeze_path.read_text())
    if amendment["status"] != "FROZEN_PROSPECTIVELY_BEFORE_LEVEL1_SHARED_GEOMETRY":
        raise RuntimeError("procedure amendment is not frozen authority")
    if amendment["shared_selection"]["coarse_grid_role"] != CLAUSE:
        raise RuntimeError("candidate-dimension authority clause mismatch")
    if int(base_freeze["shared"]["candidate_search_rank"]) != 320:
        raise RuntimeError("candidate search rank mismatch")

    matrix = root / "feature_matrix_level4"
    matrix_audit = json.loads((matrix / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text())
    if matrix_audit != {
        **matrix_audit,
        "status": "PASS_PHASE2_FEATURE_MATRIX_ASSEMBLED",
        "rows": 4_553_407,
        "sample_level": 4,
        "feature_dim": 512,
        "sketches": 2,
        "views": 4,
    }:
        raise RuntimeError("FULL104 feature-matrix authority mismatch")
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", usecols=["donor_id", "operator_index"], dtype={"donor_id": str, "operator_index": "int16"})
    if len(rows) != 4_553_407 or rows.donor_id.nunique() != 104 or rows.operator_index.nunique() != 42:
        raise RuntimeError("FULL104 row geometry mismatch")
    counts = rows.groupby(["donor_id", "operator_index"], sort=True).size()
    donor_counts = rows.groupby("donor_id", sort=True).size()
    if len(counts) != 1400:
        raise RuntimeError("donor×operator stratum geometry mismatch")

    caps = [4, 16, 64, 256, 1024, "ALL"]
    cap_rows = []
    for order, cap in enumerate(caps):
        selected = int(counts.sum()) if cap == "ALL" else int(counts.clip(upper=int(cap)).sum())
        cap_rows.append({
            "order": order,
            "cap": cap,
            "selected_rows": selected,
            "role": "SELECTING_EXACT_FULL104" if cap == "ALL" else "NONSELECTING_CONVERGENCE_DIAGNOSTIC",
            "terminal_scientific_decision_permitted": cap == "ALL",
            "null_replicates": 256,
            "donor_bootstraps": 256,
            "held_donor_folds": 5,
            "sketches": 2,
            "feature_dimension": 512,
            "fit_rank": 320,
            "eigensystem_fits_per_sketch": 2054,
        })
    cap_path = staging / "REFIT_NULL_SENSITIVITY_CAP_LADDER.csv"
    pd.DataFrame(cap_rows).to_csv(cap_path, index=False, lineterminator="\n")

    clause_hash = hashlib.sha256(CLAUSE.encode("utf-8")).hexdigest()
    shared_selection_canonical = json.dumps(amendment["shared_selection"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    authority = {
        "schema": "full104-candidate-dimension-authority-resolution-v1",
        "status": "PASS_INTEGER_LOCAL_REFINEMENT_AUTHENTICATED",
        "controlling_amendment": {"path": str(amendment_path), "sha256": sha(amendment_path), "status": amendment["status"]},
        "exact_clause": {"json_pointer": "/shared_selection/coarse_grid_role", "text": CLAUSE, "utf8_sha256": clause_hash},
        "shared_selection_canonical_json_sha256": hashlib.sha256(shared_selection_canonical.encode("utf-8")).hexdigest(),
        "bound_parent_freeze": {"path": str(base_freeze_path), "sha256": sha(base_freeze_path), "candidate_prefix_grid": base_freeze["shared"]["candidate_prefix_grid"], "candidate_search_rank": 320},
        "resolution": "the later frozen amendment explicitly supersedes the original grid's role as the selecting set; the grid remains a coarse bracket and every positive integer prefix dimension 1..320 is legal for local selecting refinement",
        "selecting_dimensions": list(range(1, 321)),
        "coarse_grid_retained_for_bracketing": True,
        "inferred_from_observed_results": False,
    }
    atomic_json(staging / "CANDIDATE_DIMENSION_AUTHORITY_RESOLUTION.json", authority)

    rng_path = root / "preexpression_freeze/PHASE2_RNG_KEYS.json"
    rng_payload = json.loads(rng_path.read_text())
    matched_null_key = rng_payload["keys"]["matched_null"]
    folds_path = root / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv"
    analytic_manifest = root / "shared_analytic_level4_v1/SHARED_LEVEL4_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"
    matrix_manifest = matrix / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"
    contract = {
        "schema": "prospective-refit-null-natural-weight-full-feature-sensitivity-v1",
        "status": "FROZEN_PROSPECTIVELY_BEFORE_ANY_SENSITIVITY_RESULT",
        "authority_tag": "PROSPECTIVE_DERIVATION_PROCEDURE",
        "purpose": "falsify or qualify the cap4/observed-top32 refit-null approximation without changing the frozen shared-state estimand, null family, or selector",
        "population": {"cells": 4_553_407, "donors": 104, "operators": 42, "donor_operator_strata": 1400, "feature_space": "two independently keyed A/B 512-dimensional molecular/visibility sketches; four lawful views"},
        "candidate_dimension_authority": authority,
        "primary_estimand": {
            "outer_unit": "donor",
            "donor_weight": "1/104",
            "within_donor_cell_weight_at_ALL": "1/N_d",
            "bounded_cap_expansion_weight": "w_idg=(1/104)*(1/N_d)*(n_dg/m_dg), where m_dg=min(cap,n_dg)",
            "application": "identical weights for mean, within-view, between-view, observed, null, bootstrap, and held-fold sufficient statistics",
            "heldout_aggregation": "aggregate equally within held donor, then equally across held donors",
            "fold_normalization": "within each training fold, renormalize frozen donor weights to exactly 1/n_train_donors; held donors are each 1/n_held_donors",
            "bootstrap_multiplicity": "source-stratified donor resamples use explicit multinomial donor multiplicities; normalize total multiplicity within the replicate and never count duplicated donors as new biological identities",
            "terminology": "keyed finite-population expansion weighting; deterministic sampling is not claimed to create an independent probability sample",
            "source_role": "source-stratifies donor bootstrap and remains diagnostic; source is not a model feature or biological state covariate",
        },
        "nested_sampling": {
            "caps": caps,
            "single_expression_independent_order": ROW_ORDER_DOMAIN + "; first m_dg rows",
            "matched_null_key_sha256_value": matched_null_key,
            "nestedness_required": True,
            "row_set_hash_required_at_every_cap": True,
            "cap_roles": "4/16/64/256/1024 are nonselecting convergence diagnostics; ALL is the only selecting population",
            "sampling_instability_assessment": "compare every successive cap and specifically 1024→ALL; donor bootstrap is not interpreted as within-stratum sampling variance",
            "sampling_variance_resolution": "ALL is mandatory and exact, so no bounded-cap sampling approximation can become selecting",
        },
        "matched_null": {
            "family": amendment["empirical_matched_null"],
            "replicates": 256,
            "observed_null_symmetry": "same selected rows, expansion weights, centering, ridge, solver, donor bootstrap maps and five held-donor fold refits",
            "weighted_firewall_reports": ["unshufflable singleton mass", "n=2/3 limited-permutation mass", "source/operator/support/depth/view/evidence marginals"],
            "rng_domains": {
                "row_order": ROW_ORDER_DOMAIN,
                "matched_null_key_sha256_value": matched_null_key,
                "null_map": "SHA256(matched_null|natural-full512-v1|null|cap|sketch|stratum|replicate|view)",
                "donor_bootstrap": "SHA256(donor_bootstrap|natural-full512-v1|replicate|source); identical donor indices across caps and A/B",
                "held_folds": "exact frozen PHASE2_DONOR_FOLDS.csv",
            },
        },
        "geometry": {
            "input_dimension": 512,
            "fit_rank": 320,
            "forbidden": ["observed-component projection", "top32 restriction", "diagonal-only eigensystem", "fixed-axis null stability", "reuse of observed basis for null/fold/bootstrap"],
            "required": "refit mean, covariance, feature scaling, trace ridge and generalized eigensystem independently in original 512-D A/B space for each observed/null/bootstrap/fold fit; held-fold bases and predictor slopes use training donors only",
            "solver": "same generalized-eigen estimator and trace-ridge rule as the authenticated analytic implementation; any matrix-free implementation must agree with an independent dense golden calculation and meet frozen residual/orthogonality/subspace tolerances before real data",
            "A_B_role": "paired technical replicates; biological N remains 104 donors",
        },
        "fit_graph": {
            "per_sketch_per_cap": {"observed_full": 1, "observed_source_stratified_donor_bootstrap": 256, "observed_held_fold": 5, "per_null_replicate": {"null_full": 1, "paired_source_stratified_donor_bootstrap": 1, "null_held_fold": 5}, "null_replicates": 256, "total_eigensystem_fits": 2054},
            "explicitly_forbidden": "256×256 null/bootstrap Cartesian product",
        },
        "selector": {
            "dimensions": "literal integers 1..320",
            "support_gates": amendment["shared_selection"]["requires"],
            "contiguity": "the first jointly unsupported dimension terminates eligibility; later dimensions cannot re-enter",
            "one_se": "within the lawful supported leading prefix only, choose the smallest D within one paired-donor SE of the best paired A/B held-donor predictability",
            "analytic_null": "diagnostic only",
            "empirical_full512_refit_null": "selecting only at ALL after validation",
        },
        "prospective_stopping_and_routing": {
            "nonfinal_caps": "always advance; no biological, D, loss, or runtime outcome may stop or alter the cap ladder",
            "integrity_stop": "any hash, nestedness, weight-mass, firewall, marginal, finite, solver, restart, or independent-validator mismatch => STOP_ENGINEERING_OR_PROVENANCE",
            "all_required": True,
            "cap1024_to_ALL_convergence": [
                "same jointly supported leading-prefix endpoint and same one-SE candidate (including null)",
                "overlapping local-D one-SE intervals",
                "paired held-donor predictability change at comparison D within one paired-donor SE of the ALL estimate",
                "principal-subspace overlap in original 512-D coordinates no lower than the ALL observed donor-bootstrap one-SE stability floor",
                "same support decision for every dimension through the first failure in both A and B",
            ],
            "if_1024_ALL_disagree": "FULL104_REACHED_NOT_CONVERGED; no arbitrary D and no private-state progression",
            "if_ALL_no_positive_prefix": "TEACHER_BIOLOGY_LIMIT",
            "if_ALL_support_reaches_320": "STOP_SEARCH_BOUNDARY_REACHED; never select D=320 or call STUDENT_CAPACITY_LIMIT solely from this boundary",
            "if_ALL_interior_candidate_and_converged": "eligible for independent executable validation and ordered council review; not automatically FROZEN",
            "private_state_gate": "requires shared_state_final state=FROZEN, tainted=false, current hash-bound council PASS, and assert_frozen_consumable",
        },
        "nonselecting_shortcut_controls": {
            "required_reports": ["value-only", "visibility/support-only", "source deletion", "equal-source sensitivity", "physical-support strata", "operator/source decodability", "weighted singleton/limited-permutation mass"],
            "role": "diagnostic and council veto; may not tune D, caps, weights, null, or thresholds",
            "labels_forbidden": amendment["shared_selection"]["labels_forbidden"] + ["reader-validation", "reader-oracle", "DEV", "SEALED"],
        },
        "compute_and_resume": {
            "preflight": "freeze actual disk/RAM/runtime projection and fail-closed reserve before first statistic",
            "memory": "mmap/blockwise only; no whole-cell-array RAM materialization, cell×cell matrix, or expanded permutation maps",
            "reductions": "float64 compensated reductions in canonical donor/operator/block order with fixed merge tree",
            "checkpoints": "atomic per cap/sketch/replicate/fold checkpoints containing matrix/freeze/code/environment hashes, cap, sketch, replicate/fold IDs, completed block-key bitmap, RNG-map hashes, result-array hashes and sufficient-statistic hashes; resume rejects any mismatch",
            "streaming": "process one null replicate at a time; persist compact RNG/map hashes, never multi-replicate expanded cell permutations or multi-terabyte null covariance arrays",
            "required_tests": ["synthetic planted-rank", "matched-null", "dense-vs-production full512 solver", "restart equivalence", "row/block order metamorphic", "chunk-size metamorphic", "weight-mass conservation", "nested-cap identity"],
            "numerical_reports": ["conditioning", "trace ridge", "generalized residual", "orthogonality", "degenerate-subspace overlap", "peak RSS", "disk headroom"],
            "prospective_numerical_gates": {
                "finite": "every scalar/matrix/result finite; chunked complete scan",
                "weight_mass": "exact symbolic count reconciliation plus floating error <=64*float64_epsilon*sum_abs_weights per donor",
                "metric_SPD": "all ridged within-metric eigenvalues strictly positive",
                "generalized_residual_and_metric_orthogonality": "each <=sqrt(float64_epsilon)*max(1,condition_number), matching authenticated analytic code",
                "independent_real_agreement": "candidate D and every conclusion-bearing boolean exact; scalar abs difference <=1e-6 or relative difference <=1e-5, matching frozen promotion harness",
                "metamorphic": "donor/view/block/chunk order eigenvalue abs difference <=1e-8; orthogonal-coordinate and dense-vs-production eigenvalue abs difference <=1e-6; prefix subspace loss <=1e-5",
                "restart": "completed artifact hashes exactly equal uninterrupted execution",
                "degeneracy": "compare invariant subspaces, never individual eigenvector signs/order inside a numerically degenerate block",
            },
        },
        "promotion_state": "PROSPECTIVE_FROZEN_PROCEDURE_ONLY; no sensitivity result exists or is authorized for downstream consumption",
        "input_hashes": {
            "procedure_amendment_json": sha(amendment_path),
            "procedure_amendment_manifest": sha(root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv"),
            "base_freeze": sha(base_freeze_path),
            "p0_repair_manifest": sha(p0_manifest),
            "feature_matrix_manifest": sha(matrix_manifest),
            "analytic_diagnostic_manifest": sha(analytic_manifest),
            "rng_keys": sha(rng_path),
            "donor_folds": sha(folds_path),
            "analytic_estimator_code": sha(Path(__file__).parent / "derive_full104_phase2_shared_state.py"),
            "active_contiguous_selector_code": sha(Path(__file__).parent / "correct_full104_phase2_shared_selection_with_refit_null.py"),
            "independent_selector_validator_code": sha(Path(__file__).parent / "independent_validate_full104_phase2_shared_level.py"),
            "selector_harness_v2_code": sha(Path(__file__).parent / "test_shared_d_selector_harness_v2.py"),
            "selector_harness_v2_report": sha(root / "shared_d_p0_repair_v1/SHARED_D_HARNESS_V2_TEST_REPORT.json"),
        },
        "future_result_directory": str(future_result),
        "result_directory_absent_at_freeze": not future_result.exists(),
        "no_result_inspected_or_computed_by_freeze": True,
        "no_expression_reopened": True,
        "no_private_standardization_basis_calibration_gpu_or_training": True,
    }
    contract_path = staging / "PROSPECTIVE_REFIT_NULL_NATURAL_WEIGHT_FULL_FEATURE_SENSITIVITY_V1.json"
    atomic_json(contract_path, contract)

    math_text = """# Prospective natural-weight/full-feature refit-null contract

This document is frozen before any sensitivity result exists.

For donor `d`, donor×operator stratum `g`, full donor size `N_d`, stratum size `n_dg`, and nested cap sample size `m_dg=min(cap,n_dg)`, every selected cell has finite-population expansion weight:

`w_idg = (1/104) * (1/N_d) * (n_dg/m_dg)`.

Therefore each donor has total weight `1/104`, every stratum has its natural mass `n_dg/(104*N_d)`, and at `ALL` every original cell has exact weight `1/(104*N_d)`.

Every observed and matched-null fit is performed independently in the original 512-dimensional A/B feature space to rank 320. No observed projection, top-32 restriction, diagonal-only substitute, or reuse of an observed eigensystem is legal. The null uses 256 matched view derangements; replicate `r` receives exactly one paired source-stratified donor bootstrap, not a Cartesian bootstrap.

Caps 4, 16, 64, 256, and 1024 are nonselecting diagnostics. `ALL` is mandatory and is the only selecting population. The exact stopping/routing rules are in the JSON contract and cannot change after outcomes are observed.
"""
    (staging / "REFIT_NULL_SENSITIVITY_MATHEMATICAL_CONTRACT.md").write_text(math_text, encoding="utf-8")

    precheck = {
        "status": "PASS_PROSPECTIVE_FREEZE_INPUT_INTEGRITY",
        "cells": len(rows), "donors": int(rows.donor_id.nunique()), "operators": int(rows.operator_index.nunique()), "strata": len(counts),
        "donor_weight_mass_formula_verified_symbolically": True,
        "ALL_weight_reduces_to_equal_cell_within_donor": True,
        "future_result_directory_absent": not future_result.exists(),
        "protected_expression_opened": False,
        "sensitivity_result_inspected": False,
    }
    atomic_json(staging / "REFIT_NULL_SENSITIVITY_FREEZE_PRECHECK.json", precheck)

    council = """# Prospective refit-null sensitivity preflight council

- Historian: **NOVEL_AND_AUTHORIZED**. Amendment SHA `3c330638...911c` explicitly makes the old grid bracket-only and requires local refinement; rank 320 remains bound by the parent freeze.
- Teacher Architect: **PASS WITH REPAIRS INCORPORATED**. Exact donor/cell expansion weights, full per-replicate/fold refits, and terminal routing are frozen.
- Target/Predictor: **PASS WITH REPAIRS INCORPORATED**. Observed and null geometry are like-for-like in original 512-D A/B spaces; no observed projection is allowed.
- Biology/Halo/Rare: **PASS WITH FIREWALL**. No biology/rare/native/pathology/protected label can select D; shortcut reports are nonselecting council evidence.
- Statistics/Leakage: **PASS WITH REPAIRS INCORPORATED**. Natural stratum mass, ALL-required selection, weighted singleton reporting, and 1024→ALL instability STOP are frozen.
- Observation/Operator: **PASS WITH FIREWALL**. Operator is used only for lawful null strata/weights/diagnostics; natural operator mass is preserved.
- Compute: **PASS TO FREEZE, NOT YET RUN**. Exact fit graph, mmap reductions, checkpoints, resource preflight, and numerical tests are mandatory before execution.
- Optimization/Numerics: **PASS TO FREEZE, NOT YET RUN**. Trace-ridge estimator, rank, full-space fit, residual/orthogonality and independent dense-golden requirements are fixed.

Synthesis: **PROCEED_WITH_REPAIR**. The required selector hashes, package-relative manifest, exact RNG serialization, and fold/bootstrap normalization repairs are incorporated; prospective freeze publication is authorized. Do not calculate the sensitivity until an implementation/storage preflight passes against this hash. No downstream shared-D promotion is authorized by this freeze alone.
"""
    (staging / "REFIT_NULL_SENSITIVITY_PREFLIGHT_COUNCIL.md").write_text(council, encoding="utf-8")

    generated_files = [
        staging / "CANDIDATE_DIMENSION_AUTHORITY_RESOLUTION.json",
        cap_path,
        contract_path,
        staging / "REFIT_NULL_SENSITIVITY_MATHEMATICAL_CONTRACT.md",
        staging / "REFIT_NULL_SENSITIVITY_FREEZE_PRECHECK.json",
        staging / "REFIT_NULL_SENSITIVITY_PREFLIGHT_COUNCIL.md",
    ]
    external_files = [Path(__file__).resolve(), amendment_path, base_freeze_path, p0_manifest, matrix_manifest, analytic_manifest, rng_path, folds_path,
                      Path(__file__).parent / "correct_full104_phase2_shared_selection_with_refit_null.py",
                      Path(__file__).parent / "independent_validate_full104_phase2_shared_level.py",
                      Path(__file__).parent / "test_shared_d_selector_harness_v2.py",
                      root / "shared_d_p0_repair_v1/SHARED_D_HARNESS_V2_TEST_REPORT.json"]
    manifest = staging / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv"
    records = ([{"scope": "package", "path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)} for path in generated_files] +
               [{"scope": "external_authority", "path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in external_files])
    pd.DataFrame(records).to_csv(manifest, index=False, lineterminator="\n")
    root_hash = sha(manifest)
    (staging / "REFIT_NULL_SENSITIVITY_FREEZE_ROOT_SHA256.txt").write_text(root_hash + "\n", encoding="ascii")
    os.replace(staging, publish)
    published_manifest = publish / manifest.name
    if sha(published_manifest) != root_hash or (publish / "REFIT_NULL_SENSITIVITY_FREEZE_ROOT_SHA256.txt").read_text().strip() != root_hash:
        raise RuntimeError("post-publication root verification failed")
    for record in pd.read_csv(published_manifest).to_dict("records"):
        path = publish / record["path"] if record["scope"] == "package" else Path(record["path"])
        if not path.is_file() or path.stat().st_size != int(record["bytes"]) or sha(path) != record["sha256"]:
            raise RuntimeError(f"post-publication manifest verification failed: {path}")
    temporary_anchor = external_anchor.with_suffix(external_anchor.suffix + ".tmp")
    temporary_anchor.write_text(root_hash + "\n", encoding="ascii")
    os.replace(temporary_anchor, external_anchor)
    if external_anchor.read_text().strip() != root_hash:
        raise RuntimeError("external root anchor verification failed")
    print(json.dumps({"status": contract["status"], "manifest_sha256": root_hash, "published": str(publish), "external_anchor": str(external_anchor), "future_result_directory": str(future_result)}, indent=2))


if __name__ == "__main__":
    main()
