"""Additive decision layer: accepted QR-HC3 result plus repaired evidence trend."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
HC3_ADAPTER = HERE / "contextual_target_f1_hc3_15c_adapter_v2.py"
SLOPE = HERE / "contextual_target_f1_evidence_slope_v1.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_evidence_trend_only(accepted_hc3_decision: dict, evidence_rows) -> dict:
    if list(accepted_hc3_decision.get("gates", {})).count("evidence_trend_one_sided_positive") != 1:
        raise ValueError("exactly one evidence-trend gate required")
    if accepted_hc3_decision.get("conclusion_bearing_hc3_method") != "REDUCED_QR_TRIANGULAR_SOLVE_HC3":
        raise ValueError("accepted QR HC3 authority required")
    before_gates = copy.deepcopy(accepted_hc3_decision["gates"])
    before_reports = copy.deepcopy(accepted_hc3_decision["reports"])
    repaired = copy.deepcopy(accepted_hc3_decision)
    report = _load(SLOPE, "f1_evidence_slope_v1_runtime").donor_trend_report(evidence_rows)
    repaired["reports"]["evidence_slope"] = {key: value for key, value in report.items() if key != "gate"}
    repaired["gates"]["evidence_trend_one_sided_positive"] = bool(report["gate"])
    repaired["qualified"] = bool(all(repaired["gates"].values()))
    repaired["legacy_v1_evidence_slope_nonauthoritative"] = True
    repaired["conclusion_bearing_evidence_slope_method"] = "PAIRED_DIFFERENCE_FLOAT64"
    if any(repaired["gates"][key] != value for key, value in before_gates.items() if key != "evidence_trend_one_sided_positive"):
        raise RuntimeError("non-evidence gate changed")
    if any(repaired["reports"][key] != value for key, value in before_reports.items() if key != "evidence_slope"):
        raise RuntimeError("non-evidence report changed")
    if repaired["reports"]["nuisance"] != before_reports["nuisance"] or repaired["gates"]["hc3_nuisance_positive"] != before_gates["hc3_nuisance_positive"]:
        raise RuntimeError("accepted HC3 changed")
    return repaired


def qualify_synthetic(synthetic: dict, *, authority_root: Path, repo_root: Path) -> dict:
    hc3 = _load(HC3_ADAPTER, "accepted_f1_hc3_adapter_v2_runtime")
    accepted = hc3.qualify_synthetic(synthetic, authority_root=authority_root, repo_root=repo_root)
    schema, _, _ = hc3.load_frozen_effective_design(authority_root)
    rows = [synthetic["donor_records"][donor]["evidence_A"] for donor in schema["donor_order"]]
    return replace_evidence_trend_only(accepted, rows)


def integrate_real_records(*_args, **_kwargs):
    raise ValueError("STOP_F1_REAL_READER_FORWARD_AUTHORITY_UNSET")
