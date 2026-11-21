#!/usr/bin/env python3
"""Read-only, pinned-source audit of the V74/V77 -> PS Task3 interface.

Only reads listed Python source files and a public-facing QC authority manifest.
Does not import the inspected modules, open compressed QC payloads, generate
synthetic RNA, fit a model, score biology or grant source/STOP authority.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "qc": ("scripts/v64/v73_full104_qc_calibration.py", "497c787d82d93adf62f8c34a79a62b209e20f11f"),
    "observer": ("scripts/v64/build_v73_full104_sharded_observer.py", "ce4407dbe4489e37fe3936a2d634b133ead43ac3"),
    "population": ("scripts/v64/v73_full104_population_geometry.py", "979ef1888be70aa2e72c0401bb317257031a1cb4"),
    "real_train": ("scripts/v77/build_v77_real_calibration.py", "fc0aa759530ec0559cbf425850441c245f600e2d"),
    "extended": ("scripts/v77/build_v77_extended_rna_observer.py", "121413bf3b03275231d931f965e5cb86746919df"),
    "task3": ("scripts/production_synthetic/calibration_v1.py", "8d7299268631fa33414c900ae8d4fd96f20cdf65"),
    "qc_manifest": ("results/v64/V74_FULL104_RNA_QC_CALIBRATION_AUTHORITY_50K_V2.json", "40394fc9b4e12f4376746d0b15931d2d28c93fce"),
}
PARAMETERS = (
    "OBS_DEPTH_SCALE", "OBS_DETECTION_SCALE", "OBS_SUPPORT_RATE",
    "OBS_MISSINGNESS_RATE", "OBS_DONOR_OPERATOR_ALLOCATION",
    "OBS_FRAGMENT_MULTIPLICITY", "OBS_MODALITY_AVAILABILITY",
)
NA = "NOT_BOUND_TO_TASK3_REGISTRY__NO_AUTHORITY"


class AuditRefusal(ValueError):
    """Pinned source changed or the static proof no longer applies."""


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_pinned(root: Path = ROOT) -> dict[str, str]:
    source = {}
    for key, (path, expected_blob) in FILES.items():
        raw = (root / path).read_bytes()
        if git_blob_sha1(raw) != expected_blob:
            raise AuditRefusal(f"{key}: Git blob changed; new scoped review required")
        source[key] = raw.decode("utf-8")
    return source


def tree(source: str) -> ast.Module:
    return ast.parse(source)


def function_node(source: str, name: str) -> ast.FunctionDef:
    for item in tree(source).body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    raise AuditRefusal(f"required source function missing: {name}")


def calls(source: str, function: str) -> set[str]:
    names = set()
    for node in ast.walk(function_node(source, function)):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                names.add(fn.id)
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                names.add(fn.value.id + "." + fn.attr)
    return names


def literals(source: str, function: str) -> set[str]:
    return {
        node.value for node in ast.walk(function_node(source, function))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditRefusal(message)


def assignment(source: str, name: str) -> ast.expr:
    for node in tree(source).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = [x.id for x in node.targets if isinstance(x, ast.Name)] if isinstance(node, ast.Assign) else [node.target.id] if isinstance(node.target, ast.Name) else []
            if name in names:
                return node.value
    raise AuditRefusal(f"missing code-pinned variable: {name}")


def audit(s: dict[str, str]) -> dict:
    require(set(s) == set(FILES), "unexpected inspected-source roster")
    manifest = json.loads(s["qc_manifest"])
    require(manifest.get("status") == "QUALIFIED_SAMPLED_QC_AUTHORITY", "V74 manifest status changed")
    require(manifest.get("sample_total_cells") == 50000, "V74 sampling frame changed")
    require(manifest.get("qc_quantiles_are_full_population_exact") is False, "incorrect full-population claim")
    definitions = manifest["definitions"]
    require(all(k in definitions for k in (
        "rna_library_size", "rna_detected_feature_count", "rna_zero_fraction",
        "structural_missing_fraction", "log1p_library_vs_detected_pearson"
    )), "V74 QC meaning changed")

    require("load" in calls(s["qc"], "by_operator"), "QC operator loader disconnected")
    require("sha256" in s["qc"], "QC loader lost its checksum logic")
    observer = calls(s["observer"], "observe")
    require({"Q.by_operator", "operator_availability", "empirical_targets", "exact_counts"} <= observer,
            "historical V74 physical observation call path no longer verified")
    target_calls = calls(s["observer"], "empirical_targets")
    require("Q.interp_quantiles" in target_calls, "real depth/detection quantile consumption lost")
    target_names = literals(s["observer"], "empirical_targets")
    require({"rna_library_size_quantiles", "rna_detected_feature_quantiles",
             "log1p_library_vs_detected_pearson", "measured_scalar_addresses"} <= target_names,
            "V74 sampled operator QC field changed")
    require("structural_missing_fraction" in literals(s["observer"], "operator_availability"),
            "structural support projection no longer verified")
    require("quotas_for_n" in calls(s["population"], "assignments_for_ids"),
            "population source/operator/donor quotas disconnected")
    require({"F.operator_availability", "F.empirical_targets", "F.exact_counts"} <=
            calls(s["extended"], "observe"), "V77 observer no longer inherits frozen V74 measurements")
    require("cell_class_counts" in literals(s["real_train"], "extract"),
            "V77 real class composition measurement lost")

    require(isinstance(assignment(s["task3"], "OBSERVATION_PARAMETER_SEMANTICS_BOUND"),
                       ast.Constant) and
            assignment(s["task3"], "OBSERVATION_PARAMETER_SEMANTICS_BOUND").value is False,
            "Task3 now claims parameter semantics; independent review needed")
    registry = assignment(s["task3"], "_AUTHENTICATED_CALIBRATION_REGISTRY")
    require(isinstance(registry, ast.Call) and isinstance(registry.func, ast.Name) and
            registry.func.id == "frozenset" and not registry.args and not registry.keywords,
            "Task3 authenticated issuer registry is no longer empty")
    registered = {n.value for n in ast.walk(
        assignment(s["task3"], "OBSERVATION_PARAMETER_REGISTRY_ROWS"))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value.startswith("OBS_")}
    require(registered == set(PARAMETERS), "Task3 parameter names changed")
    for part in ("qc", "observer", "population", "extended"):
        require(not any(name in s[part] for name in PARAMETERS),
                f"{part} mentions a Task3 parameter; source-only absence proof is stale")
    require("N_GENES=96" in s["observer"].replace(" ", ""),
            "the original frozen World-A observer is no longer a 96-address projection")

    return {
        "schema": "SYNTHETIC_OBSERVATION_REAL_QC_SOURCE_BINDING_STATIC_V1",
        "conclusion": "HISTORICAL_V74_V77_QC_CONSUMPTION_CONFIRMED__TASK3_PARAMETER_BINDING_UNPROVEN",
        "checked_source_git_blobs": {k: v[1] for k, v in FILES.items()},
        "historical_consumed": {
            "operator_library_depth": "SOURCE_CALL_PATH_CONFIRMED__50K_SAMPLED",
            "operator_detected_features": "SOURCE_CALL_PATH_CONFIRMED__50K_SAMPLED",
            "measured_zero_vs_structural_support": "PARTIAL_96_ADDRESS_PROJECTION__NOT_FIVE_STATE_RIGHTS_AUTHORITY",
            "source_donor_operator_quotas": "SOURCE_CALL_PATH_CONFIRMED",
            "real_broad_class_counts": "MEASURED_ONLY__NOT_PROVEN_GENERATIVE",
            "extended_observer_reuses_V74": "SOURCE_CALL_PATH_CONFIRMED",
        },
        "task3_parameters": {name: NA for name in PARAMETERS},
        "task3_authenticated_calibration_registry": "EMPTY",
        "actual_task3_to_generator_parameter_binding": "NOT_VERIFIED__NO_AUTHORITY",
        "RNA_only_scope": ["fragment_multiplicity_NOT_CHECKED", "modality_availability_NOT_CHECKED"],
        "real_raw_values_opened": False,
        "synthetic_world_generated": False,
        "optimizer_executed": False,
        "production_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(audit(read_pinned(args.root)), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
