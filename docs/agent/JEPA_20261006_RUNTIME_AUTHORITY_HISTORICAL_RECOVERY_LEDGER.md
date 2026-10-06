# JEPA runtime / authority historical recovery ledger — 2026-10-06

Purpose: prevent repeated loss of completed work caused by overloaded version labels, branch drift, renamed authority layers, and local work living outside the current default branch. This is a custody/governance record only; it does not authorize training or qualify new biology.

## Version axes — do not collapse these

The repository uses several independent version families:

1. **Project milestone**: V61, V64, V75, V77, etc.
2. **Teacher/student runtime generation**: V4 -> V5.
3. **Training-authority object generation**: separately versioned.
4. **Authority-root graph generation**: separately versioned.
5. **Optimizer/guard and checkpoint schema generations**: separately versioned.

A project milestone number is not a trainer-generation number. Never infer runtime authority from a `Vxx` project label alone.

## Recovered teacher/student runtime lineage

The most advanced teacher/student JEPA runtime generation positively recovered so far is **V5**, not V4.

Direct evidence:

- `.github/workflows/teacher_student_v5_data_first_audit.yml` runs the frozen V4 active suite unchanged, then a distinct exact V5 active suite, then compiles `src/sea_ad_jepa/v5/*.py`.
- `.github/workflows/v5-runtime-closure.yml` exists on the V64-era lineage and exercises the V5 runtime closure rather than defining a new V6 trainer.

Working lineage:

`teacher/student V4 -> V5 data-first successor -> V5 runtime-closure hardening -> later V61/V62/V64 q-safety / authority / anti-cheat / optimizer / checkpoint hardening -> V72-V77 measurement, synthetic and scientific qualification work`

No clean post-V5 `V6 trainer` successor has been positively identified in the audit so far. This is an evidence statement, not proof that no such historical artifact can exist.

## Recovered local-only work now on origin

Macha performed a local scan across branches, ~80 worktrees and stashes. The genuinely unpushed work was preserved without rebasing or rewriting:

- `f1-real-production-executor-20260904` @ `f1b591613d0a593cc49e7765845aa36b12c1ae01` — 8 commits.
- `claude/v5-phase4-preexecution-redteam-20260921` @ `d5ab33b337b50ac1b90bdac9ea239018cfea6cb7` — 1 commit.
- `custody/local-only-jepa-recovery-20261006` @ `c86dac574bdf99f228d3e2040673855c701b10c4` — custody commit containing the genuinely local-only recovery set / manifest.

The three F1 nuisance-authority sources (`derive -> finalize -> validate`, dated 2026-09-02) are historical scientific evidence pending audit, not current target authority and not runtime authority.

Only `critics/observation_provenance_adversarial.md` was genuinely local-only among the initially suspected documents. `REAL_PRODUCTION_FORWARD_TARGET_GATE.md`, `FULL104_PHASE2_STATE_DERIVATION.md`, and the referenced superpowers plan were already reachable on origin.

The contextual-teacher reference packet is 24 files / 81,955 bytes, not 24 MB; the larger earlier number was NTFS allocation reporting. It is forensic/reference material, not current authority.

## F1 production executor — what it is and is not

The 8-commit `f1-real-production-executor-20260904` branch is a bounded executor / verification workstream, **not a neural trainer**.

Its independent validator explicitly checks that the executor has no `.backward()`, `optimizer.step()`, `ema.update()`, or `.train()` surface.

Reusable patterns:

- fail-closed launch authorization before production;
- exact remote-Git-bound external authority bytes;
- implementation/source/contract byte binding;
- independent validator reconstructing claims rather than trusting producer PASS fields;
- private-output and outcome-blindness guards;
- interruption/resume parity by semantic root and final bytes.

Do not use this branch as evidence that current JEPA optimizer/EMA mechanics are already wired.

The useful launch/resume hardening commit is `f1f14fdbe461c66951ec707e7ee4b3783fe14c10`.

## Phase-IV pre-execution red-team — durable lesson

`claude/v5-phase4-preexecution-redteam-20260921@d5ab33b337b50ac1b90bdac9ea239018cfea6cb7` found `STOP__PREEXECUTION_DEFECT_FOUND`.

The most important reusable rule is:

> An authority/contract is not in force merely because its module and tests exist. The actual executor must consume and enforce it.

Historical example: RNG V3 existed and its own tests passed, but the frozen planner still accepted a free `global_seed`; the runtime had not actually consumed the new authority.

Additional durable findings:

- freezing samples without freezing the decision rule is insufficient;
- mutation tests must prove verdict-bearing fields move the bound digest;
- free string inputs such as `cell_key` can reopen hidden dependency channels;
- held-out/fold claims require executor-side consistency guards, not caller trust.

These are acceptance criteria for the current canonical-consumer audit.

## Old PROD41K/T1 checkpoint

`phase_e_restart_checkpoint.pt` and related PROD41K/T1 checkpoints are **forensic only**.

The terminal lineage audit found all 48 mandatory pre-attention tensors gradient-dead under the historical fp16 configuration while loss still fell. Therefore:

- they do not demonstrate healthy V5 neural training;
- they must not be promoted as runtime qualification;
- architecture/checkpoint structure may be inspected for forensics only.

## Current reconciliation target

Do **not** rebuild JEPA and do **not** merge an old project branch wholesale.

The current engineering target is to recover and reconcile:

`latest positively identified V5 neural runtime mechanics`
`+ newest compatible q-safe preprocessing`
`+ newest compatible training-authority object`
`+ newest compatible authority-root graph`
`+ newest compatible optimizer-step guard`
`+ current checkpoint/resume binding`

onto the current main/governance lineage.

Every component must be proven through the executable consumer call graph:

`41K reader -> q-safe views -> encoder -> predictor -> teacher -> loss -> backward -> training authority -> optimizer guard -> optimizer.step -> EMA -> checkpoint -> deterministic resume -> representation extraction`

Existence of a file or passing isolated test is not enough.

Current reconciliation audit branch: `reconcile/v64-runtime-authority-onto-main-20261006`.
Audit record commit for recovered V5 executor / red-team reuse: `8941d52d00f5c3fe869e5e5ba64c29499afd51d8`.

## Do-not-repeat / do-not-confuse

- Do not call the recovered current runtime “V4”; V5 is a real, separately tested successor.
- Do not assume a project milestone such as V64/V75/V77 names a trainer generation.
- Do not search indefinitely for a presumed `V65/V6 trainer` merely because project milestones advanced; no such clean successor has been positively identified so far.
- Do not merge V64 wholesale into current main.
- Do not mistake the F1 real-production executor for an optimizer/EMA training loop.
- Do not use the PROD41K/T1 checkpoint as evidence of healthy V5 training.
- Do not infer current authority from filename version alone; training authority, root graph, guard and checkpoint each have independent generations.
- Do not treat later V75/V77 measurement/synthetic/scientific work as proof of a new teacher/student runtime generation.
- Do not mark a new authority as active until its actual executor consumes it.

## Still unresolved — preserve uncertainty

The exact latest mutually compatible set of training-authority object, authority-root graph, optimizer guard and checkpoint schema is still being re-audited across later branches. Do not freeze a version number in a handoff until the actual producer/consumer chain is positively demonstrated.

Training remains OFF unless separately authorized by the current canonical authority surface.
