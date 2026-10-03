# JEPA NEW-CHAT HANDOFF — 2026-10-03 — V74 AUDIT TAKEOVER

## Purpose

This is an audit-first takeover document for a new agent. It is not a scientific authority by itself. The new agent must re-query GitHub branch heads before making changes, inspect diffs rather than trust commit messages, preserve all negative results/retractions, and keep Sol and Macha/Claude lanes separate until each is independently audited.

This handoff is based on the live repository state verified on 2026-10-03 around 11:26 ET plus the current chat's completed custody and lane reports.

## Project operating rules

1. Do not overclaim. PASS, qualification, independent validation, biological interpretation, and authorization require exact evidence.
2. Historical smaller-run outputs, placeholders, or stale receipts must not leak into full runs.
3. The model predicts biological state, not the literal hidden gene value.
4. Technology/operator belongs in the observation model, not as biological identity.
5. Synthetic controls/twins must reproduce the actual matching, filtering, QC, missingness, pairing, and selection mechanism, not merely similar marginal distributions.
6. Synthetic biology may be planted and known, but observation/noise/coverage geometry should be calibrated to the real datasets.
7. Preserve provenance, hashes, immutable scripts/shards, execution conditions, negative results, and retractions.
8. Large scientific binaries do not belong in ordinary Git history. Preserve exact byte size/hash/recovery provenance instead.
9. Macha/Claude work must be independently audited from bytes, diffs, receipts, tests, and branch history. Do not accept a chat summary or commit message as proof.
10. If a check is supposed to protect against corruption, demonstrate a mutation that makes it fail. A green check that cannot fail is not evidence.
11. Do not reopen protected data or outcomes unless the current governance explicitly authorizes it.
12. Current governance remains: TRAINING OFF; multimodal training OFF; Stage 4 NOT AUTHORIZED; correspondence UNOPENED; Morabito protected; recoverability TEST sealed.

## Core model architecture

Teacher target remains conceptually:

`Z_teacher = Z_global ⊕ Z_query ⊕ Z_reg_shared ⊕ Z_reg_private`

RNA student predicts:

`Z_global ⊕ Z_query ⊕ Z_reg_shared`

Private privileged state stays teacher-private. If identical RNA can correspond to different private privileged states, the student should express uncertainty rather than hallucinate the private state.

## FULL104 population authority

Current FULL104 population constants used by the synthetic work:

- total cells: 4,553,407
- donors: 104
- canonical molecular addresses: 41,238
- operators: 42
- SEA_AD: 4,118,213 cells = ~90.442%
- NPH52: 236,476 cells = ~5.193%
- HVS: 198,718 cells = ~4.364%
- 17,346 addresses measured in all three sources = 42.063%
- 17,186 addresses measured under all 42 operators = 41.675%

A compact reader-fit population authority was extracted in this chat from the authenticated foundation calibration metadata and is under chat-runtime custody as:

`V73_FULL104_READER_FIT_POPULATION_GROUPS.csv`

Its runtime SHA-256 is:

`45eabda298727e171fadbf82590433e6255b89aa88de0cdafb109a65ee5ecc0d`

The new agent must distinguish exact population geometry from sampled QC distributions. Population geometry came from the reader-fit metadata SQLite; RNA/QC distribution calibration uses the frozen discovery-expression sample and must not be described as full-population QC precision.

---

# LIVE BRANCH / PR MAP

Re-query every head before work because Macha lanes may move.

## Sol synthetic authority

### V72 coupled synthetic ecosystem

PR #201 — `chatgpt/v72-synthetic-ecosystem-successor-20261002`

Verified historical head:

`6cb5e234886b6a240c2ef9bda6162377feaef7f8`

Exact-head GitHub Actions run `37012617882` was SUCCESS.

This is the current Sol-side V72 synthetic authority. It closes the V71 CI/readiness gap and creates one coupled hidden truth projected into FULL104-like RNA, Stage4-like data, GSE214979/SCENIC+-like paired multiome/raw fragments, Morabito-like separate nuclei, SEA-AD paired multiome-like anchor, perturbation, spatial, and checkpoint twins.

Do not confuse PR #200 with the current Sol synthetic authority. PR #200 is useful historical parallel evidence but #201 is the controlling V72 Sol branch.

### V73 stress twin

PR #204 — `chatgpt/v73-synthetic-stress-twin-20261002`

Verified live head on 2026-10-03:

`ed7ac610601580ae3bc3ca185d6047f34b7cb042`

Commit message at that head: `V73: preserve empirical operator support in stress quotas`.

Architecture at this line includes:

- one stateless, cell-identity-keyed sharded master hidden truth;
- FULL104-like RNA from the same master truth;
- paired RNA+ATAC observer on the same synthetic cell identities;
- deterministic five-column 10x-style fragment shards derived from model-facing ATAC counts;
- shard-invariance tests;
- truth-firewall checks;
- resource accounting;
- source composition corrected away from the original erroneous 80/14/6 placeholder;
- deterministic FULL104 source proportions/counts;
- donor/source/operator empirical calibration work;
- fragment integrity and promotion-gate work added during this chat.

Important: the original V73 contract's 80/14/6 source target is historical error and must not be revived. Preserve it as historical evidence only.

### V74 synthetic calibration closure

PR #205 — `chatgpt/v74-synthetic-calibration-closure-20261003`

Verified live head:

`525611a8a70faf425c4f7f0f5d2354269beb3322`

Exact-head workflow run `37129241516` completed SUCCESS.

PR #205 was created specifically to audit/fix calibration problems after V73. Its documented first defect was that source→triplet largest-remainder apportionment could erase a low-support operator at 100K. The successor changes the hierarchy to source→operator→donor/operator group so observed operator support is preserved before group rounding.

PR #205 must be treated as the current Sol synthetic-calibration successor, but it is still draft and is not a license to claim 100K/full-scale scientific qualification. Audit its full diff and tests before promotion.

The next unresolved synthetic-calibration question is whether the FULL104 RNA observer actually consumes empirical zero-fraction/detected-feature calibration rather than merely storing those targets in metadata beside generated counts. The new agent should inspect the PR #205 diff and prove this from implementation/tests before making a claim.

## Chat-runtime custody

PR #206 — `chatgpt/v73-chat-runtime-custody-20261003`

Verified head:

`318896621957141472ba9eb9ef0700fe67812e0c`

This is docs/custody only. It is based on Sol science head `ed7ac610...` and must not be treated as a science branch.

It records the 12 original artifacts physically present in the chat runtime and preserves the five small chat-exclusive artifacts inside:

`docs/agent/archive/chat_runtime_20261003/payloads/CHAT_RUNTIME_SMALL_PAYLOADS_20261003.tar.gz`

The large binaries remain hash/provenance-bound by design rather than inserted into ordinary Git history. V2 overstated small-payload byte custody; V3 retracts that; V4 actually stores the recovery tar. The new agent should cite V4/current branch state, not the superseded V2 language.

## Handoff branch

This document lives on:

`handoff/jepa-v74-audit-takeover-20261003`

It was created from custody head `318896621957141472ba9eb9ef0700fe67812e0c` specifically so it carries the latest chat custody without merging scientific lanes.

---

# MACHA / CLAUDE LANES — LIVE HEADS AND AUDIT REQUIREMENTS

The following are independent branches. Do not assume one contains another's fixes.

## Lane 1 / Route-B custody

Branch:

`claude/v74-routeb-custody-20261002`

Verified head:

`32dfcbfdcfced5683d9646e10a7db679ea9ba323`

The current chat reports Lane 1 complete. The important finding is that the old fragment digest linkage did not actually exist: the V69 QC receipt copied `fragments_sha256` from the acquisition receipt instead of computing it from bytes, so receipt-to-receipt equality was self-agreement, not byte authentication.

Lane 1 reportedly repaired this by computing SHA-256 from the compressed fragment bytes as they stream, without a second full pass and without a time-of-check/time-of-use gap. The resulting digest was reported as:

`b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f`

for exactly:

`63,641,120,882` bytes.

It also reportedly re-counted fragment multiplicity per cohort barcode from authenticated bytes and required exact agreement with the QC table:

- cohort cells: 2,534
- total retained fragments: 23,522,438
- all 2,534 barcode totals matched the QC table.

This retroactively strengthens the V69 QC table's linkage to authenticated bytes.

Two prior checks were found incapable of protecting what they claimed:

1. Duplicate-barcode guard ran after `dict(zip(...))`, so conflicts had already been discarded.
2. Empty consensus raised ordinary `ValueError`, not the structured fail-closed exception caught by `main()`, so no failure receipt was written.

The real cohort reportedly had 2,534 rows, zero duplicates and zero conflicts, so the duplicate-map defect was latent rather than realized.

The lane reports 50 tests and 13 mutations, all demonstrated capable of failing. One especially important mutation preserved file length and decompressed records while changing the gzip MTIME byte; only the compressed-byte digest detected it.

Audit this lane independently:

- inspect the branch diff from its base;
- verify the digest is computed from the actual compressed bytes during the real stream, not copied from a receipt or parameter;
- verify the file-length-plus-byte-change mutation really passes downstream decompressed-count checks but fails the SHA check;
- verify barcode duplicate/conflict validation happens on dataframe rows before any dict collapse;
- verify fragment counts are independently re-derived and exactly reconciled to the QC table;
- verify fail-closed exceptions always produce a structured receipt;
- verify the consensus gate happens before consensus construction;
- verify no change to biological thresholds or selection rules was smuggled into custody repair;
- verify no protected outcome was opened.

The lane also added durable UTF-8/newline I/O helpers and a replay verifier. Inspect them; do not accept "50 tests passing" without verifying what the tests assert and that the mutation driver actually mutates the intended check.

### Route-A analogous defect

The user reported `build_routea_cistopic_object_v1.py:114` has the same `dict(zip(...))` conflict-loss defect. The user explicitly said they would fix it inline once Lane E reports. Do not let another agent silently edit that file before checking whether the user's fix has landed.

## Lane E / blacklist + 512-motif pilot

Branch:

`claude/v74-blacklist-and-512pilot-20261002`

Verified head at handoff creation:

`60b0971086bc414dc14e65da59818316450a0a16`

This head contains a successor scaling-authority producer committed before the quiet 512-motif run landed. The commit explicitly marks earlier scaling text as internally contradictory and says the old ~33.5 h projection must not be cited alone because direct measurement contradicted it.

At the moment of this handoff, the current chat says Lane E's quiet pilot was still running. Therefore the next agent must re-query this branch before doing anything. Do not assume `60b097...` is still current.

Blacklist decision remains prospective Route-B policy:

- blacklist ON;
- ENCODE GRCh38 blacklist accession `ENCFF356LFX`;
- ENCODE dataset `ENCSR636HFF`;
- expected portal MD5 from prior audit: `393688b4f06c9ce26165d47433dd8c37`;
- authenticate actual bytes/build/hash before use;
- record pre/post region attrition.

Why the blacklist gate is hard rather than advisory: pycisTopic applies blacklist handling inside `get_consensus_peaks` during iterative overlap. Therefore a no-blacklist consensus is not equivalent to the decided universe followed by post-hoc blacklist filtering. It is a different consensus universe and cannot be repaired after construction by simple subtraction.

Audit Lane E when it reports:

- confirm exact authenticated blacklist bytes, not accession-only assertions;
- confirm build is GRCh38 and provenance is unambiguous;
- confirm the quiet pilot did not overlap with other heavy jobs after the already-acknowledged scheduling mistake;
- verify pilot timing/logging was measured from tool logs, not reconstructed by hand;
- verify worker count, shard size, concurrency, scratch footprint and route are all bound in the successor receipt;
- verify no historical extrapolation is presented as direct measurement;
- inspect the 512-motif result before any full 10,249-motif build;
- verify the result cannot tune scientific thresholds or network interpretation after the fact;
- if the pilot fails, preserve the negative result and do not tune until it passes.

Known scheduling incident: the Route-B 3h18m extraction overlapped 58% of Lane E's pilot window. This was explicitly acknowledged as a scheduling error. It invalidates timing claims for the overlapping run, not correctness of replay-verified pseudobulk bytes. Do not rerun the 3h18m pseudobulk just to get a clean timing number; it has no timing claim and rerunning would not change correctness.

## Lane A / G2 continuous successor

Branch:

`claude/v74-g2-continuous-successor-20261002`

Verified head:

`03c0c48612860e4bd2f094ce54fdef9cde274490`

This lane freezes the successor contract as `NOT_IN_FORCE`.

The contract reportedly fixes:

- continuous CVC estimand;
- statistic;
- three-valued verdict structure;
- fail-closed guards;
- reported quantities;
- implementation repairs I1/I2;
- all deciding margins remain UNSET.

Any executor binding it must HALT rather than choose a default. That is an important protection against repeating S102.

S102 remains OPEN. Current narrowed statement from the branch: the absolute equivalence margin is not derivable from current evidence; a relative margin is derivable at f=1 only. Do not promote that to a final Stage4 rule without independent audit of the contract and rationale.

Do not run another thresholded K curve to settle S102. Do not top up K=50/K=200 after seeing the result. The successor problem is prospective continuous-CVC/equivalence design, not more K-curve precision.

## Lane 4 / stale-claim audit

Branch:

`claude/v74-stale-claim-audit-20261002`

Verified head:

`14326480882f5bc4618634ba7f95c94f4924437d`

Reported audit scope:

- all 6,016 git-tracked files at the audited base;
- sixteen literal stale-claim markers;
- nine semantic paraphrases;
- full JSON walks of candidates;
- exhaustive listings of `results/v64/`, `results/v64/phase_b_design/`, and active execution-plan material;
- explicit statement of what was not searched.

Result:

- 27 occurrences classified;
- 12 FALSE_STALE_CLAIM;
- 7 SUPERSEDED;
- 5 STRUCTURAL_ARGUMENT_ONLY;
- 3 HISTORICAL_RETAIN_FOR_RECORD;
- plus current correctly stated groups.

All 12 false stale claims were reportedly in two files:

1. the V1 K-curve artifact, which had no supersession marker and still said `COMPLETE` while making the invalid "structurally identical to planted biology" statement for its historical K=200 world;
2. the Stage-4 closeout receipts block, one block below the S109 repair, still carrying the withdrawn V1 interpretation and `g2_rate_monotone_in_K: true` despite the repaired V2 curve being non-monotone.

No executable contradiction was found: no code, gate, threshold, alpha, or acceptance criterion reads the V1 result.

Seven stale-text occurrences were intentionally not edited because they are SHA-frozen provenance artifacts. That is correct unless an independent audit proves otherwise.

Important self-audit findings to preserve:

- S111: annotating V1 in place mutates a historical measurement record. The lane preserved the prior hash/blob in the header and recorded dissent. A reviewer who treats historical result files as immutable may reasonably prefer a sibling supersession notice instead.
- S112 OPEN: V2 still has a bare convergence flag next to inherited text saying a monotone rise is unmistakable, although the actual curve is non-monotone. Do not interpret the bare flag as a scientific conclusion.
- S115: two of 26 quotes called "verbatim" were reconstructed from continuation lines. The lane corrected those labels after a self-falsification check.

The current exact-sampler successor branch has moved beyond the earlier S109 head. Verified live head:

`claude/v64-exact-sampler-successor-20260930`

`78f13e71db968ad42486fdecb718dacd48704a5a`

That head also updates `docs/agent/ACTIVE_STATE.md`, which had been four weeks stale. A new agent must inspect this live head rather than relying on the older `498f56...` chat reference.

---

# STAGE-4 K-CURVE / S102 STATE

The repaired exact-K curve is historical measurement, not a final Stage4 safeguard.

Frozen repaired experiment:

- K = 1, 5, 20, 50, 200;
- 282 donors;
- 20 draws per K;
- exact-K occupied balanced blocks;
- 100 attempts, 100 successes;
- no topping up allowed.

Observed repaired V2 rates:

- K1: G1 1.00, G2 0.20, G3 1.00, all-five 0.20, median |CVC| 0.0127, delta/biology 1.0165, G2 Wilson95 [0.081, 0.416]
- K5: G1 1.00, G2 0.25, G3 1.00, all-five 0.25, median |CVC| 0.0078, delta/biology 0.9743, G2 Wilson95 [0.112, 0.469]
- K20: G1 1.00, G2 0.40, G3 1.00, all-five 0.40, median |CVC| 0.0057, delta/biology 0.9739, G2 Wilson95 [0.219, 0.613]
- K50: G1 1.00, G2 0.65, G3 1.00, all-five 0.65, median |CVC| 0.0030, delta/biology 0.9737, G2 Wilson95 [0.433, 0.819]
- K200: G1 1.00, G2 0.50, G3 1.00, all-five 0.50, median |CVC| 0.0040, delta/biology 0.9739, G2 Wilson95 [0.299, 0.701]

The curve is non-monotone. K50 vs K200 is unresolved at the precommitted 20 draws/cell and the intervals overlap heavily.

Treat the K50/K200 precision question as closed unresolved-by-choice rather than an indefinitely open invitation to top up. The scientific reason: post-result topping up is forbidden and distinguishing 0.65 from 0.50 would not settle S102 or authorize Stage4.

Permitted conclusion:

The historical G2 implementation has a non-monotone observed operating characteristic across the repaired exact-K synthetic confound family at the precommitted 20 draws/K. The experiment does not identify whether G2 responds to confound sharing, edge specificity, another construction feature, or sampling variability.

Not permitted:

- G2 is proven protective;
- G2 is proven useless;
- G2 contributes nothing against true edge-specific artifact;
- the historical V1 K=200 world was structurally identical to planted biology;
- the K curve determines a final margin, alpha, threshold, or equivalence rule;
- a positive Stage4 result is evidence of regulation.

The structural identifiability argument remains conceptual: an edge-private latent factor varying across metacells within donor and loading on both modalities can be statistically indistinguishable from regulation. That argument is not itself a measured operating characteristic.

---

# SCENIC+ / GSE214979 STATE

Route A historical dimensions:

- 187,215 features × 105,332 cells;
- nnz 927,291,782;
- 36,601 genes;
- 150,614 peaks;
- 3,179 microglia;
- development population 2,534 nuclei / 12 donors.

Motif resource:

- v10nr_clust_public;
- 10,249 motifs;
- direct and extended motif support must remain separate.

Crosswalk facts:

- 35,445 / 36,601 genes map FULL104;
- 4,370 / 4,372 Stage4 genes map;
- 17,686 / 150,614 peaks overlap Stage4;
- corrected Stage4 interval coverage is 22,991 / 32,153 = 71.5%;
- prior ~41.4% value came from a first-overlap bug;
- empirical coordinate evidence indicates Stage4 intervals are hg38 despite historical hg19-primary wording; do not insert a liftOver step without renewed evidence.

Route-B fragments authenticated target:

- compressed size: 63,641,120,882 bytes;
- SHA-256: `b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f`;
- 5,831,261,753 records scanned historically;
- 23,522,438 cohort fragments retained;
- 12/12 donors passing;
- barcode suffixes 5/6/7 span multiple donors, so suffix is not donor authority.

Current execution order should remain:

1. independently audit Route-B custody successor;
2. authenticate/freeze blacklist ON;
3. verify pseudobulk replay/correctness;
4. construct real Route-B consensus only with the authenticated blacklist in the algorithm;
5. audit the 512-motif pilot;
6. only then decide whether the full cisTarget build is qualified to proceed;
7. build Route-B first if qualified;
8. derive networks and run controls/donor stability;
9. Route-A/B comparison;
10. freeze network authority and crosswalks before any downstream biological claim.

Do not claim a broad SCENIC+ network exists until the actual network build and qualification are present on GitHub with receipts.

---

# SYNTHETIC ECOSYSTEM STATE AND NEXT WORK

The synthetic benchmark is not supposed to be a convenient toy. It must preserve the important real-data observation geometry while retaining planted, known biological truth.

Current intended construction:

`real empirical population/QC/coverage geometry -> synthetic hidden biology -> deterministic observation operators -> model-facing twins`

not:

`convenient fake distributions -> fake cells -> visual resemblance`

Already established or under current successor audit:

- shared master hidden truth;
- shard-size invariance;
- exact FULL104 source counts at full scale;
- deterministic stress-scale source apportionment;
- empirical reader-fit donor/source/operator population authority available;
- operator-support preservation repair at 100K in PR #205;
- paired RNA+ATAC observer;
- ATAC can carry private regulatory state while RNA does not expose it directly;
- synthetic fragment stream;
- fragment integrity verifier concept from the Route-B custody lesson;
- truth firewall;
- resource accounting;
- promotion firewall.

Required before a 100K promotion claim:

1. Audit PR #205 and prove donor/source/operator geometry is actually consumed, not merely recorded.
2. Prove RNA observation uses the empirical depth/sparsity/detected-feature calibration from the frozen expression sample rather than only storing reference statistics.
3. Add/verify real-vs-synthetic diagnostics for at least:
   - source composition;
   - donor size distribution;
   - source×operator support and occupancy;
   - RNA library-size distribution;
   - RNA sparsity / zero fraction;
   - detected features per cell;
   - feature prevalence distribution;
   - relevant correlation/dependence summaries;
   - structural missingness versus measured zeros;
   - paired multiome coverage/sparsity;
   - fragment density/storage/runtime.
4. Keep exact population geometry and sampled-QC uncertainty explicitly separate.
5. Ensure a 100K calibration pass is not declared by metadata fields alone: output must cryptographically bind the authority artifact(s) and show generated geometry/statistics derived from them.
6. Run adversarial negative cases inspired by Macha Lane 1:
   - same-size/different-byte fragment corruption;
   - copied-vs-computed digest;
   - barcode-count mismatch;
   - duplicate/conflicting barcode before dict construction;
   - fail-closed receipt emission on errors;
   - blacklist-before-consensus semantics.
7. Only after the above is independently green should 100K stress materialization be considered.
8. 500K follows only after 100K stress exposes no scaling/pathology problems.
9. Full ~4.553M twin is a qualification run, not the first stress test.

Resource projections already measured at 2K CI scale in this chat included approximately:

- truth ~142 bytes/cell;
- FULL104-like RNA ~402 bytes/cell;
- paired multiome ~776 bytes/cell;
- compressed fragments ~603 bytes/cell;
- known combined ~1,923 bytes/cell.

At 100K this implied roughly ~107.6 MB for matrices/truth and ~60.3 MB for compressed fragments, ~167.9 MB known total. This explicitly excludes pseudobulk, peaks, motif rankings, cisTarget databases, networks, perturbation and spatial outputs. Do not present this as total full-ecosystem storage.

---

# CHAT-EXCLUSIVE CUSTODY

PR #206 inventories 12 original runtime artifacts. Important examples:

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` — 303,979,881 bytes — SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` — 303,979,880 bytes — SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- reassembled archive — 607,959,761 bytes — SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — 410,278,055 bytes — SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- `checkpoints.zip` — 71,356,460 bytes — SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- `expression.zip` — 3,599,456 bytes — SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- NPZ `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — 1,531,109 bytes — SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

The five small original chat-only artifacts are recoverable from the committed tar on PR #206. Large binaries remain external/hash-bound by design. Never claim hash custody alone qualifies the scientific content.

---

# WHAT NOT TO REPEAT

Do not repeat these already-resolved or explicitly superseded paths:

- Do not rerun the historical broken sampling-with-replacement K curve as if it were exact-K.
- Do not cite historical K=200 as edge-specific or structurally identical to biology.
- Do not top up repaired K50/K200 after observing the curve.
- Do not use the historical null-significance G2 implementation as the final Stage4 rule.
- Do not treat a copied receipt digest as byte authentication.
- Do not validate duplicate conflicts after `dict(zip(...))`.
- Do not build a no-blacklist consensus and attempt to filter it later.
- Do not rerun the 3h18m Route-B pseudobulk merely to recover uncontended timing; correctness is replay-verified and no timing claim is required.
- Do not substitute the 149-donor foundation population for the reader-fit 104-donor FULL104 population.
- Do not treat sampled QC summaries as exact full-population distributions.
- Do not put technology/operator into biological identity.
- Do not open Morabito or recoverability TEST to tune architecture.
- Do not start multimodal training.
- Do not merge Macha lane branches blindly into Sol; audit and integrate narrow commits intentionally.

---

# FIRST ACTIONS FOR THE NEW AGENT

Perform these in order.

## 1. Re-pin live heads

Re-query:

- `chatgpt/v74-synthetic-calibration-closure-20261003`
- `chatgpt/v73-synthetic-stress-twin-20261002`
- `chatgpt/v73-chat-runtime-custody-20261003`
- `claude/v74-routeb-custody-20261002`
- `claude/v74-blacklist-and-512pilot-20261002`
- `claude/v74-g2-continuous-successor-20261002`
- `claude/v74-stale-claim-audit-20261002`
- `claude/v64-exact-sampler-successor-20260930`

If any have moved, inspect the new commits before relying on this handoff.

## 2. Audit Macha Route-B lane first

This is the most consequential completed Macha lane because it changes the evidence chain from self-consistent receipts to actual byte-linked custody.

Return an explicit verdict:

`ROUTEB_CUSTODY_AUTHENTICATED`

or

`BLOCKED`

with defect IDs, exact file/line or receipt paths, tests/mutations, and whether any real result changes.

## 3. Audit Lane E when it lands

Do not start a competing heavy job. Verify blacklist bytes, pilot isolation, measurement provenance, and successor scaling authority. Return whether a full Route-B cisTarget build is actually authorized.

## 4. Audit Sol PR #205

Confirm exact-head CI, inspect all 13 commits, and prove empirical calibration is consumed by generation. Return:

`STRESS_ARCHITECTURE_ACCEPTABLE_FOR_100K_PROMOTION`

or

`BLOCKED`

Do not launch 100K before this verdict.

## 5. Reconcile stale-claim authority

Check whether `ACTIVE_STATE.md`, `START_HERE`, latest handoff pointers, Stage4 closeouts, V1/V2 curve artifacts, and S102 successor contract agree. Do not mutate SHA-frozen receipts merely to make history look tidy. Prefer explicit sibling supersession notices where needed.

## 6. Keep S102 prospective

Audit the continuous-CVC successor contract. The next science question is equivalence/magnitude framing and independently justified margins. Do not choose a margin because it separates already-seen synthetic worlds.

## 7. Only after the audits converge

Proceed on two main execution tracks:

- SCENIC+ critical path: authenticated Route-B custody -> blacklist -> consensus -> 512 pilot -> full cisTarget/network if qualified.
- synthetic scaling: calibrated 100K -> 500K -> full ~4.553M twin.

Keep Stage4 real correspondence closed until the G2 successor and overall authorization are genuinely resolved.

---

# REQUIRED AUDIT REPORT FORMAT

For every lane audited, report:

- starting branch and exact SHA;
- ending/audited SHA;
- files changed relative to base;
- scientific claims made by the lane;
- which claims were independently reproduced;
- which claims rely only on commit text or self-consistent receipts;
- tests run;
- mutation/failure-injection evidence;
- any test that could not fail;
- any stale or contradictory authority surfaces;
- whether thresholds/stopping rules changed after outcome inspection;
- whether protected data/outcomes were opened;
- whether code changed a biological estimand or only custody/engineering;
- remaining blockers;
- final narrow verdict.

Do not give a generic "looks good" conclusion.

---

# CURRENT SCIENTIFIC BOTTOM LINE

The project has a mature and increasingly well-audited architecture, but several important things remain deliberately unqualified.

Qualified/strong engineering state:

- V72 coupled synthetic ecosystem architecture;
- shared hidden-truth design;
- exact-K repaired synthetic Stage4 experiment as historical measurement;
- strong Route-B custody repair direction;
- reader-fit FULL104 population geometry recovered for synthetic calibration;
- exact-head CI on the current Sol V74 calibration branch.

Not yet qualified:

- final G2/Stage4 safeguard;
- real Stage4 biological interpretation;
- full SCENIC+ regulatory network;
- 100K/500K/full synthetic stress promotion;
- multimodal training;
- protected Morabito/recoverability evaluation.

The immediate critical path is still SCENIC+ Route-B plus independent audit, with S102 successor design and synthetic calibration/scaling proceeding in parallel. The right next move is not more broad exploration; it is to finish the audit/qualification chain around the work already produced and only then promote execution scale or biological claims.
