# JEPA new-chat takeover addendum — Claude/Macha supervision

Date: 2026-10-06

This addendum supplements `JEPA_NEW_CHAT_TAKEOVER_20261006_RUNTIME_QUALIFICATION_CONVERGENCE.md` and is specifically for the new ChatGPT agent who must supervise, audit, and direct Claude/Macha's local GPU lane while also continuing runtime/shared-interface convergence.

## Identity and lane boundary

Claude and Macha are the same local GPU agent/environment. Do not treat them as separate dependent agents.

Claude/Macha owns the V77/S127 synthetic instrument lane and eventual local execution of the shared qualification pipeline. The separate GPT scientific lane owns future real-data scientific qualification choices. The runtime/shared-interface lane owns machine-enforced contracts and lawful execution mechanics.

Synthetic work is not an independent scientific program. V77 exists to test the same qualification pipeline that will later be used on real RNA, with synthetic oracle truth kept physically downstream.

## Exact Claude/Macha GitHub anchor at takeover

Branch:

`claude/v77-synthetic-premise-custody-20261005`

Exact head audited here:

`8497916e5a9d9b232597ac1891b6c630d3b17931`

Head message: `V77 S146/S147 downstream: driver to re-run component detect/reject on repaired worlds`.

GitHub commit status at this head has no reported CI contexts (`total_count=0`). Therefore local test claims in commit messages are useful evidence but are not equivalent to an independent GitHub CI witness. Future supervision should ask Claude/Macha to preserve exact local commands/results in committed receipts and, where practical, add or run an independent CI gate.

## Fresh audit conclusions

### 1. S146/S147 repair is real and important

Commit:

`954cee9e2a2e818b1ee712569bdd71715890853b`

The branch identified two structural-support defects in the synthetic observer:

- S146: truth source indices used World-A order `(SEA_AD, NPH52, HVS)` while registry coverage rows used `(HVS, NPH52, SEA_AD)`, swapping HVS and SEA-AD support.
- S147: operator structural missingness was applied inside cohort coverage even though the operator QC keep fraction was already registry-relative, double-counting the cohort coverage gap.

The repair maps by source name, checks source/operator cohort consistency, computes attrition relative to cohort coverage, and emits producer-side per-element support masks.

This finding directly motivated the shared-interface operator/source identity and per-element support receipts in PR #223. Preserve that linkage.

Historical consequence: canonical V2 worlds built before this repair have defective absolute measurement support. Same-world twin contrasts may still be internally comparable, but absolute measurement-structure claims from those worlds must not be cited as repaired evidence.

### 2. Current head is executor-only for repaired component detect/reject

Current head `8497916e...` adds `scripts/v77/run_v77_component_detect_reject_v2.py`.

The commit explicitly says `Executor only; receipt follows`.

Therefore the repaired-support B4/C1/C2/C3 detect/reject result is NOT complete at the current remote head. Do not quote a pass/fail summary until Claude/Macha executes that exact tracked clean-head driver, writes the result receipt, commits it, and pushes it.

The driver has good anti-retuning properties: it rebuilds worlds fresh, verifies the repaired structural-support rule, uses unchanged signed-oracle statistics and existing frozen thresholds, records executor digests, and refuses modified tracked executors. Audit the resulting receipt anyway.

### 3. S149 is pushed and repository-backed

Relevant commits:

- `66bd9bed48753dd8eaae357e07a062364357688d` — within-cohort envelope executor / material pivot proposal.
- `f91feac9199b27f531be31057cac3178c0ea3dd9` — executor validating detection-inferred strata against true study identity.
- `fd21f649a7671dd345160e60079d0fac8d01418f` — committed S149 validation receipt.

The validation is substantively useful. The inferred stratum is derived from each cell's detections plus the address-universe support geometry, while the comparison label comes independently from the FULL104 population authority's operator-to-study mapping. The committed result reports 3,292/3,292 agreement for cache cells belonging to production donors and no production donor measured by multiple studies.

This supports the narrow conclusion that the detected coverage strata are genuine study/measurement-process strata, not merely a depth partition. The reported medians also show HVS is not simply the shallowest group.

### 4. Qualification on the phrase `cache is donor-weighted`

Do not repeat this as a literal sampling-design claim.

The committed S149 result shows:

- calibration-cache cell mixture: about 65.0% HVS, 5.2% NPH52, 29.8% SEA_AD;
- FULL104 production cell mixture: about 4.4% HVS, 5.2% NPH52, 90.4% SEA_AD;
- FULL104 donor mixture: about 39.4% HVS, 16.3% NPH52, 44.2% SEA_AD;
- cache cells per donor vary from 2 to 74, median 37.

So the cache's study mixture is much closer to a donor-level mixture than to the production cell mixture, but that does not establish a formally equal-donor weighting design. Use wording like:

`the cache composition is substantially closer to donor-level than production-cell study proportions`

unless the sampling algorithm itself is separately audited and proven donor-weighted.

### 5. Cross-lane authority problem in the S149 'replacement target' wording

Commit `66bd9bed...` calls within-cohort real envelopes the `replacement target` for synthetic calibration. That is too strong for this lane.

Claude/Macha may:

- diagnose pooled-envelope confounding;
- build a prospective within-cohort candidate diagnostic;
- run read-only, pathology-blind calibration measurements if already authorized by the historical V77 lane;
- propose how the synthetic instrument should be tested.

Claude/Macha may NOT independently settle the scientific estimand/target that the future real-data qualification pipeline should use.

The separate GPT real-data scientific lane must review the S149 evidence and decide whether the eventual scientific contract uses within-study envelopes, hierarchical donor/study estimands, production-mixture weighting, conditional residual dependence, or another prospectively specified quantity.

Until that review, treat `build_v77_within_cohort_envelope.py` outputs as a candidate calibration diagnostic / development instrument, not an authoritative replacement scientific target.

### 6. Claim namespace should not hide real-data use

The S149 real-data diagnostics are recorded under `V77_SYNTHETIC_WORLD_QUALIFICATION`, but they read real TRAIN calibration data in a pathology-blind, read-only way.

That may be lawful under the historical calibration lane, but future receipts should make the distinction explicit:

- `real_data_used_for_instrument_calibration=true`;
- exact population/partition identity;
- pathology-blind/read-only status;
- scientific-selection-authority=false;
- protected TEST/Morabito not accessed.

Do not let a synthetic claim namespace make real-data exposure invisible to later auditors.

## How the new ChatGPT agent should supervise Claude/Macha

Treat Claude/Macha as an execution/research collaborator whose work must be independently audited before it is promoted into project state.

For every substantial Claude/Macha handback:

1. Fetch the exact remote branch head before reading claims.
2. Compare it to the last audited head and audit only the delta first.
3. Distinguish:
   - executor commit;
   - result/receipt commit;
   - interpretation/governance commit.
4. Do not accept an executor as evidence that the experiment ran.
5. Do not accept a local transcript result until the exact receipt is pushed and provenance can be inspected.
6. Check that thresholds/statistics were frozen before the run.
7. Check whether the same synthetic world or real calibration data were already inspected during design. If so, classify the result as development/calibration evidence rather than sealed validation.
8. Check that oracle truth stayed downstream of frozen ordinary outputs.
9. Check that no oracle-derived quantity fed representation fitting, threshold tuning, preprocessing, target construction, optimizer updates, or model inputs.
10. Check feature identity, source/operator identity, and producer-side per-element support against the PR #223 contracts.
11. Check that scientific choices reserved for the real-data lane have not been silently promoted by the synthetic lane.
12. Preserve negative results and invalidated historical receipts; do not rewrite history after a repair.
13. Require a clean-head receipt with source SHA, executor digests, input/artifact digests, exact command, status, and claim class.
14. Record the audit outcome on the handoff branch.

## Instructions to give Claude/Macha now

The next local priority should be:

1. Do NOT start a synthetic mutation/training run.
2. From exact clean committed head `8497916e...`, run the repaired-support component detect/reject driver exactly as committed unless the branch has moved; if moved, report the new SHA first.
3. Use fresh custody directories; do not reuse pre-repair worlds.
4. Commit and push the resulting receipt with exact source head, executor hashes, world manifests, structural-support rule, detect/reject values, and frozen thresholds.
5. Do not retune statistics or thresholds after seeing the result.
6. If any B4/C1/C2/C3 arm fails after support repair, preserve the failure and diagnose it rather than changing the acceptance rule.
7. Treat all pre-S146/S147 absolute-support synthetic results as historical/development evidence only.
8. Continue adapter work toward the shared PR #223 `QualificationBatch` contract, but do not create an independent synthetic trainer, optimizer, EMA, checkpoint, or guard.
9. The adapter must provide mechanically checkable:
   - ordered feature identity;
   - source/operator identity;
   - producer-side per-element support;
   - observation ordering;
   - scientific batch identity;
   - inference grouping;
   - synthetic realization identity;
   - challenge partition.
10. Keep `SyntheticOracleTruth` in a physically separate downstream object. Ordinary preprocessing/model/runtime APIs should not accept it.
11. Zero-update synthetic qualification is the first integration target. Bounded mutation comes only after runtime convergence and separate mutation authority.
12. Do not declare the within-cohort envelope the final replacement target. Call it a candidate diagnostic pending real-data-lane review.
13. Do not choose the real-data representation winner, estimand, deciding threshold, or biological target.
14. Keep TRAINING=OFF, STAGE_A_EXECUTION=OFF, TEST=SEALED, MORABITO=PROTECTED.
15. Push all substantive local work promptly so the supervising ChatGPT agent can audit repository evidence rather than transcript-only state.

## Questions the supervisor should ask after Macha's next receipt

For the repaired-support detect/reject receipt:

- Was the source head exactly the committed executor head?
- Were all five worlds newly built?
- Does every manifest say `S146_S147_NAME_MAPPED_REGISTRY_RELATIVE_V1`?
- Is producer-side `support_mask_packed` present in every shard?
- Did source/operator cohort consistency pass with no default/fallback mapping?
- Were the same pre-frozen signed statistics and thresholds used?
- Did ON detect and matching OFF reject for B4, C1, C2, C3?
- If not, which signal changed after structural-support repair and why?
- Were any thresholds or diagnostics changed after seeing the result?

For the adapter:

- Can a same-length feature permutation pass? It must not.
- Can source order be permuted? It must not.
- Can per-element support be reconstructed from counts/nonzeros? It must not.
- Can donor/study/source IDs become model-visible or derived model-visible features? They must not.
- Can oracle truth enter preprocessing or fitting? It must not.
- Does microbatching/device packing leave scientific identity unchanged?
- Are units of inference preserved independently of cell-level model batching?

## Coordination with the real-data GPT scientific lane

Send the S149 package to the real-data lane as evidence, not as a decision.

Ask that lane to evaluate, prospectively and before future confirmatory synthetic scoring:

- what quantity should define synthetic-real calibration for dependence structure;
- whether within-study envelopes are sufficient;
- whether study effects should be modeled hierarchically;
- how donor weighting/estimands should be defined;
- how measurement OOD versus biological OOD should be separated;
- what aspects of V77 calibration are development-only after repeated inspection.

The real-data lane should produce a machine-readable successor `QualificationProtocol` decision when ready. Runtime and Claude/Macha should consume it, not pre-empt it.

## Coordination with runtime convergence

Do not wait for perfect synthetic realism before completing runtime convergence.

Proceed in parallel:

- shared-interface/runtime lane: one canonical #221/#222 successor, real AdamW/AMP guard, no bypass, deterministic restart, proof binding into #223;
- Claude/Macha lane: repaired-support receipt, adapter conformance, zero-update synthetic pipeline preparation;
- real-data GPT lane: scientific calibration/estimand/representation qualification decisions.

The first point where these lanes should physically join is a ZERO_UPDATE synthetic `QualificationBatch` passed through the shared scientific pipeline under #223 visibility/provenance rules. Mutation remains a later, separately authorized rehearsal.

## Supersession and evidence discipline

Never let a later repair retroactively upgrade old evidence.

Specifically:

- pre-S146/S147 worlds remain pre-repair worlds;
- pooled real envelopes remain composition-inclusive historical references;
- V77 diagnostics used during development are not sealed independent validation;
- S149 within-cohort candidate does not become science authority by being implemented;
- a successful synthetic instrument does not authorize real-data execution;
- a successful runtime mechanic does not establish biological validity.

## Current immediate frontier for Claude/Macha supervision

`audit remote head -> run/push repaired-support detect/reject receipt -> independently audit receipt -> adapt repaired synthetic observations to PR #223 QualificationBatch -> zero-update integration only after shared runtime/interface convergence is ready`

No synthetic mutation, production training, Stage A, TEST, Morabito, target winner, representation winner, selected estimand, or deciding threshold is authorized by this addendum.
