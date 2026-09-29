# JEPA new-chat handoff — V63 audited external-regulatory / target-authority state

Date: 2026-09-29
Status: AUDITED HANDOFF; TRAINING=OFF; TD60=BLOCKED
Immediate predecessor implementation/governance head audited live: PR #196, `chatgpt/v61-target-backbone-governance-20260928 @ 59791740187587f655ac69c721de4464ab9d7a9e`.
This handoff is a custody/documentation successor; it must not silently upgrade scientific qualification.

## 1. Scientific objective
Build a JEPA-like model for human brain single-cell/single-nucleus data in which the teacher observes richer biological evidence and the student predicts a query-conditioned biological cellular state from restricted evidence. The target is NOT the hidden queried gene scalar and must not collapse to technical capture/QC, arbitrary projections, donor/source/operator identity, or RNA normalization leakage.

## 2. Current scientific boundary
The central unresolved problem is biological specificity: same-RNA nulls are insufficient because same-cell latent technical capture can mimic relational biological structure. V48 established a semantic-twin non-identifiability boundary: if allowed observables are byte-identical and only their interpretation changes, no RNA-only statistic can force a biological world to pass and a technical twin to fail. Therefore the next target layer needs an independently constructed observable/modality plus a prospectively frozen nuisance class.

This does NOT mean the biology is absent. It means the current evidence cannot identify it with the required specificity.

## 3. Current RNA backbone candidate
The best current RNA-only discovery candidate is the source-balanced common covariance manifold: universal all-42-operator protein-coding features; global z/QC residualization and source centering; equal 1/3 covariance weighting across HVS/NPH52/SEA-AD; eigendecomposition of the common covariance; and donor-disjoint recurrence stress testing.

Key evidence: top-4 A/B mean principal-angle cosine ~0.9951; donor-disjoint rank-4 mean cosine ~0.9869/min ~0.9613; held-out-half biology trace eta2 ~0.3895, source ~0.0363, donor after source+class ~0.1168, SEA-AD operator after class ~0.1361. This argues against simple donor memorization, but remains `DISCOVERY_CANDIDATE__SOURCE_BALANCED_COMMON_STATE_BACKBONE`, not a biologically qualified final target. Source eta2 near zero is mechanically induced by source centering and must not be sold as biological deconfounding.

HVS/NPH52 operator/class are structurally aliased; do not use their operator residuals as clean technical metrics. SEA-AD operator conditional on class is usable.

## 4. q-safety is a separate prerequisite
The discovery expression archive was normalized using a library denominator that includes q. Therefore the current backbone is NOT q-safe for production use. A future student preprocessing rebuild must use either `q_excluded_total__q_token_dropped` or `fixed_reference__q_token_dropped`. Teacher target q-blindness is a separate requirement. Do not conflate student leakage (Q1) with teacher target determination (Q2).

## 5. Regulatory/cis synthetic evidence
V53–V57 showed that local cis geometry is biologically responsive but not sufficiently specific at realistic donor counts. V54 fully matched pseudo-cis benchmark primary margin was -0.0143 RED. Fresh V57 192-seed n18 margin was -0.0287. Power was nonmonotonic and SEA-AD-like n15 / GSE272082 n9 were below the gate. Do not open real biology to tune this benchmark.

V58/V59 external-anchor synthetic benchmark separated represented nuisance arms from positives, but an anchor-keyed semantic twin (NEG5) was byte-identical to the positive and passed 1.0. Therefore it is qualified only within its represented nuisance class. A historical result-byte attestation was withdrawn because the claimed digest did not match the observed digest; the synthetic scientific finding remains, but not the byte-attestation claim.

## 6. Corces route — STOP for target construction
The full public Corces GSE147672 H3K27ac HiChIP + scATAC route was reconstructed without DUA and without RNA-derived edge construction. The clean contact object used q<.01, >=2 donors, both anchors accessible, hg38 coordinate identity. It was structurally valid and enriched over a distance-matched null.

However the all-24-cluster fit-for-purpose test failed for microglia: Cluster24 microglia ranked 22/24 for contact/accessibility enrichment (~6.35x), while oligodendrocyte/OPC clusters ranked highest and a doublet cluster ranked third. A size-matched OPC comparator still materially outperformed microglia. This is a substrate-fit failure, not evidence that microglial biology is absent. Do not build positives on the Corces contact object and do not open Morabito to rescue it.

Donor correction: Supplementary Data Set 2 defines full `Donor_ID` as the individual identifier. scATAC has 8 distinct individuals: 03_39, 04_38, 06_0615, 09_1589, 09_35, 11_0393, 14_0586, 14_1018. Earlier six-donor parsing collapsed two distinct 09_* and two distinct 14_* donors and is superseded. Cross-assay same-person mapping to HiChIP remains likely but unproven.

## 7. External validation datasets and exposure
Morabito GSE174367: separate-nucleus RNA/ATAC from 18 shared donors; valuable donor-level validation because it breaks same-nucleus quality confounding. Prior RNA Stage75F/coactivity development and marginal ATAC coverage/accessibility exposure exist. Treat exposure at outcome-family granularity. The protected target-state cis correspondence outcome remains unopened in this handoff. Do not tune on Morabito.

GSE214979: paired multiome; metadata/depositor support same-nucleus pairing but the 1.369GB HDF5 common-barcode verification was historically not physically completed. Frozen exclusions produce 12 donors, 92,957 nuclei, 2,872 microglia. Possible UCI donor overlap with Morabito remains unresolved.

GSE272082: corrected to 9 donors (4 sEOAD, 5 control), with NIH NeuroBioBank and UTHealth sources. No public identity bridge to Kosoy; overlap unresolved. Paired-by-construction claim still needs primary matrix verification. Microglia counts need acquisition/annotation.

SEA-AD exact paired subset is internal to FULL104 and same-nucleus, so it is not independent confirmation.

## 8. Controlled-access boundary
The user explicitly decided not to pursue institutional DUA. Controlled-access Kosoy/FreshMicro donor crosswalk or distributed enhancer-gene objects are out of scope as load-bearing evidence. Do not suggest DUA again unless the user explicitly reverses that decision.

## 9. Governance / authority state
PR #196 is the latest audited implementation/governance head for this handoff. It contains versioned successors for biological-specificity authority, q-safety authority, critical-test execution receipts, V3 authority closure, V3 trainer preexecution, V3 teacher-target receipt, training authority/policy successor, q-safe preprocessing, optimizer guard V4, and CI/tests.

Important: verify CI and exact remote bytes before treating these successors as closed. Historical V1/V2 authority paths must not silently remain an alternate route once V3 is selected. Until the complete closure chain is demonstrated, `TRAINING=OFF` and `TD60=BLOCKED` remain controlling.

## 10. Current external-data pivot
The next resource must be microglia-native at the regulatory-link level, not merely another generic brain ATAC or bulk HiChIP dataset. Ideal evidence is public/no-DUA human primary or iPSC-derived microglia with a direct enhancer→promoter/gene relation: promoter Capture Hi-C/Capture-C, HiChIP/PLAC-seq, CRISPRi/Perturb-seq/causal mapping. Prefer genome-wide/broad construction, hg38/stable IDs, no RNA covariance used to define edges, and a design that permits an independent fit-for-microglia comparator before protected outcomes are opened.

Priority public candidates identified for deep audit:
1. GSE173316 — reported microglia-specific promoter Capture Hi-C plus ATAC/RNA/scRNA and CRISPRi/HyPR-seq context. Audit whether the distributed promoter-contact map itself is broad/genome-wide versus disease-locus-conditioned downstream.
2. GSE207628 — related pooled CRISPRi in microglia targeting cCREs near TREM2, PICALM, BIN1, INPP5D, SLC24A4/RIN3. Likely too locus-limited as the whole construction object, but potentially valuable orthogonal causal validation.
3. GSE293118/GSE293119 — newer public promoter Capture-C/ATAC/microglial CRISPRi resource; likely GWAS-directed. Determine whether the underlying Capture-C object is broad enough for construction or only suitable as supporting/causal validation.

## 11. NIH-CARD paired RNA/ATAC schema probe now in chat custody
This chat contains a bounded, outcome-blind .h5ad schema probe plus fixtures/receipts. Its purpose is strictly mechanical: identify raw-count matrix slots, verify RNA/ATAC barcode namespace and donor-label agreement, and count microglia per donor/cohort without computing RNA–ATAC relationships. Preserve that exposure boundary. Do not use the probe as biological validation.

## 12. Chat-exclusive custody policy
Prior Project-mounted foundation/checkpoint archives are not reclassified as chat-exclusive merely because they are mounted here. V46 already SHA-indexed those. R2/R4 recovered archives are already mirrored or SHA-pinned by V52 and should not be redundantly duplicated unless exact-byte recovery requires it.

The V63 custody manifest distinguishes exact bytes mirrored, SHA/size indexed but not duplicated, prior-project assets intentionally not re-added, and generated custody bundles. Custody does not upgrade scientific evidence.

## 13. Next-agent instructions — execute in this order
1. Verify repository authority first: fetch PR #196 head and CI status; confirm branch/head SHA and changed-file set.
2. Verify V63 custody against remote tree/blob SHAs. Never call a hash-only binary “exact GitHub custody.”
3. Deep-audit GSE173316 before touching protected outcomes: cell model, donors/replicates, capture assay, bait universe, genome build, public processed artifacts, edge construction, disease-locus conditioning, RNA dependence, and freeze independence.
4. Audit GSE207628 and GSE293118/119 in parallel as causal/support candidates; explicitly classify construction-grade versus validation/support-only.
5. Design and freeze a prospective microglia-fit test before target overlap: comparator, nuisance class, pass/fail rule, outcome firewall.
6. Keep Morabito closed while selecting/tuning the external object.
7. Rebuild q-safe student preprocessing using one accepted normalization contract and physically test q intervention; keep teacher q-blindness separate.
8. Only after external-object construction + fit qualification + q-safety + governance closure define the combined target: source-balanced RNA common-state backbone + query-specific external regulatory neighborhood.
9. Training remains OFF. Do not execute TD60 or optimizer/training until all authority roots and execution receipts are physically satisfied under the successor chain.

## 14. Red-team questions
- Is the external regulatory object genuinely independent of the RNA covariance it is supposed to validate?
- Is it microglia-fit, or merely technically clean?
- Is it genome-wide/broad enough to avoid disease-locus selection bias?
- Could same-cell capture/quality still generate the apparent correspondence?
- Are donor identities/replicates the true independent units?
- Was any protected real outcome inspected before the design and nuisance class were frozen?
- Is q absent from both the student evidence path and the teacher target construction where required?
- Can an older authority path still authorize training without the new roots?

## 15. Controlling interpretation
The project has not failed to find biology. It has repeatedly eliminated target constructions that were technically plausible but insufficiently identifiable or insufficiently microglia-specific. The source-balanced RNA backbone remains promising discovery structure. The highest-value next move is to find and freeze a genuinely microglia-native, public, independently constructed regulatory neighborhood object, qualify its substrate fit before protected outcomes, then combine it with a q-safe RNA state backbone under the successor authority chain.
