"""Independent red-team controls for the September-23 perturbation receipt gate.

Synthetic test bytes stand in for an independently frozen root only inside
explicit monkeypatched unit tests. This is a gate-mechanics test, NEVER physical
source requalification. Physical roots remain frozen in production code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sea_ad_jepa.perturbation import execution_authority_v1 as gate


def fixture_context(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-blob.bin"
    data = b"test-only-synthetic-frozen-source"
    path.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    role = "TEST_FIXTURE_ONLY_DO_NOT_USE_AS_PHYSICAL_EVIDENCE"
    monkeypatch.setitem(gate.REVIEWED_SOURCE_ROOTS, role, (sha, len(data)))
    script = tmp_path / "synthetic_producer.py"
    script.write_bytes(b"# fixture only\\n")
    script_sha = gate.sha256_file(script)
    monkeypatch.setitem(gate.REVIEWED_QUALIFICATION_TASKS, "TEST_ONLY_FROZEN_ROOT_BEHAVIOR", {
        "roles": frozenset({role}), "code_sha256": script_sha,
    })
    ctx = gate.ExecutionContext(
        mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
        task="TEST_ONLY_FROZEN_ROOT_BEHAVIOR",
        code_sha256=script_sha,
        code_path=str(script),
        inputs=[gate.AuthenticatedInput(role, str(path), sha, len(data))],
        parameters={"n": 2},
    )
    return path, ctx, role


def test_receipt_positive_frozen_fixture_role(tmp_path, monkeypatch):
    path, ctx, role = fixture_context(tmp_path, monkeypatch)
    dst = tmp_path / "receipt.json"
    digest = gate.emit_qualification_receipt(
        path=dst, context=ctx, body={"test_observation": 3},
    )
    obj = json.loads(dst.read_text(encoding="utf-8"))
    assert obj["schema"] == "PERTURBATION_QUALIFICATION_RECEIPT_V2"
    assert obj["receipt_sha256"] == digest
    assert obj["inputs"][0]["role"] == role
    assert obj["evidence"]["test_observation"] == 3
    assert obj["production_execution_authorized"] is False
    assert obj["training_authorized"] is False
    assert obj["qualification_scope"] == "SOURCE_AND_SCRIPT_PREFLIGHT_ONLY"
    assert obj["scientific_execution_verified"] is False
    assert obj["output_results_verified"] is False


@pytest.mark.parametrize("reserved", [
    "schema", "mode", "task", "context_digest", "inputs", "parameters",
    "code_sha256", "identity_digests", "authorization_receipt_sha256",
    "receipt_sha256",
])
def test_evidence_cannot_override_provenance_or_authorization(
    tmp_path, monkeypatch, reserved,
):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    dst = tmp_path / "never.json"
    with pytest.raises(gate.ExecutionAuthorityError, match="protected provenance"):
        gate.emit_qualification_receipt(
            path=dst, context=ctx, body={reserved: "FORGED"},
        )
    assert not dst.exists()


def test_authenticator_rejects_self_supplied_hash_for_reviewed_role(
    tmp_path, monkeypatch,
):
    path, ctx, role = fixture_context(tmp_path, monkeypatch)
    forged = tmp_path / "different.bin"
    forged.write_bytes(b"other bytes")
    wrong_hash = gate.sha256_file(forged)
    assert wrong_hash != ctx.inputs[0].sha256
    with pytest.raises(
        gate.ExecutionAuthorityError, match="disagrees with the independently reviewed",
    ):
        gate.authenticate_physical_input(
            role=role, path=forged, expected_sha256=wrong_hash,
            mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
        )


def test_receipt_rechecks_physical_bytes_after_initial_authentication(
    tmp_path, monkeypatch,
):
    path, ctx, _ = fixture_context(tmp_path, monkeypatch)
    path.write_bytes(b"swapped-after-initial-authentication")
    dst = tmp_path / "never.json"
    with pytest.raises(gate.ExecutionAuthorityError, match="digest mismatch"):
        gate.emit_qualification_receipt(path=dst, context=ctx, body={"ok": True})
    assert not dst.exists()


def test_receipt_rejects_forged_preconstructed_input(tmp_path, monkeypatch):
    fake = tmp_path / "fake.bin"
    fake.write_bytes(b"fake")
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    ctx.inputs = [
        gate.AuthenticatedInput("FAKE_ROLE", str(fake), "f" * 64, 4)
    ]
    with pytest.raises(
        gate.ExecutionAuthorityError, match="physical input roles differ from the reviewed",
    ):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={},
        )


def test_duplicate_input_roles_rejected(tmp_path, monkeypatch):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    ctx.inputs.append(ctx.inputs[0])
    with pytest.raises(gate.ExecutionAuthorityError, match="duplicate physical input roles"):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={},
        )


def test_empty_physical_inputs_cannot_claim_pass(tmp_path):
    ctx = gate.ExecutionContext(
        mode=gate.ExecutionMode.PHYSICAL_QUALIFICATION,
        task="FALSE_PHYSICAL_PASS",
        code_sha256="a" * 64,
    )
    with pytest.raises(
        gate.ExecutionAuthorityError, match="requires independently reviewed physical inputs",
    ):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={"terminal": "PASS"},
        )


def test_64_digit_fake_production_grant_still_denied(tmp_path, monkeypatch):
    path, ctx, _ = fixture_context(tmp_path, monkeypatch)
    ctx.mode = gate.ExecutionMode.PRODUCTION
    ctx.authorization_receipt_sha256 = "f" * 64
    with pytest.raises(gate.ExecutionAuthorityError, match="PRODUCTION is CLOSED"):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={"terminal": "PASS"},
        )
    with pytest.raises(gate.ExecutionAuthorityError, match="PRODUCTION is CLOSED"):
        gate.authenticate_physical_input(
            role=ctx.inputs[0].role, path=path,
            expected_sha256=ctx.inputs[0].sha256,
            mode=gate.ExecutionMode.PRODUCTION,
        )


def test_qualification_receipts_are_immutable(tmp_path, monkeypatch):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    dst = tmp_path / "receipt.json"
    gate.emit_qualification_receipt(path=dst, context=ctx, body={"value": 1})
    first = dst.read_bytes()
    with pytest.raises(FileExistsError):
        gate.emit_qualification_receipt(path=dst, context=ctx, body={"value": 2})
    assert dst.read_bytes() == first



def test_cannot_self_approve_a_different_scientific_task(tmp_path, monkeypatch):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    ctx.task = "UNREVIEWED_THERAPEUTIC_EFFICACY_CLAIM"
    with pytest.raises(gate.ExecutionAuthorityError, match="task lacks a separately reviewed"):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={"terminal": "PASS"},
        )


def test_actual_script_mutation_rejected_despite_stale_declared_script_sha(
    tmp_path, monkeypatch,
):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    Path(ctx.code_path).write_bytes(b"changed script after review")
    with pytest.raises(gate.ExecutionAuthorityError, match="actual script bytes differ"):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={"terminal": "PASS"},
        )


def test_wrong_approved_code_root_rejected_even_if_script_is_present(
    tmp_path, monkeypatch,
):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    ctx.code_sha256 = "f" * 64
    with pytest.raises(gate.ExecutionAuthorityError, match="script digest differs"):
        gate.emit_qualification_receipt(
            path=tmp_path / "never.json", context=ctx, body={},
        )


@pytest.mark.parametrize("claim", [
    {"terminal": "PASS_PHYSICAL"},
    {"status": "PASS"},
    {"scientific_execution_verified": True},
    {"nested": {"execution_completed": True}},
    {"nested": [{"output_results_verified": True}]},
    {"production_execution_authorized": True},
])
def test_source_prefight_rejects_scientific_or_production_claims(
    tmp_path, monkeypatch, claim,
):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    target = tmp_path / "must_not_exist.json"
    with pytest.raises(gate.ExecutionAuthorityError, match="(protected provenance|cannot attest)"):
        gate.emit_qualification_receipt(path=target, context=ctx, body=claim)
    assert not target.exists()


def test_no_script_execution_or_output_check_is_claimed(tmp_path, monkeypatch):
    _, ctx, _ = fixture_context(tmp_path, monkeypatch)
    receipt_path = tmp_path / "preflight.json"
    gate.emit_qualification_receipt(path=receipt_path, context=ctx,
                                    body={"source_census": 2})
    obj = json.loads(receipt_path.read_text())
    assert obj["qualification_scope"] == "SOURCE_AND_SCRIPT_PREFLIGHT_ONLY"
    assert obj["scientific_execution_verified"] is False
    assert obj["output_results_verified"] is False
    assert obj["production_execution_authorized"] is False
    assert obj["training_authorized"] is False
