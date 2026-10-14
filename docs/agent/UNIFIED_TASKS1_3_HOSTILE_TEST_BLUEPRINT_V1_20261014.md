# Unified Tasks 1–3 hostile-test blueprint V1 — 2026-10-14

Status: `ANALYSIS_ONLY__TEST_BLUEPRINT_FROZEN__IMPLEMENTATION_NOT_AUTHORIZED`

This blueprint refines the accepted implementation plan without changing its authority or sequence. It exists so Task 1–3 implementation can start RED-first immediately after Task 0 custody acceptance and Macha Task 1–2 consolidation.

## Task 1 — canonical identity + one authority model

### Identity hostile cases
1. Copy a valid 64-hex digest onto a mutated payload: reject.
2. Mutate a parent payload while retaining child parent digest string: recursive verification rejects.
3. Omit a required parent object: reject.
4. Supply two parents with the same declared identity but different canonical payloads: reject.
5. Change only navigation PR/branch metadata: scientific digest must not change if navigation metadata is outside scientific payload; navigation must never confer authority.
6. Change decision-bearing code/policy/input identity: scientific receipt identity must change.
7. Nonfinite float, bytes, set, tuple-with-ambiguous-semantics, or other non-JSON scientific value: reject unless prospectively encoded by an explicit schema representation.
8. Canonical key order permutation: same canonical digest.
9. Stable registry rows reordered with stable scientific identity keys: same ordered-registry digest.
10. Same semantic JSON with different raw transport bytes: semantic digest may agree; raw transport hash must differ.

### Authority hostile cases
1. `PASS`, `GREEN`, `QUALIFIED`, `MECHANICALLY_QUALIFIED`, `SYNTHETIC_TEST_QUALIFIED` cannot deserialize as `qualification_stage`.
2. Missing `authority_scope`: reject.
3. Unit-scoped `KNOWN_TRUTH_QUALIFIED` cannot imply pipeline/project human/training authority.
4. `REVOKED_BY_DEFECT` or `SUPERSEDED` cannot be treated as active because historical receipt is valid.
5. Unknown stage/status: reject closed.
6. Stage cannot skip promotion requirements because ordinal value is higher.

### Consolidation-specific regression
If Macha old Task 1 is accepted, unified tests must import/use the accepted canonical primitive or compare against frozen canonical test vectors. A second independently coded serializer that can diverge is a failure.

## Task 2 — TD execution manifest + population/access law

### Population/access hostile cases
1. `reader_validation` read during current-TD producer execution: invalidate receipt even if numeric result is correct.
2. `reader_oracle` read: same failure.
3. Caller labels data `held_out` without manifest-bound partition identity: no authority.
4. Producer reports only intended access while actual access log contains protected partition: reject.
5. Missing actual access class or partition enumeration: reject.
6. Attempt to rescue underpowered `reader_fit` by validation/oracle data: reject.
7. Cross-fitting that mixes validation/oracle into folds: reject.
8. Moved population/split identity without new manifest digest: reject.

### Manifest identity hostile cases
1. PR number or branch name used where exact code/policy digest required: reject.
2. Candidate registry changes but manifest digest unchanged: reject.
3. Endpoint/source/support policy changes without new manifest: reject.
4. Controller policy changes without new manifest: reject.
5. Qualification registry changes without new manifest: reject.
6. Observation/support contract changes without new manifest: reject.

### F9 additions
1. Manifest must expose decision-bearing normalization/library provenance when applicable; hidden denominator/source channel is not allowed to remain implicit.
2. Equal address count cannot be used as proof of equal evidence burden.
3. Per-source estimability scope must be bindable rather than inferred from aggregate availability.

## Task 3 — qualification registry + revocation + prerequisites

### Historical/lineage hostile cases
1. Historical promotion receipt remains byte-identical after later revocation.
2. Revoked unit cannot enter a new active manifest.
3. New code/policy identity cannot inherit prior stage automatically.
4. Supersession must bind predecessor, successor and requalification scope.
5. Valid old receipt cannot be deleted to hide a defect.

### Independent qualification hostile cases
1. Scientific producer/executor self-issues its own human semantics qualification: reject.
2. Qualification controller identity equals scientific unit identity where independence is required: reject.
3. Human-executable promotion without independent promotion receipt: reject.

### Prerequisite-graph hostile cases
1. `ready=true` with one missing prerequisite: derive false.
2. One revoked reference: `REAL_REFERENCE_READY=false`.
3. One prerequisite bound to the wrong manifest/access policy: false.
4. Unsatisfied prerequisites must remain machine-visible, not disappear after a higher-level failure.
5. Aggregate CI success cannot satisfy a missing producer/reference prerequisite.
6. PR #369 system-battery success cannot promote constituent gates.

### Historical-custody additions
Registry must be able to attach, as non-promoting history:
- Macha real-TD/corrected-replay stream;
- Macha V79/Bayesian/Q00–Q11 stream;
- spent PR #314 evidence bound to old execution law;
- V79 immutable NOT_QUALIFIED;
- V80 benchmark-only scope;
- F6–F9 limitations/obligations as inherited prerequisites where relevant.

## Required RED preservation

For each task, preserve:
- exact RED head;
- exact failing tests and reason;
- exact GREEN head;
- focused workflow/run/job;
- inherited regression workflow/run/job;
- fresh independent review verdict;
- statement that candidate outcomes, reader_validation and reader_oracle remained unopened.

Terminal:
`TASKS1_3_HOSTILE_TEST_BLUEPRINT_FROZEN__READY_FOR_RED_AFTER_TASK0_ACCEPTANCE__NO_IMPLEMENTATION_AUTHORITY`
