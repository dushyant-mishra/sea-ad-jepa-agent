# V40 physical source + JUnit critical-test preflight — research, NOT B2

2026-09-26. Stacked on V39 PR #168 at `65675eed01e5fff579937176e01b154a98f1e457`. This is a **versioned candidate validator**, deliberately separate from the production `CriticalTestExecutionAuthorityV1` and current closure/issuer/guard schemas. Training, N1, protected confirmation, all fully closed current V5 roots remain OFF/zero.

## Historical gap being repaired

V30 proved self-consistent fabricated digests entered the original issuer; V34 now invokes the real typed 32-role validator; V36 makes the guard reissue before installing hooks, arming and executing a step. V39 physically proved that the *real typed critical-test parent* still accepts a user-declared test list, an unread arbitrary source SHA and fake `EXECUTED_PASS` statuses. Rerunning historical synthetic optimizer controls would not address this new upstream source/evidence gap.

## What V40 actually verifies

`critical_test_physical_preflight_research_v40.py` requires a **separately obtained expected SHA-256** for an immutable external suite manifest, not a digest copied from the manifest payload; physical local Git HEAD exactly equals frozen `source_commit`; each test-source file and distinct runner file is present under the checkout and matches its frozen SHA-256 from original bytes, rejecting symlink/path traversal; exact complete case identities are present *once each* in real JUnit XML with zero skipped, failed, errored or missing tests; and declared aggregate test counts must agree with actual case rows. Incomplete tests, duplicate names, mutated sources, stale commits and forged manifests anchored to a genuinely separate fixed expected digest fail closed.

The returned result has `locally_verified=True`, `external_ci_origin_authenticated=False`, `full_v5_graph_qualified=False`, and `training_authorized=False` **regardless** of passing tests. The local fixture is a brand-new tiny test Git repo, never confused with FULL104 or actual V5 root closure.

## Explicit security boundaries

1. An *argument* named `externally_trusted_manifest_sha256` does not manufacture reviewer custody or an independent root. The caller MUST obtain and lock it through separately reviewed governance before any physical preflight is authority.
2. Local JUnit XML can be fabricated by a dishonest caller. This validator checks syntax/content/source parity; it **does not verify that a CI provider actually ran these tests** or authenticate remote job identity, protected branch policy, runner provenance or artifact custody. A later trusted CI-API/artifact fetch and independently reviewed job/source binding is required.
3. Git HEAD proves only the checkout identity; a dirty working tree is acceptable ONLY because **all required test and runner paths are hashed by content**. It does not prove the actual test binary/data dependencies, loader behavior, environment, execution policy or scientific completeness. These must be separate reviewed manifest roles and predicates.
4. To eventually consume a V2 critical-test authority in production, freeze the exact required test IDs and all source/runner/requirements dependencies prospectively, authentically retrieve CI evidence, then add a typed migration of the V2 scientific closure, final issuer and optimizer guard. Do **not** silently replace existing V1 test semantics or claim that the old 33 graph is ready.
5. No old Stage81A3 TRAIN cache, historical T1/C2 gradient test or V4 teacher pilot becomes FULL104 production proof; no sealed/protected outcomes may be inspected to choose tests.

## V40 red-team controls

Dedicated hosted workflow pins 17 exact test identities (15 functions, one 3-way parameterization) with zero skips, failures or errors. Tests cover physical matching synthetic checkout/JUnit, suite and runner tampering, independently anchored forged manifest, changed Git HEAD, missing/extra/duplicate JUnit identities, 3 hidden nonpass statuses, falsified count, symlink escape, unsafe path, duplicate frozen IDs, illegal training flag and JUnit DTD/entity rejection. The positive local parity fixture explicitly asserts `external_ci_origin_authenticated=False`.

**Next genuine physical gate:** obtain the independently frozen required-test manifest and hosted CI raw test artifact/job provenance for current V5 at a reviewer-approved exact source commit, then apply these checks to authentic originals. This file and workflow alone can never set `training_authorized=True`.
