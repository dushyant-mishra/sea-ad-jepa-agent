# V5 next checkpoint step: read-only model + complete Adam state audit (NO OPTIMIZER STEP)

**Scope:** This is a *narrow checkpoint component preflight*, not a qualified full training checkpoint. The new module `scripts/v5/jepa_v5_full_state_readonly_audit_v1.py` inspects already-existing CPU PyTorch states, serializes a structurally verified snapshot, and verifies SHA-256 + `torch.load(weights_only=True)` on read. It exposes NO optimizer `step`, trainer, or model restore call.

## Why it is needed

The existing V5 inactive reference `src/sea_ad_jepa/v5/inactive_update_reference.py` has a `V5ReferenceCheckpoint` containing online, teacher, predictor, optimizer, scaler and presentation cursor, but its helper `_optimizer_step_scalar` can return a valid-looking count even when optimizer moments for other parameters are completely **missing**. Matching a single counter is not an exact restart test.

The new independent audit checks:
- All `online` and `predictor` *trainable tensors*, including `value_encoder`, occur **exactly once** in AdamW parameter groups; teacher is frozen and has no gradients.
- At u0, optimizer state is empty. At any u>=1, **every trainable parameter** has exactly one `step`, `exp_avg`, and `exp_avg_sq` entry. The per-parameter steps equal the declared completed-update count, moments have correct tensor shape, dtype and finite values; second moments are nonnegative; missing, wrong, reordered or duplicate named IDs refuse.
- The saved optimizer parameter IDs are bound to specific `online.` and `predictor.` tensor names, shapes and dtypes, rather than silently relying on positional `load_state_dict` mapping.
- Teacher, predictor and online state dicts are included as cloned CPU tensors, along with optimizer group hyperparameters, CPU RNG bytes, explicit keyed Philox seed, EMA/presentation counts and exact gene-axis, frozen panel, source, rights and config SHA commitments.
- The snapshot refuses any attempt to set training or execution authority. Safe loading requires a pinned SHA-256 of the bytes. An altered file or missing/mutated Adam state refuses before any model can be restored.

The tests create tiny fake untrained CPU `torch.nn` models and **manually populate** synthetic optimizer moments. They *explicitly prohibit* calling `optimizer.step()`, forward propagation or training. This does not constitute execution of the V5 update. PyTorch is installed only for these read-only tests.

## Limits and next step

This is not yet complete V5 checkpoint serialization or exact resume. It lacks masking RNG generator state, Python/NumPy and optional CUDA RNG, AMP scaler support, actual data iterator/presentation cursor authority, source/rights content authentication, model-class/version binding, genuine optimizer-step evidence, gradient observations, EMA arithmetic, and the state-to-panel collapse witness. The SHA hashes are supplied bindings, not external independently trusted attestations. A full model restore and bitwise replay RT1–RT8 would require explicit owner authorization for **synthetic optimizer steps**. Passing this preflight proves only inspection completeness of the provided CPU states and artifact structure.

The new work is stacked on V2 [PR #570](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/570) but does NOT modify its journal, its original Macha REDs (#557/#560/#561/#566/#567), or any source/target qualifications. Full integration of this serializable component into journal V2, plus live physical measurements for all trainable tensors and fixed panel biology controls, remains a separate reviewed task.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
