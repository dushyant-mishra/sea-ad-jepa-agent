#!/usr/bin/env python3
"""V77_SYNTHETIC_WORLD_QUALIFICATION: generator dynamic range under a FIXED Poisson observer.

THE QUESTION. Stochastic counting was shown to collapse the recovered dependence topology:
between arms identical in everything but realization, transitivity fell 0.7645 to 0.3555 and
mean degree 1562 to 8.4. The proposed explanation is insufficient latent rate dynamic range -
a module switch currently moves a gene about 3.3-fold, which shifts detection probability from
roughly 0.63 to 0.96, a margin Poisson noise swamps. Real detection reaches a correlation of
0.377 at comparable depth, implying excursions that carry genes from effectively absent to
clearly present.

FROZEN FOR THIS EXPERIMENT, varied: dynamic range ONLY.
  canonical evaluation universe   TRAIN_PREVALENCE05_19569
  capture parameterization        O3_capture_independent_wide
  cell-state parameterization     same sd, same draw
  realization rule                Poisson, never deterministic
  scoring implementation          one function per scorer, applied identically to every arm
  seed protocol                   one seed for all arms
  real-data envelopes             unchanged

The deterministic-threshold observer is NOT optimized here. It is retained only as a
diagnostic control, because at current parameters it destroys 9,964 of 19,569 canonical genes
and is therefore a poor production-observer candidate.

PREDECLARED MECHANISTIC FAMILY, not a continuous search. Four graded-amplitude arms and one
structurally different arm:

  DR1  module_scale 1.20   the current baseline, a graded additive shift
  DR2  module_scale 2.50
  DR3  module_scale 4.00
  DR4  module_scale 5.50
  DR5  TRUE ON/OFF switching: a module that is off is driven to a floor rather than merely
       shifted down. Biologically this is the difference between a gene being modulated and a
       gene being transcriptionally silent, and only the latter produces the near-absent to
       clearly-present excursion the real detection topology implies.

REJECTION RULES, declared before results are seen. A topology improvement is REJECTED if it is
purchased by losing canonical genes, worsening the abundance marginal, distorting the depth or
capture marginals, collapsing sign structure, or producing pathological community structure.

REVISION V2, from the self-audit. No parameter of any arm has changed.

  S129  DR5 as first run (0627b2e7) thresholded eta at a GLOBAL median, which is not on/off
        switching at all. DR5 now silences, cell by cell, the modules that cell's own
        sub-state leaves in their silent state.
  S138  The first S129 repair silenced every OFF module regardless of the module's sign. For a
        repressive module (negative loadings) off is the PRESENT state, so its genes stayed low
        in both states and produced no excursion. Switching is now sign-aware, which is the
        only reading under which DR5 does what its declaration says it is for. This was settled
        before any corrected DR5 result existed.
  S139  score_v1_binary_hvg chose genes by binary-detection variance; the frozen real envelope
  S140  chooses them by expression variance, and computes T5 on the expression layer with a
        200-cell floor. V1 is retained unchanged ONLY so DR1-DR4 can be checked for exact
        reproduction of 0627b2e7. Comparisons with the real envelopes use score_matched.

PREDICTION RECORDED BEFORE THE V2 RUN. L1_two_giant has two modules, each about 41% of all
addresses. Under sign-aware switching a cell silences each module with probability about one
half, so DR5 silences roughly 40% of the transcriptome per cell. That is not module-local in any
biological sense. Expected: DR5 detects FEWER genes per cell than DR4 and fails the depth rule;
transitivity under v1 stays high. If DR5 instead keeps depth near DR1, this prediction is wrong.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v77_substate_generator as SS
import v77_observer_v2_capture as OV2
import v77_address_universe as AU
import build_v77_calibration_envelope as ENV
import v77_matched_scoring as MS

TARGET_MEDIAN_LIBRARY = 14340.0
CAPTURE = "O3_capture_independent_wide"
BASE_GENERATOR = "L1_two_giant"

ARMS = {
 "DR1_scale_1p20_baseline": dict(mode="graded", module_scale=1.20,
    note="current baseline; a module switch moves a gene about 3.3-fold"),
 "DR2_scale_2p50": dict(mode="graded", module_scale=2.50, note="about 12-fold"),
 "DR3_scale_4p00": dict(mode="graded", module_scale=4.00, note="about 55-fold"),
 "DR4_scale_5p50": dict(mode="graded", module_scale=5.50, note="about 245-fold"),
 "DR5_true_on_off": dict(mode="onoff", module_scale=4.00, off_floor=-6.0,
    note="structurally different: a module in its silent state drives its genes to a floor, "
         "i.e. transcriptionally silent rather than merely reduced"),
}

EXECUTOR_FILES = ("run_v77_dynamic_range_tournament.py", "v77_matched_scoring.py",
                  "v77_substate_generator.py", "v77_observer_v2_capture.py",
                  "v77_address_universe.py", "build_v77_calibration_envelope.py",
                  "build_v77_topology_calibration.py")


def build_eta(arm_cfg, n_cells, n_addr, seed):
    """Sub-state generator with ONLY the dynamic-range mechanism altered."""
    cfg = dict(SS.SUBSTATE_CANDIDATES[BASE_GENERATOR])
    cfg["module_scale"] = arm_cfg["module_scale"]
    gen = SS.SubStateGenerator(cfg, n_addr, seed)
    g = gen.generate(n_cells, seed=seed)
    eta, cls = g["eta"], g["cls"]
    info = {}
    if arm_cfg["mode"] == "onoff":
        # MODULE-LOCAL, SIGN-AWARE silencing driven by each cell's OWN sub-state (S129, S138).
        # An activating module (positive loadings) is present when on and silent when off; a
        # repressive module (negative loadings) is silent when on and present when off. Where
        # modules overlap, silencing by either one wins.
        on = gen.table[g["substate"]]                       # (cells, modules) on/off
        eta = eta.copy()
        silenced = np.zeros(eta.shape, dtype=bool)
        signs = []
        for j, (m, w) in enumerate(gen.loadings):
            if not (np.sign(w) == np.sign(w[0])).all() or w[0] == 0:
                raise RuntimeError(f"module {j} has mixed-sign or zero loadings")
            activating = bool(w[0] > 0)
            signs.append("activating" if activating else "repressive")
            silent_cells = np.where((on[:, j] == 0) if activating else (on[:, j] == 1))[0]
            if len(silent_cells):
                eta[np.ix_(silent_cells, m)] = arm_cfg["off_floor"]
                silenced[np.ix_(silent_cells, m)] = True
        eta = eta.astype(np.float32)
        frac = silenced.mean(1)
        info = dict(module_signs=signs, module_sizes=[int(len(m)) for m, _ in gen.loadings],
                    silenced_fraction_of_addresses_per_cell=dict(
                        mean=float(frac.mean()), p10=float(np.quantile(frac, .1)),
                        p90=float(np.quantile(frac, .9))))
    return eta, cls, g, info


def score_v1_binary_hvg(counts, universe, cls):
    """THE ORIGINAL 0627b2e7 SCORER, unchanged, retained only to check reproduction.
    Its gene selection (binary variance) and T5 (binary layer, 150-cell floor) do not match the
    frozen real envelopes (S139, S140): do NOT compare these numbers with real values."""
    sub = counts[:, universe]
    det = (sub > 0).astype(np.float64)
    var = det.var(0)
    idx = np.where(var > 0)[0]
    n_hvg = min(3000, len(idx))
    sel = idx[np.argsort(-var[idx])[:n_hvg]]
    t = ENV.stats_from_logmatrix(det, sel, n_hvg)
    gm = sub.sum(0) / len(sub); nz = gm[gm > 0]; srt = np.sort(gm)[::-1]
    H = det[:, sel]; H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    C = (H.T @ H) / len(H)
    pooled = float(np.quantile(np.abs(C[~np.eye(len(C), dtype=bool)]), .5))
    wc = []
    for c in np.unique(cls):
        m = cls == c
        if m.sum() < 150: continue
        Hc = det[m][:, sel]; Hc = (Hc - Hc.mean(0)) / (Hc.std(0) + 1e-9)
        Cc = (Hc.T @ Hc) / m.sum()
        wc.append(float(np.quantile(np.abs(Cc[~np.eye(len(Cc), dtype=bool)]), .5)))
    return dict(
        canonical_genes_nonzero_variance=int(len(idx)),
        canonical_genes_lost=int(len(universe) - len(idx)),
        median_detected_per_cell=float(np.median((sub > 0).sum(1))),
        abundance_max_median__TRAIN_PREVALENCE05_19569=(float(srt[0] / np.median(nz)) if len(nz) else float("nan")),
        top1pct_count_share__TRAIN_PREVALENCE05_19569=float(srt[: max(1, len(universe) // 100)].sum() / gm.sum()),
        median_abs_corr=float(t["median_abs_corr"]), frac_abs_gt_0p3=float(t["frac_abs_gt_0p3"]),
        mean_degree=float(t["mean_degree"]), transitivity=float(t["transitivity"]),
        pos_over_neg_ratio=float(t["pos_over_neg_ratio"]),
        frac_pos_gt_0p3=float(t["frac_pos_gt_0p3"]), frac_neg_lt_m0p3=float(t["frac_neg_lt_m0p3"]),
        largest_community_frac=float(t["largest_community_frac"]),
        t5_within_over_pooled=(float(np.mean(wc) / pooled) if wc and pooled > 0 else float("nan")))


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=HERE).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--allow-dirty", action="store_true",
                    help="development only; the receipt is then marked NOT_FROM_A_CLEAN_COMMITTED_HEAD")
    a = ap.parse_args()
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    # an untracked executor passes a status check, so check each one explicitly (S154)
    untracked = [f for f in EXECUTOR_FILES if not _git("ls-files", "--", f)]
    if (dirty or untracked) and not a.allow_dirty:
        sys.exit("refusing to run: a receipt must describe committed code\n" + dirty
                 + "".join(f"\nuntracked executor: {f}" for f in untracked))
    # digests taken BEFORE the work, so an edit during the run cannot be misrecorded (S153)
    executor_digests = {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in EXECUTOR_FILES}

    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    N = AU.N_ADDRESSES
    AB = AU.AddressUniverse(seed=7302).log_abundance.astype(np.float32)
    cfg_cap = OV2.OBSERVER_CANDIDATES[CAPTURE]
    kappa = OV2.build_kappa(cfg_cap, AB, a.seed)
    s = np.exp(cfg_cap["cell_state_sd"] * np.random.default_rng(a.seed + 7).standard_normal(a.cells))

    results = {}
    for arm, acfg in ARMS.items():
        eta, cls, _, info = build_eta(acfg, a.cells, N, a.seed)
        lograte = eta + AB[None, :] + np.log(kappa)[None, :] + np.log(s)[:, None]
        rate = np.exp(np.clip(lograte, -12, 12))
        rate = rate * (TARGET_MEDIAN_LIBRARY / max(np.median(rate.sum(1)), 1e-9))
        counts = np.random.default_rng(a.seed + 8).poisson(rate).astype(np.float32)
        v1 = score_v1_binary_hvg(counts, universe, cls)
        mt = MS.score_matched(counts, universe, cls)
        results[arm] = dict(note=acfg["note"], mode=acfg["mode"], module_scale=acfg["module_scale"],
                            mean_count_per_detected_gene=float(counts[counts > 0].mean()),
                            dr5_switching=info or None,
                            v1_binary_hvg__NOT_COMPARABLE_TO_REAL=v1,
                            matched_to_real_envelopes=mt)
        d = mt["detection"]
        print("%-24s lost=%5d det/cell=%5.0f | v1 TRANS=%.4f T5=%.4f | matched TRANS=%.4f frac>.3=%.4f deg=%7.1f T5=%.4f"
              % (arm, mt["canonical_genes_lost"], mt["median_detected_per_cell"], v1["transitivity"],
                 v1["t5_within_over_pooled"], d["transitivity"], d["frac_abs_gt_0p3"],
                 d["mean_degree"], mt["t5"]["within_over_pooled"]))

    here = HERE
    rec = dict(
        schema="V77_DYNAMIC_RANGE_TOURNAMENT_V2",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        supersedes=dict(receipt="results/v77/V77_DYNAMIC_RANGE_TOURNAMENT_V1.json",
                        why="S129/S138 DR5 implementation, S139/S140 scorer mismatch"),
        question="does larger latent rate dynamic range let the topology survive Poisson realization?",
        frozen=dict(evaluation_universe="TRAIN_PREVALENCE05_19569",
                    capture=CAPTURE, realization="Poisson", base_generator=BASE_GENERATOR,
                    seed=a.seed, cells=a.cells),
        varied="generator dynamic range only",
        predeclared_family=list(ARMS),
        arm_parameters_changed_since_v1="none",
        scorers=dict(v1_binary_hvg="0627b2e7 scorer, retained for reproduction only (S139, S140)",
                     matched_to_real_envelopes=MS.RULE),
        rejection_rules=["topology gains purchased by losing canonical genes are rejected",
                         "worsening abundance marginal rejects the arm",
                         "distorted depth or capture marginals reject the arm",
                         "collapsed sign structure rejects the arm",
                         "pathological community structure rejects the arm"],
        deterministic_observer="retained as diagnostic control only; not optimized",
        command=f"python scripts/v77/run_v77_dynamic_range_tournament.py --universe {a.universe} "
                f"--out {a.out} --cells {a.cells} --seed {a.seed}",
        source_commit=_git("rev-parse", "HEAD"),
        provenance_status=("NOT_FROM_A_CLEAN_COMMITTED_HEAD" if (dirty or untracked)
                           else "CLEAN_COMMITTED_HEAD"),
        executor_sha256=executor_digests,
        universe_sha256=hashlib.sha256(Path(a.universe).read_bytes()).hexdigest(),
        arms=results,
        no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")


if __name__ == "__main__":
    main()
