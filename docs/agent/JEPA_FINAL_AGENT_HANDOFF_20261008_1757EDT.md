# JEPA final new-agent handoff — 2026-10-08 17:57 EDT

## Status and scope

This is a **non-authorizing, cold-start takeover checkpoint** for the next agent. It supersedes the earlier same-day conversational checkpoint as the first document a new agent should read, but it does **not** delete or replace the older custody documents.

Read this together with:

- `docs/agent/JEPA_COMPLETE_TAKEOVER_20261008.md`
- `docs/agent/JEPA_NEW_AGENT_HANDOFF_20261008_1518EDT.md`
- `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`
- `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`
- `custody/takeover_20261008/MANIFEST.json`
- `custody/takeover_20261008/PR230_PRIOR_HANDOFF.md`
- `custody/takeover_20261008/s174_working_snapshot/`

Immediately before this file was written, PR #237 was re-read and was open, draft, mergeable at head:

`438640ee91de310768d02b5f5e342696e166445e`

PR #237 branch:

`handoff/jepa-20261008-complete-runtime-s174-takeover`

Base:

`impl/v77-bounded-synthetic-mutation-20261007`

Base SHA:

`8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

This checkpoint is documentation-only. It does not modify runtime code, tests, workflows, scientific outputs, or large binary data.

---

# 1. Executive takeover state

There are **three distinct lanes**. Do not collapse them.

## A. Runtime/provenance lane

The project has moved beyond ZERO_UPDATE in one narrow, preregistered, synthetic-only rehearsal. Exactly one guarded optimizer update was completed, EMA advanced only after proven optimizer completion, typed continuation was persisted, and exact fresh-module restore was verified.

This is an engineering qualification result only. It is **not real-data training authority**.

## B. Synthetic-science / S174 lane

The corrected 14,417-address replay is reproducible and materially changes the earlier interpretation. No synthetic mechanism is qualified. The most important mechanistic defect now exposed is that the current hidden synthetic substate is independent of annotated broad cell class, while the real data contain substantial broad-class structure. The next move should be a prospectively frozen biological-mechanism redesign, not further free parameter sweeping.

## C. Target-discovery / objective lane

Historical target work is more mature than “pick a tensor.” Recovered handoff history says the target work had pivoted toward **relational objective qualification** after TD56/TD57B, with TD59 reported as the latest success and TD60 prospectively frozen. However, the exact file/SHA producer-panel-pair chain for TD34→TD60 and the ATAC/SCENIC+/NIH-CARD evidence graph were **not fully reconstructed in this chat**.

That unresolved evidence reconstruction is now one of the highest-priority scientific audit tasks. Do not freeze a target from shorthand stage labels or prose summaries.

---

# 2. Canonical runtime lineage

Known runtime/provenance chain:

- PR #224 runtime head: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- PR #226 shared qualification interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- PR #228 joined V77 ZERO_UPDATE: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- PR #232 physical provenance successor: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- PR #233 2K operator-smoke CI successor: `c919d957de79a3866fdaeab3ae2ae5a0891d4859`
- PR #234 pre-rehearsal freeze: historical recorded head `0ec385889630b3a7f02caa489d95d988304ad9dd`
- PR #235 preregistered bounded-mutation design: `71a3d6d84a36e1812ffd776153d48948bd8b945c`
- PR #236 audit-record head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`
- PR #237 takeover branch: this handoff branch

Do not infer authority from branch order alone. The bounded rehearsal contract and its audit record are the controlling documents for the one-step mutation proof.

---

# 3. Bounded synthetic mutation rehearsal — exact proven state

Contract:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

Contract head:

`71a3d6d84a36e1812ffd776153d48948bd8b945c`

Final implementation/test head used for the audited execution:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Successful workflow evidence:

- `v77-qualified-zero-update-join` run `37712331165` — SUCCESS
- job `113100879103`
- focused suite: **51 passed in 9.87s**
- independent successful rehearsal custody rerun: **1 passed in 3.41s**
- `shared-qualification-interface-v1` run `37712331253` — SUCCESS

Final verdict:

`PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION`

Observed state transition:

- optimizer step `0 -> 1`
- teacher presentations `0 -> 2`
- online/student state changed
- predictor state changed
- teacher state changed only through permitted post-completion EMA
- optimizer state changed
- typed continuation persisted
- exact fresh-module restore verified
- `execution_authorized=false`
- `training_authorized=false`
- `production_promotable=false`

Test-only EMA half-life:

`1000 successful base-cell presentations`

This is **not** production EMA authority.

### Final custody digests

- adapter source: `15092b16d1a71241e8e5883ff228b5d89595073d79e8df70adaf63641103c4d6`
- joined runtime source: `5a820949a9fc9264461a43488847ce89ad5ef17b5125561aa577bfbfd8148f33`
- mutation runtime source: `f1bb0f5615206ffa4239aa7e09d95f8d82ced4e8920d83c85867ee62d3c62857`
- batch scientific identity: `213a07a136020b16ea62e3754bfd2f4e5789317d2d1c68781ce2bf7f85cc39d5`
- physical bindings: `24110c202d85945d865fb4c43f5bf278de1b6d15c8565c3df466ab71eadde8fb`
- q-safety proof: `7cd9fac2e222ce650bc808dc8a13cdfc8c9367f5191baf2073afbbf3f94f446f`
- EMA configuration: `V5_PRESENTATION_EMA:6d0e321b897246c1d1e32209c2d59c85c071a1862b0dcdf856542a6237d1eb20`
- completed guard receipt: `452da0f0d79dad7cad2625fff0496b3dd87b763928fdfd10d2b421dd95093293`
- EMA completion proof: `e50f3829bcbf50d684e5ee526559c2222ab1b7d8f7fd8a3633097de2a04965ef`
- typed continuation artifact: `8db05a5fb0ec0f996c949b384af1359d0ddd9c38bc85eb5267ddb8bef5b7c550`
- checkpoint before: `7e6e8c275ab43e518b47f59d162a72ee10e27347db027d61bc7607d4533d75f7`
- checkpoint after/restored: `e5611c0d92c5dd8835836d9c838dd32344cb133647d63953e5a3a428fc7d2222`
- online after/restored: `effeca5e904029bea6847df60fd2e88d671d0b7c86918965a7f4b409e56e9a20`
- predictor after/restored: `b51d3d4b3feb23e340c1d3cfe78408708211ce736ede0a36c47fc12ddab225f8`
- teacher after/restored: `3478c6be6cef2a28413c197fcf84baad06180f8320df9828a43e2df231cb0b48`
- optimizer after/restored: `e723a7ab311933b3da66834a86f25fac495b9ca41e1036954d5f6b0cda541700`

---

# 4. Runtime audit history completed in this chat

The implementation was not rubber-stamped.

Initial pre-audit implementation head:

`c59db70046c5dcc7c6c8be6e30bebb745604cad5`

The audit found four material defects:

1. a fresh module object existed, but post-update checkpoint state was not actually restored into it and exact equality was not proved;
2. failed mutation attempts could disappear without a durable failure receipt;
3. wrong-runtime/wrong-values/q-safety-replay failures could leave no durable custody marker;
4. the same rehearsal identity could be executed again through a different persistence path.

RED-test commit:

`f0de464fcf921c14a96ef75df806075cc5b69da2`

Expected-failure CI:

`37711581663`

Result:

- 45 passed
- 5 failed

The five failures exactly exposed the missing contract behavior.

Minimal repair commit:

`6f9f51704431825c4d95649944c7613a77c4dcf6`

Primary implementation file:

`src/sea_ad_jepa/qualification/v77_bounded_mutation.py`

Repairs:

- stable `rehearsal_run_receipt_path(...)` keyed by `experiment_run_id`;
- reserve run identity before mutation;
- durable failure verdict `FAIL__NO_COMPLETED_MUTATION_CONTINUATION`;
- completed/failed run identity cannot be reused under another output path;
- partial typed continuation deleted on failure;
- actual `restore_reference_checkpoint(...)` into fresh modules;
- exact restored checkpoint/online/predictor/teacher/optimizer digests compared with post-step state;
- resumed EMA authority issued from restored modules and loaded typed checkpoint.

No update mathematics or model architecture changed in that repair.

CI after repair:

`37712004919` — SUCCESS, **50 passed**.

A final direct bounded-path adversary for missing physical binding proof was then added at:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Final focused result: **51 passed**.

### Mandatory adversary crosswalk

1. missing physical proof — direct bounded rehearsal test
2. wrong consumed values — direct bounded rehearsal test
3. wrong adapter digest — direct bounded rehearsal test
4. wrong runtime digest — direct bounded rehearsal test
5. q-safety proof replay from another batch — direct bounded rehearsal test
6. nonfinite/GradScaler skip — canonical guard regression, no completion/no EMA
7. EMA before proven optimizer completion — canonical guard regression rejects it
8. second optimizer step under same rehearsal identity — rejected even with different output filename
9. weak/V1 base proof cannot promote — shared-interface V2 regression
10. EMA configuration drift on restart — typed continuation regression
11. exact child reload — fresh modules restored and all state digests compared
12. authorization flags remain false

Any later attempt to enable real-data training or a larger mutation regime is a **new authority problem** and requires a new preregistered contract and fresh adversarial qualification.

---

# 5. PR #232 physical payload/provenance audit

PR #232 head:

`d3430ce6c0e878272e92b61e01822334e088d8c8`

Important change:

`PhysicalRowValueBindingV2` includes `authenticated_payload_sha256`, and joined ZERO_UPDATE requires `physical_bindings` at both execution boundaries.

Checks bind:

- exact batch coverage;
- physical row identity;
- observation/donor identity;
- feature digest;
- actual executed student-expression values;
- aggregate physical-binding digest.

CI:

`37693805825` — **29 passed**.

Critical qualification: this proves fail-closed enforcement of a **supplied** physical proof. It does not independently prove real-byte authentication of a protected production dataset.

---

# 6. PR #233 2K observation-operator smoke audit

Historical regression:

- stress-twin 2K: 42/42 operators represented, minimum 1
- calibration-closure 2K: 36/42, minimum 0
- calibration-closure 10K: 41/42
- >=100K: 42/42

Root cause: removal of the historical zero-quota rescue. This matters because the 2K smoke is the gate before larger execution.

PR #233 head:

`c919d957de79a3866fdaeab3ae2ae5a0891d4859`

CI:

- run `37695987219`
- job `113047706088`
- **128 passed**
- actual 2K regression executes and proves 42/42 operators with minimum >=1

No scientific sampler change was introduced by the CI custody repair itself.

---

# 7. Corrected S174 synthetic-science state

Working source branch:

`claude/s174-train-cache-rebuild-20261007`

Current preserved source head:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

Corrected replay commit:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

CI:

`37693603160` — SUCCESS, **146 passed, zero skipped** in the recorded replay custody.

PR #237 preserves the S174 working/audit snapshot under:

`custody/takeover_20261008/s174_working_snapshot/`

Snapshot tree:

`d52f665aeb393c368102c5b71afc59f03b10225f`

Use that snapshot for exact S174 preregistrations, scripts, tests, corrected replay outputs, downstream re-score records, and CI custody. Do not revive the old divergent runtime lineage wholesale.

## Correct replay protocol

Each arm was first rerun on the old universe and matched its committed output exactly. Only the universe/output location changed for corrected replay; seed, arm, preprocessing, scoring, and tuning did not. V1 receipts were superseded and were not replayed.

## Current statistical ruling

Until S159 is resolved:

- pooled p05–p95 envelopes are **not qualification thresholds**;
- corrected real points are descriptive references;
- donor bootstrap is an uncertainty diagnostic;
- no binary pass/fail threshold has been selected;
- no post-outcome recentering is authorized.

## Corrected real references

From `docs/agent/S174_SYNTHETIC_REPLAY.md` in S174 custody:

- expression median |r|: `0.0562`; interval `[0.0569,0.0591]`
- expression fraction |r| > 0.3: `0.0242`; `[0.0233,0.026]`
- expression top-10 variance fraction: `0.262`; `[0.2613,0.2679]`
- detection median |r|: `0.1946`; `[0.1889,0.1965]`
- detection fraction |r| > 0.3: `0.1348`; `[0.1242,0.1513]`
- detection mean degree: `404.3647`; `[372.4921,453.687]`
- detection transitivity: `0.6672`; `[0.6454,0.667]`
- largest community fraction: `0.1367`; `[0.127,0.2128]`
- T5 class-separation within/pooled: `0.7435`
- abundance max/median nonzero: `2273.2075`; `[2183.824,2382.7249]`
- top1% count share: `0.2741`; `[0.2716,0.2767]`
- median detected per cell: `4495.5`

Two real points lie just outside their own donor-bootstrap intervals: expression median |r| and detection transitivity. That is one reason the bootstrap interval cannot be treated as a pass/fail qualification envelope.

## Main mechanistic findings

- Poisson counting still collapses detection topology: transitivity `0.7436 -> 0.3377`, mean degree `845.2427 -> 7.342`.
- The 12-fold / DR2 arm can move detection density/degree toward real, but remains wrong in multiple independent ways: transitivity about 1.17× real, abundance about 10.4× real, depth about 0.35× real.
- All replayed arms underproduce detection median |r|.
- All remain too concentrated in abundance/top1% share.
- All are too shallow in depth.
- T5 class-separation values are all too high relative to corrected real T5 `0.7435`.
- Current synthetic hidden substates are drawn independently of annotated broad cell class by construction.

Conclusion: **no synthetic mechanism is qualified**. The corrected replay reopened the biological-substate / observer / capture design problem.

---

# 8. Biological redesign discussed in this chat — current design direction only

The latest scientific design discussion in this chat proposed replacing the effective structure:

`cell class + class-independent hidden substate -> observation -> counts`

with the more biologically defensible hierarchy:

`broad cell class -> class-shared biological programs -> within-class continuous/substate biology -> measurement operator -> counts`

The key principle is that broad class should influence a **shared gene program**, not merely be stored as a label or implemented as a trivial global multiplicative offset.

Three prospective mechanism families were proposed for a first tournament:

1. class-shared program only;
2. **class-shared program + within-class continuous state** — recommended default;
3. class-shared program + the existing substate mechanism nested within class.

The observation/counting mechanism should initially be held fixed to isolate the biological mechanism. T5 must not become a tuning target by itself. Evaluation should remain multidimensional: expression dependence, detection dependence/topology, class separation, abundance concentration, depth, and other already-preregistered diagnostics.

### Important process status

This design direction was discussed but **not implemented**. Under the design discipline used in this project, the next agent should first write a frozen scientific specification, self-audit it, and obtain user approval before implementation.

A good specification should include preregistered negative controls such as:

- shuffled broad-class labels while preserving marginal class counts;
- class-independent/rotated shared programs;
- current class-blind baseline;
- frozen program basis and frozen evaluation metrics before any outcomes are seen.

A safer two-stage plan is:

- **Stage B1:** biological-hierarchy tournament with observer/capture fixed;
- **Stage B2:** only if B1 meaningfully broadens the biological span, cross the best biological mechanisms with observer/capture alternatives.

Do not tune biology and observation simultaneously in the first experiment.

SCENIC+/regulatory structure may be useful as a frozen/exogenous program basis, but only after its provenance and exposure are reconstructed. TRAIN-only RNA class contrasts are another possible basis. ATAC should not be over-weighted simply because it exists.

---

# 9. Target-discovery audit still unresolved — TD34 -> TD60

This chat recovered that:

- the target lane had advanced beyond “find a target tensor”;
- historical work reportedly pivoted to **relational objective qualification** after TD56/TD57B;
- TD59 was reported as the latest success in prior handoff history;
- TD60 was reported as prospectively frozen.

But the exact file-level chain for:

`TD34`, `TD41`, `TD43`, `TD56`, `TD57`, `TD57B`, `TD59`, `TD60`

was **not fully reconstructed** here.

The next agent must reconstruct one evidence table with one row per stage containing at minimum:

- stage identifier;
- exact producer script path;
- producer script SHA-256 or Git blob/commit identity;
- exact input manifest(s);
- exact panel/pair manifest(s);
- exact output/result artifact(s);
- output hashes;
- Git commit/branch/PR;
- source dataset(s);
- train/development/test exposure classification;
- whether the result is reproducible today;
- whether downstream decisions depended on it;
- whether any referenced source script is missing and must be recovered from history/custody.

Search terms:

`TD34`, `TD41`, `TD43`, `TD56`, `TD57`, `TD57B`, `TD59`, `TD60`, `target discovery`, `relational objective`, `pair manifest`, `panel manifest`, `producer manifest`.

Search old custody/takeover branches and archived chat handoffs, not only current top-level source. Likely locations include:

- `docs/agent/archive/`
- `custody/`
- historical handoff branches
- archived chat-runtime manifests
- old ZIP handoffs

Specific user-requested recovery targets:

1. old **Sept 7 target-discovery handoff ZIP** or anything containing the original TD34 producer/panel manifests;
2. authenticated **Nott ATAC / liftover inputs** or V64 execution artifacts;
3. historical **TD41/TD43 panel or pair manifests**;
4. original **NIH-CARD Stage 3/4 execution outputs**, if they exist locally;
5. old scripts whose hashes are referenced by audits but whose source is missing from GitHub.

Do not freeze a target until this evidence graph is exact enough that another agent can reproduce the objective history without relying on “the previous agent said so.”

---

# 10. ATAC / SCENIC+ / Nott / Morabito / NIH-CARD evidence rules

Do not collapse these into one generic external-validation bucket.

## Nott / liftover

Historical V64 work had explicit authentication/custody for Nott ATAC and hg19<->hg38 liftover inputs. Recover:

- exact source files;
- source URLs if preserved;
- byte counts and checksums;
- coordinate build;
- chain-file direction actually used;
- derived execution receipts;
- script identity for any coordinate transformation.

## Morabito

Morabito ATAC had prior exposure through coverage analysis. That does **not** make the dataset useless, but it means “pristine,” “never-seen,” or equivalent independence claims are not allowed unless a finer-grained exposure reconstruction supports them.

## SCENIC+

SCENIC+/regulatory structure must be included in the objective audit. Recover producer/version/input provenance and exposure. It may be useful as an exogenous frozen biological-program basis, but not as a post hoc rescue after protected outcomes are inspected.

## NIH-CARD

Recover the original Stage 3/4 execution artifacts if present, plus producing scripts and exact input hashes. Do not substitute a later prose summary for the original result package.

## Evidence matrix deliverable

Produce one matrix with rows = candidate target/objective claims and columns including:

- RNA evidence;
- SCENIC+ evidence;
- ATAC evidence;
- Nott evidence;
- Morabito exposure status;
- NIH-CARD evidence;
- historical controls;
- train/development/test exposure;
- independent versus previously exposed status;
- reproducibility status.

---

# 11. Chat-local files physically available in this environment

The following ten assets were freshly hashed in the earlier same-day handoff and are physically present under `/mnt/data` in this ChatGPT environment.

| file | bytes | SHA-256 |
|---|---:|---|
| `WSL execution issue.txt` | 14,576 | `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv` | 437 | `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` | 303,979,881 | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` | 303,979,880 | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` |
| `checkpoints.zip` | 71,356,460 | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` |
| `expression.zip` | 3,599,456 | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` |
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | 1,531,109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` |
| `t1_checkpoint_u0200.zip` | 233,729,581 | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` |
| `Status and Repair Plan.txt` | 5,233 | `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56` |

### Split 41K expression archive integrity

Concatenate:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`

then:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`

Expected complete archive:

- bytes: `607,959,761`
- SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Contained NPZ path:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz`

### Useful archive inventories

`checkpoints.zip` contains:

- `t1_checkpoint_u0100.pt`
- `t1_checkpoint_u0200.pt`

`expression.zip` contains:

- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json`
- per-operator sample metadata for operators `op00` through `op41`

The calibration bundle contains historical code/contracts that may be essential to source reconstruction. Inspect it before assuming a referenced historical script is lost.

Do **not** commit these multi-hundred-megabyte raw archives into ordinary Git history merely to make the handoff self-contained. Existing custody intentionally uses cryptographic hashes, inventories, and recovery paths instead.

---

# 12. Historical local note: dataset-first V5 closure

`/mnt/data/Status and Repair Plan.txt` records an older V5 dataset-first production-closure effort on:

`planning/v5-dataset-first-production-closure-20260912`

Treat it as historical evidence, not current authority. It may help reconstruct why particular dimensions, execution gates, and production-closure tasks existed, but it cannot supersede current runtime or scientific contracts.

`/mnt/data/WSL execution issue.txt` preserves local execution context and may explain historical environment failures. It is not itself scientific evidence.

---

# 13. Hard boundaries that remain in force

Nothing in this handoff authorizes:

- real-data training;
- more optimizer updates beyond a newly preregistered successor;
- protected TEST execution;
- treating Morabito as pristine/unseen;
- 500K execution;
- Stage 4 execution;
- production EMA selection;
- target freeze;
- representation freeze;
- threshold selection from corrected S174 outcomes;
- multimodal training;
- post hoc recentering/tuning of S174 thresholds;
- interpreting the test-only 1000-presentation EMA as a production hyperparameter.

The project has proved that one synthetic optimizer update can be executed through the guarded runtime. That does not answer whether the target/objective or synthetic qualification environment is scientifically ready.

---

# 14. Ordered next work for the new agent

## Task 0 — cold-start verification

Before doing science, verify:

- PR #237 current head and diff;
- PR #236 execution/audit head;
- workflow run `37712331165`;
- S174 source head `750cb83...` and replay run `37693603160`;
- local custody hashes if those files are still mounted;
- no parallel agent has moved the relevant branches.

## Task 1 — reconstruct TD34 -> TD60 evidence graph

This is the highest-priority unresolved audit task.

Deliverables:

1. machine-readable stage table;
2. human audit note;
3. explicit list of missing artifacts/scripts;
4. exposure/independence classification;
5. statement of which historical conclusions reproduce today.

No target implementation yet.

## Task 2 — recover multimodal/external provenance

Recover exact Nott, liftover, SCENIC+, Morabito-exposure, and NIH-CARD provenance and original artifacts. Tie every conclusion back to files, producer scripts, hashes, and commits.

## Task 3 — adjudicate current target/objective state

Only after Tasks 1–2, state whether the historical relational objective survives reconstruction. Distinguish:

- reproducible evidence;
- exposed evidence;
- independent evidence;
- missing evidence;
- historical inference only.

If the objective cannot be reconstructed, do not silently recreate a new one and call it the same target.

## Task 4 — write the frozen S174 biological-redesign specification

Use the current design direction:

`broad class -> class-shared biological programs -> within-class biology -> fixed observer -> counts`

Define:

- latent variables and hierarchy;
- allowed source of program basis;
- frozen arm definitions;
- negative controls;
- fixed observer/capture path;
- exact metrics;
- non-selection rules;
- stopping rule;
- artifact/receipt schema;
- RED adversarial tests;
- explicit statement that current donor-bootstrap intervals are diagnostic only.

Then self-audit the spec and obtain user approval before implementation.

## Task 5 — only after approval, implement S174 redesign RED -> GREEN

Implementation should be minimal, preregistered, and test-first. Preserve the current corrected real references and evaluation code unless the written spec prospectively changes them for a justified reason.

## Task 6 — runtime work only if a new scientific decision requires it

Further runtime mutation is **not** the default next step. Do not expand from one synthetic step merely because the guard path is now green.

---

# 15. Takeover competency checklist

A new agent is not fully assimilated until it can answer, with exact files/receipts rather than memory:

1. What exactly did the one-step mutation rehearsal prove, and what did it not prove?
2. What RED failures were found before the final GREEN result?
3. Which tests prevent replay, missing physical proof, EMA-before-completion, nonfinite step, restart drift, and weak-proof promotion?
4. What exact S174 universe/replay state is current?
5. Why are donor-bootstrap intervals diagnostics rather than qualification thresholds?
6. What mechanistic defect did corrected S174 expose?
7. Where are the exact 41K expression, calibration, checkpoint, NPZ, and local note assets, and what are their hashes?
8. What are the exact TD34->TD60 producers, manifests, results, and commits?
9. How were Nott, SCENIC+, Morabito, and NIH-CARD exposed/authenticated?
10. Which target/objective evidence is reproducible versus historical-only?
11. Why is the proposed class-shared biological-program redesign not yet implementation-authorized?
12. Why does none of this authorize real-data training, TEST, target freeze, or production EMA selection?

If an answer is only “the previous agent said so,” the takeover is incomplete.

---

# 16. Bottom line

The runtime lane is no longer blocked on whether a single optimizer step can be made safely: that narrow synthetic engineering question has been answered and audited fail-closed.

The dominant blockers are now scientific and evidentiary:

1. **What biological relationship should the JEPA predict?** The TD34→TD60 and multimodal evidence chain must be reconstructed before a target/objective freeze.
2. **Does the synthetic qualification world contain the right hierarchy of biology?** Corrected S174 says the current class-independent hidden-substate mechanism does not reproduce important real dependence. The next synthetic design should introduce class-shared biological programs prospectively and isolate that change before revisiting observer/capture mechanisms.

Solve those before expanding training.