# V29 Lane B — V3/V1 masking reconciliation and integration review

Revision `258f84fa`, branch `lane-b/v29-root-closure-20260926`.
Scope: authority and provenance only. No training, no protected pathology, no
sealed outcomes, no terminal masking results, no `D_shared`/G5. No gate edited.

---

## Verdict first

**Mixed, and nothing here is a new emergency.**

* **Good news.** The substrate root is genuinely authenticated and three of its
  six consumers genuinely carry it. The two V3 masking artifacts are real,
  internally valid and their declared digests reproduce exactly. One of the two
  so-called "identical" V3/V1 conflicts turns out to be a pure naming problem
  with no scientific content, so it is cheap to fix correctly.
* **Bad news.** The other conflict is a real disagreement about the experiment,
  not about types, and no amount of type surgery can resolve it. Separately, the
  closure performs **no class check at all** on five of its roots, and the
  issuance boundary re-derives only two of thirty-two roots from live objects —
  so the "closure" is, at present, mostly an agreement between strings.
* **Still fine.** Zero roots were closed before this review and zero are closed
  after it. Nothing was promoted, nothing was cast, no placeholder was written.
  Training remains off and unissuable. Every finding here was made **before** any
  training run, which is the whole point of the preterminal discipline.

---

## Task 2 — the two V3 artifacts are not the same kind of conflict

PR151 correctly found two `isinstance` conflicts. Measured against what the
closure actually reads, they are different in kind, and lumping them together
would lead to the wrong fix for one of them.

Measurement: `scripts/agent/laneb_v29_masking_v3_v1_reconcile_v1.py`.

### 2.1 `masking_qualification_parameters_authority_sha256` — NOMINAL

The closure reads exactly two attributes off this parameter:

```
masking_qualification_parameters.primary_attacker_id
masking_qualification_parameters.primary_score_id
```

`MaskingQualificationParametersAuthorityV3` supplies **both**, with values
imported from the V1 module's own constants, so they cannot drift. V3 is a
strict **field superset** of V1: every V1 field is present, and every V1 numeric
is pinned by `validate()` to the frozen `EXPECTED` tuple from V2
(`targeted_partner_cap=8`, `ridge_candidate_pool_count=64`,
`ridge_score_feature_count=32`, `ridge_alpha=1/100`, `prefix_inner_fold_count=3`,
`prefix_candidate_count=20`, `prefix_floor=1/20`, `prefix_reduction=1/2`).

V3 then **adds** constraints V1 does not have: it binds the authenticated FULL104
substrate, binds the support-estimability root, pins the terminal universe
(`FULL_COMMON_CORE_17186_V1`, 17,186), carries four distinct discovery-provenance
digests with an explicit rule that they may not occupy current authority roles,
and asserts two blinding flags
(`terminal_full104_masking_outcomes_inspected=False`,
`protected_outcomes_authorized=False`).

Independently verified here, not taken from PR149:

| check | result |
|---|---|
| V3 artifact reconstructs and `validate()` passes | PASS |
| recomputed `canonical_digest` vs declared `parameter_authority_sha256` | agree (`e942c125…`) |
| V3's hard-pinned substrate vs byte-authenticated substrate | identical (`66f589e5…`) |
| V3's hard-pinned support root vs the digest recomputed from the committed support artifact | identical (`cab2cecd…`) |

That last row matters: the support root V3 hard-codes is exactly the digest I
recompute from `docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json`. The
two artifacts genuinely agree; this was not assumed.

**Recommendation: ADOPT V3, through an explicitly versioned successor closure.**
There is no scientific change to evaluate — V3 says everything V1 says, with the
same numbers, plus more. The only obstruction is the class name.

### 2.2 `masking_rng_replay_authority_sha256` — SCIENTIFIC DIVERGENCE

The closure reads three attributes:

```
masking_rng_replay.canonical_registry_authority_sha256
masking_rng_replay.outer_split_authority_sha256
masking_rng_replay.target_panel_authority_sha256
```

`MaskingRngReplayAuthorityV3` supplies **none of the three**. Two are renamed
(`canonical_registry_sha256`, `outer_split_receipt_sha256`) and the third,
`target_panel_authority_sha256`, **does not exist and is deliberately absent**.
The artifact says so in its own words:

```json
"target_panel_dependency": "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"
```

So removing the `isinstance` check would not help. The closure would still fail,
because the closure asserts a substantive claim — *the base-mask family is bound
to the target panel* — that V3 explicitly denies.

This is a disagreement about the experiment. It must be decided on the science.

#### What V3 changes, and whether the science is right

**Changes that are genuine improvements:**

1. **The global seed stops being a free parameter.** In V1 `global_seed` is a
   caller-supplied integer with no provenance; a different integer yields a
   different mask family and nothing records why that integer was chosen. In V3
   the seed is *derived* from the frozen roots. This removes a seed-shopping
   degree of freedom — under V1 one could try several seeds and keep whichever
   gave a favourable qualification result, and nothing downstream would show it.
2. **The per-draw namespace can no longer carry smuggled content.** V1 accepts
   any nonempty string as `cell_key`. A caller could pass the masking policy arm
   (silently destroying common random numbers across arms) or, worse, something
   value-dependent. V3 restricts `cell_key` to three fixed constants. This is the
   value-independence requirement enforced in code rather than trusted.
3. **`outer_fold` is bounded to 0..3**, matching the authenticated four-fold
   split. V1 accepts any nonnegative integer, so a wrong fold index silently
   produces a valid-looking seed.
4. **Prospective blinding is asserted in the object**
   (`terminal_outcomes_inspected_before_freeze` must be `False`).
5. **Panel independence is the correct dependency direction.** Under V1, changing
   the eventual panel re-rolls every base mask, which makes it impossible to bind
   mask geometry in an outcome-blind burden audit before H3/G5 select a terminal
   panel. Under V3, choosing a panel later only *subsets* an already-defined mask
   family. This preserves common random numbers across panel definitions, which
   is exactly what a paired comparison needs.

**The concern I raised, and how it resolved.** V3's `derive_seed` no longer takes
a cell identity — `cell_key` is a stream namespace, not a cell. If per-cell masks
were then drawn by consuming one stream in iteration order, every cell's mask
would depend on its position in block order rather than on its `selection_row`,
and repacking the Level-4 blocks would silently change every mask. That is a
failure mode this project has already been bitten by.

It is **not** realized. `src/sea_ad_jepa/v5/audit_b_n1_runtime_rng_bridge_v1.py`
freezes the runtime composition, and the base-mask preimage is:

```
PIPE_JOIN_NAMESPACE_GLOBAL_SEED_OUTER_FOLD_INTEGER_TARGET_ADDRESS_UNIVERSE_SIZE_V1
METHOD_IN_BASE_MASK_SEED        = False
TARGET_PANEL_IN_ANY_RUNTIME_SEED = False
```

There is no per-cell draw at all. The common-random base mask is one mask per
(outer fold, target address, universe size), shared by every cell in that
stratum. That is order-independent, repack-invariant, and is what "common random
numbers" should mean here. The policy arm is excluded, so cross-arm comparisons
remain paired; the panel is excluded, so cross-panel comparisons remain paired.
The bridge also records that the typed `derive_seed` helper is explicitly **not**
the runtime seed function, which removes the ambiguity rather than papering it.

**Two qualifications that should be carried forward, neither a defect today:**

* *The mask geometry is keyed on the integer molecular-address column.*
  `TARGET_ID_RULE_ID = INTEGER_MOLECULAR_ADDRESS_COLUMN_V1`. The registry's own
  invariant says `molecular_address_index` is "contiguous 0..N-1 and strictly
  increasing in file order" — that is a position in a file, whereas
  `molecular_address_id` is the stable identity. This is safe **only** because
  V3's `validate()` hard-pins the registry to `7d61ed7b…`, so within that exact
  frozen file the index is a deterministic function of identity. It follows that
  the registry hash pin is load-bearing, not hygiene: a semantically identical
  registry rebuilt in a different row order would silently re-roll every mask. A
  future successor should seed from `molecular_address_id`.
* *The seed depends on the burden ladder and the qualification parameters.*
  Within one frozen experiment these are constant, so common random numbers
  across arms and across burden levels are preserved. But any revision to the
  ladder or to a masking parameter re-rolls the whole mask family — a weaker
  version of the problem V3 set out to fix. It is defensible, because both are
  genuinely upstream of mask construction in a way the panel is not, but it
  should be stated rather than discovered later.

**Recommendation: V3's scientific direction is correct and I recommend adopting
it — but it cannot enter the current closure, and it is not adopted by anything
I have done here.** The closure's three RNG equality checks must be *replaced*,
not satisfied. That is a closure change, which is an owner decision.

### 2.3 What must never be done

* Do **not** cast, subclass or re-label a V3 object to satisfy
  `isinstance(..., MaskingRngReplayAuthorityV1)`. V1's `validate()` requires
  `seed_namespace_id in ("V5_COMMON_RANDOM_BASE_MASK_V1",)`; V3's namespace is
  `V5_COMMON_RANDOM_BASE_MASK_PREPANEL_ROOT_DERIVED_V3`. Any subclass that
  overrode `validate()` to get past that would be fabricating a V1 instance,
  which is precisely the prohibited remedy.
* Do **not** substitute the committed
  `V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1` for the absent
  `OuterDonorSplitAuthorityV1`. A split *receipt* is evidence about donor folds;
  the split *authority* is the frozen contract the closure digests. They are
  different scientific roles with different schemas, and promoting one to the
  other would be exactly the foreign-role receipt substitution this lane forbids.

### 2.4 Successor design (proposed, NOT implemented)

A successor closure `validate_current_v5_authority_closure_v3` should:

1. Accept the parameters root as an **explicit union of named classes**
   (`MaskingQualificationParametersAuthorityV1 | V3`), not as a structural
   `Protocol`. A protocol would admit any object carrying two attributes and
   would reopen exactly the role-splicing hole the `isinstance` check exists to
   close.
2. **Record the accepted version in the closure payload**, so the closure digest
   distinguishes a V1-backed closure from a V3-backed one. Without this, two
   scientifically different graphs could produce indistinguishable closures —
   which would be a new provenance hole, not a fix.
3. For the RNG root, **replace** the three V1 equality checks with checks against
   V3's five actual roots (substrate, registry, split receipt, qualification
   parameters, burden ladder), and additionally assert
   `target_panel_dependency == "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"` so
   the panel-independence claim is enforced rather than merely documented.
4. Carry the runtime-composition bridge as a first-class binding, since it — not
   the typed `derive_seed` — defines the mask geometry actually drawn.

None of this is implemented on this branch. It is a design recommendation for the
owner, and the closure remains untouched.

---

## Task 3 — integration review of the remaining chain

### 3.1 Five roots have no class check whatsoever

Measured by `scripts/agent/laneb_v29_closure_root_extract_v1.py`:

| enforcement | roots |
|---|---|
| `isinstance` enforced | 24 |
| duck-typed, **no class check at all** | 5 |
| raw string cross-binding constant | 3 |

The five unchecked roots are `representation`, `support_estimability`,
`base_training_estimand`, `protected_registry` and `critical_test`. They are
typed `Any` and reached only through `getattr(..., default=None)` or bare
attribute access. Any object exposing `validate()`, `canonical_digest()` and
`training_authorized == False` is accepted.

These are not peripheral. `support_estimability` carries **8** downstream
equality bindings and `representation` **5** — the two heaviest loads in the
entire graph. The closure verifies their *content* against other roots but never
verifies *what they are*.

This is the mechanism behind PR156. That red-team's `SyntheticCritical` class
works because `critical_test` is duck-typed; the same substitution is available
for four more roots.

### 3.2 The issuance boundary re-derives 2 of 32 roots

`issue_training_authority_v1` takes `closure_v2` as a **Mapping**, not as the
return value of a live validator call. It checks the schema string, checks the
root *names* match the 32-tuple, and recomputes the closure digest from the very
mapping it was handed. That check is self-referential: any 32 syntactically valid
hex strings satisfy it.

Only `critical_test_authority_sha256` and `runtime_source_authority_sha256` are
re-derived from live objects via `_live_digest`. **Thirty of the thirty-two
upstream roots are never re-derived from anything at issuance.**

`preexecution_authority_sha256`, the 33rd root, is computed at issuance from the
same caller-supplied mapping, so it adds no independent evidence either.

### 3.3 The two "live" anchors cannot detect a fabrication

This sharpens PR156 rather than repeating it. The two roots the issuer *does*
re-derive are themselves self-declared:

* `CriticalTestExecutionAuthorityV1` requires
  `status_by_test[test_id] == "EXECUTED_PASS"` for every required test — but
  `required_test_ids` and `status_by_test` are both caller-supplied. Declaring a
  single trivial test id with status `EXECUTED_PASS` satisfies it. Nothing binds
  the authority to a pytest run, a test count floor, or the committed suite;
  `test_suite_source_sha256` is a free hex string never compared to anything.
* `CurrentRuntimeSourceAuthorityV1` requires four digests that are merely
  well-formed and mutually distinct. None is compared against an actual file.

So the issuance boundary has **no** independent anchor to reality. PR156 called
this a provenance gap in a caller-facing function; measured here, the gap is
total rather than partial.

This is a finding about what the code proves, not an accusation that anything was
faked. No training authority has been issued.

### 3.4 Artifact self-authentication is uneven

Three committed artifacts are stored as the exact canonical JSON bytes their own
`canonical_digest()` hashes — the file **is** its own authority digest:

| artifact | digest = file bytes sha256 |
|---|---|
| `docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json` | `92756711…` |
| `docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json` | `cab2cecd…` |
| `docs/agent/V5_BASE_TRAINING_ESTIMAND_AUTHORITY_20260915.json` | `a766d42f…` |

This is a strong property and should be the standard.

`docs/agent/V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json` is **not** in
that form. It carries the schema label `V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1`
but is a structured document with nested `ADDRESS_REGISTRY`,
`FULL104_SUBSTRATE` and `OPERATOR_ADDRESS_OBSERVATION_STATE` blocks and none of
the eight declared dataclass fields at top level. Reaching an instance requires an
external adapter that decides which nested block fills which authority role.

I reproduced PR149's adapter independently and it does reconstruct to
`28b20a45…`, matching the document's own `canonical_authority_digest`, and it does
supply the authentic substrate. So the binding is real. But the role-to-field
mapping lives in code outside the artifact, so this root's validation is not
reproducible from the artifact alone. The matrix records it as
`PASS_VIA_ADAPTER`, never as equivalent to the three self-authenticating files.

### 3.5 Parent-digest chain verified

Every parent the RNG V3 authority declares was checked against a committed
artifact, not taken on trust:

| declared parent | value | verified against |
|---|---|---|
| `full104_substrate_sha256` | `66f589e5…` | file bytes, 2,372,002 B |
| `canonical_registry_sha256` | `7d61ed7b…` | registry file hash in the registry document |
| `outer_split_receipt_sha256` | `5d616c9c…` | `receipt_sha256` in both committed copies of `full104_split_receipt_v1.json` (file `56f045d7…`, byte-identical) |
| `qualification_parameters_authority_sha256` | `e942c125…` | recomputed digest of the committed parameters V3 artifact |
| `burden_ladder_authority_sha256` | `85148fdf…` | declared `authority_sha256` of the committed burden ladder V2 artifact |

The RNG V3 authority's own digest `775aba50…` and global seed
`1267387626254385975` both reproduce, and both match the constants pinned in the
runtime bridge.

Historical note: `B3_RNG_V3_AUTHORITY_BLOCKER.md` (2026-09-22) recorded that the
RNG V3 artifact could **not** be produced because the builder read
`authority_sha256` where the producer wrote `parameter_authority_sha256`. That
blocker was resolved at some point before `258f84fa`; the artifact now exists and
validates. The note remains accurate about its own moment and is not retracted.

---

## Closure status

**FALSE.** `fully_closed = 0` of 33. It is computed in
`scripts/agent/laneb_v29_root_status_matrix_v2.py`, not asserted.

For any root to be closed it would need, at minimum: a committed artifact of the
class the closure actually requires; that artifact self-authenticating or bound
by a committed adapter; every closure equality binding naming it satisfied by a
committed artifact on the other side; and an issuance path that re-derives it
from a live object rather than accepting a hex string. No root meets all four.

---

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
