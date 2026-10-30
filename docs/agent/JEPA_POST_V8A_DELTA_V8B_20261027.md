# JEPA V8b post-V8a delta — 2026-10-27

This is an **append-only** status delta. It does not rewrite V8 or V8a. Read V8a first for the full historical custody context, then use this file only to update the latest actionable PR heads.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Why this delta exists

After the V8a snapshot was frozen, PR #457 moved to a new exact head and its previously failing result-receipt workflow was repaired. PRs #458, #459 and #460 remain at their V8a exact heads. The new agent must not mistake a later GREEN engineering head for new biological authority, and must not treat the older V8a PR457 RED as the latest execution state.

Machine mirror:
`results/target_discovery/unified_qualification_v1/JEPA_POST_V8A_DELTA_V8B_20261027.json`.

## Current exact heads

### PR #457 — public E2G external reference audit

Current exact head:

`17e7cc8818d27222fac5c0a3e91677640ea81153`

Current workflows:

- External E2G evidence intake audit — run `40530132817` — SUCCESS.
- E2G seven-track result receipt validation — run `40530132741` — SUCCESS.

This supersedes only the **engineering execution status** recorded in V8a for PR #457's earlier result-receipt RED head.

It does **not** change the scientific classification:

- public reference annotation only;
- no authenticated TF-bound-enhancer→gene causal chain;
- no canonical Ensembl-to-symbol biological qualification;
- no explicitly microglia-labelled source track in the surveyed portal metadata;
- no SEA-AD MTG ATAC fragment acquisition;
- no direct perturbation evidence;
- no Target Discovery PASS;
- no target selection, Stage4 or training authorization.

The current PR itself explicitly states these limitations. Do not merge its positive coverage counts into the TD gate ledger as causal evidence.

### PR #458 — Production Synthetic Tasks1–2 hostile recheck

Exact head remains:

`3b08081d7fb3fa99cf1459b13cbe47d5b0962547`

The **13 hostile RED** are still the controlling review result against repaired #453/#456.

Do not infer cumulative Task1/2 acceptance from old GREEN repair runs. Production Synthetic Task4 remains blocked.

### PR #459 — Task4 X1 transaction candidate

Exact head remains:

`57e707149b46ca011eee096f01dc08b64aeb8f9f`

Author CI remains GREEN, including Task4 run `40518058012`.

This is Macha-authored work on top of Macha-authored cumulative Task4. It requires independent adversarial review and then a non-author cumulative Task4 acceptance decision.

X3 mixed Windows/WSL coordination and external publisher/issuer trust are not independently qualified.

**Do not implement another X1 in parallel. Review #459.**

### PR #460 — active clean successor

Exact head remains:

`a081f8d719372b14ab95120f4f7ba290a0940e4a`

Handoff pointer run `40527188414` and successor custody run `40527188357` are GREEN.

PR #460 is the current operational read-first branch.

PR #323 remains historical handoff custody and must not be used as the active successor.

## Current first actions for a new agent

1. Checkout/read PR #460 first.
2. Read PR #322 V8a complete file index before repository-wide historical searches.
3. Confirm current heads of PRs #457–#460 against this V8b delta.
4. Independently review PR #459. Preserve all #452 hostile tests and X1/X3 lineage.
5. Independently review PR #458's 13 RED against the exact repaired Task1/2 dependencies; do not begin Production Synthetic Task4.
6. Treat PR #457 only as external public reference context.
7. Do not reopen PR #438 Bayesian/four-world work, rebuild the post-TD harness, replay closed synthetic TD challenges, or invent real G7 provenance from caller-labelled atoms.
8. If any active head moves again, add **V8c** (or later) as another append-only delta. Never rewrite V8/V8a/V8b.

## Takeover rule

A future agent should spend time only on:

- a genuinely new defect;
- a changed dependency requiring requalification;
- an independently required review;
- a new authenticated external source;
- or an explicitly authorized next stage.

Everything else should first be classified against the complete historical audit index as:

`ALREADY_AUDITED | REJECTED_OR_CLOSED | SUPERSEDED | OPEN_DEFECT | CHANGED_INPUT_REQUIRES_REQUALIFICATION | AUTHORITY_NOT_EARNED`

Passing CI alone never changes the last category.
