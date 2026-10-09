"""The handoff's q-safety probe must pass the adapter and refuse a leak. It changes only counts at
hidden-target positions: the model view, operator context and split context must not move, and the
readout must. An adapter that writes hidden values into the evidence (the S167 defect) must fail it,
and the leaky control view must always move."""
from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


FIX = _load("v77_adapter_fixture_for_handoff", ROOT / "tests" / "v77" / "test_v77_synthetic_batch_adapter.py")
H = _load("v77_runtime_handoff", ROOT / "scripts" / "v77" / "build_v77_runtime_handoff.py")


def test_probe_passes_the_adapter(tmp_path):
    world = FIX._world(tmp_path)
    r = H.hidden_value_invariance(world, FIX.UNIVERSE, obs_dir="TESTOBS")
    assert r["hidden_entries_changed"] > 0, "the fixture must give the probe something to change"
    assert r["verdict"] == "PASS" and r["leaky_control_digest_changed"], r


def test_probe_refuses_an_adapter_that_leaks_hidden_values(tmp_path, monkeypatch):
    world = FIX._world(tmp_path)
    real = H.AD.build_from_world

    def leaky(*args, **kwargs):
        conv = real(*args, **kwargs)
        m, rd = conv.model, conv.readout
        lib = np.maximum(rd.full_library_size.astype(np.float64), 1.0)[:, None]
        student = np.where(m.hidden_target_mask, np.log1p(rd.query_counts / lib * 1e4),
                           m.student_expression).astype(np.float32)
        model = H.AD.SyntheticModelBatch(gene_ids=m.gene_ids, student_expression=student,
                                         measurement_mask=m.measurement_mask,
                                         hidden_target_mask=m.hidden_target_mask)
        return dataclasses.replace(conv, model=model)

    monkeypatch.setattr(H.AD, "build_from_world", leaky)
    r = H.hidden_value_invariance(world, FIX.UNIVERSE, obs_dir="TESTOBS")
    assert r["model_digest_unchanged"] is False and r["verdict"] == "FAIL", r
