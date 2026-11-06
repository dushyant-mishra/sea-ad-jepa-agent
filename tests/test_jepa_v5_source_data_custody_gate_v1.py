"""Static hostile provenance tests, no torch import or neural execution.

This test does not inspect SEA-AD restricted data or the sealed V80 controller.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]


def _copy_fixture(tmp_path):
    """Only the original 15 pinned source files and one preexisting U0 adapter."""
    for item in (*gate.ORIGINAL_SOURCE_GIT_BLOBS, gate.READINESS_ADAPTER):
        source, destination = ROOT / item, tmp_path / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return tmp_path


def test_control_exact_original_15_v5_files_and_original_2048_input_adapter(tmp_path):
    root = _copy_fixture(tmp_path)
    result = gate.audit(repo_root=root)
    assert result["source"]["all_15_original_v5_git_blobs_match"] is True
    assert result["source"]["canonical_runtime_file_count"] == 12
    assert result["source"]["private_implementation_count"] == 2
    assert result["source"]["pr548_u0_actor_and_data_declarations_match"] is True
    assert result["data"]["fit_bytes_verified"] is False
    assert result["pipeline"]["single_end_to_end_model_journal_train_path_proved"] is False
    assert result["pipeline"]["multi_update_v5_driver_exists_or_proved"] is False
    assert result["training_authorized"] is False


def test_wrong_main_or_v4_actor_cannot_substitute_for_original_guarded_v5(tmp_path):
    root = _copy_fixture(tmp_path)
    actor = root / "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py"
    actor.unlink()
    # Historical V4 is a real file but not a substitute for the V5 actor.
    (root / "src/sea_ad_jepa/v4").mkdir(exist_ok=True)
    (root / "src/sea_ad_jepa/v4/teacher_student_runtime.py").write_text("historical v4")
    with pytest.raises(gate.SourceDataRefusal, match="REQUIRED_REGULAR_FILE_MISSING_OR_SYMLINK"):
        gate.audit_sources(root)


@pytest.mark.parametrize("name", [
    "src/sea_ad_jepa/v5/inactive_update_reference.py",
    "src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py",
    "src/sea_ad_jepa/v5/_inactive_checkpoint_binding_impl_v1.py",
    "src/sea_ad_jepa/v4/gene_tokenizer.py",
])
def test_any_original_runtime_byte_change_refused_even_when_v5_file_exists(tmp_path, name):
    root = _copy_fixture(tmp_path)
    with (root / name).open("ab") as stream:
        stream.write(b"\n# mutated after PR224 freeze\n")
    with pytest.raises(gate.SourceDataRefusal, match="ORIGINAL_V5_SOURCE_CHANGED"):
        gate.audit_sources(root)


def test_substituted_pr548_data_adapter_or_query_mapping_refused(tmp_path):
    root = _copy_fixture(tmp_path)
    adapter = root / gate.READINESS_ADAPTER
    adapter.write_bytes(adapter.read_bytes().replace(b"1675", b"1676"))
    with pytest.raises(gate.SourceDataRefusal, match="PR548_2048_INPUT_ADAPTER_CHANGED"):
        gate.audit_sources(root)


def test_symlink_to_right_bytes_is_not_an_authenticated_git_source(tmp_path):
    root = _copy_fixture(tmp_path)
    source = root / "src/sea_ad_jepa/v5/inactive_update_reference.py"
    elsewhere = root / "old-main-same-filename.py"
    elsewhere.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(elsewhere)
    with pytest.raises(gate.SourceDataRefusal, match="MISSING_OR_SYMLINK"):
        gate.audit_sources(root)


def test_wrong_public_zip_rejected_even_when_member_files_are_named_correctly(tmp_path):
    zip_path = tmp_path / "wrong_public_pr547_fit.zip"
    zip_path.write_bytes(b"PK\\x03\\x04wrong")
    with pytest.raises(gate.SourceDataRefusal, match="WRONG_SIZE"):
        gate.audit_dev_fit(zip_path)


def test_no_fit_path_must_not_be_reported_as_verified_real_data(tmp_path):
    root = _copy_fixture(tmp_path)
    result = gate.audit(repo_root=root)
    assert result["data"]["fit_bytes_verified"] is False
    assert result["pipeline"]["source_rights_issuer_or_real_PANEL_authority_proved"] is False
    assert result["pipeline"]["physical_probes_proved"] is False
