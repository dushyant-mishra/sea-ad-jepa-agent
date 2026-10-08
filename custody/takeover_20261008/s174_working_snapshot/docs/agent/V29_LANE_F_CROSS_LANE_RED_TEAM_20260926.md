# Lane F — cross-lane integration and independent red team

Reviews Lanes A–E and Agents 2–6 **without modifying their source artifacts**.
Every claim below is marked by how I established it: `VERIFIED_BY_ME` means I
re-derived it from source in this session; `LANE_CLAIM_UNVERIFIED` means I am
relaying it and have not checked it.

**Nothing here authorizes anything.** `fully_closed = 0 of 33`.

---

## 1. Verification status of each lane's load-bearing claim

| lane | load-bearing claim | my status |
|---|---|---|
| **A** (PR #163) | teacher receives the hidden gene's value; target is scalar regression | **VERIFIED_BY_ME** — encoder signature `forward(gene_ids, expression, measurement_mask, hidden_target_mask, …)`; `inactive_update_reference.py:167` passes `torch.zeros_like(true_t)` |
| **A** | `GLOBAL_CONTEXT_ONLY` does not fire on its own planted failure | `LANE_CLAIM_UNVERIFIED` — method (planting the failure) is sound; numbers not re-derived |
| **B** (PR #160) | six substrate consumers, not four | **VERIFIED_BY_ME** — closure_v2 lines 195, 196, 202, 209, 210, 245 |
| **B** | issuance re-derives 2 of 32 roots from live objects | **VERIFIED_BY_ME** — `_live_digest` occurs exactly twice, lines 106–107 |
| **B** | `CriticalTestExecutionAuthorityV1` is forgeable | **VERIFIED_BY_ME** — only check is `status != 'EXECUTED_PASS'`; no execution artifact exists repo-wide |
| **C** (PR #169) | planner change is behaviourally inert; 924/0 | `LANE_CLAIM_UNVERIFIED` — **the strongest evidence in this cycle that I did not check.** See §4 |
| **E** (PR #158) | guide library complete, 6×3 + 6 controls | **VERIFIED_BY_ME** — 72 rows, 24 unique protospacers, every name ×3, from the archived deposit file |
| **D, 2, 4, 5, 6** | — | **INCOMPLETE_INTERRUPTED**; no number citable |


## 1b. Lane D (PR #164) — added after delivery

| claim | my status |
|---|---|
| 10/10 assets authenticated, zero downloads; all 10 inventory figures reproduce (58,721x61,770; 219,070x143,401; 4,126/18; 12,232/20) | `LANE_CLAIM_UNVERIFIED` |
| gene coverage 38,838/41,238 = 94.18%, 294 unresolved collisions | `LANE_CLAIM_UNVERIFIED` |
| zero GSE174367 donors in FULL104; no cell-level pairing (16-mer overlap 190 vs 9,893 expected) | `LANE_CLAIM_UNVERIFIED` |
| coordinate-perturbation control: +50 kb shift moves 99.99% of distances | `LANE_CLAIM_UNVERIFIED` |
| independence: no Stage75F script reads ATAC counts | `LANE_CLAIM_UNVERIFIED` — lane states it grepped the code rather than relaying |
| **Stage73 shuffled controls were bit-identical (deltas 0.0, CI [0.0,0.0] over 1,000 iters); after Stage73R repair the graph LOST to its own target-shuffled control, 0.32361 vs 0.33229** | **`LANE_CLAIM_UNVERIFIED` — I attempted verification and FAILED** |

**My failed verification, recorded because the failure matters.** I grepped for
`0.32361` and `0.33229` across `results/`, `outputs/` and `docs/`. The hits were
those digit strings appearing inside unrelated embedding-coordinate CSVs, not
Stage73 control results. **A grep that matches the right characters in the wrong
file is not verification**, and had I reported those hits as confirmation it
would have been the S17/S19/S21 pattern a fourth time. Marked unverified.

This claim deserves priority verification by whoever continues: it asserts that a
historical control **could not fail**, and that once repaired the graph lost to
its own null. If true it is the most consequential correction in the cycle and it
invalidates a direction the project previously took. It corrects my own brief to
the lanes, which described the Stage73 error as accepting a graph over a no-graph
baseline — the actual failure was worse.

## 2. The nine required red-team checks

| check | finding |
|---|---|
| counts verified against authenticated files | **PARTIAL.** Verified for A, B, E. Not for C. Not possible for D/2/4/5/6 (interrupted). |
| exact overlap with the FULL104 address registry | **UNKNOWN** — Agent 2 owns it and has not delivered. Not zero. |
| no RNA-feature / ATAC-peak confusion | **NOT YET ASSESSABLE** — requires Lane D + Agent 2 output |
| no false cell-level RNA–ATAC pairing | **CONSTRAINT ISSUED AND NOT YET VIOLATED.** Lanes D and 5 were both instructed that these are separate nuclei. No lane has yet produced a pairing claim to audit. |
| no small-panel output presented as genome-wide | **HOLDING.** Stage75F is 10 regulators / 96 TF–target rows. Every lane touching it (D, 4, 5) carries the hypothesis-not-network constraint. No lane has yet claimed genome-wide coverage. |
| no circular SCENIC+ priors as independent validation | **HOLDING, UNPROVEN.** The circularity register is specified in D, 4 and 5 but none has delivered one. |
| no pseudoreplication | **ONE RESOLVED, ONE PENDING.** Lane E independently reached n=2 differentiations, one genetic background — the correct unit, matching the constraint rather than inheriting it. Agent 5's donor-level replication is pending. |
| no duplicate costly computation | **HOLDING.** Agent 2 was routed to read Lane D's authentication rather than re-authenticate; Agent 6 was routed to PR #158 rather than re-derive GSE289721; Lane C preserved PR #153's 17 adversaries rather than reimplementing them. |
| no previously inspected outcome promoted to confirmation | **HOLDING.** No lane opened a protected outcome. All reserved flags unchanged. |

## 3. The coverage funnel — every transition is UNKNOWN, and that is the honest answer

```
41,238 canonical addresses
   → structurally measured in Morabito RNA        39,081  (94.77%)   Agent 2, PR #175
        MEASURED_DETECTED          31,455  (76.28%)
        MEASURED_BUT_UNDETECTED     7,626  (18.49%)
        UNMEASURED                  2,122  ( 5.15%)  <- NOT converted to zero
        AMBIGUOUSLY_MAPPED             35  ( 0.08%)
   → gene-mapped ATAC                             25,966 accessible promoter
                                                  13,814 distal-only (PROVISIONAL)
                                                     698 no assayed region
                                                     755 UNKNOWN
   → matched RNA-ATAC eligible                    37,966  (donor/pseudobulk level only)
   → context-specific ATAC activity               UNKNOWN
   → motif-supported regulatory candidates        UNKNOWN  (Agent 4, stopped)
   → independently evaluable genes                UNKNOWN
```

**No transition may be reported as zero.** The assignment's immediate milestone —
a defensible, measured answer to how much of FULL104 can be covered — is now
**ANSWERED for the first two transitions**: **94.77 % structurally measured**,
with 37,966 addresses matched-RNA-ATAC eligible at donor level. The later
transitions remain **UNKNOWN**.

**VERIFIED_BY_ME:** the prohibited 41,238-vs-61,770 comparison was a *category
error*, not imprecision. `matrix/shape = [58721, 61770]`: **58,721 features,
61,770 barcodes**. Comparing the address count to 61,770 compares genes against
nuclei. Re-read directly from the RNA h5 this session.

**VERIFIED_BY_ME (arithmetic):** the four states sum to exactly 41,238, and
31,455 + 7,626 = 39,081 = 94.77 %. Had UNMEASURED been collapsed into zero the
figure would have read **99.9 %** on 2,122 fabricated zeros. The only defensible statement today is that the historical pilot
covers 10 regulators and 96 TF–target rows, and that this is not a measurement of
available coverage.

## 4. The largest unaudited claim in this cycle

Lane C reports `826 passed / 5 failed → 924 passed / 0 failed`, a
`LEGITIMATE_VERSION_CHANGE` classification, and bitwise equivalence over 88
emitted rows, 22 per-fold row sets and 22 `_ridge_partners` calls.

**I have not verified any of it.** It is the most consequential *engineering*
claim of the cycle and it rests on my relaying it. Its method is unusually
strong — it recovered the frozen implementation from blob `083bd8aa`, re-verified
the original digest, and ran a mutation control to prove the comparison was not
blind — and it self-reported a real defect (a regex that read past its own broken
YAML). That raises my confidence but is **not** verification.

**Recommended next action for whoever picks this up: independently re-run Lane
C's equivalence harness and the full suite.** A green CI check is not evidence
that the right thing ran; that is the specific lesson Lane C itself recorded.

## 5. Dependency graph — what can proceed without anything else

**Can proceed now, no approval or GPU needed:**
Agent 2 coverage crosswalk · Lane D authentication and peak-to-gene · Agent 6
registry · Agent 4 Stage75F authentication and restriction trace · independent
re-verification of Lane C.

**Needs GPU:** nothing currently. The mechanical diagnostic is CPU; no
authorized real-data run exists.

**Needs owner scientific approval:**
D0 normalization rule → D1 teacher target → masking configuration → the frozen
`reader_fit` development contract. **D0 precedes D1** because per-cell
total-count normalization leaks the query scalar into every other token, so
dropping the query token does not remove it.

**Needs owner governance decision:**
what constitutes a valid test-run binding for `CriticalTestExecutionAuthorityV1`
(see §1) · whether RNG V3's three closure checks are replaced · PR #144's design
question, raised by Lane C, that a development-only feature now lives inside a
frozen execution artifact.

**Prohibited regardless:** real `reader_fit` training; protected pathology;
sealed confirmation outcomes; terminal masking outcomes; D_shared/G5;
reader_validation; reader_oracle; whole-study Siletti.

## 6. Claims kept distinct, per the assignment

These are four different things and no lane has conflated them:
**external observational validation** · **regulatory association** ·
**experimental perturbation agreement** · **causal validation**.

Nothing in this cycle reaches even the first. GSE301119's estimator is
disqualified; the CRISPRbrain pair is not independent replication; the historical
LODO inputs are absent. **None of that invalidates the molecular signal
previously observed in FULL104** — a benchmark failing qualification and an
experiment showing no signal are different claims.

## 7. Red team of my own work

Three of my errors this cycle shared one mechanism — reporting a pattern-match or
a truncated view as exhaustive (S17 directory list, S19 one spelling of a key,
S21 ninety "forgeable" modules that were a design property). S17 and S19 were
published before being caught; S19 was caught by Lane B, not by me. S9 was a
false alarm I withdrew in full after finding the condition had been documented
and qualified five days earlier.

The corresponding risk in *this* document is that §1's `VERIFIED_BY_ME` rows are
the only ones carrying my own check, and I have marked every other row
accordingly rather than letting relayed claims inherit that status.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
