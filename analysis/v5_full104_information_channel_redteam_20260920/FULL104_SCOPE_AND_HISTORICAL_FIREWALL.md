# FULL104 scope and historical-artifact firewall

Date: 2026-09-20
Status: **controlling discipline for this red-team lane; no scientific authority changed**

This file exists to prevent accidental promotion of smaller runs, historical
artifacts, fixtures, placeholders, convenience subsets, or stale handoff values
into claims about the current FULL104 substrate.

## Scope classes

| class | meaning | may set current FULL104 numeric authority? |
|---|---|---|
| `CURRENT_FULL104_AUTHORITY` | hash-bound current authority artifact explicitly frozen for its role | **yes, only for that bound role** |
| `CURRENT_FULL104_RECONNAISSANCE` | measured on all authenticated FULL104 rows/addresses but not frozen authority | no |
| `REDUCED_POOL_DIAGNOSTIC` | current FULL104 rows but restricted candidate/target universe or other reduced mechanism mirror | no |
| `FIXTURE_ONLY` | synthetic/calibration construction with known answer | no |
| `HISTORICAL_SUPPORTING_ONLY` | older model/run/subset used to motivate or red-team current design | no |
| `WITHDRAWN` | superseded, invalidated, or based on a wrong reference | no |

## Non-promotion rules

1. A value from a smaller address pool, capped cell subset, historical checkpoint,
   old target semantics, or synthetic fixture **must not be described as the
   corresponding FULL104 production value**.
2. Historical findings may motivate a test, negative control, or failure mode,
   but may not set a current threshold, equivalence margin, rank, policy, target
   universe, or repair choice.
3. A current FULL104 mechanism measurement does not automatically become a
   terminal outcome. Terminal masking, D_shared, pathology, DEV/SEALED outcomes,
   and training remain separately sealed.
4. A report must distinguish:
   - the substrate actually traversed;
   - the candidate/target universe actually searched;
   - the donor/fold weighting actually used;
   - whether the quantity matches the production estimand.
5. Any cached/heavy artifact reused after code semantics change requires either:
   - byte-identical producer semantics proven by an explicit equivalence check; or
   - a new heavy run.
6. Stale handoff SHAs and manifest row counts are historical metadata. The live
   branch and current files must always be re-fetched before action.
7. `NOT_MEASURABLE`, `OPEN`, and undefined scientific quantities must never be
   coerced to zero merely to satisfy a finite evidence schema.

## Current lane classification

- Audit A physical denominator mass accounting:
  `CURRENT_FULL104_RECONNAISSANCE`.
- Audit B per-address burden distribution:
  `CURRENT_FULL104_RECONNAISSANCE`.
- Audit B 512-address selected-vs-baseline ratios and implied rung deltas:
  `REDUCED_POOL_DIAGNOSTIC`; actual fold-specific production policy burden remains
  `OPEN`.
- Audit C donor/source support and all-zero counts:
  `CURRENT_FULL104_RECONNAISSANCE`; fold-aware C2 must be bound to the authenticated
  FULL104 split before it can characterize terminal evidence geometry.
- Audit D magnitude fixtures:
  `FIXTURE_ONLY`; the algebraic invariance/property findings may be general, but
  fixture magnitudes do not transfer.
- Audit E 512-address decomposition:
  `REDUCED_POOL_DIAGNOSTIC`, with pooled E1/E2 versus source-balanced E3 currently
  not production-estimand matched.
- Audit F scalar zero-stratified fixtures:
  `HISTORICAL_SUPPORTING_ONLY` / mechanism fixture for the old scalar seam, not
  the current V5 query-local latent target semantics.
- Audit G earlier population-marginal cache defects:
  `WITHDRAWN`.
- Historical T1/u0/50K results:
  `HISTORICAL_SUPPORTING_ONLY`.

## Historical perspective rule

Historical evidence is retained because repeated shortcut mechanisms matter.
It should answer **"what failure should we make impossible or test for?"**, not
**"what is the current FULL104 value?"**.

That distinction is mandatory for all future handoffs and reviews.

```
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED / PATHOLOGY / DEV / SEALED = SEALED
TRAINING_OFF
```
