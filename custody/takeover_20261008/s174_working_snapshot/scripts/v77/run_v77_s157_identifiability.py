#!/usr/bin/env python3
"""S157 paired challenge: biology versus a measurement twin, scored blind, by pre-registered rules.

Claim namespace: V77_SYNTHETIC_WORLD_QUALIFICATION. Pre-registration:
results/v77/V77_S157_PAIRED_CHALLENGE_PREREGISTRATION_V1.json (f36ad6ad). Worlds:
results/v77/V77_S157_CHALLENGE_WORLDS_BUILD_V1.json. ZERO_UPDATE: nothing here trains a model.
The principal components and linear readouts are diagnostic, fit inside this scorer, and are not a
representation candidate.

ORDER, ENFORCED. (1) every world is converted by the canonical adapter; (2) schema identity and the
exact twin's byte identity are checked (RED_3, RED_1); (3) oracle-free features are computed from
model-visible structures only and a digest of all of them is recorded; (4) only then may any oracle
quantity be loaded (challenge spec, latent, module, state, operator set): the unblinding function
refuses without the frozen record and refuses if the features no longer match it (RED_4).

Context arms (pre-registered): ARM1 evidence only; ARM2 log visible library size and n_measured;
ARM3 raw operator and source identity, an EXPLORATORY POSITIVE CONTROL ONLY. ARM2_DEPTH_ONLY and
ARM2_SUPPORT_ONLY split ARM2 into its two descriptors; they were not pre-registered and are labelled
EXPLORATORY_DECOMPOSITION.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import fields
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "v64"))
import v77_synthetic_batch_adapter as AD  # noqa: E402

EXECUTOR_FILES = ("scripts/v77/run_v77_s157_identifiability.py", "scripts/v77/v77_synthetic_batch_adapter.py",
                  "scripts/v77/build_v77_fullscale_rna_observer_v2.py", "scripts/v77/v77_address_universe.py")
PREREG = ROOT / "results" / "v77" / "V77_S157_PAIRED_CHALLENGE_PREREGISTRATION_V1.json"
BUILD = ROOT / "results" / "v77" / "V77_S157_CHALLENGE_WORLDS_BUILD_V1.json"
OBS_DIR = "FULLSCALE_V2_CANONICAL_sharded"
WORLDS = ("NULL", "BIO", "TWIN_EXACT", "TWIN_OPERATOR")
N_PCS, N_BOOT, BOOT_SEED, HIDDEN_FRACTION, ADAPTER_SEED = 20, 200, 20261006, 0.15, 20261006
# Declared before any scoring: identical inputs may differ in the last bits under threaded linear
# algebra, so RED_2 allows 1e-9 absolute and reports exact equality separately; beyond it is a LEAK.
FLOAT_TOLERANCE = 1e-9
PREREGISTERED_ARMS = ("ARM1", "ARM2", "ARM3")
EXPLORATORY_ARMS = ("ARM2_DEPTH_ONLY", "ARM2_SUPPORT_ONLY")


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


# ----------------------------------------------------------------------- model-visible side

def schema_of(conv) -> dict:
    out = {}
    for name in ("model", "operator_context", "split_context", "readout"):
        s = getattr(conv, name)
        out[name] = {f.name: [str(getattr(s, f.name).dtype), list(getattr(s, f.name).shape)] for f in fields(s)}
    return out


def digests_of(conv) -> dict:
    return {name: getattr(conv, name).digest() for name in ("model", "operator_context", "split_context", "readout")}


def principal_components(student: np.ndarray, k: int) -> np.ndarray:
    X = student.astype(np.float64)
    sd = X.std(0)
    keep = sd > 0
    Z = (X[:, keep] - X[:, keep].mean(0)) / sd[keep]
    w, V = np.linalg.eigh(Z @ Z.T)
    idx = np.argsort(w)[::-1][:k]
    S = V[:, idx] * np.sqrt(np.maximum(w[idx], 0.0))
    sgn = np.sign(S[np.argmax(np.abs(S), axis=0), np.arange(S.shape[1])])
    sgn[sgn == 0] = 1.0
    return S * sgn


def one_hot(v: np.ndarray) -> np.ndarray:
    u = np.unique(v)
    return (v[:, None] == u[None, :]).astype(np.float64)


def context_features(conv) -> dict:
    oc = conv.operator_context
    lib = np.log1p(oc.visible_library_size.astype(np.float64))[:, None]
    nm = oc.n_measured.astype(np.float64)[:, None]
    raw = np.hstack([one_hot(oc.operator_index.astype(np.int64)), one_hot(oc.source_index.astype(np.int64))])
    return {"ARM1": None, "ARM2": np.hstack([lib, nm]), "ARM3": raw,
            "ARM2_DEPTH_ONLY": lib, "ARM2_SUPPORT_ONLY": nm}


def frozen_digest(features: dict) -> str:
    h = hashlib.sha256()
    for w in sorted(features):
        for k in sorted(features[w]):
            a = features[w][k]
            if a is None:
                h.update(f"{w}:{k}:None".encode()); continue
            a = np.ascontiguousarray(a)
            h.update(f"{w}:{k}:{a.dtype}:{a.shape}".encode()); h.update(a.tobytes())
    return h.hexdigest()


class Blinding:
    """Refuses any oracle access before the frozen-feature record exists and still matches."""
    def __init__(self):
        self.record = None

    def freeze(self, features: dict) -> dict:
        self.record = dict(frozen_feature_digest=frozen_digest(features), sequence="FROZEN_BEFORE_ANY_ORACLE_ACCESS")
        return self.record

    def unblind(self, world: Path, features: dict, conv) -> dict:
        if self.record is None:
            raise RuntimeError("refusing to unblind: no frozen-feature record exists")
        if frozen_digest(features) != self.record["frozen_feature_digest"]:
            raise RuntimeError("refusing to unblind: features changed after freezing")
        import build_v77_fullscale_rna_observer_v2 as OBS
        spec = OBS.load_challenge(Path(world) / "hidden_truth")
        truth = {}
        for f in sorted((Path(world) / "hidden_truth").glob("TRUTH_*.npz")):
            d = np.load(f, allow_pickle=False)
            for k in ("global_cell_index", "state_index", "operator_index"):
                truth.setdefault(k, []).append(d[k])
        truth = {k: np.concatenate(v)[: len(conv.global_cell_index)] for k, v in truth.items()}
        if not np.array_equal(truth["global_cell_index"], conv.global_cell_index):
            raise RuntimeError("truth and conversion are not aligned")
        build = json.loads(BUILD.read_text())["design"]
        latents = {}
        for kind in ("BIO", "TWIN_OPERATOR"):
            latents[kind] = OBS.challenge_latent(dict(build, kind=kind), truth, conv.global_cell_index, 7302)
        return dict(spec=spec, truth=truth, latents=latents, module=np.asarray(build["module_addresses"]))


# ----------------------------------------------------------------------- scoring

def max_numeric_difference(a, b) -> float:
    if isinstance(a, dict):
        if set(a) != set(b):
            return float("inf")
        return max([max_numeric_difference(a[k], b[k]) for k in a] or [0.0])
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return float("inf")
        return max([max_numeric_difference(x, y) for x, y in zip(a, b)] or [0.0])
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if a != a and b != b:
            return 0.0
        return abs(float(a) - float(b))
    return 0.0 if a == b else float("inf")


def _fit(X, y):
    X1 = np.c_[np.ones(len(X)), X]
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def _pred(X, b):
    return np.c_[np.ones(len(X)), X] @ b


def _r2(y, yhat):
    ss = ((y - y.mean()) ** 2).sum()
    return float(1.0 - ((y - yhat) ** 2).sum() / ss) if ss > 0 else float("nan")


def _boot(y, yhat):
    """Fixed resampling indices for every statistic, independent of call order, so identical data
    always yield identical intervals (a shared stream would separate an exact twin spuriously)."""
    rng = np.random.default_rng(BOOT_SEED)
    n = len(y)
    vals = [_r2(y[i], yhat[i]) for i in (rng.integers(0, n, n) for _ in range(N_BOOT))]
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]


def recoverability(F, C, y, tr, te):
    """Residualize features on context (fit on train), predict the latent from residuals."""
    if C is None:
        mu = F[tr].mean(0)
        Rtr, Rte = F[tr] - mu, F[te] - mu
    else:
        bC = _fit(C[tr], F[tr])
        Rtr, Rte = F[tr] - _pred(C[tr], bC), F[te] - _pred(C[te], bC)
    yhat = _pred(Rte, _fit(Rtr, y[tr]))
    return dict(r2=_r2(y[te], yhat), ci95=_boot(y[te], yhat))


def context_share(f, C, tr, te):
    if C is None:
        return None
    fhat = _pred(C[te], _fit(C[tr], f[tr]))
    return dict(r2=_r2(f[te], fhat), ci95=_boot(f[te], fhat))


def identity_leakage(C, op, tr, te):
    if C is None:
        return dict(mean_operator_indicator_r2=0.0, operators_scored=0)
    vals = []
    for o in np.unique(op):
        if (op == o).sum() < 10:
            continue
        ind = (op == o).astype(np.float64)
        vals.append(_r2(ind[te], _pred(C[te], _fit(C[tr], ind[tr]))))
    return dict(mean_operator_indicator_r2=float(np.mean(vals)), operators_scored=len(vals))


def support_lookup_identification(nm, op, tr, te):
    seen = {}
    for v, o in zip(nm[tr], op[tr]):
        seen.setdefault(int(v), set()).add(int(o))
    ok = [seen.get(int(v)) == {int(o)} for v, o in zip(nm[te], op[te])]
    return float(np.mean(ok))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds-dir", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--arms", default="ARM1,ARM2,ARM3")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for rel in EXECUTOR_FILES:
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True, cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} is not tracked")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} differs from HEAD")
    if _git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("refusing: tracked files are modified")
    head = _git("rev-parse", "HEAD")
    digests = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in EXECUTOR_FILES}
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    if not set(arms) <= set(PREREGISTERED_ARMS):
        sys.exit(f"arms must be pre-registered: {PREREGISTERED_ARMS}")
    if "ARM2" in arms:
        arms += list(EXPLORATORY_ARMS)
    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    wd = Path(a.worlds_dir)

    # (1) conversion through the canonical adapter
    conv = {w: AD.build_from_world(wd / w, OBS_DIR, universe, HIDDEN_FRACTION, ADAPTER_SEED) for w in WORLDS}
    # (2) RED_3 schema, RED_1 exact-twin byte identity, and proof that RED_1 can fail
    schemas = {w: schema_of(c) for w, c in conv.items()}
    dg = {w: digests_of(c) for w, c in conv.items()}
    red3 = all(schemas[w] == schemas["NULL"] for w in WORLDS)
    red1 = dg["TWIN_EXACT"] == dg["BIO"]
    with tempfile.TemporaryDirectory() as td:
        mutant = Path(td) / "TWIN_EXACT_MUTANT"
        shutil.copytree(wd / "TWIN_EXACT", mutant)
        shard = sorted((mutant / "observable_raw" / OBS_DIR).glob("RNA_SPARSE_*.npz"))[0]
        z = dict(np.load(shard, allow_pickle=False))
        z["data"] = z["data"].copy(); z["data"][0] += 1      # one count, inside support
        np.savez_compressed(shard, **z)
        mutant_dg = digests_of(AD.build_from_world(mutant, OBS_DIR, universe, HIDDEN_FRACTION, ADAPTER_SEED))
    red1_can_fail = mutant_dg != dg["BIO"]

    # (3) oracle-free features, frozen
    feats = {}
    for w, c in conv.items():
        ctx = context_features(c)
        feats[w] = dict(PCS=principal_components(c.model.student_expression, N_PCS), **ctx)
    blind = Blinding()
    try:
        blind.unblind(wd / "BIO", feats, conv["BIO"])
        red4 = False                                   # unblinding before freezing must refuse
    except RuntimeError:
        red4 = True
    frozen = blind.freeze(feats)

    # (4) unblinding, then scoring
    results, oracle_digest = {}, {}
    for w in WORLDS:
        c, ora = conv[w], blind.unblind(wd / w, feats, conv[w])
        oracle_digest[w] = hashlib.sha256(json.dumps(ora["spec"], sort_keys=True).encode()).hexdigest() if ora["spec"] else None
        gci = c.global_cell_index
        tr, te = gci % 2 == 0, gci % 2 == 1
        cols = np.searchsorted(universe, ora["module"]) if np.all(np.diff(universe) > 0) else \
            np.array([int(np.where(universe == m)[0][0]) for m in ora["module"]])
        ev = c.model.evidence_mask[:, cols]
        module = (np.where(ev, c.model.student_expression[:, cols], 0.0).sum(1) / np.maximum(ev.sum(1), 1))[:, None]
        op = c.operator_context.operator_index.astype(np.int64)
        per = {}
        for arm in arms:
            C = feats[w][arm]
            per[arm] = dict(
                status=("EXPLORATORY_DECOMPOSITION" if arm in EXPLORATORY_ARMS else
                        "EXPLORATORY_POSITIVE_CONTROL_ONLY" if arm == "ARM3" else "PREREGISTERED"),
                bio_latent=dict(MODULE=recoverability(module, C, ora["latents"]["BIO"], tr, te),
                                PCS=recoverability(feats[w]["PCS"], C, ora["latents"]["BIO"], tr, te)),
                operator_latent=dict(MODULE=recoverability(module, C, ora["latents"]["TWIN_OPERATOR"], tr, te),
                                     PCS=recoverability(feats[w]["PCS"], C, ora["latents"]["TWIN_OPERATOR"], tr, te)),
                module_context_share=context_share(module[:, 0], C, tr, te),
                identity_leakage=identity_leakage(C, op, tr, te))
        per_world = dict(kind=(ora["spec"] or {}).get("kind", "NULL"), arms=per)
        if "ARM2" in arms:
            per_world["support_count_identifies_operator"] = support_lookup_identification(
                c.operator_context.n_measured, op, tr, te)
        results[w] = per_world

    # pre-registered verdicts
    def strip_ci(x):
        return json.loads(json.dumps(x))
    red2_exact = strip_ci(results["BIO"]["arms"]) == strip_ci(results["TWIN_EXACT"]["arms"])
    red2_maxdiff = max_numeric_difference(results["BIO"]["arms"], results["TWIN_EXACT"]["arms"])
    red2 = red2_maxdiff <= FLOAT_TOLERANCE
    adequacy = results["BIO"]["arms"]["ARM1"]["bio_latent"]["MODULE"]["r2"] >= 0.3
    separation = {}
    for arm in arms:
        sb = results["BIO"]["arms"][arm]["module_context_share"]
        so = results["TWIN_OPERATOR"]["arms"][arm]["module_context_share"]
        if sb is None:
            separation[arm] = "NOT_APPLICABLE_NO_CONTEXT"
            continue
        apart = sb["ci95"][1] < so["ci95"][0] or so["ci95"][1] < sb["ci95"][0]
        separation[arm] = "SEPARABLE" if apart else "NOT_SEPARATED"
    exact = "NON_IDENTIFIABLE_BY_DESIGN" if (red1 and red2) else "LEAK"
    verdict = ("LEAK" if not (red1 and red2 and red3 and red4) else
               "UNINFORMATIVE_DESIGN" if not adequacy else "SCORED")
    rec = dict(
        schema="V77_S157_PAIRED_CHALLENGE_SCORE_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        mode="ZERO_UPDATE; diagnostic PCA and linear readouts only, not a representation candidate",
        preregistration=dict(path=str(PREREG.relative_to(ROOT)).replace("\\", "/"),
                             sha256=hashlib.sha256(PREREG.read_bytes()).hexdigest()),
        build=dict(path=str(BUILD.relative_to(ROOT)).replace("\\", "/"), sha256=hashlib.sha256(BUILD.read_bytes()).hexdigest()),
        realization="seed 7302, 2,000 cells, DEVELOPMENT_CALIBRATION",
        arms_scored=arms,
        red_checks=dict(RED_1_exact_twin_byte_identical=red1, RED_1_shown_able_to_fail_by_one_count=red1_can_fail,
                        RED_2_exact_twin_scored_identically=red2, RED_2_bitwise_equal=red2_exact,
                        RED_2_max_abs_difference=red2_maxdiff, RED_2_tolerance=FLOAT_TOLERANCE,
                        RED_3_schema_identical=red3,
                        RED_4_unblinding_before_freezing_refused=red4),
        model_facing_digests=dg, frozen=frozen, oracle_spec_digests=oracle_digest,
        design_adequacy=dict(rule="BIO, ARM1, MODULE test R2 >= 0.3", pass_=adequacy),
        exact_twin_verdict=exact, operator_twin_separation=separation, run_verdict=verdict,
        results=results,
        command=" ".join(["python", "scripts/v77/run_v77_s157_identifiability.py", *sys.argv[1:]]),
        source_commit=head, provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256=digests, no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(red=rec["red_checks"], adequacy=adequacy, exact_twin=exact, separation=separation,
                          verdict=verdict), indent=1))


if __name__ == "__main__":
    main()
