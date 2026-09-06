# C2 — engineering causal condition established

Terminal: `C2_CAUSAL_CONDITION_ESTABLISHED_FOR_HISTORICAL_128x8_PATH__BACKWARD_EXECUTED_UNDER_FP16_AUTOCAST`

Scope: the claim is about the historical 128/8 path as executed here. It is
**not** a claim about universal PyTorch behaviour.

Package root: `8b7c4811dbf74d92ecc055d8eb2a0f1ed21539b8fba1ea42fae68d66407a774d`
Manifest: `outputs/c2_t1_gradient_forensic_20260906/C2_RESULT_MANIFEST.csv`
Exact K0 to K1 diff: `outputs/c2_t1_gradient_forensic_20260906/C2_K0_K1_SOURCE_DIFF.txt`
Implementing agent: `CLAUDE_CODE`. Not self-certified; requires independent verification.

## The paired test

Both arms are derived by textual substitution on `inspect.getsource` of the
canonical `phase_e.run_update` and executed in its own namespace, so every line
except the substituted one is byte-identical. The recorded diff is two lines.

Exact historical geometry: cuda, batch 128, microbatch 8, 4 views, fp16 autocast,
`GradScaler` on, gradient checkpointing on, seed 8113002, one optimizer update.
Preserved identically across arms: device, fp16 forwards, teacher reuse, masks and
block construction, view sequence, per-view forward-then-backward interleaving,
loss division by 64, optimizer, RNG progression. **Ambient autocast state during
backward is the only changed factor.**

| arm | change | mandatory dead | zero-both moments | attention.output | movement > decay | all criteria |
|---|---|---|---|---|---|---|
| `K0_HISTORICAL` | none | **48 / 48** | 48 / 48 | 0 / 12 dead | 0 / 48 | false (required) |
| `K1_BACKWARD_AUTOCAST_DISABLED` | `.backward()` wrapped in `torch.autocast(enabled=False)` | **0 / 48** | **0 / 48** | 0 / 12 dead | **48 / 48** | **TRUE** |

All nine frozen criteria hold simultaneously for `K1`: every mandatory gradient
finite and strictly nonzero post-unscale, both Adam moments nonzero for all 48
after the step, all 12 `attention.output` tensors healthy, per-tensor movement
beyond pure decay for all 48, loss finite, optimizer step succeeded,
`online_moved` true, EMA equation exact, and the production gate reporting no
missing or nonfinite gradients. The historical arm simultaneously continues to
reproduce 48/48 dead.

## The causal condition

`phase_e.run_update` issues `.backward()` inside the `torch.autocast` fp16
region. PyTorch AMP guidance is that backward passes are **not recommended**
under autocast; the standard example exits the region first, and notes that
backward ops run in the dtype chosen for their corresponding forward ops.

Necessity and sufficiency are established at the code-condition level: disabling
autocast only around the backward call, with everything else untouched, restores
all 48 tensors.

## Deliberately not claimed

The deeper CUDA and kernel reason for collapse to *exact* zero rather than merely
inaccurate values remains open. Two candidate mechanisms were tested and refuted
at 128/8: the autocast weight cache (`I1`) and
`allow_fp16_reduced_precision_reduction` (`J1`). That question is scientifically
interesting but is no longer required to unblock the engineering diagnosis.

## Criterion repair, declared

`K1` initially returned 42 of 48 on movement. The six were exactly
`blocks.{0..5}.attention_norm.bias`, all zero-baseline, where relative movement
is a division by zero and undefined rather than small — the same defect the
independent F1-B verifier named `MOVEMENT_SKIPS_NEAR_ZERO_BASELINE`.
Zero-baseline tensors are now judged on strictly positive absolute movement.
Decoupled decay scales the parameter, so an exactly-zero parameter remains
exactly zero under decay alone and any movement is necessarily gradient-driven.
The repair could have failed and did not favour the outcome. Both evaluations are
preserved, the pre-repair artifact as `C2_V3_K1_PRE_CRITERION_REPAIR.json`.

## Repaired gradient gate

`scripts/v4/c2_mandatory_gradient_gate_v1.py` rejects, per protected tensor and
before any optimizer step, a missing gradient, a nonfinite gradient, or an
exact-zero gradient norm. No generic small-gradient threshold is invented: the
historical defect is exact zero, and a tiny finite nonzero gradient is real
training signal. Nine adversarial tests pass, including two that replay the
preserved bytes — the repaired gate rejects `K0` 48/48 and accepts `K1` 48/48 —
and one that confirms the historical gate saw nothing to reject because it
counted only missing and nonfinite.

The gate is **not yet adopted** by any successor training path. Adoption, not
existence, is what closes that blocker.

## Defects found by independent verification

Independent verification from a clean native-Linux clone rejected an earlier
form of this package. Three real defects were found and repaired, and they are
recorded here because the package would otherwise look as though it had passed
first time.

1. **The package was not preserved at all.** `.gitignore` excluded `outputs/`
   wholesale, so all 42 closure files existed only as untracked local files in
   one Windows worktree. A clean clone contained none of them. Repaired by
   tracking the package and marking it `-text` so byte-exact digests survive
   checkout on either platform.
2. **The manifest was stale.** The packager had run before the final edit to
   this document, recording 4725 bytes for a 5854-byte file, which also
   invalidated the package root. Repaired by running the packager as the last
   mutation and recomputing every row from disk before registering it.
3. **The gradient gate misclassified live tensors as dead.** `gate_module`
   used a gradient norm, which squares before summing. At fp32 the smallest
   subnormal `1.4e-45` squares to `2e-90` and underflows to a norm of exactly
   zero, so 48 genuinely nonzero tensors were reported as exact zero. The gate
   would have rejected real training signal. Repaired by testing emptiness
   exactly with `any(grad != 0)` and finiteness separately, never squaring. A
   scalar-only test had missed this; the live-tensor test in the real gradient
   dtype caught it.

None of the three touched the five closure-critical result artifacts, which
matched their authority digests unchanged throughout.

## Governance consequence

`component_gradient_report` counts only missing and nonfinite gradients, never
zero. It passed on every defective run while 48 tensors were dead, and it did
catch overflow in `D9`. That asymmetry is why T1 completed 205 updates without
raising a mechanics error. Any successor training path must gate zero per tensor
per role.

The DEC-013 characterisation of T1 as having valid mechanics is not defensible in
the parameter-wise sense. The historical biological outcome stands: T1 did not
qualify biology at u205. The causal interpretation changes — the run cannot be
read as a mechanically healthy model that merely under-optimised. Supersession
must follow independent C2 verification, not precede it.

## Not done, and not authorized here

The production-safe rewrite has not been run. Its current draft accumulates every
scaled loss and drains the backwards after the autocast block, holding 64 live
graphs at 128/8; it will exhaust memory. The recommended structure moves the
autocast region inside the view loop to preserve per-view accumulation. That
repair, its 128/8 regression, independent C2 verification, and DEC-013
supersession are all downstream of this stop.

T1 is not repaired or retrained. C3, real F1 and fresh production training remain
unauthorized.
