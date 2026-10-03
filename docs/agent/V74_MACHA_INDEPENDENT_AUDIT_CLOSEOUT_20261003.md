# V74 Macha independent audit closeout — 2026-10-03

## Scope

This is an audit record, not a scientific-authority upgrade. It independently re-queried the live Macha branches after the V74 audit-takeover handoff and reconciled them against the supplied Lane-1/Lane-E execution transcript. No source, tests, thresholds, contracts, scientific results, protected outcomes, or training state are modified by this document.

## Exact live heads re-queried

- `claude/v74-routeb-custody-20261002` — `32dfcbfdcfced5683d9646e10a7db679ea9ba323`
- `claude/v74-blacklist-and-512pilot-20261002` — `60b0971086bc414dc14e65da59818316450a0a16`
- `claude/v74-g2-continuous-successor-20261002` — `03c0c48612860e4bd2f094ce54fdef9cde274490`
- `claude/v74-stale-claim-audit-20261002` — `14326480882f5bc4618634ba7f95c94f4924437d`
- `claude/v64-exact-sampler-successor-20260930` — `78f13e71db968ad42486fdecb718dacd48704a5a`

The Lane-E branch is still exactly at `60b09710...`. The supplied transcript continues into a local `QUIET512_t8` rerun after that commit, but no later Git commit exists on the branch. Therefore the quiet-512 run is **not repository evidence** and no final quiet-512 result is promoted by this audit.

## Finding M1 — Route-B fragment-byte custody repair is materially stronger than V69

The supplied Lane-1 transcript records that the V69 QC receipt had copied `fragments_sha256` from the acquisition receipt rather than independently computing it, so equality of those two fields was circular. Lane 1 replaced that with a streaming SHA-256 over the actual compressed fragment bytes, with no second pass/time-of-check gap, and reported agreement with `b7c5aa2d...` over 63,641,120,882 bytes.

The same lane re-counted fragments by cohort barcode and reported exact reconciliation for all 2,534 cells at 23,522,438 fragments. The live Route-B head records the corresponding replay verifier and custody changes.

**Verdict:** strong engineering/provenance repair within the stated Route-B scope. It does not by itself authorize consensus, SCENIC+, Stage 4, or biology.

## Finding M2 — two V69 checks were structurally incapable of protecting their claims

The supplied transcript records:

1. duplicate/conflicting barcode checking happened after `dict(zip(...))`, so conflicting duplicate keys could already have been silently collapsed;
2. empty consensus raised plain `ValueError`, bypassing the structured `FailClosed` receipt path.

For the real Route-B cohort the transcript reports 2,534 rows, 0 duplicates and 0 conflicts, so these are latent integrity defects rather than evidence that the existing pseudobulk result was wrong.

The Route-B lane reports 50 tests and 13 mutation arms proven capable of failing, including a same-length/different-byte gzip mutation that defeats a size-only check but is caught by SHA-256.

**Verdict:** repair is meaningful; historical V69 guard claims should not be cited as though they already provided byte authentication or pre-collapse duplicate protection.

## Finding M3 — Route-A still contains the same dict(zip(...)) defect and remains OPEN

At exact live Lane-E head `60b09710...`, `scripts/v69/build_routea_cistopic_object_v1.py` still executes:

```python
guard_evidence = assert_donor_map_is_not_suffix_derived(
    dict(zip(bc["barcode"].astype(str), bc["donor"].astype(str))))
```

The identical vulnerable file is also present at Route-B head `32dfcbfd...`.

A duplicate barcode mapped to conflicting donors can therefore be collapsed by Python dictionary construction before the guard receives the mapping. This is the same bug class Lane 1 removed from Route B.

**Required repair before Route-A closure:** validate uniqueness/conflicts on the raw barcode/donor rows before any dictionary construction, add explicit duplicate/conflict negative tests and a mutation proving the guard fails if moved after dictionary construction, and emit a structured fail-closed receipt.

**Verdict:** OPEN, P0 for Route-A integrity. No Route-A cisTopic object should be promoted as fully guarded until this is fixed on a reconciled successor.

## Finding M4 — blacklist-before-consensus semantics are correct

The live Route-B head records a hard blacklist-policy gate. The supplied audit correctly identifies that pycisTopic applies blacklist handling inside iterative consensus construction. Therefore a no-blacklist consensus followed by post-hoc blacklist filtering is not guaranteed to reproduce the universe that would have been obtained with blacklist active during consensus.

**Verdict:** the hard gate is the correct semantics. A no-blacklist object is not an acceptable temporary substitute for the decided blacklist-ON route.

## Finding M5 — cisTarget runtime projection was biased by motif ordering

The supplied Lane-E transcript records a controlled 128-vs-128 comparison using the same FASTA, `cbust`, 8 workers, ranking seed, thread pinning and quiet-machine condition. The alphabetical-prefix 128 motifs cost 11.56 s/motif while a frozen random-128 sample cost 18.45 s/motif. Mean PWM lengths were 9.19 vs 17.30 positions; the full collection mean is reported as 21.57 with a maximum of 1,480.

This establishes that the historical prefix benchmark sampled an unusually cheap corner of the collection. The old 33.5 h projection is therefore superseded. The transcript estimates ~52.5 h as a random-128-rate floor and ~62.9 h from a two-point PWM-length interpolation, with total build roughly 54–65 h after non-scoring overhead. The interpolation is not a measurement and must remain labelled as such.

**Verdict:** credible engineering correction. It changes runtime planning, not biological/scientific results.

## Finding M6 — the quiet-512 run is not closed in GitHub

The supplied transcript shows `QUIET512_t8` launched after thresholds were declared prospectively. It ends while the run is still active. The live branch has not advanced beyond the pre-result producer commit `60b09710...`.

Therefore none of the following may be treated as repository-qualified evidence yet:

- final quiet-512 wall time;
- final quiet-machine classification;
- contended-vs-quiet bitwise digest equality for the 512 workload;
- final shard-size decision branch based on that run;
- a generated successor scaling-authority receipt consuming the quiet-512 result.

The producer script is present, but a producer committed before a result is not the result.

**Verdict:** INCOMPLETE / LOCAL-ONLY until a hash-bound result/receipt is committed and audited.

## Finding M7 — the Macha lanes are parallel/diverged, not one cumulative scientific head

Direct GitHub comparisons show the Route-B and Lane-E branches diverged from common ancestor `d5b76230...`; neither contains the other's later work. The G2 and stale-claim branches likewise diverged from `498f56a3...`. The exact-sampler/ACTIVE_STATE branch is a separate lineage.

Consequently, statements such as “Macha V74 fixed Route B, blacklist/scaling, G2 and stale K-curve claims” are only true as a set of parallel lane results. They are not yet true of any single exact repository head.

**Verdict:** a deliberate reconciliation successor is required before claiming one current Macha implementation state.

## Finding M8 — S102 and Stage-4 status remain correctly blocked

The G2 continuous-successor head freezes a replacement contract as `NOT_IN_FORCE` with deciding absolute margins unset. It narrows S102 but explicitly leaves S102 OPEN.

The stale-claim audit identifies stale/retracted K-curve claims and reports no current executable gate consuming the invalid V1 conclusion, but also leaves its S112 issue open because a V2 artifact still juxtaposes a bare convergence flag with inherited monotonicity language.

The repaired/historical K curve therefore remains a historical measurement, not the final Stage-4 safeguard.

**Verdict:** S102 OPEN; Stage 4 NOT AUTHORIZED.

## Protected-data / scientific-boundary audit

No evidence found in the inspected Macha heads or supplied execution transcript that the following boundaries moved:

- Stage 4: NOT AUTHORIZED
- correspondence: UNOPENED
- training: OFF
- multimodal training: OFF
- Morabito: PROTECTED
- recoverability TEST: SEALED
- full SCENIC+ network: DOES NOT EXIST / NOT CLAIMED
- 100K synthetic qualification: NOT CLAIMED by the Macha lanes audited here

Infrastructure and provenance qualification must not be converted into a biological claim.

## Narrow final verdict

### Qualified/scoped

- Route-B byte-level fragment authentication and barcode-count replay are substantially repaired relative to V69.
- Route-B duplicate/conflict and structured-failure protections are materially improved, with mutation evidence reported.
- blacklist-before-consensus is the correct prospective semantics.
- the alphabetical-prefix cisTarget runtime projection is invalid as a representative whole-collection estimate; the 33.5 h estimate is superseded.
- stale K-curve claims were materially audited; no evidence was found that an executable threshold currently depends on the retracted V1 conclusion.

### Still open / blocking

1. **Route-A duplicate/conflict guard defect remains physically present at the live heads.**
2. **Quiet-512 result is not committed and cannot be promoted.**
3. **Macha lanes remain diverged and require explicit reconciliation.**
4. **S102 remains open; G2 successor is NOT_IN_FORCE.**
5. **Stale-claim audit S112 remains open.**
6. **No Stage-4 authorization, SCENIC+ biological network, or training authority exists.**

## Required next repository action

Create a new reconciliation successor from an explicitly chosen audited base. Bring in, with conflict review rather than blind merging:

1. Route-B custody/replay/blacklist-gate repairs from `32dfcbfd...`;
2. Lane-E blacklist/scaling work from `60b09710...` only for committed evidence;
3. Route-A pre-dict duplicate/conflict repair with dedicated tests/mutations;
4. G2 NOT_IN_FORCE successor semantics from `03c0c486...`;
5. stale-claim corrections from `14326480...` while preserving SHA-frozen historical artifacts;
6. ACTIVE_STATE/current-governance updates from `78f13e71...` where non-conflicting.

Then run an exact-head audit suite and emit one machine-readable reconciliation receipt that lists every source branch/SHA, conflict resolution, tests/mutations, protected-data state, and remaining open blockers.

Until that exists, **there is no single Macha head that may be called the fully reconciled current scientific implementation.**
