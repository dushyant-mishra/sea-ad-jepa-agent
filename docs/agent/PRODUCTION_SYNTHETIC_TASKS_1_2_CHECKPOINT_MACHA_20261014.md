# Production synthetic V3.1.1 — Tasks 1–2 checkpoint (Macha controller)

Date: 2026-10-14.

Status: `TASKS_1_2_COMPLETE_AND_REVIEWED__TASK_3_NOT_STARTED_BY_OWNER_INSTRUCTION__STOP_FOR_REVIEW_AND_AUDIT`

Authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This file is non-controlling (V3.1.1 E7). It follows the §9 checkpoint format of the Tasks 1–3 execution handoff (`plan/production-synthetic-v3-1-1-20261014` @ `2c2723a1`), scoped to Tasks 1–2. The owner instructed a stop after Task 2 for review and audit.

## Bottom line

**Good news.** The first two building blocks of the sealed synthetic testbed are written, tested and reviewed:
- **Task 1, canonical identity.** How artifacts get stable fingerprints.
- **Task 2, custody.** Sealed seeds, version freezing, the exposure ledger and the secret withheld family.

Each passed a fresh spec reviewer and a fresh code-quality reviewer.

**What it means.** The reviews found real holes in every Task 2 round, and each was closed. For example, swapping in an easier withheld family, or rerolling sealed draws by creating near-identical versions. The custody layer now fails closed on all of them. Several protections still depend on later tasks doing their part; §5 lists them as binding obligations.

## 1. Exact identities

| item | value |
|---|---|
| implementation branch | `implementation/production-synthetic-v3-1-1-20261014` |
| head at checkpoint | `ff597faf2182522a320ec5322f8db9b67c9c6094`, plus this checkpoint commit |
| stacked on | plan head `befd95c2` (PR #356) |
| plan branch now | `2c2723a1` — `BRANCH_MOVED_NO_SCIENTIFIC_EXECUTABLE_CHANGE` (two non-authorizing docs: a dependency delta and a Tasks 1–3 handoff; Tasks 1–3 unchanged) |
| controlling specs | V3.1 blob `48e71346…`, SHA-256 `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c`; V3.1.1 blob `977faa75…`, SHA-256 `ab1ae1bb67765cc025f580205d7c082ee4af470dd39ef23c4f000414e8e9363f` |
| environment | Python 3.11.15, numpy 2.4.6, pytest 9.1.1 (`sea-ad-jepa-v3`), Windows 11 |
| test evidence class | **local execution only, not CI.** No workflow exists yet (Task 12). |

Command (from the worktree root):
`PYTHONDONTWRITEBYTECODE=1 C:/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe -B -m pytest -p no:cacheprovider tests/production_synthetic -q`

Output at `ff597faf`: `331 passed, 1 skipped in 9.83s`.

The skip is the Task 1 rejection test for numpy floats wider than float64. `np.longdouble` is 8 bytes on Windows, so the test needs a Linux/WSL run to exercise the rule.

## 2. Task 1 — canonical identity and serialization

| | |
|---|---|
| files | `scripts/production_synthetic/canonical_v1.py`, `tests/production_synthetic/test_canonical_v1.py` |
| commits | `aa497d9d` feat → `986514f0` → `4cd4d36f` → `5ea1c2e6` fixes → `c76e824d` docs |
| spec review | ✅ after two fix rounds: strict JSON loader; nonzero underflow-to-zero rejected; normalization-colliding keys rejected; then a confirmation of the API split |
| quality review | **Ready to merge: Yes**, after one fix round: known-answer tests; a byte-level docstring spec; explicit `semantic_text_sha256` and `semantic_json_file_sha256` |
| independent check | the quality reviewer recomputed all six frozen known-answer digests from the docstring alone, without importing the module: all matched |

## 3. Task 2 — custody, commit/reveal and identity-keyed RNG

| | |
|---|---|
| files | `scripts/production_synthetic/custody_v1.py` (2413 lines at ff597faf), `tests/production_synthetic/test_custody_v1.py`, `tests/production_synthetic/test_custody_v1_hostile.py`, `tests/production_synthetic/custody_fixtures_v1.py` |
| commits | `3306ddc8` feat → `38bd6d1f` → `c1bb5d11` → `c4ed2463` → `e7014599` → `dc4cc42a` → `44bed54c` fixes → `ff597faf` refactor |
| spec review | ✅ at `dc4cc42a` after five fix rounds; behaviour re-confirmed ✅ at `ff597faf` |
| quality review | **Ready to merge: Yes** at `ff597faf`, after one fix round |
| mutation checks (implementer, local) | 59/62 → 92/94 → 109/113 → 7/8 → 16/17 → 8/9 → 17/17. Every survivor was judged unreachable or implied by another rule. |
| performance (quality reviewer) | 168 KB spec, 234 entries: build 128 s → 3.5 s, replay 67 s → 1.9 s; 1,000-entry ledger builds in about 4 s; queries ≤ 50 ms |

Holes found by review and closed:
1. The "can't get easier" check ignored most frozen components.
2. A replaced version could still be committed and exposed.
3. The withheld commitment could use the early-revealed debug nonce.
4. An easier withheld family could be swapped in.
5. A no-change successor could reroll the sealed draws.
6. A reused family stayed "secret" after its reveal.
7. A class-nonce reveal leaked a family shared by an open run.
8. A successor could revert to an already-public family.
9. Renaming a method reset its draw count.
10. A late exposure could follow the fit freeze.
11. The scanner crashed on realistic secret sizes.
12. Eligibility read True before the version's own reveal.
13. A full ledger build took about two minutes.

## 4. Controller decisions taken during execution (recorded for audit)

Task 1:
- **Strict canonical policy.** `None` is the only missing value; NaN/Inf are rejected; `-0.0` → `0.0`; `1.0` ≠ `1`; `bool` ≠ `int`; code-point key order (not JCS).
- **Order-sensitive registry digest.** Plus an identity-keyed, order-invariant row-set digest.
- **Bytes rejected by `semantic_sha256`.** This replaces my initial decision 3: explicit text and JSON-file entry points remove the type-dispatch ambiguity.

Task 2:
- **E1 after exposure.** Only harder difficulty levels and added challenge names are allowed without a defect record. Any other component change needs a generator-side defect record → `POST_EXPOSURE_VERSION` / `NEW_SCIENTIFIC_TESTBED`. A requalification prerequisite is required before exposure.
- **Lineage.** Strictly linear; a superseded version is never committed or exposed again; one successor per parent.
- **Withheld nonce.** The commitment uses the SYNTH_QUALIFICATION nonce (E2 literal), verified at reveal.
- **Precommitment hash.** The withheld commitment binds a hash of the spec without the commitment, because E2 as written is circular (see §6).
- **Withheld family frozen per lineage** (`UNCHANGED` / `CHANGED_BY_DEFECT`), with hash checks at reveal.
- **Reveal guards.** Open-run guards on withheld and class-nonce reveals across family groups.
- **Eligibility.** `withheld_check_eligible` fails closed for public or reused families and is final only after the version's own reveal.
- **Rerolls.** Exact copies are refused. Near-copies are made visible by draw counting: per method (method id = 64-hex content digest) and lineage-wide.
- **Fit freeze.** Per exposure; late exposures refused.

## 5. Deferred minors, parked rulings and binding downstream obligations

Deferred minors (not blocking; recommended before Task 3):
- **D1.** `CustodyLedger._append` / `from_bytes` use a catch-all `except Exception`, which wraps internal bugs as custody refusals. Only 23 of 182 `pytest.raises(CustodyError)` tests match the message. Fix: include `type(exc).__name__` in the wrapped message, and add `match=` to the late-exposure, reveal-gating and W1/W2 tests.
- **D2.** Task 1's character-by-character string escaping is about 9× slower than `json.dumps`. This is safe to optimize now that known-answer tests exist.
- **D3.** The wide-float rejection test is unexercised on Windows (§1).
- **D4.** `draw_index_tag` is kept in the RNG identity vocabulary. Seed-shopping through it would need a code change, which creates a new version.

Binding obligations on Tasks 9/11/12. These are listed in the module's DOWNSTREAM OBLIGATIONS section and are not enforceable inside Task 2:
- **O1.** One ledger per testbed, anchored from genesis. A fresh ledger that freezes an easier generator as a new lineage root bypasses E1/W1/W2.
- **O2.** The ledger head must be published after every entry, and the expected head checked. Exposure erasure by wholesale re-chaining is detectable only against a published head; this is the honest answer to the handoff's "exposure cannot be erased" check.
- **O3.** Every qualification claim reports both `qualification_draws_for_method` and `qualification_draws_in_lineage`, and accounts for multiplicity.
- **O4.** `withheld_check_eligible` is consulted only after the version's own withheld reveal.
- **O5.** Realization content is regenerated from the sealed root at reveal; same-ID content swaps are otherwise undetectable.
- **O6.** The secret scan runs on a full `git archive` export of each published commit, not a sparse worktree.
- **O7.** Withheld-family worlds are emitted inside the SYNTH_QUALIFICATION budget.
- **O8.** Defect justifications are attested declarations that need reviewer audit.

Labelled `PROSPECTIVE_CONVENTION`s:
- ≥16 distinct byte values in nonces/roots;
- 16-byte minimum for scanned secrets;
- decimal needle only for secrets ≤64 bytes and ≥20 digits;
- a 10 s performance bound in tests.

## 6. Questions for the deciding lane (Sol) — not resolved here

1. **E2 circularity (erratum candidate).** `H(withheld_spec ‖ nonce ‖ generator_semantic_hash ‖ tag)` cannot bind a generator hash that itself contains the commitment. The implementation binds a precommitment hash; the controlling text should say so.
2. **A fresh withheld family after a reveal** is not implemented. A version that reuses an already-public family is fail-closed ineligible.
3. **V3.1 §2.2 and reader_fit.** Is `reader_fit` a "development population used to evaluate downstream claims"? If so, it cannot be a calibration source for Task 3's firewall.
4. **Correction of my earlier suggestion.** Support-hole facts derived from reader-validation/oracle metadata cannot be `AUTHENTICATED_EMPIRICAL_CALIBRATION`. They may enter only as labelled `PROSPECTIVE_CONVENTION` stress structure, or be recomputed from reader-fit donors. These are: NPH52 0/2 held-out donors; 4,894 NPH52-only addresses never measured in reader-validation; SEA_AD held-out subclass donor counts. The post-Macha dependency delta lists them as "reproduce prospectively"; Task 3 must apply this restriction.
5. **From the real-data review.**
   - The held-out definition per gate: leave-one-donor-out within reader-fit versus reader-validation/oracle.
   - Whether technical calibration on hold-out RNA spends the hold-out.

## 7. Explicit statements

- No Critical or Important finding is open for Task 1 or Task 2.
- No production realization was created; only fixture and dummy worlds were used in tests.
- No real withheld spec or nonce was authored, shared or committed. Tests use dummy secrets generated in-test.
- None of `STOP_A_FIRST_PRODUCTION_REALIZATION`, `STOP_B_SEALED_QUALIFICATION`, `STOP_C_FINALIZER` was crossed.
- Task 3 was **not** started (owner instruction). Task 4 remains locked until Task 3 clears its reviews and the full post-Task-3 checkpoint is audited.
- No real data, candidate outcome, pathology or DEV/SEALED object was read by this implementation work.

## 8. Moving real-lane dependency heads at checkpoint

All are open PRs. Each is at exactly the head recorded in the plan table or the post-Macha dependency delta, so each is `AT_RECORDED_HEAD__NO_MOVEMENT`.

| PR | head | PR | head |
|---|---|---|---|
| #343 | `82d17bfb` | #355 | `6e5182e2` |
| #346 | `5a314bde` | #357 | `c174d052` |
| #349 | `1ab453e5` | #358 | `b7c317c6` |
| #350 | `9b9078c1` | #359 | `bfb1a892` |
| #351 | `2abcb9fe` | #360 | `01ebdb93` |
| #352 | `bb1e35d3` | #361 | `b2e27a87` |
| #353 | `1df20029` | #362 | `5a711f9a` |
| #354 | `d9004730` | #363 | `fcb47d05` |

The plan PR #356 itself is at `2c2723a1` (documentation-only movement, §1).

## 9. Review evidence

The reviewers' probe scripts and outputs are copied into `docs/agent/production_synthetic_tasks_1_2_review_evidence_20261014/` (29 files, SHA-256 in `SHA256SUMS.txt`):
- `t1_spec/`
- `t1_quality/` (including `indep_kat.py`, the independent known-answer recomputation)
- `t2_spec/` (probes 1–9)
- `t2_quality/`

These are local execution evidence. They are not re-executed by CI.

## 10. Next lawful step

1. Owner/Sol audit of this checkpoint.
2. Optionally fix D1 before Task 3.
3. Task 3 (calibration firewall, numeric provenance, realism contract) under the same per-task protocol, carrying §6 item 4.
4. The full post-Task-3 checkpoint, then audit, before Task 4.
