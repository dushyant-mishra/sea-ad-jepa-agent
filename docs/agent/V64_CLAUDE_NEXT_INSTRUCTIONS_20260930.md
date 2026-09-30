# Claude instructions — V64 corrected Phase-A successor

**Date:** 2026-09-30

Continue from:

`claude/v64-exact-sampler-successor-20260930`

Last independently audited head:

`0d3874cb198f0fdeddff5a41777e3e0e9d0db5ab`

## 1. Important correction

The exact sampler is qualified.

S50 is closed for the current production chain.

The value:

`13,510`

is accepted as:

`FULL_E2_EXACT_CONTROL_A_AVAILABILITY`

It is **not yet accepted as the complete frozen Phase-A retained population**.

The prior wording "Phase A accepted at 13,510" is retracted.

## 2. Why full Phase A is still incomplete

The frozen contract:

`results/v64/V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.json`

requires the primary funnel to include:

1. `DROP_GENE_NOT_IN_NIHCARD`
2. `DROP_GENE_AMBIGUOUS_IN_NIHCARD`
3. `DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL`
4. then `DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START`

The live executor at `0d3874cb` loads all 20,709 E2 edges and determines primary retention only from CONTROL_A success.

Therefore your next task is **not** another sampler repair.

It is to lawfully compose:

`frozen linked-side structural eligibility + already-qualified exact CONTROL_A/B machinery`

without restoring any superseded control logic.

## 3. Preserve exact-control machinery unchanged unless a real defect is found

Do not change:

- exact admissible-set construction;
- side-before-admissibility semantics;
- no opposite-side retry;
- CONTROL_B never rescues A;
- independent deterministic A/B sub-seeds;
- coincidence retained without redraw;
- exact uniform sampling over A_exact;
- S50 cross-chain ambiguity guard.

The exact sampler already passed:
- 64/64 real-edge exact-set equality;
- 42 non-empty comparisons;
- zero algebra-only/oracle-only differences;
- deterministic rerun equality;
- positive-control sensitivity;
- uniformity;
- frozen fixtures;
- failure paths;
- orientation checks.

Do not retune it to recover a desired Phase-A retention count.

## 4. Build a true Phase-A structural successor

Starting from the same frozen 20,709 E2 rows, execute the linked-side stages prospectively:

### Linked-side eligibility

For every E2 edge, determine:

- whether its gene is present in NIH-CARD;
- whether gene mapping is unambiguous;
- whether the linked distal interval overlaps at least one NIH-CARD consensus peak.

Record the exact frozen drop reason when a stage fails.

Only linked-side-eligible edges proceed to primary exact-control retention.

### Exact-control stage

For linked-side-eligible edges:

- use the already-qualified CONTROL_A/B machinery;
- CONTROL_A determines primary retention;
- CONTROL_B never rescues;
- if A passes/B fails, primary retained, null unavailable;
- coincidence retained;
- no redraw.

Final funnel must reconcile exactly to 20,709.

Do not assume the final count will remain 13,510.

## 5. Produce the complete V2 feature artifact

The output must satisfy:

`results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json`

Required structural fields include at minimum:

- `promoter_key`
- `promoter_index`
- `pair_key`
- `population`
- `control_role`
- `source_hg19_distance_bp`
- `log_distance`
- `promoter_degree`
- `re_density`
- `anchor_frequency`
- `distal_chrom`
- `distal_start_hg38`
- `distal_end_hg38`

Valid population/control-role combinations:

- LINKED + NONE
- CONTROL + A
- CONTROL + B

CONTROL_A and CONTROL_B must use separate pair keys.

Linked/control rows for the same edge must retain the same promoter identity.

## 6. Anchor-frequency definition

Do not reuse the superseded exact-start multiplicity.

Frozen definition:

> number of DISTINCT E2 promoter_keys with at least one E2 distal partner overlapping the interval by >=1 bp.

Compute identically for:

- LINKED
- CONTROL_A
- CONTROL_B

## 7. Complete provenance binding

The receipt must bind:

- producer git blob;
- producer SHA-256;
- SHA-256 of every emitted artifact;
- authenticated NIH-CARD RNA/ATAC receipt;
- pairing closeout receipt;
- E2 edge-table digest;
- Phase-A V2 contract digest;
- liftOver binary digest;
- hg19→hg38 chain digest;
- hg38→hg19 chain digest;
- Nott PU.1 hg38 track digest;
- NIH-CARD peak-source identity;
- row counts by population/control_role;
- promoter count;
- primary funnel;
- null-arm availability counts.

Write the producer receipt after the artifacts exist.

## 8. Singleton/small-support strata remain frozen

Preserve:

- `RANDOMIZED_SUPPORT_GT10`
- `SMALL_RANDOMIZED_SUPPORT_2_TO_10`
- `FORCED_SINGLETON_SUPPORT_1`

The current exact-control run found:

- 344 CONTROL_A-success edges with admissible-set size 1;
- 377 with size <=10;
- 167 structurally degenerate A/B nulls.

These are support properties, not sampler defects.

Carry the needed structural cardinality/side fields into the successor artifact.

Do not drop/reweight them based on matrix outcomes.

## 9. Phase B remains stopped

Do not open:

- promoter activity matrix values;
- distal accessibility values;
- RNA↔ATAC correspondence;
- Stage 4;
- Morabito;
- TD60;
- training.

The corrected Phase-A successor remains structural/outcome-blind.

## 10. Parallelization

Parallelize only independent deterministic work where safe:

- linked eligibility checks;
- structural feature derivations;
- provenance/hash calculations;
- artifact validation.

Use deterministic shard membership and exact reconciliation.

Do not parallelize scientific gate decisions.

## 11. Required report back

Return:

- branch/head;
- changed files;
- confirmation exact sampler bytes/semantics were not changed, or exact reason if they were;
- full 20,709-edge linked-side funnel;
- final CONTROL_A-retained count after linked eligibility;
- CONTROL_B availability/non-rescue counts;
- singleton/small-support counts after final funnel;
- row counts by population/control_role;
- promoter count;
- feature-schema validation;
- all provenance digests;
- artifact hashes;
- exact funnel reconciliation;
- explicit confirmation:
  - Phase B STOPPED
  - Stage 4 NOT AUTHORIZED
  - TD60 BLOCKED
  - Morabito PROTECTED
  - TRAINING OFF
  - no correspondence outcome opened.

Then STOP for independent audit.

Do not proceed further.
