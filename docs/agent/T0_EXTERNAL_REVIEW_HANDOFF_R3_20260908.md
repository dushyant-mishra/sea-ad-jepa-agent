# T0 external-review handoff — R3

Prepared for independent review of the owner work order items 1–9. Nothing in this
document promotes any authority to PASS. Every status below is either a measured
fact or an explicit STOP.

## Standing terminal statements

    PRODUCTION_B2_NOT_RUN
    DONOR_ROLE_GATE_SHUT
    real_execution_ready=False
    NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED

The donor-role gate is SHUT in the sense of active and blocking, not resolved. No
production B2 execution has taken place; every authority below that would require
the authenticated B2 substrate is exercised on synthetic fixtures only.

## Branch and ancestry

    branch          t0/v20-pathology-blind-materialization-20260908
    sealed base     21ec629667eeda5a7d37d3f1d822fbf93b213325   (unchanged, ancestral)
    prior review    6c6d841ee7e9e57875a02c0400a2bf1ec2798981
    implementation  3b5ff3a1788d25176fd476fff4acf9f227e5c1ba

Commits added since the prior reviewed head, oldest first:

    8b49ff84  freeze the input dependency contract and build IMMUNE_FRACTION
    760c68ef  R2 red cases for the four remaining B2 defects
    ca540b31  freeze the IMMUNE_FRACTION formula and bind production provenance
    032ad149  close the B2 R2 execution-authority defects, A through I
    24b2c9ff  add the IMMUNE support-count and age/sex authorities
    3b5ff3a1  technical completeness, estimability preflight, two review repairs

The governance commit carrying this document follows `3b5ff3a1`.

## Suite counts

Collected and passing, not estimated.

| suite | cases |
|---|---|
| `test_work_checkpoint_v1` | 33 |
| `test_t0_at8_availability_authority_v1` | 32 |
| `test_t0_v20_feature_projection_authority_v1` | 38 |
| `test_t0_v20_row_count_authority_v1` | 50 |
| **original four aggregate** | **153** |
| `test_t0_v20_row_count_authority_r2_red_v1` | 36 |
| `test_t0_input_dependency_contract_v1` | 56 |
| `test_t0_immune_fraction_authority_v1` | 47 |
| `test_t0_immune_fraction_authority_r2_v1` | 26 |
| `test_t0_immune_support_count_authority_v1` | 35 |
| `test_t0_age_sex_authority_v1` | 50 |
| `test_t0_technical_completeness_authority_v1` | 51 |
| `test_t0_estimability_preflight_v1` | 28 |
| **all twelve aggregate** | **482** |

The feature suite is 38 cases. An earlier handoff said 39, which made the
four-suite total add to 154 rather than the 153 actually observed; that figure is
withdrawn and must not be restored.

No CI or status check is attached to these commits. The counts above are from a
local run and should be reproduced by the reviewer rather than taken on trust.

## Changed files

Added under `scripts/v4/`:

    t0_input_dependency_contract_v1.py
    t0_immune_fraction_formula_spec_v1.py
    t0_immune_fraction_authority_v1.py
    t0_immune_support_count_authority_v1.py
    t0_age_sex_authority_v1.py
    t0_technical_completeness_authority_v1.py
    t0_estimability_preflight_v1.py
    t0_v20_row_count_authority_v1.py            (modified this cycle)
    t0_v20_feature_projection_authority_v1.py
    t0_at8_availability_authority_v1.py

Added under `tests/v4/`: the matching twelve suites plus
`fixtures/t0_consumer_declarations_v1.json`. `tests/test_work_checkpoint_v1.py` is
modified.

## Source identities

    MTG donor pathology table   ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a
    accepted immune membership  d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete Phase2 manifest    66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
    MTG H5AD source (declared)  e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79

The complete manifest was verified to hold 8,915 blocks across 42 operators with
exactly 1,247 operator-31 blocks on the MTG matrix, whose declared rows total
638,150. Its first row is operator 0, which is why authenticate-then-filter is the
only workable contract.

## Authority roots

    input dependency contract     8589d9aec3f683073d22b33f5047b92be034f952408e69cdb64cabfc0ba4cf0d
    IMMUNE_FRACTION formula spec  d639f0cd697f3ccd22ce062d89d309ccb2e24445a221c5aa26966ebc567f4c58   (v1.0.0)
    IMMUNE_FRACTION value root    831139259fe78c5cede5457cb4cdc6bbb7bedd53831af95508b9bdfb56741653
    IMMUNE support count root     e6364ee036bc21058a502ed113047799899dec693510049909a60f7ab20a6d5e
    IMMUNE support package root   72b0384954acd01a375fe0ef62d80f9cd78946bc4885821ac2ad6e35c1a70a76
    age/sex root                  95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff
    age/sex package root          8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b
    candidate donor set           59769cfda71860570eddc005ab7ee844e74d2dda8146245ddb930ade88af6345
    B1 feature authority root     538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8
    B1 projection root            0a0739ec30c758a53070f76989cd4964d7d37224fd20890951b63aacf66e8002
    AT8 availability root         e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b

Authority packages are written under `outputs/`, which is gitignored, for the same
reason throughout this lane: committing them as tracked text would let a platform
line-ending transform change the bytes and therefore the root. A reviewer should
rebuild them from the named sources rather than expect them in the tree.

## Production geometry, as measured

    complete manifest blocks   8,915
    operators                     42
    operator-31 blocks         1,247
    operator-31 cells        638,150
    accepted IMMUNE cells     20,804
    candidate donors              46
    tail-measurable donors        45     (H20.33.037 at 67 cells is below the floor)
    sex composition        31 F / 15 M
    age range                 65–100     across 25 distinct values
    address width             41,238
    projected features        35,076     = 28,061 SCORING + 7,015 COHERENCE_HOLDOUT

The operator-31 store is exactly the `reader_fit` partition. The canonical
foundation SQLite reports op31 partitions as reader_fit 638,150, reader_validation
173,736 and reader_oracle 121,386; an independent scan of all 1,247 op31 metadata
files counts exactly 638,150. That equality settles the IMMUNE_FRACTION denominator
without adding any dependency on the 2.7 GB SQLite, and independently confirms by
count that the store excludes the validation and oracle partitions.

## Red-before, green-after

Every repair was reproduced before it was fixed, and the reproduction was verified
against the *previous* head rather than asserted. The procedure substituted that
head's module, ran the suite, and restored the working module with a digest check
before reporting.

| set | red against prior head | now |
|---|---|---|
| B2 R2 (A–I) | 25 of 26 | 36 of 36 green |
| B2 R3 (logical-root chain) | 8 of 9 | included above |
| IMMUNE_FRACTION production provenance | 18 of 26 | 26 of 26 green |
| age/sex candidate universe | 9 of 9 | 50 of 50 green |

The cases that were already green are reported as green regressions pinning
existing correct behaviour, not as reproduced defects. Specifically: a pre-filtered
manifest declared with the complete-manifest digest was already refused, the
logical rows already carried their paths (they were simply not bound), and the
eight formula-specification cases were green on arrival because item 1 built them.

## What each item did

1. **IMMUNE_FRACTION formula frozen** as an explicit successor specification,
   v1.0.0. Guarded so it can never claim to be recovered V18 executable semantics.
2. **Production provenance repaired.** The entrypoint no longer accepts
   preassembled rows or detached digest labels; it takes parent bytes, authenticates
   them, selects operator 31 internally, and derives the rows itself.
3. **External verification strengthened.** The loader binds membership, manifest,
   formula-spec and derivation-code identities, individually or through one parent
   contract root, and establishes stored == recomputed == externally expected.
4. **B2 R2 defects A–I closed**, including authenticate-then-filter, real raw-source
   authentication, the `expression_row` / `row_index` separation, authenticated
   payload-to-row coupling, geometry, anti-splice, the three external root verifiers
   and execution-path binding.
5. **IMMUNE support-count authority.** 46 donors, 20,804 cells. The 80-cell floor is
   tail-only and guarded against widening.
6. **Age/sex authority.** Reads only three columns from the pathology table and
   asserts no pathology field reaches its emitted schema.
7. **Technical-completeness authority** on the exact recovered formulas,
   threshold-free, with authority failures raising a global STOP rather than
   recording a donor as incomplete.
8. **Stagewise estimability preflight**, three stages, all pathology-blind, with the
   response refused outright.
9. **Governance corrected**, including the DEC-020 amendment below.

## Correction to DEC-020

DEC-020 recorded the measurement sensitivity as the binding parent threshold. That
was wrong. It applied the primary alpha of 0.025 to all three parent models, but
the frozen `sensitivity_directional_alpha` is 0.05, so the sensitivities are tested
at a *less* stringent alpha than the primary despite carrying fewer residual
degrees of freedom.

Frozen alphas: state primary 0.025, sensitivity directional 0.05, tail primary
0.02, negative 0.005.

| parent model | res df | alpha | r to clear |
|---|---|---|---|
| primary | 13 | 0.025 | **0.514** |
| composition sensitivity | 12 | 0.05 | 0.458 |
| measurement sensitivity | 11 | 0.05 | 0.476 |

So the **primary at alpha 0.025 is binding**, not the measurement sensitivity.

The previously recorded "80% power" figures are a noncentral-t reference
approximation, not exact power for the studentized Freedman–Lane permutation parent
test or the HC3 tail test. They are withdrawn and are **not** replaced by another
approximation. The exact overall parent PASS probability is to be evaluated
separately with the frozen V20 permutation engine. What survives is the residual
degrees of freedom and the Student-t-equivalent significance thresholds above,
which are exact given the design.

## Known limitations

- No CI is attached, so the reviewer cannot use a status check as evidence.
- The technical-completeness authority has never run on real data, because that
  requires the authenticated B2 substrate and production B2 is not authorized.
- The estimability preflight has never run on real donor roles, because the
  donor-role gate is shut.
- Availability V6 still needs either its exact ZIP bytes for artifact acceptance or
  the owner-witnessed re-derivation route.
- The eligible-donor authority does not exist yet. The 46 donors are the candidate
  upper bound, not the eligible set.
- The input dependency contract's reverse scan is a name-based heuristic over
  declared column-set literals. Every exclusion is declared inside the contract
  module rather than accepted from a caller, but the heuristic is not a proof.

## What a reviewer should attack next

The chain from closure root through logical root to physical plan root, now that
all three are externally verified and the logical root binds its closure and its
paths. Then the technical-completeness predicate, specifically whether any path
through it can drop a donor for a reason other than undefinedness. Then the
estimability preflight's claim to be pathology-blind.
