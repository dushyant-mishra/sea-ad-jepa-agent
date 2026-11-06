"""Fail-closed ORIGINAL guarded V5 -> public PR547 DEV2048 -> synthetic
#582 checkpoint-journal identity contract. STATIC VERIFICATION ONLY.

Does not import V5 model, structured journal, old V4 trainer, torch, or any
mutation module. Does not open a journal, construct a model, train, inspect
sealed V80 controller, read restricted RNA or confer a model/target/rights pass.

The genuine production-rights issuer and full V5 model-to-journal execution
path do not exist here. The only available output is a nonauthorizing
development identity receipt, tied to a physically verified public FIT file.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile

from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

SCHEMA = "JEPA_ORIGINAL_V5_DEV2048_PIPELINE_STATIC_CONTRACT_V1"
AUTHORITY = gate.AUTHORITY
CONTRACT_KIND = "STATIC_DEV_ONLY__NOT_A_RUN_OR_EXECUTION_AUTHORIZATION"
POLICY_KIND = "PR525_NONAUTHORIZING_V4_SOURCE_PLAN__NOT_V5_EXECUTOR"
DATASET_KIND = "PR547_ORIGINAL_PUBLIC_FIT_ONLY__ARTIFICIAL_NO_CONTROLLER"
JOURNAL_KIND = "PR582_FAKE_SNAPSHOT_REPORTED_PROBES_ONLY"
PANEL_KIND = "SYNTHETIC_TRAIN_ONLY_ROSTER_BOUND__NOT_FROZEN_REAL_PANEL"
NO_ISSUER = "NO_INDEPENDENT_SOURCE_RIGHTS_OR_TARGET_ISSUER"
FILE_PINS = {
    "scripts/v5/jepa_v5_source_data_custody_gate_v1.py":
        "6126722a028670538204ecfebac54ffa22a73022",
    "scripts/v5/jepa_v5_structured_journal_preflight_v1.py":
        "d056da358e1d68e57d02e16a07e9c4f9ff2a2fe1",
    "scripts/v5/jepa_v5_full_state_readonly_audit_v1.py":
        "ae79cd1b705d33d29c7d28b5481dd0b91ee19ba9",
    "scripts/v5/jepa_synth2048_attempt_journal_v2.py":
        "d5dd8c26cf7e8e99c1d665c6482ce053997fbb09",
}
ENTRYPOINTS = {
    "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py":
        {"run_guarded_inactive_reference_update"},
    "src/sea_ad_jepa/v5/inactive_update_reference.py":
        {"run_inactive_reference_update"},
    "scripts/v5/jepa_synth2048_v5_readiness.py":
        {"verified_fit", "restore_full_address_space", "audit_fit"},
    "scripts/v5/jepa_v5_structured_journal_preflight_v1.py":
        {"open_synthetic_journal", "commit_synthetic_preflight",
         "check_structured_bytes"},
    "scripts/v5/jepa_synth2048_attempt_journal_v2.py":
        {"open_journal", "begin_attempt", "commit_reported_update"},
}
ROSTER_FIELDS = {
    "donor_id", "synthetic_source", "split", "rna_entity_id",
    "atac_same_entity_id", "atac_separate_entity_id", "perturbation_arm",
}
STUDENT_FIELDS = {
    "rna_base_counts", "rna_base_support",
    "rna_base_address_ids", "projected_base_depth",
}
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


class PipelineContractRefusal(ValueError):
    """A failure to establish a static, development-only source/data identity."""


def insist(condition: bool, reason: str) -> None:
    if not condition:
        raise PipelineContractRefusal("REFUSE_V5_PIPELINE_STATIC_CONTRACT__" + reason)


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False, ensure_ascii=True).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__INVALID_JSON") from exc


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def _source_bytes(root: Path, path: str) -> bytes:
    try:
        return gate._regular_bytes(root, path)
    except gate.SourceDataRefusal as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__MISSING_OR_SYMLINK_SOURCE__"
            + path) from exc


def verify_source_interfaces(repo_root: Path) -> dict:
    """Static byte pin + function boundary checks, with ZERO module imports."""
    root = Path(repo_root)
    try:
        result = gate.audit_sources(root)
    except gate.SourceDataRefusal as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__WRONG_ORIGINAL_V5_SOURCE") from exc
    for path, expected in FILE_PINS.items():
        insist(gate._git_sha1(_source_bytes(root, path)) == expected,
               "FAKE_JOURNAL_OR_GATE_SOURCE_CHANGED__" + path)

    # The original 15-file declaration is only a *subset* of the actually
    # imported V5 + PR548 dependency closure. Macha #587 independently
    # established 35 exact in-repository modules, including legitimate V4
    # low-level utilities and package initializers. Pin their full closure
    # and Python's search-path resolution before accepting any live model.
    try:
        closure = gate.audit_executed_closure(
            root, require_complete=True,
            search_path=[str(root / "src"), str(root)])
    except gate.SourceDataRefusal as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__EXECUTED_SOURCE_CLOSURE_OR_IMPORT_SHADOW"
        ) from exc
    insist(closure["executed_import_closure_verified"] is True
           and closure["executed_closure_file_count"] == 35
           and closure["import_resolution_checked"] is True,
           "WRONG_OR_INCOMPLETE_ORIGINAL_V5_IMPORT_CLOSURE")

    for path, functions in ENTRYPOINTS.items():
        tree = ast.parse(_source_bytes(root, path), filename=path)
        found = {node.name for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        insist(functions <= found, "ACTIVE_INTERFACE_MISSING__" + path)

    # Validate the *existing* call paths, not only filenames or existence.
    # Their exact Git blobs are already pinned above.
    model = ast.parse(
        _source_bytes(root, "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py"))
    calls = {x.func.id for x in ast.walk(model)
             if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)}
    insist("run_inactive_reference_update" in calls,
           "ORIGINAL_GUARDED_V5_NO_NUMERICAL_CONSUMER_LINK")
    bridge = ast.parse(_source_bytes(
        root, "scripts/v5/jepa_v5_structured_journal_preflight_v1.py"))
    bridge_calls = {
        (x.func.value.id, x.func.attr)
        for x in ast.walk(bridge) if isinstance(x, ast.Call)
        and isinstance(x.func, ast.Attribute)
        and isinstance(x.func.value, ast.Name)
    }
    insist({("journal", "open_journal"),
            ("journal", "commit_reported_update")} <= bridge_calls,
           "FAKE_STRUCTURED_BRIDGE_NO_JOURNAL_LINK")
    # Old PR525's separate V4 planning/target policy is NOT on #582.
    # This lookup is a historical status only: we never import or attest it.
    policy_path = root / "scripts/v5/jepa_post_td_harness_contract_v1.py"
    insist(not policy_path.exists() and not policy_path.is_symlink(),
           "EXTERNAL_PR525_V4_PLAN_PRESENT__MUST_BE_RECONCILED_SEPARATELY")
    return {
        "original_v5_sources": result,
        "original_v5_source_count": 15,
        "strict_executed_v5_plus_pr548_closure": closure,
        "all_35_executed_imported_source_files_verified": True,
        "journal_and_gate_source_pins": deepcopy(FILE_PINS),
        "bounded_existing_call_paths_static_only": True,
        "post_target_pr525_v4_policy_used_as_v5_identity": False,
        "post_target_pr525_policy_verified_as_v5": False,
    }


def _read_npz_bytes(raw: bytes, expected: set[str]) -> dict:
    """Read only public artificial FIT NPZ with no pickles (not private truth)."""
    try:
        import numpy as np  # public FIT read only; NO torch or model
        with np.load(BytesIO(raw), allow_pickle=False) as data:
            insist(set(data.files) == expected, "PUBLIC_NPZ_FIELD_SET_CHANGED")
            out = {name: data[name] for name in expected}
        insist(all(v.dtype.kind not in {"O", "V"} for v in out.values()),
               "PUBLIC_NPZ_OBJECT_OR_VOID_DTYPE")
        return out
    except PipelineContractRefusal:
        raise
    except (ValueError, TypeError, OSError, KeyError, zipfile.BadZipFile) as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__UNSAFE_PUBLIC_NPZ") from exc


def audit_public_dev_rows(fit_zip: Path) -> dict:
    """Independently check sample/gene/data-role/split identities in PUBLIC FIT.

    The exact original ZIP and five member digests are verified first, before
    parsing *only* student and roster views. Teacher counts, controller truth,
    private V80 and restricted patient RNA are never loaded.
    """
    try:
        exact = gate.audit_dev_fit(fit_zip)
    except gate.SourceDataRefusal as exc:
        raise PipelineContractRefusal(
            "REFUSE_V5_PIPELINE_STATIC_CONTRACT__WRONG_PUBLIC_DEV_FIT") from exc

    import numpy as np
    with zipfile.ZipFile(fit_zip) as z:
        student = _read_npz_bytes(z.read("student_qexcluded.npz"), STUDENT_FIELDS)
        roster = _read_npz_bytes(z.read("roster_evaluation_only.npz"), ROSTER_FIELDS)
        receipt = json.loads(z.read("DEVELOPMENT_RECEIPT.json"))
    insist(receipt.get("schema") ==
           "JEPA_EXPANDED_COMMON_WORLD_DEVELOPMENT_FIT_ONLY_V1",
           "SOURCE_RECEIPT_WRONG_WORLD")
    insist(receipt.get("frozen_dimensions") == gate.DEV_ROSTER,
           "SOURCE_RECEIPT_WRONG_DIMENSIONS")
    insist(receipt.get("all_six_candidate_recoverability") == "UNASSESSED",
           "SOURCE_RECEIPT_PRETENDS_C1_C6_PASS")
    for field in ("controller_truth_exported",
                  "model_training_or_controller_scoring_executed",
                  "real_biology_or_production_authority"):
        insist(receipt.get(field) is False,
               "SOURCE_RECEIPT_FALSE_PRODUCTION_AUTHORITY__" + field)

    cells, genes, donors_n = (gate.DEV_ROSTER["cells"],
                             gate.DEV_ROSTER["genes"], gate.DEV_ROSTER["donors"])
    q = np.array(gate.DEV_QUERY_GENE_ADDRESSES, dtype=np.int32)
    expected_addresses = np.setdiff1d(np.arange(genes, dtype=np.int32), q)
    count, support, addr, depth = (student["rna_base_counts"],
                                   student["rna_base_support"],
                                   student["rna_base_address_ids"],
                                   student["projected_base_depth"])
    insist(count.shape == support.shape == (cells, len(expected_addresses)),
           "STUDENT_BASE_COUNTS_SUPPORT_WRONG_SHAPE")
    insist(count.dtype == np.dtype("int32")
           and support.dtype == np.dtype("bool")
           and addr.dtype == np.dtype("int32")
           and depth.dtype == np.dtype("int64"),
           "STUDENT_BASE_DATA_TYPE_DRIFT")
    insist(np.array_equal(addr, expected_addresses),
           "Q_REMOVAL_RENUMBERED_DUPLICATED_OR_ALIASED_ADDRESSES")
    insist(depth.shape == (cells,) and np.array_equal(
        depth, count.sum(axis=1, dtype=np.int64)),
        "WHOLE_LIBRARY_DEPTH_OR_Q_TRUTH_LEAK")
    insist(not np.any(count < 0) and not np.any(count[~support]),
           "STUDENT_UNSUPPORTED_COUNTS")
    # The physical 2044-array cannot become the canonical 2048 axis.
    expanded = np.zeros((cells, genes), dtype=np.int32)
    expanded[:, addr] = count
    insist(not np.any(expanded[:, q])
           and np.array_equal(expanded[:, expected_addresses], count),
           "CANONICAL_GENE_AXIS_MISALIGNED")

    donor, source, split = (roster["donor_id"],
                             roster["synthetic_source"],
                             roster["split"])
    insist(donor.shape == source.shape == split.shape == (cells,)
           and donor.dtype == np.dtype("int32"),
           "ROSTER_ROW_AND_DONOR_ID_TYPE_DRIFT")
    insist(len(np.unique(donor)) == donors_n
           and set(source.tolist()) == {"SYNTH_A", "SYNTH_B", "SYNTH_C"}
           and set(split.tolist()) == {"train", "val", "test"},
           "SOURCE_LABEL_DONOR_OR_SPLIT_ROLE_DRIFT")
    for d in np.unique(donor):
        mask = donor == d
        insist(len(np.unique(source[mask])) == 1
               and len(np.unique(split[mask])) == 1,
               "DONOR_LEAKED_ACROSS_SYNTH_SOURCE_OR_SPLIT")
    ids = roster["rna_entity_id"]
    insist(ids.shape == (cells,) and len(np.unique(ids)) == cells,
           "ROW_ENTITY_ID_DUPLICATED_OR_MISSING")
    # Panel is only the original *public synthetic roster*, not a frozen
    # issuer-qualified biological panel or scored evaluation universe.
    return {
        "public_zip_exact_verified": exact["exact_member_digests_verified"],
        "public_fit_zip_sha256": gate.DEV_FIT_ZIP_SHA256,
        "member_sha256": deepcopy(gate.DEV_FIT_MEMBERS),
        "schema": receipt["schema"],
        "rows": cells, "gene_addresses": genes, "synthetic_donors": donors_n,
        "original_query_ids": list(gate.DEV_QUERY_GENE_ADDRESSES),
        "source_labels": ["SYNTH_A", "SYNTH_B", "SYNTH_C"],
        "split_labels": ["train", "val", "test"],
        "donor_source_and_split_purity_checked": True,
        "rna_row_entity_ids_distinct": True,
        "student_address_axis_preserved": True,
        "student_q_values_available": False,
        "teacher_private_controller_read": False,
        "source_roster_authority": PANEL_KIND,
        "source_assay_realism_proved": False,
        "C1_to_C6_biology": "UNASSESSED",
    }


def _make_receipt(source: dict, data: dict) -> dict:
    """Construct fixed *non-executable* synthetic-only hashes, not rights."""
    axis = {"schema": "DEV2048_CANONICAL_AXIS_V1",
            "ids": list(range(gate.DEV_ROSTER["genes"])),
            "query_hidden_ids": list(gate.DEV_QUERY_GENE_ADDRESSES),
            "index_semantics": "ORIGINAL_UNSHIFTED_GENE_ADDRESS"}
    names = dict(sorted(gate.ORIGINAL_SOURCE_GIT_BLOBS.items()))
    names.update(dict(sorted(FILE_PINS.items())))
    names[gate.READINESS_ADAPTER] = gate.READINESS_BLOB
    binding = {
        "schema": SCHEMA,
        "kind": CONTRACT_KIND,
        "authority": AUTHORITY,
        "source": {
            "original_head": gate.ORIGINAL_V5_HEAD,
            "active_model": "V5_ONE_GUARDED_UPDATE_INACTIVE_NOT_AUTHORIZED",
            "all_original_15_git_blobs": names,
            "model_entrypoint":
                "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py:"
                "run_guarded_inactive_reference_update",
            "journal": JOURNAL_KIND,
            "post_target_policy": POLICY_KIND,
            "post_target_pr525_v4_source_set_is_valid_v5_executor": False,
            "static_call_path_only": source["bounded_existing_call_paths_static_only"],
        },
        "data": data,
        "coordinates": {
            "gene_axis_sha256": digest(axis),
            "gene_axis": "ORIGINAL_0_TO_2047_WITH_Q_1672_1675_HIDDEN",
            "q_ids": list(gate.DEV_QUERY_GENE_ADDRESSES),
            "donor_source_split_roster_member_sha256":
                gate.DEV_FIT_MEMBERS["roster_evaluation_only.npz"],
            "student_member_sha256":
                gate.DEV_FIT_MEMBERS["student_qexcluded.npz"],
            "public_dev_fit_only": True,
            "source_manifest_sha256": digest(names),
        },
        "locked_dev_journal_bindings": {
            "panel_sha256": digest({
                "kind": PANEL_KIND,
                "roster_member_sha256":
                    gate.DEV_FIT_MEMBERS["roster_evaluation_only.npz"],
                "status": "NONAUTHENTICATED_ONLY",
            }),
            "config_sha256": digest({
                "schema": "V5_PR548_U0_ONLY_MODEL_CONFIGURATION",
                "width": 160, "heads": 4, "blocks": 6,
                "input_gene_addresses": 2048,
                "model_source": gate.ORIGINAL_V5_HEAD,
                "actual_execution": False,
            }),
            "rights_sha256": digest({
                "schema": "UNAUTHENTICATED_DEV_FIT_RIGHTS_HOLD",
                "public_dev_fit_sha256": gate.DEV_FIT_ZIP_SHA256,
                "real_donor_RNA_allowed": False,
                "model_optimizer_training_authorized": False,
                "independent_rights_issuer": None,
            }),
            "gene_axis_sha256": digest(axis),
            "source_manifest_sha256": digest(names),
            "philox_contract_sha256": digest({
                "kind": "ORIGINAL_V5_KEYED_RNG_SOURCE_ONLY",
                "keyed_rng_git_blob":
                    gate.ORIGINAL_SOURCE_GIT_BLOBS[
                        "src/sea_ad_jepa/v5/keyed_rng_contract_v2.py"],
                "actual_rng_state_or_position_verified": False,
            }),
            "keyed_run_seed": 8113002,
            "bound_to_real_model_or_actual_checkpoint": False,
            "can_open_journal": False,
        },
        "rights_and_teacher": {
            "issuer": NO_ISSUER,
            "human_donor_source_authorized": False,
            "production_target_selected": False,
            "teacher_target_biology_proved": False,
            "evaluation_panel_scored": False,
            "held_out_real_donor_study_tech_proved": False,
            "C1_to_C6_qualified": False,
        },
        "hard_holds": {
            "train_authorized": False,
            "execution_authorized": False,
            "optimizer_step_allowed": False,
            "ema_update_allowed": False,
            "backward_allowed": False,
            "RT1_to_RT8_allowed": False,
            "stage4_authorized": False,
            "full_optimizer_teacher_amp_rng_dataloader_restore_proved": False,
            "real_cell_and_gene_token_health_measured": False,
            "production_v5_multi_update_driver_proved": False,
            "V5_model_to_journal_end_to_end_executed": False,
            "journal_writer_opened": False,
            "model_imported_by_this_contract": False,
        },
    }
    insist(not binding["hard_holds"]["journal_writer_opened"]
           and binding["rights_and_teacher"]["issuer"] == NO_ISSUER,
           "CONTRACT_INADVERTENTLY_PROMOTED")
    return {"contract": binding, "contract_sha256": digest(binding)}


def verify_claim(claimed: dict, authoritative: dict) -> None:
    """Reject changed hashes, status, model, q, source or issuer; no update API."""
    insist(type(claimed) is dict and type(authoritative) is dict,
           "CLAIM_NOT_A_CONTRACT_OBJECT")
    insist(canonical(claimed) == canonical(authoritative),
           "SOURCE_DATA_POLICY_GENE_PANEL_RIGHTS_OR_JOURNAL_IDENTITY_CHANGED")
    insist(claimed.get("contract_sha256") == digest(claimed["contract"]),
           "CLAIM_DIGEST_MISMATCH")
    insist(claimed["contract"]["hard_holds"]["train_authorized"] is False
           and claimed["contract"]["hard_holds"]["journal_writer_opened"] is False,
           "TRAIN_OR_WRITE_NOT_ALLOWED")


def build_static_contract(*, repo_root: Path, public_fit_zip: Path) -> dict:
    """Physically reverify exact public synthetic FIT and current source bytes.

    No fallback to synthetic fixture, fake caller SHA, public V80, or real RNA.
    """
    source = verify_source_interfaces(repo_root)
    data = audit_public_dev_rows(public_fit_zip)
    return _make_receipt(source, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--public-fit-zip", type=Path, required=True)
    args = parser.parse_args()
    result = build_static_contract(repo_root=args.repo_root,
                                   public_fit_zip=args.public_fit_zip)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
