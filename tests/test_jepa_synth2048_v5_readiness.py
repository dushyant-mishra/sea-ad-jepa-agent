"""Hostile zero-update V5 integration tests; no controller truth and no training."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path

import numpy as np
import pytest

from scripts.v5 import jepa_synth2048_v5_readiness as v5


@pytest.fixture(scope="module")
def fit():
    path = os.environ.get("JEPA_SYNTH2048_DEV_ZIP")
    if path is None:
        pytest.skip("exact PR547 FIT ZIP not connected; no replacement allowed")
    receipt, student, roster = v5.verified_fit(Path(path))
    return receipt, student, roster


def test_actual_v5_source_hashes_are_pinned():
    result = v5.verify_v5_runtime_sources()
    assert result == v5.SOURCE_SHA1
    assert result["src/sea_ad_jepa/v5/inactive_guarded_update_v1.py"] == (
        "59647eb0122dfd98068844f68b6d48c2c33d67ca"
    )


def test_refuse_fabricated_or_changed_source(tmp_path):
    with pytest.raises(v5.PreflightRefusal, match="V5 source missing"):
        v5.verify_v5_runtime_sources(tmp_path)


def test_actual_zip_hash_members_and_status(fit):
    receipt, student, roster = fit
    assert receipt["all_six_candidate_recoverability"] == "UNASSESSED"
    assert receipt["controller_truth_exported"] is False
    assert receipt["fit_file_sha256"]["student_qexcluded.npz"] == v5.MEMBER_SHA256[
        "student_qexcluded.npz"
    ]
    assert "rna_counts" not in student and "donor_id" not in student
    assert "perturbation_arm" in roster


def test_archive_byte_mutation_fails_closed(tmp_path, fit):
    original = Path(os.environ["JEPA_SYNTH2048_DEV_ZIP"])
    payload = bytearray(original.read_bytes())
    payload[200] ^= 0x80
    mutated = tmp_path / "altered.zip"
    mutated.write_bytes(payload)
    with pytest.raises(v5.PreflightRefusal, match="archive SHA"):
        v5.verified_fit(mutated)


def test_restored_genes_have_original_addresses_not_shifted(fit):
    receipt, student, roster = fit
    full, rights, report = v5.audit_fit(receipt, student, roster)
    assert full.shape == rights.shape == (1440, 2048)
    assert full.dtype == np.int32 and rights.dtype == np.bool_
    original_indices = student["rna_base_address_ids"]
    assert np.array_equal(full[:, original_indices], student["rna_base_counts"])
    assert np.array_equal(rights[:, original_indices], student["rna_base_support"])
    assert not rights[:, list(v5.Q)].any()
    assert not full[:, list(v5.Q)].any()
    assert report["gene_identity_restored_exactly"]
    assert report["actual_optimizer_updates"] == report["actual_ema_updates"] == 0
    assert report["train_donors"] + report["val_donors"] + report["test_donors"] == 36


def test_alias_duplicate_or_renumbered_gene_address_rejected(fit):
    _, student, _ = fit
    copy = dict(student)
    address = student["rna_base_address_ids"].copy()
    assert 1676 in address
    address[np.where(address == 1676)[0][0]] = 1672
    copy["rna_base_address_ids"] = address
    with pytest.raises(v5.PreflightRefusal, match="address renumbered"):
        v5.restore_full_address_space(copy)
    address2 = student["rna_base_address_ids"].copy()
    address2[np.where(address2 == 1676)[0][0]] = 1674
    copy["rna_base_address_ids"] = address2
    with pytest.raises(v5.PreflightRefusal, match="address renumbered"):
        v5.restore_full_address_space(copy)


def test_hidden_query_scalar_and_depth_descendant_rejected(fit):
    _, student, _ = fit
    assert not np.isin(v5.Q, student["rna_base_address_ids"]).any()
    with pytest.raises(v5.PreflightRefusal, match="queries must be frozen"):
        v5.restore_full_address_space(student, query_ids=(1672, 1673, 1674, 1676))
    altered = dict(student)
    altered["projected_base_depth"] = student["projected_base_depth"].copy()
    altered["projected_base_depth"][0] += 1000
    with pytest.raises(v5.PreflightRefusal, match="whole-library depth"):
        v5.restore_full_address_space(altered)


def test_unsupported_nonzero_and_wrong_support_dtype_rejected(fit):
    _, student, _ = fit
    altered = dict(student)
    counts = student["rna_base_counts"].copy()
    mask = student["rna_base_support"]
    a, b = np.argwhere(~mask)[0]
    counts[a, b] = 1
    altered["rna_base_counts"] = counts
    # Conservative refusal even if a matching fake depth is supplied.
    altered["projected_base_depth"] = counts.sum(axis=1, dtype=np.int64)
    with pytest.raises(v5.PreflightRefusal, match="negative/unsupported"):
        v5.restore_full_address_space(altered)
    altered = dict(student)
    altered["rna_base_support"] = mask.astype(np.uint8)
    with pytest.raises(v5.PreflightRefusal, match="dtype"):
        v5.restore_full_address_space(altered)


def test_donor_split_forgery_rejected(fit):
    receipt, student, roster = fit
    altered = dict(roster)
    s = roster["split"].copy()
    donor = roster["donor_id"]
    j = int(np.where(donor == donor[0])[0][-1])
    assert j != 0
    s[j] = "test" if s[j] != "test" else "train"
    altered["split"] = s
    with pytest.raises(v5.PreflightRefusal, match="donor split"):
        v5.audit_fit(receipt, student, altered)


def test_duplicate_relational_view_or_wrong_query_fails(fit):
    receipt, student, roster = fit
    mutated = deepcopy(receipt)
    roles = mutated["frozen_preoutcome_address_roles"]
    roles["relational_views_3x512"][1][3] = roles["relational_views_3x512"][0][3]
    with pytest.raises(v5.PreflightRefusal, match="overlap"):
        v5.audit_fit(mutated, student, roster)
    mutated = deepcopy(receipt)
    mutated["frozen_preoutcome_address_roles"]["query_addresses"][0] = 999
    with pytest.raises(v5.PreflightRefusal, match="C3 q-ids"):
        v5.audit_fit(mutated, student, roster)


@pytest.mark.slow
def test_actual_six_block_full_address_u0_without_training(fit):
    receipt, student, roster = fit
    full, rights, _ = v5.audit_fit(receipt, student, roster)
    report = v5.run_zero_update_model_probe(full, rights, roster)
    assert report["status"] == "ACTUAL_V5_SIX_BLOCK_U0_FORWARD_PASS__NO_LEARNING"
    assert report["encoder_blocks"] == 6 and report["width"] == 160
    assert report["molecular_addresses"] == 2048
    assert report["optimizer_updates"] == report["ema_updates"] == 0
    assert report["teacher_grads"] == 0
    assert report["target_qualified"] is False
    assert np.isfinite(report["u0_jepa_mse_mechanics_only"])
