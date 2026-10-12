# Unified Synthetic Biology + Target-Discovery Rehearsal Design

Date: 2026-10-12  
Status: DESIGN ONLY — NO GENERATION, FITTING, SCORING, TARGET SELECTION OR TRAINING AUTHORITY  
Source lineage: PR #311 synthetic rare-biology work + PR #312 unified target-discovery architecture + PR #313 tournament executor framework

## 1. Purpose

Build one synthetic biological substrate that mirrors the downstream target-discovery and teacher/student pipeline proposed for real data, but with known planted biological truth.

The synthetic system is not a separate rare-biology dataset and is not a replacement for Q00–Q11. It is a higher-level biological simulator in which common, continuous, intermediate-frequency and rare biology coexist in the same donors/cells. Q00–Q11 remain immutable measurement/statistical qualification worlds and inform the observation layer only.

Primary objective:

> Qualify the target-discovery candidate system, target-portfolio convergence, rich-teacher/partial-RNA decomposition, shared-backbone versus specialist-head architecture, support/uncertainty behavior and learned-teacher continuity against known biological truth before exposing corresponding real biological outcomes.

## 2. Non-negotiable boundaries

1. **Q00–Q11 are immutable.** No regeneration, mutation, reseeding or retrofitting of their frozen realized bytes.
2. **Rare biology is cross-cutting.** It is a low-prevalence regime of the same latent biological factors used by common biology, not a separate dataset or target family.
3. **Source/operator/depth are observation processes, not causes of biology.** They may affect visibility, noise, support and measurement uncertainty, but cannot directly create the biological latent state.
4. **Synthetic truth does not become human biological truth.** STAT1-like/regulatory/context/perturbation amplitudes remain synthetic stress settings informed by real TRAIN calibration.
5. **Teacher evidence and student evidence remain distinct.** Privileged evidence can sharpen/expand a teacher state without implying student point-recoverability.
6. **Synthetic target-discovery rehearsal must mirror the real TD pipeline.** Candidate logic, dependency logic, falsifiers, donor-primary estimands, complementarity/interference tests, recoverability classes and continuity tests should be structurally aligned wherever scientifically appropriate.
7. **No architecture may be rescued by aggregate performance if a required biological block fails.** Block-level accountability is preserved.
8. **Measured zero, masked, structurally unmeasured and modality-absent states remain distinct.**
9. **No pathology enters synthetic design or qualification.**

## 3. Relationship to Q00–Q11

Q00–Q11 are retained as Layer 0: observation-model/statistical qualification.

They test gene-wise detection/positive-value behavior under depth, class, source, donor effects, structural support, sparse prevalence, positive tails, S174 imbalance and omitted-operator perturbation. They do not define a coherent multigene cell-state program.

The new unified simulator sits above them:

`latent biology -> observation operator -> RNA / ATAC / context / perturbation observations`

Observation operators should reuse the scientific lessons qualified by Q00–Q11:
- two-part detection + positive-value structure;
- depth and quadratic-depth dependence;
- class/source/donor structure where applicable;
- structural support and unmeasured-feature poisoning semantics;
- donor-held-out and same-donor replicate logic;
- technical pseudo-rarity and operator/source/depth shortcut challenges.

Q00–Q11 themselves remain separate frozen qualification artifacts.

## 4. Unified latent biological manifold

Each synthetic cell belongs to one common biological population and carries a structured latent state:

`Z_cell = Z_identity ⊕ Z_shared ⊕ Z_query ⊕ Z_rel ⊕ Z_regulatory ⊕ Z_context ⊕ Z_perturbation ⊕ support_bio ⊕ U_bio`

with donor-level and interaction terms.

### 4.1 Z_identity

Cell identity / broad lineage component. This creates ordinary biological heterogeneity and prevents target qualification from being dominated by planted challenge factors.

### 4.2 Z_shared — C1 analogue

Continuous shared/global biological programs present across the population with donor-level heterogeneity.

Requirements:
- continuous rather than binary-only;
- donor-recurrent directions;
- common, intermediate and tail realizations;
- no source identity as direct biological coordinate;
- sufficient dimensionality to test collapse, rotation/subspace equivalence and transfer.

### 4.3 Z_query — C3 analogue

Query-conditioned/local biological information.

Requirements:
- query identity is allowed to define which biological quantity is being asked about;
- student must not receive unsafe query value leakage;
- teacher may use rich same-cell evidence including the queried measurement where prospectively allowed;
- planted contextual signal must be separable from q-count-only, q-address-only, wrong-q and query-agnostic controls;
- include both true increment and null cases.

### 4.4 Z_rel — C2 analogue

Donor-recurrent broad/mesoscale relational geometry.

Requirements:
- true anchored ordering known from latent state;
- no requirement that absolute cross-source distances match;
- global/mesoscale positive cases;
- hard fine-locality negative case consistent with historical TD57C lesson;
- donor-held-out evaluation;
- exact ties represented as unresolved rather than forced.

### 4.5 Z_regulatory — C5 analogue and rare/common regulatory biology

A family of coherent multigene regulatory/state programs embedded inside the same population.

The existing STAT1-like module becomes one member of this family, not a separate world.

Requirements:
- donor-dependent activity/prevalence;
- continuous activity with a high-activity rare tail, not binary rarity only;
- common/intermediate/rare realizations in one population;
- at least one RNA-recoverable regulatory program;
- at least one predictable-but-stochastic program;
- at least one teacher-private multimodal program;
- matched technical pseudo-rarity generated through observation only;
- no causal-GRN claim from Stage75 topology.

### 4.6 Z_context

Context-sensitive and context-insensitive biology coexist.

Requirements:
- true physical/context neighborhood can alter selected latent programs;
- intrinsic-null programs do not benefit materially from context;
- shuffled/distant-neighbor controls exclude focal/adjacent leakage;
- context may be teacher-private or RNA-recoverable depending on prospectively planted class.

### 4.7 Z_perturbation

Matched intervention arms act on selected latent programs.

Requirements:
- actual response arm;
- matched null intervention;
- arm-balance and prevalence controls;
- perturbation effects can be common or rare;
- causal truth is synthetic only.

### 4.8 Donor hierarchy

Donor is the primary biological replication unit.

Requirements:
- donor-specific baseline biological state;
- donor-specific activity/prevalence for specialist programs;
- held-donor realizations with new donor effects;
- no raw-cell-count domination of scientific mass;
- source assignment after donor biology is generated.

## 5. Frequency is a regime, not a dataset

For every eligible biological block, realizations span frequency/activity regimes:
- common;
- intermediate;
- low-frequency/rare;
- extreme tail where useful as report-only stress.

Rarity is defined relative to activity/support within the same latent program and population. A rare regulatory state should share its biological program basis with non-rare realizations unless a separate specialist factor is explicitly planted.

The existing empirical STAT1 TRAIN calibration may inform donor recurrence and tail prevalence, but does not define a universal human prevalence constant.

## 6. Observation and modality layer

Latent biology is generated first. Observation comes second.

### 6.1 RNA

Generate RNA through a two-part observation model:
- structural support mask;
- detection process;
- positive-value process;
- depth / quadratic-depth effects;
- source-dependent observability and noise;
- donor effects;
- optional operator perturbations only as measurement stress.

### 6.2 Same-nucleus RNA+ATAC

RNA and ATAC are observations of the same synthetic nucleus.

ATAC may contain:
- redundant support for RNA biology;
- informative but stochastic increment;
- teacher-private regulatory increment.

Exact latent provenance is retained so recoverability class is known.

### 6.3 Separate-nucleus donor-level RNA/ATAC

RNA and ATAC nuclei are independently sampled from the same donor-level latent distribution. No fake cell pairing.

Evaluation is donor- or donor×cell-state-level only.

### 6.4 Spatial/context observation

Physical coordinates/neighborhoods are generated from the same cell population. Context-conditioned and intrinsic-null programs coexist.

### 6.5 Technical pseudo-rarity

Pseudo-rare cells are not separate worlds. They are cells in the same population whose unusual observed pattern is produced by measurement conditions/noise/support while biological rare-factor activity is absent.

## 7. Synthetic target-discovery tournament

The known-truth substrate must support the same candidate logic as real TD.

### 7.1 C1_SHARED_EMERGENT

Question: does the candidate recover the planted shared/global biological subspace while resisting source/operator/depth shortcuts and preserving both common and rare realizations?

### 7.2 C2_RELATIONAL_SHARED

Question: does the candidate preserve planted donor-recurrent broad/mesoscale relational order beyond shared-state performance?

C2 remains dependency-aware in the synthetic tournament: it should not be rewarded merely for having a relational head if the relational truth increment is absent.

### 7.3 C3_QUERY_MEASURED

Question: does the candidate recover true q-conditioned information beyond q scalar/address, wrong-q, query-agnostic and technical controls?

### 7.4 C6_SHARED_QUERY_COMPOSITE

Plant two prospectively declared classes:
- **C6-positive:** a true shared×query interaction/increment exists;
- **C6-null:** shared and query blocks exist but no additional fused increment exists.

A correct tournament must promote C6 only in the positive class and refuse automatic promotion in the null class.

### 7.5 C4_STRUCTURED_COMPOSITE

Similarly plant:
- **C4-positive:** an additional structured relational increment exists beyond C6 + C2 constituents;
- **C4-null:** no extra composite increment.

No constituent failure may be compensated by aggregate composite score.

### 7.6 C5_REGULATORY_SPECIALIST

Question: does the specialist recover planted regulatory biology without rescuing failure of all foundation blocks and without hallucinating teacher-private multimodal realization?

## 8. Candidate gate executor rehearsal

PR #313's real tournament framework is engineering-qualified but real biological decision executors remain unmaterialized.

The synthetic system will be used to qualify executor behavior against known truth before real outcome opening.

For every candidate×gate role:
1. define estimand prospectively;
2. define decision rule prospectively;
3. run positive, null, shortcut and NOT_ESTIMABLE synthetic fixtures;
4. require correct terminal behavior;
5. hash-bind executor, estimand and rule identities.

Synthetic numerical performance is not automatically copied as a real-human cutoff. The purpose is to prove implementation/estimand/falsifier logic, not to tune real outcomes.

## 9. Portfolio convergence rehearsal

After block-level qualification, run the same convergence questions as real TD:
- single qualified block;
- multiple complementary blocks;
- fused implementation preserving block accountability;
- specialist-augmented portfolio;
- no qualified portfolio.

Required joint tests:
- complementarity/non-redundancy;
- destructive interference;
- rare/common preservation;
- held-donor transfer;
- support/abstention calibration;
- no aggregate rescue of block failure.

## 10. Rich-teacher / partial-RNA student rehearsal

For every active biological block, privileged evidence is prospectively classified into:

1. **DETERMINISTIC_OR_HIGHLY_RECOVERABLE**  
   Student point target allowed.

2. **PREDICTABLE_BUT_STOCHASTIC**  
   Student distributional/uncertainty target; exact realization is not required.

3. **TEACHER_PRIVATE**  
   No deterministic point loss to the student. Student must express support/uncertainty/abstention.

4. **NOT_ESTIMABLE**  
   Remains unresolved.

Teacher family mirrors TD:
- T_SHARED_RNA;
- T_QUERY;
- T_RELATIONAL when active;
- T_REGULATORY_MULTIOME;
- T_CONTEXT_PRIVILEGED.

Where biology overlaps, teachers share a constrained biological core with evidence-specific adapters/heads.

## 11. Student architecture rehearsal

Default challenger:
- one full-capacity shared partial-RNA backbone;
- S_SHARED, S_QUERY, S_RELATIONAL, S_REGULATORY and S_SUPPORT_UNCERTAINTY heads.

Separate full students are challengers only and must be earned by:
- stable negative transfer/interference;
- incompatible lawful evidence interfaces;
- materially incompatible support/abstention geometry.

Forbidden default:
- half-capacity dual students;
- architecture zoo added simply because multiple target blocks exist.

## 12. EMA / learned-teacher continuity rehearsal

EMA is a stabilization mechanism, not biological truth.

Reuse the canonical successful-optimizer-step -> EMA update semantics.

After a bounded qualification-only teacher-learning phase, test continuity of every selected synthetic target block:
- shared-state fidelity;
- query-state fidelity;
- relational-order fidelity;
- regulatory common/rare fidelity;
- support/uncertainty separation;
- no destructive narrowing/collapse.

Relational continuity is the synthetic analogue of TD60. Other blocks receive their own block-specific continuity tests.

Classify failures as:
- **PRESERVATION FAILURE:** learned teacher loses planted biology;
- **INFERENCE LIMITATION:** teacher preserves biology, student cannot recover it from lawful evidence;
- **UNCERTAINTY FAILURE:** evidence is insufficient/stochastic but uncertainty or abstention is miscalibrated;
- **SHORTCUT FAILURE:** model predicts using source/operator/depth/query leakage rather than biology.

## 13. Transport rehearsal

Prospectively evaluate:
1. held donor;
2. held observation/operator regime;
3. held source-like acquisition regime;
4. held modality/technology simulation where lawful.

Biological novelty/support and measurement-domain OOD are reported separately.

## 14. Reuse of existing rare-biology work

The following PR #311 work is reusable as components, not as a separate dataset:
- empirical donor recurrence/tail calibration;
- STAT1-like multigene regulatory prototype;
- source-specific visibility/noise calibration;
- technical pseudo-rarity concept;
- same-nucleus versus separate-nucleus semantics;
- evidence/depth ladders;
- spatial true/shuffled/distant controls and repaired leakage guard;
- perturbation actual/null controls;
- teacher-private versus RNA-recoverable challenge logic.

Artifacts that describe these as separate rare biological worlds are retained as historical qualification evidence but are not the final unified biological architecture.

## 15. Development sequence

No implementation may mutate Q00–Q11.

Implementation should proceed in prospectively auditable stages:

1. **Truth schema + latent manifold** — no observation generation yet.
2. **Observation adapters** — RNA first, then same-nucleus ATAC, separate-nucleus ATAC, context and perturbation.
3. **Known-truth unit fixtures** — common, intermediate, rare, pseudo-rare, null and NOT_ESTIMABLE cases.
4. **Synthetic candidate tournament interface** — C1/C2/C3/C6/C4/C5 outputs and truth bindings.
5. **Gate-executor qualification harness** — positive/null/shortcut/NE fixtures.
6. **Portfolio convergence harness**.
7. **Rich-teacher/partial-RNA recoverability harness**.
8. **Student architecture interference comparison**.
9. **Bounded learned-EMA teacher continuity qualification**.
10. **Transport rehearsal**.

Every stage receives its own prospective contract/authority before any result can be used to alter the next stage's gates.

## 16. Success criteria

The unified synthetic program is ready to authorize model qualification only when:

- one biological population contains common + rare activity across the same target blocks;
- Q00–Q11 remain unchanged and separately auditable;
- source/operator/depth cannot create biological truth;
- technical pseudo-rarity coexists with true rarity in the same observed population;
- same-nucleus and separate-nucleus geometry are represented correctly;
- C1/C2/C3/C6/C4/C5 positive/null/dependency semantics can be rehearsed against known truth;
- block-level failures cannot be rescued by composite aggregate scores;
- recoverable/stochastic/private/NOT_ESTIMABLE classes are planted and auditable;
- shared-backbone interference and separate-student triggers can be tested;
- learned EMA teacher continuity can be adjudicated per block;
- held-donor/support/measurement transport can be tested;
- no pathology or protected real outcome is required.

## 17. Explicit non-claims

This design does not claim:
- any synthetic program is a validated human disease mechanism;
- STAT1 is the final target;
- Stage75/SCENIC is a causal GRN;
- ATAC/context/perturbation amplitudes are measured universal human effects;
- a synthetic gate threshold is automatically a valid real-data cutoff;
- any target portfolio, representation or architecture has already qualified;
- training is authorized.
