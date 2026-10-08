#!/usr/bin/env python3
"""Measurement-context shortcut audit (V77 Phase 5). DIAGNOSTIC ONLY.

For every proposed lawful context field, and for model-visible fields that carry measurement
structure, ask whether a probe can reconstruct source, study, operator or donor identity from it.

Probes, declared before any run:
  LINEAR  one-vs-rest ridge on standardized features; dual form when features outnumber cells
  KNN     k nearest neighbours: Euclidean on standardized scalars, Hamming on binary patterns
  LOOKUP  exact-key majority vote, discrete fields only
Split: train on even global_cell_index, test on odd. Every probe is rerun on permuted training
labels; a lift no larger than the permutation maximum is indistinguishable from chance.

Risk class per field, a DIAGNOSTIC CONVENTION declared here and not a deciding threshold. It admits
and rejects nothing; the raw lifts are reported so any lane can relabel:
  FORBIDDEN_RAW_IDENTITY_CONTROL  the field is raw identity, by name, whatever the probes say
  HIGH_IDENTITY_PROXY_RISK        some probe recovers source, study or operator with lift >= 0.5
                                  and above its permutation maximum
  CONDITIONAL                     some probe beats its permutation maximum for some target, but no
                                  identity target reaches 0.5: the risk depends on the probe class
                                  or on the use (donor-only signal lands here)
  LOW_SHORTCUT_RISK               no probe beats its permutation maximum for any target
Lift is balanced accuracy rescaled so chance is 0 and perfect is 1. The class is also reported at
cutoffs 0.25 and 0.75, without choosing between them. Test classes absent from training cannot be
predicted, so lift has a ceiling below 1 when classes are small; the raw-identity controls measure
that ceiling per target, and every field's best lift is also reported as a fraction of it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

KNN_K = 15
RIDGE_REL = 1e-3
N_PERM = 20
PERM_SEED = 20261007
LIFT_CUTOFF = 0.5
SENSITIVITY_CUTOFFS = (0.25, 0.75)
IDENTITY_TARGETS = ("source", "study", "operator")
RAW_IDENTITY_FIELDS = {"source_index", "operator_index", "donor_index", "global_cell_index"}
PROBES = ("LINEAR", "KNN", "LOOKUP")


def study_family(source_name: str) -> str:
    """Sources sharing a study collapse to one family (SEA-AD variants), as in the spillover audit."""
    s = str(source_name)
    return "SEA_AD" if s.lower().replace("-", "_").startswith("sea_ad") else s


# ------------------------------------------------------------------------------------- metrics

def lift_of(y_true: np.ndarray, y_pred: np.ndarray, y_train: np.ndarray | None = None) -> dict:
    classes = np.unique(y_true)
    recalls = [float(np.mean(y_pred[y_true == c] == c)) for c in classes]
    bal = float(np.mean(recalls))
    k = len(classes)
    lift = (bal - 1.0 / k) / (1.0 - 1.0 / k) if k > 1 else 0.0
    out = dict(lift=round(lift, 6), balanced_accuracy=round(bal, 6),
               accuracy=round(float(np.mean(y_true == y_pred)), 6), n_classes_test=int(k))
    if y_train is not None:
        out["n_test_classes_unseen_in_train"] = int(len(set(classes.tolist()) - set(np.unique(y_train).tolist())))
    return out


# -------------------------------------------------------------------------------------- probes

def _prepare(X: np.ndarray, binary: bool, tr: np.ndarray):
    X = np.asarray(X, dtype=np.float64)
    if binary:
        return X - X[tr].mean(0)
    mu, sd = X[tr].mean(0), X[tr].std(0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def _vote(labels: np.ndarray, classes: np.ndarray) -> int:
    counts = np.array([(labels == c).sum() for c in classes])
    return int(classes[int(np.argmax(counts))])


class _Linear:
    """One-vs-rest ridge; lambda = RIDGE_REL * trace(Gram) / n_train, identical in primal and dual."""

    def __init__(self, Z: np.ndarray, tr: np.ndarray, te: np.ndarray):
        Ztr = Z[tr]
        self.dual = Z.shape[1] > len(tr)
        if self.dual:
            G = Ztr @ Ztr.T
            lam = RIDGE_REL * np.trace(G) / len(tr)
            self.solve = np.linalg.cholesky(G + lam * np.eye(len(tr)))
            self.cross = Z[te] @ Ztr.T
        else:
            G = Ztr.T @ Ztr
            lam = RIDGE_REL * max(np.trace(G), 1e-12) / len(tr)
            self.solve = np.linalg.cholesky(G + lam * np.eye(G.shape[0]))
            self.Ztr, self.Zte = Ztr, Z[te]

    def predict(self, ytr: np.ndarray) -> np.ndarray:
        classes = np.unique(ytr)
        Y = (ytr[:, None] == classes[None, :]).astype(np.float64)
        ym = Y.mean(0)
        Yc = Y - ym
        L = self.solve
        if self.dual:
            alpha = np.linalg.solve(L.T, np.linalg.solve(L, Yc))
            S = self.cross @ alpha + ym
        else:
            W = np.linalg.solve(L.T, np.linalg.solve(L, self.Ztr.T @ Yc))
            S = self.Zte @ W + ym
        return classes[np.argmax(S, axis=1)]


class _Knn:
    def __init__(self, Z: np.ndarray, tr: np.ndarray, te: np.ndarray):
        A, B = Z[te], Z[tr]
        d2 = (A * A).sum(1)[:, None] + (B * B).sum(1)[None, :] - 2.0 * (A @ B.T)
        self.nn = np.argsort(d2, axis=1, kind="stable")[:, :KNN_K]

    def predict(self, ytr: np.ndarray) -> np.ndarray:
        classes = np.unique(ytr)
        return np.array([_vote(ytr[row], classes) for row in self.nn])


class _Lookup:
    def __init__(self, keys: np.ndarray, tr: np.ndarray, te: np.ndarray):
        self.ktr, self.kte = keys[tr], keys[te]

    def predict(self, ytr: np.ndarray) -> np.ndarray:
        classes = np.unique(ytr)
        default = _vote(ytr, classes)
        table = {}
        for k in np.unique(self.ktr):
            table[k] = _vote(ytr[self.ktr == k], classes)
        return np.array([table.get(k, default) for k in self.kte])


def _keys(X: np.ndarray) -> np.ndarray:
    X = np.ascontiguousarray(np.asarray(X))
    return np.array([hashlib.sha256(r.tobytes()).hexdigest()[:24] for r in X])


def audit_field(name: str, field: dict, targets: dict, global_cell_index: np.ndarray) -> dict:
    """Run every probe for one field against every target, with the permutation null."""
    gci = np.asarray(global_cell_index)
    tr, te = np.flatnonzero(gci % 2 == 0), np.flatnonzero(gci % 2 == 1)
    X = np.asarray(field["X"])
    Z = _prepare(X, bool(field.get("binary")), tr)
    machines = {"LINEAR": _Linear(Z, tr, te), "KNN": _Knn(Z, tr, te)}
    if field.get("discrete"):
        machines["LOOKUP"] = _Lookup(_keys(X), tr, te)
    probes = {}
    for pname, m in machines.items():
        probes[pname] = {}
        for tname, y in targets.items():
            y = np.asarray(y)
            obs = lift_of(y[te], m.predict(y[tr]), y[tr])
            rng = np.random.default_rng([PERM_SEED, PROBES.index(pname), sorted(targets).index(tname)])
            null = [lift_of(y[te], m.predict(rng.permutation(y[tr])))["lift"] for _ in range(N_PERM)]
            obs.update(null_max_lift=round(float(max(null)), 6), null_mean_lift=round(float(np.mean(null)), 6))
            obs["beats_null"] = bool(obs["lift"] > obs["null_max_lift"])
            probes[pname][tname] = obs
    out = dict(field=name, visibility=field.get("visibility"), discrete=bool(field.get("discrete")),
               binary=bool(field.get("binary")), n_features=int(X.shape[1]), probes=probes)
    out["risk_class"] = risk_class(name, probes, LIFT_CUTOFF)
    out["risk_class_at_cutoff"] = {str(c): risk_class(name, probes, c) for c in SENSITIVITY_CUTOFFS}
    return out


def risk_class(name: str, probes: dict, cutoff: float) -> str:
    if name in RAW_IDENTITY_FIELDS:
        return "FORBIDDEN_RAW_IDENTITY_CONTROL"
    cells = [(t, r) for p in probes.values() for t, r in p.items()]
    if any(t in IDENTITY_TARGETS and r["beats_null"] and r["lift"] >= cutoff for t, r in cells):
        return "HIGH_IDENTITY_PROXY_RISK"
    if any(r["beats_null"] for _, r in cells):
        return "CONDITIONAL"
    return "LOW_SHORTCUT_RISK"


# ------------------------------------------------------------------------- fields from a world

def principal_components(student: np.ndarray, k: int) -> np.ndarray:
    """The S157 scorer's unsupervised components, kept as a reference row, not a context field."""
    X = student.astype(np.float64)
    sd = X.std(0)
    keep = sd > 0
    Zs = (X[:, keep] - X[:, keep].mean(0)) / sd[keep]
    w, V = np.linalg.eigh(Zs @ Zs.T)
    idx = np.argsort(w)[::-1][:k]
    return V[:, idx] * np.sqrt(np.maximum(w[idx], 0.0))


def fields_from_conversion(conv) -> dict:
    oc, mb = conv.operator_context, conv.model
    mm = np.asarray(mb.measurement_mask, dtype=bool)
    ev = mm & ~np.asarray(mb.hidden_target_mask, dtype=bool)
    zeros = (ev & (mb.student_expression == 0)).sum(1)
    lib = np.log1p(oc.visible_library_size.astype(np.float64))[:, None]
    nm = oc.n_measured.astype(np.float64)[:, None]
    return {
        "visible_library_size": dict(X=lib, discrete=False, visibility="LAWFUL_OPERATOR_CONTEXT"),
        "n_measured": dict(X=nm, discrete=True, visibility="LAWFUL_OPERATOR_CONTEXT"),
        "depth_and_support": dict(X=np.hstack([lib, nm]), discrete=False, visibility="LAWFUL_OPERATOR_CONTEXT"),
        "hidden_target_count": dict(X=mb.hidden_target_mask.sum(1).astype(np.float64)[:, None], discrete=True,
                                    visibility="MODEL_VISIBLE (count of the artificial training mask)"),
        "measured_zero_fraction": dict(X=(zeros / np.maximum(ev.sum(1), 1)).astype(np.float64)[:, None],
                                       discrete=False, visibility="MODEL_VISIBLE (derived from evidence)"),
        "support_pattern": dict(X=mm, discrete=True, binary=True,
                                visibility="MODEL_VISIBLE (measurement mask; required by measurement semantics)"),
        "source_index": dict(X=oc.source_index.astype(np.float64)[:, None], discrete=True,
                             visibility="RAW IDENTITY (exploratory positive control)"),
        "operator_index": dict(X=oc.operator_index.astype(np.float64)[:, None], discrete=True,
                               visibility="RAW IDENTITY (exploratory positive control)"),
        "REFERENCE_rna_components": dict(X=principal_components(mb.student_expression, 20), discrete=False,
                                         visibility="REFERENCE: the RNA evidence itself, not a context field"),
    }


def targets_from_conversion(conv) -> dict:
    oc = conv.operator_context
    roster = conv.provenance["observation_identity"]["source_roster"]
    fam = np.array([study_family(roster[i]) for i in oc.source_index.astype(int)])
    _, study = np.unique(fam, return_inverse=True)
    return dict(source=oc.source_index.astype(np.int64), study=study.astype(np.int64),
                operator=oc.operator_index.astype(np.int64),
                donor=conv.split_context.donor_index.astype(np.int64))


# ---------------------------------------------------------------------------------------- main

SEVERITY = ["LOW_SHORTCUT_RISK", "CONDITIONAL", "HIGH_IDENTITY_PROXY_RISK", "FORBIDDEN_RAW_IDENTITY_CONTROL"]


def best_lift(result: dict, target: str) -> float:
    return max(p[target]["lift"] for p in result["probes"].values())


def summarize(worlds: dict) -> dict:
    """Most severe class per field over the worlds, and each identity target's best lift beside the
    ceiling that the raw-identity controls reach in the same world."""
    out = {}
    names = list(next(iter(worlds.values()))["results"])
    for name in names:
        classes = [w["results"][name]["risk_class"] for w in worlds.values()]
        ref = name.startswith("REFERENCE")
        entry = dict(risk_class="REFERENCE_NOT_A_CONTEXT_FIELD" if ref else max(classes, key=SEVERITY.index),
                     per_world=dict(zip(worlds, classes)),
                     visibility=next(iter(worlds.values()))["results"][name]["visibility"], identity_lift={})
        for t in IDENTITY_TARGETS:
            best = min(best_lift(w["results"][name], t) for w in worlds.values())
            worst = max(best_lift(w["results"][name], t) for w in worlds.values())
            ceil = min(max(best_lift(w["results"][c], t) for c in RAW_IDENTITY_FIELDS if c in w["results"])
                       for w in worlds.values())
            entry["identity_lift"][t] = dict(best_lift_range=[round(best, 6), round(worst, 6)],
                                             raw_identity_ceiling=round(ceil, 6),
                                             fraction_of_ceiling=round(worst / ceil, 6) if ceil > 0 else None)
        out[name] = entry
    return out


def main() -> None:
    sys.path.insert(0, str(HERE))
    import v77_synthetic_batch_adapter as AD
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds-dir", required=True)
    ap.add_argument("--worlds", default="NULL,BIO,TWIN_EXACT,TWIN_OPERATOR")
    ap.add_argument("--universe", required=True)
    ap.add_argument("--obs-dir", default="FULLSCALE_V2_CANONICAL_sharded")
    ap.add_argument("--hidden-fraction", type=float, default=0.15)
    ap.add_argument("--adapter-seed", type=int, default=20261006)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    git = lambda *x: subprocess.run(["git", *x], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    worlds = {}
    for w in a.worlds.split(","):
        conv = AD.build_from_world(Path(a.worlds_dir) / w, a.obs_dir, universe, a.hidden_fraction, a.adapter_seed)
        F, T = fields_from_conversion(conv), targets_from_conversion(conv)
        res = {name: audit_field(name, f, T, conv.global_cell_index) for name, f in F.items()}
        worlds[w] = dict(n_cells=int(len(conv.global_cell_index)),
                         n_classes={k: int(len(np.unique(v))) for k, v in T.items()},
                         digests={n: getattr(conv, n).digest() for n in ("model", "operator_context", "split_context")},
                         results=res)
        print(w, {n: r["risk_class"] for n, r in res.items()}, flush=True)
    summary = summarize(worlds)
    study_is_source = {w: bool(v["n_classes"]["study"] == v["n_classes"]["source"]) for w, v in worlds.items()}
    rec = dict(
        schema="V77_CONTEXT_SHORTCUT_AUDIT_V1", claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        status="DIAGNOSTIC_ONLY: the risk classes admit and reject nothing; the deciding lane decides",
        realization="truth seed 7302, 2,000 cells: DEVELOPMENT_CALIBRATION",
        declared=dict(split="train even global_cell_index, test odd", probes=list(PROBES), knn_k=KNN_K,
                      ridge_rel=RIDGE_REL, n_perm=N_PERM, perm_seed=PERM_SEED, lift_cutoff=LIFT_CUTOFF,
                      sensitivity_cutoffs=list(SENSITIVITY_CUTOFFS), identity_targets=list(IDENTITY_TARGETS),
                      study_rule="SEA-AD source variants collapse to one study family",
                      worst_class_across_worlds="the summary reports the most severe class over the worlds"),
        summary=summary,
        caveats=[("study equals source in this realization: no source shares a study family" if all(study_is_source.values())
                  else "study differs from source in at least one world"),
                 ("LOW classes describe this synthetic observer only; real context fields need this audit run "
                  "on real data by the real-data lane before any approval"),
                 "operator lifts are bounded by the raw-identity ceiling: small operators cannot be predicted",
                 "donor lifts are small; beating the permutation maximum there is detection, not reconstruction"],
        worlds=worlds, head=git("rev-parse", "HEAD"),
        executor={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                  ("scripts/v77/audit_v77_context_shortcuts.py", "scripts/v77/v77_synthetic_batch_adapter.py")},
        command=" ".join(["python"] + [Path(sys.argv[0]).as_posix()] + sys.argv[1:]),
        wall_seconds=round(time.time() - t0, 1))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: v["risk_class"] for k, v in summary.items()}, indent=1))


if __name__ == "__main__":
    main()
