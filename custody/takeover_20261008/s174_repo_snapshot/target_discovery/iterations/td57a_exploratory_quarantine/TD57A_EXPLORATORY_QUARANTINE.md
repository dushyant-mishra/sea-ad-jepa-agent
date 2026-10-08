# TD57A exploratory local artifacts — quarantine / non-authority record

Status: `EXPLORATORY_OUTCOME_SEEN_BEFORE_FREEZE__NOT_DECISION_BEARING`
Date: 2026-09-08

## Why this exists

A local workspace audit after the TD57 design correction found pre-existing exploratory TD57/TD57A scripts and result files created after TD56 but **without a prospective GitHub freeze that predates their outcomes**.

They may inform implementation/debugging, but they cannot qualify donor recurrence, scale invariance, a relational target, or training authority.

## Local artifacts observed

Scripts:
- `/mnt/data/run_td57_source.py` — SHA-256 `67c8fce216503ff5a21c36d77752cc946d5c4c07f9ac5e3e7685ef55b4536199`
- `/mnt/data/run_td57a_source.py` — `cca6894b4635a8305eb461233218eb1cf59c8387f33710acb3696b02f1b22730`
- `/mnt/data/run_td57a_nullspecific.py` — `c3989fd0e5524b51610a05480210ca96518d73480cb4a2138340e77eb93b3ef8`
- `/mnt/data/run_td57a_nullspecific_last.py` — `19992c35da513a3ef31b771d95ad91b5c909e83dbedefe61e781a2d6c6fcaa0b`

Observed result artifacts included HVS, NPH52 and SEA_AD triplet-order recurrence screens.

## Exploratory finding only

The exploratory runs suggested that the **ordering of TD56 concordance distances within anchored cell triplets** may recur across donor halves and sources beyond matched wrong-cell nulls.

That observation is not authority because the outcome was visible before any binding prospective contract.

## Important implementation issue found

The first exploratory null reused the observed triplet set after requiring the observed Y relation to be measurable/non-tied. That conditions the null on observed-Y measurability and can make observed/null support asymmetric.

The later exploratory implementation improved this by:
- defining the base triplet set using X measurability/non-tie only;
- recomputing Y measurability/non-tie separately inside each null permutation.

Any prospective successor must use the corrected null-specific support semantics.

## Prospective successor rule

No future decision may cite TD57A exploratory PASS/FAIL values.

A decision-bearing successor must:
- use previously unused gene views;
- have exact pair/triplet/hash/null semantics frozen before execution;
- use null-specific Y measurability;
- bind source scripts/results by digest;
- stop sequentially on failure.

Terminal:

`TD57A_EXPLORATORY_QUARANTINED__NEW_INDEPENDENT_FREEZE_REQUIRED`
