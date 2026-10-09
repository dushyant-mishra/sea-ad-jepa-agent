#!/usr/bin/env python3
"""Task 3 — measured-target T_A/T_B comparison under the common 23-gene reference.

IMPLEMENTS THE OWNER'S DECISIONS
  target        : the explicitly MEASURED developmental target. Three queries -
                  APOE, P2RY12, HLA-DRA - each with four partner genes, plus
                  separate reference genes for normalization. This is the
                  biological question, not an arbitrary RNA panel.
  normalization : COMMON 23-GENE EXCLUSION as the primary controlled arm, with
                  full-source and fixed-reference retained as sensitivity arms.
  teacher       : T_B (q-blind) is the candidate for developmental testing;
                  T_A (q-visible) is retained as a CONTROLLED COMPARISON, not
                  as something already qualified.

WHY A COMMON EXCLUSION SET RATHER THAN A PER-QUERY ONE
  Excluding only q removes the direct contribution but NOT the partner and
  reference genes, which also sit in the denominator. And a per-query exclusion
  set changes the denominator between queries, so the SAME complementary RNA
  would look different under different q - manufacturing an apparent query
  effect that is pure normalization. A single 23-gene union held fixed across
  all three queries removes that confound by construction.

THE TWO-STAGE TEST, in the owner's order
  Stage 1  does the teacher represent meaningful variation in the measured
           partner-gene state BEYOND technical effects, a q-only representation
           and generic cell state?
  Stage 2  can a query-conditioned student predict that state from its lawful,
           strictly smaller evidence?

  A target is not accepted because it is predictable. T_B's immunity to a
  q-count intervention is NECESSARY, NOT SUFFICIENT.

QUERY-SWAP CONTROL
  Compares targets in a COMMON biological coordinate system (the shared
  partner-state axes), so a difference between unrelated output coordinates
  cannot masquerade as genuine query conditioning.

SCOPE
  Synthetic counts with realistic microglial geometry, structured so that a
  real partner-state signal EXISTS and is separable from technical variation.
  This measures whether the constructions and controls behave correctly. It is
  NOT a biological result and opens no protected data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

# --- the measured developmental target ------------------------------------
# Eight reference genes, SHARED across all three queries. The union is therefore
# 3 queries + 12 partners + 8 references = 23 genes exactly, which is the set the
# owner reports physically testing on 84 historical cells across all 42 operators.
REFERENCE_GENES = ["ACTB", "GAPDH", "RPL13A", "B2M",
                   "PPIA", "TBP", "HPRT1", "UBC"]
QUERIES = {
    "APOE":    {"partners": ["APOC1", "TREM2", "TYROBP", "CTSD"],
                "references": REFERENCE_GENES},
    "P2RY12":  {"partners": ["CX3CR1", "SELPLG", "TMEM119", "SIGLEC11"],
                "references": REFERENCE_GENES},
    "HLA-DRA": {"partners": ["CD74", "HLA-DRB1", "HLA-DPA1", "CIITA"],
                "references": REFERENCE_GENES},
}
N_CELLS, N_GENES, N_OPERATORS = 8000, 300, 6
MIN_ROWS_PER_FEATURE = 5   # below this the fit is degenerate, not informative
SEED = 20260926


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_gene_index():
    named = []
    for q, spec in QUERIES.items():
        named += [q] + spec["partners"] + spec["references"]
    named = sorted(dict.fromkeys(named))                 # stable, deduplicated
    filler = [f"GENE_{i:04d}" for i in range(N_GENES - len(named))]
    genes = named + filler
    return genes, {g: i for i, g in enumerate(genes)}


def exclusion_sets(idx):
    """Per-query (13) and the common union (the owner's 23-gene set)."""
    per_query = {}
    union = set()
    for q, spec in QUERIES.items():
        s = {q} | set(spec["partners"]) | set(spec["references"])
        per_query[q] = sorted(idx[g] for g in s)
        union |= s
    return per_query, sorted(idx[g] for g in union), sorted(union)


def synth(rng, genes, idx):
    """Counts with a REAL latent partner-state per query, plus technical structure."""
    operators = rng.integers(0, N_OPERATORS, size=N_CELLS)
    depth = rng.lognormal(mean=np.log(6000), sigma=0.55, size=N_CELLS)
    depth *= (1.0 + 0.25 * (operators - operators.mean()) / max(operators.std(), 1e-9))
    base = rng.lognormal(0.0, 1.7, size=N_GENES); base /= base.sum()

    # one latent activity per query; partners co-vary with it, q correlates but
    # is NOT the state itself - so a q-blind teacher can still recover it
    latent = {q: rng.standard_normal(N_CELLS) for q in QUERIES}
    mult = np.ones((N_CELLS, N_GENES))
    protected_idx = {idx[g] for qq, s in QUERIES.items()
                     for g in [qq] + s["partners"] + s["references"]}
    free = np.array([i for i in range(N_GENES) if i not in protected_idx])
    # FIXTURE CORRECTION. A first version gave the COMPLEMENTARY genes no
    # dependence on the latent state, so only q and the partners carried signal.
    # T_B (q-blind) was then unable to work BY CONSTRUCTION, and the experiment
    # could not discriminate - it was testing a hypothesis the fixture had
    # already made false. Real cellular state is reflected across many genes, so
    # each query's latent program now also loads on a disjoint set of
    # complementary "program" genes at moderate strength.
    program_members = {}
    cursor = 0
    for q, spec in QUERIES.items():
        z = latent[q]
        members = free[cursor:cursor + 60]; cursor += 60
        program_members[q] = members.tolist()
        loadings = rng.uniform(0.25, 0.65, size=len(members))
        for gi, w in zip(members, loadings):
            mult[:, gi] *= np.exp(w * z)
        for p in spec["partners"]:
            mult[:, idx[p]] *= np.exp(0.85 * z)
        mult[:, idx[q]] *= np.exp(0.55 * z + 0.4 * rng.standard_normal(N_CELLS))
    lam = np.outer(depth, base) * mult
    counts = rng.poisson(lam).astype(np.int64)

    # STRUCTURAL MISSINGNESS: each operator fails to assay a distinct gene subset.
    # This is NOT zero expression - it is "not measured here", and it must stay
    # distinguishable downstream. Collapsing it to zero is the substitution that
    # silently inflates coverage and corrupts every derived statistic.
    measured = np.ones((N_CELLS, N_GENES), dtype=bool)
    protected = {idx[g] for q, s in QUERIES.items()
                 for g in [q] + s["partners"] + s["references"]}
    for op in range(N_OPERATORS):
        rs = np.random.default_rng(1000 + op)
        drop = rs.permutation([i for i in range(N_GENES) if i not in protected])[:40]
        rows = np.flatnonzero(operators == op)
        measured[np.ix_(rows, drop)] = False
    counts = np.where(measured, counts, 0)          # unmeasured entries carry no count
    return counts, operators, depth.astype(np.int64), latent, measured, program_members


def normalize(counts, *, rule, excluded, lib_full):
    """Return student-visible normalized matrix under one normalization rule."""
    if rule == "full_source":
        denom = lib_full.astype(np.float64)
    elif rule == "common_23_excluded":
        denom = (lib_full - counts[:, excluded].sum(axis=1)).astype(np.float64)
    elif rule == "fixed_reference":
        denom = np.full(counts.shape[0], 6000.0)
    else:
        raise ValueError(rule)
    return np.log1p(counts / np.maximum(denom, 1.0)[:, None] * 1e4), np.maximum(denom, 1.0)


def measured_target(counts, q, idx, lib_denom):
    """The MEASURED partner-gene state: normalized partner activity, plus
    composition, support and an uncertainty proxy. Not a random projection."""
    p_idx = [idx[g] for g in QUERIES[q]["partners"]]
    raw = counts[:, p_idx].astype(np.float64)
    act = np.log1p(raw / lib_denom[:, None] * 1e4)
    tot = np.maximum(raw.sum(axis=1, keepdims=True), 1.0)
    comp = raw / tot                                   # composition within partners
    support = (raw > 0).sum(axis=1).astype(np.float64) # how many partners detected
    unc = 1.0 / np.sqrt(np.maximum(raw.sum(axis=1), 1.0))
    return {"activity": act, "composition": comp, "support": support,
            "uncertainty": unc,
            "vector": np.hstack([act, comp, support[:, None], unc[:, None]])}


class DegenerateFit(Exception):
    """The design cannot resolve the question; refuse rather than report a number."""


def _fit_predict(Xtr, ytr, Xte, alpha):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Z, Zt = (Xtr - mu) / sd, (Xte - mu) / sd
    ym = ytr.mean(0)
    A = Z.T @ Z + alpha * len(Z) * np.eye(Z.shape[1])
    W = np.linalg.solve(A, Z.T @ (ytr - ym))
    return Zt @ W + ym


def _r2(y, pred):
    ss_res = ((y - pred) ** 2).sum()
    ss_tot = ((y - y.mean(0)) ** 2).sum()
    return float(1.0 - ss_res / max(ss_tot, 1e-12))


ALPHA_GRID = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0)


def ridge_r2(X, y, train, test, alpha=None, groups=None):
    """Operator-held-out ridge R^2 with alpha selected on TRAIN ONLY.

    TWO CORRECTIONS over the first revision, both of which produced misleading
    negative R^2 that looked like substantive verdicts:

      (i)  REFUSE an under-determined design instead of reporting a number.
           A ridge with fewer than MIN_ROWS_PER_FEATURE rows per feature returns
           large negative R^2 that reads as "the teacher fails every control"
           when it only means the fit could not be estimated.

      (ii) SELECT alpha PER ARM. Comparing a 277-feature teacher against a
           1-feature q-only control at one fixed alpha is not a fair comparison:
           the same penalty is far too weak for the wide arm and irrelevant for
           the narrow one. Each arm now gets its own alpha chosen by an inner
           split of the TRAINING operators only, so no test information is used.
    """
    if len(train) < MIN_ROWS_PER_FEATURE * X.shape[1]:
        raise DegenerateFit(
            f"{len(train)} train rows for {X.shape[1]} features "
            f"(< {MIN_ROWS_PER_FEATURE} rows/feature); fit is under-determined")
    if alpha is None:
        # THIRD CORRECTION. The previous revision tuned alpha on a POSITIONAL
        # slice of the training rows, which contains every training operator.
        # Alpha was therefore optimised for WITHIN-operator generalisation and
        # then evaluated ACROSS held-out operators - a structural mismatch that
        # left the wide arms overfit and produced large negative R^2 that read
        # as a substantive verdict. The inner split now holds out a whole
        # TRAINING operator, matching the outer structure.
        best, best_r2 = ALPHA_GRID[0], -np.inf
        if groups is None:
            cut = int(len(train) * 0.75)
            folds = [(train[:cut], train[cut:])]
        else:
            tr_ops = sorted(set(groups[train].tolist()))
            folds = []
            for held in tr_ops:
                itr = train[groups[train] != held]
                iva = train[groups[train] == held]
                if len(iva) and len(itr) >= MIN_ROWS_PER_FEATURE * X.shape[1]:
                    folds.append((itr, iva))
            if not folds:
                cut = int(len(train) * 0.75)
                folds = [(train[:cut], train[cut:])]
        for a in ALPHA_GRID:
            scores = [_r2(y[iva], _fit_predict(X[itr], y[itr], X[iva], a))
                      for itr, iva in folds]
            r = float(np.mean(scores))
            if r > best_r2:
                best, best_r2 = a, r
        alpha = best
    return _r2(y[test], _fit_predict(X[train], y[train], X[test], alpha))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    rng = np.random.default_rng(SEED)
    genes, idx = build_gene_index()
    per_query_excl, common_excl, common_names = exclusion_sets(idx)
    counts, operators, _, latent, measured, program_members = synth(rng, genes, idx)
    lib_full = counts.sum(axis=1)

    # operator-held-out split (stand-in for donor-held-out)
    test_ops = {0, 1}
    test = np.array([i for i in range(N_CELLS) if operators[i] in test_ops])
    train = np.array([i for i in range(N_CELLS) if operators[i] not in test_ops])

    out = {"per_query": {}, "normalization_arms": {}}

    for rule in ("common_23_excluded", "full_source", "fixed_reference"):
        Xnorm, denom = normalize(counts, rule=rule, excluded=common_excl, lib_full=lib_full)
        arm = {}
        for q, spec in QUERIES.items():
            qi, p_idx = idx[q], [idx[g] for g in spec["partners"]]
            forbidden = set([qi]) | set(p_idx) | {idx[g] for g in spec["references"]}
            lawful = np.array([i for i in range(N_GENES) if i not in forbidden])

            tgt = measured_target(counts, q, idx, denom)
            Y = tgt["vector"]

            # ---- teachers, all on the SAME complementary raw observations ----
            comp_cols = np.array([i for i in range(N_GENES) if i not in forbidden])
            T_B = Xnorm[:, comp_cols]                       # q-blind
            T_A = np.hstack([T_B, Xnorm[:, [qi]]])          # q-visible: + q only
            q_only = Xnorm[:, [qi]]
            generic = np.hstack([Xnorm[:, comp_cols].mean(1, keepdims=True),
                                 Xnorm[:, comp_cols].std(1, keepdims=True)])
            technical = np.hstack([np.log1p(lib_full)[:, None],
                                   (counts > 0).sum(1)[:, None].astype(float),
                                   np.eye(N_OPERATORS)[operators]])

            # structural missingness is a SEPARATE channel, never folded into value
            support_ch = measured[:, comp_cols].astype(np.float64)
            T_B = np.hstack([T_B, support_ch.mean(1, keepdims=True)])
            T_A = np.hstack([T_A, support_ch.mean(1, keepdims=True)])
            def _score(M):
                try:
                    return ridge_r2(M, Y, train, test, groups=operators)
                except DegenerateFit as exc:
                    return {"REFUSED_DEGENERATE": str(exc)}
            stage1 = {name: _score(M) for name, M in (
                ("T_A_q_visible", T_A), ("T_B_q_blind", T_B),
                ("q_only", q_only), ("generic_cell_state", generic),
                ("technical_only", technical))}

            # ---- Stage 2: student sees strictly LESS than the teacher -------
            rs = np.random.default_rng(7)
            student_cols = comp_cols[rs.permutation(len(comp_cols))[: len(comp_cols) // 2]]
            student = Xnorm[:, np.sort(student_cols)]
            stage2 = {"student_predicts_measured_target": _score(student)}

            # ---- q-count intervention (separate from identity swap) ---------
            mutated = counts.copy(); mutated[:, qi] = mutated[:, qi] * 7 + 23
            lib_m = mutated.sum(axis=1)
            Xm, dm = normalize(mutated, rule=rule, excluded=common_excl, lib_full=lib_m)
            # compare like with like: the support channel is unaffected by a q
            # count change (the measured mask does not move), so append it to both
            sup = support_ch.mean(1, keepdims=True)
            tb_shift = float(np.abs(np.hstack([Xm[:, comp_cols], sup]) - T_B).max())
            ta_shift = float(np.abs(
                np.hstack([Xm[:, comp_cols], Xm[:, [qi]], sup]) - T_A).max())

            s1 = stage1
            three_effects = {
                "effect_1_direct_q_dependence":
                    float(s1["q_only"]),
                "effect_2_complementary_rna_dependence":
                    float(s1["T_B_q_blind"] - max(s1["generic_cell_state"], s1["technical_only"])),
                "effect_3_query_identity_dependence": "see query_swap_common_coordinates",
                "note": ("all arms share the SAME normalization within a given rule, "
                         "so any T_B advantage here cannot come from a normalization "
                         "difference between arms"),
            }
            arm[q] = {"three_effect_decomposition": three_effects,
                      "stage1_teacher_vs_controls_r2": stage1,
                      "stage2_student_r2": stage2,
                      "q_mutation_max_shift": {"T_B_q_blind": tb_shift,
                                               "T_A_q_visible": ta_shift},
                      "lawful_student_genes": int(len(student_cols)),
                      "forbidden_genes": sorted(genes[i] for i in forbidden)}
        out["normalization_arms"][rule] = arm

    # ---- query-swap control in a COMMON coordinate system -------------------
    _unused_measured = measured
    Xnorm, denom = normalize(counts, rule="common_23_excluded",
                             excluded=common_excl, lib_full=lib_full)
    swap = {}
    qs = list(QUERIES)
    for q in qs:
        tgt_true = measured_target(counts, q, idx, denom)["vector"]
        for q2 in qs:
            if q2 == q:
                continue
            tgt_other = measured_target(counts, q2, idx, denom)["vector"]
            # SAME teacher evidence, DIFFERENT query identity -> different target?
            comp_cols = np.array([i for i in range(N_GENES)
                                  if i not in ({idx[q]} | {idx[g] for g in QUERIES[q]["partners"]}
                                               | {idx[g] for g in QUERIES[q]["references"]})])
            try:
                r_true = ridge_r2(Xnorm[:, comp_cols], tgt_true, train, test, groups=operators)
                r_swap = ridge_r2(Xnorm[:, comp_cols], tgt_other, train, test, groups=operators)
            except DegenerateFit as exc:
                swap[f'{q}->{q2}'] = {'REFUSED_DEGENERATE': str(exc)}
                continue
            swap[f"{q}->{q2}"] = {"r2_correct_query": r_true,
                                  "r2_swapped_query": r_swap,
                                  "degrades_under_swap": bool(r_swap < r_true)}
    out["query_swap_common_coordinates"] = swap

    def _num(v):
        return float('nan') if isinstance(v, dict) else float(v)
    prim = out["normalization_arms"]["common_23_excluded"]
    receipt = {
        "schema": "V5_MEASURED_TARGET_TA_TB_COMPARISON_V1",
        "status": "SYNTHETIC_DEVELOPMENTAL__NOT_A_BIOLOGICAL_RESULT__NOT_TRAINING",
        "owner_decisions_implemented": {
            "candidate_teacher": "T_B q-blind, with T_A retained as controlled comparison",
            "primary_normalization": "common_23_excluded",
            "sensitivity_arms": ["full_source", "fixed_reference"],
            "target": "measured partner-gene state (activity, composition, support, uncertainty)",
        },
        "queries": {q: QUERIES[q] for q in QUERIES},
        "fixture_program_genes_per_query": {q: len(v) for q, v in program_members.items()},
        "fixture_correction": ("a first version gave complementary genes NO dependence on the latent state, making T_B impossible by construction; each query now loads on 60 disjoint complementary program genes"),
        "common_exclusion_set": {"n_genes": len(common_names), "genes": common_names},
        "per_query_exclusion_sizes": {q: len(v) for q, v in per_query_excl.items()},
        "split": {"kind": "operator_held_out", "test_operators": sorted(test_ops),
                  "n_train": int(len(train)), "n_test": int(len(test))},
        "results": out,
        "verdicts": {
            "T_B_invariant_to_q_mutation": all(
                prim[q]["q_mutation_max_shift"]["T_B_q_blind"] == 0.0 for q in QUERIES),
            "T_A_moves_under_q_mutation": all(
                prim[q]["q_mutation_max_shift"]["T_A_q_visible"] > 0.0 for q in QUERIES),
            "T_B_beats_q_only_everywhere": all(
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["T_B_q_blind"]) >
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["q_only"]) for q in QUERIES),
            "T_B_beats_generic_cell_state_everywhere": all(
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["T_B_q_blind"]) >
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["generic_cell_state"]) for q in QUERIES),
            "T_B_beats_technical_only_everywhere": all(
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["T_B_q_blind"]) >
                _num(prim[q]["stage1_teacher_vs_controls_r2"]["technical_only"]) for q in QUERIES),
        },
        "interpretation_guard": (
            "Predictability is NOT acceptance. T_B's invariance to a q-count "
            "intervention is necessary, not sufficient. These are synthetic counts "
            "with a planted partner-state signal; the experiment tests whether the "
            "constructions and controls behave correctly, not whether the biology "
            "is real."),
        "training_authorized": False,
        "protected_data_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "MEASURED_TARGET_TA_TB_COMPARISON_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"  common exclusion set: {len(common_names)} genes")
    print(f"  split: operator-held-out, train {len(train)} / test {len(test)}\n")
    print("  PRIMARY ARM (common_23_excluded) — Stage 1 teacher vs controls, R^2 on measured target")
    print(f"    {'query':10s} {'T_B':>8s} {'T_A':>8s} {'q_only':>8s} {'generic':>8s} {'technical':>10s}")
    for q in QUERIES:
        s = prim[q]["stage1_teacher_vs_controls_r2"]
        f=lambda k: (f"{_num(s[k]):8.4f}" if not isinstance(s[k],dict) else "  REFUSED")
        print(f"    {q:10s} {f('T_B_q_blind')} {f('T_A_q_visible')} "
              f"{f('q_only')} {f('generic_cell_state')} {f('technical_only')}")
    print("\n  Stage 2 — student (half the lawful genes) predicting the measured target")
    for q in QUERIES:
        v=prim[q]["stage2_student_r2"]["student_predicts_measured_target"]
        print(f"    {q:10s} R^2 " + ("REFUSED" if isinstance(v,dict) else f"{v:.4f}"))
    print("\n  q-count intervention (max shift in teacher evidence)")
    for q in QUERIES:
        m = prim[q]["q_mutation_max_shift"]
        print(f"    {q:10s} T_B {m['T_B_q_blind']:.6e}   T_A {m['T_A_q_visible']:.6e}")
    print("\n  verdicts:")
    for k, v in receipt["verdicts"].items():
        print(f"    {k:42s} {v}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
