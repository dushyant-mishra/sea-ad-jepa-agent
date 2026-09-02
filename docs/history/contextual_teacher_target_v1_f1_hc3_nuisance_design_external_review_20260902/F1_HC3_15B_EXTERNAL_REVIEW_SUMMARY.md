# F1 HC3 Command 15B — independent external-review summary

Date: 2026-09-02

## Overall adjudication

`PROCEED_WITH_NARROW_PROVENANCE_REPAIR_BEFORE_15C`

The current-cohort scientific selection and numerical design are accepted. Command 15C integration and F1 evaluation should remain blocked until the two provenance concerns below are repaired without changing the selected design or scientific rules.

## Accepted result

- Published package: `outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902/`
- Package manifest SHA-256: `a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174`
- Selected prefix: `(HVS=5, NPH52=0, SEA_AD=4)`.
- Selected design: 104 donors × 16 columns, rank 16, df 88.
- Selected-design SHA-256: `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.
- The 30-row admissible frontier has one Pareto-maximal and universally dominating row.
- Exact reconstruction from authenticated primitives matches the published float64 array and byte stream.
- SVD and independent pivoted QR agree at rank 16; maximum leverage difference is about `6.66e-16`.
- All 104 leave-one-donor deletions retain rank.
- `min(1-h)=0.13062683379202333`, safely above the frozen HC3 boundary `1.4901161193847656e-08`.
- Adding the excluded NPH52 direction fails closed at `NPH52::human_NPH_906`.
- No expression, model/checkpoint, forward, outcome, training, optimizer, or EMA access occurred.

## Review verdicts

1. Prospective selection/statistical validity: `CONCERN` — scientific rule and outcome blindness pass; chronology anchoring is incomplete.
2. Numerical linear algebra/HC3: `PASS`.
3. Provenance/firewall/dataset semantics: `CONCERN` — hashes, firewall, and biology semantics pass; external root and review-record authentication are incomplete.

## Provenance concerns

### P0-1: prospective chronology is not independently authenticated

The executable requires the exact frozen selection-contract hash before applying the frontier rule, so runtime ordering is enforced. However, the creation/application timestamps in `F1_HC3_15B_AUTHORITY.json` originate from hard-coded source literals rather than a separately anchored pre-application record. The package alone therefore does not cryptographically prove when the contract was authored relative to result inspection.

Required repair: bind the already-existing selection-contract SHA-256 `3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac` to an external, append-only pre-application execution/provenance record if such a trustworthy record exists. Do not invent or rewrite chronology. If it cannot be independently established, retain that limitation explicitly rather than claiming cryptographic prospectivity.

### P0-2: review and package-root authentication is too textual

The finalizer recognizes the six internal review outcomes through expected label substrings and counts of `VERDICT: PASS`. Fabricated prose could satisfy that gate. The top-level manifest hash is reported externally but is not itself anchored by a separate root artifact inside an independent review chain.

Required repair: create machine-readable per-review records with explicit lens identity, reviewer/run identity, evidence-root hash, verdict enum, findings hash, and record hash; independently validate all six records. Externally anchor the published 15B manifest SHA without modifying the frozen package.

## Scope of the repair

This is provenance-only. Preserve unchanged:

- selection contract and rule;
- all 70 frontier rows and 30 admissible rows;
- selected triple `(5,0,4)`;
- exact selected design bytes and SHA;
- rank, leverage, LOO and HC3 results;
- nuisance primitives and donor population;
- all firewall restrictions.

Do not patch the production F1 decision engine, run outcomes, or begin F1 evaluation during this repair.

