#!/usr/bin/env python3
"""Fail-closed authorization gate for real V65 TRAIN+VALIDATION recoverability execution.

This module does not fit models. It validates whether a future executor is permitted to
open real TRAIN+VALIDATION values. TEST access can never be authorized by this gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPERIMENT="Z_PRIV_ATAC_V1_RECOVERABILITY"
SCOPE="TRAIN_AND_VALIDATION_ONLY"
TEST_ACCESS="FORBIDDEN"
SOURCE_SHA256="6dca0d35ed7fd6cc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6"


class AuthorizationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def _required_digest(path: Path) -> str:
    if not path.exists():
        raise AuthorizationError(f"authority file missing: {path}")
    return sha256_file(path)


def expected_authority(root: Path) -> dict:
    split=root/"results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json"
    decision=root/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md"
    mechanics=root/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_EXECUTION_MECHANICS_CONTRACT_20260930.md"
    preflight=root/"results/v64/V65_PRIVILEGED_RECOVERABILITY_TRAIN_VALIDATION_PREFLIGHT_RECEIPT_V1.json"
    executor_contract=root/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_TRAIN_VALIDATION_EXECUTOR_CONTRACT_20260930.md"
    return {
        "source_sha256":SOURCE_SHA256,
        "split_sha256":_required_digest(split),
        "decision_contract_sha256":_required_digest(decision),
        "mechanics_contract_sha256":_required_digest(mechanics),
        "preflight_receipt_sha256":_required_digest(preflight),
        "executor_contract_sha256":_required_digest(executor_contract),
    }


def validate_authorization(path: Path, root: Path) -> dict:
    if not path.exists():
        raise AuthorizationError("explicit authorization artifact is absent")
    a=json.loads(path.read_text(encoding="utf-8"))
    if a.get("authorized") is not True:
        raise AuthorizationError("authorization artifact does not set authorized=true")
    if a.get("experiment") != EXPERIMENT:
        raise AuthorizationError("wrong experiment")
    if a.get("scope") != SCOPE:
        raise AuthorizationError("scope must be TRAIN_AND_VALIDATION_ONLY")
    if a.get("test_access") != TEST_ACCESS:
        raise AuthorizationError("TEST access must remain FORBIDDEN")

    expected=expected_authority(root)
    for k,v in expected.items():
        if a.get(k) != v:
            raise AuthorizationError(f"stale or wrong authority digest: {k}")

    forbidden_keys={"test_metrics","test_rows","test_predictions","test_authorized"}
    present=forbidden_keys & set(a)
    if present:
        raise AuthorizationError(f"authorization contains forbidden TEST fields: {sorted(present)}")

    return {
        "status":"AUTHORIZED_TRAIN_VALIDATION_ONLY",
        "experiment":EXPERIMENT,
        "scope":SCOPE,
        "test_access":TEST_ACCESS,
        "authority":expected,
    }


def main(argv=None) -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--authorization",type=Path,required=True)
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    args=ap.parse_args(argv)
    try:
        out=validate_authorization(args.authorization,args.repo_root)
    except AuthorizationError as e:
        print(json.dumps({"status":"STOP","reason":str(e)},sort_keys=True))
        return 2
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
