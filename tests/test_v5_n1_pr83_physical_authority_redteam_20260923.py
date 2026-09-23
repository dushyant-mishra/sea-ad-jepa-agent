"""Independent fail-closed review of PR83's physical N1 authority boundary.

All bytes in these tests are deliberately SYNTHETIC fixtures; fixture roots are
monkeypatched *only inside the tests*. They are not physical qualification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5 import audit_b_n1_physical_lineage_adapter_v1 as gate


def _fixture(tmp_path: Path, monkeypatch):
    contents = {
        "corrected_derivative": b"corrected-synthetic-NPZ-fixture",
        "pass1_whole_file": b"synthetic-pass1-NPZ-fixture",
        "full104_level4_manifest": b"synthetic-Level4-manifest",
        "split_receipt": json.dumps({
            "receipt_sha256": "c" * 64,
            "pass1_npz_sha256": hashlib.sha256(
                b"synthetic-pass1-NPZ-fixture"
            ).hexdigest(),
        }, sort_keys=True).encode(),
        "per_member_manifest": json.dumps({
            "derivative_sha256": hashlib.sha256(
                b"corrected-synthetic-NPZ-fixture"
            ).hexdigest(),
            "members_total": 35, "members_changed": 2,
        }, sort_keys=True).encode(),
        "v2_preflight_receipt": json.dumps({
            "derivative_sha256": hashlib.sha256(
                b"corrected-synthetic-NPZ-fixture"
            ).hexdigest(),
            "source_invariant_violations": 0,
        }, sort_keys=True).encode(),
    }
    paths = {}
    roots = {}
    for role, data in contents.items():
        path = tmp_path / (role + ".bin")
        path.write_bytes(data)
        paths[role] = path
        roots[role] = gate.sha256_file(path)
    monkeypatch.setattr(gate, "PHYSICAL_INPUT_ROOTS", roots)
    monkeypatch.setattr(gate, "CORRECTED_DERIVATIVE_SHA256", roots["corrected_derivative"])
    monkeypatch.setattr(gate, "CORRECTED_DERIVATIVE_BYTES", paths["corrected_derivative"].stat().st_size)
    monkeypatch.setattr(gate, "FROZEN_PASS1_SHA256", roots["pass1_whole_file"])
    monkeypatch.setattr(gate, "FULL104_MANIFEST_SHA256", roots["full104_level4_manifest"])
    monkeypatch.setattr(gate, "SPLIT_CANONICAL_SHA256", "c" * 64)
    return paths, roots


def _ctx(tmp_path, monkeypatch):
    paths, roots = _fixture(tmp_path, monkeypatch)
    inputs = gate.authenticate_corrected_inputs(
        mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
        derivative=paths["corrected_derivative"],
        pass1=paths["pass1_whole_file"],
        split_receipt=paths["split_receipt"],
        level4_manifest=paths["full104_level4_manifest"],
        array_manifest=paths["per_member_manifest"],
        preflight_receipt=paths["v2_preflight_receipt"],
    )
    ctx = gate.build_context(
        mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
        task="AUDIT_B_N1_PHYSICAL_ADAPTER_QUALIFICATION",
        code_sha256=gate.sha256_file(Path(gate.__file__)),
        inputs=inputs,
        identity_digests={"synthetic_donor_order": "d" * 64},
        parameters={"synthetic_only_fixture": "TRUE"},
    )
    return paths, roots, ctx


def test_actual_six_input_binding_positive_control(tmp_path, monkeypatch):
    paths, roots, ctx = _ctx(tmp_path, monkeypatch)
    assert {i.role for i in ctx.inputs} == set(gate.PHYSICAL_INPUT_ROOTS)
    out = tmp_path / "v2.json"
    digest = gate.emit_adapter_qualification_receipt(
        path=out, ctx=ctx,
        body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW"},
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["receipt_sha256"] == digest
    assert payload["schema"] == "AUDIT_B_N1_PHYSICAL_ADAPTER_QUALIFICATION_V2"
    assert payload["n1_execution_authorized"] is False
    assert payload["training_authorized"] is False
    assert len(payload["inputs"]) == 6


def test_claimed_approval_sha_and_boolean_never_open_n1(tmp_path, monkeypatch):
    _, _, ctx = _ctx(tmp_path, monkeypatch)
    ctx.mode = gate.ExecutionMode.PRODUCTION
    ctx.n1_execution_authorized = True
    ctx.execution_authorization_sha256 = "f" * 64
    with pytest.raises(gate.PhysicalLineageError, match="STOP_N1_NOT_AUTHORIZED"):
        gate.require_n1_execution_authority(ctx)
    with pytest.raises(gate.PhysicalLineageError, match="only PHYSICAL_QUALIFICATION"):
        gate.emit_adapter_qualification_receipt(
            path=tmp_path / "never.json", ctx=ctx, body={},
        )


@pytest.mark.parametrize("protected", [
    "n1_execution_authorized", "training_authorized", "masks_executed",
    "audit_b_n1", "precision_calculated", "inputs", "receipt_sha256",
    "schema", "mode", "context_digest",
])
def test_forged_evidence_cannot_overwrite_authority(
    tmp_path, monkeypatch, protected,
):
    _, _, ctx = _ctx(tmp_path, monkeypatch)
    with pytest.raises(gate.PhysicalLineageError, match="override protected fields"):
        gate.emit_adapter_qualification_receipt(
            path=tmp_path / "never.json", ctx=ctx,
            body={
                "terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW",
                protected: True,
            },
        )
    assert not (tmp_path / "never.json").exists()


def test_same_semantics_resealed_unreviewed_receipt_rejected_at_real_input_gate(
    tmp_path, monkeypatch,
):
    paths, _, _ = _ctx(tmp_path, monkeypatch)
    altered = json.loads(paths["v2_preflight_receipt"].read_text())
    altered["extra_unreviewed_claim"] = "YES"
    paths["v2_preflight_receipt"].write_text(json.dumps(altered))
    with pytest.raises(gate.PhysicalLineageError, match="byte digest mismatch"):
        gate.authenticate_corrected_inputs(
            mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
            derivative=paths["corrected_derivative"],
            pass1=paths["pass1_whole_file"],
            split_receipt=paths["split_receipt"],
            level4_manifest=paths["full104_level4_manifest"],
            array_manifest=paths["per_member_manifest"],
            preflight_receipt=paths["v2_preflight_receipt"],
        )


def test_altered_physical_source_rejected_again_on_receipt_emission(
    tmp_path, monkeypatch,
):
    paths, _, ctx = _ctx(tmp_path, monkeypatch)
    paths["pass1_whole_file"].write_bytes(b"changed after preflight")
    with pytest.raises(gate.PhysicalLineageError, match="byte digest mismatch"):
        gate.emit_adapter_qualification_receipt(
            path=tmp_path / "never.json", ctx=ctx,
            body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW"},
        )
    assert not (tmp_path / "never.json").exists()


def test_empty_or_partial_census_rejected_before_claim(tmp_path, monkeypatch):
    _, _, ctx = _ctx(tmp_path, monkeypatch)
    ctx.inputs.pop()
    with pytest.raises(gate.PhysicalLineageError, match="six distinct"):
        gate.emit_adapter_qualification_receipt(
            path=tmp_path / "never.json", ctx=ctx,
            body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW"},
        )


def test_receipt_cannot_overwrite_existing_immutable_evidence(tmp_path, monkeypatch):
    _, _, ctx = _ctx(tmp_path, monkeypatch)
    p = tmp_path / "old-receipt.json"
    p.write_text("immutable prior review evidence", encoding="utf-8")
    with pytest.raises(FileExistsError):
        gate.emit_adapter_qualification_receipt(
            path=p, ctx=ctx,
            body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW"},
        )
    assert p.read_text(encoding="utf-8") == "immutable prior review evidence"
