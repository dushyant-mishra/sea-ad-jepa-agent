#!/usr/bin/env python3
"""Build (or --check) the frozen corrected-replay contract, TD_CORRECTED_REPLAY_CONTRACT_V1.json.

The contract defines no new science. It binds:
  - the owner's prospective prerequisite amendment (2026-10-12);
  - the predecessor facts: accepted G6, G7 NOT_ESTIMABLE, the disjointness diagnostic, spent authority;
  - every frozen science reference by SHA-256;
  - the exact recovered executors (archive members) and the admitted TD59 successor;
  - the frozen stage order, invocation order, sequential-stop rules and terminals;
  - the adapter and execution environment;
  - the fresh one-shot namespace;
  - the authority, estimability and interpretation policies;
  - two owner decisions the frozen documents do not make. These are recorded as PROPOSED and must be ratified
    before QUALIFY can pass.
Every SHA is recomputed from bytes at build time: committed files, and members of the authenticated archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json"
AMENDMENT = ROOT / "target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_PREREQUISITE_AMENDMENT_20261012.json"
ARCHIVE_NAME = "JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip"
ARCHIVE_SHA = "c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417"
ARCHIVE_BYTES = 92_478_083

SCIENCE_REFERENCES = [
    "custody/target_discovery/TD_CORRECTED_BIOLOGICAL_REPLAY_PREFREEZE_20261010.json",
    "custody/target_discovery/TD_CORRECTED_REPLAY_EXECUTOR_PROVENANCE_LEDGER_20261010.json",
    "custody/target_discovery/TD57C_EXECUTOR_RECOVERY_RECEIPT_20261010.json",
    "custody/target_discovery/TD_HISTORICAL_FIXTURE_LOCAL_REPLAY_QUALIFICATION_20261010.json",
    "docs/agent/JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md",
    "docs/superpowers/specs/2026-10-10-td59-replay-provenance-addendum.md",
    "docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md",
    "docs/superpowers/specs/2026-10-12-td-corrected-replay-routing-v2-c6.md",
    "docs/superpowers/specs/2026-10-12-td-downstream-turnkey-gates-design.md",
    "docs/superpowers/plans/2026-10-10-td-corrected-replay-adapter-qualification.md",
    "docs/superpowers/plans/2026-10-12-td-corrected-replay-turnkey-gate.md",
    "scripts/v5/td_corrected_replay_routing_v2.py",
    "scripts/v5/td_target_tournament_routing_v4.py",
    "target_discovery/iterations/td56s_disjoint_gene_relational_geometry/TD56S_PROSPECTIVE_SCREEN.md",
    "target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_PROSPECTIVE_SCREEN.md",
    "target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_LOCAL_EXECUTION_BINDING.md",
    "target_discovery/iterations/td57c_three_view_local_geometry/TD57C_PROSPECTIVE_SCREEN.md",
    "target_discovery/iterations/td59_mesoscale_half_locality/TD59_PROSPECTIVE_SCREEN.md",
    "target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/TD59_REPLAY_CLOSURE_20260908.md",
    "target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/TD59_REPLAY_CLOSURE_CASE_MATCH.csv",
]
TD59_PATH = "target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py"
SOURCE_ORDER = ["HVS", "NPH52", "SEA_AD"]
PANEL_ORDER = [[0, "HVS"], [0, "NPH52"], [0, "SEA_AD"], [1, "HVS"], [1, "NPH52"], [1, "SEA_AD"]]
NOT_ESTIMABLE_PATTERNS = ["has <4 measurable donors", "null vector is not exactly 64 finite values",
                          "structurally eligible donors"]


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_commit(prefix: str) -> str:
    """Resolve an evidence commit through git; never hand-type a full SHA into the contract."""
    import subprocess
    full = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--verify", prefix + "^{commit}"], text=True).strip()
    if not full.startswith(prefix) or len(full) != 40:
        raise SystemExit(f"STOP: cannot resolve commit {prefix}")
    return full


def git_blob_sha256(commit: str, path: str) -> str:
    """SHA-256 of a committed file, read from the git object; never hand-typed."""
    import subprocess
    return hashlib.sha256(subprocess.check_output(["git", "-C", str(ROOT), "cat-file", "blob", f"{commit}:{path}"])).hexdigest()


def archive_members(archive: Path, names: list[str]) -> dict:
    if sha(archive) != ARCHIVE_SHA:
        raise SystemExit("STOP: authenticated TD41-TD58 archive SHA mismatch")
    out = {}
    with zipfile.ZipFile(archive) as z:
        for n in names:
            m = [x for x in z.namelist() if x == n or x.endswith("/" + n)]
            if len(m) != 1:
                raise SystemExit(f"STOP: archive member {n} not unique: {m}")
            raw = z.read(m[0])
            out[n] = {"archive_path": m[0], "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return out


def build(archive: Path) -> dict:
    exe = archive_members(archive, ["run_td56_hvs.py", "run_td56_nph.py", "run_td56_sea_fast.py",
                                    "td57b_fixed_relational_recurrence.py", "td57b_fast_wrapper.py",
                                    "td57c_three_view_local_geometry.py"])
    hist = archive_members(archive, ["td56_HVS_result.npz", "td56_NPH52_result.npz", "td56_SEA_AD_result.npz",
                                     "td57b_p0_hvs.json", "td57b_p0_nph52.json", "td57b_p0_seaad.json",
                                     "td57b_p1_hvs.json", "td57b_p1_nph52.json", "td57b_p1_seaad.json",
                                     "td57c_p0_hvs.json", "td50_HVS.npz", "td50_NPH52.npz", "td50_SEA_AD.npz"])
    want_exec = {"run_td56_hvs.py": "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43",
                 "run_td56_nph.py": "090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162",
                 "run_td56_sea_fast.py": "c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866",
                 "td57b_fixed_relational_recurrence.py": "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e",
                 "td57c_three_view_local_geometry.py": "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c"}
    for n, s in want_exec.items():
        if exe[n]["sha256"] != s:
            raise SystemExit(f"STOP: executor {n} is not the frozen {s}")
    if sha(ROOT / TD59_PATH) != "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085":
        raise SystemExit("STOP: TD59 successor is not 870ddea0")
    refs = {p: sha(ROOT / p) for p in SCIENCE_REFERENCES}
    flags = {"g6_execution_authorized": False, "g7_execution_authorized": False, "target_selection_authorized": False,
             "td60_authorized": False, "stage4_authorized": False, "training_authorized": False}
    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_CONTRACT_V1",
        "status": "FROZEN_FOR_LAUNCH_QUALIFICATION__CORRECTED_REPLAY_NOT_RUN",
        "date": "2026-10-12",
        "replay_science_frozen": True,
        "prerequisite_amendment": {"path": AMENDMENT.relative_to(ROOT).as_posix(), "sha256": sha(AMENDMENT)},
        "predecessors": {
            "g6": {"producer_commit": "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0",
                   "external_acceptance_sha256": "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb",
                   "external_acceptance_source": {"commit": "17a68667174ae8583305c546639dced7dded94d9",
                                                  "path": "docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json"},
                   "receipt_sha256": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
                   "values_sha256": "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9",
                   "metadata_sha256": "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74",
                   "artifact_sha256": {
                       "G6_EXECUTION_START.json": "49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1",
                       "G6_RECEIPT.json": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
                       "MANIFEST.json": "4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf",
                       "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz": "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9",
                       "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz": "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74"},
                   "namespace": "D:/jepa_td_real_g6_20261011/G6_OUT_ff4a21f9"},
            "g7": {"implementation_commit": "8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27",
                   "marker_sha256": "2579b9a6a5cbfc89f4dd38082515a290681fc5413afeb95536b62bbfd46f2667",
                   "receipt_sha256": "47f9be6e8fef3fa70c07fbe8011fa1360df72e26b8259fc9655a369768a97fcf",
                   "terminal": "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP", "is_pass": False,
                   "namespace": "D:/jepa_td_real_g6_20261011/G7_OUT_8d41fb98",
                   "execution_evidence_commit": git_commit("bffba425")},
            "g7_diagnostic": {"evidence_commit": git_commit("0b50938e"),
                              "result_path": "docs/agent/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_RESULT.md",
                              "transforms_path": "docs/agent/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012/STAGE3_TRANSFORMS.json",
                              "transforms_sha256": "f7378b2a872b558c76bad2b1b7f4c201a3e30c38f4f63e25f73c76826129daca",
                              "result_sha256": git_blob_sha256(git_commit("0b50938e"), "docs/agent/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_RESULT.md"),
                              "spec_sha256": "cfee4477871f4c50600cc4dbc6a2fc32e675950507ff23d27ff233e0be8c96e1",
                              "classification": "GENUINELY_DISJOINT_NATURAL_CELL_SETS",
                              "claims_value_agreement": False},
            "spent_authority_sha256": [
                "3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a",
                "28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7",
                "19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee",
                "c1bac85b4da9f447590b9f7172fc69f612b878a7ad851fc29f4efd87f2f0eaf1",
                "be097fb21f58cbccea6b88cfad531eae4c8fbf3dc05582029f3d7dcc710bf1fa",
                "c171b91b853e9e136c28c3051cd3baae4e74a1be337f70b3d6ecdb175dd643ed",
                "b1bcc74f3e508fed72669aa323e9b9a8e7ccb4d72050e2dcd8fa9339e1bc1525"]},
        "prerequisite": {"amended_rule": "ACCEPTED_G6 + ACCEPTED_G7_EXECUTION_INTEGRITY + G7_NOT_ESTIMABLE_DUE_TO_INDEPENDENTLY_DIAGNOSED_STRUCTURAL_DISJOINTNESS",
                         "supersedes_requirement": "G7 exact PASS_TD_G7_S174_EXACT_OVERLAP",
                         "closure_reason": "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS",
                         "g7_pass": False, "claims_s174_sample_a_value_agreement": False},
        "science_references_sha256": refs,
        "archive": {"name": ARCHIVE_NAME, "sha256": ARCHIVE_SHA, "bytes": ARCHIVE_BYTES},
        "executors": {
            "TD56": {"kind": "td56", "by_source": {"HVS": exe["run_td56_hvs.py"], "NPH52": exe["run_td56_nph.py"],
                                                   "SEA_AD": exe["run_td56_sea_fast.py"]},
                     "variants_not_bound": ["run_td56_sea.py", "*_numericpair.py", "*_secondblock.py"]},
            "TD57B": {"kind": "module", **exe["td57b_fixed_relational_recurrence.py"],
                      "fast_wrapper_bound": False, "fast_wrapper_sha256_not_bound": exe["td57b_fast_wrapper.py"]["sha256"]},
            "TD57C": {"kind": "module", **exe["td57c_three_view_local_geometry.py"]},
            "TD59": {"kind": "module", "repo_path": TD59_PATH, "sha256": sha(ROOT / TD59_PATH),
                     "role": "ADMITTED_REPLAY_CLOSURE_SUCCESSOR",
                     "unrecovered_original_sha256": "3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0"}},
        "historical_equivalence_references": hist,
        "stages": [
            {"stage": "TD56", "invocation_order": [[None, s] for s in SOURCE_ORDER], "sequential_stop": "first source failure",
             "pass_rule": "PASS_SOURCE iff observed > null_p95 and observed > 0; stage PASS iff all three sources pass",
             "terminal_pass": "TD56S_DISJOINT_GENE_RELATIONAL_GEOMETRY_SURVIVES__FREEZE_DONOR_BLOCK_AND_CROSS_SOURCE_SCALE_GATE_NEXT",
             "terminal_fail": "NO_DISJOINT_GENE_RELATIONAL_PREDICTABILITY__TD56S_FAIL"},
            {"stage": "TD57B", "invocation_order": PANEL_ORDER, "sequential_stop": "first source-panel failure; Panel 1 opens only if Panel 0 passes all three sources",
             "pass_rule": "executor status PASS for all 6 source-panels (24/24 cases)",
             "terminal_pass": "TD57B_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER_SURVIVES__FREEZE_LOCAL_NEIGHBORHOOD_STABILITY_GATE_NEXT",
             "terminal_fail": "NO_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER__TD57B_FAIL"},
            {"stage": "TD57C", "invocation_order": PANEL_ORDER, "sequential_stop": "first failure",
             "pass_rule": "executor status PASS for all 6 source-panels",
             "terminal_pass": "TD57C_THREE_VIEW_FINE_LOCAL_RELATIONAL_GEOMETRY_SURVIVES__FIXED_CONCORDANCE_LOCAL_MINING_ADMISSIBLE_FOR_RELATIONAL_OBJECTIVE_QUALIFICATION",
             "terminal_fail": "NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL"},
            {"stage": "TD59", "invocation_order": PANEL_ORDER, "sequential_stop": "first source-panel failure",
             "pass_rule": "executor status PASS for all 6 source-panels (24/24 cases)",
             "terminal_pass": "TD59_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PILOT_FRONTIER_BRACKETED_BETWEEN_ONE_THIRD_AND_ONE_HALF__NO_TRAINING_AUTHORITY",
             "terminal_fail": "NO_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE__TD59_FAIL__STOP_LOCALITY_FRACTION_TUNING_ON_50K"}],
        "stage_order": ["TD56", "TD57B", "TD57C", "TD59"],
        "cross_stage_rule": "Replay all four already-opened historical objects for audit even if an earlier corrected replay fails. Preserve each stage's internal historical sequential-stop rule. No stage outcome may redesign another replay.",
        "invocation_outcome_mapping": {
            "td56": "non-zero exit or no result file -> IMPLEMENTATION_FAILURE; NOT_ESTIMABLE if observed or null_p95 is not finite; PASS iff observed > null_p95 and observed > 0; else FAIL",
            "module": ("exit 0 -> PASS and exit 2 -> FAIL, each only when the executor's own written result has that status for this source and panel "
                       "(otherwise IMPLEMENTATION_FAILURE: Python also exits 2 on argument or missing-script errors); any other exit: an exception whose "
                       "final stderr line contains a frozen support pattern -> NOT_ESTIMABLE, else IMPLEMENTATION_FAILURE (preserved, never relabelled)"),
            "support_patterns": NOT_ESTIMABLE_PATTERNS,
            "stage_status": "PASS iff every invocation PASS; FAIL at the first FAIL; NOT_ESTIMABLE at the first NOT_ESTIMABLE; IMPLEMENTATION_FAILURE at the first implementation failure"},
        "historical_fixture_equivalence": {
            "receipt_path": "custody/target_discovery/corrected_replay_20261012/TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1.json",
            "required_cases": 16,
            "rule": "every case exactly equal; produced at the implementation commit with the exact adapter/bootstrap bytes in the pinned Linux environment"},
        "adapter": {"module": "scripts/v5/td_corrected_replay_adapter_v1.py", "bootstrap": "scripts/v5/td_corrected_replay_exec_bootstrap_v1.py",
                    "value_source": {"HVS": "G6 corrected", "SEA_AD": "G6 corrected", "NPH52": "G6 authenticated historical pass-through"},
                    "redirections": {"td56": "numpy load/savez paths under /mnt/data only",
                                     "module": ["ARRAY_ROOT", "SUPPORT_PATH", "META_PATHS", "ARRAY_SHA256", "META_SHA256", "SUPPORT_SHA256"]},
                    "historical_fixture_equivalence_required": True},
        "execution_environment": {"platform": "WSL2 Ubuntu (Linux)", "python": "3.13.5", "numpy": "2.3.5", "scipy": "1.17.0",
                                  "pandas": "2.2.3", "conda_env": "td-replay-hist",
                                  "lock": {"path": "target_discovery/iterations/corrected_replay_20261012/TD_REPLAY_ENV_WSL_PIP_FREEZE.txt",
                                           "sha256": sha(ROOT / "target_discovery/iterations/corrected_replay_20261012/TD_REPLAY_ENV_WSL_PIP_FREEZE.txt")},
                                  "rationale": "Historical executors were byte-exact on Linux with these versions. On Windows, null vectors differ by 1 ULP."},
        "namespace": {"root_windows": "D:/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1",
                      "root_wsl": "/mnt/d/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1",
                      "start_marker": "TD_CORRECTED_REPLAY_EXECUTION_START.json", "one_shot": True,
                      "attempt_ledger": "D:/jepa_td_corrected_replay_20261012/TD_CORRECTED_REPLAY_ATTEMPT_LEDGER_V1.json",
                      "one_shot_guards": ["attempt ledger (exclusive create, beside the namespace)", "namespace absent",
                                          "no earlier launch_EXECUTE_ONCE_*/record/RUN_RECORD.txt that recorded attempt_spent=yes",
                                          "the committed evidence record is the durable spend record"]},
        "decisions_requiring_owner_ratification": {
            "detected_field": {"question": "Which G6 metadata detected count feeds the executors' td50 'detected' (depth/detection null blocks)?",
                               "options": ["detected_corrected", "detected_historical"], "proposed": "detected_corrected",
                               "status": "PROPOSED_PENDING_OWNER_RATIFICATION"},
            "routing_input_rule": {"question": "How are stage outcomes mapped to routing V2 inputs, including universal_source?",
                                   "proposed": {
                                       "stage_inputs": "the frozen stage status (PASS/FAIL/NOT_ESTIMABLE); an IMPLEMENTATION_FAILURE yields no routing input",
                                       "universal_qualification": ("per stage, descriptive: ESTABLISHED only when every planned source/panel execution was observed and "
                                                                   "passed its frozen per-source gate (stage PASS); NOT_ESTABLISHED when an observed execution failed "
                                                                   "its frozen gate (stage FAIL); otherwise the stage status. Each record lists the observed per-source "
                                                                   "outcomes, the source/panels the frozen sequential stop left unobserved, and any same-panel PASS/FAIL "
                                                                   "threshold discordance"),
                                       "source_order_censoring": ("source/panels not run because of the frozen sequential stop are missing evidence, recorded as "
                                                                  "UNOBSERVED; they are never counted as agreement or as disagreement"),
                                       "threshold_discordance": ("a PASS and a FAIL on the same stage and panel is recorded descriptively as failure to establish "
                                                                 "universality; it is not a between-source test and is never labelled source heterogeneity"),
                                       "source_heterogeneity": ("UNRESOLVED__NO_PROSPECTIVELY_FROZEN_DIRECT_BETWEEN_SOURCE_TEST for every stage; Pattern G "
                                                                "(source-specific disagreement) is never assigned in this replay"),
                                       "routing_v2_universal_source_input": ("FAIL is reserved for formally established source heterogeneity and is never produced; "
                                                                             "NOT_ESTIMABLE if any stage is NOT_ESTIMABLE; otherwise PASS. Routing V2 rules 1 "
                                                                             "(universal FAIL) and 9 (universal NOT_ESTIMABLE) therefore never change a route: the route "
                                                                             "is exactly the frozen TD56 -> TD57B -> TD57C -> TD59 stage hierarchy, a function of the four "
                                                                             "stage statuses only"),
                                       "no_source_averaging": ("no pooled or cross-source averaged statistic exists or is computed; a stage PASS needs every planned "
                                                               "source/panel PASS, so no source can rescue another source's frozen-gate failure"),
                                       "examples": [
                                           ("TD57C P0 HVS PASS, NPH52 FAIL, with TD56/TD57B/TD59 PASS -> TD57C FAIL; route BROAD_MESO (Pattern A) exactly as for "
                                            "TD57C P0 HVS FAIL; TD57C universal qualification NOT_ESTABLISHED with threshold discordance on P0 and the "
                                            "universality qualifier; source heterogeneity UNRESOLVED"),
                                           ("TD56 NOT_ESTIMABLE with TD59 P0 HVS PASS, NPH52 FAIL -> NOT_ESTIMABLE__TD56: a later straddle never strengthens "
                                            "an upstream NOT_ESTIMABLE"),
                                           ("TD57C P0 HVS FAIL (nothing after it runs) -> NPH52/SEA_AD P0 and all of P1 UNOBSERVED; no agreement is recorded"),
                                           "TD56 HVS PASS, NPH52 PASS, SEA_AD FAIL -> TD56 FAIL (frozen stage rule); discordance recorded; route TD56 FAIL",
                                           "TD59 P0 HVS PASS, NPH52 NOT_ESTIMABLE -> TD59 NOT_ESTIMABLE; no discordance"],
                                       "residual_source_order_dependence": ("the frozen stage rule takes the first non-PASS invocation, so when one source would FAIL "
                                                                            "and another would be NOT_ESTIMABLE, the stage status (FAIL vs NOT_ESTIMABLE) depends "
                                                                            "on which runs first; this is replay fidelity and is not changed")},
                                   "status": "PROPOSED_PENDING_OWNER_RATIFICATION",
                                   "amended_after": ("external audit of PR #307 (2026-10-12): "
                                                     "NOT_ACCEPTED_FOR_EXECUTE_ONCE__SOURCE_QUALIFICATION_AND_SOURCE_HETEROGENEITY_MUST_BE_SEPARATED__ONE_SHOT_ATTEMPT_UNSPENT; "
                                                     "superseded f5673f9b rule: a same-panel PASS/FAIL anywhere set universal_source FAIL")}},
        "interpretation_policy": {
            "routing_module": "scripts/v5/td_corrected_replay_routing_v2.py",
            "frozen_table": [
                "TD56 FAIL -> stop relational promotion",
                "TD56 PASS + TD57B FAIL -> CORRECTED_DISJOINT_GEOMETRY_PRESENT__DONOR_RECURRENT_SCALE_FREE_ORDER_NOT_CONFIRMED",
                "TD56 PASS + TD57B PASS + TD57C FAIL + TD59 PASS -> CORRECTED_RELATIONAL_PROGRAM_CONSISTENT_WITH_HISTORICAL_SCALE_BRACKET",
                "TD56 PASS + TD57B PASS + TD57C FAIL + TD59 FAIL -> CORRECTED_GLOBAL_SCALE_FREE_RELATION_SURVIVES__MESOSCALE_LOCALITY_NOT_CONFIRMED",
                "corrected TD57C PASS -> divergence; stop and require a new prospective locality experiment",
                "source disagreement -> no universal-source claim; do not average it away",
                "any NOT_ESTIMABLE -> remains not estimable, never a biological PASS"],
            "pattern_F": "no frozen 'materially narrow' number: any corrected TD59 PASS is flagged for auditor judgment and the HVS TD59 case margins are reported",
            "source_universality": ("the frozen 'source disagreement -> no universal-source claim' line is met descriptively: a stage with threshold "
                                    "discordance makes no universal claim for that stage (universal qualification NOT_ESTABLISHED, universality "
                                    "qualifier recorded); formal source heterogeneity stays unresolved and Pattern G is never assigned"),
            "historical_comparison_classes": ["QUALITATIVE_HISTORICAL_CONCLUSION_REPRODUCED",
                                              "QUALITATIVE_HISTORICAL_CONCLUSION_NOT_REPRODUCED", "NOT_ESTIMABLE",
                                              "NOT_COMPARABLE__IMPLEMENTATION_FAILURE"]},
        "estimability_policy": {"pre_marker_checks": [
            "G6 metadata Sample-A rows equal the frozen freeze rows in sample_row order",
            "per source, the G6 metadata (global_row, donor, operator) equal the historical td50 structural fields exactly, so every comparison population is the historical one",
            "per source, donor counts and donor x operator strata with >= 4 cells meet the executors' structural floors (TD56: >= 8 donors; TD57B: >= 4 per half; TD57C/TD59: >= 8 structurally eligible)",
            "the support calibration bundle (SHA 07748d5b) and the support member it yields (SHA 852cb3ec) are the frozen bytes (QUALIFY, and again in the orchestrator before the marker)",
            "the detected field is read from the parsed, ratified decision JSON before the marker"],
            "value_dependent_measurability": "checked only by the executors after the start marker"},
        "authority_policy": {"required": ["fresh replay-only owner decision", "fresh replay-only runtime authorization",
                                          "fresh replay-only operational authorization", "committed external launch-audit acceptance"],
                             "refuse_spent": True, "single_attempt": True},
        "forbidden_downstream": ["G6 rerun", "G7 rerun", "target tournament", "TD60", "Stage 4", "training",
                                 "threshold, panel, null, donor-split or locality change", "relabel NOT_ESTIMABLE as PASS"],
        "downstream_authority": flags,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    raw = (json.dumps(build(Path(a.archive)), indent=2, sort_keys=True) + "\n").encode("utf-8")
    if a.check:
        if not OUT.is_file() or OUT.read_bytes() != raw:
            print("STOP: committed contract is not regenerated byte for byte")
            return 1
        print("contract regenerated byte for byte:", hashlib.sha256(raw).hexdigest())
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(raw)
    print(hashlib.sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
