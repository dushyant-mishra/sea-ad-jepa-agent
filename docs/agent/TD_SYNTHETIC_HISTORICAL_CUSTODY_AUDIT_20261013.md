# TD + synthetic historical custody audit — 2026-10-13

Status: `HISTORICAL_AUDIT_CONSOLIDATED__CURRENT_PREFLIGHT_IDENTITY_FROZEN__BIOLOGICAL_EXECUTION_OFF`

This audit branch is the error-lineage / custody companion to the takeover branch. It is intentionally not a new biological analysis. Its function is to preserve what has already been audited, what failed, what was repaired, what is superseded, and what remains unresolved.

## Current authority pair

- TD repaired execution code: `audit/td-relational-blind-custody-v3-20261013` @ `1f474a44a6baabc667dbfda726e0755426c732e7`.
- Synthetic sealed V2.1 package code: `synthetic/td-relational-test-package-v2-1-20261013` @ `15f519c00137d581e25232c16be52c2b9badd83e`.
- final package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`.
- final cross-cert receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`.
- final terminal: `READY_TO_EXECUTE_BLIND_FIT`.

No blinded biological fit has run. Controller truth remains unopened.

## Consolidated defect history

### A. Unified synthetic architecture defects caught before implementation

The initial PR #315 design failed its own audit. The corrected V2 design preserved the old document for history rather than deleting it. Main findings:

1. The design omitted the older Stage81A3 biological synthetic substrate, incorrectly treating V79 Q00-Q11 as the main historical synthetic foundation.
2. Candidate-shaped latent truth (`shared/query/relational/regulatory`) was too circular; it risked qualifying candidates in a universe built in their image.
3. Controller truth and fit-side lawful data lacked a sufficiently explicit trust-domain firewall.
4. A synthetic-only tournament/runtime would not qualify the real downstream pipeline; synthetic qualification must reuse the same real executor/runtime interfaces.
5. The production modern-reader / 41K molecular-address contract was under-specified.
6. Rare-program eligibility across lineages/states was under-specified.
7. Source could not be allowed to cause biology directly, but realistic acquisition can still create source-biological correlation through sampling.
8. Query truth needed to arise from the same biology rather than an independent planted query axis.
9. Synthetic controller oracle, teacher-side measured evidence, constructed teacher state, student evidence, and student prediction had been conceptually conflated.
10. Uncertainty should be derived from conditional variability/repeat observation, not a planted arbitrary scalar coordinate.
11. Synthetic planted effect sizes cannot automatically become real-human decision thresholds.
12. Earlier PR #311 PASS language needed narrowing to component geometry / engineering evidence, not final unified biological qualification.

These are considered repaired architectural conclusions. Do not redo them unless the architecture materially changes.

### B. TD blind-custody defects caught before biological execution

External review of the relational successor found that a scientifically plausible gate was not enough; the process itself had to guarantee blindness and exact artifact identity.

Repairs now present at PR #320 head:

- phase 1 has no controller truth in custody;
- blind fit and controller adjudication are separate invocations;
- controller mapping is hidden by a controller-only 256-bit nonce rather than relying on a low-entropy bare digest;
- phase 2 must authenticate the exact frozen blinded receipt before controller truth can be opened;
- output paths cannot overlap protected fit custody;
- the blinded receipt is bound to exact fit-engine/science-code SHA-256 values;
- phase 2 verifies that engine identity before truth opening.

The repair suite and frozen V2 spillover tests passed before cross-certification.

### C. Cross-cert controller identity ambiguity caught after an initial CI pass

An independent byte audit found that the original V2.1 transport finalizer used the field name `controller_manifest_sha256` for the **canonical semantic commitment** of the controller object, not the SHA-256 of the raw manifest file bytes.

This was not treated as cosmetic. The prior successful cross-certification was failed closed and superseded.

The correction is `scripts/v79/finalize_td_relational_synthetic_package_v2_1_1.py`. The final cross-certification schema is `JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_CROSS_CERTIFICATION_V2` and records separately:

- raw controller-manifest file SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`;
- controller semantic commitment SHA-256: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`.

A fresh sealed realization was then cross-certified. The final preflight environment proved that controller bytes were absent and that no blinded-fit command was invoked by the certification workflow.

## Historical inputs preserved by immutable reference

- Stage81A3 biological synthetic precedent: commit `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.
- V79 synthetic history: `audit/v79-synthetic-lane-history-20261012` @ `414cac96a6491855f06e3382c59fefbd63a9a547`.
- target-discovery takeover audit: `audit/target-discovery-takeover-20261011-v2` @ `73a2820bf6057d28937ad337d401b7ee51b5c5ab`.
- PR #311 rare biology component lane: `2b6d3439105e087acdab53a318c57bbb468eae26`.
- PR #313 real tournament executor: `206167a1eb86f1dec5f8285db56accbcd469bce9`.
- PR #315 unified synthetic V2 design: `af03ef67d52651463944a6de3a08e101ad00e0ea`.
- PR #316 relational successor prefreeze: `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`.
- PR #320 repaired custody: `1f474a44a6baabc667dbfda726e0755426c732e7`.
- PR #321 synthetic V2.1: `15f519c00137d581e25232c16be52c2b9badd83e`.

Full branch discovery inventory is in `docs/agent/HISTORICAL_BRANCH_INDEX_20261013.txt`.

## Local/project-only evidence custody

The exact inventory is `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.

Small non-secret text/CSV audit results may be archived on the handoff branch. This audit branch preserves the final **non-secret** cross-certification/preflight receipts and the SHA-256 identities needed to verify controller custody. Controller-manifest and controller-realization bytes are deliberately **not** copied to either successor branch because they are controller truth; only their frozen hashes/commitment are recorded here.

Large binary assets are not duplicated through the GitHub contents API. Their exact current byte size/SHA-256 is frozen in the manifest. This is explicit custody, not a claim that GitHub contains those bytes.

## Unresolved issues carried forward

### 1. 50K `sample_row` ambiguity

The project-custody `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` contains 50,000 rows but only 25,000 unique `sample_row` values; both A and B samples use 0..24,999. Any analysis that interpreted `sample_row` as one global physical row must be revisited with physical row identity. This is especially important before hard use of older STAT1 calibration quantities.

### 2. Real-human numerical gate authority

Synthetic known-truth can qualify estimand/gate implementation, direction, null behavior, shortcut detection and NOT_ESTIMABLE handling. It cannot silently define real-human effect-size thresholds. Real numerical decision rules remain separately governed.

### 3. Biological test-of-test result does not yet exist

Current terminal is only `READY_TO_EXECUTE_BLIND_FIT`. There is no valid biological PASS/FAIL/NOT_ESTIMABLE result to report yet.

## Pending action queue and audit gates

1. **Phase-1 blinded synthetic TD fit:** run only against the exact cross-certified pair. Controller bytes must remain absent. Freeze the V4 blinded receipt and stop.
2. **Receipt audit:** independently verify all nine opaque challenges, output completeness, engine identity, package/binding hashes, custody separation and absence of selective reruns. A failed receipt audit blocks truth opening.
3. **Separate phase-2 authority:** only after receipt audit PASS may controller adjudication be authorized. Phase 2 must authenticate the frozen blind receipt before reading controller truth.
4. **Capability-level adjudication:** preserve PASS/FAIL/`NOT_ESTIMABLE` per challenge and matched-control behavior. No aggregate rescue of a failed required capability.
5. **Qualification decision:** explicitly state what TD machinery is qualified and what remains outside scope. Synthetic PASS does not authorize real TD automatically.
6. **Macha Layer-A closeout when evidence arrives:** audit the final 1,056-fit Q00-Q11 receipt before any scoring authority. This is parallel/separate and must not mutate the frozen TD synthetic package.
7. **STAT1 row-index repair before hard calibration:** recompute only the row-identity-dependent analyses using true physical row indexing; do not redo unrelated rare-biology work.
8. **Broader unified biological/model qualification:** after TD synthetic test-of-test qualification, return to PR #315's Stage81A3 + V79 + PR311 integration, teacher/student recoverability, common/rare interference, EMA continuity and transport program.
9. **Real TD only after explicit readiness:** require qualified synthetic gate behavior, any required Layer-A closeout, prospectively frozen real estimands/decision rules, and authenticated current data/split/support contracts.
10. **Training remains OFF:** TD60, Stage4 and JEPA/foundation training need explicit future authority regardless of synthetic results.

## Audit rule for the successor

Do not repeat a historical audit simply to establish personal familiarity. First consume the current takeover document, no-repeat ledger, branch index, immutable refs, and exact receipts. Reopen only a specific unresolved or contradicted item.

## Audit terminal

`AUDIT_CUSTODY_COMPLETE__KNOWN_FAILURES_PRESERVED__SUPERSEDED_RUNS_MARKED__PENDING_ACTION_QUEUE_FROZEN__CURRENT_PREFLIGHT_FROZEN__NEXT_SCIENCE_ACTION_PHASE1_BLINDED_FIT_ONLY`
