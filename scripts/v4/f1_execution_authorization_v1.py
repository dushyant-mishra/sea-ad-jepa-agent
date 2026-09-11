#!/usr/bin/env python3
"""F1 real-execution authorization: an external, pre-result binding.

This module removes an architectural dead end. The producer previously carried
`REAL_EXECUTION_READY = False` and three `None` output roots in its own source,
so the only way to make the frozen source runnable was to edit it -- which
destroys the freeze. Authorization now lives entirely outside the frozen Python
source, in an artifact whose path is supplied by the environment, and the frozen
source reads it.

Two boundaries matter and are enforced here:

1. Authorization is a PRE-RESULT binding. It names the exact package root,
   frozen source digests, checkpoint, reader population, authority digests,
   accepted mechanics and frozen geometry that a run is permitted to use. It
   must exist before the sweep and it may not contain any produced output root.
2. The post-run data-only closure is NOT authorization. A closure artifact
   carries capture/shard/effect roots that cannot exist before execution, so
   anything carrying them is rejected as an authorization. That closes the
   retroactive-authorization path: a run cannot be legitimised after the fact by
   writing a closure for it.

Every mismatch is a distinct fail-closed STOP rather than a generic refusal, so
a reviewer sees which binding drifted.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_ENV = "F1_EXECUTION_AUTHORIZATION"
AUTHORIZATION_SCHEMA = "f1-real-execution-authorization-v1"

STOP_NO_AUTHORIZATION = "STOP_F1_EXECUTION_AUTHORIZATION_ABSENT"
STOP_AUTHORIZATION_SCHEMA = "STOP_F1_EXECUTION_AUTHORIZATION_SCHEMA"
STOP_AUTHORIZATION_SELF_ROOT = "STOP_F1_EXECUTION_AUTHORIZATION_ROOT_MISMATCH"
STOP_PACKAGE_ROOT = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_PACKAGE_ROOT"
STOP_SOURCE_ROOT = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_SOURCE_ROOT"
STOP_CHECKPOINT = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_CHECKPOINT"
STOP_POPULATION = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_READER_POPULATION"
STOP_AUTHORITY_DRIFT = "STOP_F1_EXECUTION_AUTHORIZATION_AUTHORITY_DRIFT"
STOP_MECHANICS = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_MECHANICS"
STOP_GEOMETRY = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_GEOMETRY"
STOP_RETROACTIVE = "STOP_F1_EXECUTION_AUTHORIZATION_IS_A_CLOSURE_ARTIFACT"
STOP_SCOPE = "STOP_F1_EXECUTION_AUTHORIZATION_WRONG_SCOPE"
STOP_AUTHORIZATION_ISSUER_UNTRUSTED = "STOP_F1_AUTHORIZATION_ISSUER_UNTRUSTED"

# The only lawful scope this lane may be authorized for. The first real F1 run
# is a reference production-mechanics baseline on the clean u0 fixture; it is not
# a healthy trained teacher, not a biological qualification of u0, and not
# authority to select a training target or to begin D1.
LAWFUL_SCOPE = "F1_U0_PRODUCTION_MECHANICS_REFERENCE_BASELINE"

# Frozen u0 mechanics fixture checkpoint. Not a qualified biological teacher.
FROZEN_U0_CHECKPOINT_SHA256 = (
    "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4")

# Output-root keys that may only ever appear in a post-result closure artifact.
CLOSURE_ONLY_KEYS = ("capture_root_sha256", "shard_set_root_sha256",
                     "effect_row_root_sha256", "real_capture_root",
                     "real_shard_set_root", "real_effect_row_root")

REQUIRED_KEYS = ("schema", "authorization_id", "scope", "issued_by", "issued_at",
                 "package_root_sha256", "source_sha256", "checkpoint_sha256",
                 "reader_population", "authority_sha256", "accepted_mechanics",
                 "frozen_geometry", "accepted_real_forward_root",
                 "authorization_root_sha256")


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def authorization_body_root(payload: Mapping[str, Any]) -> str:
    """Digest over the authorization body, excluding its own stated root."""
    body = {k: v for k, v in payload.items() if k != "authorization_root_sha256"}
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def _require(condition: bool, stop: str, detail: str) -> None:
    if not condition:
        raise PermissionError("%s: %s" % (stop, detail))


def load_authorization_payload(path: str | Path | None = None) -> dict[str, Any]:
    """Read the authorization artifact from an explicit path or the environment.

    Absence is refused, never defaulted. There is deliberately no in-source
    fallback: the whole point is that the frozen source cannot authorize itself.
    """
    location = str(path) if path is not None else os.environ.get(AUTHORIZATION_ENV, "")
    if not location:
        raise PermissionError(
            "%s: set %s to an execution-authorization artifact; the frozen source "
            "cannot authorize itself and contains no override"
            % (STOP_NO_AUTHORIZATION, AUTHORIZATION_ENV))
    resolved = Path(location)
    if not resolved.is_file():
        raise PermissionError("%s: %s is not a file" % (STOP_NO_AUTHORIZATION, resolved))
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PermissionError("%s: authorization must be a JSON object"
                              % STOP_AUTHORIZATION_SCHEMA)
    payload["_artifact_path"] = str(resolved)
    payload["_artifact_sha256"] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return payload


def validate_execution_authorization(
    payload: Mapping[str, Any], *,
    package_root_sha256: str,
    observed_source_sha256: Mapping[str, str],
    observed_authority_sha256: Mapping[str, str],
    accepted_mechanics: Mapping[str, Any],
    frozen_geometry: Mapping[str, int],
    accepted_real_forward_root: str,
    lawful_partition: str,
    expected_donor_count: int,
    expected_donor_roster_root: str,
    trusted_authorizations: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate an authorization against everything it claims to bind.

    Each check is separate and named so a reviewer can tell which binding
    drifted rather than seeing one opaque refusal.
    """
    absent = [k for k in REQUIRED_KEYS if k not in payload]
    _require(not absent, STOP_AUTHORIZATION_SCHEMA, "missing keys %r" % absent)
    _require(payload["schema"] == AUTHORIZATION_SCHEMA, STOP_AUTHORIZATION_SCHEMA,
             "schema is %r, expected %r" % (payload["schema"], AUTHORIZATION_SCHEMA))

    # Retroactive authorization is impossible: a closure artifact is not an
    # authorization, and an authorization may not carry produced output roots.
    present_output_keys = [k for k in CLOSURE_ONLY_KEYS if k in payload]
    _require(not present_output_keys, STOP_RETROACTIVE,
             "authorization carries produced output roots %r, which cannot exist "
             "before the sweep" % present_output_keys)

    _require(payload["scope"] == LAWFUL_SCOPE, STOP_SCOPE,
             "scope is %r, expected %r" % (payload["scope"], LAWFUL_SCOPE))

    stated_root = str(payload["authorization_root_sha256"])
    recomputed = authorization_body_root(
        {k: v for k, v in payload.items() if not k.startswith("_")})
    _require(stated_root == recomputed, STOP_AUTHORIZATION_SELF_ROOT,
             "stated %s but the body digests to %s" % (stated_root, recomputed))

    # Self-consistency is not issuer authenticity. The caller must supply an
    # independently trusted issuer->authorization-root mapping. There is no
    # default and no self-trust path; until governance issues such a trust
    # anchor, real execution remains unauthorized.
    issuer = str(payload["issued_by"])
    trusted = dict(trusted_authorizations or {})
    trusted_root = trusted.get(issuer)
    _require(trusted_root is not None, STOP_AUTHORIZATION_ISSUER_UNTRUSTED,
             "issuer %r has no independent trusted authorization root" % issuer)
    _require(str(trusted_root) == stated_root, STOP_AUTHORIZATION_ISSUER_UNTRUSTED,
             "issuer %r is trusted for root %s, not supplied root %s"
             % (issuer, trusted_root, stated_root))

    _require(str(payload["package_root_sha256"]) == str(package_root_sha256),
             STOP_PACKAGE_ROOT,
             "authorized for package root %s but the package is %s"
             % (payload["package_root_sha256"], package_root_sha256))

    declared_sources = dict(payload["source_sha256"])
    for name, observed in sorted(observed_source_sha256.items()):
        _require(name in declared_sources, STOP_SOURCE_ROOT,
                 "authorization does not bind source %r" % name)
        _require(str(declared_sources[name]) == str(observed), STOP_SOURCE_ROOT,
                 "source %r is %s but the authorization binds %s"
                 % (name, observed, declared_sources[name]))
    unbound = sorted(set(declared_sources) - set(observed_source_sha256))
    _require(not unbound, STOP_SOURCE_ROOT,
             "authorization binds sources that were not verified: %r" % unbound)

    _require(str(payload["checkpoint_sha256"]) == FROZEN_U0_CHECKPOINT_SHA256,
             STOP_CHECKPOINT,
             "checkpoint is %s but this lane is bound to the frozen u0 fixture %s"
             % (payload["checkpoint_sha256"], FROZEN_U0_CHECKPOINT_SHA256))

    population = dict(payload["reader_population"])
    _require(str(population.get("partition")) == str(lawful_partition), STOP_POPULATION,
             "partition is %r, expected %r" % (population.get("partition"), lawful_partition))
    _require(int(population.get("donor_count", -1)) == int(expected_donor_count),
             STOP_POPULATION,
             "donor_count is %r, expected %d" % (population.get("donor_count"),
                                                 expected_donor_count))
    _require(str(population.get("donor_roster_root")) == str(expected_donor_roster_root),
             STOP_POPULATION,
             "donor roster root is %r, expected %s" % (population.get("donor_roster_root"),
                                                       expected_donor_roster_root))
    forbidden = population.get("forbidden_populations_accessed")
    _require(forbidden in ([], (), None) or not forbidden, STOP_POPULATION,
             "authorization declares access to forbidden populations %r" % (forbidden,))

    declared_authorities = dict(payload["authority_sha256"])
    drift = {name: (declared_authorities.get(name), digest)
             for name, digest in sorted(observed_authority_sha256.items())
             if str(declared_authorities.get(name)) != str(digest)}
    _require(not drift, STOP_AUTHORITY_DRIFT, "authority drift %r" % drift)

    declared_mechanics = dict(payload["accepted_mechanics"])
    _require(declared_mechanics == dict(accepted_mechanics), STOP_MECHANICS,
             "mechanics differ from the frozen acceptance contract: %r"
             % {k: (declared_mechanics.get(k), v) for k, v in accepted_mechanics.items()
                if declared_mechanics.get(k) != v})

    declared_geometry = {k: int(v) for k, v in dict(payload["frozen_geometry"]).items()}
    expected_geometry = {k: int(v) for k, v in dict(frozen_geometry).items()}
    _require(declared_geometry == expected_geometry, STOP_GEOMETRY,
             "geometry differs: %r" % {k: (declared_geometry.get(k), v)
                                       for k, v in expected_geometry.items()
                                       if declared_geometry.get(k) != v})

    _require(str(payload["accepted_real_forward_root"]) == str(accepted_real_forward_root),
             STOP_AUTHORITY_DRIFT,
             "accepted real-forward root is %r, expected %s"
             % (payload["accepted_real_forward_root"], accepted_real_forward_root))

    return {
        "schema": "f1-execution-authorization-validated-v1",
        "authorization_id": str(payload["authorization_id"]),
        "scope": str(payload["scope"]),
        "authorization_root_sha256": stated_root,
        "artifact_path": payload.get("_artifact_path"),
        "artifact_sha256": payload.get("_artifact_sha256"),
        "package_root_sha256": str(payload["package_root_sha256"]),
        "checkpoint_sha256": str(payload["checkpoint_sha256"]),
        "partition": str(population.get("partition")),
        "donor_count": int(population.get("donor_count")),
        "donor_roster_root": str(population.get("donor_roster_root")),
        "binds_output_roots": False,
        "is_closure": False,
        "authorizes": ("execution of the F1 u0 production-mechanics reference baseline "
                       "on reader_fit only"),
        "does_not_authorize": [
            "a healthy trained-teacher result",
            "biological qualification of u0",
            "selection of a future training target",
            "starting D1 or production teacher training",
            "reader-validation, reader-oracle, development, sealed, external holdout "
            "or pathology access",
        ],
    }


def assert_not_closure_artifact(payload: Mapping[str, Any]) -> None:
    """A post-result closure may never be used as execution authorization."""
    present = [k for k in CLOSURE_ONLY_KEYS if k in payload]
    if present or str(payload.get("schema", "")).lower().find("closure") >= 0:
        raise PermissionError(
            "%s: this artifact carries %r and reads as a post-result closure; closure "
            "is produced only after outputs exist and can never authorize the run that "
            "produced them" % (STOP_RETROACTIVE, present or payload.get("schema")))


__all__ = [name for name in dir() if not name.startswith("_")]
