# JEPA target-recovery custody and supersession checkpoint — 2026-10-07

Status: `TARGET_RECOVERY_KNOWLEDGE_DURABLY_CHECKPOINTED__TRAINING_OFF__REAL_RNA_STAGE_A_OFF__TARGET_WINNER_NONE`

This checkpoint preserves the conclusion-bearing target-discovery archaeology, the newly recovered local source artifacts, the current supersession map, and the exact custody status of the local runtime files. It is documentation/custody only. It does not authorize training, Stage A, Stage 4, protected-outcome access, or target promotion.

## 1. Current scientific target status

There is still **no qualified production target winner**.

The durable scientific constraint is:

- a rich teacher may use more lawful biological evidence than the student;
- the student sees partial RNA plus the query;
- the student cannot be required to deterministically reproduce teacher-state components that are not conditionally identifiable from the student view;
- target components must therefore be classified as recoverable, partially recoverable, nonrecoverable, or not identified from the student view;
- a biologically important teacher-private component is not automatically a student/model failure;
- biological fidelity, student recoverability, and uncertainty calibration are separate gates.

The mathematically appropriate deterministic squared-error limit is the conditional expectation `E[z_T | C,q]`, not the realized rich-teacher state when teacher-private information remains.

Current V3 prose contains this principle, but the machine-readable Stage-A contract was found to enforce mainly top-level family verdicts rather than a mandatory per-component recoverability ledger. That is a pre-Stage-A governance gap.

## 2. Historical target-lineage findings now preserved

### Historical T1 / rich-H matching

Recovered historical evidence shows the starting `u0` representation already contained useful correct-cell/query-aware biology, while the T1 objective drove mathematical loss downward and eroded fine query-local/contextual geometry. A later large learned-predictor analysis over ~4.785M queries found:

- modest donor-reproducible H-space improvement;
- benefit mostly cell-global rather than query/program-specific;
- self-masked molecular reader ceiling approximately negative;
- visible RNA predicted protected program scores substantially better;
- ~95% of correct-vs-shuffled advantage was cell-global;
- attention nearly maximally diffuse (normalized entropy ~0.998);
- different queries used nearly identical routing (cosine ~0.991);
- program-matched memory enrichment ~1x.

All four adjudicators denied promotion. A single donor-cross-fitted residual-target rescue was later executed and also failed to rescue protected biology. Therefore direct rich-H matching and strict residual-target rescue are closed historical branches.

### Shared-state D_shared lineage

The historical FULL104 shared-state branch ended at `TEACHER_BIOLOGY_LIMIT` with `D_shared = null`. However, that biological terminal is **not currently decision-grade**, because the deciding HVS/SEA-AD FULL104 Level-4 expression substrate is now known to have a physical-column semantic defect (see Section 4). Preserve the procedure and negative-history lesson, but do not treat the biological numerical terminal as requalified evidence until corrected replay.

### Contextual Teacher Target V1

`CONTEXTUAL_TEACHER_TARGET_V1` passed F0 implementation/leakage mechanics. Historical F1 design was extensively frozen (2,781 cells; 104 donors; 42 operators; 44,496 statistical assignments; 43,108 unique `(cell,q)` compute pairs; planned 474,188 expensive forwards), but the Sept-3 handoff explicitly records **REAL F1 NOT RUN** and real reader/forward authority not frozen. Therefore F0 PASS is not biological target qualification.

### R5 measured target and later developmental work

The Sept-26 R5 lineage correctly re-separated teacher fidelity, query specificity, and student predictability. Its measured eight-partner q-context is a developmental anchor, not a qualified production neural target. Historical results were mixed: APOE showed some complementary-RNA predictability, but separate prespecified readouts did not establish a qualified teacher; P2RY12/HLA-DRA were weaker. No program has passed independent chromatin/protein fidelity. Training remained off.

### TD41–TD58 recovery

The Sept-7/Sept-8 target-discovery packages and working archive were recovered. The original TD34 producer hash was recovered and TD41–TD58 code/results were inspected. Current interpretation:

- TD55 query-specific proxy selection did not transport cleanly to NPH52 and is not a live target candidate.
- TD56–TD58 provide evidence for recurring donor-level relational structure across HVS/NPH52/SEA-AD, including partial-RNA views.
- This is evidence for **shared predictable relational structure**, not evidence that a partial-RNA student can reproduce the entire rich-teacher state.
- TD57C primary failure remains a failure; its later forensic analysis cannot rescue it.

## 3. Critical correction: earlier 50K feature-axis closure is superseded for HVS/SEA-AD

Earlier in this audit, recovery of `foundation_materialize_discovery_expression.py`, `foundation_materialize_nph_discovery_sample.R`, `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`, and `FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json` led to an interim classification that the historical 50K discovery expression address axis had been primary-source verified.

That interim classification is now **superseded for HVS and SEA-AD**.

Reason: a later recovered V46-era audit establishes that the historical `HVS_COMMON` and `SEA_AD_COMMON` provenance field named `source_feature_index` is an Ensembl-harmonized rank, **not the physical H5AD feature-column index**. The newly recovered 50K producer directly does:

`source_to_address[source_feature_index] = molecular_address_index`

and then consumes HDF5 sparse matrix `indices` as if those physical column indices were keys in `source_to_address`.

Therefore the 50K HVS/SEA-AD producer has the same semantic risk class as the invalidated FULL104 HVS/SEA-AD Level-4 materializer: a canonical address can receive counts from the wrong physical gene column while all downstream positional/hash checks remain internally consistent.

Updated classification:

`DISCOVERY_50K_HVS_SEAAD_FEATURE_AXIS = NOT_REQUALIFIED__PHYSICAL_COLUMN_SEMANTIC_DEFECT_POSSIBLE_AND_NOW_PRIMARY_SOURCE_SUPPORTED`

`DISCOVERY_50K_NPH52_FEATURE_AXIS = SEPARATE_LINEAGE__NOT_INVALIDATED_BY_HVS_SEAAD_FINDING__STILL_REQUIRES_OWN_PRIMARY_SEMANTIC CHECK`

This explicitly supersedes the earlier over-broad checkpoint classification `DISCOVERY_EXPRESSION_ADDRESS_AXIS_PRIMARY_SOURCE_VERIFIED` for HVS/SEA-AD.

## 4. FULL104 HVS/SEA-AD invalidation now controlling

Current branch commit `be522a911002f53f0f225f602e125cbeb29eca37` records the stronger physical-column defect for historical FULL104 HVS/SEA-AD Level-4 materialization.

Controlling status:

`HVS_SEAAD_FULL104_LEVEL4_SEMANTICALLY_INVALID_PENDING_PHYSICAL_COLUMN_REMATERIALIZATION__NPH52_SEPARATE`

Reader-fit104 blast radius was HVS 198,718 cells + SEA-AD 4,118,213 cells = 4,316,931 / 4,553,407 historical reader-fit104 cells (~94.8%).

Consequently, historical mixed-source FULL104 gene-addressed biological conclusions are not decision-grade until corrected rematerialization/replay. This includes the old `TEACHER_BIOLOGY_LIMIT` numerical terminal and later gene/program-labelled analyses that depended on the affected blocks.

## 5. Required substrate repair before real-RNA target qualification

For every HVS/SEA-AD matrix and every decision-bearing canonical address, prove:

`canonical molecular address -> exact intended source feature identity -> exact matrix-specific physical feature column -> raw count slot -> canonical output column`

Do not use harmonized-rank `source_feature_index` as a physical H5AD column. Resolve physical columns from authenticated feature identities/order, verify identity before consuming counts, preserve collision/unresolved semantics fail-closed, and rematerialize under new hashes rather than overwriting historical artifacts.

Only biological results whose numerical inputs changed need replay; method/provenance/firewall tests that do not depend on the corrupted values may remain useful.

## 6. Local runtime custody captured in this checkpoint series

The current runtime contains ~1.4 GB of project artifacts, including:

- split historical 50K discovery-expression archive parts;
- calibration bundle;
- checkpoint bundles;
- TD Sept-7 handoff and TD41–TD58 working archive;
- Nott Table S5;
- expression metadata bundle;
- original recovered discovery materializers;
- discovery audit/lineage JSON;
- V63 handoff/custody material;
- WSL/status notes;
- small execution receipts and test artifacts.

Exact top-level byte sizes and SHA-256 hashes are committed separately in `docs/agent/archive/chat_runtime_20261007_target_recovery/JEPA_CHAT_RUNTIME_CUSTODY_SHA256_20261007.csv`.

ZIP member inventories (name, uncompressed/compressed bytes, CRC32, parent archive hash) are committed separately in `docs/agent/archive/chat_runtime_20261007_target_recovery/JEPA_CHAT_RUNTIME_ZIP_INVENTORY_20261007.csv`.

Large binary bytes are intentionally **not** inserted into ordinary Git history when doing so would duplicate hundreds of MB of local scientific data/checkpoints. Their exact identity is preserved cryptographically and their internal inventories are recorded. Critical small source/receipt files are copied directly into the same archive directory in subsequent custody commits.

## 7. Current hard boundaries

- `TRAINING = OFF`
- `REAL_RNA_STAGE_A_EXECUTION = NOT_AUTHORIZED`
- `STAGE_4 = NOT_AUTHORIZED`
- `500K = NOT_AUTHORIZED`
- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- `SELECTED_POPULATION_ESTIMAND = UNSET`
- real NIH-CARD biological correspondence remains unopened
- TEST remains sealed
- Morabito remains protected

## 8. Immediate scientific continuation

1. Repair/requalify HVS/SEA-AD physical feature-column mapping for the exact substrates needed by Stage A.
2. Keep NPH52 separate; verify its derivative feature-row semantics rather than assuming the HVS/SEA-AD finding applies or does not apply.
3. Add machine-enforced **component-level recoverability** to the Stage-A premise contract before comparing rich-teacher targets.
4. Re-evaluate target candidates only on semantically qualified RNA.
5. Teacher fidelity first; student recoverability second; uncertainty/abstention third. Do not promote a target because latent loss or cosine alignment is good.
6. Treat TD56–TD58 as relational-structure evidence only; do not upgrade them into full rich-state identifiability.
7. Keep ATAC/SCENIC+/other rich evidence for teacher fidelity/biology tests without demanding impossible deterministic reconstruction of teacher-private components from partial RNA.

This file is intended to be a takeover-safe summary of the current target-recovery state and to prevent future agents from resurrecting superseded conclusions.