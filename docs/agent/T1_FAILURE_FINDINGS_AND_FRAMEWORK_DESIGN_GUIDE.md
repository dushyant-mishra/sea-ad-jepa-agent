# The T1 training failure — findings, evidence, and what to carry into future frameworks

Written 2026-09-09 from the committed C2 closure package, not from recollection.
Every claim below is traceable to a tracked artifact named in the Evidence
section. Where the package's own prose overstates something, that is flagged
rather than repeated.

Scope discipline, stated once and meant: this is a finding about **the historical
128/8 training path as executed on one machine**. It is not a claim about
universal PyTorch behaviour, and the package says so in its own terminal.

---

## 1. What the failure was

T1 completed 205 optimizer updates and did not qualify biology at u205. The
original characterisation (DEC-013) was that T1 had valid training mechanics and
had merely under-optimised. **That characterisation is not defensible in the
parameter-wise sense.**

At exact historical geometry — CUDA, batch 128, microbatch 8, 4 views, fp16
autocast, `GradScaler` on, gradient checkpointing on, seed 8113002, one optimizer
update — **48 of 48 protected tensors received gradients that were exactly zero**
after unscaling.

The 48 are enumerated, not discovered:

    blocks.{0..5}.{attention_norm, attention.query, attention.key, attention.value}.{weight, bias}

Simultaneously, all 12 `attention.output` tensors were healthy. So the model was
not globally dead. Six blocks' worth of attention **input** projections and
normalisation were receiving no learning signal at all, while the output
projections learned normally. Loss fell smoothly throughout — 2.2177 → 1.9858 →
1.7699 over three updates at batch 4 — which is exactly why nothing looked wrong.

The consequence for interpretation: T1 cannot be read as a mechanically healthy
model that under-optimised. It was a model whose attention input pathway was not
training. The historical biological outcome stands; the causal story behind it
changes completely.

---

## 2. The causal condition

`phase_e.run_update` calls `.backward()` **inside** the `torch.autocast` fp16
region:

```python
with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=...):
    with torch.no_grad():
        teacher = target(...)
    for view in range(VIEWS):
        ...
        scaler.scale(scaled_loss).backward()   # inside the autocast region
```

PyTorch's own AMP guidance is that backward passes are **not recommended** under
autocast; the documented example exits the region first, and notes that backward
ops run in the dtype chosen for their corresponding forward ops.

### The paired test that establishes it

Both arms were derived by textual substitution on `inspect.getsource` of the
canonical `phase_e.run_update` and executed in their own namespace, so every line
except the substituted one is byte-identical. **Nothing was retyped.** The
recorded diff is two lines:

```
-                scaler.scale(scaled_loss).backward()
+                with torch.autocast(device_type=device.type, enabled=False):
+                    scaler.scale(scaled_loss).backward()
```

| arm | change | mandatory dead | zero-both moments | attention.output | movement > decay | all criteria |
|---|---|---|---|---|---|---|
| `K0_HISTORICAL` | none | **48 / 48** | 48 / 48 | 0 / 12 dead | 0 / 48 | false |
| `K1_BACKWARD_AUTOCAST_DISABLED` | backward wrapped in `autocast(enabled=False)` | **0 / 48** | **0 / 48** | 0 / 12 dead | **48 / 48** | **true** |

Ambient autocast state during backward is the only changed factor. Device, fp16
forwards, teacher reuse, masks and block construction, view sequence, per-view
forward-then-backward interleaving, loss division by 64, optimizer and RNG
progression are all preserved identically.

All nine frozen criteria hold simultaneously for `K1`. The historical arm
continues to reproduce 48/48 dead.

### It is graded in the number of accumulated backwards

| views | backward location | mandatory dead |
|---|---|---|
| 1 | inside autocast | 0 / 48 |
| 2 | inside autocast | 2 / 48 |
| 4 | inside autocast | 40 / 48 |
| 4 | **outside** autocast | 0 / 48 |

The package flags this table as **confounded** — it changes ambient autocast and
the forward/backward interleaving together — and supersedes it with the paired
128/8 test above. That honesty is worth preserving when citing it.

### Why exactly 48 versus 12

The role partition follows gradient magnitude. In fp32, `attention.output`
gradients are all ≥ 1.74e-1, while the mandatory tensors reach down to 1.71e-4 —
roughly a thousandfold smaller. Small gradients die, large ones survive. That is
why the split is exactly 48 versus 12, and why the effect is graded rather than
all-or-nothing.

---

## 3. What was excluded, at exact geometry

Ten conditions tested at 128/8, one update each:

| id | change | dead | verdict |
|---|---|---|---|
| `E0`/`F0`/`G0`/`H0`/`I0` | none | 48/48 | endpoint reproduces every time |
| `E1` | outer autocast disabled | **0/48** | rescues |
| `E2` | outer autocast **bf16** | **0/48** | rescues |
| `E3` | `GradScaler` disabled | 48/48 | **void** — `attention.output` also 12/12 dead |
| `E4` | gradient checkpointing off | 48/48 | not the cause |
| `F1` | output cast moved after the output projection | 48/48 | not the cause |
| `G1` | q/k/v projections in fp32 | 48/48 | not the cause |
| `H1` | entire attention branch in fp32 | 48/48 | not the cause |
| `I1` | autocast weight cache disabled | 48/48 | candidate mechanism **refuted** |
| `J1` | `allow_fp16_reduced_precision_reduction = False` | 48/48 | candidate mechanism **refuted** |

**bf16 rescues.** bf16 has fewer mantissa bits than fp16 but fp32's exponent
range, so the sensitivity is to **dynamic range**, not rounding precision. That
is the single most useful diagnostic fact in the table.

Severity modifiers recorded but excluded from the causal matrix: microbatch
(`D5` 42/48, `D6` 42/48), target-block cardinality (`D7`, `D8` both 48/48), mask
fraction (`D9` aborted with 94 nonfinite gradients).

---

## 4. Why it went undetected for 205 updates — the transferable lesson

This is the part that should shape future frameworks.

`phase_e.component_gradient_report` counted only **missing** and **nonfinite**
gradients. It never counted **zero**. It passed on every defective run while 48
tensors were dead, and it did correctly catch overflow in `D9`.

That asymmetry is the whole failure. A monitor that checks for `None` and `NaN`
is blind to the one pathology that produces a smooth, plausible loss curve. A
dead gradient is not an exception — it is a silent, well-behaved zero that
integrates into a decaying parameter and looks like convergence.

**Design rule: gate zero, per tensor, per role, before the optimizer step.**
Aggregate norms, global checks, and loss curves cannot substitute.

---

## 5. Reusable assets

### 5.1 `scripts/v4/c2_mandatory_gradient_gate_v1.py`

The repaired gate. Rejects, per protected tensor and before any optimizer step:
a missing gradient, a nonfinite gradient, or a gradient that is exactly empty.

Public surface:

```
FROZEN_MANDATORY_REGISTRY     the 48 protected identities, enumerated
MANDATORY_ROLES               ("attention_norm","attention.query","attention.key","attention.value")
validate_registry(module)     fails closed unless discovery yields exactly that set
enforce_registry(module)
mandatory_names(module)
classify_tensor(grad)         live-tensor classification
gate_module(module, names)    the live adjudicator
enforce(module, names)
classify_norm / gate_from_norms / report_from_statuses   replay-only
```

Two design decisions in it are worth copying:

**It never computes a norm on a live tensor.** A norm squares before summing, so
a tensor whose only nonzero element is a small subnormal underflows to a norm of
exactly zero and is misclassified as dead. At fp32 the smallest subnormal
`1.4e-45` squares to `2e-90` → 0. Emptiness is tested elementwise with
`any(grad != 0)`; finiteness separately with `torch.isfinite(grad).all()`.
`gate_from_norms` exists **only** to replay recorded norms out of preserved
artifacts and must never adjudicate a live tensor.

**No generic small-gradient threshold is invented.** The historical defect is
exact zero. A tiny finite nonzero gradient is real training signal and must not
be rejected.

### 5.2 The frozen protected registry

`FROZEN_MANDATORY_REGISTRY` enumerates all 48 identities explicitly, and
`validate_registry` fails closed unless dynamic discovery yields exactly that
set.

Dynamic discovery alone cannot establish completeness: a renamed or removed
module silently shrinks the registry, the gate then protects fewer tensors, and
it still reports a pass. A test confirms a five-block encoder is rejected with 40
discovered and 8 missing rather than quietly accepted.

Adoption must call `enforce_registry` **alongside** the gate.

### 5.3 The paired-substitution forensic method

The most reusable technique in the package. To attribute a defect to one line:

1. Take `inspect.getsource` of the canonical function.
2. Produce the variant by **textual substitution** on that source.
3. Execute each arm in its own namespace.
4. Emit the diff as an artifact and digest it.

This makes "everything else is identical" a verifiable property rather than a
claim, and it is why the two-line diff is the evidence. `C2_K0_K1_SOURCE_DIFF.txt`
records the substitution plus `historical_step_sha256`, `ipb_jepa_sha256`,
`forensic_source_sha256`, geometry, torch version and GPU.

### 5.4 Harness and runners

    scripts/v4/run_c2_t1_exact_path_forensic_v3.py    the exact-path harness
    scripts/v4/run_c2_t1_gradient_forensic_v1.py      the earlier harness
    scripts/v4/c2_corrective_run_update_v3.py         the corrective variant
    scripts/v4/c2_attention_cast_variant_v3.py        cast-boundary variants (F/G/H)
    scripts/v4/c2_probe_attention_boundary_v3.py      activation-gradient probes
    scripts/v4/c2_synthetic_loader_v3.py              deterministic loader
    scripts/v4/c2_build_closure_package_v1.py         packager, manifest and root
    configs/v4/c2_t1_gradient_forensic_v1.json        frozen forensic configs
    configs/v4/c2_t1_gradient_forensic_v2.json

    tests/test_c2_mandatory_gradient_gate_v1.py       13 adversarial cases
    tests/test_c2_successor_gate_adoption_v1.py       adoption enforcement
    tests/test_c2_synthetic_loader_v3.py
    tests/test_c2_t1_checkpoint_gradient_provenance_v1.py
    tests/test_c2_t1_gradient_forensic_v1.py
    tests/v4/test_stage81a3_gradient_firewall.py

### 5.5 The historical reference implementation

`scripts/v4/stage81a3_prod41k_engineering_smoke.py` holds `phase_e.run_update` —
the authoritative historical construction. **Read it before reconstructing
anything about T1.** An earlier harness of mine diverged from it in five ways,
one large: the real target-block sampler hides `floor(0.40 * n_measured)` genes
per cell across 16 blocks of hundreds of genes each, while mine hid 256 genes in
blocks of 16. The target was an `EMATargetEncoder` in eval mode, not a `deepcopy`
in train mode, and `gene_ids` was a canonical `arange` shared across cells rather
than a per-cell `randperm`. Two full CUDA runs returned "endpoint not reproduced"
and I reported that as a negative result about the system. It was a statement
about my harness.

---

## 6. Evidence, by digest

Package: `outputs/c2_t1_gradient_forensic_20260906/`, 42 files tracked, marked
`-text` in `.gitattributes` so byte-exact digests survive checkout on any
platform.

Closure-critical artifacts:

    C2_V3_K0_HISTORICAL.json                  01908fd62b1a233207092758b3cb27344f8b7ca81140f5e9295039a35987abd8
    C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json  c5b9edf17f57756c201582f130a2bd7e0c7945f40d3412d7ea8742291465d381
    C2_V3_K1_PRE_CRITERION_REPAIR.json        260b9aeef913482f1b3bff8ae6edfe7e88359284ceedf1e1562e196e4a7cc97a
    C2_K0_K1_SOURCE_DIFF.txt                  d0cd70bae1e71e35d4ee02a09c8954360a155215af22998fee17d3314075caf9

Independent verification: `PASS_C2_INDEPENDENT_VERIFICATION` at commit
`712cd07d52371c4cbbfb0760a09399e9c23ec1b4`, manifest
`b4d2fafc0665bd0c135c3ddac0c76b873602034b79f267a808e82636ad11960b`, package root
`f6463bdc3ca85f29708db6d444b4843087a483cc60ba75a40df35f24bb9c4222`, 55 manifest
rows.

Narrative documents: `C2_CAUSAL_CONDITION_ESTABLISHED.md`,
`C2_V3_LOCALIZATION.md`, `C2_V3_REPRODUCTION.md`, `C2_PROVISIONAL_RESULT.md`.
Environment: torch 2.7.0+cu128, NVIDIA GeForce RTX 3080 Laptop GPU.

---

## 7. Corrections to the package's own claims

Recorded because the package's value is that its failures stay visible.

**The test count is environment-dependent.** `C2_CAUSAL_CONDITION_ESTABLISHED.md`
says "Thirteen adversarial tests pass". On this checkout:

    9 passed, 4 skipped — could not import 'torch': No module named 'torch'

Thirteen exist. Nine run without torch. The four that skip include **the
live-tensor test in the real gradient dtype covering fp32 and fp16 subnormals** —
the test that caught the norm defect, and the most important one in the file. In
an environment without torch the suite reports green while that test never runs.

This is the same class of defect as an earlier F1-A finding: a test that can skip
is not a test that ran. **Anyone adopting this gate must confirm the four
torch-dependent tests actually execute**, not merely that the suite is green.

**Three defects were found by independent verification** of an earlier form of
the package, and are recorded in it: the whole package was untracked because
`.gitignore` excluded `outputs/` wholesale, so a clean clone contained none of the
42 closure files; the manifest was stale, recording 4725 bytes for a 5854-byte
file and invalidating the root; and the gate misclassified live tensors as dead
via the norm defect above. None touched the four closure-critical artifacts,
which matched their digests unchanged throughout.

**An earlier review candidate failed.** Commit
`76b9449e61ca4f3561c2c85e0ce9175f82bcd636` returned
`STOP_C2_INDEPENDENT_VERIFICATION__FROZEN_CANDIDATE_AUTHORITY_INCONSISTENT`. The
causal evidence survived re-derivation; the failure was stale authority
statements in the prose. It is preserved unmodified.

---

## 8. Still open

**The mechanism.** Why backward-inside-autocast produces exactly zero rather than
merely inaccurate values is unresolved. Both obvious candidates are refuted
(`I1` autocast weight cache, `J1` fp16 reduced-precision reduction).

A constraint, not an explanation: activation gradients arriving at the q/k/v
projection outputs are healthy and nearly identical in fp16 and fp32 (`query`
absmax 1.41e-3 fp16 versus 9.05e-4 fp32), so the loss occurs in the **weight-
gradient reduction** rather than the activation-gradient path. That measurement
came from a 1-view probe which does **not** reproduce the defect, so it
constrains rather than explains. Tracked as `C2_DEEP_KERNEL_MECHANISM_OPEN`.

**The gate is not adopted.** It exists and is tested; no successor training path
calls it. Adoption, not existence, closes that blocker.

**The production-safe rewrite has not been run.** Its draft accumulates every
scaled loss and drains the backwards after the autocast block, holding 64 live
graphs at 128/8 — it will exhaust memory. The recommended structure moves the
autocast region **inside** the view loop to preserve per-view accumulation.

**T1 is not repaired or retrained.** DEC-013 supersession follows independent
verification rather than preceding it.

---

## 9. Design rules for future frameworks

1. **Gate zero per tensor per role, before the optimizer step.** Missing and
   nonfinite are not enough. This one rule would have caught T1 at update 1
   instead of never.
2. **Never adjudicate a live tensor with a norm.** Squaring underflows
   subnormals to exactly zero. Test emptiness elementwise, finiteness
   separately.
3. **Enumerate protected identities and fail closed on discovery drift.** A
   renamed module must break the gate loudly, not shrink it silently.
4. **Do not invent thresholds for a defect whose signature is exact.** A tiny
   finite gradient is signal.
5. **Keep backward outside the autocast region**, and if AMP is used, prefer
   bf16 where the hardware allows — the sensitivity here was dynamic range, not
   precision.
6. **Attribute defects by textual substitution on `inspect.getsource`**, emit
   the diff as a digested artifact, and let the diff be the evidence.
7. **Track evidence packages in git with `-text`.** A package that exists only
   in one worktree does not exist. A wholesale `outputs/` ignore rule will eat
   it.
8. **Regenerate the manifest as the last mutation**, and recompute every row
   from disk before registering it.
9. **Never embed a package root inside a manifested member.** It goes stale the
   moment it is written — the file is part of what the root covers.
10. **Confirm environment-dependent tests actually ran.** A skip is not a pass,
    and the tests most likely to skip are the ones touching the hardware where
    the defect lives.
11. **A monitor that has never failed is not evidence of health.** Ask what it
    is structurally incapable of seeing. `component_gradient_report` could not
    see zero.
12. **Verify a reconstruction against the authoritative implementation before
    running it.** "Endpoint not reproduced" is a statement about the harness
    until the harness is shown faithful.
