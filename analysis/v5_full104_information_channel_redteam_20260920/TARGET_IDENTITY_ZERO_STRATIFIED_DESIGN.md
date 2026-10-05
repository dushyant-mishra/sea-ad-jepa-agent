# Audit F — target identity × target-zero: design and controls

Date: 2026-09-20
Current V5 real-measurement status: **`DESIGN_OPEN__REAL_TEACHER_REQUIRED`**

Produced by `scripts/audit_f_target_identity_zero_decomposition_20260920.py`,
validated by `tests/test_v5_audit_f_target_identity_zero_v1.py` (10 passed, 0
skipped).

> **Semantic correction.** The scalar zero/detection/quantitative decomposition in
> this file is a historical mechanism fixture only. Current V5 authority defines
> `QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1`, with
> `HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1`,
> `QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1`, and
> `SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1`. Therefore target detection or scalar
> expression must **not** be treated as desired positive components of the future
> V5 teacher target.

This is **not** generic target-identity archaeology, which is already open and is
not redone here. It asks one new question.

---

## 1. The new question

At `core_measured_zero_frequency = 0.8329826626244999`, about five out of six
(cell, core address) pairs are measured zeros. When the model is asked to predict
a masked target on such a cell:

> How much of the target representation could be **address identity and cell
> context**, rather than anything target-specific?

On a target-zero cell the target's quantitative value is constant. Nothing can be
attributed to it *even in principle*. So whatever variance the representation
carries there comes from identity and context — and a model can score well on
those pairs without having learned target-specific biology at all.

## 2. The decomposition

For a representation `T(cell, address)`, fit nested least-squares models and take
incremental variance explained:

```
M0: T ~ address identity                        -> R2_identity
M1: T ~ address identity + context              -> R2_identity_context
M2: M1 + binary detection state of the target   -> R2_plus_detection
M3: M2 + quantitative value among detected      -> R2_plus_quantitative
```

```
share_identity     = R2_identity
share_context      = R2_identity_context  - R2_identity
share_detection    = R2_plus_detection    - R2_identity_context
share_quantitative = R2_plus_quantitative - R2_plus_detection
```

**The ordering is declared before any result**, and it is deliberately
conservative: identity is the cheapest explanation and quantitative the most
demanding, so variance is credited to target-specific information only after
identity, context and mere detection have had their chance at it. A different
ordering would produce different shares, which is why the ordering is frozen here
rather than chosen later.

Everything is reported **stratified** by target-observed-zero and
target-observed-nonzero. Pooling the two hides precisely the effect of interest,
and the strata must partition every attempted unit — a test pins that none are
dropped.

`zero != missing` throughout. A measured zero is evidence of non-detection, not
absence of evidence.

## 3. Controls, and what they establish

Six synthetic representations of **known composition**, all built at the
authoritative sparsity so the decomposition is exercised at the geometry it will
actually face:

| fixture | identity | context | detection | quantitative |
|---|---|---|---|---|
| `pure_noise` | 0.0008 | 0.0004 | 0.0001 | 0.0001 |
| `identity_only` | **0.9980** | 0.0000 | 0.0000 | 0.0000 |
| `identity_plus_context` | 0.1988 | **0.8008** | 0.0000 | 0.0000 |
| `detection_only` | 0.6806 | 0.0000 | **0.3179** | **0.0000** |
| `quantitative` | 0.2106 | 0.0002 | 0.4932 | **0.2955** |
| `identity_context_detection_quantitative` | 0.1476 | 0.5947 | 0.1983 | 0.0591 |

The load-bearing row is `detection_only`. A representation that responds to
*whether* the target is on but not to *how much* must yield a quantitative share
of **zero** — and it does (0.0000). Had the decomposition credited that to
quantitative, a teacher that merely memorised detection state would look like it
had learned expression. That is exactly the error this audit exists to catch, and
the control proves the instrument does not make it.

The complementary control is `quantitative`, which yields a genuinely nonzero
quantitative share (0.2955), so the instrument is not simply insensitive.

A further test pins the structural fact: within the target-zero stratum the
quantitative share is `< 1e-6` and the detection share is `< 1e-6` — both are
constant there — while identity + context explain more than half the variance.

## 4. Why no real number is reported

**No lawful current teacher representation exists.** Producing one requires
training or protected outcomes, both out of scope for this phase. Fabricating a
stand-in and reporting its decomposition would be worse than reporting nothing:
it would occupy the slot where the real measurement belongs.

So the real measurement is marked

```
CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION
```

and the instrument is committed now, with its controls passing, so the
measurement is **unavoidable** once a real teacher exists rather than negotiable
after the fact. Running it then requires only supplying `representation`,
`address_code`, `context` and `target_value`; no design decisions remain open.

## 5. Relation to the other audits

Audit E decomposes *partner association* into co-detection versus quantitative
co-expression. Audit F decomposes the *target representation* along the same
seam. They are the same distinction applied at two different points in the
pipeline, and a consistent answer across both would be considerably stronger
evidence than either alone.

If, when the real teacher exists, identity + context dominate on target-zero
cells, then for ~83% of pairs the prediction task carries little target-specific
information, and both the masking evaluation and any claim about learned
biology would need restating in those terms. That is a hypothesis with a
preregistered test, not a finding.

## 5b. Successor decomposition for the actual V5 target

The real-teacher measurement must be redesigned around the current query-local
latent semantics:

1. **F1 — address identity baseline:** variance in `T(c,q)` explained by query
   identity `q` alone.
2. **F2 — cell/context main effect:** additional variation explained by lawful
   global cell context shared across queries.
3. **F3 — query × context interaction:** reproducible query-specific contextual
   variation after removing F1/F2; this is the component closest to
   `QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1`.
4. **F4 — technical decoy explanation:** how much of F2/F3 is explained by lawful
   source/operator/depth/sparsity/support geometry alone.
5. **F5 — query-scalar invariance:** a **negative control** requiring the teacher
   state to remain invariant to direct intervention on the withheld query scalar
   when lawful non-query context is held fixed.
6. **F6 — remaining-RNA necessity:** removing lawful remaining-RNA/context should
   destroy the query-local interaction in the expected direction.

Because the teacher state is multivariate, the successor must use a prospective
vector-valued decomposition (for example Frobenius SSE/SST plus a declared
per-latent-dimension summary) with scalable grouped/fixed-effect residualization.
No scalar fixture number in this file may set that design's threshold or expected
magnitude.

## 6. Status

```
DECOMPOSITION_DESIGN         = FROZEN
CONTROLS                     = PASSING (10 tests, 0 skipped)
REAL_MEASUREMENT             = CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION
BIOLOGICAL_CLAIM             = NONE
TRAINING_OFF
```
