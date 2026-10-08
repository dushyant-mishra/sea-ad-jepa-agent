We are continuing the JEPA project. Do not restart from scratch.

Open START_HERE.md first, then docs/agent/JEPA_LATEST_HANDOFF_POINTER.json, then the V24 handoff and state.

Re-fetch all live GitHub heads before acting.

Hard boundaries remain:
TRAINING=OFF
AUDIT_B_N1=UNOPENED
PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED
RARE_TAIL_MOLECULAR=UNOPENED
THERAPEUTIC_RANKING=OFF

Current experimental head at handoff: PR #77 @ c81ad41b485f16d4aa82dbe4cffca5d23aa93927.
FULL104 PR #83 was merged into its parent at 64148023740d57777666faff15395262d4b0e3da but N1 is still unauthorized.

GSE178317 is DEVELOPMENT only. PR #102 is integrated: matched target/NTC lane support is required and lane spread is never biological uncertainty. No full physical V2 result was qualified at the audited head. PR #99 is stale; PR #100 is superseded.

Work next on GSE178317 V2 input binding/physical audit, benchmark donor/cell-line/barcode independence, real cross-study annotation authority, then pending physical V2 reruns. Do not open protected outcomes or training.
