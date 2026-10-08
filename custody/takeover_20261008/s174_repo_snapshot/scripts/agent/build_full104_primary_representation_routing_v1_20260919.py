#!/usr/bin/env python3
"""Build the executable FULL104 representation-routing authority from live bytes."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.primary_representation_routing_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FEATURE_PARENT_MANIFEST_SHA256,
    FULL104_BLOCK_MANIFEST_SHA256,
    OBSERVATION_STATE_SHA256,
    VALUE_ONLY_SELECTION_ARTIFACT_SHA256,
    V0_FULL_PARENT_SHA256,
    V1_FULL_PARENT_SHA256,
    PrimaryRepresentationRoutingAuthorityV1,
    validate_value_only_selection_payload,
)

SELECTION_RELPATH = Path("docs/agent/V5_PRIMARY_REPRESENTATION_SELECTION_20260915.json")
PARENTS_RELPATH = Path("docs/agent/V5_PRIMARY_REPRESENTATION_FEATURE_PARENTS_20260915.json")
STREAMING_SOURCE_RELPATH = Path("src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--v0-full-parent", type=Path, required=True)
    p.add_argument("--v1-full-parent", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    live_inputs = {
        "FULL104 Level-4 manifest": (
            args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv",
            FULL104_BLOCK_MANIFEST_SHA256,
        ),
        "canonical registry": (args.registry, CANONICAL_REGISTRY_SHA256),
        "observation state": (args.observation_state, OBSERVATION_STATE_SHA256),
        "V0 full parent": (args.v0_full_parent, V0_FULL_PARENT_SHA256),
        "V1 full parent": (args.v1_full_parent, V1_FULL_PARENT_SHA256),
    }
    observed_live_roots = {}
    for role, (path, expected) in live_inputs.items():
        path = Path(path)
        if not path.is_file():
            raise SystemExit(f"required live representation input is missing: {role}: {path}")
        observed = sha256_file(path)
        if observed != expected:
            raise SystemExit(
                f"{role} root mismatch: expected {expected}, observed {observed}; "
                "do not substitute historical, smaller-run, placeholder, or reconstructed bytes"
            )
        observed_live_roots[role] = observed

    selection_path = args.repo / SELECTION_RELPATH
    parents_path = args.repo / PARENTS_RELPATH
    streaming_path = args.repo / STREAMING_SOURCE_RELPATH
    for required in (selection_path, parents_path, streaming_path):
        if not required.is_file():
            raise SystemExit(f"required representation-routing input is missing: {required}")

    observed_selection = sha256_file(selection_path)
    observed_parents = sha256_file(parents_path)
    if observed_selection != VALUE_ONLY_SELECTION_ARTIFACT_SHA256:
        raise SystemExit(
            "value-only selection byte root mismatch; do not substitute a stale or reconstructed selection"
        )
    if observed_parents != FEATURE_PARENT_MANIFEST_SHA256:
        raise SystemExit(
            "V0/V1 feature-parent byte root mismatch; do not substitute historical feature parents"
        )

    authority = PrimaryRepresentationRoutingAuthorityV1(
        authority_id="JEPA_V5_FULL104_PRIMARY_REPRESENTATION_ROUTING_AUTHORITY_V1",
        full104_block_manifest_sha256=observed_live_roots["FULL104 Level-4 manifest"],
        canonical_registry_sha256=observed_live_roots["canonical registry"],
        observation_state_sha256=observed_live_roots["observation state"],
        feature_parent_manifest_sha256=observed_parents,
        value_only_selection_artifact_sha256=observed_selection,
        v0_full_parent_sha256=observed_live_roots["V0 full parent"],
        v1_full_parent_sha256=observed_live_roots["V1 full parent"],
        full104_streaming_source_sha256=sha256_file(streaming_path),
    )
    authority.validate()
    authority.bind_streaming_source(streaming_path)
    authority.bind_global_context_parent_files(
        v0_parent_path=args.v0_full_parent,
        v1_parent_path=args.v1_full_parent,
    )
    validate_value_only_selection_payload(
        authority,
        load_json(selection_path),
        load_json(parents_path),
    )

    payload = {
        "schema": "V5_PRIMARY_REPRESENTATION_ROUTING_AUTHORITY_V1",
        **asdict(authority),
        "authority_sha256": authority.canonical_digest(),
        "scope": {
            "remaining_rna_route": (
                "authenticated canonical-address expression values from FULL104 Level-4; "
                "exact log1p10K normalization is delegated to the bound streaming source"
            ),
            "global_context_route": (
                "V0/V1 cell-level value channels [0:256) only; visibility [256:512) excluded"
            ),
            "physical_v0_v1_parent_bytes_authenticated": True,
            "production_model_consumer_bound": False,
            "f13_status": "ROUTING_EXECUTABLE__PRODUCTION_MODEL_CONSUMER_STILL_OPEN",
        },
        "does_not_authorize": [
            "TARGET_PANEL_LADDER",
            "MASKING_POLICY_OUTCOMES",
            "D_SHARED",
            "PROTECTED_OUTCOMES",
            "MODEL_GEOMETRY",
            "TRAINING",
        ],
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
