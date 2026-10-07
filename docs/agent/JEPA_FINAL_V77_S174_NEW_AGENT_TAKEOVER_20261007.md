# JEPA final V77 + S174 new-agent takeover — 2026-10-07

Status: **COLD-START TAKEOVER GUIDE — NON-AUTHORIZING**

This document is intended to let a new agent take over without reconstructing the state from chat. It consolidates the canonical runtime/interface lineage, the V77 joined ZERO_UPDATE work, the historical provenance/spillover audits, the Macha/S174 real-TRAIN repair lane, and the exact next actions.

---

## 1. Absolute starting point

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Do **not** start from `main`, old PR #223, or a historical V64/V74/V77 branch and assume it is current authority.

Read in this order:

1. `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md` on `handoff/jepa-20261007-runtime-interface-custody`.
2. `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md` on the same branch.
3. `docs/agent/JEPA_V77_RUNTIME_WIRING_AUDIT_20261007.md` on `handoff/jepa-20261007-v77-wiring-audit`.
4. This document.
5. PR #228 changed files and workflow before touching implementation.
6. Macha/S174 branch `claude/s174-train-cache-rebuild-20261007` and its newest replay/custody docs before citing any old V77 real-data calibration claim.

The custody branch is documentation-only. Do not implement there.

---

## 2. Exact canonical heads and lanes at handoff

### Canonical runtime

PR #224: `Converge canonical V5 runtime safety path`

Accepted runtime checkpoint:

`9d00684e08ba34ef8d7b04e478b9c380cd36d537`

Branch:

`reconcile/canonical-v5-runtime-successor-20261006`

This is the accepted low-level runtime lineage for student/teacher/predictor/optimizer/EMA/checkpoint mechanics.

### Shared qualification interface

PR #226: `Validate shared qualification V2 on canonical V5 runtime`

Head:

`e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`

Branch:

`reconcile/shared-qualification-v2-on-canonical-runtime-20261007`

PR #226 is deliberately stacked on the canonical runtime head and deliberately does **not** transplant the older V5 runtime copies from PR #223.

### Active V77 joined ZERO_UPDATE lane

PR #228: `Join V77 to qualified ZERO_UPDATE runtime`

Branch:

`integrate/v77-qualified-zero-update-20261007`

Head at this handoff:

`6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`

Base:

`e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`

This branch is the active implementation lane for the joined path:

`V77 adapter -> QualificationBatchV1 -> shared qualification V2 -> canonical V5 runtime`

Initially and currently: **ZERO_UPDATE only**.

### Durable wiring audit

Branch:

`handoff/jepa-20261007-v77-wiring-audit`

Latest audit checkpoint before this final handoff branch:

`416dc1cd660bca838d4e834adef7dad65eba1345`

Key file:

`docs/agent/JEPA_V77_RUNTIME_WIRING_AUDIT_20261007.md`

### Final takeover branch

Branch:

`handoff/jepa-20261007-final-v77-s174-takeover`

This branch is documentation-only. Do not turn it into an implementation branch.

### Original Macha/V77 science branch

Branch:

`claude/v77-synthetic-premise-custody-20261005`

Current head visible at handoff:

`976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`

This branch contains the S174 value-verification probe result and the prior V77 scientific custody. The synthetic conclusions remain useful, but its earlier runtime handoff references are stale and must not supersede #226/#228.

### S174 TRAIN-cache rebuild / replay lane

Branch:

`claude/s174-train-cache-rebuild-20261007`

Current head visible at handoff:

`a6075ffcce6b89572f0e17731f8415cf1d22d6f3`

This lane is separate from PR #228 and contains the real-TRAIN cache rebuild, gate analysis, corrected calibration replays, and downstream re-scoring.

---

## 3. Hard boundaries that remain in force

These are not suggestions. They remain hard constraints unless a later explicit authority record supersedes them:

- `TRAINING=OFF` for real data.
- `STAGE_A_EXECUTION=OFF`.
- `MULTIMODAL_TRAINING=OFF`.
- `500K=NOT_AUTHORIZED`.
- `STAGE4=NOT_AUTHORIZED`.
- `TEST=SEALED`.
- `MORABITO=PROTECTED`.
- no production target is selected;
- no production representation dimension is selected;
- no production uncertainty model is selected;
- no production threshold is selected;
- no production EMA half-life is selected;
- no real-RNA optimizer/EMA mutation is authorized.

A tiny **synthetic** bounded mutation rehearsal may only be considered after the joined runtime/interface/adapter gate is fully GREEN and frozen.

---

## 4. Canonical runtime mechanics — what is current and what is obsolete

The accepted V5 runtime lineage uses:

- student/online encoder: `KeyedIPBEncoderV2Reference`;
- V4 IPB / `BlockPredictor` mechanics;
- V4 gene tokenizer mechanics;
- teacher initialized as a parameter-identical deep copy of the authenticated student encoder;
- teacher frozen/eval and advanced only through guarded EMA after a proven successful optimizer step;
- AdamW over online encoder + predictor parameters only;
- gradient unscale before validation when GradScaler is used;
- physical step-completion proof before EMA;
- checkpoint/restart that binds online, predictor, EMA teacher, optimizer, scaler, cursor and typed continuation/provenance.

Presentation-normalized EMA is current runtime mechanics:

`momentum = exp(log(0.5) * presentations_this_update / half_life_presentations)`

Teacher age unit:

`SUCCESSFUL_BASE_CELL_PRESENTATIONS`

Important non-authority:

- historical fixed `.996` is **not** current V5 production authority;
- candidate `16,249` presentations is **not** a selected production half-life;
- the deterministic teacher/block loss in the runtime is a mechanics fixture, not scientific target authority.

Do not resurrect old `CurrentTrainingAuthorityV2`, `OptimizerGuardV4`, inactive guard files, generic donor rehearsal paths, legacy dict EMA persistence, or PR #223's copied V5 runtime sources.

---

## 5. Scientific teacher/student rule that must not be lost

The teacher may have richer evidence than the student. That is desirable.

But a partial-RNA student cannot in general be required to reproduce teacher-private realization-level information it never observes. Under deterministic squared error, the student can only recover a conditional expectation of the target given its admitted evidence.

Therefore:

- rich teacher is allowed and desirable;
- deterministic matching of the full private teacher realization is **not** automatically scientifically valid;
- shared/predictable target components, distributional targets, uncertainty or abstention may be needed;
- runtime mechanics do not decide this scientific target question.

Do not promote the runtime teacher-block test into a scientific target freeze.

---

## 6. Historical provenance failures that drive the current RED-team tests

### TD23/TD33 reset/local/global row alias

A B-side `sample_row` was reset locally to `0..24999` and then treated as a global expression row. This created a false relationship around `0.3906061`; the correct global row gave about `0.0062546`.

Any old analysis without proven B-side addressing is `ROW_BINDING_UNVERIFIED`.

### Sept-8 physical row/value binding lesson

Metadata or payload authentication alone is insufficient if the consumed values are from the wrong row.

The required proof chain is:

- global `expression_row`;
- `source_row_index == expression_row`;
- block-local `row_index` remains distinct;
- selected local row is validated;
- source cell identity equals logical row identity;
- source donor identity is coupled;
- matrix slot is authenticated;
- feature-space identity is authenticated;
- payload physical location and digest are authenticated;
- consumed values digest equals the authenticated values digest.

The invariant is:

`coordinate + logical identity + payload provenance + consumed values = one proof chain`

### Smoke-scale observation-operator regression

Historical regression:

- 2K: stress-twin 42/42 operators, calibration-closure 36/42;
- 10K: 42/42 vs 41/42;
- 100K: both 42/42;
- 500K: both 42/42;
- full 4,553,407: both 42/42.

Root cause: calibration-closure removed the stress-twin zero-quota rescue.

The 2K smoke gate must explicitly preserve all 42 observation operators before later bounded rehearsal.

---

## 7. What was completed on PR #228 in this chat

Work was performed under RED -> GREEN discipline and recorded on the audit branch.

### A. Policy-only q-safety cannot promote execution proof

RED:

`0d393d296ea5168e739fc4c3a5768e22844852d7`

GREEN:

`0618e639fb2f124790e5fa3bf206fca0c971ff3a`

Result: `POLICY_ONLY_NOT_EXECUTION_PROVEN` cannot be treated as executed q-safety.

### B. Bare enum spoof closed

RED:

`6d891e51eec5494441200c00940ad8f428edab7d`

GREEN:

`1a4f2e8ebca66ed0c63fa4b1b4f2bcf03dd86dcb`

Result: a bare `PROVEN_BY_BOUND_ADAPTER_RUNTIME` enum is insufficient; a typed `BoundAdapterQSafetyProofV1` is required.

### C. Cross-run proof replay closed

RED:

`0ceac519e1bab1578a25e3f6d4ee800f41d978d0`

GREEN:

`74f2b99d827e16134bf02c1820958442b78c37ee`

Result: q-safety proof is bound to exact adapter ID/digest, exact batch scientific identity digest, and exact runtime-source digest.

### D. Real V77 conversion -> `QualificationBatchV1`

RED:

`3fe29343bd415bd18a5d1c27f85ccd21eeed44a0`

GREEN:

`8e631460f3c286f46e34139431c990ec687ecb52`

The bridge binds:

- exact ordered feature identity;
- structural measurement support;
- source/operator rosters and mapping;
- donor grouping;
- query/evidence masks;
- adapter digest;
- observer/producer manifest digest;
- split identity;
- target identity.

Visibility classes are preserved:

- student expression + masks: model-visible;
- query counts + full library size: readout-only;
- donor identity: split-only;
- raw source/operator IDs: provenance/operator context only and stripped before learnable context.

### E. Executed hidden-query q-safety perturbation

The V77 adapter is physically executed twice with identical worlds except for the hidden query value.

The proof checks that:

- hidden readout changes;
- model-visible digest remains identical;
- lawful operator-context digest remains identical;
- support, mask and observation identity remain fixed;
- query values stay readout-only.

This re-exercises the S167/S168 repair rather than trusting a policy receipt.

CI coverage omission was caught before falsely claiming RED. The workflow was then corrected so the test actually ran.

RED gate:

`74135e3036e117b388fbd3bcfaabb824abcf109e`

GREEN implementation candidate recorded in audit:

`1e6e28d895d9c9d2b04d754b4154884b74b02b1c`

The produced proof remains non-authorizing:

- `execution_authorized=False`;
- `training_authorized=False`;
- `production_promotable=False`.

### F. Canonical ZERO_UPDATE runtime bridge

The joined test now exercises the canonical V5 student, teacher and predictor under `torch.no_grad()` and captures state before/after.

Target assertions include:

- online parameters unchanged;
- teacher parameters unchanged;
- predictor parameters unchanged;
- optimizer state unchanged;
- checkpoint digest unchanged;
- optimizer step remains `0`;
- teacher presentations remain `0`;
- no EMA;
- no optimizer step;
- `training_authorized=False`.

The canonical ZERO_UPDATE module intentionally owns no alternative training/optimizer/EMA/checkpoint implementation; it delegates to the inherited canonical V5 constructors/checkpoint helpers.

### G. Physical V77 adapter source binding

A later RED required the ZERO_UPDATE receipt to bind the **physical source bytes** of the V77 adapter, not a caller-supplied arbitrary digest.

RED commit:

`787915d67575501c6fd4629c2a1c0c555f62da1f`

The branch then added a small source-binding facade and receipt binding. Do not treat the caller-supplied digest alone as proof.

### H. Provenance V2 strengthening

At PR #228 head `6282b59c...`, the historical provenance attack surface was strengthened beyond V1.

Changed file:

`src/sea_ad_jepa/qualification/physical_binding_v2.py`

Purpose: keep V1 historical, while V2 additionally binds:

- donor identity;
- matrix slot;
- feature-space digest;
- physical payload location;
- payload digest;
- authenticated value digest;
- consumed value digest;
- global/local row and logical/source cell identity.

Tests attack wrong global row, wrong selected local row, wrong cell ID, wrong donor ID, wrong matrix slot, wrong feature-space digest, wrong payload location and wrong consumed values.

**Important:** at the moment of final takeover, this latest provenance-V2 head must still be verified with fresh workflow evidence before it is called GREEN. Do not infer GREEN from source inspection alone.

---

## 8. Exact PR #228 files the new agent should inspect first

At handoff the changed-file surface is intentionally small:

- `.github/workflows/v77-qualified-zero-update-join.yml`
- `docs/superpowers/plans/2026-10-07-v77-qualified-zero-update-join.md`
- `scripts/v77/v77_synthetic_batch_adapter.py`
- `src/sea_ad_jepa/qualification/physical_binding_v2.py`
- `src/sea_ad_jepa/qualification/v77_bound_zero_update.py`
- `src/sea_ad_jepa/qualification/v77_join.py`
- `src/sea_ad_jepa/qualification/v77_zero_update.py`
- `tests/integration/test_v77_canonical_zero_update.py`
- `tests/integration/test_v77_executed_q_safety.py`
- `tests/integration/test_v77_joined_zero_update.py`

Before adding code, compare these files against the exact PR #226 base and verify that no inherited V5 runtime source was modified.

---

## 9. Final spillover audit still required on PR #228

Do not authorize mutation until these are complete and documented:

1. fresh GitHub Actions GREEN at the exact current PR #228 head;
2. verify the canonical ZERO_UPDATE test is actually included in the workflow path and executed;
3. verify physical-binding V2 attack tests are actually executed;
4. run inherited shared-interface runtime-binding regressions proving V1 cannot promote mutation proof;
5. verify only typed presentation-EMA V2 physical continuation can promote runtime mutation proof;
6. grep/audit PR #228 and inherited path for:
   - fixed `.996` defaults;
   - alternate optimizer `.step()` routes;
   - direct EMA mutation;
   - alternate checkpoint serialization/reload routes;
   - old authority/guard classes;
   - hidden private implementation imports;
   - V1 proof promotion;
   - source/operator IDs reaching learnable model parameters;
   - q/readout values or full-library normalization leaking into student input;
   - stale scientific thresholds/targets being imported as runtime authority;
7. confirm the 2K synthetic smoke lineage preserves all 42 observation operators;
8. freeze exact runtime + interface + adapter + join + synthetic world/realization + workflow SHAs.

Only then may the preregistered tiny synthetic bounded-mutation rehearsal be handed to Macha.

---

## 10. Macha/V77 synthetic science — what remains valid

The S157 exact RNA semantic twin result remains important:

`NON_IDENTIFIABLE_BY_DESIGN`

Do not tune it away.

Core interpretation:

- exact same-assay RNA twins can be non-identifiable from admitted RNA evidence;
- raw source/operator identity can separate them only as a shortcut control, not as biology;
- measurement/support context itself can act as an identity proxy and must remain guarded;
- SCENIC+/ATAC are not automatically independent evidence if they were constructed from the same RNA or otherwise circular;
- richer external evidence should be qualified by independence, pairing and exposure history.

The preregistered bounded synthetic mutation experiment remains **unexecuted** unless a later branch explicitly records otherwise.

Minimum arms when eventually authorized:

- planted lawful biological signal;
- exact RNA semantic twin;
- operator-linked nuisance twin;
- query-leak negative;
- clean negative.

Keep init/runtime/update budget/context/visibility/scoring identical across arms.

Primary question:

`Does learned representation behavior distinguish biology from nuisance beyond what is possible from admitted observations?`

Loss reduction alone is not success.

---

## 11. S174 real-TRAIN cache defect — now value verified

This is separate from PR #228.

The old cache:

`D:/Jepa project/data/cache/stage81a3r_corrected_real_train`

was built with a scrambled HVS/SEA-AD feature-axis mapping.

The probe was preregistered before counts were read and then value-verified on real TRAIN cells.

Original value-verification branch head:

`claude/v77-synthetic-premise-custody-20261005@976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`

Probe summary:

- 36 cells total, 12 per matrix;
- one HVS + two SEA-AD matrices;
- builder's scrambled map agreement: 100%;
- true-gene-by-Ensembl agreement: about 2.4-3.0%;
- validated decoder recovery: 99.9-100%.

Named marker examples included MBP, PLP1, SNAP25 and GAD1 where real source counts were nonzero but cache addresses held unrelated genes and zeros.

Therefore S174 is `VALUE_VERIFIED`.

Affected V77 real-data calibration results that used the old cache must not be cited as current scientific evidence without corrected replay.

S157 synthetic conclusions are unaffected by this cache defect.

---

## 12. S174 rebuild lane — current state at handoff

Branch:

`claude/s174-train-cache-rebuild-20261007`

Current head:

`a6075ffcce6b89572f0e17731f8415cf1d22d6f3`

New rebuilt cache location:

`D:/Jepa project/data/cache/s174_rebuilt_real_train_v1`

The old cache was not modified.

Rebuild design:

- fresh physical H5AD gene-ID join;
- HVS and SEA-AD rebuilt;
- NPH carried over unchanged;
- collisions excluded and recorded, never guessed or summed;
- decoder retained as an independent cross-check rather than as the primary rebuild path.

Frozen rebuild commit:

`cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`

Initial build/audit record:

`70a27edb68319020104dc722aef9e2ef886ba74c`

### G1 nuance

The frozen G1 rule failed literally for SEA-AD because the simple independent reread did not follow 897 pre-existing frozen provenance remappings.

Do **not** rewrite history and call frozen G1 a pass.

The failure was fully localized:

- all 24 HVS matrices matched exactly;
- all non-remapped SEA-AD addresses matched exactly;
- every remapped entry matched its physical source count;
- 100% of the disagreements were confined to the known remapped set.

The owner authorized a prospective successor gate (G1b concept): preserve frozen G1 as failed, but allow use of the cache only if a prospectively frozen successor verifies all remapped entries, all non-remapped entries and zero unexplained discrepancies without changing the already-built artifact.

Check the S174 branch for the actual later gate record before relying on this summary.

### Important identity issue separate from S174

353 of 897 SEA-AD remappings follow Ensembl history to a gene with a different symbol.

This is an identity-governance question, not a reason to retroactively tune the S174 replay. Keep it separate.

### Replays already progressed beyond the original handoff

At branch head `a6075ffc...`, Macha/Claude recorded corrected downstream re-scoring against the rebuilt/corrected calibration points.

Examples from that head:

- background search remains 0/18 accepted, but best match moved from 5/11 to 2/11;
- Step 3 remains not closed;
- the old latent-C6 “matches real on 5/6” premise no longer holds against corrected points;
- the old post-observation shortfall becomes an overshoot against corrected topology metrics;
- one prior factor-family falsifying invariant disappears because corrected detection transitivity lies inside the family range;
- the substate headline setting falls from 4/5 inside the old detection band to 0/5 against corrected points;
- the cited Observer-V2 close match was to old corrupted points and is materially farther from corrected points;
- T5 failure direction remains but the real within/pooled reference shifts;
- S159 corrected pooled points fall outside the old donor-bootstrap p05-p95 band on at least expression median |r| and detection transitivity.

Do not automatically treat corrected pooled envelopes as biological targets. They are corrected measurements, not selected scientific estimands.

At `a6075ffc...`, pending synthetic replay was explicitly recorded for:

- realization isolation V1/V2;
- dynamic-range tournament V1/V2;
- two exploratory variants;
- dynamic-range verdict;
- Observer-V2 audit correction.

The next agent must read the latest S174 branch history before assuming those remain pending, because that lane may continue in parallel.

---

## 13. S149/S159 interpretation after S174

S149's prior ~89% pooled-topology result is no longer valid evidence from the old cache. It was computed on a scrambled cross-study gene axis and must be judged only through the corrected replay.

Do not say “S149 was false” solely because the old input was corrupted. The corrected replay determines what survives.

S159 bootstrap was already `NEEDS_REPAIR` before S174:

- 24 or 20-ish donor bootstrap replicates in historical variants are not sufficient authority for sealed-challenge tail thresholds;
- corrected points now expose additional envelope mismatch;
- do not recenter thresholds after seeing corrected outcomes;
- do not promote bootstrap p05/p95 bands into biological target authority.

---

## 14. Representation dimension authority remains unresolved

A previous lineage created mechanics for FULL104 dimension authority, but the numeric dimension is **not** frozen.

A lawful `D_shared / D_private / D_total / D_obs` selection still requires:

1. physical FULL104 closure (>30 GB, 8,915 blocks under the exact binder);
2. real full-stream metrics;
3. prospective Monte Carlo precision authority;
4. hash-bound selection/firewall.

Do not promote 160D merely because it appears in historical design documents.

---

## 15. Large scientific assets and custody

Do not assume large binary scientific inputs live in ordinary Git history.

Prior exact-hash custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef`

Key custody docs are on `handoff/jepa-20261007-runtime-interface-custody` and its predecessor custody branches.

Known chat/runtime assets historically include:

- split expression archive parts;
- calibration bundle;
- checkpoints bundle;
- expression bundle;
- NPZ scientific artifact;
- T1 checkpoint archive;
- WSL execution notes;
- status/repair-plan notes.

The two expression parts have recorded reassembly SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Large binary custody is cryptographic/provenance custody, not automatic scientific validity.

Historical old PROD41K/T1 checkpoint is `FORENSIC_ONLY` because the fp16 lineage had 48 gradient-dead mandatory tensors.

Historical local teacher-target code under:

`D:/Jepa project/CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2`

is forensic reference only; do not resurrect it as current runtime authority.

---

## 16. Things the next agent must NOT do

Do not:

- merge the documentation custody branch into implementation as if it were a code successor;
- merge Macha's branch wholesale into PR #228;
- transplant old V5 runtime files from #223;
- resurrect fixed `.996` EMA;
- select 16,249 presentations as production authority;
- treat V1 runtime proof as mutation authority;
- treat q-safety policy declarations as executed proof;
- treat source/operator IDs as model covariates;
- treat support masks or measurement context as unrestricted identity embeddings;
- treat SCENIC+ or ATAC as independent without explicit circularity/exposure audit;
- treat Morabito as pristine independent validation simply because the current architecture changed;
- tune exact RNA twins until they become identifiable;
- use the corrupted old Stage81A3R cache for new calibration claims;
- overwrite old results after S174; report old vs corrected side-by-side;
- silently change a preregistered failed gate into a pass;
- call local tests GitHub CI;
- call a receipt “executed” unless the executor physically ran;
- equate authenticated provenance with scientific validity;
- infer GREEN when CI/status evidence is absent.

---

## 17. Recommended next actions for the new agent

### Lane A — finish PR #228 first

1. Fetch PR #228 live head and make sure it has not moved from `6282b59c...` before editing.
2. Read the 10 changed files listed above.
3. Inspect the latest GitHub Actions run for the exact head.
4. If `physical_binding_v2.py` / provenance attacks are not in the workflow, add them before claiming RED/GREEN.
5. Get a real GREEN run for:
   - joined ZERO_UPDATE tests;
   - executed q-safety tests;
   - canonical ZERO_UPDATE state-invariance tests;
   - inherited V1/V2 runtime-binding regressions.
6. Run final source spillover audit for `.996`, alternate optimizer/EMA/checkpoint paths and learnable identity leakage.
7. Verify 2K all-42-operator support.
8. Update `docs/agent/JEPA_V77_RUNTIME_WIRING_AUDIT_20261007.md` with exact head, workflow IDs, tests and evidence classes.
9. Freeze the exact adapter/runtime/interface/world/workflow identities.
10. Only then decide whether the preregistered tiny synthetic mutation rehearsal may proceed.

### Lane B — monitor S174 separately

1. Fetch `claude/s174-train-cache-rebuild-20261007` live head; it may have advanced beyond `a6075ffc...`.
2. Read all `results/v77/s174_replay/` outputs and S174 docs before citing corrected V77 conclusions.
3. Verify G1/G1b history was not rewritten.
4. Verify corrected replays use only TRAIN and preserve old-vs-new reporting.
5. Keep identity-history remapping question separate from replay outcome tuning.
6. Do not import S174 real-data code into PR #228.

### Lane C — science after joined runtime qualification

When PR #228 is fully GREEN, revisit the preregistered synthetic mutation experiment exactly as frozen. Do not redesign arms after seeing new outcomes.

---

## 18. Evidence vocabulary to preserve

Use these labels precisely:

- `GREEN_MECHANICS`
- `POLICY_ONLY_NOT_EXECUTION_PROVEN`
- `PROVEN_BY_BOUND_RUNTIME`
- `DEVELOPMENT_CALIBRATION`
- `NEEDS_REPAIR`
- `NON_IDENTIFIABLE_BY_DESIGN`
- `ROBUST_TO_MODELED_NUISANCE`
- `SUPPORTIVE_BUT_NOT_IDENTIFYING`
- `UNQUALIFIED`
- `FORENSIC_ONLY`
- `SUPERSEDED`
- `VALUE_VERIFIED`

Do not overstate authority.

---

## 19. Operational lessons from this work

Several mistakes were caught in prior audit and should not be repeated:

- large source files were once reconstructed from incomplete fetched views and temporarily lost public functions; exact prior Git blobs were restored;
- a temp marker was accidentally committed and later removed;
- a stale source-grep provenance test had to be replaced by behavioral/exported-manifest checks;
- a workflow once omitted the new q-safety test, meaning the test existed but was not actually CI-executed;
- GitHub intermittently returned 502s; never convert a transport failure into a scientific/code conclusion;
- with large files, prefer minimal patches or exact blob restoration over rewriting whole source from truncated connector output.

The rule is evidence before assertion.

---

## 20. Handoff bottom line

The project is **not blocked on designing another runtime**. The canonical student/teacher/predictor/optimizer/EMA/checkpoint mechanics are already qualified enough for the current purpose.

The immediate job is to finish proving the **join**:

`authenticated V77 synthetic world -> physical adapter -> QualificationBatchV1 -> executed q-safety -> canonical V5 ZERO_UPDATE -> exact no-mutation receipt`

and to prove the historical row/value and identity attacks fail closed.

In parallel, S174 has shown that a major old V77 real-TRAIN calibration cache was gene-axis scrambled. A corrected cache has been rebuilt and corrected replays are materially changing several historical calibration premises. That scientific repair lane is separate and must not be conflated with runtime qualification.

No real-data training is authorized.
