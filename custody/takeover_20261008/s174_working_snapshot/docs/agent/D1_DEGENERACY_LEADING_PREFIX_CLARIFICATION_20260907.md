# D1 Degeneracy / Leading-Prefix Clarification V1 — Prospective Authority

Status: **FROZEN PROSPECTIVE CLARIFICATION CANDIDATE — NO REAL D1 OUTCOME INSPECTED**

Date: 2026-09-07

Base scientific authority:
`docs/agent/D1_REAL_DATA_PARAMETER_DERIVATION_AUTHORITY_20260907.md`

Implementation candidate under review:
`566079ad2ef4a1e99efff77bfc0bdb79559b77b7`

## Purpose

The base authority contains two requirements that need one exact operational
reading before a trained teacher exists:

1. adjacent components whose population eigengap is not resolved are a **joint
   subspace** and may not receive separate biological identities; and
2. production `D` is a **leading-prefix** claim: stability must remain
   separated from the null for every leading rank through the claimed prefix.

This clarification resolves only how those requirements compose. It does not
change the parallel-analysis null, donor-block resampling, confidence level,
population, or any production numerical value.

## Frozen rule

1. Form maximal contiguous degeneracy blocks from the prospectively frozen
   eigengap-uncertainty rule.
2. Candidate ranks are only cumulative **block boundaries**. A rank that cuts
   through an unresolved block is not an identified object and is never tested
   as an independent candidate.
3. Walk admissible block-boundary ranks in increasing order.
4. A boundary is accepted only when its donor-block subspace-stability lower
   bound separates from the corresponding donor/operator-preserving null upper
   bound.
5. Stop at the first failed **admissible boundary**.
6. `D` is the last accepted admissible boundary.
7. A later/larger boundary may **not rescue** an earlier failed admissible
   boundary.
8. If the first admissible boundary fails, emit
   `STOP_D1_NO_STABLE_RANK`; no fallback D exists.

## Consequences

- If axes 1-3 form one unresolved leading block, ranks 1 and 2 are not
  admissible. Rank 3 may be the first tested object and may qualify.
- If axis 1 is an isolated block and axes 2-3 form the next block, admissible
  ranks are 1 and 3. If rank 1 fails, rank 3 cannot rescue it even if the
  3-dimensional projection overlap is large.
- This preserves the original leading-prefix claim while avoiding the forbidden
  requirement that an arbitrary axis inside a degenerate block be individually
  stable.

## Rationale

A large subspace can have high projection overlap even when an earlier
identified leading component does not recur across donor blocks. Allowing the
larger subspace to rescue that earlier failed boundary would silently change the
estimand from a stable leading hierarchy to “some larger span that happens to
separate.” That is not the frozen D1 claim.

Conversely, demanding rank-by-rank stability **inside** an unresolved block
would assign identity to axes the base authority explicitly says are not
identified. Block-boundary prefixing is the unique fail-closed composition of
the two frozen requirements.

## Required executable attacks

Any implementation bound to this clarification must prove at least:

- `[[0,1,2]]` with rank-3 separation and arbitrary rank-1/rank-2 behavior may
  return D=3 because 3 is the first admissible boundary.
- `[[0],[1,2]]` with rank-1 failure and rank-3 success must STOP.
- `[[0],[1,2],[3]]` with rank-1 and rank-3 success but rank-4 failure returns
  D=3.
- No candidate rank inside a multi-axis block can affect D.
- Reordering or overlapping degeneracy blocks is invalid input and must fail
  before adjudication.

## Governance

This clarification is outcome-blind and may be frozen before a healthy trained
teacher exists. It authorizes no D1 execution and no data access.
