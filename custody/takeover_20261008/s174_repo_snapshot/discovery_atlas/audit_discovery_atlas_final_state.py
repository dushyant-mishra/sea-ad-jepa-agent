from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REQUIRED_FILES = [
    "results/tables/discovery_final_candidate_shortlist_v3.csv",
    "results/reports/discovery_final_candidate_shortlist_v3.md",
    "results/tables/discovery_targeted_manifold_audit_v1.csv",
    "results/tables/discovery_tier1_pending_manifold_audit_v1.csv",
    "results/tables/discovery_baseline_predictive_representation_comparison.csv",
    "results/tables/discovery_baseline_discovery_ranking_comparison.csv",
    "results/reports/discovery_baseline_comparison_gate.md",
    "results/reports/open_validation_framework_plan_v1.md",
    "discovery_atlas/discovery_logic.py",
    "tests/test_discovery_atlas_logic.py",
]

DISTANCE_COLUMNS = [
    "mean_nearest_real_cell_distance",
    "p95_nearest_real_cell_distance",
    "baseline_nn_p95_threshold",
    "manifold_violation_fraction",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the final Discovery Atlas technical state."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/tables/discovery_atlas_final_state_audit.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("results/reports/discovery_atlas_final_state_audit.md"),
    )
    return parser.parse_args()


class Audit:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def add(
        self,
        name: str,
        passed: bool,
        observed: object,
        expected: object,
        notes: str = "",
        warning: bool = False,
    ) -> None:
        self.rows.append(
            {
                "check_name": name,
                "status": "pass" if passed else ("warning" if warning else "fail"),
                "observed": str(observed),
                "expected": str(expected),
                "notes": notes,
            }
        )


def run_logic_tests() -> tuple[bool, str]:
    if importlib.util.find_spec("pytest") is not None:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_discovery_atlas_logic.py", "-q"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, "pytest_passed" if result.returncode == 0 else result.stderr[-500:]

    path = Path("tests/test_discovery_atlas_logic.py")
    spec = importlib.util.spec_from_file_location("test_discovery_atlas_logic", path)
    if spec is None or spec.loader is None:
        return False, "could_not_load_test_module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tests = [
        getattr(module, name)
        for name in dir(module)
        if name.startswith("test_") and callable(getattr(module, name))
    ]
    try:
        for test in tests:
            test()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, f"direct_assertion_tests_passed ({len(tests)} tests)"


def main() -> None:
    args = parse_args()
    audit = Audit()

    for filename in REQUIRED_FILES:
        exists = Path(filename).exists()
        audit.add(f"required_file::{filename}", exists, exists, True)
    if any(row["status"] == "fail" for row in audit.rows):
        frame = pd.DataFrame(audit.rows)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.out, index=False)
        raise SystemExit("Required files are missing")

    shortlist = pd.read_csv(REQUIRED_FILES[0])
    original = pd.read_csv(REQUIRED_FILES[2])
    pending = pd.read_csv(REQUIRED_FILES[3])
    predictive = pd.read_csv(REQUIRED_FILES[4])
    ranking = pd.read_csv(REQUIRED_FILES[5])
    baseline_report = Path(REQUIRED_FILES[6]).read_text(encoding="utf-8")
    open_plan = Path(REQUIRED_FILES[7]).read_text(encoding="utf-8")

    tier1 = shortlist[
        shortlist["final_tier"].eq("scorecard_supported_isolated_hypothesis")
    ]
    broad = shortlist[shortlist["final_tier"].eq("broad_state_caution")]
    audit.add("shortlist_gene_unique", shortlist["gene"].is_unique, shortlist["gene"].nunique(), len(shortlist))
    audit.add("shortlist_retained_count", len(shortlist) == 149, len(shortlist), 149)
    audit.add("shortlist_tier1_count", len(tier1) == 41, len(tier1), 41)
    audit.add(
        "tier1_manifold_safe",
        tier1["manifold_qc_status"].eq("manifold_safe").all(),
        int(tier1["manifold_qc_status"].eq("manifold_safe").sum()),
        41,
    )
    audit.add(
        "tier1_final_status",
        tier1["final_candidate_status_v3"]
        .eq("promoted_model_hypothesis_manifold_qc_pass")
        .all(),
        tier1["final_candidate_status_v3"].value_counts().to_dict(),
        "all promoted_model_hypothesis_manifold_qc_pass",
    )
    broad_promoted = broad["final_candidate_status_v3"].astype(str).str.startswith("promoted")
    audit.add("broad_state_not_promoted", not broad_promoted.any(), int(broad_promoted.sum()), 0)
    positive_graph = (
        shortlist["graph_neighborhood_label"].eq("coherent_cleaner_neighborhood")
        | shortlist["graph_interpretation"].astype(str).str.contains(
            "positive_support", case=False, na=False
        )
    )
    audit.add(
        "graph_not_positive_support",
        not positive_graph.any(),
        int(positive_graph.sum()),
        0,
        "Graph evidence must remain penalty/context only.",
    )

    audit.add("original_audit_rows", len(original) == 45, len(original), 45)
    audit.add("pending_audit_rows", len(pending) == 19, len(pending), 19)
    overlap = set(original["gene"]) & set(pending["gene"])
    audit.add("audit_gene_sets_disjoint", not overlap, sorted(overlap), [])
    combined_tier1 = (set(original["gene"]) | set(pending["gene"])) & set(tier1["gene"])
    audit.add("combined_audits_cover_tier1", len(combined_tier1) == 41, len(combined_tier1), 41)
    for label, frame in [("original", original), ("pending", pending)]:
        missing = [column for column in DISTANCE_COLUMNS if column not in frame.columns]
        audit.add(f"{label}_distance_columns", not missing, missing, [])
        if not missing:
            audit.add(
                f"{label}_distance_non_null",
                frame[DISTANCE_COLUMNS].notna().all().all(),
                frame[DISTANCE_COLUMNS].isna().sum().to_dict(),
                "all zero null counts",
            )
            audit.add(
                f"{label}_positive_distances",
                frame["baseline_nn_p95_threshold"].gt(0).all()
                and frame["mean_nearest_real_cell_distance"].gt(0).all()
                and frame["p95_nearest_real_cell_distance"].gt(0).all(),
                {
                    "baseline_min": frame["baseline_nn_p95_threshold"].min(),
                    "mean_nn_min": frame["mean_nearest_real_cell_distance"].min(),
                    "p95_nn_min": frame["p95_nearest_real_cell_distance"].min(),
                },
                "all positive",
            )
        backend_column = next(
            (
                column
                for column in ["manifold_nn_backend", "manifold_neighbor_backend"]
                if column in frame.columns
            ),
            None,
        )
        audit.add(
            f"{label}_torch_backend",
            backend_column is not None and frame[backend_column].eq("torch").all(),
            (
                frame[backend_column].value_counts().to_dict()
                if backend_column is not None
                else "missing"
            ),
            "torch",
        )

    tested = predictive[predictive["status"].eq("tested")]
    required_representations = {
        "graph_jepa_real_graph_latent",
        "pca_expression_baseline",
        "module_mean_baseline",
        "raw_expression_regularized_baseline",
    }
    audit.add(
        "baseline_tested_representations",
        required_representations.issubset(set(tested["representation"])),
        sorted(set(tested["representation"])),
        sorted(required_representations),
    )
    unavailable = predictive[
        predictive["status"].eq("not_available_existing_artifact")
    ]
    required_unavailable = {
        "shuffled_graph_jepa",
        "no_graph_jepa",
        "expression_only_autoencoder",
    }
    audit.add(
        "baseline_unavailable_artifact_rows",
        required_unavailable.issubset(set(unavailable["representation"])),
        sorted(set(unavailable["representation"])),
        sorted(required_unavailable),
    )
    mean_spearman = (
        tested.groupby("representation")["oof_spearman"].mean().sort_values(ascending=False)
    )
    module_led = (
        not mean_spearman.empty and mean_spearman.index[0] == "module_mean_baseline"
    )
    expected_phrase = "superiority over simpler baselines was not established"
    audit.add(
        "baseline_report_conclusion",
        (not module_led) or expected_phrase in baseline_report,
        expected_phrase in baseline_report,
        True if module_led else "not required",
    )
    audit.add("ranking_table_nonempty", len(ranking) > 0, len(ranking), ">0")

    tests_passed, test_note = run_logic_tests()
    audit.add("discovery_logic_tests", tests_passed, test_note, "tests pass")

    lower_plan = open_plan.lower()
    plan_checks = {
        "open_validation_plan_only": "this is a plan only" in lower_plan,
        "open_validation_controlled_statuses": "not_available_public_artifact" in lower_plan
        and "not_testable" in lower_plan,
        "open_validation_no_forced_candidates": all(
            token in lower_plan for token in ["app", "apoe", "tlr2", "top-ranked"]
        ),
        "open_validation_no_spatial_fabrication": "should not fabricate spatial" in lower_plan
        and "plaque-proximity" in lower_plan,
    }
    for name, passed in plan_checks.items():
        audit.add(name, passed, passed, True)

    frame = pd.DataFrame(audit.rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)

    counts = frame["status"].value_counts()
    non_pass = frame[~frame["status"].eq("pass")]
    lines = [
        "# Discovery Atlas Final-State Audit",
        "",
        "## Status",
        "",
        *[f"- `{status}`: {count}" for status, count in counts.items()],
        "",
        "## Mean out-of-fold Spearman by representation",
        "",
        *[f"- `{name}`: {value:.6f}" for name, value in mean_spearman.items()],
        "",
        "## Non-pass checks",
        "",
    ]
    if non_pass.empty:
        lines.append("_None._")
    else:
        lines.extend(
            [
                "| check_name | status | observed | expected | notes |",
                "| --- | --- | --- | --- | --- |",
                *[
                    "| "
                    + " | ".join(
                        str(value).replace("|", "/")
                        for value in row
                    )
                    + " |"
                    for row in non_pass[
                        ["check_name", "status", "observed", "expected", "notes"]
                    ].itertuples(index=False, name=None)
                ],
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit checks artifact consistency and reproducibility contracts. It does not add biological, causal, spatial, or experimental evidence.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(frame["status"].value_counts().to_string())
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    if frame["status"].eq("fail").any():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
