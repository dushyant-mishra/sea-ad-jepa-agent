"""Original V5 live-module U0 -> V2 development journal, no training.

This is the real PR224 V5 model structure, not the fake torch-module fixtures
previously used by the journal tests and not the historical V4 trainer.
Only snapshots fully initialized CPU modules with EMPTY AdamW slots at u0.
Does NOT forward, backward, zero_grad, optimizer.step, EMA, restore, or import
any private V80 controller. Does NOT create a post-step write capability.

The current V2 journal requires a *caller-reported* run-panel probe even at
U0. That probe is NOT independently verified or proof of biological health.
The caller must provide it explicitly; this adapter never manufactures one.

The original public PR547 FIT and all pinned original V5 source bytes are
independently checked *before* any journal write. A static DEV contract cannot
issue patient rights, real frozen panel or owner optimizer authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from scripts.v5 import jepa_v5_dev2048_pipeline_contract_v1 as contract

SCHEMA = "JEPA_REAL_ORIGINAL_V5_U0_TO_SYNTHETIC_JOURNAL_V1"
# Do not allow the word "real" (meaning real PyTorch V5 *module* weights)
# to be misread as real biological data, a trained model or production rights.
ARTIFACT_CLASS = "QUARANTINED_PUBLIC_SYNTHETIC_DEV_U0_ONLY"
PRODUCTION_ELIGIBLE = False
REAL_DONOR_DATA_ELIGIBLE = False
REAL_TARGET_ISSUER_VERIFIED = False
REAL_PROBE_PANEL_VERIFIED = False
TOY_MODULES_ELIGIBLE = False
AUTHORITY = contract.AUTHORITY
RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
CONFIG = {
    "vocabulary_size": 2048, "width": 160, "heads": 4,
    "blocks": 6, "ffn_width": 320, "dropout": .10,
    "learning_rate": 1e-4, "betas": (.9, .999),
    "eps": 1e-8, "weight_decay": .01, "init_seed": 8113002,
}


class LiveV5JournalRefusal(ValueError):
    """No real-model U0 state is recorded when original bindings diverge."""


def require(ok: Any, reason: str) -> None:
    if not bool(ok):
        raise LiveV5JournalRefusal("REFUSE_REAL_V5_U0_JOURNAL_V1__" + reason)


@dataclass(frozen=True)
class RealV5U0Snapshot:
    """Byte-exact initialized model state, not a post-update or safe resume."""
    state_bytes: bytes
    snapshot_sha256: str
    model_structure_sha256: str
    run_id: str
    contract_sha256: str
    metadata: dict
    actual_original_v5_module_states_captured: bool = True
    completed_updates: int = 0
    actual_backward_or_optimizer_or_ema_executed: bool = False
    biological_probe_proved: bool = False
    resume_authorized: bool = False
    training_authorized: bool = False


def _validate_actual_reference_modules(modules: Any) -> None:
    """Enforce *real* original model classes and exact PR548 DEV config.

    No nn forward or optimizer method is invoked. The caller constructs the
    original V5 modules; this code only reads structural attributes.
    """
    import torch
    from sea_ad_jepa.v5.inactive_update_reference import V5ReferenceModules
    from sea_ad_jepa.v5.keyed_dropout_prototype_v2 import (
        KeyedIPBEncoderV2Reference,
    )
    from sea_ad_jepa.v4.ipb_jepa import BlockPredictor

    require(type(modules) is V5ReferenceModules,
            "NOT_ORIGINAL_V5_REFERENCE_MODULES")
    online, teacher, predictor, optimizer = (
        modules.online, modules.teacher, modules.predictor, modules.optimizer)
    require(type(online) is KeyedIPBEncoderV2Reference
            and type(teacher) is KeyedIPBEncoderV2Reference
            and type(predictor) is BlockPredictor
            and type(optimizer) is torch.optim.AdamW,
            "V4_OR_SUBSTITUTE_MODEL_OR_OPTIMIZER")
    require(online.training and predictor.training and not teacher.training,
            "ORIGINAL_V5_U0_MODEL_MODES_CHANGED")
    require(online.tokenizer.vocabulary_size == CONFIG["vocabulary_size"]
            and teacher.tokenizer.vocabulary_size == CONFIG["vocabulary_size"]
            and online.tokenizer.gene_identity.num_embeddings == CONFIG["vocabulary_size"]
            and teacher.tokenizer.gene_identity.num_embeddings == CONFIG["vocabulary_size"],
            "FULL_2048_ORIGINAL_GENE_AXIS_REQUIRED")
    # Gene identity width comes from a legitimate imported V4 *utility*
    # contract (gene_tokenizer defaults), not the old V4 trainer.
    require(online.tokenizer.gene_identity.embedding_dim == 48
            and teacher.tokenizer.gene_identity.embedding_dim == 48,
            "GENE_IDENTITY_EMBEDDING_WIDTH_48_REQUIRED")
    require(tuple(online.cell_token.shape) == (1, 1, CONFIG["width"])
            and tuple(predictor.block_mask.shape) == (1, 1, CONFIG["width"])
            and len(online.blocks) == len(teacher.blocks) == CONFIG["blocks"]
            and online.tokenizer.width == CONFIG["width"]
            and teacher.tokenizer.width == CONFIG["width"]
            and predictor.cross_attention.embed_dim == CONFIG["width"]
            and predictor.cross_attention.num_heads == CONFIG["heads"],
            "ORIGINAL_V5_SIX_BLOCK_WIDTH_HEADS_CHANGED")
    require(all(
        b.attention.heads == CONFIG["heads"]
        and b.attention.width == CONFIG["width"]
        and b.ffn[0].out_features == CONFIG["ffn_width"]
        and b.ffn[3].out_features == CONFIG["width"]
        and b.attention_dropout.p == CONFIG["dropout"]
        and b.ffn[2].p == CONFIG["dropout"]
        and b.ffn[4].p == CONFIG["dropout"]
        for b in online.blocks
    ), "ORIGINAL_V5_BLOCK_FFN_OR_DROPOUT_CHANGED")
    require(len(optimizer.param_groups) == 1 and not optimizer.state,
            "U0_ADAM_STATE_MUST_BE_EMPTY")
    group = optimizer.param_groups[0]
    require(group["lr"] == CONFIG["learning_rate"]
            and tuple(group["betas"]) == CONFIG["betas"]
            and group["eps"] == CONFIG["eps"]
            and group["weight_decay"] == CONFIG["weight_decay"]
            and group.get("amsgrad") is False
            and group.get("maximize") is False
            and group.get("foreach") in (None, False)
            and group.get("fused") in (None, False),
            "ORIGINAL_V5_ADAMW_HYPERPARAMETERS_CHANGED")
    require(all(p.device.type == "cpu" and p.grad is None
                for m in (online, teacher, predictor)
                for p in m.parameters()),
            "GPU_OR_PREEXISTING_REAL_GRADIENT_REFUSED")
    require(all(p.requires_grad is False for p in teacher.parameters()),
            "TEACHER_WAS_NOT_FROZEN")
    # Capturing at U0 only: an optimizer state with real or fake moments is
    # NOT accepted as an initialized checkpoint by this adapter.
    # The source/model SHAs and tensor shapes alone cannot authenticate the
    # PR548 initialization seed. Recreate the *original* initializer under an
    # isolated CPU RNG fork and compare ALL model/teacher/predictor tensors.
    # No forward, backward, optimizer step or EMA operation occurs.
    from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules
    with torch.random.fork_rng(devices=[]):
        expected = build_reference_modules(**CONFIG)
    for name in ("online", "teacher", "predictor"):
        observed_tensors = getattr(modules, name).state_dict()
        expected_tensors = getattr(expected, name).state_dict()
        require(set(observed_tensors) == set(expected_tensors)
                and all(torch.equal(t, expected_tensors[k])
                        for k, t in observed_tensors.items()),
                "INITIAL_WEIGHTS_NOT_PR548_EXACT_SEED")
    del expected


def _locked_contract(*, repo_root: Path, public_fit_zip: Path,
                     expected_contract: dict) -> dict:
    try:
        observed = contract.build_static_contract(
            repo_root=Path(repo_root), public_fit_zip=Path(public_fit_zip))
        contract.verify_claim(expected_contract, observed)
    except (contract.PipelineContractRefusal, OSError, ValueError) as exc:
        raise LiveV5JournalRefusal(
            "REFUSE_REAL_V5_U0_JOURNAL_V1__PUBLIC_SOURCE_DATA_CONTRACT_NOT_VERIFIED"
        ) from exc
    scope = observed["contract"]
    require(scope["rights_and_teacher"]["issuer"] == contract.NO_ISSUER
            and scope["source"]["active_model"] ==
                "V5_ONE_GUARDED_UPDATE_INACTIVE_NOT_AUTHORIZED"
            and scope["source"]["post_target_policy"] == contract.POLICY_KIND
            and scope["data"]["public_zip_exact_verified"] is True
            and scope["data"]["student_address_axis_preserved"] is True,
            "WRONG_ORIGINAL_V5_DEV_SCOPE")
    require(all(val is False for val in scope["hard_holds"].values()),
            "STATIC_SCOPE_PROMOTED_TO_TRAINING")
    return observed


def capture_real_v5_u0(*, modules: Any, repo_root: Path, public_fit_zip: Path,
                       expected_contract: dict, run_id: str) -> RealV5U0Snapshot:
    """Read-only capture of actual PR224 V5 weights, teacher, AdamW and RNG at U0.

    The original PR547 public dataset is verified as bytes but NOT supplied
    to the neural forward pass (there is no forward pass). Snapshot uses
    actual nn.Module state_dicts, never fabricated Adam moments.
    """
    require(type(run_id) is str and RUN_ID.fullmatch(run_id) is not None,
            "RUN_ID_INVALID")
    observed = _locked_contract(
        repo_root=repo_root, public_fit_zip=public_fit_zip,
        expected_contract=expected_contract)
    _validate_actual_reference_modules(modules)
    from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
    from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge

    binds = observed["contract"]["locked_dev_journal_bindings"]
    metadata = {
        "schema": state.SCHEMA,
        "run_id": run_id, "completed_updates": 0, "ema_updates": 0,
        "presentations_seen": 0, "keyed_run_seed": binds["keyed_run_seed"],
        "gene_axis_sha256": binds["gene_axis_sha256"],
        "source_rights_sha256": binds["rights_sha256"],
        "panel_sha256": binds["panel_sha256"],
        "config_sha256": binds["config_sha256"],
        "keyed_philox_contract_sha256": binds["philox_contract_sha256"],
        "source_manifest_sha256": binds["source_manifest_sha256"],
        "execution_authorized": False, "training_authorized": False,
    }
    # Mandatory in-memory direct observation of actual source V5 modules.
    # Existing validator rejects missing/mismatched teacher/Adam layout/shape.
    try:
        bundle = state.capture_readonly_bundle(
            online=modules.online, teacher=modules.teacher,
            predictor=modules.predictor, optimizer=modules.optimizer,
            metadata=metadata)
        raw, digest = state.to_verified_bytes(bundle)
        checked = bridge.check_structured_bytes(
            raw, expected_update=0, run_id=run_id,
            panel_sha256=binds["panel_sha256"],
            config_sha256=binds["config_sha256"],
            rights_sha256=binds["rights_sha256"],
            gene_axis_sha256=binds["gene_axis_sha256"],
            source_manifest_sha256=binds["source_manifest_sha256"],
            philox_contract_sha256=binds["philox_contract_sha256"],
            keyed_run_seed=binds["keyed_run_seed"])
    except (state.FullStateRefusal, bridge.StructuredJournalRefusal) as exc:
        raise LiveV5JournalRefusal(
            "REFUSE_REAL_V5_U0_JOURNAL_V1__LIVE_MODEL_OR_ADAM_STATE_INVALID") from exc
    # Snapshot must be the actual original PR224 tokenizer. The lower-level
    # fake synthetic journal deliberately supports toy fixtures for its
    # historic unit tests; that compatibility must NEVER count as evidence
    # that this real-V5 connector has accepted a production actor.
    actual_names = set(bundle["parameter_names"])
    required_live_tokenizer = {
        "online.tokenizer.value_encoder.0.weight",
        "online.tokenizer.value_encoder.0.bias",
        "online.tokenizer.value_encoder.2.weight",
        "online.tokenizer.value_encoder.2.bias",
        "teacher.tokenizer.value_encoder.0.weight",
        "teacher.tokenizer.value_encoder.0.bias",
        "teacher.tokenizer.value_encoder.2.weight",
        "teacher.tokenizer.value_encoder.2.bias",
    }
    require(required_live_tokenizer <= actual_names
            and "online.value_encoder.weight" not in actual_names
            and "teacher.value_encoder.weight" not in actual_names,
            "TOY_VALUE_ENCODER_OR_INCOMPLETE_ORIGINAL_V5_FORBIDDEN")
    require(checked["snapshot_sha256"] == digest
            and checked["state_update"] == 0
            and checked["optimizer_tensor_count"] == 0
            and checked["has_expression_value_encoder"] is True,
            "ORIGINAL_REAL_V5_U0_STATE_DID_NOT_MATCH_JOURNAL")
    return RealV5U0Snapshot(
        state_bytes=raw, snapshot_sha256=digest,
        model_structure_sha256=checked["structure_sha256"],
        run_id=run_id, contract_sha256=observed["contract_sha256"],
        metadata=metadata)


def record_real_v5_u0_to_journal(*, snapshot: RealV5U0Snapshot,
                                 modules: Any, repo_root: Path,
                                 public_fit_zip: Path,
                                 expected_contract: dict,
                                 journal_root: Path, external_custody: Path,
                                 horizon: int, caller_reported_probe: dict) -> dict:
    """Record exact real model *initialized U0* bytes via existing V2 writer.

    No biological measurement is created. This input probe remains
    CALLER_REPORTED__NOT_PHYSICALLY_PROVED, as recorded by the V2 journal.
    To prevent substitute old-state publication, re-capture and compare all
    actual module bytes structurally and by tensor value before any I/O.
    """
    require(type(snapshot) is RealV5U0Snapshot
            and snapshot.completed_updates == 0
            and snapshot.training_authorized is False
            and type(horizon) is int and horizon >= 1,
            "INVALID_OR_UNAUTHORIZED_U0_SNAPSHOT")
    _validate_actual_reference_modules(modules)
    observed = _locked_contract(repo_root=repo_root, public_fit_zip=public_fit_zip,
                                expected_contract=expected_contract)
    require(snapshot.contract_sha256 == observed["contract_sha256"],
            "CONTRACT_CHANGED_SINCE_LIVE_U0_CAPTURE")
    # Verify the original tensors have not been modified since the snapshot:
    from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
    from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
    from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal

    # Hard quarantine: this is a public synthetic U0 DEVELOPMENT receipt,
    # not an authorized production model or biological measurement. Prevent
    # caller-reported fake probe values from presenting as physical evidence.
    require(type(caller_reported_probe) is dict
            and caller_reported_probe.get("measurement_origin") ==
                journal.MEASUREMENT_ORIGIN
            and caller_reported_probe.get("state_update") == 0
            and caller_reported_probe.get("state_payload_sha256") ==
                snapshot.snapshot_sha256
            and caller_reported_probe.get("probe_panel_sha256") ==
                snapshot.metadata["panel_sha256"],
            "CALLER_REPORTED_ONLY_PROBE_REQUIRED")
    try:
        current = state.capture_readonly_bundle(
            online=modules.online, teacher=modules.teacher,
            predictor=modules.predictor, optimizer=modules.optimizer,
            metadata=snapshot.metadata)
        prior, _ = state.read_verified_bytes(
            snapshot.state_bytes, expected_sha256=snapshot.snapshot_sha256)
        # The serialized byte stream may have zip headers, so compare actual
        # in-memory tensor values, module by module, and strict Adam state.
        import torch
        require(set(current["modules"]) == set(prior["modules"]),
                "MODEL_MODULE_SET_CHANGED_SINCE_CAPTURE")
        for label in current["modules"]:
            require(set(current["modules"][label]) ==
                    set(prior["modules"][label]),
                    "MODEL_TENSOR_NAMES_CHANGED_SINCE_CAPTURE")
            for name, value in current["modules"][label].items():
                require(torch.equal(value, prior["modules"][label][name]),
                        "LIVE_MODEL_WEIGHTS_CHANGED_SINCE_CAPTURE")
        require(current["parameter_layout"] == prior["parameter_layout"]
                and current["parameter_names"] == prior["parameter_names"]
                and not current["optimizer"]["state"]
                and current["optimizer"]["param_groups"] ==
                    prior["optimizer"]["param_groups"],
                "OPTIMIZER_OR_PARAMETER_LAYOUT_CHANGED_SINCE_CAPTURE")
        binds = observed["contract"]["locked_dev_journal_bindings"]
        opened = bridge.open_synthetic_journal(
            root=journal_root, custody=external_custody, run_id=snapshot.run_id,
            horizon=horizon, panel_sha256=binds["panel_sha256"],
            config_sha256=binds["config_sha256"],
            rights_sha256=binds["rights_sha256"],
            gene_axis_sha256=binds["gene_axis_sha256"],
            source_manifest_sha256=binds["source_manifest_sha256"],
            philox_contract_sha256=binds["philox_contract_sha256"],
            keyed_run_seed=binds["keyed_run_seed"],
            state_bytes=snapshot.state_bytes,
            reported_probe=caller_reported_probe)
    except (state.FullStateRefusal, bridge.StructuredJournalRefusal,
            journal.JournalRefusal) as exc:
        raise LiveV5JournalRefusal(
            "REFUSE_REAL_V5_U0_JOURNAL_V1__STATE_OR_PROBE_NOT_RECORDABLE") from exc
    return {
        "schema": SCHEMA,
        "status": "ACTUAL_ORIGINAL_V5_INITIALIZED_U0_BYTES_RECORDED",
        "artifact_class": ARTIFACT_CLASS,
        "production_eligible": PRODUCTION_ELIGIBLE,
        "real_donor_data_eligible": REAL_DONOR_DATA_ELIGIBLE,
        "real_target_issuer_verified": REAL_TARGET_ISSUER_VERIFIED,
        "real_probe_panel_verified": REAL_PROBE_PANEL_VERIFIED,
        "toy_modules_eligible": TOY_MODULES_ELIGIBLE,
        "data_class": "PR547_PUBLIC_SYNTHETIC_DEV2048_ONLY",
        "checkpoint_class": "DEV_ONLY_U0_INITIALIZATION__NOT_PRODUCTION_CHECKPOINT",
        "source_rights_issuer_verified": False,
        "qualified_teacher_target_bound": False,
        "physical_probe_panel_bound": False,
        "synthetic_fixture_model_used": False,
        "original_v5_actual_module_weights_captured": True,
        "original_v5_u0_snapshot_sha256": snapshot.snapshot_sha256,
        "model_structure_sha256": snapshot.model_structure_sha256,
        "journal": opened,
        "completed_optimizer_steps": 0,
        "actual_model_forward_executed_by_connector": False,
        "actual_backward_or_ema_executed_by_connector": False,
        "probe_measurement_origin": journal.MEASUREMENT_ORIGIN,
        "physical_c1_c6_biology_or_collapse_proved": False,
        "post_step_journal_integration_implemented": False,
        "restore_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def assert_production_eligible(*args: Any, **kwargs: Any) -> None:
    """Fail closed, even for caller-provided 'valid' SHA or staged approvals.

    No production pipeline exists in this branch. A future independently
    signed model/data/target/probe/rights issuer must use a NEW, peer-reviewed
    implementation and owner authorization. Never promote public synthetic
    DEV U0 checkpoints, mock probes, or legacy V4 training as production.
    """
    raise LiveV5JournalRefusal(
        "REFUSE_REAL_V5_U0_JOURNAL_V1__PRODUCTION_PATH_NOT_IMPLEMENTED__"
        "PUBLIC_SYNTHETIC_AND_CALLER_REPORTED_PROBES_NOT_AUTHORIZED"
    )


def refuse_post_step_without_separate_authority(*args: Any, **kwargs: Any) -> None:
    """Deliberate hard stop. No unauthorized real V5 post-update writer."""
    raise LiveV5JournalRefusal(
        "REFUSE_REAL_V5_U0_JOURNAL_V1__POST_STEP_REAL_TRAINING_NOT_AUTHORIZED"
    )
