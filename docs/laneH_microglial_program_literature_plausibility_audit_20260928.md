# Lane H — Deep Literature Plausibility Audit of Three Microglial State Programs

**Lane:** H (literature only)
**Date:** 2026-09-28
**Worktree:** `D:/jepa_wt_laneH-literature_20260928`
**Branch:** `lane/laneH-literature-20260928`
**Base commit:** `1ceaf3e9a3de15cd2386da7398e8620510ed8be1`
**Output directory:** `D:/jepa_v5_outputs_20260925/out_laneH-literature`
**TRAINING:** OFF
**Project data opened:** NONE
**Protected outcome variables read:** NONE

---

## 0. What this lane is, and what it explicitly is not

This report asks one question: **are the three microglial gene programs we already found biologically coherent in independent published literature, and can known technical artifacts produce the same apparent patterns?**

It does **not** identify a target, does not qualify one, and cannot confirm any project result. Literature is background plausibility. It constrains what is worth testing; it never substitutes for our own experiment. Every conclusion below is of evidence class **LITERATURE**.

### The single most important framing rule, stated up front

Most of what the literature offers for these three programs is **many papers measuring RNA, in human postmortem brain, with droplet single-cell or single-nucleus sequencing**. When twenty papers replicate a signature that way, that is *one* kind of evidence repeated twenty times — it is not twenty independent confirmations. Shared technology plus shared tissue source means shared failure modes. Throughout this report that is labelled `RNA_ONLY_REPLICATION`, and the count of such papers is deliberately **not** treated as strengthening the case.

---

## 1. Bottom line first

**Is this good news or bad news? It is mixed, and the mix is different for each of the three programs.**

| Program | Strongest evidence class available | Verdict |
|---|---|---|
| Homeostatic (P2RY12, TMEM119, CX3CR1, GPR34, SALL1) | `PERTURBATIONAL_SUPPORT` + `PROTEIN/SPATIAL_SUPPORT` + `DIRECT_MULTIMODAL_SUPPORT` | Strongest of the three. Real, causally anchored, visible at protein level. But its *loss* is the single most artifact-prone readout in the whole field. |
| Lipid/phagocytic/DAM (APOE, LPL, GPNMB, TREM2, APOC1, ABCA1) | `GENETIC_SUPPORT` + `PERTURBATIONAL_SUPPORT` + `DIRECT_MULTIMODAL_SUPPORT` | Strong. Human genetics and gene-knockout experiments point at the same genes, which RNA co-expression alone never could. But its two flagship genes, APOE and CD74, are exactly the genes single-nucleus RNA-seq is documented to under-detect. |
| Antigen presentation (HLA-DRA, HLA-DPA1, HLA-DMB, HLA-DMA, CD74, CTSS, IFI30) | `GENETIC_SUPPORT` + `PROTEIN/SPATIAL_SUPPORT` | Real as a biological module, but the **direction** of its change in Alzheimer's is genuinely contested between RNA and protein measurements. Weakest chromatin-level evidence of the three. |

**What it means for the project.** Nothing here blocks the RNA↔ATAC step. Three findings change how that step should be designed:

1. **Single-nucleus RNA-seq is documented to under-detect APOE and CD74 specifically** — two of our own program genes. Any program score built from nuclear RNA is measuring an attenuated version of the biology, and the attenuation is gene-specific, not uniform.
2. **Handling artifacts reproduce "loss of the homeostatic program" almost exactly.** A microglial nucleus that sat at room temperature looks like a microglial nucleus that left the homeostatic state. This is the strongest technical alternative we found and it targets Program 1 directly.
3. **Nobody has published the experiment we most need.** We could not find any study demonstrating whether nucleus-level damage drives RNA and ATAC in a *correlated* way within the same nucleus in brain multiome data. The one paper that measured anything close found ambient contamination in the two modalities is only weakly correlated (Spearman 0.08) — in adipose tissue, not brain. **We will have to measure this ourselves. The literature cannot rule it out and cannot rule it in.**

**What still stands.** The three programs are not inventions. Each is recovered by multiple independent groups, and — decisively — each has at least one line of evidence that is *not* RNA co-expression: knockouts that abolish the program, GWAS variants that sit in the program's genes, and antibodies that stain the program's proteins in tissue. That is the part that volume of citations cannot fake.

---

## 2. Classification key

Every conclusion in this report carries exactly one label.

| Label | Meaning |
|---|---|
| `DIRECT_MULTIMODAL_SUPPORT` | Chromatin accessibility (or another orthogonal molecular layer) measured alongside RNA and agreeing on the same program. Highest value for us, because our next step is RNA↔ATAC. |
| `RNA_ONLY_REPLICATION` | The program was recovered again from transcriptomes. Same technology class, similar tissue. Adds breadth, **not** independence. |
| `GENETIC_SUPPORT` | Human genetic variation (GWAS, eQTL, coding variants) implicates the program's genes. Independent of expression-measurement artifacts, because genotype is not affected by tissue handling. |
| `PROTEIN/SPATIAL_SUPPORT` | Protein-level detection (IHC, mass cytometry, imaging mass spectrometry, proteomics) or spatial localization. Independent of RNA capture chemistry. |
| `PERTURBATIONAL_SUPPORT` | A deliberate intervention (knockout, knockdown, CRISPR screen, inhibitor, xenotransplant) moved the program. Causal, not correlational. |
| `KNOWN_TECHNICAL_ALTERNATIVE` | A documented artifact capable of producing a similar apparent pattern. |
| `SPECULATIVE` | Plausible, not demonstrated. |

### Verification marking

Because provenance matters more than volume, each citation is marked:

- **[F]** — I fetched and read the page/PDF/abstract in this session.
- **[S]** — I saw only a search-result snippet describing it. Claims resting on **[S]** sources are weaker and are flagged as such in the self-audit.

---

## 3. PROGRAM 1 — Homeostatic microglia (P2RY12, TMEM119, CX3CR1, GPR34, SALL1)

### 3.1 Is the module real?

**Conclusion: yes, and it is causally anchored.** — `PERTURBATIONAL_SUPPORT`

`SALL1` is not just a co-expressed marker; it is an upstream regulator whose removal collapses the rest of the module. Inducible deletion of *Sall1* in adult mouse microglia converts them "from resting tissue macrophages into inflammatory phagocytes," with loss of homeostatic phenotype and reduced hippocampal neurogenesis.

- *Sall1 is a transcriptional regulator defining microglia identity and function.* **Nature Immunology**, 2016. https://www.nature.com/articles/ni.3585 — **[S]** (Buttgereit et al.)
- *SALL1 enforces microglia-specific DNA binding and function of SMADs to establish microglia identity.* **Nature Immunology**, 2023. https://www.nature.com/articles/s41590-023-01528-8 — **[S]**

This matters for us specifically: a program containing its own transcription factor, where deleting that factor dismantles the program, is structurally different from a list of genes that merely correlate. It is the difference between a module and a correlation.

**Conclusion: the module has an identified enhancer-level basis.** — `DIRECT_MULTIMODAL_SUPPORT`

IRF8 binds stepwise to enhancer regions in postnatal microglia together with SALL1 and PU.1, and "IRF8 binding correlated with a stepwise increase in chromatin accessibility, which preceded the initiation of microglia-specific transcriptome." *Irf8* deletion caused "loss of microglia identity and gain of disease-associated microglia-like genes."

- *IRF8 configures enhancer landscape in postnatal microglia and directs microglia specific transcriptional programs.* bioRxiv 2023 / PMC. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10461927/ — **[S]**

This is the most directly relevant statement we found for an RNA↔ATAC design: chromatin accessibility change *preceding* transcriptome change, at the homeostatic module, in a system where the driver is known. Note the caveat: it is mouse and developmental, not human adult disease.

**Conclusion: the module is visible at protein level and is lost specifically near plaques.** — `PROTEIN/SPATIAL_SUPPORT`

- *Patterns of Expression of Purinergic Receptor P2RY12, a Putative Marker for Non-Activated Microglia, in Aged and Alzheimer's Disease Brains.* **Int J Mol Sci** 21(2):678, 2020. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7014248/ — **[S]**
- *Co-expression patterns of microglia markers Iba1, TMEM119 and P2RY12 in Alzheimer's disease.* **Neurobiology of Disease**, 2022. https://www.sciencedirect.com/science/article/pii/S0969996122000754 — **[S]**
- *Regulation of microglial TMEM119 and P2RY12 immunoreactivity in multiple sclerosis white and grey matter lesions is dependent on their inflammatory environment.* **Acta Neuropathologica Communications**, 2019. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6907356/ — **[S]**
- *Human microglia regional heterogeneity and phenotypes determined by multiplexed single-cell mass cytometry.* **Nature Neuroscience** 22:78–90, 2019. https://www.nature.com/articles/s41593-018-0290-2 — **[S]**

The plaque result is the informative one: "Loss of P2RY12 was specifically attributed to presence of Aβ-plaques, whereas TMEM119 was more generally lost in both grey and white matter." So P2RY12 and TMEM119 do **not** move together spatially. That is a genuine internal structure within our Program 1 that RNA co-expression would smooth over, and it is a testable prediction for our data.

**Conclusion: the module is replicated across many human transcriptomic studies.** — `RNA_ONLY_REPLICATION`

Sun et al. annotate MG0 as homeostatic "with high expression of well-known homeostatic markers P2RY12 and CX3CR1"; Olah et al. find clusters 1 and 2 represent homeostatic states. This is consistent and unremarkable. **It adds essentially nothing beyond what the perturbational and protein evidence already establish**, and should not be counted as independent support.

- *Human microglial state dynamics in Alzheimer's disease progression.* **Cell** 186(20):4386–4403, 2023. https://www.cell.com/cell/fulltext/S0092-8674(23)00971-6 — **[S]**
- *Single cell RNA sequencing of human microglia uncovers a subset associated with Alzheimer's disease.* **Nature Communications** 11:6129, 2020. https://www.nature.com/articles/s41467-020-19737-2 — **[S]**

### 3.2 Strongest technical alternative for Program 1

**`KNOWN_TECHNICAL_ALTERNATIVE` — tissue handling reproduces homeostatic-program loss.**

This is the most serious finding in the whole report, and it lands squarely on Program 1.

Marsh et al. characterised an *ex vivo* activation signature (`exAM`) induced by tissue processing: immediate-early genes *Fos*, *Jun*; stress genes *Hspa1a*, *Dusp1*; chemokines *Ccl3*, *Ccl4*; NF-κB genes *Nfkbiz*, *Nfkbid*; histone genes. Critically, **"microglia expressing the exAM signature lost expression of homeostatic markers."** The signature is present in human postmortem snRNA-seq datasets, is "highly variable between subjects," and in acutely resected human neurosurgical tissue was induced simply by leaving tissue 2 h at room temperature then 4 h at 4 °C before freezing.

- *Dissection of artifactual and confounding glial signatures by single-cell sequencing of mouse and human brain.* **Nature Neuroscience** 25:306–316, 2022. https://www.nature.com/articles/s41593-022-01022-8 · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11645269/ — **[F]**

Two details cut both ways and both must be reported:

- **Against us:** a room-temperature delay before freezing is enough. Brain banks vary enormously in this. A donor-level difference in handling would look exactly like a donor-level difference in homeostatic-program score.
- **For us:** Marsh et al. found `exAM` enrichment **did not correlate with postmortem interval**. So PMI as recorded in a brain bank is *not* a sufficient covariate to adjust this away — the damaging variable is agonal/handling temperature history, which is usually unrecorded. Adjusting for PMI and declaring the confound handled would be a false green.

Supporting, same direction:

- *Characterizing cell type specific transcriptional differences between the living and postmortem human brain.* **medRxiv**, 2024, doi 10.1101/2024.05.01.24306590. https://www.medrxiv.org/content/10.1101/2024.05.01.24306590v1.full — **[S]**. 31 living neurosurgical vs 21 postmortem prefrontal cortex samples; cell types identified consistently but "large proportions of differentially expressed genes between postmortem and living samples for each cell type."
- *Postmortem Interval Leads to Loss of Disease-Specific Signatures in Brain Tissue.* **eNeuro** 12(3), 2025. https://www.eneuro.org/content/12/3/ENEURO.0505-24.2025 — **[S]**
- *Single-nucleus RNA sequencing revealed the impact of post-mortem interval on the cellular component and gene expression analysis of mouse brains.* **bioRxiv**, 2024, doi 10.1101/2024.12.30.630832. — **[S]**

**Net assessment for Program 1:** the module is real and causally established. But *"microglia in condition X have lost the homeostatic program"* is the single most confoundable statement in this field, and a result of that shape in our data should be treated as unproven until handling variation is addressed by design, not by covariate adjustment.

---

## 4. PROGRAM 2 — Lipid / phagocytic / disease-associated (APOE, LPL, GPNMB, TREM2, APOC1, ABCA1)

### 4.1 Is the module real?

**Conclusion: yes, and human genetics independently nominates its genes.** — `GENETIC_SUPPORT`

This is the strongest argument available for Program 2, because genotype cannot be altered by tissue handling. Independent of any expression measurement:

- **TREM2** coding variants (R47H, R62H) raise AD risk; in human AD tissue "the reactive phenotype of microglia was less palpable in TREM2 R47H and R62H carriers than in non-carriers." — **[S]**
- **APOE** is the strongest common genetic risk factor for late-onset AD.
- **GPNMB** is a Parkinson's disease GWAS locus with a caudate eQTL sharing a causal variant at 94% posterior probability; the risk haplotype is associated with ~3-fold higher GPNMB expression across caudate, cerebellum and cingulate cortex, and GPNMB "displayed a robust causal role for PD at the protein level in blood, cerebrospinal fluid and brain."
  - *GPNMB confers risk for Parkinson's disease through interaction with α-synuclein.* **Science** 377(6608):eabk0637, 2022. https://www.science.org/doi/10.1126/science.abk0637 — **[S]**
- **ABCA7** (same transporter family as ABCA1) is an AD risk gene. — **[S]**
- Microglia-specific eQTL atlases place AD causal variants inside microglial regulatory elements: MiGA (255 microglial samples, 100 donors) found 3,611 eGenes and 15 QTLs affecting genes at 10 AD risk loci.
  - *Genetic analysis of the human microglial transcriptome across brain regions, aging and disease pathologies.* **Nature Genetics** 54:4–17, 2022. https://www.nature.com/articles/s41588-021-00976-y — **[S]** (de Paiva Lopes et al.)
  - Young et al., primary human microglia (n=93), 401 eQTLs, colocalising with AD loci including BIN1. **Nature Genetics**, 2021. — **[S]**

Why this matters more than another RNA replication: a GWAS hit at GPNMB and a coding variant at TREM2 were discovered without ever looking at a microglial transcriptome. They converge on our program from outside it.

**Conclusion: the module is causally constructed and dismantlable.** — `PERTURBATIONAL_SUPPORT`

- DAM induction is two-staged: the homeostatic→stage-1 transition is TREM2-independent and downregulates *Cx3cr1*, *P2ry12*; the stage-1→stage-2 transition **requires TREM2** and upregulates lysosomal/phagocytic/lipid genes including *Lpl*, *Cst7*, *Axl*. *Trem2*<sup>−/−</sup> microglia show reduced *Apoe* and *Fabp5*.
  - *Disease-Associated Microglia: A Universal Immune Sensor of Neurodegeneration.* **Cell** 173(5), 2018. https://www.cell.com/cell/fulltext/S0092-8674(18)30576-2 — **[S]**
  - *The TREM2-APOE Pathway Drives the Transcriptional Phenotype of Dysfunctional Microglia in Neurodegenerative Diseases.* **Immunity** 47(3), 2017. https://www.sciencedirect.com/science/article/pii/S1074761317303667 — **[S]**
  - *TREM2 drives microglia response to amyloid-β via SYK-dependent and -independent pathways.* **Cell**, 2022. https://www.cell.com/cell/fulltext/S0092-8674(22)01252-1 — **[S]**
  - Original DAM description: Keren-Shaul et al., **Cell** 169(7):1276–1290, 2017 — cited here via the reviews above, **not** independently retrieved. — **[S, indirect]**
- **In human cells:** genetic deletion of TREM2 or APOE, APOE polymorphisms, and TREM2-R47H in xenografted human iPSC microglia each modulate the response differentially (138,577 cells).
  - *Xenografted human microglia display diverse transcriptomic states in response to Alzheimer's disease-related amyloid-β pathology.* **Nature Neuroscience** 27, 2024. https://www.nature.com/articles/s41593-024-01600-y · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11089003/ — **[S]** (Mancuso et al.)
- **CRISPR screens in human iPSC microglia** recovered a state spectrum "mirroring those observed in human brains," and an SPP1-marked disease-associated state was selectively depleted by CSF1R inhibition.
  - *A CRISPRi/a platform in human iPSC-derived microglia uncovers regulators of disease states.* **Nature Neuroscience** 25:1149–1162, 2022. https://www.nature.com/articles/s41593-022-01131-4 — **[S]** (Dräger et al.)
- **TREM2 and lipid handling directly:** TREM2-deficient microglia phagocytose myelin but fail to clear myelin cholesterol, accumulating cholesteryl ester and lipid droplets. *TREM2 Regulates Microglial Cholesterol Metabolism upon Chronic Phagocytic Challenge.* **Neuron** 105(5), 2020. https://www.sciencedirect.com/science/article/pii/S0896627319310499 — **[S]**
- **APOE genotype → lipid droplets:** APOE4 causes glial lipid-droplet accumulation, an activated phenotype, and "a weakened response to neuronal cues mediated by the purinergic P2RY12 receptor"; inhibiting fatty-acid synthesis reversed it.
  - *APOE4 disrupts intracellular lipid homeostasis in human iPSC-derived glia.* **Science Translational Medicine** 13(583), 2021. https://www.science.org/doi/10.1126/scitranslmed.aaz4564 — **[S]**
  - *APOE4/4 is linked to damaging lipid droplets in Alzheimer's microglia* (ACSL1+ microglia enriched for triglyceride lipid droplets in APOE4/4 AD patients). bioRxiv 2023 / PMC. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11290272/ — **[S]**

That last item is an important cross-link for us: **the same genotype that drives Program 2 up also drives Program 1 (P2RY12 function) down, in a single controlled system.** If our data show Programs 1 and 2 anticorrelated, that anticorrelation has a published mechanistic precedent and is not automatically an artifact.

**Conclusion: the module has chromatin-level structure.** — `DIRECT_MULTIMODAL_SUPPORT`

- *Apoe* showed enriched H3K27ac at downstream distal enhancers in both developmental PAM and 5xFAD DAM; *Clec7a* and *Trem2* showed "robust histone modifications at promoters and enhancers distinguishing reactive states." 385 PAM-specific and 840 DAM enhancers with state-switching activity. DNA methylation, notably, stayed relatively stable across states — so the state switch is enhancer-activity-level, not methylation-level.
  - *State-specific enhancer landscapes govern microglial plasticity.* **Immunity**, 2026 (online 2025). https://www.cell.com/immunity/fulltext/S1074-7613(25)00525-4 · https://pmc.ncbi.nlm.nih.gov/articles/PMC13050238/ — **[S]**
  - Preprint version: *Microglial plasticity governed by state-specific enhancer landscapes.* **bioRxiv** 2025, doi 10.1101/2025.01.30.635595. https://pmc.ncbi.nlm.nih.gov/articles/PMC11838276/ — **[F]** (Hamagami, Kapadia, Abduljawad et al.)
  - **Important honesty note from the fetched text:** the authors document chromatin changes *accompanying* rather than *preceding* transcription. Do not cite this paper as showing chromatin leads RNA.
- Human AD multi-omics profiling chromatin accessibility and expression in the same samples (130,418 ATAC nuclei + 61,472 RNA nuclei, 12 AD + 8 control prefrontal cortices) supports DAM existence in human tissue and identifies SREBF1 — a lipid-synthesis transcription factor — as a glial trajectory regulator.
  - *Single-nucleus chromatin accessibility and transcriptomic characterization of Alzheimer's disease.* **Nature Genetics** 53:1143–1155, 2021. https://www.nature.com/articles/s41588-021-00894-z · https://pmc.ncbi.nlm.nih.gov/articles/PMC8766217/ — **[S]** (Morabito et al.)
- AD risk loci are enriched in **microglial enhancers** specifically, and deletion of a microglia-specific enhancer carrying AD-risk variants ablated BIN1 expression in microglia but not neurons or astrocytes — a chromatin element with a demonstrated causal effect.
  - *Brain cell type–specific enhancer–promoter interactome maps and disease-risk association.* **Science** 366(6469):1134–1139, 2019. https://www.science.org/doi/10.1126/science.aay0793 — **[S]** (Nott et al.)
- 850,000 nuclei from 92 donors (48 control, 44 AD): AD risk loci enriched in microglial enhancers and for SPI1, ELF2, RUNX1 motifs; late-stage AD shows global "epigenome erosion" and cell-identity loss.
  - *Epigenomic dissection of Alzheimer's disease pinpoints causal variants and reveals epigenome erosion.* **Cell** 186(20), 2023. https://www.cell.com/cell/fulltext/S0092-8674(23)00974-1 — **[S]** (Xiong et al.)
- **Microglial states defined from chromatin alone.** 682,667 QC-passing nuclei, 41 donors (10 control, 10 AD, 10 Pick's, 11 PSP), three regions, snATAC-seq only: 10 microglial subclusters including homeostatic (mg.C16, mg.C14), inflammatory (mg.C13, mg.C11), DAM (mg.C12); marker genes include *TREM2*, *GPNMB*, *TMEM119*, *LGALS3*, *SORT1*. FTD heritability was maximally enriched in a disease-associated microglial state's accessible regions.
  - *Single-nucleus epigenomic dysregulation unmasks genetic risk-associated neurodegenerative glia states.* **Nature Communications**, 2026, doi 10.1038/s41467-026-73007-1. https://www.nature.com/articles/s41467-026-73007-1 · https://pmc.ncbi.nlm.nih.gov/articles/PMC13376791/ — **[F]** (Han, Rosenberg, Kisling, Zhang et al.)

That last paper is, for our purposes, the most valuable single citation in this report: **microglial states recovered from chromatin accessibility without using RNA at all**, with GWAS heritability enriched in the state-specific peaks. It is the closest published thing to the design we are proposing.

**Conclusion: replicated widely in human transcriptomes.** — `RNA_ONLY_REPLICATION`

- Gerrits et al., 482,472 nuclei: AD1 microglia correlate with amyloid load and carry *GPNMB*, *SPP1*, *LPL*, *PPARG*, *ITGAX*, *MSR1*, *AXL*; AD2 correlate with phospho-tau. 15 of 63 microglia-expressed AD risk genes are enriched in AD1.
  - *Distinct amyloid-β and tau-associated microglia profiles in Alzheimer's disease.* **Acta Neuropathologica** 141, 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8043951/ — **[S]**
- Sun et al. MG4 = "lipid processing," annotated by lipid homeostasis and cholesterol-efflux enrichment (ABCA1's pathway). **Cell** 186(20), 2023. — **[S]**
- *Human and mouse single-nucleus transcriptomics reveal TREM2-dependent and TREM2-independent cellular responses in Alzheimer's disease.* **Nature Medicine** 26:131–142, 2020. https://www.nature.com/articles/s41591-019-0695-9 — **[S]** (Zhou et al.)
- Cross-species taxonomy of >1,000,000 CNS cells from >30 conditions: 27 superclusters / 192 clusters, largely conserved mouse↔human; activation-associated states shown *in vivo* to depend on interferon and CSF1R signalling (that last part is `PERTURBATIONAL_SUPPORT`).
  - *A transcriptomic microglia taxonomy across mouse and human pathologies.* **Nature Immunology**, 2026. https://www.nature.com/articles/s41590-026-02472-z — **[S]** (Chhatbar, Sankowski, Prinz et al.)

**Counter-evidence that must be stated.** Human snRNA-seq replication of DAM is *not* uniform. Mathys et al. and Zhou et al. "have not recovered a consistent microglial activation signature," and the earliest human study found AD-enriched modules dominated by myelination and neuronal-survival genes with **no DAM signature observed**. — **[S]**. Section 6 and 4.2 give the likely technical reason.

**Conclusion: protein and spatial evidence exists but is partly discordant.** — `PROTEIN/SPATIAL_SUPPORT`

Lipid-droplet-accumulating microglia (LDAM) are a directly *visualised* (not inferred) state — lipid droplets accumulate with age in mouse and human brain; LDAM are phagocytosis-defective, ROS-high, and pro-inflammatory, with a transcriptional profile the authors call distinct from previously reported microglial states. A CRISPR screen identified genetic modifiers including *GRN*, itself a cause of human neurodegeneration.

- *Lipid-droplet-accumulating microglia represent a dysfunctional and proinflammatory state in the aging brain.* **Nature Neuroscience** 23:194–208, 2020. https://www.nature.com/articles/s41593-019-0566-1 — **[S]**

But imaging mass spectrometry of human tissue reports **decreased ApoE protein** in AD hippocampal microglia alongside increased CD33/CD44 — the opposite direction to the RNA signature.

- *Spatial proteomics of Alzheimer's disease-specific human microglial states.* **Nature Immunology** 26(8):1397–1410, 2025. https://www.nature.com/articles/s41590-025-02203-w · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12725032/ — **[S]**

I am not resolving that discordance here. It should be recorded as unresolved.

### 4.2 Strongest technical alternative for Program 2

**`KNOWN_TECHNICAL_ALTERNATIVE` — single-nucleus RNA-seq systematically under-detects exactly these genes, and ambient RNA can supply them spuriously.**

Two distinct artifacts, pulling in *opposite* directions, which is why this program's measurement is fragile in both directions.

**(a) Under-detection in nuclei.** Thrupp et al. compared single-cell and single-nucleus RNA-seq from the temporal lobe of the same four human donors. ~246 genes (~1.1% of detectable genes) were significantly more abundant in whole cells than nuclei; this small set is enriched for microglial activation genes and includes **APOE, CST3, SPP1 and CD74**, comprising **18% of previously identified microglial disease-associated genes**. The authors conclude snRNA-seq "is not suited for detecting cellular activation in microglia in human disease."

- *Single-Nucleus RNA-Seq Is Not Suitable for Detection of Microglial Activation Genes in Humans.* **Cell Reports** 32(13):108189, 2020. https://www.cell.com/cell-reports/fulltext/S2211-1247(20)31178-5 · preprint https://www.biorxiv.org/content/10.1101/2020.04.13.035386 — **[S]**, with a fetched summary and expert commentary at https://www.alzforum.org/papers/single-nucleus-rna-seq-not-suitable-detection-microglial-activation-genes-humans — **[F]**

**This hits two of our three programs at once: APOE from Program 2 and CD74 from Program 3.** The published expert rebuttal is worth recording rather than suppressing: commentators note the affected genes "remain within the top 500 abundant genes in microglial nuclei," so relative differences between conditions may still be detectable, and nuclei-isolation and integration methods have improved since 2020. That is a reasonable defence — but it converts a clean measurement into an attenuated one whose attenuation factor we do not know.

**(b) Ambient RNA supplying the signal spuriously.** APOE is among the most highly expressed genes in astrocytes. Ambient RNA from lysed cells is loaded into every droplet, and "contamination from ambient RNA is evident when highly-expressed cell-type-specific genes are observed at low levels in other cell populations." In brain snRNA-seq the ambient signature is predominantly neuronal and "all glia are contaminated" unless glia and neurons are physically separated; some previously annotated cell types were shown to be distinguished by contamination rather than biology. Conversely, an *Apoe+* microglia/macrophage subgroup was only revealed *after* removing ambient RNA — so decontamination can create as well as destroy apparent states.

- *Neuronal ambient RNA contamination causes misinterpreted and masked cell types in brain single-nuclei datasets.* **Neuron** 110(24), 2022. https://www.sciencedirect.com/science/article/pii/S0896627322008157 · https://pubmed.ncbi.nlm.nih.gov/36240767/ — **[S]**
- *Ambient RNAs removal of cortex-specific snRNA-seq reveals Apoe+ microglia/macrophage after deeper cerebral hypoperfusion in mice.* **Journal of Neuroinflammation** 20, 2023. https://jneuroinflammation.biomedcentral.com/articles/10.1186/s12974-023-02831-9 — **[S]**
- *Understanding and mitigating the impact of ambient mRNA contamination in single-cell RNA-sequencing analysis.* **PLOS One**, 2025. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0332440 — **[S]**
- *Decontamination of ambient RNA in single-cell RNA-seq with DecontX.* **Genome Biology**, 2020. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7059395/ — **[S]**

**Net assessment for Program 2:** the biology is the best-supported of the three by *orthogonal* evidence (genetics + knockouts + chromatin-only state definition). The *measurement* in nuclear RNA is the most compromised of the three. Those are two different statements and must not be merged. In particular, the reported failures of Mathys/Zhou to recover a DAM signature are at least as easily explained by the Thrupp depletion as by absence of the biology.

---

## 5. PROGRAM 3 — Antigen presentation (HLA-DRA, HLA-DPA1, HLA-DMB, HLA-DMA, CD74, CTSS, IFI30)

### 5.1 Is the module real?

**Conclusion: yes — and unusually, this program is a known biochemical pathway, not just a correlation cluster.** — `PROTEIN/SPATIAL_SUPPORT`

Every gene in our Program 3 occupies a defined position in one mechanism, MHC class II peptide loading:

- **HLA-DRA / HLA-DPA1** — the class II heterodimers that display peptide.
- **CD74** — the invariant chain that occupies the groove during assembly and routes the complex to the endolysosome.
- **CTSS** — cathepsin S, which degrades the invariant chain down to CLIP. "Cathepsin S alone, in marked contrast with other endosomal proteases, was required for efficient Ii processing."
- **HLA-DMA / HLA-DMB** — HLA-DM, which exchanges CLIP for antigenic peptide.
- **IFI30** — GILT, the lysosomal thiol reductase that reduces disulfide bonds in internalised antigen so it can be processed.

Citations for the pathway:
- *Essential Role for Cathepsin S in MHC Class II–Associated Invariant Chain Processing and Peptide Loading.* **Immunity**, 1999. https://www.cell.com/AJHG/fulltext/S1074-7613(00)80249-6 — **[S]**
- *Human cathepsin S, but not cathepsin L, degrades efficiently MHC class II-associated invariant chain in nonprofessional APCs.* **PNAS**, 2003. https://www.pnas.org/doi/10.1073/pnas.1131604100 — **[S]**

**An important caution on this point.** Mechanistic coherence is a good reason to believe the genes *belong together*. It is **not** evidence that our data measured them independently. These genes share one transcriptional master regulator, CIITA, and share IFN-γ responsiveness; a single upstream signal — biological *or* technical — moves all seven together. A tight co-expression module here is the expected result under both the interesting hypothesis and the boring one. Labelled `SPECULATIVE` for any inference that tight co-expression of this module in our data indicates a distinct cell state.

**Conclusion: protein-level presentation machinery is demonstrated in human microglia.** — `PROTEIN/SPATIAL_SUPPORT`

Mass-spectrometry immunopeptidomics of human iPSC-derived microglia identified ~7,000 HLA class I and II presented peptides, with significant upregulation of HLA-DRA, HLA-DRB1, HLA-DRB5 in microglia versus iPSCs and further enhancement by IFN-γ; interactome data showed HLA-II complexes enriched for vesicular trafficking and antigen-processing proteins. This is the program doing its job, measured as protein, not inferred from RNA.

- *Large-scale HLA immunopeptidome and interactome profiling in microglia.* **bioRxiv** 2025, doi 10.1101/2025.04.23.650327. https://pmc.ncbi.nlm.nih.gov/articles/PMC12190351/ — **[F]** (Klaisner, Hao, Beilina, Park et al.)

Classical neuropathology agrees: MHC class II–positive microglia are markedly increased in AD, with cells clustered around senile plaque amyloid and neurofibrillary tangles, and with "darkly stained plump somata and short, thick processes."
- *MHC class II-positive microglia in human brain: association with Alzheimer lesions.* 1992. https://pubmed.ncbi.nlm.nih.gov/1484388/ — **[S]**

Mass cytometry finds HLA-DR<sup>hi</sup>/CD68<sup>hi</sup> microglia enriched in white matter versus grey — a spatial, protein-level gradient in the module.
- **Nature Neuroscience** 22:78–90, 2019. https://www.nature.com/articles/s41593-018-0290-2 — **[S]**

In multiple sclerosis, microglia downregulate TMEM119/CX3CR1/P2RY12 while upregulating CD74, HLA-DRA, HLA-DRB1, HLA-DPB1 — i.e. **Program 1 down, Program 3 up, measured together** in a disease unrelated to AD.
- https://www.frontiersin.org/journals/molecular-neuroscience/articles/10.3389/fnmol.2020.583811/full — **[S]**

**Conclusion: human genetics implicates the HLA locus in neurodegeneration.** — `GENETIC_SUPPORT`

- Multiancestry HLA analysis across >176,000 individuals found a shared adaptive-immune signal in AD and PD mediated by **HLA-DRB1\*04** subtypes.
  - *Multiancestry analysis of the HLA locus in Alzheimer's and Parkinson's diseases uncovers a shared adaptive immune response mediated by HLA-DRB1\*04 subtypes.* **PNAS** 120(36), 2023. https://www.pnas.org/doi/10.1073/pnas.2302720120 — **[S]**
- HLA-DRB5/HLA-DRB1 are late-onset AD susceptibility loci in European-ancestry meta-analysis. — **[S]**
- rs3129882 in **HLA-DRA** is associated with increased MHC-II transcript and surface protein and increased late-onset PD risk. — **[S]**
- The PD HLA locus "exhibits epigenetic regulation" — a chromatin-level link at this locus, though reducing MHC-II was insufficient to protect mice from α-synuclein-induced degeneration.
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11908218/ — **[S]**

**Honest caveat specific to HLA:** the HLA region has extreme linkage disequilibrium, extreme polymorphism, and poor short-read mappability. An HLA GWAS signal supports "adaptive immunity matters" more securely than it supports "this particular microglial program is the causal actor." Labelled `GENETIC_SUPPORT` for the locus, `SPECULATIVE` for the microglia-specific causal attribution.

**Conclusion: induction of the module is demonstrated.** — `PERTURBATIONAL_SUPPORT`

IFN-γ is the canonical inducer of MHC-II on microglia; IFN-γ from memory CD8+ T cells upregulates microglial MHC-II and sustains activation, and CD8+ T cells are elevated in human AD brain and localise near microglia. The cross-pathology taxonomy showed *in vivo* that activation-associated microglial states depend on interferon and CSF1R signalling. The PLCG2-P522R protective AD variant promotes antigen-presentation gene expression in human microglia in an AD mouse model.

- https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2017.01905/full — **[S]**
- *A transcriptomic microglia taxonomy across mouse and human pathologies.* **Nature Immunology**, 2026. https://www.nature.com/articles/s41590-026-02472-z — **[S]**
- *The P522R protective variant of PLCG2 promotes the expression of antigen presentation genes by human microglia in an Alzheimer's disease mouse model.* **Alzheimer's & Dementia**, 2022. https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.12577 — **[S]**

**Conclusion: the module appears as a recurrent cluster in human transcriptomic studies.** — `RNA_ONLY_REPLICATION`

CD74 marks Olah cluster 7, the antigen-presentation cluster; xenografted human microglia show "a more pronounced HLA state" than mouse microglia in the same amyloid brain. — **[S]**

**The direction of change in AD is contested. This is a genuine unresolved conflict and I am not smoothing it over:**

| Measurement | Direction in AD |
|---|---|
| snRNA-seq cluster frequency | Antigen-presentation cluster frequency **diminished** in AD — **[S]** |
| Classical HLA-DR immunohistochemistry | **Increased** HLA-DR — **[S]** |
| Imaging mass spectrometry, hippocampus | **Decreased** HLA-DR protein; "microglia tend to lose antigen-presenting function" — **[S]** |

Three technologies, three answers. Any claim our project makes about the *direction* of Program 3 in disease must therefore be treated as unsettled by the literature, whichever way it comes out.

### 5.2 Strongest technical alternative for Program 3

**`KNOWN_TECHNICAL_ALTERNATIVE` — CD74 is a documented nuclear-depletion casualty, and this module is the most ambient-prone of the three.**

1. **CD74 is explicitly on Thrupp's depleted list** — one of only four genes named in the summary (APOE, CST3, SPP1, CD74). Our Program 3's most abundant member is measured worst in nuclei. — **[F]** (alzforum summary) / **[S]** (paper).
2. **MHC-II transcripts are highly expressed in microglia and perivascular macrophages**, so ambient RNA propagates them into other droplets, and any variation in ambient load across libraries appears as variation in the antigen-presentation score. The general mechanism is documented; I found **no** brain paper that specifically quantified HLA-module ambient leakage into microglial nuclei. That is an untested gap, not a cleared one.
3. **A single shared regulator makes the module technically fragile.** Because CIITA/IFN-γ coordinate all seven genes, *any* nuisance variable correlated with interferon tone — agonal state, infection at death, dissection temperature — reproduces the entire program coherently. Coherence is therefore not evidence against a technical origin here.
4. **White-matter content.** HLA-DR<sup>hi</sup> microglia are enriched in white matter — **[S]**. Variation in grey/white sampling proportion between donors or blocks produces an apparent antigen-presentation gradient with no change in any cell's state. This is a *dissection* confound, not a sequencing one, and it is the one most likely to be overlooked.

**Net assessment for Program 3:** real pathway, demonstrated at protein level, genetically implicated at the locus level. The weakest chromatin evidence of the three, the most contested direction of change, and a confound (white-matter fraction) that no computational correction addresses.

---

## 6. Cross-cutting: continuous transitions, branching, trajectories

**Conclusion: the field has moved to a continuum view, but largely on the strength of the same clustering methods it criticises.** — `RNA_ONLY_REPLICATION` for the empirical claim; `SPECULATIVE` for strong directional claims.

The consensus statements:
- *Microglia states and nomenclature: A field at its crossroads.* **Neuron** 110(21):3458–3483, 2022. doi 10.1016/j.neuron.2022.10.020. https://pubmed.ncbi.nlm.nih.gov/36327895/ — **[S]** (Paolicelli, Sierra, Stevens, Tremblay, Aguzzi, Ajami et al.). Rejects "resting vs activated" and "M1/M2" dichotomies.
- *A dynamic and multimodal framework to define microglial states.* **Nature Neuroscience**, 2025. https://www.nature.com/articles/s41593-025-01978-3 — **[S]** (paywalled; could not fetch).
- Review literature explicitly identifies "a methodological over-reliance on computational clustering algorithms… with arbitrary cluster numbers being interpreted as biological reality." https://www.scienceopen.com/hosted-document?doi=10.15212%2Fnpt-2025-0015 — **[S]**

Evidence for branching rather than a single axis — **`RNA_ONLY_REPLICATION`**:
- Gerrits et al.'s AD1 (amyloid-associated, lipid/phagocytic) and AD2 (tau-associated) are *two different destinations*, not one severity scale. Our Programs 2 and 3 could correspond to distinct branches rather than distinct points on one trajectory. This is a concrete, testable structural prediction. https://pmc.ncbi.nlm.nih.gov/articles/PMC8043951/ — **[S]**
- Mancuso et al. report separate DAM, HLA, and cytokine (CRM) responses co-existing in the same amyloid brain — again branching, not a ladder. — **[S]**
- Fate-mapping showed developmental PAM transition into DAM and WAM states, with shared enhancers — a genuine lineage-tracked transition rather than an inferred one. — **[F]**/**[S]**

**`KNOWN_TECHNICAL_ALTERNATIVE` — apparent trajectories are a documented artifact class.**

This is important and specific: *"Low-quality libraries generated from different cell types can cluster together based on similarities in damage-induced expression profiles, creating artificial intermediate states or trajectories between otherwise distinct subpopulations,"* and *"doublets can be mistaken for intermediate populations or transitory states that do not actually exist."* Worse for us, doublet detection is itself unreliable in trajectory data, because genuine intermediate cells look like doublets by construction.

- *Orchestrating Single-Cell Analysis with Bioconductor* — Quality Control and Doublet Detection chapters. https://bioconductor.org/books/3.13/OSCA.basic/quality-control.html · https://bioconductor.org/books/3.15/OSCA.advanced/doublet-detection.html — **[S]**
- *DoubletFinder.* **Cell Systems** 8(4), 2019. https://www.cell.com/cell-systems/fulltext/S2405-4712(19)30073-0 — **[S]**
- *Scrublet.* **Cell Systems** 8(4), 2019. https://www.cell.com/cell-systems/fulltext/S2405-4712(18)30474-5 — **[S]**
- Additional: *"Some clusters showed a gradient of expression and chromatin accessibility, resulting in their distinction as separate clusters, although they were not physically distinct"* — a quality gradient producing apparent clusters **in chromatin data too**. — **[S]**

**RNA velocity should not be used as our directional evidence.** — `KNOWN_TECHNICAL_ALTERNATIVE`
Documented failure modes include incorrect negative velocities from transcription-rate changes, erroneous directions in mature cell types, and a projection step that makes a cell's velocity depend largely on its nearest neighbours' expression rather than on real dynamics.
- *RNA velocity—current challenges and future perspectives.* **Molecular Systems Biology** 17:e10282, 2021. https://link.springer.com/article/10.15252/msb.202110282 — **[S]** (Bergen et al.)
- Zheng et al. 2023 projection critique — **[S]**, via the above.

---

## 7. The question that matters most for our next step: do technical confounds move RNA and ATAC together?

We asked specifically whether published work shows confounds affecting **RNA and ATAC in a correlated way from the same nucleus**. This determines whether RNA↔ATAC agreement is meaningful evidence or a shared artifact.

### 7.1 What the literature actually says

**Finding 1 — the only direct measurement we found says the two modalities' ambient contamination is *uncorrelated*.** — `KNOWN_TECHNICAL_ALTERNATIVE` (bounded)

Ambimux models ambient fractions separately for RNA and ATAC within each 10x Multiome droplet. *"The ambient fractions between modalities were weakly correlated… with a Spearman coefficient of 0.08,"* suggesting *"background contamination of RNA and ATAC molecules occurs independently."* Mean contamination ≈7% (RNA) and ≈6.3% (intra-peak ATAC). Contamination reduced power for differential-abundance detection and produced *"potentially more spurious associations"* in gene–peak linkage analysis.

- *Integrated ambient modeling and genetic demultiplexing of single-cell RNA+ATAC multiome experiments with Ambimux.* **bioRxiv** 2025, doi 10.1101/2025.08.21.671671. https://pmc.ncbi.nlm.nih.gov/articles/PMC12407767/ — **[F]** (Alvarez et al.)

**This is good news, with a caveat that must not be dropped: the tissue was visceral adipose, not brain.** Brain has the additional neuronal-ambient problem documented above, which adipose does not. Do not carry the 0.08 figure into a brain context as if it had been measured there.

**Finding 2 — the gene-activity bridge between the modalities is weak.** — `KNOWN_TECHNICAL_ALTERNATIVE`

In matched multimodal snATAC/snRNA data, *"within broad cell types… there was minimal correlation between real gene expression and five different GAS [gene activity score] methods,"* and *"differential accessibility region strength was positively dependent on sequencing depth,"* with label-transfer scores also depth- and cell-count-dependent.

- *Defining effective strategies to integrate multi-sample single-nucleus ATAC-seq datasets via a multimodal-guided approach.* **bioRxiv** 2025, doi 10.1101/2025.04.02.646871. https://www.biorxiv.org/content/10.1101/2025.04.02.646871 — **[S, snippet only — fetch returned HTTP 429]**
- *Is single nucleus ATAC-seq accessibility a qualitative or quantitative measurement?* **bioRxiv** 2022. https://www.biorxiv.org/content/10.1101/2022.04.20.488960 — **[S]**
- *Uniform quantification of single-nucleus ATAC-seq data with Paired-Insertion Counting.* **Nature Methods**, 2023. https://www.nature.com/articles/s41592-023-02103-7 — **[S]**
- *Depth-corrected multi-factor dissection of chromatin accessibility for scATAC-seq data with PACS.* PMC. https://pmc.ncbi.nlm.nih.gov/articles/PMC11701134/ — **[S]**

**Direct consequence for us: if we score ATAC "expression" of P2RY12 or APOE via a gene-activity score and correlate it with RNA, a weak or absent correlation is the documented default even when the biology is fine.** A negative result from that design would be uninterpretable. Peak-level and motif-level analyses, and depth-matched comparisons, are the defensible route.

**Finding 3 — shared technical axes that plausibly hit both modalities.** — `SPECULATIVE` (mechanism plausible, not demonstrated for brain multiome)

- **Nucleus fragility/integrity** affects ATAC directly (TSS enrichment, nucleosome signal) and RNA content simultaneously; neuronal nuclei show systematically lower TSS enrichment and higher QC exclusion "likely reflecting… nucleus fragility." — **[S]**
- **Apoptotic/degraded free DNA is tagmentable by Tn5**, producing false accessibility signal — a damage-linked ATAC artifact that would co-occur with RNA degradation in the same tissue. — **[S]**
- **Nuclei:Tn5 stoichiometry** is a per-library batch effect on ATAC depth; it does not affect RNA, so it is a *modality-specific* confound that would *weaken* apparent RNA–ATAC agreement rather than manufacture it.
  - *Reducing batch effects in single cell chromatin accessibility measurements by pooled transposition with MULTI-ATAC.* PMC. https://pmc.ncbi.nlm.nih.gov/articles/PMC11870453 — **[S]**
- **Freeze–thaw and cryopreservation method** change the number of open chromatin regions recovered from frozen brain tissue; flash-frozen cells are unsuitable for ATAC while slow-cooled cryopreserved cells work.
  - *Protocol for single-nucleus ATAC sequencing and bioinformatic analysis in frozen human brain tissue.* **STAR Protocols**, 2022. https://pmc.ncbi.nlm.nih.gov/articles/PMC9218237/ — **[S]**
  - *Cell type-specific chromatin accessibility analysis in the mouse and human brain.* **Epigenetics**, 2021. https://www.tandfonline.com/doi/full/10.1080/15592294.2021.1896983 — **[S]**
  - *Cell freezing protocol suitable for ATAC-Seq on motor neurons derived from human induced pluripotent stem cells.* **Scientific Reports** 6:25474, 2016. https://www.nature.com/articles/srep25474 — **[S]**
- **Nuclei isolation protocol changes cell-type proportions.** A systematic comparison of three isolation strategies found "protocol-dependent differences in cell type proportions, transcriptional homogeneity, and preservation of cell-type-specific and cell-state-specific markers."
  - *Comparative analysis of nuclei isolation methods for brain single-nucleus RNA sequencing.* 2025/2026. https://www.sciencedirect.com/science/article/pii/S2667237526000378 · https://www.biorxiv.org/content/10.1101/2025.03.25.645306 — **[S]**
- **Microglia are especially vulnerable to QC thresholds**, because they "often have a smaller number of unique transcripts than other cell types, likely due to their biological size," so a uniform UMI threshold "can potentially exclude microglia from analysis not because they're low quality, but because they express fewer transcripts." A threshold applied to *nuclei* therefore selects non-randomly *within* the microglial population — and if activation state correlates with transcript content, the selection is on state.
  - *All the single cells: single-cell transcriptomics/epigenomics experimental design and analysis considerations for glial biologists.* arXiv 2408.06521. https://arxiv.org/pdf/2408.06521 — **[S]**
  - *Automatic quality control of single-cell and single-nucleus RNA-seq using valiDrops.* **NAR Genomics and Bioinformatics** 5(4):lqad101, 2023. https://academic.oup.com/nargab/article/5/4/lqad101/7429070 — **[S]**

### 7.2 The honest verdict on section 7

**No published study we could find directly tests whether nucleus-level damage drives RNA and ATAC in a correlated way in brain multiome data.** Our own searches on this repeatedly returned the observation that the topic "does not appear to have been extensively covered in the available literature."

That is the correct and useful answer, and it is the opposite of reassuring: **the literature neither supports nor refutes the shared-confound hypothesis for our design, so our design has to test it internally.** Concretely, the minimum internal controls implied:

1. Regress program scores on per-nucleus quality in **both** modalities (RNA UMIs/genes detected; ATAC fragments, TSS enrichment, FRiP, nucleosome signal) and report whether program structure survives.
2. Depth-match before comparing conditions, given the documented depth-dependence of differential accessibility.
3. Do not rest RNA↔ATAC agreement on gene-activity scores.
4. Treat donor-level handling history (not merely recorded PMI) as the confound of record for Program 1, since `exAM` enrichment was explicitly *uncorrelated* with PMI.
5. Record grey/white matter fraction per sample as a Program 3 covariate.

---

## 8. Summary table of conclusions

| # | Conclusion | Label |
|---|---|---|
| C1 | The homeostatic module is a real, causally-anchored program: SALL1 deletion dismantles it | `PERTURBATIONAL_SUPPORT` |
| C2 | The homeostatic module has an enhancer-level basis; IRF8-driven accessibility change preceded transcriptome change (mouse, developmental) | `DIRECT_MULTIMODAL_SUPPORT` |
| C3 | P2RY12/TMEM119 protein loss is real and plaque-localised, and the two markers dissociate spatially | `PROTEIN/SPATIAL_SUPPORT` |
| C4 | Repeated human snRNA-seq recovery of the homeostatic cluster adds breadth only | `RNA_ONLY_REPLICATION` |
| C5 | Tissue handling (`exAM`) reproduces homeostatic-marker loss; present in human postmortem data; **uncorrelated with PMI** | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C6 | Human genetics independently nominates TREM2, APOE, GPNMB, ABCA7 and microglial enhancers | `GENETIC_SUPPORT` |
| C7 | The DAM/lipid module is causally constructed: TREM2 and APOE deletion modulate it in human xenografted microglia; CSF1R inhibition depletes a disease state | `PERTURBATIONAL_SUPPORT` |
| C8 | Microglial states — including DAM — can be defined from chromatin accessibility alone, with GWAS heritability enriched in state-specific peaks | `DIRECT_MULTIMODAL_SUPPORT` |
| C9 | Lipid-droplet microglia are directly visualised, not inferred | `PROTEIN/SPATIAL_SUPPORT` |
| C10 | snRNA-seq under-detects APOE and CD74 specifically (~18% of DAM genes); human DAM replication is inconsistent partly for this reason | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C11 | Ambient RNA can supply APOE/MHC-II signal into microglial droplets; decontamination changes which states appear | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C12 | Program 3 is a single defined biochemical pathway (CD74→CTSS→CLIP→HLA-DM→peptide; IFI30 reduction) | `PROTEIN/SPATIAL_SUPPORT` |
| C13 | Human microglia genuinely present antigen: ~7,000 HLA-presented peptides, IFN-γ-inducible | `PROTEIN/SPATIAL_SUPPORT` |
| C14 | HLA-DRB1\*04 / HLA-DRA / HLA-DRB5 variants associate with AD and PD | `GENETIC_SUPPORT` |
| C15 | Attributing the HLA GWAS signal specifically to this microglial program | `SPECULATIVE` |
| C16 | IFN-γ and T cell contact induce the antigen-presentation module | `PERTURBATIONAL_SUPPORT` |
| C17 | Direction of Program 3 change in AD is contested across RNA, IHC and imaging mass spectrometry | (unresolved; reported, not concluded) |
| C18 | White-matter sampling fraction can produce an apparent antigen-presentation gradient with no state change | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C19 | Microglial states are better described as a continuum with branches (amyloid vs tau; DAM vs HLA vs cytokine) than as a single severity axis | `RNA_ONLY_REPLICATION` |
| C20 | Low-quality libraries and doublets are documented to create artificial intermediate states and trajectories, including quality gradients producing apparent clusters in chromatin data | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C21 | RNA velocity is not a safe source of directional evidence for us | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C22 | The only direct measurement found reports RNA and ATAC ambient contamination are near-independent (Spearman 0.08) — but in adipose, not brain | `KNOWN_TECHNICAL_ALTERNATIVE` (bounded) |
| C23 | Gene-activity scores correlate minimally with measured RNA within broad cell types; differential accessibility is depth-dependent | `KNOWN_TECHNICAL_ALTERNATIVE` |
| C24 | Nucleus damage as a *shared* RNA+ATAC confound in brain multiome is **untested in the literature** | `SPECULATIVE` |
| C25 | Uniform UMI thresholds select microglia non-randomly, potentially on activation state | `KNOWN_TECHNICAL_ALTERNATIVE` |

---

## 9. MANDATORY SELF-AUDIT

### 9.1 Provenance

| Item | Value |
|---|---|
| Starting SHA | `1ceaf3e9a3de15cd2386da7398e8620510ed8be1` |
| Branch | `lane/laneH-literature-20260928` |
| Worktree | `D:/jepa_wt_laneH-literature_20260928` |
| Worktree status at start | clean (`git status --porcelain` empty) |
| Final SHA | recorded in `D:/jepa_v5_outputs_20260925/out_laneH-literature/laneH_selfaudit_receipt.json` after commit |
| Files changed | 1 added: `docs/laneH_microglial_program_literature_plausibility_audit_20260928.md` (documentation, literature only) |
| Other worktrees touched | NONE |
| Other branches touched | NONE |
| Push | NOT performed (per instruction) |

### 9.2 Data access attestation

- **Project data opened: NONE.** No `.h5ad`, `.h5`, `.zarr`, `.npy`, `.parquet`, expression matrix, fragment file, metadata table or results artifact was read.
- **Protected outcome variables read: NONE.** No pathology outcome, donor-level phenotype, or held-out readout was accessed.
- **Training: OFF.** No model was trained, loaded or evaluated.
- Gene symbols used in this report are public marker genes taken from the lane brief; no values from project data are quoted anywhere.

### 9.3 Evidence class of this lane

**This lane's evidence class is LITERATURE. It is never confirmatory for our target.** Nothing in this report qualifies, validates, or partially validates any target. It establishes prior plausibility and enumerates confounds to be tested with our own data. A downstream document that cites this report as support for a target claim would be misusing it.

### 9.4 Strongest KNOWN_TECHNICAL_ALTERNATIVE for each program

**Program 1 (homeostatic): tissue handling temperature history.** The `exAM` artifact (Marsh et al., **Nature Neuroscience** 2022) causes microglia to lose homeostatic markers, is detectable in human postmortem snRNA-seq, is inducible by a few hours at room temperature in fresh human tissue, and — critically — **does not correlate with recorded postmortem interval**. Any donor- or batch-level difference in homeostatic program score is confounded by a variable that is usually not recorded and cannot be adjusted for using PMI.

**Program 2 (lipid/phagocytic/DAM): nuclear depletion of the program's own genes, plus astrocytic ambient APOE.** Thrupp et al. (**Cell Reports** 2020) showed APOE among ~246 genes significantly depleted in nuclei versus whole cells, covering 18% of the microglial disease-associated gene set. Simultaneously, APOE is an abundant astrocyte transcript that ambient contamination distributes into all droplets. The program can therefore be *understated* by nuclear chemistry and *overstated* by ambient leak, in the same experiment, with the balance varying by library. The already-documented failure of some large human studies to recover a DAM signature shows this is not hypothetical.

**Program 3 (antigen presentation): CD74 nuclear depletion plus grey/white matter sampling fraction.** CD74 is explicitly named in Thrupp's depleted set. Independently, HLA-DR<sup>hi</sup>/CD68<sup>hi</sup> microglia are enriched in white matter, so differences in white-matter content between blocks, regions or donors generate an apparent antigen-presentation gradient without any cell changing state. No computational correction addresses a dissection difference. Compounding both: the module's seven genes share one regulator (CIITA/IFN-γ), so any nuisance variable correlated with interferon tone reproduces the whole program coherently — meaning internal coherence of this module is *not* evidence against a technical origin.

### 9.5 Strongest criticism of my own report

Numbered as self-audit items, continuing the project's S-series.

**S-H1 — Most of my evidence is search-snippet-level, not read-in-full. This is the report's biggest weakness.** Only six sources were fetched and read directly (**[F]**): Marsh 2022 (PMC), the Hamagami enhancer preprint (PMC), Han *et al.* Nature Communications (PMC), Ambimux (PMC), the microglial immunopeptidome preprint (PMC), and an Alzforum summary of Thrupp. Everything else is **[S]** — a search engine's paraphrase. Paraphrases drop caveats, and I have reproduced several numbers (18% of DAM genes; 246 genes; Spearman 0.08 in adipose; 94% posterior probability at GPNMB) that I have not verified against the papers' own text except where marked **[F]**. *Status: open. Not closable by this lane.* Cell.com, Nature and PubMed all returned 403/CAPTCHA, so full-text verification was not available here. Anyone relying on a specific number above should re-verify it at source.

**S-H2 — I very likely over-read `DIRECT_MULTIMODAL_SUPPORT` in at least three places.** Naming them explicitly:

- **C2 (IRF8 accessibility preceding transcription).** This is mouse, postnatal, developmental. I applied it to a human adult disease-state question. The word "preceded" is doing heavy lifting and came from a snippet.
- **The Hamagami enhancer paper.** The full text I *did* fetch says plainly that chromatin changes **accompany rather than precede** transcription and that the study "primarily documents simultaneous changes rather than demonstrating causal precedence." I have flagged this inline, but the risk remains that the citation gets reused elsewhere as though it showed chromatin leads RNA. It does not.
- **Morabito 2021.** I described it as profiling both modalities "in the same samples," and one source called it same-nuclei. The numbers I recorded (130,418 ATAC nuclei; 61,472 RNA nuclei) are *different counts*, which is more consistent with parallel assays on matched samples than with true same-nucleus multiome. **I did not resolve this, and I may have overstated the modality pairing.** Treat as unresolved.

**S-H3 — I let a mechanistically satisfying story stand in for independence, for Program 3.** The MHC-II pathway narrative (CD74 → CTSS → CLIP → HLA-DM → peptide, with IFI30 reducing disulfides) is genuinely elegant and it made me more confident than the evidence warrants. I flagged this inline, but the flag deserves repeating here because it is the exact failure mode that matters: **a module with one shared upstream regulator will look internally coherent under a technical confound just as readily as under real biology.** Elegance is not independence.

**S-H4 — My confound search may still be under-powered relative to my support search, despite instructions to give equal effort.** I ran roughly comparable numbers of searches, but the support literature is far larger and better indexed, so equal search effort yields unequal evidence density. Specifically, I found **no** study that directly demonstrates a technical confound generating apparent *microglial-state substructure* (as opposed to generating an artifactual signature, or artifactual clusters in general). Absence of that paper is not evidence that such confounding does not occur — it may simply be that nobody has published the negative-control experiment. I should not be read as having cleared that possibility.

**S-H5 — I treated GWAS/eQTL evidence as cleanly orthogonal. It is orthogonal to *tissue handling*, but not to everything.** eQTL studies (MiGA, Young) measure microglial *expression* and inherit the same isolation and dissociation artifacts as any other expression measurement — MiGA used acutely isolated microglia, which carries the `exAM` dissociation risk Marsh documented. The genotype side is clean; the expression side is not. My `GENETIC_SUPPORT` label is correct for GWAS association, and slightly generous for colocalisation results that depend on an expression phenotype.

**S-H6 — I reported discordances without weighting them.** For Program 3, three technologies disagree about the direction of change in AD, and for Program 2 protein ApoE goes down while RNA APOE goes up. I listed these honestly but did not assess which measurement to believe. That is the right call for a literature lane — but it means this report **cannot** be cited as establishing the direction of change for either program, and a reader skimming the support sections might not notice that.

**S-H7 — A check that could not fail, in my own method.** The question "is there literature support for these programs?" is almost guaranteed to return yes for any set of well-known marker genes, because these genes are famous *because* they are heavily published. My search design cannot distinguish "this program is real" from "these genes are popular." The only parts of this report that could genuinely have come back negative — and therefore the only parts carrying real information — are: (a) the knockout results, which could have shown the program does not collapse; (b) the chromatin-only state definitions, which could have failed to recover DAM; (c) the confound searches, which could have returned nothing. All three returned informative results, so the exercise was not vacuous. But the `RNA_ONLY_REPLICATION` sections were a foregone conclusion and should carry no weight at all.

**S-H8 — One citation is knowingly second-hand.** Keren-Shaul et al. 2017 (**Cell**), the origin of the DAM concept, is cited via reviews rather than retrieved directly. I have marked it `[S, indirect]`. I did not fabricate a URL or DOI for it. Where I could not verify a first author from the sources I actually saw, I have given title/venue/year/URL without an author name rather than guess.

### 9.6 What would actually move the needle

None of the following exists yet for our system, and each is a real experiment rather than more reading:

1. Program scores regressed on per-nucleus quality in both modalities, showing the programs survive.
2. A negative control: nuclei matched on all quality metrics, differing only in program score, still showing the expected ATAC structure.
3. Peak-level (not gene-activity-score) RNA↔ATAC concordance at depth-matched libraries.
4. A handling-variation control that does not rely on recorded PMI.
5. Grey/white matter fraction measured per sample and shown not to explain Program 3.
