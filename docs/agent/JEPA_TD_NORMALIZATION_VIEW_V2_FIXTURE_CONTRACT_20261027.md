# TD observation normalization view V2 — *fixture-only* typed depth, separate teacher/student outputs (2026-10-27)

**Scope:** prospective, nonpromoting contract implementation stacked on [independent PR #478](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/478), which reviews Macha's [PR #474](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/474) fixture-only q-excluded observation producer. This is *not* a production CaseBundle V2 issuer, not the original CaseBundle V1, not real G7 E3 authentication, not a new synthetic generator, and not evidence for JEPA target/architecture selection. The current producer/consumer source paths are under `scripts/v5/td_unified/`. Independent scientific review required; author CI is just mechanics.

## Why a distinct version is mandatory

Old `casebundle_v1.py` and `td_real_g7_content_enforcement_v1.py` require each measured count (and/or accumulated measured counts) to be bounded by `library_size` as a **physical-total-shaped** scalar. Macha #474 instead computes rights-invariant **normalization depth** as
`D_base = whole_source_row_library_total - Σ(raw measured molecule counts assigned outside frozen base rights)`.
A teacher may lawfully observe a non-base count larger than `D_base`; treating `D_base` as a V1 physical `library_size` is a semantic conflation. Original #474 projection passed 172/200 G7 fixture probes because the remaining 28 exposed this contract disagreement, **not** because 172 pass authenticates physical counts.

The new `TD_OBSERVATION_NORMALIZATION_VIEW_V2_FIXTURE` is a *separate, strictly validated visible view*. It has `base_rights_normalization_depth` rather than `library_size` and exposes **no** `physical_library_total`, `library_total`, or raw-input hash. The source whole-library total is accepted only as private producer input and excluded from both published projections. Two distinct functions independently construct `STUDENT_BASE_RIGHTS` and `TEACHER_RICHER_RIGHTS`; no function returns both views in one student payload. An external actor must still enforce routing: interface separation alone is **not** evidence of physical custody or information rights.

The source paths for historical V1 and G7 are **unchanged**. In particular, no `count <= normalization_depth` condition is introduced, and no historic V1 `library_size` inequality is disabled. The V2 consumer checks row shape, state/null discipline, consistent per-cell depth, query masking for students and exact observable hash **without interpreting normalization depth as physical total**.

## Inputs and math

- Inputs are the original Macha #474 `cells`, `address_rights`, `operator_states`, ordered frozen rights `ladder`, **plus explicit `query_address_id`**. Snapshot with exact built-in JSON types before any validation/lookup; refuse subclass-selected Python operators.
- The query must exist as a mapped address and be **outside base rights**. It is lawful for its *identity* to be exposed to the RNA student; its scalar count and depth at the query row may not appear in the student view.
- After PR474's original rights-ladder producer runs, this fixture adapter conservatively requires `whole_source_row_total == Σ(mapped MEASURED_SCALAR counts)` for every cell. Any off-ledger, alias, collision-unresolved, or unaccounted mass causes `QExcludedDepthNotEstimable`. **This equality is a necessary fixture conservation test, not an authenticated gene/UMI mapping proof.** Real source data may legitimately have residual non-addressed mass, in which case this strict fixture route must abstain rather than guess.
- Original PR474 `QExcludedDepthNotEstimable` for collision outside base or zero remaining depth remains a hard refusal. We do not manufacture a q-excluded denominator by subtracting guesses from normalized `log1p` expression.
- Student level = original ladder L0; teacher level = original highest measured-rights level. Rows have distinct `state, count, base_rights_normalization_depth`; non-scalar rows carry null count/depth. Rich teacher rows can have `count > depth`, unlike V1.
- Canonical `observable_sha256` binds only published bytes. It is a local content consistency digest **not** a source issuer signature. Private total is not hashed into public student payload, which would otherwise create a possible hidden-count side channel.
- All receipt/authority flags are exactly FALSE and `authority_effect=NONE`. `reader_partition` remains fixture-only `reader_fit`; no validation/oracle access.

## Executable adversarial tests

`tests/v5/td_unified/test_observation_normalization_view_v2_fixture.py` checks mapped-q counterfactual invariance of the *entire* student payload/digest; teacher count greater than base depth; off-ledger residual abstention; query wrongly assigned base rights; unknown q; outside-base collision; measured zero vs structural absence; duplicate cells; caller mutation; payload-chosen Python subclass; forgery of source-authenticated claims, physical total field, query value and digest; preservation of the original V1 CaseBundle physical total requirement.

The new CI also runs the **original 101 Macha #474 producer-law tests** and the **five independently authored PR #478 scope tests**, then asserts the source of original V1 and G7 validators is unchanged and the V2 sample has no physical total. Preserve old and new failure receipts rather than adjusting tests to pass.

## Current stop conditions and future production obligations

This candidate solves the *shape and namespace* conflict at fixture scope, not the underlying source authority.

- **Off-ledger and alias closure:** whole row source total was computed before 41,238-feature gene mapping. Even equality of totals and mapped values supplied by the caller cannot prove full coverage of physical reads/genes without independently authenticated upstream issuer. Partial missingness, non-universal NPH52 addresses, genuine collisions and source/sample selection must be handled by a source-versioned policy.
- **Q rights and QC leakage:** explicit q ID now prevents a q whose declared right is base, but cannot prove the mapping from a human query or evidence policy to the declared q and rights set. Historical library-based cell inclusion/QC could still leak withheld counts through which rows appear.
- **Physical unit and donors:** R1/R1D remain RED (deposited matrix row versus true physical nucleus; specimen pseudodonor, cross-source donor aliases). No BAM/FASTQ acquisition outside project policy; no inferred independence from strings.
- **G7 E3:** PR #476 source snapshot fixes the known fixture mutation R6 in author tests, but external atom/issuer E3 remains RED. Never substitute this V2 fixture consumer for a source-authenticated production G7 executor. Macha independent review of #476 pending.
- **Production synthetic:** Task2 T2-D external scan issuer RED, Task3 real calibration registry unqualified, **PS Task4 candidate-neutral biological generator absent**. This contract does not change frozen V3.1.1 realism threshold law or resolve V79/V80 objective selection.
- **Teacher:** measured target construction from lawful richer measurements, teacher-surrogate baselines, and donor-held-out recoverability are separate tests; V2 observation routing does not qualify C1/C2/C3/C5 targets.
- **Next production design decision:** the authority owner must version a *source-attested* private physical measurement artifact plus a *released* rights-bound depth view, with independently reviewed issuer, digest ancestry, trusted feature-to-address map, per-q policy and a sealed external truth boundary. Until then `NOT_ESTIMABLE` for unsupported physical claims.

**Standing status:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
