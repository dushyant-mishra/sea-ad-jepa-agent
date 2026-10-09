# JEPA new-agent takeover checkpoint — 2026-10-08 15:18 EDT

## Status of this document

This is a **non-authorizing, cold-start handoff** for the next agent. It records the work and audits completed in the current ChatGPT custody lane, the current GitHub execution/science state, the exact local assets available in this environment, and the ordered next work.

It intentionally **does not authorize** real-data training, protected-dataset execution, target freeze, representation freeze, production EMA selection, TEST/Morabito/500K/Stage 4, or any other production/scientific promotion. It also does not silently convert historical results into current authority.

This checkpoint was added to PR #237 as a documentation-only successor. Before this file was written, PR #237 was re-read at head:

`ef8612f7ece7bd6af629d25146bbfdc6f318ae77`

PR #237 is based directly on the audited PR #236 head:

`8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

The existing takeover document remains important:

`docs/agent/JEPA_COMPLETE_TAKEOVER_20261008.md`

Do not replace it with this file; use the two together. This file adds the current-chat audit record, local custody inventory, target-discovery recovery work, and an explicit ordered continuation plan.

---

# 1. Executive state

There are now three conceptually separate lanes. Keep them separate.

1. **Runtime/provenance lane:** the project has progressed beyond ZERO_UPDATE and has one audited, preregistered, synthetic-only guarded optimizer update with post-step EMA and deterministic fresh-module restore. This lane is GREEN for exactly the bounded rehearsal that was preregistered. It is **not real-data training authority**.
2. **Synthetic-science/S174 lane:** the corrected 14,417-address replay is reproducible and materially changes the earlier interpretation. No synthetic mechanism is qualified. The current generator fails to reproduce important biological dependence, especially the broad cell-class contribution. The next move is prospective scientific redesign, not more unstructured parameter sweeping.
3. **Target-discovery lane:** historical target work is substantially more mature than “find a target tensor.” The recovered handoff history says it had already pivoted toward **relational objective qualification** after TD56/TD57B, with TD59 reported as the latest success and TD60 prospectively frozen. However, this chat did **not finish exact file-level reconstruction of TD34/TD41/TD43/TD56/TD57B/TD59/TD60 plus the ATAC/SCENIC+/NIH-CARD evidence chain**. That is now a first-class takeover task. Do not freeze a target until that exact evidence graph is recovered and reconciled.

The immediate next agent should therefore **not start training** and should **not jump directly into a new target implementation**. First recover and verify the target-discovery evidence graph; in parallel, turn the already discussed S174 biological redesign into a frozen written scientific specification before implementation.

---

# 2. Canonical runtime lineage and current authority

Known canonical chain:

- PR #224 runtime head: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- PR #226 shared qualification interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- PR #228 joined V77 ZERO_UPDATE: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- PR #232 physical provenance successor: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- PR #233 2K operator-smoke CI successor: `c919d957de79a3866fdaeab3ae2ae5a0891d4859`
- PR #234 pre-rehearsal freeze: initially `0ec385889630b3a7f02caa489d95d988304ad9dd`
- PR #235 preregistered bounded-mutation design: `71a3d6d84a36e1812ffd776153d48948bd8b945c`
- PR #236 audit-record head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`
- PR #237 takeover branch head before this checkpoint: `ef8612f7ece7bd6af629d25146bbfdc6f318ae77`

The bounded synthetic rehearsal contract is:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

Contract head:

`71a3d6d84a36e1812ffd776153d48948bd8b945c`

The durable post-execution audit is:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`

Audit-record commit:

`8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

## Exactly what is proven

Final implementation/test head:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Successful workflow:

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
- online/student parameters changed
- predictor parameters changed
- teacher parameters changed only through the permitted post-completion EMA route
- optimizer state changed
- typed continuation persisted
- checkpoint restored into fresh modules and exact restored state was verified
- `execution_authorized=false`
- `training_authorized=false`
- `production_promotable=false`

Test-only EMA half-life is **1000 successful base-cell presentations**. This is not a production EMA choice.

## Exact final custody digests

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

# 3. Runtime audit performed in this chat: RED -> GREEN, not rubber-stamped GREEN

The earlier implementation at:

`c59db70046c5dcc7c6c8be6e30bebb745604cad5`

looked promising but did not satisfy the full preregistered contract. The audit found four material classes of defect:

1. a “fresh module” was instantiated, but the post-update checkpoint state was not actually restored into it and state equality was not proved;
2. failed mutation attempts could disappear without a durable failure receipt;
3. wrong-runtime/wrong-values/q-safety-replay failures did not necessarily leave a durable custody marker;
4. the same rehearsal identity could be executed again under a different output path.

RED tests were committed at:

`f0de464fcf921c14a96ef75df806075cc5b69da2`

Expected-failure CI:

`37711581663`

Result:

- 45 passed
- 5 failed

The five failures mapped exactly to the missing contract behavior above.

Minimal repair commit:

`6f9f51704431825c4d95649944c7613a77c4dcf6`

Primary implementation file:

`src/sea_ad_jepa/qualification/v77_bounded_mutation.py`

Repairs included:

- stable `rehearsal_run_receipt_path(...)` based on `experiment_run_id`;
- reservation of the run identity before mutation;
- durable failed-attempt verdict `FAIL__NO_COMPLETED_MUTATION_CONTINUATION`;
- rejection of completed or failed identity reuse even under a different persistence path;
- deletion of partial typed continuation after failure;
- actual `restore_reference_checkpoint(...)` into fresh modules;
- exact restored checkpoint/online/predictor/teacher/optimizer digest comparisons;
- resumed EMA authority issued from the restored modules and loaded typed checkpoint.

No update mathematics or model architecture changed in this repair.

CI after repair:

`37712004919` — SUCCESS, 50 passed.

A final direct adversary for missing physical binding proof at the bounded rehearsal was then added at:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Final focused result: **51 passed**.

## Mandatory adversary crosswalk now covered

1. missing physical proof — direct bounded rehearsal test
2. wrong consumed values — direct bounded rehearsal test
3. wrong adapter digest — direct bounded rehearsal test
4. wrong runtime digest — direct bounded rehearsal test
5. q-safety proof replay from another batch — direct bounded rehearsal test
6. nonfinite/GradScaler skip — canonical guard regression, no completion/no EMA
7. EMA before proven optimizer completion — canonical guard regression rejects it
8. second optimizer step under same rehearsal identity — run-identity rejection, including different output filename
9. weak/V1 base proof cannot promote — shared-interface V2 regression
10. EMA configuration drift on restart — typed continuation regression
11. exact child reload — fresh modules restored and all state digests compared
12. authorization flags remain false

A successor must preserve these tests and should treat any later training-enabling change as a **new authority problem**, not as an extrapolation from this one-step synthetic proof.

---

# 4. PR #232 physical payload/provenance repair

PR #232 head:

`d3430ce6c0e878272e92b61e01822334e088d8c8`

Key change: `PhysicalRowValueBindingV2` includes `authenticated_payload_sha256` and the joined ZERO_UPDATE path requires `physical_bindings` at both execution boundaries.

Checks bind:

- exact batch coverage;
- physical row identity;
- observation/donor identity;
- feature digest;
- the actual executed student-expression values;
- aggregate physical binding digest.

CI:

`37693805825` — **29 passed**.

Critical qualification: this proves fail-closed enforcement of a **supplied** physical proof. It does **not** independently prove real-byte authentication for a protected production dataset. Do not promote it into such a claim.

---

# 5. PR #233 2K operator-smoke regression

Historical regression:

- stress-twin 2K: 42/42 operators represented, minimum 1
- calibration-closure 2K: 36/42 operators, minimum 0
- calibration-closure 10K: 41/42
- >=100K: 42/42

Root cause: removal of the historical zero-quota rescue. This matters because 2K is the smoke scale used before larger execution.

PR #233 head:

`c919d957de79a3866fdaeab3ae2ae5a0891d4859`

CI:

- run `37695987219`
- job `113047706088`
- **128 passed**
- actual 2K regression executes and proves 42/42 operators with minimum >=1

No sampler/scientific-result change was introduced by the CI custody repair itself.

---

# 6. Corrected S174 synthetic-science state

Working source branch:

`claude/s174-train-cache-rebuild-20261007`

Current source/receipt head preserved in takeover custody:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

Corrected replay commit:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

CI:

`37693603160` — SUCCESS, records report **146 passed, zero skipped**.

PR #237 contains a working/audit snapshot under:

`custody/takeover_20261008/s174_working_snapshot/`

Snapshot tree recorded by the earlier takeover work:

`d52f665aeb393c368102c5b71afc59f03b10225f`

Use that snapshot for the exact S174 preregistrations, scripts, tests, corrected replay results, downstream re-score records, and CI custody without reviving the entire divergent historical runtime lineage.

## Corrected replay protocol

Each arm was first rerun on the old universe and matched the committed output exactly. Only the universe/output location was changed for corrected replay; seed, arm, preprocessing, scoring, and tuning were not changed. V1 receipts were superseded and not replayed.

## Statistical ruling

Until S159 is resolved:

- pooled p05-p95 envelopes are **not qualification targets**;
- corrected real points are descriptive references;
- donor bootstrap is an uncertainty diagnostic;
- no binary pass/fail threshold has been selected;
- no recentering should be introduced after seeing these outcomes.

## Corrected real references

From `docs/agent/S174_SYNTHETIC_REPLAY.md` in the S174 custody:

- expression median |r|: `0.0562`; interval `[0.0569, 0.0591]`; point outside its own interval
- expression fraction |r| > 0.3: `0.0242`; `[0.0233, 0.026]`
- expression top-10 variance fraction: `0.262`; `[0.2613, 0.2679]`
- detection median |r|: `0.1946`; `[0.1889, 0.1965]`
- detection fraction |r| > 0.3: `0.1348`; `[0.1242, 0.1513]`
- detection mean degree: `404.3647`; `[372.4921, 453.687]`
- detection transitivity: `0.6672`; `[0.6454, 0.667]`; point just outside its own interval
- largest community fraction: `0.1367`; `[0.127, 0.2128]`
- T5 class-separation within/pooled: `0.7435`
- abundance max/median nonzero: `2273.2075`; `[2183.824, 2382.7249]`
- top-1% count share: `0.2741`; `[0.2716, 0.2767]`
- median detected per cell: `4495.5`

## Main corrected findings

Poisson counting still destroys detection topology in the examined comparison:

- transitivity `0.7436 -> 0.3377`
- mean degree `845.2427 -> 7.342`

The 12-fold/DR2 arm has detection density/degree near the real reference, but:

- transitivity is about 1.17x real;
- abundance is about 10.4x real;
- depth is about 0.35x real.

This is an observation, not a winner declaration.

No replayed arm reproduces the full corrected reference structure. In particular:

- detection median |r| remains too low across arms;
- abundance/top-1% concentration remains too high;
- depth remains too low;
- T5 class separation remains too high.

All replayed-arm T5 values are approximately `1.0166-1.2087` versus real `0.7435`, with reported ratios to real `1.3673-1.6258`.

The major mechanistic audit finding is that the current hidden synthetic substates are drawn independently of broad annotated cell class by construction. Therefore the generator cannot faithfully reproduce the portion of pooled dependence generated by broad cell-class separation. This is a design constraint, **not evidence that the corrected replay is invalid**.

No synthetic mechanism is qualified. Factor/substate/observer/capture mechanisms remain open.

A historical naming quirk remains: runners may call the universe `TRAIN_PREVALENCE05_19569`, while the corrected universe actually contains **14,417 addresses**. Use the receipt path/checksum, not the stale label, as authority.

---

# 7. Next synthetic-science design: discussed but not implementation-authorized

The scientifically preferred next architecture discussed in this chat is:

`broad cell class -> class-shared biological programs -> within-class continuous/substate biology -> measurement operator -> counts`

This replaces the effective historical structure:

`cell class + unrelated substate -> counts`

The important idea is that class should change a **shared gene program**, not simply appear as a label or a global multiplicative offset.

A prospective first tournament should compare at least:

1. class-shared program only;
2. **class-shared + within-class continuous state** — current recommended mechanism;
3. class-shared + current discrete-substate mechanism.

Initially hold the observer/counting mechanism fixed so biological and measurement changes are not confounded. Do not select a mechanism merely because T5 approaches `0.7435`. Score the same corrected multimetric structure: expression dependence, detection dependence/topology, class separation, abundance, concentration, and depth.

Recommended controls include:

- class-blind/current baseline;
- shuffled class labels preserving marginal class counts;
- a shared-program direction not linked to class;
- frozen program bases rather than jointly tuning program basis and strength after outcome inspection.

Potential program bases should be prospectively justified from allowed evidence. Candidate sources include TRAIN-only RNA class contrasts and pre-existing regulatory/SCENIC+ structure. ATAC should only enter if its authentication, coordinate mapping, and scientific role are explicitly recovered and frozen. Do not leak protected benchmark outcomes into program construction.

A sensible staged design is:

- **B1:** biological hierarchy tournament with observation process fixed;
- **B2:** only if B1 improves the biological span, cross the surviving biological mechanisms with observer/capture mechanisms in a preregistered factorial design.

This design is architectural. Per the scientific-design workflow used in this chat, it should be turned into a written frozen specification, self-reviewed, then reviewed/approved before code is written. The prose above is **not code authorization**.

---

# 8. Target-discovery lane: current recovered interpretation and exact unresolved work

This chat had just resumed a full target-discovery audit when the user requested this handoff.

The recovered conceptual status is:

- the target lane had already advanced substantially beyond “find a target tensor”;
- historical work had reportedly pivoted to **relational objective qualification** after TD56/TD57B;
- TD59 was reported in the canonical handoff history as the latest success;
- TD60 was reported as prospectively frozen.

However, the exact file-level chain for **TD34, TD41, TD43, TD56, TD57/TD57B, TD59, TD60** was not fully recovered in this chat before handoff. GitHub connector code search for the literal `TD60` string returned no direct hit on the live takeover branch. That means a new agent must not rely on the shorthand stage names alone.

## Required recovery task

Reconstruct a table with one row per target-discovery stage containing:

- stage ID/name;
- exact branch and commit SHA;
- producer script path and SHA;
- panel/pair/manifest input paths and SHAs;
- train/development/test exposure status;
- exact output/result paths and SHAs;
- scientific question tested;
- result;
- why it passed/failed/superseded;
- whether it is allowed to influence the next target specification.

The target lane should only move after that table is complete.

## Search order

Search repository history and custody for the exact terms:

`TD34`, `TD41`, `TD43`, `TD56`, `TD57`, `TD57B`, `TD59`, `TD60`, `target discovery`, `relational objective`, `pair manifest`, `panel manifest`, `producer manifest`.

Also search old takeover/custody branches and archived chat handoffs, not only current top-level source. Historical artifacts may have been preserved under `docs/agent/archive/`, `custody/`, or older handoff branches even when literal stage names are absent from the current source tree.

The user specifically asked earlier for recovery of:

1. the old **Sept 7 target-discovery handoff ZIP** or anything containing the original TD34 producer/panel manifests;
2. authenticated **Nott ATAC / liftover inputs** or V64 execution artifacts;
3. historical **TD41/TD43 panel or pair manifests**;
4. original **NIH-CARD Stage 3/4 execution outputs** if they exist locally;
5. old scripts whose hashes are referenced by audits but whose source is missing from GitHub.

Those are not optional archaeology. They may determine whether the current objective is reproducible, independent, and scientifically interpretable.

## Target-freeze gate

Do **not** freeze a target merely because a later TD result looks positive. The new agent must answer:

- what exact target object is constructed by the teacher;
- what biological evidence is available to teacher versus student;
- whether the target is query-conditioned rather than an indirect generic-cell predictor;
- what part of the target is directly measured versus predicted;
- whether any evaluation gene/value leaked into target construction or normalization;
- what training/development/protected data influenced objective or panel selection;
- how SCENIC+/ATAC/external evidence changes the biological interpretation;
- which historical negative controls remain binding.

The earlier project audit already identified a fundamental trap: a “rich teacher” fitted on a panel excluding the evaluation panel can still be only another predictor of the proposed target. A proper teacher must construct the state using its assigned biological evidence, not merely outperform another predictor on a separately defined RNA panel.

Target freeze remains **unauthorized** until this evidence graph is exact.

---

# 9. ATAC, SCENIC+, Nott, Morabito, NIH-CARD: how to treat the evidence

Do not collapse these into one generic “external validation” bucket.

The historical project discussion established several important cautions:

- ATAC has sometimes been over-weighted in target discussions; the project also has SCENIC+/regulatory information and extensive RNA/ETL audit structure. Fold all of them into the objective audit.
- Morabito ATAC had prior exposure through coverage analysis. Exposure alone does not make the data useless, but any independence claim must match the actual exposure history. Do not label it pristine/unseen without reconstructing that history.
- Nott ATAC/liftover inputs had explicit authentication/custody work in the V64 lineage. Recover the exact files, source URLs/checksums, coordinate build, chain files, and derived execution receipts before using them.
- NIH-CARD Stage 3/4 outputs, if present, must be recovered from local/custody assets and tied to their producing scripts and exact input hashes. Do not substitute a later summary for the original execution artifact.
- SCENIC+ regulatory structure may be valuable as an exogenous/frozen program basis or as orthogonal biological evidence, but only after reconstructing its provenance and data exposure. It should not be used post hoc to rescue a target after protected outcomes are seen.

A successor should produce one explicit evidence matrix with rows = candidate target/objective claims and columns = RNA, SCENIC+, ATAC, Nott, Morabito exposure status, NIH-CARD, historical controls, and train/development/test exposure.

---

# 10. Chat-local scientific/runtime custody available in this environment

The following ten uploaded assets are physically present under `/mnt/data` in the current ChatGPT environment. They were freshly hashed during this handoff. These hashes are preferable to relying on filename memory.

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

## Split 41K expression archive integrity

Concatenating:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`

then:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`

reproduces the manifest-declared complete archive size and SHA:

- bytes: `607,959,761`
- SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

The reconstructed archive contains:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz`

## Archive inventories

`checkpoints.zip` contains:

- `checkpoints/checkpoint_manifest.json`
- `checkpoints/t1_checkpoint_u0000.pt`
- `checkpoints/t1_checkpoint_u0205.pt`

`t1_checkpoint_u0200.zip` contains:

- `t1_checkpoint_u0010.pt`
- `t1_checkpoint_u0025.pt`
- `t1_checkpoint_u0050.pt`
- `t1_checkpoint_u0100.pt`
- `t1_checkpoint_u0200.pt`

`expression.zip` contains:

- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`
- `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json`
- per-operator sample metadata for operators `op00` through `op41`

The calibration bundle contains, among other things, exact historical code and contracts that may matter for reconstruction:

### calibration docs/results

- `calibration/FOUNDATION_GEOMETRY_REVIEW.md`
- `calibration/FOUNDATION_H_ADDRESS_OPERATOR_DECOMPOSITION.csv`
- `calibration/FOUNDATION_PARTIAL_EVIDENCE_CEILING.csv`
- `calibration/FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv`
- `calibration/FOUNDATION_TEACHER_SHORTCUT_ATLAS.md`
- `calibration/SYNTH_BALANCED_VS_EMPIRICAL_ADJUDICATION.md`
- `calibration/SYNTH_BALANCED_VS_EMPIRICAL_RESULTS.csv`
- `calibration/SYNTH_HETEROGENEOUS_GENERATOR_AUDIT.md`

### historical code

- `code/foundation_measurement_masks.py`
- `code/gene_tokenizer.py`
- `code/ipb_jepa.py`
- `code/masking.py`
- `code/prepare_prod41k_t1_v2_freeze.py`
- `code/production_train_loader.py`
- `code/stage81a3_prod41k_engineering_smoke.py`
- `code/stage81a3_prod41k_teacher_t1.py`

### contracts/provenance

- `contracts/address_measurement_support.csv.gz`
- `contracts/address_namespace.csv`
- `contracts/collision_ledger.csv.gz`
- `contracts/matrix_measurement_support.csv.gz`
- `contracts/production_loader_manifest.json`
- `contracts/unregistered_collisions.csv`

### metadata

- `metadata/FOUNDATION_METADATA_ALL149_CONTEXT.csv`
- `metadata/FOUNDATION_METADATA_ATLAS.json`
- `metadata/FOUNDATION_METADATA_DONOR.csv`
- `metadata/FOUNDATION_METADATA_OPERATOR.csv`
- `metadata/foundation_metadata_rows.sqlite`
- `metadata/FOUNDATION_METADATA_SOURCE.csv`
- `metadata/FOUNDATION_METADATA_SOURCE_X_OPERATOR.csv`

### sampler/splits

- `sampler/HISTORICAL_STAGE81B_TAXONOMY_NEUTRAL_SAMPLER.py`
- `sampler/t1_encoder_fit_inventory.csv`
- `sampler/t1_historical_waterfill_donor_quotas.csv`
- `sampler/T1_SAMPLER_AUTHORITY.md`
- `sampler/t1_training_schedule.csv`
- `sampler/t1_training_schedule_summary.json`
- `splits/foundation_split_registry.csv`
- `splits/reader_donor_split.csv`
- `splits/T1_BIOLOGY_EVALUATION_FREEZE.json`

### support/truth table

- `support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`
- `support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv`
- `support/FOUNDATION_SUPPORT_ATLAS.json`
- `support/FOUNDATION_SUPPORT_ATLAS.md`
- `support/FOUNDATION_SUPPORT_BY_CELL_CLASS.csv`
- `support/FOUNDATION_SUPPORT_BY_OPERATOR.csv`
- `support/FOUNDATION_SUPPORT_BY_SOURCE.csv`
- `truth_table/FOUNDATION_84_CELL_TRUTH_TABLE.npz`
- `truth_table/FOUNDATION_84_CELL_TRUTH_TABLE_METADATA.csv`

The standalone NPZ `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` contains at least one object-typed array. During this handoff it was **not deserialized with `allow_pickle=True`**. Keep that safety boundary until provenance is known; inspect ZIP/NPY headers or recover its producing script first.

## Reproduction commands for custody verification

A successor with these files can verify without trusting this prose:

```bash
cd /mnt/data
sha256sum \
  'WSL execution issue.txt' \
  FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv \
  FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001 \
  FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002 \
  checkpoints.zip \
  FOUNDATION_CALIBRATION_BUNDLE_20260824.zip \
  expression.zip \
  66e64913-959f-4a7c-bbfe-6ff906fb281d.npz \
  t1_checkpoint_u0200.zip \
  'Status and Repair Plan.txt'
cat FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001 \
    FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002 \
  | sha256sum
```

Do not commit the multi-hundred-megabyte raw archives into ordinary Git history merely to make the handoff self-contained. Existing custody deliberately uses exact hashes/inventories for these local bytes.

---

# 11. Historical dataset-first/dimension work preserved in local notes

`Status and Repair Plan.txt` records an older V5 dataset-first production-closure effort on:

`planning/v5-dataset-first-production-closure-20260912`

It is historical evidence, not current authority. It documents important design decisions and missing work, including:

- closing a TRAIN-cache -> FULL104 authority loophole;
- canonical artifact binding;
- an explicit FULL104 -> dimension-authority interface;
- `scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`;
- held-donor D_shared predictability gating;
- prospective D_private and D_obs rules;
- physical FULL104 expression closure requirement;
- missing prospective Monte-Carlo precision authority;
- a permanent blocker ledger `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`.

It explicitly states that the >30 GB / 8,915-block FULL104 store still required physical execution in the appropriate environment and that no numeric D_shared/D_private/D_total/D_obs authority should be inferred merely from having selectors/firewalls.

`WSL execution issue.txt` contains historical design reasoning that technology should be represented as an **observation operator**, not a free biological covariate/dataset embedding. It distinguishes invariance to measurement realization from sensitivity to genuine biological state. These ideas remain relevant to both S174 observer redesign and representation qualification, but the note itself is not current code authority.

---

# 12. Hard prohibitions / things the next agent must not claim

Do not claim or perform any of the following without a new explicit authority chain:

- real-data optimizer updates;
- more than the single preregistered synthetic optimizer update already audited;
- production training;
- Stage A execution on protected/real data;
- TEST execution;
- Morabito “unseen” validation without exposure accounting;
- 500K execution;
- Stage 4;
- production EMA selection;
- target freeze;
- representation freeze;
- threshold selection from the corrected S174 outcomes;
- multimodal training;
- independent real-byte authentication merely because PR #232 enforces a supplied physical proof;
- a qualified synthetic generator;
- a qualified target merely because a historical TD stage was described as successful;
- a valid numeric dimension result merely because historical dimension selectors/firewalls exist.

The older 16,249 EMA candidate remains unselected. The test-only 1000-presentation half-life is not a production choice.

---

# 13. Ordered next-agent plan

## Task 0 — cold-start verification

Before editing anything:

1. fetch PR #237 and record its current head;
2. verify this handoff file and `JEPA_COMPLETE_TAKEOVER_20261008.md` are present;
3. verify PR #236 audit doc and exact implementation head `8dabe9ef...`;
4. confirm no parallel agent has advanced the target-discovery or S174 design branches since this checkpoint;
5. re-hash any local custody bytes actually used.

Do not reset/force-push shared branches.

## Task 1 — reconstruct target-discovery evidence graph

This is the most important unresolved audit task from the current chat.

Recover exact TD34/TD41/TD43/TD56/TD57B/TD59/TD60 producers, manifests, outputs, commits and exposure histories. Recover the old Sept 7 target-discovery handoff ZIP if available. Recover referenced-but-missing script sources by hash from Git history/chat custody if possible.

Deliverable: one machine-readable table plus a human audit note. No target implementation yet.

## Task 2 — recover multimodal/external evidence provenance

Recover:

- Nott ATAC source files/checksums;
- hg19<->hg38 liftover chains/checksums and exact direction used;
- V64 execution artifacts/receipts;
- SCENIC+/regulatory producer/version/input provenance;
- Morabito exposure history;
- NIH-CARD Stage 3/4 original execution outputs and producing scripts.

Deliverable: evidence matrix tied to the target candidates/relational objectives from Task 1.

## Task 3 — decide whether target discovery is reproducible and whether TD60 remains the correct prospective successor

Do not assume the stage numbering implies validity. Re-run or reconstruct only with allowed TRAIN/development inputs and frozen rules. Preserve old negative controls. If original producer code is missing, say so rather than reimplementing from memory and calling it the same stage.

Deliverable: audited “target objective state” with explicit remaining blockers. Target freeze only becomes discussable after this.

## Task 4 — write the S174 biological-redesign specification

Convert Section 7 above into a frozen design document. Specify:

- latent hierarchy;
- permitted data used to define class-shared program bases;
- exact arms;
- randomization/seeds;
- observer held fixed for B1;
- negative controls;
- metrics copied from corrected S174;
- no post-outcome envelope fitting;
- decision rule based on multimetric mechanistic span, not T5 alone;
- what would justify B2 biological x observer factorial work.

Self-review it for leakage/tuning and ask for approval before implementation.

## Task 5 — only after approved spec, implement RED -> GREEN

Write tests before generator changes. Preserve corrected replay as a regression. Do not touch runtime-training authority while doing synthetic-science mechanism work.

## Task 6 — keep runtime lane stopped unless a separately approved authority problem is opened

The bounded mutation rehearsal achieved its scoped purpose. Additional runtime mutation is not the default next step.

---

# 14. Acceptance criteria for a successful takeover

A new agent has genuinely taken over when it can answer, with exact file/SHA evidence rather than chat memory:

1. What exact runtime can mutate, under what authority, and why only once synthetically?
2. What exact failure tests prevent replay/bypass/EMA-before-completion/restart drift?
3. What exact S174 universe and replay outputs are current?
4. Why are the corrected donor-bootstrap intervals diagnostics rather than pass/fail thresholds?
5. What mechanistic defect in the current synthetic generator was exposed?
6. Where are the exact local 41K expression/calibration/checkpoint assets and what are their hashes?
7. What are the exact TD34->TD60 producer/result/manifests and which are still reproducible?
8. How were Nott/SCENIC+/Morabito/NIH-CARD data exposed and authenticated?
9. What is currently allowed to influence a target/objective freeze?
10. Why does none of this yet authorize real-data training or target freeze?

If any answer relies on “the prior agent said so” rather than a receipt, manifest, exact file, or exact commit, takeover is not complete.

---

# 15. Short biological interpretation

The project is no longer blocked by the ability to make one optimizer step safely. That narrow engineering question has been answered synthetically and fail-closed.

The main scientific blockers are now upstream:

- **what biological relationship the JEPA should be asked to predict**, and whether that target/objective survives full reconstruction of the TD34->TD60 and multimodal evidence history; and
- **whether the synthetic qualification environment contains the right hierarchy of biology**, because the corrected S174 work shows that class-independent hidden substates do not reproduce important real dependence.

Those should be solved before expanding training.
