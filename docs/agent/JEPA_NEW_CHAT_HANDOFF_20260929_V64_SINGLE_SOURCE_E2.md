# JEPA NEW-CHAT HANDOFF — V64 SINGLE-SOURCE E2 / CONTINUOUS-ADJUSTMENT SUCCESSOR
Date: 2026-09-29
Status: CURRENT TAKEOVER DOCUMENT
Training: OFF
TD60: BLOCKED

## 0. Canonical starting point

Repository:
`dushyant-mishra/sea-ad-jepa-agent`

Current ChatGPT successor branch:
`chatgpt/v64-e2-single-source-successor-20260929`

Current tip:
`003ad549a158ebf44093d9771cb7c2aabd240d05`

Claude's active scientific branch / PR:
PR #198
`claude/v63-external-regulatory-qualification-20260929`

Claude authenticated Nott/Table-S5 head:
`e96d22854250cfb8938a876606011614a65f1856`

The ChatGPT V64 branch is exactly six commits ahead of `e96d2285` and adds governance/results/custody documentation only. It does NOT modify Claude's scientific source/tests/results.

Do NOT assume main is current.

## 1. Scientific objective

Build a JEPA-style representation-learning system for human brain single-cell/single-nucleus biology where:
- the teacher observes richer biological evidence;
- the student sees restricted evidence;
- the target is a query-conditioned biological cellular state.

The target is NOT:
- the hidden queried-gene scalar;
- a technical capture/QC score;
- donor/source/operator identity;
- a generic RNA embedding;
- a target recoverable through q leakage.

The intended production target combines:
1. recurrent cross-dataset RNA biological state;
2. independently constructed query-local regulatory evidence;
3. q-safe preprocessing;
4. explicit nuisance/adversarial qualification;
5. protected external validation.

## 2. Working rules / governance

These rules are controlling:
- preserve negative results;
- do not retune failed gates after seeing outcomes;
- do not lower M_MIN;
- do not rebuild nuisance arms quietly;
- distinguish theorem/design non-identifiability from empirical estimator failure;
- keep Morabito protected outcomes closed during design;
- no institutional DUA route unless user explicitly reverses prior decision;
- training remains OFF until target semantics, q-safety, biological specificity, and authority closure are all satisfied.

The user is a neurobiologist. Explain technical issues in biological language when useful, but maintain full audit precision.

## 3. RNA backbone state

Best RNA-only discovery object:
`DISCOVERY_CANDIDATE__SOURCE_BALANCED_COMMON_STATE_BACKBONE`

Construction:
- discovery matrix: 50k cells x 41,238 addresses;
- universal protein-coding genes across 42 operators: 15,758;
- equal covariance weighting across HVS / NPH52 / SEA-AD;
- source centering;
- common covariance eigendecomposition.

Evidence:
- top-4 A/B principal-angle mean cosine ~0.9951, min ~0.9907;
- donor-disjoint rank-4 mean cosine ~0.9869, min ~0.9613;
- held-out biology trace eta2 ~0.3895;
- source eta2 ~0.0363;
- donor after source+class ~0.1168;
- SEA-AD operator after class ~0.1361.

Interpretation:
This is strong recurrent RNA biology, but NOT a final target.

Important caveat:
source eta2 near zero is partly induced by centering and is not proof of biological deconfounding.

HVS/NPH52 operator/class are structurally aliased. SEA-AD operator conditional on class is cleaner.

## 4. q-safety remains unresolved for production

The discovery normalization included q in the library denominator.

Therefore the discovery backbone is not production q-safe.

Accepted production student preprocessing forms:
- `q_excluded_total__q_token_dropped`
- `fixed_reference__q_token_dropped`

Teacher q-blindness is a separate requirement.

Do not conflate:
- q leakage into student evidence;
- q dependence in teacher target construction.

No production training until both are physically tested.

## 5. Identifiability boundary

V48 established a semantic-twin boundary:
if allowed observables are byte-identical and only hidden interpretation changes, no RNA-only statistic can force biology PASS and semantic twin FAIL.

Status:
`NON_IDENTIFIABLE_BY_DESIGN`

Do not attempt to "beat" the semantic twin.

The response is to add independent biological observables and freeze nuisance classes prospectively.

## 6. Corces route — STOP

Public Corces GSE147672 H3K27ac HiChIP + scATAC was reconstructed successfully.

Technically valid contact object, but poor microglia substrate fit:
- microglia Cluster24 ranked 22/24;
- oligodendrocyte/OPC highest;
- doublet cluster 3rd;
- size control did not rescue.

Status:
STOP for target construction.

This is not evidence that microglial biology is absent.

Do not use Morabito to rescue Corces.

## 7. External-source state

### DS010
GSE308668 / GSE308906:
- embargoed until 2027-02-01;
- no public contact bytes now;
- approximately 20 donors x 3 regions;
- 59/60 possible microglia donor-region pseudobulk combinations represented in public metadata;
- all 20 donors represented.

Status:
`BLOCKED_BY_EMBARGO__NOT_BY_IMPUTATION`

Do not pursue DUA.

### Yang GSE173316
Public GEO series, but physical RAW tar inspection found only:
- 8 RSEM gene-expression outputs;
- 2 CRISPR count matrices;
- no pcHi-C interaction artifact.

Status:
`ARTIFACT_UNLOCATED`

Useful if the interaction artifact is later found, but not load-bearing now.

### Morabito GSE174367
18 shared donors, separate-nucleus RNA/ATAC.

Valuable later because it breaks same-nucleus quality confounding.

Protected target-state cis correspondence remains closed.

Prior exposure does NOT globally invalidate Morabito; exposure must be treated by outcome family.

### NIH-CARD
Paired RNA/ATAC substrate:
- 1,501,089 nuclei;
- 38,606 genes;
- exact barcode strings = 0 because ATAC repeats sample suffix;
- composite (sample, raw_barcode) = 1,501,089 1:1 matches;
- .X contains count-like uint16;
- raw/X is log-like float32;
- 87,384 microglia across 357 donors;
- median 217 microglia/donor;
- 167/357 donors <200; 45 <50;
- HBCC median microglia depth 157 vs NABEC 256.5;
- RNA covariates include Age, Sex, PMI, cohort, batch, Brain_bank, Race, Ancestry;
- ATAC carries cohort.

Keep NIH-CARD biological correspondence closed during design.

## 8. Synthetic specificity history

### Tournament v2
Primary full run:
- NULL LCB95 +0.03184 PASS
- TECH +0.00768 FAIL at M_MIN=.010
- GEO +0.01349 PASS
- ACC +0.02418 PASS
- ANCHOR +0.01852 PASS
- DONOR +0.03098 PASS
- held-out ambient +0.02987 generalises

Binding nuisance:
`NEG_TECH_2` latent capture correlated with target geometry.

Semantic twin:
identical to POS_BIO_1 to zero tolerance.
Correct classification:
`NON_IDENTIFIABLE_BY_DESIGN`

Common support under 5-bin matching:
- 146/960 linked retained = 15.2%;
- strongest retained-vs-discarded SMD: log-distance +0.346.

### Matching-granularity frontier
Result:
`NO_FEASIBLE_REGION_ON_THIS_FRONTIER`

Representative regimes failed TECH.
TECH-clearing regimes retained only 4.7% or 0.9% of links and were materially selected.

Licensed claim:
`NEG_TECH_2 = EMPIRICALLY_UNRESOLVED_WITHIN_CURRENT_OBSERVABLE_AND_ESTIMATOR_CLASS`

NOT theorem-level non-identifiability.

## 9. Continuous-adjustment breakthrough

Claude froze and executed one continuous-adjustment successor before inspecting its outcome.

Primary full result at Claude commit:
`c4e78de24049400a403f80770af86f5ac136b7dc`

Full donors=18 / seeds=24:

- NULL margin +0.03228 / LCB95 +0.03206 PASS
- TECH +0.01996 / +0.01948 PASS
- GEO +0.02556 / +0.02517 PASS
- ACC +0.03166 / +0.03031 PASS
- ANCHOR +0.03700 / +0.03578 PASS
- DONOR +0.03202 / +0.03161 PASS
- held-out ambient +0.03233 / +0.03174 generalises

Support:
- 960/960 linked scored;
- Kish ESS 935 = 97.4%;
- top-10% contribution share 0.128;
- residual geometry correlations <= |0.0066|;
- pre-adjustment linked-vs-control imbalance ~1.964 SMD.

Positive biology preserved:
- POS_BIO_1 +0.22825 vs previous +0.22976;
- POS_BIO_2 +0.03140 vs previous +0.03223.

Ablation:
replace fitted nuisance surface with training-fold mean, keep everything else fixed:
- NEG_TECH_2 +0.01185 -> +0.16990;
- TECH, GEO, ANCHOR collapse to failure;
- support remains broad.

Interpretation:
This is strong evidence that coarse matching, not intrinsic non-identifiability, caused the previous support-vs-TECH tradeoff for the represented nuisance surface.

Important limitation:
NEG_TECH_2 is close to the frozen model span because its nuisance geometry depends on degree and inverse distance, and the estimator includes those variables/interactions.

Therefore the result is a major project-specific statistical success, but not yet a universal robustness claim.

## 10. V64 statistical red-team successors

A separate ChatGPT branch was created:
`chatgpt/v64-parallel-successors-20260929`

It contains three prospectively frozen contracts:
1. depth-sensitivity leakage diagnostic;
2. out-of-span TECH stress;
3. Nott same-study substrate-fit contract.

These were not yet reconciled into the current single-source branch.

### Depth-sensitivity leakage diagnostic
Concern:
`rna_depth_sensitivity` and `atac_depth_sensitivity` are computed from the arm's observed signals and are therefore outcome-derived / potentially arm-dependent.

Required ablation:
remove only those two variables.
Do not retune anything.

If the pass survives, continuous-adjustment reading A is strengthened.
If the pass depends on them, do not promote the estimator until depth sensitivity is reconstructed independently.

### Out-of-span TECH stress
A single prospectively frozen nonlinear hidden-quality geometry was specified outside the present ridge span.

Do not add new basis terms after seeing the result.
Do not run an estimator tournament.

If out-of-span TECH fails while old families remain green:
limit the estimator claim to nuisance surfaces near the frozen model span.

## 11. Nott Table S5 — now authenticated

User supplied:
`NIHMS1066836-supplement-Table_S5.xlsx`

Authenticated by Claude at:
`e96d22854250cfb8938a876606011614a65f1856`

File:
- 36,876,140 bytes
- SHA-256:
  `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`

Microglia interactome:
- 104,802 interactions;
- 22 autosomes;
- zero trans rows;
- both anchors uniformly 5 kb.

Artifact-derived thresholds:
- FDR < 0.01;
- max FDR = 0.00999901918857552;
- all 104,802 rows satisfy the depositor threshold;
- observed cis span 10 kb–1 Mb;
- median span ~180 kb;
- anchor width 5 kb.

Genome build confirmed independently:
max chr1 end = 249,205,000.
This exceeds hg38 chr1 length 248,956,422 and is compatible with hg19 chr1 length 249,250,621.

Therefore hg19 -> hg38 liftover is required.

Same-study interactome comparators in Table S5:
- neuronal: 93,290 interactions;
- oligodendrocyte: 61,895;
- astrocytes have enhancer/promoter sheets but no interactome.

This makes same-study cell-type specificity controls possible without importing a cross-study batch effect.

## 12. Critical P1 contract gap — formally resolved

Original V63 C4/P1 required:
cross-source contact concordance > promoter-fixed distal shuffle before E2 construction.

But there is currently only one admissible contact source:
Nott.

DS010 is embargoed.
Yang interaction artifact is unlocated.
Kosoy is access-required/supporting-only.

Cross-cell-type agreement within Nott is NOT independent source replication and must never be relabelled as P1.

At the same time, V63 C1 explicitly allowed:
"if no second admissible source exists, build a Nott-centered object."

Therefore the original contract contained an internal contradiction.

ChatGPT created a formal successor:
`results/v64/V64_E2_SINGLE_SOURCE_SUCCESSOR_CONTRACT_V1.json`

Commit:
`3903e6d2cc137bf8e210350ab8c52322e8f4a5ed`

Ruling:
`P1_cross_source_contact_concordance = NOT_APPLICABLE_ON_SINGLE_SOURCE_PATH`

Explicitly NOT:
PASS.

Replacement:
`P1S_SINGLE_SOURCE_SUBSTRATE_QUALIFICATION`

The preliminary object is named:
`E2_NOTT_CANDIDATE`

It MUST NOT be called:
- independently replicated contact set;
- multi-source supported;
- causal enhancer-gene map.

Future independent-source concordance can later upgrade the claim.

## 13. Nott ATAC + liftover chains now authenticated

User supplied five additional files.

Authentication receipt:
`results/v64/V64_NOTT_ATAC_AND_CHAIN_AUTHENTICATION_RECEIPT_V1.json`

Commit:
`194f8a6aafc4fbf4ca3ceef12c87943b740fd505`

### Microglia ATAC
`formatted_output_PU1_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz`
- 841,467 bytes
- 50,199 rows
- MD5 `9fc7767d501a938f90c44caa25a2d68f`
- SHA-256 `7cadc9906dbf335e252c823a8f19da738b64c7c45692ab4abbb962e18971cf36`

### Neuron ATAC
`formatted_output_NeuN_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz`
- 943,524 bytes
- 55,932 rows
- MD5 `021f5f79663b653312674edba82d0333`
- SHA-256 `e5a094c69ef4d06338583c7d3fec5aced1e6b4fdf4e49a5d726c3e20d96299a4`

### Oligodendrocyte ATAC
`formatted_output_Olig2_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz`
- 655,864 bytes
- 38,476 rows
- MD5 `6b2c4ffe6b3231aad4c075865a59f6ed`
- SHA-256 `220db7ae656001e81dd9af84c0382c6d020c1b023ffdbd5abb231a61ba1b0922`

All three:
- 6-column FILER representation;
- zero malformed BED rows;
- lifted hg38 coordinates plus source-coordinate provenance.

### UCSC chain files
`hg19ToHg38.over.chain.gz`
- 227,698 bytes
- MD5 `35887f73fe5e2231656504d1f6430900`
- SHA-256 `5c0598e500ceb5a78c73086929e8ef993aec309bcafb595139b53d440b125a1d`

`hg38ToHg19.over.chain.gz`
- 1,246,411 bytes
- MD5 `ff3031d93792f4cbb86af44055efd903`
- SHA-256 `14a712e8e147d9fc8e9d87d51977b46f6f8ddb93efbe5d0843d86b6205f587b1`

No additional data are currently required for the Nott substrate-fit stage.

## 14. Current Nott execution path

The next biological execution is now mechanical:

1. Liftover all 104,802 Nott microglia interactions hg19 -> hg38.
2. Require both anchors to map appropriately.
3. Report attrition with the original 104,802 denominator.
4. Round-trip mapped anchors hg38 -> hg19 and report exact recovery fraction.
5. Execute P1S same-study substrate fit:
   - same microglia contact pairs against microglia ATAC;
   - same pairs against neuron ATAC;
   - same pairs against oligodendrocyte ATAC.
6. Run promoter-fixed distal shuffle preserving chromosome/promoter/distance structure.
7. Execute cell-type-negative eligibility:
   a neuron/oligodendrocyte edge is a valid negative only if target gene is expressed in microglia, distal substrate is accessible in microglia, and the relationship itself is absent from the microglia map.
8. Report trivial-negative attrition.
9. If P1S passes, instantiate:
   `E2_NOTT_CANDIDATE`

Do not inspect:
- Morabito protected target-state cis correspondence;
- NIH-CARD linked RNA-ATAC correspondence;
- JEPA target overlap;
- AD-risk enrichment as tuning objective
before the construction/fit stage is fixed and executed.

## 15. C6 matching rule is superseded for primary specificity

Original V63 C6 used coarsened exact matching.

The matching frontier demonstrated:
`NO_FEASIBLE_REGION_ON_THIS_FRONTIER`.

Therefore V64 successor retires coarsened exact matching as the PRIMARY specificity estimator.

It may remain a sensitivity analysis.

Primary correspondence should use the frozen continuous-adjustment lineage only after its V64 leakage/out-of-span qualification is resolved.

Do not silently trim to a tiny matched population and call it representative.

## 16. Data custody

Current custody manifest:
`docs/agent/V64_CHAT_RUNTIME_CUSTODY_MANIFEST_20260929.md`

The six newly acquired scientific binaries are HASH_ONLY in GitHub custody because the available connector cannot stream arbitrary local binary bytes directly into the repository.

The manifest records exact:
- file size;
- MD5;
- SHA-256;
- recovery URL where public;
- authentication state.

These include:
- Table S5;
- 3 Nott ATAC files;
- 2 chain files.

Any reacquired copy must match SHA-256 before use.

Prior large project archives/checkpoints are not duplicated because V46 already SHA-indexed them.

Archived chat-only text artifacts are under:
`docs/agent/archive/chat_runtime_20260929/`

## 17. Branch reconciliation warning

There are now TWO V64 ChatGPT successor branches with complementary content:

A. Current Nott/custody branch:
`chatgpt/v64-e2-single-source-successor-20260929`
tip `003ad549...`

Contains:
- E2 single-source successor ruling;
- Nott ATAC/chain authentication receipt;
- custody manifest;
- archived chat handoff/source artifacts.

B. Parallel statistical-contract branch:
`chatgpt/v64-parallel-successors-20260929`

Contains:
- depth-sensitivity leakage diagnostic;
- out-of-span TECH stress;
- Nott same-study substrate-fit contract.

Before execution, reconcile/cherry-pick the relevant frozen contracts onto ONE successor branch.
Do not rewrite their substance after seeing outcomes.

## 18. What is solved, provisional, and blocked

### Solved strongly enough to move forward
- source-balanced RNA backbone recurrence demonstrated;
- semantic-twin identifiability boundary understood;
- Corces ruled out for target construction;
- Nott Table S5 authenticated;
- Nott thresholds/build/comparators fixed by source artifact;
- three same-study ATAC tracks authenticated;
- both liftover chains authenticated;
- P1 single-source contract contradiction formally resolved;
- continuous adjustment broke the coarse matching support-vs-TECH tradeoff on the represented nuisance class.

### Provisional / needs red-team
- continuous-adjustment pass pending depth-sensitivity leakage ablation;
- generalisation beyond near-model-span geometry pending out-of-span TECH stress;
- Nott microglia substrate fit not yet executed;
- liftover/round-trip not yet executed;
- cell-type-negative eligibility not yet executed;
- E2_NOTT_CANDIDATE not yet instantiated;
- q-safe production preprocessing not yet physically closed.

### Blocked / intentionally deferred
- DS010 until 2027-02-01;
- Yang broad pcHi-C until artifact located;
- Morabito protected biological outcome until design closed;
- training / TD60 until all authority gates satisfied.

## 19. Immediate next actions for the new chat

Execute in this order:

### A. Reconcile V64 branches
Bring the three frozen parallel contracts onto the current V64 successor branch without changing their content.

### B. Run depth-sensitivity leakage diagnostic
Remove only:
- rna_depth_sensitivity
- atac_depth_sensitivity

Keep all else fixed.

If the continuous-adjustment pass depends on them, stop and prospectively redesign depth sensitivity.
If it survives, promote the current continuous estimator claim within represented nuisance scope.

### C. Run out-of-span TECH stress
Use the already frozen nonlinear nuisance.
Do not modify estimator basis.
Do not retune alpha.
Do not lower M_MIN.

### D. Run Nott liftover + round-trip
Use the authenticated chain files.
Report:
- attempted anchors/pairs;
- mapping successes/failures;
- chromosome changes;
- length changes;
- round-trip exact recovery.

### E. Run P1S Nott same-study substrate fit
Compare microglia contact support against:
- microglia ATAC;
- neuron ATAC;
- oligodendrocyte ATAC;
plus promoter-fixed distal shuffle.

No AD-gene or target-overlap rescue.

### F. Execute P3 cell-type negative eligibility
Discard trivial negatives and report attempted/retained counts.

### G. Instantiate E2_NOTT_CANDIDATE only if P1S + harmonisation + P3 pass

### H. Only then move toward NIH-CARD real correspondence
Keep Morabito closed until later protected validation.

### I. Rebuild/verify q-safe production student features before target promotion/training

## 20. Do not redo these historical dead ends

Do not:
- retry Corces as primary target substrate;
- reinterpret semantic twin as a benchmark bug;
- lower M_MIN from .010;
- relax anchor matching to make TECH pass;
- resurrect coarse matching as primary after the frontier result;
- silently rebuild donor nuisance arms again;
- call same-study cell-type concordance independent source replication;
- use AD loci/target genes to rescue Nott fit;
- use Morabito during target design;
- request DUA/controlled data;
- train before q-safety and authority closure.

## 21. Controlling scientific interpretation

The strongest current statement is:

The project has a recurrent cross-dataset RNA state and now has a plausible route to a query-local regulatory target using an authenticated primary-microglia Nott contact map.

The previous hidden-quality/support-collapse bottleneck was substantially solved for the represented synthetic nuisance class by continuous adjustment with almost complete support preservation, but model-misspecification and outcome-derived-depth-feature red-teams remain.

The next decisive scientific experiment is not another synthetic estimator tournament. It is:
1. close the two predeclared statistical red-team checks;
2. prove the Nott object is genuinely microglia-fit relative to same-study neuronal/oligodendrocyte controls and a geometry-preserving null;
3. instantiate E2_NOTT_CANDIDATE;
4. then test real regulatory correspondence in NIH-CARD under the frozen estimator;
5. preserve Morabito for later protected validation.

If these steps pass, the project will have crossed from recurrent RNA discovery into a genuinely independently constrained, query-specific biological target architecture.

