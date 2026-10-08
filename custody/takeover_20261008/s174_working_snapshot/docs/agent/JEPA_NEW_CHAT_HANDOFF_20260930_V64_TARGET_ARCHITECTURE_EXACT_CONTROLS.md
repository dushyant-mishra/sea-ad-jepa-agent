# JEPA New-Chat Handoff — V64 NIH-CARD exact controls, target coverage, and factorized target architecture

**Date:** 2026-09-30  
**Purpose:** audited takeover package for a new agent/chat.  
**Handoff branch:** `handoff/jepa-v64-target-architecture-20260930`

## 0. Read this first

This project is NOT at training.

Current hard governance:

- **TRAINING = OFF**
- **TD60 = BLOCKED**
- **Stage 4 biological correspondence = NOT AUTHORIZED**
- **Morabito protected validation = PROTECTED**
- Do not silently tune gates or simulator families after seeing outcomes.
- Do not encode NOT_MEASURED as numeric zero.
- Do not call multiple resources independent merely because their names/modalities differ.
- Preserve failed/superseded artifacts and negative results.

The central scientific objective is no longer “predict a hidden gene.” It is to learn a **query-conditioned biological cellular state** that remains meaningful across donors, datasets and measurement operators.

The strongest current architectural hypothesis is **factorized**, not a giant concatenated target:

- `Z_global(cell)`: recurrent global biological state, broad RNA coverage.
- `Z_query(cell,q)`: query-conditioned state beyond generic cell identity.
- `Z_reg(cell,q)`: local regulatory state where paired/regulatory evidence exists.
- `Z_response(cell,q/intervention)`: functional/perturbational response where available.

These factors may eventually share a representation only after their required invariances and biological consistency are demonstrated. This is a **hypothesis / tournament candidate**, not an implemented target.

---

## 1. Live branch state at handoff creation

### Canonical ChatGPT scientific/audit branch

`chatgpt/v64-e2-single-source-successor-20260929`

Verified head before creating this docs-only handoff branch:

`23255baaf81381d5c22c655a605642db27f2a173`

That commit contains the independent audit of the exact-control sampler completeness issue.

### Claude execution branch

`claude/v64-nihcard-realism-design-20260929`

Verified current head:

`fc3736d215c3d75eac9d31d181465771c2036503`

Latest Claude finding at that head: direct evidence that E2 anchoring and NIH-CARD RNA detectability share substantial expression/activity bias; resource count is therefore not evidence-independence count.

### Frozen historical Claude checkpoint

`claude/v64-nihcard-e2-design-20260929 @ 6d08386f`

Keep frozen. Do not fast-forward/delete it merely because newer lanes exist.

### Important divergence rule

Do NOT assume Claude head is canonical merely because it is newer.  
Do NOT overwrite canonical V2 contracts with same-named Claude design checkpoints.

Before continuing:

```bash
git fetch --all --prune
git show 23255baaf81381d5c22c655a605642db27f2a173 --stat
git show fc3736d215c3d75eac9d31d181465771c2036503 --stat
```

Audit the diff and preserve explicit supersession history.

---

## 2. Target-discovery history in one page

### Original problem

A hidden-gene scalar is not the desired JEPA target.

The project wants the student to predict **biological state**, not a noisy expression count.

### RNA relational backbone

A source-balanced common-state RNA backbone remains the broadest target substrate.

Historical discovery evidence included highly recurrent cross-source / donor-disjoint relational geometry. It is promising but not by itself enough to prove biological authority because RNA-only structure can be reproduced by hidden technical processes.

### Identifiability lesson

Synthetic work established an important negative result:

- measured technical confounding can be removed by adjustment;
- latent technical capture can closely mimic biological structure;
- semantic twins with identical allowed observables are non-identifiable by RNA-only statistics.

Therefore **RNA recurrence is necessary but not sufficient** to call the state biological.

### Current scientific response

Use multiple evidence types with distinct meaning:

- RNA recurrence → broad global state.
- Paired RNA+ATAC → broad regulatory measurement.
- Nott/E2 contacts → sparse external structural anchors.
- SCENIC+ / eGRN → inferred upstream regulatory mechanism.
- perturbation → functional/interventional evidence.
- separate cohorts/modalities → transport / replication evidence.

Do not treat these as interchangeable features. They are evidence about a latent biological object.

---

## 3. RNA backbone: status and caution

Historical broad state object:

`DISCOVERY_CANDIDATE__SOURCE_BALANCED_COMMON_STATE_BACKBONE`

Discovery object historically described as 50k cells × 41,238 addresses, with a universal protein-coding intersection across 42 operators.

Historical evidence:
- top-4 A/B principal-angle mean cosine ~0.9951;
- donor-disjoint rank-4 mean ~0.9869;
- held-out biological trace eta² ~0.3895;
- source eta² ~0.0363.

Do NOT convert the remembered “15,758 universal protein-coding genes” into a current FULL104 coverage denominator without locating the committed source artifact. Both ChatGPT and Claude searched and did not establish that denominator from current committed artifacts. A remembered number is not authority.

FULL104 scale remains approximately:
- 4,553,407 cells;
- 104 donors;
- 42 operators.

This is the broad training substrate, not the E2 edge count.

---

## 4. Query safety

Discovery normalization historically included q in the library denominator; that is not production-safe.

Accepted q-safe concepts:
- `q_excluded_total__q_token_dropped`
- `fixed_reference__q_token_dropped`

Teacher target dependence and student q-leakage are separate questions.

No production training until q-safety is physically qualified.

---

## 5. Nott / E2 regulatory substrate

Authenticated Nott Table S5 SHA-256:

`81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`

C3 exact-identity retained contacts:
- 102,701 / 104,802.
- zero identity violations under the qualified C3 object.

E2 candidate object:
- 20,709 edges;
- 5,253 genes;
- 7,390 promoter anchors;
- 22 autosomes.

Important: **20,709 is an edge count**, not cells, genes or donors.

E2 is currently best interpreted as a **candidate sparse regulatory anchor**, not the universal JEPA target.

---

## 6. E2 coverage now measured explicitly

Claude commit lineage culminating in the 2026-09-30 coverage work established:

- edges: 20,709
- genes: 5,253
- promoter anchors: 7,390
- edges/gene: median 2, p75 5, p95 13, max 68, mean 3.94
- promoters/gene: median 1, max 6
- 1,904 genes have >1 promoter
- NIH-CARD RNA universe: 38,606 genes
- 5,143 E2 genes resolve into NIH-CARD
- therefore 13.32% of the NIH-CARD gene universe has any E2 anchor

This demonstrates that E2 cannot be the universal target layer.

### Edge-mass concentration

Measured:
- top 1% of anchored genes: 8.4% of edge mass
- top 5%: 25.4%
- top 10%: 38.3%
- top 25%: 62.2%
- 1,725 genes have exactly one edge (32.8% of anchored genes) but only 8.3% of edges

Correct interpretation:
- **edge-summed losses** can be dominated by highly connected loci;
- gene-equal weighting is what neutralizes gene-degree dominance;
- if a future auxiliary loss uses edges, normalize hierarchically (gene → promoter → edge) or justify another prospective weighting.

No loss has been selected yet.

---

## 7. NIH-CARD authentication and pairing: CLOSED

Zenodo NIH-CARD exact files:

RNA:
- 1,501,089 × 38,606
- size 18,439,154,935
- MD5 `f628b17aab355f80b912e3c715543cbd`

ATAC:
- same nuclei × 521,217 peaks
- size 14,508,702,462
- MD5 `b71589e0033e391e2fe97c1ae3928a7f`

Microglia:
- 87,384 nuclei
- 357 donors
- 282 donors meet frozen ≥100-MG support threshold in recent Phase-A census

Pairing:
- exact 1,501,089 bijection using recovered RNA/ATAC naming transformation;
- R1b independently corroborated by barcode+sample namespace;
- independent depth witness over 200 permutations passed strongly.

Qualified pairing wording:

`PAIRING_KEY_RECOVERED_EXACTLY__INDEPENDENTLY_CORROBORATED__PIPELINE_LINEAGE_CIRCUMSTANTIAL`

Residual depositor/producer lineage caveat travels with same-nucleus claims.

---

## 8. NIH-CARD coverage ladder: broad regulatory measurement may be much larger than E2

Latest completed coverage results reported by Claude:

- NIH-CARD RNA universe: 38,606
- RNA-measurable in microglia: 17,063 (44.2%)
- Nott PU.1-active promoter genes: 10,884
- RNA-measurable ∩ PU.1-active: 9,848
- E2 anchored: 5,253
- E2 anchored ∩ RNA-measurable: 4,874 (92.8% of E2)
- RNA-measurable but unanchored: 12,189 (71.4% of RNA-measurable)
- 379 E2-anchored genes are not RNA-measurable in NIH-CARD microglia
- measurable ATAC peaks: 520,299 / 521,217 = 99.82%

Interpretation:
- ATAC measurement itself is not the dominant coverage bottleneck.
- RNA detection and promoter/regulatory-definition rules are stronger bottlenecks.
- NIH-CARD may support a much broader paired-regulatory layer than the E2 anchors.

However strict “Tier B” regulatory-measurable query coverage is not yet fully computed because Nott promoters require qualified hg19→hg38 mapping under frozen C3 semantics.

Do not report 9,848 as strict Tier-B truth; it is an upper-bound-like precursor until the required promoter mapping is completed.

---

## 9. Evidence independence: NEW, IMPORTANT, QUALIFIED AS ASSOCIATION

Claude `fc3736d2` measured a shared bias directly from outcome-blind column marginals.

Microglial RNA detection rate:

E2-anchored + RNA-measurable:
- n = 4,874
- median = 0.043
- p25 = 0.013
- p75 = 0.128

RNA-measurable but unanchored:
- n = 12,189
- median = 0.009
- p25 = 0.003
- p75 = 0.037

Median ratio: **4.92×**

Mann-Whitney reported p = 0.0 (numerical underflow / effectively extremely small; do not narrate as literally zero probability).

Within anchored genes:
- degree 1: n=1,567, median detection 0.030
- degree ≥10: n=417, median detection 0.168
- ratio 5.57×
- Mann-Whitney p = 3.376e-60

Scientific implication:

**Nott/E2 support + NIH-CARD measurability is not automatically two independent lines of evidence.**

Both preferentially resolve active/highly expressed/open-chromatin genes.

This does not mean either assay is “wrong.” It is a shared biological/measurement selection mechanism.

Therefore the future atlas needs two axes:
1. coverage;
2. evidence independence.

Resource count is not independence count.

---

## 10. Three evidence states are mandatory

Future target/teacher data model must distinguish:

1. **MEASURED_AND_SUPPORTS**
2. **MEASURED_AND_DOES_NOT_SUPPORT**
3. **NOT_MEASURED**

Never collapse states 2 and 3 to numeric zero.

P3 already provides a real example of state 2: expressed microglial genes with accessible distal structure but relationship absent from the qualified MG map.

Missingness itself is highly predictive because most genes are unanchored. A naïve zero-fill would create an availability shortcut.

---

## 11. Stage-3 Phase-A control construction: why it matters

Future NIH-CARD correspondence asks whether real E2 enhancer–gene pairs outperform fair controls.

Controls must preserve:
- same promoter;
- same chromosome;
- 5-kb interval width;
- source-hg19 distance within ±10% or 10 kb;
- promoter-specific exclusion of known E2 distal partners;
- exact C3 hg19→hg38→hg19 identity;
- hg38 Nott PU.1 overlap;
- hg38 NIH-CARD consensus-peak overlap;
- no rescue.

CONTROL_A determines primary eligibility.

CONTROL_B is an independent second draw used only for the control-vs-control null.

B never rescues A.

A/B are independent and allowed to coincide. Coincidence is recorded; never redraw merely to force difference.

---

## 12. Superseded Phase-A checkpoint

Claude `9ed92fff` reported 15,646 structurally supported linked rows after repairing two self-found bugs:
- bounded 40-draw control proposal bias;
- hg19-vs-hg38 PU.1 coordinate-space error.

That 15,646 result is **superseded diagnostic evidence**, not current authority.

Independent audit found additional issues:
- global rather than promoter-specific exclusions;
- missing exact C3 reverse round-trip;
- density-weighted side choice;
- missing second control draw;
- wrong anchor_frequency definition;
- grid/lattice search;
- incomplete provenance.

Do not reuse 15,646 as the current testable population.

---

## 13. Exact control sampler: current state

Rejected design checkpoint:
- Claude `a129ce5a` proposed bounded 512-draw rejection search.
- Critical audit: this measures “found within 512 attempts,” not “an admissible control exists.”

Mathematically, if k valid starts exist among N candidates:

`P(false not-found) = (1-k/N)^512`

No genome-wide PU.1 rate provides a per-edge lower bound on k/N.

Conditional on success, rejection sampling is uniform over valid starts; the defect is **false-negative edge classification**.

### Canonical exact strategy

Use exact interval algebra where mapping is provably affine/safe, then an exact supplement for everything else.

Latest Claude measurement:

Across 41,412 edge-sides:
- total band positions: 1,905,484,412
- covered by safe single-block interval algebra: 1,888,432,882 = 99.105%
- uncovered: 17,051,530 = 0.895%
- edge-sides with any uncovered position: 1,635 = 3.95%

Uncovered positions include:
- chain-block boundaries;
- chain gaps;
- inverted/query-minus-strand regions;
- any region not proven safe for the affine interior formula.

Forward-chain minus-strand omission discovered by Claude:
- 96,903,239 bp hg19 span on primary chromosomes
Reverse-chain analogous span:
- 201,464,858 bp

Therefore call the slow path **A_supplement**, not merely boundary.

Final required universe:

`A_exact = A_interior ∪ A_supplement`

- `A_interior`: exact affine interval algebra in proven-safe chain interiors.
- `A_supplement`: exhaustively enumerate all remaining finite candidate starts and send them through real liftOver v479 + ambiguity + exact length + exact reverse round-trip + hg38 PU.1 + NIH-CARD peak gates.

The 17.05M-start supplement is large but tractable and makes completeness exact rather than assumed.

---

## 14. Exact-sampler qualification still required before Phase-A rerun

Canonical frozen test contract:

`results/v64/V64_NIH_CARD_STAGE3_PHASE_A_EXACT_SAMPLER_TEST_CONTRACT_V1.json`

Required before full Phase A:
- deterministic fixtures;
- explicit boundary-crossing PASS fixture;
- boundary-crossing failure fixture;
- full 32 deterministic real edges × both sides;
- exact start-for-start equality versus brute-force liftOver;
- report non-empty comparison count to avoid vacuous all-empty PASS;
- uniformity chi-square at predeclared alpha;
- failure-path tests;
- chain-orientation coverage report.

Claude already found and corrected a vacuous test:
- first 2-edge test gave 0 vs 0 equality;
- widened 10 edges × 2 sides produced seven non-empty comparisons;
- all seven reported exact elementwise equality.

That is encouraging but **not the full frozen qualification**.

Current audit verdict remains:
- exact sampler not yet qualified;
- Phase-A rerun blocked pending supplement + full test suite.

---

## 15. Phase B / Stage 4 boundaries

Phase B is the first stage needing actual matrix-value reads for:
- promoter_activity;
- distal_accessibility.

It remains **STOPPED** until repaired Phase A is independently re-audited.

Part 3 empirical metacell precision also remains outstanding.

Stage 4 correspondence remains sealed:
- no E2 gene RNA × linked distal ATAC correlation;
- no linked-v-control correspondence Δ;
- no biological outcome opened.

---

## 16. Historical realism / nuisance qualification context

V63 continuous adjustment successfully separated several represented nuisance families with broad support.

Claude frozen red-team later showed:
- historical represented families passed;
- frozen nonlinear OUTSPAN_TECH failed.

Licensed interpretation:
- estimator can handle nuisance geometry in/near its represented basis;
- it is not universally robust to arbitrary hidden technical structure.

Do NOT add a post-hoc sin/tanh-like term to “fix” the outspan failure.

S45 remains open:
- NIH-CARD-realistic RNA/ATAC depth-sensitivity geometry.

S46 remains open:
- donor/metacell counts;
- sparsity;
- missingness;
- edge-specific donor support.

These require a separate prospective simulator successor after real outcome-blind ETL geometry is known.

---

## 17. Factorized target architecture: hypothesis, not implementation

Current best scientific hypothesis:

### Z_global(cell)
Broad recurrent RNA biological state.

### Z_query(cell,q)
Query-specific deviation/state beyond generic cell identity.

### Z_reg(cell,q)
Local regulatory state constrained where paired RNA+ATAC / regulatory evidence exists.

### Z_response(cell,q/intervention)
Functional state change under perturbation where intervention data exist.

Do NOT fuse automatically.

First demonstrate:
- which invariances are shared;
- which factors transport across donors/datasets/technologies;
- whether regulatory constraints add information beyond global RNA;
- whether response-state geometry aligns with perturbational evidence.

This is explicitly NOT “add every modality to the teacher.”

---

## 18. All-resource query-evidence atlas: next major scientific deliverable

After exact Phase A and its audit, elevate this to the main architecture task.

For every query gene, record separately:

### Coverage axes
- cells
- donors
- query genes
- regulatory relations
- datasets/modalities

### Evidence classes
Tier 0: broad RNA-state support  
Tier 1: paired regulatory measurement support  
Tier 2: external structural anchors (Nott/E2 etc.)  
Tier 3: convergent multimodal/network evidence  
Tier 4: functional perturbation evidence  
Tier 5: independent replication/protected validation

### Independence metadata
For every apparent convergence, record:
- shared donors?
- shared assay?
- shared activity/expression selection?
- shared chromatin accessibility input?
- shared inferred priors?
- shared gene-selection rule?
- truly independent perturbational or structural evidence?

A gene with five correlated observational resources is not automatically stronger than a gene with one orthogonal perturbation plus one independent structural anchor.

Also test whether Tier-3 convergence merely enriches for:
- high expression;
- high promoter activity;
- high degree;
- heavily studied genes.

---

## 19. Observation-operator / uncertainty architecture from historical chat-only file

The preserved `WSL execution issue.txt` contains valuable earlier architecture reasoning that remains relevant:

- technology should be modeled as an observation operator, not a free biological covariate;
- distinguish legitimate biological change from measurement realization;
- audit basis/subspace stability, not merely individual PCA axes;
- separate biological-evidence convergence from depth/measurement convergence;
- distinguish biological novelty from measurement OOD;
- keep donor biology from being automatically “corrected away”;
- hierarchical dataset→donor→cell sampling before production training;
- molecular ledger can remain fine-resolution escape hatch while the global state is an accountable low-dimensional coordinate system.

These are architectural context, not current authorization to implement new machinery.

---

## 20. Chat-runtime asset custody

Current audited custody file:

`chat_runtime_20260930/CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V2.json`

Important rules:
- hashes for binary assets do NOT mean bytes are in GitHub;
- oversized foundation archives remain external/local-only;
- GSE73721 is public and has an exact recovery script + hash;
- the two Nott Table S5 copies are byte-identical and not independent artifacts;
- checkpoint/foundation archives are historical and confer no current training authority.

The split-archive checksum CSV was repaired on the handoff branch to preserve its exact BOM/CRLF text representation.

---

## 21. What the next agent should do first

### A. Verify branch heads

1. Fetch canonical ChatGPT branch.
2. Fetch Claude branch.
3. Check whether Claude has advanced beyond `fc3736d2`.
4. Do not merge same-named contracts blindly.

### B. Finish exact sampler qualification

Audit/implement:
- `A_interior`
- `A_supplement`
- strand/gap/boundary handling
- exact cardinality
- uniform sampling
- full frozen test contract

Then rerun Phase A and STOP.

### C. Audit Phase-A funnel

Demand:
- exact 20,709 reconciliation;
- CONTROL_A primary population;
- CONTROL_B null population;
- promoter/gene counts;
- no opposite-side retry;
- no B rescue;
- exact C3 receipts;
- artifact and producer digest binding.

### D. Only after audit, allow Phase B

Then:
- promoter_activity;
- distal_accessibility;
- Part-3 metacell precision.

### E. Build all-resource evidence atlas

Do this before freezing final teacher/target architecture.

### F. Run factorized-target tournament

At minimum compare:
- H1 RNA relational state only;
- H2 RNA state + sparse regulatory anchor;
- H3 factorized multi-view query-conditioned latent with broad NIH-CARD regulatory supervision and orthogonal anchors.

No winner may be selected using the same outcome used to construct it without explicit development/validation reclassification.

---

## 22. Things explicitly NOT to do

- Do not reopen 15,646 as authoritative.
- Do not use the rejected 512-draw existence sampler.
- Do not use a proposal lattice to define control existence.
- Do not use global E2 distal exclusion for a promoter-specific control.
- Do not omit exact reverse liftOver.
- Do not count exact distal-start multiplicity as anchor_frequency.
- Do not let CONTROL_B rescue CONTROL_A.
- Do not force A and B to differ.
- Do not call a 0-vs-0 equality test adequate.
- Do not use remembered 15,758 as a FULL104 denominator without artifact authority.
- Do not call Nott + NIH-CARD independent merely because they are different datasets.
- Do not zero-fill NOT_MEASURED regulatory evidence.
- Do not add a modality simply because more modalities sound biologically richer.
- Do not open Morabito or Stage 4 casually.
- Do not enable training.

---

## 23. Current scientific bottom line

The project has moved from:

> predict a hidden gene

to:

> learn a query-conditioned biological state whose broad component is recurrent across millions of RNA cells and whose query-specific meaning is constrained by regulatory, structural, network, perturbational and independent evidence where those evidence types genuinely add new information.

E2 is now clearly a **sparse high-confidence anchor**, not a universal target.

NIH-CARD may provide much broader regulatory measurement coverage, but must not select and validate its own gene–regulatory relationships circularly.

The most important new lesson is that **coverage and evidence independence are different axes**. In this project's own data, E2 anchoring is strongly enriched for highly detectable genes, so a count of supporting resources can dramatically overstate independent biological support.

Finish the exact-control mechanics, then move the scientific center of gravity to the all-resource evidence atlas and factorized-target tournament.
