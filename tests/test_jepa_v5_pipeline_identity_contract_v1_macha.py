"""Adversarial, non-executing tests of the V5 DEV2048 pipeline identity contract.

No model import or forward pass, optimizer step, EMA update, GPU, real RNA
or sealed controller. The public PR547 FIT is used only when
JEPA_PUBLIC_FIT_ZIP points to it. One test builds a fabricated CPU snapshot
(torch, never stepped) to show contract bindings fit the integrated journal.
"""
from __future__ import annotations

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import zipfile

import pytest

from scripts.v5 import jepa_v5_pipeline_identity_contract_v1 as pic

ROOT = Path(__file__).resolve().parents[1]
REFUSED = pic.PipelineIdentityRefusal


@pytest.fixture(scope="module")
def contract():
    return pic.load_contract(ROOT / pic.CONTRACT_PATH)


def test_committed_contract_is_self_consistent_and_confers_nothing(contract):
    assert contract["authorization"] and not any(contract["authorization"].values())
    assert contract["journal_bindings"] == pic.derive_bindings(contract)
    c = contract["components"]
    assert len(c["actor_runtime"]["executed_closure_git_blobs"]) == 35
    assert c["teacher_target_provenance"]["status"] == "NOT_BOUND__NO_QUALIFIED_TARGET"
    assert c["dataset"]["is_full104"] is False and c["dataset"]["is_real_human_rna"] is False
    assert c["policy"]["may_bind_actor_identity"] is False
    assert c["molecular_coordinates"]["student_address_ids"][1671:1673] == [1671, 1676]


def test_repository_matches_contract_by_git_blob(contract):
    report = pic.verify_repository(contract, ROOT)
    assert report["source_identity_complete"] is True
    assert report["executed_closure_file_count"] == 35


@pytest.mark.parametrize("edit", ["q", "blob", "authorize", "rehash_only"])
def test_tampered_contract_refuses_even_when_rehashed(tmp_path, contract, edit):
    bad = deepcopy(contract)
    c = bad["components"]
    if edit == "q":
        c["molecular_coordinates"]["query_withheld"] = [1672, 1673, 1674, 1676]
    elif edit == "blob":
        c["actor_runtime"]["executed_closure_git_blobs"][
            "src/sea_ad_jepa/v4/contracts.py"] = "0" * 40
    elif edit == "authorize":
        bad["authorization"]["training_authorized"] = True
    else:
        c["dataset"]["is_full104"] = True
    body = {k: v for k, v in bad.items() if k != "contract_sha256"}
    bad["contract_sha256"] = pic.canonical_sha256(body)
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(REFUSED, match="CONTRACT_CLAIMS_AUTHORITY|CONTRACT_DIFFERS"):
        pic.load_contract(path)


def test_expected_request_is_consistent_but_never_authorized(contract):
    result = pic.verify_run_request(contract, pic.expected_run_request(contract))
    assert result["status"] == "CONSISTENT_WITH_CONTRACT__EXECUTION_NOT_AUTHORIZED"
    assert result["execution_authorized"] is False
    assert result["teacher_target_bound"] is False


def _fifteen_file_manifest(contract):
    c = contract["components"]
    declared = {k: v for k, v in c["actor_runtime"]["executed_closure_git_blobs"].items()
                if k in pic.gate.ORIGINAL_SOURCE_GIT_BLOBS}
    return pic.canonical_sha256({"schema": "JEPA_V5_SOURCE_MANIFEST_V1",
                                 "executed_closure": declared,
                                 "custody_layer": c["checkpoint_journal"]["git_blobs"]})


HOSTILE = {
    # class 8: historical V4 training mistaken for V5
    "v4_runner_version": (lambda r, c: r.update(actor_version="V4_HEALTHY_TEACHER_U0_U40"),
                          "WRONG_MODEL_VERSION"),
    "pr525_runtime_identity_as_actor": (
        lambda r, c: r.update(actor_source_manifest_sha256=pic.PR525_POLICY["runtime_identity_sha256"]),
        "PR525_V4_RUNTIME_IDENTITY_IS_NOT_V5_ACTOR_IDENTITY"),
    "fifteen_file_partial_manifest": (
        lambda r, c: r.update(actor_source_manifest_sha256=_fifteen_file_manifest(c)),
        "SOURCE_MANIFEST_MISMATCH"),
    # class 5: synthetic development data presented as FULL104 / production
    "full104_label": (lambda r, c: r.update(dataset_class="FULL104_REAL_HUMAN"), "WRONG_DATA"),
    "production_41k_axis": (lambda r, c: r.update(n_addresses=41238), "WRONG_DATA"),
    "full104_cells": (lambda r, c: r.update(n_cells=4553407), "WRONG_DATA"),
    "bool_for_int": (lambda r, c: r.update(n_cells=True), "WRONG_DATA"),
    # class 4: q withheld by renumbering instead of hiding
    "student_axis_compacted": (lambda r, c: r.update(student_address_ids=list(range(2044))),
                               "MOLECULAR_ORDER_CHANGED"),
    "teacher_axis_reversed": (lambda r, c: r.update(
        teacher_address_ids=list(reversed(r["teacher_address_ids"]))), "MOLECULAR_ORDER_CHANGED"),
    "query_transposed": (lambda r, c: r.update(query_withheld=[1672, 1673, 1675, 1674]),
                         "MOLECULAR_ORDER_CHANGED"),
    # teacher/student and optimizer configuration
    "teacher_width_differs": (lambda r, c: r["teacher_model_config"].update(width=128),
                              "TEACHER_STUDENT_CONFIG_INCONSISTENT"),
    "external_teacher_target": (lambda r, c: r["teacher_config"].update(
        external_teacher_target="STAGE81B_CELL_ANCHOR"), "TEACHER_STUDENT_CONFIG_INCONSISTENT"),
    "identity_dim_changed_both": (lambda r, c: (r["student_model_config"].update(gene_identity_dim=32),
                                                r["teacher_model_config"].update(gene_identity_dim=32)),
                                  "MODEL_CONFIG_NOT_CONTRACT"),
    "gradient_ascent": (lambda r, c: r["optimizer_config"].update(maximize=True),
                        "OPTIMIZER_CONFIG_NOT_CONTRACT"),
    "lr_schedule_added": (lambda r, c: r["optimizer_config"].update(lr_schedule="COSINE"),
                          "OPTIMIZER_CONFIG_NOT_CONTRACT"),
    # unauthorized sources and caller-chosen journal bindings
    "real_rights": (lambda r, c: r.update(rights_scope="SEA_AD_CONTROLLED_ACCESS"),
                    "UNAUTHORIZED_SOURCE_OR_RIGHTS"),
    "caller_gene_axis_sha": (lambda r, c: r["journal_bindings"].update(gene_axis_sha256="a" * 64),
                             "JOURNAL_BINDING_MISMATCH__gene_axis_sha256"),
    "extra_binding": (lambda r, c: r["journal_bindings"].update(panel_sha256="c" * 64),
                      "JOURNAL_BINDING_FIELDS"),
    # class 7: health/authority claims the contract cannot confer
    "training_authorized": (lambda r, c: r["authorization"].update(training_authorized=True),
                            "AUTHORIZATION_NOT_CONFERRED"),
    "health_claim": (lambda r, c: r["authorization"].update(biological_health_proved=True),
                     "AUTHORIZATION_NOT_CONFERRED"),
    "unknown_field": (lambda r, c: r.update(stage4=True), "REQUEST_FIELDS"),
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_hostile_run_request_fails_closed(contract, name):
    mutate, reason = HOSTILE[name]
    request = pic.expected_run_request(contract)
    mutate(request, contract)
    with pytest.raises(REFUSED, match=reason):
        pic.verify_run_request(contract, request)


def test_legacy_fictional_runtime_path_present_refuses(tmp_path, contract, monkeypatch):
    calls = {}
    monkeypatch.setattr(pic.gate, "audit_sources", lambda root: calls.setdefault("s", 1))
    monkeypatch.setattr(pic.gate, "audit_executed_closure", lambda root, **k: {
        "executed_import_closure_verified": True, "executed_closure_file_count": 35})
    monkeypatch.setattr(pic.gate, "_regular_bytes", lambda root, p: (ROOT / p).read_bytes())
    legacy = tmp_path / pic.FORBIDDEN_SUBSTITUTES["legacy_fictional_runtime_path"]
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# reconstructed from memory\n")
    with pytest.raises(REFUSED, match="LEGACY_FICTIONAL_RUNTIME_PATH_PRESENT"):
        pic.verify_repository(contract, tmp_path)


def _mini_fit(compact_naively: bool, swap_roster_rows: bool) -> bytes:
    """Tiny public-shaped FIT: 4 cells x 8 addresses, address 5 withheld."""
    np = pytest.importorskip("numpy")
    counts = np.arange(32, dtype=np.int32).reshape(4, 8)
    support = counts % 3 != 0
    counts = np.where(support, counts, 0).astype(np.int32)
    ids = np.arange(8, dtype=np.int32)
    keep = np.array([0, 1, 2, 3, 4, 6, 7], dtype=np.int32)
    base = counts[:, :7] if compact_naively else counts[:, keep]
    base_support = support[:, :7] if compact_naively else support[:, keep]
    donor = np.array([0, 0, 1, 1], dtype=np.int32)
    ent = np.array(["DEV_D%03d_CELL%05d" % (d, i) for i, d in enumerate(donor)])
    if swap_roster_rows:
        ent = ent[[1, 0, 2, 3]]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        def put(name, **arrays):
            buf = io.BytesIO()
            np.savez(buf, **arrays)
            z.writestr(name, buf.getvalue())
        put("teacher_measured.npz", rna_counts=counts, rna_support=support, rna_address_ids=ids)
        put("student_qexcluded.npz", rna_base_counts=base, rna_base_support=base_support,
            rna_base_address_ids=keep, projected_base_depth=base.sum(axis=1, dtype=np.int64))
        put("roster_evaluation_only.npz", donor_id=donor, rna_entity_id=ent,
            atac_same_entity_id=ent, synthetic_source=np.array(["S"] * 4),
            split=np.array(["train"] * 4))
    return out.getvalue()


@pytest.mark.parametrize("naive,swap", [(False, False), (True, False), (False, True)])
def test_semantic_measure_detects_row_value_and_axis_misalignment(tmp_path, naive, swap):
    """Classes 1 and 4: same shapes, wrong address/value or row identity."""
    path = tmp_path / "mini.zip"
    path.write_bytes(_mini_fit(naive, swap))
    m = pic.measure_fit_semantics(path)
    assert m["address_ids_missing_from_student"] == [5]
    assert m["student_counts_equal_teacher_at_same_address"] is (not naive)
    assert m["row_entity_serial_equals_row_index"] is (not swap)


@pytest.mark.skipif(not os.environ.get("JEPA_PUBLIC_FIT_ZIP"),
                    reason="public PR547 FIT not supplied")
def test_public_fit_bytes_and_measured_semantics_match_contract(contract):
    result = pic.verify_dataset(contract, Path(os.environ["JEPA_PUBLIC_FIT_ZIP"]))
    assert result["fit_bytes_and_semantics_verified"] is True
    m = contract["components"]["dataset"]["measured"]
    assert (m["cells"], m["addresses"], m["donors"]) == (1440, 2048, 36)
    assert m["address_ids_missing_from_student"] == [1672, 1673, 1674, 1675]
    assert m["student_counts_equal_teacher_at_same_address"] is True
    assert m["naive_leading_column_compaction_equals_student"] is False


def test_contract_bindings_are_accepted_by_the_integrated_journal_bridge(tmp_path, contract):
    """Fabricated CPU u0 only (never stepped): the derived bindings fit the
    #582/#586 preflight metadata, so a future driver can carry them."""
    pytest.importorskip("torch")
    from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
    from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
    from tests.test_jepa_v5_full_state_readonly_audit_v1 import fixture
    from tests.test_jepa_v5_structured_journal_preflight_v1 import probe
    b = contract["journal_bindings"]
    online, teacher, predictor, optimizer, meta = fixture(updates=0)
    meta.update(run_id="contract-bound", gene_axis_sha256=b["gene_axis_sha256"],
                source_manifest_sha256=b["source_manifest_sha256"],
                source_rights_sha256=b["source_rights_sha256"],
                keyed_philox_contract_sha256=b["philox_contract_sha256"],
                config_sha256=b["config_sha256"])
    raw, _ = state.to_verified_bytes(state.capture_readonly_bundle(
        online=online, teacher=teacher, predictor=predictor,
        optimizer=optimizer, metadata=meta))
    opened = bridge.open_synthetic_journal(
        root=tmp_path / "run", custody=tmp_path / "head", run_id="contract-bound",
        horizon=1, panel_sha256=meta["panel_sha256"], config_sha256=b["config_sha256"],
        rights_sha256=b["source_rights_sha256"], gene_axis_sha256=b["gene_axis_sha256"],
        source_manifest_sha256=b["source_manifest_sha256"],
        philox_contract_sha256=b["philox_contract_sha256"],
        keyed_run_seed=meta["keyed_run_seed"], state_bytes=raw,
        reported_probe=probe(0, raw, panel=meta["panel_sha256"]))
    assert opened["training_authorized"] is False
