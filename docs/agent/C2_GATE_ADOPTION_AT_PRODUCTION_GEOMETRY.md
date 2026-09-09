# C2 gradient gate: adoption and the 128×8 regression

Status: the gate is adopted as the only supported successor step, and the
historical failure has been shown to be stopped at the exact production
geometry. No training has been started, and no closed gate has been opened.

## What was actually missing

The gate module and its 13 tests already existed, as did a `successor` variant
that inserts it into the real update function and a five-test adoption suite.
Two things were not true of that state.

The gate suites reported *9 passed, 4 skipped* because the execution environment
had no torch, and the four skips included the live-tensor subnormal test — the
one covering the defect external review had found. A skipped test is not a test
that ran.

The adoption had never executed at production shape. The five adoption tests run
at batch 4 / microbatch 2, and the runner that reaches the exact historical
128×8 geometry — the one that produced the K0 and K1 records — exposed three
variants, neither of them gated. So the gate had never been between an unscale
and an optimizer step at the geometry where the failure happened.

## Environment

`sea-ad-jepa-v3`, torch 2.7.0+cu128, CUDA available, NVIDIA GeForce RTX 3080
Laptop GPU — the same device named in the K0 and K1 records.

All four gate suites now run with torch and CUDA present:

| suite | result |
| --- | --- |
| `test_c2_mandatory_gradient_gate_v1` | 13 passed, 0 skipped |
| `test_c2_successor_gate_adoption_v1` | 5 passed, 0 skipped |
| `test_c2_gate_stop_attribution_v1` | 8 passed, 0 skipped |
| `test_v5_successor_training_step_v1` | 10 passed, 0 skipped |
| `test_v5_successor_teacher_entrypoint_v1` | 8 passed, 0 skipped |
| total | **44 passed, 0 skipped** |

## The 128×8 regression

Both runs use the exact historical geometry — effective batch 128, microbatch 8,
views 4, seed 8113002, fp16 autocast — recorded as
`is_historical_geometry: true`.

`L0_GATED_HISTORICAL` is the negative control: the historical backward left
inside autocast, with the gate in place.

```
u000 GATE STOPPED the update  rejected=48/48  adam-moments-created=0  params-moved=0
```

The adjudication is the historical signature exactly: registry 48 discovered of
48 expected, `EXACT_ZERO=48`, `LIVE=0`, `MISSING=0`, `NONFINITE=0`. The stop
evidence is what makes it a stop rather than a complaint — no protected tensor
acquired Adam moments, and every protected tensor was bit-identical to its
pre-update value. This is the update that historically ran 205 times.

`L1_SUCCESSOR` is the adopted path: backward outside fp16 autocast, same gate.

```
u000 loss=2.2177  dead=0/48  zero-moments=0/48  live_ref dead=0/12  move>decay=48/48  ALL_CRITERIA=True
```

The recorded diff against the canonical function is three changes and nothing
else — the rename, the backward wrapped in `autocast(enabled=False)`, and the
two gate calls immediately after `scaler.unscale_(optimizer)`. That placement is
the required ordering, since `scaler.step` updates the Adam moments and
`controller.after_successful_optimizer_step` applies EMA after it:

    unscale → gradient gate → optimizer step → Adam moments → EMA

Records: `outputs/c2_successor_adoption_20260909/`.

## Adoption

`scripts/v4/v5_successor_training_step_v1.py` is the only supported way to
obtain a successor step. It has no parameter to disable the gate and no ungated
return path, and it re-verifies the built source before handing it back, so the
property is established for the run about to happen rather than for the machine
that last ran the tests.

The step remains a function derived from `inspect.getsource` of the canonical
`run_update` rather than an edit to it. Retyping the update loop to add two
lines would introduce transcription risk into the exact code the causal result
depends on being unchanged.

## Two defects found in this work, by attacking it

**False attribution of a gate stop.** The runner records a STOP when the update
raises and the gate is judged responsible. My first handler caught `RuntimeError`
and re-adjudicated. `torch.cuda.OutOfMemoryError` subclasses `RuntimeError`, and
OOM at 128×8 is a documented failure of this path, so an OOM raised while the
protected gradients happened to be dead would have been written down as proof
the gate works. Out-of-memory errors are now re-raised before the gate is
consulted, and attribution is attempted only for variants that actually carry
the gate — in `historical` every protected gradient is dead by construction, so
re-adjudication alone would have objected on every run with no gate present.

**A wrong expectation in my own test.** I wrote a case asserting the verifier
must refuse a source with a second, conditional `optimizer.step()` after the
gate. It should not: the gate has already adjudicated the gradients that step
applies, so the historical failure cannot recur through it. Flipping the
assertion to match the code would have been the mirror error, so the case is
documented as an accepted limit of scope with its reason, and replaced by the
cases that are genuinely unsafe for the structural reason I was reaching for —
a `.backward()` or a `zero_grad` between the gate and the step, which lets the
optimizer apply gradients the gate never saw. The verifier now rejects both.

## What this does not establish

The gate protects the 48 enumerated attention tensors. The predictor's gradients
are reported but not gated, which matches the frozen registry and the stated
scope of exactly 48 protected tensors.

One update was run per variant, not a training run. The claim is that the
historical failure is stopped before it can change state, not that the corrected
path trains well.

Production-shape memory behaviour is a separate item. Both runs here complete at
128×8 on 16 GB, as K0 and K1 did; the known OOM belongs to the superseded
`production_safe` variant, which holds 64 live graphs and remains unexecuted.

## The real teacher entrypoint

The section above adopted the gate into the *step*. That left the actual
production entrypoint untouched: `stage81a3_prod41k_teacher_t1.py` is the script
that ran T1, and its loop calls `phase_e.run_update` directly and accepts the
update when `step_succeeded`, `online_moved` and `ema_equation["equal"]` all
hold — all three of which held for 205 consecutive updates while every protected
tensor was dead. Adopting anywhere short of that call site changes nothing about
the path that failed.

The historical file is not edited. Its digest is bound in the preservation
manifests and the T1 evaluation freeze, and it is the only faithful record of
what was run, so editing it would break that provenance and remove the ability
to reproduce the failure.

`scripts/v4/v5_successor_teacher_entrypoint_v1.py` derives the successor
entrypoint from that source instead, by the same substitution technique the
corrective variants use, with exactly one declared change:

    result = phase_e.run_update(   ->   result = _v5_successor_step(phase_e)(

Verified, not asserted: the diff is one added and one removed line, the changed
line is the update call, and no ungated `phase_e.run_update(` call survives.

The repository root is an explicit input rather than an inference. The teacher
script computes `ROOT = Path(__file__).resolve().parents[2]` and reads its
loader, exports and data from underneath it, and the gate stack lives in the T0
lane, which has neither `exports/contextual_biology_v6r5a_20260822` nor
`exports/static_context_decomposition_v4_20260821`. The derived module's
`__file__` is set to the historical script under the chosen root so the script's
own path arithmetic stays internally consistent, and a root that cannot supply
what training reads is refused up front rather than failing inside the loader.

Built against the real root, without calling `main()`:

```
module built  : v5_successor_teacher
root resolved : D:\Jepa project
geometry      : EFFECTIVE_BATCH=128 MICROBATCH=8 MAX_UPDATES=205
ungated call in derived source: False
[v5] gated successor step verified: gate at lines [100, 101], optimizer steps at
[111], ordering unscale -> gate -> optimizer step -> Adam moments -> EMA
gated step    : run_update_successor
```

No training was started. `TRAINING_AUTHORIZED` remains false, and the production
memory behaviour of this entrypoint against the real loader is the next item,
not something established here.

## Production 128×8 memory: the premise checked

The next item was to fix the production 128×8 OOM path before teacher training.
Checking it before building a fix, the OOM does not belong to the production
path.

**The real T1 run did not run out of memory.** It completed all 205 updates at
128×8 and recorded both peak counters every update. Worst case across the whole
run: **5.54 GiB allocated, 5.75 GiB reserved**, on a 16 GiB RTX 3080 Laptop —
about 10.25 GiB of headroom. The two recorded T1 run failures were a frozen
address-reader identity mismatch and a pandas attribute error. Neither was a
memory failure, and no artifact in either root records an out-of-memory event.

**The OOM is a property of one superseded corrective variant.**
`production_safe` accumulates every scaled loss and drains the backwards after
the autocast block, holding 64 live graphs at 128/8. It is marked
`SUPERSEDED_DO_NOT_RUN` and has never been executed. It is not the production
path and is not what training would use — the minimal `backward_autocast_disabled`
correction supersedes it, and that is what the successor step is built from.

**The corrected path costs nothing at production shape.** The forensic runner now
records peak memory the same way the teacher script does — reset the counters
immediately before the update, read both peaks immediately after — so the
numbers are directly comparable. At exact 128×8 geometry:

| variant | peak allocated | peak reserved |
| --- | --- | --- |
| `historical` | 5.4186 GiB | 5.7031 GiB |
| `successor` (gated, corrected) | 5.4186 GiB | 5.7031 GiB |
| real T1 run, worst of 205 updates | 5.54 GiB | 5.75 GiB |

Identical to four decimal places. Wrapping the backward in
`autocast(enabled=False)` and enforcing the gate changes peak memory not at all,
and the harness reproduces the real run's memory to within 0.05 GiB, which is
also a check on the harness rather than only on the correction.

So there is no OOM to fix, and the condition the item existed to protect — the
corrected path actually running at production shape — is met.

**What is still not proven.** These runs use the synthetic loader. The real T1
peaks quoted above do include the real loader and they match, so the model step
is covered, but the *gated entrypoint* has never executed against the real
loader. Doing that needs one update written to an isolated output directory:
`RUN` is hardcoded to `exports/prod41k_teacher_t1_20260823/t1_run`, and a run
there would overwrite preserved T1 records. That is not something to do without
authorization, and it is not done here.
