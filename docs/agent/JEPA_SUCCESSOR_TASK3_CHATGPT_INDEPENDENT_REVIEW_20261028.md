# Active successor — independently tested PS Task3 #437 source defects (2026-10-28)

**Start with** the latest [PR #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460) successor V2 handoff, [PR #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) historical no-repeat audit and [PR #480](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/480) independent Task3 tests-only review. The 2026-10-27 source history remains controlling; this is an **append-only execution update**, not a new historical audit or selected target.

## Executed since prior handoff

Original Macha [PR #437](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/437) calibration firewall source frozen at `fd3242ada6f77ba09ff2d8a1c7716eb9725ced11`, Git blob `bafd0a24536a30ca927c9808e2feddda4cb29428`. ChatGPT independently built [draft PR #480](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/480) tests-only RED probe; original Macha Task3 code/tests were **not** modified. The review covers:

1. **R1, numeric witness false invariance.** `validate_address_universe_agnostic` compares `float(value)==float(other)`, aliasing distinct integer observations `2**53` and `2**53+1`. Even a fixture-only invariant witness must not make a false exact numeric claim. No real data exhibited this extreme value; test is synthetic.
2. **R2, biology-like tunable-name spoof.** The V3.1.1 realism contract permits any observation parameter string with prefix `OBS_`. `OBS_DISEASE_PREVALENCE` and `OBS_TARGET_WINNER` are accepted despite the source contract forbidding biological-state/target tuning. This does not establish a real generator uses those names; it proves the naming guard cannot enforce the scientific constraint.
3. **Preserved nonauthority.** A self-pinned fixture SHA does not authenticate calibration; `_AUTHENTICATED_CALIBRATION_REGISTRY` stays empty. Protected donor partition checks and process-local *cooperative-only* realism custody are unchanged. No current REAL_REFERENCE_READY/TASK3/STOP_B acceptance.

**Exact original-source CI:** [PR480 reviewer workflow 40733195290](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195290) SUCCESS when **three intentional hostile FAIL** plus **one unpromoted positive control PASS** are recorded; original Macha suite **33 PASS**. Full inherited [Task3 run 40733195258](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195258) FAILURE **3 failed / 391 passed / 1 xfailed**, because it also collects new reviewer RED tests. Unchanged [unified synthetic run 40733195217](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195217) SUCCESS. These are test source `9f2ea674b41730faacd9801a82a20745e592d9ad`, not biological executions. Document-only PR480 head `f39e605abc616cf59051a8bda9b0270cef5d6f09` follows original verified CI head `3635eae7ee0df5a4e311f04c16e9ab0e6d574fff`; no source test changes.

**Verdict:** `REPAIR_REQUIRED__R1_NUMERIC_ALIAS__R2_OBS_PARAMETER_SPOOF`. Only narrow mechanical contract defects; cannot infer any human biology outcome.

## Historical evidence now archived in audit #322

New `results/production_synthetic/JEPA_TASK3_CHATGPT_INDEPENDENT_REVIEW_20261028.json` machine receipt, verbatim `docs/agent/JEPA_PS_TASK3_MACHA437_INDEPENDENT_REVIEW_20261028.md` and original failing tests archived under `docs/agent/review_probes/chatgpt_20261028/ps_task3_437_expected_red_probe.py.txt` (not collected as normal pytest). A new static verifier and hostile tests protect exact original SHA and prevent turning reviewer RED into real calibration acceptance. Check audit exact-head CI before treating custody claim as tested.

## Next work; do not repeat earlier science

- **Macha/another repair author:** repair `float` numeric alias (exact mathematical comparison or prospectively constrained numeric domain) and closed, source-versioned observation-only tunable parameter registry. Reviewer tests in PR480 remain immutable and must turn PASS on a new *separately reviewed repair head*. An allowlist alone does not authenticate generator operator semantics.
- **ChatGPT/independent lane:** review the repair, then continue true post-HVS/SEA source-issued TRAIN-only calibration feasibility. Source/archive SHA does not prove physical original reads, donor/specimen grouping, per-q rights, off-ledger full-count coverage or QC selection independence.
- **Macha assigned independent #479/#476/#477:** V2 normalization contract, G7 R5X/R6 snapshots, PS portable encoder remain separate and require exact-head reviews. G7 R1/R1D/R2 and PS T2-D remain RED.
- **Production synthetic biological world:** candidate-neutral PS Task4 generator absent in examined branches; no sealed known-truth run may be substituted with PR328 planted mechanics or PR469 fixture rows. Preserve the corrected real PR314 relational and developmental R5/V44 evidence, not rerun it.

**Hard stop:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
