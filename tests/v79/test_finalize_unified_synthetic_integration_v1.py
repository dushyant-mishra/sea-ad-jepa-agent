from __future__ import annotations
from pathlib import Path
import json, tempfile
from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology
from scripts.v79.unified_synthetic_fit_view_v1 import UnifiedObservationConfig, observe_unified_world, serialize_fit_view, fit_view_sha256
from scripts.v79.unified_synthetic_controller_truth_v1 import derive_controller_truth, controller_truth_sha256
from scripts.v79.finalize_unified_synthetic_integration_v1 import build_integration_receipt, write_integration_receipt_once


def test_receipt_binds_fit_and_controller_separately_with_authority_off():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=240,n_genes=32,n_donors=12),seed=21)
    f=observe_unified_world(w,UnifiedObservationConfig(),seed=22)
    c=derive_controller_truth(w)
    r=build_integration_receipt(world=w,fit_view=f,controller_truth=c)
    assert r["world_sha256"] == w.world_hash
    assert r["fit_view_sha256"] == fit_view_sha256(f)
    assert r["controller_truth_sha256"] == controller_truth_sha256(c)
    assert r["synthetic_package_sha256"] != r["controller_truth_sha256"]
    assert not any(r["authority"].values())


def test_receipt_is_write_once():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=120,n_genes=24,n_donors=8),seed=31)
    f=observe_unified_world(w,UnifiedObservationConfig(),seed=32)
    c=derive_controller_truth(w); r=build_integration_receipt(world=w,fit_view=f,controller_truth=c)
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
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=120,n_genes=24,n_donors=8),seed=41)
    f=observe_unified_world(w,UnifiedObservationConfig(),seed=42)
    c=derive_controller_truth(w)
    receipt=build_integration_receipt(world=w,fit_view=f,controller_truth=c)
    portfolio=build_target_portfolio(selected_candidate="C1", qualifications={"C1":"PASS"})
    architecture=build_architecture_plan(portfolio=portfolio, ema_half_life_presentations=1000)
    with tempfile.TemporaryDirectory() as td:
        preflight=build_synthetic_rehearsal_preflight(
            repo_root=Path.cwd(), portfolio=portfolio, architecture_plan=architecture,
            synthetic_package_sha256=receipt["synthetic_package_sha256"], output_root=Path(td),
        )
    assert preflight["status"] == "READY_FOR_SYNTHETIC_REHEARSAL_ONLY"
    assert not any(preflight["authority"].values())
