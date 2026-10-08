# C2-v3 localization — the severing condition

Status: `C2_SEVERING_CONDITION_IDENTIFIED__BACKWARD_INSIDE_AUTOCAST`
Mechanism (why): **still open.** Two candidate explanations were tested and both
refuted.
Implementing agent: `CLAUDE_CODE`. Not self-certified; requires review.

## The condition

`phase_e.run_update` calls `.backward()` **inside** the
`torch.autocast("cuda", dtype=float16)` block:

```python
with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=...):
    with torch.no_grad():
        teacher = target(...)
    for view in range(VIEWS):
        ...
        scaler.scale(scaled_loss).backward()   # <-- inside the autocast region
```

PyTorch's AMP guidance is that backward passes are **not recommended** under
autocast -- its standard example exits the region before backward, and notes
that backward ops run in the dtype chosen for their corresponding forward ops.
Moving the backward outside the region, changing nothing else, removes the
defect completely.

Measured with the real modules, real loader and real
`sample_uniform_target_blocks`, 2 cells:

| views | `.backward()` location | mandatory dead |
|---|---|---|
| 1 | inside autocast | **0 / 48** |
| 2 | inside autocast | **2 / 48** |
| 4 | inside autocast | **40 / 48** |
| 4 | **outside** autocast | **0 / 48** |

NOTE: this probe row changes ambient autocast during backward AND the
forward/backward interleaving at the same time. It is a confounded comparison
and is superseded by the paired 128/8 test below, which changes only ambient
autocast state.

Identical forward, identical fp16 autocast, identical `GradScaler`, identical
accumulation and loss division. Only the backward's position differs.
`attention.output` is live 12/12 in every row.

## Exclusion set, all at exact historical geometry (128 / 8, one update)

| id | change | mandatory dead | note |
|---|---|---|---|
| `E0` / `F0` / `G0` / `H0` / `I0` | none | 48/48 | endpoint reproduces every time |
| `E1` | outer autocast disabled | **0/48** | rescues |
| `E2` | outer autocast bf16 | **0/48** | rescues |
| `E3` | `GradScaler` disabled | 48/48 | **void**: `attention.output` also 12/12 dead |
| `E4` | gradient checkpointing off | 48/48 | not the cause |
| `F1` | output cast moved after the output projection | 48/48 | not the cause |
| `G1` | q/k/v projections computed in fp32 | 48/48 | not the cause |
| `H1` | entire attention branch in fp32 | 48/48 | not the cause |
| `I1` | autocast weight cache disabled | 48/48 | **candidate mechanism refuted** |
| `J1` | `allow_fp16_reduced_precision_reduction = False` | 48/48 | **candidate mechanism refuted** |

Severity modifiers, recorded but excluded from the causal matrix: microbatch
(`D5` 42/48, `D6` 42/48), target-block cardinality (`D7` 48/48, `D8` 48/48),
mask fraction (`D9` aborted with 94 nonfinite gradients — the historical pooled
check does catch overflow, just never zero).

## What is established

1. The historical endpoint reproduces at exact geometry: 48/48 mandatory dead,
   `attention.output` healthy, zero-both-moment counts tracking exactly, loss
   falling normally (2.2177 → 1.9858 → 1.7699 over three updates at batch 4).
2. The condition is `.backward()` executed inside the autocast region with more
   than one accumulated backward. It is graded in the number of backwards
   (0 → 2 → 40 dead for 1 → 2 → 4 views) and removed entirely by relocating the
   backward.
3. It is **not** gradient checkpointing, **not** the `GradScaler`, **not** the
   position of the fp32/fp16 cast around the attention output projection,
   **not** the dtype of the q/k/v projections, **not** anything inside the
   attention branch, **not** the autocast weight cache, and **not** fp16
   reduced-precision matmul reduction.
4. bf16 also rescues. bf16 has fewer mantissa bits than fp16 but fp32's exponent
   range, so the sensitivity is to dynamic range rather than rounding precision.
5. The role partition follows gradient magnitude. In fp32, `attention.output`
   gradients are all ≥ 1.74e-1, while the mandatory tensors reach down to
   1.71e-4 — roughly a thousandfold smaller. The small ones die and the large
   ones survive, which is why the split is exactly 48 versus 12 and why it is
   graded rather than all-or-nothing.

## What is not established

**Why** backward-inside-autocast produces exactly zero rather than merely
inaccurate gradients. The two obvious mechanisms are refuted (`I1`, `J1`). The
activation gradients arriving at the q/k/v projection outputs are healthy and
nearly identical in fp16 and fp32 (`query` absmax 1.41e-3 fp16 versus 9.05e-4
fp32), so the loss occurs in the weight-gradient reduction rather than in the
activation gradient path. That measurement came from a probe condition which
does **not** reproduce the defect (1 view), so it constrains rather than
explains.

## The candidate fix

Move `.backward()` outside the `torch.autocast` block in `run_update`. Two
lines. It is not an architecture change, not an optimizer change, and not a
change to `KernelLinearAttention`.

Not yet run: the corrective variant at 128/8 through `run_update` itself. That
is the regression test and it is the next step.

## Required regression criteria, frozen

Historical path must still reproduce the dead signature. Corrected path, one
update at 128/8, must show all 48 mandatory gradients finite and nonzero before
the optimizer step, both Adam moments nonzero afterwards, per-tensor movement
exceeding pure decay, `attention.output` healthy, and finite loss.

## Governance

`phase_e.component_gradient_report` counts only missing and nonfinite gradients,
never zero. It passed on every run above while 48 tensors were dead. Any
successor training path must gate zero per tensor per role.

T1 is not repaired or retrained. DEC-013 is not amended. C3, real F1 and fresh
production training remain unauthorized.
