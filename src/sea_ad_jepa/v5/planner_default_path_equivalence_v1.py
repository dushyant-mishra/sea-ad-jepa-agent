"""Physical old-vs-new equivalence check for the FULL104 streaming planner.

Phase-IV binds ``full104_masking_streaming_executor_v1.py`` by SHA-256 because
its partner-selection functions decide *which addresses a masking policy would
swap in*. When those bytes change, the frozen Audit-B target sample no longer
means what it said, and the runtime preflight refuses to start.

This module answers the only question that can justify a versioned successor
binding: **does the new planner, called the way Audit-B calls it, compute the
identical numbers as the frozen planner?**

It does that by executing both implementations over the same authenticated
stream fixture and requiring *bitwise* equality of every emitted row. It is not
a code review and not a hash comparison; it is an execution comparison.

Scope and honesty
-----------------
* The frozen planner is recovered from an immutable in-repo copy of the exact
  bytes that were bound, and its SHA-256 is re-verified before it is imported.
* Equality is required to be exact (``==`` on float64), not approximate. A
  tolerance would let a real numerical change pass as "close enough".
* The fixtures are SYNTHETIC. They establish implementation equivalence, which
  is a statement about code, not about FULL104 biology. No FULL104 expression,
  pathology, sealed outcome, terminal masking result, D_shared or G5 quantity is
  read, and nothing here authorizes training or Audit-B execution.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import scipy.sparse as sp

SCHEMA = "V5_PLANNER_DEFAULT_PATH_EQUIVALENCE_V1"

#: SHA-256 of the planner source bound by AUDIT_B_FROZEN_TARGET_SAMPLE.json.
FROZEN_PLANNER_SHA256 = (
    "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
)

#: SHA-256 of the successor planner this check qualifies. Pinned on purpose: a
#: further planner edit must re-run this check rather than inherit its verdict.
SUCCESSOR_PLANNER_SHA256 = (
    "de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8"
)

REPO_ROOT = Path(__file__).resolve().parents[3]

FROZEN_PLANNER_COPY = REPO_ROOT / (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
    "frozen_planner_source__143645be.pysrc"
)

SUCCESSOR_PLANNER_PATH = REPO_ROOT / (
    "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
)


def sha256_file(path: str | Path) -> str:
    handle_path = Path(path)
    if not handle_path.is_file():
        raise ValueError(f"required file is missing: {handle_path}")
    digest = hashlib.sha256()
    with handle_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_planner(path: str | Path, *, expected_sha256: str, module_name: str) -> Any:
    """Import a planner implementation after proving its exact bytes.

    The module is registered under ``sea_ad_jepa.v5.*`` so that its relative
    imports (the shared qualification runner) resolve against the real package.
    """
    source = Path(path)
    actual = sha256_file(source)
    if actual != expected_sha256:
        raise ValueError(
            f"planner digest mismatch for {source}: "
            f"expected {expected_sha256}, observed {actual}"
        )
    qualified = f"sea_ad_jepa.v5.{module_name}"
    # An explicit SourceFileLoader is required: the preserved frozen copy
    # deliberately does not carry a .py extension so it can never be imported
    # or collected by accident.
    loader = importlib.machinery.SourceFileLoader(qualified, str(source))
    spec = importlib.util.spec_from_file_location(qualified, source, loader=loader)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load planner module from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(qualified, None)
        raise
    return module


# --------------------------------------------------------------------------- #
# Authenticated stream fixture
# --------------------------------------------------------------------------- #


def _sha_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build_stream_materials(
    root: str | Path,
    *,
    n_donors: int = 12,
    cells_per_donor: int = 4,
    n_addresses: int = 8,
    n_folds: int = 3,
    n_sources: int = 2,
    seed: int = 0,
) -> dict[str, Any]:
    """Materialize an authenticated Phase-2-shaped block manifest on disk.

    Counts are integral and donor-structured so that per-donor standardization,
    ridge screening and the prefix policies all exercise non-degenerate paths.
    The geometry is deliberately small: this proves implementation equality, and
    implementation equality does not depend on n.
    """
    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    donor_ids = [f"D{i:02d}" for i in range(n_donors)]
    source_by_donor = np.array(
        [chr(ord("A") + (i % n_sources)) for i in range(n_donors)], dtype=object
    )
    fold_by_donor = np.array([i % n_folds for i in range(n_donors)], dtype=np.int64)
    donor_code = np.repeat(np.arange(n_donors, dtype=np.int64), cells_per_donor)

    n_cells = n_donors * cells_per_donor
    raw = np.zeros((n_cells, n_addresses), dtype=np.int32)
    row = 0
    for donor in range(n_donors):
        donor_shift = rng.integers(1, 6)
        for cell in range(cells_per_donor):
            target0 = 1 + int((3 * cell + donor) % 7)
            target1 = 2 + int((5 * cell + 2 * donor + 1) % 9)
            values = [target0, target1]
            for col in range(2, n_addresses):
                values.append(
                    1
                    + int(
                        (col * target0 + (col + 1) * target1 + donor_shift * cell + donor)
                        % (7 + col)
                    )
                )
            raw[row] = np.asarray(values[:n_addresses], dtype=np.int32)
            row += 1

    libraries = raw.sum(axis=1).astype(np.int64)
    if not np.all(libraries > 0):
        raise ValueError("fixture produced an empty library; adjust the geometry")

    block_root = base / "blocks_root"
    block_root.mkdir(exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    selection_row = 0
    for donor, donor_id in enumerate(donor_ids):
        block_dir = block_root / f"op{donor:02d}"
        block_dir.mkdir(exist_ok=True)
        begin = donor * cells_per_donor
        end = begin + cells_per_donor
        matrix = sp.csr_matrix(raw[begin:end])
        counts_rel = Path(f"op{donor:02d}") / "block-00000.counts.npz"
        meta_rel = Path(f"op{donor:02d}") / "block-00000.meta.csv"
        counts_path = block_root / counts_rel
        meta_path = block_root / meta_rel
        sp.save_npz(counts_path, matrix, compressed=True)
        with meta_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(
                [
                    "selection_row",
                    "canonical_cell_id",
                    "donor_id",
                    "expression_row",
                    "primary_row_weight",
                    "source_library",
                ]
            )
            for local in range(cells_per_donor):
                index = begin + local
                writer.writerow(
                    [
                        selection_row,
                        f"cell-{selection_row:05d}",
                        donor_id,
                        index,
                        "1.0",
                        int(libraries[index]),
                    ]
                )
                selection_row += 1
        manifest_rows.append(
            {
                "block_key": f"op{donor:02d}/block-00000",
                "source": str(source_by_donor[donor]),
                "operator_index": donor,
                "matrix_id": f"M{donor:02d}",
                "rows": cells_per_donor,
                "nnz": int(matrix.nnz),
                "counts_path": counts_rel.as_posix(),
                "counts_sha256": _sha_path(counts_path),
                "meta_path": meta_rel.as_posix(),
                "meta_sha256": _sha_path(meta_path),
            }
        )

    manifest = base / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "block_key",
                "source",
                "operator_index",
                "matrix_id",
                "rows",
                "nnz",
                "counts_path",
                "counts_sha256",
                "meta_path",
                "meta_sha256",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    return {
        "manifest_path": manifest,
        "block_root": block_root,
        "expected_manifest_sha256": _sha_path(manifest),
        "donor_id_to_code": {donor_id: i for i, donor_id in enumerate(donor_ids)},
        "source_by_donor": source_by_donor,
        "fold_by_donor": fold_by_donor,
        "universe_cols": np.arange(n_addresses, dtype=np.int64),
        "target_cols": np.array([0, 1], dtype=np.int64),
        "target_ids": np.array(["q0", "q1"], dtype=object),
        "expected_cell_count": int(n_cells),
        "verify_block_hashes": True,
        "_donor_code": donor_code,
        "_folds": sorted({int(f) for f in fold_by_donor}),
    }


def _stream_for(module: Any, materials: Mapping[str, Any]) -> Any:
    kwargs = {k: v for k, v in materials.items() if not k.startswith("_")}
    return module.Full104ManifestStreamV1(**kwargs)


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #


def _normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (np.floating, float)):
            # repr of a float64 round-trips exactly; this makes the comparison
            # bitwise rather than tolerance-based.
            out[key] = ("float", float(value).hex())
        elif isinstance(value, (np.integer,)):
            out[key] = ("int", int(value))
        elif isinstance(value, (list, tuple, np.ndarray)):
            out[key] = ("seq", tuple(int(x) for x in value))
        elif isinstance(value, (set, frozenset)):
            out[key] = ("set", tuple(sorted(int(x) for x in value)))
        else:
            out[key] = ("raw", value)
    return out


def _diff_rows(
    frozen_rows: Iterable[Mapping[str, Any]],
    successor_rows: Iterable[Mapping[str, Any]],
) -> list[str]:
    left = [_normalize_row(r) for r in frozen_rows]
    right = [_normalize_row(r) for r in successor_rows]
    problems: list[str] = []
    if len(left) != len(right):
        problems.append(f"row count differs: frozen={len(left)} successor={len(right)}")
        return problems
    for index, (a, b) in enumerate(zip(left, right)):
        if set(a) != set(b):
            problems.append(
                f"row {index}: key set differs; "
                f"frozen_only={sorted(set(a) - set(b))} "
                f"successor_only={sorted(set(b) - set(a))}"
            )
            continue
        for key in sorted(a):
            if a[key] != b[key]:
                problems.append(
                    f"row {index} field {key!r}: frozen={a[key]!r} successor={b[key]!r}"
                )
    return problems


def compare_default_path(
    *,
    frozen: Any,
    successor: Any,
    materials: Mapping[str, Any],
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> dict[str, Any]:
    """Run both planners with Audit-B's default arguments and diff every row."""
    frozen_all = frozen.run_all_primary_folds_streaming(
        stream=_stream_for(frozen, materials),
        parameters=parameters,
        evidence_budget=evidence_budget,
        global_seed=int(global_seed),
    )
    successor_all = successor.run_all_primary_folds_streaming(
        stream=_stream_for(successor, materials),
        parameters=parameters,
        evidence_budget=evidence_budget,
        global_seed=int(global_seed),
    )
    problems = list(_diff_rows(frozen_all, successor_all))

    per_fold: dict[str, int] = {}
    for fold in materials["_folds"]:
        frozen_fold = frozen.run_primary_fold_streaming(
            stream=_stream_for(frozen, materials),
            fold_index=int(fold),
            parameters=parameters,
            evidence_budget=evidence_budget,
            global_seed=int(global_seed),
        )
        successor_fold = successor.run_primary_fold_streaming(
            stream=_stream_for(successor, materials),
            fold_index=int(fold),
            parameters=parameters,
            evidence_budget=evidence_budget,
            global_seed=int(global_seed),
        )
        per_fold[str(fold)] = len(frozen_fold)
        problems.extend(
            f"fold {fold}: {p}" for p in _diff_rows(frozen_fold, successor_fold)
        )

    # The Audit-B N1 planner imports _ridge_partners directly, so compare it as
    # its own entrypoint rather than only through the fold runner.
    partner_problems: list[str] = []
    frozen_stream = _stream_for(frozen, materials)
    successor_stream = _stream_for(successor, materials)
    frozen_stream.validate_layout()
    successor_stream.validate_layout()
    fold_by_donor = np.asarray(materials["fold_by_donor"])
    partner_calls = 0
    for fold in materials["_folds"]:
        train = np.flatnonzero(fold_by_donor != int(fold)).astype(np.int64)
        for target_col in map(int, materials["target_cols"]):
            a = frozen._ridge_partners(
                frozen_stream,
                train_donors=train,
                target_col=target_col,
                candidate_pool_count=int(parameters.ridge_candidate_pool_count),
                cap=int(parameters.targeted_partner_cap),
                alpha=float(parameters.ridge_alpha),
            )
            b = successor._ridge_partners(
                successor_stream,
                train_donors=train,
                target_col=target_col,
                candidate_pool_count=int(parameters.ridge_candidate_pool_count),
                cap=int(parameters.targeted_partner_cap),
                alpha=float(parameters.ridge_alpha),
            )
            partner_calls += 1
            if tuple(map(int, a)) != tuple(map(int, b)):
                partner_problems.append(
                    f"_ridge_partners fold={fold} target={target_col}: "
                    f"frozen={tuple(map(int, a))} successor={tuple(map(int, b))}"
                )
    problems.extend(partner_problems)

    return {
        "rows_compared": len(frozen_all),
        "folds_compared": per_fold,
        "ridge_partner_calls_compared": partner_calls,
        "equivalent": not problems,
        "problems": problems[:50],
    }


def default_parameters_and_budget() -> tuple[Any, Any]:
    from .masking_qualification_parameters_authority_v1 import (
        MaskingQualificationParametersAuthorityV1,
    )
    from .target_evidence_budget_authority_v1 import TargetEvidenceBudgetAuthorityV1

    parameters = MaskingQualificationParametersAuthorityV1(
        authority_id="V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_score_id=(
            "SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1"
        ),
        targeted_partner_cap=2,
        ridge_candidate_pool_count=5,
        ridge_score_feature_count=3,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=5,
        prefix_floor_numerator=0,
        prefix_floor_denominator=1,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
    )
    budget = TargetEvidenceBudgetAuthorityV1(
        authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        support_estimability_authority_sha256=hashlib.sha256(b"support").hexdigest(),
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=2,
        min_retained_non_target_rna_count=1,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    return parameters, budget


#: Fixture geometries the receipt must cover. More than one so that a single
#: lucky configuration cannot carry the verdict.
DEFAULT_GEOMETRIES: tuple[dict[str, int], ...] = (
    {"n_donors": 12, "cells_per_donor": 4, "n_addresses": 8, "n_folds": 3, "n_sources": 2, "seed": 0},
    {"n_donors": 16, "cells_per_donor": 6, "n_addresses": 11, "n_folds": 4, "n_sources": 3, "seed": 7},
    {"n_donors": 20, "cells_per_donor": 3, "n_addresses": 9, "n_folds": 4, "n_sources": 2, "seed": 19},
)


def run_equivalence(
    workdir: str | Path,
    *,
    geometries: Iterable[Mapping[str, int]] = DEFAULT_GEOMETRIES,
    global_seed: int = 20260926,
) -> dict[str, Any]:
    frozen = load_planner(
        FROZEN_PLANNER_COPY,
        expected_sha256=FROZEN_PLANNER_SHA256,
        module_name="_frozen_planner_143645be",
    )
    successor = load_planner(
        SUCCESSOR_PLANNER_PATH,
        expected_sha256=SUCCESSOR_PLANNER_SHA256,
        module_name="_successor_planner_de2f019e",
    )
    parameters, budget = default_parameters_and_budget()

    cases: list[dict[str, Any]] = []
    root = Path(workdir)
    for index, geometry in enumerate(geometries):
        materials = build_stream_materials(root / f"case{index:02d}", **dict(geometry))
        outcome = compare_default_path(
            frozen=frozen,
            successor=successor,
            materials=materials,
            parameters=parameters,
            evidence_budget=budget,
            global_seed=global_seed,
        )
        cases.append({"geometry": dict(geometry), **outcome})

    return {
        "schema": SCHEMA,
        "frozen_planner_sha256": FROZEN_PLANNER_SHA256,
        "successor_planner_sha256": SUCCESSOR_PLANNER_SHA256,
        "frozen_planner_recovered_from": str(
            FROZEN_PLANNER_COPY.relative_to(REPO_ROOT).as_posix()
        ),
        "comparison": "BITWISE_EQUALITY_OF_EVERY_EMITTED_ROW__NO_TOLERANCE",
        "call_convention": "AUDIT_B_DEFAULT__NO_G3_FIT_OBJECTIVE_SUPPLIED",
        "evidence_class": "SYNTHETIC_FIXTURE__IMPLEMENTATION_EQUIVALENCE_ONLY",
        "full104_expression_read": False,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
        "cases": cases,
        "equivalent": all(case["equivalent"] for case in cases),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="receipt JSON path")
    parser.add_argument("--workdir", default=None, help="fixture directory (temp if unset)")
    args = parser.parse_args(argv)

    if args.workdir:
        report = run_equivalence(args.workdir)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_equivalence(tmp)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not report["equivalent"]:
        print("PLANNER DEFAULT PATH IS NOT EQUIVALENT", file=sys.stderr)
        for case in report["cases"]:
            for problem in case["problems"]:
                print(f"  {problem}", file=sys.stderr)
        return 1
    total = sum(case["rows_compared"] for case in report["cases"])
    print(
        "PLANNER DEFAULT PATH EQUIVALENT: "
        f"{len(report['cases'])} geometries, {total} rows, bitwise"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
