from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v1 as D1
import td_relational_successor_disk_runner_v2 as D
import td_relational_successor_gate_v2 as G
import td_relational_successor_qualification_runner_v2 as Q
import td_relational_successor_readiness_v2 as R
import td_relational_successor_synthetic_adapter_v2 as A
import td_test_qualification_package_v2 as P


def _authority_binding():
    return {
        "synthetic_world_generation_authorized": False,
        "synthetic_world_regeneration_authorized": False,
        "qualification_model_fitting_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _write_fit(path: Path, challenge_index: int, n: int = 3):
    z = np.zeros((n, 512), dtype=np.float32)
    x = np.zeros((n, 512), dtype=np.float32)
    y = np.zeros((n, 512), dtype=np.float32)
    measured = np.ones((n, 512), dtype=bool)
    control_ids = np.asarray([f"c{challenge_index}-{j}" for j in range(A.OPAQUE_CONTROL_PROFILE_COUNT)], dtype="U16")
    np.savez(
        path,
        source=np.asarray("SYN", dtype="U8"), panel_id=np.asarray("P0", dtype="U8"),
        z_values=z, x_values=x, y_values=y,
        z_measured=measured, x_measured=measured, y_measured=measured,
        z_feature_ids=np.asarray([f"Z{i:04d}" for i in range(512)], dtype="U8"),
        x_feature_ids=np.asarray([f"X{i:04d}" for i in range(512)], dtype="U8"),
        y_feature_ids=np.asarray([f"Y{i:04d}" for i in range(512)], dtype="U8"),
        donor_ids=np.asarray(["D0"] * n, dtype="U8"),
        operator_ids=np.asarray(["O0"] * n, dtype="U8"),
        global_rows=np.arange(challenge_index * 100, challenge_index * 100 + n, dtype=np.int64),
        source_library=np.full(n, 1000.0, dtype=np.float64),
        detected_genes=np.full(n, 512, dtype=np.int64),
        focal_mask=np.ones(n, dtype=bool), neighbor_pool_mask=np.ones(n, dtype=bool),
        min_focal_anchors_per_donor=np.asarray(1, dtype=np.int64),
        control_ids=control_ids,
        control_focal_masks=np.ones((A.OPAQUE_CONTROL_PROFILE_COUNT, n), dtype=bool),
        control_neighbor_pool_masks=np.ones((A.OPAQUE_CONTROL_PROFILE_COUNT, n), dtype=bool),
        control_min_focal_anchors_per_donor=np.ones(A.OPAQUE_CONTROL_PROFILE_COUNT, dtype=np.int64),
    )


def test_v2_disk_preflight_authenticates_nine_opaque_npz_without_semantics(tmp_path):
    fit_dir = tmp_path / "fit"
    fit_dir.mkdir()
    fit_views = []
    for i in range(9):
        scratch = fit_dir / f"scratch-{i}.npz"
        _write_fit(scratch, i)
        sha = hashlib.sha256(scratch.read_bytes()).hexdigest()
        final = fit_dir / f"{sha}.npz"
        scratch.rename(final)
        fit_views.append({"challenge_id": f"opaque-{i:02d}", "sha256": sha})
    binding = {
        "schema": P.EXPECTED_SCHEMA,
        "package_id": "pkg-v2",
        "package_sha256": "a" * 64,
        "controller_truth_sha256": "b" * 64,
        "fit_view_fields": sorted(D1.FIT_VIEW_NPZ_FIELDS),
        "fit_views": fit_views,
        "authority": _authority_binding(),
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    package, adapter, receipt = D.preflight_disk_package(
        binding_path=binding_path,
        fit_dir=fit_dir,
        authenticated_package_sha256="a" * 64,
    )
    assert package.package_id == "pkg-v2"
    assert not hasattr(package, "capabilities")
    assert adapter.status == "READY"
    assert set(adapter.fit_inputs) == {f"opaque-{i:02d}" for i in range(9)}
    assert all(len(fit["control_profiles"]) == A.OPAQUE_CONTROL_PROFILE_COUNT for fit in adapter.fit_inputs.values())
    assert receipt["status"] == "READY_TO_EXECUTE_BLIND_FIT"
    assert receipt["authority"]["biological_qualification_executed"] is False


def _scale(label, status, obs=.72, null=.55):
    a, b = map(int, label.split("/"))
    if status == "NOT_ESTIMABLE":
        obs = null = None
    return G.ScaleResult(label, a, b, status, status, obs, null, 5, {}, {}, tuple([.5] * 64), 64,
                         tuple(f"D{i}" for i in range(5)))


def _profile(pid, kind):
    statuses = {label: "FAIL" for label in G.SCALE_LABELS}
    if kind == "broad": statuses["1/2"] = "PASS"
    elif kind in {"fine", "rare"}: statuses["1/4"] = "PASS"
    elif kind == "stress": statuses["1/2"] = "PASS"
    elif kind == "under": statuses = {label: "NOT_ESTIMABLE" for label in G.SCALE_LABELS}
    results = {label: _scale(label, statuses[label], .78 if kind == "rare" and statuses[label] == "PASS" else .72, .55)
               for label in G.SCALE_LABELS}
    return G.RelationalProfileReceipt("S", "P0", pid, results, tuple(), 20,
                                      "SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
                                      {k: False for k in ("target_selection_authorized", "td60_authorized", "stage4_authorized", "training_authorized")})


def _control(pid, high=False):
    results = {label: _scale(label, "PASS" if label == "1/4" else "FAIL",
                             .82 if high and label == "1/4" else (.60 if label == "1/4" else .50), .55)
               for label in G.SCALE_LABELS}
    return G.RelationalProfileReceipt("S", "P0", pid, results, tuple(), 20,
                                      "SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
                                      {k: False for k in ("target_selection_authorized", "td60_authorized", "stage4_authorized", "training_authorized")})


def _semantic(cap):
    if cap == "REL_SOURCE_VISIBILITY_STRESS": return "STRESS_TRUTH"
    if cap in {"REL_TECHNICAL_TWIN_NEGATIVE", "REL_NULL_NEGATIVE"}: return "NEGATIVE_TRUTH"
    if cap == "REL_UNDERPOWERED_POSITIVE": return "UNDERIDENTIFIED_TRUTH"
    return "POSITIVE_TRUTH"


def test_v2_controller_semantics_remain_postfit_and_qualify_expected_behavior():
    fit_views = {f"opaque-{i:02d}": f"{i + 1:064x}"[-64:] for i in range(9)}
    profiles = {}
    controls = {}
    claims = {}
    roles = Q.MANDATORY_CONTROL_ROLES
    for i, cap in enumerate(A.MANDATORY_RELATIONAL_CAPABILITIES):
        cid = f"opaque-{i:02d}"
        if cap == "REL_BROAD_MESO_POSITIVE": kind = "broad"
        elif cap == "REL_FINE_RECURRENT_POSITIVE": kind = "fine"
        elif cap in {"REL_RARE_LOCAL_ISLAND_POSITIVE", "REL_MULTI_ISLAND_POSITIVE", "REL_DONOR_RESTRICTED_POSITIVE"}: kind = "rare"
        elif cap == "REL_SOURCE_VISIBILITY_STRESS": kind = "stress"
        elif cap == "REL_UNDERPOWERED_POSITIVE": kind = "under"
        else: kind = "null"
        profiles[cid] = _profile(cid, kind)
        controls[cid] = {}
        role_map = {}
        for j, role in enumerate(roles):
            control_id = f"c{i}-{j}"
            controls[cid][control_id] = _control(control_id, high=(cap == "REL_TECHNICAL_TWIN_NEGATIVE"))
            if cap in Q.RARE_CONTROL_CAPABILITIES:
                role_map[role] = [control_id]
        claims[cap] = {
            "challenge_id": cid,
            "semantic_class": _semantic(cap),
            "control_roles": role_map,
            "expected_status": "PASS" if cap == "REL_SOURCE_VISIBILITY_STRESS" else None,
        }
    manifest = {
        "schema": Q.CONTROLLER_SCHEMA,
        "package_sha256": "a" * 64,
        "claims": claims,
        "authority": {key: False for key in Q.CONTROLLER_AUTHORITY_KEYS},
    }
    package = P.ValidatedExternalPackage("pkg", "a" * 64, fit_views, Q.canonical_sha256(manifest), tuple())
    fit = Q.BlindedFitReceipt("pkg", "a" * 64, profiles, controls,
                              {key: False for key in sorted(Q.RUN_AUTHORITY_KEYS)})
    binding = {
        "qualified_gate_executor_sha256": "1" * 64,
        "estimand_sha256": "2" * 64,
        "decision_rule_sha256": "3" * 64,
        "failure_scope": "TEST_QUALIFICATION_ONLY",
        "required_capabilities": list(A.MANDATORY_RELATIONAL_CAPABILITIES),
    }
    receipt = Q.adjudicate_blinded_qualification(
        package=package, fit_receipt=fit, controller_manifest=manifest, gate_binding=binding
    )
    assert receipt.status == "QUALIFIED"
    assert receipt.capability_statuses["REL_TECHNICAL_TWIN_NEGATIVE"] == "FAIL"
    assert receipt.capability_statuses["REL_NULL_NEGATIVE"] == "FAIL"
    assert receipt.capability_statuses["REL_UNDERPOWERED_POSITIVE"] == "NOT_ESTIMABLE"


def test_v2_readiness_never_authorizes_real_execution():
    binding = R.build_relational_gate_binding(ROOT)
    blocked = R.assess_relational_successor_readiness(
        binding=binding, external_package_present=False, qualification_receipt=None
    )
    assert blocked.real_execution_authorized is False
    ref = R.MinimalQualificationReference(
        "QUALIFIED", "a" * 64,
        binding["qualified_gate_executor_sha256"], binding["estimand_sha256"], binding["decision_rule_sha256"],
    )
    ready = R.assess_relational_successor_readiness(
        binding=binding, external_package_present=True, qualification_receipt=ref
    )
    assert ready.status == "READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY"
    assert ready.real_execution_authorized is False
    assert all(value is False for value in ready.authority.values())
