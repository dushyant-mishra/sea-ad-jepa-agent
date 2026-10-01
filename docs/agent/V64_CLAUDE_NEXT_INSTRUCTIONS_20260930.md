# Claude instructions — V64 Phase-B substrate audit repairs

**Date:** 2026-09-30

Continue from:

`claude/v64-exact-sampler-successor-20260930`

Audited head:

`7b51aac902b5dd4bb6ec697bb7e144a9a595224c`

Do NOT execute Phase B yet.

## What is accepted

- Exact sampler: QUALIFIED.
- S50: CLOSED for current production chain.
- Phase-A V3 code/receipt now carries the complete linked-side funnel and V2 structural schema.
- Phase-A V3 retained population used by the substrate: 13,175.
- The measurement-substrate architecture is directionally sound:
  - persist metacell assignment;
  - persist one-modality RNA/ATAC metacell vectors;
  - persist depth;
  - never compute a two-modality statistic in Phase B;
  - gene-key T3 under the frozen linked-gene RNA definition;
  - recoverability split remains scoped only to recoverability selection;
  - protected demographic values remain unread.

## Blocking finding S57 — residual hardcoded denominator

In:

`scripts/v64/build_phase_b_measurement_substrate_contract_v1.py`

this line still uses:

`round(len(extra) / 24187, 6)`

where 24,187 is today's CONTROL_A + available CONTROL_B row count:

`13,175 + 11,012`

It is correct now but stale by construction.

Fix it by recomputing the denominator from the loaded Phase-A V3 artifact.

Add a negative-control test that changes control availability and proves the emitted fraction changes accordingly.

Search again for other live population/count literals before closeout.

## Blocking finding S58 — R3 is a statistical decision

The substrate contract states:

`changes_no_statistical_decision = true`

but it introduces:

- R1 exact A-side enumeration;
- R2 exact joint A/B when both arms are <=10;
- R3 exact conditional when one arm is <=10 and the other is large.

R3 in particular is a new inferential rule:

> enumerate the small arm completely while holding the large arm at its realised draw.

The bound V2 null/statistical contract does not freeze that rule.

T13 proves the 57-row arithmetic under R3. It does NOT prove that R3 is upstream statistical authority.

### Required repair

Create an explicit prospectively frozen successor/amendment to:

`V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V2.json`

that defines R1/R2/R3.

For R3 state explicitly:

- eligibility;
- which arm is conditioned on;
- the conditioning value is the already-realised large-arm draw;
- what reference distribution/statistic it governs;
- why this is a conditional estimand rather than an approximation to the full joint;
- how it is reported separately from full-joint cases;
- no outcome value informed the choice.

Update:

- decision-state artifact;
- null/statistical tests;
- substrate authority digest.

Add a cross-contract test:

> every enumeration/reference rule emitted by the substrate must exist identically in the bound statistical contract.

Only after that may the substrate truthfully state that it changes no statistical decision.

Do not tune R3 after matrix values are opened.

## Finding S59 — Phase-A V3 byte custody

The substrate depends on:

- `PHASE_A_V3_ROWS.jsonl.gz`
  - 1,866,271 bytes
  - sha256 `ab103675e715fec32cee27b2d402ef1b45d63332b190bb4a6878e946059a24d4`
- `PHASE_A_V3_FUNNEL_PER_EDGE.jsonl.gz`
  - 63,355 bytes
  - sha256 `b4c6eb6fc9568b036d0b9217c102ab68a07d4b492db8625674a9e2a4db18a056`

They are currently hash-bound but not in Git.

They are small enough that future independent audit should not depend on a local D: drive.

Put the exact bytes in durable Git/release/Actions custody, or add a deterministic rematerialization/export workflow that verifies these hashes.

Do not change the bytes while doing this.

## Additional implementation assertion

The frozen measurement universes are:

- RNA: 38,606 genes
- ATAC: 521,217 peaks

These are inherited from the correspondence-design contract. In the eventual Phase-B executor, assert the authenticated matrix dimensions equal these frozen values before normalisation.

## Preserve these decisions

Do not change:

- Phase-A population 13,175 without a real Phase-A defect;
- primary CONTROL_A semantics;
- non-rescue;
- singleton/small-support strata;
- donor as sole independent/resampling unit;
- gene-balanced primary weighting;
- metacell algorithm/seed;
- bootstrap seed 20260929 / 4,000 replicates;
- 100 microglia / 4 metacells / 30 donors thresholds;
- recoverability 16/4/4 scope;
- missing != zero;
- protected obs-column firewall.

## Governance

Phase B = STOPPED.  
Stage 4 = NOT AUTHORIZED.  
TD60 = BLOCKED.  
Morabito = PROTECTED.  
TRAINING = OFF.  
No correspondence outcome opened.

After repairs, STOP again for audit. Do not execute Phase B.
