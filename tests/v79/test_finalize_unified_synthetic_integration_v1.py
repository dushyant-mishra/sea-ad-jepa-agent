from __future__ import annotations
from pathlib import Path
import json, tempfile
from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology
from scripts.v79.unified_synthetic_fit_view_v1 import UnifiedObservationConfig, observe_unified_world, fit_view_sha256
from scripts.v79.unified_synthetic_controller_truth_v1 import derive_controller_truth, controller_truth_sha256
from scripts.v79.finalize_unified_synthetic_integration_v1 import build_integration_receipt, write_integration_receipt_once

MANIFEST = Path("results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json")


def _receipt(*, n_cells=120, n_genes=24, n_donors=8, world_seed=31, obs_seed=32):
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=n_cells,n_genes=n_genes,n_donors=n_donors),seed=world_seed)
    f=observe_unified_world(w,UnifiedObservationConfig(),seed=obs_seed)
    c=derive_controller_truth(w)
    r=build_integration_receipt(world=w,fit_view=f,controller_truth=c,repo_root=Path.cwd(),integration_manifest_path=MANIFEST)
    return w,f,c,r


def test_receipt_binds_fit_controller_manifest_and_source_bytes_with_authority_off():
    w,f,c,r=_receipt(n_cells=240,n_genes=32,n_donors=12,world_seed=21,obs_seed=22)
    assert r["world_sha256"] == w.world_hash
    assert r["fit_view_sha256"] == fit_view_sha256(f)
    assert r["controller_truth_sha256"] == controller_truth_sha256(c)
    assert len(r["integration_manifest_sha256"]) == 64
    assert set(r["integration_source_sha256"]) == {
        "scripts/v79/unified_synthetic_integration_v1.py",
        "scripts/v79/unified_synthetic_fit_view_v1.py",
        "scripts/v79/unified_synthetic_controller_truth_v1.py",
        "scripts/v79/finalize_unified_synthetic_integration_v1.py",
    }
    assert all(len(x) == 64 for x in r["integration_source_sha256"].values())
    assert r["synthetic_package_sha256"] != r["controller_truth_sha256"]
    assert r["calibration"] == {
        "stat1_50k_physical_row_status": "QUARANTINED_NOT_HARD_AUTHORITY",
        "rare_frequency_source": "SYNTHETIC_STRESS_PRESETS_NOT_EMPIRICAL_CALIBRATION",
    }
    assert not any(r["authority"].values())


def test_receipt_refuses_manifest_that_relabels_quarantined_frequency_as_empirical(tmp_path):
    manifest=json.loads(MANIFEST.read_text())
    manifest["calibration"]["rare_frequency_source"]="EMPIRICAL_HUMAN_CALIBRATION"
    bad=tmp_path/"manifest.json"
    bad.write_text(json.dumps(manifest), encoding="utf-8")
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=120,n_genes=24,n_donors=8),seed=31)
    f=observe_unified_world(w,UnifiedObservationConfig(),seed=32)
    c=derive_controller_truth(w)
    try:
        build_integration_receipt(world=w,fit_view=f,controller_truth=c,repo_root=Path.cwd(),integration_manifest_path=bad)
    except ValueError as exc:
        assert "calibration" in str(exc)
    else:
        raise AssertionError("empirical relabeling of quarantined rarity calibration was accepted")


def test_receipt_is_write_once():
    _,_,_,r=_receipt()
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"receipt.json"; write_integration_receipt_once(p,r)
        assert json.loads(p.read_text())["synthetic_package_sha256"] == r["synthetic_package_sha256"]
        try:
            write_integration_receipt_once(p,r)
        except ValueError:
            pass
        else:
            raise AssertionError("write-once receipt was overwritten")


def test_fit_package_enters_existing_post_td_preflight_without_authority_escalation():
    from scripts.v5.jepa_post_td_harness_contract_v1 import (
        build_target_portfolio, build_architecture_plan, build_synthetic_rehearsal_preflight,
    )
    _,_,_,receipt=_receipt(world_seed=41,obs_seed=42)
    portfolio=build_target_portfolio(selected_candidate="C1", qualifications={"C1":"PASS"})
    architecture=build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=1000)
    with tempfile.TemporaryDirectory() as td:
        preflight=build_synthetic_rehearsal_preflight(
            repo_root=Path.cwd(), portfolio=portfolio, architecture_plan=architecture,
            synthetic_package_sha256=receipt["synthetic_package_sha256"], output_root=Path(td),
        )
    assert preflight["status"] == "READY_FOR_SYNTHETIC_REHEARSAL_ONLY"
    assert not any(preflight["authority"].values())
