"""The bridge to the shared qualification interface (PR #223), tested against its pinned commit.

These tests need the interface worktree at the pinned commit (env V77_QUALIFICATION_INTERFACE, or
the default path below). Where it is absent they SKIP and say so; a skip proves nothing, so the
committed qualification receipt, produced against the pinned commit, is the evidence. Two tests are
adversarial: a tampered batch mask and an operator outside its cell's source must be refused by the
interface's own validators, which shows the cross-checks can fail.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
V77 = ROOT / "scripts" / "v77"
sys.path.insert(0, str(V77))
IFACE = Path(os.environ.get("V77_QUALIFICATION_INTERFACE", "D:/jepa_wt_qualification_iface_f6d63b2f"))

if not (IFACE / "src" / "sea_ad_jepa" / "qualification").is_dir():
    pytest.skip(f"PR #223 interface worktree not available at {IFACE}; these tests prove nothing here",
                allow_module_level=True)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


B = _load(V77 / "v77_qualification_bridge.py", "v77_qualification_bridge")
T = _load(ROOT / "tests" / "v77" / "test_v77_synthetic_batch_adapter.py", "adapter_fixture_for_bridge")
Q, IFACE_INFO = B.load_interface(IFACE)
ADDRESS_IDS = [f"addr{i}" for i in range(T.N_ADDR)]


def _batch(tmp_path, conv=None):
    world = T._world(tmp_path)
    conv = conv or T._conv(world, hidden_fraction=0.3)
    return conv, B.build_qualification_batch(
        Q, conv, world=world, obs_dir="TESTOBS", universe=T.UNIVERSE, address_ids=ADDRESS_IDS,
        registry_check=False, experiment_run_id="bridge-test", realization_id="TEST_REALIZATION",
        code_commit="test", environment_digest="0" * 64)


def test_interface_is_the_pinned_commit():
    assert IFACE_INFO["commit"] == B.INTERFACE_COMMIT


def test_batch_validates_and_zero_update_sees_only_model_and_operator_fields(tmp_path):
    _, batch = _batch(tmp_path)
    protocol, out, seen = B.run_plumbing_qualification(Q, batch)
    assert seen["model_inputs"] == ["gene_ids", "hidden_target_mask", "measurement_mask", "student_expression"]
    assert seen["lawful_operator_context"] == ["n_measured", "operator_index", "source_index", "visible_library_size"]
    assert seen["readout_only"] == ["full_library_size", "query_counts"] and seen["split_only"] == ["donor_id"]
    assert out.mutation_proof_status.value == "NOT_PROVEN_BY_SHARED_INTERFACE", (
        "the shared interface cannot prove absence of mutation; the receipt must not claim it")
    assert protocol.estimand_spec == B.UNSET and protocol.threshold_status.value == B.UNSET


def test_no_oracle_or_hidden_value_is_model_visible(tmp_path):
    _, batch = _batch(tmp_path)
    vis = {f.declaration.name: f.declaration.visibility.value for f in batch.fields}
    assert "ORACLE_ONLY" not in vis.values()
    assert vis["query_counts"] == "READOUT_ONLY" and vis["donor_id"] == "SPLIT_ONLY"
    assert not set(batch.model_view().model_inputs) & {"query_counts", "full_library_size", "donor_id",
                                                        "global_cell_index", "source_index", "operator_index"}


def test_interface_refuses_a_batch_mask_that_differs_from_producer_support(tmp_path):
    conv = T._conv(T._world(tmp_path / "w"), hidden_fraction=0.3)
    flipped = conv.model.measurement_mask.copy()
    flipped[0, 0] = not flipped[0, 0]
    bad = dataclasses.replace(conv, model=dataclasses.replace(conv.model, measurement_mask=flipped))
    with pytest.raises(Q["identity"].MeasurementSupportError):
        _batch(tmp_path / "b", conv=bad)


def test_interface_refuses_an_operator_outside_its_cells_source(tmp_path):
    conv = T._conv(T._world(tmp_path / "w"), hidden_fraction=0.3)
    op = conv.operator_context.operator_index.copy()
    op[0] = 2                                              # cell 0 is SEA_AD; operator 2 is NPH52
    bad = dataclasses.replace(conv, operator_context=dataclasses.replace(conv.operator_context, operator_index=op))
    with pytest.raises(Q["identity"].ObservationOperatorIdentityError):
        _batch(tmp_path / "b", conv=bad)


def test_bridge_refuses_an_interface_worktree_at_another_commit():
    with pytest.raises(B.BridgeContractError):
        B.load_interface(ROOT)
