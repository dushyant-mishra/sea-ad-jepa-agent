# G7 E3 Macha independent RED #449 — scoped R3–R5 repair, R1/R2 fail-closed external boundary (2026-10-27)

**Classification:** `AUTHOR_REPAIR_CANDIDATE__INDEPENDENT_REVIEW_REQUIRED__G7_E3_REAL_AUTHORITY_OFF`. This is an incremental implementation and a historical **preservation record**, not real G7 verification, a full synthetic-world rehearsal, an accepted same-code-path qualification unit, a real target result or a new scientific gate. **Do not use fixture-green as scientific authorization.**

## Exact lineage and unchanged historical work

| Source | Identity | Claim |
|---|---|---|
| Original source-content fixture PR #433 | `21c3fb3bd389f9a513ca9ed33b31acad56b0015f` | Authored E3 candidate; not independent attestation |
| Macha first hostile tests-only PR #441 | `771672405bf1071830300a4b235a4d6c85fa6799` | F1–F7 hostile findings, RED historical |
| ChatGPT earlier repair PR #446 | `f088f40625020253d4378812511e3c473063bb10` | Narrow mechanical repair; residual physical-identity/depth defects |
| **Macha independent recheck PR #449** | `062bfe369348ac4d9ed89c0aa162abf0d9806397` | 13 hostile cases. R1 = opaque physical-measurement split/copy and aliases; R2 = q-withheld count leaking through pooled/per-unit `library_size`; R3 = V3 `source::donor` collision; R4 = loss of explicit unauthenticated provenance flags; R5 = escaped recursion exception |
| New narrowly stacked candidate | This review's exact PR head (resolve from GitHub) | Repairs **only** R3, R4, R5 without modifying original hostile tests or original V3 decision executor |

The original hostile test file identities are fixed in this candidate: Macha #449 `tests/v5/test_td_real_g7_content_enforcement_v1_macha_recheck.py` Git blob `02b7923e42df901c5f14bb757c44e5fb3cfa1373`; Macha #441 file `tests/v5/test_td_real_g7_content_enforcement_v1_macha_hostile.py` `efaf84b0fb6fe22ad199e677e546ad27fee42c08`; original base test file `tests/v5/test_td_real_g7_content_enforcement_v1.py` `d28ca093f8b50c422f01e2182c93816222890121`; inherited V3 decision executor Git blob `b9a232011f370d89038edadfd053a9333230acbe`. No original hostile test is rewritten, made `xfail`, skipped as an accepted passing case, or reclassified.

## Scopable corrections, with corresponding unchanged independent attacks

- **R3 / cross-field composite identity:** Real G7 V3 constructs key `f"{source}::{donor}"`. The earlier `"::"` substring screen cannot establish injectivity: `("A:", "B")` and `("A", ":B")` are distinct physical groups with the same consumer key. The E3 binder now checks injectivity across the **complete materialized source/donor roster**, before admitting downstream rows. It rejects only an actual consumer-key collision, without pretending the V3 key is independently physically authenticated or changing the frozen V3 executor.
- **R4 / consumer receipt limitations:** The binder copies the validator's explicit `physical_atom_identity_authenticated=False` and `q_excluded_library_provenance_authenticated=False` fields into its consumer-facing fixture receipt. A missing flag is not a safe implicit negative.
- **R5 / exception containment:** Bounded canonical JSON nesting (max 128 levels) now raises `G7ContentError` on hostile recursive structures. This is a technical safety bound, **not** an evidence-support threshold or biological parameter. Exact built-in type refusal, content canonicalization and assay-right logic remain unchanged.

## Non-fixable without external source facts — R1 and R2 stay RED

- **R1:** Distinguishing independent physical measurements from one UMI library split into fragments, batch-coded copies or duplicate observations **cannot be inferred from opaque user-supplied atom IDs, count magnitudes, metadata strings or their hashes**. A producer must authenticate the physical measurement unit/address/source, acquisition relation and canonical grouping. Rebranding IDs or extending a substring denylist is insufficient.
- **R2:** Proving q-excluded library/normalization noninterference requires an independently authenticated normalizer lineage and rights-aware observation producer, including when a perfectly ordinary per-cell library total contains withheld gene counts. Equality against a donor-pooled sum, even with added offset/scale cases, is insufficient. Rewriting the scalar to mask a leak does not retroactively authenticate its source.
- These conditions apply equally to a synthetic observation fit view and human measurements **at the production gate**. For a fixture they may be reported as **limitations** but the input must not be described as physical-source/rights-verified, nor promote to same-code-path/human/Stage4. All existing negative R1/R2 tests remain deliberately RED.
- Any future remedy must be a **separate, independently reviewed producer/issuer trust design**, require actual external identity and q-excluded-normalizer ancestry, freeze an exact source policy, preserve producer/artifact/executor equivalence, and obtain independent same-code-path qualification. In-process Python object identity, a trusted-looking SHA field, or a caller-provided boolean cannot supply the missing proof.

## Test/CI and scope

The existing `.github/workflows/td-real-g7-e3-content-v1.yml` intentionally runs **all** Macha #449 hostile cases and must remain **RED** as long as R1/R2 are unresolved. The new `td-g7-e3-macha449-r3-r5-scoped-review.yml` runs unmodified base/old hostile/V3 suites and Macha R3–R5; then asserts exactly ten unresolved R1/R2 failures and stores their verbatim log as a CI artifact. That second expected-RED check is a **recorded blocker**, never a passed security claim. A green scoped job does not override the full hostile RED or imply external issuer trust. Refer to the exact-head GitHub Actions runs before judging the result.

**Independent review requested:** Macha tests the candidate code against old #441 and current #449 unchanged tests, probes additional composite-key aliases, nesting and proof-of-identity dependence, and checks any legitimate source/donor IDs or consumers affected. The review can at most give `ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS`, not cumulative G7.

## Relation to synthetic → TD → JEPA

- Corrected human relational TD56/TD57B/TD59 PR #314 is already executed and cannot be spent again; TD57C nearest-third remains negative.
- The PR #328 unified source world and PR #469 source-generated fixture-to-Task5 test are **mechanics only**. They cannot certify the production biology or the source rights required by G7.
- Production synthetic V3.1/V3.1.1 #344 explicitly prohibits deriving synthetic biological truth from PR #328's contiguous gene blocks. The shared producer chain must preserve the `KNOWN_TRUTH_CASEBUNDLE_V1` / `TRUTH_BUNDLE_V1` separation under #379 and the frozen challenge worlds A–I.
- PR #369 is a qualified test-of-test in its source-limited scope; its green result cannot overwrite later G7 E3 RED.
- C1/C2/C3 target construction requires measured-object provenance, not a surrogate predictor. C5 pairing and TF motif claims require distinct modality evidence.
- No changed human data, protected outcome, synthetic sealed world, biological threshold or JEPA parameter is created by this correction.

**Standing state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
