#!/usr/bin/env python3
"""Freeze the repaired K-curve execution contract only after equivalence is proven."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B

PRECOMMIT = "results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_PRECOMMIT_V1.json"
GEOM = "results/v64/phase_b_design/V64_CONFOUND_BLOCK_GEOMETRY_VERIFICATION_V1.json"
ISOLATION = "results/v64/phase_b_design/V64_SYNTHETIC_RUN_ISOLATION_V1.json"
EQUIV = "results/v64/phase_b_design/V73_STAGE4_KCURVE_SERIAL_PARALLEL_EQUIVALENCE_V1.json"
OUT = "results/v64/phase_b_design/V73_STAGE4_G2_REPAIRED_PREEXECUTION_CONTRACT_V1.json"

FILES = {
    "builder": "scripts/v64/build_stage4_synthetic_worlds_v1.py",
    "geometry_verifier": "scripts/v64/verify_confound_block_geometry_v1.py",
    "executor": "scripts/v64/stage4_executor_v1.py",
    "runner": "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py",
    "equivalence_gate": "scripts/v64/qualify_v73_kcurve_serial_parallel_equivalence.py",
}


def require(path, predicate, message):
    obj = json.load(open(path))
    if not predicate(obj):
        raise SystemExit("STOP: " + message)
    return obj


def main() -> int:
    pc = require(PRECOMMIT, lambda x: "design" in x, "precommit unreadable/incomplete")
    geom = require(
        GEOM,
        lambda x: x.get("status") == "PASS"
        and x.get("ALL_REPAIRED_K_GEOMETRY_QUALIFIED") is True
        and x.get("positive_control", {}).get(
            "verifier_rejects_the_defective_construction") is True,
        "byte-level exact-K geometry is not fully qualified")
    iso = require(
        ISOLATION,
        lambda x: x.get("status") == "PASS"
        and x.get("n_checks") == x.get("n_holding"),
        "synthetic run isolation is not fully qualified")
    eq = require(
        EQUIV,
        lambda x: x.get("status") == "PASS"
        and x.get("all_draws_byte_identical") is True,
        "serial-vs-parallel scientific digest equivalence is not PASS")

    Ks = pc["design"]["K_values"]
    n_draws = int(pc["design"]["draws_per_K"])
    seeds = {
        str(K): [
            dict(draw_index=i, seed_base=800000 + 1000 * i)
            for i in range(n_draws)
        ]
        for K in Ks
    }
    bindings = {
        name: dict(path=path, sha256=B.sha_file(path))
        for name, path in FILES.items()
    }
    bindings.update({
        "original_precommit": dict(path=PRECOMMIT, sha256=B.sha_file(PRECOMMIT)),
        "geometry_receipt": dict(path=GEOM, sha256=B.sha_file(GEOM)),
        "isolation_receipt": dict(path=ISOLATION, sha256=B.sha_file(ISOLATION)),
        "serial_parallel_equivalence_receipt": dict(
            path=EQUIV, sha256=B.sha_file(EQUIV)),
    })

    out = dict(
        schema="V73_STAGE4_G2_REPAIRED_PREEXECUTION_CONTRACT_V1",
        date="2026-10-02",
        status="FROZEN__READY_FOR_REPAIRED_SYNTHETIC_CURVE_ONLY",
        scope="synthetic HIDDEN_CONFOUND_K operating-characteristic experiment only",
        design=dict(
            K_values=Ks,
            donor_count=pc["design"]["donor_count"],
            draws_per_K=n_draws,
            seeds=seeds,
            seed_identity_rule=(
                "seed_base = 800000 + 1000*draw_index; scientific identity is "
                "(K, draw_index, seed_base); worker number, completion order, PID and "
                "wall clock are forbidden from scientific identity"),
            partition_semantics="EXACT_K_OCCUPIED_BALANCED_BLOCKS",
            K_max_singleton_requirement=True,
            run_namespace="JEPA_SYNTHETIC_RUN_ID",
            scheduling_workers="operational only; may vary only after equivalence PASS",
        ),
        prerequisite_receipts=dict(
            geometry_status=geom.get("status"),
            isolation_status=iso.get("status"),
            serial_parallel_equivalence_status=eq.get("status"),
        ),
        bindings=bindings,
        historical_v1=dict(
            artifact="results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_CURVE_V1.json",
            preserved=True,
            supersession_scope=(
                "V1 remains valid only as a measurement of the historical "
                "sampling-with-replacement factor-pool generator. It is superseded for "
                "claims about exact-K partition behavior or a one-factor-per-edge K=200 endpoint."),
        ),
        repaired_result_path=(
            "results/v64/phase_b_design/"
            "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json"),
        S102=dict(
            status="OPEN",
            rule=(
                "The repaired curve characterises the named historical executor G2 "
                "implementation only. It must not define or tune the final Stage-4 G2 "
                "statistic, alpha, confidence level, equivalence margin or biological "
                "acceptance threshold."),
        ),
        governance=dict(
            real_stage4="NOT_AUTHORIZED",
            real_correspondence="UNOPENED",
            training="OFF",
            multimodal_training="OFF",
        ),
        real_substrate_read=False,
        computed_real_correspondence_values=0,
    )
    with open(OUT, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("FROZEN repaired K-curve pre-execution contract")
    print("sha256 " + B.sha_file(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
