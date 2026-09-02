#!/usr/bin/env python3
"""Targeted production golden fixtures; never touches real conclusion-bearing outputs."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from derive_full104_phase2_shared_state import fit_basis
from full104_refit_null_sensitivity_core_v1 import (
    build_nested_plan, heldout_predictability, null_between_one, overlap_curve,
    select_dimension, signal_supported, source_stratified_bootstrap, validate_plan,
    weighted_moments,
)
from run_full104_refit_null_sensitivity_v1 import (
    assert_checkpoint_identity, assert_checkpoint_payload, assert_plan_exact, atomic_npz,
    canonical_sha, checkpoint_identity, checkpoint_identity_arrays, checkpoint_payload_sha256,
    load_lossless_plan, plan_arrays, plan_semantic_sha256, semantic_payload_sha,
    verify_gate_implementation, write_lossless_plan,
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""): h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True); parser.add_argument("--device", default="cpu")
    args = parser.parse_args(); out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(20260829); donors, operators, cells, views_n, dim, rank, reps = 8, 2, 7, 4, 12, 6, 8
    donor_ids = [f"D{d:02d}" for d in range(donors)]; sources = np.asarray(["S0"] * 4 + ["S1"] * 4); folds = np.arange(donors) % 4
    load, _ = np.linalg.qr(rng.normal(size=(dim, 3))); blocks, records = [], []; row = 0
    for d, donor in enumerate(donor_ids):
        for operator in range(operators):
            latent = rng.normal(size=(cells, 3)) + d * 0.04
            signal = (latent * np.asarray([3.0, 2.0, 1.0])) @ load.T
            block = np.stack([signal + rng.normal(scale=.05, size=(cells, dim)) + operator * .02 for _ in range(views_n)], axis=1).astype(np.float32)
            blocks.append(block)
            for _ in range(cells): records.append({"donor_id": donor, "operator_index": operator, "selection_row": row}); row += 1
    x = np.concatenate(blocks); rows = pd.DataFrame(records); key = hashlib.sha256(b"fixture-null-key").hexdigest(); boot_key = hashlib.sha256(b"fixture-boot-key").hexdigest()
    plan2 = build_nested_plan(rows, 2, key, donor_total=donors); plan4 = build_nested_plan(rows, 4, key, donor_total=donors)
    audit = validate_plan(plan4, rows, donor_total=donors)
    lossless_path = out / "LOSSLESS_PLAN_FIXTURE.npz"
    lossless_file_sha, lossless_semantic_sha = write_lossless_plan(lossless_path, plan4)
    plan_reload, reload_file_sha, reload_semantic_sha = load_lossless_plan(lossless_path, lossless_file_sha, lossless_semantic_sha)
    memory_arrays, reload_arrays = plan_arrays(plan4), plan_arrays(plan_reload)
    weights_bitwise = all(np.array_equal(memory_arrays[c], reload_arrays[c]) for c in ("within_donor_weight", "global_weight"))
    membership_exact = all(np.array_equal(memory_arrays[c], reload_arrays[c]) for c in ("row_index", "selection_row", "donor_id", "operator_index", "stratum_n", "stratum_m", "sample_rank"))
    reload_audit = validate_plan(plan_reload, rows, donor_total=donors)
    csv_provenance = out / "LOSSLESS_PLAN_FIXTURE_PROVENANCE.csv"; plan4.to_csv(csv_provenance, index=False)
    csv_corrupted = pd.read_csv(csv_provenance); csv_corrupted["global_weight"] = 0.0; csv_corrupted.to_csv(csv_provenance, index=False)
    binary_after_csv, _, after_csv_semantic = load_lossless_plan(lossless_path, lossless_file_sha, lossless_semantic_sha)
    csv_nonauthoritative = plan_semantic_sha256(binary_after_csv) == lossless_semantic_sha and float(pd.read_csv(csv_provenance).global_weight.sum()) == 0.0
    corrupted_path = out / "LOSSLESS_PLAN_FIXTURE_CORRUPTED.npz"; corrupted_arrays = dict(memory_arrays); corrupted_arrays["global_weight"] = corrupted_arrays["global_weight"].copy(); corrupted_arrays["global_weight"][0] = 0.0; atomic_npz(corrupted_path, **corrupted_arrays)
    corrupted_rejected = False
    try:
        load_lossless_plan(corrupted_path, lossless_file_sha, lossless_semantic_sha)
    except RuntimeError:
        corrupted_rejected = True
    dtype_path = out / "LOSSLESS_PLAN_FIXTURE_FLOAT32.npz"; dtype_arrays = dict(memory_arrays); dtype_arrays["global_weight"] = dtype_arrays["global_weight"].astype(np.float32); atomic_npz(dtype_path, **dtype_arrays)
    dtype_downgrade_rejected = False
    try: load_lossless_plan(dtype_path)
    except RuntimeError: dtype_downgrade_rejected = True
    substituted = plan_reload.copy(); substituted.loc[[0,1], "row_index"] = substituted.loc[[1,0], "row_index"].to_numpy()
    coordinated_substitution_rejected = False
    try: assert_plan_exact(plan4, substituted)
    except RuntimeError: coordinated_substitution_rejected = True
    lossless_pass = bool(weights_bitwise and membership_exact and reload_file_sha == lossless_file_sha and reload_semantic_sha == lossless_semantic_sha and reload_audit["donors"] == donors and csv_nonauthoritative and corrupted_rejected and dtype_downgrade_rejected and coordinated_substitution_rejected)
    nested = set(plan2.row_index).issubset(set(plan4.row_index))
    mean, within, between = weighted_moments(x, plan4, donor_ids, args.device)
    shuffled = plan4.sample(frac=1, random_state=91).reset_index(drop=True)
    mean2, within2, between2 = weighted_moments(x, shuffled, donor_ids, args.device)
    metamorphic_max = max(float(np.max(np.abs(mean - mean2))), float(np.max(np.abs(within - within2))), float(np.max(np.abs(between - between2))))
    basis = fit_basis(mean, within, between, np.arange(donors), rank)
    observed_eigen, observed_stability = [], []
    for rep in range(reps):
        sample = source_stratified_bootstrap(sources, boot_key, rep); fitted = fit_basis(mean, within, between, sample, rank)
        observed_eigen.append(fitted["eigenvalues"]); observed_stability.append(overlap_curve(basis["q"], fitted["q"], rank))
    observed_eigen, observed_stability = np.asarray(observed_eigen), np.asarray(observed_stability)
    observed_held = heldout_predictability(mean, within, between, folds, rank)
    null_full, null_boot, null_stability, null_held, map_hashes = [], [], [], [], []
    for rep in range(reps):
        nb, mapping = null_between_one(x, plan4, donor_ids, "fixture", "A", rep, key, args.device)
        full = fit_basis(mean, within, nb, np.arange(donors), rank); sample = source_stratified_bootstrap(sources, boot_key, rep); boot = fit_basis(mean, within, nb, sample, rank)
        null_full.append(full["eigenvalues"]); null_boot.append(boot["eigenvalues"]); null_stability.append(overlap_curve(full["q"], boot["q"], rank))
        null_held.append(heldout_predictability(mean, within, nb, folds, rank)); map_hashes.append(mapping)
    null_full, null_boot, null_stability, null_held = map(np.asarray, [null_full, null_boot, null_stability, null_held])
    signal = signal_supported(observed_eigen, null_boot); calibration = []
    for j in range(rank):
        stability = observed_stability[:, j].mean() - observed_stability[:, j].std(ddof=1)/math.sqrt(reps) > null_stability[:, j].mean() + null_stability[:, j].std(ddof=1)/math.sqrt(reps)
        null_donor = null_held[:, :, j].mean(0)
        predict = observed_held[:, j].mean() - observed_held[:, j].std(ddof=1)/math.sqrt(donors) > null_donor.mean() + null_donor.std(ddof=1)/math.sqrt(donors)
        calibration.append({"sketch": "A", "dimension": j + 1, "signal_supported": bool(signal[j]), "stability_supported": bool(stability), "predictability_supported": bool(predict), "jointly_supported": bool(signal[j] and stability and predict)})
        calibration.append({"sketch": "B", "dimension": j + 1, "signal_supported": bool(signal[j]), "stability_supported": bool(stability), "predictability_supported": bool(predict), "jointly_supported": bool(signal[j] and stability and predict)})
    selection = select_dimension(pd.DataFrame(calibration), observed_held, observed_held)

    # Distinct-sketch E2E falsification: A carries the planted signal; B is an
    # independently generated view tensor and must veto an A-only prefix.
    x_b = np.random.default_rng(20260830).normal(size=x.shape).astype(np.float32)
    mean_b, within_b, between_b = weighted_moments(x_b, plan4, donor_ids, args.device)
    basis_b = fit_basis(mean_b, within_b, between_b, np.arange(donors), rank)
    obs_e_b, obs_s_b = [], []
    for rep in range(reps):
        sample = source_stratified_bootstrap(sources, boot_key, rep); fitted = fit_basis(mean_b, within_b, between_b, sample, rank)
        obs_e_b.append(fitted["eigenvalues"]); obs_s_b.append(overlap_curve(basis_b["q"], fitted["q"], rank))
    obs_e_b, obs_s_b = np.asarray(obs_e_b), np.asarray(obs_s_b); obs_h_b = heldout_predictability(mean_b, within_b, between_b, folds, rank)
    nb_e_b, ns_b, nh_b = [], [], []
    for rep in range(reps):
        null_b, _ = null_between_one(x_b, plan4, donor_ids, "fixture", "B", rep, key, args.device)
        sample = source_stratified_bootstrap(sources, boot_key, rep); full_b = fit_basis(mean_b, within_b, null_b, np.arange(donors), rank); boot_b = fit_basis(mean_b, within_b, null_b, sample, rank)
        nb_e_b.append(boot_b["eigenvalues"]); ns_b.append(overlap_curve(full_b["q"], boot_b["q"], rank)); nh_b.append(heldout_predictability(mean_b, within_b, null_b, folds, rank))
    nb_e_b, ns_b, nh_b = map(np.asarray, [nb_e_b, ns_b, nh_b]); signal_b = signal_supported(obs_e_b, nb_e_b); joint_b = []
    for j in range(rank):
        stable_b = obs_s_b[:, j].mean()-obs_s_b[:, j].std(ddof=1)/math.sqrt(reps) > ns_b[:, j].mean()+ns_b[:, j].std(ddof=1)/math.sqrt(reps)
        null_donor_b = nh_b[:, :, j].mean(0); predict_b = obs_h_b[:, j].mean()-obs_h_b[:, j].std(ddof=1)/math.sqrt(donors) > null_donor_b.mean()+null_donor_b.std(ddof=1)/math.sqrt(donors)
        joint_b.append(bool(signal_b[j] and stable_b and predict_b))
    joint_a = np.asarray([item["jointly_supported"] for item in calibration[::2]])
    ab_table = pd.DataFrame([{"sketch": sketch, "dimension": j+1, "jointly_supported": bool(value)}
                             for sketch, values in (("A", joint_a), ("B", joint_b)) for j, value in enumerate(values)])
    selection_ab = select_dimension(ab_table, observed_held, obs_h_b)
    distinct_ab_pass = bool(joint_a[0] and not joint_b[0] and selection_ab["candidate_D_shared"] is None)

    crafted_obs = np.tile(np.linspace(1.0, .5, rank), (reps, 1)); crafted_null_boot = crafted_obs + .2; crafted_null_full = crafted_obs - .2
    paired_rejects = not bool(signal_supported(crafted_obs, crafted_null_boot)[0]); old_asymmetric_would_pass = bool(signal_supported(crafted_obs, crafted_null_full)[0])
    raw = out / "SYNTHETIC_END_TO_END_INPUTS.npz"; np.savez_compressed(raw, views=x, views_B=x_b, donor_id=np.asarray(donor_ids, dtype="U"), rows_donor=rows.donor_id.astype(str).to_numpy(dtype="U"), rows_operator=rows.operator_index.to_numpy(), selection_row=rows.selection_row.to_numpy(), sources=np.asarray(sources, dtype="U"), folds=folds, key=np.asarray(key), bootstrap_key=np.asarray(boot_key))
    production = out / "SYNTHETIC_END_TO_END_PRODUCTION.npz"
    np.savez_compressed(production, mean=mean, within=within, between=between, observed_bootstrap_eigen=observed_eigen, observed_stability=observed_stability,
                        observed_heldout=observed_held, null_full_eigen=null_full, paired_null_bootstrap_eigen=null_boot, null_stability=null_stability,
                        null_heldout=null_held, signal_supported=signal, jointly_supported=np.asarray([x["jointly_supported"] for x in calibration[::2]]),
                        candidate=np.asarray(-1 if selection["candidate_D_shared"] is None else selection["candidate_D_shared"]), map_hashes=np.asarray(map_hashes),
                        distinct_B_jointly_supported=np.asarray(joint_b), distinct_AB_candidate=np.asarray(-1 if selection_ab["candidate_D_shared"] is None else selection_ab["candidate_D_shared"]))
    input_hashes = {"fixture": "abc"}; expected_identity = checkpoint_identity(
        "fixture-fingerprint", "gate-manifest", input_hashes, "4", "A", 3, "plan-sha", "plan-semantic-sha", "moment-sha", "map-sha")
    payload = {"values": np.arange(12, dtype=np.float64).reshape(3, 4), "flags": np.asarray([True, False])}
    checkpoint = out / "FINGERPRINT_CHECKPOINT.npz"
    np.savez_compressed(checkpoint, **payload, **checkpoint_identity_arrays(expected_identity))
    saved = np.load(checkpoint, allow_pickle=False); fingerprint_ok = True
    try:
        assert_checkpoint_identity(saved, expected_identity)
    except RuntimeError:
        fingerprint_ok = False
    mismatch_rejected = {}
    for field, bad in (("implementation_fingerprint", "mixed-version"), ("cap", "8"), ("sketch", "B"),
                       ("replicate", 4), ("plan_sha256", "wrong-plan"), ("plan_semantic_sha256", "wrong-plan-semantic"),
                       ("mapping_sha256", "wrong-map")):
        altered = dict(expected_identity); altered[field] = bad
        try:
            assert_checkpoint_identity(saved, altered); mismatch_rejected[field] = False
        except RuntimeError:
            mismatch_rejected[field] = True
    uninterrupted_sha = semantic_payload_sha(payload)
    resumed_payload = {key: np.asarray(saved[key]) for key in payload}
    resumed_sha = semantic_payload_sha(resumed_payload)
    semantic_equal = uninterrupted_sha == resumed_sha
    def execute_resumable(directory: Path, interrupt_after=None):
        directory.mkdir(exist_ok=True); values = []
        for rep in range(4):
            identity = checkpoint_identity("fixture-fingerprint", "gate-manifest", input_hashes, "4", "A", rep, "plan-sha", "plan-semantic-sha", "moment-sha", f"map-{rep}")
            path = directory / f"replicate_{rep:03d}.npz"
            if path.exists():
                item = np.load(path, allow_pickle=False); assert_checkpoint_identity(item, identity); value = np.asarray(item["value"])
            else:
                value = np.random.default_rng(700 + rep).normal(size=(3, 2)); atomic_npz(path, value=value, **checkpoint_identity_arrays(identity))
            values.append(value)
            if interrupt_after is not None and len(values) == interrupt_after:
                return None
        return semantic_payload_sha({"replicates": np.stack(values)})
    uninterrupted_execution_sha = execute_resumable(out / "resume_uninterrupted")
    interrupted_dir = out / "resume_interrupted"; forced_stop = execute_resumable(interrupted_dir, 2) is None
    resumed_execution_sha = execute_resumable(interrupted_dir)
    forced_resume_equal = forced_stop and uninterrupted_execution_sha == resumed_execution_sha
    scientific_payload = {"value": np.arange(6, dtype=np.float64)}; scientific_sha = checkpoint_payload_sha256(scientific_payload)
    payload_path = out / "PAYLOAD_TAMPER_FIXTURE.npz"; atomic_npz(payload_path, **scientific_payload, payload_semantic_sha256=np.asarray(scientific_sha))
    with np.load(payload_path, allow_pickle=False) as item: assert_checkpoint_payload(item, ("value",), scientific_sha)
    atomic_npz(payload_path, value=np.arange(6, dtype=np.float64)+1, payload_semantic_sha256=np.asarray(scientific_sha))
    payload_tamper_rejected = False
    try:
        with np.load(payload_path, allow_pickle=False) as item: assert_checkpoint_payload(item, ("value",), scientific_sha)
    except RuntimeError: payload_tamper_rejected = True
    fake_gate = out / "FAKE_GATE"; fake_gate.mkdir(); (fake_gate / "IMPLEMENTATION_GATE_MANIFEST.csv").write_text("fixture\n", encoding="utf-8")
    import full104_refit_null_sensitivity_core_v1 as core_module
    components = {"runner_sha256": sha(Path(inspect.getsourcefile(verify_gate_implementation))),
                  "core_sha256": sha(Path(inspect.getsourcefile(core_module))),
                  "fit_basis_code_sha256": sha(Path(inspect.getsourcefile(fit_basis)))}
    (fake_gate / "IMPLEMENTATION_COMPONENTS.json").write_text(json.dumps({"components": components, "implementation_fingerprint": canonical_sha(components)}), encoding="utf-8")
    gate_status = {"status":"PASS_IMPLEMENTATION_AND_COMPUTE_GATE", "freeze_root":"593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c", "gate_manifest_sha256":sha(fake_gate/"IMPLEMENTATION_GATE_MANIFEST.csv"), "implementation_fingerprint":canonical_sha(components)}
    (fake_gate / "IMPLEMENTATION_PREFLIGHT_STATUS.json").write_text(json.dumps(gate_status), encoding="utf-8")
    valid_gate_bound = verify_gate_implementation(fake_gate)[0] == canonical_sha(components)
    bad_components = dict(components); bad_components["core_sha256"] = "0"*64; gate_status["implementation_fingerprint"] = canonical_sha(bad_components)
    (fake_gate / "IMPLEMENTATION_COMPONENTS.json").write_text(json.dumps({"components": bad_components}), encoding="utf-8"); (fake_gate / "IMPLEMENTATION_PREFLIGHT_STATUS.json").write_text(json.dumps(gate_status), encoding="utf-8")
    post_gate_core_change_rejected = False
    try: verify_gate_implementation(fake_gate)
    except RuntimeError: post_gate_core_change_rejected = True
    report = {"status": "PASS_PRODUCTION_TARGETED_FIXTURES" if lossless_pass and payload_tamper_rejected and valid_gate_bound and post_gate_core_change_rejected and nested and audit["donors"] == donors and metamorphic_max <= 1e-8 and paired_rejects and old_asymmetric_would_pass and distinct_ab_pass and fingerprint_ok and all(mismatch_rejected.values()) and semantic_equal and forced_resume_equal else "STOP_PRODUCTION_TARGETED_FIXTURES",
              "lossless_plan": {"format": "atomic-npz-columnar-v1", "file_sha256": lossless_file_sha,
                                "semantic_sha256": lossless_semantic_sha, "weights_bitwise_equal": weights_bitwise,
                                "membership_exact": membership_exact, "donor_mass_reload_pass": reload_audit["donors"] == donors,
                                "corrupted_plan_rejected": corrupted_rejected, "dtype_downgrade_rejected": dtype_downgrade_rejected,
                                "coordinated_substitution_rejected": coordinated_substitution_rejected,
                                "csv_explicitly_nonauthoritative": csv_nonauthoritative},
              "payload_and_gate_binding": {"checkpoint_payload_tamper_rejected": payload_tamper_rejected,
                                           "valid_gate_bound": valid_gate_bound,
                                           "post_gate_core_change_rejected": post_gate_core_change_rejected},
              "paired_bootstrap_symmetry": {"production_rejects": paired_rejects, "old_asymmetric_would_pass": old_asymmetric_would_pass},
              "distinct_A_B_end_to_end": {"A_dimension1_pass": bool(joint_a[0]), "B_dimension1_pass": bool(joint_b[0]),
                                          "combined_candidate": selection_ab["candidate_D_shared"], "B_vetoes_A_only_prefix": distinct_ab_pass},
              "nested_cap_identity": nested, "weight_mass": audit, "row_chunk_metamorphic_max_abs": metamorphic_max,
              "resume_fingerprint": {"same_version_accepted": fingerprint_ok, "mismatch_rejected": mismatch_rejected,
                                     "uninterrupted_semantic_sha256": uninterrupted_sha, "resumed_semantic_sha256": resumed_sha,
                                     "semantic_hash_equal": semantic_equal, "forced_interruption_occurred": forced_stop,
                                     "uninterrupted_execution_sha256": uninterrupted_execution_sha,
                                     "resumed_execution_sha256": resumed_execution_sha,
                                     "forced_interruption_resume_equal": forced_resume_equal},
              "selection": selection, "input_sha256": sha(raw), "production_sha256": sha(production)}
    path = out / "PRODUCTION_TARGETED_FIXTURE_REPORT.json"; path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"].startswith("STOP"): raise SystemExit(2)


if __name__ == "__main__": main()
