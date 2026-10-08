# V5 development-only diagnostic execution contract, and its authorization blocker

**Verdict up front: the integration is assembled and mechanically verified, and
the real-data run is blocked by two independent authorization gates that I must
not and did not bypass.** This document is the runnable contract plus the exact
blocker, written so that the moment authority is issued the run is one command.

Nothing here opens protected data. No real `reader_fit` expression was consumed.

---

## 1. What was physically executed

| item | status |
|---|---|
| V5 test suite, CUDA environment, zero-skip census | **COMPLETED_AND_PHYSICALLY_EXECUTED** — 1,620 collected, **1,617 passed, 0 skipped, 3 failed** |
| Teacher/student integration freeze audit **V4** | **COMPLETED_AND_PHYSICALLY_EXECUTED** — `PASS`, 21 source rows, 7 active tests, **0 failures** |
| Bounded mechanical integration diagnostic | **SYNTHETIC_TESTED_ONLY** — see §4; the reported run is the one whose receipt is named there, and no verdict is claimed here ahead of it |
| Real-data `reader_fit` diagnostic | **BLOCKED_BY_AUTHORIZATION** — see §5 |

The three failures are `test_teacher_student_integration_freeze_v1/v2/v3`. They
are **superseded**, not drift: the current freeze is **V4**, and V4 passes
cleanly against current bytes. See §6, which records this as a test-hygiene
defect rather than an integrity failure — I initially mis-read it as drift and
checked the design intent before reporting.

## 2. The traced execution path

Every component named in the handoff exists. Tracing the full path:

| stage | component | state |
|---|---|---|
| authenticated FULL104 input | `full104_pass1_builder_v1.py`, `full104_pass1_physical_binding_v1.py`, corrected derivative `4b15ee52…`, frozen pass1 `37f79e49…` | PRESENT |
| development sampler | `finite_relational_sampling.py`, `full104_strict_support_selection_v1.py` | PRESENT |
| input/observation separation | `data_first_geometry.py`, `evidence_estimability_contract_v2.py` | PRESENT |
| masking | `current_masking_policy_authority_v2.py`, `masking_authority_v1.py` | PRESENT |
| online encoder + predictor | `KeyedIPBEncoderV2Reference`, `BlockPredictor` | PRESENT |
| detached teacher target | `inactive_update_reference.py` (teacher `requires_grad_(False)`) | PRESENT, **verified** |
| loss | `weighted_block_jepa_loss` | PRESENT, **verified** |
| backward | `run_inactive_reference_update` | PRESENT, **verified** |
| protected gradient verification | `_gradient_report`, `production_protected_registry_authority_v1.py` | PRESENT, **verified** |
| proved optimizer update | AdamW, step asserted exactly once | PRESENT, **verified** |
| Adam moment verification | `qualified_optimizer_guard_v3.py` | PRESENT, **verified** |
| EMA update | `ema_presentation_v1.py`, `ema_timescale_authority_v2.py` | PRESENT, **verified** |
| atomic checkpoint + telemetry | `current_atomic_checkpoint_guard_v2.py`, `capture/restore_reference_checkpoint` | PRESENT, **verified** |

**The one genuinely missing connection** is the adapter between the
authenticated FULL104 streaming readers and the update harness. The readers
exist (`full104_masking_streaming_executor_v1.py`,
`full104_physical_shakedown_v1.py`) and the harness exists
(`run_inactive_reference_update`), but nothing wires a real `reader_fit` cell
batch into the harness signature. That adapter is deliberately **not** written
here, because writing it would be building the thing the authorization gate
exists to withhold.

This is not "the architecture is unimplemented." It is one missing adapter
behind a closed gate.

## 3. No legacy geometry was inherited

`model_geometry_authority_v2.py` states in its own source that *no historical
width/depth is encoded*. The diagnostic binds its own declared constants and the
receipt asserts all three legacy-inheritance checks are **false**:

The values below are transcribed from `declared_geometry` in the published
receipt `results/v26/V5_MECHANICAL_INTEGRATION_DIAGNOSTIC_V1.json`, which is the
authority for what actually ran. Script and receipt were verified to agree
field-by-field.

| quantity | historical value | diagnostic value | inherited? |
|---|---|---|---|
| EMA momentum | 0.996 | **0.99** | no — deliberately distinct so inheritance would show as a mismatch |
| block depth | 6 | **2** | no |
| cells per update | 128 x 8 | **12** | no |
| vocabulary_size | — | 96 | declared |
| width / heads / ffn_width | historical | **32 / 4 / 64** | declared |
| dropout | — | 0.10 | declared |
| target_block_count / mask_fraction | — | 4 / 0.40 | declared |
| views_per_update | — | 2 | declared |
| max_teacher_tokens_per_microbatch | — | 48 | declared |
| AdamW lr / betas / eps / weight_decay | — | 3e-4 / (0.9, 0.999) / 1e-8 / 0.01 | declared |

**Correction, raised by the independent audit of PR #147.** An earlier version of
this table read `24 cells/update` and `64 / 8 / 128` for width/heads/ffn. Those
were the values of a *first* geometry that was measured at 169.6 s per update and
reduced for tractability before the reported run. I updated the producer and its
budget note but left this table stale, so the document disagreed with the code it
described. The table above is now transcribed from the receipt. This was a
documentation defect only — the receipt, the producer and the executed run were
consistent with each other throughout, and no reported measurement changes.

Every one of these is labelled `DECLARED_WITHOUT_EXTERNAL_JUSTIFICATION` in the
producer. They are conventional diagnostic choices, they carry **no** production
authority, and they must be re-derived from real dataset geometry before any
production run. Declaring a number prospectively does not make it scientifically
authoritative.

The V4 `production_update` is **not** on this path. The runtime source authority
enforces `CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1`, and the only
V5 modules importing V4 are `inactive_update_reference` (importing the encoder
and block primitives, not the update), plus two modules whose own docstrings say
they are deliberately not wired into `production_update`.

## 4. The bounded mechanical diagnostic

`scripts/v5/v5_mechanical_integration_diagnostic_v1.py`, synthetic fixtures
only, 40 updates with a checkpoint/restore at update 20. It verifies physically:

* the optimizer steps **exactly once** per update (step sequence asserted to
  increase by exactly 1);
* the teacher carries **no** gradient and advances **only** after a successful
  optimizer step;
* online parameters move on every update, and by more than weight decay alone;
* Adam first **and** second moments populate and stay nonzero;
* every loss is finite;
* **checkpoint restart reproduces the uninterrupted run** — compared by a
  name-keyed parameter fingerprint, not by loss value, because equal losses do
  not prove equal state;
* cell identity is an explicit unique stable key, never a storage position.

The receipt records seeds, environment, torch and CUDA versions, the producer
SHA-256, wall clock, and the full per-update trajectory.

**Interpretation guard, recorded in the receipt itself:** a falling loss on
synthetic tensors demonstrates gradient flow and nothing about biology.

### Measured result — `PASS_V5_MECHANICAL_INTEGRATION_SYNTHETIC`

```
receipt  D:/jepa_v5_outputs_20260925/mech_integration_v3/
         V5_MECHANICAL_INTEGRATION_DIAGNOSTIC_V1.json      54,990 bytes
producer sha256 b967c8954872fb7af9e13794da02ac672958356a79c2ee39f71096ae9a38ef0f
env      python 3.11.15, torch 2.7.0+cu128, CUDA available (RTX 3080 Laptop)
         device_used cpu, gpu_memory_bytes_used 0
wall     1,488.754 s   40 updates   10 microbatches x 2 views per update
```

| invariant | result |
|---|---|
| optimizer steps exactly once per update | **True** — sequence 1..40, every delta exactly +1 |
| EMA advanced on every successful step | **True** |
| max EMA residual | **0.0** exactly |
| online parameters moved every update | **True** — min max-delta 2.935e-04 |
| Adam first and second moments populated | **True** — 59/59 parameters, every update |
| all losses finite | **True** |
| **checkpoint restart reproduces uninterrupted run** | **True** — fingerprints identical, `c1f522a6…0c5db3` |
| protected-gradient gate affirmative | **40/40** |

Gradient gate, every update: `missing 0, nonfinite 0, exact_zero 0,
teacher_gradients 0`, with `max_abs_gradient` ranging 0.065887–0.189149 — so
gradients are present, finite, nonzero, and absent from the teacher.

Loss fell 1.988835 → 0.741762 (62.7 %) on synthetic tensors. Per the guard
above, that is gradient flow, not biology.

**The gate assertion was tightened after this run and before publication.** An
earlier version asserted only that the gate object `is not None`, which is close
to a tautology — it would pass on any returned object, including one reporting
dead gradients. It now requires the four counters to be zero and
`max_abs_gradient > 0`. The strict predicate was then evaluated against the 40
stored per-update gate records from this run: **40/40 affirmative, zero
failures.** The stored values are what the run actually produced; the strict
check is a re-evaluation of them, recorded here as such rather than presented as
having gated the run inline.

### Device honesty

`inactive_update_reference` documents itself as a *bounded CPU mechanics
harness*. It was run on CPU, the device it is written for, and the receipt
records `gpu_memory_bytes_used: 0` with that rationale. Forcing it onto CUDA
would have changed the method rather than repaired anything.

## 5. The authorization blocker — two independent gates

### Gate B1 — governance: the population registry

`docs/agent/JEPA_POPULATION_ACCESS_REGISTRY_V1_20260907.json`, `populations.reader_fit`:

```
current_state              : ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY
allowed_now                : [ "metadata-only planning",
                               "already-authorized bounded technical preflight",
                               "D1-A synthetic/u0-safe development when no real
                                 reader-fit expression is consumed" ]
forbidden_without_new_authority : [ ..., "new teacher training", ... ]
future_eligible_uses       : [ "healthy-teacher training corpus after separate
                               frozen training contract", ... ]
```

A real-data training diagnostic on `reader_fit` is **"new teacher training"**,
which is explicitly `forbidden_without_new_authority`. The registry names the
remedy: a **separate frozen training contract**. No such contract exists.

Note precisely what *is* permitted: synthetic/u0-safe development **when no real
reader-fit expression is consumed**. That is the clause §4 executes under.

### Gate B2 — code: the issuance function cannot be called

`src/sea_ad_jepa/v5/current_training_authority_v1.py` is, by its own docstring,
*the only current V5 schema allowed to carry `training_authorized=True`*. Its
issuance function `issue_training_authority_v1(...)` requires six inputs, and
validates every one:

1. `closure_v2` — a `V5_CURRENT_AUTHORITY_CLOSURE_V2` whose roots match
   `CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2` exactly;
2. `preexecution` — a `CurrentTrainerPreexecutionAuthorityV2` bound to that closure;
3. `receipt_v2` — a current teacher-target receipt, validated against
4. `expected_target_package_root` — **a frozen teacher-target package**;
5. `critical_test` — critical-test authority, digest-matched to the closure roots;
6. `runtime_source` — runtime-source authority, digest-matched to the closure roots.

The binding constraint is (4): **the teacher-target package is not frozen.**
`START_HERE.md` lists teacher-target semantics first among current blockers, and
`issue_training_authority_v1` cannot produce a valid receipt against a target
package root that does not exist. The function is fail-closed and will raise.

**This is the correct behaviour and I did not work around it.** The instruction
was explicit that a diagnostic must not be authorized by modifying or bypassing
a failed gate, and the failure mode here is exactly the one the gate exists to
prevent: running a teacher whose target semantics are still open, then
discovering the estimand was wrong afterwards. That is the same class of failure
the GSE301119 matched-NT null demonstrated concretely — two faithful
implementations of an unfrozen estimand agree perfectly and are both wrong.

### What would unblock it

Both gates, in order, and neither is mine to issue:

1. **Freeze the teacher-target package** and record its root, so `receipt_v2`
   can validate. This is a scientific decision about target semantics, not an
   engineering step.
2. **Issue a named frozen training contract** for `reader_fit` scoped to a
   development diagnostic — naming the candidate, the masking configuration,
   the update budget, and the prospectively recorded DEVELOPMENT scoring — so
   that `reader_fit` moves out of `ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY` for
   this one bounded purpose.

Once both exist, the remaining engineering is the single FULL104→harness adapter
named in §2.

## 6. Self-audit findings this cycle

Findings about **my own** work and this machine, which the external audit did not
raise. Numbering continues the existing series.

| | finding | status |
|---|---|---|
| **S8** | I read the three failing freeze audits as byte drift and nearly reported the teacher/student seam as broken. The current freeze is **V4** and passes with 0 failures; V1–V3 are superseded. Checking which baseline the design targets, before calling a deviation a defect, changed the verdict completely. | **corrected before reporting** |
| **S9** | The designated project CUDA environment `sea-ad-jepa` has a **broken numpy BLAS**: every matmul crashes with Windows fatal exception `0xc06d007f`, including a 3x3, while torch matmul is fine. This crashed the V5 suite mid-run. The healthy environment is `sea-ad-jepa-v3` (numpy 2.4.6, torch 2.7.0+cu128, CUDA available). **Any prior result produced in `sea-ad-jepa` that used numpy linear algebra should be re-checked.** | **open — environment defect, recorded not repaired** |
| **S10** | `test_teacher_student_integration_freeze_v1/v2/v3` fail permanently rather than declaring supersession. A test that can only fail trains readers to ignore failures and would mask a real V4 regression in the same file set. | **open — test hygiene** |
| **S11** | `scripts/v4/contextual_target_f1_preflight_core_v1.py` imports POSIX-only `resource` and cannot be collected on Windows, so its test never runs here. A preflight that cannot execute on the execution machine is not a preflight. | **open** |
| **S12** | The existing harness unit tests pass `ema_momentum=.996` as a fixture argument. That is legitimate for a fixture, but it means the historical constant is still present in the tree and could be copied into a real run by anyone reading the tests as an example. The diagnostic deliberately uses 0.99 so that inheritance is visible. | **mitigated in the diagnostic, noted in the tree** |

## 7. Status classifications

```
COMPLETED_AND_PHYSICALLY_EXECUTED : V5 suite zero-skip census (1,617 passed / 0 skipped / 3 superseded-failing)
                                    Integration freeze audit V4 (PASS, 0 failures)
SYNTHETIC_TESTED_ONLY             : bounded mechanical integration diagnostic, 40 updates
INDEPENDENTLY_REPRODUCED          : none claimed in this lane
DEVELOPMENT_RESULT                : none - no real reader_fit data consumed
SCIENTIFICALLY_QUALIFIED          : none
BLOCKED_BY_AUTHORIZATION          : real-data reader_fit diagnostic (gates B1 and B2)
NOT_EXECUTED                      : FULL104 -> harness adapter (deliberately not built)
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
