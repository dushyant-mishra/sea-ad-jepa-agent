# V29 Lane A — Teacher-target decision sheet, V1

Date: 2026-09-26
Document version: `LANE_A_TEACHER_TARGET_DECISION_SHEET_V1`
Role: `NON_AUTHORIZING_SCIENCE_DECISION_REQUEST` — this sheet decides nothing and permits nothing.
Branch: `lane-a/v29-teacher-target-decision-20260926`, built on `main` @ `c49b13bd75c2d23716c777336db8fbfc78c09cd0`.
Companion machine-readable file: `JEPA_V29_LANE_A_TEACHER_TARGET_PROPOSAL_V1_20260926.json`.

This is a **companion** to PR #152 (`planning/v29-prospective-teacher-science-20260926`). It does not replace it,
re-issue it, or compete with it. Section 1 states exactly which parts of PR #152 this sheet adopts unchanged and
which dimensions it opens.

---

## 0. Read this first — what the owner must decide

A few words defined once, then used freely:

- **Teacher / student.** Two copies of the same network. The *student* sees a deliberately incomplete cell and
  tries to predict something. The *teacher* produces the thing to be predicted. The teacher is never trained
  directly; it is a slowly-updated running average of the student, which is what **EMA** (exponential moving
  average) means.
- **Latent state / embedding.** A vector of numbers the network computes to describe something. "Latent" only
  means it was learned rather than measured. It is not automatically biology.
- **Query.** The one molecular address (gene) we hide and ask about.
- **Query scalar.** That gene's actual measured count in that cell — the number we are hiding.
- **Contextual mixing.** The self-attention step where every gene's token is allowed to look at every other gene's
  token. After mixing, information is smeared across all positions. Anything present *before* mixing is present
  *everywhere* after it.
- **Stop-gradient.** A wall that lets a number be used as a training signal without letting training change where
  that number came from.
- **Leakage.** Any route by which the answer reaches the thing that is supposed to be guessing it.

**The scientific goal, as the owner stated it:** predict the *query-local latent cellular state* associated with a
hidden gene, using the remaining observed RNA. Explicitly **not**: reconstructing the hidden gene's count, and not
predicting source, donor identity, QC metrics, or measurement support.

**The central finding of this sheet.** The construction that exists in the codebase today, and the construction
PR #152's checker currently enforces as a constant, both let the hidden gene's count into the teacher **before**
contextual mixing. Once that happens, the teacher's output at the query position is a deterministic function of the
number we are hiding, pushed through a few attention layers. Training the student to match it is scalar
reconstruction wearing a latent-state costume. It is not "no scalar regression"; it is *indirect* scalar
regression. This is a legitimate design choice that some projects make deliberately — but it is the opposite of
the owner's stated goal, and it is currently being made silently, by a default and by a checker constant rather
than by a decision.

**Good news or bad news, plainly.** This is good news, and it was found before any training run. Nothing has been
trained, no result is invalidated, no published claim is affected, and no protected data was touched. What it costs
is one decision and a small amount of tokenizer work: the teacher needs to be able to accept a gene whose value
slot is blanked. What still stands, entirely untouched: the FULL104 substrate and its counts, every measured
Layer-2 result, the 2026-09-16 masking findings, the EMA / optimizer / checkpoint mechanics, and the whole
governance chain.

### The decisions, ordered by how much else they determine

| # | Decision | Options | Why it matters at this position |
|---|---|---|---|
| **D0** | Per-cell value-normalization rule | `N_RAW_MASK_INDEPENDENT` / `N_FROZEN_REFERENCE_SET` / `N_VISIBLE_SET_RECOMPUTED` / `N_TOTAL_COUNT_INCLUDING_QUERY` | The last option is the field-standard default, and it leaks the query scalar into **every other token** — defeating all four candidates below no matter which is chosen |
| **D1** | Where the query scalar is withheld from the teacher | `T_A` / `T_B1` / `T_B2` / `T_C`, with optional modifier `T_D` | This *is* the target construction. Everything else is downstream of it |
| **D2** | Teacher context breadth | `TEACHER_HIDES_QUERY_ONLY` / `TEACHER_HIDES_FULL_MASK` | Decides whether the target carries information the student cannot have, or only a smoothed echo of the student's own input |
| **D3** | How query identity is supplied | `Q1_SHARED_TRAINABLE` / `Q2_FIXED_CODE` / `Q3_DETACHED_ONLINE`, plus teacher-side `QT_EMA_IDENTITY` / `QT_FIXED_CODE` | The project already carries the open blocker `TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED` |
| **D4** | Target read-out and normalization | `R1_RAW` / `R2_LAYERNORM` / `R3_BLOCKMEAN_LAYERNORM` / `R4_L2_UNIT` | Decides whether the evaluation metric can be bounded, which decides whether any relative threshold is meaningful at all |
| **D5** | Target granularity | `ADDRESS_LEVEL` / `BLOCK_LEVEL` | Block-level inherits an unresolved blocking authority — the 2026-09-16 grid produced no qualified rule |
| **D6** | Measurement-state channels | `SEPARATE_DETACHED_AUXILIARY_OUTPUTS` / `ABSENT` — never `INPUT_TO_PRIMARY_PATH` | Visibility alone predicts Q_DETECT at about 0.977 in V0; as an input it is a shortcut, as a detached output it is a control |
| **D7** | Pre-training teacher-only target screen | run / skip, and its (UNSET) bar | A cheap check that can disqualify a candidate before a single training step |
| **D8** | Numeric margin for every control | all `UNSET_REQUIRES_APPROVAL` | The *direction and pairing* of each control are proposed frozen here; only the sizes are open |
| **D9** | Whether PR #152's checker keeps `query_scalar_teacher` as an enforced constant | keep / demote to a decision field | As written it hard-codes candidate `T_A` and makes `T_B1`, `T_B2` and `T_C` unrepresentable |

Everything the assignment requires to be left unset — mask fraction, training population and split, model
width / depth / heads, EMA half-life, optimizer settings, seeds, update budget, and every numerical evaluation
threshold — is recorded as `UNSET_REQUIRES_APPROVAL` in the companion JSON and is **not** proposed here.

**Nothing in this sheet is selected.** Four candidate constructions are presented with their trade-offs. The owner
chooses.

---

## 1. Classification against PR #152 — what is already done, what is genuinely open

PR #152 = `planning/v29-prospective-teacher-science-20260926`: one decision-request JSON, one reviewer memo, one
fail-closed checker (`scripts/v5/v29_teacher_decision_firewall.py`), and 15 tests including a non-authorizing
positive control.

| Element | PR #152 | Classification | Lane A action |
|---|---|---|---|
| Non-authorizing posture; explicit `false` authority flags | present, checker-enforced | **ALREADY_DONE** | adopt by reference; add nothing |
| Unset parameters held at `null` (split, mask, geometry, EMA, optimizer, seed, budget, thresholds) | present; `REQUIRED_NULL` groups enforce it | **ALREADY_DONE** | adopt; mirror only the fields Lane A newly introduces |
| Rejection of `0.40` mask, `0.99` / `0.996` EMA, historical width / depth / batch, old-94 population | present as spillover tests | **ALREADY_DONE** | adopt, and re-assert inside Lane A's own checker so the two files cannot silently drift apart |
| 2026-09-16 nine-cell grid recorded as `NINE_CELL_GRID_NO_QUALIFIER` | present | **ALREADY_DONE** | adopt verbatim |
| Governance seals (pathology, reader_oracle, foundation, `D_shared`/G5, N1, therapeutic ranking) | present | **ALREADY_DONE** | adopt verbatim |
| Statement of the biological question | one paragraph | **ALREADY_DONE** | cited, not restated |
| FULL104 substrate digests and counts | present and pinned | **ALREADY_DONE** | cited, not recomputed |
| **Competing target constructions** | **absent** — exactly one construction is asserted | **GENUINELY_OPEN** | §3: four candidates across three axes |
| **Per-candidate mechanism** — teacher inputs, identity supply, scalar-withholding point, mixing operation, stop-gradient boundary, exact target formula | **absent** — enum labels such as `STRICT_MEASURED_SCALAR_RNA_INCLUDING_QUERY__LAWFUL_CONTEXT_ONLY__PROPOSED` name a position without specifying a mechanism | **GENUINELY_OPEN** | §3, one full specification per candidate |
| **Query scalar in the teacher** | pre-selected as `query_scalar_teacher = MAY_ENTER_TARGET_ONLY__NO_DIRECT_SCALAR_REGRESSION`, and the checker *requires* the substring `NO_DIRECT_SCALAR_REGRESSION` to be present | **SUPERSEDED_AS_SOLE_OPTION** | §2 and D9: must become a decision field, not a checker constant |
| **Controls with a disqualifying outcome** | six control *names*; `minimum_effect_threshold: null`; no failing outcome attached to any of them | **GENUINELY_OPEN** | §5: every control gets an explicit falsifying result |
| **Remaining-RNA necessity procedure** | flagged `remaining_rna_ablation_required: true`, root `null`; no procedure given | **PARTIALLY_DONE** | §5 C4: three substitution levels, with the depth-preserving one as primary |
| **Seam-by-seam leakage enumeration** | prose risk classes | **GENUINELY_OPEN** | §4: fourteen enumerated paths, each with detection and repair |
| **Measurement-state channels as separate outputs** | input-side statements only (`support_states`, `operator_source`) | **GENUINELY_OPEN** | §4 L5 and D6: an architectural constraint, not a metric |
| Positive control in tests | `test_complete_original_proposal_is_non_authorizing_positive_control` — a positive control for the *document* checker | **ALREADY_DONE for that scope** | Lane A adds its own positive control for the *candidate-space* checker, and requires a planted-signal fixture in §5 C5 |

**Plain summary.** PR #152 gets the governance and the negative space right — it is a good statement of what is
*not* decided. What it does not contain is the science of the decision itself: the competing things the target
could be, how each one physically withholds the answer, and what measurable outcome would kill each one. That is
the whole of Lane A's addition. Two elements of PR #152 need owner attention rather than adoption: the
pre-selection of the teacher's query-scalar position (D9), and the absence of any failing outcome behind the six
control names (D8).

---

## 2. What exists in the code today, and why it is not the stated goal

These are facts about files at `main` @ `c49b13bd`, not opinions.

**The token.** `src/sea_ad_jepa/v4/gene_tokenizer.py`:

    token_g = LayerNorm( identity_projection(E_id[g]) + value_encoder(x_g) )

A gene's token is its learned identity vector plus an encoding of its value. The value enters at layer 0.

**The teacher call.** `src/sea_ad_jepa/v5/inactive_update_reference.py`, line 167:

    teacher_state = modules.teacher(pt.canonical_gene_ids, pt.expression, true_t,
                                    torch.zeros_like(true_t), 'target', ...)

The fourth argument is the hidden-target mask. It is `torch.zeros_like(true_t)` — **nothing is hidden from the
teacher**. The teacher receives the full measured support, the query's real value included.

**The view rule.** `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`, line 67:

    safe_expression = expression.masked_fill(~gene_valid, 0.0)
    gene_valid      = measurement_mask & ~hidden_target_mask

For the student, hidden addresses are zeroed *and* marked invalid in the attention mask. For the teacher
`hidden_target_mask` is all zeros, so `gene_valid = measurement_mask` and every measured value, query included, is
tokenized and attended over.

**The target.** `src/sea_ad_jepa/v4/ipb_jepa.py`, lines 311–320:

    zT_ib = LayerNorm( mean over g in B_ib of  H^T_ig )

the layer-normalized mean of the teacher's *final* per-gene states across the target block.

**Therefore.** `H^T_iq` — the teacher's final state at the query position — begins at layer 0 as
`LN(identity(q) + value_encoder(x_iq))` and is then mixed with everything else. The target is a smooth function of
the number we are hiding. A student that matches it well has, to the extent the teacher's map is invertible,
recovered the hidden count. The loss is not an L2 on `x_iq`, so "no direct scalar regression" is literally true; it
is nonetheless scalar recovery by another route.

And the four controls named in PR #152 cannot tell the two apart, because a model that recovers `x_iq` **also**
beats identity-only, **also** beats global-context-only, **also** beats technical-only, and **also** collapses when
the remaining RNA is removed. The leak is invisible to exactly the instruments meant to find it. That is why the
candidate space below is organized around *where* the scalar is withheld, and why the withholding point has to be
before the first attention layer rather than after it.

---

## 3. The candidate target constructions

### 3.0 Shared notation and invariants

- Cell `i`; its identity is `selection_row` from the physical block metadata — never block order, shard key, or an
  enumeration counter. Donor identity is the donor ID string.
- `M_i` — strictly measured support (a value was reported; measured zeros included). `U_i` — structurally
  unmeasured (not in the assay's reference). Collision-unresolved addresses are excluded from both.
- `x_ig` — the raw integer count. `x~_ig = h(x_ig ; s_i)` — the normalized value actually handed to the tokenizer.
  **`h` and `s_i` are decision D0 and are not fixed by the tokenizer.**
- `H_i` subset of `M_i` — the hidden set. `q` in `H_i` — the query. `V_i = M_i \ H_i` — the remaining observed RNA.
- `f_theta` student encoder; `f_phibar` teacher encoder with `phibar <- m*phibar + (1-m)*theta`; `p_psi` predictor.
- Invariants required of every candidate, inherited from the existing audited mechanics and not re-opened here:
  teacher parameters carry no gradients and are absent from the optimizer's parameter set; the target is detached
  before entering the loss; EMA advances **only** after an accepted optimizer step and never after a skipped one;
  the existing gradient chain is reused unchanged —
  `FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_GRADIENT_GATE ->
  OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE ->
  SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`.
- Mask eligibility depends **only** on declared support, never on the realized value (§4 L3).
- Deterministic randomness is keyed from scientific identity — `(selection_row, donor_id, canonical_address,
  presentation_index)` — never from block, shard, or file order.

### 3.1 Candidate `T_A` — QUERY_VALUE_IN_TEACHER (what exists today; PR #152 as written)

| Aspect | Specification |
|---|---|
| Teacher molecular inputs | every `g` in `M_i` with its value `x~_ig`, **query included** |
| Query identity supplied to student | predictor query = mean of target-gene identity embeddings projected to model width, plus a learned block-mask parameter (`BlockPredictor`) |
| **Where the query scalar is withheld** | **from the student only.** Student sees `V_i`; hidden addresses are zeroed and marked invalid. The scalar is **not** withheld from the teacher at any point |
| Contextual mixing | teacher self-attention over `|M_i|` gene tokens plus a cell token. The query's value is present before the first attention layer and is therefore smeared across every position |
| Stop-gradient boundary | `zT` detached; teacher parameters `requires_grad_(False)`; optimizer holds online encoder and predictor only; EMA after an accepted step |
| Exact target | `zT_ib = LayerNorm( (1/|B_ib|) * sum over g in B_ib of H^T_ig )` |
| **Leakage verdict** | **the answer is in the target by construction** (§4 L1). Contradicts the stated goal |

*In favour:* the only candidate with an executable reference path today; the most informative target; the least
collapse-prone; and it matches image-JEPA practice, where the teacher does see the masked patches.

*Against:* it measures scalar recoverability, not query-local state; **none of the four required controls can
detect this failure**, because scalar recovery passes all four; and the resulting claim would have to be worded as
"predicts a contextualized encoding of the hidden count", which is not the claim the project exists to make.

### 3.2 Candidate `T_B1` — VALUE_BLIND_QUERY_SLOT, TEACHER_HIDES_QUERY_ONLY

| Aspect | Specification |
|---|---|
| Teacher molecular inputs | every `g` in `M_i \ {q}` with its value; **plus** a query slot token `LN( identity_projection(E_id[q]) + m_val )`, where `m_val` is a single learned vector shared across all addresses and all cells and carries no information about `x_iq` |
| Query identity supplied | to the teacher through the query slot's identity component; to the student and predictor through D3 |
| **Where the query scalar is withheld** | **at tokenization, before layer 1.** The value channel of the query token is replaced by `m_val`. No attention layer ever sees `x~_iq` |
| Contextual mixing | teacher self-attention over the `M_i \ {q}` value-bearing tokens, the value-blind query token, and the cell token |
| Stop-gradient boundary | as §3.0; additionally `m_val` on the teacher side is updated only by EMA, never by the optimizer directly |
| Exact target | `zT_iq = readout( H^T_iq )`, readout per D4 |
| **Leakage verdict** | closes L1 at the tokenizer. Remaining exposure: L2 (normalization), L9 (a correlated partner is still visible to the teacher), L8 (the identity component of the target) |

*In favour:* the most literal realization of "the query-local latent cellular state associated with a hidden gene,
using the remaining observed RNA". The teacher's advantage over the student is *other genes' real values*, never
the query's, so the target is asymmetric and non-trivial without being contaminated.

*Against:* it requires tokenizer work that does not exist today — a value-withheld token path in the teacher. The
target is seeded by `E_id[q]` plus a constant, so a larger share of its variance may be address-constant, which
makes control C1 the decisive test rather than a formality. And the teacher is given a strictly easier problem than
the student — it hides one gene, the student hides all of `H_i` — so the target may be systematically "too easy to
be worth predicting" in a way only C1 and C2 can reveal.

### 3.3 Candidate `T_B2` — VALUE_BLIND_QUERY_SLOT, TEACHER_HIDES_FULL_MASK

Identical to `T_B1` except the teacher's context is `V_i = M_i \ H_i` — the student's own visible set — with the
query supplied as a value-blind slot.

*In favour:* removes teacher/student view asymmetry entirely as a confounder. The target depends only on
information the student also has, so any gap between student and teacher is attributable to capacity and EMA
smoothing rather than to privileged data. It is the cheapest candidate to reason about.

*Against:* the target becomes a smoothed function of exactly the student's own inputs. This is the classic collapse
geometry — the student can approach the target by reproducing its own EMA, without the target carrying any
query-local content at all. Control C2 and the §3.7 pre-training screen are load-bearing here, and if either fails
this candidate dies. The target also now depends on the mask, so it moves as `H_i` is redrawn (§4 L13).

### 3.4 Candidate `T_C` — BLOCK_NEIGHBOURHOOD_TARGET, WHOLE_BLOCK_VALUES_WITHHELD

| Aspect | Specification |
|---|---|
| Teacher molecular inputs | every `g` in `M_i \ B_ib` with its value; **every member of the target block** supplied as a value-blind slot |
| **Where the query scalar is withheld** | at tokenization, for the whole block, before layer 1 |
| Exact target | `zT_ib = LayerNorm( (1/|B_ib|) * sum over g in B_ib of H^T_ig )` — the existing V4 target *shape*, with the block's scalars removed from the teacher's context |

*In favour:* keeps the existing block-summary target shape, so the existing `BlockPredictor` query geometry
survives; averaging over block members makes the target less noisy than a single address; and it partially
mitigates L9, because a correlated partner *inside the block* is blinded too.

*Against:* "query-local" becomes "block-local" — a per-address question is no longer answerable. And it inherits an
**unresolved** blocking authority. The 2026-09-16 frozen (K, R) grid was exhausted across all nine cells with no
qualifier. Under metric D at 600 addresses: uniform baseline exposure 0.1946; historical pooled-Pearson **0.2129,
i.e. 9.4% worse than uniform**, with structural expansion 12.5; donor-recurrent 0.1853 (−4.8%); source-balanced
recurrent 0.1947 (+0.0%). The contract required a reduction of at least 20%. A structural expansion of 1.0 for both
recurrent candidates means the dependency-aware component contributed nothing. Choosing `T_C` therefore imports an
open blocker rather than resolving one.

### 3.5 Modifier `T_D` — RESIDUALIZED_TARGET (applies on top of `T_A` only)

`zT_iq_perp = zT_iq - ghat(x_iq, support_state(q))`, with `ghat` a fitted map from the realized scalar to the
target.

*In favour:* keeps `T_A`'s informative target while attempting to strip the leak, with no tokenizer change.

*Against:* this is a nuisance-removal estimator, and the project's standing rule is that such an estimator must
first be run on a controlled fixture that contains the nuisance structure and **zero** query-local signal, and
shown to report approximately zero, before any real use. Removing a scalar from a `d`-vector is only ever
"complete" in a fitted sense; whatever the teacher's nonlinearity leaves behind is still leak, and it is not
observable from the residual itself. **Recommended posture: diagnostic only.** It is listed as a modifier, not a
primary candidate, and should not be selected without both a null fixture and a planted-signal fixture passing.

### 3.6 Orthogonal axes — these multiply with the candidate chosen above

**Axis D3 — how query identity is supplied.** The project already carries the open blocker
`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`, whose path is
`target identity -> predictor query -> JEPA gradient -> online identity table -> EMA teacher -> future target`.

| Option | Mechanism | Trade-off |
|---|---|---|
| `Q1_SHARED_TRAINABLE` | predictor query built from `modules.online.tokenizer.gene_identity` (current) | the identity table is in the optimizer's parameter set, so the target can be reshaped to suit the query. The direct path is open |
| `Q2_FIXED_CODE` | a deterministic, replay-stable, non-trainable code per canonical address | closes the direct path entirely. The external precedent is I-JEPA's `predictor_pos_embed` with `requires_grad=False`, which establishes only that address conditioning and content representation *need not* share trainable parameters — it is not authority for a gene architecture. Cost: the code carries no learned similarity structure, so the predictor must learn address relationships from scratch and may need more capacity |
| `Q3_DETACHED_ONLINE` | `stopgrad(E_id[q])` | breaks the direct gradient but not the indirect coupling — the table still moves because the encoder uses it, and the EMA teacher follows it. **Diagnostic only**; do not treat it as safe merely because gradients are stopped |
| teacher-side `QT_EMA_IDENTITY` vs `QT_FIXED_CODE` | whether the teacher's own value-blind query slot uses the teacher's EMA identity table or the same fixed code | if the teacher's slot uses a moving identity, the address-constant share of the target grows over training, so C1 must be re-measured at several training points rather than once |

**Axis D4 — target read-out.** `R1_RAW` / `R2_LAYERNORM` (inherited) / `R3_BLOCKMEAN_LAYERNORM` (inherited V4) /
`R4_L2_UNIT`. This is not cosmetic. A relative-improvement threshold is only meaningful on a metric that is bounded
in the rewarded direction. `R4_L2_UNIT` makes cosine similarity the natural score, bounded in `[-1, 1]`, and makes
every paired delta in §5 interpretable. `R1_RAW` leaves the metric unbounded and would force absolute rather than
relative thresholds. LayerNorm removes scale from the target, and whether that scale is biology or sequencing depth
is itself unresolved — so `R2` and `R3` discard something whose nature is not yet known.

**Axis D0 — value normalization.** See §4 L2. It is listed first in the decision table because the common default
silently defeats all four candidates.

### 3.7 A cheap screen that can disqualify a candidate before any training

For a chosen candidate, run the **teacher alone** — randomly initialized or at any checkpoint, with no student, no
optimizer and no gradient — over a lawful development sample, and compute, per cell, the variance of `zT_iq`
**across queries within the cell**, against the variance of `mean_q zT_iq` **across cells**.

If the within-cell across-query variance is negligible relative to the across-cell variance, the "query-local
state" is a cell-level object wearing a query label, and no amount of training will make it query-local. This costs
one forward pass, needs no training authority, and can kill `T_B2` or a badly-chosen read-out before anything
expensive happens. Its pass bar is `UNSET_REQUIRES_APPROVAL`; the *direction* — within-cell across-query variance
must be non-negligible — is proposed frozen.

---

## 4. Leakage analysis — every path by which the answer can reach the student

Detection and repair are given for each. Paths marked **open** are not currently mitigated anywhere in the repo.

| # | Path | Mechanism | Affects | Detection | Repair |
|---|---|---|---|---|---|
| **L1** | **Query scalar into teacher contextual layers** | `x~_iq` is tokenized at layer 0 and self-attention smears it everywhere; the target is then a function of it | `T_A` by construction; `T_C` if the block is not blinded | static: read the teacher's hidden-mask argument — today it is `torch.zeros_like(true_t)`. Dynamic: perturb `x_iq` alone and measure the change in `zT`; under `T_B*` it must be exactly zero | value-blind query slot (`T_B1`, `T_B2`, `T_C`) — withhold **before** the first attention layer |
| **L2** | **Query scalar via per-cell value normalization** | if `s_i = sum over g in M_i of x_ig` (total-count normalization, the field default), every visible token's `x~` depends on `x_iq`. Dropping the query *token* does not remove this. It leaks into the student as well as the teacher | **all candidates** | perturb `x_iq` and check whether any *other* address's `x~` changes; it must be bit-identical | `N_RAW_MASK_INDEPENDENT` (no per-cell scaling) or `N_FROZEN_REFERENCE_SET` (scale from a disjoint, never-maskable address set frozen in advance). `N_VISIBLE_SET_RECOMPUTED` removes the leak but makes inputs mask-dependent and couples the target to the mask |
| **L3** | **Mask eligibility encoding the value** | if only detected (non-zero) addresses are eligible to be hidden, then "`q` was hidden" implies `x_iq > 0` | all | enumerate the eligibility predicate and confirm it reads only declared support | eligibility depends on declared support alone; a measured zero must be exactly as maskable as a measured non-zero |
| **L4** | **Support / visibility state encoding** | today `gene_valid = measurement_mask & ~hidden_target_mask`, so hidden and structurally-unmeasured addresses become indistinguishable. Three distinct states exist — measured-present, measured-hidden, structurally-unmeasured — and collapsing them either destroys panel information or, if hidden is encoded as measured-zero, teaches the model that hidden means zero | all | enumerate the state encoding; check that the hidden state carries no value-derived component | explicit three-state encoding, with the hidden state a constant carrying no value information |
| **L5** | **Measurement-state shortcut** | depth, detection rate and the binary visibility pattern are close to sufficient statistics for one another — in V0, visibility-only predicts Q_DEPTH at about 0.834 and Q_DETECT at about 0.977, while VALUE_ONLY is materially lower | all | control C3, including its support-only sub-arm | **architectural, not a metric**: depth, detection, operator and source may exist only as *outputs* of separate auxiliary heads fed from a **detached** copy of the primary state — never as inputs to the primary molecular path and never as a gradient route into it. The existing `biology_observation_adapter_v2.py` detachment is the pattern to reuse |
| **L6** | **Operator / source structure** | 42 operators; 46 SEA_AD, 41 HVS and 17 NPH52 donors. A target dominated by an operator-level mean is solvable from operator identity alone | all | control C3; report every score per source | no operator or source input to the molecular path; a source-stratified donor split; per-source reporting, never a single pooled number. The measured estimand sensitivity is large — the molecular increment over context moved from +0.0311 unweighted to +0.1207 under empirical / FULL104 weighting |
| **L7** | **Identity shortcut, direct parameter sharing** | `target identity -> predictor query -> gradient -> online identity table -> EMA teacher -> future target` | `Q1`, partially `Q3` | static: enumerate every parameter shared between query construction, the online encoder, and teacher target generation | `Q2_FIXED_CODE` |
| **L8** | **Identity shortcut, target carries stable identity** | even with fixed codes, `H^T_iq` is seeded by `E_id[q]` plus a constant, so a large share of target variance may be address-constant across all cells | all; **worst in `T_B1` and `T_B2`** | control C1, re-measured at several training points, plus the §3.7 screen | if identity-only is not clearly beaten, the *target* is redesigned — never the threshold |
| **L9** | **Correlated-partner and collision leakage** | a paralog, a duplicated symbol, or a near-perfect correlate of `q` remains visible, so the answer is present under another name. Measured and currently **unmitigated**: pooled-Pearson partner masking was 9.4% *worse* than uniform (exposure 0.2129 vs 0.1946); donor-recurrent achieved only −4.8% against a required ≥20%; and at a 2,000-address universe at most 5 of roughly 4M ordered pairs reach a recurrence fraction of 0.5 | all; partially mitigated in `T_C` | the exposure metric D from the 2026-09-16 contract; collision-unresolved addresses excluded from `M_i` | **open.** Whichever candidate is chosen inherits `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`. This sheet does not resolve it and it must not be treated as resolved |
| **L10** | **Positional and ordering artifacts** | token order correlated with expression rank, block index, padding position, or storage order | all | permutation test: reorder tokens and require the target to be invariant | identity is `selection_row` for cells and the canonical address for genes — never block position, shard key, or enumeration counter. This exact failure has already occurred once in this project and was caught only by a physical re-derivation |
| **L11** | **EMA teacher memorization** | the same cell is presented repeatedly under different masks; the target for cell `i` is stable, so the student can memorize cell-to-target without using RNA | all | evaluate only on held-out donors; additionally report the train / held-out gap as a diagnostic | donor-held-out evaluation protects the *reported* number, but it does not stop training-time diagnostics inflating, so training-time scores must never be quoted as evidence |
| **L12** | **Cross-cell mixing inside the batch** | any batch-level normalization, or a cell state that pools across cells, lets same-donor neighbours leak | all | shuffle batch composition and require bit-identical per-cell outputs | per-cell normalization only; no BatchNorm; loss reduction algebraically transparent under microbatching and packing |
| **L13** | **Mask-dependent target** | in `T_B2`, and under `N_VISIBLE_SET_RECOMPUTED`, the teacher's input depends on `H_i`, so the target moves with the mask draw | `T_B2`, `N_VISIBLE_SET_RECOMPUTED` | replay the same cell under the same identity key and require the same mask and the same target | key the mask RNG from `(selection_row, donor_id, canonical_address, presentation_index)` — never from block or shard order, because repacking would otherwise change the target |
| **L14** | **Split contamination through method development** | if held-out donors influence any design choice, even a pathology-blind diagnostic one, they stop being held out | all | freeze the split and the decision rule before scoring any candidate | the split, the metric, the pairing and the direction of every control are frozen prospectively; only the numeric margins remain open, and they are frozen before the first score is inspected, never after |

---

## 5. Required controls, with the result that disqualifies the candidate

**Common protocol.** All conditions run **paired, under common random numbers**: the same cells, the same donor
split, the same mask draws, the same teacher weights, the same scientific cell weights, the same folds. Only the
ablated channel differs.

`S(condition)` is the donor-weighted mean of a **bounded** agreement metric between prediction and target — cosine
if D4 selects `R4_L2_UNIT`, otherwise a fraction-of-target-variance quantity. The choice is D4, and an unbounded
metric would make every relative statement below meaningless.

Uncertainty is computed by **donor-clustered resampling**: the independent unit is the donor — 104 of them — not
the cell, of which there are 4,553,407. Cells improve the precision with which a donor's representation is
measured; they do not add independent replicates, and a cell-level effective sample size must never be reported as
though it were an independent n.

Every score is reported **unconditionally** over the declared evaluation population, with every attempted unit in
the denominator, and **separately per source** — never pooled into a single number.

Each control below states a **direction and a pairing**, proposed to be frozen now, and a **margin**, which is
`UNSET_REQUIRES_APPROVAL`.

### C1 — IDENTITY_ONLY

The predictor receives the query address code and nothing else from the cell: no visible RNA tokens, no cell state,
no measurement channel. Run under **both** `Q1_SHARED_TRAINABLE` and `Q2_FIXED_CODE`.

- **DISQUALIFYING (target):** if the paired delta `S(full) - S(identity_only)` has a confidence interval that
  includes or lies below zero, the target is solved from address identity and the remaining RNA adds nothing. The
  candidate is disqualified.
- **DISQUALIFYING (bar):** if `S(identity_only)` on its own exceeds the frozen minimum-effect bar that the full
  model must clear, the bar cannot discriminate for this target. The **target** is redesigned. The bar is not
  moved.
- **DISQUALIFYING (identity supply):** if `S(identity_only, Q1) - S(identity_only, Q2)` is materially positive, the
  shared trainable table is doing the work and `Q1` is disqualified even if the target survives.
- Re-measure at several training points, not once, because under `QT_EMA_IDENTITY` the address-constant share of
  the target grows during training.
- Stratify the reported identity-only fraction by address frequency, block size, source, operator, and rare versus
  common address, so a failure concentrated in rare addresses is visible rather than averaged away.

### C2 — GLOBAL_CONTEXT_ONLY

The predictor receives the student's pooled cell-level state and the query address code, but no token-level access
to the visible genes — no attention over individual addresses.

- **DISQUALIFYING:** if `S(full) - S(global_only)` has a confidence interval including zero, the target has no
  query-local content — every query in a cell maps to essentially the same vector. The construction does not
  measure a *query-local* state and is disqualified for the stated goal.
- Companion, run first and far cheaper: the §3.7 teacher-only within-cell across-query variance screen.

### C3 — TECHNICAL_ONLY

The predictor receives only measurement and technical channels — library depth, detection rate, the binary
visibility vector, operator ID, source ID — plus the query address code. No RNA values.

- **DISQUALIFYING:** if `S(full) - S(technical_only)` has a confidence interval including zero, the target is a
  measurement-state object rather than a molecular one. Disqualified.
- **Required sub-arm:** the binary visibility vector *alone*, with no depth, no detection, no operator and no
  source. Because visibility-only predicts Q_DETECT at about 0.977 and Q_DEPTH at about 0.834 in V0, visibility is
  very nearly the whole technical channel, and bundling it with the others would hide its individual contribution.
  If the support-only arm approaches the full model, the candidate is disqualified.
- **Architectural requirement, not a measurement (D6):** these channels may exist only as **separate auxiliary
  outputs** predicted from a *detached* copy of the primary state. They are never inputs to the primary molecular
  path, and no gradient from an auxiliary head may reach the primary state. A candidate whose design routes any of
  them into the primary path is rejected on inspection, with no experiment required.

### C4 — REMAINING_RNA_NECESSITY

Replace the visible RNA values with a cell-independent substitute while preserving shape, support pattern, token
count, query code and technical channels. Three levels, increasing in severity:

- **C4a — within-cell value shuffle (primary).** Permute the visible values across the visible addresses of the
  *same* cell. This destroys the address-to-value pairing while leaving library depth and detection rate
  **exactly** unchanged, so any drop is attributable to molecular content rather than to a technical side-effect.
- **C4b — across-cell, within-donor value swap.** Substitute another same-donor cell's visible value vector on a
  matched support. Destroys cell-specific RNA while preserving donor and technical structure.
- **C4c — constant values.** All visible values set to a single constant, identities and support intact. Leaves
  only support and identity.

- **DISQUALIFYING:** if `S(full) - S(C4a)` has a confidence interval including zero, the model is not using the
  remaining RNA *as RNA* — the address-to-value pairing is unused — and the candidate is disqualified. The same
  rule applies to `S(full) - S(C4b)` at the donor level. Failure to clear zero at C4c would be a more severe form
  of the same failure.

### C5 — LEAK_INJECTION — a **positive** control that must SUCCEED

Deliberately reinsert `x~_iq` into the student's context as an extra token and score again.

- **DISQUALIFYING — of the apparatus, not the candidate:** if `S(leaked) - S(full)` does **not** have a confidence
  interval that excludes zero and lies above it, then handing the model the answer did not help, which means the
  evaluation cannot detect leakage at all. Every negative control above is then uninformative and no conclusion may
  be drawn from any of them. A control battery with no demonstrated sensitivity is not evidence.
- **Second positive control — planted query-local signal.** A synthetic fixture matching the real geometry — donor
  count, address count, per-cell marginal count distribution, dependence structure and missingness pattern — with a
  *planted* query-local dependence. The full model must recover it and identity-only must not. A fixture that does
  not match the real geometry cannot certify a control that will be run on real geometry.

### C6 — DONOR_OR_CELL_KEY_CHEAT

The predictor receives the donor ID or a stable cell key, and nothing molecular.

- **DISQUALIFYING:** if `S(full) - S(donor_key_only)` is not clearly above zero, the target encodes donor identity
  and the donor-held-out claim is void.
- **Required accompanying closure check, not a score:** maintain a `seen` vector over the evaluation identity space
  and require that every `selection_row` in range is filled exactly once, that there are no duplicates, and that no
  held-out donor's cell appears in training under any relabelling. An internally consistent aggregate is not
  evidence that the row identity is correct; the mapping is verified against the physical block metadata by
  indexing known rows, not by comparing totals.

### C7 — target-identity structure report (diagnostic, not disqualifying)

Identity-only fraction broken out by address frequency, target-block size, source, operator, donor where lawful,
and rare-versus-common address strata, so a failure concentrated in one stratum is visible rather than averaged
away.

---

## 6. What this sheet does not do

- It does not select a candidate and does not rank them. D1 is the owner's.
- It does not set a mask fraction, a training population or split, a model width, depth, head count or FFN width,
  an EMA half-life, an optimizer setting, a seed, an update budget, or any numerical evaluation threshold. All are
  `UNSET_REQUIRES_APPROVAL` in the companion JSON.
- Historical numbers are **not** inherited and are **not** defaults. The `0.40` mask fraction and `0.99` EMA are
  synthetic fixture values from a mechanics test. `0.996` EMA, six-block depth, width 160, 4 heads, identity
  dimension 48, 16 blocks, 4 views and 128x8 batch geometry are historical V4 mechanics evidence only.
- The 2026-09-16 frozen masking (K, R) nine-cell grid produced **no qualified winner**. Nothing here relabels any
  arm of it as qualified, and `T_C` is explicitly marked as *importing* that open blocker rather than resolving it.
- It does not open protected pathology, sealed confirmation outcomes, terminal masking results, `D_shared` / G5,
  `reader_validation` or `reader_oracle`. No protected outcome informed any statement above.
- It does not treat any provisional network width as a measured biological dimension.
- It contains no authorization language and sets no training authority anywhere.

## 7. Reproduction

    PYTHONPATH=src:. python scripts/v5/lane_a/v29_lane_a_candidate_space_firewall_v1.py \
        docs/agent/lane_a/JEPA_V29_LANE_A_TEACHER_TARGET_PROPOSAL_V1_20260926.json
    PYTHONPATH=src:. python -m pytest -q tests/lane_a/test_v29_lane_a_candidate_space_firewall_v1.py

A green result proves only that this proposal keeps every open choice open, attaches a falsifying outcome to every
control, and issues no authority. It is not evidence about biology, not a target selection, and not permission to
train.

---

`TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED · D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF`
