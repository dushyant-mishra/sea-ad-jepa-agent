# TD relational successor — implementation-boundary amendment

Date: 2026-10-13
Status: `PROSPECTIVE_INTERFACE_AMENDMENT__NO_SYNTHETIC_OR_REAL_OUTCOME_READ__NO_EXECUTION_AUTHORITY`
Parent: `TD_FINE_RARE_RELATIONAL_SUCCESSOR_MECHANICS_PREFREEZE_20261012.md`

## Purpose

Move the complete mathematical estimand into Target Discovery before any external known-truth package is opened.

The earlier mechanics prefreeze allowed 64 prospectively supplied matched Y-identity reassignments and the first adapter accepted precomputed Z/X/Y distance matrices. Those choices leave part of the TD estimand outside the TD lane. This amendment prospectively supersedes only that implementation boundary. It does **not** change the scientific question, scale grid, donor statistic, null family, thresholds, multiplicity rule, rare-program specificity rule, or failure scope.

No synthetic qualification outcome and no new real biological outcome has been opened under the successor.

## External fit-side package now supplies observations, not TD statistics

For each opaque challenge/profile, the external read-only fit view may supply only:

- `source`;
- `panel_id`;
- three mutually disjoint observed molecular views `Z`, `X`, `Y`;
- exactly 512 blinded feature IDs per view;
- observed values for each cell×feature;
- measured/support mask for each cell×feature, preserving measured zero versus structurally unmeasured;
- donor ID;
- operator ID;
- immutable global/entity row ID;
- `source_library`;
- full-row detected-gene count;
- frozen focal-anchor mask;
- frozen lawful neighbor-pool mask;
- the already-frozen minimum focal-anchor requirement for that profile.

The external package may **not** supply:

- Z/X/Y cell-cell distance matrices;
- pair-coordinate selections;
- pair-sign matrices;
- TD null permutations;
- TD observed/null statistics;
- expected TD verdicts or controller truth.

## TD-owned pair-coordinate construction

Each view contains exactly 512 features. Feature IDs must be unique within a view and the Z/X/Y feature sets must be pairwise disjoint.

For view `V in {Z,X,Y}` enumerate every unordered feature pair. Canonicalize the two feature IDs lexicographically as `g0 < g1`, hash:

`TD316|panel|<P>|view|<V>|g0|<g0>|g1|<g1>`

with SHA-256, sort by full digest ascending with `(g0,g1)` as deterministic tie break, and retain the first **2,048** pairs.

The 512-view width, 2,048 pair width and 256 informative-coordinate threshold are historical continuity/falsification constants from TD57C/TD59. They are not production constants and must themselves survive known-truth qualification.

## TD-owned pair signs and concordance distance

For a cell and selected pair `(g0,g1)`:

- the coordinate is structurally resolved only if both features are measured in that cell;
- if resolved, pair sign is `sign(value[g0] - value[g1])` in `{-1,0,+1}`;
- if either feature is structurally unmeasured, the pair sign is unresolved.

For cells `a,b`, a selected pair coordinate is informative only when:

1. both cells have resolved pair signs; and
2. at least one of the two resolved signs is nonzero.

Require at least **256 informative pair coordinates**. Otherwise the cell-cell distance is non-estimable.

When estimable:

`d(a,b) = mean(abs(sign_a - sign_b)) / 2`.

This is the same concordance-distance family used by TD57C/TD59.

## TD-owned matched Y-cell null construction

The successor inherits the exact TD37A v1.1 depth/detection block construction rather than accepting upstream permutations.

Within each donor×operator stratum of size `n`:

1. rank detected-gene count lexicographically by `(detected_genes, global_row)`;
2. rank source library lexicographically by `(source_library, global_row)`;
3. ordinal ranks are `0..n-1`, no averaging;
4. rank fraction is `ordinal_rank / n`;
5. detected octile is `floor(8 * detected_rank_fraction)`;
6. sort rows by `(detected_octile, library_rank_fraction, detected_rank_fraction, global_row)`;
7. partition consecutive rows into blocks of 8;
8. if the final remainder is exactly 1, append it to the previous block to make 9; remainders 2..7 remain separate; singleton strata remain singleton.

For null replicate `q=0..63` and each block of size `m>=2`, use:

`shift = 1 + SHA256_U64("TD316|null|panel|<P>|q|<q>|source|<S>|donor|<D>|operator|<O>|block|<b>") mod (m-1)`

where `SHA256_U64` is digest bytes 0..7 interpreted as unsigned big-endian uint64.

Y identities are cyclically shifted forward within the sorted block. Singleton blocks self-pair. The resulting mapping must be a full cell permutation preserving donor, operator and TD37A block membership.

## Fit/controller firewall

The observation-to-geometry builder and null builder are TD code and are part of the exact executor identity that must pass known-truth qualification.

The synthetic lane remains responsible only for frozen observations/support and controller truth. It does not own TD pair selection, distance construction, null construction, source statistics or verdicts.

## What remains unchanged

All previously frozen successor mechanics remain binding:

- scales `1/8, 1/6, 1/4, 1/3, 1/2`;
- minimum 5 selected neighbors;
- minimum 20 resolved relations per donor;
- minimum 5 measurable donors per source-scale;
- donor median statistic;
- 64 nulls;
- family-wise max-null p95 at sorted index 60;
- strict `observed > 0.5` and `observed > family_null_p95`;
- no early stopping;
- scale-specific failure scope;
- separate rare-program matched-control increment;
- `NOT_ESTIMABLE` never becomes biological FAIL;
- no direct C2/C4/dataset elimination;
- no target, TD60, Stage4 or training authority.

## Hard terminal

`TD_RELATIONAL_SUCCESSOR_COMPLETE_ESTIMAND_MOVED_INTO_TD__EXTERNAL_PACKAGE_OBSERVATIONS_ONLY__TEST_OF_TEST_REQUIRED__REAL_EXECUTION_OFF__NO_TARGET_AUTHORITY__TRAINING_OFF`
