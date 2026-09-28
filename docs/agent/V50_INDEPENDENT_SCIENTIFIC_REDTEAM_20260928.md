# V50 independent scientific red-team

**Date 2026-09-28. Reviewer: Claude. Base PR #178 @ `5d49a970030fc7e783b822437ac4761b3f9e4865`.
Subject: PR #189 @ `6f78b04a88a950ab74366aa3a619beea428ecd3c` — both heads verified live
before review. `TRAINING=OFF`. No biological outcome opened by this document.**

## Verdict

**RETAINED WITH SUBSTANTIAL MODIFICATIONS.**

V50's claim decomposition and governance are the best scientific framing this project
has produced. Its *method* choice and its *phase ordering* are both wrong, and it is
missing a positive identifying signature — without which its control list cannot do
the work asked of it.

Four changes, in descending importance:

1. **Name a positive discriminating signature. V50 has none.** I propose cis coupling.
2. **Reverse Phases C and D.** Morabito (separate nuclei) must come *before* SEA-AD
   MTG (same nuclei), or the same-nucleus result is uninterpretable.
3. **Replace edge-level SCENIC+ with donor-stable cis peak–gene modules** as the
   primary object. The TF/motif layer is optional and later.
4. **Stop treating the three programs symmetrically.** Published measurement bias hits
   two of them specifically.

---

## A. What is scientifically strong

- **The C0–C8 decomposition.** Retiring one binary "target qualified" for eight
  separable claims is correct and overdue. C0 (structure exists) versus C1 (measured
  nuisance insufficient) is exactly the distinction V47/V48 forced.
- **§3's multidimensional independence.** Replacing a "same-nucleus > donor > RNA-only"
  ladder with orthogonal axes is right. The reframing — *which alternative explanation
  does this evidence remove, and which does it still share?* — is the correct question.
  See §E for why V50 asks it and does not answer it.
- **The Stage73R rule.** "A label saying SHUFFLED is not evidence that a graph changed",
  with mandatory content digests and a planted-identical control that must fail, is a
  permanent methodological gain. It should govern every control in this project, not
  only graphs.
- **Refusing Stage75F edges as an answer key.** Correct and non-obvious: those edges
  came from the same Morabito RNA pseudobulk, so they cannot validate an RNA state.
- **Refusing joint-manifold alignment as proof.** Correct. A latent fitted to force RNA
  and ATAC together cannot then evidence that they agree.
- **The N0–N2H nuisance map** is the most complete enumeration the project has.

---

## B. What is unnecessary

- **§11's fifteen-field per-cell record.** This is an output schema for a project that
  already has a qualified state. Designing it now is effort spent on a deliverable
  whose inputs do not exist.
- **Phases E–H in detail.** Their design depends on the outcomes of B–D. Planning them
  now invites the sunk-cost pull that this project keeps having to resist.
- **The ten-TF Stage75F panel as an organising frame.** V50 already says not to restrict
  to it; the document should stop discussing it structurally.

---

## C. What is circular

**The central circularity V50 does not name.**

V50 proposes learning the regulatory architecture from **GSE214979 paired Multiome** —
RNA and ATAC from the same nuclei — then testing it on **SEA-AD MTG paired Multiome**,
also same nuclei.

A network learned from paired multiome is learned from precisely the RNA↔ATAC
covariance structure that the cross-modal test then uses as evidence. If a hidden
nuclear-quality latent (N2A) generates part of that covariance in GSE214979, the
learned network **encodes that nuisance as if it were regulatory structure**, and
carries it into SEA-AD, where the same nuisance mechanism is present and will
reproduce it. The test would then confirm a network that is partly a quality artifact,
using data with the same artifact.

This is not the Stage75F circularity (RNA-derived edges scoring an RNA state). It is
subtler: **cross-modal covariance cannot be used to test whether cross-modal covariance
is biological.**

V50 partially mitigates this with "cell/nucleus pairing permutation" (§5 control 4),
which is the right instrument — but it appears as one of eight co-equal controls rather
than as the load-bearing one. And pairing permutation within donor only removes the
*same-nucleus* link; it does not remove a donor-level quality latent.

**The complete break is Morabito**, where RNA and ATAC come from different nuclei so no
same-nucleus quality latent can couple them. V50 has this as C4 and as Phase D — but
places it *after* the SEA-AD test. See §G.

---

## D. What is not identifiable

**V50 lists controls but never names a positive signature, and that gap is decisive.**

Controls are subtractive: each removes a *named* alternative. N0 through N2H is a good
list, but a control list can never rule out the alternative nobody wrote down. V48
already demonstrated the limit case — a semantic twin whose observable arrays are
**byte-identical** between a biological and a technical world. Against byte-identical
observables, no control helps, because every control is a function of those observables.

Identification therefore requires one of:
- **a larger information set**, or
- **a prospectively restricted nuisance class**, or
- **a positive structural signature that nuisance has no reason to produce.**

V50 pursues the first (add ATAC) but the second modality does not by itself escape the
twin: a shared nuclear-quality latent drives RNA *and* ATAC exactly as a biological
latent does. Adding a channel that the nuisance also occupies buys nothing.

**The proposed positive signature: cis coupling.**

A biological program regulates specific genes through specific *nearby* regulatory
elements. Its RNA effect and its ATAC effect are therefore coupled *at loci*. A
nuclear-quality latent has no access to genomic coordinates: it degrades transcripts
and fragments by abundance and accessibility, not by which peak sits near which gene.

The identifying statistic is consequently **cis correspondence minus
accessibility-matched trans correspondence**, not raw cross-modal agreement. Matching
the trans set on baseline accessibility is what stops a global quality factor from
lifting the cis arm on its own.

**The restriction this buys, declared in advance:** identification holds for technical
nuisance that is *agnostic to genomic position*. A locus-dependent nuisance — GC or
fragment-length bias tracking gene density, or systematic mappability structure —
would defeat it. That restriction is an assumption about physics. It is defensible, but
it must be stated before the test, not discovered after.

**Honesty about my own attempt:** I built this probe and it is currently RED
(`claude/laneB-crossmodal-20260928` @ `671ccb3b`). The planted positive control
cancelled, because I drew cis peak loadings with random signs; the statistic as written
then favoured the technical arm (+0.0142) over the biological one (+0.0029). **No
cross-modal separation has been demonstrated by me.** The signature is a proposal with
a diagnosed-but-unfixed implementation, not a result.

One finding from that work does survive and transfers: **the QC covariate must exclude
the program.** Measured on the fixture, program genes were 22.5% of the RNA library and
the program score correlated +0.844 with log library, so residualising on a
program-inclusive library removed 76.5% of the positive control's variance and silently
destroyed it. This is the same defect frozen protocol v7 already fixed for counts with
`EXCLUDED(P,Q)`, recurring cross-modally. Any V50 implementation must carry it.

---

## E. What project evidence was overlooked

**E1 — snRNA-seq under-detects two of the three programs, and V50 treats all three
symmetrically.** Thrupp et al., *Cell Reports* 2020: ~1% of genes are depleted in nuclei
versus whole cells, enriched for activation genes **APOE, CST3, SPP1, CD74**, comprising
**18% of microglial disease-associated genes**. This is recorded on PR #178 at
`5d49a970` — the very base V50 is stacked on. APOE anchors the lipid/DAM panel; CD74 is
the most abundant partner of the antigen panel.

Consequence V50 misses: the **RNA side of the cross-modal test is attenuated
specifically for two of three programs**, so statistical power is asymmetric by program.
A weaker cross-modal result for DAM or antigen presentation is partly a measurement
property and must not be read as weaker biology. V50's N2H names the nuisance class but
never propagates it into the design, the power expectations, or the interpretation
rules.

**E2 — the three sources do not place genes on a common scale.** The FULL104 candidate
pool census found that **9 of 12 program partners vary more between sources than the
matching band is wide** (median 2.40×; CX3CR1 0.651 → 4.691 → 1.207, a 7.21× range).
V50's Phase G proposes transport across SEA-AD, HVS and NPH52 without addressing this.
Any *level-based* transport statistic will fail for reasons that are not biological.
The project's own surviving screens (TD56–TD59) are **ordinal/relational**, which is
precisely the formulation robust to this — V50 does not connect the two facts, and it
should, because it explains *why* relational order survived where coordinates failed.

**E3 — §3 asks the right question and never answers it.** "Which alternative explanation
does this evidence remove?" deserves a completed table. Partial version:

| source | removes | still shares |
|---|---|---|
| SEA-AD MTG paired (1,594 myeloid / 15 donors) | RNA-only same-assay twin | same-nucleus quality (N2A), handling (N2B), donor fingerprint (N2C) |
| Morabito (18 donors, separate nuclei) | same-nucleus quality (N2A) | donor fingerprint (N2C), cohort/lab (N2G), handling if shared protocol |
| GSE214979 (used for development) | nothing, if it defined the network | everything it defined |
| Spatial (MERFISH/Xenium) | dissociation component of N2B | segmentation/spillover — a **new** class with no controls |
| Qualified perturbation | observational confounding generally | engagement validity, lineage mismatch |

---

## F. What assumptions are unsupported

**F1 — that 12 donors supports edge-level GRN inference.** GSE214979 has ~12 donors and
~2,872 microglia. Donor is the replication unit. Edge-level TF→region→target inference
at n=12 donors is not stable, and — worse — **a leave-donor-out test at n=12 has very
low power to detect instability**, so "stable under LODO" would be uninformative rather
than reassuring. V50 lists module-level as a *pivot condition* if edges prove unstable;
it should be the **starting object**.

**F2 — that spatial attacks the handling nuisance without cost.** Microglia are small
with little cytoplasm; segmentation error and transcript spillover from neighbours are
the dominant artifacts for microglia in imaging-based assays. Spatial trades N2B for a
nuisance class the project has **no controls for and no experience with**. V50's caveat
("does not automatically solve postmortem or donor-level confounding") does not name it.

**F3 — that adding a modality escapes the twin.** Stated in §D. Unsupported as written.

---

## G. What should be replaced

**G1 — the regulatory object. Replace edge-level SCENIC+ with donor-stable cis
peak–gene modules.**

The biological objective, as the brief states, is *an independently defined regulatory
object capable of challenging the biological identity of the RNA relational state* —
not "run SCENIC+". Assessed against that:

| | SCENIC+ eRegulons | cis peak–gene modules |
|---|---|---|
| stability at ~12 donors | poor; edge-level | better; module-level aggregation |
| instantiates the identifying signature (cis) | indirectly, via TF→region→target | **directly** |
| requires motif database | yes | **no** |
| introduces annotation-supply nuisance (N2E) | **yes — self-inflicted** | no |
| interpretability of a negative | confounded by TF annotation density | clean |

The decisive point: **the identifying assumption is cis structure, and cis structure
needs no TF identity at all.** Adopting SCENIC+ imports motif annotation as a dependency
and with it an entire nuisance class (N2E) that we then have to build controls for —
the very class PR #179 stopped in the middle of investigating. That is a self-inflicted
wound taken in exchange for a TF layer the identifying argument does not use.

Recommendation: **primary object = donor-stable cis peak–gene modules. TF/motif layer
optional, later, and only if the cis result qualifies.** chromVAR-style motif activity
and topic models are also inferior here for the same reason: they answer a TF/program
question, not the cis question.

**G2 — the phase order. Run Morabito before SEA-AD.**

V50 has Phase C = SEA-AD MTG (same nucleus), Phase D = Morabito (separate nuclei).
Reverse them.

Morabito is the only asset that breaks N2A, because its RNA and ATAC come from
different nuclei of the same donors. A **positive in SEA-AD alone is uninterpretable** —
it is exactly what a shared nuclear-quality latent predicts. A positive in Morabito
first makes a subsequent SEA-AD positive meaningful; a *negative* in Morabito tells you
the same-nucleus result would have been an artifact, and saves the internal modality.

There is also an exposure argument. SEA-AD is internal (it contributed to FULL104 target
discovery) and finite — 1,594 paired myeloid nuclei across 15 donors in one region.
Spending it on a test that cannot distinguish the dominant nuisance is a poor use of a
scarce, non-renewable asset.

**G3 — program-asymmetric power expectations.** Per E1, state expected power per program
in advance, and pre-commit that a weaker DAM/antigen result will be attributed to
measurement attenuation unless shown otherwise.

---

## H. The strongest feasible design given the assets we actually possess

**Object.** Donor-stable cis peak–gene modules, learned on an external cohort, frozen
before any internal data is touched.

**Identifying statistic.** Cis correspondence minus accessibility-matched trans
correspondence, with QC covariates that **exclude the program's own genes and their cis
peaks**.

**Declared nuisance restriction.** Technical nuisance agnostic to genomic position.
Stated now; a locus-dependent nuisance defeats the design and that is admitted up front.

**Order.**

1. **Freeze** the statistic, the cis window, the matching rule, seeds, and all controls
   — including a planted-identical control that must fail — before opening anything.
2. **Morabito first** (18 donors, separate nuclei, no FULL104 donor overlap): does the
   cis-vs-trans differential exceed its matched null at donor level? This removes N2A.
   A negative here stops the programme cheaply and correctly.
3. **SEA-AD MTG second** (1,594 myeloid, 15 donors): same frozen statistic. Label
   `INTERNAL_INDEPENDENT_MODALITY_SUPPORT`, never independent cohort confirmation.
4. **GSE272082 third**, as independent same-nucleus replication, if authenticated.
5. Perturbation and spatial only after 2–4, and only with their own gates.

**Development/confirmation hygiene.** If GSE214979 is used to learn the modules it is
`REGULATORY_DEVELOPMENT_EXPOSED` and can never be the confirmation. Given ~12 donors, I
would rather **not** learn modules from it at all — use an external reference cis map
and keep GSE214979 as a second same-nucleus replication cohort.

**Unit of inference.** Donor, everywhere. 1,594 nuclei are not 1,594 replicates; at a
median of 98 nuclei per donor they are 15 donor-level estimates of improved precision.

**Stopping rule, pre-committed.** If the cis-vs-trans differential does not separate
from its matched null in Morabito, record
`INSUFFICIENTLY_SPECIFIC_AGAINST_SHARED_CROSS_MODAL_TECHNICAL_STATE` and stop. Do not
widen the cis window, re-pick programs, or move to a different cohort hoping for a
better answer.

---

## Self-audit

**Starting SHA** `5d49a970030fc7e783b822437ac4761b3f9e4865`; **ending SHA** recorded in
the commit. **Branch/worktree** `claude/v50-redteam-20260928` in
`D:/jepa_wt_v50-redteam_20260928`. **Changed files:** this document only — class
**docs**. No source, no test, no result.

**Exact data read:** PR #189's two files at `6f78b04a` (git object read); PR #178 head
metadata; live PR heads for #178/#189 via `gh`. **Access class:**
`PROJECT_ALREADY_LOCAL` for all. **Protected outcomes opened: NO.** **Biological
outcomes opened: none.** **Exposure:** this document creates no development or
confirmatory exposure.

**Positive control:** the Thrupp claim was re-verified by independent search rather than
taken from a lane summary. **Negative control:** I checked whether my "central
circularity" objection was already covered — it is *partially*, by V50's §5 control 4,
and I say so rather than claiming a novel catch. **Skips:** none — no tests were run;
this is a design review.

**Strongest alternative explanation for my own conclusion:** that cis coupling is weaker
in real data than the argument assumes. Published work already reports gene-activity
scores correlating only *minimally* with measured RNA within broad cell types, and
differential accessibility being depth-dependent. If real cis coupling is near the noise
floor at 15–18 donors, my recommended design fails for power reasons and the SCENIC+
route would fail no worse. My design is then not better, only cleaner.

**Strongest criticism of my own result:** I am recommending a statistic whose only
implementation I have written is **currently RED**, with a positive control that cancels
and a sign that favours the technical arm. Recommending it over SCENIC+ — a published,
peer-reviewed method — on the strength of a broken probe and an analytic argument is a
real asymmetry of evidence, and a reader should weight it accordingly. The argument for
cis coupling stands on reasoning about what nuisance can and cannot know, not on any
demonstration I have produced.

**What remains unknown:** whether cis coupling is detectable at these donor counts;
whether Morabito's separate-nucleus design has adequate microglial depth for a
donor-level cis test; whether an external cis map exists whose provenance is clean
relative to all our cohorts; and whether the position-agnostic nuisance restriction
actually holds for 10x multiome chemistry.

**Retraction:** none in this document.
