# D1 base-only source-edge proposal — 2026-10-29

**Classification:** `REDUCTED_BASE_INPUT_FIXTURE_ONLY__SOURCE_ISSUER_UNQUALIFIED__NO_G7_V2`.

**Base:** ChatGPT draft PR #510 at `ef51325d0c31bbac2eb0bf74bd3f770d244657f2`, **not** a modification to Macha #507's independent RED tests, ChatGPT #502's unsafe teacher-aware public validator, Macha #504 A4 source, or the original V2 fixture. Macha is independently reviewing #510; this is separate engineering work.

## Why this versioned producer is needed

The historical V2 fixture producers `observation_normalization_view_v2_fixture.py` and `observation_normalization_view_v2_bound_content_v1.py` take `library_total`, pass it through the legacy rights-ladder producer, and require `library_total == sum(stored mapped measured counts)`. The August 50K audit #492 and source identity audit #509 establish that this full conservation law is not available for SEA-AD and NPH52 operators with collision/off-ledger mass. It would be scientifically wrong to weaken the check by renaming physical `library_size` as D1 or by injecting a guessed residual.

Prospective D1 under #491 is **the sum of MEASURED_SCALAR raw base-rights counts**. It does not need physical library total, source residual, unknown features, or richer query counts. The new `observation_d1_base_only_student_fixture_v1.py` accordingly accepts only:

- `base_observations`: one base-rights-redacted count map per requested cell, with omitted measured zeros allowed; **no full count map and no physical source-total field**.
- `expected_policy`: exact query/address-rights mapping, base-rights set, operator-specific measured/collision/structural state mask, complete source/donor/operator cell roster. This policy is **NOT** authenticated by the fixture. It must be frozen and independently source-issued in a future qualified implementation.

The output is only the existing #502 versioned `STUDENT_BASE_RIGHTS` JSON shape, whose content is checked with the **new student-only** #510 `validate_public_student_v2b`. It has D1 for base-visible measured rows, null counts/depths on every non-base address including q, and distinct unmeasured vs collision-unresolved states. It does not call #502's unsafe shared public teacher validator, does not read `_VIEW_BINDINGS`, and has no teacher entry point.

Because hidden q mass and residual are absent from this function's inputs, changing them cannot affect its output **provided the upstream redaction and selected-cell roster are independently query-safe**. This is a dataflow invariant, not a proof that depositor selection, source-feature alias equivalence or annotation are safe.

## Positive tests / negative limitations

- Source-total/teacher/query-count/residual keywords are impossible in the function interface. Non-base scalar inputs are refused, including zero-valued extra private entries.
- Measured base counts must be exact nonnegative integers; missing measurement zeros become zero; D1 must be positive and below the canonical exact integer limit. Zero base yields one fixed `QExcludedDepthNotEstimable` refusal, without reading hidden mass.
- Rows cover the complete frozen address universe for every expected cell. Missing/duplicated/foreign roster rows, unsupported source states, query-right promotion, unknown addresses and hostile Python payloads refuse.
- A synthetic physical-total residual example is refused by the old V2 conservation gate and accepted by this **base-only fixture**; it is **not** an actual SEA-AD/NPH52 human-data acceptance.
- A deliberate positive limitation: changing base counts while preserving their total can produce another consistent view, because the policy and sum rule are not a physical raw-count signature. The independent source producer is still missing.
- **Potential leakage outside this function:** a base address that is an unadjudicated alias of q can carry q molecules in D1; 18 candidate alias pairs / 11 at-risk query addresses in Macha #509 remain a fail-closed external rights obligation. The function also cannot undo upstream q-dependent cell selection/QC or feature filtering.
- **NPH52 real query issuance stays blocked** under the deciding-lane ruling; symbol-only off-ledger identities cannot be negatively cleared. Quarantined NPH52 expression access is not authorized. HVS/SEA-AD identity accounting in candidate tables does not itself authenticate a physical nucleus/donor or unfiltered whole-cell library.
- The existing G7 V1/CaseBundle physical `library_size` law is unchanged. This fixture does not issue G7 E3 V2 or real learner inputs.

## Next review gates

(1) Independent Macha #510 security review, (2) independently authenticated source-side policy and base-count redaction, (3) source alias-equivalence and depositor QC/selection closures including physical nucleus/donor/specimen identity, (4) explicit trust-separated student vs teacher routing and source custody, (5) a separately versioned G7 E3 V2 content law with physical vs D1 semantics, and (6) real known-truth/calibration authority before any Task4/Stage4/training.

**Standing:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
