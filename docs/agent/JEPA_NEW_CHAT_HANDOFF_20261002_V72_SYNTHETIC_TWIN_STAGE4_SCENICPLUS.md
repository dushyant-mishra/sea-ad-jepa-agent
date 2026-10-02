# JEPA NEW-CHAT TAKEOVER HANDOFF — 2026-10-02
## V72: synthetic full-project twin + Stage-4 specification audit + SCENIC+ network execution

**Purpose:** This is the canonical takeover document for the next ChatGPT/Sol agent. It is deliberately detailed and audit-oriented. The successor is expected to continue Sol's implementation work **and** independently audit Macha/Claude's Stage-4 and SCENIC+ work. Do not trust a pasted handback merely because it is detailed; verify every material claim against GitHub, receipts, and executable behavior.

---

# 0. Immediate takeover instructions

On the first turn in the new chat:

1. Re-query the four branch heads listed below. They are exact as of this handoff, but Macha may have pushed after this document was written.
2. Read this handoff before changing code.
3. Read the six raw chat uploads under `docs/agent/archive/chat_runtime_20261001/` if a chronology, exact Macha quote, or superseded claim matters.
4. Keep Sol and Macha as separate evidence/implementation authorities. Do **not** merge Macha branches into Sol's branch as a shortcut.
5. Preserve all retractions and superseded receipts; never delete an inconvenient result.
6. Do not authorize real Stage 4, Morabito, TD60, the sealed recoverability TEST, or training.
7. Continue the synthetic full-project twin while Stage-4 G2 semantics and the real SCENIC+ network remain unresolved.
8. Independently audit any new Macha push before incorporating its scientific interpretation.

The successor should call the assistant **Sol** and the external execution/audit agent **Macha**, matching the working convention in this project.

---

# 1. Exact branch heads at handoff time

Repository:

`dushyant-mishra/sea-ad-jepa-agent`

## Sol implementation branch

`chatgpt/v64-privileged-information-recoverability-20260930`

Head:

`4fd4305395c4da0c025f336006be7c9dbbe6dd70`

Latest commit:

`V71: add synthetic pipeline readiness validator`

This branch contains V64–V71 architecture work, including the initial V71 synthetic-twin contracts and small fixture. It **does not** contain Macha's latest Stage-4 or SCENIC+ execution work.

## Macha Stage-4 branch

`claude/v64-exact-sampler-successor-20260930`

Head:

`759bf0f276307ad296e9a8669f39adccc1a7f83a`

Latest commit:

`S102: the G2 test is not specified by the contract, and the one I chose gets stricter with n`

Important recent lineage:

- `943abc740055...` — V2 320-draw calibration landed
- `8617fe9b3a20...` — G2 sensitivity curve precommit
- `e37ae28ffcf9...` — K-parameterised hidden-confound world and runner
- `ca532b5b4ba9...` — S100: runner invented an unfrozen tolerance; corrected before draws
- `54aeaebf4386...` — endpoint overlap test demoted to corroboration
- `759bf0f27630...` — S102 G2 contract specification gap disclosed

## Macha SCENIC+ branch

`claude/v69-scenicplus-external-network-20261001`

Head:

`f8dc493516db079fd529e4a69f370d8b9db0dfad`

Important recent lineage:

- `c39e688c98ce...` — S23 rankings RNG seed defect
- `f5142f4a90b7...` — BLAS pinning output-equivalence result
- `c0f05ffc5cda...` — Route-B pseudobulk extractor written, not run
- `1ef3687cfa14...` — Route-B MACS/consensus producer written, not run
- `6a540263a149...` — C-vs-D storage digest equivalence; SSD bind mount no speed advantage
- `0a1c5733e1c9...` — speed benchmark receipt updated; worker scaling still partial
- `3e8af232d175...` — unpinned cisTarget tool-recipe hazard documented
- `f8dc493516db...` — tested-vs-assumed self-audit update

## Docs-only chat custody/handoff branch

`handoff/jepa-20261001-chat-exclusive-custody`

Head before this successor package:

`b8e985b2f8927b5b0bd7ca4ce2be18a9f5a18d96`

This branch is intentionally documentation/archive only and is based on Sol head `4fd4305...`. It contains the six raw chat uploads and the prior custody handoff.

---

# 2. Source-of-truth hierarchy

When sources disagree, use this order:

1. **Current repository bytes at an exact SHA**.
2. **Machine-readable receipt produced by those bytes**.
3. **Prospective/frozen contract or precommit written before execution**.
4. **Independent audit/recomputation**.
5. **Commit message**.
6. **Pasted Macha handback / chat transcript**.
7. **Narrative recollection**.

A commit message is provenance, not proof that the claimed bytes were actually written. This project has already observed multiple cases where commit messages claimed file changes that did not occur.

A PASS receipt is also not automatically evidence that the check could fail. For every gate, ask:

- what input would make this check fail?
- what input would make this check pass?
- can either condition actually be reached?
- is the gate comparing semantics or merely filenames/string sentences?

---

# 3. Non-negotiable governance

At takeover:

- Stage 4: **NOT AUTHORIZED**
- Real NIH-CARD RNA×ATAC correspondence: **UNOPENED**
- Training: **OFF**
- Multimodal training: **OFF**
- Morabito: **PROTECTED**
- TD60: **BLOCKED**
- real recoverability TEST: **SEALED**
- broad current SCENIC+ eRegulon network: **NOT YET QUALIFIED**
- no synthetic result may be presented as biological confirmation

Technology remains an observation operator, not a biological covariate:

`z_biology -> O_t -> X_observed`

Structural missingness is not biological zero.

Do not pool cells/donors across external cohorts to manufacture a larger biological n.

---

# 4. Core JEPA biological architecture

Teacher constructs state from richer evidence; RNA student predicts only the recoverable/shared state.

Teacher state:

`Z_teacher = Z_global ⊕ Z_query ⊕ Z_reg_shared ⊕ Z_reg_private`

RNA student target:

`Z_global ⊕ Z_query ⊕ Z_reg_shared`

`Z_reg_private` remains teacher-private and must never be forced into the RNA student loss.

Training concept:

`RNA -> Student -> predicted shared state`

compared with a richer teacher representation built from qualified privileged evidence.

Inference:

`new RNA -> Student -> predicted shared biological state + uncertainty`

If two cells have identical RNA but differ only in privileged/private regulatory state, the correct RNA-only response is uncertainty, not hallucination.

Important user correction preserved from project history:

**We are not predicting the actual hidden gene; we are predicting the biological state.**

---

# 5. FULL104 backbone

Current audited FULL104 reader-fit:

- 4,553,407 cells
- 104 donors
- 41,238 canonical molecular addresses
- 42 reader operators

Source cells:

- HVS: 198,718 = 4.364%
- NPH52: 236,476 = 5.193%
- SEA_AD: 4,118,213 = 90.442%

Address support:

- 17,346 measured by all 3 source families = 42.063%
- 17,186 measured by all 42 operators = 41.675%

Any measured by source:

- HVS: 18,736 / 41,238 = 45.434%
- NPH52: 35,098 / 41,238 = 85.111%
- SEA_AD: 35,076 / 41,238 = 85.057%

All operators in source:

- HVS: 18,736 = 45.434%
- NPH52: 29,136 = 70.653%
- SEA_AD: 35,076 = 85.057%

Approximate structural support/missingness:

- HVS measured ~45.43%; structurally unmeasured ~54.57%
- NPH52 measured ~80.71%; structurally unmeasured ~17.97%; collision unresolved ~1.321%
- SEA_AD measured ~85.06%; structurally unmeasured ~13.22%; collision unresolved ~1.722%

Never convert structural absence to expression zero.

---

# 6. Stage-4 substrate and frozen intent

## Phase A

Accepted V3:

- 13,175 retained edges
- denominator 20,709
- genes 4,372
- promoters 5,964

## Phase B

- 282 qualifying donors
- 84,129 microglia
- 3,231 metacells
- 4,372 genes
- 32,153 intervals
- 37,419 pair keys
- T5 rows 10,552,158
- T3 nnz 6,624,289
- T4 nnz 55,467,544
- pairs meeting minimum donors: 36,794
- aggregate binding:
  `2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`

Availability states:

1. `MEASURED`
2. `NOT_MEASURED_RNA_ZERO_COVERAGE`
3. `NOT_MEASURED_ATAC_ZERO_COVERAGE`
4. `NOT_MEASURED_RNA_ZERO_VARIANCE`
5. `NOT_MEASURED_ATAC_ZERO_VARIANCE`

Key Stage-4 substrate hashes:

- T5: `5403458558ea9d5c4b7adb3a86b8c514526713c4b3561fbb6754584a2066efa8`
- availability: `4aeebb8b82f3fe395a5da4ae48b8d3a2b5b7405620721b940f6563eb93606a81`
- aggregate receipt: `f98125f3710a252fbafd90ff7110db2c393a7cd647d98f1e312f5602335ccaf5`
- closeout receipt: `12d460bfc0ea863e31d91b2eaad15d4fead0f6f5a18beb8086104d282d823020`
- R3 conditioning: `82045d8fe26c46ac03462adffeff1dca266465e44384b9e97bf58f32b4a2f0a2`
- enum intervals: `4b78ef131b06f69729ca92db436ffaad3fe8f966b8d0e62e9771dc7d2c1fc619`
- statistical contract: `f537564edf9217bfa60f98e8aabc30267fa56d1f1eeab98e4aef3a7d7792bdf9`
- measurement substrate: `17987ce727382cd6fcd998de2cca285eb12063889236bdbc553dfe500a9ca32b`

Frozen design intent:

- per donor/pair Pearson across metacells
- RNA gene vs ATAC assigned peak set
- measured zero remains zero
- zero coverage/variance -> MISSING
- nuisance basis: 14 features, ridge alpha 1.0, 5-fold promoter cross-fit
- primary distance convention: hg19 source convention
- actual Stage-4 matrix interval coordinates empirically resolved as hg38/GRCh38
- >=100 microglia/donor
- >=4 metacells/donor
- >=30 donors/edge
- primary donor-averaged `GENE_BALANCED` residualized linked-control difference
- `PROMOTER_EQUAL` mandatory companion
- `EDGE_EQUAL` sensitivity
- donor-only bootstrap 4000, seed 20260929
- no prospectively frozen minimum real Delta

Anti-false-green controls include control-vs-control, covariate balance, support concentration and pairing/funnel checks.

---

# 7. Stage-4 chronology that the successor MUST preserve

## 7.1 Early synthetic qualification was not enough

Macha's early end-to-end worlds appeared to show:

- biology passes
- measured technical largely adjusted
- hidden confound can fool the statistic

A 4-seed robustness run later showed seed dependence and motivated a larger prospective calibration.

## 7.2 V1 160-draw calibration — executed faithfully but invalid for frozen-design inference

V1 measured:

- TRUE_NULL near nominal
- MEASURED_TECHNICAL high positive rates, 0.875 at 60 donors and 1.000 at 282 donors

This looked alarming.

Then S99 showed the synthetic fixture used the wrong control construction: controls were effectively random rather than the frozen `PROMOTER_FIXED_DISTAL_MATCHED_CONTROL`.

Therefore:

**V1 rates are valid statements about that old fixture only. They must never be quoted as Stage-4 design calibration without the S99 qualification.**

Do not delete V1.

## 7.3 S99 repair

The repaired synthetic control construction:

- same promoter
- distance matched under the frozen tolerance
- non-overlapping linked/control interval
- symmetric accessibility qualification
- same measurement/matching support
- trim edges with no admissible control
- fail closed if matching audit fails

This permanently changes the synthetic-twin requirement: a synthetic benchmark must reproduce **selection and matching mechanisms**, not merely similar distributions.

## 7.4 Five gates implemented

The executor now computes the full intended decision components:

1. G1 primary one-sided LCB95 > 0
2. G2 control-vs-control null
3. G3 worst absolute SMD <= 0.25
4. G4 top 1% donor contribution <=10%, with Kish ESS
5. G5 funnel/attrition reconciliation

Important audit note:

G4 is close to structurally vacuous under equal donor weighting. It was implemented as frozen rather than redefined.

## 7.5 V2 320-draw calibration — real result

Commit:

`943abc740055da641638852d4ab06856aab55b27`

Design:

4 worlds × 2 donor counts × 40 draws = 320 runs.

Worlds:

- BIOLOGY_POSITIVE
- TRUE_NULL
- MEASURED_TECHNICAL
- HIDDEN_CONFOUND

Results:

| world | all-five @60 | G1 | G2 | G3 | all-five @282 | G1 | G2 | G3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BIOLOGY_POSITIVE | 0.750 | 1.00 | 0.78 | 0.97 | 0.625 | 1.00 | 0.62 | 1.00 |
| TRUE_NULL | 0.000 | 0.05 | 0.97 | 0.95 | 0.050 | 0.05 | 0.97 | 0.93 |
| MEASURED_TECHNICAL | 0.000 | 0.15 | 0.70 | 0.00 | 0.000 | 0.38 | 0.38 | 0.00 |
| HIDDEN_CONFOUND | 0.200 | 1.00 | 0.23 | 0.85 | 0.100 | 1.00 | 0.10 | 0.97 |

### Result that IS settled

The old measured-depth alarm is retracted.

- 0/80 MEASURED_TECHNICAL draws pass the full decision
- G3 fails in 100% of those draws
- worst SMD median ~1.88–1.90 on `atac_depth_sensitivity`

Under this planted matched-control depth world, the frozen matching/balance machinery catches the artifact.

TRUE_NULL G1 fires at exactly 0.05 at both donor counts.

### Hidden-confound magnitude

The tested hidden confound has median Delta essentially indistinguishable from genuine biology:

- ratio ~1.0144 at 60
- ratio ~1.0234 at 282

No simple “small effect” interpretation separates that synthetic confound from biology.

## 7.6 S102 changes the interpretation of G2

This is the most important current Stage-4 specification issue.

Macha audited the frozen contracts and found they say only:

- control-vs-control “must not show excess”
- a nonzero control-vs-control contrast means the pipeline may manufacture a difference

The contracts **do not define a test, statistic or level for G2**.

Macha had implemented G2 as:

`two-sided 95% donor-bootstrap interval must contain zero`

That is an executor choice, not a frozen contract term.

As n rises, a null-significance test becomes stricter around tiny residual drift. Therefore the observed biology G2 pass rates 0.78 -> 0.62 may reflect the chosen test tightening rather than the biological design getting worse.

The earlier headline “the complete design discards roughly a third of real signal at 282 donors” is therefore **not currently safe to state as a property of the frozen design**.

Macha correctly did not change the G2 rule after seeing the result.

He added a diagnostic:

`|control-vs-control Delta| / |primary Delta|`

with **no threshold**, because choosing a threshold after V2 would create another unfrozen number.

Canonical biology example:

- cvc Delta ~0.00280
- current G2 CI ~[-0.0063, 0.01198]
- magnitude ratio ~0.00505

### Decision required from contract owner / Sol + user

Before real Stage 4, G2 must be prospectively specified.

Possible semantic families:

1. **Null-test reading**
   - “no statistically detectable control-control difference”
   - becomes stricter with more data

2. **Magnitude/equivalence reading**
   - “manufactured difference is sufficiently small”
   - requires a prospectively justified equivalence/magnitude margin

Do **not** choose a threshold from V2 outcomes.

This must be resolved before Stage 4 can be authorized.

## 7.7 K-parameterised hidden-confound sensitivity experiment

Macha built a noncanonical `HIDDEN_CONFOUND_K` world.

K controls sharing:

- K=1: one metacell-level hidden factor shared across all edges
- increasing K: progressively less sharing
- K≈edge count: edge-specific factors

The hypothesis:

G2 may be detecting **shared structure**, not hidden confounding per se.

Smoke test at K=5:

- 40 edges/block
- matching audit passes
- adjusted Delta ~+0.5388
- control-vs-control Delta ~+0.0114

This is directionally consistent with the hypothesis but is one smoke run only.

The 100-draw K curve is **not yet launched at current GitHub head**.

Why held:

SCENIC+ worker-scaling benchmark had machine priority; running both would contaminate the timing curve.

### S100 and S101 self-audits

S100:
The runner initially invented ±0.20 as “matches biology.” The precommit did not define that tolerance. It was removed before any long draws.

S101:
The replacement endpoint Wilson-interval overlap test is nearly unable to fail with 20 draws/cell. It was demoted to corroboration.

Primary evidence is now intended to be the **shape of the G2 rate across K**, not the endpoint overlap.

No draw count was increased after discovering weak power.

### Critical caveat

Because S102 means G2 itself is under-specified, the K curve inherits that ambiguity. The successor should preserve the current implementation for historical comparability and report its raw/statistical outputs, but should not promote its G2 PASS rates into the final Stage-4 contract until G2 semantics are prospectively closed.

---

# 8. SCENIC+ / GSE214979 lane

## 8.1 Route A authenticated substrate

GSE214979 Route A:

- matrix: 187,215 features × 105,332 cells
- nnz: 927,291,782
- 36,601 genes
- 150,614 peaks
- all microglia: 3,179
- default development population: 2,534 nuclei / 12 donors
- pathology-blind exclusion frozen prospectively

Motif resource:

SCENIC+ v10nr_clust_public

- 10,249 motifs
- HGNC annotation pinned
- direct vs orthology/similarity/extended support must remain separate

Structural crosswalk:

- 35,445 / 36,601 GSE RNA features map to FULL104 in the current development population
- 4,370 / 4,372 Stage-4 genes present
- 17,686 / 150,614 GSE peaks overlap at least one Stage-4 interval
- corrected Stage-4 interval coverage:
  22,991 / 32,153 = 71.5%

The earlier 13,325 / 32,153 = 41.4% value was a bug: only the first overlapping Stage-4 interval was counted. Preserve this correction and the original erroneous value in audit history.

## 8.2 Genome build resolution

Stage-4 identifiers/design wording could be misread as hg19.

Macha empirically checked 57 enumerated-control pair keys:

- 57/57 actual substrate intervals match hg38 coordinates
- 0/57 match hg19

Therefore the actual Stage-4 interval matrix and GSE214979 Route A are both GRCh38/hg38. No liftOver is required for this structural crosswalk.

Do not confuse “hg19-primary distance convention” with matrix coordinate build.

## 8.3 Route-B fragment asset

Authenticated fragments file:

- bytes: 63,641,120,882
- SHA-256:
  `b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f`

Independent re-hash in this chat matched exactly.

Route-B QC completed:

- full scan, not partial
- records scanned: 5,831,261,753
- cohort-barcode records kept: 23,522,438
- outside-cohort/failing records counted and discarded
- 12/12 development donors have passing cells

Earlier handback said QC was still running because the receipt was looked for in the wrong directory. The receipt actually lives under `receipts/`. Preserve the path error as provenance history.

## 8.4 Barcode donor identity guard

Real data showed barcode suffixes 5, 6 and 7 each span more than one donor.

Therefore:

**donor identity must never be inferred from barcode suffix.**

Every producer touching barcodes should join through the frozen barcode→donor authority and fail closed on suffix-derived mappings.

This is a measured data defect, not a theoretical precaution.

## 8.5 Route-B next producers

Macha has written but not executed at current GitHub head:

`scripts/v69/routeb_extract_pseudobulk_fragments_v1.py`

Intent:

- stream the full fragments file
- keep only cohort barcodes passing explicit >=1000-fragment QC
- pseudobulk unit = donor × published microglial subcluster
- discard/count outside-cohort records
- fail closed on donor-identity guard
- re-read outputs from disk before receipt

And:

`scripts/v69/routeb_call_peaks_and_consensus_v1.py`

Intent:

- reuse pycisTopic's own `peak_calling()`
- reuse `get_consensus_peaks()`
- MACS2 2.2.9.1 because validated container lacks MACS3
- BEDPE
- shift 73
- ext_size 146
- keep_dup all
- q=0.05
- `nolambda=True`
- peak_half_width 250
- compute donor recurrence for every consensus region
- do not filter by recurrence before reporting it

### MACS text erratum

The frozen prose called the settings “pycisTopic protocol defaults” but omitted `--nolambda` from the typed flag list. pycisTopic uses `nolambda=True` by default.

Macha recorded this as an under-specified string, not a tuned parameter change.

## 8.6 Open blacklist decision

The freeze does not specify an ENCODE blacklist.

pycisTopic protocols normally exclude blacklist regions.

Macha correctly did not silently add or omit it as if settled.

Before freezing Route-B region universe, the successor/user must make an explicit prospective amendment:

- apply a pinned/authenticated blacklist, or
- explicitly omit it and carry the artifact-region limitation

Do not make this choice after looking at which option gives nicer Route-A/B agreement.

---

# 9. SCENIC+ compute/reproducibility speed work

The original projected custom cisTarget cost was ~33.7–41.2 hours per route, ~67–83 hours for two independent route builds.

The goal became: shorten wall time without changing biology.

## 9.1 S23: rankings RNG seed defect

The cisTarget builder generated a fresh random seed to break ranking ties.

On identical workloads:

- score feathers were identical
- rankings feather differed

Consequences if unfixed:

- production rankings irreproducible
- storage/worker digest comparisons falsely look numerically inconsistent

Fix:

explicit ranking seed `20261001`

Treat it as an engineering convention, not a biological parameter.

## 9.2 BLAS oversubscription

Image had OpenBLAS defaulting to 16 threads.

At 16 outer workers on an 8-physical-core machine this can explode into severe oversubscription.

BLAS/OpenMP threads were pinned to 1.

Measured equivalence:

both score feathers were bitwise identical pinned vs unpinned.

Therefore pinning is safe as an execution fix.

## 9.3 Union scoring reuse — major legitimate speedup

Prospective equivalence test:

- two disjoint 2,000-region slices
- union deliberately assembled in reversed order
- score union once
- subset back by region name

Results:

- scores: 0/16,000 cells differ; max diff 0
- ranking counter-control: 15,981/16,000 differ

Conclusion:

**motif-region scoring may be shared across Route A ∪ Route B**

but

**route-specific rankings may NOT be shared**

if the full implementation preserves the tested semantics.

This can approximately halve the dominant duplicate scoring cost without changing the scientific route comparison.

## 9.4 C: SSD vs D: external drive

User has ~193 GB free on internal SSD; project data is on external drive.

A pinned-seed/pinned-thread 16-motif ×150,561-region benchmark compared Docker Desktop bind mounts:

- D external: wall 532 s, cbust 203.1 s
- C internal SSD: wall 535 s, cbust 206.6 s

All three outputs byte-identical.

Conclusion:

**C bind-mounted SSD showed no measurable speed advantage.**

Caveat:

both paths were Docker Desktop bind mounts, so mount-layer overhead may dominate. This does not test true container-local or WSL-native storage.

Do not spend scratch budget simply copying cisTarget bind-mounted data to C.

## 9.5 Worker-scaling state

Latest chat handback, not yet fully committed to GitHub at current SCENIC+ head, reports an idle-machine 16-motif curve:

- t4: wall 604 s; cbust 339.6; non-scoring 264.4
- t8: wall 486 s; cbust 222.4; non-scoring 263.6
- t16: wall 513 s; cbust 184.0; non-scoring 329.0

All measured points had identical digests.

Interpretation:

- scoring continues improving beyond 8
- gain 8->16 is small
- non-scoring phase incurs ~65 s penalty beyond physical-core count
- t8 is currently the observed wall-clock minimum

At latest chat handback, t2 and t1 were still running and full worker curve was not yet committed.

**First SCENIC+ takeover action: re-query branch and find whether the full scaling receipt landed.**

Do not claim 8-worker production configuration until the completed receipt exists and is audited, even though it is very likely.

## 9.6 Sharding requirements

Hard requirements:

- deterministic motif shards
- immutable ordered motif list per shard
- motif-list SHA
- region-universe SHA
- FASTA SHA
- container image ID
- explicit ranking seed
- explicit worker/thread settings
- output SHA
- completion receipt written only after output closed and re-read from disk
- failed shard restartable independently
- merge proves exact ordered union of motif lists, no duplicates/omissions
- merged database motif axis equals expected list element-by-element
- never edit a mounted script while it is running; execute immutable snapshots
- voiding a run must stand down watchers/monitors

## 9.7 cisTarget build-recipe hazard

The current Dockerfile recipe clones `create_cisTarget_databases` from unpinned `master`.

The validated current image is still reproducible by its recorded content digest, so current results are not invalid.

But a future rebuild from the Dockerfile could silently use different code.

Current tool aggregate content digest:

`25845094fbc2202e5c96add0ea6f984be9950b6c8e7855cd92f0d72c1ae007b4`

Macha correctly did not edit the current recipe in place because that would sever even the weak correspondence to the validated image.

Future successor recipe should:

- pin exact create_cisTarget_databases commit matching current bytes if possible
- record git metadata in image
- pin cbust/liftOver/downloaded tools by digest
- emit aggregate tool digest at build time
- explicitly distinguish validated old image from successor recipe

---

# 10. SCENIC+ historical prior art and interpretation limits

Historical Stage75F:

- only 10 regulators
- 96 TF-target rows
- hypothesis-generating only

Do not call it a qualified network.

The old explanation of Stage75F failure has itself changed multiple times. Do not reduce it to one sentence.

Current more defensible contributing limitations include:

- too few query regions per TF (~57–91)
- sparse direct motif support
- annotation-supply problems
- previous processed-region strategy limitations

Current prospective rule:

programs inferred from fewer than 100 regions should be `UNRESOLVED`, not “absent.”

Direct and extended/orthology/similarity motif support must remain separate evidence classes.

No current broad GSE214979 eRegulon network is yet qualified.

---

# 11. Multi-source regulatory integration

NIH-CARD remains the sole **primary Stage-4 correspondence experiment**.

Other modalities/cohorts are independent evidence channels at regulatory-program level:

- PRIMARY_CORRESPONDENCE
- REGULATORY_ARCHITECTURE
- SAME_NUCLEUS_SUPPORT
- SEPARATE_NUCLEUS_REPLICATION
- CAUSAL_SUPPORT
- INTACT_TISSUE_SUPPORT
- TRANSPORT_SUPPORT

Do not concatenate cohorts into one biological n.

Program identity must be immutable/versioned:

- program_id/version
- definition source
- TF ids
- target gene ids
- region ids/build
- construction population/method
- membership SHA
- status

Membership or region-set changes create a new program version.

Teacher-candidate eligibility should require:

- frozen/versioned SHA-bound program
- source-specific crosswalks
- Stage-4 interpretable if Stage 4 is used
- >=1 additional evidence family with a different dominant failure mode
- no protected outcome used to define/prune membership
- explicit missingness/disagreement
- default minimum distinct biological evidence families = 2

Forbidden:

- promoting largest Delta
- pruning against protected Morabito outcome
- choosing Route A/B because protected agreement is favorable
- ad-hoc weighted score after seeing outcomes
- treating FULL104 predicted transport as independent validation
- treating absence in a source as biological negative

---

# 12. External evidence coverage reminders

## NIH-CARD Stage 4

Direct development substrate:

- 84,129 microglia
- 282 donors
- 4,372 genes = 10.602% of FULL104 address registry

Do not divide NIH-CARD cells by 4.55M FULL104 cells and call that “coverage.”

## Morabito GSE174367

Structural feature coverage:

- 37,966 / 41,238 FULL104 addresses = 92.066%
- 18 shared RNA/ATAC donors
- 4,126 RNA microglia
- 12,232 ATAC microglia
- separate nuclei, not cell-paired

Morabito remains protected.

## SEA-AD public paired multiome

- 66,288 exact paired RNA/ATAC nuclei overall
- 16 donors
- 1,594 candidate-myeloid paired nuclei across 15 donors

Internal same-nucleus anchor, not a pristine independent cohort.

## Perturbation atlas

- 8 studies
- 16 authenticated physical assets
- 16 processed assets
- 0 globally training-ready studies in the atlas state

Evidence remains target/program-specific; do not invent a global FULL104 percentage.

## Spatial

Recovered R4 is supporting only:

- full three-program state not covered
- homeostatic program absent from recovered panels
- lipid/DAM incomplete
- detection/segmentation asymmetry exists
- custody incomplete

---

# 13. V71 full synthetic benchmark/twin — current Sol work

This is the primary unfinished Sol implementation lane.

The user explicitly wants a **very realistic synthetic ecosystem** that tests the entire JEPA pipeline, not merely Stage 4.

One shared hidden truth should generate multiple synthetic datasets through different observation processes.

Hidden truth should include:

- `Z_global`
- `Z_query`
- `Z_reg_shared`
- `Z_reg_private`
- source-specific biology
- technical latents
- true TF→region→gene graph
- recoverability truth
- intervention truth

The pipeline must remain blind to truth until final unblinding.

## Synthetic datasets required

### FULL104-like RNA backbone

Target full scale:

- 4,553,407 cells
- 104 donors
- 41,238 addresses
- SEA_AD/NPH52/HVS source imbalance
- 42 reader operators
- structural missingness/operator coverage patterns
- source/donor technical structure

### NIH-CARD Stage-4-like RNA+ATAC

Must reproduce:

- donor/metacell structure
- overlapping 5 kb interval geometry
- linked edges
- promoter-fixed matched controls
- distance/accessibility qualification
- matching/selection/trimming mechanism
- measured depth confound worlds
- shared and edge-specific hidden confounds
- all five Stage-4 diagnostics
- missingness semantics

### GSE214979 / SCENIC+-like paired multiome

Must mimic raw-ish inputs:

- same-nucleus RNA/ATAC barcodes
- 10x-style multiome matrix structure
- fragments TSV.gz
- metadata CSV
- donor imbalance
- submitted Route-A peak universe
- Route-B fragments→pseudobulk→MACS→consensus peaks
- motif annotation supply
- direct vs extended support
- route disagreement
- program-level stability

### Morabito-like separate-nucleus RNA/ATAC

- broad feature overlap
- donor-level correspondence
- separate RNA/ATAC nuclei
- no fake cell pairing

### SEA-AD paired multiome-like anchor

- exact same-nucleus paired observations
- smaller candidate-myeloid population
- separate evidence class

### Perturbation-like datasets

- guide assignments
- guide noise
- target engagement
- positive/negative controls
- perturbation efficacy variation
- program-specific causal effects

### Spatial-like datasets

- limited panels
- missing programs
- segmentation/detection bias
- intact-tissue support only
- no missing=zero shortcut

### Synthetic checkpoints

Required adversarial twins:

- healthy checkpoint
- partial checkpoint
- collapsed checkpoint
- source shortcut
- donor shortcut
- private-state leakage
- overconfident unrecoverable state
- corrupted manifest / wrong axes

## Progressive scales

1. CI twin: ~10k cells
2. stress twin: ~100k–500k cells
3. full twin: 4,553,407 cells /104 donors /41,238 addresses

Do not jump straight to full scale.

---

# 14. V71 files already committed on Sol branch

Committed sequence:

- `2ae9122df04e...`
  `results/v64/V71_FULL_SYNTHETIC_TWIN_SYSTEM_CONTRACT_V1.json`

- `a83a3df5bb07...`
  `results/v64/V71_SYNTHETIC_RAW_ETL_CONTRACT_V1.json`

- `3646d1d87e0b...`
  `results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json`

- `d7966e16fc80...`
  `results/v64/V71_SYNTHETIC_TRUTH_FIREWALL_CONTRACT_V1.json`

- `8fcac421cdb2...`
  `results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json`

- `6b3dbb0e7684...`
  `scripts/v64/build_v71_small_synthetic_etl_fixture.py`

- `c9e4ad87768d...`
  `scripts/v64/validate_v71_small_synthetic_etl_fixture.py`

- `792542649aab...`
  `tests/test_v71_small_synthetic_etl_fixture.py`

- `4fd4305395c4...`
  `scripts/v64/validate_v71_synthetic_pipeline_readiness.py`

Small fixture currently models:

- 120 cells
- 24 genes
- 30 peaks
- 8 donors
- SEA_AD/NPH52/HVS imbalance
- hidden global/shared/private states
- RNA/ATAC counts
- HVS structural missingness block
- physically separated hidden-truth root
- protected-like metadata fields
- digests/manifests

Behavioral tests include:

- clean pass
- physical truth separation
- duplicate barcode failure
- transpose corruption
- metadata barcode reorder
- truth leak
- digest mismatch

## CRITICAL: V71 is not CI-qualified yet

At Sol head `4fd4305...`:

- V71 test files exist
- V71 readiness validator exists
- they have **not been established as run/passing in this handoff**
- the main workflow `.github/workflows/v64-privileged-architecture-smoke.yml` only includes V64–V70 path triggers/tests
- V71 artifacts/tests are absent from that workflow

The successor must not say “V71 passed CI.”

---

# 15. V71 work that still needs to be implemented

## Priority A — finish R0/R1 qualification plumbing

1. Add tests for `validate_v71_synthetic_pipeline_readiness.py`.
2. Run the existing V71 fixture tests locally/CI.
3. Update `.github/workflows/v64-privileged-architecture-smoke.yml`:
   - trigger on V71 docs/results/scripts/tests
   - execute V71 fixture tests
   - execute V71 readiness validator
4. Verify exact-head GitHub Actions.
5. Preserve failure outputs if CI fails.

## Priority B — encode the lessons learned since V71 contracts were first written

Add explicit contracts/tests for:

### Stage-4 geometry and selection

- overlapping 5 kb windows
- one peak may overlap many Stage-4 windows
- all-overlaps, not first-overlap-only
- promoter-fixed control selection
- distance matching
- accessibility qualification
- edge trimming if no admissible control
- donor/metacell construction
- G2 under-specification represented as an open contract variable, not silently frozen to current executor choice

### Barcode/donor identity

- suffix collisions
- frozen barcode→donor join
- failure on suffix-derived donor mapping

### SCENIC+ reproducibility

- explicit rankings RNG seed
- worker-axis digest equivalence
- BLAS/OpenMP pinning
- route union score reuse
- route-specific rankings
- immutable script snapshots
- shard completion re-read from disk
- merge axis/order verification
- tool-content digest binding

### Raw-route fidelity

Synthetic Route B must actually produce fragments, donor-aware pseudobulks, MACS peak calls and consensus peaks rather than receiving a pre-clean matrix.

## Priority C — executable coupled hidden truth

Build a multi-dataset generator where one hidden truth is projected through all observation operators.

Do not create each synthetic dataset independently; that would fail the main cross-source integration test.

## Priority D — checkpoint twins

Create behaviorally distinct checkpoints and validators for:

- healthy
- collapse
- source shortcut
- donor shortcut
- private leakage
- overconfidence under unrecoverable state
- manifest/axis corruption

The validation should test actual behavior, not JSON sentences.

## Priority E — scale progression

After CI twin passes:

- stress-scale ETL and memory tests
- then full 4.55M-cell twin

Do not freeze quantitative SCENIC+ network topology until real Route-A/B network characteristics are known.

Do not freeze final Stage-4 hidden-confound/G2 behavior until G2 semantics are prospectively resolved.

---

# 16. Macha audit protocol for the successor

Every Macha handback should be treated as a candidate result, not accepted truth.

For each new Macha report:

## Step 1 — identify exact pushed head

Query GitHub branch ref.

Do not rely on a short SHA in pasted text if branch has advanced.

## Step 2 — enumerate new commits since last audited head

For each commit:

- commit SHA
- first-line message
- changed files
- whether source/test/result/docs changed
- whether commit claims more than diff contains

## Step 3 — inspect material artifacts

Open:

- executable code
- machine-readable receipt
- prospective contract/precommit
- tests
- self-audit document

Do not audit from commit message alone.

## Step 4 — verify chronology

Ask:

- Was precommit actually committed before draws?
- Did a fixture/code change occur before or after seeing results?
- Were draw counts/thresholds altered after outcomes?
- Were failures kept?
- Were canonical fixtures restored/rebuilt and digests checked?

## Step 5 — test for false-green / false-red checks

Common project defect classes:

- check cannot fail
- check cannot pass
- filenames compared instead of semantic artifact kinds
- string assertions instead of behavior
- digest computed on in-memory object rather than re-read file
- mutable script edited while process reads it
- wrong directory/receipt path
- source axis/order silently changed
- first-overlap-only instead of all overlaps
- barcode suffix treated as donor
- structural missingness treated as zero
- null-significance gate tightened merely by larger n
- unpinned RNG seed
- BLAS/worker oversubscription
- unpinned dependency `master`
- commit message claims absent from file diff

## Step 6 — independently recompute a small subset when possible

Examples:

- S89-style parent quantities
- region overlaps
- ordered-axis digest
- control matching audit
- worker output digests
- route-union equivalence
- donor identity collisions

## Step 7 — classify claims

Use labels such as:

- VERIFIED
- VERIFIED_WITH_LIMIT
- SUPPORTING_ONLY
- SYNTHETIC_SOFTWARE_ONLY
- STRUCTURAL_ONLY
- SUPERSEDED
- RETRACTED
- UNRESOLVED
- NOT_AUTHORIZED

Never silently promote a synthetic result to biological evidence.

## Step 8 — push audit artifacts separately

Prefer docs/results/audit commits that do not mutate Macha's execution branch.

If Sol changes implementation in response, clearly separate:

- audit finding
- implementation fix
- new prospective design
- subsequent execution

---

# 17. Known Macha self-audit findings to keep in perspective

Do not lose these:

- S0/S7–S15: commit messages claimed self-audit text that Windows encoding replacement had not actually inserted
- S6: first-overlap-only structural crosswalk bug, 41.4% -> 71.5%
- S16/S24: editing executing mounted scripts caused command re-entry
- S20: BLAS oversubscription
- S23: random ranking seed
- S25: voided run left watcher alive
- S26: frozen MACS flag string omitted `--nolambda`
- S27: comparator compared run-specific filenames and could never pass
- S99: synthetic controls did not implement frozen matched-control construction
- S100: G2 sensitivity runner invented an unfrozen tolerance
- S101: endpoint overlap test almost could not fail
- S102: G2 itself was not statistically specified by the frozen contract

These are not reasons to discard Macha's work. They are reasons to keep independent auditing active.

---

# 18. Do-not-redo list

The successor should not restart:

- FULL104 coverage auditing
- Phase A V3 selection
- Phase B substrate assembly
- Stage-4 exact sampler qualification history
- B6 metadata-only correction
- generic V64/V65 recoverability architecture
- basic shared/private teacher-state synthetic proof
- initial V69/V70 multisource integration contracts
- GSE214979 Route-A acquisition
- motif collection acquisition
- hg38 vs hg19 Stage-4 coordinate resolution
- GSE214979 FULL104 structural crosswalk from scratch
- Route-B 63.6 GB fragment acquisition
- Route-B full fragment QC
- V1 calibration as if still authoritative
- C-vs-D bind-mounted storage benchmark
- union-score equivalence experiment
- BLAS output-equivalence experiment

Use those results as historical substrate and reopen only if an audit finds a concrete reason.

---

# 19. Immediate next actions, in priority order

## 19.1 First: re-query Macha branches

Because the last chat ended while long jobs were running.

### SCENIC+ expected possible new results

Look for:

- complete 1/2/4/8/16 worker scaling receipt
- 128-motif decomposition / shard-size recommendation
- Route-B pseudobulk extraction receipt
- Route-B consensus-peak receipt
- explicit blacklist amendment
- custom cisTarget build launch

Audit each before accepting.

### Stage 4 expected possible new results

Look for:

- G2 K-sensitivity curve execution
- any proposed G2 contract amendment

Do not allow a G2 threshold to be justified from V2/K outcomes after the fact.

## 19.2 Close V71 CI gap

This is the cleanest Sol work available immediately and does not depend on long Macha jobs.

Add V71 tests/readiness validator to CI and run.

## 19.3 Add post-S99/post-S102 synthetic-twin contracts

The current V71 contracts predate several critical lessons.

Add explicit synthetic-twin requirements for:

- matched-control generation
- overlapping-window geometry
- all-overlap crosswalk
- barcode donor identity
- SCENIC+ RNG/thread/shard reproducibility
- G2 semantics as unresolved

## 19.4 Design a prospective G2 specification process

Do not choose a threshold from existing synthetic outcomes.

Instead:

1. state biological purpose of G2
2. decide whether it is a significance/null gate, equivalence gate, or descriptive safeguard
3. if magnitude/equivalence is selected, define margin from an external/technical rationale independent of V2 outcomes
4. precommit
5. qualify on fresh synthetic worlds
6. only then consider Stage-4 authorization

## 19.5 Continue full synthetic ecosystem implementation

After V71 CI is green:

- coupled hidden-truth generator
- raw-like adapters
- checkpoint twins
- CI-scale full-pipeline run
- stress-scale run
- full-scale twin last

---

# 20. Current project scientific posture in plain language

The project has built a strong data and audit substrate, but it is **not yet at real multimodal training**.

The central remaining scientific problem is not “can we compute RNA–ATAC correlation?” It is:

**Can richer regulatory evidence define a teacher state that contains real biological information the RNA student can recover, while keeping unrecoverable/private information out of the student and distinguishing biology from technical or cross-modal shortcuts?**

Stage 4 is one primary qualification channel.

SCENIC+ is another independent regulatory-architecture channel.

Perturbation, spatial, paired multiome and separate-nucleus evidence are other channels.

They should meet at **program-level recoverability**, not by pooling cells.

The full synthetic twin is the engineering/scientific dress rehearsal that should prove the entire architecture can survive:

- raw ETL
- source-specific missingness
- selection/matching
- route disagreement
- technical confounding
- hidden confounding
- private information
- checkpoint failure
- provenance errors
- axis/order bugs
- scale

before real multimodal training is opened.

---

# 21. Chat-exclusive evidence preserved for successor audit

Under:

`docs/agent/archive/chat_runtime_20261001/`

there are six numbered verbatim uploads:

- `CHAT_UPLOAD_01_PASTED_TEXT.txt`
- `CHAT_UPLOAD_02_PASTED_TEXT.txt`
- `CHAT_UPLOAD_03_PASTED_TEXT.txt`
- `CHAT_UPLOAD_04_PASTED_MARKDOWN.md`
- `CHAT_UPLOAD_05_PASTED_MARKDOWN.md`
- `CHAT_UPLOAD_06_PASTED_MARKDOWN.md`

These preserve Macha's raw reports, including statements later retracted or qualified.

Use them for chronology, not as the canonical current state.

Project-backed large files are separately identified in:

`CHAT_RUNTIME_BINARY_CUSTODY_MANIFEST_20261001.json`

They are not duplicated into Git history.

---

# 22. Success criteria for the next Sol agent

A good takeover should result in:

1. Current Macha heads independently audited.
2. No stale/superseded Stage-4 claim repeated without qualification.
3. V71 tests actually run and wired into CI.
4. Synthetic twin updated for S99, S102, overlapping windows, barcode identity, and SCENIC+ reproducibility.
5. G2 specification gap treated as open governance/science, not silently patched.
6. SCENIC+ scaling/build receipts audited before full 10,249-motif execution is trusted.
7. Route-B region-universe construction audited before network inference.
8. Real Stage 4 still closed until G2 semantics and remaining authorization requirements are prospectively resolved.
9. No protected outcome leakage.
10. No synthetic software qualification promoted to biology.

---

# 23. One-line takeover command

**Re-query Macha's two live branches, audit everything pushed after `759bf0f2` and `f8dc4935`, then close the V71 CI gap and extend the synthetic full-project twin with the post-S99/S102 and SCENIC+ reproducibility requirements—without authorizing real Stage 4 or protected data.**
