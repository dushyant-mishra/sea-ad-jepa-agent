# Lane C — PR #144 masking-runner regression: root cause, classification, repair

**Status:** repaired via a versioned successor binding. The original frozen record
is unmodified. Nothing here authorizes Audit-B execution or training.

**Lane:** `lane-c/v29-masking-regression-repair-20260926` - PR #169, based on the
PR #144 branch `review/v26-g3-explicit-streaming-attacker-integration-20260926`
rather than on `main`. That is the true parent of this repair, and it is also the
only base that merges cleanly: the PR #143/#144 stack currently conflicts with
`main` in `START_HERE.md` and `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, two
files this lane did not touch and must not resolve on another lane's behalf.

`TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF`

---

## 1. Verdict first

This is **good news**. The workflow went red because an integrity check did
exactly what it was built to do, and the thing it caught turned out to be a real
but harmless code change. Nothing scientific is invalidated, no result is in
doubt, and the Audit-B target sample is provably the same sample it always was.

* **Classification: (a) LEGITIMATE_VERSION_CHANGE.**
* The five failures were all one cause. Two of them were collateral — a
  different gate's refusal was being hidden behind this one.
* The frozen planner's *default* behaviour is unchanged, and that is established
  by running both versions and comparing every number, not by reading the diff.
* The fix is a **new, versioned successor binding**. The original frozen digest
  `143645becff6…` is still recorded, still authoritative for what was frozen, and
  still verified by its own test.

What this did **not** change: the frozen target sample, the escalation ladder,
the precision criterion, the execution prohibition, or any of the other six bound
inputs. Audit-B remains unexecuted and unauthorized.

---

## 2. What broke

The failed run is hosted CI
[36208393701](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36208393701)
on PR #144 head `21efb1047c73cfe7b88047f0aeee1978b035971f`: **5 failed, 826 passed**.
Reproduced locally on the canonical environment, byte-for-byte the same verdict:
**5 failed, 826 passed** (`BASELINE_masking_runner_at_21efb104.txt`).

`AUDIT_B_FROZEN_TARGET_SAMPLE.json` records the SHA-256 of seven files whose
change would alter what the frozen sample means. One of them drifted:

| role | recorded | observed |
|---|---|---|
| `planner_source` (`src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`) | `143645becff6…` | `de2f019e2867…` |

The other six were byte-identical. That single mismatch produced all five
failures:

| # | test | nature |
|---|---|---|
| 1 | `test_v5_audit_b_frozen_target_sample_v1.py::test_bound_digests_still_match_the_repository` | direct |
| 2 | `test_v5_audit_b_execution_preflight_v1.py::test_real_frozen_sample_bound_inputs_match_current_checkout` | direct |
| 3 | `test_v5_audit_b_execution_contract_builder_v1.py::test_default_builder_is_content_addressed_but_execution_forbidden` | direct |
| 4 | `test_v5_audit_b_execution_contract_builder_v1.py::test_builder_rejects_phase_i_v1_receipt` | **collateral** |
| 5 | `test_v5_audit_b_execution_contract_builder_v1.py::test_builder_rejects_rng_v2` | **collateral** |

Tests 4 and 5 are negative tests. They assert the builder refuses *and* refuses
for a named reason — `"qualification V2 is required"`, `"RNG authority V3 is
required"`. The builder did refuse, but for the planner drift, which runs
earlier. Their own gates were never reached. This **gate-masking** effect is
worth naming: a suite in this state reports the wrong cause, and a reader would
conclude three separate subsystems were broken rather than one.

---

## 3. Root cause

Commit `65ff187c9668cf0af28056222fde897380929141`, *"feat(g3): explicit opt-in
fit masses in primary ridge and RIDGE8; preserve historical default"*, on PR #144.

It is the only commit touching the planner between PR #143
(`8776d27384a1543bb6716ad724eb2a521fb7c4ac`, where the file still hashes to
`143645becff6…`) and PR #144 head.

The whole PR is four files and **zero deletions**:

```
55 +  .github/workflows/v26-g3-streamed-attacker-integration.yml
38 +  docs/agent/JEPA_V26_G3_STREAMED_ATTACKER_INTEGRATION_20260926.md
39 +  src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py   <-- the only bound input
92 +  tests/test_v26_g3_streaming_attacker_integration_v1.py
```

The 39 added lines thread an **opt-in** attacker-fit objective through
`_fit_ridge_weights`, `_ridge_primary_score`, `_ridge_partners`,
`run_primary_fold_streaming` and `run_all_primary_folds_streaming`. Every new
behaviour sits behind `if fit_objective is not None` / `if g3_fit_objective is
not None`, and every new parameter defaults to `None`.

---

## 4. Classification: (a) LEGITIMATE_VERSION_CHANGE

Not (b) UNINTENDED_MODIFICATION:

* one commit, with a message describing precisely this change;
* PR #144's description documents it in detail, including which entrypoints it
  threads through and why;
* it ships with its own 92-line test file and its own CI workflow, both green
  (hosted run 36208393845: 50 passed, 0 skipped);
* zero deletions anywhere in the PR. An accidental edit does not arrive with a
  workflow and a test suite.

Not (c) SEMANTIC_CHANGE:

The planner can now compute a second thing, but only when explicitly asked, and
nothing in the Audit-B path asks. Under Audit-B's calling convention the numbers
are **bit-identical**. That is measured, not inferred:

`analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/PLANNER_DEFAULT_PATH_EQUIVALENCE_V1.json`

* the frozen implementation was recovered from git blob `083bd8aa` and
  re-verified to SHA-256 `143645becff6…` before being imported;
* both implementations ran over three authenticated stream geometries
  (12×4×8/3 folds/2 sources, 16×6×11/4/3, 20×3×9/4/2);
* **88 emitted rows, 22 per-fold row sets and 22 `_ridge_partners` calls compared
  bitwise** — float equality on the hex representation, no tolerance;
* zero differences.

Supporting static evidence:

* `g3_explicit_attacker_fit_objective_v1` is import-pure — constants and function
  definitions only — so the added import has no effect on the default path;
* no name in it collides with anything the planner already defined;
* `audit_b_n1_cached_planner_v1`, `audit_b_n1_crossfold_planner_v1` and
  `audit_b_mask_plan_generator_20260920` contain no occurrence of
  `fit_objective`, enforced by a static test.

### The residual risk a hash bump would have missed

A byte digest used to pin behaviour, because the file did one thing. It now does
two, selected at call time. **A digest alone no longer pins what the planner
computes.** So the successor record additionally pins the execution mode:

```
required_execution_mode.g3_fit_objective = "MUST_BE_ABSENT__HISTORICAL_DEFAULT_PATH_ONLY"
```

---

## 5. The repair — a successor, never an edit

**The original frozen record was not touched.** `AUDIT_B_FROZEN_TARGET_SAMPLE.json`
still records `143645becff6…`, still carries freeze digest
`c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac`, and that
digest is still pinned by `PHASE_IV_SAMPLE_FREEZE_DIGEST`. The original planner
bytes are preserved verbatim in-repo as
`evidence/frozen_planner_source__143645be.pysrc` (SHA-256 `143645becff6…`,
deliberately not a `.py` file so nothing imports or collects it by accident).

New artifacts:

| artifact | role |
|---|---|
| `evidence/phase_iv/AUDIT_B_BOUND_INPUT_SUCCESSOR_V2.json` | the versioned successor binding |
| `src/sea_ad_jepa/v5/audit_b_bound_input_successor_v2.py` | its validator + pinned digest |
| `src/sea_ad_jepa/v5/planner_default_path_equivalence_v1.py` | the executed equivalence check |
| `evidence/PLANNER_DEFAULT_PATH_EQUIVALENCE_V1.json` | its receipt |
| `evidence/FREEZE_EXECUTION_ADVERSARIES_V1.json` | planted-failure receipt |

### Why this is a stronger gate, not a weaker one

`verify_phase_iv_sample_freeze` gained one optional argument that defaults to
`None`. **With no successor, behaviour is exactly what it always was: any drift
is a refusal.** A successor does not widen what is accepted; it permits one named
role to move from one exact digest to one exact digest, and it must clear every
one of:

1. its own canonical digest equals a constant pinned in code;
2. it descends from the pinned parent freeze digest;
3. the parent freeze artifact is still byte-identical;
4. `from_sha256` equals what the freeze recorded and `to_sha256` equals what is
   observed *now* — so the waiver expires the instant the file moves again;
5. `from_sha256 != to_sha256` — no rubber-stamping the status quo;
6. classification is `LEGITIMATE_VERSION_CHANGE`. `UNINTENDED_MODIFICATION` and
   `SEMANTIC_CHANGE` are recordable but **non-authorizing** — explanations, not
   permissions;
7. a written rationale, not a label;
8. a cited equivalence receipt that exists, matches its recorded digest, reports
   `equivalent: true`, and compares *those exact two* digests;
9. **sample identity** — N1/N2/N3 re-derived from the parent's salt and the
   parent's unchanged target universe must be identical to the parent's recorded
   targets. Verified: `2c39b45ae150…` both ways, prefix ordering re-checked. A
   re-rolled sample cannot be rescued by any successor;
10. it may cover only roles that **actually drifted** — a waiver written ahead of
    time to be cashed in later is rejected;
11. it authorizes nothing else: execution, training and outcome access all False,
    and `audit_b_n1_burden_outcomes_opened` is cross-checked against
    `AUDIT_B_PREEXECUTION_STATUS_V1.json`.

One further hardening: the builder now resolves the successor record relative to
`--repo-root` rather than to the module's own repository, so a mirror or
alternate checkout cannot silently inherit a waiver that does not live in it.

---

## 6. Planted failures against this path

`FREEZE_EXECUTION_ADVERSARIES_V1.json`. Every case names the refusal it must
produce and measures the state afterwards — an exception is evidence that control
left the function, not that nothing was written.

| adversary | exact refusal point | state changed |
|---|---|---|
| silent hash bump of the frozen record | `Phase-IV sample freeze internal digest mismatch` | none |
| hash bump + recomputed internal digest | `runtime uses a different Phase-IV sample freeze` | none |
| planner moves again after the successor | `successor binding planner_source authorizes de2f019e… but the checkout contains 6cf332f4…` | none |
| successor waives an untouched role | `supersedes bindings that did not drift … may not pre-authorize a future change` | none |
| builder sees drift, no successor present | `Phase-IV bound input drift for planner_source: expected 143645be…, observed de2f019e…` | none |
| heavy qualification V1 (gate-masking check) | `exhaustive heavy-statistics qualification V2 is required` | none |
| RNG authority V2 (gate-masking check) | `pre-panel masking RNG authority V3 is required` | none |
| tampered sample membership | `Phase-IV sample freeze has an invalid internal digest` | none |

"State changed" is measured over: the contract artifact the builder would emit,
`AUDIT_B_FROZEN_TARGET_SAMPLE.json`, `AUDIT_B_BOUND_INPUT_SUCCESSOR_V2.json`, the
equivalence receipt, the live planner bytes, the preserved frozen planner copy,
and the absence of any `*optimizer*`, `*ema*`, `*cursor*`, `*checkpoint*`,
`*.ckpt`, `*.pt` or `COMMIT.json` artifact. All eight: unchanged, no artifact
written, no training-side state created.

**Positive control:** the builder still *succeeds* on good inputs (returncode 0,
artifact written, `phase_iv_sample_freeze_digest = c2c5e1b5…`,
`execution_authorized: false`, `precision_scope_id:
UNRESOLVED__EXECUTION_FORBIDDEN`). Without it, a builder that refused everything
would satisfy all eight adversaries and be useless.

The last two rows are the gate-masking regression turned into a standing test:
each downstream gate's own refusal must stay reachable.

---

## 6b. Regression results

Complete affected suite = all **106** test files invoked by
`.github/workflows/v5-full104-masking-runner.yml`, run on the canonical
environment (`C:/Users/dushy/anaconda3/envs/sea-ad-jepa/python.exe`, Python
3.11.15, numpy 1.26.4, scipy 1.15.3, `Library/bin` on PATH).

| run | files | passed | failed | skipped | xfailed | xpassed | deselected | errors |
|---|---|---|---|---|---|---|---|---|
| baseline, PR #144 head `21efb104` | 103 | 826 | **5** | 0 | 0 | 0 | 0 | 0 |
| hosted CI 36208393701, same head | 103 | 826 | **5** | 0 | 0 | 0 | 0 | 0 |
| after repair, before adversaries | 105 | 904 | 0 | 0 | 0 | 0 | 0 | 0 |
| **final, complete suite** | **106** | **924** | **0** | **0** | **0** | **0** | **0** | **0** |

The local baseline reproduces the hosted failure exactly, so the repair is
measured against the same 826/5 starting point rather than a subset. The final
run is the whole workflow list, not a focused selection; `-rs` emitted no short
summary, which is why every non-passed column is zero. The workflow's separate
"fail closed on skips" step is satisfied for the same reason.

Wall-clock times are not comparable between these runs: the machine was running
other lanes' work concurrently. The counts are the measurement.

---

## 7. Evidence class

**PHYSICAL** — real repository bytes, real git history, real executions:

* every SHA-256 in this report, computed from the actual files;
* the git history isolating `65ff187c` as the sole planner change;
* recovery of the frozen implementation from blob `083bd8aa`, re-verified to
  `143645becff6…`;
* the local reproduction of the CI failure (5 failed / 826 passed) and the
  post-repair suite, both on the canonical environment;
* the sample-identity re-derivation, which reads the real 17,053-target
  eligibility receipt and the real frozen sample;
* `AUDIT_B_PREEXECUTION_STATUS_V1.json` confirming N1 outcomes unopened.

**SYNTHETIC** — constructed fixtures:

* the three stream geometries in the equivalence check. They prove *implementation
  equivalence*, a statement about code, and are the right instrument for it: two
  implementations that agree bitwise on structured input agree because they are
  the same computation. They are **not** evidence about FULL104 biology, and no
  FULL104 expression was read;
* the heavy-qualification and RNG fixtures the builder adversaries feed in;
* the mutated successor records in the negative tests.

No claim here rests on synthetic data alone: the classification rests on git
history plus a bitwise execution comparison, and the freeze integrity rests
entirely on physical digests.

---

## 8. Open items for the PR #144 owner (not actioned by this lane)

1. **A development-only feature now lives inside a frozen execution artifact.**
   The alternative — a successor module wrapping the frozen planner — would have
   kept the binding intact at the cost of duplicating
   `run_primary_fold_streaming`. Threading it through the real function is
   defensible and is what PR #144 chose; this lane repaired the binding rather
   than overruling that design. It is worth an explicit decision for next time.
2. **Gate-masking is generic.** Any fail-closed chain where an early gate can
   hide a later one's refusal will mis-report its cause. The two reachability
   tests added here cover this chain only.
3. The successor pins `g3_fit_objective` as absent for Audit-B, but nothing yet
   *enforces* it at the Audit-B entrypoints beyond a static source check. If
   Audit-B ever gains a configurable planner call, that pin needs a runtime
   assertion.
