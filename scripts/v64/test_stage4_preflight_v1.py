#!/usr/bin/env python3
"""Prove every Stage-4 preflight gate can REJECT, by planting a violation for each.

A preflight that only ever sees correct inputs proves nothing. Each gate here is run
against a deliberately corrupted copy of the authority contract, and a gate that still
passes on its own violation is reported as NOT A REAL GATE.

Mutations are applied to an in-memory copy. The live contract is never written to, so this
suite cannot leave a stale artifact behind -- the defect that produced S61.

TRAINING=OFF. STAGE 4 NOT AUTHORISED. No correspondence value is computed.
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import verify_stage4_preflight_v1 as PF                          # noqa: E402

DIR = "results/v64/phase_b_design"
AUTH = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json")


def mutations():
    return [
      ("G1_INPUT_DIGESTS", "corrupt a bound substrate-shard digest",
       lambda c: c["BOUND_PHASE_B_INPUTS"]["substrate_shards"][
           "PHASE_B_SUBSTRATE_s00.npz"].__setitem__("sha256", "0" * 64)),
      ("G2_ESTIMATOR_UNMODIFIED", "claim a different estimator digest",
       lambda c: c["ESTIMATOR_IMPORTED_UNMODIFIED"].__setitem__("sha256", "f" * 64)),
      ("G3_NO_MATRIX_REOPEN", "drop the matrix-reopening prohibition",
       lambda c: c.__setitem__("WHAT_STAGE_4_MAY_NOT_READ",
                               ["nothing in particular"])),
      ("G4_PARTITION_NOT_REBUILT", "drop a substrate shard from the binding",
       lambda c: c["BOUND_PHASE_B_INPUTS"]["substrate_shards"].pop(
           "PHASE_B_SUBSTRATE_s07.npz")),
      ("G5_WEIGHTING", "promote the companion weighting to primary",
       lambda c: c["METHOD_LOCKS"]["weighting_hierarchy"].__setitem__(
           "PRIMARY", "PROMOTER_EQUAL")),
      ("G6_BOOTSTRAP", "change the replicate count",
       lambda c: c["METHOD_LOCKS"]["uncertainty"].__setitem__("replicates", 1000)),
      ("G7_NULL_DENOMINATOR", "fold the forced coincidences back into the denominator",
       lambda c: c["NULL_AND_STRATA_LOCKS"].__setitem__(
           "randomized_null_denominator", 10654 + 158)),
      ("G8_R3_LABEL", "remove the mandatory conditional label",
       lambda c: c["NULL_AND_STRATA_LOCKS"].__setitem__("R3_required_label", "NONE")),
      ("G9_CONTROL_B_NULL_ONLY", "let CONTROL_B into the primary contrast",
       lambda c: c["NULL_AND_STRATA_LOCKS"].__setitem__(
           "control_B_role", "may be used in the primary linked-versus-control contrast")),
      ("G10_ANTI_FALSE_GREEN", "soften the control-vs-control STOP to a warning",
       lambda c: [a.__setitem__("if_it_fails", "note it and continue")
                  for a in c["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"]
                  ["anti_false_green"] if a["name"] == "CONTROL_VS_CONTROL_NULL"]),
      ("G11_PROTECTED", "turn training on",
       lambda c: c["governance"].__setitem__("training", "ON")),
      ("G12_NO_THRESHOLD_ON_EFFECT", "impose a minimum effect size",
       lambda c: c["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"].__setitem__(
           "no_minimum_effect_size", {"why": "a minimum of 0.010 is imposed"})),
      ("G13_FUNNEL", "drop the funnel reconciliation requirement",
       lambda c: c["SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT"].__setitem__(
           "PASS_requires_all_of", ["one-sided LCB95 of Delta > 0"])),
      ("G14_STRATA", "allow silent pooling across strata",
       lambda c: c["NULL_AND_STRATA_LOCKS"].__setitem__(
           "no_silent_pooling", "pooling is fine")),
      # S68: a required input that is ABSENT must STOP, not be skipped
      ("G1_INPUT_DIGESTS", "point a required input at a path that does not exist",
       lambda c: c["BOUND_PHASE_B_INPUTS"]["t5_donor_aggregates"].__setitem__(
           "path", "D:/jepa_v5_outputs_20260925/v64_phase_b/THIS_FILE_DOES_NOT_EXIST.npz")),
      # S70: a repo-resident input must carry a real blob
      ("G1b_REPO_INPUTS_HAVE_GIT_BLOBS", "blank a repo-resident input's git blob",
       lambda c: c["INHERITED_NOT_RESTATED"]["downstream_null_statistical_V3"].__setitem__(
           "git_blob", "UNCOMMITTED")),
      # S69: both permutation digests must be checked, and the binding must be present
      ("G15_PERMUTATION_COROBORATION", "corrupt the permutation array-content digest",
       lambda c: c["CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT"]["pairing_permutation"]
       .__setitem__("array_content_sha256", "0" * 64)),
      ("G15_PERMUTATION_COROBORATION", "corrupt the permutation npy-file digest",
       lambda c: c["CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT"]["pairing_permutation"]
       .__setitem__("npy_file_sha256", "f" * 64)),
      ("G15_PERMUTATION_COROBORATION", "remove the permutation binding entirely",
       lambda c: c.__setitem__("CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT", {})),
    ]


def main() -> int:
    live = json.load(open(AUTH))
    before = B.sha_file(AUTH)
    base = PF.run_gates(live)
    base_failed = [k for k, (ok, _) in base.items() if not ok]
    if base_failed:
        print(f"STOP: the live authority already fails {base_failed}")
        return 2

    results = []
    for gate, what, mut in mutations():
        c = copy.deepcopy(live)
        mut(c)
        g = PF.run_gates(c)
        fired = sorted(k for k, (ok, _) in g.items() if not ok)
        caught = gate in fired
        results.append(dict(gate=gate, planted=what, gates_that_fired=fired,
                            caught_by_its_own_gate=caught,
                            is_a_real_gate=caught))
        print(f"  {gate:<28} {what[:44]:<46} fired={fired if fired else 'NONE'}  "
              f"{'OK' if caught else 'NOT A REAL GATE'}")

    after = B.sha_file(AUTH)
    real = [r for r in results if r["is_a_real_gate"]]
    out = dict(schema="V64_STAGE4_PREFLIGHT_TESTS_V1", date="2026-09-30",
               authority=dict(path=AUTH, sha256=after),
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               live_contract_untouched=before == after,
               mutations_applied_in_memory_only=True,
               n_gates=len(results), n_real_gates=len(real),
               every_gate_rejects_its_own_violation=len(real) == len(results),
               results=results,
               definition_of_real="a gate counts as real only if the preflight passes on "
                                  "the live contract AND that same gate fails on a "
                                  "contract carrying its specific violation",
               computed_no_correspondence_value=True,
               EXECUTION_AUTHORITY="NOT_GRANTABLE",
               unsatisfied_execution_prerequisites=live.get(
                   "EXECUTION_PREREQUISITES_NOT_YET_SATISFIED", {}).get(
                   "unsatisfied_prerequisites", []),
               note="every gate below rejects its own violation. That makes the DESIGN "
                    "gates real; it does not make execution grantable, which waits on the "
                    "executor being implemented and bound.",
               status="PASS" if len(real) == len(results) else "FAIL",
               governance=live["governance"])
    p = os.path.join(DIR, "V64_STAGE4_PREFLIGHT_TESTS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nlive contract untouched: {out['live_contract_untouched']}")
    print(f"{len(real)}/{len(results)} gates reject their own violation -> {out['status']}")
    print(f"receipt sha256 {B.sha_file(p)}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
