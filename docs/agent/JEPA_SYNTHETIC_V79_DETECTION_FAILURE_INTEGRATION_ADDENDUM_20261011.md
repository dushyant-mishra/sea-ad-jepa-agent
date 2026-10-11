# V79 factorial integration addendum — terminal detection-family failure

Date: 2026-10-11

Scope: synthetic/factorial lane only. Target discovery is separate.

## New upstream fact

Macha's Bayesian geometry source branch reached code snapshot `d9d8cac6fa65463529374c50a9c309e7eb7e5405` after adding per-attempt divergence-location assertions.

Under the prospectively frozen recovery rules, detection/Bernoulli V2 failed S4. After the allowed retry and one same-chain extension, the limiting effective sample size was `362`, below the frozen minimum `400`. V2 was the final precommitted detection parameterization.

Therefore:

`DETECTION_FAMILY_NOT_QUALIFIED__NO_V3__NO_THRESHOLD_CHANGE__NO_POST_FAILURE_TUNING`

S0/S1 completion remains useful preserved evidence but cannot reverse the family-level S4 failure.

## Factorial consequence

The factorial lane must not consume any Macha Bernoulli/detection posterior, point estimate, fitted detection effect, or derived detection parameter as qualified observation authority.

Other Macha families (Gaussian, log-normal, ZTNB) remain independently eligible to continue their preregistered recovery qualification. Their success or failure must be adjudicated separately.

If those remaining families qualify, a future successor H1/H2 package may consume only the geometry each family lawfully identifies. The failed detection family must remain explicitly marked `UNQUALIFIED`, not imputed from a provisional fit and not replaced by a newly tuned V3.

If a proposed successor H2/H3 architecture requires a qualified detection mechanism specifically, then Macha cannot currently supply a complete successor observation authority. The lawful prospective choices before any H0-H3 outcome are:

1. retain the already frozen pre-Macha synthetic observation authority unchanged; or
2. construct a successor authority using only independently qualified components and explicitly omit/neutralize the unqualified detection component, followed by a fresh scientific review and byte-authenticated preexecution gate.

No choice may be made after observing factorial outcomes.

## Current factorial state

The factorial implementation itself remains internally engineering-closed and unexecuted. The detection failure changes only what upstream Bayesian information may be imported.

Current terminal:

`FACTORIAL_INTERNAL_ENGINEERING_CLOSED__MACHA_DETECTION_NOT_QUALIFIED__OTHER_MACHA_FAMILIES_PENDING__FINAL_H1_H2_AUTHORITY_DECISION_PENDING__FINAL_BYTE_CUSTODY_REPLAY_PENDING__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`

Hard false gates remain:
- `training_authorized=false`;
- no H0/H1/H2/H3/C_OBS/C_BIO scientific outcome read;
- no V78 retuning;
- no TEST/Morabito/pathology;
- no target-discovery evidence in synthetic truth;
- no post-outcome rescue.
