from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v3 as D3
import td_relational_successor_gate_v2 as G
import td_relational_successor_qualification_runner_v2 as Q2
import td_relational_successor_qualification_runner_v3 as Q3
import td_relational_successor_synthetic_adapter_v2 as A
import td_test_qualification_package_v2 as P


def _binding_authority():
    return {
        "synthetic_world_generation_authorized": False,
        "synthetic_world_regeneration_authorized": False,
        "qualification_model_fitting_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _controller_authority():
    return {key: False for key in Q2.CONTROLLER_AUTHORITY_KEYS}


def _semantic(capability: str) -> str:
    if capability == "REL_SOURCE_VISIBILITY_STRESS":
        return "STRESS_TRUTH"
    if capability in {"REL_TECHNICAL_TWIN_NEGATIVE", "REL_NULL_NEGATIVE"}:
        return "NEGATIVE_TRUTH"
    if capability == "REL_UNDERPOWERED_POSITIVE":
        return "UNDERIDENTIFIED_TRUTH"
    return "POSITIVE_TRUTH"


def _claims():
    claims = {}
    for i, capability in enumerate(A.MANDATORY_RELATIONAL_CAPABILITIES):
        cid = f"q-{i:02d}-a91f"
        roles = {}
        if capability in Q2.RARE_CONTROL_CAPABILITIES:
            for j, role in enumerate(Q2.MANDATORY_CONTROL_ROLES):
                roles[role] = [f"c-{i:02d}-{j:02d}-b27"]
        claims[capability] = {
            "challenge_id": cid,
            "semantic_class": _semantic(capability),
            "control_roles": roles,
            "expected_status": "PASS" if capability == "REL_SOURCE_VISIBILITY_STRESS" else None,
        }
    return claims


def _manifest(nonce: str = "7a" * 32):
    return {
        "schema": Q3.CONTROLLER_SCHEMA,
        "package_sha256": "a" * 64,
        "blind_nonce": nonce,
        "claims": _claims(),
        "authority": _controller_authority(),
    }


def _package(manifest):
    fit_views = {
        claim["challenge_id"]: f"{i + 1:064x}"[-64:]
        for i, claim in enumerate(manifest["claims"].values())
    }
    return P.ValidatedExternalPackage(
        package_id="pkg-v3",
        package_sha256="a" * 64,
        fit_views=fit_views,
        controller_truth_sha256=Q3.canonical_sha256(manifest),
        fit_view_fields=("x",),
    )


def test_v3_controller_commitment_requires_controller_only_256_bit_nonce():
    manifest = _manifest()
    package = _package(manifest)
    normalized = Q3.validate_controller_manifest_v3(package, manifest)
    assert tuple(normalized) == A.MANDATORY_RELATIONAL_CAPABILITIES

    bad = dict(manifest)
    bad["blind_nonce"] = "abcd"
    bad_package = _package(bad)
    with pytest.raises(Q3.QualificationRunnerV3Error, match="blind_nonce"):
        Q3.validate_controller_manifest_v3(bad_package, bad)


def test_v3_nonce_makes_same_semantics_commit_to_different_hashes():
    first = _manifest("11" * 32)
    second = _manifest("22" * 32)
    assert first["claims"] == second["claims"]
    assert Q3.canonical_sha256(first) != Q3.canonical_sha256(second)


def test_phase1_api_has_no_controller_parameter():
    params = set(inspect.signature(D3.run_blinded_fit_phase).parameters)
    assert "controller_manifest_path" not in params
    assert "controller_manifest" not in params
    assert "controller" not in params


def test_all_output_modes_reject_writing_inside_fit_custody(tmp_path):
    fit_dir = tmp_path / "fit"
    fit_dir.mkdir()
    with pytest.raises(D3.DiskRunnerV3Error, match="fit custody"):
        D3._guard_new_output(fit_dir / "receipt.json", fit_dir=fit_dir)


def test_existing_output_is_never_overwritten(tmp_path):
    output = tmp_path / "receipt.json"
    output.write_text("spent", encoding="utf-8")
    with pytest.raises(D3.DiskRunnerV3Error, match="already exists"):
        D3._guard_new_output(output)


def test_wrong_blinded_hash_stops_before_controller_truth_read(tmp_path, monkeypatch):
    fit_dir = tmp_path / "fit"
    fit_dir.mkdir()
    manifest = _manifest()
    package = _package(manifest)
    binding = {
        "schema": P.EXPECTED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "controller_truth_sha256": package.controller_truth_sha256,
        "fit_view_fields": ["source"],
        "fit_views": [
            {"challenge_id": cid, "sha256": sha}
            for cid, sha in package.fit_views.items()
        ],
        "authority": _binding_authority(),
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    blind = tmp_path / "blinded.json"
    blind.write_text("{}", encoding="utf-8")
    controller = tmp_path / "controller.json"
    controller.write_text(json.dumps(manifest), encoding="utf-8")

    called = {"controller": False}

    def forbidden_read(_):
        called["controller"] = True
        raise AssertionError("controller truth must remain closed")

    monkeypatch.setattr(D3, "_read_controller_json", forbidden_read)
    with pytest.raises(D3.DiskRunnerV3Error, match="blinded receipt SHA-256 mismatch"):
        D3.adjudicate_frozen_blinded_phase(
            repo_root=ROOT,
            binding_path=binding_path,
            fit_dir=fit_dir,
            authenticated_package_sha256="a" * 64,
            blinded_receipt_path=blind,
            expected_blinded_receipt_sha256="0" * 64,
            controller_manifest_path=controller,
            output_path=tmp_path / "final.json",
        )
    assert called["controller"] is False


def _scale(label: str) -> G.ScaleResult:
    a, b = map(int, label.split("/"))
    return G.ScaleResult(
        scale_label=label,
        numerator=a,
        denominator=b,
        status="FAIL",
        reason="RELATION_NOT_ESTABLISHED",
        observed_statistic=0.5,
        family_null_p95=0.6,
        n_observed_donors=5,
        observed_donor_agreements={f"D{i}": 0.5 for i in range(5)},
        observed_resolved_relations={f"D{i}": 20 for i in range(5)},
        null_source_statistics=tuple([0.5] * 64),
        n_sampled_triplets=320,
        eligible_donors=tuple(f"D{i}" for i in range(5)),
    )


def _profile(profile_id: str) -> G.RelationalProfileReceipt:
    return G.RelationalProfileReceipt(
        source="S0",
        panel_id="P0",
        profile_id=profile_id,
        scale_results={label: _scale(label) for label in G.SCALE_LABELS},
        characterization=("NO_RELATION_ESTABLISHED",),
        focal_anchor_count=40,
        failure_scope="SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
        authority={
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    )


def test_frozen_blinded_json_roundtrips_back_to_exact_receipt_shape():
    manifest = _manifest()
    package = _package(manifest)
    profiles = {cid: _profile(cid) for cid in package.fit_views}
    controls = {
        cid: {f"c-{j}": _profile(f"{cid}::c-{j}") for j in range(5)}
        for cid in package.fit_views
    }
    fit = Q2.BlindedFitReceipt(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        profiles=profiles,
        controls=controls,
        authority={key: False for key in sorted(Q2.RUN_AUTHORITY_KEYS)},
    )
    document = {
        "schema": D3.BLINDED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "fit_receipt": D3._jsonable(fit),
        "authority": {**D3._PHASE_AUTHORITY, "controller_truth_opened": False},
    }
    restored = D3._fit_receipt_from_document(document, package)
    assert restored == fit


def test_blinded_receipt_hash_is_byte_identity_not_json_semantic_identity(tmp_path):
    path = tmp_path / "blind.json"
    path.write_bytes(b'{"a":1}\n')
    first = D3._sha256_file(path)
    path.write_bytes(b'{ "a" : 1 }\n')
    second = D3._sha256_file(path)
    assert first != second
    assert first == hashlib.sha256(b'{"a":1}\n').hexdigest()
