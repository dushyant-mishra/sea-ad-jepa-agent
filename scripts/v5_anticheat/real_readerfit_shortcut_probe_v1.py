#!/usr/bin/env python3
"""Pathology-blind real reader-fit shortcut atlas for Teacher/Student V5.

Inputs are provenance-bound as a three-artifact chain:
  1) expression metadata package containing the frozen 50k sample + operator metadata;
  2) reconstructed 580 MB foundation expression archive containing the exact CSR NPZ;
  3) frozen calibration bundle containing the operator observation-state authority.

The metadata package audit must name the same SHA-256 as the expression archive's
single NPZ member. No T0 confirmation, pathology, DEV/SEALED,
reader_validation, or reader_oracle data are opened. This is an input-channel
shortcut atlas, not checkpoint qualification and not training authority.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from sea_ad_jepa.v5.anticheat_qualification_v1 import (
    categorical_group_holdout_attack,
    categorical_purity,
    mask_row_sha256,
    qualification_skeleton,
    quantile_scalar_group_holdout_attack,
    split_manifest_for_entities,
    state_count_features,
)

META_AUDIT = "expression/expression/FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json"
META_FREEZE = "expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
META_OPERATOR_PREFIX = "expression/expression/sample_operator_metadata/"
CAL_BASE = "FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/"
CAL_SUPPORT = CAL_BASE + "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"

EXPECTED_METADATA_ZIP_SHA256 = "1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4"
EXPECTED_EXPRESSION_ARCHIVE_SHA256 = "63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7"
EXPECTED_CALIBRATION_ZIP_SHA256 = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_zip_member(zf: zipfile.ZipFile, member: str) -> str:
    h = hashlib.sha256()
    with zf.open(member, "r") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_expression_lineage(metadata_zip: Path, expression_archive: Path) -> dict[str, object]:
    with zipfile.ZipFile(metadata_zip) as zf:
        audit = json.loads(zf.read(META_AUDIT))
    required = {"schema", "freeze_sha256", "cells", "addresses", "nnz", "output_sha256", "firewalls"}
    if not required.issubset(audit):
        raise RuntimeError(f"metadata audit missing {sorted(required - set(audit))}")
    if audit["schema"] != "foundation-discovery-expression-v1":
        raise RuntimeError("unexpected metadata audit schema")
    if int(audit["cells"]) != 50000 or int(audit["addresses"]) != 41238:
        raise RuntimeError("metadata audit geometry mismatch")
    firewalls = audit["firewalls"]
    for key in ("heldout_expression_read", "dev_expression_read", "sealed_expression_read", "pathology_read"):
        if firewalls.get(key) is not False:
            raise RuntimeError(f"metadata audit firewall not closed: {key}")

    with zipfile.ZipFile(expression_archive) as zf:
        members = [n for n in zf.namelist() if n.endswith(".npz")]
        if len(members) != 1:
            raise RuntimeError("foundation expression archive must contain exactly one NPZ member")
        member = members[0]
        member_sha = sha256_zip_member(zf, member)
    if member_sha != audit["output_sha256"]:
        raise RuntimeError("metadata audit output SHA does not match reconstructed expression NPZ member")
    return {
        "metadata_audit_schema": audit["schema"],
        "metadata_freeze_sha256": audit["freeze_sha256"],
        "expression_member": member,
        "expression_member_sha256": member_sha,
        "cells": int(audit["cells"]),
        "addresses": int(audit["addresses"]),
        "nnz": int(audit["nnz"]),
        "firewalls": firewalls,
    }


def _read_expression_metadata(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        freeze = pd.read_csv(io.BytesIO(zf.read(META_FREEZE)))
        required = {"stable_key", "operator_index", "donor_id", "matrix_id", "source"}
        if not required.issubset(freeze.columns):
            raise RuntimeError(f"freeze missing columns {sorted(required - set(freeze.columns))}")
        frames = []
        for operator_index in range(42):
            member = f"{META_OPERATOR_PREFIX}op{operator_index:02d}.meta.csv"
            frame = pd.read_csv(io.BytesIO(zf.read(member)))
            if not {"stable_key", "source_library"}.issubset(frame.columns):
                raise RuntimeError(f"{member} missing stable_key/source_library")
            frames.append(frame[["stable_key", "source_library"]].copy())
    depth = pd.concat(frames, ignore_index=True)
    if depth["stable_key"].duplicated().any():
        raise RuntimeError("stable_key duplicated across operator metadata")
    out = freeze.merge(depth, on="stable_key", how="left", validate="one_to_one")
    if out["source_library"].isna().any():
        raise RuntimeError("source_library missing after stable-key join")
    if len(out) != 50000:
        raise RuntimeError(f"expected 50000 frozen rows, found {len(out)}")
    return out


def _read_operator_states(path: Path) -> np.ndarray:
    with zipfile.ZipFile(path) as zf:
        payload = zf.read(CAL_SUPPORT)
    with np.load(io.BytesIO(payload), allow_pickle=False) as npz:
        states = np.asarray(npz["states"], dtype=np.uint8)
        operator_index = np.asarray(npz["operator_index"], dtype=np.int64)
    if states.shape[0] != 42 or not np.array_equal(operator_index, np.arange(42)):
        raise RuntimeError("operator observation-state authority is not exact 42-row order")
    return states


def build_report(metadata_zip: Path, expression_archive: Path, calibration_zip: Path) -> dict:
    lineage = verify_expression_lineage(metadata_zip, expression_archive)
    frame = _read_expression_metadata(metadata_zip)
    states = _read_operator_states(calibration_zip)
    signatures = mask_row_sha256(states)
    counts = state_count_features(states)

    op = pd.DataFrame({
        "operator_index": np.arange(42, dtype=np.int64),
        "mask_signature": signatures,
        "state0_count": counts[:, 0],
        "state1_count": counts[:, 1],
        "state2_count": counts[:, 2],
    })
    frame = frame.merge(op, on="operator_index", how="left", validate="many_to_one")
    if frame[["mask_signature", "state0_count", "state1_count", "state2_count"]].isna().any().any():
        raise RuntimeError("operator support join incomplete")

    support_signature = (
        frame[["state0_count", "state1_count", "state2_count"]]
        .astype("int64")
        .astype(str)
        .agg("|".join, axis=1)
        .to_numpy()
    )
    donor = frame["donor_id"].astype(str).to_numpy()
    source = frame["source"].astype(str).to_numpy()
    operator = frame["operator_index"].astype(str).to_numpy()
    mask = frame["mask_signature"].astype(str).to_numpy()
    log_depth = np.log1p(frame["source_library"].to_numpy(dtype=np.float64))

    atlas = {
        "rows": int(len(frame)),
        "donors": int(frame["donor_id"].nunique()),
        "operators": int(frame["operator_index"].nunique()),
        "sources": int(frame["source"].nunique()),
        "mask_signatures": int(frame["mask_signature"].nunique()),
        "support_count_signatures": int(pd.Series(support_signature).nunique()),
        "mask_signature_to_source_purity": categorical_purity(mask, source),
        "mask_signature_to_operator_purity": categorical_purity(mask, operator),
        "support_count_signature_to_source_purity": categorical_purity(support_signature, source),
        "support_count_signature_to_operator_purity": categorical_purity(support_signature, operator),
        "mask_only_source_attack_donor_holdout": categorical_group_holdout_attack(
            mask, source, donor, salt="V5_MASK_SOURCE_DONOR_HOLDOUT_V1"
        ),
        "mask_only_operator_attack_donor_holdout": categorical_group_holdout_attack(
            mask, operator, donor, salt="V5_MASK_OPERATOR_DONOR_HOLDOUT_V1"
        ),
        "support_only_source_attack_donor_holdout": categorical_group_holdout_attack(
            support_signature, source, donor, salt="V5_SUPPORT_SOURCE_DONOR_HOLDOUT_V1"
        ),
        "support_only_operator_attack_donor_holdout": categorical_group_holdout_attack(
            support_signature, operator, donor, salt="V5_SUPPORT_OPERATOR_DONOR_HOLDOUT_V1"
        ),
        "depth_only_source_attack_donor_holdout": quantile_scalar_group_holdout_attack(
            log_depth, source, donor, salt="V5_DEPTH_SOURCE_DONOR_HOLDOUT_V1"
        ),
        "depth_only_operator_attack_donor_holdout": quantile_scalar_group_holdout_attack(
            log_depth, operator, donor, salt="V5_DEPTH_OPERATOR_DONOR_HOLDOUT_V1"
        ),
    }

    splits = split_manifest_for_entities({
        "donor": donor,
        "matrix": frame["matrix_id"].astype(str).to_numpy(),
        "source_or_study": source,
    })
    splits["technology"] = {
        "status": "NOT_ESTIMABLE",
        "reason": (
            "no independently declared technology column exists in the supplied "
            "pathology-blind 50k freeze; source is not silently relabeled as technology"
        ),
    }

    report = qualification_skeleton(input_shortcut_atlas=atlas)
    report.update({
        "artifact_kind": "PATHOLOGY_BLIND_READER_FIT_INPUT_SHORTCUT_ATLAS",
        "metadata_zip_sha256": sha256_file(metadata_zip),
        "expression_archive_sha256": sha256_file(expression_archive),
        "calibration_zip_sha256": sha256_file(calibration_zip),
        "expression_lineage": lineage,
        "transfer_split_manifests": splits,
        "protected_or_confirmation_data_opened": False,
        "optimizer_executed": False,
        "interpretation": (
            "Strong input-side support/mask/depth predictability proves shortcut "
            "channels exist. It is not a z_bio failure because no model embedding "
            "is evaluated by this input-only atlas."
        ),
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-zip", required=True, type=Path)
    parser.add_argument("--expression-archive", required=True, type=Path)
    parser.add_argument("--calibration-zip", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-metadata-sha256", default=EXPECTED_METADATA_ZIP_SHA256)
    parser.add_argument("--expected-expression-archive-sha256", default=EXPECTED_EXPRESSION_ARCHIVE_SHA256)
    parser.add_argument("--expected-calibration-sha256", default=EXPECTED_CALIBRATION_ZIP_SHA256)
    args = parser.parse_args()

    for path in (args.metadata_zip, args.expression_archive, args.calibration_zip):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    expected = {
        args.metadata_zip: args.expected_metadata_sha256,
        args.expression_archive: args.expected_expression_archive_sha256,
        args.calibration_zip: args.expected_calibration_sha256,
    }
    for path, digest in expected.items():
        actual = sha256_file(path)
        if actual != digest:
            raise SystemExit(f"SHA-256 mismatch for {path}: {actual}")

    report = build_report(args.metadata_zip, args.expression_archive, args.calibration_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_V5_REAL_READERFIT_SHORTCUT_ATLAS_V1")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
