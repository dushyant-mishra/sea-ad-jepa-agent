# Existing PR328 → Unified Task5 → post-TD source-edge audit and two-head synthetic probe

**Date:** 2026-10-27. **Status:** SOURCE-INSPECTED; separate cross-head CI controls whether the new fixture-only probe executed. **No target/training authority.** This is a narrow incremental test, not a new generator, qualification registry, graph, target-discovery controller, production issuer, or JEPA harness.

## Scope and exact immutable source heads

| Component | Reviewed source | Exact head/receipt |
|---|---|---|
| Qualified limited unified synthetic generator/fit | PR #328 `scripts/v79/unified_synthetic_integration_v1.py`, `unified_synthetic_fit_view_v1.py`, `unified_synthetic_controller_truth_v1.py`, `finalize_unified_synthetic_integration_v1.py` | `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`; existing V2 receipt `results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json`: frozen world `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`, fit `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`. Those are **existing** receipt/world IDs, not the new probe fixture. |
| Common CaseBundle fixture validator and dual-mode diagnostic | PR #440 code inherited unchanged by PR #451: `scripts/v5/td_unified/casebundle_v1.py`, `mode_equivalence_v1.py` | Case blob `23bbdcfc3234b7d621beb870fa019b34822446af`; diagnostic blob `e0bf61113f7c1acc46cc4b46cd69ca8b1092594b` |
| Existing fixture→portfolio bridge | PR #451 `scripts/v5/td_unified/post_td_fixture_bridge_v1.py` | `bbdf9a90973303e41cee6d8bd9d05de38e9b828a`; bridge blob `7ee09461cab959f4cfe67d2dc945fbcc372a0654`; independent review `ACCEPT_INCREMENTAL_TASK5_FIXTURE_BRIDGE_MECHANICS_WITH_LIMITATIONS`, comment 6426554595, exact CI 40392005207 |
| Common isolated repaired gate test-of-test | PR #369 `scripts/v5/td_sealed_cross_gate_battery_v3.py` | `651d7a5a1d4f4047d5ac875cc603f9151c2fed36`; CI 38577114860 |
| Real population/support and migration | PRs #349 / #381; Macha Oct14 audit; later accepted Task3 PR #401 | 149 donors / 42 operators, 104/22/23 split in source metadata; real evidence contract not inherited from fixture |
| TQB and downstream NONE gate | PR #447 `scripts/v5/td_unified/target_bundle_v1.py` | `729a0b4c67694baa25b46badce476df7a4c98a7d`; `issue_selected_target_bundle` unconditionally raises |
| Human relational biological result | PR #314 corrected one-shot replay (Oct12), independently audited in PR #322 historical architecture ledger | TD56/TD57B/TD59 PASS; TD57C nearest-third FAIL; C2 active, no JEPA target selected |

**Repo/worktree note:** these sources are held on **separate still-open PR branches**. Merely importing one package into another checkout does not establish a reviewed merged producer/artifact/executor lineage. PR #379 and Task0 #381 define the shared architecture, not a completed production merge into `main`.

## Execution-edge findings (reusing existing implementations)

| Edge | Actual producer / consumer and typed boundary | Already executed? | Source authentication, claim & decision |
|---|---|---|---|
| 1. Synthetic biology → RNA/ATAC fit observations | `build_unified_biology` → `observe_unified_world`; `UnifiedFitView(values,support,address_index,donor_id,source,operator,split,rna_entity_id,atac_entity_id,...)` | **YES, on PR328**, plus source/fit V2 receipt | Source and runtime/test fixture hashes pinned. Controller truth separate. Gene-block and rare-frequency settings are synthetic stress presets, NOT measured human biological target truth. |
| 2. PR328 fit observations → Task5 `KNOWN_TRUTH_CASEBUNDLE_V1` | `serialize_fit_view` returns array-oriented `UNIFIED_SYNTHETIC_FIT_VIEW_V1`; `validate_casebundle` requires exact row states `MEASURED_SCALAR`/structural/collision/withheld, source/donor/operator/address IDs, per-cell library size, evidence right, reader partition and manifest/policy IDs | **NO production source-authenticated adapter found in the inspected exact heads.** This new probe supplies a **test-only ephemeral projection** and checks actual compatibility at fixture scope. | Projection uses only a TRAIN-fold subset relabelled `reader_fit` **as fixture shape**, not Task2 population custody. All fit-gene count sums used as *synthetic proxy* library mass, not authenticated original measured total. Synthetic address IDs, not verified 41,238 human molecular addresses; no q-right partition, no measured collision proof. Must not promote this projection. |
| 3. Task5 CaseBundle → two outer mode traces | `validate_casebundle` → `trace_scientific_path(KNOWN_TRUTH/HUMAN_SEALED)` with ten `FixtureStage` handler roles → `certify_mode_path_equivalence` | **YES on handwritten Task5 fixtures**. Cross-head CI probes one generated PR328 fixture, not a true human-sealed second run | In PR451 bridge both modes are run **same process and same data**; it explicitly returns `SAME_PROCESS_SELF_COMPARISON__NOT_MODE_EQUIVALENCE_EVIDENCE`. Handlers are fixture functions, not registered production G2/G6/G7 executors. |
| 4. Generated world → common scientific real gate executors | PR369 separately tests repaired G2/G6/G7/G8/R1/geometry against sealed synthetic traps, each at pinned frozen head | **YES for isolated test-of-test; NO integrated PR328 CaseBundle→registered production gate execution shown in inspected source/CI** | Known-truth gate tests are not automatically a real evidence-right producer; G7 E3 external physical atom/rights/depth and G8/G6/R1/G2 substantive reference/issuer are distinct blockers. |
| 5. Gate results → authentic `TARGET_QUALIFICATION_BUNDLE_V1` | PR447 can issue/verify content-addressed **NONE development fixture**; selected-target issuer raises `TargetBundleError` | **NONE fixture yes; selected real TQB NO** | Parent digest resolution checks typed fixture objects, `scope=DEVELOPMENT_FIXTURE_ONLY`, `externally_authenticated=False`; no real issuance. |
| 6. Fixture label → existing TargetPortfolio & architecture | `stage_fixture_downstream(case_payload, stages, fixture_candidate, fixture_qualifications)` → PR351 `build_target_portfolio` / `build_architecture_plan` | **YES**, independently accepted narrow PR451 bridge | Caller inputs `fixture_qualifications={"C1":"PASS"}` are labelled `TASK5_PLANTED_FIXTURE_LABEL`, `biological_qualification=False`, bound to case digest; existing harness internally reads `status`. A future trusted consumer must explicitly reject these as production. |
| 7. Portfolio/architecture plan → real JEPA optimizer/EMA/Stage4 | Existing post-TD preflight/teacher evidence/EMA mechanics; PR328 also tested synthetic fit → **existing** preflight without authority | **Fixture preflight/plan yes; real target-consuming optimizer update no** | No real A7, external producer/bundle, verified target winner or authorized training. Source inspected is not proof of an unseen branch being absent; exact producers and receipts must be checked prospectively. |

### Additional source-authentication observation

`casebundle_v1.validate_casebundle` checks that `manifest_sha256`, `population_access_policy_sha256`, and `address_universe_sha256` are well-formed 64-character lowercase hex, and snapshots canonical *case content*. It does **not** resolve those claimed parent digests to independently authorized objects. The new two-head test deliberately replaces a valid-looking manifest SHA with another valid hex string; the fixture validator should still return `externally_authenticated=False` (and a different content digest). This is a **known fixture-mode limitation**, not an assertion of a novel implementation defect.

## What the two-head test actually does

Under a workflow tied to this PR only:

1. Fetch original PR #328 exact `25bbdbe...` to a separate read-only worktree and check its revision, install its pinned synthetic runtime.
2. Call **its existing** `build_unified_biology` and `observe_unified_world` with fixed unsealed seeds, select a donor-distinct nonprotected synthetic TRAIN subset, and create a **test-only CaseBundle-shaped projection from observed RNA values**. No `derive_controller_truth` call; no latent/perturbation truth or ATAC secret transmitted.
3. In the separate PR #451 descendant checkout, verify unchanged Git blob identity for `casebundle_v1.py`, `mode_equivalence_v1.py` and `post_td_fixture_bridge_v1.py`; validate generated observations using those real fixture functions.
4. Run the inherited Task5 ten-role fixture path and BOTH downstream `TARGET_NONE` and **planted** C1 `PASS` labels; reject any real/A7/EMA/training authority, test truth-field refusal and demonstrate unverified digest limits.
5. Publish only a small non-promoting metadata receipt, **not** the hidden world or the generated synthetic counts. The exact GitHub Actions conclusion governs whether step 2–4 can be called *executed*.

**Never infer:** the test-local projection is not the required production adapter; generated seed-31 world is not PR328's frozen V2 world nor V3.1.1 complete synthetic biology; count sum is not source-authenticated library; RNA-only passed case is not ATAC/SCENIC+/perturbation equivalence; in-process stages aren't real G7 E3; a fixture portfolio isn't an authenticated selected target.

## Scientific continuation from this boundary

Use PR #314 corrected relational Pattern A and R5 actual query-conditioned results as bounded *existing* human-development evidence; C3 is measured query context, not rare-cell specialist. Respect Macha GSE174367 independent ATAC and GSE301119 target engagement scopes. **The first missing promotion edge is authentic observation/assay/evidence-right issuer → CaseBundle**, followed by exact common scientific producers, independent known-truth qualification and a consumer that refuses fixture labels. Reuse Task0/Task1–4 law and #349 source support; do not propose a parallel generator/TD registry. A real run must await independent accepted producer, calibrator, cumulative Task4 and G7 E3 trust, and prospective outcome authorization.

**Standing state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
