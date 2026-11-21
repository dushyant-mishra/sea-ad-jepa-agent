# Action correction after verifying original six-IPB planted JEPA training (2026-11-03)

Canonical [audit #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) latest source-pinned commit `296961b4ea6f92988291d7d155ec0b66ee158310`, **44 events**, original validation must be checked. [Live #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460) retains current handoff. Read #322 `docs/agent/JEPA_20261103_PRIOR_PLANTED_IPB_JEPA_AND_EMA_EXPERIMENT_NO_REPEAT_CORRECTION.md` and machine `results/target_discovery/unified_qualification_v1/JEPA_20261103_ALREADY_TESTED_SIX_IPB_PLANTED_EMA_NO_REPEAT_V1.json`.

## STOP generic V65→V5 model pilot: historic same-backbone experiment executed

The owner required proof this had not been tried before. Deeper direct source archaeology shows it **had been done substantially**:

- Original Stage81A3 `stage81a3_synthetic_geometry_escape.py`: **10 × 500** actual self-supervised JEPA/EMA training runs on two 8,192-cell/4,096-gene/32-factor planted worlds; all 10 **failed** biological-factor/geometry tests while JEPA MSE fell >99%.
- Original `stage81a3_ema_bootstrap_disambiguation.py`: another matched **10 × 500** runs with faster EMA `.996`, did not rescue geometry. Original `stage81a3_final_information_preservation_qualification.py`: improved attention/PCA but **S2–S7 and geometry failed**, masked factor R² negative in all 10.
- Crucial **near-exact existing six-token-preserving-block model**: `scripts/v4/stage81a3_ipb_jepa_feasibility.py` really instantiated `IPBEncoder(width=160, blocks=6)`, `BlockPredictor` and EMA on candidate-agnostic 4,096-gene planted synthetic biology under 500-step training; two fixtures × two seeds × IPB-JEPA vs anchor-only = **eight prescribed trajectories**. Its actual historical report `results/v4/stage81a3_ipb_jepa_feasibility.json` has **SHA-256 `aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308`**, matched independently in the preserved `docs/history/preservation_20260902/results/v4/stage81a3_context_evidence_audit.json` and bound in Stage81A3R freeze. **Exact numeric outcome should be read from existing GPU laptop receipt, not invented or re-run.**
- Historical Stage81B `JEPA_ONLY/CURRENT/ANCHOR_ONLY` 500-update causal controls already closed the hidden gene/CELL anchor as harmful; preserved `docs/agent/archive/governance/ACTIVE_STATE_20260903_HISTORICAL.md` and DEC-001.
- V65 5,200-cell supervised planted factor recovery and supervised 120-step EMA, V65/V67 negatives, V77 canonical guarded tiny update, #336 relational truth 9/9, PR536 2/2 negative admission are all done. V5 keyed source shares the **same six-block token-preserving IPB architecture** as historical v4.1 and primarily adds keyed dropout, exact donor/operator packing and guarded state; a new **reduced** width32–64, 96-gene short pilot would be a weaker repetitive test, not a novel model.

## Do now instead

**Macha / GPU source custodian:** Find the existing `results/v4/stage81a3_ipb_jepa_feasibility.json`, verify SHA-256 exactly `aa949f23…c449308`, and report its original terminal classification, paired JEPA-vs-anchor outcomes, masked/full factor R² and geometry without any new simulation, training or reinterpretation. If file genuinely absent, record archival-status limitation without rerunning it.

**GPT:** Use that exact result plus already completed JEPA_ONLY/anchor and T0/T1/TCTX target comparisons to define a genuinely outcome-changing next test: actual **C2 broad/mesoscale learned teacher relations or C3 multi-query non-q measured biological target**, source-bound lawful partial student, matched wrong-cell/wrong-q/technical/control truth and independent hidden controller adjudication through original producer/gates, **only where prior experiments did not do this**. The PR328 48-address world is not 3×512 PR316 and original C3 truth is a population mean, not R5's per-cell eight vector. Do not generate a fresh candidate-shaped plant or silently change frozen science.

**Additional gotcha:** V65 `Xr` is normalized by full same-cell RNA library *before* masking; masking those already-normalized scalars leaks hidden count information through visible values. Any future model using that source must use an explicitly lawful independently computed partial-view normalization. This is not a reason to rerun the generic model.

No model fitting, source mutation or GPU task launched with this no-repeat correction. No claim that current main contains the historical exact IPB numeric report. Preserve original negative evidence, exact code semantics and audit #322 chronology event44.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
