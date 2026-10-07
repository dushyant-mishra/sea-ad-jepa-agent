# V77 S157 — what an independent regulatory object must contribute (handoff, not a decision)

**Status:** requirements only. No evidence object is selected here; Nott, ATAC, SCENIC+ and the
others below are candidates on equal footing. The real-data scientific lane decides.
**Trigger:** S157 stop condition A. The repaired RNA synthetic challenge still has an exact semantic
twin (`results/v77/V77_S157_LINEAGE_CROSSWALK_V1.json`).
**Framing:** an RNA relational / common-state backbone **plus** an independently constructed
regulatory object. The backbone says *what co-varies*; the object must say *why*, using a
measurement the RNA twin cannot also have produced.

## What S157 left standing

| Twin (from the V77 challenge) | Status from RNA plus measurement context |
|---|---|
| **T1 exact capture twin.** A capture process tied to the biological state, with the same law as the program (`TWIN_EXACT`) | Non-identifiable under every context, raw identity included |
| **T2 operator-linked capture twin** (`TWIN_OPERATOR`) | Removed only by raw dataset identity (a positive control, never a design) or a *measured* capture covariate. Lawful depth and coverage counts fail |
| **T3 anchor-keyed twin** (V63 Task 8). A nuisance that also moves the external object | Not represented in V77; any object below must rule it out for itself |

## Minimum the object must supply, whichever it is

1. **A quantity whose expectation differs between "biology" and "capture."** If biology and the twin
   predict the same value of the object, it cannot break the twin, however strong it is.
2. **Construction without the RNA being explained** (feature-definition independence). Stage75F's edges
   came from the same Morabito RNA and cannot be an answer key for an RNA state.
3. **Its own nuisance, characterised.** It must rule out T3, a twin keyed to the object itself, such as
   nuclear quality moving RNA capture and ATAC fragment yield together.
4. **Structural negative controls that prove physical distinctness** (adjacency or content digests,
   changed-edge fraction, a planted identical-control failure): the Stage73 lesson.
5. **Donor-level inference.** Nuclei refine each donor's estimate; they are not independent replicates.
6. **Governance.** Exposure recorded in the existing ledger (PR #90 pattern); Morabito is PROTECTED and
   unused here; DS010 is embargoed; TEST stays sealed.

## Requirements by evidence object

| Evidence object | Biological quantity it measures independently | Provenance requirements | Specificity requirements | Measurement-confounding risks | Twin it can falsify | What it still cannot identify |
|---|---|---|---|---|---|---|
| **Same-nucleus chromatin accessibility** (paired RNA+ATAC; e.g. SEA-AD public exact pairing, GSE272082) | Accessibility of the program's regulatory regions in the *same nucleus* | Exact nucleus pairing authenticated; region set fixed before outcomes; donor overlap with FULL104 declared | State-specific accessibility at the program's regions against matched decoy regions and same-donor, other-state nuclei | Nuclear quality and fragment yield can move ATAC and RNA capture together (T3); TSS-enrichment and depth differences by batch | T1 and T2, **if** the program has a chromatin footprint and ATAC capture is independent of RNA capture | Programs regulated post-transcriptionally (they look like capture in RNA and have no chromatin footprint); T3 keyed to nuclear integrity |
| **Separate-nucleus or donor-level chromatin** (unpaired ATAC cohorts; Morabito excluded here as PROTECTED) | Donor-level regulatory state in different nuclei | Cohort and lab independence documented; donor matching by stable identifiers | Donor-level association between program activity and regional accessibility, beyond donor fingerprint | Donor-level confounders (age, postmortem interval, pathology are off-limits) and cohort batch | T1 at donor level: a cell-level capture artefact should not reappear in separate nuclei | Cell-level attribution; anything shared at donor level by both measurements |
| **Cell-type enhancer–promoter interactome** (Nott Table S5, authenticated; hg19, liftover required) | Physical 3D contact between enhancers and the program's promoters in sorted nuclei of a cell type | Authenticated file and SHA-256 (81c99689...); liftover receipt; same-study comparators (neuronal, oligodendrocyte) | Contacts specific to the relevant cell type against same-study comparators and a promoter-fixed distal shuffle | H3K27ac and interactome selection share expression and activity selection with RNA ("resource count is not evidence-independence count"); a single contact source | T1 if the program's genes are wired to cell-type-specific enhancers that a capture artefact would not explain | Program activity level in a given cell; causality; states absent from the sorted populations |
| **Sequence-level cis evidence** (TF motifs, cisTarget over regulatory regions) | Whether regulatory regions carry binding sites for a candidate regulator; genome sequence, independent of any measurement | Motif collection and version pinned; region set constructed without the outcome | TF-specific motif support beats **annotation-supply** and **TF-label permutation** controls (the required PR #179 control) | Annotation supply (more motifs annotated to some TFs); all TFs scanning the same region set | T1 only jointly with an object that localises activity: sequence alone is constant across cells | Whether the site is used in these cells; capture versus transcription on its own |
| **SCENIC+ eRegulons** (TF → region → target, from RNA+ATAC) | A candidate gene-regulatory network linking regulators, regions and targets | Built on data **other than** the RNA being explained, or the circularity register shows otherwise; PR #179 (`INCOMPLETE_STOPPED`) is not citable | Motif support passes the PR #179 controls; eRegulon membership stable across donors and resamples | Target linkage still comes from RNA co-variation, so a capture twin in the *same* RNA would be absorbed into the network | T1 or T2 only when built on independent data and its region evidence carries the weight | Causality: eRegulons are candidate GRNs, not causal truth. Not independent of RNA when built on the same cells |
| **Perturbation with qualified engagement** (CRISPRi/a; e.g. GSE289721 after its gates, GSE301119 as myeloid auxiliary) | The program's response to an intervention on its candidate regulator | Complete guides, target-held-out benchmark (PR #84), exposure ledger (PR #90); CRISPRbrain is not truth | Engagement shown first; response specific against non-targeting and off-program controls | Lineage mismatch (macrophage versus microglia); differentiation batch; one genetic background | T1 and T2: a capture artefact should not follow knock-down of the program's regulator | Programs without a perturbable regulator; in vivo context; donor-level biology |
| **Spatial in situ transcriptomics** (e.g. MERFISH or Xenium) | Program expression in intact tissue, with a different capture chemistry and no dissociation | Region, donor and panel audit; FULL104 overlap declared; pathology fields excluded | Program enrichment in the mapped cell state against panel-matched genes | Probe and panel design; segmentation; RNA integrity shared with droplet assays | T2 and a droplet-specific T1: a dissociation or droplet capture artefact should not survive a different chemistry in intact tissue | A shared RNA-integrity artefact present in every chemistry; regulatory cause |
| **Genetics** (cis-eQTL, caQTL, allele-specific expression) | Genotype-dependent expression or accessibility of the program's genes | Genotype access authorised; donor identity resolved through stable identifiers | Cis effects concentrated in the program's state against matched genes | 3' UTR or poly-A variants can change *capture* (a genotype-keyed T3) | T1, except for capture-altering variants | Trans regulation; states without genetic variation in the cohort |
| **Direct capture measurement** (spike-ins, external RNA standards, chemistry and protocol variables) | Capture efficiency itself, per cell or per batch | Spike-in design and lots recorded; per-library capture estimates | Calibrated against known input amounts | Spike-ins differ from endogenous transcripts in sequence and structure, so gene-specific capture may not transfer | T2, by supplying the measured capture covariate S157 showed is needed | T1 when the capture bias is gene-specific and state-linked beyond what spike-ins report |
| **Protein-level measurement** (CITE-seq, proteomics) | Program products at a different molecular layer | Antibody panel or proteomics provenance; same-cell or donor pairing declared | Protein elevation in the state against matched non-program proteins | RNA–protein discordance; antibody specificity | T1, if the program's proteins rise with its RNA in that state | Regulatory mechanism; programs with poor RNA–protein coupling |

## Questions for the deciding lane (not answered here)

- Which objects are admissible under current exposure and licensing? Downloadable is not the same
  as licensed.
- What prospective positive and negative signatures should be frozen before any scarce real
  outcome is opened (V52 closeout)?
- How should evidence from several objects combine? Count independent alternatives removed, not
  resources: V50 asks "which alternative explanation does this evidence remove, and which does it
  still share?"

## What this does not do

It selects no object, target, estimand, weighting or threshold. It opens no protected data, trains
nothing, and adds no runtime work. The V77 synthetic world can host a future challenge pairing one
of these objects with the RNA twins, but only once the deciding lane names the object and its
frozen signatures.
