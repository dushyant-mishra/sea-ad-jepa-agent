# Phase I — qualification of the heavy B/C/E sufficient statistics

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`**
Determination: **PASS — reuse qualified. No rebuild required.**

```
BASE_SHA : ae5dc5c624fff341b8ef30c5359c55528383920a
branch   : claude/v5-full104-blocker-clearance-20260921
```

---

## 1. Why this gate exists

The 242 MB artifact `core_sufficient_statistics_v1.npz` was produced **before**
the shared builder adopted the exact production `source_library` parser. Its
producer used `int(float(token))`. `EXTERNAL_ARTIFACTS.json` therefore marked it

```
REQUIRES_METADATA_ONLY_STRICT_PARSE_EQUIVALENCE_CHECK_BEFORE_REUSE
```

Audits B, C and E all consume it, so nothing downstream may proceed until this
is settled one way or the other.

## 2. Scientific question

> Does the legacy `int(float(token))` coercion return **exactly the same
> integer** as the production parser for every one of the 4,553,407 authenticated
> FULL104 metadata rows — and are the artifact's contents consistent with the
> authenticated substrate?

## 3. What would have falsified reuse

Any single one of: a strict-parser rejection, a legacy-parser failure, a parsed
**value** difference, a row-count mismatch, or a metadata hash mismatch. Any of
these forces `REBUILD_HEAVY_SUFFICIENT_STATISTICS_REQUIRED`. There is no
"small enough" branch and the existing NPZ is never patched.

## 4. Result — parser equivalence

`scripts/audit_source_library_parser_equivalence_20260920.py`,
evidence `evidence/parser_equivalence/SOURCE_LIBRARY_PARSER_EQUIVALENCE.json`.

| | |
|---|---|
| blocks checked | **8,915** |
| rows checked | **4,553,407** |
| strict-parser rejections | **0** |
| legacy-parser rejections | **0** |
| **value or parse mismatches** | **0** |
| block manifest SHA-256 | `66f589e5…` (authenticated) |
| every metadata SHA-256 | authenticated per block |
| runtime | 2m04s |

Token syntax encountered:

| syntax | rows |
|---|---|
| integer | 4,552,895 |
| **decimal** | **512** |
| scientific | 0 |

The 512 decimal-syntax tokens matter. They are exactly the class where
`int(float(…))` and the strict parser *could* diverge — a fractional value would
be silently truncated by one and rejected by the other. All 512 are integral
decimals, and both parsers agree. That is what makes this a real check rather
than a formality.

```
reuse_decision = ALLOW_CONTENT_ADDRESSED_REUSE_WITH_CURRENT_PARSER
```

## 5. Result — independent aggregate qualification

Parser equivalence shows the artifact's **inputs** were parsed identically. It
does not show the artifact's **contents** are consistent with the substrate. That
gap is closed by `scripts/qualify_heavy_sufficient_statistics_20260920.py`,
evidence `evidence/parser_equivalence/HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION.json`.

| invariant | expected | observed |
|---|---|---|
| artifact SHA-256 | `f77dff47…` | **matches** |
| rows traversed | 4,553,407 | 4,553,407 |
| donors | 104 | 104 |
| core addresses | 17,186 | 17,186 |
| `selection_row` range | [0, 4,553,406] | [0, 4,553,406] |
| HVS cells | 198,718 | 198,718 |
| NPH52 cells | 236,476 | 236,476 |
| SEA_AD cells | 4,118,213 | 4,118,213 |
| per-donor cell totals | artifact | **all 104 agree** |
| failures | 0 | **0** |

### The substantive check — three independent routes

Total source library across all 4,553,407 cells:

| route | value |
|---|---|
| recomputed from metadata by this script (8 workers) | **122,517,308,792** |
| the artifact's own `libraries` vector | **122,517,308,792** |
| Audit A, a different script in a different run | **122,517,308,792** |

Exact integer equality, three ways. Route 1 shares no accumulation code with the
artifact's producer, so agreement is corroboration rather than tautology.

Per-donor library sums were additionally cross-checked for a deterministic
12-donor sample, keyed by a hash of a fixed salt and the donor id — chosen
without reference to any result. Each was compared against the artifact's cell
vector indexed through pass1's authenticated `cell_donor` map, a third
independent source of the cell→donor assignment.

```
verdict = HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE
```

## 6. Controls

`tests/test_v5_heavy_sufficient_statistics_qualification_v1.py` — 8 tests, 0 skipped.

**Positive control.** A synthetic store and artifact that agree by construction
must qualify.

**Five negative controls**, each corrupting exactly one invariant and requiring
refusal:

| control | corruption | must be refused because |
|---|---|---|
| artifact SHA mismatch | bound digest wrong | content addressing is the reuse basis |
| **library value drift** | one cell's library differs by **one count** | this is the substantive check; a one-count drift across 4.55M rows must not pass |
| per-donor cell total mismatch | one donor off by one cell | geometry must match the substrate |
| core dimension mismatch | core size off by one | address space must match |
| tampered metadata hash | one block's digest zeroed | the sweep must never run on unauthenticated metadata |

Plus the pre-existing parser controls (positive, float-precision spillover above
2^53, fractional truncation) — 3 tests, all passing.

Expectation constants were parameterized via CLI **solely** so the instrument can
be exercised against a fixture with a known answer. The defaults remain
hard-bound to the authenticated census, and the real run uses them.

## 7. Red-team

| question | answer |
|---|---|
| Held-out data used to choose method? | No. Metadata only; no expression matrices, no folds, no outcomes. |
| Reduced-pool or historical value promoted? | No. All 4,553,407 rows, all 8,915 blocks. |
| Estimand silently changed? | No. This qualifies an artifact; it computes no score. |
| Undefined turned into zero? | No. Any parse failure is a counted failure, never a zero. |
| Population weighting used where donor weighting intended? | Not applicable — these are exact counts and sums, unweighted by construction. |
| Cache with changed semantics reused? | **That is precisely what this gate tested**, and the semantics are proven identical. |
| Could the positive control pass with a wrong implementation? | No — five negative controls each falsify a different invariant, including a one-count drift. |
| Threshold chosen after seeing the result? | No thresholds exist here. Every criterion is exact equality. |
| Sealed information used? | No. |
| Second computation reproduces the headline? | Yes — three routes on the headline total. |

## 8. What this establishes

The existing 242 MB artifact is **byte-identical to what the current production
parser would have produced**, and its aggregates reconcile exactly with the
authenticated substrate along an independent route. Audits B, C and E may reuse
it under content addressing.

## 9. What this does NOT establish

- It says nothing about whether B, C or E's **scientific conclusions** are
  correct — only that their shared input is sound.
- It does not qualify the artifact for any role beyond reconnaissance. It is
  `CURRENT_FULL104_RECONNAISSANCE`, not authority.
- It does not validate the per-address or per-stratum matrices cell-by-cell;
  it validates geometry, per-donor totals, and the exact global library sum.
- It opens no terminal outcome and authorizes no training.

## 10. Blockers discovered

None. The predeclared PASS branch was taken.

```
PARSER_EQUIVALENCE               = PASS (0 mismatches / 4,553,407 rows)
HEAVY_ARTIFACT_REUSE             = QUALIFIED
REBUILD_REQUIRED                 = NO
TERMINAL_MASKING_OUTCOMES        = UNOPENED
TRAINING_OFF
```

**Next dependent step:** Phase II — authenticated fold-aware C2 source × fold
estimability, which may now consume this artifact.
