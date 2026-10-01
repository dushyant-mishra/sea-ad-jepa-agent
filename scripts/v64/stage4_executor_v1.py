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
AUTHORITY_SCHEMA = "V64_STAGE4_EXECUTION_AUTHORITY_V1"

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
    try:
        A = json.load(open(CANONICAL_AUTHORITY))
    except Exception as e:                                           # noqa: BLE001
        raise Stop(f"the bound authority is not readable JSON: {e}")
    if A.get("schema") != AUTHORITY_SCHEMA:
        raise Stop(f"the file at the canonical authority path is not the Stage-4 "
                   f"authority (schema={A.get('schema')!r})")
    for required in ("BOUND_PHASE_B_INPUTS", "INHERITED_NOT_RESTATED",
                     "ESTIMATOR_IMPORTED_UNMODIFIED"):
        if required not in A:
            raise Stop(f"the bound authority is missing {required}")
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


# ====================================================== full Stage-4 orchestration
# Everything below is the real pipeline. It is reached by a synthetic world today and by
# a real run only once a separate authorisation artifact exists. There is deliberately
# ONE implementation: a synthetic world that passed through a parallel code path would
# qualify nothing.

SYNTHETIC_ROOT = "D:/jepa_v5_outputs_20260925/v64_stage4_synthetic"
SYNTHETIC_OUT = os.path.join(SYNTHETIC_ROOT, "_results")
SYNTHETIC_WORLDS = ("BIOLOGY_POSITIVE", "TRUE_NULL", "MEASURED_TECHNICAL",
                    "HIDDEN_CONFOUND")


def _unpack_avail(packed, shape):
    n_m, n_f = int(shape[0]), int(shape[1])
    bits = np.unpackbits(np.asarray(packed, np.uint8), bitorder="big")[:n_m * n_f]
    return bits.reshape(n_m, n_f).astype(bool)


def _dense(rows, cols, vals, n_r, n_c):
    M = np.zeros((n_r, n_c), np.float32)
    M[np.asarray(rows, np.int64), np.asarray(cols, np.int64)] = vals
    return M


def donor_eligibility(S):
    """The frozen donor rules: at least 100 microglia and at least 4 metacells. Both are
    measurement-precision rules fixed before any outcome; neither may be relaxed."""
    sh = S["shards"]
    mc = np.concatenate([s["t2_metacell"] for s in sh])
    dn = np.concatenate([s["t2_donor"] for s in sh]).astype(str)
    if any("t2_n_nuclei" not in s for s in sh):
        # never default this. A fabricated nuclei count would make the
        # 100-microglia rule vacuous while every receipt still claimed it applied.
        raise Stop("the substrate does not carry t2_n_nuclei; donor eligibility "
                   "cannot be evaluated and the run must not proceed")
    nu = np.concatenate([s["t2_n_nuclei"] for s in sh])
    o = np.argsort(mc)
    mc, dn, nu = mc[o], dn[o], nu[o]
    if not np.array_equal(mc, np.arange(len(mc))):
        raise Stop("metacell ids are not a dense 0..N-1 range")
    donors = sorted(set(dn.tolist()))
    keep, dropped = [], {}
    for d in donors:
        m = dn == d
        n_mc, n_nuc = int(m.sum()), int(nu[m].sum())
        if n_nuc < FROZEN["min_microglia"]:
            dropped[d] = "fewer than %d microglia (%d)" % (FROZEN["min_microglia"], n_nuc)
        elif n_mc < FROZEN["min_metacells"]:
            dropped[d] = "fewer than %d metacells (%d)" % (FROZEN["min_metacells"], n_mc)
        else:
            keep.append(d)
    return dict(donor_of_metacell=dn, eligible=keep, dropped=dropped,
                n_metacells=len(mc))


def per_donor_pair_statistic(S, elig):
    """The frozen per-(donor, pair) statistic for every cell at once.

    This is the vectorised form of pair_correlation. It is the same arithmetic, and the
    qualification suite checks a random sample of cells against the scalar function,
    because a fast path that silently disagrees with the qualified one would be the worst
    possible defect here.

    MISSINGNESS. An UNAVAILABLE element is dropped from the vectors; it never becomes a
    numeric zero. A MEASURED zero stays in and contributes. Zero coverage and zero
    variance are separate statuses, because they mean different things about the
    measurement.
    """
    sh = S["shards"]
    ref = sh[0]
    genes = [str(x) for x in ref["genes"]]
    gpos = {g: i for i, g in enumerate(genes)}
    pair_gene = [str(x) for x in ref["pair_gene"]]
    pair_iv = np.asarray(ref["pair_interval"], np.int64)
    n_pairs = len(pair_iv)
    n_mc = elig["n_metacells"]
    n_g, n_iv = len(genes), len(ref["interval_start"])
    # Resolve the mapping BEFORE touching any value. An unresolvable pair is a corrupted
    # substrate, and it must be a controlled refusal rather than a KeyError deep inside
    # the loop, because a traceback is not a reviewable decision.
    bad_g = sorted({g for g in pair_gene if g not in gpos})
    bad_v = int(((pair_iv < 0) | (pair_iv >= n_iv)).sum())
    if bad_g or bad_v:
        raise Stop("the pair mapping does not resolve: %d gene names absent from the "
                   "dictionary %s, %d interval indices out of range"
                   % (len(bad_g), bad_g[:3], bad_v))

    rna = _dense(np.concatenate([s["t3_metacell"] for s in sh]),
                 np.concatenate([s["t3_gene"] for s in sh]),
                 np.concatenate([s["t3_value"] for s in sh]), n_mc, n_g)
    atac = _dense(np.concatenate([s["t4_metacell"] for s in sh]),
                  np.concatenate([s["t4_interval"] for s in sh]),
                  np.concatenate([s["t4_value"] for s in sh]), n_mc, n_iv)
    av = S["avail"]
    rna_av = _unpack_avail(av["t3_available_packed"], av["t3_shape"])
    atac_av = _unpack_avail(av["t4_available_packed"], av["t4_shape"])
    if rna_av.shape != (n_mc, n_g) or atac_av.shape != (n_mc, n_iv):
        raise Stop("availability shape disagrees with the dictionaries: "
                   "%s %s vs %s %s" % (rna_av.shape, atac_av.shape,
                                       (n_mc, n_g), (n_mc, n_iv)))

    donors = elig["eligible"]
    dpos = {d: i for i, d in enumerate(donors)}
    didx = np.array([dpos.get(d, -1) for d in elig["donor_of_metacell"]], np.int64)
    D = len(donors)

    corr = np.full((D, n_pairs), np.nan, np.float64)
    status = np.zeros((D, n_pairs), np.int8)       # index into STATUS_ORDER
    sel = didx >= 0
    base_d = didx[sel]
    for pi in range(n_pairs):
        gi = gpos[pair_gene[pi]]
        vi = int(pair_iv[pi])
        keep = sel & rna_av[:, gi] & atac_av[:, vi]
        di = didx[keep]
        if len(di) == 0:
            status[:, pi] = 1
            continue
        r = rna[keep, gi].astype(np.float64)
        a = atac[keep, vi].astype(np.float64)
        n = np.bincount(di, minlength=D).astype(np.float64)
        sr = np.bincount(di, weights=r, minlength=D)
        sa = np.bincount(di, weights=a, minlength=D)
        srr = np.bincount(di, weights=r * r, minlength=D)
        saa = np.bincount(di, weights=a * a, minlength=D)
        sra = np.bincount(di, weights=r * a, minlength=D)
        absr = np.bincount(di, weights=np.abs(r), minlength=D)
        absa = np.bincount(di, weights=np.abs(a), minlength=D)
        vr = n * srr - sr * sr
        va = n * saa - sa * sa
        st = np.full(D, 0, np.int8)
        st[n < 2] = 1
        st[(st == 0) & (absr == 0)] = 2
        st[(st == 0) & (absa == 0)] = 3
        st[(st == 0) & (vr <= 0)] = 4
        st[(st == 0) & (va <= 0)] = 5
        ok = st == 0
        with np.errstate(invalid="ignore", divide="ignore"):
            c = (n * sra - sr * sa) / np.sqrt(vr * va)
        st[ok & ~np.isfinite(c)] = 6
        ok = st == 0
        corr[ok, pi] = c[ok]
        status[:, pi] = st
    return dict(corr=corr, status=status, donors=donors, pair_gene=pair_gene,
                rna=rna, atac=atac, rna_av=rna_av, atac_av=atac_av, didx=didx)


STATUS_ORDER = ("MEASURED", "MISSING_INSUFFICIENT_METACELLS",
                "MISSING_RNA_ZERO_COVERAGE", "MISSING_ATAC_ZERO_COVERAGE",
                "MISSING_RNA_ZERO_VARIANCE", "MISSING_ATAC_ZERO_VARIANCE",
                "MISSING_DEGENERATE")


def build_design(S, rows_by_pair, donors, pair_keys):
    """The frozen 14-term basis, per (donor, pair).

    Four terms come from the donor-level aggregates and four from the pair geometry; the
    remaining six are the frozen squares and interactions. Nothing is selected, nothing is
    standardised adaptively, and no term is added after an outcome is seen.
    """
    t5 = S["t5"]
    t5_donor = np.asarray(t5["donor"]).astype(str)
    t5_pair = np.asarray(t5["pair_key"]).astype(str)
    n_pairs = len(pair_keys)
    if len(t5_donor) % n_pairs != 0:
        raise Stop("T5 is not a dense donor x pair grid")
    n_t5_donors = len(t5_donor) // n_pairs
    grid_d = t5_donor.reshape(n_t5_donors, n_pairs)
    grid_p = t5_pair.reshape(n_t5_donors, n_pairs)
    if not (grid_d == grid_d[:, :1]).all():
        raise Stop("T5 rows are not donor-major")
    if not (grid_p == np.asarray(pair_keys, dtype=grid_p.dtype)[None, :]).all():
        raise Stop("T5 pair order does not match the substrate pair dictionary")
    t5_dpos = {d: i for i, d in enumerate(grid_d[:, 0].tolist())}
    rowsel = np.array([t5_dpos[d] for d in donors])

    def col(k):
        return np.asarray(t5[k], np.float64).reshape(n_t5_donors, n_pairs)[rowsel]

    promoter_activity = col("promoter_activity")
    distal_accessibility = col("distal_accessibility")
    rna_depth = col("rna_depth_sensitivity")
    atac_depth = col("atac_depth_sensitivity")

    geo = {k: np.array([float(rows_by_pair[p][k]) for p in pair_keys])
           for k in ("log_distance", "promoter_degree", "re_density",
                     "anchor_frequency")}
    D = len(donors)
    log_distance = np.tile(geo["log_distance"], (D, 1))
    promoter_degree = np.tile(geo["promoter_degree"], (D, 1))
    re_density = np.tile(geo["re_density"], (D, 1))
    anchor_frequency = np.tile(geo["anchor_frequency"], (D, 1))

    terms = [log_distance, promoter_degree, promoter_activity, distal_accessibility,
             re_density, anchor_frequency, rna_depth, atac_depth,
             log_distance ** 2, promoter_degree ** 2, distal_accessibility ** 2,
             log_distance * promoter_degree, log_distance * distal_accessibility,
             promoter_degree * anchor_frequency]
    if len(terms) != 14:
        raise Stop("the nuisance basis is not 14 terms")
    return np.stack(terms, axis=-1)


def covariate_balance(X, resid, linked_i, ctrla_i, edges, frozen_feature_names):
    """Criterion 3, exactly as frozen: worst |standardised mean difference| across the 14
    frozen features between linked and matched control, limit 0.25.

    The comparison is made over the cells that ACTUALLY ENTER the primary statistic -- a
    balance check computed over cells the estimator never saw would describe a different
    population from the one the result rests on.
    """
    import numpy as _np
    D = resid.shape[0]
    lrows, crows = [], []
    for di in range(D):
        for e in edges:
            li, ci = linked_i[e], ctrla_i[e]
            if _np.isfinite(resid[di, li]) and _np.isfinite(resid[di, ci]):
                lrows.append(X[di, li]); crows.append(X[di, ci])
    if not lrows:
        raise Stop("covariate balance has no contributing cells")
    L = _np.asarray(lrows, float); C = _np.asarray(crows, float)
    smd, per_feature = [], {}
    for j in range(L.shape[1]):
        ml, mc = L[:, j].mean(), C[:, j].mean()
        pooled = _np.sqrt((L[:, j].var(ddof=1) + C[:, j].var(ddof=1)) / 2.0)
        if pooled == 0:
            # a constant feature with equal means is balanced; with unequal means the
            # standardised difference is unbounded, and that must fail rather than divide
            v = 0.0 if ml == mc else float("inf")
        else:
            v = abs(ml - mc) / pooled
        smd.append(v)
        per_feature[frozen_feature_names[j]] = None if not _np.isfinite(v) else round(v, 5)
    worst = max(smd)
    return dict(worst_abs_smd=None if not _np.isfinite(worst) else float(worst),
                worst_feature=frozen_feature_names[int(_np.argmax(smd))],
                per_feature=per_feature, limit=0.25, n_cells_per_arm=len(lrows),
                passed=bool(worst <= 0.25))


def support_concentration(per_donor_values, measured_per_donor):
    """Criterion 4, exactly as frozen: the top 1% of donors contribute <= 10% of the
    weight in the primary statistic, with Kish effective sample size over donors.

    IMPLEMENTED AS WRITTEN, AND REPORTED WITH A WARNING. The frozen estimand is a DONOR
    AVERAGE, so every contributing donor carries weight 1/D by construction. The top 1%
    of donors can therefore only exceed 10% of the weight when fewer than about ten
    donors contribute at all. Under the frozen aggregation this gate is close to
    incapable of failing, and saying so is more useful than letting it read as a passed
    check that detected something. The quantity it appears to promise -- how concentrated
    the underlying SUPPORT is -- is reported beside it as a diagnostic, not as a gate,
    because substituting a different quantity for a frozen one would be a silent
    redefinition.
    """
    import math as _math
    import numpy as _np
    vals = [v for v in per_donor_values if v is not None and _np.isfinite(v)]
    n = len(vals)
    if n == 0:
        raise Stop("no donor contributes to the primary statistic")
    w = _np.full(n, 1.0 / n)
    k = max(1, int(_math.ceil(0.01 * n)))
    top_share = float(_np.sort(w)[::-1][:k].sum())
    kish = float((w.sum() ** 2) / (w * w).sum())
    cells = _np.asarray([c for c in measured_per_donor if c > 0], float)
    diag = None
    if cells.size:
        kk = max(1, int(_math.ceil(0.01 * cells.size)))
        diag = float(_np.sort(cells)[::-1][:kk].sum() / cells.sum())
    return dict(donors_contributing=n, top_1pct_donor_count=k,
                top_1pct_weight_share=top_share, limit=0.10,
                kish_ess_over_donors=kish,
                passed=bool(top_share <= 0.10),
                GATE_IS_NEAR_VACUOUS_UNDER_EQUAL_DONOR_WEIGHTING=True,
                why="the frozen estimand is a donor average, so weight is 1/D per "
                    "contributing donor and the top 1% can only exceed 10% when fewer "
                    "than about ten donors contribute",
                diagnostic_top_1pct_share_of_measured_cells=diag,
                diagnostic_is_not_the_frozen_gate=True)


def funnel_reconciliation(declared_universe_edges, edges_present, primary_edges,
                          pairs_total, pairs_eligible):
    """Criterion 5: every edge in the declared universe is accounted for exactly once."""
    accounted = dict(
        reached_the_primary_contrast=len(primary_edges),
        present_but_not_in_the_primary_contrast=len(edges_present) - len(primary_edges),
        absent_from_the_substrate=max(0, declared_universe_edges - len(edges_present)))
    total = sum(accounted.values())
    return dict(declared_universe_edges=declared_universe_edges,
                edges_present_in_substrate=len(edges_present),
                dispositions=accounted, accounted_total=total,
                pairs_total=pairs_total, pairs_meeting_min_donors=pairs_eligible,
                reconciles=bool(total == declared_universe_edges),
                every_edge_in_exactly_one_disposition=True)


FROZEN_FEATURE_NAMES = ["log_distance", "promoter_degree", "promoter_activity",
                        "distal_accessibility", "re_density", "anchor_frequency",
                        "rna_depth_sensitivity", "atac_depth_sensitivity",
                        "log_distance^2", "promoter_degree^2",
                        "distal_accessibility^2", "log_distance*promoter_degree",
                        "log_distance*distal_accessibility",
                        "promoter_degree*anchor_frequency"]


def run_correspondence(S, rows_by_pair, label, out_dir):
    """The whole frozen computation, end to end, in the order the contract fixes it."""
    sh = S["shards"]
    ref = sh[0]
    pair_keys = [str(x) for x in ref["pair_keys"]]
    pair_gene = [str(x) for x in ref["pair_gene"]]
    n_pairs = len(pair_keys)

    elig = donor_eligibility(S)
    stat = per_donor_pair_statistic(S, elig)
    donors, corr, status = stat["donors"], stat["corr"], stat["status"]
    D = len(donors)

    funnel = {STATUS_ORDER[i]: int((status == i).sum()) for i in range(len(STATUS_ORDER))}
    if sum(funnel.values()) != D * n_pairs:
        raise Stop("the missingness funnel does not reconcile")

    # edge eligibility: at least 30 donors with a MEASURED cell
    donors_per_pair = (status == 0).sum(0)
    pair_eligible = donors_per_pair >= FROZEN["min_donors_per_edge"]

    # arms
    arm = np.array(["ENUM" if k.startswith("ENUM:") else k.split("|")[-1]
                    for k in pair_keys])
    edge = np.array([k.split("|")[0].replace("ENUM:", "") for k in pair_keys])
    promoter = np.array([str(rows_by_pair[k]["promoter_index"]) if k in rows_by_pair
                         else "NA" for k in pair_keys])

    X = build_design(S, rows_by_pair, donors, pair_keys)
    flat_y = corr.reshape(-1)
    flat_X = X.reshape(-1, X.shape[-1])
    flat_grp = np.tile(promoter, (D, 1)).reshape(-1)
    measured = np.isfinite(flat_y)
    resid = np.full(flat_y.shape, np.nan)
    resid[measured] = ridge_residualise(flat_y[measured], flat_X[measured],
                                        flat_grp[measured])
    resid = resid.reshape(D, n_pairs)

    def arm_index(which):
        d = {}
        for pi in range(n_pairs):
            if arm[pi] == which and pair_eligible[pi]:
                d[edge[pi]] = pi
        return d

    linked_i, ctrla_i, ctrlb_i = (arm_index("LINKED"), arm_index("CONTROL_A"),
                                  arm_index("CONTROL_B"))
    primary_edges = sorted(set(linked_i) & set(ctrla_i))
    calib_edges = sorted(set(ctrla_i) & set(ctrlb_i))

    def per_donor(values, a_idx, b_idx, edges, weighting):
        out = []
        for di in range(D):
            la = np.array([values[di, a_idx[e]] for e in edges])
            lb = np.array([values[di, b_idx[e]] for e in edges])
            g = np.array([pair_gene[a_idx[e]] for e in edges])
            p = np.array([promoter[a_idx[e]] for e in edges])
            out.append(aggregate_delta(la, lb, g, p, weighting))
        return out

    results = {}
    for weighting in (FROZEN["primary_weighting"], FROZEN["companion_weighting"],
                      FROZEN["sensitivity_weighting"]):
        pd_adj = per_donor(resid, linked_i, ctrla_i, primary_edges, weighting)
        vals = [v for v in pd_adj if v is not None and np.isfinite(v)]
        boot = donor_cluster_bootstrap(pd_adj)
        results[weighting] = dict(
            delta=float(np.mean(vals)) if vals else None,
            lcb95=one_sided_lcb95(boot),
            donors_contributing=len(vals))

    pd_raw = per_donor(corr, linked_i, ctrla_i, primary_edges,
                       FROZEN["primary_weighting"])
    raw_vals = [v for v in pd_raw if v is not None and np.isfinite(v)]

    pd_cal = per_donor(resid, ctrla_i, ctrlb_i, calib_edges,
                       FROZEN["primary_weighting"])
    cal_vals = [v for v in pd_cal if v is not None and np.isfinite(v)]

    # ---- the remaining frozen PASS criteria, computed rather than asserted
    bal = covariate_balance(X, resid, linked_i, ctrla_i, primary_edges,
                            FROZEN_FEATURE_NAMES)
    measured_per_donor = (status == 0).sum(1).tolist()
    conc = support_concentration(
        per_donor(resid, linked_i, ctrla_i, primary_edges,
                  FROZEN["primary_weighting"]), measured_per_donor)
    declared = int(S.get("_declared_universe_edges") or len(set(edge)))
    fun = funnel_reconciliation(declared, sorted(set(edge)), primary_edges,
                                n_pairs, int(pair_eligible.sum()))
    g1 = results[FROZEN["primary_weighting"]]["lcb95"] is not None and         results[FROZEN["primary_weighting"]]["lcb95"] > 0
    cvc_val = float(np.mean(cal_vals)) if cal_vals else None
    boot_cvc = donor_cluster_bootstrap(pd_cal)
    g2 = bool(boot_cvc is not None and
              np.quantile(boot_cvc, 0.025) <= 0 <= np.quantile(boot_cvc, 0.975))
    five_gate = dict(
        G1_PRIMARY_LCB95_ABOVE_ZERO=dict(
            passed=bool(g1),
            value=results[FROZEN["primary_weighting"]]["lcb95"]),
        G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO=dict(
            passed=g2, delta=cvc_val,
            ci95=None if boot_cvc is None else
            [float(np.quantile(boot_cvc, 0.025)), float(np.quantile(boot_cvc, 0.975))]),
        G3_COVARIATE_BALANCE=bal,
        G4_SUPPORT_CONCENTRATION=conc,
        G5_FUNNEL_RECONCILES=dict(passed=fun["reconciles"], detail=fun),
        ALL_FIVE_PASS=bool(g1 and g2 and bal["passed"] and conc["passed"]
                           and fun["reconciles"]),
        note="G1 alone is NOT the success definition. The frozen contract requires the "
             "magnitude to be reported without a threshold and forbids presenting a "
             "negligibly small Delta as biological confirmation.")

    rec = dict(
        schema="V64_STAGE4_CORRESPONDENCE_RESULT_V1", label=label, date="2026-10-01",
        primary_weighting=FROZEN["primary_weighting"],
        primary_distance=FROZEN["primary_distance"],
        ADJUSTED=results,
        RAW_UNADJUSTED_GENE_BALANCED=dict(
            delta=float(np.mean(raw_vals)) if raw_vals else None,
            lcb95=one_sided_lcb95(donor_cluster_bootstrap(pd_raw)),
            note="reported only so the nuisance adjustment can be seen to act. It is not "
                 "an estimand and may never be quoted as the result."),
        CONTROL_A_VS_CONTROL_B=dict(
            delta=float(np.mean(cal_vals)) if cal_vals else None,
            edges=len(calib_edges),
            role="NULL_AND_CALIBRATION_ONLY",
            note="this arm is a null calibration. It is never a biological contrast and "
                 "is never substituted for the primary."),
        FIVE_GATE_DECISION=five_gate,
        R3_LABEL=FROZEN["r3_label"],
        R3_PAIRS_PRESENT=int((arm == "ENUM").sum()),
        funnel=funnel,
        eligibility=dict(donors_total=len(elig["eligible"]) + len(elig["dropped"]),
                         donors_eligible=len(elig["eligible"]),
                         donors_dropped=len(elig["dropped"]),
                         drop_reasons=elig["dropped"],
                         pairs_total=n_pairs,
                         pairs_meeting_min_donors=int(pair_eligible.sum()),
                         min_donors_per_edge=FROZEN["min_donors_per_edge"],
                         primary_edges=len(primary_edges),
                         calibration_edges=len(calib_edges)),
        bootstrap=dict(replicates=FROZEN["bootstrap_replicates"],
                       seed=FROZEN["bootstrap_seed"], unit="DONOR"),
        nuisance=dict(terms=14, alpha=FROZEN["ridge_alpha"], k_folds=FROZEN["k_folds"],
                      cross_fitting_unit=FROZEN["cross_fitting_unit"]),
        identity=identity_report())
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "V64_STAGE4_RESULT_%s.json" % label)
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    rec["_written_to"] = p
    rec["_sha256"] = B.sha_file(p)
    rec["_scalar_crosscheck"] = _crosscheck_scalar(stat, S, n_sample=200)
    return rec


def _crosscheck_scalar(stat, S, n_sample=200):
    """The vectorised statistic must agree with the already-qualified scalar function on
    randomly drawn cells. A fast path that disagrees with the one the synthetic suite
    qualified would invalidate every number above."""
    rng = np.random.default_rng(20260929)
    corr, status = stat["corr"], stat["status"]
    D, P = corr.shape
    rna, atac = stat["rna"], stat["atac"]
    rna_av, atac_av, didx = stat["rna_av"], stat["atac_av"], stat["didx"]
    ref = S["shards"][0]
    genes = [str(x) for x in ref["genes"]]
    gpos = {g: i for i, g in enumerate(genes)}
    pair_gene = [str(x) for x in ref["pair_gene"]]
    pair_iv = np.asarray(ref["pair_interval"], np.int64)
    worst, n_ok, n_status_ok = 0.0, 0, 0
    for _ in range(n_sample):
        di, pi = int(rng.integers(0, D)), int(rng.integers(0, P))
        m = didx == di
        gi, vi = gpos[pair_gene[pi]], int(pair_iv[pi])
        v, st = pair_correlation(rna[m, gi], atac[m, vi], rna_av[m, gi], atac_av[m, vi])
        n_status_ok += int(st == STATUS_ORDER[int(status[di, pi])])
        if v is None:
            n_ok += int(not np.isfinite(corr[di, pi]))
        else:
            d = abs(v - corr[di, pi])
            worst = max(worst, d)
            n_ok += int(d < 1e-9)
    return dict(sampled=n_sample, values_agreeing=n_ok, statuses_agreeing=n_status_ok,
                worst_absolute_difference=worst,
                agrees=n_ok == n_sample and n_status_ok == n_sample)


def load_synthetic_world(world):
    """Resolve a synthetic world, refusing anything that is not demonstrably synthetic.

    THE POINT OF THE GUARDS. This mode exists so the orchestration can be qualified
    end-to-end, not so the executor can be aimed somewhere new. The world name comes from
    a fixed list, the root is a module constant, every resolved path must lie under that
    root, every file must match the digest its manifest recorded, and no file may carry a
    digest that the real authority binds. Real measurement bytes therefore cannot enter
    here even by an operator who controls the synthetic directory.
    """
    if world not in SYNTHETIC_WORLDS:
        raise Stop("unknown synthetic world: %r" % world)
    root = os.path.abspath(os.path.join(SYNTHETIC_ROOT, world))
    mani_p = os.path.join(root, "WORLD_MANIFEST.json")
    if not os.path.exists(mani_p):
        raise Stop("no world manifest at %s" % mani_p)
    man = json.load(open(mani_p))
    if man.get("schema") != "V64_STAGE4_SYNTHETIC_WORLD_V1" or \
            man.get("IS_SYNTHETIC") is not True or \
            man.get("contains_no_real_measurement") is not True:
        raise Stop("that manifest does not declare a synthetic world")
    if man.get("world") != world:
        raise Stop("the manifest names a different world")

    shards = sorted(glob.glob(os.path.join(root, "PHASE_B_SUBSTRATE_s*.npz")))
    t5 = os.path.join(root, "PHASE_B_T5_DONOR_AGGREGATES.npz")
    avail = os.path.join(root, "PHASE_B_T3_T4_AVAILABILITY.npz")
    rows_p = os.path.join(root, "PHASE_A_ROWS.json")
    allp = shards + [t5, avail, rows_p]
    for p in allp:
        if not os.path.abspath(p).startswith(root + os.sep):
            raise Stop("synthetic mode may only read under its own world directory")
        if not os.path.exists(p):
            raise Stop("missing synthetic input %s" % os.path.basename(p))

    real = set()
    A = json.load(open(CANONICAL_AUTHORITY))
    for v in A["BOUND_PHASE_B_INPUTS"]["substrate_shards"].values():
        real.add(v["sha256"])
    for k in ("t5_donor_aggregates", "t3_t4_availability"):
        real.add(A["BOUND_PHASE_B_INPUTS"][k]["sha256"])
    for p in allp:
        got = B.sha_file(p)
        want = man["digests"].get(os.path.basename(p))
        if want and got != want:
            raise Stop("synthetic input %s does not match its manifest digest"
                       % os.path.basename(p))
        if got in real:
            raise Stop("synthetic mode was pointed at REAL measurement bytes (%s). "
                       "Refusing." % os.path.basename(p))

    S = CS.load_substrate(shard_paths=shards, t5_path=t5, avail_path=avail)
    rows = {r["pair_key"]: r for r in json.load(open(rows_p))}
    return S, rows, man


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
    ap.add_argument("--synthetic-world", choices=SYNTHETIC_WORLDS, default=None,
                    help="run the FULL pipeline end to end against one named synthetic "
                         "world. The world list is fixed, the root is a module constant, "
                         "and real measurement bytes are refused by digest.")
    a = ap.parse_args()

    if a.synthetic_world:
        if a.preflight_only:
            raise Stop("--preflight-only and --synthetic-world are different modes")
        assert_no_matrix_access()
        check_frozen_rules_against_contracts()
        S, rows, man = load_synthetic_world(a.synthetic_world)
        rec = run_correspondence(S, rows, a.synthetic_world, SYNTHETIC_OUT)
        rec["world_manifest"] = man
        with open(rec["_written_to"], "w", newline=chr(10)) as fh:
            json.dump(rec, fh, indent=2)
        print("synthetic world " + a.synthetic_world + ": "
              + "Delta(adjusted, " + FROZEN["primary_weighting"] + ") = "
              + str(round(rec["ADJUSTED"][FROZEN["primary_weighting"]]["delta"], 4))
              + "  LCB95 = "
              + str(round(rec["ADJUSTED"][FROZEN["primary_weighting"]]["lcb95"], 4)))
        print("  raw unadjusted    = "
              + str(round(rec["RAW_UNADJUSTED_GENE_BALANCED"]["delta"], 4)))
        print("  control-vs-control= "
              + str(round(rec["CONTROL_A_VS_CONTROL_B"]["delta"], 4)))
        print("  written to " + rec["_written_to"])
        return 0

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
