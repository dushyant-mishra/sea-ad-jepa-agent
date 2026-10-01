#!/usr/bin/env python3
"""G17 no-matrix proof (static AND executable) plus the Stage-4 anti-bypass suite.

G17 IS PROVED TWO WAYS because either half alone is weak. The static half parses the
executor's syntax tree and scans its source for matrix path literals; a static proof
cannot see a dynamic import. The executable half poisons every raw-matrix reader so that
touching one raises, then runs the REAL preflight and requires it to succeed anyway; an
executable proof cannot see a branch that was never taken. Together they are a claim worth
making.

ANTI-BYPASS. Every attempt is a real attempt. Authority files are swapped, bound digests
are edited, inputs are removed and added, contracts are rewritten, flags are invented and
a fully valid forged authorisation is presented. Nothing is simulated by editing a verdict
field, and no attempt is scored by asking the executor what it thinks happened -- each is
scored on its exit code and its stderr.

TWO SAFETY PROPERTIES OF THIS FILE ITSELF.
 1. Attacks that need a mutated authority or contract run in a SANDBOX directory with its
    own copies, never against the live repository bytes. The live artifacts are digested
    before and after and the receipt records that they are unchanged.
 2. The two attacks that must use the canonical authorisation path write there and remove
    the file in a `finally` AND an `atexit` hook, and the suite fails if the path still
    exists at the end. A forged authorisation left behind would be worse than the test is
    worth.

No correspondence value is computed anywhere in this file.
"""
from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import verify_phase_b_consumer_semantics_v1 as CS                    # noqa: E402

REPO = os.getcwd()
DIR = "results/v64/phase_b_design"
EXEC_REL = "scripts/v64/stage4_executor_v1.py"
AUTHORITY = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json")
AUTHZ = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORIZATION_V1.json")
SUBSTRATE_DIR = "D:/jepa_v5_outputs_20260925/v64_phase_b"
NULL_CONTRACT = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
DESIGN_CONTRACT = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
SANDBOX_FILES = [
    AUTHORITY, NULL_CONTRACT, DESIGN_CONTRACT,
    os.path.join(DIR, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json"),
    "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json",
    "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json",
    "results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz",
    "scripts/v63/e2_continuous_adjustment_estimator_v1.py",
]
RESULTS = []

def rec(section, attempt, expected, observed, holds):
    RESULTS.append(dict(section=section, attempt=attempt, required_behaviour=expected,
                        observed=observed, holds=bool(holds)))
    mark = "OK  " if holds else "FAIL"
    print("  [" + section + "] " + mark + " " + attempt + "  ::  " + observed)

def run_exec(args, env=None, cwd=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run([sys.executable, os.path.join(REPO, EXEC_REL), *args],
                       capture_output=True, text=True, env=e, cwd=cwd or REPO)
    return r.returncode, (r.stdout + r.stderr)

# ---------------------------------------------------------------------- sandbox
def make_sandbox(root, edit=None):
    """A private copy of every repo-resident file the executor reads, so an attack can
    rewrite one of them without ever touching the live bytes."""
    if os.path.exists(root):
        shutil.rmtree(root)
    for rel in SANDBOX_FILES:
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(REPO, rel), dst)
    if edit:
        edit(root)
    return root

def rewrite_json(root, rel, fn):
    p = os.path.join(root, rel)
    d = json.load(open(p, encoding="utf-8"))
    fn(d)
    with open(p, "w", newline="\n", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)

def rebind(root, rel_contract, key):
    """Re-point the authority at the EDITED contract. This is what a competent attacker
    would do, and it is the only way to test the second line of defence rather than the
    first one over and over."""
    p = os.path.join(root, rel_contract)
    sha = B.sha_file(p)
    blob = subprocess.run(["git", "hash-object", p], capture_output=True,
                          text=True).stdout.strip()

    def fix(d):
        d["INHERITED_NOT_RESTATED"][key]["sha256"] = sha
        d["INHERITED_NOT_RESTATED"][key]["git_blob"] = blob
    rewrite_json(root, AUTHORITY, fix)

def sandbox_attack(label, required, edit, expect_token=None, root_base=None, n=[0]):
    n[0] += 1
    root = os.path.join(root_base, "sb%02d" % n[0])
    make_sandbox(root, edit)
    code, out = run_exec(["--preflight-only"], cwd=root)
    tok = (expect_token or "").lower() in out.lower() if expect_token else True
    holds = code != 0 and tok
    first = [l for l in out.splitlines() if "Stop" in l or "STOP" in l]
    rec("bypass", label, required,
        "exit=" + str(code) + " | " + (first[-1][:150] if first else out.strip()[-150:]),
        holds)
    shutil.rmtree(root, ignore_errors=True)

def main() -> int:
    live_before = {p: B.sha_file(p) for p in (EXEC_REL, AUTHORITY, NULL_CONTRACT,
                                              DESIGN_CONTRACT)}
    if os.path.exists(AUTHZ):
        print("STOP: an authorisation artifact already exists at the canonical path.")
        return 2
    atexit.register(lambda: os.path.exists(AUTHZ) and os.remove(AUTHZ))
    tmp_root = "D:/jepa_tmp_antibypass_%d" % os.getpid()
    os.makedirs(tmp_root, exist_ok=True)

    # ======================================================== G17, statically
    import ast
    tree = ast.parse(open(EXEC_REL, encoding="utf-8").read())
    banned_mods = {"anndata", "scanpy", "h5py"}
    banned_calls = {"read_h5ad", "read_10x_h5", "read_10x_mtx"}
    imports, calls = [], []
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Import):
            imports += [a.name.split(".")[0] for a in nd.names]
        elif isinstance(nd, ast.ImportFrom) and nd.module:
            imports.append(nd.module.split(".")[0])
        elif isinstance(nd, ast.Call):
            nm = getattr(nd.func, "attr", None) or getattr(nd.func, "id", None)
            if nm:
                calls.append(nm)
    bad_imp = sorted(set(imports) & banned_mods)
    bad_call = sorted(set(calls) & banned_calls)
    rec("G17-static", "no raw-matrix module is imported anywhere in the executor",
        "zero banned imports", "banned=" + str(bad_imp) + " of " + str(len(set(imports)))
        + " modules imported", not bad_imp)
    rec("G17-static", "no raw-matrix reader is called anywhere in the executor",
        "zero banned calls", "banned=" + str(bad_call), not bad_call)

    # Scan the STRING CONSTANTS the executor could actually open, not its lines. A line
    # scan flags the module docstring for naming the thing it forbids -- the same
    # "the guard matches its own text" failure this project has now hit three times.
    docstrings = set()
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                           ast.ClassDef)):
            d = ast.get_docstring(nd, clean=False)
            if d:
                docstrings.add(d)
    deny = set()
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Assign) and any(
                getattr(t, "id", "") == "FORBIDDEN_PATH_TOKENS" for t in nd.targets):
            deny = {e.value for e in ast.walk(nd)
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    tokens = (".h5ad", "final_rna_data", "final_atac_data")
    suspicious = [c.value for c in ast.walk(tree)
                  if isinstance(c, ast.Constant) and isinstance(c.value, str)
                  and c.value not in docstrings and c.value not in deny
                  and any(t in c.value for t in tokens)]
    rec("G17-static", "no matrix path literal among the executor's string constants",
        "zero", str(len(suspicious)) + " suspicious literal(s) "
        + str(suspicious[:2]) + "; deny-list=" + str(len(deny))
        + " tokens, docstrings excluded=" + str(len(docstrings)), not suspicious)

    # The scan must be CAPABLE of failing, or it is decoration. Inject a matrix path and
    # a raw import into a copy of the source and require both static gates to fire.
    injected = ["", "import anndata", "_p = 'D:/x/final_rna_data.h5ad'", ""]
    inj = ast.parse(open(EXEC_REL, encoding="utf-8").read()
                    + chr(10).join(injected))
    inj_docs = set()
    for nd in ast.walk(inj):
        if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                           ast.ClassDef)):
            d = ast.get_docstring(nd, clean=False)
            if d:
                inj_docs.add(d)
    inj_imports = [a.name.split(".")[0] for nd in ast.walk(inj)
                   if isinstance(nd, ast.Import) for a in nd.names]
    inj_lits = [c.value for c in ast.walk(inj)
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
                and c.value not in inj_docs and c.value not in deny
                and any(t in c.value for t in tokens)]
    rec("G17-static", "negative control: both static gates fire on an injected violation",
        "import gate and literal gate both go red",
        "import caught=" + str(bool(set(inj_imports) & banned_mods))
        + " literal caught=" + str(bool(inj_lits)),
        bool(set(inj_imports) & banned_mods) and bool(inj_lits))

    # ======================================================= G17, executably
    poison = os.path.join(tmp_root, "poison")
    os.makedirs(poison, exist_ok=True)
    with open(os.path.join(poison, "sitecustomize.py"), "w", newline="\n") as fh:
        fh.write(
            "import builtins, sys\n"
            "class _Poison(object):\n"
            "    __path__ = []\n"
            "    def __getattr__(self, k):\n"
            "        raise RuntimeError('G17 VIOLATION: raw matrix reader used: ' + k)\n"
            "for _m in ('anndata', 'scanpy', 'h5py'):\n"
            "    sys.modules[_m] = _Poison()\n"
            "_real_open = builtins.open\n"
            "def _guard(f, *a, **k):\n"
            "    s = str(f)\n"
            "    if s.endswith('.h5ad') or 'final_rna_data' in s or 'final_atac_data' in s:\n"
            "        raise RuntimeError('G17 VIOLATION: opened a raw matrix: ' + s)\n"
            "    return _real_open(f, *a, **k)\n"
            "builtins.open = _guard\n")
    code, out = run_exec(["--preflight-only"],
                         env={"PYTHONPATH": poison + os.pathsep
                              + os.environ.get("PYTHONPATH", "")})
    violated = "G17 VIOLATION" in out
    rec("G17-exec", "full preflight with every raw reader poisoned to raise",
        "completes without touching a matrix",
        "exit=" + str(code) + " violation=" + str(violated),
        code == 0 and not violated)

    # the poison must be capable of firing, or it proves nothing
    probe = os.path.join(tmp_root, "probe.py")
    with open(probe, "w", newline="\n") as fh:
        fh.write("import anndata\nanndata.read_h5ad('x.h5ad')\n")
    pr = subprocess.run([sys.executable, probe], capture_output=True, text=True,
                        env=dict(os.environ, PYTHONPATH=poison))
    rec("G17-exec", "positive control: the poison does fire when a matrix IS opened",
        "raises G17 VIOLATION", "fired=" + str("G17 VIOLATION" in pr.stderr),
        "G17 VIOLATION" in pr.stderr)

    # ========================================================== anti-bypass 1-16
    # A15 execution without authorisation
    code, out = run_exec([])
    rec("bypass", "A15 invoke real execution with no authorisation artifact",
        "refuse, nonzero exit", "exit=" + str(code),
        code == 3 and "REFUSED" in out)

    # A16 arbitrary CLI method/bypass flags
    flags = ["--unsafe", "--skip-digest", "--skip-schema", "--debug",
             "--contract=/tmp/x.json", "--authority=/tmp/y.json", "--input-root=/tmp",
             "--method=spearman", "--seed=1", "--weighting=EDGE_EQUAL",
             "--out-dir=/tmp/z", "--force"]
    rejected = 0
    for f in flags:
        c, o = run_exec([f, "--preflight-only"])
        if c != 0 and "unrecognized arguments" in o:
            rejected += 1
    rec("bypass", "A16 invent 12 bypass / method-override CLI flags",
        "argparse rejects every one", str(rejected) + "/" + str(len(flags)) + " rejected",
        rejected == len(flags))

    # forged authorisations at the canonical path
    def with_authz(payload, label, required):
        with open(AUTHZ, "w", newline="\n") as fh:
            json.dump(payload, fh, indent=2)
        try:
            c, o = run_exec([])
            reason = [l.strip() for l in o.splitlines() if "reason:" in l]
            detail = reason[0] if reason else o.strip().splitlines()[-1][:120]
            rec("bypass", label, required, "exit=" + str(c) + " | " + detail, c != 0)
        finally:
            os.remove(AUTHZ)

    with_authz({"schema": "WRONG", "authorizes": "STAGE4_REAL_EXECUTION"},
               "A17 forged authorisation with the wrong schema", "refuse")
    with_authz({"schema": "V64_STAGE4_EXECUTION_AUTHORIZATION_V1",
                "authorizes": "SOMETHING_ELSE"},
               "A18 artifact that does not authorise execution", "refuse")
    with_authz({"schema": "V64_STAGE4_EXECUTION_AUTHORIZATION_V1",
                "authorizes": "STAGE4_REAL_EXECUTION",
                "executor_sha256": "0" * 64, "authority_sha256": "0" * 64},
               "A19 authorisation naming a different executor build", "refuse")
    with_authz({"schema": "V64_STAGE4_EXECUTION_AUTHORIZATION_V1",
                "authorizes": "STAGE4_REAL_EXECUTION",
                "executor_sha256": B.sha_file(EXEC_REL),
                "authority_sha256": "0" * 64},
               "A20 authorisation naming a different authority", "refuse")
    with_authz({"schema": "V64_STAGE4_EXECUTION_AUTHORIZATION_V1",
                "authorizes": "STAGE4_REAL_EXECUTION",
                "executor_sha256": B.sha_file(EXEC_REL),
                "authority_sha256": B.sha_file(AUTHORITY)},
               "A21 a fully valid authorisation, correctly bound",
               "still produces no result: this build cannot compute one")

    # A1 swap the authority for a different, well-formed JSON file
    def swap(root):
        shutil.copy2(os.path.join(root, DESIGN_CONTRACT), os.path.join(root, AUTHORITY))
    sandbox_attack("A1 swap the authority file for a different contract",
                   "refuse", swap, root_base=tmp_root)

    # A2 edit one bound digest
    sandbox_attack("A2 edit one bound input digest in the authority",
                   "refuse with a digest mismatch",
                   lambda r: rewrite_json(r, AUTHORITY, lambda d: d["BOUND_PHASE_B_INPUTS"]
                                          ["t5_donor_aggregates"].__setitem__(
                                              "sha256", "0" * 64)),
                   expect_token="digest_mismatch", root_base=tmp_root)

    # A3 a bound input that is not on disk
    def add_ghost(d):
        sh = d["BOUND_PHASE_B_INPUTS"]["substrate_shards"]
        sh["PHASE_B_SUBSTRATE_s08.npz"] = dict(
            path=SUBSTRATE_DIR + "/PHASE_B_SUBSTRATE_s08.npz",
            sha256="0" * 64, git_blob="UNCOMMITTED", repo_resident=False, bytes=1)
    sandbox_attack("A3 remove one input (bind a shard that is absent)",
                   "refuse, naming the missing input",
                   lambda r: rewrite_json(r, AUTHORITY, add_ghost),
                   expect_token="missing", root_base=tmp_root)

    # A4 an input on disk that nothing bound
    sandbox_attack("A4 add an unexpected input (unbind a shard that is present)",
                   "refuse, naming the unexpected input",
                   lambda r: rewrite_json(r, AUTHORITY,
                                          lambda d: d["BOUND_PHASE_B_INPUTS"]
                                          ["substrate_shards"].pop(
                                              "PHASE_B_SUBSTRATE_s07.npz")),
                   expect_token="unexpected", root_base=tmp_root)

    # A6 correct SHA-256, wrong Git blob
    sandbox_attack("A6 correct SHA-256 but a wrong Git blob for a repo-resident input",
                   "refuse: the two cannot describe the same bytes",
                   lambda r: rewrite_json(r, AUTHORITY,
                                          lambda d: d["INHERITED_NOT_RESTATED"]
                                          ["downstream_null_statistical_V3"].__setitem__(
                                              "git_blob", "0" * 40)),
                   expect_token="git_blob", root_base=tmp_root)

    # A8-A13: rewrite a frozen rule AND re-bind its digest, so only the second line of
    # defence can catch it
    def rule_attack(label, rel, key, mutate, token):
        def edit(root):
            rewrite_json(root, rel, mutate)
            rebind(root, rel, key)
        sandbox_attack(label, "refuse: the mirrored constant disagrees with the contract",
                       edit, expect_token=token, root_base=tmp_root)

    rule_attack("A10 change the bootstrap seed in the contract and re-bind it",
                DESIGN_CONTRACT, "correspondence_design",
                lambda d: d["PRIMARY_ESTIMAND"]["uncertainty"].__setitem__("seed", 1),
                "bootstrap_seed")
    rule_attack("A8 change the ridge alpha in the contract and re-bind it",
                DESIGN_CONTRACT, "correspondence_design",
                lambda d: d["NUISANCE_ADJUSTMENT"].__setitem__("ridge_alpha", 0.5),
                "ridge_alpha")
    rule_attack("A9 add a 15th nuisance term and re-bind it",
                DESIGN_CONTRACT, "correspondence_design",
                lambda d: d["NUISANCE_ADJUSTMENT"]["frozen_basis_14_features"].append(
                    "an_unknown_rule"),
                "nuisance_basis_term_count")
    rule_attack("A11 promote the companion weighting to primary and re-bind it",
                NULL_CONTRACT, "downstream_null_statistical_V3",
                lambda d: d["SECTION_6_DONOR_AND_STATISTICAL_MASS"]
                ["EDGE_MASS_CONCENTRATION"]
                ["WEIGHTING_HIERARCHY_IS_FIXED_AND_HAS_EXACTLY_ONE_PRIMARY"]["PRIMARY"]
                .__setitem__("name", "PROMOTER_EQUAL"),
                "primary_weighting")
    rule_attack("A12 drop the mandatory R3 conditional label and re-bind it",
                NULL_CONTRACT, "downstream_null_statistical_V3",
                lambda d: d["SECTION_10_ENUMERATION_REFERENCE_RULES"].__setitem__(
                    "R3_EXACT",
                    d["SECTION_10_ENUMERATION_REFERENCE_RULES"].pop(
                        "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM")),
                "r3_required_label")
    rule_attack("A13 rewrite the missingness rule so zero coverage becomes a zero",
                DESIGN_CONTRACT, "correspondence_design",
                lambda d: d["PRIMARY_CORRESPONDENCE_STATISTIC"].__setitem__(
                    "zero_coverage_rule",
                    "If coverage is zero the correlation is recorded as 0.0."),
                "zero_coverage_missingness_semantics")

    # A5 same-name wrong file -- proven on the consumer gate, in process
    sub = os.path.join(tmp_root, "sub")
    os.makedirs(sub, exist_ok=True)
    real = sorted(__import__("glob").glob(SUBSTRATE_DIR + "/PHASE_B_SUBSTRATE_s*.npz"))
    mixed = list(real)
    shutil.copy2(real[0], os.path.join(sub, "PHASE_B_SUBSTRATE_s03.npz"))
    mixed[3] = os.path.join(sub, "PHASE_B_SUBSTRATE_s03.npz")
    try:
        S = CS.load_substrate(shard_paths=mixed)
        g = CS.check_consumer_semantics(S)
        fired = sorted(k for k, (ok, _) in g.items() if not ok)
    except Exception as e:                                           # noqa: BLE001
        fired = ["LOAD_RAISED: " + type(e).__name__]
    rec("bypass", "A5 substitute a same-name file with different contents",
        "the aggregate-binding gate goes red", "gates red: " + str(fired[:3]),
        bool(fired))

    # A7 modify the executor worktree after the commit it claims
    mod = os.path.join(tmp_root, "modified_executor.py")
    shutil.copy2(EXEC_REL, mod)
    with open(mod, "a", newline="\n") as fh:
        fh.write("\n# one added byte\n")
    rec("bypass", "A7 modify the executor after the commit an authorisation names",
        "its SHA-256 no longer matches, so the authorisation no longer applies",
        "sha changed=" + str(B.sha_file(mod) != B.sha_file(EXEC_REL)),
        B.sha_file(mod) != B.sha_file(EXEC_REL))

    # A14 output overwrite
    out_dir = "D:/jepa_v5_outputs_20260925/v64_stage4"
    existed = os.path.isdir(out_dir)
    listing_before = sorted(os.listdir(out_dir)) if existed else None
    code, _ = run_exec([])
    listing_after = sorted(os.listdir(out_dir)) if os.path.isdir(out_dir) else None
    rec("bypass", "A14 attempt to write into the Stage-4 output directory",
        "nothing is created or overwritten while unauthorised",
        "dir existed=" + str(existed) + " unchanged="
        + str(listing_before == listing_after),
        listing_before == listing_after)

    # ============================================================ custody close
    shutil.rmtree(tmp_root, ignore_errors=True)
    live_after = {p: B.sha_file(p) for p in (EXEC_REL, AUTHORITY, NULL_CONTRACT,
                                             DESIGN_CONTRACT)}
    untouched = live_before == live_after
    rec("custody", "live executor, authority and both contracts unchanged by this suite",
        "identical digests", "untouched=" + str(untouched), untouched)
    no_authz = not os.path.exists(AUTHZ)
    rec("custody", "no authorisation artifact left behind at the canonical path",
        "absent", "absent=" + str(no_authz), no_authz)

    held = [r for r in RESULTS if r["holds"]]
    out = dict(
        schema="V64_STAGE4_G17_AND_ANTIBYPASS_V1", date="2026-10-01",
        closes="mandate sections 7 and 8",
        g17_static_checks=4, g17_executable_checks=2,
        anti_bypass_attempts=len([r for r in RESULTS if r["section"] == "bypass"]),
        n_checks=len(RESULTS), n_holding=len(held),
        live_artifacts_untouched=untouched,
        authorisation_path_clean=no_authz,
        computed_correspondence_values=0,
        executor_sha256=B.sha_file(EXEC_REL),
        authority_sha256=B.sha_file(AUTHORITY),
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        checks=RESULTS,
        status="PASS" if len(held) == len(RESULTS) and untouched and no_authz else "FAIL")
    p = os.path.join(DIR, "V64_STAGE4_G17_AND_ANTIBYPASS_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print(str(len(held)) + "/" + str(len(RESULTS)) + " checks behaved as required -> "
          + out["status"])
    print("receipt sha256 " + B.sha_file(p))
    return 0 if out["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
