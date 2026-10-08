from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from sea_ad_jepa.v5 import full104_masking_streaming_executor_v1 as streaming
from sea_ad_jepa.v5 import masking_control_executor_v1 as controls
from sea_ad_jepa.v5 import masking_donor_evidence_v1 as donor_evidence
from sea_ad_jepa.v5 import masking_nonlinear_challenge_executor_v1 as nonlinear
from sea_ad_jepa.v5 import masking_terminal_evidence_assembly_v1 as assembly
from sea_ad_jepa.v5.masking_qualification_run_contract_v4 import (
    TERMINAL_EXECUTION_INPUT_ROLE_ID,
)
from sea_ad_jepa.v5.masking_terminal_mechanical_controls_v1 import (
    TerminalMechanicalControlReceiptV1,
    assert_complete_policy_mask_grid,
    assert_no_privileged_metadata_interface,
    assert_untreated_input_identity,
    canonical_mask_sha256,
    mask_grid_digest,
    reconstruct_policy_mask_roots,
)

from test_v5_full104_masking_streaming_executor_v1 import _fixture, budget, parameters


def file_sha(module) -> str:
    h = hashlib.sha256()
    with Path(module.__file__).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ContractStub:
    full104_streaming_execution_source_sha256 = file_sha(streaming)
    donor_evidence_source_sha256 = file_sha(donor_evidence)
    control_executor_source_sha256 = file_sha(controls)
    nonlinear_executor_source_sha256 = file_sha(nonlinear)
    terminal_evidence_assembly_source_sha256 = file_sha(assembly)

    def validate(self):
        return None

    def assert_terminal_execution_input_role(self, role):
        if role != TERMINAL_EXECUTION_INPUT_ROLE_ID:
            raise ValueError("wrong terminal input role")

    def canonical_digest(self):
        return hashlib.sha256(b"contract").hexdigest()


def test_mask_digest_is_order_independent_and_content_sensitive():
    assert canonical_mask_sha256({3, 1, 2}) == canonical_mask_sha256({2, 3, 1})
    assert canonical_mask_sha256({1, 2}) != canonical_mask_sha256({1, 2, 3})


def test_replay_control_reconstructs_exact_complete_fold_grid(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    rows = donor_evidence.run_streaming_fold_with_donor_evidence(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    roots = reconstruct_policy_mask_roots(
        rows=rows,
        stream=stream,
        evidence_budget=budget(),
        global_seed=17,
    )
    assert_complete_policy_mask_grid(
        roots=roots,
        policy_ids=(
            "UNIFORM_RANDOM",
            "TOP8_CORRELATION",
            "RIDGE8_CONDITIONAL",
            "PREFIX3_SELECTIVE",
        ),
        target_count=2,
        outer_fold_count=1,
    )
    assert len(roots) == 8
    assert len(mask_grid_digest(roots)) == 64


def test_replay_control_rejects_duplicate_primary_row(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    rows = donor_evidence.run_streaming_fold_with_donor_evidence(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    with pytest.raises(ValueError, match="duplicate terminal policy row"):
        reconstruct_policy_mask_roots(
            rows=[*rows, rows[0]],
            stream=stream,
            evidence_budget=budget(),
            global_seed=17,
        )


def test_no_privileged_metadata_control_binds_exact_source_interfaces(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    assert assert_no_privileged_metadata_interface(
        run_contract=ContractStub(),
        stream=stream,
    ) is True


def test_no_privileged_metadata_control_rejects_source_drift(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)

    class BadContract(ContractStub):
        control_executor_source_sha256 = hashlib.sha256(b"wrong").hexdigest()

    with pytest.raises(ValueError, match="control_executor_source_sha256"):
        assert_no_privileged_metadata_interface(
            run_contract=BadContract(),
            stream=stream,
        )


def test_no_privileged_metadata_control_rejects_privileged_runtime_attribute(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    stream.pathology_by_donor = object()
    with pytest.raises(ValueError, match="privileged metadata"):
        assert_no_privileged_metadata_interface(
            run_contract=ContractStub(),
            stream=stream,
        )


def test_untreated_identity_revalidates_physical_bytes(tmp_path: Path):
    _, stream, _, manifest_rows = _fixture(tmp_path)
    stream.validate_layout()
    before = stream.revalidate_physical_inputs()
    assert assert_untreated_input_identity(
        stream=stream,
        before_manifest_sha256=before,
    ) is True

    counts = stream.block_root / manifest_rows[0]["counts_path"]
    with counts.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match="physical revalidation"):
        assert_untreated_input_identity(
            stream=stream,
            before_manifest_sha256=before,
        )


def test_control_receipt_requires_all_three_mechanical_controls():
    receipt = TerminalMechanicalControlReceiptV1(
        run_contract_sha256=hashlib.sha256(b"contract").hexdigest(),
        terminal_input_manifest_sha256=hashlib.sha256(b"manifest").hexdigest(),
        mask_grid_sha256=hashlib.sha256(b"grid").hexdigest(),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
    )
    receipt.validate()
    assert len(receipt.canonical_digest()) == 64

    with pytest.raises(ValueError, match="replay"):
        TerminalMechanicalControlReceiptV1(
            run_contract_sha256=hashlib.sha256(b"contract").hexdigest(),
            terminal_input_manifest_sha256=hashlib.sha256(b"manifest").hexdigest(),
            mask_grid_sha256=hashlib.sha256(b"grid").hexdigest(),
            replay_exact=False,
            untreated_identity_exact=True,
            no_privileged_metadata=True,
        ).validate()
