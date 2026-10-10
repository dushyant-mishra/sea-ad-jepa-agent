from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .build_v79_factorial_worlds import ArmManifest, canonical_manifest_json, manifest_hash, validate_arm_manifest
from .score_v79_factorial_worlds import compare_factorial_mechanisms

FROZEN_V78_BASE_SHA = "e959d9a732698ae9a41e8cb1f6c10052d7390326"
_FALSE_FLAGS = (
    "test_or_morabito_accessed",
    "pathology_accessed",
    "target_discovery_modified",
)


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bind_authority_file_hashes(contract: Mapping[str, Any], paths: Mapping[str, str | Path]) -> dict[str, Any]:
    """Recompute actual authority hashes from bytes; never trust self-declared `actual`."""
    bound = json.loads(json.dumps(dict(contract)))
    recs = bound.setdefault("authority_hashes", {})
    for name, path in paths.items():
        if name not in recs:
            recs[name] = {"expected": None}
        recs[name]["actual"] = _sha256_file(path)
    return bound


def preexecution_gate(contract: Mapping[str, Any], manifest: Mapping[str, Any] | ArmManifest) -> dict[str, Any]:
    m = validate_arm_manifest(manifest)
    blockers: list[str] = []
    if contract.get("v78_base_sha") != FROZEN_V78_BASE_SHA:
        blockers.append("frozen_v78_base_moved")
    for name, rec in dict(contract.get("authority_hashes", {})).items():
        if not rec.get("expected") or rec.get("actual") != rec.get("expected"):
            blockers.append(f"authority_hash_mismatch:{name}")
    if not contract.get("authority_hashes"):
        blockers.append("authority_hashes_missing")
    if contract.get("preregistered_manifest_hash") != manifest_hash(m):
        blockers.append("arm_manifest_hash_mismatch")
    if contract.get("test_or_morabito_accessed") is True:
        blockers.append("protected_data_access")
    if contract.get("pathology_accessed") is True:
        blockers.append("pathology_access")
    if contract.get("target_discovery_modified") is True:
        blockers.append("target_discovery_modified")
    if contract.get("post_outcome_arm_mutation") is True:
        blockers.append("post_outcome_arm_mutation")
    if contract.get("training_authorized") is True or m.training_authorized:
        blockers.append("training_authorization_contamination")
    blockers = sorted(set(blockers))
    return {
        "schema": "V79_FACTORIAL_PREEXECUTION_GATE_V1",
        "status": "READY" if not blockers else "BLOCKED",
        "blockers": blockers,
        "v78_base_sha": contract.get("v78_base_sha"),
        "manifest_hash": manifest_hash(m),
        "authority_hashes": dict(contract.get("authority_hashes", {})),
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_modified": False,
    }


def falsification_blockers(checks: Mapping[str, Any]) -> list[str]:
    required = (
        "within_class_geometry_plausible",
        "degree_transitivity_preserved",
        "biology_independent_of_source",
        "detected_counts_emergent",
        "c_obs_truth_identical",
        "c_bio_truth_distinct",
        "identity_firewall_clean",
        "manifest_unchanged",
        "protected_data_clean",
        "training_authorized_false",
    )
    missing = [k for k in required if k not in checks]
    if missing:
        return [f"missing_check:{k}" for k in missing]
    return [k for k in required if checks.get(k) is not True]


def terminal_ruling(evidence: Mapping[str, Mapping[str, Any]], checks: Mapping[str, Any], *, adequacy_pass: bool) -> dict[str, Any]:
    blockers = falsification_blockers(checks)
    ruling = "FAMILY_UNRESOLVED"
    promoted = None
    if adequacy_pass and not blockers:
        ruling = compare_factorial_mechanisms(evidence)
        if ruling != "FAMILY_UNRESOLVED":
            promoted = {"family_recommendation": ruling, "authority": "NOT_TRAINING_AUTHORITY"}
    return {
        "schema": "V79_FACTORIAL_TERMINAL_RULING_V1",
        "mechanism_family_ruling": ruling,
        "falsification_blockers": blockers,
        "adequacy_pass": bool(adequacy_pass),
        "synthetic_arm_promoted": promoted,
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_modified": False,
    }


def make_receipt(kind: str, contract: Mapping[str, Any], manifest: Mapping[str, Any] | ArmManifest,
                 payload: Mapping[str, Any]) -> dict[str, Any]:
    m = validate_arm_manifest(manifest)
    return {
        "schema": f"V79_FACTORIAL_{str(kind).upper()}_V1",
        "v78_base_sha": contract.get("v78_base_sha"),
        "authority_hashes": contract.get("authority_hashes", {}),
        "manifest_hash": manifest_hash(m),
        "seed_set": {
            "biology": m.biology_seed,
            "observation": m.observation_seed,
            "counterfactual_biology": m.counterfactual_biology_seed,
            "crossing": m.crossing_seed,
        },
        "endpoint_version": m.endpoint_version,
        "training_authorized": False,
        "v78_retuning_authorized": False,
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_modified": False,
        "payload": dict(payload),
    }


def _atomic_json(path: Path, obj: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")
    os.replace(tmp, path)


def run_preexecution_only(contract: Mapping[str, Any], manifest: Mapping[str, Any] | ArmManifest, out_dir: Path) -> dict[str, Any]:
    m = validate_arm_manifest(manifest)
    gate = preexecution_gate(contract, m)
    out = Path(out_dir)
    _atomic_json(out / "V79_FACTORIAL_PREEXECUTION_GATE_V1.json", gate)
    if gate["status"] != "READY":
        return gate
    manifest_rec = make_receipt("ARM_MANIFEST", contract, m, {"manifest": asdict(m)})
    _atomic_json(out / "V79_FACTORIAL_ARM_MANIFEST_V1.json", manifest_rec)
    return gate


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fail-closed V79 factorial tournament executor")
    p.add_argument("--manifest", required=True)
    p.add_argument("--custody", required=True)
    p.add_argument("--biology-authority", required=True)
    p.add_argument("--observation-authority", required=True)
    p.add_argument("--authority-file", action="append", default=[], metavar="NAME=PATH")
    p.add_argument("--out", required=True)
    p.add_argument("--preexecution-only", action="store_true")
    args = p.parse_args(argv)

    manifest = _load_json(args.manifest)
    contract = _load_json(args.custody)
    # Authorities are opened and their actual byte hashes are recomputed here; a self-declared
    # `actual` hash in the custody contract cannot authenticate the file used by execution.
    _load_json(args.biology_authority)
    _load_json(args.observation_authority)
    authority_paths = {"biology": args.biology_authority, "observation": args.observation_authority}
    for item in args.authority_file:
        if "=" not in item:
            raise ValueError("--authority-file must be NAME=PATH")
        name, path = item.split("=", 1)
        if not name or name in authority_paths:
            raise ValueError(f"invalid or duplicate authority-file name: {name!r}")
        authority_paths[name] = path
    contract = bind_authority_file_hashes(contract, authority_paths)
    gate = run_preexecution_only(contract, manifest, Path(args.out))
    if gate["status"] != "READY":
        return 2
    if not args.preexecution_only:
        raise PermissionError(
            "scientific execution is intentionally disabled until the committed preexecution package receives independent review"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
