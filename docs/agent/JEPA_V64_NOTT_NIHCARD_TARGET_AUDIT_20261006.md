# JEPA V64 Nott / NIH-CARD target-lineage audit

Date: 2026-10-06
Branch: `audit/td34-genealogy-s149-20261006`
Status: `NOTT_E2_IS_VALID_CANDIDATE_REGULATORY_SCAFFOLD__NIHCARD_CORRESPONDENCE_NOT_OPENED__EVIDENCE_INDEPENDENCE_CONFOUNDED__NO_TARGET_AUTHORITY`

## Why this audit was done

The post-V47 audit identified the strongest current target hypothesis as a recurrent RNA relational/common-state backbone plus an independently constructed regulatory object. Historical V63 records had treated Nott Table S5 recovery as incomplete. The current Project Library physically contains the Nott Table S5 workbook, and repository history contains a much more extensive V64 Nott/NIH-CARD lineage. This audit reconciles that later work before any new target experiment is proposed.

Training remains OFF. Morabito remains protected. No new biological correspondence is opened in this audit.

## Nott asset recovery and historical E2 construction

The Nott Table S5 workbook is present in the Project environment and matches the historical V64 source identity:

- local SHA-256: `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`
- sheets include `Microglia interactome`, `Microglia enhancers`, and `Microglia promoters`.

Historical V64 already converted this substrate into `E2_NOTT_CANDIDATE` under explicit coordinate/provenance rules. The committed construction contains:

- 20,709 promoter-distal edges;
- 5,253 distinct genes;
- 7,390 promoter anchors;
- full attrition accounting from 104,802 source interactions;
- C3/liftOver identity handling and later audits;
- no protected target or NIH-CARD correspondence opened during E2 construction.

Therefore no new E2 construction should be performed from scratch.

## E2 scope

E2 is useful because it is constructed from chromatin contact/accessibility evidence rather than from the RNA relational outcome it would later constrain. It is therefore a materially cleaner regulatory scaffold than an RNA-derived gene/program target.

But its internal evidence is not independent in the strongest sense: Nott contact and accessibility evidence arise from the same study/source material. V64 correctly treated it as a candidate scaffold rather than biological validation.

## NIH-CARD realism and correspondence status

Historical V64 NIH-CARD work authenticated/pair-mapped the independent substrate and spent substantial effort qualifying negative controls, nuisance adjustment, matched controls, structural support and precision.

A critical distinction survives the audit:

**the real E2 biological correspondence was not opened.**

The realism and Phase-A work were qualification machinery, not target-validation results.

The historical realism stress test also exposed a serious limitation: the harder out-of-span technical negative was not controlled adequately, while the exact semantic twin remained observationally identical to the biological positive. Thus the V48 theorem-level identifiability boundary was not solved by these controls.

## Phase-A iterative audit

The original Phase-A funnel was explicitly rejected as current authority. Independent audit identified control-universe, C3 round-trip, side-draw, second-control, anchor-frequency, candidate-search and artifact-binding defects.

A later bounded-rejection design was also rejected: a finite 512-proposal search could falsely declare that no admissible control exists.

The exact interval-algebra successor improved this substantially, but the final canonical audit at commit `23255baaf81381d5c22c655a605642db27f2a173` still found a completeness defect: valid 5-kb controls crossing a liftOver chain-block boundary could be omitted. Required repair was an exact boundary supplement plus strand/completeness checks.

At that canonical branch head:

- exact sampler = `NOT_YET_QUALIFIED`;
- Phase-A rerun blocked;
- Phase B stopped;
- Stage 4 not authorised;
- correspondence opened = false.

This is the correct V64 terminal for the canonical ChatGPT successor branch.

## Later Claude branch: evidence-independence audit

The later Claude V64 branch did not claim a target result. It instead tested whether Nott/E2 support and NIH-CARD RNA measurability behave like independent evidence sources.

They do not.

Using precomputed column marginals with correspondence still sealed:

- E2-anchored, RNA-measurable genes: median microglial detection ≈ 0.043;
- RNA-measurable but unanchored genes: median ≈ 0.009;
- ratio ≈ 4.92x;
- within anchored genes, degree>=10 median detection ≈ 0.168 vs degree-1 ≈ 0.030, ratio ≈ 5.57x.

Interpretation: Nott active-promoter/contact evidence and NIH-CARD RNA detectability share an activity/measurement bias toward highly expressed/open genes. Therefore apparent support from both resources is not automatically two independent confirmations.

This is not evidence that E2 is wrong. It is evidence that evidence-independence must be measured rather than counted by resource name.

## Historical-spillover decisions

Do not carry forward any of the following as target authority:

1. V64 E2 construction success: proves scaffold construction, not biological target validity.
2. NIH-CARD authentication/pairing: proves data identity and pairing, not biological correspondence.
3. Realism-control PASSes inside represented nuisance families: conditional evidence only.
4. Phase-A 15,646-edge funnel: superseded by structural-control defects.
5. Exact interval-algebra spot checks: not full admissible-set completeness.
6. Nott + NIH-CARD being two named resources: not evidence independence because activity/detection bias is shared.
7. Nott degree concentration: partly expression/activity-confounded and must not be interpreted as pure regulatory information mass.

## Updated target architecture judgment

The strongest current scientific direction is no longer a single fused target.

Use a **factorized target hypothesis**:

- `Z_global`: recurrent RNA biological/common-state geometry;
- `Z_query`: query-conditioned local RNA state where independently justified;
- `Z_reg`: regulatory state constrained by a prospectively qualified external object such as E2;
- later `Z_response`: perturbational/interventional state only when separate causal evidence exists.

These objects should be kept distinct and required to agree only on prospectively defined biological relationships. A modality/resource must not earn extra authority merely because its signal correlates with another modality that shares gene activity/measurement bias.

## Current ranking

1. **Factorized recurrent-RNA + independently qualified regulatory-state family** — strongest target hypothesis; not yet qualified.
2. **V61/TD56–TD59 recurrent RNA relational/common-state backbone** — strongest RNA substrate; same-assay semantic-twin boundary remains.
3. **PR #163 value-blind query-local family** — still live as a component candidate; not a solution to same-assay biological identifiability.
4. **TD41/TD43** — useful reliability evidence, lower priority than later cleaner relational lineage.

`TARGET_WINNER=NONE_QUALIFIED`

## Next action

Do not execute Phase B or open E2 biological correspondence yet.

The next target-lane action is to audit the later **factorized-target / four-family representation tournament** already present in project history (global vs query-local vs program/subspace vs structured/factorized combined representation). Determine whether it already specifies a scientifically cleaner target object that incorporates the V48/V64 independence lessons, or whether a new prospective factorized tournament is still required.

The audit must check for:

- provenance of each component;
- S149 study/operator sensitivity;
- independence/shared-bias between evidence channels;
- donor-primary estimand;
- biological versus measurement OOD separation;
- subspace versus coordinate stability;
- query-self/value leakage;
- whether any historical outcome was seen before design choices were frozen.

`TRAINING=OFF`
`TD60=BLOCKED`
`STAGE4=NOT_AUTHORIZED`
`MORABITO=PROTECTED`
