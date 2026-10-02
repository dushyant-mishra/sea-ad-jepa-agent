#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "results/v64/V72_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate(root: Path = ROOT):
    errors = []
    contract_path = root / "results/v64/V72_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json"
    if not contract_path.exists():
        return ["V72_READINESS_CONTRACT_MISSING"]
    c = json.loads(contract_path.read_text())

    # First inherit the V71 R0/R1 checks rather than silently replacing them.
    v71 = root / "scripts/v64/validate_v71_synthetic_pipeline_readiness.py"
    if not v71.exists():
        errors.append("V71_READINESS_VALIDATOR_MISSING")
    else:
        inherited = load_module(v71, "v71_readiness").validate(root)
        errors.extend([f"V71:{e}" for e in inherited])

    for rel in c.get("required_json", []):
        p = root / rel
        if not p.exists():
            errors.append(f"MISSING_REQUIRED_JSON:{rel}")
            continue
        try:
            json.loads(p.read_text())
        except Exception as exc:
            errors.append(f"BAD_REQUIRED_JSON:{rel}:{type(exc).__name__}")

    for key in ("required_executables", "required_tests"):
        for rel in c.get(key, []):
            if not (root / rel).exists():
                errors.append(f"MISSING_{key.upper()}:{rel}")

    # Execute the clean coupled fixture in a temporary directory.
    builder = root / "scripts/v64/build_v72_coupled_multidataset_synthetic_fixture.py"
    validator = root / "scripts/v64/validate_v72_coupled_multidataset_synthetic_fixture.py"
    if builder.exists() and validator.exists():
        b = load_module(builder, "v72_builder")
        v = load_module(validator, "v72_validator")
        with tempfile.TemporaryDirectory() as td:
            challenge = Path(td) / "challenge"
            b.build(challenge)
            errors.extend([f"V72_FIXTURE:{e}" for e in v.validate(challenge)])

    # Governance checks that should remain machine-readable.
    g2_path = root / "results/v64/V72_STAGE4_G2_SPECIFICATION_GAP_CONTRACT_V1.json"
    if g2_path.exists():
        g2 = json.loads(g2_path.read_text())
        if not str(g2.get("status", "")).startswith("OPEN"):
            errors.append("G2_SPECIFICATION_GAP_NOT_OPEN")
        if g2.get("current_action") != "NO_STAGE4_AUTHORIZATION_CHANGE":
            errors.append("G2_CONTRACT_CHANGED_STAGE4_AUTHORIZATION")

    bl_path = root / "results/v64/V72_ROUTEB_HG38_BLACKLIST_PROSPECTIVE_AMENDMENT_V1.json"
    if bl_path.exists():
        bl = json.loads(bl_path.read_text())
        if not str(bl.get("status", "")).startswith("PROSPECTIVE"):
            errors.append("ROUTEB_BLACKLIST_NOT_PROSPECTIVE")

    old_docker = root / "docker/scenicplus/Dockerfile"
    new_docker = root / "docker/scenicplus/Dockerfile.successor_pinned"
    if old_docker.exists() and new_docker.exists():
        old = old_docker.read_text()
        new = new_docker.read_text()
        if "CREATE_CISTARGET_DATABASES_REF=master" not in old:
            errors.append("HISTORICAL_DOCKERFILE_WAS_REWRITTEN")
        if "CREATE_CISTARGET_DATABASES_REF=master" in new:
            errors.append("SUCCESSOR_DOCKERFILE_STILL_USES_MASTER")
        if "304d5dc1b15e5c923908a50a1ec291c3faaccf9c" not in new:
            errors.append("SUCCESSOR_DOCKERFILE_CISTARGET_COMMIT_NOT_PINNED")

    return errors


if __name__ == "__main__":
    errs = validate()
    if errs:
        print("\n".join(errs))
        raise SystemExit(1)
    print("PASS: V72 synthetic pipeline R0/R1 executable readiness")
