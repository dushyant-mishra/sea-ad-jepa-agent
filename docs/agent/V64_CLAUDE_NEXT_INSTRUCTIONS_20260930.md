# Claude instructions — V64 final substrate executability repair

**Date:** 2026-09-30

Continue from:

`claude/v64-exact-sampler-successor-20260930`

Audited head:

`a0500111254315504de3618ea832931ea54cdc26`

Do NOT execute Phase B yet.

## Accepted closures

S57 CLOSED:
- denominator 24,187 is no longer hardcoded;
- it is recomputed from loaded Phase-A V3 control rows;
- T18 rejects a stale denominator.

S58 CLOSED:
- R1/R2/R3 now live in statistical contract V3;
- V3 explicitly declares that it makes this statistical decision;
- substrate is rebound to the V3 digest.

S59 CLOSED:
- both Phase-A V3 gzip artifacts are now committed as Git bytes at the expected sizes;
- retain their receipt-bound SHA-256s unchanged.

## Remaining blocker S60 — persist the R3 conditioning identity

Statistical V3 requires R3 to mean:

`EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM`

and explicitly states that the realised large-arm draw is recorded per pair alongside the reference.

The current substrate contract says this in prose but T6 does not freeze the conditioning identity as persisted data.

That is an executability gap.

Stage 4 must never have to reconstruct after outcomes are visible:
- which arm was small;
- which arm was large;
- which realised large-arm draw was conditioned on;
- whether the quantity must carry the conditional label.

### Required repair

Add a persisted R3 reference/conditioning structure to the substrate contract and eventual substrate artifact.

For every one of the 21 R3 pairs, persist at minimum:

- `edge_index`
- `reference_rule_id = R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM`
- `small_arm_role` (A or B)
- `small_arm_drawn_side`
- `large_arm_role`
- `realised_large_arm_drawn_side`
- `realised_large_arm_hg19_start`
- `realised_large_arm_hg19_end`
- `required_label = CONDITIONAL_ON_REALISED_LARGE_ARM`

Also bind each ENUMERATION_ONLY small-arm row to its R3 conditioning record, e.g. by `reference_id`.

If R1/R3 overlap on an A-small pair, preserve both rule memberships rather than duplicating biological measurement.

### Required test

Add a real adversarial test that independently recomputes R3 membership from the committed Phase-A V3 rows and exact admissible sets and verifies:

- 21 R3 pairs;
- A small = 11;
- B small = 10;
- same drawn side = 0;
- different drawn side = 21;
- every conditioning record's realised large-arm start/side equals the actual frozen Phase-A draw;
- every R3 reference carries `CONDITIONAL_ON_REALISED_LARGE_ARM`;
- every R3 ENUMERATION_ONLY row points to the correct conditioning record.

Plant failures for:
- wrong large-arm start;
- wrong large-arm role;
- missing conditional label;
- invented/unbound reference_id.

Each must be rejected.

## Strengthen T17

Keep the identifier/authority check, but add semantic enforcement:
- substrate R1/R2/R3 eligibility/reference definition must be derived from or compared against V3;
- an existing rule identifier with altered semantics must fail.

The current T17 blocks a new downstream rule identifier, but does not by itself catch semantic drift under an existing identifier.

## Preserve everything else

Do not change:
- Phase-A V3 population 13,175;
- randomness strata;
- R1/R2/R3 definitions;
- donor/metacell thresholds;
- bootstrap seed/replicates;
- gene-balanced primary weighting;
- recoverability split scope;
- protected-column firewall;
- missingness rules;
- Phase-B single-modality boundary.

## Governance

Phase B = STOPPED.  
Stage 4 = NOT AUTHORIZED.  
TD60 = BLOCKED.  
Morabito = PROTECTED.  
TRAINING = OFF.  
Correspondence remains unopened.

After S60 is closed, STOP again for audit. Do not execute Phase B.
