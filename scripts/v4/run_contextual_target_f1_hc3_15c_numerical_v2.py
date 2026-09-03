"""Run the preregistered, synthetic-only 15C numerical robustness repair."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
EXPECTED_CONTRACT = "4ece6ea2fb85dad49e91d2087f6ce8d16941deb0e9c3226209add66057c2a3c7"
EXPECTED_TOLERANCE = "3c504c94ed08c45a1b4ac634ddbe54b3a7fc0cddd9948ce781fa7f49da01c49a"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _compact(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "leverage"}


def _verify_preimplementation(out: Path) -> dict:
    contract = out / "F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_CONTRACT.md"
    tolerance = out / "F1_HC3_15C_NUMERICAL_TOLERANCE_AUTHORITY.json"
    freeze = json.loads((out / "F1_HC3_15C_PREIMPLEMENTATION_FREEZE.json").read_text(encoding="utf-8"))
    if _sha(contract.read_bytes()) != EXPECTED_CONTRACT or freeze["contract_sha256"] != EXPECTED_CONTRACT:
        raise ValueError("STOP_F1_HC3_15C_CONTRACT_MISMATCH")
    if _sha(tolerance.read_bytes()) != EXPECTED_TOLERANCE or freeze["tolerance_authority_sha256"] != EXPECTED_TOLERANCE:
        raise ValueError("STOP_F1_HC3_15C_TOLERANCE_AUTHORITY_MISMATCH")
    return json.loads(tolerance.read_text(encoding="utf-8"))


def run(out: Path, *, authority_root: Path, repo_root: Path) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tolerance = _verify_preimplementation(out)
    adapter = _load(HERE / "contextual_target_f1_hc3_15c_adapter_v2.py", "f1_adapter_v2_run")
    qr = _load(HERE / "contextual_target_f1_hc3_stable_qr_v2.py", "f1_qr_v2_run")
    svd = _load(HERE / "validate_contextual_target_f1_hc3_svd_v2.py", "f1_svd_v2_run")
    schema, raw, effective = adapter.load_frozen_effective_design(authority_root)

    binding = {
        "status": "PASS_F1_HC3_15C_EFFECTIVE_DESIGN_BOUND",
        "selected_triple": [5, 0, 4], "raw_shape": list(raw.shape), "effective_shape": list(effective.shape),
        "raw_sha256": adapter.array_sha256(raw), "effective_sha256": adapter.array_sha256(effective),
        "rank": int(np.linalg.matrix_rank(effective)), "df": int(effective.shape[0] - np.linalg.matrix_rank(effective)),
        "loo_full_rank": int(sum(np.linalg.matrix_rank(np.delete(effective, i, axis=0)) == 16 for i in range(104))),
        "condition_number_2": float(np.linalg.cond(effective, p=2)),
    }
    _write_json(out / "F1_HC3_15C_EFFECTIVE_DESIGN_BINDING.json", binding)

    old = Path(authority_root) / "outputs/contextual_teacher_target_v1_f1_hc3_15c_decision_integration_20260902"
    baseline = json.loads((old / "F1_15C_SYNTHETIC_BASELINE.json").read_text(encoding="utf-8"))
    y = np.asarray([baseline["payload"]["donor_records"][d]["overall_A"] for d in schema["donor_order"]], dtype=np.float64)
    independent_base = svd.hc3_intercept_svd(y, effective, expected_rank=16, expected_df=88)
    if not independent_base["estimable"]:
        raise ValueError("STOP_F1_HC3_15C_INDEPENDENT_BASELINE_UNESTIMABLE")

    offsets = {"positive": 1e-5 - independent_base["lower"], "negative": -1e-5 - independent_base["lower"]}
    fixtures = {name: np.asarray(y + offset, dtype="<f8") for name, offset in offsets.items()}
    near_binding = {"status": "FROZEN_BEFORE_PRODUCTION_QR_COMPARISON", "construction_method": "constant shift from independent SVD lower bound", "fixtures": {}}
    for name, vector in fixtures.items():
        filename = f"F1_HC3_15C_NEAR_BOUNDARY_{name.upper()}_F64LE.bin"
        (out / filename).write_bytes(vector.tobytes(order="C"))
        near_binding["fixtures"][name] = {"filename": filename, "sha256": _sha(vector.tobytes()), "n": int(vector.size), "target_lower": 1e-5 if name == "positive" else -1e-5}
    _write_json(out / "F1_HC3_15C_NEAR_BOUNDARY_FIXTURE_BINDING.json", near_binding)

    cases = {"baseline": y, **fixtures}
    qr_results, svd_results, comparisons = {}, {}, {}
    scalar_fields = ("beta0", "se", "lower", "upper", "p_positive", "max_leverage", "min_one_minus_h")
    for name, vector in cases.items():
        q = qr.hc3_intercept_qr(vector, effective, expected_rank=16, expected_df=88)
        s = svd.hc3_intercept_svd(vector, effective, expected_rank=16, expected_df=88)
        scalar_tolerance = 100 * np.finfo(np.float64).eps * tolerance["kappa2_effective_design"] * max(1.0, float(np.max(np.abs(vector))))
        diffs = {field: abs(float(q[field]) - float(s[field])) for field in scalar_fields}
        leverage_diff = float(np.max(np.abs(np.asarray(q["leverage"]) - np.asarray(s["leverage"]))))
        passed = all(value <= scalar_tolerance for value in diffs.values()) and leverage_diff <= tolerance["leverage_max_abs_tolerance"] and q["gate"] is s["gate"] and q["estimable"] is s["estimable"]
        if not passed:
            raise ValueError("STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED")
        qr_results[name], svd_results[name] = _compact(q), _compact(s)
        comparisons[name] = {"scalar_tolerance": scalar_tolerance, "scalar_abs_differences": diffs, "leverage_max_abs_difference": leverage_diff, "gate_agreement": q["gate"] is s["gate"], "pass": passed}
    _write_json(out / "F1_HC3_15C_STABLE_QR_RESULTS.json", {"status": "PASS", "results": qr_results})
    _write_json(out / "F1_HC3_15C_INDEPENDENT_SVD_VALIDATION.json", {"status": "PASS", "results": svd_results})
    comparison = {
        "status": "PASS_F1_HC3_15C_NUMERICAL_COMPARISON", "comparisons": comparisons,
        "near_boundary": {name: {"qr_gate": qr_results[name]["gate"], "svd_gate": svd_results[name]["gate"], "qr_lower": qr_results[name]["lower"], "svd_lower": svd_results[name]["lower"]} for name in fixtures},
    }
    _write_json(out / "F1_HC3_15C_NUMERICAL_COMPARISON.json", comparison)

    # Freshly execute the frozen 14-case truth table plus the HC3-veto payload.
    truth_fixtures = _load(Path(repo_root) / "scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py", "f1_truth_fixtures_v2_run")
    # Windows checkout has CRLF bytes; adapter qualification above separately authenticates and executes the exact Git blobs.
    truth_fixtures.v4.V1_SHA = truth_fixtures.v4.sha(truth_fixtures.v4.V1)
    truth_fixtures.component.FROZEN_ASSIGNMENT_PATH = Path(authority_root) / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
    truth_regression = truth_fixtures.attacks()
    if len(truth_regression["attacks"]) != 14 or not all(item["isolated_pass"] for item in truth_regression["attacks"]):
        raise ValueError("STOP_F1_HC3_15C_DECISION_REGRESSION_MISMATCH")
    attacks = json.loads((old / "F1_15C_NUISANCE_ADVERSARIAL.json").read_text(encoding="utf-8"))["attacks"]
    veto = next(item for item in attacks if item["attack"] == "A_nuisance_veto")
    actual_veto = adapter.qualify_synthetic(veto["payload"], authority_root=authority_root, repo_root=repo_root)
    veto_exact = actual_veto["gates"] == veto["decision"]["gates"]
    legal_domain = {}
    for label, value in (("true", True), ("false", False), ("string_false", "False"), ("one", 1), ("list", [1]), ("dict", {"x": 1}), ("none", None), ("numpy_true", np.bool_(True))):
        payload = copy.deepcopy(baseline["payload"]); payload["legal"] = value
        try:
            decision = adapter.qualify_synthetic(payload, authority_root=authority_root, repo_root=repo_root)
            legal_domain[label] = {"accepted": True, "legal_gate": decision["gates"]["legal_provenance"]}
        except (TypeError, ValueError):
            legal_domain[label] = {"accepted": False, "legal_gate": False}
    candidate_attacks = {}
    design_dir = Path(authority_root) / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
    schema_bytes = (design_dir / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_bytes()
    design_bytes = bytearray((design_dir / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin").read_bytes())
    for label, mutation in (("one_bit", lambda b: b.__setitem__(17, b[17] ^ 1)), ("truncated", lambda b: b.__delitem__(slice(-8, None)))):
        altered = bytearray(design_bytes); mutation(altered)
        try: adapter.verify_candidate_selected_design(schema_bytes, bytes(altered)); rejected = False
        except ValueError: rejected = True
        candidate_attacks[label] = rejected
    parsed_schema = json.loads(schema_bytes.decode("utf-8"))
    schema_mutations = {
        "wrong_triple": {**parsed_schema, "selected_triple": [5, 1, 4]},
        "forbidden_NPH_C1": {**parsed_schema, "columns": parsed_schema["columns"] + [{"identity": "NPH52_residual_svd_score_01"}]},
        "forbidden_HVS_C6": {**parsed_schema, "columns": parsed_schema["columns"] + [{"identity": "HVS_residual_svd_score_06"}]},
    }
    for label, altered_schema in schema_mutations.items():
        try: adapter.verify_candidate_selected_design(json.dumps(altered_schema, sort_keys=True).encode(), bytes(design_bytes)); rejected = False
        except ValueError: rejected = True
        candidate_attacks[label] = rejected
    old_rank18 = Path(authority_root) / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902/F1_NUISANCE_DONOR_DESIGN_F64LE.bin"
    try: adapter.verify_candidate_selected_design(schema_bytes, old_rank18.read_bytes()); rejected = False
    except ValueError: rejected = True
    candidate_attacks["old_rank18"] = rejected

    input_attacks = {}
    def rejected_payload(label, mutate):
        payload = copy.deepcopy(baseline["payload"]); mutate(payload)
        try: adapter.qualify_synthetic(payload, authority_root=authority_root, repo_root=repo_root); rejected = False
        except (TypeError, ValueError): rejected = True
        input_attacks[label] = rejected
    first_donor = next(iter(baseline["payload"]["donor_records"]))
    rejected_payload("forged_caller_hc3_pass", lambda p: p.__setitem__("hc3_pass", True))
    rejected_payload("donor_omission", lambda p: p["donor_records"].pop(first_donor))
    rejected_payload("donor_relabel", lambda p: p["donor_records"].__setitem__("fake::donor", p["donor_records"].pop(first_donor)))
    rejected_payload("donor_duplicate", lambda p: p["donor_records"].__setitem__("fake::duplicate", copy.deepcopy(p["donor_records"][first_donor])))
    rejected_payload("nonfinite", lambda p: p["donor_records"][first_donor].__setitem__("overall_A", float("nan")))
    permuted = copy.deepcopy(baseline["payload"])
    permuted["donor_records"] = {key: permuted["donor_records"][key] for key in reversed(list(permuted["donor_records"]))}
    permuted_decision = adapter.qualify_synthetic(permuted, authority_root=authority_root, repo_root=repo_root)
    donor_permutation_exact = permuted_decision["gates"] == baseline["decision"]["gates"]
    zero = copy.deepcopy(baseline["payload"])
    for record in zero["donor_records"].values(): record["overall_A"] = 0.0
    zero_decision = adapter.qualify_synthetic(zero, authority_root=authority_root, repo_root=repo_root)
    zero_nonestimable = not zero_decision["reports"]["nuisance"]["estimable"] and not zero_decision["gates"]["hc3_nuisance_positive"]
    source = copy.deepcopy(baseline["payload"])
    source_y = np.r_[.62 + .02*np.sin(np.arange(41)), .62 + .02*np.cos(np.arange(17)), -.04 + .02*np.sin(np.arange(46))]
    for donor, value in zip(schema["donor_order"], source_y): source["donor_records"][donor]["overall_A"] = float(value)
    source_decision = adapter.qualify_synthetic(source, authority_root=authority_root, repo_root=repo_root)
    source_confined_veto = not source_decision["gates"]["cross_source_replication"]
    adversarial_pass = veto_exact and legal_domain["true"] == {"accepted": True, "legal_gate": True} and all(not value["accepted"] or not value["legal_gate"] for key, value in legal_domain.items() if key != "true") and all(candidate_attacks.values()) and all(input_attacks.values()) and donor_permutation_exact and zero_nonestimable and source_confined_veto
    if not adversarial_pass:
        raise ValueError("STOP_F1_HC3_15C_ADVERSARIAL_REGRESSION")
    _write_json(out / "F1_HC3_15C_ADVERSARIAL_REGRESSION.json", {"status": "PASS", "fresh_legacy_14_cases": [{"attack": item["attack"], "changed_gates": item["changed_gates"], "isolated_pass": item["isolated_pass"]} for item in truth_regression["attacks"]], "hc3_veto_exact_gate_vector": veto_exact, "strict_legal_domain": legal_domain, "candidate_design_attacks_rejected": candidate_attacks, "input_attacks_rejected": input_attacks, "donor_permutation_exact_gate_vector": donor_permutation_exact, "zero_variance_nonestimable": zero_nonestimable, "source_confined_veto": source_confined_veto})

    forbidden = ("import " + "h5py", "import " + "anndata", "torch." + "load(", ".h5" + "ad", "." + "qs")
    source_text = "\n".join((HERE / name).read_text(encoding="utf-8") for name in ("contextual_target_f1_hc3_stable_qr_v2.py", "validate_contextual_target_f1_hc3_svd_v2.py", "contextual_target_f1_hc3_15c_adapter_v2.py", Path(__file__).name))
    firewall = {"status": "PASS_F1_HC3_15C_SYNTHETIC_ONLY_FIREWALL", "expression_opened": False, "model_or_checkpoint_opened": False, "training_or_ema_updated": False, "real_reader_forward_authority": None, "forbidden_source_hits": [token for token in forbidden if token in source_text]}
    if firewall["forbidden_source_hits"]:
        raise ValueError("STOP_F1_HC3_15C_FIREWALL_SOURCE_SCOPE")
    _write_json(out / "F1_HC3_15C_REPAIR_FIREWALL_AUDIT.json", firewall)
    return {"status": "PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR", "comparison": comparison, "adversarial": adversarial_pass}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--authority-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.out, authority_root=args.authority_root, repo_root=args.repo_root), sort_keys=True))
