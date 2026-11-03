"""Synthetic-first diagnosis from immutable PR328/PR348 worlds into existing PR474/Task5.

Not a new generator, estimator, qualification, or real source experiment.
PR328 original world and fit hashes are checked against its frozen V2 receipt.
V80 original eight challenge worlds are replayed only for structural/detection
diagnostics, never used for candidate selection or scoring.
Controller truth never enters the reader/consumer transport.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PR328 = "25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec"
PR348 = "e99d1f214e76a5e3911eea438c32a1e60f70754f"
PR474 = "e7635e7982e950a010d181ec6f6883a18ade0db6"
PR328_WORLD = "dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66"
PR328_FIT = "fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a"
V80_BENCHMARK = "16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38"
OFF = {"real_training_authorized": False, "target_selection_authorized": False,
       "representation_selection_authorized": False, "stage4_authorized": False,
       "real_source_qualified": False}


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def head(root: Path, expected: str):
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    check(actual == expected, f"unexpected frozen synthetic source head: {actual}")


def persist(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def replay_pr328(root: Path, output: Path):
    head(root, PR328)
    sys.path.insert(0, str(root))
    from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology
    from scripts.v79.unified_synthetic_fit_view_v1 import (
        UnifiedObservationConfig, observe_unified_world, fit_view_sha256,
    )
    receipt = json.loads((root / "results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json").read_text())
    check(receipt["schema"] == "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2", "wrong V2 receipt")
    check(receipt["world_sha256"] == PR328_WORLD and receipt["fit_view_sha256"] == PR328_FIT,
          "frozen PR328 receipt changed")
    world = build_unified_biology(UnifiedBiologyConfig(), seed=20261013)
    fit = observe_unified_world(world, UnifiedObservationConfig(), seed=20261014)
    check(world.world_hash == PR328_WORLD, "not original frozen PR328 world")
    check(fit_view_sha256(fit) == PR328_FIT, "not original frozen PR328 fit view")
    check(fit.values.shape == fit.support.shape, "counts/support shape mismatch")
    check(not bool((fit.values[~fit.support] != 0).any()), "unmeasured contains scalar")
    check(bool((fit.support & (fit.values == 0)).any()), "no measured-zero stress case")
    check(bool((~fit.support).any()), "no structural absence stress case")

    # Selection is deterministic from synthetic *source and train-fold metadata*
    # only. Never select cells by count, target, diagnosis or controller truth.
    chosen = []
    for source in sorted(set(str(x) for x in fit.source)):
        selected = [i for i in range(len(fit.split))
                    if fit.split[i] == "train" and str(fit.source[i]) == source][:10]
        check(len(selected) == 10, f"insufficient frozen metadata stratum {source}")
        chosen.extend(selected)
    cells = []
    for i in chosen:
        counts = [int(v) for v in fit.values[i]]
        measured = [bool(v) for v in fit.support[i]]
        cells.append({
            "cell_id": str(fit.rna_entity_id[i]),
            "donor_id": f"D{int(fit.donor_id[i]):04d}",
            "source_id": "PR328_SYNTH_" + str(fit.source[i]),
            "operator_id": "PR328_SYNTH_OPERATOR_" + str(fit.source[i]),
            "split": str(fit.split[i]),
            "counts": counts,
            "support": measured,
        })
    payload = {
        "schema": "PR328_FROZEN_FIT_ONLY_TO_CASEBUNDLE_ADMISSION_V1",
        "frozen_generator_head": PR328,
        "world_sha256": PR328_WORLD,
        "fit_view_sha256": PR328_FIT,
        "source_counts_sha256": fit.counts_hash,
        "source_manifest_sha256": hashlib.sha256(
            (root / "results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json").read_bytes()
        ).hexdigest(),
        "n_original_cells": len(fit.donor_id),
        "n_original_addresses": len(fit.address_index),
        "n_chosen_cells": len(cells),
        "chosen_sources": sorted(set(c["source_id"] for c in cells)),
        "measured_zero_original": int((fit.support & (fit.values == 0)).sum()),
        "structural_unmeasured_original": int((~fit.support).sum()),
        "cells": cells,
        "authority": dict(OFF),
        "limits": ["Frozen PR328 support derived from empirical detection fractions, NOT real assay membership",
                   "All library totals computed as synthetic integer counts; NOT physical human source totals",
                   "Fit-only observed RNA; no latent biology, perturbation truth, model labels or controller truth exported",
                   "This exercise diagnoses software contracts, not qualified estimator or biology"],
    }
    check(len(payload["chosen_sources"]) == 3, "source strata missing from deterministic sample")
    check(all(c["split"] == "train" for c in cells), "nontraining observations exported")
    check(all(v is False for v in payload["authority"].values()), "authority escalated")
    persist(output, payload)
    print("PR328_ORIGINAL_WORLD_AND_FIT_VERIFIED__FIT_ONLY_OBSERVATIONS_READY")


def exercise_pr474(root: Path, payload_path: Path, report: Path):
    head(root, PR474)
    sys.path.insert(0, str(root))
    from scripts.v5.td_unified.q_excluded_depth_v1 import (
        MEASURED_SCALAR, STRUCTURALLY_UNMEASURED, MEASURED_COLLISION_UNRESOLVED,
        QExcludedDepthNotEstimable, produce_rights_ladder_observations,
    )
    from scripts.v5.td_unified.casebundle_v1 import validate_casebundle, CaseBundleError

    p = json.loads(payload_path.read_text())
    check(p["schema"] == "PR328_FROZEN_FIT_ONLY_TO_CASEBUNDLE_ADMISSION_V1"
          and p["world_sha256"] == PR328_WORLD and p["fit_view_sha256"] == PR328_FIT, "wrong transport")
    check(p["authority"] == OFF, "synthetic source authority changed")
    check(p["n_chosen_cells"] == 30 and len(p["cells"]) == 30, "unexpected sample size")
    addresses = [f"PR328_SYNTH_ADDR_{i:04d}" for i in range(p["n_original_addresses"])]
    query = addresses[0]  # PR328 makes this commonly supported; frozen before seeing counts
    wrong_query = addresses[1]
    states = {}
    raw_cells = []
    for c in p["cells"]:
        source, op = c["source_id"], c["operator_id"]
        check(source.endswith(op.split("_")[-1]), "source/operator transport mismatch")
        by_a = {a: MEASURED_SCALAR if ok else STRUCTURALLY_UNMEASURED
                for a, ok in zip(addresses, c["support"])}
        if op in states:
            check(states[op] == by_a, "source mask differs within a synthetic source")
        else:
            states[op] = by_a
        raw_cells.append({
            "cell_id": c["cell_id"], "donor_id": c["donor_id"],
            "source_id": source, "operator_id": op,
            "counts": {a: n for a, n, available in zip(addresses, c["counts"], c["support"])
                       if available and n > 0},
            "library_total": sum(c["counts"]),  # fixture sum ONLY, not real physical library
        })
        check(not any(n > 0 and not available for n, available in zip(c["counts"], c["support"])),
              "structurally unavailable gene has observed count")
    rights = {a: "QUERY_ONLY" if a == query else "BASE" for a in addresses}
    ladder = [{"level_id": "BASE", "evidence_rights": ["BASE"]},
              {"level_id": "RICH", "evidence_rights": ["BASE", "QUERY_ONLY"]}]
    accepted = []
    abstained = 0
    for c in raw_cells:
        try:
            output = produce_rights_ladder_observations(cells=[c], address_rights=rights,
                                                         operator_states=states, ladder=ladder)
        except QExcludedDepthNotEstimable:
            abstained += 1
            continue
        check(output["authority_scope"] == "FIXTURE_ONLY" and output["source_authenticated"] is False,
              "fixture falsely authenticated")
        base, rich = output["levels"]
        rows = base["rows"]
        qrow = next(row for row in rows if row["address_id"] == query)
        check(qrow["state"] in ("WITHHELD_BY_EVIDENCE_RIGHTS", STRUCTURALLY_UNMEASURED),
              "query not withheld")
        check(qrow["count"] is None and qrow["library_size"] is None, "private query leaked")
        base_scalars = [r for r in rows if r["state"] == MEASURED_SCALAR]
        check(base_scalars and len({r["library_size"] for r in base_scalars}) == 1,
              "base source does not have one depth")
        depth = base_scalars[0]["library_size"]
        check(depth == sum(c["counts"].get(a, 0) for a in addresses[1:]),
              "q-excluded depth must be base-right mapped count mass in this fixture")
        check(depth != c["library_total"] or c["counts"].get(query, 0) == 0,
              "source total illicitly copied into D1")
        for r in rows:
            if r["state"] == MEASURED_SCALAR and r["address_id"] not in c["counts"]:
                check(r["count"] == 0, "measured zero changed to structural absence")
        accepted.append((c, output, depth))
    check(accepted and len(accepted) + abstained == 30, "fixture lost cells")
    check({c["source_id"] for c, _, _ in accepted} == set(p["chosen_sources"]),
          "one source could not exercise qualified fixture math")

    original, prior, base_depth = accepted[0]
    q_original = original["counts"].get(query, 0)
    altered = deepcopy(original)
    q_new = max(q_original + 17, base_depth + 5)
    altered["counts"][query] = q_new
    altered["library_total"] += (q_new - q_original)
    changed = produce_rights_ladder_observations(cells=[altered], address_rights=rights,
                                                  operator_states=states, ladder=ladder)
    check(changed["levels"][0]["rows_sha256"] == prior["levels"][0]["rows_sha256"],
          "mapped hidden query changed base-visible bytes")
    check(changed["levels"][1]["rows_sha256"] != prior["levels"][1]["rows_sha256"],
          "richer observation failed positive query perturbation")

    # Exact existing Task5 fixture: base passes, richer data with query count > D1
    # depth must refuse its physical-library_size contract. Never rewrite Task5.
    def case(observations, label):
        return {
            "schema": "KNOWN_TRUTH_CASEBUNDLE_V1",
            "case_id": label,
            "authority_scope": "FIXTURE_ONLY",
            "manifest_sha256": p["source_manifest_sha256"],
            "population_access_policy_sha256": sha(rights),
            "address_universe_sha256": sha(addresses),
            "reader_partition": "reader_fit",
            "observations": observations,
        }
    base_fixture = validate_casebundle(case(changed["levels"][0]["casebundle_observations"],
                                             "PR328_BASE_ONLY_DIAGNOSTIC"))
    check(base_fixture["status"] == "CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY"
          and base_fixture["externally_authenticated"] is False, "base fixture authority drift")
    try:
        validate_casebundle(case(changed["levels"][1]["casebundle_observations"],
                                 "PR328_RICH_VIEW_MUST_NOT_BE_CAST_AS_PHYSICAL_TOTAL"))
    except CaseBundleError:
        richer_refused = True
    else:
        richer_refused = False
    check(richer_refused, "Task5 unexpectedly accepted projected depth as physical total")

    # PR478's known source-issuer weaknesses, now exercised on PR328 *frozen*
    # source/donor/zero-support regimes rather than a hand-made generator world.
    offledger = deepcopy(original)
    offledger["library_total"] += 11  # hidden off-ledger molecule, no mapped address
    leaky = produce_rights_ladder_observations(cells=[offledger], address_rights=rights,
                                               operator_states=states, ladder=ladder)
    check(leaky["levels"][0]["rows_sha256"] != prior["levels"][0]["rows_sha256"],
          "off-ledger hidden-mass counterexample did not change D1")
    unbound_source = deepcopy(original)
    unbound_source["source_id"] = "PR328_SYNTH_FORGED_SOURCE"
    forged = produce_rights_ladder_observations(cells=[unbound_source], address_rights=rights,
                                                operator_states=states, ladder=ladder)
    check(forged["source_authenticated"] is False
          and forged["levels"][0]["rows_sha256"] != prior["levels"][0]["rows_sha256"],
          "source-id forgery witness missing")
    not_excluded = {a: "BASE" for a in addresses}
    q_exposed = produce_rights_ladder_observations(cells=[altered], address_rights=not_excluded,
                                                   operator_states=states, ladder=ladder)
    exposed_q = next(x for x in q_exposed["levels"][0]["rows"] if x["address_id"] == query)
    check(exposed_q["state"] == MEASURED_SCALAR and exposed_q["count"] == q_new
          and q_exposed["source_authenticated"] is False,
          "missing independently bound query-issuer witness")
    collided = deepcopy(states)
    collided[original["operator_id"]] = dict(collided[original["operator_id"]])
    collided[original["operator_id"]][query] = MEASURED_COLLISION_UNRESOLVED
    collision_cell = deepcopy(original)
    collision_cell["counts"].pop(query, None)
    try:
        produce_rights_ladder_observations(cells=[collision_cell], address_rights=rights,
                                           operator_states=collided, ladder=ladder)
    except QExcludedDepthNotEstimable:
        collision_refused = True
    else:
        collision_refused = False
    check(collision_refused, "outside-base collision was coerced to scalar")

    alternate = dict(rights)
    alternate[query] = "BASE"
    alternate[wrong_query] = "QUERY_ONLY"
    wrong = produce_rights_ladder_observations(cells=[original], address_rights=alternate,
                                               operator_states=states, ladder=ladder)
    check(wrong["levels"][0]["rows_sha256"] != prior["levels"][0]["rows_sha256"],
          "wrong-query policy has no observable effect at all")

    summary = {
        "schema": "PR328_FROZEN_SYNTHETIC_CASEBUNDLE_CROSS_COMPONENT_DIAGNOSTIC_V1",
        "status": "EXISTING_FIXTURE_MATH_PASSES__SOURCE_BINDING_AND_RICH_CASEBUNDLE_NOT_QUALIFIED",
        "original_world_sha256": PR328_WORLD,
        "original_fit_sha256": PR328_FIT,
        "pr474_head": PR474,
        "all_original_cells": p["n_original_cells"],
        "metadata_selected_fixture_cells": p["n_chosen_cells"],
        "source_strata": p["chosen_sources"],
        "fixture_cell_passes": len(accepted),
        "fixture_cell_not_estimable": abstained,
        "original_measured_zero": p["measured_zero_original"],
        "original_structurally_unmeasured": p["structural_unmeasured_original"],
        "synthetic_hidden_query_base_invariance": True,
        "positive_richer_query_perturbation": True,
        "source_id_forgery_accepted_by_unauthenticated_fixture": True,
        "q_in_base_accepted_by_unauthenticated_fixture": True,
        "offledger_hidden_mass_changes_student_depth": True,
        "rich_view_falsely_uses_student_depth_as_physical_total_and_is_refused": True,
        "outside_base_collision_refused_not_estimable": True,
        "wrong_query_changes_fixture_view_only_not_a_learned_control": True,
        "authority": dict(OFF),
        "scientific_limits": [
            "Original PR328 VISIBILITY>0 source-support semantics cannot infer real assay support",
            "Source labels are synthetic regimes, not authentic human provider IDs",
            "Output uses only recorded frozen fit-side synthetic integer RNA; no controller truth or fitting",
            "PR474 and Task5 code tested unchanged; no real source issuance, q rights, target, or Stage4",
        ],
    }
    persist(report, summary)
    print(summary["status"])


def replay_v80(root: Path, report: Path):
    head(root, PR348)
    sys.path.insert(0, str(root))
    import numpy as np
    from scripts.v80.v80_sparse_positive_benchmark import (
        build_sparse_positive_worlds, benchmark_identity, serialize_fit_transport,
        validate_fit_transport, ESTIMABLE, NOT_ESTIMABLE,
    )
    frozen = json.loads((root / "results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json").read_text())
    check(frozen["benchmark_identity_sha256"] == V80_BENCHMARK and frozen["n_worlds"] == 8
          and frozen["n_fits"] == 192 and frozen["status"] == "BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN",
          "original V80 frozen receipt does not match expected benchmark")
    worlds = build_sparse_positive_worlds(seed_root=41000000)
    # Bounded no-truth diagnostic: hash ONLY fit-visible arrays to distinguish
    # support/detection drift from continuous positive-value floating drift.
    # Do not print controller latent arrays, gene effects or cell-level values.
    import platform
    fit_digests = []
    for world in worlds:
        fit_digests.append({
            "family": world.family,
            "support_digest": hashlib.sha256(world.support.tobytes()).hexdigest(),
            "detected_digest": hashlib.sha256(world.detected.tobytes()).hexdigest(),
            "design_digest": hashlib.sha256(world.design_matrix.tobytes()).hexdigest(),
            "positive_value_digest": hashlib.sha256(world.positive_value.tobytes()).hexdigest(),
        })
    print("V80_FIT_VISIBLE_FIELD_SHA_DIAGNOSTIC=" + json.dumps({
        "numpy": np.__version__, "python": platform.python_version(),
        "processor": platform.processor(), "platform": platform.platform(),
        "families": fit_digests,
    }, sort_keys=True), flush=True)
    observed_v80_hash = benchmark_identity(worlds)
    if observed_v80_hash != V80_BENCHMARK:
        # Never retune or relax the frozen benchmark identity. Expose only digests
        # and runtime metadata, not controller truth, to diagnose host-dependent drift.
        import platform
        print("V80_PINNED_SHA_MISMATCH__REFUSE", json.dumps({
            "expected": V80_BENCHMARK, "actual": observed_v80_hash,
            "numpy": np.__version__, "python": platform.python_version(),
            "processor": platform.processor(), "platform": platform.platform(),
            "fit_sha256": sha(serialize_fit_transport(worlds)),
        }, sort_keys=True), flush=True)
        raise AssertionError("V80 frozen eight-world identity mismatch; source stays frozen")
    fit = serialize_fit_transport(worlds)
    validate_fit_transport(fit)
    check(fit["authority"] == {"estimator_qualification_authorized": False,
                                "training_authorized": False}, "V80 fit package self-promoted")
    cases = []
    for world in worlds:
        support = np.asarray(world.support)
        detected = np.asarray(world.detected)
        check(not bool((detected & ~support).any()), "unmeasured scalar was detected")
        check(bool((support & ~detected).any()), "support conflated with detection")
        check(set(np.unique(world.split)) == {"train", "test"}, "donor-isolated split absent")
        for donor in np.unique(world.donor_id):
            check(len(set(world.split[world.donor_id == donor])) == 1, "donor crossed split")
        info = {
            "family": world.family,
            "structural_missing_atoms": int((~support).sum()),
            "measured_zero_atoms": int((support & ~detected).sum()),
            "detected_measured_atoms": int((support & detected).sum()),
            "estimability_truth_scope": "CONTROLLER_DIAGNOSTIC_SUMMARY_ONLY_NOT_FIT_TRANSPORT",
        }
        if world.family == "SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE":
            check(world.estimability_truth == NOT_ESTIMABLE and not detected.any()
                  and support.any(), "all-zero measured is NOT structural absence")
        if world.family == "SP06_RANK_DEFICIENT_NOT_ESTIMABLE":
            check(world.estimability_truth == NOT_ESTIMABLE
                  and np.linalg.matrix_rank(world.design_matrix) < world.design_matrix.shape[1],
                  "rank-deficient null not preserved")
        if world.family == "SP04_SUPPORT_THINNED_ESTIMABLE":
            check(info["structural_missing_atoms"] > 0 and info["measured_zero_atoms"] > 0,
                  "support thinning lost measured-zero distinction")
        cases.append(info)
    check(len(cases) == 8 and len(fit["worlds"]) == 8, "frozen stress families omitted")
    persist(report, {
        "schema": "V80_FROZEN_EIGHT_FAMILY_SUPPORT_DETECTION_DIAGNOSTIC_V1",
        "benchmark_identity_sha256": V80_BENCHMARK,
        "original_seed_root": 41000000,
        "fit_transport_schema": fit["schema"],
        "status": "EIGHT_FROZEN_STRESS_FAMILIES_REPLAYED__NO_ESTIMATOR_RUN",
        "cases": cases,
        "authority": dict(OFF),
        "note": "V80 positives are continuous fit outcomes, NOT raw integer physical RNA; never cast into CaseBundle or use 85 V79 forensic results for model selection",
    })
    print("V80_EIGHT_FROZEN_STRESS_FAMILIES_REPLAYED__NO_ESTIMATOR")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["pr328", "pr474", "v80"])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.mode == "pr328":
        check(args.payload is not None, "pr328 payload path required")
        replay_pr328(args.source_root.resolve(), args.payload)
    elif args.mode == "pr474":
        check(args.payload is not None and args.report is not None, "consumer paths required")
        exercise_pr474(args.source_root.resolve(), args.payload, args.report)
    else:
        check(args.report is not None, "V80 report path required")
        replay_v80(args.source_root.resolve(), args.report)


if __name__ == "__main__":
    main()
