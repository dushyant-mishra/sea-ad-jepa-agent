# V5 structured CPU model/Adam preflight before V2 synthetic journal publication

**2026-11-05. Synthetic-only checkpoint-component integration; TRAINING OFF.** This draft is stacked on the owner's latest Sol #574 optimized V2 journal, which itself depends on #573 fork safety and Macha #572 crash/first-collapse fixes. It carries the exact unmodified read-only structural model and Adam validator source and original tests from #571, rather than reimplementing them.

## New isolated component

`scripts/v5/jepa_v5_structured_journal_preflight_v1.py` adds a preflight **before any attempt outcome bytes are written**. It accepts an existing serialized CPU `torch.save` checkpoint, verifies SHA and performs safe `torch.load(weights_only=True)` through #571's read-only validator. The bundle must contain named `online` (including `value_encoder`), `teacher` with matching tensor names/shapes/dtypes and `predictor` weights; complete per-trainable-parameter AdamW moment slots with matching ID/name/shape/dtype and step/EMA counters; CPU RNG and declared source/gene-axis, rights, config, panel, keyed Philox and seed; metadata must match the exact run ID and update index. Mutations or missing components are refused before creating a u0 run or writing a later `UPDATE_COMMITTED`.

The new bridge's `open_synthetic_journal` validates u0's empty Adam and caller-provided noncollapsed exact-state/panel probe before V2 publishes RUN_OPEN. `commit_synthetic_preflight` requires a pre-existing V2 ATTEMPT_BEGIN, validates the already supplied complete CPU component bytes plus the caller-reported no-exact-collapse probe, and only then calls V2 `commit_reported_update`. The bridge stores a process-local opening contract to guard inadvertent switching of gene-axis/source/Philox/seed between updates, in addition to #573's process+PID writer token; it never circumvents V2 journal or its crash recovery.

`inspect_stored_structured_snapshot` is read-only: it fetches SHA-linked opaque bytes by the V2 forensic reader and verifies the serialized components without reconstructing an executable model. It **cannot** authorize model loading, resuming, a next optimizer step or biological interpretation.

## Scientific distinctions and limits

- The tests fabricate tiny CPU modules and manually seed Adam moments with the number declared in metadata. No PyTorch forward, backward, optimizer.step, EMA update, GPU, human RNA or real training occurs.
- A structurally complete and SHA-valid file is **not proof that any optimizer update happened** or that the student is healthy; a self-reported `NOT_COLLAPSED_ONLY` probe remains caller-reported and not a physical fixed-panel measurement.
- The V2 disk run lock physically commits panel/config/rights; **gene-axis, source manifest, Philox contract and keyed seed are not independently sealed in V2's run lock**. The bridge requires matching external expected values and caches a session-local consistency contract; it does not claim cryptographic provenance.
- No masking/Python/NumPy/CUDA RNG, optional AMP scaler, exact batch iterator, physical gradient source, teacher EMA equation, identity-only/shuffled-expression controls, actual complete V5 class/version compatibility, RT1–RT8 or recovered executable model.
- CPU parsing of a 23MiB checkpoint adds a one-time state-validation cost; this adapter does **not** cause V2 to rehash all historical checkpoints every update. I/O efficiency #574 is under separate Macha review. No 205-update laptop benchmark is claimed.
- The existing immutable Macha RED files #557/#560/#561/#566/#567, original Macha #572 tests and Sol #573/#574 tests remain unchanged. All work stays in a new draft; independent Macha review required before scoped acceptance.

## Independent acceptance checklist

1. Check bad Adam slot and changed run ID/update/rights/source/gene-axis/seed/panel are rejected *before any state or telemetry is created*.
2. Check forked process cannot inherit the bridge's opener capability.
3. Confirm teacher/online tensor keys and shapes match, expression-value encoder cannot disappear, no false healthy label.
4. Check V2's original crash/prefix recovery and Sol's incremental I/O budgets still pass on the stacked branch.
5. Confirm expected external SHA bindings aren't misrepresented as trusted independent source evidence and no optimizer step is executed.

**Next actual implementation frontier:** a versioned real V5 checkpoint execution contract with all RNG/AMP/source provenance, a physically measured same-TRAIN-panel proof connected to each checkpoint and evidence-bearing last healthy state. RT1–RT8 optimizer replay needs explicit owner authorization. No merging/training/Stage4 promotion.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
