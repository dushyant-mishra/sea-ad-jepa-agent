# JEPA target-discovery contamination and identifiability boundary — 2026-10-07

Status: `AUDIT_ONLY__NO_TARGET_WINNER__NO_REPRESENTATION_WINNER__TRAINING_OFF`

Base custody head audited: `d6a020bc25a891039a72c89d7b04bc3e59f381a0` on `handoff/jepa-20261006-macha-audit-successor`.

This checkpoint resumes the historical target-discovery audit from the latest custody state. It does not authorize real-RNA Stage A, training, TEST, pathology, Morabito, 500K, Stage 4, or any target/representation promotion.

## 1. Governing scientific constraint

A rich teacher may use biological evidence unavailable to the partial-RNA student. That is desirable when it improves biological fidelity. But the student cannot be required to point-predict the realized teacher-only component of that state.

For teacher evidence `T`, lawful student evidence `C`, and query `q`, deterministic squared-error prediction can at best recover the conditional expectation of the teacher state given `(C,q)`. Therefore the prospective target contract must distinguish:

- `z_predictable`: components empirically demonstrated to be recoverable from lawful partial RNA;
- `z_teacher_private`: components supported by richer teacher evidence but not established as point-identifiable from partial RNA;
- biological uncertainty / support: the change or ambiguity induced by missing relevant biological evidence, kept distinct from sequencing-depth uncertainty.

Deterministic student loss may apply only to components that prospectively earn `RECOVERABLE_FROM_VIEW` status. Partially recoverable or nonrecoverable components require probabilistic treatment, calibrated uncertainty/abstention, or exclusion from deterministic matching while remaining available to construct/validate the rich teacher state.

Historical `D_shared` / `D_private` terms must not be silently redefined as these new recoverability classes; their historical semantics were different and require re-derivation.

## 2. 50K discovery-expression artifact: byte custody versus semantic qualification

The split package present in the current runtime was independently rechecked without writing a reconstructed copy.

Expected package:

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`
- expected bytes: `607959761`
- expected SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Observed split parts:

- part001 bytes `303979881`; SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 bytes `303979880`; SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

Stream-concatenated result:

- bytes: `607959761`
- SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Therefore physical package identity is established in this runtime.

The contained historical matrix identity remains:

- dimensions: `50000 x 41238`
- matrix SHA-256: `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

However, artifact authentication does **not** establish HVS/SEA-AD gene-value semantic correctness.

## 3. HVS / SEA-AD physical-feature defect applies to historical 50K producer too

The recovered historical producer `foundation_materialize_discovery_expression.py` builds an HVS/SEA-AD map from provenance `source_feature_index` to `molecular_address_index`, then looks up raw H5 sparse physical `indices` through that map.

Current custody establishes that the provenance `source_feature_index` for affected HVS/SEA-AD lineages is an Ensembl-harmonized rank, not the raw H5AD physical feature-column coordinate. Using it as the raw sparse column index can bind a value from physical gene A to canonical identity B.

Consequences:

- historical 50K HVS values: `BYTE_AUTHENTIC__GENE_VALUE_SEMANTICS_QUARANTINED_PENDING_CORRECTED_REMATERIALIZATION`
- historical 50K SEA-AD values: same classification
- later FULL104 HVS/SEA-AD Level-4 materialization: `SEMANTICALLY_INVALID_PENDING_REMATERIALIZATION`
- prior lineage PASS/hash match: retained as byte/provenance evidence only, not biological feature-axis qualification

Historical artifacts must remain unchanged for custody. Corrected materialization must use new hashes and an explicit physical-column mapping receipt.

## 4. NPH52 is a separate dependency-repair lineage and remains unresolved, not invalidated by association

The recovered 50K sample freeze contains:

- HVS: `10958` cells
- NPH52: `5221` cells
- SEA-AD: `33821` cells
- total: `50000`

The historical expression audit lists 35 direct HVS/SEA-AD shards. The seven NPH52 operators occupy operator indices 35-41 and were introduced through a separate NPH dependency-repair/helper path using the historical TRAIN full-feature derivative.

The recovered R helper indexes that derivative using `source_feature_index + 1`. This is structurally different from the raw-H5AD HVS/SEA-AD producer.

Therefore current classification is:

`NPH52__SEPARATE_LINEAGE__FEATURE_AXIS_SEMANTICS_NOT_YET_REPROVEN_IN_THIS_TAKEOVER`

Do not mark NPH52 invalid merely because HVS/SEA-AD are invalid. Also do not mark it safe until the producer/order of the historical TRAIN full-feature derivative is recovered and it is proven that the helper index addresses its actual physical columns.

Required NPH proof:

1. recover the TRAIN full-feature derivative producer and exact artifact identity;
2. establish its physical feature-column order;
3. prove the NPH provenance index addresses that physical order, not a harmonized/sorted rank;
4. perform sentinel gene/value checks where raw ancestry is available;
5. issue a hash-bound NPH feature-axis receipt.

## 5. Target-discovery contamination boundary

The preserved TD41-TD58 archive remains valuable, but interpretation must be dependency-aware.

Current safe classifications:

- Any result requiring gene-addressed HVS or SEA-AD values from the affected historical 50K materialization is **not decision-grade until corrected replay**.
- TD56-TD58 remain evidence for the *idea* of recurrent/shared relational structure, but their mixed-source biological conclusion requires corrected HVS/SEA-AD replay.
- NPH-only portions of historical analyses are not automatically contaminated by the HVS/SEA-AD defect, but remain provisional until the NPH derivative feature axis is independently requalified.
- TD55 remains non-promotable; prior history already found poor clean transfer to NPH52.
- TD57C primary failure remains a failure; later forensic positives do not rescue it.
- No historical aggregate cosine, reconstruction score, or recurrence result selects a production target.

A fine-grained TD41-TD58 replay ledger should be built from the archived scripts/results, recording for each statistic whether it depends on HVS, NPH52, SEA-AD, mixed-source pooling, or source-independent logic. Only affected statistics should be recomputed.

## 6. Historical multimodal evidence: what it can and cannot answer

### Stage75 / SCENIC+

Historical Stage75 constructed enhancer-informed regulatory evidence from GSE174367 snRNA and snATAC, but the modalities are separate nuclei and were linked using sample/state annotations. Stage75 itself retained explicit boundaries: no validated regulation, no validated GRN claim, no causal-validation pass, and no therapeutic-target claim.

This evidence can improve a biologically rich teacher or define regulatory hypotheses, but it does **not** demonstrate same-cell RNA -> ATAC/regulatory-state predictability.

### Morabito / GSE174367

Current governance classifies Morabito as separate-nucleus, donor-level, heavily development-exposed, and protected from target/representation selection. It cannot be used to tune the prospective target or claim same-cell correspondence.

### GSE214979

The audited external-asset matrix identifies GSE214979 as verified same-nucleus paired RNA+ATAC across audited rows. It also records donor-identity conflicts/possible pooled-lane label-swap issues and a small effective donor count.

Its lawful future role is conditional external support after prospective exclusions and role freeze. It is especially useful as a falsification/support asset for RNA-predictability of richer chromatin/regulatory components, but it must not silently become target-selection authority.

### Core distinction

`teacher can construct richer state from multimodal evidence` does not imply `student can deterministically recover that state from partial RNA`.

Same-nucleus paired data are the correct evidence class for directly testing that recoverability; separate-nucleus donor-level data are not.

## 7. Historical calibration evidence supports component-wise recoverability

The preserved 2026-08-24 calibration bundle already contains an informative partial-evidence ceiling. On the heldout-combined 45-donor reader set, the lawful-RNA predictive baseline reported approximately:

- broad_common: `R2 = 0.9792`
- weak_distributed: `R2 = 0.9530`
- local: `R2 = 0.9940`
- local_core: `R2 = 0.9756`
- local_halo: `R2 = 0.9987`
- core_halo: `R2 = 0.9996`
- sparse_marker_like: `R2 = 0.9340`
- innovation_tail: `R2 = 0.5753`

Rare-event average precision was substantially below the exact-full-RNA oracle as well.

These historical numbers do not qualify a production target, and their exact relevance must respect the lineage limitations above. But conceptually they strongly argue against one all-or-nothing deterministic target: common/program structure can be highly RNA-predictable while innovation/rare components can remain much less determined by partial RNA.

## 8. Prospective target architecture to evaluate after data repair

The next candidate family should be explicitly decomposed rather than a monolithic latent:

`z_teacher = z_shared_predictable + z_teacher_private`

with a separate uncertainty/support output `U_bio`.

Qualification must ask independently:

1. **Teacher fidelity:** Does richer evidence improve biologically meaningful state construction over RNA-only/global baselines?
2. **Recoverability:** Which target components can be predicted from lawful partial RNA on donor-held-out and source-held-out evaluation?
3. **Incremental information:** Does each retained component beat global-cell-state, program-only, query-only, technical/support, and simple RNA regression baselines?
4. **Teacher-private residual:** Is nonrecoverable rich evidence preserved as uncertainty/private state rather than charged as deterministic student error?
5. **Evidence response:** Does `U_bio` change appropriately as relevant biological evidence is withheld/added, independently of sequencing-depth uncertainty?
6. **Query safety:** If query-conditioned, do executed transitive q-safety and no-leakage controls pass?
7. **Transport:** Are the same components stable across lawful donors/sources/operators rather than surviving only through pooled/source-confounded geometry?

TD56-TD58 relational structure is a candidate ingredient for `z_shared_predictable`, not itself the complete target.

SCENIC+/ATAC/regulatory evidence is a candidate ingredient for improving teacher fidelity and defining `z_teacher_private` or shared components only after recoverability is directly measured.

## 9. Required execution order

No new real-RNA Stage-A comparison should run before these gates:

1. recover/prove NPH52 full-feature derivative physical feature order;
2. reconstruct HVS/SEA-AD canonical-address -> raw physical-column mapping from stable source feature identity;
3. fail closed on missing, duplicate, ambiguous, version-conflicted, or many-to-one mappings;
4. rematerialize affected HVS/SEA-AD blocks under new hashes with explicit mapping receipts;
5. perform sentinel raw-vs-materialized value checks;
6. build the TD41-TD58 dependency/replay ledger;
7. selectively replay only contaminated historical statistics;
8. freeze the component-level recoverability ledger and candidate comparison before any Stage-A execution;
9. keep same-nucleus multimodal support assets outside target-selection unless separately and prospectively authorized.

Only after those gates should the ZERO_UPDATE qualification/runtime join be revisited for a real biological candidate.

## 10. Permanent boundaries at this checkpoint

- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- selected population estimand = unset
- current Phase-A eligible population authority = `13510` cells
- historical ~4.55M reader-fit population is not current Phase-A selection authority
- `REAL_RNA_STAGE_A_EXECUTION = NOT_AUTHORIZED`
- `TRAINING = OFF`
- `500K = NOT_AUTHORIZED`
- `STAGE_4 = NOT_AUTHORIZED`
- NIH-CARD real biological correspondence = unopened
- TEST = sealed
- Morabito = protected
- pathology = unopened

## 11. Immediate next work

The next audit task is **not another broad historical search**. It is the narrow missing dependency proof:

`NPH52 TRAIN derivative physical feature order -> NPH source_feature_index semantics -> hash-bound qualification`

In parallel, recover the exact HVS/SEA-AD source feature-identity tables needed to construct an explicit raw physical-column mapping. Once those are in hand, implement the corrected rematerializer and replay ledger under a separate repair lane; do not modify historical artifacts in place.
