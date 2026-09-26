# V40 remote critical-test JUnit evidence experiment — NOT B2

Date 2026-09-26. Stacked on V39 draft PR #168. Main production and frozen existing `CriticalTestExecutionAuthorityV1` are deliberately untouched. Training remains OFF.

## Why this is new and limited

V30 exposed fabricated top-level closure digests; V34 added actual typed closure revalidation; V36 added guard-side live issuer reissuance; V39 showed the real typed *parent* `CriticalTestExecutionAuthorityV1` still accepts arbitrary caller-supplied test IDs, `EXECUTED_PASS` and unread source SHA. Do not repeat V39 toy test counts as physical execution.

This V40 successor is an **independent read-only measurement** of one fixed, non-authorizing seven-test V39 workflow. First job runs the unaltered seven V39 tests and publishes the actual original JUnit XML as a GitHub Actions artifact. A **separate second job** refetches the run, path-identified workflow, exact producing job and actual artifact via GitHub REST API, requires its run-head SHA equals the exact externally provided SHA, checks completed successful producing job, artifact-run identity and unexpired unique name, enforces a single safe JUnit member, recomputes exact seven named test identities/counts and zero skipped/failures/errors, then independently refetches the executed test source original bytes pinned to that run head via the GitHub contents API and recomputes the Git blob SHA1 and source SHA256.

The ten test-only mocked-transport controls prove parser/negative-case mechanics; their stubbed success is **never** an independent remote authority. The second job's actual GitHub read is required for the only physical remote result. This same-workflow experiment is also **not** an independent B1 reviewer-approved full critical-test suite: the CI workflow and code live on an experimental PR branch and the seven tests are diagnostic V39 tests, not a prospectively frozen full current-V5 critical-test manifest.

## Trusted inputs / remaining attack boundaries

- External controlling reviewer must separately pin the expected run HEAD, workflow path/byte SHA, complete approved suite source and test IDs, runner/environment policy, artifact SHA, and original GitHub API response origin. This experiment only binds the run's own seven diagnostic tests. Its source-byte read detects fabricated source-hash fields but not malicious edits to the unreviewed branch.
- GitHub API authenticated transport (scoped `actions:read,contents:read` GITHUB_TOKEN) is used, not an arbitrary caller-supplied JSON fixture; archive retrieval uses the GitHub artifact endpoint with documented signed redirect. The local test-only fake transport is explicitly not production-proof.
- Runtime run/job success plus artifact JUnit are necessary evidence, not sufficient for trustworthy biology, inference, complete V5 critical graph, signed source governance or unforgeable execution against a compromised GitHub account.
- The original V1 critical authority and V36 guard are unchanged: no implicit promotion, no new critical root or B2 authorization. Proposed full V2 schema migration requires separate frozen test vocabulary and reviewer approval, actual all-suite CI artifact and source/runtime evidence, and independent on-GPU revalidation where needed.

**Stop boundaries:** do not read protected FULL104/D_shared/N1 outcomes, do not run production training, do not use V39 diagnostic tests as a critical-suite replacement. Never claim `critical_test_execution_root CLOSED` from V40.
