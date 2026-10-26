# Next-stage JEPA execution runbook — 2026-10-26

**Status:** executable fixture-only Task5 candidate; **NO TASK4 / TASK5 AUTHORITY**, NO protected data. This is an execution handoff, not a repetition of historical audits.

## 0. Branch and intended integration target

- Task5 candidate draft PR **#440**, branch `implementation/unified-task5-fixture-handoff-20261026`, based on **frozen Unified Task3** `117dd51dea827e734b299982da93991b934bdc8f`.
- RED-first Task5 tests at `b9e6cd88b7789302c048c45780f8420b26e70a95`; dedicated CI missing-module RED run `40352978431`. Initial implementation + plumbing passed **23 Task5 fixtures** in `40353546742`.
- Follow-up content-fidelity RED `4c4dc135fa4cb2b35fbf729b5f4f0329633c6f56`, CI `40353838104`: **2 failed, 24 passed**. New non-authorizing physical consistency checks reject cell-to-donor/source/operator swaps and summed observed counts beyond cell library.
- Current fixed exact head `7c65ac803583062e368570eb0264ca053cefc7d2`, Task5 Actions **40353983606**: **26 passed**.
- Source: `scripts/v5/td_unified/casebundle_v1.py`, `scripts/v5/td_unified/mode_equivalence_v1.py`; tests: `tests/v5/td_unified/test_task5_fixture_handoff_v1.py`. Workflow: `.github/workflows/td-unified-task5-fixture-handoff.yml`.
- **Do not merge/cherry-pick Task5 as formally accepted before an independent fresh-context review and the accepted Task4 base is resolved.** No source in frozen Tasks0–3 is modified.

## 1. What was built, and what is NOT built

**Built (fixture mechanics only):**
1. Canonically hash a physical observation CaseBundle using *existing* Unified Task1 serializer. Preserve measured zero, structural absence, collision-unresolved, and rights-withheld values; reject truth/controller keys and illicit labels in the observable tree.
2. Reject duplicate molecular atoms, non-integer/negative counts, inconsistent physical cell/donor/source/operator identity, inconsistent per-cell library mass and measured counts exceeding library. The four state classes are noninterchangeable.
3. Require a dummy TD output freeze before touching a separate fixture-only truth bundle; never return truth contents to the scientific path.
4. Invoke a prospectively declared ten-stage scientific fixture path (schema, access, producer, serializer, receipt, executor, metric, support, reference, status) with the SAME observable bytes on two wrappers. Check actual handler/output/trace digests and refuse a divergent stage.
5. Expose only explicitly non-authorizing outputs: `externally_authenticated=False`, `same_code_path_authorized=False`, `known_truth_qualified=False`, `real_reference_ready=False`, `training_authorized=False`, `authority_effect=NONE`.

**NOT built / must never be implied:** true Task2 manifest/reader split raw-byte revalidation; Task4 issued campaign/exposure/lease authentication; a real producer; real executor/reference signatures; true independently authenticated A7 path attestation (Python marshal fingerprints here are *diagnostic*, version-local, not trust roots); protected sealed challenge access; genuine human-mode equivalence; external adjudicator; production CaseBundle, TargetPortfolio winner, or JEPA training. The `freeze_fixture_td_output` receipt is caller-provided fixture input, not durable external custody.

## 2. Dependency-ordered actions when Macha returns

### Lane PS: production-synthetic V3.1.1
1. **Re-fetch** the actual PR #437 head and compare to the last independently reviewed rejected `273f4a18016ef5b0a2665ae74abc96183c3d478b`; re-run the isolated hostile tests of PR #439 against the *new* head and independently adjudicate numerical, canonical identity and hostile same-process trust claims. PR437 had already moved from the rejected head by this writing. Do not auto-adopt author self-review.
2. Recover independent fresh-context ACCEPT evidence for separate production-synthetic Tasks1–2; a CI rerun alone is not an acceptance verdict.
3. Complete post-Task3 checkpoint (§9 of PR #356 handoff), including no Critical/Important open findings, no withheld controller secret or production realization and no STOP crossing.
4. Only after all three approvals may PS Task4 candidate-neutral biology start under PR #356 §Task4. This **does not authorize** STOP_A first production realization, STOP_B sealed qualification or STOP_C finalizer. Do not implement old independent synthetic Tasks4–12 against the post-#379 unified architectural pivot without compatibility adjudication.

### Lane Unified TD: Task4 → Task5 → Task6 → Task7 → Task8
1. Resolve PR #428 cumulative Task4 DEVELOPMENT review plus PR #435 independent RED / PR #436 local stale-writer repair. Review latest exact adopted source and R4/C1(b) external trust separately. A green benchmark is not final custody or owner trust.
2. Once the **accepted** Task4 integration base is chosen, create a new clean successor branch from that exact head; selectively transplant the Task5 fixture-only source/tests/workflow from PR #440. Do **not** overwrite any frozen Task0–3 files. Re-run `python -m pytest -q tests/v5/td_unified/test_task5_fixture_handoff_v1.py` and upstream Task4/full-unit CI. Record exact rerun heads and receipts. Perform independent Task5 review on the integrated head.
3. To complete real Task5 (A7): bind CaseBundle to the real Task2 authenticated manifest/access contract; bind freeze/exposure to accepted Task4 custody; reuse same gate-facing validator/producer/serializer/executor/metric/support/reference/status code objects in both modes; seal truth entirely outside the scientific executor; independently recompute code/input/branch/trace identities. Add genuine producer-specific hostile tests. Until then **SAME_CODE_PATH remains unqualified**.
4. Task6: register G2/G6/G7/G8/G9/R1/R4/C6/C4/G12 against their exact repaired producer heads at at most `FIXTURE_SAME_INTERFACE` initially; test that PR #369 PASS mechanics cannot promote constituent gates. Candidate-aware qualified reference producers and reviewer receipts remain missing. Do not conflate raw CI success with gate evidence.
5. Task7: implement `TARGET_QUALIFICATION_BUNDLE_V1` including a real first-class `TARGET=NONE` (binding negative controls/registry/manifest); NO target selection without qualified biological verdict, and no widened support.
6. Task8: implement exact downstream bundle consumption, inherited falsifiers, observation rights, teacher/student evidence partitions, downstream check receipts and frozen evaluation commitments. Include the permanently negative RBB/Bayesian trainable-belief prior and rejected fake-rich-teacher/query-leakage cases as hostile regressions; do not replay/retune old experiments.
7. Only after later independent qualification: Tasks9–12 known-truth cases → prospective approved challenge/adjudication → real producer prerequisites → representation-family held-donor qualification. Every stage remains independently gated. Real training needs separate owner authorization regardless of CI.

### Lane G7 and JEPA representation diagnostics
- Real G7 E3 PR #433 `21c3fb3bd389f9a513ca9ed33b31acad56b0015f`: **23 fixture mechanics PASS**, independent Macha review pending; authenticated real producer and human G7 remain blocked. If accepted, carry the **content anti-thinning rules** into authentic real/synthetic support rights; do not copy a fixture digest as external attestation.
- Read-only frozen four-world diagnostic PR #438 `034cb8ab5a2e9ff3240404ad56289ee606feb6c0`: 14 tests GREEN, Macha review pending; no Bayesian encoder head, EMA update, NB raw count model, or interpretation as biology. If accepted, use it only as a non-promoting diagnostic sidecar to Task8 after an independently accepted Target Qualification Bundle.

## 3. Known inherited workflow issue

On this Task3-frozen base the old `Unified Task 3 B6 workflow policy` still fails because its CI installs only pytest although `tests/v5/td_unified/conftest.py` imports NumPy. Earlier Task4 branches contain this already-known workflow-maintenance fix. The new Task5 CI explicitly installs NumPy and passes. Do not modify frozen Task3 production code; during Task4-base integration ensure the intended inherited workflow dependency fix survives. Distinguish missing CI dependency from actual downstream scientific failure.

## 4. Explicit next runnable commands (fixture only)

```bash
python -m pytest -q tests/v5/td_unified/test_task5_fixture_handoff_v1.py
python -m pytest -q tests/v5/td_unified/test_canonical_v1.py tests/v5/td_unified/test_manifest_v1.py tests/v5/td_unified/test_registry_v1.py
```

Resolve actual test paths if upstream accepted branch reorganized them; never silently skip expected gates. CPU-only, no special secrets, datasets, external controller, production generator, WSL requirement or GPUs.

## 5. STOP / authority declaration

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

`TASK5_FIXTURE_HANDOFF_GREEN__TASK4_INDEPENDENT_ACCEPTANCE_OPEN__TASK5_REAL_A7_NOT_QUALIFIED__PS_TASK3_NEW_HEAD_REVIEW_OPEN__STOP_A_B_C_INTACT`.
