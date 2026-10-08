#!/usr/bin/env python3
"""Publish the focused FULL104 shared-D P0 repair/adjudication package."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def leading_prefix(common: dict[int, bool], rank: int) -> list[int]:
    result = []
    for dimension in range(1, rank + 1):
        if not common.get(dimension, False):
            break
        result.append(dimension)
    return result


def manifest_hash(path: Path) -> str | None:
    return sha(path) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", required=True)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--publish", required=True)
    args = parser.parse_args()
    root = Path(args.phase2_root).resolve()
    staging = Path(args.staging).resolve()
    publish = Path(args.publish).resolve()
    if publish.exists():
        raise RuntimeError("published P0 package already exists")
    staging.mkdir(parents=True, exist_ok=True)

    scripts = Path(__file__).resolve().parent
    roles = {
        "analytic_shared_state": "derive_full104_phase2_shared_state.py",
        "empirical_matched_null": "derive_full104_phase2_shared_empirical_null.py",
        "refitted_null": "validate_full104_phase2_empirical_null_refit.py",
        "corrected_selection": "correct_full104_phase2_shared_selection_with_refit_null.py",
        "independent_validation": "independent_validate_full104_phase2_shared_level.py",
        "ladder_adjudication": "adjudicate_full104_phase2_shared_ladder_refit.py",
        "promotion_state_core": "jepa_scientific_promotion_harness_v1.py",
        "p0_package_and_real_dag": Path(__file__).name,
    }
    superseded = {
        "adjudicate_full104_phase2_shared_ladder.py": "pre-refit ladder route; executable fail-closed guard installed",
        "freeze_full104_phase2_shared_candidate.py": "pre-refit Level-1 freezer; executable fail-closed guard installed",
        "record_full104_shared_promotion_state.py": "Level-2-only snapshot; executable fail-closed guard installed",
    }
    authority = {
        "schema": "full104-active-shared-d-code-authority-v1",
        "status": "P0_REPAIRED_CODE_PATH__SCIENTIFIC_PROMOTION_BLOCKED",
        "authoritative": {role: {"path": str(scripts / name), "sha256": sha(scripts / name)} for role, name in roles.items()},
        "superseded_do_not_use": {name: {"path": str(scripts / name), "sha256": sha(scripts / name), "reason": reason} for name, reason in superseded.items()},
        "frozen_authorities": {
            "phase2_freeze": sha(root / "preexpression_freeze/PHASE2_DERIVATION_FREEZE.json"),
            "procedure_amendment": sha(root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json"),
            "promotion_harness_v1": sha(root / "scientific_promotion_harness_v1/JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1.json"),
        },
        "upstream_recomputed": False,
    }
    write_json(staging / "ACTIVE_SHARED_D_CODE_AUTHORITY.json", authority)

    freeze = json.loads((root / "preexpression_freeze/PHASE2_DERIVATION_FREEZE.json").read_text())
    amendment = json.loads((root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json").read_text())
    provisional = json.loads((root / "shared_analytic_level4_v1/SHARED_DIMENSION_SELECTION_PROVISIONAL.json").read_text())
    calibration_dims = sorted(pd.read_csv(root / "shared_analytic_level4_v1/TEACHER_DIMENSION_CALIBRATION_SHARED.csv").dimension.astype(int).unique().tolist())
    prefix_audit = {
        "schema": "full104-contiguous-prefix-rule-audit-v1",
        "status": "PASS_MECHANICAL_REPAIR__PROMOTION_BLOCKED_BY_REFIT_NULL_METHOD",
        "frozen_rule": freeze["shared"]["selection"],
        "candidate_prefix_grid": freeze["shared"]["candidate_prefix_grid"],
        "grid_interpretation": amendment["shared_selection"]["coarse_grid_role"],
        "calibration_dimensions": calibration_dims,
        "level4_descriptive_fields": {
            "best": provisional.get("best"),
            "eligible": provisional.get("eligible"),
            "one_se_candidate_descriptive": provisional.get("one_se_candidate_descriptive"),
            "D_shared_provisional": provisional.get("D_shared_provisional"),
        },
        "dimension_5_interpretation": "literal dimension D=5, not candidate-prefix index 5 (which would be D=40)",
        "provenance_mismatch": False,
        "old_behavior": "all jointly passing dimensions remained eligible, permitting re-entry after a failed dimension",
        "repaired_behavior": "eligibility is exactly the jointly supported leading run starting at D=1; the first false or missing dimension terminates it; one-SE is applied only inside that run",
        "production_selector_sha256": sha(scripts / roles["corrected_selection"]),
        "independent_selector_sha256": sha(scripts / roles["independent_validation"]),
    }
    write_json(staging / "CONTIGUOUS_PREFIX_RULE_AUDIT.json", prefix_audit)

    ladder_rows = []
    level_specs = {
        1: ("shared_analytic_level1_v2", "shared_empirical_level1_v2", "shared_selection_refit_corrected_level1_v2", "shared_selection_contiguous_level1_v1"),
        2: ("shared_analytic_level2_v1", "shared_empirical_level2_v1", "shared_selection_refit_corrected_level2_v1", "shared_selection_contiguous_level2_v1"),
        3: ("shared_analytic_level3_v1", "shared_empirical_level3_v1", "shared_selection_refit_corrected_level3_v1", "shared_selection_contiguous_level3_v1"),
    }
    for level, (analytic_dir, empirical_dir, old_dir, new_dir) in level_specs.items():
        analytic = pd.read_csv(root / analytic_dir / "TEACHER_DIMENSION_CALIBRATION_SHARED.csv")
        empirical = pd.read_csv(root / empirical_dir / "TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL.csv")
        refit = pd.read_csv(root / old_dir / "TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL_REFIT_CORRECTED.csv")
        old = json.loads((root / old_dir / "SHARED_DIMENSION_SELECTION_LEVEL_REFIT_CORRECTED.json").read_text())
        new = json.loads((root / new_dir / "SHARED_DIMENSION_SELECTION_LEVEL_REFIT_CORRECTED.json").read_text())
        refit_support = {}
        for sketch in "AB":
            rows = refit[refit.sketch.eq(sketch)].set_index("dimension")
            refit_support[sketch] = (rows.refit_signal_supported.astype(bool) & rows.refit_stability_supported.astype(bool) & rows.refit_heldout_supported.astype(bool)).to_dict()
        common = {d: bool(refit_support["A"].get(d, False) and refit_support["B"].get(d, False)) for d in range(1, 321)}
        prefix = leading_prefix(common, 320)
        first_failure = (len(prefix) + 1) if len(prefix) < 320 else None
        for dimension in range(1, 321):
            a = analytic[analytic.dimension.eq(dimension)]
            e = empirical[empirical.dimension.eq(dimension)]
            observed_support = bool(a.jointly_supported.astype(bool).all()) if len(a) else False
            empirical_support = bool(e.jointly_supported.astype(bool).all()) if len(e) else False
            ladder_rows.append({
                "sample_level": level,
                "dimension": dimension,
                "observed_support_both_sketches": observed_support,
                "empirical_null_support_both_sketches": empirical_support,
                "refit_null_A_support": bool(refit_support["A"].get(dimension, False)),
                "refit_null_B_support": bool(refit_support["B"].get(dimension, False)),
                "jointly_supported": common[dimension],
                "first_failing_dimension": first_failure,
                "lawful_contiguous_prefix_end": prefix[-1] if prefix else None,
                "old_reported_corrected_D": old["candidate_D_shared"],
                "repaired_candidate_D": new["candidate_D_shared"],
                "post_failure_reentry_used_by_old_D": bool(old["candidate_D_shared"] is not None and old["candidate_D_shared"] not in prefix),
            })
    pd.DataFrame(ladder_rows).to_csv(staging / "LADDER_SUPPORT_RECONCILIATION.csv", index=False, lineterminator="\n")

    level_refit = {}
    for level, directory in ((1, "shared_refit_empirical_null_level1_v2"), (2, "shared_refit_empirical_null_level2_v1"), (3, "shared_refit_empirical_null_level3_v1")):
        audit = json.loads((root / directory / "SHARED_REFIT_EMPIRICAL_NULL_VALIDATION.json").read_text())
        level_refit[str(level)] = {key: audit[key] for key in ("cells", "donors", "operators", "strata", "cells_per_stratum_cap", "singleton_strata", "n_lt_4_strata", "validation_rank", "validation_rank_authority")}
    scale_audit = {
        "schema": "full104-refit-null-scale-and-geometry-audit-v1",
        "status": "STOP_PROSPECTIVE_METHOD_AMENDMENT_REQUIRED",
        "completed_levels": level_refit,
        "full104_exact_if_current_cap4_rule_were_run": {"population_cells": 4553407, "selected_cells": 5485, "donor_operator_strata": 1400, "singleton_strata": 19, "n_lt_4_strata": 57, "maximum_stratum_cells": 42209},
        "sampling_rule": "deterministically hash-rank rows within donor×operator and retain min(4,n)",
        "weighting_rule": "selected cells are averaged within donor, with equal donor weighting; cap4 changes natural within-donor operator/cell composition by capping abundant strata and relatively upweighting sparse strata",
        "coordinate_space": "project selected A/B views through the observed-data full-level top-32 basis, then refit observed and null generalized eigensystems only inside that coordinate space",
        "frozen_authority_status": "cap4 and observed-top32 projection are not explicitly authorized by the prospective freeze, amendment, or promotion harness",
        "independent_validator_scope": "reuses the production subset/maps and observed top-32 coordinates; confirms reproducibility, not adequacy of the approximation",
        "additional_convergence_validation_required": True,
        "required_prospective_resolution": "before inspecting a revised answer, freeze a sensitivity/amendment comparing natural within-donor weighting and a full tested-feature-space refit (or demonstrate hash-bound equivalence) using existing feature matrices/sufficient outputs",
        "expression_reopen_required": False,
    }
    write_json(staging / "REFIT_NULL_SCALE_AND_GEOMETRY_AUDIT.json", scale_audit)

    harness_source = root / "_staging_shared_d_p0_repair_v1/harness_v2/SHARED_D_HARNESS_V2_TEST_REPORT.json"
    harness_report = json.loads(harness_source.read_text())
    harness_report["publication_note"] = "mechanical selector harness only; it does not qualify cap4/top32 refit-null geometry"
    write_json(staging / "SHARED_D_HARNESS_V2_TEST_REPORT.json", harness_report)

    def node(state, dependencies, hashes=None, tainted=False, reason=None):
        return {"state": state, "depends_on": dependencies, "artifact_hashes": hashes or {}, "tainted": tainted, "reason": reason}

    nodes = {
        "phase2_frozen_authority": node("FROZEN", [], {"freeze": sha(root / "preexpression_freeze/PHASE2_DERIVATION_FREEZE.json"), "amendment": sha(root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json")}),
        "full104_expression": node("FROZEN", ["phase2_frozen_authority"], {"manifest": sha(root / "expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv")}),
        "full104_feature_matrix": node("FROZEN", ["full104_expression"], {"manifest": sha(root / "feature_matrix_level4/PHASE2_FEATURE_MATRIX_MANIFEST.csv")}),
        "level1_refit_selection_prepatch": node("INVALIDATED", ["phase2_frozen_authority"], tainted=True, reason="post-failure re-entry; old D22"),
        "level2_refit_selection_prepatch": node("INVALIDATED", ["level1_refit_selection_prepatch"], tainted=True, reason="post-failure re-entry; old D6"),
        "level3_refit_selection_prepatch": node("INVALIDATED", ["level2_refit_selection_prepatch"], tainted=True, reason="post-failure re-entry; old D13"),
        "level1_contiguous_selection": node("EXPLORATORY", ["phase2_frozen_authority"], {"manifest": sha(root / "shared_selection_contiguous_level1_v1/SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv")}, tainted=True, reason="mechanically repaired D1; selecting refit-null method requires prospective adjudication"),
        "level2_contiguous_selection": node("EXPLORATORY", ["level1_contiguous_selection"], {"manifest": sha(root / "shared_selection_contiguous_level2_v1/SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv")}, tainted=True, reason="mechanically repaired null candidate; selecting refit-null method requires prospective adjudication"),
        "level3_contiguous_selection": node("EXPLORATORY", ["level2_contiguous_selection"], {"manifest": sha(root / "shared_selection_contiguous_level3_v1/SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv")}, tainted=True, reason="mechanically repaired D1; selecting refit-null method requires prospective adjudication"),
        "full104_analytic": node("QUALIFIED", ["full104_feature_matrix"], {"manifest": sha(root / "shared_analytic_level4_v1/SHARED_LEVEL4_ANALYTIC_DIAGNOSTIC_MANIFEST.csv")}, reason="diagnostic only; empirical selecting null pending"),
        "full104_empirical_null": node("EXPLORATORY", ["full104_analytic"], reason="allowed to finish unchanged; not selecting without valid refit geometry"),
        "full104_refit_null": node("EXPLORATORY", ["full104_empirical_null"], tainted=True, reason="cap4/top32 P0 method question unresolved"),
        "full104_corrected_selection": node("EXPLORATORY", ["full104_refit_null"], tainted=True, reason="not calculated under an authorized selecting refit-null"),
        "full104_independent_validation": node("EXPLORATORY", ["full104_corrected_selection"], tainted=True),
        "terminal_ladder_adjudication": node("EXPLORATORY", ["full104_independent_validation"], tainted=True),
        "shared_state_final": node("EXPLORATORY", ["terminal_ladder_adjudication"], tainted=True, reason="must be current hash-bound FROZEN before downstream use"),
        "private_state": node("EXPLORATORY", ["shared_state_final"], tainted=True, reason="blocked; consumer must assert shared_state_final is FROZEN and untainted"),
    }
    dag = {
        "schema": "full104-real-promotion-dependency-dag-v1",
        "status": "PASS_RECURSIVE_TAINT_DEMONSTRATED__DOWNSTREAM_BLOCKED",
        "nodes": nodes,
        "recursive_taint_demonstration": {"invalidated_root": "level1_refit_selection_prepatch", "transitively_tainted": ["level2_refit_selection_prepatch", "level3_refit_selection_prepatch"], "private_state_consumable": False},
        "consumption_rule": "only state=FROZEN and tainted=false may be consumed; all other machine-readable states fail closed",
        "stale_bypass_repairs": ["three obsolete scripts now raise SUPERSEDED_DO_NOT_USE", "active refit ladder adjudicator requires current selector/validator code hashes and PASS harness-v2"],
    }
    write_json(staging / "REAL_PROMOTION_DEPENDENCY_DAG.json", dag)

    council = """# FULL104 shared-D P0 multi-agent adjudication

Terminal verdict: **DO NOT PROMOTE; PROCEED WITH A PROSPECTIVE REFIT-NULL METHOD AMENDMENT ONLY.**

## Historian
PASS on authority reconciliation. The active chain is analytic → empirical null → refitted null → repaired selector → independent validator → refit ladder adjudicator → promotion harness. The pre-refit adjudicator/freezer and Level-2-only registry writer are `SUPERSEDED_DO_NOT_USE` and now fail closed.

## Dataset-Fidelity
PASS. Upstream hashes and the 4,553,407-cell / 104-donor / 42-operator firewall remain unchanged. No expression or protected data was reopened by this repair.

## Objective/Gradient
PASS on the selector repair. Eligibility now ends at the first jointly unsupported dimension, and one-SE is applied only inside the lawful leading prefix. The coarse multiples-of-8 grid is a bracket; the frozen amendment authorizes integer local refinement.

## Teacher Mechanics
PASS on mechanics only. The descriptive Level-4 “5” is literal D=5, not grid index 5; it remains non-promotable because the selecting null/refit and terminal ladder gates are incomplete.

## Interface/Student Mechanics
CONCERN resolved mechanically: stale adjudicator/freezer routes fail closed, and the active ladder adjudicator now requires current selector/validator hashes plus harness-v2. `private_state` remains explicitly non-consumable.

## Representation Geometry
STOP on old results. Level 1 D22, Level 2 D6, and Level 3 D13 all used post-failure re-entry. Under the repaired rule the cheap recomputations are D1, null, and D1 respectively; none is promoted.

## Statistics/Leakage
STOP. The refit-null uses 5,485 of 4,553,407 cells via cap4 per donor×operator and refits inside an observed top-32 projection. Neither approximation is prospectively authorized; the independent validator reproduces rather than challenges them. A prospective natural-weight/full-feature-space sensitivity is required.

## Biology/Rare
CONCERN. No biology, rare, program, native-cell, or pathology label selects D, which is correct. Therefore shared cross-view stability alone is not a biological qualification; existing operator/source shortcut diagnostics must remain part of later interpretation.

## Red-Team
STOP promotion. The prefix re-entry exploit is closed and stale scripts fail closed, but a tiny operator-reweighted subset and observed-data-derived projection can still determine D. The repair is falsified unless the prospectively frozen sensitivity supports like-for-like geometry under natural donor-primary weighting.

## Preserved dissent and decision
The mechanics reviewers PASS the contiguous selector. Statistics and Red-Team STOP scientific promotion because the selecting refit-null approximation is not authorized or independently challenged. STOP controls. FULL104 empirical-null computation may finish unchanged as diagnostic evidence; no refit-null selection, shared freeze, or downstream Phase-2 stage may start.
"""
    (staging / "MULTIAGENT_P0_ADJUDICATION.md").write_text(council, encoding="utf-8")

    required = [
        "ACTIVE_SHARED_D_CODE_AUTHORITY.json", "CONTIGUOUS_PREFIX_RULE_AUDIT.json",
        "LADDER_SUPPORT_RECONCILIATION.csv", "REFIT_NULL_SCALE_AND_GEOMETRY_AUDIT.json",
        "SHARED_D_HARNESS_V2_TEST_REPORT.json", "REAL_PROMOTION_DEPENDENCY_DAG.json",
        "MULTIAGENT_P0_ADJUDICATION.md",
    ]
    records = [{"path": name, "bytes": (staging / name).stat().st_size, "sha256": sha(staging / name)} for name in required]
    records.extend({"path": str(path.relative_to(Path.cwd())), "bytes": path.stat().st_size, "sha256": sha(path)} for path in [scripts / name for name in [*roles.values(), *superseded.keys(), "test_shared_d_selector_harness_v2.py"]])
    manifest = staging / "P0_REPAIR_HASH_MANIFEST.csv"
    pd.DataFrame(records).to_csv(manifest, index=False, lineterminator="\n")
    root_hash = sha(manifest)
    (staging / "P0_REPAIR_ROOT_SHA256.txt").write_text(root_hash + "\n", encoding="ascii")
    package_status = {
        "status": "PASS_P0_MECHANICAL_REPAIR__STOP_SCIENTIFIC_PROMOTION",
        "manifest_sha256": root_hash,
        "previous_D_changed": {"level1": {"old": 22, "repaired": 1}, "level2": {"old": 6, "repaired": None}, "level3": {"old": 13, "repaired": 1}},
        "cap4_top32": "PROSPECTIVE_AMENDMENT_REQUIRED",
        "full104_D_selection_authorized": False,
        "next_authorized_stage": "freeze a prospective natural-weight/full-feature-space refit-null convergence amendment; then run only that sensitivity using existing FULL104 matrix/sufficient outputs",
    }
    write_json(staging / "P0_REPAIR_STATUS.json", package_status)
    # Status was written after the content manifest by design; anchor it too.
    anchor = {"content_manifest_sha256": root_hash, "status_sha256": sha(staging / "P0_REPAIR_STATUS.json")}
    write_json(staging / "P0_REPAIR_EXTERNAL_ANCHOR.json", anchor)
    os.replace(staging, publish)
    print(json.dumps({**package_status, "published": str(publish)}, indent=2))


if __name__ == "__main__":
    main()
