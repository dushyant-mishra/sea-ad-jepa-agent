# JEPA V3 four-family prefreeze vs V64 factorized-target audit

Date: 2026-10-06
Branch: `audit/td34-genealogy-s149-20261006`
Status: `V3_RNA_FAMILY_PREFREEZE_SOUND__DOES_NOT_RESOLVE_V48_V64_BIOLOGICAL_IDENTIFIABILITY__FACTORIZED_EXTERNAL_REGULATORY_FAMILY_NOT_YET_TESTED`

## Question

Does the merged V3 four-family representation qualification already provide the scientifically cleaner target tournament implied by the later V48/V64 identifiability work?

Answer: **partly, but not completely**.

The V3 framework is a strong prospective RNA-representation comparison. It does not yet constitute a tournament result, and it does not test the V64 factorized regulatory target hypothesis.

## What V3 already gets right

Merged PR #220 (`f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`) freezes a neutral comparison across:

1. `GLOBAL_CELL_STATE`
2. `QUERY_LOCAL_STATE`
3. `PROGRAM_STATE`
4. `STRUCTURED_COMBINED_STATE`

Important strengths:

- no incumbent priority for `cell_state`;
- no automatic preference for the more expressive structured family;
- q/query-value leakage is an absolute failure;
- address identity, wrong-query, global-summary, source/operator/depth/support and technical-only shortcuts are explicit controls;
- donor-level held-out evaluation is mandatory for deciding evidence;
- donor, operator, study and technology transfer are separate axes;
- basis/subspace stability is separated from coordinate stability;
- biological-evidence convergence is distinct from measurement-depth convergence;
- `D_biological_support` is distinct from `D_measurement`;
- technology is treated as an observation process, not biological state;
- no unrestricted donor/dataset-ID embedding;
- rare/unusual biology must not automatically be erased as domain shift;
- no winner is selected and numeric deciding margins remain unset.

These are scientifically aligned with the S149 and V64 lessons.

## What Stage A can and cannot establish

The companion Stage-A contract is explicitly TRAIN-only, zero encoder/predictor/EMA updates, with protected assets sealed.

Its strongest permitted conclusion is `QUALIFIED_FOR_RNA_REPRESENTATION`.

That boundary is correct. Stage A does not and cannot establish biological truth merely from RNA reconstruction/transport.

Therefore the V3 framework **does not contradict V48**. It accepts the semantic-twin limitation by keeping the Stage-A claim ceiling at RNA representation.

## The important missing family

`STRUCTURED_COMBINED_STATE` in V3 combines RNA-derived global, query-local and/or program-level components.

It is not the later V64 factorized hypothesis:

- `Z_global`: recurrent RNA state;
- `Z_query`: query-local RNA state where justified;
- `Z_reg`: separately constructed and independently qualified regulatory state;
- later `Z_response`: perturbational/interventional state under separate causal evidence.

This difference is load-bearing.

V48 showed that same-assay observables cannot generally distinguish biological state from an observationally equivalent hidden technical state. V64 further showed that even named external modalities/resources can share activity/measurement bias: Nott/E2 anchoring was ~4.9x enriched for NIH-CARD RNA detectability and E2 edge degree also tracked detection strongly.

Therefore simply concatenating or fusing RNA and regulatory/multiomic features would not solve identifiability. The evidence channels must stay factorized until prospectively defined agreement tests demonstrate what is shared and what remains modality/measurement specific.

## Population estimand remains unresolved

The V3 population-estimand document correctly leaves four candidates unselected:

- cell-weighted empirical;
- donor-weighted;
- source-balanced donor-weighted;
- hierarchical tempered.

This is not an administrative detail. S149 showed source/study and observation process are deeply entangled, and FULL104 is highly unequal by cell count. A deciding target tournament cannot silently inherit cell-uniform or source-balanced weighting merely because either gives favorable metrics.

For target discrimination, donor must remain the biological replication unit, but the exact population estimand still requires prospective approval.

## Observation-operator contract

The V3 observation contract is compatible with the required factorization:

`z_biology -> O_t -> X_observed`

It allows lawful physical/experimental descriptors but forbids unrestricted donor/dataset/matrix IDs. It also requires biology×operator interactions to be reported where identifiable rather than forcing all interaction into either 'biology' or 'nuisance'.

This is a suitable observation-process layer for a future factorized target tournament.

## Historical-spillover findings

Do not make the following promotions:

1. Four-family V3 prefreeze -> completed tournament. No deciding result exists.
2. `STRUCTURED_COMBINED_STATE` -> V64 factorized biological target. It is RNA-internal in the current V3 definition.
3. Stage-A success -> biological state. V3 explicitly limits Stage A to RNA representation.
4. Stable subspace -> biologically meaningful coordinates. V3 correctly forbids that promotion.
5. Study/technology transport -> regulatory validity. Claim ladder requires new evidence.
6. Nott/E2 + NIH-CARD support -> independent confirmation. V64 demonstrated shared activity/detection bias.
7. Source balancing -> biological deconfounding. The estimand remains scientifically unresolved.

## Current scientific judgment

The best current architecture is not a single winner among the existing four RNA representation families.

The strongest hypothesis is a **two-stage factorized qualification**:

### Stage A — RNA representation family
Use the existing V3 four-family framework to determine which RNA representation(s), if any, earn `RNA_REPRESENTATION` under leakage, shortcut, donor-transport, stability and uncertainty controls.

### Stage B — biological/regulatory triangulation
Only after an RNA representation is frozen, test a separately constructed `Z_reg` / regulatory object under its own provenance, nuisance and independence controls. Agreement with RNA must be tested, not built in by construction.

This preserves the V48 identifiability boundary and the V64 evidence-independence lesson.

## What is not yet done

- no Stage-A execution authority;
- no selected population estimand;
- no numeric deciding margins;
- no RNA-family winner;
- no qualified `Z_reg`;
- no factorized RNA-regulatory tournament result;
- no biological target winner;
- no training authority.

## Next design decision requiring prospective approval

A future successor should decide between:

A. **Keep V3 four-family Stage A unchanged, then add a separate Stage-B factorized regulatory qualification.**
   - strongest provenance firewall;
   - preserves the claim ladder cleanly;
   - recommended.

B. Add a fifth `FACTORIZED_RNA_REGULATORY_STATE` directly into the Stage-A family tournament.
   - more direct comparison;
   - but risks mixing an RNA-representation question with an external-evidence/biological-support question and complicating the claim ceiling.

C. Replace `STRUCTURED_COMBINED_STATE` with a factorized RNA-regulatory object.
   - not recommended because it would discard the useful RNA-internal structured-family question and conflate two scientific layers.

Recommendation: **A**. Do not modify the merged V3 four-family contract until this architecture choice is explicitly approved.

`TARGET_WINNER=NONE_QUALIFIED`
`REPRESENTATION_WINNER=NONE_QUALIFIED`
`SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`
`TRAINING=OFF`
`STAGE_A_EXECUTION=NOT_AUTHORIZED`
`TD60=BLOCKED`
`MORABITO=PROTECTED`
