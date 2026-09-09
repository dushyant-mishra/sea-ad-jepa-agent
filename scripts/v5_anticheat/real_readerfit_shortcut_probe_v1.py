#!/usr/bin/env python3
"""Pathology-blind real reader-fit shortcut atlas for Teacher/Student V5.

Reads only the frozen 50k reader-fit discovery sample metadata plus the
calibration observation-state authority.  It never opens T0 confirmation,
pathology, DEV/SEALED, reader_validation, or reader_oracle.  This is an
input-channel shortcut atlas, not model checkpoint qualification.
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
    NOT_ESTIMABLE,
    categorical_group_holdout_attack,
    categorical_purity,
    mask_row_sha256,
    qualification_skeleton,
    quantile_scalar_group_holdout_attack,
    split_manifest_for_entities,
    state_count_features,
)

EXPR_FREEZE = "expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
EXPR_META_PREFIX = "expression/expression/sample_operator_metadata/"
CAL_BASE = "FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/"
CAL_SUPPORT = CAL_BASE + "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"

EXPECTED_EXPRESSION_SHA256 = "63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7"
EXPECTED_CALIBRATION_SHA256 = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _read_expression_metadata(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        freeze = pd.read_csv(io.BytesIO(zf.read(EXPR_FREEZE)))
        required_freeze = {"stable_key", "operator_index", "donor_id", "matrix_id", "source"}
        if not required_freeze.issubset(freeze.columns):
            raise RuntimeError(f"freeze missing columns {sorted(required_freeze - set(freeze.columns))}")
        metadata = []
        for operator_index in range(42):
            member = f"{EXPR_META_PREFIX}op{operator_index:02d}.meta.csv"
            frame = pd.read_csv(io.BytesIO(zf.read(member)))
            if not {"stable_key", "source_library"}.issubset(frame.columns):
                raise RuntimeError(f"{member} missing stable_key/source_library")
            metadata.append(frame[["stable_key", "source_library"]].copy())
    depth = pd.concat(metadata, ignore_index=True)
    if depth["stable_key"].duplicated().any():
        raise RuntimeError("stable_key duplicated across operator metadata")
    out = freeze.merge(depth, on="stable_key", how="left", validate="one_to_one")
    if out["source_library"].isna().any():
        raise RuntimeError("source_library missing after exact stable-key join")
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


def build_report(expression_zip: Path, calibration_zip: Path) -> dict:
    frame = _read_expression_metadata(expression_zip)
    states = _read_operator_states(calibration_zip)
    signatures = mask_row_sha256(states)
    state_counts = state_count_features(states)

    op = pd.DataFrame({
        "operator_index": np.arange(42, dtype=np.int64),
        "mask_signature": signatures,
        "state0_count": state_counts[:, 0],
        "state1_count": state_counts[:, 1],
        "state2_count": state_counts[:, 2],
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
        "status": NOT_ESTIMABLE,
        "reason": (
            "no independently declared technology column exists in the supplied "
            "pathology-blind 50k freeze; source is not silently relabeled as technology"
        ),
    }

    report = qualification_skeleton(input_shortcut_atlas=atlas)
    report.update({
        "artifact_kind": "PATHOLOGY_BLIND_READER_FIT_INPUT_SHORTCUT_ATLAS",
        "expression_zip_sha256": sha256_file(expression_zip),
        "calibration_zip_sha256": sha256_file(calibration_zip),
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
    parser.add_argument("--expression-zip", required=True, type=Path)
    parser.add_argument("--calibration-zip", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-expression-sha256", default=EXPECTED_EXPRESSION_SHA256)
    parser.add_argument("--expected-calibration-sha256", default=EXPECTED_CALIBRATION_SHA256)
    args = parser.parse_args()

    for path in (args.expression_zip, args.calibration_zip):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    if sha256_file(args.expression_zip) != args.expected_expression_sha256:
        raise SystemExit("expression zip SHA-256 mismatch")
    if sha256_file(args.calibration_zip) != args.expected_calibration_sha256:
        raise SystemExit("calibration zip SHA-256 mismatch")

    report = build_report(args.expression_zip, args.calibration_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_V5_REAL_READERFIT_SHORTCUT_ATLAS_V1")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
