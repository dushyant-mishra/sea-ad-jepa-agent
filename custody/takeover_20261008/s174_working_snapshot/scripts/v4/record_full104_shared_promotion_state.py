#!/usr/bin/env python3
"""Write a hash-bound machine-readable promotion snapshot for one shared level."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from jepa_scientific_promotion_harness_v1 import promote, save_registry, sha256


def main() -> None:
    raise RuntimeError("SUPERSEDED_DO_NOT_USE: Level-2-only snapshot cannot represent the active Level1->FULL104 taint DAG")
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--analytic", required=True)
    parser.add_argument("--refit-null", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--independent", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    paths = {name: Path(getattr(args, name)).resolve() for name in ("harness", "tests", "analytic", "refit_null", "selection", "independent", "out")}
    paths["out"].mkdir(parents=True, exist_ok=False)
    registry = json.loads((paths["harness"] / "SCIENTIFIC_PROMOTION_REGISTRY.json").read_text())["artifacts"]
    level = int(json.loads((paths["selection"] / "SHARED_DIMENSION_SELECTION_LEVEL_REFIT_CORRECTED.json").read_text())["sample_level"])
    if level != 2:
        raise RuntimeError("initial promotion snapshot is defined for Level 2")
    test_result = json.loads((paths["tests"] / "SHARED_PROMOTION_HARNESS_EXECUTABLE_TESTS.json").read_text())
    independent = json.loads((paths["independent"] / "INDEPENDENT_SHARED_VALIDATION.json").read_text())
    if test_result["status"] != "PASS_PROMOTION_HARNESS_EXECUTABLE_TESTS" or independent["status"] != "PASS_INDEPENDENT_SHARED_VALIDATOR":
        raise RuntimeError("executable promotion validators unavailable")
    promote(registry, "harness_executable_tests", "QUALIFIED", {"golden_and_metamorphic": True, "independent_fixture": True, "taint_propagation": True})
    promote(registry, "level2_shared_statistics", "PROVISIONAL", {})
    promote(registry, "level2_shared_statistics", "QUALIFIED", {"independent_real_calculation": True, "observed_null_symmetry": True, "hash_agreement": True})
    promote(registry, "level2_shared_selection", "PROVISIONAL", {})
    registry["level2_shared_statistics"]["artifact_hashes"] = {
        "analytic": sha256(paths["analytic"] / "SHARED_LEVEL2_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"),
        "refit_null": sha256(paths["refit_null"] / "SHARED_REFIT_EMPIRICAL_NULL_MANIFEST.csv"),
        "independent": sha256(paths["independent"] / "INDEPENDENT_SHARED_VALIDATION_MANIFEST.csv"),
    }
    registry["level2_shared_selection"]["artifact_hashes"] = {"selection": sha256(paths["selection"] / "SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv")}
    registry_path = paths["out"] / "SCIENTIFIC_PROMOTION_REGISTRY_LEVEL2.json"
    save_registry(registry_path, registry)
    table_path = paths["out"] / "SCIENTIFIC_PROMOTION_STATES_LEVEL2.csv"
    pd.DataFrame([{"artifact": node, "state": record["state"], "tainted": record.get("tainted", False), "depends_on": "|".join(record.get("depends_on", []))} for node, record in registry.items()]).to_csv(table_path, index=False, lineterminator="\n")
    manifest = paths["out"] / "SCIENTIFIC_PROMOTION_STATE_LEVEL2_MANIFEST.csv"
    files = [registry_path, table_path, Path(__file__)]
    pd.DataFrame([{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (paths["out"] / "SCIENTIFIC_PROMOTION_STATE_LEVEL2_ROOT_SHA256.txt").write_text(sha256(manifest) + "\n", encoding="ascii")
    print(json.dumps({"status": "PASS_LEVEL2_STATISTICS_QUALIFIED_SELECTION_PROVISIONAL", "manifest_sha256": sha256(manifest)}, indent=2))


if __name__ == "__main__":
    main()
