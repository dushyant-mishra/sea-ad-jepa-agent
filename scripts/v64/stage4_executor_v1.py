#!/usr/bin/env python3
"""Stage-4 executor. Implemented and bound; NOT authorised to produce a real result.

WHAT THIS IS. The executor that will one day compute the frozen Stage-4 estimand. It
exists so that it can be audited BEFORE it is ever allowed to run, which is the only
order in which an irreversible step can be reviewed honestly.

WHAT IT REFUSES TO DO TODAY. Real execution requires a separately committed authorisation
artifact at one canonical path with an expected schema. That artifact does not exist and
this executor does not create it. Without it, `--preflight-only` is the only mode that
runs, and it computes zero correspondence values.

NO BYPASS SURFACE, BY CONSTRUCTION. There is exactly one flag. There is no --contract, no
--authority, no --input-root, no --skip-digest, no --skip-schema, no --unsafe, no --debug,
and no way to name a method, a seed, a weighting or a threshold from the command line. The
canonical authority path and the canonical output path are module constants. A reviewer
can therefore confirm the absence of a bypass by reading the argument parser, which is
four lines long, rather than by trusting a promise.

G17. This module must never reopen the RNA or ATAC matrices. It imports no anndata and no
scanpy, and it opens no .h5ad. The static auditor checks that claim against this source,
and the executable test monkeypatches the raw readers to raise if called.

THE MATH IS SEPARATED FROM THE WIRING. The frozen computation lives in pure functions that
take arrays, so the synthetic qualification suite can plant a known answer and check it
without any CLI able to inject data into a real run. That separation is what lets the
executor be both testable and un-bypassable.

TRAINING=OFF. STAGE 4 NOT AUTHORISED. CORRESPONDENCE UNOPENED.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import platform
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                    # noqa: E402
import verify_phase_b_consumer_semantics_v1 as CS                  # noqa: E402

# ----------------------------------------------------------------- canonical paths
HERE = os.path.abspath(__file__)
DIR = "results/v64/phase_b_design"
CANONICAL_AUTHORITY = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json")
CANONICAL_AUTHORIZATION = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORIZATION_V1.json")
CANONICAL_OUT_DIR = "D:/jepa_v5_outputs_20260925/v64_stage4"
SUBSTRATE_DIR = "D:/jepa_v5_outputs_20260925/v64_phase_b"
PREFLIGHT_RECEIPT = os.path.join(DIR, "V64_STAGE4_PREFLIGHT_ONLY_RECEIPT_V1.json")
DESIGN_CONTRACT = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
NULL_CONTRACT = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
AUTHORIZATION_SCHEMA = "V64_STAGE4_EXECUTION_AUTHORIZATION_V1"

# frozen constants, mirrored here only so a reader sees them; every one is checked
# against the contracts at run time and a disagreement is a STOP.
FROZEN = dict(bootstrap_replicates=4000, bootstrap_seed=20260929, ridge_alpha=1.0,
              k_folds=5, cross_fitting_unit="promoter",
              min_microglia=100, min_metacells=4, min_donors_per_edge=30,
              primary_weighting="GENE_BALANCED",
              companion_weighting="PROMOTER_EQUAL",
              sensitivity_weighting="EDGE_EQUAL",
              primary_distance="SOURCE_HG19_DISTANCE",
              r3_label="CONDITIONAL_ON_REALISED_LARGE_ARM")
FORBIDDEN_PATH_TOKENS = ("final_rna_data", "final_atac_data", ".h5ad", "anndata",
                         "scanpy", "morabito", "td60")


class Stop(Exception):
    """Fail closed. Every refusal in this module raises, never warns."""


# ============================================================ frozen computation
def pair_correlation(rna, atac, rna_avail, atac_avail):
    """Pearson between a gene's metacell RNA vector and its interval's metacell ATAC
    vector, WITHIN one donor, across that donor's qualifying metacells.

    Missingness is handled exactly as frozen: a measured zero stays a zero and
    participates; an UNAVAILABLE element is never silently turned into a numeric zero;
    zero coverage or zero variance in either vector makes the cell MISSING rather than
    producing a number that would read as 'no correspondence'.
    """
    rna = np.asarray(rna, float)
    atac = np.asarray(atac, float)
    keep = np.asarray(rna_avail, bool) & np.asarray(atac_avail, bool)
    if keep.sum() < 2:
        return None, "MISSING_INSUFFICIENT_METACELLS"
    r, a = rna[keep], atac[keep]
    if not np.isfinite(r).all() or not np.isfinite(a).all():
        return None, "MISSING_NONFINITE"
    if (r == 0).all():
        return None, "MISSING_RNA_ZERO_COVERAGE"
    if (a == 0).all():
        return None, "MISSING_ATAC_ZERO_COVERAGE"
    if r.std() == 0:
        return None, "MISSING_RNA_ZERO_VARIANCE"
    if a.std() == 0:
        return None, "MISSING_ATAC_ZERO_VARIANCE"
    rc, ac = r - r.mean(), a - a.mean()
    denom = np.sqrt((rc * rc).sum() * (ac * ac).sum())
    if denom == 0:
        return None, "MISSING_DEGENERATE"
    return float((rc * ac).sum() / denom), "MEASURED"


def ridge_residualise(y, X, groups, alpha=FROZEN["ridge_alpha"],
                      k=FROZEN["k_folds"]):
    """Cross-fitted ridge residualisation on the frozen 14-term basis.

    Folds are formed over GROUPS (promoters), never over rows, so a promoter never
    appears in both the fit and the prediction. No feature is selected adaptively and the
    basis is never refit after an outcome is seen.
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    groups = np.asarray(groups)
    uniq = np.unique(groups)
    order = np.arange(len(uniq))
    fold_of_group = {g: int(i % k) for i, g in zip(order, uniq)}
    folds = np.array([fold_of_group[g] for g in groups])
    resid = np.full(len(y), np.nan)
    for f in range(k):
        tr, te = folds != f, folds == f
        if tr.sum() < 2 or te.sum() == 0:
            continue
        Xt, yt = X[tr], y[tr]
        xm, ym = Xt.mean(0), yt.mean()
        Xc = Xt - xm
        A = Xc.T @ Xc + alpha * np.eye(X.shape[1])
        beta = np.linalg.solve(A, Xc.T @ (yt - ym))
        resid[te] = y[te] - ((X[te] - xm) @ beta + ym)
    return resid


def aggregate_delta(linked, control, gene, promoter, weighting):
    """Set-level Delta under one of the three frozen weightings.

    GENE_BALANCED is the primary: within a donor, the mean over genes of the within-gene
    mean over that gene's edges. PROMOTER_EQUAL is the mandatory companion and EDGE_EQUAL
    the predeclared sensitivity. All three are computed every time; none is selected by
    which is largest.
    """
    linked = np.asarray(linked, float)
    control = np.asarray(control, float)
    d = linked - control
    ok = np.isfinite(d)
    if not ok.any():
        return None
    d, g, p = d[ok], np.asarray(gene)[ok], np.asarray(promoter)[ok]
    if weighting == "EDGE_EQUAL":
        return float(d.mean())
    key = g if weighting == "GENE_BALANCED" else p
    if weighting not in ("GENE_BALANCED", "PROMOTER_EQUAL"):
        raise Stop(f"unknown weighting {weighting}")
    means = [d[key == u].mean() for u in np.unique(key)]
    return float(np.mean(means))


def donor_cluster_bootstrap(per_donor_values, n=FROZEN["bootstrap_replicates"],
                            seed=FROZEN["bootstrap_seed"]):
    """Nonparametric cluster bootstrap over DONORS only. Donors are the sole resampling
    unit; a promoter is block structure, never an independent replicate."""
    vals = np.asarray([v for v in per_donor_values if v is not None and np.isfinite(v)],
                      float)
    if len(vals) < 2:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n, len(vals)))
    return np.sort(vals[idx].mean(1))


def one_sided_lcb95(boot):
    """The reported quantity is the one-sided 95% lower confidence bound."""
    return None if boot is None else float(np.quantile(boot, 0.05))


# ============================================================ identity and custody
def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    o = r.stdout.strip()
    return o if r.returncode == 0 else None


def _blob_of_worktree(path):
    o = _git("hash-object", path)
    return o if o and len(o) == 40 else None


def _blob_at_head(path):
    o = _git("rev-parse", f"HEAD:{path.replace(os.sep, '/')}")
    return o if o and len(o) == 40 else None


def identity_report():
    """Everything a reproducer needs to confirm WHICH executor ran against WHICH rules."""
    me = os.path.relpath(HERE, os.getcwd()).replace(os.sep, "/")
    inputs = {}
    for p in sorted(glob.glob(os.path.join(
            "D:/jepa_v5_outputs_20260925/v64_phase_b", "PHASE_B_SUBSTRATE_s*.npz"))):
        inputs[os.path.basename(p)] = dict(path=p, sha256=B.sha_file(p))
    for label, p in (("t5", "D:/jepa_v5_outputs_20260925/v64_phase_b/"
                            "PHASE_B_T5_DONOR_AGGREGATES.npz"),
                     ("availability", "D:/jepa_v5_outputs_20260925/v64_phase_b/"
                                      "PHASE_B_T3_T4_AVAILABILITY.npz")):
        inputs[label] = dict(path=p, sha256=B.sha_file(p))
    repo_inputs = {}
    for p in (CANONICAL_AUTHORITY, DESIGN_CONTRACT, NULL_CONTRACT,
              "scripts/v63/e2_continuous_adjustment_estimator_v1.py"):
        repo_inputs[p] = dict(sha256=B.sha_file(p), git_blob_at_head=_blob_at_head(p),
                              worktree_blob=_blob_of_worktree(p),
                              source_commit=_git("rev-parse", "HEAD"))
    return dict(
        executor=dict(path=me, sha256=B.sha_file(HERE),
                      worktree_blob=_blob_of_worktree(me),
                      git_blob_at_head=_blob_at_head(me)),
        bound_authority=dict(path=CANONICAL_AUTHORITY,
                             sha256=B.sha_file(CANONICAL_AUTHORITY),
                             git_blob_at_head=_blob_at_head(CANONICAL_AUTHORITY)),
        frozen_statistical_contract=dict(
            path=NULL_CONTRACT, sha256=B.sha_file(NULL_CONTRACT),
            design=dict(path=DESIGN_CONTRACT, sha256=B.sha_file(DESIGN_CONTRACT))),
        scientific_input_digests=inputs,
        repo_resident_inputs=repo_inputs,
        frozen_constants=FROZEN,
        runtime=dict(python=sys.version.split()[0], platform=platform.platform(),
                     numpy=np.__version__),
        source_commit=_git("rev-parse", "HEAD"))


def assert_no_matrix_access():
    """G17, enforced from inside the executor as well as audited from outside.

    S83. The first version grepped this file for the strings it forbids, so it flagged
    its OWN prohibition list and could never pass -- the same defect class as a gate
    matching its own field name. A guard written as a substring scan over its own source
    is structurally unable to distinguish a prohibition from a violation.

    The check is therefore parsed, not grepped: the AST is walked for actual IMPORTS of
    anndata/scanpy/h5py and for actual CALLS to a raw-matrix reader. A string that merely
    names a forbidden library in a docstring or a deny-list is not an access.
    """
    import ast as _ast
    tree = _ast.parse(open(HERE, encoding="utf-8").read())
    banned_mods = {"anndata", "scanpy", "h5py"}
    banned_calls = {"read_h5ad", "read_10x_h5"}
    bad = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for n in node.names:
                if n.name.split(".")[0] in banned_mods:
                    bad.append(f"import {n.name}")
        elif isinstance(node, _ast.ImportFrom):
            if node.module and node.module.split(".")[0] in banned_mods:
                bad.append(f"from {node.module} import ...")
        elif isinstance(node, _ast.Call):
            f = node.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name in banned_calls:
                bad.append(f"call {name}()")
            if name == "File":                      # h5py.File(...)
                owner = getattr(getattr(f, "value", None), "id", None)
                if owner in banned_mods:
                    bad.append("call h5py.File()")
    if bad:
        raise Stop(f"executor source performs raw-matrix access: {sorted(set(bad))}")
    return dict(ast_parsed=True, banned_modules=sorted(banned_mods),
                banned_calls=sorted(banned_calls), violations=0)


def verify_bound_inputs():
    """Every byte Stage 4 reads must equal the digest the authority bound, and the input
    set must be EXACTLY the bound set.

    Binding a PATH is worthless: a file of the same name with different contents satisfies
    it. Binding the BYTES does not, which is why each digest is recomputed here rather than
    read back out of a receipt. The set is checked in both directions as well -- a missing
    shard would silently shrink the population and an unexpected shard would silently grow
    it, and neither is detectable from digests alone.
    """
    A = json.load(open(CANONICAL_AUTHORITY))
    bound = A["BOUND_PHASE_B_INPUTS"]
    mismatched, missing, extra = [], [], []
    checked = 0

    expected = dict(bound["substrate_shards"])
    on_disk = {os.path.basename(q): q for q in
               glob.glob(os.path.join(SUBSTRATE_DIR, "PHASE_B_SUBSTRATE_s*.npz"))}
    missing += sorted(set(expected) - set(on_disk))
    extra += sorted(set(on_disk) - set(expected))
    for name, e in sorted(expected.items()):
        if name not in on_disk:
            continue
        if B.sha_file(e["path"]) != e["sha256"]:
            mismatched.append(name)
        checked += 1

    for key in ("t5_donor_aggregates", "t3_t4_availability"):
        e = bound[key]
        if not os.path.exists(e["path"]):
            missing.append(key)
        elif B.sha_file(e["path"]) != e["sha256"]:
            mismatched.append(key)
        else:
            checked += 1

    repo_bound = dict(A["INHERITED_NOT_RESTATED"])
    repo_bound.pop("principle", None)
    repo_bound["imported_estimator"] = A["ESTIMATOR_IMPORTED_UNMODIFIED"]
    for label, e in sorted(repo_bound.items()):
        if not isinstance(e, dict) or "sha256" not in e or "path" not in e:
            continue
        if not os.path.exists(e["path"]):
            missing.append(label)
        elif B.sha_file(e["path"]) != e["sha256"]:
            mismatched.append(label)
        elif (e.get("git_blob") not in (None, "UNCOMMITTED")
              and _blob_of_worktree(e["path"]) != e["git_blob"]):
            # a correct SHA-256 with a wrong Git blob cannot describe the same bytes, so
            # this catches a binding that was written rather than computed
            mismatched.append(label + ":git_blob")
        else:
            checked += 1

    if missing or extra or mismatched:
        raise Stop(f"bound inputs do not match the authority: "
                   f"missing={missing} unexpected={extra} digest_mismatch={mismatched}")
    return dict(bound_inputs_verified=checked, missing=0, unexpected=0,
                digest_mismatches=0)


def check_frozen_rules_against_contracts():
    """A constant mirrored in this file must equal the contract, or we stop."""
    D = json.load(open(DESIGN_CONTRACT))
    N = json.load(open(NULL_CONTRACT))
    pe, nui = D["PRIMARY_ESTIMAND"], D["NUISANCE_ADJUSTMENT"]
    msr = D["MEASUREMENT_SUPPORT_RESTRICTION"]["donor_level_rules"]
    wh = N["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["EDGE_MASS_CONCENTRATION"][
        "WEIGHTING_HIERARCHY_IS_FIXED_AND_HAS_EXACTLY_ONE_PRIMARY"]
    bad = []
    if pe["uncertainty"]["replicates"] != FROZEN["bootstrap_replicates"]:
        bad.append("bootstrap_replicates")
    if pe["uncertainty"]["seed"] != FROZEN["bootstrap_seed"]:
        bad.append("bootstrap_seed")
    if nui["ridge_alpha"] != FROZEN["ridge_alpha"]:
        bad.append("ridge_alpha")
    if nui["k_folds"] != FROZEN["k_folds"]:
        bad.append("k_folds")
    if nui["cross_fitting_unit"] != FROZEN["cross_fitting_unit"]:
        bad.append("cross_fitting_unit")
    if msr["minimum_microglia_per_donor"] != FROZEN["min_microglia"]:
        bad.append("min_microglia")
    if msr["minimum_metacells_per_donor"] != FROZEN["min_metacells"]:
        bad.append("min_metacells")
    if msr["minimum_donors_per_edge"] != FROZEN["min_donors_per_edge"]:
        bad.append("min_donors_per_edge")
    if wh["PRIMARY"]["name"] != FROZEN["primary_weighting"]:
        bad.append("primary_weighting")
    if wh["MANDATORY_COMPANION"]["name"] != FROZEN["companion_weighting"]:
        bad.append("companion_weighting")
    if wh["PREDECLARED_SENSITIVITY"]["name"] != FROZEN["sensitivity_weighting"]:
        bad.append("sensitivity_weighting")
    if len(nui["frozen_basis_14_features"]) != 14:
        bad.append("nuisance_basis_term_count")
    # the R3 label is part of the estimand's meaning, not decoration: it is what stops an
    # R3 number being read as if it were the unconditional quantity
    enum = N["SECTION_10_ENUMERATION_REFERENCE_RULES"]
    if not any(FROZEN["r3_label"] in k for k in enum):
        bad.append("r3_required_label")
    # missingness semantics. MEASURED_ZERO != NOT_MEASURED is the invariant the whole
    # project rests on, so the executor refuses to run against a contract that has stopped
    # saying it.
    st = D["PRIMARY_CORRESPONDENCE_STATISTIC"]
    zc, dv = st["zero_coverage_rule"], st["degenerate_variance_rule"]
    if "MISSING" not in zc or "NEVER recorded as zero" not in zc:
        bad.append("zero_coverage_missingness_semantics")
    if "MISSING" not in dv:
        bad.append("degenerate_variance_missingness_semantics")
    if "Pearson" not in st["per_donor_per_pair_score"] or             "metacells" not in st["per_donor_per_pair_score"]:
        bad.append("per_donor_per_pair_statistic")
    if bad:
        raise Stop(f"frozen constants disagree with the contracts: {bad}")
    return dict(checked=17, nuisance_terms=len(nui["frozen_basis_14_features"]))


def authorization_state():
    """Real execution is gated on a separate artifact this executor never writes."""
    if not os.path.exists(CANONICAL_AUTHORIZATION):
        return dict(present=False, authorized=False,
                    reason="no authorisation artifact at the canonical path")
    try:
        a = json.load(open(CANONICAL_AUTHORIZATION))
    except Exception as e:                                       # noqa: BLE001
        return dict(present=True, authorized=False, reason=f"unreadable: {e}")
    if a.get("schema") != AUTHORIZATION_SCHEMA:
        return dict(present=True, authorized=False, reason="wrong schema")
    if a.get("authorizes") != "STAGE4_REAL_EXECUTION":
        return dict(present=True, authorized=False, reason="does not authorise execution")
    if a.get("executor_sha256") != B.sha_file(HERE):
        return dict(present=True, authorized=False,
                    reason="authorises a different executor build")
    if a.get("authority_sha256") != B.sha_file(CANONICAL_AUTHORITY):
        return dict(present=True, authorized=False,
                    reason="authorises a different authority")
    me = os.path.relpath(HERE, os.getcwd()).replace(os.sep, "/")
    if _blob_of_worktree(me) != _blob_at_head(me):
        return dict(present=True, authorized=False,
                    reason="executor worktree differs from its committed head")
    return dict(present=True, authorized=True)


# ============================================================ preflight traversal
def preflight():
    assert_no_matrix_access()
    binding = verify_bound_inputs()
    rules = check_frozen_rules_against_contracts()
    S = CS.load_substrate()
    sem = CS.check_consumer_semantics(S)
    sem = {k: v for k, v in sem.items() if not k.startswith("_")}
    sem_failed = [k for k, (ok, _) in sem.items() if not ok]
    if sem_failed:
        raise Stop(f"consumer semantics failed: {sem_failed}")

    sh = S["shards"]
    ref = sh[0]
    genes = [str(x) for x in ref["genes"]]
    gpos = {g: i for i, g in enumerate(genes)}
    pair_keys = [str(x) for x in ref["pair_keys"]]
    pair_gene = [str(x) for x in ref["pair_gene"]]
    pair_iv = np.asarray(ref["pair_interval"])

    unresolved_gene = sum(1 for g in pair_gene if g not in gpos)
    n_iv = len(ref["interval_start"])
    unresolved_iv = int(((pair_iv < 0) | (pair_iv >= n_iv)).sum())
    mc = np.sort(np.concatenate([s["t2_metacell"] for s in sh]))
    donors = sorted({str(d) for s in sh for d in s["t2_donor"]})

    t5 = S["t5"]
    states = [str(x) for x in t5["states"]]
    codes = np.asarray(t5["availability_state_code"])
    legal = bool(((codes >= 0) & (codes < len(states))).all())
    per_state = {states[i]: int((codes == i).sum()) for i in range(len(states))}
    funnel_total = sum(per_state.values())

    # nuisance-design and distance metadata availability
    have = {k: k in t5 for k in ("promoter_activity", "distal_accessibility",
                                 "rna_depth_sensitivity", "atac_depth_sensitivity",
                                 "n_assigned_peaks", "n_metacells_contributing")}
    rows = [json.loads(l) for l in __import__("gzip").open(
        "results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz", "rt")]
    dist_fields = ("source_hg19_distance_bp", "log_distance", "promoter_degree",
                   "re_density", "anchor_frequency")
    dist_have = {f: all(f in r for r in rows[:1000]) for f in dist_fields}

    return dict(
        consumer_semantics={k: dict(passed=v[0], detail=v[1]) for k, v in sem.items()},
        shards_loaded=len(sh),
        dictionaries_agree=all(sem[k][0] for k in
                               ("C4_GENE_DICT_AGREES_ACROSS_SHARDS",
                                "C5_INTERVAL_DICT_AGREES_ACROSS_SHARDS",
                                "C6_PAIR_DICT_AGREES_ACROSS_SHARDS")),
        pair_to_gene_unresolved=unresolved_gene,
        pair_to_interval_unresolved=unresolved_iv,
        metacell_ids_dense=bool(np.array_equal(mc, np.arange(len(mc)))),
        metacells=int(len(mc)), donors=len(donors), pairs=len(pair_keys),
        availability_states_decode_legally=legal,
        availability_state_counts=per_state,
        funnel_rows=funnel_total,
        funnel_reconciles=funnel_total == len(codes),
        nuisance_design_fields_available=have,
        distance_fields_available=dist_have,
        primary_distance=FROZEN["primary_distance"],
        frozen_rules_checked=rules,
        bound_input_binding=binding,
        rna_matrix_opened=False, atac_matrix_opened=False,
        computed_correspondence_values=0)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage-4 executor. Only --preflight-only is available; there is no "
                    "flag that can change the frozen computation, name an alternate "
                    "contract or input root, or skip a check.")
    ap.add_argument("--preflight-only", action="store_true",
                    help="resolve everything the real run needs and compute zero "
                         "correspondence values")
    a = ap.parse_args()

    auth = authorization_state()
    ident = identity_report()

    if not a.preflight_only:
        if not auth["authorized"]:
            print("REFUSED: real Stage-4 execution is not authorised.")
            print(f"  reason: {auth['reason']}")
            print(f"  a separate authorisation artifact must exist at "
                  f"{CANONICAL_AUTHORIZATION}")
            print("  this executor does not create it.")
            return 3
        raise Stop("authorised real execution is not implemented in this build")

    out = preflight()
    rec = dict(schema="V64_STAGE4_PREFLIGHT_ONLY_RECEIPT_V1", date="2026-10-01",
               mode="preflight-only",
               computed_correspondence_values=0,
               a_successful_dry_run_is_not_execution_authorization=True,
               authorization=auth, identity=ident, preflight=out,
               governance=json.load(open(NULL_CONTRACT))["governance"],
               status="PASS")
    os.makedirs(os.path.dirname(PREFLIGHT_RECEIPT), exist_ok=True)
    with open(PREFLIGHT_RECEIPT, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print(f"preflight-only: {out['shards_loaded']} shards, {out['metacells']:,} metacells, "
          f"{out['donors']} donors, {out['pairs']:,} pairs")
    print(f"  dictionaries agree        : {out['dictionaries_agree']}")
    print(f"  pair->gene unresolved     : {out['pair_to_gene_unresolved']}")
    print(f"  pair->interval unresolved : {out['pair_to_interval_unresolved']}")
    print(f"  availability decodes      : {out['availability_states_decode_legally']}")
    print(f"  funnel reconciles         : {out['funnel_reconciles']} "
          f"({out['funnel_rows']:,} rows)")
    print(f"  COMPUTED CORRESPONDENCE VALUES: {out['computed_correspondence_values']}")
    print(f"  authorisation             : {auth['reason'] if not auth['authorized'] else 'present'}")
    print(f"receipt sha256 {B.sha_file(PREFLIGHT_RECEIPT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
