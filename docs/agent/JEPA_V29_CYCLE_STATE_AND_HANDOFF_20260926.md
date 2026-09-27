# V29 cycle state — durable handoff

Written deliberately before budget exhaustion so this cycle survives without me.
**Nothing here is a training authorization. `fully_closed = 0 of 33`.**

## 1. The single most important finding of this cycle

**`CriticalTestExecutionAuthorityV1` is forgeable, and it sits at the
authorization boundary.**

```python
if status != 'EXECUTED_PASS': raise ValueError(...)   # the entire check
```

`status_by_test` is a caller-supplied `Mapping[str,str]`; the gate is satisfied
by *writing the literal string*. `test_suite_source_sha256` is validated for
SHA-256 **shape** only. Repo-wide greps confirm **no committed artifact anywhere
records an `EXECUTED_PASS` status**, and the suite-source digest is **never
computed from an actual suite file**. Both fields are free-floating.

**Consequence: even with all 33 roots populated, issuance would not prove the
required tests ever ran.** Populating roots is necessary, not sufficient.

**Deliberately NOT patched.** Defining a valid test-run binding is an owner
governance decision; editing the gate to look stronger is the error this project
repeatedly warns against.

**This is NOT systemic.** 96 authority modules validate SHA-shaped fields and 90
never hash a file — but that is the digest-passing *design*, with producers
computing digests elsewhere (verified: registry digest `7d61ed7b…` appears in
3+ producer receipts). The defect is confined to `critical_test`, because what it
attests — execution — has no artifact in existence.


## 1b. The most important SCIENTIFIC finding: the teacher can see the answer

`KeyedIPBEncoderV2Reference.forward(gene_ids, expression, measurement_mask,
hidden_target_mask, view, ...)` — and `inactive_update_reference.py:167` passes
`torch.zeros_like(true_t)` as `hidden_target_mask`. **Nothing is hidden from the
teacher**, while `expression` carries every measured value including the query
gene's count. Verified against source.

**The teacher target is therefore a smooth function of the number the student is
asked to predict.** The current construction is indirect *scalar regression*, not
query-local latent-state prediction. It does not implement the stated goal.

**All four named controls are blind to it** — a model that recovers the count
passes every one. This could not have been caught downstream; it had to be found
by reading the construction. Found before any training run: the cost is one
scientific decision plus a value-blind token path, not a retraction.

Related, same family: `GLOBAL_CONTEXT_ONLY` does **not** fire on the failure it
was written to catch (0.5887 vs 0.7980 full, delta +0.2093 [+0.1801, +0.2378]),
because a query-conditioned predictor plus a pooled cell summary already suffices
to emit a query-local answer. Demoted to diagnostic; `QUERY_EXCHANGEABILITY`
takes the falsifying role and does fire. Caught by *planting* the failure.

The seam that defeats **all** candidate constructions: **per-cell total-count
normalization leaks the query scalar into every other token**, so dropping the
query token does not remove it. The normalization rule must be decided *before*
the target construction.

Lane A: PR #163, 170 passed / 0 failed / 0 skipped.

## 2. Authority state

| | |
|---|---|
| roots | 32 upstream + `preexecution` = **33** |
| **fully closed** | **0** (computed, not asserted) |
| own-schema validated | 6 (a *subset*, 2 of which have consumer-class conflicts) |
| issuance re-derives from live objects | **2 of 32** (`_live_digest`, lines 106–107) |

**Substrate root** `full104_substrate_sha256` = `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
— authenticated as the **2,372,002-byte** Level-4 file
`.../03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv`
under `D:/Jepa project/outputs/full104_v014_20260826/`.

**DECOY — never bind from these:** identically named, **2,380,918 bytes**,
`e482d9da21232bdeb6b3f198f42b9fbcf1530ba1b3e86e104ffbb651ca9df808`, under
`/d/jepa_ppa_20260904/docs/history/` and `/d/jepa_f1b_20260905/docs/history/`.

**Six** consumers (closure_v2 lines 195, 196, 202, 209, 210, 245): three carry
the authentic substrate (`representation`, `support_estimability`,
`canonical_address_registry`); three block with no committed artifact
(`outer_split`, `target_panel`, `masking_qualification_design`).

`observation_gradient_firewall_authority_sha256` is **unbound on both sides**.

**V3/V1 conflicts — not one problem, two:** *parameters* is nominal (V3 is a
strict field superset pinning V1 numerics; adopt). *RNG* is a scientific
divergence — V3 supplies none of the three compared attributes and cannot enter
by any typing change; the checks must be replaced, which is an owner decision.
No cast, no subclass, no fabricated V1 instance.

## 3. Benchmark status — failed qualification is NOT absence of signal

| source | status |
|---|---|
| GSE301119 | estimator **disqualified** — NT-vs-NT null median −1.504 vs real −1.344; survives the PR #127 tie-safe rerun unchanged |
| CRISPRbrain pair | **not benchmark truth** — engagement 1/31 joint, concordance at chance, shared lab/paper/guide library |
| Historical Layer-2 LODO | inputs **absent** from both drives; 94-donor unweighted linear proxy, not comparable to a 104-donor JEPA |
| P1-6 bulk | 179,384 rows reproduced — **software reproducibility, not biological validation** |
| GSE289721 | **QUALIFIED-FEASIBLE pending gates**; n=2 differentiations, 1 genetic background; INPP5D overlaps training |

**None of this invalidates the molecular signal previously observed in FULL104.**
A benchmark failing qualification and an experiment showing no signal are
different claims.

## 4. Live lanes at time of writing

Resumed: **lane-a** (teacher target), **lane-c** (PR #144 planner regression),
**lane-d** (GSE174367 auth + peak-to-gene). Complete: **lane-b** (PR #160),
**lane-e** (PR #158). New: **agent-2** (41,238-address coverage crosswalk — the
immediate milestone), **agent-4** (SCENIC+), **agent-5** (validation protocol),
**agent-6** (dataset registry).

Salvaged interrupted work is committed and labelled `INCOMPLETE_INTERRUPTED`
(`cb5a6f81`, `40dc242f`, `f63eff5d`) — **no number in those commits may be cited
as evidence**.

## 5. Self-audit S8–S21 — the pattern in my own errors

Three errors this cycle share one mechanism: **reporting a pattern-match or a
truncated view as if it were exhaustive.**

* **S17** — transcribed a command's directory list instead of its output; a
  silently-skipping loop let a plan masquerade as a result.
* **S19** — grepped one spelling of a field name; two consumers bind the same
  digest under different names, so my pattern could never have matched them.
  *Caught by Lane B, not by me.*
* **S21** — a regex found 90 claim-only modules; reporting that as 90 defects
  would have been badly wrong. *Caught before reporting.*

Standing rules adopted: **transcribe from output, never from intent**; **search
by the value being bound, not one spelling of a key**; **check the mechanism
before reporting the match.**

Also withdrawn earlier this cycle: **S9** (the environment was never defective —
I invoked it without `<env>/Library/bin` on PATH, which was already documented
and qualified on 2026-09-20); **S14/S15** (my gradient-gate counters were
vacuous — the four counters are hard-coded literals on the healthy path, so
asserting them proved nothing; `max_abs_gradient` 0.065887–0.189149 is the only
real measurement, and six negative controls now prove the gate actually refuses).

## 6. What blocks the first real run

1. **Teacher target undecided** — the science, not the code.
2. **Masking configuration** — the Sept-16 K/R grid produced *no qualified
   winner*; a failed arm must not be relabelled.
3. **B1** — registry lists "new teacher training" as `forbidden_without_new_authority`.
4. **B2** — 33 roots, 0 closed; and per §1 closure alone would still not prove
   the tests ran.

Engineering remaining after authorization: **one adapter**, FULL104 streaming
readers → `run_inactive_reference_update`.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```

---

## 7. Cycle close-out (appended after Tasks 1-3)

**PR #178** carries this entire branch, 24 commits. PRs #179/#180/#181 carry the
three lanes stopped to conserve budget, each labelled `INCOMPLETE_STOPPED` with
an explicit instruction that no number on them is citable.

### Delivered after the handoff was first written

* **Control sensitivity ledger V1 then V2** — every control needs three legs:
  quiet on healthy, **must fire** on planted, **must refuse to score** on
  degenerate. V2 repaired four V1 defects, each *demonstrated* rather than
  asserted. The worst: V1 hashed `repr()`, and NumPy **truncates** repr, so two
  10,000-element arrays differing at index 5000 hashed identically — a
  distinctness detector blind precisely on real-sized data. **36/36, 0 skipped.**
* **Complete machine-state snapshot** — planted failures must leave every
  mutable tensor byte-identical (online, teacher, predictor, every optimizer
  state tensor, every param_group scalar, cursor). Proven able to detect a
  single 1e-6 weight perturbation and a cursor advance alone.
* **Task 2, q-leakage through the real path.** Production rule
  `log1p(raw x 10000 / source_library)`; `pack_valid_tokens` does not normalize,
  so the model path is normalization-agnostic and q-safety belongs to the
  **reader boundary**. Token-dropping does not move the denominator (it is a
  frozen metadata constant); but that constant **includes q**, so student inputs
  are not invariant to q's raw value. **Bounding the claim:** the reader and the
  neural harness are **disjoint subsystems** — the reader feeds masking
  calibration, never the update harness. This describes the masking lane, not an
  established neural production rule.
* **Task 3, reported `NOT_INFORMATIVE`.** Four corrections, each producing a
  clean-looking table that would have supported "the q-blind teacher fails":
  n≈p; a fixture with no complementary signal; fixed `alpha` across arms of
  different width; inner CV tuned within-operator then evaluated across
  operators. Fixing the last moved T_B from -0.8360 to +0.1525 on P2RY12. The
  final design is sound and **still does not discriminate**, because the
  fixture's signal split between q and the program genes is an arbitrary choice.
  Tuning it until T_B wins would fit the fixture to the desired answer. **The
  comparison needs real RNA.** The harness, exclusion sets, missingness channel,
  degeneracy guard and structurally-matched tuning are correct and reusable.

### Corrections to my own published claims, all withdrawn or restated

| | |
|---|---|
| **S9** | environment "defective" — **RETRACTED IN FULL**; I invoked it without `Library/bin` on PATH. No re-execution required. |
| gradient "40/40 affirmative" | **WITHDRAWN** — counters are hard-coded literals on the healthy path |
| Stage73 "the graph lost" | **RESTATED** — CI includes zero, so *failure to establish an advantage*, not a demonstrated loss |
| leakage worst case | **9.49e-02 → 6.91e-01**, 7x larger; a q-count loop never entered the computation |
| substrate consumers | **four → six** (caught by Lane B, not by me) |
| S17 / S18 | a directory never swept; an ambiguous count |

### The through-line

Five instances of one failure mode across independent lanes: my vacuous gradient
counters, Lane A's `GLOBAL_CONTEXT_ONLY`, three of Agent 5's eight controls,
Stage73's bit-identical shuffles, and my own `repr`-based detector. **Controls
that cannot fail are systemic here.** Four of my own last five findings were
corrections to my measurement rather than discoveries about the system — which
is the reason to prove every control can fail before trusting a real-data run.

### Restored after being dropped

The **paired-multiome authentication lane** (GSE214637/GSE214979, GSE272082) was
stopped with Agent 6 and not carried forward as a debt. It is running again as a
dedicated lane. Two traps are non-negotiable there: **GSE214979 is a subseries of
GSE214637**, not an independent cohort; and **GSE272082 is n=9 people, not n=27**
— three brain regions per donor are not three donors.
