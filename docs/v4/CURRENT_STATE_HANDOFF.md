# SEA-AD MRA-JEPA v4 Current-State Handoff

## Repository Identity

- Repository: `dushyant-mishra/sea-ad-jepa-agent`
- Remote: `https://github.com/dushyant-mishra/sea-ad-jepa-agent.git`
- Checkpoint branch: `stage81a3-checkpoint-20260813`
- Checkpoint evidence base: `f1d07b6` (`Preserve Stage81A3 development evidence`)
- Canonical historical Stage81A2 freeze: `808ce4f170055c5568cc5c1e0e3a56415b52f908`
- Relationship: this branch adds an A3 development checkpoint without amending,
  replacing, or declaring a successor freeze to Stage81A2.

Resolve the exact branch tip with `git rev-parse HEAD`. The handoff cannot embed
its own commit SHA without creating a self-reference; the evidence-base SHA
above is the last scientific-evidence commit before this handoff update.

## Authority Labels

- **FROZEN:** human-approved historical contract that must not be rewritten.
- **VERIFIED:** reproduced or protected by current code, evidence, and tests.
- **PROVISIONAL:** supported development evidence that is not scientifically frozen.
- **LOCAL CANDIDATE:** useful local output not promoted to a governing decision.
- **SUPERSEDED:** retained history replaced by a later valid method or audit.
- **REJECTED:** tested route that failed its predeclared role or harmed retention.
- **OPEN BLOCKER:** unresolved issue that prevents the next scientific freeze.
- **NOT STARTED:** no authorized implementation or production run has begun.

## Stage State

| Stage or freeze | Status | Authority |
|---|---|---|
| Stage81A2 | FROZEN | Commit `808ce4f` and tracked A2 evidence |
| Stage81A3 | IN PROGRESS, NOT FROZEN | This development checkpoint |
| Freeze 1 | NOT DECLARED | Blocked by address-space and representation-resolution adjudication |
| Stage81B | NOT STARTED | No deterministic representation stage begun |
| Stage81C | NOT STARTED | No production foundation trajectory begun |
| Freeze 2 | NOT DECLARED | Downstream of Stage81C qualification |

## Frozen Stage81A2 Contract

- 13 foundation datasets and 36 matrices.
- 149 TRAIN, 19 DEV, and 19 SEALED donors; zero detected cross-split leakage.
- Freeze seed `8102`.
- Frozen vocabulary: 4,096 unique canonical genes.
- Vocabulary semantic hash:
  `f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb`.
- Vocabulary CSV file hash:
  `d8fbe2f0d2208f0034103443b6424169ff66e1b674769eda6b635c8ce84523e4`.
- Eligible canonical universe: 37,346 genes; ambiguous mapping records: 106,118;
  unresolved duplicate genes: 0.
- Normalization: `log(1 + 10000 * count_gene / total_cell_count)`.
- HVS: 24 partitions, 379,330 cells, 78 exact source donor identifiers.
- NPH: 957,659 source cells, 892,828 retained cells, and 64,831 cells with
  `missing_required_annotation`. Missing annotation is not a demonstrated QC
  failure, and those cells remain in source/audit accounting.
- GSE226602 and GSE226267 have 45 exact overlapping donors.
- No physical matrix merge, training shards, cloud upload, or model training.

The 78 exact HVS identifiers versus the publication description of 75 donors is
an unresolved provenance/documentation discrepancy. No authoritative alias
table supports merging the three additional identifiers.

## Stage81A3 Development Evidence

### Intrinsic representation lineage

The historically tested intrinsic contract is the token-preserving Molecular
Ledger over the frozen 4,096-gene address space, represented as 4,096 gene
tokens by 160 dimensions, with PCA160 as its qualified accountable global
summary. The
24-slot Perceiver compression route failed information-preservation gates and
is **SUPERSEDED**. It remains in history and tests only for forensic continuity.

The balanced reproducible cross-count REP160 basis was evaluated as a candidate
replacement. It was partial, added complexity, and did not earn replacement of
PCA160. Individual axes can rotate inside a stable subspace; coordinate-wise
biological claims therefore remain constrained. PCA160 remains valid evidence
about the tested architecture, but neither the per-gene token width nor the
global 160-D resolution is frozen or biologically privileged for the future
revision.

The IPB/learned CELL-token feasibility work was stopped after partial runs and
is not a completed qualification. Its protected report SHA-256 is
`aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308`.
The RLC-CD protected report SHA-256 is
`ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc`.

### Observation process and uncertainty

Technology is modeled conceptually as an observation operator, not an
unrestricted biological covariate. Physical acquisition facts may enter the
measurement stream, while donor, arbitrary dataset/matrix identity, and
pathology remain prohibited foundation inputs. The uncertainty ledger keeps
`U_BIO`, `U_MEAS`, `U_DOMAIN`, and `U_CONTEXT` distinct.

Trainable RBB/belief routes that degraded intrinsic retention are **REJECTED**.
Their negative evidence remains tracked. RBB covariance, recovery, panel, and
uncertainty-localization outputs are diagnostic and do not define the governing
foundation architecture.

### Rare-state chronology

Early matrix-balanced audits under-sampled several rare classes, and one OPC
comparison used unmatched cell subsets. Those apparent failures were audit
defects, not demonstrated architecture failures. Later deterministic,
donor-balanced paired-cell audits found no critical PCA160 loss in all 14
identifiable donor-recurring annotation-defined rare states. Microglia/PVM,
rare neuronal classes, and other tested families were adequate under that
bounded contract; REP160 showed no material advantage.

The separate pathology-blind, data-defined audit examined 4,001 bounded TRAIN
cells, found 105 candidates, 65 neighborhoods, and three donor-recurring
neighborhoods, but all three failed four-resample stability. Discovery was
`SATURATING`, not exhaustive. This chronology must not be collapsed into either
"rare biology solved" or "encoder failed."

### Context and UCDQ

Context remains read-only with respect to intrinsic molecular state. Physical
coordinates or experimentally grounded adjacency are required; expression-kNN
is not a physical-contact proxy, and iterative neighbor overwriting is
forbidden. ContextReader mechanics are verified, but mechanics qualification is
not empirical context benefit.

The original automated UCDQ applied one contract to 21 datasets and 234 samples.
It produced bounded/cross-donor/cross-technology identifiability of
`NO / PARTIAL_TARGETED_ONLY / NO` because SCP2167 provenance was `UNKNOWN`.
That original result and the incidental pre-audit pathology-field exposure are
preserved; pathology values were not used by the audited qualifier.

Following explicit human authorization, the primary publication was used to
adjudicate SCP2167 from `UNKNOWN` to `NEUROTYPICAL_DECLARED`. The unchanged
contract then classified SCP2167 as `CORE_SAME_ENTITY_BROAD_CONTEXT`, with five
eligible Fang STG MERFISH experiments supplying directly measured replication.
Post-adjudication identifiability is `YES / YES / YES`. This means a bounded real
context-value experiment is identifiable. It does **not** mean context benefit
was demonstrated: no context experiment, model training, optimizer update, or
architecture change occurred. Five Fang MTG experiments remain quarantined for
surgical-provenance review.

Known acquired spatial resources include MTG MERFISH, HIP/MEC MERSCOPE, Caudate
Xenium, SCP2167 Slide-tags, and Fang MERFISH assets. Their panel sizes and exact
eligibility are governed by the tracked UCDQ tables, not by approximate prose.
External context assets establish future testability only and do not enter
Stage81C foundation training.

## Chronological Stage81A3 Audit Ledger

The detailed chronology is preserved in
`docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md`. The ordered
interpretation is:

1. Visibility, tokenization, predictor, primary JEPA-loss, gradient-firewall,
   checkpoint, and telemetry mechanics were validated with synthetic fixtures.
   These were mechanics checks, not biological validation or production-policy
   freezes.
2. A bounded pathology-blind real-RNA forward smoke verified normalization,
   vocabulary order, exact-count masking, finite CUDA execution, and input
   firewalls. Its untrained pooled geometry was narrow, which triggered a
   forensic initialization audit rather than a claim of training collapse.
3. Synthetic geometry-escape runs and a faster-EMA matched rerun remained
   trapped. The exact failed-trajectory replay localized retained information
   in full gene tokens but ineffective near-uniform token-to-slot routing.
4. A forward-only attention-logit-scale intervention showed that learned Q/K
   rankings contained useful factor information, but pooled readout remained
   inadequate. It diagnosed a bottleneck; it did not create a production model.
5. The final 24-slot information-preservation qualification failed its gates.
   The subsequent learned CELL-token IPB candidate was stopped after partial
   trajectories and is protected as incomplete evidence.
6. The full-vocabulary RLC-CD probe found linear completion matched or beat the
   neural route. Conditional-predictability work found the 60/40 target largely
   unidentifiable, motivating uncertainty audits rather than stronger claims.
7. The reproducible-state and RBB sequence tested correlated Gaussian belief,
   out-of-fold covariance, adaptive correlation, frozen-encoder recovery,
   structural-panel exposure, and uncertainty localization. Several runs were
   informative, including confirmed gradient interference, but correlated or
   trainable belief machinery did not earn a governing foundation role. A
   numerical failure remains recorded as a failure rather than retroactive pass.
8. Foundation heterogeneity and FBSDQ then established the shared observation
   contract, PCA160/REP160 comparison, measurement-domain accounting, and
   source-balanced pathology-blind diagnostics. This is the direct parent of
   the later rare-state and context qualification work.
9. Rare-state audits progressed from under-sampled intermediate results to
   paired donor-balanced annotation-defined resolution, followed by a separate
   data-defined completeness audit whose recurring neighborhoods were unstable.
10. Public context acquisition, uniform UCDQ, and the explicitly authorized
    SCP2167 publication adjudication established that a real context experiment
    is identifiable, while leaving empirical context benefit untested.

Later valid audits supersede earlier audit defects, but negative and stopped
routes remain preserved. None of these steps declares Stage81A3 complete.

## Rejected and Superseded Routes

- 24-slot Perceiver compression as the governing intrinsic representation:
  **SUPERSEDED after failed information-preservation gates**.
- REP160 as a replacement for PCA160: **NOT EARNED**.
- Trainable RBB/belief routes that harmed intrinsic retention: **REJECTED**.
- Graph-first or Graph-JEPA intrinsic foundation interpretation: **REJECTED as
  governing v4A architecture**; historical graph evidence remains downstream.
- Context that overwrites intrinsic state: **FORBIDDEN**.
- Expression-kNN as physical adjacency: **FORBIDDEN**.
- Unrestricted donor/dataset/matrix identity or pathology as foundation input:
  **FORBIDDEN**.
- Claims that motif, graph, spatial, or perturbation evidence alone proves a
  causal regulator or validated GRN: **FORBIDDEN**.

## Open Blockers

### 1. Biological address space versus the 4,096 cap

This is the next scientific/governance blocker. Stage81A2 configured a target
vocabulary size of 4,096 and selected the top-ranked eligible genes. The number
was a computational capacity choice, not a transcriptome-derived biological
saturation result. Cross-family support and ranking can disadvantage rare,
lineage-specific, regulatory, receptor, ion-channel, neuropeptide, lncRNA, and
other specialized biology.

Stage81A2 remains immutable historical evidence. Before Freeze 1, a versioned
Stage81A2 revision must forensically design and qualify a maximal exact-gene or
full-transcriptome biological address space that is separate from tile/batch
capacity. No such revision has started, and this checkpoint does not choose its
size or implementation.

### 2. Independent representation-capacity and resolution assumptions

The number 160 currently has two biologically distinct roles and must not be
treated as one constraint:

- `d_gene = 160` is the learned contextual width of each Molecular Ledger gene
  token. It is an architecture-capacity parameter, not a biological vocabulary
  limit. A larger gene address space adds gene tokens; it does not require
  squeezing all genes into one 160-D vector. Its sufficiency after the future
  transcriptome revision is unresolved.
- `d_cell = 160` in PCA160 is a whole-cell compression bottleneck. It is a
  derived coordinate view, not the complete molecular identity of a cell.

Future design must independently parameterize `G` (biological gene address
space), `d_gene` (per-gene contextual capacity), and `d_cell` (global-state
resolution). The canonical Molecular Ledger should retain explicit gene
identity, observed expression, and measured/unmeasured state in addition to any
learned contextual vector. Global state should be treated as a resolution
question, potentially with nested or multiresolution summaries if no defensible
saturation emerges. Replacing 160 with another arbitrary fixed number would not
resolve the scientific issue.

No width change, sweep, evidence regeneration, or historical reinterpretation
was performed in this checkpoint.

### 3. HVS donor-count discrepancy

The source contains 78 exact identifiers while the publication describes 75
donors. Preserve all 78 until authoritative alias evidence exists.

### 4. Remaining context provenance

SCP2167 publication adjudication is complete in this checkpoint, but Fang MTG
surgical provenance remains quarantined. That quarantine does not invalidate
the eligible SCP2167/Fang STG identifiability result.

### 5. Local-only reproducibility dependencies

Source data, downloaded context assets, R-derived caches, model/checkpoint
binaries, and oversized detail tables remain outside Git. Their policies and
hashes are documented in `docs/v4/STAGE81A3_LOCAL_ONLY_ARTIFACTS.md`,
`results/v4/stage81a3_local_only_artifact_manifest.csv`, and the Stage81A1
acquisition manifests. Pytest basetemp directories and `.tmp/` browser/download
diagnostics are reconstructible scratch, not evidence authority.

### 6. WSL/R execution

The project path in WSL is `/mnt/d/Jepa project`. The established R command for
NPH cache work is
`/home/dushyant_mishra/miniconda3/envs/stage81a1d-r-audit/bin/Rscript`.
The A2 documentation records exact cache-generation commands. No unresolved
scientific failure is inferred from Windows being unable to execute that WSL R
environment directly. Current Python tests do not require rerunning the frozen
R cache builders.

## Data-Access Firewall

- DEV RNA: closed and not opened by this checkpoint.
- SEALED RNA: closed and not opened by this checkpoint.
- Pathology as a foundation input: closed and not used.
- Context training before the appropriate freeze: prohibited.
- Stage81B: not started.
- Stage81C: not started.

## Reproduction Environment

- Principal Windows environment: `sea-ad-jepa-v3`.
- Full deterministic v4 test command:
  `conda run -n sea-ad-jepa-v3 python -m pytest -q tests/v4 --basetemp results/v4/.pytest-stage81a3-checkpoint-final`
- Python syntax check:
  `conda run -n sea-ad-jepa-v3 python -m compileall -q src/sea_ad_jepa/v4 scripts/v4 tests/v4`
- WSL project path: `/mnt/d/Jepa project`.
- NPH R environment: `stage81a1d-r-audit` at the absolute WSL path above.
- Frozen A2 cache/audit commands are in
  `docs/v4/STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md`.
- A3 audit commands and chronology are in
  `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md`.

## Exact Next Scientific Decision

Re-establish the intrinsic representation under a versioned maximal-exact-
transcriptome data contract while independently qualifying per-gene contextual
capacity and global-state resolution, without imposing arbitrary biological
top-K or fixed-dimension assumptions and while preserving Stage81A2 unchanged.
