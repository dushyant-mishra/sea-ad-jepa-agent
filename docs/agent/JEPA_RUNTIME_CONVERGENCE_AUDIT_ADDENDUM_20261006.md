# JEPA runtime convergence audit addendum — 2026-10-06

This addendum is binding for the PR #221 / PR #222 convergence audit. It supplements, and does not weaken, the prior full runtime self-audit and convergence contract.

## 1. Exact-head evidence rule

Do not trust earlier GREEN milestones from superseded designs. Historical GREEN results remain evidence only for the exact SHA/design they tested.

Superseded designs include:

- training-authority-shaped rehearsal objects created by flipping current V3 OFF booleans;
- caller-supplied optimizer-step counter/probe as completion proof;
- weaker checkpoint-lineage designs;
- governance validation that allowed same-shape scientific mutation.

Only current exact-head behavior counts for a current claim. PR #222 remains draft and is not approved runtime authority merely because its focused tests are green.

## 2. Scientific/runtime separation

Runtime convergence consumes scientific governance. It must not create scientific authority.

The runtime layer must not:

- choose the target;
- choose the representation;
- assign biological meaning to model width or coordinates;
- choose the estimand;
- choose deciding thresholds;
- open TEST;
- open Morabito;
- authorize Stage A, JEPA training, multimodal training, 500K, or Stage 4.

PR #220 on `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777` remains the controlling scientific/prefreeze governance.

## 3. `width=160` is architecture capacity, not biological dimensionality

`width=160` is network/token capacity only. It does not establish a 160-dimensional biological state and does not confer biological meaning on learned coordinates. Any later coordinate interpretation remains subject to the representation-stability governance frozen in PR #220.

## 4. The 41,238-address identity chain remains a separate hard requirement

Runtime safety does not establish biological identity correctness.

An eventual production path must authenticate the complete chain:

`41,238 feature registry`
→ registry ordering
→ reader/index mapping
→ tokenizer identity
→ tensor entering the model.

Shape, byte identity, hashes, and historical reproducibility are insufficient by themselves because registry rank/source index can differ from actual matrix column identity.

This issue is separate from optimizer/runtime convergence and must not be silently declared closed by runtime tests.

## 5. q-leakage is transitive

Removing the queried feature from visible model tokens is not sufficient.

New consumers must preserve q-safety through every downstream transformation and prove the query cannot leak through:

- normalization denominators;
- library-size summaries;
- detected-feature summaries;
- QC-derived features;
- support/missingness summaries;
- query-dependent preprocessing;
- other descendants of the hidden/query feature.

Historical fixes are evidence, not an automatic guarantee for a new consumer.

## 6. Historical residual-target work is closed negative evidence

Do not restart residualization as an untried rescue route.

The V6R5B residual target result did not rescue the target problem; gains were largely cell-global and molecular recovery remained weak.

The corrected synthetic T_A/T_B experiment was explicitly not informative about real biology.

Preserve these as negative constraints on future design rather than rerunning them by default.

## 7. V75 / 100K scope is narrow

The 100K lane qualified measurement architecture within its declared scope, including all 104 donors and 42 feasible observation operators.

It did not qualify:

- 500K;
- learned biological state;
- target;
- representation;
- training.

The source-feasible zero-quota rescue at 2K remains important. The alternative calibration-closure lineage erased operators at smoke scale and must not spill into future smoke qualification.

## 8. V77 / S127 is an instrument lane

Synthetic worlds can support:

- anti-cheat tests;
- runtime mechanics qualification;
- measurement/operator qualification;
- controlled failure modes.

They cannot select the real-RNA biological target or representation and cannot provide biological validation by themselves.

Weak-covariance synthetic worlds are known to differ materially from real TRAIN geometry; the historical unsigned module oracle also under-read mixed-sign programs. Synthetic success must therefore remain scoped to the synthetic/mechanical claim actually tested.

## 9. Claude and Macha are the same local GPU agent

Do not invent a dependency between Claude and Macha. Those names refer to the same local GPU-laptop agent/environment.

A separate GPT lane is working on real-data premise/representation qualification. Coordinate with that lane and avoid duplicating its scientific work.

## 10. PR #221 and PR #222 are overlapping donor lanes

They are not complementary merge candidates.

- PR #221 is valuable because it reaches the real inactive V5 PyTorch consumer and supplies real PyTorch/checkpoint donor mechanics.
- PR #222 is valuable because repeated adversarial audits produced substantially stronger governance and spillover protection.

The intended outcome is one successor. Once the successor reproduces the retained behavior, the losing implementation should be superseded/closed rather than independently merged.

## 11. Real PyTorch / AMP remains open until physically demonstrated

Ordinary optimizer-hook tests do not prove mixed-precision safety.

Required physical invariant:

If `GradScaler` skips optimizer mutation because of overflow/non-finite gradients, then:

- optimizer completion is not recorded;
- EMA does not advance;
- the lawful update cursor does not advance;
- no completed checkpoint receipt is produced for a nonexistent update.

This must be demonstrated using the intended PyTorch/AMP semantics rather than inferred from a fake optimizer.

## 12. Checkpoint digest is provenance, not deterministic restart

Full restart qualification must explicitly determine and bind every state component required by the deterministic claim. Potentially required state includes:

- encoder/student;
- predictor;
- EMA teacher;
- optimizer;
- GradScaler;
- authority/guard cursor;
- update/global cursor;
- Python/NumPy/PyTorch/CUDA RNG as applicable;
- sampler/data position;
- accumulation position;
- presentations seen;
- other state needed by keyed dropout or deterministic addressing if not fully derivable from frozen coordinates.

Then prove:

`uninterrupted trajectory`

versus

`checkpoint → reload → continuation`

to an explicitly declared equality/tolerance standard.

## 13. Historical artifacts are evidence, not automatic authority

Apply these rules throughout convergence:

- later repair does not retroactively upgrade an old receipt;
- a narrow repair stays narrow;
- physical reproducibility does not establish semantic correctness;
- historical checkpoints remain forensic unless prospectively requalified;
- search historical audits and custody before rebuilding anything.

## 14. Preserve negative findings

Do not erase failed designs from the audit history.

For each new defect:

1. add a failing test first;
2. record the observed RED;
3. make the smallest repair;
4. record the observed GREEN;
5. preserve the defect and its lesson in audit/history.

## 15. Convergence status and next job

Current intended state:

- `main`: post-PR-220 scientific/prefreeze governance;
- PR #221: draft donor runtime lane;
- PR #222: draft donor/runtime-governance lane;
- neither should be merged as-is.

Next job:

`independent audit → #221/#222 convergence → real AdamW/AMP qualification → complete restart qualification → independent review`

Even after successful mechanics qualification:

`TRAINING=OFF`

until a separate prospective execution authority is explicitly created and approved.

## 16. Additional convergence acceptance gates introduced by this addendum

The single-successor audit must also demonstrate that convergence did not regress any of these independent scientific/governance constraints:

- no biological interpretation of `width=160`;
- no 41K registry/index/tokenizer identity shortcut;
- no q-leakage through downstream summaries or preprocessing;
- no resurrection of residual-target or corrected T_A/T_B work as open rescue routes;
- no broadening of V75/100K claims;
- no synthetic-to-biological authority promotion;
- no historical receipt/checkpoint retroactive promotion;
- no deletion/obscuring of negative findings.
