# V50 provisional framework — regulatory triangulation, causal support, and FULL104 transport

**Date:** 2026-09-28  
**Status:** `PROVISIONAL_SCIENTIFIC_DESIGN__MUST_BE_RED_TEAMED`  
**Base:** PR #178 @ `5d49a970030fc7e783b822437ac4761b3f9e4865`  
**TRAINING:** OFF

This document is intentionally **not an authority artifact**. Claude or another reviewer is expected to reopen the science, challenge every assumption below, and replace this framework if a stronger design exists. What must remain auditable is provenance, outcome exposure, and the distinction between development evidence and confirmation.

## 1. Central correction

The biological-identification problem must not be reduced to RNA-versus-ATAC concordance.

The project already contains:
- reproducible RNA relational geometry from TD56–TD59;
- same-assay identifiability failures from V47/V48;
- authenticated historical regulatory/SCENIC+/cisTarget work;
- an unused independent Morabito ATAC matrix;
- paired-Multiome cohorts;
- perturbational datasets with extensive reliability audits;
- public SEA-AD spatial modalities;
- source/readout/provenance and exposure ledgers.

The stronger strategy is therefore a **mechanistic triangulation graph**:

```
FULL104 relational RNA state
        |
        v
external regulatory architecture
(TF -> region -> target/eRegulon)
        |
        +-------------------+
        |                   |
        v                   v
direct chromatin       perturbational consequences
        |                   |
        +---------+---------+
                  |
                  v
          spatial/tissue context
                  |
                  v
        cross-cohort/source transport
                  |
                  v
        JEPA teacher/student continuity
```

No single arrow proves biology. The strength comes from evidence sources with **different failure modes**.

## 2. The claims must be separated

The project should stop using one binary "target qualified" concept for several distinct scientific questions.

### C0 — relational RNA structure exists
Historical evidence: TD56S, TD57B, TD58S, TD59.

What survives:
- disjoint-gene relational geometry recurs;
- donor-recurrent mesoscale order exists;
- partial evidence can recover part of it.

What does not follow:
- biological specificity.

### C1 — measured same-assay nuisance is insufficient to explain it
Historical V47/V48 evidence shows measured-QC technical state can be removed in the tested statistic.

What remains:
- unobserved same-assay latent technical state is non-identifiable under a semantic-twin construction.

### C2 — an independently learned regulatory architecture exists
Open claim.

Preferred development source: an external paired-Multiome cohort such as GSE214979, with diagnosis/pathology removed from method development.

The object is not a ten-TF Stage75F shortlist. It should be a broader, donor-stable enhancer-driven regulatory architecture, potentially using SCENIC+ or a competing method after red-team.

SCENIC+ is appropriate as a candidate because it explicitly models TF -> regulatory region -> target-gene relationships from RNA+ATAC, but its eRegulons are **candidate GRNs, not causal truth**. The original paper itself benchmarks enhancer/TF/target predictions and discusses limitations in enhancer-gene validation and perturbation prediction:
https://www.nature.com/articles/s41592-023-01938-4

### C3 — the FULL104-defined state has independent chromatin support
Open claim.

This should not be implemented as generic manifold alignment or a joint latent whose objective already forces RNA and ATAC together.

The strongest version is:
- regulatory architecture defined outside FULL104;
- chromatin activity measured directly;
- prediction/association tested within donor and across held-out donors;
- state object defined independently from ATAC.

SEA-AD MTG supplies independent **measurement modality** evidence but is not a pristine independent RNA discovery cohort because SEA-AD contributed to FULL104 target discovery.

### C4 — the regulatory relationship survives exact-nucleus independence
Open claim.

Morabito is valuable precisely because RNA and ATAC are from **different nuclei** of the same brains/donors. If a relationship recurs there, a same-nucleus quality artifact becomes less plausible.

### C5 — qualified perturbation changes the predicted regulatory/state program
Open causal-support claim.

Only perturbations with authenticated identity, demonstrated/estimable engagement, appropriate independent units, and an exposure-safe outcome may enter this claim.

### C6 — the state/regulatory program recurs in intact tissue
Open claim.

SEA-AD MERFISH/Xenium/spatial assets may help attack the extraction/dissociation/handling nuisance class, subject to a separate access/identity/panel audit.

### C7 — the anchored RNA state transports across FULL104
Open after C2–C6 provide sufficient biological anchoring.

Transport is not new multimodal validation. It asks whether the already-anchored RNA object recurs across all 104 donors and the three FULL104 source cohorts.

### C8 — a lawful JEPA teacher/student preserves the anchored state
Downstream only.

TD60 successor and any scientific training remain blocked until the biological state is sufficiently qualified and q-safe mechanics are closed.

## 3. Independence is multidimensional, not a ladder

Do not rank evidence simply as "same-nucleus > donor-level > RNA-only".

Each source should be described along independent axes:

- **unit independence:** same nucleus / separate nucleus / donor / cohort;
- **assay independence:** RNA / ATAC / perturbation / spatial / genetics;
- **cohort-lab independence:** internal source vs external laboratory;
- **feature-definition independence:** whether the hypothesis/network was defined using the outcome source;
- **technical-environment independence:** same extraction/library versus different pipeline;
- **causal direction:** observational versus intervention;
- **tissue-context independence:** dissociated/nuclear versus intact spatial tissue;
- **outcome exposure:** unopened / development-exposed / historically exposed / confirmatory-eligible;
- **population scope:** cells, donors, regions, lineages.

The correct question is not "which evidence is strongest?" but:
**which alternative explanation does this evidence remove, and which does it still share?**

## 4. Historical regulatory evidence — what can and cannot be reused

### Stage73 / Stage73R
PR #178 and PR #164 preserve the correction:
- original shuffled-graph controls were structurally identical because of a mode-label bug;
- Stage73R repaired the control;
- the real graph did not establish an advantage over its shuffled control.

Permanent rule:
**every structural negative control must prove physical distinctness** using adjacency/content digests, changed-edge fraction, correlation/invariants, and a planted identical-control failure.

A label saying "shuffled" is not evidence that a graph changed.

### Stage75F
PR #164 authenticated the Stage75F source chain and bounded its meaning:
- 10 regulators;
- 96 TF-target rows;
- a highly restricted motif-screened hypothesis package;
- not a validated eRegulon network;
- not causal evidence.

Critically:
- Stage75F candidate TF-target edges were derived from the same Morabito RNA pseudobulk;
- therefore they cannot be an independent answer key for an RNA-based state.

What can be reused:
- historical hypotheses;
- authenticated source/resource chain;
- control lessons;
- motif/cisTarget infrastructure.

What cannot be reused as truth:
- Tier A/B/C as validated regulatory strength;
- candidate edges as independent validation;
- historical negative-gate labels as causal negatives.

### PR #179 — incomplete SCENIC+ recovery
PR #179 is explicitly `INCOMPLETE_STOPPED`. No number/result on that branch is citable.

However, its intended audit identifies a valid required control:
**TF-specific motif support must be tested against annotation-supply and TF-label permutation.**

A TF must not appear "supported" merely because more motifs in the collection are annotated to that TF or because all TF batches analyze nearly the same regulatory region set.

### PR #175 — broad external coverage
PR #175 materially changes the feasible scope:
- all 41,238 canonical FULL104 addresses were individually resolved against Morabito;
- 37,966 addresses were reported eligible for donor-level matched RNA/ATAC analysis;
- Stage75F's 10 TFs are all measured/detected with promoter accessibility;
- the targeted manifold panel has broad external coverage, with PLCG2 explicitly absent from the FULL104 canonical registry.

Therefore a new regulatory analysis should **not** be restricted to the historical ten TFs.

## 5. Proposed regulatory-development architecture

### Development cohort
Use an external paired-Multiome cohort, provisionally GSE214979, to infer a broader microglial regulatory architecture.

Do not use AD/control/pathology to define or tune the network.

Potential outputs:
- TF -> region links;
- region -> target links;
- eRegulons;
- region and target-gene enrichment/activity scores;
- donor-stability measures.

### Required stability/audit controls
At minimum:
1. leave-donor-out or donor-bootstrap stability;
2. TF-label / motif-annotation-supply control;
3. region-gene link permutation matched on chromosome, distance/TSS class, accessibility and detection;
4. cell/nucleus pairing permutation where relevant;
5. donor-fingerprint negative;
6. structural-distinctness proof for every graph/control;
7. broad-cell-class confounding check;
8. within-microglia/fine-state analysis separated from trivial neuron-vs-glia identity.

### Role of historical Stage75F
After the new external regulatory architecture is frozen:
- ask whether historical TFs/edges recur;
- report recurrence as historical convergence;
- do not force them into the new network;
- do not tune the network to recover them.

## 6. Cross-modal confirmation roles

### SEA-AD public exact pairing
Current completed A/F result:
- 66,288 exact public RNA-ATAC paired nuclei overall;
- MTG only;
- 16 donors overall;
- 1,594 candidate-myeloid paired nuclei across 15 donors.

Role:
**internal independent-modality mechanistic support**, not pristine independent cohort validation.

Use donor-wise inference. Thousands of nuclei improve each donor estimate but do not create thousands of independent biological replicates.

### GSE214979
If used to build the regulatory architecture, label it:
`REGULATORY_DEVELOPMENT_EXPOSED`.

Do not also present the same data as primary independent confirmation of that network.

Internal donor holdouts remain useful, but the main confirmation should come elsewhere.

### GSE272082
Potential independent same-nucleus replication after minimal acquisition/authentication.

Its nine donors are nine biological units; multiple region libraries do not become independent people.

### Morabito GSE174367
PR #164:
- 18 shared RNA/ATAC donors;
- no FULL104 donor overlap;
- no same-cell pairing;
- authenticated independent ATAC matrix unused by Stage75F.

Role:
**separate-nucleus donor-level regulatory replication**.

This is not weaker or stronger than same-nucleus data in one dimension; it breaks a different confound.

## 7. Perturbation axis

Perturbation is the most important source of information that can break some observational semantic-twin explanations, but only when the experiment itself is qualified.

### GSE301119
PR #77:
- robust target-engagement direction in CRISPRi/CRISPRa;
- two independent donors;
- primary human macrophage, not microglia.

Role:
auxiliary myeloid causal-support test for overlapping regulators/programs, with lineage limitation explicit.

### GSE289721
PR #158:
- six-target microglial CRISPRi design;
- two independent differentiations, one genetic background;
- complete guide sequences;
- engagement measurable but not yet qualified;
- INPP5D overlaps prior training/development exposure and must be handled separately;
- five cleaner external targets are available if gates pass.

Role:
potential high-value microglial perturbational support **after** engagement/control gates.

### CRISPRbrain iTF/iPSC pair
PR #137:
- not acceptable as benchmark truth;
- joint engagement only 1/31;
- profile concordance near chance;
- not independent replication.

Role:
do not use as causal truth.
Potentially useful as a **noise/adversarial negative**: a method that reproduces these screens too closely may be fitting unreliable response structure.

### GSE178317
PR #114:
same-experiment development evidence, not independent biological replication.

Do not promote its retrospective concordance to external confirmation.

### Perturbation governance
PR #84 supplies target-held-out benchmark mechanics.
PR #90 supplies the append-only outcome exposure ledger.

The new framework should reuse these governance patterns rather than creating a second exposure system.

## 8. Spatial axis

SEA-AD publicly exposes spatial resources including MERFISH/Xenium according to the V49 modality inventory.

No spatial biological claim is currently qualified in this framework.

Potential role:
- intact-tissue recurrence of frozen RNA/regulatory programs;
- anatomical/neighborhood coherence;
- attack the dissociation/nucleus-extraction component of the handling/exAM nuisance.

Before use, perform a dedicated audit:
- exact regions/donors;
- microglial support;
- gene panel support;
- cell-type mapping;
- whether donors overlap FULL104;
- whether outcome/pathology fields are present;
- whether the relevant spatial readouts have been previously exposed.

Spatial evidence does not automatically solve postmortem or donor-level confounding.

## 9. Nuisance map

The cross-modal/regulatory framework should explicitly attack:

### N0 — independence
No shared biological or technical structure.

### N1 — measured QC
Shared state fully captured by measured RNA/ATAC QC.

### N2A — hidden nucleus quality
Unobserved quality/capture latent affects both modalities.

### N2B — handling/exAM-like state
Handling induces apparent activation/homeostatic loss and chromatin changes not captured by PMI.

### N2C — donor fingerprint
Donor-specific technical state appears in both modalities but there is no within-donor fine-state correspondence.

### N2D — broad cell-class identity
A statistic appears successful because neurons, glia, etc. are trivially separable in both assays.

### N2E — motif/annotation supply
TF support reflects database annotation density rather than TF-specific regulatory structure.

### N2F — structurally ineffective control
A shuffled/permuted control is accidentally identical or nearly identical to the real object.

### N2G — source/lab fingerprint
A relationship is reproducible only within one assay pipeline or cohort.

### N2H — feature-support artifact
A state appears absent because genes/features are structurally unmeasured or unavailable, especially in NPH52 or snRNA-depleted programs.

Every claimed qualification must state exactly which nuisance classes were tested and which remain possible.

## 10. Proposed evidence sequence

Do not expose all biological datasets at once.

### Phase A — reconstruct/audit
1. Build the complete evidence/independence ledger.
2. Finish or supersede PR #179's control questions without treating its partial output as evidence.
3. Audit spatial assets.
4. Create regulatory-exposure states analogous to PR #90.

### Phase B — regulatory development
5. Build an external regulatory architecture from GSE214979 or a better external cohort after audit.
6. Red-team donor stability, annotation supply, graph distinctness and broad-class confounding.
7. Freeze a first regulatory model/version.

### Phase C — internal mechanistic anchor
8. Apply the frozen external regulatory model to SEA-AD MTG ATAC.
9. Test whether chromatin-derived regulatory activity predicts/organizes the already-defined RNA state within held-out donors.
10. Label this INTERNAL_INDEPENDENT_MODALITY, not independent cohort confirmation.

### Phase D — external replication
11. Test GSE272082 if qualified.
12. Test Morabito at donor x microglia level using separate nuclei.
13. Keep each dataset separate; do not pool cells into an inflated n.

### Phase E — perturbational support
14. Intersect the frozen regulatory network with qualified perturbation targets.
15. Freeze expected downstream/regulon/state displacement before opening eligible outcomes.
16. Execute only where engagement, independent unit and exposure gates pass.

### Phase F — spatial support
17. Project frozen RNA/regulatory programs into spatial data where gene support permits.
18. Test intact-tissue recurrence and spatial organization without tuning on pathology.

### Phase G — FULL104 transport
19. Freeze the RNA-side state/regulon representation.
20. Derive per-source feature-support masks.
21. Test transport separately in SEA-AD, HVS and NPH52 with donor-uniform inference.
22. Do not interpret structural absence as biological zero.

### Phase H — JEPA continuity
23. q-safe mechanics must pass.
24. NPH52 reader/value fidelity must be appropriately bounded or the source quarantined.
25. Only then run the TD60 successor / bounded teacher continuity test.
26. Training remains OFF until that sequence earns authority.

## 11. Maximum-coverage representation

Whole-dataset coverage should be reported as a tensor, not one percentage.

For each state/regulatory program record:
- cells with an RNA state estimate;
- donors;
- regions;
- source cohorts;
- exact paired-Multiome support;
- separate-nucleus donor-level ATAC support;
- external cohort replication;
- perturbational support;
- spatial support;
- feature-measurement support;
- transport status;
- model-predicted versus directly measured evidence.

A possible per-cell record later:

```
cell_id
state_version
state_coordinates
source
donor
region
lineage
regulon_activity_version
feature_support_fraction
same_nucleus_multimodal_support
donor_level_orthogonal_support
perturbation_supported_programs
spatial_supported_programs
source_transport_status
evidence_flags
limitations
```

This allows near-complete computational coverage without falsely claiming near-complete multimodal validation.

## 12. Failure/pivot rules

Claude/reviewer is explicitly authorized to reject this framework.

Key pivot conditions:

- external eRegulons unstable across donors -> abandon edge-level interpretation; consider module/state-level regulatory objects;
- annotation-supply controls fail -> do not use TF-specific claims;
- only broad cell-class concordance survives -> qualify broad identity only, not fine state;
- same-nucleus positive but Morabito/separate-nucleus negative -> same-nucleus technical coupling remains serious;
- SEA-AD positive but independent cohort negative -> narrow to source/cohort-specific state;
- perturbation contradicts a qualified regulatory prediction -> revise/regionalize that eRegulon; do not rescue by threshold tuning;
- spatial evidence absent -> handling/extraction concern remains unresolved;
- HVS/NPH52 transport failure -> state is not universal under current definition; consider hierarchical/source-specific components;
- q-safety failure -> no teacher/student scientific training;
- NPH52 value fidelity unresolved -> no value-level NPH52 claim beyond the verified boundary.

## 13. Current best scientific thesis

The strongest realistic endpoint is not:

> "the latent is proven biological."

It is:

> A relational cellular-state representation independently discovered in RNA is supported by a regulatory architecture learned outside FULL104, is reflected in chromatin across donors and independent cohorts, survives separate-nucleus replication, shows compatible effects under qualified perturbation where available, recurs in intact tissue where measurable, and transports across the FULL104 atlas under explicit source-specific measurement constraints.

That is a bounded, mechanistic, falsifiable claim.

## 14. Repository anchors

- PR #178 — current V27–V29 review/current head  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/178
- PR #187 — V48 same-RNA identifiability / semantic twin  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/187
- PR #188 — multimodal/access inventory  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/188
- PR #179 — incomplete SCENIC+ recovery; do not cite as evidence  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/179
- PR #164 — Morabito/Stage75F authentication and benchmark readiness  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/164
- PR #175 — 41,238-address external RNA/ATAC coverage crosswalk  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/175
- PR #182 — paired-Multiome authentication  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/182
- PR #77 — GSE301119 perturbation ETL/engagement  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/77
- PR #84 — target-held-out perturbation benchmark mechanics  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/84
- PR #90 — perturbation outcome-exposure ledger  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/90
- PR #137 — CRISPRbrain reliability failure  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/137
- PR #158 — GSE289721 microglial perturbation feasibility  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/158
- PR #16 — restored Target Discovery/T0 lineage  
  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/16

## 15. Governance

This proposal does not authorize:
- TD60 execution;
- protected-outcome opening;
- biological cross-modal outcome inspection;
- teacher training;
- student training;
- therapeutic ranking.

`TRAINING=OFF`.

The next reviewer should first attempt to **break the independence logic**, not implement it faithfully.
