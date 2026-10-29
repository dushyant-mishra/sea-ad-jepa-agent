# JEPA deciding-lane D1/D2 depth interface ruling — 2026-10-29

**Scope:** prospective contract choice for a *new versioned V2 consumer/producer*, **not** source/data qualification, historical V1 mutation, biological target selection, or authorization to train.

## Decision (explicit)

**D1 SELECTED as the proposed default for a separate, non-promoting V2 observation-depth interface.** The exact cellwise covariate is

`D1(cell) = Σ count(cell,address)` over **base-rights-visible addresses** whose operator state is exactly `MEASURED_SCALAR`, with frozen, source-issued address/right assignment and raw integer measurements.

This is a *released measured-depth covariate*, **not** physical library total. It can be checked by the receiving student using the same visible address/count roster. Its attractive invariant is that adding legitimate richer evidence rights cannot change D1 when the base roster, cell roster, mapping and operator are held fixed.

**D2 REJECTED as the default.** D2 = D1 + source residual can carry the queried or other withheld molecule mass. It remains **OFF / NOT_AUTHORIZED** until a query- and operator-specific independent audit proves every included residual molecule is lawful and query-independent, including all off-ledger aliases/collisions and source row-selection effects. An apparently plausible residual, source total, or SHA is not proof.

**This is a design ruling, not source acceptance.** D1 is not currently authenticated on human data. Neither a passed synthetic test nor the process-local fixture rights binding authorizes emitting D1 for production training.

## Operational boundary for V2

1. Introduce an explicitly versioned content law and typed field `base_rights_normalization_depth`; **never reuse or silently reinterpret** V1/G7 `library_size` (physical-total-shaped count-bound law). Existing physical `count <= library_size` checks remain intact on V1.
2. Require an **independent immutable evidence-rights binding** from a real source issuer. Consumer self-declared rights and a caller-resigned digest are insufficient. Exact base scalar equality alone does not prove source/authentication.
3. Require physical-feature/address/alias accounting, per-query evidence rights, observed-versus-structurally-unmeasured disambiguation, query exclusion from normalization, and source/operator/row-selection/QC independence of withheld q. Source identity and donor/specimen mapping remain separate R1/R1D/R2 requirements.
4. When the base measured sum is zero or mapping/right closure cannot be established, return `NOT_ESTIMABLE` consistently **independent of withheld mass**. Upstream #474 A4 currently violates equality of refusal classes for equal empty base rights; preserve its RED receipt and repair upstream before promotion.
5. No physical total, teacher/private content hash, query count, source residual, or inferable unkeyed digest is exposed through the student view. Do not count conservation of caller-provided totals as independent full physical alias coverage.
6. Teacher rich-view measured counts may exceed D1 without violating the distinct V2 law. Do not graft this onto CaseBundle V1/G7 V1 physical-total constraints. A new G7 E3 V2 content contract, reviewed against the actual common producer/consumer, is required.
7. No release or target qualification before independent source-issuer, ETL, held-out biological baselines and same scientific producer/gate custody are established. `TARGET_NONE` remains a valid scientific result.

## Existing PRs and compatibility

- Original #479 `ae762d7096a94ac663a0788f6f577ba404e37536`; independent Macha #481 `957fa4a558ce2bd219b5c2dec6dad8f65dca81ab` is the immutable hostile verdict.
- A3-only #495 `d2e430d739e1ef16806120752b867c6aeeba4972` passes existing CI, but is not a full repair.
- A1/A2 process-local-binding #496 `ee0e6ca983a693240830a0ba361d45768bab8521` has selected Macha A1-A3 hostile cases green **but cumulative CI RED**. The previous V2 author test treats a re-signed base measured count of 999 as valid so long as its type is exact, while D1 makes base-depth/count conservation an actual content invariant. These are **incompatible contracts** for the same consumer entry point. The former shape-only expectation must be retained at its pinned historical scope; the stricter content consumer must receive its own versioned interface and tests, not be silently substituted or made to pass by editing the immutable Macha #481 tests.
- Neither #496 process-local map nor a digest creates external independent rights authentication. Keep #496 draft until version split and review; never present its targeted 23/23 result as full qualification.
- G7 #497/#500 adds exact-type and bound-to-V3 **fixture** composition only; existing R1 physical aliases, R1D pseudodonors and R2 depth leakage remain RED.
- PS #498/#501 exact-type/exception-cause tests address mechanics only; independent T2-D external scan issuer remains RED.
- Task3 #486 independent #499 mechanical R1/R2 acceptance does not bind knob semantics or authenticate calibration.

## Authority / next executable steps

Design decision: `D1_PROSPECTIVE_V2_CONTENT_DEFAULT__D2_DEFAULT_REJECTED__REAL_SOURCE_UNQUALIFIED`.

Next: version the V2 content consumer; qualify authenticated source feature/alias and rights/QC rosters; repair upstream #474 A4; independently review G7 V2 E3 and bind source→consumer→decision in a sealed custody path. Do not implement/promote production-synthetic Task4 or real training yet.

**Standing scientific state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
