# JEPA Claude Work — External Review Handoff

Date: 2026-09-05
Audience: ChatGPT acting as external scientific and implementation reviewer
Status: `ADDITIVE_EVIDENCE_AWAITING_EXTERNAL_REVIEW`

## Scope and firewall

This memo summarizes Claude Code's recent JEPA work and Codex's read-only
reconciliation. It does not promote a new scientific authority.

- Real F1 has not been run and remains unauthorized.
- No DEV, SEALED, pathology, reader-validation, or reader-oracle expression was
  opened in this reconciliation.
- Historical result bytes and branches remain unchanged.
- Only the 104 `reader_fit` donors are lawful for the proposed next technical
  work.
- No agent may self-certify conclusion-bearing code.

## Repository state

Last fetched `origin/main`:
`76fe7d63efe81451ef0fae3ef3eaf116be14f6be`

Claude's newer work is distributed across review/evidence branches and is not
merged into `main`:

| Branch | Head | Current meaning |
|---|---|---|
| `f1b-minimal-bridge-20260905` | `f0fb23c2c520028fc4d8c18a32e197f03a1d7cf8` | Immutable descriptive F1-B v1 evidence |
| `review/f1b-independent-verifier-repair-20260905` | `a90fdc1339c7c71d8a27db4fdf391ed9d62f9104` | Independent STOP and repair requirements |
| `protected-program-family-audit-20260904` | `9a590b3a6774fd32c5456927de4438c31c73e6a7` | Outcome-blind construct audit |
| `review/protected-program-independent-verifier-20260905` | `60eb96cf5399f84ff3b30e145d751410f380662e` | Independent verifier implementation |
| `review/pre-f1-mechanism-repair-20260905` | `02907fb27f3e41fc03e01451d11b014b89b78493` | Historical-mechanics review packet |
| `review/f1-three-valued-report-schema-20260905` | `b42907fbc61f2717678109f30961f6e038678abe` | Report visibility only, not true three-valued adjudication |
| `review/f1-byte-authority-portability-20260905` | `7715a53` | LF source LF-byte pinning |

Codex's pre-existing real-F1 executor repair worktree is preserved but paused.
Its scientific contract predates the findings below and must not be promoted
without reconciliation.

## Package integrity independently checked by Codex

### Comprehensive handoff

File: `JEPA_COMPREHENSIVE_HANDOFF_20260905.zip`
ZIP SHA-256:
`28f99ae682b4a5718a2c0725cb342e8a00372cb6b3f0e84cb37e0d48a350842f`

- 230 ZIP entries.
- 227/227 manifest rows independently rehashed.
- Zero missing members, byte-count mismatches, or SHA-256 mismatches.
- Declared package root:
  `56d54977c7870aa52f810fda39c329fd9b1bb45f801413e4f8c97f1e00b894c0`.

### C0 canonical export

File: `JEPA_C0_CANONICAL_EXPORT_20260905.zip`
ZIP SHA-256:
`9d5dd0ef598a017125b428336b1932c4e6c39d7d951776b21881717b591ccbcf`
Declared export root:
`51baedc071b9a2dfc17cbab8622b859e0abf5c5fc0c177357e3b84af38e8fd1b`

All five shipped members match both the ZIP manifest and existing local bytes:

| Authority | SHA-256 | Bytes |
|---|---|---:|
| F1 recipient authority | `32437e5ebb01deb8fad771f8b2d4d9bd2b62b061f89c1e79fdbc6629d11af9fe` | 2,404,675 |
| Two-draw assignments | `12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617` | 30,660,013 |
| HC3 selected design, float64 little-endian | `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3` | 13,312 |
| HC3 design schema | `d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778` | 5,966 |
| Recovered `full104_model_components_v2.py` | `c69ed6abb68f31e6177170ebafa1b412b0780d47d83e00776707a4c8cd4ae342` | 7,494 |

The unshipped 73,380,694-byte rare scoring basis was independently verified in
place at SHA-256
`5ddee92a83cd4f54ae61a6c9ed192847ac8f941f725e5a5678512460f5308b84`.

The exact successor component source is therefore recovered, not
reconstructed. Its required `DIRECT_INIT_MANIFEST.json` and corresponding
direct-head assets remain unresolved.

## Finding 1 — historical T1 attention path did not train

Independent checkpoint archaeology binds optimizer parameter order to the
historical constructor. At u10/u25/u50/u100/u200/u205:

- all 48 `{attention_norm, query, key, value} x 6 blocks` tensors have both Adam
  moments exactly zero;
- all 12 attention-output tensors have nonzero moments;
- Q/K/V and attention-normalization movement is approximately decoupled weight
  decay only;
- loss reduction and pooled gradient telemetry therefore did not demonstrate a
  live context-mixing path.

This materially narrows the historical interpretation: additional replay,
inventory, or updates alone would not repair the demonstrated mechanism defect.

## Finding 2 — C2 reproduced the signature with historical execution geometry

Claude ran the historical execution structure on synthetic expression:

- 41,238 addresses;
- effective batch 128;
- microbatch 8;
- four views;
- 16 microbatches x 4 views = 64 backwards;
- fp16 autocast, GradScaler, gradient checkpointing;
- authenticated u0 architecture, `BlockPredictor`, and `block_jepa_loss`.

Reported result:

- all 48 mandatory attention-normalization/Q/K/V gradients are exactly zero at
  backward 1, 4, 8, 16, 32, and 64;
- they remain zero before and after unscale;
- their Adam moments remain zero after the step;
- attention-output, FFN, other encoder, and predictor gradients are live;
- no nonfinite gradients were reported.

Artifact:
`outputs/_private_c2_t1_forensic_20260905/C2_T1_ACCUMULATION_FORENSIC.json`.

### Evidence limitation

The C2 JSON is untracked and unmanifested. The exact harness source, invocation,
input hashes, and environment manifest were not preserved beside it. The result
is compelling `PROVISIONAL` causal evidence, but is not yet sufficient to amend
DEC-013 or authorize a repaired training arm.

The precise severing operation remains unknown. Candidate differences between
the healthy simplified probe and defective historical-scale route are:

1. FP32-forced versus autocast loss inputs;
2. reduced versus full 41K token count;
3. no loss division versus division by views and microbatches;
4. teacher mask construction;
5. target-block construction and batch geometry.

The next experiment should reproduce both endpoints in one preserved harness and
toggle one prospectively declared factor at a time.

## Finding 3 — the architecture is not yet falsified

A separate bounded four-condition AMP x checkpointing probe produced nonzero
attention-path gradients. Thus AMP and gradient checkpointing alone do not
explain the historical failure. This does not contradict C2 because the probe
used a simplified, smaller, single-backward workload.

The current evidence supports `HISTORICAL_FULL_SCALE_PATH_DEFECT_REPRODUCED`, not
`ATTENTION_ARCHITECTURE_INTRINSICALLY_UNTRAINABLE`.

## Finding 4 — local geometry was compression limited

The original 512-dimensional FOUNDATION neighborhood result should not be read
as absence of local biological structure. Corrected recall@30 rose monotonically
with sketch dimension:

| Dimension | Recall@30 |
|---:|---:|
| 512 | 0.09345 |
| 1,024 | 0.15023 |
| 2,048 | 0.23114 |
| 4,096 | 0.34650 |
| 8,192 | 0.47124 |

At 8,192, reported within-donor recall was 0.84531, between-donor recall 0.47525,
CKA20 0.99871, and mean canonical cosine 0.98218.

Boundary: 8,192 is not proven optimal, and improved expression geometry does not
by itself qualify a disease-relevant rare state. The historical rare audit used
different RNA/LEDGER/PCA/REP isolation semantics, so the 512 CountSketch result
does not causally explain that rare-audit outcome.

## Finding 5 — protected-program construct is not eight independent directions

The outcome-blind audit reports:

- eight gated labels;
- numerical rank seven by SVD and pivoted QR;
- `core_halo = 0.5773503 * local_core + 0.8164966 * local_halo` to numerical
  precision;
- `innovation_tail`, `recurrent_5pct`, and `recurrent_1pct` have byte-identical
  raw and L2 molecular weight vectors.

Rare5 and rare1 remain distinct cell-level threshold roles on the same
innovation score; they are not distinct molecular directions.

Claude reports canonical execution of the independent protected-program
verifier as `PASS_PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER`. Codex verified
the verifier branch and underlying authority hashes, but did not find a separate
hash-bound canonical-run result artifact. Require durable publication before
promotion.

## Finding 6 — current F1 truth table does not gate program-level positivity

Two critics report reproducing a payload where five of eight protected programs
have two-sided 95% intervals entirely below zero while all 11 current gates still
pass. The current arithmetic computes protected-program positive Holm values but
labels them report-only; the gates enforce estimability and comparative
non-degradation, not positive program level.

This is a claim-definition issue, not a small implementation patch. Before real
F1, external review should decide whether the intended claim requires:

- positive evidence in each protected program;
- a prospectively defined subset/family rule; or
- an explicitly weaker claim that does not promise per-program positivity.

No rule should be selected after real outcomes are inspected.

## Finding 7 — 100% evidence is structurally degenerate for the evidence slope

Across tested operator/query fixtures, teacher and correct-student forwards at
100% evidence were reported bit-identical. This is expected from the current
mask semantics, but the 100% point receives the largest positive centered
coefficient in the evidence-slope calculation.

Recommended prospective distinction:

- retain 100% identity as a mechanics-integrity assertion;
- do not automatically treat it as conclusion-bearing evidence-response data.

External review must approve the exact replacement evidence-trend estimand
before any outcome is opened.

## Finding 8 — F1-B v1 is descriptive and independently stopped

The original 300-update synthetic result shows:

- healthy gradients in that implementation;
- predictor routing can sharpen while backbone routing remains diffuse;
- selective predictor routing is mechanically possible;
- useful biological retrieval is not established.

Its formal independent review remains:
`STOP_F1B_INDEPENDENT_VERIFICATION_REPAIR_REQUIRED`.

Twelve named implementation/contract defects are preserved:

1. G1 accepts nonfinite gradients.
2. G2 can accept a zero second moment.
3. Mean G3 movement can hide a decay-only tensor.
4. Predictor mechanics are not gated.
5. Backbone routing uses cell-0 support.
6. Backbone routing uses cell-0 queries.
7. Predictor routing uses cell-0 support.
8. Movement family incorrectly includes attention normalization.
9. Near-zero baseline tensors are skipped.
10. Optimizer step occurs before mandatory gradient STOP enforcement.
11. Real G5 implicitly loads every `l2__*` endpoint.
12. The published 300-update trajectory exceeds the frozen 40-update formal
    horizon.

The historical branch must remain immutable. Any repair is a new implementation
generation with new hashes and fresh verification.

## Finding 9 — reporting repair is incomplete

The `f1-three-valued-report-schema` branch adds existing direct-program and
QID-program reports to output without changing gate arithmetic. This improves
visibility but does not yet implement genuine three-valued scientific states.

The required semantics remain:

- `PASS` when the claim is estimable and passes;
- `FAIL` when estimable and contradicted;
- `NOT_MEASURABLE` when the assay/design cannot adjudicate it;
- terminal qualification remains fail-closed.

## Corrections that must not be propagated

- The balanced 2,781 x 8 x 2 F1 design does not overweight the 72-address
  core+halo endpoint through `/8`; equal program averaging is numerically
  identical to the balanced assignment mean.
- The F1 population contains 118 immune-lineage cells, approximately 4.24%, not
  “one microglial cell.”
- The protected-program family cannot be expanded at decision time because the
  exact payload pins the eight names; the Holm dimensionality concern is a
  prospective construct issue, not a runtime injection exploit.
- SEA-AD region equals technical operator/matrix in the current data. Regional
  classification is therefore a region/operator sensitivity control, not pure
  anatomical biology.
- Lower loss did not mean unchanged biology: historical rare-1% AP reportedly
  declined from 0.12136 to 0.09331 while loss continued falling.
- The historical encoder optimizer is recorded in the checkpoint at
  `lr=1e-4`, `weight_decay=0.01`; a separately cited `lr=3e-3` line belongs to
  the downstream reader probe, not the encoder.

## Public split-registry note

Public `main` contains named split membership and the original split seed. The
user has clarified that the underlying donor metadata was already public and is
not considered a privacy emergency. The remaining issue is narrower scientific
blinding: strict claims that SEALED membership was unknowable are no longer
defensible. Do not rewrite history. If a future claim requires a concealed
holdout, prospectively create a new split and record the old limitation.

## Codex/Claude continuity work

Codex created a clean isolated worktree at:
`D:/jepa_peer_handoff_20260905`

Base: `origin/main@76fe7d63efe81451ef0fae3ef3eaf116be14f6be`
Branch: `jepa-peer-handoff-20260905`
Peer-agent design commit: `0da73ee`

The approved design treats Codex and Claude as equal implementation agents.
Neither may self-promote scientific work. A persistent machine-readable
checkpoint, shared execution plan, and restricted direct Claude CLI consultation
bridge will allow either agent to resume the same worktree without chat history.

## Proposed dependency-ordered next work

1. Implement the peer-agent continuity/checkpoint system.
2. Rebuild C2 as a preserved, hash-bound synthetic bisection harness.
3. Name and regression-test the exact gradient-severing condition.
4. Prospectively amend the interpretation of DEC-013 only after verification.
5. Freeze a successor F1 claim contract addressing program sign,
   non-measurability, seven-direction dependence, and evidence=100 degeneracy.
6. Create a new F1-B mechanics generation addressing all twelve verifier defects.
7. Run the mandatory independent verifier.
8. Run exactly 40 synthetic updates, then the production AMP smoke and
   singleton-q/all-Q target audit.
9. Freeze checkpoint-refit donor-heldout G5 and matched real-RNA R1/R2 before
   considering real F1.

Routine implementation uses no agents. At most one independent verifier is used
at a conclusion-bearing promotion boundary unless unresolved scientific dissent
requires a broader board.

## Questions for external review

1. Is C2 correctly classified as `PROVISIONAL_REPRODUCTION` pending preserved
   source/input/environment provenance?
2. Is one-factor-at-a-time C2 bisection the correct immediate scientific task?
3. Does the current F1 claim require per-program positive evidence, or should its
   claim scope be narrowed instead?
4. Should evidence=100 be mechanics-only, and what prospective nondegenerate
   evidence-response estimand should replace the current slope?
5. How should the seven molecular directions and eight named endpoint roles be
   handled without erasing the distinct core/halo and rare-threshold semantics?
6. Are the twelve F1-B verifier defects complete enough to specify a successor
   implementation generation?
7. Does any reviewed evidence justify real F1, fresh-u0 training, or architecture
   promotion now? Codex's current answer is **no**.

## Requested external terminal

Return one of:

- `PASS_TO_IMPLEMENT_CONTINUITY_AND_C2_ONLY`
- `REPAIR_EXTERNAL_REVIEW_HANDOFF`
- `STOP_FOR_AUTHORITY_CONFLICT`

Even a PASS does not authorize real F1, protected-expression access, or training.
