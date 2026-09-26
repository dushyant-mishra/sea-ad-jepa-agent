# JEPA V27 independent execution and self-audit — September 26, 2026

**Entry point:** [draft PR #149](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/149), based on `review/v27-authority-root-inventory-20260925 @ ed9df043075cd55e16be7a61af62594640421c18`. Main V25 `START_HERE.md` remains controlling until a reviewed successor merges. This is a bounded independent source/metadata-only continuation; it **does not** merge PR #147/#146, run a GPU teacher, open protected results, grant reader_fit expression training access or settle biological masking.

## 1. What was really executed and independently checked

### A. Second PHYSICAL original FULL104 metadata replay, not just a GitHub synthetic fixture

The physically mounted `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` was SHA-256-authenticated in this environment: **410,278,055 B**, `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`. Its original, **2,709,786,624 B** `foundation_metadata_rows.sqlite` member was extracted fresh and SHA-256-authenticated: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`. The original PR #146 read-only producer was rerun on the actual database and ZIP—not a 94-donor sample, history placeholder or fixture. All five produced bytes matched the previously packaged original files:

| Actual original data/result | Exact SHA-256 | Byte identity |
|---|---|---|
| 104-donor scientific-masses CSV | `386e52ecb56031fba7bde855c7af314b08f1773427d367e0679e6de47f79c7b7` | yes |
| 42-operator token-support CSV | `e26814f33c0d665a99923f6fb41a59c31407dbc04e21aa6526cf166e252732fa` | yes |
| 1,400 donor×operator relational-capacity CSV | `e40acc06844f4a13cb956453fe54e74abed357c3777a80ec6c4a2778dcae8f65` | yes |
| Original full physical metadata receipt JSON | `d1c863e528486f24f97b3a48c6c6d7f181f68dce58efc09e78114ff3f0e1a832` | yes |
| Original four-output SHA manifest JSON | `61786aa8d523f38c0a93eff244fbb4c2f556c145106b5026519d42ea5ff9b8db` | yes |

The original independent output verifier returned **PASS**; its pre-existing **24 adversarial tests passed, 0 skipped**. Exactly 104 reader_fit donors, 4,553,407 fit cells, 42 operators and 1,400 actual groups (1,361 with at least 3 cells) independently reconcile. Complete machine-readable receipt: [second physical replay](../../results/v27/FULL104_INDEPENDENT_SECOND_PHYSICAL_METADATA_REPLAY_20260926.json).

Further **independent original-ZIP parent-byte verification**: `contracts/address_namespace.csv` is 24,946,770 B/SHA `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`, with exactly 41,238 records, contiguous ordered address indices and unique molecular-address IDs. `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` is 227,532 B/SHA `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`, with `uint8 (42, 41238)` observation states and named 42 operator/41,238 address axes. This is **not** a rehash of the separate full Level-4 block manifest `66f589…`.

Self-audit: the local downloadable original ZIP contains **nine** archived files. PR #146 additionally publishes the separately available original physical run log as a tenth readable GitHub file. Do not describe the nine-member ZIP itself as containing ten members or invent a missing log.

### B. Six actual V5 defining-class validators run on the exact six found artifacts

The prior 33-slot inventory's six items were previously **matching-schema candidates only**. New [exact-role verifier](../../scripts/v5/v27_six_candidate_authority_audit_v1.py) hard-binds each original path to its own current V5 dataclass validator and recomputes canonical digests; the nested canonical-registry record is mapped only through the known separately named `ADDRESS_REGISTRY`, `FULL104_SUBSTRATE` and `OPERATOR_ADDRESS_OBSERVATION_STATE` roles. It checks the masking parameter/RNG self-digests and exact root-derived seed, cross-bindings among base estimand/support/masking parameters, role-distinct source roots and no training flag. This deliberately **rejects similarity-based file searches**.

**All six candidate own-schema validators PASS**, and none is promoted to a fully closed root: no current closure V2 was emitted; its remaining sources and upstream parents have not all been physically authenticated. [Machine-readable 33-root ledger](JEPA_V27_33_ROOT_VALIDATION_LEDGER_20260926.json) records **6 own-schema validated candidates, 25 not matched at the reviewed branch head, 2 with an unresolved defining-module role, 0 closed roots**. Searching other unmerged heads and the GPU-laptop artifact inventory may change the 25/2 statuses; these are not global statements of nonexistence.

Hosted GitHub [run 36220418754](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36220418754) directly ran all six current validators plus **11 fail-closed adversarial tests, 0 skipped**, with JUnit exact census. Extended [run 36220645873](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36220645873) additionally verified the V4 freeze can detect a truly mutated source and prevented numeric-spillover into the teacher decision packet: **18 passed, zero skips, exact JUnit census**. No empty-verifier green.

### C. Superseded gradient plan removed, genuine V4 red-team added

The existing current V5 harness already enforces its gradient firewall **inline** before optimizer.step and EMA. The inherited [V27 root-inventory review](V27_AUTHORITY_ROOT_INVENTORY_AND_PR147_CORRECTIONS_20260925.md) still contained a stale §4 instruction to *move* the gate inline despite §2b having correctly withdrawn that instruction. This branch corrects §4 and its status without altering the immutable PR #147 historical 40-update receipt. The old 40/40 literal-zero assertion remains **withdrawn**. The six negative tests on the parent branch stand; the measured nonzero max gradients and successful nonthrowing historical 40-step run remain legitimate but are not real biological evidence.

The new [V4 mutation negative control](../../tests/test_v27_v4_freeze_mutation_control.py) runs the authentic active V4 source manifest audit on original bytes, then copies only its referenced frozen sources/authorities/tests into an isolated temporary tree, flips a real source byte **in that temporary tree** and proves an explicit SHA mismatch and STOP terminal. No frozen V4 sources or PR #147 original receipts are rewritten.

### D. A concrete, machine-checked *proposal* for the scientific decisions, not an authority forgery

[Proposed teacher-target decision packet](JEPA_V27_PROSPECTIVE_TEACHER_TARGET_DECISION_DRAFT_20260926.json) transcribes the existing V5 query-local biological-cellular-state semantics: canonical query identity available, queried scalar withheld **before contextual mixing**, only lawful remaining RNA, teacher stop-gradient, no scalar reconstruction as primary objective. Actual FULL104 donor/operator metadata and known source roots are included in their own **metadata-only** fields. Unknown real-training donor split, mask choice/fraction, geometry, EMA half-life, LR, GPU budget, RNG and scoring plan are explicit **null** and require prospective approval.

The companion [draft guard](../../scripts/v5/v27_teacher_proposal_firewall.py) and [adversarial tests](../../tests/test_v27_teacher_proposal_firewall.py) fail closed when historical/synthetic mask .40, width32, made-up EMA/update horizon, a historical 94-donor population, fabricated training authority, a fictitious heldout claim or prematurely filled protected scoring is inserted into the draft. Metadata numbers remain allowed only for the actual physically authenticated current104 role. These checks are an anti-spillover safeguard, **not** a scientific conclusion or training issuance.

## 2. Explicit blockers and remaining tasks (not silently converted to pass)

- **Authorization B1:** reader_fit remains `ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY`, and new teacher training needs the separate project-approved frozen training contract. No authority was signed, invented or issued here.
- **B2 + all remaining roots:** `issue_training_authority_v1` also requires valid closure V2 with **32 upstream roots**, preexecution, exact frozen target-package/receipt, critical-test and runtime-source authority. The receipt slot count is 33. Six candidates pass own validators, **zero** full closure slots qualified. In particular there is no current qualified masking policy from the frozen September-16 grid; the documented relational TD57C fine-local failure must not be silently relabeled. Do not freeze the provisional model's biological dimensions as D_shared.
- **Remote Windows S9 environmental quarantine:** original `sea-ad-jepa` reported crashing on even 3×3 NumPy BLAS while `sea-ad-jepa-v3` ran. A [subprocess-isolated, crash-safe dual-environment audit script](../../scripts/v5/v27_blas_environment_quarantine_audit.py) is published for the GPU laptop. **It was not physically run on that laptop from this environment**; no existing scientific output was deemed contaminated without its actual producer-env and NumPy usage receipt. Claude can run: `python scripts/v5/v27_blas_environment_quarantine_audit.py --environment sea-ad-jepa --environment sea-ad-jepa-v3 --out D:/jepa_audits/new_unique_v27_blas_env.json`. It never repairs either environment automatically.
- **PR #120/#124**: latest all-8,915-block raw-count reaggregation terminated on session limit; no actual all104 raw-count integrity verdict. The per-donor pass1 metadata bridge cannot prove per-cell source identity or raw Level-4 lineage; any independently authorized continuation needs deterministic chunking, exact-count exactly-once reducer and no protected N1 masking outcome opening.
- **Mechanical unfinished:** historical 40-step gate's four success counters were hardcoded zeros; parent branch six negative-control tests establish actual refusal on zero/nonfinite/teacher gradients. Remaining missing-report, partial-checkpoint/cursor and full active-suite V1–V3 supersession hygiene must be explicitly tested separately. No new real V5 FULL104 streaming adapter or real-model update was built here.
- **Scientific handoff:** owner must decide target-construction instance, one masking candidate (possibly development-only and explicitly unqualified), split/estimand, resource-bounded provisional model/EMA/schedule, fixed negative controls and prospective developmental scoring. PR143/144 objective-matched G3 plus six-state heldout scorers require their **own real-data qualification**, not merely synthetic unit tests. All104 model training cannot then be described as unseen reader_fit-donor LODO.

## 3. Independent replication and anti-spillover chronology

1. `main` controlling V25, until reviewed merge; V27 PR147 execution receipts immutable.
2. Sept21 FULL104 SQL atlas and PR146 physical dataset evidence are reused (not rescanned to choose a scientific effect).
3. The original calibration and SQLite physically rechecked here; only metadata queries run. Validation22/oracle23 source partition metadata are not their expression, and pathology remains a separate protected channel.
4. Candidate artifacts are accepted only under **their own defining classes**. Matching a similar schema, computing a syntactically valid digest or copying a receipt cannot stand in for a missing authority root.
5. No old94/50k synthetic fixture, old T1 checkpoint, synthetic EMA .99, historical .996, synthetic width32 or synthetic mask .40 enters the real104 training configuration; the machine-checked, unsigned proposal has all unresolved numeric training choices null.
6. Hosted CI actually executed the verifier and all declared tests with no skips; exact-head status should always be re-fetched if additional commits are pushed.
7. B1/B2 and all remaining closure checks stay **closed**. Any genuine later scientific approval is recorded prospectively in a new independently reviewed authority, never manufactured by altering a previously rejected gate.

**Current status:** `FULL104_METADATA_SECOND_PHYSICAL_REPLAY_PASS__SIX_OWN_SCHEMA_CANDIDATES_VALIDATED__ZERO_CLOSED__REAL_TRAINING_BLOCKED`. Work completed here is read-only/local physical rederivation, programmatic source validation and bounded hosted synthetic/contract red-teaming. Real biological efficacy, new GPU JEPA training and protected outcomes remain **unmeasured and unopened**.
