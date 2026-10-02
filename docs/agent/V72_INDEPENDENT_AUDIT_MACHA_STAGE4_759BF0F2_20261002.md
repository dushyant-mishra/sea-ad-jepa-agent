# V72 independent audit — Macha Stage-4 head 759bf0f2 — 2026-10-02

## Scope

Audited exact head:

`759bf0f276307ad296e9a8669f39adccc1a7f83a`

Primary files inspected:

- `results/v64/phase_b_design/V64_STAGE4_CALIBRATION_SWEEP_V2.json`
- `results/v64/phase_b_design/V64_STAGE4_G2_SENSITIVITY_PRECOMMIT_V1.json`
- `scripts/v64/stage4_executor_v1.py`
- `scripts/v64/run_stage4_g2_sensitivity_curve_v1.py`
- `scripts/v64/build_stage4_synthetic_worlds_v1.py`

This audit does not authorize real Stage 4.

## Verified findings

### A1 — V2 receipt arithmetic is internally consistent at the reported level — VERIFIED

The receipt contains 8 cells × 40 attempted draws = 320 attempted draws, with 40 successes and zero failures in every cell.

The reported headline rates match their counts:

- BIOLOGY_POSITIVE: 30/40 = 0.75 at 60; 25/40 = 0.625 at 282
- TRUE_NULL: 0/40 at 60; 2/40 = 0.05 at 282
- MEASURED_TECHNICAL: 0/40 at both donor counts
- HIDDEN_CONFOUND: 8/40 = 0.20 at 60; 4/40 = 0.10 at 282

The measured-technical G3 pass count is 0/40 in both cells and the receipt identifies `atac_depth_sensitivity` as the worst-SMD feature in all 80 draws. This supports retracting the V1 depth alarm **for this repaired synthetic world**.

### A2 — S102 is real — VERIFIED

The executor implements G2 as:

`quantile(bootstrap_cvc, .025) <= 0 <= quantile(bootstrap_cvc, .975)`

The executor now explicitly records that the contract itself never froze this test or level and reports `|cvc Delta| / |primary Delta|` descriptively without a threshold.

Therefore the V2 biology G2 pass-rate fall from 0.775 to 0.625 cannot safely be called a property of the frozen Stage-4 design. It is an operating characteristic of the current executor choice.

## New audit findings

### A3 — HIGH, BLOCKS THE K CURVE: K does not create K occupied confound blocks

The precommit states that the edges are “partitioned into K blocks” and that at K equal to the edge count every edge has its own independent factor.

The generator does not implement that.

It creates K factors and then assigns each edge using:

`block_of_edge = rng.integers(0, K, N_EDGES)`

This samples block labels **with replacement**.

Consequences:

- block sizes are random rather than a partition into prospectively intended near-equal blocks;
- some of the K factors can be unused;
- multiple edges can share a factor even when K equals the number of edges;
- at N_EDGES=K=200, the expected number of occupied factors is only about
  `200 * (1 - (199/200)^200) ≈ 126.6`, not 200;
- the K=200 endpoint is therefore **not** the promised one-factor-per-edge structural twin of BIOLOGY_POSITIVE.

The runner's guard does not catch this. It re-reads only `confound_blocks_K` from the manifest and checks it equals the requested K. That proves the requested integer was recorded, not that K blocks were occupied or that the intended block geometry was built.

The receipt field:

`edges_per_block = round(N_EDGES / K, 2)`

is nominal arithmetic, not a measurement of realised block occupancy.

#### Required repair before any K-curve draw

Build an actual partition. For example:

- create labels with each K block represented;
- allocate edges as evenly as possible;
- shuffle those labels with the seeded RNG;
- at K=N_EDGES require exactly `np.arange(N_EDGES)` up to a permutation.

The world manifest must record and the runner must verify:

- requested K;
- realised number of occupied factors;
- complete block-size vector or digest;
- min/max block size;
- at K=N_EDGES: every block size exactly 1.

The previous K=5 smoke test cannot be described as “40 edges per block” unless realised occupancy is explicitly checked. Under the current code it is only **nominally** 200/5=40.

Status: **OPEN — do not launch the 100-draw curve with the current generator.**

### A4 — HIGH INTERPRETATION DEFECT: K-curve pre-written conclusions predate S102

The K precommit and runner contain a branch saying that if G2 stays low it “does offer real protection against cross-modal confounding” and the V2 caveat is discharged.

S102 was discovered later and establishes that the statistical decision rule for G2 was never frozen by the contract.

Therefore the K experiment can characterize **the current historical G2 implementation**, but it cannot establish that the Stage-4 contract “offers real protection” until G2 semantics are prospectively specified.

Required amendment before execution:

- preserve the existing historical G2 implementation for continuity;
- scope all K-curve conclusions to that implementation;
- prohibit promotion of a favorable K result into a final Stage-4 safeguard;
- carry raw cvc Delta and scale-free cvc/primary magnitude diagnostics through the curve so a future prospectively specified G2 can be reconsidered without reconstructing the worlds if mathematically possible.

Status: **OPEN — interpretation amendment required before draw 1.**

### A5 — endpoint-overlap demotion — VERIFIED APPROPRIATE

The runner explicitly labels the Wilson-interval endpoint overlap as weak corroboration and names curve shape as primary evidence. This is consistent with the earlier S101 self-audit and avoids presenting a nearly-unfalsifiable endpoint check as confirmation.

### A6 — failed-run denominator behavior — VERIFIED AGAINST PRECOMMIT

The runner divides G2 passes by the prospectively fixed `n_draws`, not only successful draws. The precommit explicitly says a failed run stays in the denominator and its error is recorded. This behavior is therefore intentional.

A matching-audit failure is treated separately as a fixture defect and is supposed to stop execution.

## Required Macha actions

Before launching `run_stage4_g2_sensitivity_curve_v1.py`:

1. repair the K-world block assignment into a genuine K-block partition;
2. add realised block-occupancy evidence to the world manifest;
3. make the runner verify that evidence, especially K=200 -> 200 occupied singleton blocks;
4. amend the interpretation language for S102 so the curve characterizes the current G2 implementation rather than the final Stage-4 gate;
5. smoke-test K=1, K=5 and K=200 after the repair;
6. preserve the current unexecuted precommit and record the repair as a prospective amendment before the first draw.

## Governance

- Stage 4: NOT AUTHORIZED
- correspondence: UNOPENED
- real substrate: do not read for this repair
- training: OFF
