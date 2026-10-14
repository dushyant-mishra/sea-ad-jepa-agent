"""Receipt index for the Macha TD real-data qualification / hostile external review.

Binds every artifact of the review by SHA-256 and records, for each
qualification task, the fifteen fields required by the review brief.  Audit
judgments are frozen constants in this file; every number is either read from
a hash-bound artifact or is a cited executor constant.  No real expression
value, candidate output, pathology or DEV/SEALED object is read here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
NO_OUTCOMES = "NO current human candidate outcome, candidate representation, pathology field, reader_validation/reader_oracle RNA or DEV/SEALED object was inspected"
HEADS = {
    "343": {"head": "82d17bfb1650d97a95d5424160126791f09d7494", "movement": "AT_EXPECTED"},
    "345": {"head": "f16ba70f", "movement": "AT_LIVE_HEAD"},
    "349": {"head": "1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7", "movement": "AT_EXPECTED"},
    "350": {"head": "9b9078c102fa346644d6eb2bda4ff7b4bdfe854a", "movement": "AT_EXPECTED"},
    "351": {"head": "2abcb9fe", "expected": "b9774be4d9a79f3c64ed999c040f8982150d72d4",
            "movement": "BRANCH_MOVED__TEST_ONLY__NOT_SCIENTIFIC_EXECUTABLE_CHANGED"},
    "352": {"head": "bb1e35d33deb52236829012be452e4c4d8b362fc", "movement": "AT_EXPECTED"},
    "353": {"head": "1df20029defaa2bcd7a51869c1026ac6075b1323", "movement": "AT_LIVE_HEAD"},
    "354": {"head": "d90047308d633e259195a54501a230373b36d043", "movement": "AT_EXPECTED"},
    "355": {"head": "6e5182e2dc4e8e263e8cbd309aed6494b5ea7a55", "movement": "AT_EXPECTED"},
    "357": {"head": "c174d052", "movement": "AT_LIVE_HEAD__NOT_IN_BRIEF"},
}
NAMESPACES_NONE = {"calibration": None, "refit": None, "deciding": None, "null": None,
                   "note": "no RNG draw was made by this review; no namespace consumed"}

TASKS = {
    "population_support_audit": {
        "question": "What donor/source/operator/address/partition support does the frozen real population provide, and what donor resolution does each stratum have?",
        "code": ["scripts/v5/audit_td_real_population_support_v1.py"],
        "artifacts": ["POPULATION_SUPPORT_AUDIT_RECEIPT_V1.json", "population/DONOR.csv", "population/DONOR_X_OPERATOR.csv",
                      "population/OPERATOR.csv", "population/SOURCE_X_PARTITION.csv",
                      "population/BROAD_CLASS_X_PARTITION_X_SOURCE.csv", "population/NATIVE_CLASS_X_PARTITION_X_SOURCE.csv",
                      "support/OPERATOR_ADDRESS_STATE_COUNTS.csv"],
        "population": "149 donors (104 reader_fit / 22 reader_validation / 23 reader_oracle), 6,351,753 cells, 42 operators, 3 sources, 2,028 donor x operator strata",
        "support_denominators": "cells per donor/donor x operator/class stratum; addresses per operator by observation state (41,238)",
        "estimability": "REAL_SUPPORT_ESTIMABLE as a mapping; NPH52 held-out = 0 validation / 2 oracle donors -> NOT_ESTIMABLE_IN_THIS_REAL_STRATUM for every held-out donor-primary test; SEA_AD subclass held-out strata 4-5 donors -> NOT_ESTIMABLE_IN_THIS_REAL_STRATUM",
        "metric": "counts only; exact one-sided donor sign test resolution 0.5**n <= 0.01/m",
        "resolution": "n_min = 7 (m=1), 8 (m=2), 9 (m=3..5), 10 (m=6..10), 11 (m=12..20)",
        "tests": "identity closure vs frozen split and #349 counts: all PASS",
        "hostile": "donor crossing sources 0; donor crossing partitions 0; operators spanning partitions 42/42; operators with one donor 0",
        "verdict": "REAL_SUPPORT_ESTIMABLE__REFERENCE_ARTIFACT_QUALIFIED_SUPPORT_RESOLUTION_CLASS",
    },
    "rawcount_depth_support_census": {
        "question": "Do authenticated nonnegative integer raw counts exist for the calibration population, and how does p-thinning change detection without changing structural support?",
        "code": ["scripts/v5/audit_td_real_rawcount_depth_support_v1.py"],
        "artifacts": ["RAWCOUNT_DEPTH_SUPPORT_CENSUS_RECEIPT_V1.json", "support/RAWCOUNT_DONOR_X_OPERATOR_DEPTH_SUPPORT.csv"],
        "population": "reader_fit only: 104 donors, 4,553,407 cells, 1,400 donor x operator strata (Level-4 store certifies no validation/oracle/DEV/SEALED/pathology)",
        "support_denominators": "per donor x operator: cells, stored nnz, stored count sum, full-source library",
        "estimability": "raw counts REAL_SUPPORT_ESTIMABLE for reader_fit; NOT_MATERIALIZED for reader_validation/reader_oracle",
        "metric": "exact binomial-thinning expectations (no draws)",
        "resolution": "n/a",
        "tests": "8,915/8,915 blocks hash-verified; 4,553,407 unique selection rows; 0 negative; 0 explicit zeros; 0 entries outside MEASURED_SCALAR; 512 NPH52 rows with integer-valued float-formatted library",
        "hostile": "library < stored sum: 0 cells; stored/library = 1.0 for HVS, 0.960-0.999 for NPH52, 0.75-1.0 for SEA_AD -> exact thinning must also thin unmaterialized off-address library mass",
        "verdict": "REFERENCE_ARTIFACT_QUALIFIED_SUPPORT_RESOLUTION_CLASS",
    },
    "g8_human_technical_calibration": {
        "question": "Can the human dataset supply 599 exchangeable calibration observations per required G8 reference unit under the exact observation operator without pseudo-replication?",
        "code": ["scripts/v5/build_td_real_g8_calibration_feasibility_v1.py"],
        "artifacts": ["g8/G8_HUMAN_TECHNICAL_CALIBRATION_FEASIBILITY_RECEIPT_V1.json", "g8/G8_DONOR_DEPTH_ENDPOINT_FEASIBILITY_V1.csv",
                      "hostile_probes/g6_g8/g8_probe.py", "hostile_probes/g6_g8/g8_probe.log"],
        "population": "894 donor x depth x endpoint units (624 reader_fit, 270 held-out)",
        "support_denominators": "OPEN: support-fraction denominator not frozen (owned by the deciding lane)",
        "estimability": "CONTRACT_GAP for every reader_fit unit; held-out units BLOCKED (raw counts not materialized, RNA access not authorized); 599 unattainable under any donor-as-realization granularity (104 fit / 149 cohort donors)",
        "metric": "OPEN: candidate-specific displacement interface not frozen; no envelope emitted",
        "resolution": "required 599 per unit (#343 alpha_eff=0.01/6); available per granularity recorded without choosing",
        "tests": "#343 own tests 11/11 local; bound ranks exact vs rational arithmetic over 300+ (alpha,n) pairs",
        "hostile": "thinning RNG keyed to storage order not cell identity; no observation-state channel (masked unmeasured entry thinned as measured); no thinned library; namespace validator never called and lacks refit slot; -1e-12 epsilon rounds anti-conservatively",
        "verdict": "CONFORMAL_BOUND_ARITHMETIC_QUALIFIED__THINNING_MECHANICS_REPAIR_REQUIRED__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN__HUMAN_G8_NOT_EXECUTABLE",
    },
    "g6_feasibility": {
        "question": "Are the G6 teacher-target / student-evidence / teacher-evidence objects constructible on real support, and can the decision layer lawfully emit human PASS/FAIL?",
        "code": [],
        "artifacts": ["hostile_probes/g6_g8/g6_probe.py", "hostile_probes/g6_g8/g6_probe2.py", "hostile_probes/g6_g8/g6_probe_345only.log",
                      "hostile_probes/g6_g8/g6_probe_full.log", "hostile_probes/g6_g8/g6_probe2.log"],
        "population": "LODO over 104 reader_fit donors (HVS 41, NPH52 17, SEA_AD 46) would resolve; held-out NPH52 does not",
        "support_denominators": "per candidate: C1/C2/C3/C6/C4 BLOCKED_EVIDENCE_CONTRACT on all 2,028 strata (#349); C5 G6 not required",
        "estimability": "C1,C2,C3,C6,C4: BLOCKED_ON_CONTRACT; C5: NOT_APPLICABLE; ridge U_refit = 0 by construction -> NOT_ESTIMABLE_BY_CONSTRUCTION as a substantive margin",
        "metric": "donor-balanced MSE in raw target units (units undeclared in SA3; verdict changes under rescaling)",
        "resolution": "sign test n_min 7 per source stratum at m=1",
        "tests": "#345 10/10, #352 23/23 local; SA3 grid, tie rule, train-only standardization hold",
        "hostile": "zero margin accepted -> direction-only PASS; qualification checked by literal schema strings; decision layer self-qualifies with a literal; 1-D noise-free qualification world; planted-positive worlds FAIL 24/24 at b=0.2; human FAIL emitted from typed tokens; alpha free argument",
        "verdict": "STOP__NOT_MECHANICALLY_QUALIFIED_FOR_HUMAN_DECISION__CONTRACT_REPAIR_REQUIRED",
    },
    "geometry_feasibility_g9_s1_s2": {
        "question": "Can disjoint donor-balanced refits, held-out donor geometry, adverse-null resolution and same-metric references be produced on real support, and does #355 enforce its guarantees?",
        "code": [],
        "artifacts": ["hostile_probes/geometry/probe_geometry_engine.py", "hostile_probes/geometry/probe_results.jsonl",
                      "hostile_probes/geometry/probe_followup.py", "hostile_probes/geometry/probe_followup_results.json",
                      "hostile_probes/geometry/RESULTS_LOG.txt"],
        "population": "fit views per source HVS 20/21, NPH52 8/9, SEA_AD 23/23; held-out HVS 10/11, NPH52 0/2, SEA_AD 12/10 (validation/oracle)",
        "support_denominators": "estimable donor roster per source stratum (caller-labelled in #355)",
        "estimability": "NOT_ESTIMABLE_BY_CONSTRUCTION today (no frozen alignment metric, null producer, U_refit/U_measurement or subspace estimator); NPH52 held-out NOT_ESTIMABLE_IN_THIS_REAL_STRATUM",
        "metric": "aligned RMS / projector displacement, smaller-is-better; adverse lower bound q_alpha",
        "resolution": "#355 requires ceil(1/alpha)=100 null draws per donor; counts draws not distinct permutations",
        "tests": "#355 18/18 local",
        "hostile": "rotation/permutation/sign-flip invariance holds; leakage guard only checks caller ID lists; non-orthogonal map accepted; identical fake receipt hashes PASS; one null-short donor converts estimable stability FAIL into NOT_ESTIMABLE (:331-338); non-required source rows silently dropped (:313); abstention relabel turns FAIL into PASS; 3-cell donors become biological FAIL; no eigengap guard",
        "verdict": "STOP__NOT_MECHANICALLY_QUALIFIED__IMPLEMENTATION_REPAIR_REQUIRED",
    },
    "r1_feasibility": {
        "question": "Can lawful disjoint molecular views and anchored cell triplets with adequate null resolution be produced per required source/scale stratum, and does the null separate technical state from biology?",
        "code": [],
        "artifacts": ["hostile_probes/r1_g2/r1_probe.py", "hostile_probes/r1_g2/r1_probe.log",
                      "hostile_probes/r1_g2/r1_probe_depthnull.py", "hostile_probes/r1_g2/r1_probe_depthnull.log"],
        "population": "triplets not limiting at donor level (>=81 cells per fit donor); limiting in rare class strata; held-out NPH52 0/2 donors",
        "support_denominators": "address-disjoint views on the same cells; strict core 17,186 addresses measured by all 42 operators; HVS 18,736 / NPH52 35,098 / SEA_AD 35,076 addresses measured",
        "estimability": "NOT_EXECUTABLE: static manifest only; no distance/triplet/null/U_refit/decision executor",
        "metric": "Spearman/Fisher-z relational recurrence (design); tie tolerance effectively 0 with no provenance",
        "resolution": "B >= ceil(1/alpha)-1 null draws per donor required by design",
        "tests": "#350 10/10 (23/23 incl. V1), #353 8/8 local",
        "hostile": "relation-label null not depth/detection matched: library-only technical world beats it 8/8 donors; depth-block null closes it (0/8 technical, 7/8 biology); #353 has no adversarial worlds; caller-set eligibility turns 0.5 into 1.0; both-tie counts as agreement; dropped donors unreported; sources pooled",
        "verdict": "STOP__NOT_EXECUTABLE__CONTRACT_REPAIR_REQUIRED_NULL_DESIGN",
    },
    "g2_audit": {
        "question": "Can G2 be constructed on real data with frozen baselines, common orientation, same held-out cases and an identity-bound noise margin, without shortcut leakage?",
        "code": [],
        "artifacts": ["hostile_probes/r1_g2/g2_probe.py", "hostile_probes/r1_g2/g2_probe.log"],
        "population": "per candidate x endpoint x source x held-out donor (not frozen)",
        "support_denominators": "caller-labelled support in #357",
        "estimability": "baseline inputs (operator, support fingerprint, library) REAL_SUPPORT_ESTIMABLE from metadata/raw counts; candidate scores and margins BLOCKED_ON_CONTRACT",
        "metric": "generic METRIC literal not bound to candidate/endpoint",
        "resolution": "two-sided donor sign test (law says one-sided; conservative)",
        "tests": "#357 9/9 local",
        "hostile": "baseline family, required strata, alpha, qualification caller-supplied; zero margin accepted; support relabel turns FAIL into PASS; 'not demonstrated' (9/10 donors positive, p=0.021) emitted as FAIL; ties dropped -> equal-to-baseline gives NOT_ESTIMABLE; unsupported rows need finite numbers; NaN raises instead of NUMERICAL_FAILURE",
        "verdict": "CONCERN__DECISION_ARITHMETIC_MECHANICALLY_QUALIFIED__BINDING_AND_STATUS_SEMANTICS_REPAIR_REQUIRED",
    },
    "reusable_reference_artifacts": {
        "question": "Which candidate-neutral reference artifacts can lawfully be generated now?",
        "code": [],
        "artifacts": [],
        "population": "reader_fit raw counts; whole-cohort metadata",
        "support_denominators": "see population and census receipts",
        "estimability": "support-resolution receipts QUALIFIED; U_measurement NOT GENERATED (CONTRACT_GAP); U_refit NOT GENERATED (no frozen estimator; ridge degenerate); adverse-null calibration NOT GENERATED (no null producer; R1 null design fails technical negative)",
        "metric": "no universal noise threshold created",
        "resolution": "n/a",
        "tests": "byte-identical replay of all support-resolution artifacts",
        "hostile": "a reference reused across candidates or under a same-name metric would be unbound; none emitted",
        "verdict": "REFERENCE_ARTIFACT_QUALIFIED_SUPPORT_RESOLUTION_ONLY__U_MEASUREMENT_U_REFIT_ADVERSE_NULL_NOT_GENERATED",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--audit-dir", required=True)
    ap.add_argument("--replay-log", required=True)
    args = ap.parse_args()
    repo, d = Path(args.repo), Path(args.audit_dir)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    replay = [line for line in Path(args.replay_log).read_text(encoding="utf-8").splitlines()
              if line.startswith(("IDENTICAL", "DIFFERENT", "replay head", "exit"))]
    import numpy, scipy  # noqa: E401
    env = {"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
           "platform": platform.platform(), "execution": "LOCAL_EXECUTION_EVIDENCE__NOT_CI"}
    records = {}
    for name, t in TASKS.items():
        records[name] = {
            "1_scientific_question": t["question"],
            "2_code_head": {"built_from_commit": head,
                            "code_sha256": {c: sha256(repo / c) for c in t["code"]},
                            "executors_audited": HEADS},
            "3_input_and_artifact_sha256": {a: sha256(d / a) for a in t["artifacts"]},
            "4_population_split_identity": t["population"],
            "5_support_denominators": t["support_denominators"],
            "6_estimability_classification": t["estimability"],
            "7_namespace_identities": NAMESPACES_NONE,
            "8_metric_orientation": t["metric"],
            "9_required_vs_achieved_resolution": t["resolution"],
            "10_test_results": t["tests"],
            "11_hostile_test_results": t["hostile"],
            "12_receipt_sha256": "index-level: see index_sha256 sidecar",
            "13_environment": env,
            "14_candidate_outcomes_inspected": False,
            "14_statement": NO_OUTCOMES,
            "15_authority": AUTHORITY,
            "verdict": t["verdict"],
        }
    index = {
        "schema": "JEPA_TD_REAL_QUALIFICATION_RECEIPT_INDEX_V1",
        "review": "MACHA_HOSTILE_EXTERNAL_REVIEW_AND_REAL_DATA_QUALIFICATION_20261014",
        "final_verdict": ("EXTERNAL_REVIEW_COMPLETE__REAL_SUPPORT_MAPPED_AND_AUTHENTICATED__NO_HUMAN_TD_GATE_EXECUTABLE__"
                          "CONTRACT_AND_IMPLEMENTATION_REPAIR_REQUIRED__NO_CANDIDATE_OUTCOMES_OPENED"),
        "replay": replay,
        "tasks": records,
        "authority": AUTHORITY,
    }
    out = d / "QUALIFICATION_RECEIPT_INDEX_V1.json"
    out.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (d / "QUALIFICATION_RECEIPT_INDEX_V1.json.sha256").write_text(sha256(out) + "  QUALIFICATION_RECEIPT_INDEX_V1.json\n",
                                                                   encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
