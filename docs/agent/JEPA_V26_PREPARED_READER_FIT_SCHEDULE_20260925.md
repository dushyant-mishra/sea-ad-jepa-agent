# V26 prepared reader-fit schedule: one authenticated snapshot, no per-update rehash

Date: 2026-09-25. **Independent CPU-only successor stacked on PR #135; no real frozen pass1 mounted here. Training remains OFF.**

## Why this is an independent missing connection

The original PR #135 API is a strict single-update, nontraining proposal. Its physical wrapper rehashes and loads the archived 410,278,055-byte August 24 ZIP, reopens the frozen pass1 and sorts all 4,553,407 donor codes *for every update*. Running it repeatedly inside a bounded training trajectory would cause repetitive high-disk-traffic file reads and O(N log N) full-population sorting, contending with the GPU operator and Claude's independent FULL104 scans. This successor prepares one immutable donor index from authenticated inputs and reuses it for every prospectively declared update, without touching the original PR135 implementation or its 79 existing tests.

New independent file: `src/sea_ad_jepa/v5/prepared_reader_fit_development_schedule_v1.py`. New adversarial fixtures, dedicated strict CI and this document are the only additional PR files.

## Identity and exactly equivalent scientific proposal

The physical factory `prepare_from_frozen_pass1(pass1_path=..., calibration_zip=...)` first executes PR #132's exact pass1/reader-fit count bridge; it then independently rehashes and rereads the actual frozen pass1 through a *single open descriptor*, and reloads the authentic Aug24 frozen reader-fit metadata. The strict frozen roots are:

- Pass1 SHA-256 `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`.
- Archived calibration ZIP SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- Reader-fit: precisely 104 donors and 4,553,407 cells; 22 reader-validation and 23 reader-oracle donors are never included. The physically inspected Aug24 roster's smallest reader-fit donor contains 81 cells.

After successful input qualification, code creates immutable-byte-backed NumPy snapshots of donor codes, per-donor counts, sorted original selection rows and donor offsets. Unlike merely clearing the writable flag on an owning array, these arrays cannot be made writable again by calling `setflags(write=True)`. The source files may change *after* snapshot and this CPU component will not notice; the eventual real V5 execution adapter must independently revalidate its immutable asset closure at a prospectively frozen checkpoint/run boundary and guard source substitutions before optimizer updates.

For each explicit `run_seed`, `update_index`, `presentations`:
- Reuses the **exact PR135 policy, schema, canonical RNG seed digest, NumPy PCG64 generator and draw sequence**, yielding bit-identical `selection_rows`, `donor_codes`, `q_i`, unit `p_i/q_i` weights and per-update receipt relative to PR135 at the same NumPy ABI.
- Draws donor slots uniformly *with replacement*, then distinct cells without replacement within each donor in that update. It is **not IID cell sampling**; each presentation has marginal scientific/proposal mass `q_i=p_i=1/(104*n_d)`, and q is unaffected by selection-packing geometry.
- Rejects `presentations > min_d(n_d)` **before using the RNG**, rather than retrying rejected donor-capacity combinations and silently biasing q. The real frozen roster therefore permits at most 81 presentations per update for this particular proposal, but no concrete update size is chosen here.
- Uses unique `selection_row` identities within every update to match current V5's existing stable-cell-key uniqueness requirement. Existing V4 geometry, reduced 94-donor historical arrays and defaults are not accepted.

`plan(run_seed,first_update_index,update_count,presentations_per_update,maximum_authorized_presentations)` requires every argument explicitly, stops before allocation if the planned total presentations exceeds the caller's **separately authorized** cap, and rejects overflowing 64-bit cursors. It materializes a finite tuple; a future full production trainer may use a bounded streaming iterator and atomic cursor receipts instead, but no implicit trajectory policy is invented here. `plan()` is a **nontraining planning API**, not an optimizer-bound scheduler; no check is claimed for accepted optimizer step, gradient/moment/EMA or atomic model checkpoint.

## Independent red team and no historical spillover

The new suite compares the optimized prepared sampler against original PR135's *unmodified independent reference implementation* at update cursors 0,1,7,99, and independently tests contiguous schedule parity. It injects forbidden post-prepare full-sample sorting, mutable input swaps, writable cached arrays, capacity failure before RNG draw, over-budget trajectory requests, signed-cursor overflow, noncanonical source SHA, wrong donor totals and substitute/missing physical files. The complete strict CI also reruns PR135's 79 tests, including the earlier frozen metadata/pass1 count adversaries.

**Honesty boundaries:** The authentic frozen pass1 itself is NOT mounted in this ChatGPT environment. Passing CI validates only synthetic mechanics and PR135 parity; it is NOT proof of physically reconstructed per-cell lineage, V0/V1 row order, N1, any target/masking qualification, source/operator stratification, or real trained JEPA performance. The actual physical factory and downstream current-V5 adapter remain unexecuted here. PR #136/#138 own the new 104-donor linear baseline and its independent red-team, PR #133 owns historical 94-donor missing-file recovery, PR #134 owns dirty-origin CRISPRbrain replay, and Claude's GPU branch owns the real guarded V5 diagnostic. This successor does not modify any of those branches or require another 8,915-block scan.

## How a GPU-laptop operator can independently inspect the CPU-only result

Use this PR's exact live SHA, a distinct clean worktree and real SHA-authenticated source paths. In an explicitly nontraining REPL with `PYTHONPATH=src`:

```python
from sea_ad_jepa.v5.prepared_reader_fit_development_schedule_v1 import prepare_from_frozen_pass1

prepared = prepare_from_frozen_pass1(
    pass1_path=r"<EXACT_AUTHENTIC_FROZEN_PASS1_NPZ>",
    calibration_zip=r"<EXACT_AUTHENTIC_AUG24_ZIP>",
)
print(prepared.nontraining_report())
# Only after a separately frozen development contract supplies these values:
schedule = prepared.plan(
    run_seed=<FROZEN_NONNEGATIVE_RUN_SEED>,
    first_update_index=<FROZEN_NONNEGATIVE_CURSOR>,
    update_count=<FROZEN_UPDATE_COUNT>,
    presentations_per_update=<FROZEN_SIZE_AT_MOST_81>,
    maximum_authorized_presentations=<FROZEN_TOTAL_PRESENTATION_BUDGET>,
)
```

The numeric placeholders above are deliberately not executable; do not replace them with convenient inherited V4 defaults. Keep model training/protected outcomes closed until a separate current V5 execution authority is explicitly satisfied.
