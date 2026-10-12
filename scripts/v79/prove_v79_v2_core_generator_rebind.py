#!/usr/bin/env python3
"""Evidence for the controller (PR #291 rebind): numerical proofs on a TEST seed root, in memory only.

Never realizes a qualification world: the payload is an in-memory copy whose seed root is replaced by TEST_ROOT,
and nothing but this JSON receipt is written. Usage: prove_v79_v2_core_generator_rebind.py <repo_root> <out.json>
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_v79_v2_core_worlds as G  # noqa: E402
import v79_v2_core_launch as L  # noqa: E402

TEST_ROOT = 4242


def refusal(fn) -> str:
    try:
        fn()
    except SystemExit as e:
        return f"REFUSED: {e}"
    return "ACCEPTED (unexpected)"


def main() -> None:
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    contract, payload = G.load_launch_contract(root)
    test = copy.deepcopy(payload)
    test["seeds"]["root"] = TEST_ROOT
    cal = json.loads((root / "results/v79/development/v2_core_planting_calibration/"
                             "V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").read_text(encoding="utf-8"))
    amendment = G.load_pairing_amendment(root)
    designs = G.build_world_designs(root, test)
    worlds = test["worlds"]["world_list"]
    truth = {w["name"]: G.build_world_truth(test, cal, designs, w, amendment) for w in worlds}
    raw = {w["name"]: G.build_world_truth(test, cal, designs, {**w, "modifications": {}}, amendment) for w in worlds}

    donor = {}
    for name in ("Q01_WEAK_DONOR", "Q02_STRONG_DONOR", "Q07_DONOR_ABSENT"):
        donor[name] = {}
        for part in ("detection", "positive"):
            t, r = truth[name][part], raw[name][part]
            sd_mod = t["donor_effects"].std(axis=0)
            sd_raw = r["donor_effects"].std(axis=0)
            donor[name][part] = {
                "planted_donor_sd": sorted(set(float(x) for x in t["donor_sd"])),
                "mean_realized_effect_sd_modified": float(sd_mod.mean()),
                "mean_realized_effect_sd_unmodified_same_world": float(sd_raw.mean()),
                "max_abs_effects_minus_latent_x_sd": float(np.max(np.abs(t["donor_effects"]
                                                                     - t["donor_raw_centered"] * t["donor_sd"][None, :]))),
                "nonzero_effects": int(np.count_nonzero(t["donor_effects"])),
                "latent_field_identical_to_unmodified": bool(np.array_equal(t["donor_raw_centered"], r["donor_raw_centered"])),
            }
    prevalence = {}
    for w in worlds:
        name = w["name"]
        t, d = truth[name], designs[name]
        nonint = G.detection_nonintercept_predictor(d, t["detection"])
        p = 1.0 / (1.0 + np.exp(-np.clip(t["detection"]["intercept"][None, :] + nonint, -40, 40)))
        achieved = np.array([p[t["support"][:, g], g].mean() for g in range(p.shape[1])])
        prevalence[name] = {
            "max_abs_achieved_minus_target_over_measured": float(np.max(np.abs(achieved - t["detection"]["prevalence"]))),
            "target_min": float(t["detection"]["prevalence"].min()), "target_max": float(t["detection"]["prevalence"].max()),
            "mean_abs_intercept_change_vs_unmodified_same_world": float(np.mean(np.abs(
                t["detection"]["intercept"] - raw[name]["detection"]["intercept"]))),
            "structural_genes": int((~t["support"].all(axis=0)).sum()),
        }
    old = dict(amendment, final_contract_sha256=G.OBSOLETE_CONTRACT_SHA256)
    rec = {
        "schema": "V79_V2_CORE_GENERATOR_REBIND_PROOF_V1",
        "label": "TEST_SEED_ROOT_4242__IN_MEMORY_ONLY__NOT_A_QUALIFICATION_WORLD__NO_WORLD_ARTIFACTS",
        "canonical_contract_sha256_observed": G.FINAL_CONTRACT_SHA256,
        "launch_gate_status": contract["status"],
        "qualification_payload_sha256": G.QUALIFICATION_PAYLOAD_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "source_codes_from_canonical_metadata": G.source_code_mapping(root),
        "obsolete_contract_refusals": {
            "pairing_amendment_bound_to_obsolete": refusal(lambda: G.validate_pairing_amendment_content(old)),
            "realization_authorization_bound_to_obsolete": refusal(lambda: G.validate_realization_authorization({
                "schema": G.REALIZATION_AUTH_SCHEMA, "final_contract_sha256": G.OBSOLETE_CONTRACT_SHA256,
                "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256, "world_generation_authorized": True,
                "qualification_fitting_authorized": False, "generator_code_head": "0" * 40,
                "generator_green_ci": {"passed": True}})),
            "manifest_bound_to_obsolete": refusal(lambda: G.build_manifest(
                world_name="Q00_BASELINE", world_index=0, truth={}, final_contract_sha=G.OBSOLETE_CONTRACT_SHA256,
                payload_sha=G.QUALIFICATION_PAYLOAD_SHA256, generated_files={})),
        },
        "realize_worlds_with_canonical_authorization": refusal(lambda: G.realize_worlds(test, designs["Q00_BASELINE"], Path("unused"), {
            "schema": G.REALIZATION_AUTH_SCHEMA, "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
            "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256, "world_generation_authorized": True,
            "qualification_fitting_authorized": False, "generator_code_head": "0" * 40,
            "generator_green_ci": {"passed": True}})),
        "donor_rescaling": donor,
        "detection_prevalence_over_measured_cells": prevalence,
        "q10_q11_non_operator_truth_identical": G.non_operator_truth_sha(truth["Q10_S174_DESIGN_IMBALANCE"])
        == G.non_operator_truth_sha(truth["Q11_OMITTED_OPERATOR"]),
        "launch_authority_module": L.FINAL_CONTRACT_NAME,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("canonical_contract_sha256_observed", "pairing_amendment_sha256",
                                           "q10_q11_non_operator_truth_identical")}, indent=1))


if __name__ == "__main__":
    main()
