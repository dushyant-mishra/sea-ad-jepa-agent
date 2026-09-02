# Stage81A2R Closure Report

**FINAL LOCAL EVIDENCE - FROZEN 4,096 VOCABULARY UNCHANGED**

## Foundation

**FOUNDATION ONLY - SEA-AD + HVS + NPH52**

- Current exact canonical genes: **40,422**
- Source rows: **299,775**
- Distinct source features within source families: **93,536**
- Unique adjudicated biological identities across identity layers: **43,248**
- Current Exact: **40,422**
- Legacy Exact: **773**
- Alternative Authority Exact: **0**
- Source Native Anchored: **43**
- Source Native Unprojected: **0**
- Ambiguous: **1**
- Symbol Or Identifier Poor: **2,009**
- True Technical Nonbiological: **0**
- Future-data firewall: **PASS**; semantic hash `fbabd61a6ae89e1c16e7084854c3a15ce7de94de003455e400d2d82458ec2cab`.

### Foundation Source Breakdown

scope,foundation_source_rows_total,foundation_unique_source_features,foundation_unique_biological_identities,G_foundation_current_exact,G_foundation_legacy_exact,G_foundation_alternative_authority_exact,G_foundation_source_native_anchored,G_foundation_source_native_unprojected,G_foundation_ambiguous,G_foundation_symbol_or_identifier_poor,G_foundation_true_technical_nonbiological
FOUNDATION,299775,93536,43248,40422,773,0,43,0,1,2009,0
SEA-AD,36601,36601,35786,35527,259,0,0,0,0,0,0
HVS,18736,18736,18736,18735,1,0,0,0,0,0,0
NPH52,244438,38199,37543,34790,700,0,43,0,1,2009,0


### NPH Reconciliation

Of **2,009** Foundation identifier-poor identities, NPH52 contributes **2,009**, SEA-AD contributes **0**, and HVS contributes **0**.

### Molecular Evidence and Universal Address Policy

Molecular evidence preservation is distinct from universal encoder address eligibility. The Foundation Molecular Address Space contains current exact, legacy exact, and source-native anchored identities. It is not exclusively a current gene vocabulary.

identity_layer,molecular_evidence_preserved,universal_identity_established,proposed_universal_encoder_eligibility
current_exact,YES,YES,ELIGIBLE
legacy_exact,YES,YES,ELIGIBLE
alternative_authority_exact,YES,YES,HUMAN POLICY REQUIRED
source_native_anchored,YES,YES,ELIGIBLE
source_native_unprojected,YES,NO,NOT YET ELIGIBLE
ambiguous,YES,NO,NOT YET ELIGIBLE
symbol_or_identifier_poor,YES,NO,NOT YET ELIGIBLE
true_technical_nonbiological,NO,NO,NOT YET ELIGIBLE


### Foundation Molecular Address Space

- Current exact addresses: **40,422**
- Legacy exact addresses: **773**
- Source-native anchored addresses: **43**
- Exact cross-layer duplicate equivalence classes: **0**
- Exact within-layer duplicate equivalence classes: **0**
- Final distinct universal molecular addresses: **41,238**
- Preserved nonuniversal evidence identities: **2,010**
- Successor registry semantic SHA-256: `5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff`
- Ambiguous and identifier-poor identities remain preserved as **DATA / PROVENANCE LIMITATION** evidence; they are not biological top-K exclusions and are not unrestricted encoder addresses.
- Measurement support remains matrix-specific and distinguishes measured zero from structurally unmeasured.

### Matrix-Accounting Reconciliation

- Historical Stage81A2: **24 HVS + 11 SEA-AD + 1 aggregate NPH52 = 36 asset-registry entries**.
- Current Stage81A2R: **24 HVS + 11 SEA-AD + 7 NPH52 QS objects = 42 matrix-level measurement-support contracts**.
The change from 36 historical asset-registry entries to 42 measurement-support matrices is an accounting-granularity change: the historical registry represented NPH52 as one aggregate source collection, whereas A2R preserves the seven NPH QS objects as separate matrix-level measurement operators. No six new foundation datasets were introduced.

## Project-Wide Identity Audit

**PROJECT-WIDE - FOUNDATION + FUTURE DATASETS**

- Scientific datasets: **47**
- Biologically identifiable identities: **85,660**
- Safely mapped to current Ensembl: **82,809**
- Source-native/noncanonical: **2,851**
- Ambiguous: **98**
- Truly identifier-poor: **41,719**

The **41,719** truly identifier-poor identities are a project-wide total across Foundation and future-use datasets. They are not a Foundation-only count.

## NPH Sanity Check

The **2,009** unique NPH remainder was re-read from seven metadata-only source caches. Exact anchors found: **0**. Final NPH truly-unresolved count: **2,009**. Status: **PASS**.

## Protected 4,096

Four alternate/nonprimary source representations were already resolved without rewriting the frozen vocabulary.
- `MEG8_ENSG00000225746`: **SOURCE_METADATA_CONFLICT** - The source symbol is MEG8, but exact Ensembl ID ENSG00000258399 and its coordinates identify MIR493HG; conflicting source metadata cannot prove the frozen MEG8 identity wrong.
- `MEG8_ENSG00000288302`: **KEEP_FROZEN_SAME_BIOLOGICAL_GENE** - AL132709.8 is an exact HGNC alias for MEG8 and uniquely supports the already-frozen MEG8 canonical identity; the prior ENSG00000288302 assignment is not carried into the frozen vocabulary.
- `SH3BGRL2_ENSG00000272137`: **KEEP_FROZEN_HISTORICAL_ID** - Historical source ID ENSG00000272137 is preserved in provenance. Both source IDs point as possible replacements to the frozen SH3BGRL2 ID, creating a many-to-one topology; possible_replacement is not proof and does not justify a protected rewrite.
- `SH3BGRL2_ENSG00000287811`: **KEEP_FROZEN_HISTORICAL_ID** - Historical source ID ENSG00000287811 is preserved in provenance. Both source IDs point as possible replacements to the frozen SH3BGRL2 ID, creating a many-to-one topology; possible_replacement is not proof and does not justify a protected rewrite.
- Remaining protected human blockers: **0**
- Canonical correction required: **NO**

## Hashes

- Frozen vocabulary file SHA-256: `d8fbe2f0d2208f0034103443b6424169ff66e1b674769eda6b635c8ce84523e4`
- Frozen vocabulary semantic SHA-256: `f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb`
- Protected Stage81A2 and authority-cache hashes: **PASS**

## Tests

- Focused Stage81A2R tests: **75 passed**
- Full v4 tests: **862 passed**
- Repository tests: **874 passed**
- Failures: **0**
- Warnings: **0**
- Deterministic compact artifacts: **16/16 byte-identical**

## Runtime Invocation

The `sea-ad-jepa` project is installed editable in the `sea-ad-jepa-v3` environment. Repository scripts are invoked as modules (`python -m scripts.v4.<module>`) so neither tests nor scripts require a manually injected `PYTHONPATH`.

## Governance

Final Stage81A2R status: **STAGE81A2R_READY_FOR_FREEZE**

Stage81A3R not started. Stage81B not started. No model training, expression biology, pathology access, or push.
