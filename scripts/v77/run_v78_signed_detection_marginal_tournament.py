#!/usr/bin/env python3
"""V78 F0-F3 tournament contract surface.

Task-1 scope only: bind F0 to the committed E2 result, freeze F1 as a
BackgroundV2-only ablation, and reuse the proven V77 operator-support gate.
No V78 scientific arm is executed by this module yet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_v77_class_aware_fullscale_rna_observer as CLASS_OBSERVER  # noqa: E402
import run_v77_class_propagation_tournament as V77  # noqa: E402
import v77_background_v2 as BG2  # noqa: E402

ARMS = ("F0", "F1", "F2", "F3")
DEFAULT_SEED = 7302
DEFAULT_MEASUREMENT_SEED = 7302
CLASS_PROGRAM_SCALE = float(CLASS_OBSERVER.CLASS_PROGRAM_SCALE)
EXPECTED_CLASS_AUTHORITY_SHA256 = "a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014"
EXPECTED_EVALUATION_UNIVERSE_SHA256 = "e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763"
EXPECTED_E2_CELLS = 2500


def validate_arm(arm: str) -> str:
    arm = str(arm)
    if arm == "E4":
        raise PermissionError("E4 donor×class interaction remains unauthorized")
    if arm not in ARMS:
        raise ValueError(f"unknown V78 arm: {arm}")
    return arm


def arm_config(arm: str) -> dict:
    arm = validate_arm(arm)
    return {
        "arm": arm,
        "truth_arm": "E2",
        "class_scale": CLASS_PROGRAM_SCALE,
        "seed": DEFAULT_SEED,
        "measurement_seed": DEFAULT_MEASUREMENT_SEED,
        "background": "v2" if arm == "F1" else "v1",
        "signed_detection": arm in {"F2", "F3"},
        "corrected_marginals": arm == "F3",
    }


def background_v2_contract() -> dict:
    """Return the imported frozen BackgroundV2 constants; do not duplicate them."""
    return {
        "broad": dict(BG2.BROAD),
        "mid": dict(BG2.MID),
        "narrow": dict(BG2.NARROW),
        "paralog": dict(BG2.PARALOG),
    }


def load_e2_reference(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"committed E2 reference unavailable: {path}")
    rec = json.loads(path.read_text())
    failures = []
    if rec.get("schema") != "V77_CLASS_PROPAGATION_TOURNAMENT_V1":
        failures.append("schema")
    if rec.get("seed") != DEFAULT_SEED:
        failures.append("seed")
    if rec.get("cells") != EXPECTED_E2_CELLS:
        failures.append("cells")
    if rec.get("class_authority_sha256") != EXPECTED_CLASS_AUTHORITY_SHA256:
        failures.append("class_authority_sha256")
    if rec.get("evaluation_universe", {}).get("sha256") != EXPECTED_EVALUATION_UNIVERSE_SHA256:
        failures.append("evaluation_universe.sha256")
    if rec.get("fullscale_background") != "v1":
        failures.append("fullscale_background")
    if "E2" not in rec.get("results", {}) or "score" not in rec["results"]["E2"]:
        failures.append("results.E2.score")
    if failures:
        raise RuntimeError("E2 reference mismatch: " + ", ".join(failures))
    return rec


def extract_e2_score(reference: dict) -> dict:
    return reference["results"]["E2"]["score"]


def assert_f0_score_matches_reference(score: dict, reference: dict) -> None:
    expected = extract_e2_score(reference)
    if score != expected:
        raise RuntimeError("F0 score does not exactly reproduce committed E2")


def operator_support_2k() -> dict:
    return V77.operator_support_2k(DEFAULT_SEED)
