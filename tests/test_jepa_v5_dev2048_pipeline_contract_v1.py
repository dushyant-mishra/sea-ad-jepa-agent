"""Sol original-preserving hostile V5 provenance-contract tests.

Real public DEV2048 FIT (SHA-verified) is used if JEPA_PUBLIC_DEV_FIT_ZIP
is set by the CI; otherwise offline source-identity tests still run.
Never import or execute V5 neural model, writer, optimizer, EMA or V80.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import shutil

import pytest

from scripts.v5 import jepa_v5_dev2048_pipeline_contract_v1 as contract
from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def public_receipt():
    fit = os.environ.get("JEPA_PUBLIC_DEV_FIT_ZIP")
    if not fit:
        pytest.skip("original public FIT path not supplied; no fake acceptance")
    return contract.build_static_contract(
        repo_root=ROOT, public_fit_zip=Path(fit))


def test_original15_v5_and_journal_source_interfaces_static_only():
    source = contract.verify_source_interfaces(ROOT)
    assert source["original_v5_source_count"] == 15
    assert source["original_v5_sources"]["all_15_original_v5_git_blobs_match"]
    assert source["bounded_existing_call_paths_static_only"]
    assert source["post_target_pr525_v4_policy_used_as_v5_identity"] is False


@pytest.mark.parametrize("target", [
    "scripts/v5/jepa_synth2048_attempt_journal_v2.py",
    "scripts/v5/jepa_v5_structured_journal_preflight_v1.py",
    "scripts/v5/jepa_v5_full_state_readonly_audit_v1.py",
    "scripts/v5/jepa_v5_source_data_custody_gate_v1.py",
])
def test_modified_fake_journal_or_validator_code_refused(tmp_path, target):
    for p in (*gate.ORIGINAL_SOURCE_GIT_BLOBS, gate.READINESS_ADAPTER,
              *contract.FILE_PINS):
        dest = tmp_path / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, dest)
    with (tmp_path / target).open("ab") as f:
        f.write(b"\n# changed original fake journal source\n")
    with pytest.raises(contract.PipelineContractRefusal,
                       match="FAKE_JOURNAL_OR_GATE_SOURCE_CHANGED"):
        contract.verify_source_interfaces(tmp_path)


def test_missing_original_public_fit_refused_as_complete(tmp_path):
    with pytest.raises(contract.PipelineContractRefusal,
                       match="WRONG_PUBLIC_DEV_FIT"):
        contract.build_static_contract(
            repo_root=ROOT, public_fit_zip=tmp_path / "NOT_THE_ORIGINAL_FIT.zip")


def test_public_receipt_is_provenance_only_never_a_training_or_probe_pass(public_receipt):
    data = public_receipt["contract"]["data"]
    holds = public_receipt["contract"]["hard_holds"]
    rights = public_receipt["contract"]["rights_and_teacher"]
    assert data["public_zip_exact_verified"]
    assert data["rows"] == 1440 and data["gene_addresses"] == 2048
    assert data["synthetic_donors"] == 36
    assert data["student_address_axis_preserved"]
    assert data["rna_row_entity_ids_distinct"]
    assert data["donor_source_and_split_purity_checked"]
    assert data["original_query_ids"] == [1672, 1673, 1674, 1675]
    assert data["student_q_values_available"] is False
    assert data["C1_to_C6_biology"] == "UNASSESSED"
    assert public_receipt["contract"]["source"]["active_model"] == (
        "V5_ONE_GUARDED_UPDATE_INACTIVE_NOT_AUTHORIZED")
    assert public_receipt["contract"]["source"]["post_target_policy"] == (
        contract.POLICY_KIND)
    assert rights["issuer"] == contract.NO_ISSUER
    assert rights["human_donor_source_authorized"] is False
    assert rights["teacher_target_biology_proved"] is False
    assert all(v is False for v in holds.values())
    assert public_receipt["contract"]["locked_dev_journal_bindings"]["can_open_journal"] is False
    contract.verify_claim(public_receipt, public_receipt)


@pytest.mark.parametrize(("where", "field", "value"), [
    (("source",), "active_model", "V4_TEACHER_STUDENT_PRODUCTION"),
    (("source",), "post_target_policy", "PR525_V4_FILES_VALID_V5_EXECUTOR"),
    (("source",), "original_head", "0" * 40),
    (("coordinates",), "gene_axis", "COMPACT_2044_RENUMBERED_GENES"),
    (("coordinates",), "q_ids", [1672, 1673, 1674, 1676]),
    (("coordinates",), "donor_source_split_roster_member_sha256", "b" * 64),
    (("data",), "public_fit_zip_sha256", "f" * 64),
    (("data",), "source_labels", ["SEAAD", "NPH52", "HVS"]),
    (("data",), "synthetic_donors", 104),
    (("data",), "gene_addresses", 41238),
    (("data",), "student_q_values_available", True),
    (("rights_and_teacher",), "issuer", "SELF_DECLARED_VALID_RIGHTS"),
    (("rights_and_teacher",), "human_donor_source_authorized", True),
    (("rights_and_teacher",), "production_target_selected", True),
    (("rights_and_teacher",), "teacher_target_biology_proved", True),
    (("hard_holds",), "train_authorized", True),
    (("hard_holds",), "optimizer_step_allowed", True),
    (("hard_holds",), "ema_update_allowed", True),
    (("hard_holds",), "RT1_to_RT8_allowed", True),
    (("hard_holds",), "journal_writer_opened", True),
    (("locked_dev_journal_bindings",), "rights_sha256", "a" * 64),
    (("locked_dev_journal_bindings",), "panel_sha256", "a" * 64),
    (("locked_dev_journal_bindings",), "gene_axis_sha256", "a" * 64),
    (("locked_dev_journal_bindings",), "source_manifest_sha256", "a" * 64),
    (("locked_dev_journal_bindings",), "philox_contract_sha256", "a" * 64),
])
def test_caller_cannot_launder_wrong_model_gene_data_rights_or_writer(
        public_receipt, where, field, value):
    altered = deepcopy(public_receipt)
    location = altered["contract"]
    for key in where:
        location = location[key]
    location[field] = value
    # Even if caller recomputes all self-declared hashes, the original pinned
    # public-data/cross-code evidence cannot be replaced with their assertion.
    altered["contract_sha256"] = contract.digest(altered["contract"])
    with pytest.raises(contract.PipelineContractRefusal,
                       match="SOURCE_DATA_POLICY_GENE_PANEL_RIGHTS_OR_JOURNAL_IDENTITY_CHANGED"):
        contract.verify_claim(altered, public_receipt)


def test_fake_replayed_latched_contract_sha_refused(public_receipt):
    tampered = deepcopy(public_receipt)
    tampered["contract_sha256"] = "0" * 64
    with pytest.raises(contract.PipelineContractRefusal,
                       match="SOURCE_DATA_POLICY_GENE_PANEL_RIGHTS_OR_JOURNAL_IDENTITY_CHANGED"):
        contract.verify_claim(tampered, public_receipt)


def test_wrong_zip_bytes_same_name_and_size_refused(tmp_path, public_receipt):
    import zipfile
    source = os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]
    raw = bytearray(Path(source).read_bytes())
    raw[min(1024, len(raw) - 1)] ^= 1
    dest = tmp_path / "ORIGINAL_PUBLIC_DEV_FIT.zip"
    dest.write_bytes(raw)
    assert dest.stat().st_size == gate.DEV_FIT_ZIP_BYTES
    with pytest.raises(contract.PipelineContractRefusal, match="WRONG_PUBLIC_DEV_FIT"):
        contract.audit_public_dev_rows(dest)


def test_no_model_training_or_writer_import_by_static_contract():
    import ast
    path = ROOT / "scripts/v5/jepa_v5_dev2048_pipeline_contract_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("sea_ad_jepa.v5", "torch", "sea_ad_jepa.v4.teacher_student_runtime",
                 "jepa_synth2048_attempt_journal_v2",
                 "jepa_v5_structured_journal_preflight_v1")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name == v or name.startswith(v + ".")
                   for name in imports for v in forbidden), imports
