#!/usr/bin/env python3
"""Fail-closed identity contract for the actual V5 DEV2048 pipeline.

CONTRACT ONLY. It describes and checks *which* code, data, molecular axis,
rights, teacher/target provenance, held-out panels and checkpoint layer a
future V5 run would have to use. It never imports the model, never runs a
forward/backward pass, optimizer step or EMA update, and confers no
authority: every authorization flag is False and must stay False.

Reuses, never duplicates:
- the #584/#587 source/data gate (15 declared + 19 executed V5 files, PR548
  adapter, PR547 public FIT bytes);
- the #582/#586 journal, preflight and checker (custody layer pins);
- PR525's post-target planning contract, recorded as a NON-ACTOR whose
  4-file V4 runtime identity is identical on ``main`` and #582 and so cannot
  identify the V5 actor.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

SCHEMA = "JEPA_V5_DEV2048_PIPELINE_IDENTITY_CONTRACT_V1"
CONTRACT_PATH = ("results/target_discovery/unified_qualification_v1/"
                 "JEPA_V5_DEV2048_PIPELINE_IDENTITY_CONTRACT_V1.json")
AUTHORITY = gate.AUTHORITY
AUTHORIZATION = {
    "execution_authorized": False, "training_authorized": False,
    "optimizer_steps_authorized": False, "ema_updates_authorized": False,
    "rt1_rt8_authorized": False, "gpu_training_authorized": False,
    "real_rna_authorized": False, "sealed_controller_authorized": False,
    "stage4_authorized": False, "biological_health_proved": False,
}
ACTOR_VERSION = "V5_GUARDED_ONE_UPDATE"
DATASET_CLASS = "PR547_PUBLIC_SYNTHETIC_DEV2048_FIT_ONLY"
RIGHTS_SCOPE = "PUBLIC_SYNTHETIC_DEVELOPMENT_ONLY"
CUSTODY_LAYER_GIT_BLOBS = {  # #582 + #586 + #591 + Macha review of #591 (legacy-lane refusal)
    "scripts/v5/jepa_synth2048_attempt_journal_v2.py": "b10dbf5a983794b79ad08b4344661d1b176a169f",
    "scripts/v5/jepa_v5_structured_journal_preflight_v1.py": "3a4cd78e8e3a73983177458c6870f58a5f477c6e",
    "scripts/v5/jepa_v5_full_state_readonly_audit_v1.py": "ae79cd1b705d33d29c7d28b5481dd0b91ee19ba9",
    "scripts/v5/jepa_synth2048_checkpoint_capture_prefreeze_v1.py": "d05a7dc4e399390d882f33e63c3534ae83498933",
}
PR525_POLICY = {
    "pr": 525, "commit": "b493efc35af20bcf2adee29c47376e1dbf4b6dcd",
    "file": "scripts/v5/jepa_post_td_harness_contract_v1.py",
    "git_blob": "76341dbe6e2ef505dfb84a4a69c6505c28c899b6",
    "role": "POST_TARGET_PLANNING_CONTRACT__NON_ACTOR__NON_AUTHORIZING",
    "runtime_files": [
        "src/sea_ad_jepa/v4/teacher_student_runtime.py",
        "src/sea_ad_jepa/v4/teacher_student_checkpoint.py",
        "src/sea_ad_jepa/v4/ema.py",
        "src/sea_ad_jepa/v4/ipb_jepa.py",
    ],
    # Identical at main, PR224, PR525 and #582: blind to which V5 actor exists.
    "runtime_identity_sha256": "ae5d7d753501debffcb1d868fa6289ed0ef49d65448514011377807b695c7710",
    "present_in_integrated_tree": False,
    "may_bind_actor_identity": False,
}
FORBIDDEN_SUBSTITUTES = {
    "main_inactive_update_reference_git_blob": "3dc61b629c1d4723e7df058f72c1497c4b4c6c20",
    "legacy_fictional_runtime_path": "src/sea_ad_jepa/v5/canonical_runtime.py",
    "v4_healthy_teacher_u0_u40_driver": "scripts/v4/healthy_teacher_qualification_runner_v1.py",
}
MODEL_CONFIG = {  # PR548 run_zero_update_model_probe -> build_reference_modules
    "vocabulary_size": 2048, "width": 160, "heads": 4, "blocks": 6,
    "ffn_width": 320, "dropout": 0.1, "init_seed": 8113002,
    "gene_identity_dim": 48,  # implicit: v4/contracts.py MECHANICS_CONTRACT
}
OPTIMIZER_CONFIG = {
    "class": "AdamW", "param_groups": 1,
    "group_order": "online.parameters() then predictor.parameters()",
    "lr": 0.0001, "lr_schedule": "CONSTANT__NO_SCHEDULER_IN_V5_SOURCE",
    "betas": [0.9, 0.999], "eps": 1e-08, "weight_decay": 0.01,
    "amsgrad": False, "maximize": False,
}
TEACHER_CONFIG = {
    "construction": "deepcopy(online).eval(); requires_grad False",
    "architecture": "IDENTICAL_TO_ONLINE_STUDENT",
    "update": "EMA only, via sea_ad_jepa.v5.ema_presentation_v1",
    "external_teacher_target": "NONE",
}
REQUEST_FIELDS = {
    "actor_version", "actor_source_manifest_sha256", "dataset_class",
    "dataset_zip_sha256", "n_cells", "n_addresses", "teacher_address_ids",
    "student_address_ids", "query_withheld", "student_model_config",
    "teacher_model_config", "teacher_config", "optimizer_config",
    "rights_scope", "journal_bindings", "authorization",
}


class PipelineIdentityRefusal(ValueError):
    pass


def refuse(reason: str) -> None:
    raise PipelineIdentityRefusal("REFUSE_V5_PIPELINE_IDENTITY_V1__" + reason)


def canonical_sha256(value: object) -> str:
    """Same canonical form as PR525: sorted keys, compact, ASCII."""
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("utf-8")).hexdigest()


def _axes() -> dict:
    q = list(gate.DEV_QUERY_GENE_ADDRESSES)
    teacher = list(range(gate.DEV_ROSTER["genes"]))
    return {"teacher_address_ids": teacher, "query_withheld": q,
            "student_address_ids": [a for a in teacher if a not in q]}


def build_contract(measured: dict) -> dict:
    """The whole contract from code constants plus measured FIT semantics."""
    axes = _axes()
    actor_closure = {k: v for k, v in gate.EXECUTED_CLOSURE_GIT_BLOBS.items()}
    v4 = sorted(p for p in actor_closure if "/v4/" in p)
    body = {
        "schema": SCHEMA,
        "status": "CONTRACT_ONLY__NON_EXECUTING__CONFERS_NO_AUTHORITY",
        "authority": AUTHORITY,
        "authorization": dict(AUTHORIZATION),
        "components": {
            "actor_runtime": {
                "version": ACTOR_VERSION,
                "origin": {"pr": 224, "commit": gate.ORIGINAL_V5_HEAD},
                "entrypoint": "sea_ad_jepa.v5.inactive_guarded_update_v1:"
                              "run_guarded_inactive_reference_update",
                "requires": "PrefreezeMechanicalAuthorityV1 (none issued)",
                "updates_per_call": 1,
                "multi_update_v5_driver": "ABSENT__NEW_CODE_AND_OWNER_AUTHORITY_REQUIRED",
                "declared_canonical_files": list(gate.EXPECTED_SOURCE_RELATIVE),
                "executed_closure_git_blobs": actor_closure,
                "v4_files_executed_by_v5_path": v4,
                "v4_computational_dependencies": {
                    "src/sea_ad_jepa/v4/ipb_jepa.py": "encoder blocks, BlockPredictor, TargetBlocks",
                    "src/sea_ad_jepa/v4/gene_tokenizer.py": "GeneExpressionTokenizer",
                    "src/sea_ad_jepa/v4/contracts.py": "MECHANICS_CONTRACT.gene_identity_dim=48 (tokenizer default)",
                    "src/sea_ad_jepa/v4/masking.py": "keyed_mask_seed",
                    "src/sea_ad_jepa/v4/teacher_student_runtime.py":
                        "sample_uniform_target_blocks (PR548 input path)",
                },
                "forbidden_substitutes": dict(FORBIDDEN_SUBSTITUTES),
            },
            "input_adapter": {
                "origin": {"pr": 548}, "file": gate.READINESS_ADAPTER,
                "git_blob": gate.READINESS_BLOB,
                "model_config": dict(MODEL_CONFIG),
                "zero_update_forward_only_ci_run": 41919004065,
            },
            "dataset": {
                "class": DATASET_CLASS, "origin": {"pr": 547, "artifact_id": 13364085153},
                "zip_sha256": gate.DEV_FIT_ZIP_SHA256, "zip_bytes": gate.DEV_FIT_ZIP_BYTES,
                "member_sha256": dict(gate.DEV_FIT_MEMBERS),
                "is_full104": False, "is_real_human_rna": False,
                "is_production_41k_universe": False,
                "measured": measured,
                "known_limitations": "PR547/550 F1-F4: C2 view1-only rare/perturbation, "
                                     "q ATAC proxies, support masks identify sources, "
                                     "donors nested in source with different depth",
            },
            "molecular_coordinates": {
                "axis": "SYNTHETIC_DEV2048_INTEGER_ADDRESS",
                "gene_symbol_layer": "ABSENT__ALIAS_PAR_Y_BIN1_CLASSES_NOT_APPLICABLE_REBIND_FOR_REAL_DATA",
                "renumbering_forbidden": True, **axes,
            },
            "rights": {
                "scope": RIGHTS_SCOPE,
                "permitted": ["static byte identity", "forward-only zero-update readiness"],
                "not_permitted": ["optimizer step", "EMA update", "RT1-RT8", "GPU training",
                                  "real RNA", "sealed controller", "target selection"],
                "real_data_rights": "NONE",
            },
            "teacher_target_provenance": {
                "status": "NOT_BOUND__NO_QUALIFIED_TARGET",
                "teacher": dict(TEACHER_CONFIG),
                "pr525_target_portfolio": "UNBUILDABLE__REQUIRES_PASS_QUALIFIED_CANDIDATE",
            },
            "held_out_panels": {
                "query_addresses_withheld_from_student": axes["query_withheld"],
                "evaluation_only_roster_fields": [
                    "donor_id", "synthetic_source", "split", "perturbation_arm",
                    "rna_entity_id", "atac_same_entity_id", "atac_separate_entity_id"],
                "physical_probe_panel": "NOT_BOUND__JOURNAL_PANEL_SHA_IS_CALLER_SUPPLIED",
            },
            "checkpoint_journal": {
                "origin": {"prs": [582, 586]},
                "git_blobs": dict(CUSTODY_LAYER_GIT_BLOBS),
                "commit_route": "jepa_v5_structured_journal_preflight_v1."
                                "commit_synthetic_preflight ONLY (never the bare journal)",
                "structure_binding": "u0 names/shapes/dtypes, ordered named AdamW groups, "
                                     "all group fields except lr",
                "state_class": "SYNTHETIC_FAKE_POST_UPDATE_OR_REAL_PR224_INITIALIZED_U0_ONLY",
                "real_model_initialization_only": "ORIGINAL_PR224_V5_U0_REQUIRES_STRICT_NONTOY_BRIDGE",
                "original_v5_u0_policy": "DURABLE_MIRRORED_UNSIGNED_RUN_LOCK_U0_ONLY__DIRECT_V2_BEGIN_AND_COMMIT_REFUSED__NOT_PRODUCTION",
                "real_model_post_step_commit": "FORBIDDEN__NO_TRAINING_AUTHORIZATION",
                "real_model_qualified_target": "NOT_BOUND",
                "real_model_physical_probe_panel": "NOT_BOUND",
                "real_model_production_checkpoint": False,
                "run_directory": "WSL ext4; D: exFAT cannot host the journal",
            },
            "policy": dict(PR525_POLICY),
        },
    }
    body["journal_bindings"] = derive_bindings(body)
    body["contract_sha256"] = canonical_sha256(body)
    return body


def derive_bindings(contract: dict) -> dict:
    """The SHAs a journal/preflight call must carry; never caller-chosen."""
    c = contract["components"]
    axis = c["molecular_coordinates"]
    closure = c["actor_runtime"]["executed_closure_git_blobs"]
    return {
        "gene_axis_sha256": canonical_sha256({
            "schema": "JEPA_V5_DEV2048_GENE_AXIS_V1",
            "dataset_zip_sha256": c["dataset"]["zip_sha256"],
            "teacher_address_ids": axis["teacher_address_ids"],
            "student_address_ids": axis["student_address_ids"],
            "query_withheld": axis["query_withheld"]}),
        "source_manifest_sha256": canonical_sha256({
            "schema": "JEPA_V5_SOURCE_MANIFEST_V1",
            "executed_closure": closure,
            "custody_layer": c["checkpoint_journal"]["git_blobs"]}),
        "source_rights_sha256": canonical_sha256({
            "schema": "JEPA_V5_RIGHTS_V1", **c["rights"]}),
        "philox_contract_sha256": canonical_sha256({
            "schema": "JEPA_V5_KEYED_PHILOX_CONTRACT_V1",
            "module": "src/sea_ad_jepa/v5/keyed_rng_contract_v2.py",
            "git_blob": closure["src/sea_ad_jepa/v5/keyed_rng_contract_v2.py"],
            "keyed_rng": "PHILOX4X32_10_BY_STABLE_IDENTITY"}),
        "config_sha256": canonical_sha256({
            "model": c["input_adapter"]["model_config"],
            "optimizer": OPTIMIZER_CONFIG,
            "teacher": c["teacher_target_provenance"]["teacher"]}),
    }


def load_contract(path: Path) -> dict:
    """Parse, self-verify, and require byte-for-byte agreement with the code."""
    try:
        contract = json.loads(Path(path).read_bytes())
    except (OSError, ValueError) as exc:
        raise PipelineIdentityRefusal("REFUSE_V5_PIPELINE_IDENTITY_V1__UNREADABLE") from exc
    if type(contract) is not dict or contract.get("schema") != SCHEMA:
        refuse("SCHEMA")
    body = {k: v for k, v in contract.items() if k != "contract_sha256"}
    if contract.get("contract_sha256") != canonical_sha256(body):
        refuse("CONTRACT_SELF_DIGEST")
    if contract.get("authorization") != AUTHORIZATION or contract.get("authority") != AUTHORITY:
        refuse("CONTRACT_CLAIMS_AUTHORITY")
    measured = contract.get("components", {}).get("dataset", {}).get("measured")
    if type(measured) is not dict or contract != build_contract(measured):
        refuse("CONTRACT_DIFFERS_FROM_SOURCE_DEFINITION")
    return contract


def verify_repository(contract: dict, repo_root: Path) -> dict:
    """Every executed V5 file, adapter and custody-layer file, by Git blob."""
    root = Path(repo_root)
    gate.audit_sources(root)
    closure = gate.audit_executed_closure(
        root, require_complete=True, search_path=[str(root / "src"), str(root)])
    if contract["components"]["actor_runtime"]["executed_closure_git_blobs"] \
            != gate.EXECUTED_CLOSURE_GIT_BLOBS:
        refuse("CONTRACT_AND_SOURCE_GATE_PINS_DIFFER")
    for path, blob in contract["components"]["checkpoint_journal"]["git_blobs"].items():
        if gate._git_sha1(gate._regular_bytes(root, path)) != blob:
            refuse("CUSTODY_LAYER_CHANGED__" + path)
    if (root / FORBIDDEN_SUBSTITUTES["legacy_fictional_runtime_path"]).exists():
        refuse("LEGACY_FICTIONAL_RUNTIME_PATH_PRESENT")
    policy = root / PR525_POLICY["file"]
    if policy.exists():  # absent from #582; if merged later it stays a non-actor
        declared = gate._literal_name(gate._regular_bytes(root, PR525_POLICY["file"]),
                                      "_RUNTIME_FILES", PR525_POLICY["file"])
        if list(declared) != PR525_POLICY["runtime_files"]:
            refuse("PR525_RUNTIME_IDENTITY_FILES_CHANGED")
    return {"source_identity_complete": closure["executed_import_closure_verified"],
            "executed_closure_file_count": closure["executed_closure_file_count"],
            "custody_layer_verified": True,
            "pr525_policy_present": policy.exists(),
            "training_authorized": False, "authority": AUTHORITY}


def measure_fit_semantics(fit_zip: Path) -> dict:
    """What the FIT bytes mean, measured with numpy (no pickle, no model)."""
    import numpy as np
    with zipfile.ZipFile(fit_zip) as bundle:
        def arrays(member):
            return np.load(io.BytesIO(bundle.read(member)), allow_pickle=False)
        t = arrays("teacher_measured.npz")
        s = arrays("student_qexcluded.npz")
        r = arrays("roster_evaluation_only.npz")
    tid, sid = t["rna_address_ids"], s["rna_base_address_ids"]
    pos = {int(a): i for i, a in enumerate(tid)}
    cols = [pos.get(int(a), -1) for a in sid]
    aligned = -1 not in cols
    donor, ent = r["donor_id"], r["rna_entity_id"]
    q = sorted(set(int(a) for a in tid) - set(int(a) for a in sid))
    split = r["split"]
    return {
        "cells": int(t["rna_counts"].shape[0]),
        "addresses": int(tid.size),
        "donors": int(np.unique(donor).size),
        "synthetic_sources": sorted(str(x) for x in np.unique(r["synthetic_source"])),
        "split_cells": {str(k): int((split == k).sum()) for k in np.unique(split)},
        "teacher_address_ids_ascending_unique": bool(np.array_equal(tid, np.unique(tid))),
        "student_address_ids_ascending_unique": bool(np.array_equal(sid, np.unique(sid))),
        "address_ids_missing_from_student": q,
        "student_counts_equal_teacher_at_same_address": bool(
            aligned and np.array_equal(s["rna_base_counts"], t["rna_counts"][:, cols])),
        "student_support_equal_teacher_at_same_address": bool(
            aligned and np.array_equal(s["rna_base_support"], t["rna_support"][:, cols])),
        "naive_leading_column_compaction_equals_student": bool(np.array_equal(
            s["rna_base_counts"], t["rna_counts"][:, :sid.size])),
        "row_entity_serial_equals_row_index": all(
            str(e).endswith("CELL%05d" % i) for i, e in enumerate(ent)),
        "donor_id_equals_entity_donor_prefix": all(
            str(e).startswith("DEV_D%03d_" % int(d)) for e, d in zip(ent, donor)),
        "same_nucleus_atac_entity_equals_rna_entity": bool(
            (r["atac_same_entity_id"] == ent).all()),
        "donor_nested_in_one_source": all(np.unique(r["synthetic_source"][donor == d]).size == 1
                                          for d in np.unique(donor)),
        "donor_in_one_split": all(np.unique(split[donor == d]).size == 1
                                  for d in np.unique(donor)),
        "unmeasured_nonzero_count": int(((~t["rna_support"]) & (t["rna_counts"] != 0)).sum()),
        "measured_zero_count": int((t["rna_support"] & (t["rna_counts"] == 0)).sum()),
        "projected_depth_equals_student_count_sum": bool(np.array_equal(
            s["projected_base_depth"], s["rna_base_counts"].sum(axis=1, dtype=np.int64))),
    }


def verify_dataset(contract: dict, fit_zip: Path) -> dict:
    gate.audit_dev_fit(fit_zip)  # exact ZIP and member bytes first
    measured = measure_fit_semantics(fit_zip)
    if measured != contract["components"]["dataset"]["measured"]:
        refuse("FIT_SEMANTICS_DIFFER_FROM_CONTRACT")
    return {"fit_bytes_and_semantics_verified": True, "real_human_rna": False}


def expected_run_request(contract: dict) -> dict:
    """The only request shape this contract can call consistent."""
    c = contract["components"]
    axis = c["molecular_coordinates"]
    return {
        "actor_version": ACTOR_VERSION,
        "actor_source_manifest_sha256": contract["journal_bindings"]["source_manifest_sha256"],
        "dataset_class": DATASET_CLASS,
        "dataset_zip_sha256": c["dataset"]["zip_sha256"],
        "n_cells": c["dataset"]["measured"]["cells"],
        "n_addresses": c["dataset"]["measured"]["addresses"],
        "teacher_address_ids": list(axis["teacher_address_ids"]),
        "student_address_ids": list(axis["student_address_ids"]),
        "query_withheld": list(axis["query_withheld"]),
        "student_model_config": dict(c["input_adapter"]["model_config"]),
        "teacher_model_config": dict(c["input_adapter"]["model_config"]),
        "teacher_config": dict(c["teacher_target_provenance"]["teacher"]),
        "optimizer_config": json.loads(json.dumps(OPTIMIZER_CONFIG)),
        "rights_scope": c["rights"]["scope"],
        "journal_bindings": dict(contract["journal_bindings"]),
        "authorization": dict(AUTHORIZATION),
    }


def verify_run_request(contract: dict, request: dict) -> dict:
    """Fail closed on wrong version, data, order, rights, config or authority."""
    want = expected_run_request(contract)
    if type(request) is not dict or set(request) != REQUEST_FIELDS:
        refuse("REQUEST_FIELDS")
    if request["actor_version"] != want["actor_version"]:
        refuse("WRONG_MODEL_VERSION")
    manifest = request["actor_source_manifest_sha256"]
    if manifest == PR525_POLICY["runtime_identity_sha256"]:
        refuse("PR525_V4_RUNTIME_IDENTITY_IS_NOT_V5_ACTOR_IDENTITY")
    if manifest != want["actor_source_manifest_sha256"]:
        refuse("SOURCE_MANIFEST_MISMATCH")
    for key in ("dataset_class", "dataset_zip_sha256", "n_cells", "n_addresses"):
        if request[key] != want[key] or type(request[key]) is not type(want[key]):
            refuse("WRONG_DATA__" + key)
    for key in ("teacher_address_ids", "student_address_ids", "query_withheld"):
        if request[key] != want[key]:
            refuse("MOLECULAR_ORDER_CHANGED__" + key)
    if request["student_model_config"] != request["teacher_model_config"] \
            or request["teacher_config"] != want["teacher_config"]:
        refuse("TEACHER_STUDENT_CONFIG_INCONSISTENT")
    if request["student_model_config"] != want["student_model_config"]:
        refuse("MODEL_CONFIG_NOT_CONTRACT")
    if request["optimizer_config"] != want["optimizer_config"]:
        refuse("OPTIMIZER_CONFIG_NOT_CONTRACT")
    if request["rights_scope"] != want["rights_scope"]:
        refuse("UNAUTHORIZED_SOURCE_OR_RIGHTS")
    for key, value in want["journal_bindings"].items():
        if request["journal_bindings"].get(key) != value:
            refuse("JOURNAL_BINDING_MISMATCH__" + key)
    if set(request["journal_bindings"]) != set(want["journal_bindings"]):
        refuse("JOURNAL_BINDING_FIELDS")
    if request["authorization"] != want["authorization"]:
        refuse("AUTHORIZATION_NOT_CONFERRED_BY_CONTRACT")
    return {"status": "CONSISTENT_WITH_CONTRACT__EXECUTION_NOT_AUTHORIZED",
            "teacher_target_bound": False, "physical_probe_panel_bound": False,
            "execution_authorized": False, "training_authorized": False,
            "authority": AUTHORITY}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fit-zip", type=Path)
    parser.add_argument("--write", action="store_true",
                        help="measure --fit-zip and (re)write the contract JSON")
    args = parser.parse_args()
    path = args.repo_root / CONTRACT_PATH
    if args.write:
        if args.fit_zip is None:
            parser.error("--write needs --fit-zip")
        gate.audit_dev_fit(args.fit_zip)
        contract = build_contract(measure_fit_semantics(args.fit_zip))
        path.write_text(json.dumps(contract, indent=1, sort_keys=True) + "\n",
                        encoding="ascii", newline="\n")
    contract = load_contract(path)
    report = {"contract_sha256": contract["contract_sha256"],
              "repository": verify_repository(contract, args.repo_root)}
    if args.fit_zip is not None:
        report["dataset"] = verify_dataset(contract, args.fit_zip)
    report["run_request"] = verify_run_request(contract, expected_run_request(contract))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
