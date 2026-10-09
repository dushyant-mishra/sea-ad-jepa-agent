#!/usr/bin/env python3
"""V78 F0-F3 tournament contract and fail-closed execution gate.

This module binds F0 to the committed E2 result, freezes F1 as a BackgroundV2-only
ablation, reuses the proven V77 operator-support gate, and refuses scientific execution
until the canonical F3 authority is backed by the exact corrected S174 TRAIN cache bytes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import build_v77_class_aware_fullscale_rna_observer as CLASS_OBSERVER  # noqa: E402
import build_v78_marginal_authority as MARGINAL  # noqa: E402
import run_v77_class_propagation_tournament as V77  # noqa: E402
import v77_background_v2 as BG2  # noqa: E402

ARMS = ("F0", "F1", "F2", "F3")
DEFAULT_SEED = 7302
DEFAULT_MEASUREMENT_SEED = 7302
CLASS_PROGRAM_SCALE = float(CLASS_OBSERVER.CLASS_PROGRAM_SCALE)
EXPECTED_CLASS_AUTHORITY_SHA256 = "a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014"
EXPECTED_EVALUATION_UNIVERSE_SHA256 = "e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763"
EXPECTED_E2_CELLS = 2500
EXPECTED_CORRECTED_TRAIN_CELLS = 4726
CORRECTED_CALIBRATION = ROOT / "results" / "v77" / "s174_replay" / "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1.json"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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
    if json.dumps(score, sort_keys=True, allow_nan=True) != json.dumps(expected, sort_keys=True, allow_nan=True):
        raise RuntimeError("F0 score does not exactly reproduce committed E2")


def operator_support_2k() -> dict:
    return V77.operator_support_2k(DEFAULT_SEED)


def _authenticate_corrected_cache(cache_root: Path) -> tuple[bool, dict]:
    """Authenticate corrected count shards and require paired metadata shards.

    The committed corrected calibration records the exact 42 count-shard digests. Metadata
    shards are also required physically because F3 depth strata are cell-level. Paired meta
    digests are authenticated during canonical marginal-authority construction against the
    frozen production loader manifest and are explicitly bound in that authority receipt.
    """
    cache_root = Path(cache_root)
    if not cache_root.is_dir() or not CORRECTED_CALIBRATION.exists():
        return False, {"reason": "cache_or_calibration_unavailable"}
    cal = json.loads(CORRECTED_CALIBRATION.read_text())
    rows = cal.get("source", {}).get("shard_digests", [])
    if len(rows) != 42:
        return False, {"reason": "corrected_calibration_shard_receipt_invalid"}
    verified = []
    for row in rows:
        name = Path(str(row.get("file", ""))).name
        expected = str(row.get("sha256", ""))
        count_path = cache_root / name
        stem = name.removesuffix(".counts.npz")
        meta_path = cache_root / f"{stem}.meta.npz"
        if not count_path.is_file() or not meta_path.is_file():
            return False, {"reason": "corrected_shard_bytes_missing", "missing_stem": stem}
        actual = _sha256_file(count_path)
        if actual != expected:
            return False, {"reason": "corrected_count_digest_mismatch", "stem": stem,
                           "expected": expected, "actual": actual}
        verified.append(stem)
    return True, {"n_count_shards": len(verified), "n_meta_shards": len(verified),
                  "stems": sorted(verified)}


def preexecution_gate(e2_reference: Path, operator_bridge: Path,
                      marginal_authority: Path, corrected_cache_root: Path) -> dict:
    """Return a non-authorizing V78 scientific execution gate receipt.

    F0-F2 are not allowed to run early: the preregistered causal tournament is one frozen
    F0→F1→F2→F3 experiment, and the gate must be fully READY before any scientific arm runs.
    """
    blockers: list[str] = []
    details: dict = {}
    bridge_rec = None

    try:
        ref = load_e2_reference(Path(e2_reference))
        details["e2_reference"] = {
            "status": "AUTHENTICATED",
            "seed": ref["seed"],
            "class_authority_sha256": ref["class_authority_sha256"],
            "evaluation_universe_sha256": ref["evaluation_universe"]["sha256"],
        }
    except Exception as exc:
        blockers.append("committed_e2_reference")
        details["e2_reference"] = {"status": "FAILED", "reason": str(exc)}

    try:
        bridge_path = Path(operator_bridge)
        if not bridge_path.is_file():
            raise FileNotFoundError(str(bridge_path))
        bridge = json.loads(bridge_path.read_text())
        bridge_rec = MARGINAL.validate_operator_bridge(bridge)
        details["operator_bridge"] = {"status": "AUTHENTICATED", **bridge_rec}
    except Exception as exc:
        blockers.append("s174_shard_operator_bridge")
        details["operator_bridge"] = {"status": "FAILED", "reason": str(exc)}

    authority_path = Path(marginal_authority)
    if not authority_path.is_file():
        blockers.append("canonical_f3_marginal_authority")
        details["marginal_authority"] = {"status": "MISSING"}
    else:
        try:
            authority = json.loads(authority_path.read_text())
            MARGINAL.validate_runtime_authority(authority)
            canonical = authority.get("canonical_corrected_train") is True
            training_flag = authority.get("training_authorized") is True
            source = authority.get("source", {})
            provenance_checks = {
                "n_shards_42": int(source.get("n_shards", -1)) == MARGINAL.EXPECTED_N_SHARDS,
                "n_cells_4726": int(source.get("n_cells", -1)) == EXPECTED_CORRECTED_TRAIN_CELLS,
                "registry_sha256": source.get("registry_sha256") == MARGINAL.EXPECTED_REGISTRY_SHA256,
                "loader_manifest_sha256": source.get("loader_manifest_sha256") == MARGINAL.EXPECTED_LOADER_MANIFEST_SHA256,
                "paired_meta_manifest_verified": source.get("paired_meta_manifest_verified") is True,
                "operator_bridge_sha256": bridge_rec is not None and source.get("operator_bridge_sha256") == bridge_rec.get("bridge_sha256"),
            }
            provenance_ok = all(provenance_checks.values())
            if not canonical or not provenance_ok:
                blockers.append("canonical_f3_marginal_authority")
            if training_flag:
                blockers.append("training_authorization_contamination")
            details["marginal_authority"] = {
                "status": "AUTHENTICATED" if canonical and provenance_ok and not training_flag else "REJECTED",
                "sha256": _sha256_file(authority_path),
                "canonical_corrected_train": canonical,
                "training_authorized": training_flag,
                "provenance_checks": provenance_checks,
            }
        except Exception as exc:
            blockers.append("canonical_f3_marginal_authority")
            details["marginal_authority"] = {"status": "FAILED", "reason": str(exc)}

    cache_ok, cache_rec = _authenticate_corrected_cache(Path(corrected_cache_root))
    details["corrected_train_cache"] = {
        "status": "AUTHENTICATED" if cache_ok else "FAILED", **cache_rec
    }
    if not cache_ok:
        blockers.append("authenticated_corrected_train_cache_bytes")

    support = operator_support_2k()
    support_ok = support["operators_present"] == 42 and support["minimum_operator_count"] >= 1
    details["operator_support_2k"] = {"status": "PASS" if support_ok else "FAIL", **support}
    if not support_ok:
        blockers.append("operator_support_2k")

    blockers = sorted(set(blockers))
    return {
        "schema": "V78_PREEXECUTION_GATE_V1",
        "status": "READY" if not blockers else "BLOCKED",
        "blockers": blockers,
        "details": details,
        "f0_f2_early_execution_authorized": False,
        "training_authorized": False,
        "post_outcome_retuning_authorized": False,
        "e4_authorized": False,
    }


def require_execution_authority(gate_receipt: dict) -> None:
    if gate_receipt.get("status") != "READY" or gate_receipt.get("blockers"):
        raise PermissionError(
            "V78 scientific execution is blocked: " + ", ".join(gate_receipt.get("blockers", []))
        )
