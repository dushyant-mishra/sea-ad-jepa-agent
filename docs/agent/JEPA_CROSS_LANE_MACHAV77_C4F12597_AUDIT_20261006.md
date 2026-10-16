# JEPA cross-lane audit — Macha V77 Observer-V2 superseding commit — 2026-10-06

## Purpose

This is a handoff-lane synchronization record for the runtime-reconciliation agent. It records the scientific status of Macha's superseding V77 synthetic-lane commit without importing synthetic authority into the runtime lane.

Synthetic commit audited:

`c4f1259757471a09931de576a6e6c095c6ab210a`

It directly supersedes the earlier Macha baseline:

`d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

Nothing in this record authorizes Stage A, protected-data execution, production-world generation, model training, optimizer mutation, EMA mutation, or checkpoint authority.

---

## 1. Audit verdict

Macha's scientific correction is substantially valid and materially advances the V77 synthetic problem.

Record lane status as:

`SUPPORTED_FOR_NEXT_STAGE__ISSUE_1_NARROWED__PROMOTION_NOT_YET_QUALIFIED`

Issue 1 is **narrowed, not closed**.

The next justified synthetic experiment is generator dynamic range with the repaired observation assumptions held fixed, followed by Issue-2 sign/community co-calibration.

Do **not** promote Observer-V2 yet.

---

## 2. What is supported

The superseding commit separates latent abundance from capture/detection and preserves full-scale biological abundance instead of shrinking abundance merely to purchase topology.

Committed Observer-V2 mechanisms are:

1. latent biological abundance `mu = exp(eta + A)` with `A` at full scale;
2. per-gene capture propensity `kappa[g]`;
3. per-cell measurement state `s[c]`;
4. stochastic Poisson realization.

Detected genes are an outcome of `counts > 0`; the exact per-cell detected-gene-count constraint is not reintroduced.

The decisive isolation recorded in the decision receipt is:

| condition | frac |corr| > .3 | mean degree | transitivity | max/median |
|---|---:|---:|---:|---:|
| decoupled + deterministic | 0.6154 | 1846 | 0.8238 | 2908.1 |
| decoupled + Poisson | 0.0059 | 18 | 0.3558 | 3429.4 |
| real | 0.6148 | 1843.8 | 0.8871 | 1976.6 |

Therefore the earlier claim that abundance had to be shrunk to ~0.3 to recover topology is superseded.

The acceptable historical wording is:

> The observation model was the dominant shared bottleneck revealed by the Step-3 experiments, so the earlier 37 generator failures cannot be cleanly attributed to generator structure alone.

Do not retain the stronger historical statement that "the generator was never the binding constraint."

---

## 3. Canonical abundance/topology gene universe

The apparent abundance-number discrepancy is resolved by gene universe.

For qualification comparisons against the frozen topology envelope, the canonical universe is the real TRAIN prevalence-filtered universe:

- detection floor: `0.05`;
- genes: `19,569`;
- max/median point: `1976.65`;
- max/median envelope: `[1804.75, 2187.67]`;
- top-1% share point: `0.2457`;
- top-1% share envelope: `[0.2431, 0.2503]`.

The older ~`6685` and `0.322` figures are diagnostics over all `41,238` registry addresses. They are not a target move.

Future metric names should make the universe explicit, e.g.:

- `abundance_max_median__TRAIN_PREVALENCE05_19569`
- `abundance_max_median__FULL_REGISTRY_41238`

Only the first should be quoted against the frozen topology envelope.

---

## 4. Promotion blocker A — fixed topology evaluation universe

The committed candidate table reports different `genes_kept` values by candidate:

- O1: 23,891
- O2: 19,825
- O3: 12,468
- O4: 28,884
- O5: 15,657
- O6: 13,487

This is a strong audit concern.

If these counts mean each synthetic candidate is independently prevalence-filtered before graph metrics are computed, then topology statistics are being compared across different vertex sets. That is not promotion-grade comparability.

A poor observer that removes canonical genes should be penalized for their disappearance rather than silently receiving a smaller graph on which topology is scored.

Before promotion, require one fixed primary evaluation universe:

`REAL TRAIN prevalence >= 0.05 -> frozen 19,569-gene set -> evaluate every synthetic candidate on exactly those genes`

Candidate-specific prevalence-filtered metrics may remain secondary diagnostics.

This concern is confirmed by the candidate result artifact's variable `genes_kept` values, but it remains a **scoring-path concern rather than a proven implementation defect** until the exact scoring function is traced.

---

## 5. Promotion blocker B — deterministic-isolation executable provenance

The committed Observer-V2 executable implements:

`counts ~ Poisson(mu * kappa * s)`

with detection defined as `counts > 0`.

The decision receipt records the scientifically decisive comparison between decoupled+deterministic and decoupled+Poisson, but the one-commit delta from `d76631b6` to `c4f12597` contains no corresponding deterministic-isolation executor alongside the new Poisson Observer-V2 script.

Before promotion, require an executable provenance path for the causal isolation:

`same frozen generator + same capture variables + realization toggle deterministic/Poisson -> command -> seed -> artifact -> digest`

This does not invalidate the recorded result. It means the causal conclusion currently has stronger receipt evidence than committed executable provenance.

---

## 6. Causal wording for the remaining residual

Generator dynamic range is the correct next falsifiable target.

Do not yet state exclusive causality as:

> the residual belongs to the generator, not the observer.

Use the narrower statement:

> With the current fixed generator and the current biologically motivated independent-capture Poisson observer, introducing counting noise destroys the recovered dependence topology. This is consistent with insufficient latent rate dynamic range, making generator dynamic range the next falsifiable target.

The current mechanistic clue is meaningful: the recorded module switch is ~3.3-fold and moves detection probability roughly `0.63 -> 0.96`; the real dependence structure appears to require larger effectively-off to clearly-on rate excursions.

This supports a small predeclared dynamic-range family, not another broad free-parameter search.

---

## 7. Required next sequence for Macha lane

1. Correct the historical observer/generator overclaim to the accepted wording above.
2. Freeze the topology evaluation universe explicitly to the canonical real TRAIN 19,569 genes and rerun the relevant comparison.
3. Commit the deterministic-vs-Poisson isolation executor, command, seed, receipt, and digest if it does not already exist elsewhere in the lineage.
4. Freeze Observer-V2 while testing **generator dynamic range only**.
5. Predeclare a small mechanistic dynamic-range family rather than a continuous tuning search.
6. Ask whether stronger state-dependent rate excursions survive Poisson realization while retaining abundance, capture, depth, and other frozen constraints.
7. Only then perform Issue-2 sign/community co-calibration.
8. Rerun A_REPLICA when a specific observer/generator combination is proposed for promotion.

Macha's decision not to redesign or rerun A_REPLICA during the current diagnostic narrowing cycle is acceptable; it remains a promotion-time control.

---

## 8. Runtime-lane consequences

This synthetic-lane advance does **not** reopen any completed runtime audit.

The runtime lane remains governed by the completed-audits ledger and continues at:

- exact historical authority/guard source and test recovery where still missing;
- exhaustive current V5 optimizer/scaler/EMA/checkpoint/resume mutation-site inventory;
- RED bypass tests;
- minimal authority-bound mutation consumer;
- deterministic authority-bound checkpoint/restart;
- deliberate comparison against post-PR220 `main`.

No runtime implementation decision should be made from synthetic-lane scientific progress unless a concrete interface dependency appears.

Hard runtime invariants remain unchanged:

- no EMA after rejected, skipped, failed, ambiguous, or unproven optimizer mutation;
- no authority/cursor advancement for an AMP-skipped update;
- no restart accepted unless it reconstructs the exact next lawful authorized trajectory;
- training remains OFF;
- protected-data execution remains OFF.

---

## 9. Anti-repeat boundary

Do not repeat the following merely because the Macha baseline changed from `d76631b6` to `c4f12597`:

- V64 authority/guard existence archaeology;
- F1 trainer analysis;
- PROD41K/T1 scientific qualification;
- wholesale V64 merge analysis;
- AMP call-vs-mutation reasoning;
- EMA-after-proven-step ordering;
- transitive q-safety reasoning;
- worker-tuning archaeology;
- canonical-consumer architecture decision.

Reopen those only under the explicit criteria in `JEPA_RUNTIME_RECONCILIATION_COMPLETED_AUDITS_20261006.md`.
