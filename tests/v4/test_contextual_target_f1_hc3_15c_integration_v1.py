from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules():
    adapter = load(ROOT / "scripts/v4/contextual_target_f1_hc3_15c_adapter_v1.py", "adapter15c")
    fixtures = load(ROOT / "scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py", "fixtures15c")
    return adapter, fixtures


def payload(adapter, fixtures):
    p = fixtures.base_payload()
    donors=adapter.load_selected_design()[0]["donor_order"];records={}
    for i,donor in enumerate(donors):
        records[donor]={key:p[key][i] for key in adapter.VECTOR_FIELDS};records[donor]["evidence_A"]=p["evidence_A"][i]
        for family in adapter.FAMILY_FIELDS:records[donor][family]={program:p[family][program][i] for program in p[family]}
    return {"donor_records":records,"legal":True}


def test_selected_design_and_synthetic_baseline():
    adapter, fixtures = modules()
    schema, x = adapter.load_selected_design()
    assert schema["selected_triple"] == [5, 0, 4]
    assert x.shape == (104, 16)
    result = adapter.qualify_synthetic(payload(adapter, fixtures))
    assert result["qualified"] is True
    assert result["reports"]["nuisance"]["rank"] == 16
    assert result["reports"]["nuisance"]["df"] == 88


def test_donor_permutation_is_identity_aligned():
    adapter, fixtures = modules()
    p = payload(adapter, fixtures)
    base = adapter.qualify_synthetic(p)
    q = copy.deepcopy(p)
    q["donor_records"]={k:q["donor_records"][k] for k in reversed(list(q["donor_records"]))}
    assert adapter.qualify_synthetic(q)["gates"] == base["gates"]


@pytest.mark.parametrize("mutation", ["omit", "duplicate", "forge", "nonfinite"])
def test_fail_closed_attacks(mutation):
    adapter, fixtures = modules()
    p = payload(adapter, fixtures)
    if mutation == "omit":
        p["donor_records"].pop(next(iter(p["donor_records"])))
    elif mutation == "duplicate":
        p["donor_records"]["fake::donor"]=p["donor_records"].pop(next(iter(p["donor_records"])))
    elif mutation == "forge":
        p["hc3_pass"] = True
    else:
        p["donor_records"][next(iter(p["donor_records"]))]["overall_A"] = float("nan")
    with pytest.raises(ValueError):
        adapter.qualify_synthetic(p)


@pytest.mark.parametrize("value", [False, "True", "False", 1, 0, [], {}, None, np.bool_(True)])
def test_only_literal_true_can_pass_legal_boundary(value):
    adapter, fixtures = modules()
    p = payload(adapter, fixtures)
    p["legal"] = value
    if value is False:
        assert adapter.qualify_synthetic(p)["gates"]["legal_provenance"] is False
    else:
        with pytest.raises(ValueError):
            adapter.qualify_synthetic(p)


def test_real_execution_remains_unset():
    adapter, _ = modules()
    with pytest.raises(ValueError, match="UNSET"):
        adapter.integrate_real_records([], None)
