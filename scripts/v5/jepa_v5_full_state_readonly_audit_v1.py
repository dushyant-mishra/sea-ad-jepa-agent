#!/usr/bin/env python3
"""Strict read-only V5 full-state snapshot audit; no optimizer step or training.

Only for existing in-memory torch.nn modules and AdamW, including tiny synthetic
fixture modules. A passing result says model/optimizer bytes have a complete
descriptive shape; NOT that any actual update ran, that a representation is
healthy, or that bitwise next-step replay has been proved. No restore API.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from math import isfinite
import re
from typing import Mapping

import torch

SCHEMA = "JEPA_V5_FULL_STATE_READ_ONLY_AUDIT_V1"
AUTHORITY = (
    "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__"
    "STAGE4_NOT_AUTHORIZED"
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RUN = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
BINDINGS = {
    "gene_axis_sha256", "source_rights_sha256", "panel_sha256",
    "config_sha256", "keyed_philox_contract_sha256", "source_manifest_sha256",
}
META_FIELDS = BINDINGS | {
    "schema", "run_id", "completed_updates", "ema_updates",
    "presentations_seen", "keyed_run_seed", "training_authorized",
    "execution_authorized",
}
PACKAGE_FIELDS = {"metadata", "modules", "optimizer", "parameter_names",
                  "rng_state", "amp_scaler_state"}
MODULES = ("online", "teacher", "predictor")
SLOTS = {"step", "exp_avg", "exp_avg_sq"}


class FullStateRefusal(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not bool(ok):
        raise FullStateRefusal("REFUSE_FULL_STATE_AUDIT_V1__" + reason)


def _scalar_step(raw: object) -> int:
    if isinstance(raw, torch.Tensor):
        require(raw.numel() == 1 and not raw.is_complex()
                and bool(torch.isfinite(raw).all()), "ADAM_STEP_NOT_FINITE_SCALAR")
        value = float(raw.detach().cpu().item())
    else:
        require(type(raw) in (int, float) and isfinite(raw),
                "ADAM_STEP_NOT_FINITE_SCALAR")
        value = float(raw)
    require(value >= 0 and value.is_integer() and value <= 2**53,
            "ADAM_STEP_INVALID")
    return int(value)


def _tensor(value: object, *, shape: tuple[int, ...] | None = None,
            dtype: torch.dtype | None = None) -> torch.Tensor:
    require(type(value) is torch.Tensor, "EXPECTED_TENSOR_NOT_OTHER_TYPE")
    require(value.device.type == "cpu", "EXPECTED_CPU_TENSOR")
    require(not value.is_sparse and value.layout == torch.strided,
            "UNSUPPORTED_TENSOR_LAYOUT")
    require(value.numel() >= 1, "EMPTY_TENSOR")
    if shape is not None:
        require(tuple(value.shape) == shape, "TENSOR_SHAPE_MISMATCH")
    if dtype is not None:
        require(value.dtype == dtype, "TENSOR_DTYPE_MISMATCH")
    require(value.is_floating_point(), "EXPECTED_FLOATING_TENSOR")
    require(bool(torch.isfinite(value).all()), "NONFINITE_TENSOR")
    return value


def validate_metadata(meta: object) -> dict:
    require(type(meta) is dict and set(meta) == META_FIELDS,
            "METADATA_FIELDS")
    require(meta["schema"] == SCHEMA, "SCHEMA_CHANGED")
    require(type(meta["run_id"]) is str and RUN.fullmatch(meta["run_id"]) is not None,
            "RUN_ID_INVALID")
    for name in BINDINGS:
        raw = meta[name]
        require(type(raw) is str and HEX64.fullmatch(raw) is not None,
                name.upper() + "_INVALID")
    for name in ("completed_updates", "ema_updates",
                 "presentations_seen", "keyed_run_seed"):
        require(type(meta[name]) is int and meta[name] >= 0,
                "COUNTER_OR_SEED_INVALID_" + name.upper())
    require(meta["completed_updates"] == meta["ema_updates"],
            "EMA_COUNTER_DIVERGED")
    require(meta["keyed_run_seed"] < 2**32, "KEYED_SEED_OUT_OF_RANGE")
    require(meta["training_authorized"] is False
            and meta["execution_authorized"] is False, "AUTHORITY_PROMOTION")
    return dict(meta)


def _parameters(online: torch.nn.Module, teacher: torch.nn.Module,
                predictor: torch.nn.Module) -> dict[str, torch.nn.Parameter]:
    require(all(isinstance(m, torch.nn.Module)
                for m in (online, teacher, predictor)), "MODULE_TYPE")
    require(not teacher.training, "TEACHER_NOT_EVAL")
    for p in teacher.parameters():
        require(p.requires_grad is False and p.grad is None,
                "TEACHER_GRADIENT_OR_MUTATION")
    names: dict[str, torch.nn.Parameter] = {}
    for label, module in (("online", online), ("predictor", predictor)):
        for name, p in module.named_parameters():
            require(p.requires_grad is True, "UNEXPECTED_FROZEN_TRAINABLE")
            full = label + "." + name
            require(full not in names and id(p) not in {
                id(old) for old in names.values()
            }, "DUPLICATE_TRAINABLE_PARAMETER")
            names[full] = p
    require(bool(names), "NO_TRAINABLE_PARAMETERS")
    require(not any(id(p) in {id(v) for v in names.values()}
                    for p in teacher.parameters()), "TEACHER_SHARED_WITH_STUDENT")
    return names


def validate_live_adam(online: torch.nn.Module, teacher: torch.nn.Module,
                       predictor: torch.nn.Module,
                       optimizer: torch.optim.Optimizer,
                       *, completed_updates: int) -> dict:
    """Require EVERY trainable tensor to have Adam moments at u>=1.

    This blocks PyTorch's silent partial optimizer-state defaults. A state
    count or a matching *single* step is not sufficient. Does not step.
    """
    require(type(completed_updates) is int and completed_updates >= 0,
            "COMPLETED_UPDATE_INVALID")
    require(type(optimizer) is torch.optim.AdamW, "ADAMW_REQUIRED")
    names = _parameters(online, teacher, predictor)
    params = [p for group in optimizer.param_groups for p in group["params"]]
    require(len(params) == len(names) and
            {id(p) for p in params} == {id(p) for p in names.values()},
            "OPTIMIZER_PARAM_GROUP_COVERAGE_OR_DUPLICATE")
    require(len(set(id(p) for p in params)) == len(params),
            "OPTIMIZER_DUPLICATE_PARAMETER")
    require(set(optimizer.state.keys()) == set(params) if completed_updates else
            not optimizer.state, "OPTIMIZER_STATE_COVERAGE")
    by_id = {id(p): full for full, p in names.items()}
    report = {}
    for p in params:
        full = by_id[id(p)]
        require(p.dtype.is_floating_point and p.device.type == "cpu",
                "TRAINABLE_PARAMETER_NOT_CPU_FLOAT")
        _tensor(p.detach(), shape=tuple(p.shape), dtype=p.dtype)
        if completed_updates == 0:
            continue
        item = optimizer.state[p]
        # AMSGrad is intentionally not supported by this first version.
        require(type(item) is dict and set(item) == SLOTS, "ADAM_SLOT_FIELDS")
        require(_scalar_step(item["step"]) == completed_updates,
                "ADAM_STEP_NOT_EQUAL_COMPLETED")
        for name in ("exp_avg", "exp_avg_sq"):
            _tensor(item[name], shape=tuple(p.shape), dtype=p.dtype)
        require(bool((item["exp_avg_sq"] >= 0).all()),
                "ADAM_SECOND_MOMENT_NEGATIVE")
        report[full] = completed_updates
    return {
        "parameter_names": sorted(names),
        "trainable_tensor_count": len(names),
        "optimizer_state_count": len(optimizer.state),
        "all_adam_steps": report,
        "actual_optimizer_step_proved": False,
        "actual_gradient_observation_proved": False,
    }


def _deep_cpu_state(module: torch.nn.Module) -> dict:
    out = {}
    for name, tensor in module.state_dict().items():
        require(type(name) is str and type(tensor) is torch.Tensor,
                "MODULE_STATE_NONTENSOR")
        raw = tensor.detach().cpu().clone()
        # State dict buffers may be integer counters; keep their dtype.
        require(raw.numel() >= 1 and bool(torch.isfinite(raw).all()),
                "MODULE_STATE_NONFINITE")
        out[name] = raw
    require(bool(out), "MODULE_STATE_EMPTY")
    return out


def _rng_state(keyed_run_seed: int) -> dict:
    # A keyed Philox generator is stateless; the seed and cursor are in meta.
    # CPU torch state is retained for accidental non-keyed call detection.
    return {"torch_cpu": torch.get_rng_state().cpu().clone(),
            "keyed_rng": "PHILOX4X32_10_BY_STABLE_IDENTITY",
            "keyed_run_seed": keyed_run_seed}


def capture_readonly_bundle(*, online: torch.nn.Module,
                            teacher: torch.nn.Module,
                            predictor: torch.nn.Module,
                            optimizer: torch.optim.Optimizer,
                            metadata: dict) -> dict:
    meta = validate_metadata(metadata)
    measured = validate_live_adam(
        online, teacher, predictor, optimizer,
        completed_updates=meta["completed_updates"])
    modules = {
        "online": _deep_cpu_state(online),
        "teacher": _deep_cpu_state(teacher),
        "predictor": _deep_cpu_state(predictor),
    }
    # Keep Adam parameter-group hyperparameters and exact slot tensors;
    # parameter_names preserves the identity binding missing in positional
    # optimizer load_state_dict alone. This is descriptive, not a loader.
    opt = deepcopy(optimizer.state_dict())
    result = {
        "metadata": meta,
        "modules": modules,
        "optimizer": opt,
        "parameter_names": measured["parameter_names"],
        "rng_state": _rng_state(meta["keyed_run_seed"]),
        "amp_scaler_state": None,
    }
    verify_readonly_bundle(result)
    return result


def verify_readonly_bundle(bundle: object) -> dict:
    require(type(bundle) is dict and set(bundle) == PACKAGE_FIELDS,
            "PACKAGE_FIELDS")
    meta = validate_metadata(bundle["metadata"])
    state = bundle["modules"]
    require(type(state) is dict and set(state) == set(MODULES),
            "MODULES_MISSING")
    for label in MODULES:
        table = state[label]
        require(type(table) in (dict, OrderedDict) and bool(table),
                "MODULE_STATE_MISSING")
        for name, t in table.items():
            require(type(name) is str and name != "", "MODULE_TENSOR_NAME")
            require(type(t) is torch.Tensor and
                    bool(torch.isfinite(t).all()) and t.numel() >= 1,
                    "MODULE_TENSOR_NONFINITE")
    names = bundle["parameter_names"]
    require(type(names) is list and names and
            all(type(x) is str and
                (x.startswith("online.") or x.startswith("predictor."))
                for x in names)
            and sorted(set(names)) == names,
            "PARAMETER_NAMES_UNBOUND")
    optimizer = bundle["optimizer"]
    require(type(optimizer) is dict
            and set(optimizer) == {"state", "param_groups"},
            "OPTIMIZER_SCHEMA")
    groups = optimizer["param_groups"]
    slots = optimizer["state"]
    require(type(groups) is list and groups and type(slots) is dict,
            "OPTIMIZER_GROUPS_OR_STATES")
    ids = [p for g in groups for p in g["params"]]
    require(len(ids) == len(names)
            and all(type(i) is int for i in ids)
            and len(set(ids)) == len(ids),
            "OPTIMIZER_PARAM_IDS_DUPLICATE_OR_MISSING")
    require(len(slots) == (0 if meta["completed_updates"] == 0 else len(ids)),
            "ADAM_STATE_CARDINALITY")
    require(set(slots) == (set(ids) if meta["completed_updates"] else set()),
            "ADAM_STATE_KEY_COVERAGE")
    for i in ids:
        if meta["completed_updates"] == 0:
            continue
        record = slots[i]
        require(type(record) is dict and set(record) == SLOTS,
                "ADAM_SLOT_FIELDS")
        require(_scalar_step(record["step"]) == meta["completed_updates"],
                "ADAM_STEP_NOT_EQUAL_COMPLETED")
        for moment in ("exp_avg", "exp_avg_sq"):
            t = _tensor(record[moment])
            require(bool(torch.isfinite(t).all()), "ADAM_MOMENT_NONFINITE")
        require(tuple(record["exp_avg"].shape) == tuple(record["exp_avg_sq"].shape),
                "ADAM_MOMENT_SHAPE_DIFFERENT")
        require(bool((record["exp_avg_sq"] >= 0).all()),
                "ADAM_SECOND_MOMENT_NEGATIVE")
    rng = bundle["rng_state"]
    require(type(rng) is dict and set(rng) == {
        "torch_cpu", "keyed_rng", "keyed_run_seed"}, "RNG_FIELDS")
    require(type(rng["torch_cpu"]) is torch.Tensor
            and rng["torch_cpu"].dtype == torch.uint8
            and rng["torch_cpu"].ndim == 1
            and rng["torch_cpu"].numel() > 0
            and rng["keyed_rng"] == "PHILOX4X32_10_BY_STABLE_IDENTITY"
            and rng["keyed_run_seed"] == meta["keyed_run_seed"],
            "RNG_STATE_MISMATCH")
    require(bundle["amp_scaler_state"] is None, "AMP_MODE_NOT_VALIDATED")
    return {
        "schema": SCHEMA,
        "completed_updates": meta["completed_updates"],
        "ema_updates": meta["ema_updates"],
        "optimizer_tensor_count": len(slots),
        "model_modules": list(MODULES),
        "all_trainable_parameter_names_present": True,
        "full_gradient_or_amp_state_proved": False,
        "actual_step_or_bitwise_resume_proved": False,
        "biological_health_proved": False,
        "execution_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def to_verified_bytes(bundle: dict) -> tuple[bytes, str]:
    verify_readonly_bundle(bundle)
    stream = BytesIO()
    torch.save(bundle, stream)
    raw = stream.getvalue()
    return raw, sha256(raw).hexdigest()


def read_verified_bytes(raw: bytes, *, expected_sha256: str) -> tuple[dict, dict]:
    require(type(raw) is bytes and len(raw) > 0, "CHECKPOINT_BYTES")
    require(type(expected_sha256) is str
            and HEX64.fullmatch(expected_sha256) is not None
            and sha256(raw).hexdigest() == expected_sha256,
            "CHECKPOINT_SHA_CHANGED")
    try:
        bundle = torch.load(BytesIO(raw), map_location="cpu", weights_only=True)
    except Exception as exc:
        raise FullStateRefusal("REFUSE_FULL_STATE_AUDIT_V1__SAFE_LOAD_FAILED") from exc
    return bundle, verify_readonly_bundle(bundle)
