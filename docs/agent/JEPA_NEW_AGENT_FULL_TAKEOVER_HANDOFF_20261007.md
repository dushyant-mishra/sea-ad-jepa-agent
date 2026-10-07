# JEPA full new-agent takeover handoff — 2026-10-07

Status: **COLD-START TAKEOVER GUIDE — NON-AUTHORIZING**

Purpose: allow a new agent to resume the JEPA project without reconstructing the state from chat history, old branches, or misleading historical shorthand. This document consolidates the current runtime/interface state, scientific conclusions, Macha/V77 state, historical failure audits, data/custody inventory, scripts/results worth trusting, superseded/forensic material, and the exact next execution sequence.

The governing work rule is:

**bounded change -> RED -> minimal repair -> GREEN -> adversarial self-audit -> historical-spillover check -> GitHub custody checkpoint -> only then advance.**

Do not infer authority from file names such as `canonical`, `production`, `current`, `frozen`, or from old successful runs. Authority must be reconstructed from the live branch/receipt chain described here.

---

## 1. Executive state

The project is no longer blocked on core optimizer/EMA/checkpoint mechanics. The canonical V5 runtime has been mechanically qualified for a bounded synthetic rehearsal, and the shared qualification interface has been cleanly restacked and validated on top of it.

The immediate blocker before handing bounded mutation work to Macha is the **actual joined V77 adapter -> shared interface -> canonical runtime audit**, especially executed q-safety and physical row/value provenance.

The current scientific program remains deliberately open. No biological target, representation, estimand, weighting rule, deciding threshold, uncertainty model, multimodal evidence winner, or production EMA half-life has been selected.

Hard boundaries remain:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`

No real-RNA mutation run is authorized by the runtime work described here.

---

## 2. Canonical live GitHub surfaces

### 2.1 Runtime — PR #224

Branch:

`reconcile/canonical-v5-runtime-successor-20261006`

Draft PR:

`#224 — Converge canonical V5 runtime safety path`

Accepted runtime checkpoint:

`9d00684e08ba34ef8d7b04e478b9c380cd36d537`

At that accepted checkpoint the three relevant GitHub workflows were GREEN:

- `v5-inactive-runtime-step-guard`
- `v64-runtime-core-reconciliation`
- `Current authority surface guard`

Do not silently replace this runtime with historical `CurrentTrainingAuthorityV2`, `OptimizerGuardV4`, the removed `inactive_runtime_step_guard_v1.py`, or the retired generic rehearsal path.

### 2.2 Shared interface — PR #226

Old PR #223 is superseded for handoff purposes because it carried older copies of V5 runtime files.

Clean successor branch:

`reconcile/shared-qualification-v2-on-canonical-runtime-20261007`

Draft PR:

`#226 — Validate shared qualification V2 on canonical V5 runtime`

Validated head recorded by the custody branch:

`e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`

PR #226 was intentionally built from accepted runtime SHA `9d00684e...` and transplanted only:

- `src/sea_ad_jepa/qualification/*`
- qualification tests
- two V5 runtime-binding integration tests
- shared-interface workflow
- restack custody docs

It did **not** transplant old `src/sea_ad_jepa/v5/*` files from #223.

The shared qualification/governance suite and stacked V5 runtime-binding integration passed on that combined tree.

### 2.3 Custody — PR #227

Branch:

`handoff/jepa-20261007-runtime-interface-custody`

Draft PR:

`#227 — Custody checkpoint for validated runtime/interface state`

Custody head before this document:

`92c1963810add48365a00de85bd0984df211cf5c`

This branch is documentation/custody only. It must not become an implementation lane.

### 2.4 Macha / V77

Live branch rechecked 2026-10-07:

`claude/v77-synthetic-premise-custody-20261005`

Current observed head:

`51b7e2e4f91b53da6353dbff3bf944bbc5916006`

This is newer than the earlier audited `a3e272ba...` and `eb98ede...` snapshots. The latest closeout records S157, independent-evidence analysis, SCENIC+ circularity, measurement-context shortcut findings, an executed q-safety probe, and the first bounded-mutation preregistration. It still says `TRAINING=OFF`, `ZERO_UPDATE` only, nothing selected.

---

## 3. First documents a new agent should read

Read these before writing code:

1. `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md` — this file.
2. `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md` — concise current custody summary.
3. `docs/agent/JEPA_V5_RUNTIME_ARCHITECTURE_AUTHENTICATION_AUDIT_20261007.md` — architecture/EMA/provenance audit on the runtime branch.
4. `docs/agent/JEPA_RICH_TEACHER_PARTIAL_STUDENT_IDENTIFIABILITY_REAUDIT_20261007.md` — target-design correction, commit `6c576cec1aa4a8fdab863fae64eacced7945b65b`.
5. `docs/agent/JEPA_MACHA_V77_S149_INDEPENDENT_RECONSTRUCTION_20261006.md` on branch `handoff/jepa-20261006-macha-audit-successor` — independent reconstruction of S149/S159.
6. Macha branch `docs/agent/ACTIVE_STATE.md` at `51b7e2e4...` — newest S157/Phase-5 state.
7. `docs/agent/archive/chat_runtime_20261007/JEPA_RUNTIME_INTERFACE_CHAT_CUSTODY_MANIFEST_20261007.json` — current artifact/custody map.
8. Historical exact-hash custody commit `cb7a98d00359eecece8525b23c43fbc8578c69ef`.

Then inspect the canonical runtime and qualification source listed below rather than searching randomly through historical branches.

---

## 4. Canonical runtime architecture and what is actually proved

### 4.1 Student / predictor / tokenizer lineage

The reusable low-level mechanics were explicitly audited against later scientific branches.

Accepted reusable mechanics:

- student encoder: V5 `KeyedIPBEncoderV2Reference` in `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`;
- keyed RNG contract: `src/sea_ad_jepa/v5/keyed_rng_contract_v2.py`;
- data-first packing/geometry: `src/sea_ad_jepa/v5/data_first_geometry.py`;
- predictor/IPB mechanics: `src/sea_ad_jepa/v4/ipb_jepa.py`;
- gene tokenizer: `src/sea_ad_jepa/v4/gene_tokenizer.py`.

The keyed V5 encoder Git blob was unchanged across later V47/V48/V63 branches checked during the audit. The V4 predictor/IPB and tokenizer blobs were likewise unchanged through V63. Later target-discovery work changed scientific questions, not these low-level mechanics.

The teacher is structurally a parameter-identical copy of the authenticated student encoder at initialization and is advanced by EMA. That does **not** mean the scientific teacher target is selected.

### 4.2 Canonical guarded update path

Important runtime files:

- `src/sea_ad_jepa/v5/inactive_update_reference.py`
- `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py`
- `src/sea_ad_jepa/v5/prefreeze_runtime_authority.py`
- `src/sea_ad_jepa/v5/inactive_checkpoint_binding_v1.py`
- private implementation blob for checkpoint binding, transitively bound by runtime provenance
- `src/sea_ad_jepa/v5/ema_presentation_v1.py`
- `src/sea_ad_jepa/v5/ema_bound_runtime_proof_v1.py`
- private EMA implementation blob, transitively bound by runtime provenance
- `src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py`
- `src/sea_ad_jepa/v5/runtime_target_semantics_boundary_v1.py`

Mechanically qualified sequence:

`authenticated bounded input -> encoder -> predictor -> loss mechanics fixture -> backward -> GradScaler unscale when used -> gradient validation -> guarded AdamW step -> physical step completion assertion -> presentation-derived EMA -> completed update proof -> bound checkpoint -> physical write -> SHA-256 verification -> verified reload`

### 4.3 Optimizer / scaler results

Physically tested:

- actual V5 AdamW, not a toy optimizer;
- GradScaler finite path;
- unscale occurs before gradient validation;
- planted non-finite gradients can cause a physical scaler skip;
- a scaler-skipped or rejected optimizer step cannot be reported as complete;
- EMA cannot advance after an incomplete/rejected/skipped optimizer step.

### 4.4 Checkpoint / restart results

Checkpoint state covers:

- online/student parameters;
- teacher parameters;
- predictor parameters;
- optimizer state;
- GradScaler state when AMP is used;
- update cursor;
- presentations-seen cursor.

The bounded tested AMP trajectory is deterministic across interruption/reload.

Physical persistence requires:

- file exists;
- SHA-256 matches before deserialization;
- persisted object reloads;
- current premise digest matches;
- current runtime-source digest matches;
- logical checkpoint digest matches;
- completed guard receipt matches.

### 4.5 EMA authority correction

Do **not** use historical `.996` as current authority.

Recovered history:

- older V3 configuration froze EMA `0.996`, constant schedule, one EMA update after each proven valid optimizer step;
- later V5 authority explicitly kept EMA timescale open and prohibited silently inheriting `.996`;
- a candidate half-life of `16,249` successful presentations exists in recovered historical material, but was explicitly not frozen authority.

Current authenticated V5 EMA mechanics are presentation-normalized:

`momentum = exp(log(0.5) * presentations_this_update / half_life_presentations)`

Mechanical unit:

`SUCCESSFUL_BASE_CELL_PRESENTATIONS`

The runtime takes an explicit rehearsal half-life. It binds that identity and rejects drift on continuation. **No production half-life is selected.**

### 4.6 Runtime proof versions

`BoundRuntimeMutationProofV1`:

- readable/verifiable for historical/diagnostic purposes;
- insufficient to promote mutation proof.

`BoundRuntimeMutationProofV2`:

- required promotion path;
- produced only from the typed presentation-EMA persisted continuation;
- binds physical artifact digest, runtime source, premise, logical checkpoint, completed guard receipt, EMA configuration identity, EMA-bound authority, EMA completion proof, presentation unit, half-life identity, and teacher-age arithmetic;
- remains non-authorizing for training/execution/production promotion by itself.

---

## 5. Shared qualification interface state

Key package:

`src/sea_ad_jepa/qualification/`

Important modules include:

- `authorities.py`
- `canonical.py`
- `identity.py`
- `lifecycle.py`
- `oracle.py`
- `pipeline.py`
- `protocol.py`
- `qsafe.py`
- `receipts.py`
- `runtime_binding.py`
- `visibility.py`

Key properties already repaired/audited:

- oracle realization is bound;
- challenge partition is preserved;
- evaluation authorization is enforced;
- retry identities are distinct;
- CI trigger coverage is explicit;
- preflight partition validation exists;
- `REAL_RNA` cannot execute under synthetic authority;
- generic callbacks do not count as proof of physical zero mutation;
- generic policy declarations do not count as proof of executed transitive q-safety;
- V1 runtime proof cannot promote mutation proof;
- V2 typed physical runtime proof is required.

Important: q-safety proof is intentionally a **separate** object from mutation proof. Do not upgrade q-safety because the runtime checkpoint is strong.

---

## 6. The target-science invariant that runtime must not violate

Commit:

`6c576cec1aa4a8fdab863fae64eacced7945b65b`

Classification:

`RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA`

If teacher evidence is `T`, student lawful evidence is `C`, query is `q`, and teacher target is `z_T(T,q)`, then under deterministic squared error the best possible student is the conditional expectation:

`E[z_T(T,q) | C,q]`

not the realized teacher-private state when information in `T` is absent from `C`.

Therefore keep three concepts separate:

1. teacher fidelity — use richer evidence when it improves biological-state construction;
2. student predictability — only require point prediction for components demonstrably inferable from lawful student evidence;
3. shortcut control — q leakage, copied teacher embeddings, generic cell-state shortcuts and measurement identity shortcuts must fail.

The current deterministic teacher-block loss inside the V5 runtime is a **mechanics fixture only**. It is not authority to train a partial-RNA student to reproduce an arbitrary rich multimodal teacher realization.

Future target candidates must distinguish:

- shared/predictable biological state;
- teacher-private biological information;
- measurement-specific information;
- uncertainty caused by missing relevant biological evidence.

Potential valid future objectives include cross-view shared state, conditional distributions/means, explicit biological uncertainty, or abstention. No choice has been made.

Historical target interpretations to preserve:

- R5 was useful because it restored a genuinely richer teacher and separately tested predictability from complementary RNA;
- TD56–TD58 support a shared/predictable relational component across independent RNA views;
- TD58 is **not** permission to require full rich-teacher matching.

---

## 7. Historical identifiability lineage — do not erase these negative results

### V47 / technical-semantic twin

The project learned that an apparently biological RNA structure can be mimicked by technical/measurement structure. This reopened the identifiability question rather than merely demanding a stronger predictor.

### V48 / RNA-only limit

If a biological latent and a hidden capture state generate the same RNA observables, RNA alone cannot establish which causal story is correct.

### V63 / modeled nuisance versus exact twin

Later nuisance-aware machinery could reject nuisances inside its frozen modeled family. That is useful robustness evidence.

It did **not** eliminate the exact semantic twin. Keep the distinction:

`ROBUST_TO_MODELED_NUISANCE != BIOLOGICALLY_IDENTIFIED`

### Current safe scientific labels

Use terms such as:

- `DETECTABLE`
- `ROBUST_TO_MODELED_NUISANCE`
- `NON_IDENTIFIABLE_BY_RNA_ALONE`
- `REGULATORY_CORROBORATION_CANDIDATE`

Do not use `BIOLOGICALLY_SUPPORTED` until independent evidence actually earns it.

---

## 8. Macha/V77 current lane

Live branch:

`claude/v77-synthetic-premise-custody-20261005`

Latest observed head:

`51b7e2e4f91b53da6353dbff3bf944bbc5916006`

The newest `ACTIVE_STATE.md` closeout records the following.

### 8.1 S157 terminal

Result:

`results/v77/V77_S157_TERMINAL_RECEIPT_V1.json`

Conclusion:

- exact same-assay twin remains non-identifiable from RNA under every tested context;
- raw source/operator identity separates some nuisances only as an exploratory positive control and is not a production input;
- lawful depth/support descriptors do not resolve the operator twin;
- measurable-address count acts as an identity proxy;
- S157 establishes no cell-state biology.

Interpretation:

`NON_IDENTIFIABLE_BY_DESIGN_FROM_SAME_ASSAY_RNA`

Do not rerun seeds hoping the exact semantic twin magically separates. That would be tuning against a non-identifiability result.

### 8.2 Independent evidence matrix

Result:

`results/v77/V77_INDEPENDENT_EVIDENCE_MATRIX_V1.json`

Current finding:

- no candidate object is qualified to break a lineage twin today;
- measurements on the query's own nuclei/cells/donors can in principle add independent identifying information;
- static/external objects such as Nott, motifs, eRegulon catalogues, external perturbation, or other-donor spatial are supportive at best for a query-specific twin;
- same-nucleus multiome, separate-nucleus chromatin from query donors, and same-donor spatial are **UNQUALIFIED**, not declared unusable.

This is a requirements result, not a modality winner.

### 8.3 SCENIC+ circularity audit

Result:

`results/v77/V77_REGULATORY_CIRCULARITY_AUDIT_V1.json`

Current classification:

- SCENIC+ built from the same query RNA is circular for proving independent biology;
- SCENIC+ built on other data is a static regulatory object and may still have assay-class circularity/transport issues;
- no project SCENIC+ network is currently qualified as the identifying object.

Do not treat the word “regulatory” as proof of independence.

### 8.4 Context shortcut audit

Result:

`results/v77/V77_CONTEXT_SHORTCUT_AUDIT_V1.json`

High identity-proxy risks include:

- support pattern — model-visible for mechanical reasons but potentially highly identifying;
- measurable-address count;
- hidden-target count.

Synthetic observer depth was low shortcut risk in the executed diagnostic, but that does not generalize automatically to real data.

### 8.5 Runtime handoff package / q-safety probe

Result:

`results/v77/V77_RUNTIME_HANDOFF_PACKAGE_V1.json`

Macha reports an executed q-safety probe PASS on all S157 arms.

Important boundary finding BF1:

- the shared interface model view can carry lawful operator context including raw identity beside model inputs;
- only true model inputs may reach learnable parameters.

The joined runtime audit must independently verify this boundary. Do not assume Macha’s receipt alone proves the full canonical joined path.

### 8.6 Bounded-mutation preregistration

Result:

`results/v77/V77_S157_BOUNDED_MUTATION_PREREGISTRATION_V1.json`

Status:

**PRE-REGISTERED, NOT EXECUTED**

It awaits the runtime lane’s reviewed bound SHA and rehearsal contract.

---

## 9. Macha S146/S147 repaired support result

Earlier repaired synthetic support result remains useful:

- B4 ON approximately `0.8503`, designed `0.25–0.45`; OFF approximately `-0.0355`;
- C1 approximately `0.2555`, OFF approximately `-0.0049`;
- C2 approximately `0.5004`, OFF approximately `0.0040`;
- C3 approximately `0.0988`, OFF approximately `0.0151`;
- detect `3/4`, reject `4/4`.

Interpret B4 as **more recoverable than designed**, not as evidence the detector is broken.

All 2K seed-7302 worlds remain `DEVELOPMENT_CALIBRATION`, not independent confirmation.

Support must remain producer-side/per-element/name-mapped. Never infer structural support from observed nonzero values.

---

## 10. S149 / S159 real-data audit

Independent audit document:

`docs/agent/JEPA_MACHA_V77_S149_INDEPENDENT_RECONSTRUCTION_20261006.md`

Branch:

`handoff/jepa-20261006-macha-audit-successor`

### 10.1 S149 primary diagnostic

Primary result:

`results/v77/V77_REAL_COVERAGE_CONFOUND_DIAGNOSTIC_V1.json`

Producer:

`scripts/v77/diagnose_v77_real_coverage_confound.py`

Observed pooled thresholded correlation density:

`0.6148062687562521`

Coverage/composition null:

`0.5462551961765033`

Ratio approximately:

`0.8885`

Null transitivity was slightly higher than pooled real transitivity.

Supported conclusion:

`POOLED_DETECTION_TOPOLOGY_IS_STRONGLY_MEASUREMENT_COMPOSITION_CONFOUNDED`

Do **not** state the ~89% number as a donor-population estimand. The calculation is cell-weighted and preserves the sampled cell mixture:

- HVS: 3,072 cells / 62 donors;
- NPH52: 246 cells / 19 donors;
- SEA_AD: 1,408 cells / 68 donors.

The exact ratio is therefore currently cell-mixture-specific.

### 10.2 Within-cohort replacement envelope

Result:

`results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json`

Producer:

`scripts/v77/build_v77_within_cohort_envelope.py`

Classification:

`NEEDS_REPAIR`

Why:

- donor resampling does not create an equal-donor point estimand because all sampled donor cells are concatenated;
- several nominal real points lie outside their own 5–95% intervals;
- only 24 bootstrap replicates are used for 5th/95th empirical limits without a prospective precision/error budget;
- NPH52 treatment remains unresolved under the inherited class-count rule;
- population estimand and source weighting are not selected.

Examples of S159 point-outside-envelope behavior:

- HVS T5 point `0.774719...`, interval low `0.827365...`;
- SEA_AD T5 point `0.809178...`, interval low `0.888079...`.

Do not use the current within-cohort envelope as sealed-challenge threshold authority.

### 10.3 Required prospective real-data repair

Before synthetic thresholds are frozen from real data:

1. select a population estimand prospectively;
2. select biological-replicate/donor weighting;
3. specify source-combination rule;
4. recompute S149 sensitivity under at least current cell weighting, equal-donor or appropriate donor-level weighting, and equal-cell-per-donor sampling;
5. repair S159 interval construction prospectively;
6. derive bootstrap/Monte-Carlo replicate count from an error/precision requirement rather than inheriting 24;
7. decide NPH52 inclusion endpoint-by-endpoint.

This belongs to the real-data scientific lane, not the runtime lane or Macha’s synthetic lane.

---

## 11. Historical provenance/indexing failures that are now hard invariants

### 11.1 TD23 / TD33 row-addressing corruption

The historical 50K matrix stacked A then B. B-side `sample_row` reset to local `0..24999`. Treating that local/reset coordinate as the preserved global row created a false RNA dependency of approximately:

`0.3906061`

Correct global-row addressing gave approximately:

`0.0062546`

Older B-side analyses with unproven addressing were classified:

`ROW_BINDING_UNVERIFIED`

### 11.2 September-8 source-row/value authority repair

Commit lineage around `032ad149c76317466eae5f5e6b2fa8b451733fba` repaired a different problem: authentic metadata or a payload digest did not prove the values consumed came from the intended physical source row.

The durable requirements are:

- `source_row_index == expression_row` for the original source matrix;
- source cell identity matches;
- source donor identity matches;
- source-global `expression_row` and block-local `row_index` remain distinct;
- source digest / matrix slot / feature-space contract is authenticated;
- the block-local row selected is the row actually validated;
- consumed values are parsed from and coupled to the authenticated payload bytes.

Standing invariant:

**coordinates, logical identity, payload provenance, and consumed expression values must form one inseparable proof chain.**

### 11.3 Required adversarial attacks at the joined V77/runtime boundary

At minimum attack:

- global row swapped for local row;
- reset index substituted for preserved global row;
- correct payload digest but wrong row selected;
- correct metadata with wrong expression values;
- correct logical row with wrong physical payload location;
- query leakage;
- raw source/operator identity reaching learnable parameters;
- identity-proxy context fields reaching the model despite being intended only as provenance/context.

---

## 12. Historical small-scale observation-operator regression

A calibration-closure lineage removed the earlier stress-twin zero-quota rescue and silently erased observation operators at smoke-test scale.

Historical audit:

- 2K: stress-twin `42/42`, calibration-closure `36/42`;
- 10K: `42/42` versus `41/42`;
- 100K and larger: both eventually recover all 42.

This matters because 2K is a gate scale. A small smoke run must not qualify a lineage that silently drops operators.

Standing rule:

**never inherit a small-scale quota/coverage policy without explicitly verifying all required observation operators remain represented.**

---

## 13. Observation-operator scientific principle

Technology/study/source must be treated as an **observation process**, not a magical dataset-ID correction term.

Current safe direction:

`biology within observation process + transport across observation process`

Do not simply regress out study identity and call the residual biology. Do not assume source invariance is biologically correct. Do not allow raw source/operator IDs to become unrestricted learned covariates merely because they are authenticated provenance.

Measurement descriptors should represent defensible physical/technical quantities and must be audited for their ability to reconstruct dataset/operator identity.

---

## 14. Independent regulatory evidence program

The project should not tunnel on ATAC alone.

Potential evidence families include:

- same-nucleus RNA+ATAC / multiome;
- separate-nucleus chromatin from the same donors;
- Nott enhancer/promoter and cell-type regulatory evidence;
- motif / cisTarget evidence;
- SCENIC+ eRegulons;
- perturbational evidence;
- spatial evidence;
- genetics;
- protein;
- direct capture/process measurements.

Every candidate must answer:

1. what independent biological quantity is measured;
2. whether it is physically independent of the RNA value being explained;
3. whether RNA leaks into construction;
4. what biological specificity it adds;
5. what measurement nuisance could mimic it;
6. which exact semantic twin it can falsify;
7. which stronger twin remains possible;
8. whether donor/cell/query pairing is appropriate;
9. what ETL/provenance controls exist;
10. whether it is `CAN_BREAK_A_SPECIFIC_TWIN`, `SUPPORTIVE_BUT_NOT_IDENTIFYING`, `CIRCULAR_WITH_CURRENT_RNA`, `PROTECTED_OR_NOT_AVAILABLE`, or `UNQUALIFIED`.

Do not promote cross-modal evidence merely because it is a different assay. Construction, donor pairing, exposure history and measurement coupling matter.

---

## 15. Historical / authenticated data and custody map

### 15.1 Current chat-runtime scientific assets — exact custody

Immutable prior custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef`

Important files and exact SHA-256 values:

- `WSL execution issue.txt`
  - bytes `14576`
  - SHA-256 `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e`

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
  - bytes `437`
  - SHA-256 `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356`

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
  - bytes `303979881`
  - SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
  - bytes `303979880`
  - SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

Reassembled expression ZIP:

- bytes `607959761`
- SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- matched supplied checksum table in the prior custody audit.

- `checkpoints.zip`
  - bytes `71356460`
  - SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
  - key members include checkpoint manifest and T1 checkpoint files.

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
  - bytes `410278055`
  - SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

- `expression.zip`
  - bytes `3599456`
  - SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
  - bytes `1531109`
  - SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

- `t1_checkpoint_u0200.zip`
  - bytes `233729581`
  - SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`

- `Status and Repair Plan.txt`
  - bytes `5233`
  - SHA-256 `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56`

Large binaries are deliberately not duplicated into ordinary Git history. Their exact hash/size custody does not itself establish scientific validity.

### 15.2 Earlier V63 / NIH-CARD and public supplement custody

Historical V63 custody also records:

- `A_receipt.json` — NIH-CARD outcome-blind schema probe receipt A;
- `B_receipt.json` — schema probe receipt B;
- `h5ad_schema_probe.py` — mechanical matrix-slot/count classification probe;
- `make_fixtures.py` and `truth.json` — synthetic fixture producer/truth;
- `JEPA_V52_CLAUDE_RECOVERY_BUNDLE.zip`;
- Corces supplementary workbooks `41588_2020_721_MOESM12_ESM.xlsx` and `41588_2020_721_MOESM5_ESM.xlsx` with exact hashes in historical custody.

These are historical evidence/custody assets; they do not automatically authorize current Stage 3/4 execution.

### 15.3 Nott / V64 regulatory inputs

Historical V64 custody documented authentication/recovery information for:

- Nott Table S5;
- Nott microglia ATAC;
- neuron ATAC;
- oligodendrocyte ATAC;
- hg19->hg38 chain;
- hg38->hg19 chain.

Relevant historical successor:

`chatgpt/v64-e2-single-source-successor-20260929`

Historical custody head:

`003ad549a158ebf44093d9771cb7c2aabd240d05`

Treat these as authenticated/recoverable inputs where the associated custody says so, but not as automatically independent biological validation or a selected regulatory target.

### 15.4 User-recovered local packages reported 2026-10-07

These were found on the user’s machine and must not be forgotten. Unless independently present in GitHub custody, classifications here are based on the user’s inspection/report and are not a claim that this agent rehashed the local bytes.

- `C:\Users\dushy\Downloads\JEPA_CHAT_EXCLUSIVE_FINAL_SOURCES_20261005.zip`
  - reported SHA-256 `7A036B5CCF9965088D7730A54715E257E478D9BB7D768D34FE37E4BA3441BF34`
  - historical runtime text mentions approximately frozen `.996` but also says online-vs-EMA authority unresolved;
  - use as historical/custody evidence, not current timescale authority.

- `JEPA_NEW_CHAT_HANDOFF_20260916_V5_CURRENT.zip`
  - says V5 has EMA mechanics but no final EMA-timescale authority;
  - explicitly prohibits inheriting historical `.996`.

- `TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_20260909.zip`
  - includes `ema_scale_authority_v1.py`, tests, candidate half-life `16,249` successful presentations;
  - numeric choice is candidate-only, not frozen.

- `TEACHER_STUDENT_UNIFIED_V3_SELF_CONTAINED_REVIEW_PACKAGE.zip`
  - older V3 exact configuration with `.996`, constant schedule, EMA after each proven valid optimizer step;
  - historical V3 authority only.

- `JEPA_NEW_CHAT_HANDOFF_20260929_V63_AUDITED.md`
  - later governance evidence including `TRAINING=OFF`, `TD60=BLOCKED`, unresolved architecture/biological-specificity authority.

- local Git recovery branch `custody/local-only-jepa-recovery-20261006` at `c86dac574bdf99f228d3e2040673855c701b10c4`
  - reported exhaustive check of local branches/worktrees/stash;
  - formerly unpushed branches preserved and pushed;
  - old PROD41K/T1 checkpoint classified forensic-only because historical fp16 path contained 48 gradient-dead mandatory tensors.

- `D:/Jepa project/CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2`
  - contains `student_singleton_predictor_ema_direct.py` and `student_singleton_predictor_ema_qcontext.py`;
  - recovery audit classifies as forensic reference, not current authority.

---

## 16. Forensic / superseded artifacts and claims

Do not resurrect these as current authority:

- historical fixed EMA `.996` for V5;
- candidate EMA half-life `16,249` as if selected;
- old `CurrentTrainingAuthorityV2` / `OptimizerGuardV4` mechanics;
- removed `inactive_runtime_step_guard_v1.py`;
- generic donor-era rehearsal path;
- legacy dictionary EMA persistence route;
- old #223 V5 runtime file copies;
- pooled S149 topology as a biological calibration target;
- S159 recentered bootstrap intervals as qualified threshold authority;
- exact 88.85% S149 ratio as a donor-population estimand;
- V63 modeled-nuisance success as proof against exact semantic twins;
- raw source/operator IDs as production covariates;
- SCENIC+/ATAC as automatically independent biological evidence;
- seed-7302 development worlds as independent confirmation;
- any old PROD41K/T1 checkpoint with the gradient-dead fp16 lineage as current training evidence.

---

## 17. Operational errors already encountered in this runtime cycle

These are recorded because future agents should not repeat them.

1. Several stray/no-op refs were accidentally created during early branch operations. They contain no unique runtime content.
2. One checkpoint source file was accidentally replaced from an incomplete fetched view and temporarily lost public functions. The exact prior Git blob was restored and CI rerun before acceptance.
3. An orphan no-op commit object was created during Git-data staging without moving a branch ref.
4. A temporary marker file was accidentally committed during #226 staging and removed.
5. A source-grep provenance test became stale after wrapper refactoring; it was replaced with a behavioral/exported-manifest check, not weakened.

Practical rule: when editing large source files through a connector, prefer minimal patches or exact Git-blob restoration. Never reconstruct a full file from a truncated response.

---

## 18. What the next agent must do first

### Phase A — verify live heads before writing anything

Re-fetch:

- PR #224 head/status and workflows;
- PR #226 head/status and workflow;
- PR #227 custody head;
- Macha branch `claude/v77-synthetic-premise-custody-20261005` head;
- latest target/science lane head if another agent has advanced it.

Do not assume the SHAs in this document are still live if another lane has moved.

If a live branch advanced, compare from the SHA recorded here before making changes.

### Phase B — build the joined V77 + qualification + runtime branch

Do **not** modify #224 directly for V77 join logic.

Create an isolated successor from the validated #226 tree and import/adapt only the necessary V77 adapter/join code from the current Macha branch.

The joined path should be:

`repaired V77 world -> authenticated adapter -> QualificationBatchV1 -> shared qualification V2 -> canonical V5 runtime`

First mode is **ZERO_UPDATE only**.

### Phase C — prove executed q-safety

The joined path must generate q-safety evidence from the transformations actually executed.

Do not accept:

- policy declarations;
- callback registration;
- field-name checks alone;
- an adapter-local receipt that is not tied to the exact batch/runtime execution.

The proof must bind at least:

- batch scientific identity;
- synthetic realization/challenge partition;
- permitted visibility classes;
- feature identity;
- operator/support identity;
- actual transformations applied to every required q-sensitive channel;
- exact runtime/interface/adapter source identities.

### Phase D — execute coordinate/value-coupling red-team attacks

Run the historical attacks listed in Section 11 against the joined adapter.

Every substitution must fail closed before values reach learnable parameters or qualification output.

Especially verify that authenticated row metadata cannot be paired with values from another physical row while retaining a valid-looking batch identity.

### Phase E — model-input boundary / shortcut audit

Macha BF1 must be independently verified:

- lawful operator/source provenance may exist in interface/context structures;
- raw identity must not reach learnable model parameters unless explicitly authorized by future science;
- support/measurement metadata required for masking must not accidentally become an unrestricted identity embedding.

Attack model inputs with source/operator/proxy substitution and inspect the exact tensor/context objects crossing into encoder/predictor calls.

### Phase F — final joined bypass/spillover audit

Before mutation is enabled, search for:

- alternate optimizer step paths;
- direct EMA mutation;
- old guards/authorities;
- weaker V1 proof promotion;
- unverified checkpoint route;
- hidden imports of private implementation modules;
- old fixed `.996` defaults;
- historical target/threshold selection;
- row coordinates used without physical payload binding;
- source/operator IDs reaching the model;
- 2K operator coverage loss;
- q-safety status upgraded without executed proof.

### Phase G — freeze an exact rehearsal contract

Only if Phases B–F are GREEN, record exact SHAs for:

- runtime;
- shared interface;
- V77 adapter/join;
- synthetic world/realization;
- test suite/workflow.

Then define a tiny bounded synthetic mutation rehearsal.

---

## 19. First bounded synthetic mutation experiment — what it should and should not ask

Macha already has a preregistration. Reconcile it against the final joined runtime contract; do not silently rewrite it after seeing outcomes.

The first mutation experiment should be small and falsification-oriented.

Arms should include at minimum:

- BIO / planted lawful biological signal;
- exact RNA semantic twin;
- operator-linked nuisance twin;
- query-leak negative control;
- clean negative.

Keep identical across arms:

- initialization;
- optimizer/runtime;
- bounded update count;
- permitted context;
- target visibility rules;
- scoring procedure.

Freeze representations/readouts before oracle reveal.

Primary question:

**Does learned representation behavior distinguish biology from nuisance beyond what is possible from the admitted observations?**

Loss reduction alone is not success.

If exact semantic twins remain indistinguishable, that is a valid result and should remain `NON_IDENTIFIABLE`, not be tuned away.

The mechanics fixture does not authorize full rich-teacher realization matching. If the teacher uses evidence unavailable to the student, score only prospectively justified shared/predictable or probabilistic/uncertainty-aware targets.

---

## 20. Parallel work that may proceed while the joined runtime audit happens

### Scientific / real-data lane

May continue, without inspecting new synthetic challenge outcomes:

- select population estimand;
- select donor/source weighting;
- repair S149/S159 inference;
- derive bootstrap precision budget;
- qualify independent evidence candidates;
- resolve teacher/shared/private/uncertainty target semantics;
- audit Nott/ATAC/SCENIC+/spatial/genetics/protein evidence for independence and pairing.

### Macha lane

May continue only with non-mutation work until the runtime handoff contract is supplied:

- maintain S157 terminal;
- independent-evidence requirements analysis;
- shortcut diagnostics;
- adapter/join preparation;
- test fixtures;
- preregistration refinement only when it does not tune to hidden outcomes.

Macha should not implement a second optimizer/EMA/checkpoint stack.

---

## 21. Definition of “ready to hand runtime to Macha for real work”

All of the following must be true at one exact joined SHA:

1. canonical runtime workflows GREEN;
2. shared qualification workflow GREEN on exact runtime base;
3. actual V77 adapter runs through the shared interface in ZERO_UPDATE;
4. executed q-safety proof is bound to that run;
5. row/value provenance attacks fail closed;
6. raw identity/proxy leakage into learnable parameters is excluded;
7. only V2 typed physical runtime proof can promote mutation proof;
8. no alternate optimizer/EMA/checkpoint route survives;
9. historical 2K operator-coverage regression is checked for the chosen synthetic rehearsal;
10. rich-teacher target-neutrality is preserved;
11. all hard authority flags remain OFF for real/protected training;
12. exact SHAs and results are committed to GitHub.

At that point Macha may perform the explicitly approved **small bounded synthetic mutation rehearsal**. That is not authorization for real RNA, Stage A, TEST, Morabito, 500K, Stage 4, or production training.

---

## 22. Reporting vocabulary / epistemic discipline

Use exact classifications rather than vague success language.

Examples:

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

Never call local tests GitHub CI. Never call a receipt an execution if no executor ran. Never call authenticated provenance scientific validity. Never call a candidate threshold frozen because it exists in a JSON file.

---

## 23. GitHub discipline for the next agent

For each bounded phase:

1. write the RED/prospective contract first;
2. commit it;
3. observe isolated failure;
4. make the smallest repair;
5. run focused tests;
6. run broader regression/governance CI;
7. adversarially self-audit the repair;
8. check historical spillover;
9. commit a concise checkpoint/receipt;
10. verify the remote SHA;
11. report whether evidence is local or GitHub CI.

Prefer new successor branches for cross-lane integration rather than modifying the validated runtime branch with adapter-specific logic.

Keep GitHub updated continuously; do not let critical results exist only in chat or a local worktree.

---

## 24. Takeover checklist

A new agent should be able to answer all of these before changing code:

- What exact runtime SHA am I building on?
- Is #226 still the clean shared-interface successor?
- What is the current Macha head?
- Which q-safety fields are policy-only versus execution-proven?
- Is the row/value chain physically proven, or only metadata-bound?
- Am I using presentation-normalized EMA without selecting a production half-life?
- Is any old `.996`, V3, V64, generic rehearsal, or old #223 runtime file sneaking in?
- Am I treating runtime loss as mechanics-only rather than target authority?
- Am I respecting the rich-teacher/partial-student identifiability limit?
- Am I treating S149 ~89% as cell-mixture-specific?
- Am I keeping S159/24-bootstrap envelopes out of threshold authority?
- Am I preserving S157 exact-twin non-identifiability?
- Am I using raw source/operator IDs only as provenance or explicit exploratory controls?
- Have I checked all 42 observation operators at smoke scale?
- Are TEST, Morabito, real-RNA mutation, 500K and Stage 4 still closed?

If any answer is uncertain, audit before execution.

---

## 25. Bottom line

The canonical runtime and shared interface are mechanically in the best state the project has reached so far. The next meaningful step is **not** another runtime redesign and **not** large training. It is a narrow joined proof:

`V77 adapter + shared qualification V2 + canonical V5 runtime + ZERO_UPDATE executed q-safety + physical row/value provenance red-team`

If that survives, freeze the joined SHAs and run the already pre-registered tiny synthetic mutation rehearsal.

Scientifically, the project must continue to respect two negative results that prevent false confidence:

1. same-assay RNA exact semantic twins can be non-identifiable;
2. a partial-RNA student cannot be required to reproduce teacher-private information it never observes.

The path forward is therefore to combine a mechanically trustworthy runtime with prospectively qualified shared/predictable targets and genuinely independent biological evidence, without letting measurement identity, indexing mistakes, or historical defaults masquerade as biology.