# V64 parallel architecture handoff — privileged information, recoverability, promoter authority, and evidence independence

**Date:** 2026-09-30  
**Branch:** `chatgpt/v64-privileged-information-recoverability-20260930`  
**Draft PR:** #199 against `handoff/jepa-v64-target-architecture-20260930`  
**Purpose:** preserve architecture work performed in parallel with Claude's exact-control / Phase-A execution lane.

## 0. This branch does not supersede Claude's current execution sequence

Claude remains responsible for:

`exact supplement -> frozen exact-sampler suite -> repaired Phase-A rerun -> hard stop`

This ChatGPT branch does not change:
- the frozen Phase-A control semantics;
- Phase-B stop;
- Stage-4 seal;
- Morabito protection;
- TRAINING=OFF.

The branch addresses architecture questions that can be resolved outcome-blind while Claude executes.

## 1. Current teacher/student runtime finding

Audit of the current V5 reference mechanics shows:

- teacher and student are the same RNA encoder family;
- teacher receives measured RNA support;
- student receives masked RNA support;
- target blocks are gathered from RNA-derived teacher gene states;
- the current semantic authority defines one biological/query-local latent state.

There is no current semantic/runtime object for:
- multimodal-private teacher state;
- RNA-recoverability class;
- selective factor distillation;
- shared/private privileged subspaces.

Therefore adding ATAC/promoter/enhancer/contact/genetic/perturbational features to the existing teacher would be an architecture change, not a harmless enrichment.

Authority:
`results/v64/V64_PRIVILEGED_INFORMATION_RUNTIME_AUDIT_V1.json`

## 2. Privileged-information boundary

Frozen rule:

> Privileged biological measurements may constrain, annotate, validate, or provide optional modality-private state, but compulsory universal RNA-student supervision is limited to structure demonstrated to be recoverable from lawful RNA.

Recoverability classes:

- `RNA_RECOVERABLE`
- `PARTIALLY_RNA_RECOVERABLE`
- `PRIVILEGED_PRIVATE`
- `UNQUALIFIED`

A privileged factor that is not RNA-recoverable is not thereby biologically invalid.

Private state must be preserved and must not become a zero target on RNA-only cells.

Authorities:
- `docs/agent/V64_PRIVILEGED_INFORMATION_RECOVERABILITY_CONTRACT_20260930.md`
- `docs/agent/V64_PRIVILEGED_STATE_RECOVERABILITY_DECOMPOSITION_PROTOCOL_20260930.md`
- `results/v64/V64_PRIVILEGED_STATE_RECOVERABILITY_CONTRACT_V1.json`

## 3. Architectural decision: do not make one giant rich teacher

Prospective architecture:

### Universal path
`FULL104 RNA -> RNA online encoder -> predictor -> RNA EMA teacher`

### Privileged path on paired subsets
`regulatory evidence -> privileged encoder/critic -> Z_priv`

Then prospectively determine:
- `Z_priv_shared`: RNA-recoverable;
- `Z_priv_private`: privileged-private.

Before recoverability, privileged encoders are critics/validators, not universal answer keys.

After qualification, only the locked recoverable subspace can become factor-specific auxiliary RNA supervision.

Do not let the smaller selected multimodal cohort define universal scientific mass.

Authority:
- `docs/agent/V64_UNIVERSAL_RNA_TEACHER_PRIVILEGED_CRITIC_ARCHITECTURE_20260930.md`
- `results/v64/V64_UNIVERSAL_RNA_PLUS_PRIVILEGED_CRITIC_ARCHITECTURE_V1.json`

## 4. Rotation-aware recoverability

Earlier V61 work showed that stable biological structure may be stable as a subspace while individual axes rotate.

Therefore privileged recoverability is judged at stable-subspace level when coordinate identity is not established.

TEST donors may not choose:
- factor rank;
- basis rotation;
- feature selection;
- predictor complexity;
- recoverability thresholds.

Minimum scientific split:
`DONOR_DISJOINT_TRAIN_VALIDATION_TEST`

Cell-random splits have software-smoke status only.

## 5. Synthetic architecture smoke

A deterministic software fixture was executed in this chat environment.

Design:
- RNA predictors: 10;
- shared privileged dimensions: 4;
- private privileged dimensions: 4;
- shared factor generated from RNA plus small noise;
- private factor independent of RNA;
- TRAIN only fit;
- equalized target coordinate scales.

Results:

- shared mean R²: `0.9998952276297703`
- private mean R²: `-0.005015473036918544`
- forced full-state mean R²: `0.4974398772964259`

Rotation-aware fixture:
- mean principal-angle cosine: `0.9999752957547778`
- minimum cosine: `0.9999528365177357`

Interpretation:
- software correctly distinguishes recoverable from private state;
- full rich-state imitation contains an intrinsically unrecoverable component;
- rotated recoverable geometry remains recoverable at subspace level.

This is NOT biological evidence and establishes no scientific threshold.

Producer:
`scripts/v64/privileged_information_architecture_smoke_v1.py`

Receipt:
`results/v64/V64_PRIVILEGED_INFORMATION_ARCHITECTURE_SMOKE_RECEIPT_V1.json`

## 6. Promoter/TSS denominator

Base candidate promoter/TSS space must be annotation-first.

Use GENCODE to define the candidate transcript/TSS universe.

FANTOM5, SCREEN, brain promoter/isoform resources, NIH-CARD and Nott add evidence to candidates. They do not remove candidates merely because activity is absent or unmeasured.

This prevents activity/detectability selection from entering the denominator before coverage is measured.

Authority:
`docs/agent/V64_PROMOTER_TSS_CANDIDATE_UNIVERSE_CONTRACT_20260930.md`

## 7. Common support before E2 matching

The anchored/unanchored detection distributions already imply weak overlap.

Before freezing a matching operator:

1. characterize univariate and joint support;
2. measure trim fraction under candidate prospective designs;
3. freeze the operator;
4. then open the comparison outcome.

If no lawful comparator exists:
- trim;
- count;
- record.

Never widen tolerances after outcome inspection merely to preserve N.

Inference after trimming applies to the overlap population, not automatically all E2.

Authority:
`docs/agent/V64_COMMON_SUPPORT_AND_EVIDENCE_SENSITIVITY_CONTRACT_20260930.md`

## 8. Evidence independence terminology

Do not call adjusted residual association "independence."

Use:

`incremental support under observed adjustment`

because:
- expression is measured with error;
- detection is an imperfect expression proxy;
- promoter accessibility is an imperfect promoter-usage proxy;
- residual confounding can make evidence families look falsely independent.

Cross-family reports require sensitivity analysis for measurement error and omitted/shared drivers.

SCARlink versus SCENT on the same NIH-CARD cells is:
- same measurement/evidence family;
- different estimator.

It is a robustness comparison, not two independent confirmations.

## 9. Held-out-family validation

Preferred standard:

`construct from A/B/C -> lock -> evaluate on mechanistically distinct D`

A different estimator on the same measurements is not a held-out evidence family.

Potential families:
- paired observational;
- structural/contact;
- genetic association;
- interventional perturbation.

Held-out-family status does not remove activity/detectability bias; support/sensitivity diagnostics remain required.

Morabito remains protected.

Authority:
`docs/agent/V64_HELDOUT_EVIDENCE_FAMILY_VALIDATION_CONTRACT_20260930.md`

## 10. Regulatory evidence ledger

Prospective primary key:

`gene × candidate promoter × regulatory element × biological context`

The ledger keeps separate:
- measurement source;
- evidence family;
- estimator;
- support state;
- measurability;
- common support/trim;
- incremental support;
- sensitivity;
- RNA recoverability;
- access;
- license/terms;
- coordinate/provenance receipts.

Forbidden collapses include:
- NOT_MEASURED -> 0;
- estimator count -> evidence-family count;
- resource count -> independence count;
- public download -> open license;
- privileged-private -> failed biology.

Authorities:
- `results/v64/V64_REGULATORY_EVIDENCE_LEDGER_SCHEMA_V1.json`
- `docs/agent/V64_REGULATORY_EVIDENCE_LEDGER_SPEC_20260930.md`

## 11. Unrestricted resource registry

Current conservative registry includes:
- FANTOM5;
- GENCODE;
- SCREEN/cCRE;
- Dong/Roussos multi-region brain atlas;
- GSE211826;
- eQTL Catalogue;
- SCARlink;
- SCENT;
- Nott processed resources;
- Gasperini GSE120861.

Important corrections:
- FANTOM5: direct public, stated CC BY 4.0.
- eQTL Catalogue data: stated CC BY 4.0.
- GENCODE: official page states project data are open access; per-file license is not inferred from article license.
- SCREEN: public download is verified; data license was not established from the pages checked, so terms remain conservative.
- Nott processed data: public download, terms remain UNKNOWN.
- SCARlink code: MIT.
- SCENT code: MIT.

Authority:
`results/v64/V64_OPEN_REGULATORY_RESOURCE_REGISTRY_V1.json`

## 12. Availability shortcut

The 379 E2-anchored but NIH-CARD-RNA-unmeasurable genes remain a named diagnostic population:

`structural support present / paired RNA measurability absent`

They must not be treated as regulatory negatives.

Future recoverability/support models should test whether their success is driven by evidence availability.

## 13. Tests added

Focused tests now cover:
- current RNA-to-RNA runtime assumption;
- fail-closed governance;
- recoverability/private-state semantics;
- deterministic synthetic recoverability;
- exact replay;
- rotation-aware subspace smoke;
- promoter annotation-first rule;
- common-support no-rescue rule;
- estimator-family distinction;
- evidence ledger missingness;
- licensing/access separation;
- universal RNA teacher / privileged critic invariants.

Test files:
- `tests/test_v64_privileged_information_architecture_v1.py`
- `tests/test_v64_privileged_information_smoke_producer_v1.py`
- `tests/test_v64_regulatory_architecture_contracts_v1.py`
- `tests/test_v64_universal_rna_privileged_critic_architecture_v1.py`
- `tests/test_v64_open_regulatory_resource_registry_v1.py`

Focused CI:
`.github/workflows/v64-privileged-architecture-smoke.yml`

Execution status at handoff:
- synthetic logic executed in this chat environment: PASS;
- branch tests written;
- PR #199 open and mergeable;
- no GitHub Actions workflow run had appeared yet after adding the focused workflow.

Do not upgrade this to "CI passed" unless an actual run is observed.

## 14. Data requested for next empirical work

Highest-value upload:

A small donor-preserving NIH-CARD paired RNA+ATAC subset containing:
- aligned cell IDs / pairing key;
- donor ID;
- cell type;
- RNA counts or clearly declared representation;
- ATAC matrix or relevant peak subset;
- gene IDs;
- peak coordinates/IDs.

Useful optional additions:
- small FULL104 donor/source/operator-stratified RNA subset;
- promoter bridge files already available locally;
- new Claude exact-sampler/Phase-A receipts.

No protected outcomes are needed.

## 15. What becomes executable when paired data arrives

First:
1. validate pairing and schema;
2. define donor-disjoint TRAIN/VALIDATION/TEST without inspecting recoverability;
3. characterize measurement/missingness;
4. construct only a bounded development privileged factor;
5. run RNA recoverability versus simple activity/technical baselines;
6. test rotation-aware subspace stability;
7. preserve unrecoverable residual;
8. run availability-shortcut diagnostics.

No final biological threshold should be invented during that run.

## 16. Remaining hard dependencies

Before target tournament:
- Claude exact sampler must qualify;
- repaired Phase A must run and stop for audit;
- future Phase B must receive explicit authorization;
- empirical recoverability requires real paired data;
- promoter atlas execution requires actual source ingestion and provenance;
- matching operator requires common-support reconnaissance before freeze.

## Governance

TRAINING = OFF  
Phase B = STOPPED  
Stage 4 = NOT AUTHORIZED  
TD60 = BLOCKED  
Morabito = PROTECTED
