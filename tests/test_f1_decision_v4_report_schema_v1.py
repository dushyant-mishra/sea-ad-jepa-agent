from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "scripts/v4/contextual_target_f1_decision_v4.py"


def load():
    spec = importlib.util.spec_from_file_location("decision_v4_report_schema", V4)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def payload(mod):
    n = 104
    rng = np.random.default_rng(20260905)
    source = np.asarray(["HVS"] * 41 + ["NPH52"] * 17 + ["SEA_AD"] * 46, dtype=object)
    base = 0.35 + np.linspace(-0.08, 0.08, n) + rng.normal(0, 0.01, n)
    program = {
        p: (base + 0.003 * i + rng.normal(0, 0.002, n)).tolist()
        for i, p in enumerate(mod.PROGRAMS)
    }
    direct = {
        p: (0.04 + 0.002 * i + np.linspace(-0.01, 0.01, n) + rng.normal(0, 0.002, n)).tolist()
        for i, p in enumerate(mod.PROGRAMS)
    }
    qprog = {
        p: (0.03 + 0.001 * i + np.linspace(-0.008, 0.008, n) + rng.normal(0, 0.002, n)).tolist()
        for i, p in enumerate(mod.PROGRAMS)
    }
    evidence = np.stack([base + 0.03 * j + rng.normal(0, 0.002, n) for j in range(5)], axis=1)
    return {
        "overall_A": base.tolist(),
        "program_A": program,
        "program_delta": direct,
        "evidence_A": evidence.tolist(),
        "qid_margin": (0.07 + np.linspace(-0.02, 0.02, n) + rng.normal(0, 0.002, n)).tolist(),
        "qid_win_minus_half": (0.06 + np.linspace(-0.015, 0.015, n) + rng.normal(0, 0.002, n)).tolist(),
        "program_qid_margin": qprog,
        "draw0": (base + 0.01).tolist(),
        "draw1": (base + 0.015).tolist(),
        "nuisance_y": base.tolist(),
        "source_group": source.tolist(),
        "nuisance_columns": {
            "support_depth": np.linspace(-1.0, 1.0, n).tolist(),
            "operator_mix": np.sin(np.linspace(0, 3.0, n)).tolist(),
        },
        "legal": True,
    }


def test_report_schema_exposes_existing_program_arithmetic_only():
    mod = load()
    p = payload(mod)
    result = mod.qualify_current(p)
    v1 = mod.arithmetic()

    assert set(result["reports"]["direct_program"]) == set(mod.PROGRAMS)
    assert set(result["reports"]["qid_program"]) == set(mod.PROGRAMS)

    expected_direct = {name: v1.t_interval(p["program_delta"][name]) for name in mod.PROGRAMS}
    expected_qprog = {name: v1.t_interval(p["program_qid_margin"][name]) for name in mod.PROGRAMS}
    assert result["reports"]["direct_program"] == expected_direct
    assert result["reports"]["qid_program"] == expected_qprog

    expected_dneg = v1.holm([
        expected_direct[name]["p_negative"] if expected_direct[name]["estimable"] else 0.0
        for name in mod.PROGRAMS
    ])
    expected_qneg = v1.holm([
        expected_qprog[name]["p_negative"] if expected_qprog[name]["estimable"] else 0.0
        for name in mod.PROGRAMS
    ])
    assert np.array_equal(
        expected_dneg,
        np.asarray([result["reports"]["direct_negative_holm"][name] for name in mod.PROGRAMS]),
    )
    assert np.array_equal(
        expected_qneg,
        np.asarray([result["reports"]["qid_program_negative_margin_holm"][name] for name in mod.PROGRAMS]),
    )

    assert result["gates"]["no_contextual_minus_direct_degradation"] == bool(
        all(expected_direct[name]["estimable"] for name in mod.PROGRAMS)
        and np.all(expected_dneg >= mod.ALPHA)
    )
    assert result["gates"]["no_qid_v2_program_negative_margin"] == bool(
        all(expected_qprog[name]["estimable"] for name in mod.PROGRAMS)
        and np.all(expected_qneg >= mod.ALPHA)
    )


def test_nonestimable_program_remains_visible_in_report():
    mod = load()
    p = payload(mod)
    p["program_delta"]["local"] = [0.0] * 104
    p["program_qid_margin"]["local"] = [0.0] * 104
    result = mod.qualify_current(p)
    assert result["reports"]["direct_program"]["local"]["estimable"] is False
    assert result["reports"]["qid_program"]["local"]["estimable"] is False
    assert result["gates"]["no_contextual_minus_direct_degradation"] is False
    assert result["gates"]["no_qid_v2_program_negative_margin"] is False
