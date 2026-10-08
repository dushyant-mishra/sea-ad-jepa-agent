"""Execute the prospective synthetic-only F1 evidence-trend numerical repair."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np


HERE = Path(__file__).resolve().parent
AUTHORITY_BINDING_SHA = "2ce5500cc627e1afeab2dd88949958414c24e0f077e66c74fb29bd0115ff923a"
HISTORICAL_BINDING_SHA = "ac9ad0d3b423196e91d870852cfbf9a5cc7535b86ef65c7b0b7f9e845ef91dc4"
AUTHORITY_BLOBS = {
    "docs/agent/F1_EVIDENCE_TREND_NUMERICAL_REPAIR_CONTRACT_20260902.md": "02d3dc3a79dba2835eaa8663d75643ffa7f62e2c77b5bf86b5d616e1a6a229d6",
    "docs/agent/F1_EVIDENCE_TREND_NUMERICAL_TOLERANCE_AUTHORITY_20260902.json": "74f9dc7a9b4a924923109028ed092276878b821c3811dd97402dac59b052c4d4",
    "docs/agent/F1_EVIDENCE_TREND_PREIMPLEMENTATION_FREEZE_20260902.json": "833885c14dc73db3dd67fe6a5ab98f95ff1b11d6ba6ad6b3e0294b4cafa73cff",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical_text_sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def _write(path: Path, value) -> None:
    def safe(item):
        if isinstance(item, (np.bool_,)): return bool(item)
        if isinstance(item, (np.integer,)): return int(item)
        if isinstance(item, (np.floating,)): return float(item)
        if isinstance(item, np.ndarray): return safe(item.tolist())
        if isinstance(item, dict): return {str(key): safe(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)): return [safe(val) for val in item]
        return item
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def _array_bytes(array) -> bytes:
    return np.asarray(array, dtype="<f8").tobytes(order="C")


def _truth_payload_to_raw_synthetic(payload: dict, donor_order) -> dict:
    fields = (
        "overall_A", "program_A", "program_delta", "evidence_A", "qid_margin",
        "qid_win_minus_half", "program_qid_margin", "draw0", "draw1",
    )
    records = {}
    for index, donor in enumerate(donor_order):
        record = {}
        for field in fields:
            value = payload[field]
            if field.startswith("program_"):
                record[field] = {program: value[program][index] for program in value}
            else:
                record[field] = value[index]
        records[donor] = record
    return {"donor_records": records, "legal": payload["legal"]}


def _verify_authorities(out: Path, repo_root: Path) -> None:
    if _canonical_text_sha(out / "F1_EVIDENCE_TREND_REPAIR_AUTHORITY_BINDING.json") != AUTHORITY_BINDING_SHA:
        raise ValueError("STOP_F1_EVIDENCE_TREND_AUTHORITY_BINDING_MISMATCH")
    if _canonical_text_sha(out / "F1_EVIDENCE_TREND_REPAIR_HISTORICAL_HASH_BINDING.json") != HISTORICAL_BINDING_SHA:
        raise ValueError("STOP_F1_EVIDENCE_TREND_HISTORICAL_BINDING_MISMATCH")
    safe_repo = Path(repo_root).resolve().as_posix()
    for relative, expected in AUTHORITY_BLOBS.items():
        data = subprocess.check_output(["git", "-c", f"safe.directory={safe_repo}", "-C", str(repo_root), "show", "HEAD:" + relative])
        if _sha_bytes(data) != expected:
            raise ValueError("STOP_F1_EVIDENCE_TREND_PROSPECTIVE_AUTHORITY_MISMATCH")


def run(out: Path, *, authority_root: Path, repo_root: Path) -> dict:
    out, authority_root, repo_root = Path(out), Path(authority_root), Path(repo_root)
    out.mkdir(parents=True, exist_ok=True)
    _verify_authorities(out, repo_root)
    production = _load(HERE / "contextual_target_f1_evidence_slope_v1.py", "f1_evidence_slope_prod_run")
    layer = _load(HERE / "contextual_target_f1_evidence_trend_decision_v1.py", "f1_evidence_layer_run")
    independent = _load(HERE / "validate_contextual_target_f1_evidence_trend_v1.py", "f1_evidence_independent_run")
    hc3 = _load(HERE / "contextual_target_f1_hc3_15c_adapter_v2.py", "f1_accepted_hc3_run")
    old_dir = authority_root / "outputs/contextual_teacher_target_v1_f1_hc3_15c_decision_integration_20260902"
    baseline = json.loads((old_dir / "F1_15C_SYNTHETIC_BASELINE.json").read_text(encoding="utf-8"))
    schema, _, _ = hc3.load_frozen_effective_design(authority_root)
    evidence = np.asarray([baseline["payload"]["donor_records"][donor]["evidence_A"] for donor in schema["donor_order"]], dtype=np.float64)

    flat_levels = np.asarray([1.0, 0.28, 0.0, -0.31], dtype=np.float64)
    flat_rows = np.repeat(flat_levels[:, None], 5, axis=1)
    flat_bytes = _array_bytes(flat_rows)
    (out / "F1_EVIDENCE_TREND_EXACT_FLAT_FIXTURES_F64LE.bin").write_bytes(flat_bytes)
    _write(out / "F1_EVIDENCE_TREND_EXACT_FLAT_FIXTURE_BINDING.json", {"status": "FROZEN_BEFORE_COMPARISON", "shape": list(flat_rows.shape), "sha256": _sha_bytes(flat_bytes), "levels": flat_levels.tolist()})
    linear_rows = np.asarray([[0, 1, 2, 3, 4], [4, 3, 2, 1, 0]], dtype=np.float64)
    linear_bytes = _array_bytes(linear_rows)
    (out / "F1_EVIDENCE_TREND_LINEAR_FIXTURES_F64LE.bin").write_bytes(linear_bytes)
    _write(out / "F1_EVIDENCE_TREND_LINEAR_FIXTURE_BINDING.json", {"status": "FROZEN_BEFORE_COMPARISON", "shape": list(linear_rows.shape), "sha256": _sha_bytes(linear_bytes), "expected_slopes": [5.0, -5.0]})

    # Independent route fixes the prospective +/-1e-5 lower-bound fixtures before production is evaluated.
    base_slopes = 0.02 * np.sin(np.arange(104) * 0.37) + 0.004 * np.cos(np.arange(104) * 0.11)
    base_rows = np.zeros((104, 5), dtype=np.float64); base_rows[:, 4] = base_slopes
    base_reference = independent.independent_report(base_rows)
    near_rows = {}
    near_binding = {"status": "FROZEN_BEFORE_PRODUCTION_COMPARISON", "independent_construction": True, "fixtures": {}}
    for name, target in (("positive", 1e-5), ("negative", -1e-5)):
        rows = base_rows.copy(); rows[:, 4] += target - base_reference["lower_one_sided"]
        payload = _array_bytes(rows); filename = f"F1_EVIDENCE_TREND_NEAR_BOUNDARY_{name.upper()}_F64LE.bin"
        (out / filename).write_bytes(payload); near_rows[name] = rows
        near_binding["fixtures"][name] = {"filename": filename, "shape": [104, 5], "sha256": _sha_bytes(payload), "target_lower_one_sided": target}
    _write(out / "F1_EVIDENCE_TREND_NEAR_BOUNDARY_FIXTURE_BINDING.json", near_binding)

    cases = {"baseline": evidence, "near_positive": near_rows["positive"], "near_negative": near_rows["negative"]}
    production_results, independent_results, comparisons = {}, {}, {}
    maximum = 0.0
    for name, rows in cases.items():
        prod_slopes = production.paired_difference_slopes(rows)
        ref_slopes = independent.independent_slopes(rows)
        tolerances = 64 * np.finfo(np.float64).eps * np.maximum(1.0, np.max(np.abs(rows), axis=1))
        differences = np.abs(prod_slopes - ref_slopes); maximum = max(maximum, float(np.max(differences)))
        sign_agreement = bool(np.array_equal(np.signbit(prod_slopes[ref_slopes != 0]), np.signbit(ref_slopes[ref_slopes != 0])))
        prod_report = production.donor_trend_report(rows); ref_report = independent.independent_report(rows)
        passed = bool(np.all(differences <= tolerances) and sign_agreement and prod_report["gate"] is ref_report["gate"] and prod_report["estimable"] is ref_report["estimable"])
        if not passed: raise ValueError("STOP_F1_EVIDENCE_TREND_NUMERICAL_INDEPENDENCE_UNRESOLVED")
        production_results[name] = {"slopes_sha256": _sha_bytes(_array_bytes(prod_slopes)), "report": prod_report}
        independent_results[name] = {"slopes_sha256": _sha_bytes(_array_bytes(ref_slopes)), "report": ref_report}
        comparisons[name] = {"max_abs_slope_difference": float(np.max(differences)), "sign_agreement": sign_agreement, "estimability_agreement": prod_report["estimable"] is ref_report["estimable"], "gate_agreement": prod_report["gate"] is ref_report["gate"], "pass": passed}

    flat_prod = production.paired_difference_slopes(flat_rows); flat_ref = independent.independent_slopes(flat_rows)
    linear_prod = production.paired_difference_slopes(linear_rows); linear_ref = independent.independent_slopes(linear_rows)
    if not np.array_equal(flat_prod, np.zeros(4)) or not np.array_equal(flat_ref, np.zeros(4)) or not np.array_equal(linear_prod, np.asarray([5.0, -5.0])) or not np.array_equal(linear_ref, linear_prod):
        raise ValueError("STOP_F1_EVIDENCE_TREND_FIXTURE_MISMATCH")
    _write(out / "F1_EVIDENCE_TREND_REPAIRED_SLOPE_RESULTS.json", {"status": "PASS", "coefficient_vector": [-1.0, -0.5, 0.0, 0.5, 1.0], "exact_flat_slopes": flat_prod, "linear_slopes": linear_prod, "cases": production_results})
    _write(out / "F1_EVIDENCE_TREND_INDEPENDENT_REFERENCE_RESULTS.json", {"status": "PASS", "method": "MATH_FSUM_SEPARATE_IMPLEMENTATION", "exact_flat_slopes": flat_ref, "linear_slopes": linear_ref, "cases": independent_results})

    accepted = hc3.qualify_synthetic(baseline["payload"], authority_root=authority_root, repo_root=repo_root)
    repaired = layer.qualify_synthetic(baseline["payload"], authority_root=authority_root, repo_root=repo_root)
    independent_decision = independent.independent_complete_adjudication(
        baseline["payload"],
        schema["donor_order"],
        accepted_hc3_report=accepted["reports"]["nuisance"],
        accepted_hc3_method=accepted["conclusion_bearing_hc3_method"],
    )
    non_evidence_gates = all(repaired["gates"][key] is accepted["gates"][key] for key in accepted["gates"] if key != "evidence_trend_one_sided_positive")
    non_evidence_reports = all(repaired["reports"][key] == accepted["reports"][key] for key in accepted["reports"] if key != "evidence_slope")
    hc3_unchanged = repaired["reports"]["nuisance"] == accepted["reports"]["nuisance"] and repaired["gates"]["hc3_nuisance_positive"] is accepted["gates"]["hc3_nuisance_positive"]
    independent_comparison = independent.compare_complete_adjudications(independent_decision, repaired)
    complete_exact = independent_comparison["all_11_gate_comparisons"] and independent_comparison["qualified_comparison"]
    if not (non_evidence_gates and non_evidence_reports and hc3_unchanged and complete_exact):
        raise ValueError("STOP_F1_EVIDENCE_TREND_COMPLETE_ADJUDICATION_MISMATCH")
    flipped_gate_attacks = {}
    for gate in independent.GATE_ORDER:
        if gate == "evidence_trend_one_sided_positive":
            continue
        attacked = copy.deepcopy(repaired)
        attacked["gates"][gate] = not attacked["gates"][gate]
        attacked["qualified"] = bool(all(attacked["gates"].values()))
        attack_comparison = independent.compare_complete_adjudications(independent_decision, attacked)
        flipped_gate_attacks[gate] = bool(
            independent_decision["gates"] == independent.independent_complete_adjudication(
                baseline["payload"],
                schema["donor_order"],
                accepted_hc3_report=accepted["reports"]["nuisance"],
                accepted_hc3_method=accepted["conclusion_bearing_hc3_method"],
            )["gates"]
            and attack_comparison["gate_comparisons"][gate] is False
            and attack_comparison["all_11_gate_comparisons"] is False
        )
    if not all(flipped_gate_attacks.values()):
        raise ValueError("STOP_F1_EVIDENCE_TREND_INDEPENDENCE_ATTACK_UNDETECTED")

    v1 = _load(repo_root / "scripts/v4/contextual_target_f1_decision_v1.py", "f1_historical_v1_defect")
    donor_levels = np.linspace(0.1, 1.1, 104); legacy_rows = np.repeat(donor_levels[:, None], 5, axis=1)
    legacy_slopes = v1.evidence_slopes(legacy_rows); legacy_report = v1.t_interval(legacy_slopes)
    repaired_slopes = production.paired_difference_slopes(legacy_rows); repaired_report = production.donor_trend_report(legacy_rows)
    defect_pass = bool(np.any(legacy_slopes != 0.0) and legacy_report["estimable"] and legacy_report["lower_one_sided"] > 0.0 and np.array_equal(repaired_slopes, np.zeros(104)) and not repaired_report["estimable"] and not repaired_report["gate"])
    if not defect_pass: raise ValueError("STOP_F1_EVIDENCE_TREND_LEGACY_DEFECT_NOT_REPRODUCED")
    _write(out / "F1_EVIDENCE_TREND_LEGACY_DEFECT_DEMONSTRATION.json", {"status": "PASS", "fixture": "mathematically flat rows with donor levels linearly spanning 0.1 to 1.1", "legacy_nonzero_count": int(np.count_nonzero(legacy_slopes)), "legacy_max_abs_slope": float(np.max(np.abs(legacy_slopes))), "legacy_gate": True, "repaired_all_exact_zero": True, "repaired_estimable": False, "repaired_gate": False})

    truth = _load(repo_root / "scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py", "f1_truth_regression_run")
    truth.v4.V1_SHA = truth.v4.sha(truth.v4.V1)
    truth.component.FROZEN_ASSIGNMENT_PATH = authority_root / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
    truth_results = truth.attacks()
    truth_reconstruction = []
    for attack in truth_results["attacks"]:
        name = attack["attack"]
        if name == "G_hc3_nuisance":
            truth_reconstruction.append({
                "attack": name,
                "applicability": "NOT_APPLICABLE__FREE_FORM_NUISANCE_SUPERSEDED_BY_FROZEN_15C_DESIGN",
                "pass": True,
            })
            continue
        raw_attack = _truth_payload_to_raw_synthetic(attack["payload"], schema["donor_order"])
        production_rejected = independent_rejected = False
        try:
            production_attack = layer.qualify_synthetic(raw_attack, authority_root=authority_root, repo_root=repo_root)
        except (TypeError, ValueError):
            production_rejected = True
        try:
            if production_rejected:
                attack_hc3_report = accepted["reports"]["nuisance"]
                attack_hc3_method = accepted["conclusion_bearing_hc3_method"]
            else:
                attack_hc3_report = production_attack["reports"]["nuisance"]
                attack_hc3_method = production_attack["conclusion_bearing_hc3_method"]
            independent_attack = independent.independent_complete_adjudication(
                raw_attack,
                schema["donor_order"],
                accepted_hc3_report=attack_hc3_report,
                accepted_hc3_method=attack_hc3_method,
            )
        except (TypeError, ValueError):
            independent_rejected = True
        if production_rejected or independent_rejected:
            passed = production_rejected and independent_rejected
            comparison_attack = None
        else:
            comparison_attack = independent.compare_complete_adjudications(independent_attack, production_attack)
            passed = comparison_attack["all_11_gate_comparisons"] and comparison_attack["qualified_comparison"]
        truth_reconstruction.append({
            "attack": name,
            "applicability": "APPLICABLE",
            "production_rejected": production_rejected,
            "independent_rejected": independent_rejected,
            "all_11_gate_comparisons": None if comparison_attack is None else comparison_attack["all_11_gate_comparisons"],
            "qualified_comparison": None if comparison_attack is None else comparison_attack["qualified_comparison"],
            "pass": bool(passed),
        })
    if len(truth_reconstruction) != 14 or not all(item["pass"] for item in truth_reconstruction):
        raise ValueError("STOP_F1_EVIDENCE_TREND_TRUTH_ATTACK_RECONSTRUCTION_MISMATCH")
    validator_source = (HERE / "validate_contextual_target_f1_evidence_trend_v1.py").read_text(encoding="utf-8")
    forbidden_independent_construction = (
        "copy.deepcopy(accepted_hc3_decision)",
        'accepted_hc3_decision["gates"]',
        'accepted_hc3_decision["reports"]',
        "contextual_target_f1_evidence_trend_decision_v1",
        "contextual_target_f1_decision_v4",
        "qualify_current",
        "contextual_target_f1_evidence_slope_v1",
    )
    independence_hits = [token for token in forbidden_independent_construction if token in validator_source]
    if independence_hits:
        raise ValueError("STOP_F1_EVIDENCE_TREND_INDEPENDENT_CONSTRUCTION_STATIC_FAIL")
    static_independence_audit = {"forbidden_construction_hits": independence_hits, "pass": True}
    adversarial_path = old_dir / "F1_15C_NUISANCE_ADVERSARIAL.json"
    veto = next(item for item in json.loads(adversarial_path.read_text(encoding="utf-8"))["attacks"] if item["attack"] == "A_nuisance_veto")
    veto_accepted = hc3.qualify_synthetic(veto["payload"], authority_root=authority_root, repo_root=repo_root)
    veto_repaired = layer.qualify_synthetic(veto["payload"], authority_root=authority_root, repo_root=repo_root)
    veto_hc3_unchanged = veto_repaired["reports"]["nuisance"] == veto_accepted["reports"]["nuisance"] and veto_repaired["gates"]["hc3_nuisance_positive"] is veto_accepted["gates"]["hc3_nuisance_positive"]
    attacks = {}
    first = next(iter(baseline["payload"]["donor_records"]))
    for label, mutate in (
        ("forged_evidence_gate", lambda p: p.__setitem__("evidence_trend_one_sided_positive", True)),
        ("donor_omission", lambda p: p["donor_records"].pop(first)),
        ("donor_relabel", lambda p: p["donor_records"].__setitem__("fake::donor", p["donor_records"].pop(first))),
        ("nonfinite", lambda p: p["donor_records"][first]["evidence_A"].__setitem__(0, float("nan"))),
        ("wrong_evidence_length", lambda p: p["donor_records"][first].__setitem__("evidence_A", [1.0] * 4)),
    ):
        payload = copy.deepcopy(baseline["payload"]); mutate(payload)
        try: layer.qualify_synthetic(payload, authority_root=authority_root, repo_root=repo_root); rejected = False
        except (TypeError, ValueError): rejected = True
        attacks[label] = rejected
    permuted = copy.deepcopy(baseline["payload"]); permuted["donor_records"] = {key: permuted["donor_records"][key] for key in reversed(list(permuted["donor_records"]))}
    permutation_exact = layer.qualify_synthetic(permuted, authority_root=authority_root, repo_root=repo_root)["gates"] == repaired["gates"]
    regression_pass = len(truth_results["attacks"]) == 14 and all(item["isolated_pass"] for item in truth_results["attacks"]) and veto_hc3_unchanged and all(attacks.values()) and permutation_exact
    if not regression_pass: raise ValueError("STOP_F1_EVIDENCE_TREND_REGRESSION_MISMATCH")
    _write(out / "F1_EVIDENCE_TREND_REGRESSION_RESULTS.json", {"status": "PASS", "frozen_14_cases": [{"attack": item["attack"], "isolated_pass": item["isolated_pass"]} for item in truth_results["attacks"]], "accepted_15c_hc3_veto_unchanged": veto_hc3_unchanged, "attacks_rejected": attacks, "donor_insertion_order_exact": permutation_exact, "accepted_hc3_repair_manifest_sha256": "f7cc3be9340c817f57953d3ef009c568a57dca7ea4fffbc2ccefbe6266e123a5"})

    _write(out / "F1_EVIDENCE_TREND_COMPLETE_GATE_VECTOR_COMPARISON.json", {
        "status": "PASS",
        "independent_gate_construction": independent_decision["independent_gate_construction"],
        "copied_production_gate_count": independent_decision["copied_production_gate_count"],
        "accepted_hc3_authority_reused": independent_decision["accepted_hc3_authority_reused"],
        "production_gates": repaired["gates"],
        "independent_gates": independent_decision["gates"],
        "gate_comparisons": independent_comparison["gate_comparisons"],
        "all_11_gate_comparisons": independent_comparison["all_11_gate_comparisons"],
        "complete_gate_vector_exact": complete_exact,
        "qualified_comparison": independent_comparison["qualified_comparison"],
        "non_evidence_gates_unchanged": non_evidence_gates,
        "non_evidence_reports_unchanged": non_evidence_reports,
        "accepted_hc3_unchanged": hc3_unchanged,
        "deliberate_flipped_gate_attacks_detected": flipped_gate_attacks,
        "truth_table_attack_reconstruction": truth_reconstruction,
        "static_independence_audit": static_independence_audit,
    })

    comparison = {"status": "PASS", "maximum_per_donor_slope_abs_difference": maximum, "cases": comparisons, "near_boundary": {"positive": {"production_gate": production_results["near_positive"]["report"]["gate"], "independent_gate": independent_results["near_positive"]["report"]["gate"]}, "negative": {"production_gate": production_results["near_negative"]["report"]["gate"], "independent_gate": independent_results["near_negative"]["report"]["gate"]}}, "complete_gate_vector_exact": complete_exact}
    if comparison["near_boundary"]["positive"] != {"production_gate": True, "independent_gate": True} or comparison["near_boundary"]["negative"] != {"production_gate": False, "independent_gate": False}:
        raise ValueError("STOP_F1_EVIDENCE_TREND_NEAR_BOUNDARY_GATE_MISMATCH")
    _write(out / "F1_EVIDENCE_TREND_NUMERICAL_COMPARISON.json", comparison)
    source_text = "\n".join((HERE / name).read_text(encoding="utf-8") for name in ("contextual_target_f1_evidence_slope_v1.py", "contextual_target_f1_evidence_trend_decision_v1.py", "validate_contextual_target_f1_evidence_trend_v1.py", Path(__file__).name))
    forbidden = ("import " + "h5py", "import " + "anndata", "torch." + "load(", ".h5" + "ad", "." + "qs")
    hits = [token for token in forbidden if token in source_text]
    if hits: raise ValueError("STOP_F1_EVIDENCE_TREND_FIREWALL")
    _write(out / "F1_EVIDENCE_TREND_REPAIR_FIREWALL_AUDIT.json", {"status": "PASS_SYNTHETIC_ONLY_FIREWALL", "forbidden_source_hits": hits, "expression_opened": False, "real_f1_outcomes_opened": False, "reader_or_forward_authority_set": False, "model_or_checkpoint_opened": False, "training_optimizer_or_ema_updated": False, "protected_data_opened": False})
    return {"status": "PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR", "maximum_per_donor_slope_abs_difference": maximum, "complete_gate_vector_exact": complete_exact}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--authority-root", type=Path, required=True); parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(run(args.out, authority_root=args.authority_root, repo_root=args.repo_root), sort_keys=True))
