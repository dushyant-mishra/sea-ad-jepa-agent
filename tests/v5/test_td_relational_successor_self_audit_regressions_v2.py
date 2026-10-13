from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v2 as D
import td_relational_successor_gate_v2 as G
import td_test_qualification_package_v2 as P


def _blind_binding() -> dict:
    return {
        "schema": "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2",
        "package_id": "opaque-known-truth-v2",
        "package_sha256": "a" * 64,
        "fit_views": [
            {"challenge_id": f"opaque-{i:02d}", "sha256": f"{i:x}" * 64}
            for i in range(1, 10)
        ],
        "controller_truth_sha256": "b" * 64,
        "fit_view_fields": ["observations", "support", "donor_id", "operator_id", "entity_id"],
        "authority": {
            "synthetic_world_generation_authorized": False,
            "synthetic_world_regeneration_authorized": False,
            "qualification_model_fitting_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }


def test_pre_fit_binding_contains_no_capability_or_semantic_mapping():
    package = P.validate_external_package_binding(_blind_binding(), authenticated_package_sha256="a" * 64)
    assert not hasattr(package, "capabilities")

    leaked = _blind_binding()
    leaked["capabilities"] = [{
        "capability_id": "REL_NULL_NEGATIVE",
        "challenge_id": "opaque-01",
        "semantic_class": "NEGATIVE_TRUTH",
    }]
    with pytest.raises(P.PackageBindingError, match="controller-only|schema"):
        P.validate_external_package_binding(leaked, authenticated_package_sha256="a" * 64)


def test_x_resolved_triplets_are_filtered_before_hash_cap():
    n = 35
    z = np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]).astype(float)
    x = z.copy()
    x[0, 14:18] = np.nan
    x[14:18, 0] = np.nan
    donors = np.asarray(["D0"] * n, dtype=object)
    operators = np.asarray(["OP0"] * n, dtype=object)
    rows = np.arange(n, dtype=np.int64)
    focal = np.zeros(n, dtype=bool)
    focal[0] = True
    pool = np.ones(n, dtype=bool)

    _, by_donor, ntrip = G._build_scale_population(
        source="S", panel_id="P0", scale=(1, 2), z=z, x=x,
        donors=donors, operators=operators, rows=rows, focal=focal, pool=pool,
        min_focal_anchors_per_donor=1,
    )
    triplets = by_donor.get("D0", [])
    assert ntrip == 64
    assert len(triplets) == 64
    assert all(G._order_sign(x[i, j], x[i, k]) is not None for i, j, k in triplets)


def test_blinded_fit_receipt_is_durably_written_before_controller_truth_opens(monkeypatch, tmp_path):
    events = []
    binding_path = tmp_path / "binding.json"
    controller_path = tmp_path / "controller.json"
    output_path = tmp_path / "receipt.json"
    binding_path.write_text("{}", encoding="utf-8")
    controller_path.write_text("{}", encoding="utf-8")

    def fake_read_json(path):
        p = Path(path)
        if p == binding_path:
            events.append("binding_open")
            return {"binding": "stub"}
        if p == controller_path:
            events.append("controller_open")
            assert "blinded_fit_write" in events
            return {"controller": "stub"}
        raise AssertionError(p)

    package = SimpleNamespace(package_id="pkg", package_sha256="a" * 64, fit_views={})
    adapter = SimpleNamespace(status="READY")
    fit_receipt = SimpleNamespace(package_id="pkg", package_sha256="a" * 64, profiles={}, controls={}, authority={})
    qualification = SimpleNamespace(status="QUALIFIED")
    readiness = SimpleNamespace(status="READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY")

    monkeypatch.setattr(D.D1, "_read_json", fake_read_json)
    monkeypatch.setattr(D.P, "validate_external_package_binding", lambda *a, **k: package)
    monkeypatch.setattr(D, "load_authenticated_fit_payloads", lambda *a, **k: {})
    monkeypatch.setattr(D.A, "build_relational_qualification_adapter", lambda *a, **k: adapter)
    monkeypatch.setattr(D.Q, "execute_blinded_fit", lambda *a, **k: fit_receipt)
    monkeypatch.setattr(D.R, "build_relational_gate_binding", lambda *a, **k: {"gate": "binding"})
    monkeypatch.setattr(D.Q, "adjudicate_blinded_qualification", lambda **k: qualification)
    monkeypatch.setattr(D.R, "assess_relational_successor_readiness", lambda **k: readiness)
    monkeypatch.setattr(D, "_sha256_file", lambda *a, **k: "c" * 64)

    def fake_write(path, value):
        if str(path).endswith(".blinded_fit.json"):
            events.append("blinded_fit_write")
        else:
            events.append("final_write")
    monkeypatch.setattr(D, "_write_json_durable", fake_write)

    D.run_disk_qualification(
        repo_root=ROOT,
        binding_path=binding_path,
        fit_dir=tmp_path,
        controller_manifest_path=controller_path,
        authenticated_package_sha256="a" * 64,
        output_path=output_path,
    )
    assert events.index("blinded_fit_write") < events.index("controller_open") < events.index("final_write")
