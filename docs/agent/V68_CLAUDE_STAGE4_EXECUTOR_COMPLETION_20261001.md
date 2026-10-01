# V68 Claude Stage-4 executor completion instructions — 2026-10-01

Read:

- `results/v64/V68_CLAUDE_STAGE4_EXECUTOR_9F20_INDEPENDENT_AUDIT_V1.json`
- `results/v64/V68_FULL104_PRIVILEGED_EVIDENCE_COVERAGE_MAP_V1.json`

## Keep the strong work

Do not reopen S72–S75.

Preserve the S81/S82 consumer-semantics verifier and artifact-level mutation suite.

Preserve the synthetic finding that an unmeasured metacell-varying cross-modal factor can mimic biology. Do not tune Stage-4 thresholds after seeing that failure.

## Task 1 — close S84 / G16 custody

The executor is committed at head 9f20a6f with Git blob:

`01ce652cef8da70870489d74bb7763c3062521dc`

but the current preflight receipt still records `git_blob_at_head=null`.

Generate a post-commit identity/custody receipt that proves:

`stored executor SHA256 + stored Git blob + source_commit:path blob + worktree blob`

all agree.

Also bind the exact authority SHA/blob and frozen statistical/design contracts.

Commit that receipt, then regenerate only if necessary to bind the final executor build. Avoid an endless post-commit self-reference loop: the executor source identity must be stable before the receipt is written.

## Task 2 — finish the actual executor, but DO NOT RUN REAL STAGE 4

The current build stops with:

`authorised real execution is not implemented in this build`

Replace that with the real orchestration path behind the existing exact authorization gate.

The real path must:

1. load only the frozen Phase-B substrate;
2. run the exact consumer-semantics preflight before computation;
3. validate executor/authority/input custody;
4. emit a pre-computation provenance header;
5. compute per-donor/per-pair correspondence under the frozen method;
6. residualize using the frozen 14-term basis / ridge alpha 1 / promoter 5-fold cross-fitting;
7. compute GENE_BALANCED primary, PROMOTER_EQUAL mandatory companion, EDGE_EQUAL sensitivity;
8. preserve R1/R2/R3 semantics and the exact R3 conditional label;
9. run the frozen donor bootstrap (4000, seed 20260929);
10. reconcile all attrition/missingness/funnel counts;
11. write output only to the canonical output location, fail on overwrite;
12. never inspect or tune based on the output during implementation.

DO NOT create the authorization artifact and DO NOT execute the real path.

## Task 3 — test the real orchestration path on synthetic fixtures

The synthetic suite must exercise the SAME orchestration functions the future real run will call, not merely helper functions.

Use an internal test adapter or fixture object; do not add a CLI input-root or alternate contract flag.

Required properties:

- planted positive recovered;
- null remains null;
- measured technical confound residualizes;
- missingness paths remain exact;
- weighting hierarchy cannot be outcome-selected;
- Control B cannot become primary;
- R3 labeling exact;
- bootstrap deterministic;
- output overwrite refused;
- authorization absent -> real CLI refuses;
- wrong executor hash in authorization -> refuses;
- wrong authority hash -> refuses;
- wrong schema -> refuses;
- synthetic authorized execution can exercise the complete orchestration without touching real Phase-B outcome data.

## Task 4 — make the latent-confound limitation an explicit output interpretation boundary

The synthetic result:

- biological positive Delta ≈ +0.7854
- hidden within-donor metacell-varying confound Delta ≈ +0.6540
- control-vs-control ≈ 0

must be carried forward prospectively.

Do not modify the frozen design simply to make this fixture go away.

Any future Stage-4 result/authorization contract must explicitly state:

A Stage-4 positive result demonstrates correspondence under the measured nuisance basis and matched controls. It does NOT independently exclude an unmeasured technical variable that varies across metacells within donor and jointly affects RNA and ATAC.

Therefore Stage 4 is one regulatory-evidence leg, not standalone proof of biological state.

## Task 5 — stop before irreversible work

Desired end state:

`S81_S82_CLOSED__G16_BOUND__G17_BOUND__REAL_EXECUTOR_IMPLEMENTED_BUT_NOT_AUTHORIZED__CORRESPONDENCE_UNOPENED`

Then STOP for independent audit.

Do not:
- create a real Stage-4 authorization artifact;
- execute even one real donor/pair correspondence;
- inspect Delta/LCB/p-value on the real substrate;
- open Morabito;
- open recoverability TEST;
- start training.
