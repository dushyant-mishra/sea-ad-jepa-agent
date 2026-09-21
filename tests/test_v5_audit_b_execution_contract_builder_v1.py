from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import MaskingRngReplayAuthorityV3

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/build_full104_audit_b_execution_contract_v1_20260921.py"
SAMPLE = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_FROZEN_TARGET_SAMPLE.json"
)
ESTIMATOR = ROOT / "src/sea_ad_jepa/v5/audit_b_production_burden_v1.py"

HEAVY_SHA = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
FULL104_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
REGISTRY_SHA = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"


def write_heavy(path: Path, *, schema="V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2") -> None:
    path.write_text(
        json.dumps(
            {
                "schema": schema,
                "verdict": "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE",
                "artifact_sha256": HEAVY_SHA,
                "artifact_sha_matches_bound": True,
                "block_manifest_sha256": FULL104_SHA,
                "rows_traversed": 4_553_407,
                "donors": 104,
                "core_addresses": 17_186,
                "three_route_total_agreement": True,
                "all_104_donor_library_totals_agree": True,
                "per_cell_source_vector_agrees": True,
                "terminal_masking_outcomes_inspected": False,
                "training_authorized": False,
            }
        )
    )


def write_rng(path: Path, *, schema="V5_MASKING_RNG_REPLAY_AUTHORITY_V3") -> None:
    authority = MaskingRngReplayAuthorityV3(
        authority_id="TEST_RNG_V3",
        full104_substrate_sha256=FULL104_SHA,
        canonical_registry_sha256=REGISTRY_SHA,
        outer_split_receipt_sha256="1" * 64,
        qualification_parameters_authority_sha256="2" * 64,
        burden_ladder_authority_sha256="3" * 64,
    )
    payload = {
        "schema": schema,
        **authority.__dict__,
        "global_seed": authority.global_seed,
        "authority_sha256": authority.canonical_digest(),
        "target_panel_dependency": "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS",
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }
    path.write_text(json.dumps(payload))


def run_builder(tmp: Path, *, sample=SAMPLE, heavy_schema=None, rng_schema=None, scope=None):
    heavy = tmp / "heavy.json"
    rng = tmp / "rng.json"
    out = tmp / "contract.json"
    write_heavy(
        heavy,
        schema=heavy_schema
        or "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2",
    )
    write_rng(rng, schema=rng_schema or "V5_MASKING_RNG_REPLAY_AUTHORITY_V3")
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--sample-freeze",
        str(sample),
        "--heavy-qualification-receipt",
        str(heavy),
        "--rng-authority",
        str(rng),
        "--burden-estimator-source",
        str(ESTIMATOR),
        "--out",
        str(out),
    ]
    if scope is not None:
        cmd.extend(["--precision-scope", scope])
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    return proc, out


def test_default_builder_is_content_addressed_but_execution_forbidden(tmp_path: Path) -> None:
    proc, out = run_builder(tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    d = json.loads(out.read_text())
    assert d["precision_scope_id"] == "UNRESOLVED__EXECUTION_FORBIDDEN"
    assert d["execution_authorized"] is False
    assert len(d["contract_sha256"]) == 64
    assert d["phase_iv_sample_freeze_digest"].startswith("c2c5e1b5")
    assert d["heavy_artifact_sha256"] == HEAVY_SHA


def test_builder_rejects_phase_i_v1_receipt(tmp_path: Path) -> None:
    proc, _ = run_builder(
        tmp_path,
        heavy_schema="V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V1",
    )
    assert proc.returncode != 0
    assert "qualification V2 is required" in proc.stdout + proc.stderr


def test_builder_rejects_rng_v2(tmp_path: Path) -> None:
    proc, _ = run_builder(tmp_path, rng_schema="V5_MASKING_RNG_REPLAY_AUTHORITY_V2")
    assert proc.returncode != 0
    assert "RNG authority V3 is required" in proc.stdout + proc.stderr


def test_builder_rejects_tampered_sample_membership(tmp_path: Path) -> None:
    d = json.loads(SAMPLE.read_text())
    d["samples"]["N1"]["targets"][0] += 1
    bad = tmp_path / "tampered-sample.json"
    bad.write_text(json.dumps(d))
    proc, _ = run_builder(tmp_path, sample=bad)
    assert proc.returncode != 0
    assert "invalid internal digest" in proc.stdout + proc.stderr


def test_builder_can_only_authorize_after_an_explicit_precision_scope(tmp_path: Path) -> None:
    proc, out = run_builder(
        tmp_path,
        scope="ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    d = json.loads(out.read_text())
    assert d["execution_authorized"] is True
    assert d["precision_scope_id"] == "ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1"


def test_contract_digest_changes_with_precision_scope(tmp_path: Path) -> None:
    proc1, out1 = run_builder(tmp_path)
    assert proc1.returncode == 0
    first = json.loads(out1.read_text())["contract_sha256"]

    other = tmp_path / "second"
    other.mkdir()
    proc2, out2 = run_builder(
        other,
        scope="ALL_3_NONUNIFORM_X_6_RUNG_CELLS_V1",
    )
    assert proc2.returncode == 0
    second = json.loads(out2.read_text())["contract_sha256"]
    assert first != second
