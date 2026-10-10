# V79 Detection Localization Remote Execution Contract

Date: 2026-10-09
Status: EXECUTION CONTRACT / TRAIN-ONLY / NON-TRAINING / NON-PROMOTING

## Purpose

Execute the frozen V79 detection-geometry localization exactly once on the authenticated corrected S174 TRAIN substrate on the machine that physically holds the repaired shard cache. This contract does not authorize JEPA training, checkpoint generation, V78 retuning, TEST/Morabito access, target discovery, pathology use, E4, or Stage4/500K.

## Frozen lineage

- V78 scientific baseline PR: `#242`
- Required V78 base head: `e959d9a732698ae9a41e8cb1f6c10052d7390326`
- V79 implementation branch: `design/v79-detection-localization-20261009`
- The execution machine must check out the latest reviewed head of that branch and run from a clean tracked state.

If PR #242 no longer points at the exact required V78 head above, STOP. Audit only the commits after that SHA and require fresh V78/V77 CI before using a later baseline.

## Required authenticated inputs

### E2 reference

Repository path:

`results/v77/V77_CLASS_PROPAGATION_TOURNAMENT_V1.json`

Required semantics:
- schema `V77_CLASS_PROPAGATION_TOURNAMENT_V1`
- seed `7302`
- cells `2500`
- class authority SHA-256 `a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014`
- evaluation universe SHA-256 `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`

### Operator bridge

Repository path:

`results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`

This is the only source for shard→operator/source identity. Never infer operator identity from `source_library`.

### Corrected S174 cache

Extracted runtime directory recorded by the frozen corrected-universe custody:

`D:/Jepa project/data/cache/s174_rebuilt_real_train_v1`

It must contain the 42 repaired `.counts.npz` shards and 42 paired `.meta.npz` shards authenticated by the existing V78 gate.

The custody archive remains:

`/Jepa project/s174_rebuilt_real_train_v1.rar`

SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

The driver consumes the extracted directory, not the RAR archive.

### Repaired marginal authority

Canonical file:

`/Jepa project/V78_MARGINAL_AUTHORITY_REPAIRED_V1.json`

Expected SHA-256:

`997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`

On the Windows execution machine this is expected to be under the `D:/Jepa project/` project root; verify the actual path and hash before execution rather than moving or regenerating it.

### Frozen evaluation-universe bytes

Historical authenticated path:

`D:/jepa_v77_synthetic_custody_20261005/s174_replay/frozen_evaluation_universe.npz`

Required SHA-256:

`e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`

Required name:

`TRAIN_PREVALENCE05_19569`

Required size:

`14,417` canonical addresses.

The V79 driver authenticates the actual NPZ bytes through the frozen V77 `load_universe` function before using them. A receipt that merely quotes this hash is not sufficient.

## Pre-run checks

1. `git status --porcelain` must show no unintended tracked modifications.
2. Verify PR #242 still points at `e959d9a732698ae9a41e8cb1f6c10052d7390326`.
3. Verify the V79 implementation branch/head is the reviewed head intended for execution.
4. Verify the repaired marginal authority SHA-256.
5. Verify the frozen evaluation-universe NPZ SHA-256.
6. Verify the extracted corrected cache contains all 42 `.counts.npz` and all 42 matching `.meta.npz` shards.
7. Do not regenerate, repair, coarsen, or substitute any input after this point.

## Exact execution

From the repository root in Windows `cmd.exe`:

```bat
python scripts/v79/run_v79_detection_localization.py ^
  --e2-reference results/v77/V77_CLASS_PROPAGATION_TOURNAMENT_V1.json ^
  --operator-bridge results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json ^
  --marginal-authority "D:/Jepa project/V78_MARGINAL_AUTHORITY_REPAIRED_V1.json" ^
  --corrected-cache-root "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1" ^
  --evaluation-universe-npz "D:/jepa_v77_synthetic_custody_20261005/s174_replay/frozen_evaluation_universe.npz" ^
  --out results/v79_localization
```

If the canonical repaired-authority file is physically elsewhere, replace only that path after verifying its SHA-256 equals the required value above. Do not substitute a different authority.

## Fail-closed behavior

The driver writes the preexecution-gate receipt first and then refuses scientific execution unless the delegated V78 custody gate is `READY` with zero blockers.

It additionally refuses:
- evaluation-universe receipt mismatch;
- class-authority mismatch;
- any training-authorized contamination;
- missing or digest-invalid repaired shards;
- missing paired metadata;
- actual evaluation-universe NPZ byte/hash/name/length mismatch.

A blocked run is an expected safety result. Do not bypass or edit a blocker after seeing any localization output.

## Required outputs

A successful authenticated run must create exactly these scientific receipts under `results/v79_localization/`:

- `V79_DETECTION_LOCALIZATION_PREEXECUTION_GATE_V1.json`
- `V79_DETECTION_LOCALIZATION_CANONICAL_V1.json`
- `V79_DETECTION_LOCALIZATION_SENSITIVITY_V1.json`
- `V79_DETECTION_LOCALIZATION_RULING_V1.json`

All outputs are descriptive only.

The canonical/sensitivity/ruling artifacts must remain non-authorizing:

- `training_authorized: false`
- `v78_retuning_authorized: false`
- `synthetic_arm_promoted: null`

The ruling must not claim a unique causal winner without the separate Bayesian uncertainty authority.

## After execution

1. Do not rerun with changed thresholds, strata, support rules, genes, or fallback rules after viewing results.
2. Audit the gate and all four receipts for custody, identity leakage, support/fallback behavior, and non-authorizing flags.
3. Confirm L5/ruling export no gene IDs, gene names, selected positions, registry IDs, or edge-pair identities.
4. Commit the exact receipts without post-outcome edits.
5. Only after audit, interpret the L0→L4 localization path to choose a prospective V79 mechanism family.
6. Macha Bayesian geometry may then be compared prospectively, after its independent custody/leakage/identity-scrubbing audit. It cannot retroactively alter V78 or this frozen localization run.

## Hard stop

This execution does **not** authorize JEPA synthetic training or checkpoint generation. A future V79 synthetic mechanism must first be designed prospectively from the localization evidence, implemented, and scientifically qualified before synthetic JEPA training can be reconsidered.
