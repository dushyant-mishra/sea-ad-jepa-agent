# Macha closure check — PR #356 amended plan (P1–P6 only)

Date: 2026-10-14.

**Scope.** P1–P6 from the Macha #356 review (`16e411f3`) only, plus any defect introduced by the amendment.

**Read-only throughout.** No outcomes, DEV/SEALED data or pathology were opened.

**Verdict:** `P1_P6_CLOSED__TASK_4_MAY_BEGIN_AFTER_TASKS_1_3__ONE_IDENTITY_FIX_BEFORE_TASK_12__BINDING_NOTES_N3_N6`

## Custody

| object | identity |
|---|---|
| plan head | `66f323f192d1506f1be1af64c975997c69a90e82` (4 commits after `1c764c7f`; only the plan file changed; still stacked on `847fe734`) |
| live dependency heads | #343 `82d17bfb`, #350 `9b9078c1`, #351 `2abcb9fe156e…`, #352 `bb1e35d3`, #353 `1df20029`, #354 `d9004730`, #355 `6e5182e2`: all equal the plan table |

## Item checks

| item | result | basis |
|---|---|---|
| P1 ordering before exposure | **CLOSED** | Pre-exposure ordering law: Tasks 8 and 10 run on non-production fixtures only. Baseline ceilings are pre-exposure realism metrics. The first production downstream call follows the realism freeze and calls `record_exposure` at that call. Nothing runs while realism iteration is still open. |
| P2 withheld-family custody | **CLOSED** (note N3) | The spec is controller-authored and kept off-repo; subagents never see it. Only the hash commitment is committed. A private tree scan publishes only a boolean and the tree identity. Dummy-secret tests (`scan_secret_absence`). Reveal after the fit freeze. |
| P3 stop gates | **CLOSED** | `STOP_A` / `STOP_B` / `STOP_C` require fresh authorization. The current authorization covers code and fixture tests only. |
| P4 §13/§20/§22 | **CLOSED** (note N4) | Every listed item has an owning test: §20/§22.9 minimum counts plus separate poison/swap tests (T6); §13 thinning (T5); §22.14 (T5); §22.13 (T3); §22.8 and §22.12 (T9); §22.7 (T4, T7). |
| P5 freshness | **CLOSED** (notes N5, N6) | #351 is at `2abcb9fe`, with the reason restated as the §15 gaps. Moving heads fail closed and need explicit `BRANCH_MOVED_*` reclassification. G8 is updated. #355 needs implementation repair plus a separate reviewed binding before any promotion. |
| P6 identity form | **PARTIAL — fix F1** | Both specs carry their Git blob SHA. Their SHA-256 values appear only abbreviated (`234af6df…c65b`, `ab1ae1bb…363f`). That is my own review's abbreviation, copied in, and an abbreviation is not an identity binding. |

## Required fix (before Task 12; recommended in the next plan commit)

**F1.** Cite the full SHA-256 values, which T12 tests:
- V3.1: `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c`
- V3.1.1: `ab1ae1bb67765cc025f580205d7c082ee4af470dd39ef23c4f000414e8e9363f`

## Binding notes (plan-execution instructions; no further design cycle)

**N3 (P2/E2) — a code path used only by the withheld family is itself part of its spec.** "Generic mechanism code may be public" holds only if every public mechanism code path is also exercised by development realizations. Otherwise its unused presence reveals the withheld family to anyone reading the source. A code path used only by the withheld family stays off-repo with the spec.

**N4 (§13, from the concurrent real audit) — thinning must also thin the library.** `thin_measured_scalar_by_cell` must apply one cell-keyed thinning law to the normalization library as well as to the stored counts.

In the authenticated reader-fit Level-4 census, stored-address counts make up this share of the full-source library:
- HVS: exactly 1.0;
- NPH52: 0.960–0.999;
- SEA_AD: 0.75–1.0.

So an exact thinning is `L_p = Σ thinned stored + Binomial(L − S, p)`. Keeping `L` fixed injects a log(1/p) depth artifact. If synthetic observation emits off-address library mass to match these fractions, the same law applies. The fractions are a candidate `AUTHENTICATED_EMPIRICAL_CALIBRATION` input:
- branch `audit/td-real-data-qualification-macha-20261014`;
- receipt `RAWCOUNT_DEPTH_SUPPORT_CENSUS_RECEIPT_V1.json`.

**N5 (P5/G8) — no reuse of #343's thinning code.** The hostile audit of #343 found:
- the conformal-bound arithmetic is exact;
- `thin_integer_counts` keys randomness to storage order, has no observation-state channel and no thinned library;
- `validate_seed_namespaces` is never called.

The accurate label is `CONFORMAL_BOUND_ARITHMETIC_QUALIFIED__THINNING_MECHANICS_REPAIR_REQUIRED__…`. The fail-closed result is unchanged, but no task may import #343's `thin_integer_counts` as qualified mechanics. T5's own cell-keyed operator is the only allowed thinning path.

**N6 (P5/R1) — #353 is not a hostile R1 control source.** The R1 audit found #353's four worlds are non-adversarial; its TD57B arm checks a constant dictionary. The #350 relation-label null is not matched on depth or detection, and a library-size-only world beats it in 8 of 8 donors. Keep `SEMANTICS_COMPATIBLE_FIXTURE_ONLY` as the classification, but #353 may not stand in for T8's verdict-bearing controls. T8 must carry its own library/depth-only technical negative for any relational rehearsal.

## Execution

- Tasks 1–3 may proceed under the agreed subagent-driven protocol.
- Task 4 may begin after Tasks 1–3 complete their per-task reviews. F1 and N3–N6 travel with the plan.
- The per-task fresh implementer plus fresh reviewer protocol is available in this Claude Code session (Agent dispatch) if the owner prefers it to Codex. Under P2 the withheld family would still be authored by the owner or controller, never by a dispatched subagent.

Writing this check authorizes no realization, sealed qualification or finalization (STOP_A/B/C stand), and no target, representation, TD60, Stage4 or training.

Authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
