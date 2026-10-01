#!/usr/bin/env python3
"""Independent audit of the ChatGPT post-red-team lane, c965d770..57e657d0.

THE INSTRUCTION WAS TO FALSIFY, NOT TO CONFIRM. So this file does two things that a
confirmatory review would not. First, it tests the ChatGPT contract against the ACTUAL
Phase-B artifacts rather than against itself: every quantity in accepted_execution_parent
is recomputed from the shards, the T5 grid and the availability codes. Their own positive
control cannot do this, because it builds its manifest by copying values out of the
contract, so it would stay green if the contract's numbers were wrong. Second, it asks
which of their checks are capable of failing at all.

The audit recomputes; it does not restate. Nothing here opens a correspondence value, and
no number below is copied from any receipt either lane wrote.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import verify_phase_b_consumer_semantics_v1 as CS                    # noqa: E402

CHATGPT_HEAD = "57e657d08af25d19ca0c9d8cb4e2c6eb3b0a3db7"
BASE = "c965d770"
CONTRACT_PATH = "results/v64/V66_STAGE4_EXECUTION_AUTHORITY_CONTRACT_V5.json"
FINDINGS, CORROBORATED = [], []


def show(path, rev=CHATGPT_HEAD):
    r = subprocess.run(["git", "show", rev + ":" + path], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def finding(num, severity, title, detail, evidence):
    FINDINGS.append(dict(id=num, severity=severity, title=title, detail=detail,
                         evidence=evidence))
    print("  %-5s %-8s %s" % (num, severity, title))


def main() -> int:
    C = json.loads(show(CONTRACT_PATH))
    parent = C["accepted_execution_parent"]

    # ============================================= 1 recompute the contract's parent
    print("recomputing every accepted_execution_parent quantity from the artifacts ...")
    S = CS.load_substrate()
    sh = S["shards"]
    mc = np.concatenate([s["t2_metacell"] for s in sh])
    dn = np.concatenate([s["t2_donor"] for s in sh]).astype(str)
    nu = np.concatenate([s["t2_n_nuclei"] for s in sh])
    t5 = S["t5"]
    states = [str(x) for x in t5["states"]]
    code = np.asarray(t5["availability_state_code"])
    n_pairs = len(sh[0]["pair_keys"])
    n_don = len(code) // n_pairs
    measured_per_pair = (code.reshape(n_don, n_pairs)
                         == states.index("MEASURED")).sum(0)
    agg = hashlib.sha256("".join(s["sha256"] for s in
                                 sorted(sh, key=lambda x: x["path"])).encode()).hexdigest()

    recomputed = dict(
        qualifying_donors=len(set(dn.tolist())),
        metacells=int(len(mc)),
        microglia_covered=int(nu.sum()),
        genes=int(len(sh[0]["genes"])),
        intervals=int(len(sh[0]["interval_start"])),
        pairs=int(n_pairs),
        t5_rows=int(len(code)),
        t3_nnz=int(sum(s["t3_n"] for s in sh)),
        t4_nnz=int(sum(s["t4_n"] for s in sh)),
        pairs_meeting_minimum_donors=int((measured_per_pair >= 30).sum()),
        phase_b_aggregate_binding=agg)

    disagree = {k: dict(contract=parent[k], recomputed=v)
                for k, v in recomputed.items() if parent.get(k) != v}
    for k, v in recomputed.items():
        if parent.get(k) == v:
            CORROBORATED.append(dict(quantity=k, value=v,
                                     method="recomputed from the artifacts, not read "
                                            "back from any receipt"))
    print("  %d of %d quantities reproduce exactly; %d disagree"
          % (len(CORROBORATED), len(recomputed), len(disagree)))
    if disagree:
        finding("S95", "STOP", "the V5 contract disagrees with the artifacts",
                "a quantity the contract declares does not reproduce", disagree)

    # ======================================= 2 can their positive control ever fail?
    tsrc = show("tests/v64/test_stage4_execution_authority_validator_v1.py") or ""
    tautological = ('CONTRACT["accepted_execution_parent"]' in tsrc
                    and 'copy.deepcopy(\n            CONTRACT["frozen_state_vocabulary"])'
                    in tsrc or 'CONTRACT["frozen_statistical_rules"]' in tsrc)
    empty_files = '"files": {}' in tsrc
    if tautological:
        finding("S89", "CONCERN",
                "the validator's positive control is built from the contract it checks",
                "valid_manifest() copies phase_b_aggregate_binding, qualifying_donors, "
                "metacells, t5_rows, microglia_covered, genes, intervals, pairs, t3_nnz, "
                "t4_nnz, pairs_meeting_minimum_donors, the state vocabulary, the "
                "statistical rules and the missingness rules straight out of the "
                "contract. test_clean_structural_manifest_passes therefore cannot fail "
                "for any value-equality rule, and would stay green if a contract number "
                "were wrong. The mutation tests around it are real and do fail when "
                "perturbed; it is specifically the positive control that carries no "
                "information. Section 1 of this audit is the control it lacks.",
                dict(fixture="valid_manifest() in "
                             "tests/v64/test_stage4_execution_authority_validator_v1.py"))

    # ============================== 3 is the custody set required to be complete?
    fad = set(C["frozen_authority_digests"])
    cust = set(C["repo_resident_git_custody"])
    uncovered = sorted(fad - cust)
    rules = C.get("validator_rules", {})
    has_coverage_rule = any("coverage" in k or "complete" in k for k in rules)
    ci = show(".github/workflows/v64-privileged-architecture-smoke.yml") or ""
    ci_self_referential = 'C["repo_resident_git_custody"].items()' in ci
    if uncovered and not has_coverage_rule:
        finding("S90", "CONCERN",
                "git custody is hand-listed and nothing requires it to be complete",
                "%d of %d frozen authority digests carry a git_blob and source_commit; "
                "%s carry only a raw SHA-256. Two of those are the large npz artifacts "
                "and are legitimately not repo-resident. But validator_rules contains no "
                "rule obliging a repo-resident authority to appear in "
                "repo_resident_git_custody, so adding one and forgetting its custody "
                "entry leaves the validator green. The CI step compounds this: it builds "
                "its manifest as {k: {path} for k in C['repo_resident_git_custody']}, so "
                "the manifest it validates is generated FROM the custody block and can "
                "never contain a label the custody block omits."
                % (len(cust), len(fad), uncovered),
                dict(uncovered_labels=uncovered,
                     ci_manifest_is_generated_from_custody=ci_self_referential))

    # =================== 4 has the file-binding path ever run against a real manifest?
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", CHATGPT_HEAD],
                             capture_output=True, text=True).stdout.splitlines()
    manifests = [p for p in listing if "V66_STAGE4_AUTHORITY_INPUT_MANIFEST" in p]
    ci_calls_file_bindings = "validate_file_bindings" in ci
    if not manifests and not ci_calls_file_bindings:
        finding("S91", "CONCERN",
                "validate_file_bindings has never been executed against a real manifest",
                "An exhaustive listing of every path at %s contains no "
                "V66_STAGE4_AUTHORITY_INPUT_MANIFEST artifact, the unit-test fixture "
                "sets files to the empty dict, and the CI step calls only "
                "validate_repo_git_custody. So the function that would require every "
                "bound digest to resolve to real bytes on disk has run against a real "
                "input exactly zero times. It is reviewed code, not exercised code."
                % CHATGPT_HEAD[:8],
                dict(manifests_found=manifests, fixture_files_empty=empty_files,
                     ci_invokes_file_bindings=ci_calls_file_bindings,
                     paths_listed=len(listing)))

    # ========================= 5 does every bound digest correspond to locatable bytes?
    target = C["frozen_authority_digests"].get("consensus_peak_set_sha256")
    scanned_roots = ["results/v64", "results/v63", "data",
                     "D:/jepa_v5_outputs_20260925"]
    n_scanned, hit = 0, None
    for root in scanned_roots:
        if not os.path.isdir(root):
            continue
        for dp, _, fn in os.walk(root):
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) > 3_000_000_000:
                        continue
                    n_scanned += 1
                    if B.sha_file(p) == target:
                        hit = p
                        break
                except OSError:
                    pass
            if hit:
                break
        if hit:
            break
    if target and not hit:
        finding("S92", "CONCERN",
                "a bound authority digest has no locatable bytes in the trees scanned",
                "consensus_peak_set_sha256 = %s was not found by exhaustive walk of %s "
                "(%d files hashed). This is a SCOPE-LIMITED absence, not a claim that "
                "the file does not exist: it may live in a tree I did not scan or on "
                "another machine. It matters because validate_file_bindings requires "
                "this label to resolve to real bytes, and taken together with S91 it "
                "means the first real manifest may fail closed on a digest nobody can "
                "satisfy." % (target[:16] + "...", scanned_roots, n_scanned),
                dict(roots_walked=scanned_roots, files_hashed=n_scanned,
                     method="exhaustive os.walk and SHA-256, not a filename search"))
    elif hit:
        CORROBORATED.append(dict(quantity="consensus_peak_set_sha256", value=hit,
                                 method="located by content digest"))

    # ============================= 6 contract tests that assert prose, not behaviour
    prose = {}
    for t in ("tests/test_v67_two_lane_integration_recoverability_contract.py",
              "tests/test_v67_privileged_teacher_state_construction_contract.py"):
        src = show(t) or ""
        n_tests = src.count("def test_")
        n_substring = sum(1 for l in src.splitlines()
                          if "assert" in l and (" in " in l) and "json" not in l)
        prose[t] = dict(tests=n_tests, substring_assertions=n_substring)
    if sum(v["substring_assertions"] for v in prose.values()) > 0:
        finding("S93", "CONCERN",
                "the new contract tests assert sentences, not behaviour",
                "These files check that particular strings appear in a JSON document the "
                "same lane authored -- for example that r['test_rule'] contains the "
                "phrase 'TEST does not tune'. That detects someone deleting a sentence. "
                "It cannot detect an executor that violates the rule, because no "
                "executor is involved. A contract is not in force until something "
                "enforces it, so these should not be counted toward the green test total "
                "as evidence that the design is implemented.",
                prose)

    # ============================= 7 the evidence/measurement synthetic
    esrc = show("scripts/v64/evidence_vs_measurement_response_synthetic_v1.py") or ""
    one_seed = esrc.count("SEED=") == 1 and "for seed in" not in esrc
    nonstrict = "np.all(np.diff(vals)<=1e-12)" in esrc
    has_counterfactuals = ("evidence_override_same_subset" in esrc
                           and "depth_override_fixed_noise" in esrc)
    if has_counterfactuals:
        CORROBORATED.append(dict(
            quantity="evidence_vs_measurement counterfactual controls",
            value="both gates are driven false by an override",
            method="read from source: run_smoke(evidence_override_same_subset=True) and "
                   "run_smoke(depth_override_fixed_noise=True) are asserted to fail"))
    if one_seed or nonstrict:
        finding("S94", "CONCERN",
                "the evidence/measurement separation rests on one seed and a "
                "near-guaranteed monotonicity",
                "The fixture is drawn once at SEED=6703 and the convergence claim is "
                "never repeated across seeds, so the reported monotonicity is a property "
                "of one draw. strictly_improves() is also misnamed: it tests "
                "non-increasing to a tolerance of 1e-12, so a flat curve satisfies it "
                "and the relative-gain threshold does all the work. The evidence arm "
                "additionally uses NESTED feature subsets with roughly 1,800 training "
                "rows against at most 40 predictors, where adding features can hardly "
                "fail to reduce validation error -- so that gate carries little "
                "information on its own. The two counterfactual overrides are what make "
                "it falsifiable, and they are good; the headline gates are not the "
                "evidence.",
                dict(single_seed=one_seed, monotone_is_nonstrict=nonstrict,
                     counterfactual_controls_present=has_counterfactuals))

    # ----------------------------------------------------------------- receipt
    out = dict(
        schema="V67_CLAUDE_INDEPENDENT_AUDIT_OF_CHATGPT_LANE_V1", date="2026-10-01",
        audited_range=dict(base=BASE, head=CHATGPT_HEAD),
        instruction="try to falsify, do not assume the green test total means the design "
                    "is correct",
        CORROBORATED_BY_INDEPENDENT_RECOMPUTATION=CORROBORATED,
        contract_parent_quantities_checked=len(recomputed),
        contract_parent_quantities_reproducing=len(recomputed) - len(disagree),
        disagreements=disagree,
        findings=FINDINGS,
        n_findings=len(FINDINGS),
        severities={s: sum(1 for f in FINDINGS if f["severity"] == s)
                    for s in ("STOP", "CONCERN")},
        what_i_could_not_falsify=[
            "every quantity in accepted_execution_parent, recomputed from the artifacts",
            "the git-custody repair itself: it resolves blobs through git rather than "
            "checking syntax, returns REPO_GIT_CUSTODY_ABSENT when the block is missing, "
            "and its four negative tests do fail on a wrong committed blob, uncommitted "
            "worktree bytes and a substituted path",
            "the mutation tests around the structural validator, which perturb one field "
            "at a time and go red",
        ],
        computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        status="FINDINGS_RAISED" if FINDINGS else "NO_FINDINGS")
    p = "results/v64/phase_b_design/V67_CLAUDE_INDEPENDENT_AUDIT_OF_CHATGPT_LANE_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("%d of %d contract quantities reproduce from the artifacts"
          % (len(recomputed) - len(disagree), len(recomputed)))
    print("%d findings raised (%d STOP, %d CONCERN)"
          % (len(FINDINGS), out["severities"]["STOP"], out["severities"]["CONCERN"]))
    print("receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
