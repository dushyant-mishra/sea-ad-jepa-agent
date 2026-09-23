# Independent review of PR #69 / PR #70 — 2026-09-23

**Scope:** static independent code-and-receipt review of the exact live PR #69 head `83b85382f22a7672a5beb1ef9154e5b8bf36e16f` (one commit over #67 `c4a893cbc98bfa736f3d44a2fe9a9ebe31dec6fa`), PR #70 `f1cc749843e6a9329e646da3b3efc8d3d775dabe` (separate from #66 `f13c8364fe997d800cb84ad5370da43e75e17d3e`). The >30 GB FULL104 store, original 242 MB NPZ and 363 MB corrected derivative are *not* available in this review environment. Real physical outcomes are assertions backed by GitHub receipts and Claude's Windows report, not independently re-executed here. Neither PR is execution authority.

## Confirmed strengths (no reopening historical findings)

- Original metadata-only #67 diagnostic quarantined the original: 8,915 authenticated metadata blocks and 4,553,407 exactly-once selection rows; NPH52+SEA_AD mismatch 4,354,689; the parent is immutable.
- Derivative manifest reports 35 enumerated NPZ arrays, precisely 2 intended value changes (`source_names`, `src_of_cell`), 33 *value-identical* others; original producer's accumulators do not read the defective source-code arrays. This is not a claim of byte-identical NPZ members: original container is compressed, new one uncompressed.
- PR #69 has four successful hosted workflows; PR #70 documents two native Windows synthetic passes, including the previously failing fsync case. PR #70 has no new Actions run because its change is documentary.
- #63 crash-safe and #66 rare-tail lineages are not silently inherited by #69.

## F1 — HIGH, OPEN: successor accepts self-attested whole-NPZ audit without independent per-member comparison

`qualify_canonical_derivative_successor_v1_20260923.py` verifies the JSON manifest's **self-digest**, the derivative **file** SHA against a SHA supplied by that same manifest, and the two named `changed` entries. It does not recompute all 35 `old_value_sha256` / `new_value_sha256` entries from reloaded parent and derivative or verify the claimed dtype/shape/disposition of every member. This is especially important before the first new physical N1 preflight receipt is promoted. A coordinated altered derivative + rewritten manifest with correctly recomputed self-digest can satisfy these checks if it preserves the few independently inspected arrays. The reviewed original PR #69 receipt SHA should be a separately pinned *expected* input, not an expected value sourced exclusively from the untrusted candidate manifest.

**Repair:** before emitting PASS, independently reload and enumerate both physical NPZ member sets; demand the frozen exact set of 35, dtype/shape agreement, canonical value SHA equality on 33 unchanged members and exact verified canonical values of both changed members; compare every result to the reviewed per-array manifest. Pin expected derivative SHA `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b` and manifest canonical SHA `4f55158c59d2ee6cdb3ad9276e887126ae78b5b9305021c8c607b524c61293a5` for the *current* artifact review, with an explicit versioned rebinding protocol for any new compression container. Negative test: alter an unused numeric member, reseal the candidate manifest and repackage the NPZ; must reject before PASS.

## F2 — HIGH, OPEN: complete cell-to-donor provenance is sampled, not proven in the derivative producer

The producer derives all source codes from SHA-checked metadata, then validates `new_src == donor_src[cell_donor]` for all cells, but checks metadata donor identity against the supplied, **un-hashed pass1** `cell_donor` only for `np.arange(0, EXPECTED_CELLS, 4001)`. Within-source donor permutations outside that sample can preserve the source invariant, donor/source census, `duniq`, strict-core order and all sampled checks while misassigning cell-to-donor identities. The successor qualification also reads `pass1` without a frozen file SHA or full donor-identity comparison to the authenticated metadata.

**Repair:** compare authenticated metadata donor index against *every* `pass1.cell_donor[selection_row]`; verify pass1's physically recomputed SHA against its frozen receipt/manifest where available. Require exact int64/range checks before indexing. A single changed unsampled cell within the same source must fail; histogram-preserving same-source donor swap must fail. Do not substitute the old six-donor raw reaggregation for full 104-donor identity closure.

## F3 — HIGH, OPEN: declared adversarial control count overstates exercised production gates

In `tests/test_v5_canonical_source_derivative_v1.py`, tests 1–6, 9, 10, 11 and 13 largely construct arrays or simulate checks and assert local inconsistency; they do *not* invoke the producer's actual physical checks or successor `main()` with malicious inputs. Test 2 has a vacuous `... or good[0] == 0` escape in its asserted expression. A green test suite is valid for its tested assertions, but the claim that all 14 real negative controls exercised the production gate is not established by those particular tests.

**Repair:** add adversarial end-to-end synthetic fixture tests that invoke the actual producer and successor checker, with frozen fixture manifest/source identities injected only into the test's temporary copy, not production authority; demonstrate exact fail-closed output/exit and absence of a committed derivative/receipt. Include coordinated donor+source swaps, a single same-source cell-donor swap, changed uninspected numerical member with resealed candidate manifest, and missing/duplicate receipt donor IDs. Report separately which controls were actually exercised on physical heavy inputs, synthetic end-to-end, or logical unit assertions.

## F4 — HIGH, OPEN: a failed postwrite check can leave an apparently finished derivative

The producer currently writes `np.savez(stage,...)` and immediately `stage.replace(args.out_derivative)` **before** the 35-member postwrite audit and unexpected-change checks. If a postwrite check fails, the named derivative remains on disk without an authorized manifest. This need not grant scientific authority, but it creates an avoidable stale/partial artifact trap on the GPU disk.

**Repair:** run all prewrite classification checks, write the NPZ to an exclusive stage, reload and rehash *the stage*, then atomically publish the final derivative only after every negative gate passes; use atomic, exclusive manifest publication and explicit cleanup/quarantine on failure. Test forced postwrite mismatch; assert neither final derivative nor PASS receipt exists.

## F5 — MEDIUM/HIGH, OPEN: successor receipt writes conclusions instead of observing some checks

`qualify_canonical_derivative_successor_v1_20260923.py` writes `pr62_still_rejects_parent: true` and `all_physical_files_reloaded_and_hashed_here: true` without running PR #62's binder during that invocation; it does not hash the supplied pass1 file or compare it to frozen SHA. The split receipt's stored `receipt_sha256` is compared to the expected digest, but its canonical digest is not independently recomputed in this code. `fold_by_donor_sha256` is initialized with `... if False else None` and a true fold digest is only conditionally added when a matching split key happens to be present. The original six-donor receipt is hashed into the new record but this path does not first demand its frozen expected **file** SHA `bbd2b95b882f52c313a3623bab55e5d7ff6562cdba27e48f9c84009075cf713d`; it checks only count=6, not unique identity or exact set equality between `donors_checked` and `per_donor`. `numeric_rows_unchanged_from_parent` can be false and the code still constructs a qualified-looking successor receipt.

**Repair:** bind and recompute all required physical file and canonical digests, the authentic 4-fold donor vector and exact six-donor IDs/rows; convert required booleans into results of executed gates; fail before receipt write if any numeric row or old receipt total differs, if fold evidence absent, or if samples duplicate/mismatch. Preserve explicitly the original six-donor scope. Run the original binder regression as a separately documented test instead of recording an unconditional result.

## F6 — MEDIUM, OPEN: qualify downstream consumers independently of producer dependence

The original producer's numerical arrays are keyed by donor/depth/pool, which supports metadata-only *producer* repair. The review must separately inventory all **downstream** consumers of `source_names` and `src_of_cell` and verify that the old, quarantined source vectors or receipts cannot be reintroduced into N1 planners, weighting, summaries or post-qualification paths. In particular do not treat old six-donor source text labels or a historical artifact-wide `HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE` string as authority for the successor.

## Rare-tail PR #70 — bounded conclusion

The Windows fsync correction (`stage.open('rb+')`) is consistent with the reported native Windows synthetic pass and PR #66's Linux test. The documented gateway normalized-source SHA is `0f9689c513eb391c803f875fb9b7c804a8a14a3b0286a812de08d37478cd6cbd`. The older frozen molecular runner is still directly callable. Therefore **native portability testing can be marked reported complete**, but real RNA-opening execution remains barred until independent new-source approval and a reviewed non-bypass authority procedure; current PR #70 is documentation-only.

## Compression decision

**Retain the existing 363,053,057-byte uncompressed derivative** for review, provided independent all-member identity verification passes. Recompression now would change the file SHA and require reissuing every byte-bound receipt; it is not necessary to close the current source-identity question. Distinguish 33 value-identical arrays from physically byte-identical .npy/ZIP members.

## Focused downstream-consumer inventory (source-reviewed after F6)

At PR #69's frozen code lineage, direct inspection of the following relevant active paths shows:

| Consumer/producer | Source encoding dependency | Consequence |
| --- | --- | --- |
| `analysis/v5_full104_information_channel_redteam_20260920/scripts/build_core_sufficient_statistics_20260920.py` | Stores `source_names` and `src_of_cell` under first-appearance order; its accumulation uses `cell_donor`, library-depth/core-nnz deciles or address pool, not the misencoded vectors. | Original numeric sufficient statistics can be transported **only if independently per-array verified**. |
| `src/sea_ad_jepa/v5/audit_b_n1_physical_binding_v1.py` | Reads `donor_src`, `source_names` and numeric burden arrays, and compares donor-source codes with the frozen split. Does **not** load per-cell source. | Original defective names remain rejected by #62; successor must also check metadata-derived full cell alignment. |
| `src/sea_ad_jepa/v5/audit_b_n1_cpu_burden_assembly_v1.py` | Derives canonical source names via fixed `SOURCE_NAMES=("HVS","NPH52","SEA_AD")` from `donor_source_code`, and compares `stream.source_by_donor` directly. | No lookup through defective old NPZ `source_names` in this consumer; physical stream binding still mandatory. |
| `src/sea_ad_jepa/v5/audit_b_n1_crossfold_planner_v1.py` | Uses `stream.source_by_donor` to group source-specific donor statistics. | Its source accuracy depends on the authenticated stream donor-source mapping; counts/histograms alone cannot authenticate it. |
| `src/sea_ad_jepa/v5/audit_b_n1_result_contract_v1.py` | Records donor-level numeric `donor_source_code` and its hash. | New receipts must bind corrected derivative and fully authenticated donor source; old text-label receipts prohibited. |
| `audit_b_n1_cached_planner_v1.py`, `audit_b_n1_execution_authority_v1.py`, `audit_b_n1_runtime_rng_bridge_v1.py` and N1 authority/preflight CLI | No direct `src_of_cell`/`source_names` references in reviewed current files. | Not evidence that an unreviewed future physical adapter cannot reintroduce old labels. |

**Review limit:** this is a focused static inventory of the current N1 producer/binder/planner/result chain, not a proof that every historical or future repository script is source-independent. Before integrating #63, test the complete *new adapter's* stream→donor→source lineage and forbid loading the original quarantined file as an input or source-code authority.

## Required resolution / execution boundary

1. Correct F1–F5 using source-independent checker logic, real fail-closed adversarial tests and physically checked receipts. Confirm F6 via downstream consumer inventory.
2. Regenerate and independently review the affected successor receipts on the GPU machine. Do not overwrite the original or current receipts; version any successor.
3. Only then review a separate future synthetic-only #63 adapter. **Do not execute N1 or real rare-tail molecular code in this review.**

`AUDIT_B_N1=UNOPENED | MASKS=NONE | BURDEN=NOT_RUN | RARE_TAIL_MOLECULAR=UNOPENED | TD60=UNEXECUTED | PATHOLOGY_DEV_SEALED=UNOPENED | D_SHARED_G5=UNOPENED | TRAINING=OFF`
