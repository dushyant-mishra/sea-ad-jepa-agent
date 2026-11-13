"""DEV2048 pilot pre-flight tests (non-executing; explicit no-step inventory).

Model construction only where noted; the canonical route is replaced by a
mock. No forward, backward, optimizer step or EMA. The public PR547 FIT is
used only when JEPA_PUBLIC_DEV_FIT_ZIP or JEPA_PUBLIC_FIT_ZIP points to it.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from unittest import mock

import pytest
import torch

from scripts.v5 import jepa_v5_dev2048_pilot_preflight_v1 as pilot
from scripts.v5 import jepa_v5_source_data_custody_gate_v1 as gate

ROOT = Path(__file__).resolve().parents[1]
REFUSED = pilot.PilotPreflightRefusal
Q = list(pilot.Q)
FIT = os.environ.get("JEPA_PUBLIC_DEV_FIT_ZIP") or os.environ.get("JEPA_PUBLIC_FIT_ZIP")


def _mask(cells=4, genes=2048):
    measured = torch.ones(cells, genes, dtype=torch.bool)
    measured[:, Q] = False
    return measured


def _blocks(measured):
    keys = torch.arange(len(measured), dtype=torch.int64) + pilot.CELL_KEY_OFFSET
    return pilot.sample_m1_target_blocks(measured, keys)


class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.a = torch.nn.Linear(3, 2)
        self.b = torch.nn.Linear(2, 2)


def _toy_modules(**overrides):
    online = Toy()
    teacher = Toy().eval()
    teacher.load_state_dict(online.state_dict())
    for p in teacher.parameters():
        p.requires_grad_(False)
    predictor = torch.nn.Linear(2, 1)
    params = list(online.parameters()) + list(predictor.parameters())
    built = dict(online=online, teacher=teacher, predictor=predictor,
                 optimizer=torch.optim.AdamW(params, lr=1e-4))
    built.update(overrides)
    return mock.Mock(**built)


# ------------------------------------------------------------ target leakage

def test_sampled_m1_blocks_have_members_exactly_equal_to_hidden_genes():
    measured = _mask()
    report = pilot.validate_target_blocks(_blocks(measured), measured)
    assert report["hidden_per_cell"] == [int(0.40 * 2044)] * 4


@pytest.mark.parametrize("attack", ["visible_member", "repeated", "query", "unmeasured", "padding"])
def test_leaky_or_malformed_blocks_refused(attack):
    measured = _mask()
    blocks = _blocks(measured)
    row0 = blocks.member_mask[0]
    first = tuple(torch.nonzero(row0)[0].tolist())
    second = tuple(torch.nonzero(row0)[1].tolist())
    visible = int(torch.nonzero(measured[0] & ~blocks.hidden_mask[0])[0])
    if attack == "visible_member":       # hidden mask unchanged
        blocks.indices[(0, *first)] = visible
    elif attack == "repeated":
        blocks.indices[(0, *second)] = blocks.indices[(0, *first)]
    elif attack == "query":
        blocks.indices[(0, *first)] = Q[0]
    elif attack == "unmeasured":
        measured[0, int(blocks.indices[(0, *first)])] = False
    else:
        pad = tuple(torch.nonzero(~row0)[0].tolist())
        blocks.indices[(0, *pad)] = visible
    with pytest.raises(REFUSED, match="TARGET_BLOCK"):
        pilot.validate_target_blocks(blocks, measured)


# ------------------------------------------------- EMA pairing / ownership

def test_real_original_v5_modules_pass_pairing_and_ownership():
    from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules
    from scripts.v5.jepa_v5_live_model_u0_journal_connector_v1 import CONFIG
    modules = build_reference_modules(**CONFIG)          # construction only
    report = pilot.validate_ema_pairing(modules)
    assert report["teacher_in_optimizer"] is False
    assert report["optimizer_tensors"] == report["paired_tensors"] + report["predictor_tensors"]


def test_toy_pairing_control_passes():
    pilot.validate_ema_pairing(_toy_modules())


@pytest.mark.parametrize("case", ["order", "teacher_in_optimizer", "predictor_missing",
                                  "teacher_trainable", "shared_tensor"])
def test_bad_pairing_or_ownership_refused(case):
    m = _toy_modules()
    if case == "order":
        class Swapped(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.b = torch.nn.Linear(2, 2)
                self.a = torch.nn.Linear(3, 2)
        m.teacher = Swapped().eval()
        for p in m.teacher.parameters():
            p.requires_grad_(False)
    elif case == "teacher_in_optimizer":
        m.optimizer = torch.optim.AdamW(list(m.online.parameters()) + list(m.predictor.parameters())
                                        + [next(m.teacher.parameters())], lr=1e-4)
    elif case == "predictor_missing":
        m.optimizer = torch.optim.AdamW(list(m.online.parameters()), lr=1e-4)
    elif case == "teacher_trainable":
        next(m.teacher.parameters()).requires_grad_(True)
    else:
        m.teacher.a.weight = m.online.a.weight
    with pytest.raises(REFUSED):
        pilot.validate_ema_pairing(m)


# --------------------------------------------------- authorization + route

EXPECTED = {"code_commit": "c" * 40, "contract_sha256": "d" * 64}


def _authorization(**changes):
    record = {"schema": pilot.AUTHORIZATION_SCHEMA, "milestone": "M1", "horizon": 1,
              "rows": list(pilot.M1_ROWS), "half_life_presentations": 22136,
              "encoder_input_mode": pilot.ENCODER_INPUT_MODE,
              "contract_sha256": "d" * 64, "fit_zip_sha256": "e" * 64,
              "premise_state_blob": "f" * 40, "code_commit": "c" * 40,
              "run_directory": "/home/x/pilot", "owner": "owner", "authorized_on": "D",
              "expires_on": "D", "owner_authorized": True}
    record.update(changes)
    return record


def _inputs(rows=pilot.M1_ROWS):
    measured = _mask(len(rows))
    return {"mode": pilot.ENCODER_INPUT_MODE, "rows": tuple(rows),
            "expression": torch.zeros(len(rows), 2048), "measurement_mask": measured,
            "stable_cell_keys": torch.arange(len(rows)) + pilot.CELL_KEY_OFFSET,
            "operator_ids": [0] * len(rows), "measured_tokens_by_operator": {0: 2044},
            "scientific_cell_weights": torch.ones(len(rows))}


def _good_report(half_life=22136, cells=16):
    want = pilot.expected_presentation_ema(parent_presentations_seen=0, base_cells=cells,
                                           half_life_presentations=half_life)
    return {"optimizer_step_before": 0, "optimizer_step_after": 1,
            "guarded_optimizer_step": True, "guarded_ema": True,
            "ema_presentations_this_update": cells, "ema_half_life_presentations": half_life,
            "ema_child_presentations_seen": cells, "ema_momentum_used": want["momentum"],
            "presentation_ema_completion_proof": {"schema": "fake"}}


def _run(route_report, authorization=None, inputs=None, blocks=None):
    from sea_ad_jepa.v5 import ema_bound_runtime_proof_v1 as ema_v1
    inputs = inputs or _inputs()
    blocks = blocks or _blocks(inputs["measurement_mask"])
    route = mock.Mock(return_value=route_report)
    with mock.patch.object(ema_v1, pilot.CANONICAL_ROUTE[1], route):
        try:
            record = pilot.run_authorized_one_update(
                modules=_toy_modules(), inputs=inputs, blocks=blocks, authority=object(),
                authorization=authorization if authorization is not None else _authorization(),
                expected_authorization=EXPECTED, half_life_presentations=22136)
        except REFUSED as exc:
            return None, route, exc
    return record, route, None


def test_mocked_canonical_route_called_once_and_record_carries_ema_fields():
    record, route, exc = _run(_good_report())
    assert exc is None and route.call_count == 1
    kwargs = route.call_args.kwargs
    assert "ema_momentum" not in kwargs and kwargs["half_life_presentations"] == 22136
    assert kwargs["update_index"] == 0 and kwargs["run_seed"] == pilot.RUN_SEED
    assert (record.presentations_this_update, record.child_presentations_seen) == (16, 16)
    assert record.momentum == pytest.approx(0.5 ** (16 / 22136))
    assert len(record.completion_proof_sha256) == 64 and record.biological_result is False


@pytest.mark.parametrize("breakage", ["no_step", "no_ema", "momentum", "no_proof", "cells"])
def test_report_that_does_not_prove_one_step_then_one_ema_is_refused(breakage):
    report = _good_report()
    if breakage == "no_step":
        report["optimizer_step_after"] = 0
    elif breakage == "no_ema":
        report["guarded_ema"] = False
    elif breakage == "momentum":
        report["ema_momentum_used"] = 0.996
    elif breakage == "no_proof":
        report["presentation_ema_completion_proof"] = None
    else:
        report["ema_presentations_this_update"] = 15
    _, route, exc = _run(report)
    assert route.call_count == 1 and "DOES_NOT_PROVE_ONE_STEP_THEN_ONE_EMA" in str(exc)


@pytest.mark.parametrize("authorization", [
    {}, _authorization(owner_authorized=False), _authorization(milestone="M2"),
    _authorization(horizon=2), _authorization(encoder_input_mode="TEACHER_ONLY_QUERY"),
    _authorization(code_commit="0" * 40)])
def test_missing_or_wrong_authorization_refused_before_the_route(authorization):
    _, route, exc = _run(_good_report(), authorization=authorization)
    assert exc is not None and route.call_count == 0


def test_leaked_block_refused_before_the_route_is_called():
    inputs = _inputs()
    blocks = _blocks(inputs["measurement_mask"])
    member = tuple(torch.nonzero(blocks.member_mask[0])[0].tolist())
    visible = int(torch.nonzero(inputs["measurement_mask"][0] & ~blocks.hidden_mask[0])[0])
    blocks.indices[(0, *member)] = visible
    _, route, exc = _run(_good_report(), inputs=inputs, blocks=blocks)
    assert "TARGET_BLOCK_MEMBER_NOT_HIDDEN" in str(exc) and route.call_count == 0


# -------------------------------------------------------- inputs (q, depth)

@pytest.mark.skipif(not FIT, reason="public PR547 FIT not supplied")
def test_shared_base_input_excludes_query_values_for_teacher_and_student():
    from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens
    inputs = pilot.build_shared_base_inputs(Path(FIT))
    expr, measured = inputs["expression"], inputs["measurement_mask"]
    assert set(inputs) >= {"expression", "measurement_mask"} and "depth" not in str(sorted(inputs))
    assert not bool(measured[:, Q].any()) and not bool((expr[:, Q] != 0).any())
    blocks = pilot.sample_m1_target_blocks(measured, inputs["stable_cell_keys"])
    pilot.validate_target_blocks(blocks, measured)
    teacher_ids = pack_valid_tokens(expr, measured).canonical_gene_ids
    student_ids = pack_valid_tokens(expr, measured & ~blocks.hidden_mask).canonical_gene_ids
    for ids in (teacher_ids, student_ids):
        assert not set(Q) & set(ids.flatten().tolist())
    assert int(measured.sum(dim=1)[0]) == 1988 and inputs["rows"] == pilot.M1_ROWS


def test_pilot_module_never_reads_the_teacher_member_or_a_depth_field():
    source = (ROOT / "scripts/v5/jepa_v5_dev2048_pilot_preflight_v1.py").read_text(encoding="utf-8")
    code = ast.parse(source)
    constants = [n.value for n in ast.walk(code) if isinstance(n, ast.Constant)
                 and isinstance(n.value, str)]
    assert not any("teacher_measured" in c and "carries" not in c for c in constants[1:])
    assert "projected_base_depth" not in source


# ------------------------------------------------- separate dev checkpoint

def test_dev_checkpoint_path_must_be_outside_the_u0_only_journal(tmp_path):
    u0 = tmp_path / "u0-only"
    u0.mkdir()
    (u0 / "run.lock.json").write_text(json.dumps({"original_v5_u0_only": True}))
    with pytest.raises(REFUSED, match="U0_ONLY_JOURNAL"):
        pilot.require_separate_dev_checkpoint_path(u0 / "u00001", u0_journal_root=u0)
    assert pilot.require_separate_dev_checkpoint_path(
        tmp_path / "dev2048-pilot", u0_journal_root=u0) == (tmp_path / "dev2048-pilot").absolute()


# ------------------------------------------------------------- lineage

def _calls(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            names.add(getattr(f, "attr", getattr(f, "id", None)))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names |= {a.name for a in node.names} | {getattr(node, "module", None) or ""}
    return names


def test_canonical_route_reaches_the_pr224_actor_and_never_the_v4_trainer_or_toy():
    chain = {
        "src/sea_ad_jepa/v5/_ema_bound_runtime_proof_impl_v1.py": "run_guarded_inactive_reference_update",
        "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py": "run_inactive_reference_update",
        "src/sea_ad_jepa/v5/inactive_update_reference.py": "KeyedIPBEncoderV2Reference",
    }
    forbidden = {"healthy_teacher_qualification_runner_v1", "update_ema_target",
                 "EMATargetEncoder", "create_ema_target", "ema_target_module",
                 "EMAOptimizerStepController", "TinyStudent", "production_update",
                 "build_teacher_student_components", "execute_scaled_backward",
                 "execute_post_backward_protocol", "production_amp_smoke"}
    files = [*chain, "scripts/v5/jepa_v5_dev2048_pilot_preflight_v1.py",
             "src/sea_ad_jepa/v5/ema_bound_runtime_proof_v1.py",
             "src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py"]
    for path, required in chain.items():
        assert required in _calls(path), path
    for path in files:
        assert not (_calls(path) & forbidden), path
    pilot_names = _calls("scripts/v5/jepa_v5_dev2048_pilot_preflight_v1.py")
    assert "sample_uniform_target_blocks" in pilot_names          # the only V4 runtime use
    assert not pilot_names & {"run_guarded_inactive_reference_update",
                              "run_inactive_reference_update"}
    assert set(pilot.INTENTIONAL_V4) <= set(gate.EXECUTED_CLOSURE_GIT_BLOBS)
