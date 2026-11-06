# 2026-10-27 execution audit: typed V2 rights-normalization observation contract, no authority

**Audit type:** append-only completed-scoped-mechanics + forward-science blockers. This note does not revise historic V8e acceptance (`a271164554076d0acda3bd0cf0b1bf957c0fdfd3`), Macha [#474](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/474) fixture laws, ChatGPT [#478](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/478) independent conditional review, #475 source audit or corrected real relational PR #314. Machine-readable exact receipt: `results/target_discovery/unified_qualification_v1/JEPA_NORMALIZATION_VIEW_V2_FIXTURE_DELTA_20261027.json`.

## Source and observed CI (do not conflate semantics)

- **New [draft PR #479](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/479)** head `ae762d7096a94ac663a0788f6f577ba404e37536`, stacked on independent PR478 `b7aa56e2915d2af7dd733f0f0253e684164ce70a`.
- New producer and shape-only consumer `scripts/v5/td_unified/observation_normalization_view_v2_fixture.py` Git blob `fd573764d8c7d19b8cbbf12683d3e79065385cef`. Hostile suite `tests/v5/td_unified/test_observation_normalization_view_v2_fixture.py` Git blob `61349d4a69a1ace95d7f9d714e983e4aeb0fefd7`. Source design `docs/agent/JEPA_TD_NORMALIZATION_VIEW_V2_FIXTURE_CONTRACT_20261027.md` Git blob `08a85a9f4459b0d5f58965390b0cc9664d8160c6`.
- **Final [CI run #40591648499](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40591648499): 124 tests PASS** (Macha 101 original fixture laws + ChatGPT prior 5 independent caveat tests + new 18 V2 hostiles); all **6/6 exact-head workflows SUCCESS**. Source and script unchanged from that code blob.
- **Preserved RED-first mistakes:** [first run #40591276863](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40591276863) failed when V2 receipt validation invoked PR474 raw count snapshot that properly refuses Python booleans; this was fixed via V2-only exact built-in receipt copier. [Second run #40591445532](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40591445532) ran **124 tests PASS**, but job failed trying to import a G7 module from a different **unmerged branch**; corrected CI states G7 cross-head remains **untested** rather than fabricating a test result. Neither older RED was a biological result.

## Exact scientific and engineering changes

| Component | V1 status | New V2 scoped behavior | Authority |
|---|---|---|---|
| Private original `library_total` | Raw whole-row physical count includes query and possibly outside-map mass | Only private input; never returned, nor its SHA in the student-visible receipt | Source issuer NOT authenticated |
| `base_rights_normalization_depth` | PR474 previously used misleading `library_size` field | Explicit separate per-row covariate; constant across rights ladder by original PR474 law; may be smaller than teacher count | Fixture-only normalized view |
| Student/teacher separation | PR474 result contains all richer levels in same envelope | Distinct `produce_fixture_student_view_v2` / `produce_fixture_teacher_view_v2` entrypoints, never same outward result | Routing still must be externally enforced |
| Per-q mask | Original producer has no query identity | Explicit q address must be mapped outside frozen base rights; student query row must be withheld | Per-query rights issuer NOT verified |
| Off-ledger/colliding mass | PR474's math might retain unseen residual in depth | Strict fixture conservation `whole_source_total == sum(all mapped measured address counts)` or refuse as `QExcludedDepthNotEstimable` | Cannot prove source completeness from supplied inputs alone |
| Existing `CaseBundle V1` | `count <= library_size` and sum measured count bounded by library, physical mass | **Unmodified**, verified on same stacked branch. New independent V2 consumer validates typed depth instead; does **not** invent physical-total inequalities | No CaseBundle V2 issuer |
| Existing `G7 E3` | Physical provenance R1/R1D/R2 RED; #476 fixes R5X/R6 only in fixture mechanics | **Unmodified and NOT present on #479 stacked branch**; no cross-head G7 execution or real E3 equivalence evidence | G7 still blocked |
| Target discovery and JEPA | C2 active broad/meso, C3 R5 measured developmental precedent | **No teacher biological target constructed**, no current human data/ATAC/SCENIC+/perturbation rerun, no latent truth or optimizer | Target winner NONE |

Positive and hostile tests cover mapped-q counterfactual noninterference of the complete student-visible JSON/digest, distinct measured-zero versus structurally unmeasured state, legal teacher `count > depth`, rejection of withheld off-ledger residuals, unknown q or q permitted at base, collision outside base, duplicate cell, malicious caller-owned subclass, tampered digest/flags, fraudulent physical total in V2, original V1 acceptance retained. A canonical digest is a consistency check over public bytes, not a trusted signing authority. Distributing a richer teacher output to a student remains prohibited and not prevented merely by the two functions.

## Current unclosed dependencies

1. **External source and rights:** A source-issued complete raw gene/UMI mapping, per-query rights, actual deposited row physical identity, split/QC nonleakage, donor/specimen group and alias closure. Equality of caller totals does **not** certify the physical source. Current G7 R1/R1D/R2 RED.
2. **Contract promotion:** External independent review of PR479 itself. No change to original CaseBundle or G7 real executor before versioned source/issuer and full cross-head hostile replay. Macha review of ChatGPT PR476 R5X/R6 and PR477 PS encoder remains distinct.
3. **Production synthetic V3.1.1:** T2-D source-scan issuer RED, Task3 independent calibration qualification pending, candidate-neutral biological **PS Task4 generator absent** on reviewed branches. PR328 world and PR469 downstream remain limited mechanics fixture, not production biology.
4. **Human biology:** PR314 corrected relational TD replay already performed, TD57C fine locality FAIL, C2 active no target winner. R5 q-measured context developmental evidence is not production C3 qualification. Do not rerun historic studies merely to seek a PASS.

**Standing stop:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
