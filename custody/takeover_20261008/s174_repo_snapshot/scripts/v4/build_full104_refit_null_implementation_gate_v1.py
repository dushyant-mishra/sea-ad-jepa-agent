#!/usr/bin/env python3
"""Fail-atomic publisher for the FULL104 refit-null implementation gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import pandas as pd


FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("freeze", "core", "runner", "validator-code", "preflight-code", "fit-basis-code",
                 "production-package", "validator-package", "preflight-package", "council", "threat-model"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    paths = {key.replace("_", "-"): Path(value).resolve() for key, value in vars(args).items() if key != "out"}
    out = Path(args.out).resolve(); staging = out.with_name("_staging_" + out.name)
    if out.exists() or staging.exists():
        raise RuntimeError("gate output/staging already exists")
    freeze_manifest = paths["freeze"] / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv"
    production_report = paths["production-package"] / "PRODUCTION_TARGETED_FIXTURE_REPORT.json"
    validator_report = paths["validator-package"] / "INDEPENDENT_IMPLEMENTATION_VALIDATION.json"
    validator_manifest = paths["validator-package"] / "INDEPENDENT_IMPLEMENTATION_VALIDATION_MANIFEST.csv"
    preflight_report = paths["preflight-package"] / "COMPUTE_STORAGE_RUNTIME_PREFLIGHT.json"
    preflight_manifest = paths["preflight-package"] / "IMPLEMENTATION_COMPUTE_PREFLIGHT_MANIFEST.csv"
    council = json.loads(paths["council"].read_text())
    statuses = {
        "freeze": sha(freeze_manifest) == FREEZE_ROOT,
        "production": json.loads(production_report.read_text())["status"] == "PASS_PRODUCTION_TARGETED_FIXTURES",
        "independent": json.loads(validator_report.read_text())["status"] == "PASS_INDEPENDENT_IMPLEMENTATION_VALIDATOR",
        "compute": json.loads(preflight_report.read_text())["status"] == "PASS_COMPUTE_PREFLIGHT",
        "authority": council.get("Historian_Authority") == "PASS",
        "code_math": council.get("Code_Math") == "PASS",
        "statistics_geometry": council.get("Statistics_Geometry") == "PASS",
        "independent_review": council.get("Independent_Validator") == "PASS",
        "red_team": council.get("Red_Team") == "PASS",
    }
    if not all(statuses.values()):
        raise RuntimeError(f"implementation gate blocked: {statuses}")
    components = {
        "freeze_root": FREEZE_ROOT,
        "core_sha256": sha(paths["core"]), "runner_sha256": sha(paths["runner"]),
        "validator_code_sha256": sha(paths["validator-code"]), "preflight_code_sha256": sha(paths["preflight-code"]),
        "fit_basis_code_sha256": sha(paths["fit-basis-code"]), "gate_builder_code_sha256": sha(Path(__file__)),
        "production_report_sha256": sha(production_report), "validator_report_sha256": sha(validator_report),
        "validator_manifest_sha256": sha(validator_manifest), "preflight_report_sha256": sha(preflight_report),
        "preflight_manifest_sha256": sha(preflight_manifest), "council_sha256": sha(paths["council"]),
        "threat_model_scope_sha256": sha(paths["threat-model"]),
    }
    fingerprint = canonical_sha(components)
    staging.mkdir(parents=True); artifacts = staging / "artifacts"; artifacts.mkdir()
    copy_sources = [paths["core"], paths["runner"], paths["validator-code"], paths["preflight-code"],
                    paths["fit-basis-code"], Path(__file__).resolve(), production_report, validator_report,
                    validator_manifest, preflight_report, preflight_manifest, paths["council"], paths["threat-model"]]
    for index, source in enumerate(copy_sources):
        target = artifacts / f"{index:02d}_{source.name}"; shutil.copy2(source, target)
    write_json(staging / "IMPLEMENTATION_COMPONENTS.json", {"components": components, "implementation_fingerprint": fingerprint})
    component_files = sorted([p for p in staging.rglob("*") if p.is_file()])
    manifest = staging / "IMPLEMENTATION_GATE_MANIFEST.csv"
    pd.DataFrame([{"path": str(p.relative_to(staging)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in component_files]).to_csv(manifest, index=False, lineterminator="\n")
    status = {"schema": "full104-refit-null-implementation-preflight-status-v1",
              "status": "PASS_IMPLEMENTATION_AND_COMPUTE_GATE", "freeze_root": FREEZE_ROOT,
              "implementation_fingerprint": fingerprint, "gate_manifest_sha256": sha(manifest),
              "checks": statuses, "real_cap_executed": False,
              "authorization": "IMPLEMENTATION_READY; REAL CAP REMAINS HELD FOR EXPLICIT POST-REPORT START"}
    write_json(staging / "IMPLEMENTATION_PREFLIGHT_STATUS.json", status)
    root_manifest = staging / "IMPLEMENTATION_GATE_ROOT_MANIFEST.csv"
    root_files = sorted([p for p in staging.rglob("*") if p.is_file() and p != root_manifest])
    pd.DataFrame([{"path": str(p.relative_to(staging)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in root_files]).to_csv(root_manifest, index=False, lineterminator="\n")
    (staging / "IMPLEMENTATION_GATE_ROOT_SHA256.txt").write_text(sha(root_manifest) + "\n", encoding="ascii")
    os.replace(staging, out)
    print(json.dumps({"status": status["status"], "implementation_fingerprint": fingerprint,
                      "gate_manifest_sha256": status["gate_manifest_sha256"],
                      "root_manifest_sha256": sha(out / root_manifest.name)}, indent=2))


if __name__ == "__main__":
    main()
