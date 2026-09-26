# V41 independent original GitHub CI-provider replay — physical original artifact (non-authorizing)

Date 2026-09-26. Stacked on PR #172 V40 source/JUnit preflight, following V39 PR #168 critical-execution evidence red-team. Do NOT collapse branches, silently mutate prior frozen policies or promote development tests to FULL104.

## The genuinely new evidence boundary

V40's 17 synthetic tests on exact commit `1510b52417704c710ee23b4e60238e65c3acba74` passed GitHub Actions run `36252237835`. That workflow now uploads the actual test-run JUnit `v40.xml` and runner log `v40.log` as provider-backed artifact ID `10909547327`, SHA-256 `a0b77345ef65e8b9196fb616488550f0b2cf57aea773dd9d25922a65879266ef` and name `v40-original-junit-run-evidence`.

The independent V41 audit is a *different later workflow*, pinned to that exact original SHA/run/job/artifact tuple. Its own read-only `GITHUB_TOKEN` queries **GitHub's original Actions API** for the actual completed/successful PR run, original workflow path, exact commit, one successful named job and both passed test/artifact-upload steps; separately retrieves the original archived artifact, verifies GitHub's provider-reported archive SHA-256 against a value frozen in this audit source, rehashes the downloaded bytes, checks ZIP integrity and expected exact two file names, reparses original JUnit and requires the **17 exact** test names without duplicates, failures, errors or skips, and independently checks the runner log's actual 17-pass and local/non-authorizing marker. A redirect handler explicitly drops the GitHub bearer token on artifact-storage redirects.

This improves V40's `external_ci_origin_authenticated=False` limitation **for the original 17 synthetic research tests only**. It is a verification of an independently fetched provider event and its original test bytes, not a replacement for prospective original current-V5 source/test manifest, real original FULL104 critical test suite execution or B1/B2 gate. This audit has no production integration or secret key invented in source.

## Remaining authority gaps after success

- All 17 tests are synthetic V40 preflight tests, not the independently chosen actual current-V5 33-root required critical-test manifest or source-byte complete runtime.
- The fixed SHA tuple is **frozen in this audit**, but prospective reviewer approval/custody of the *real* V5 suite, runner, full dependencies, protected registry, physical source manifests and original CI artifacts still does not exist.
- The same repository author can change a draft audit before review; trust must include protected reviewer/branch governance and an independently inspected audit source, not just the job's green conclusion.
- Physical GitHub artifact retention is time-limited; export externally to immutably retained reviewed evidence for a production successor, and fail closed on disappearance.
- The current V1 `CriticalTestExecutionAuthorityV1`, V2 closure, V34 issuer and V36 optimizer guard have **not** been silently loosened or switched to V40/V41. Training remains OFF; protected outcomes untouched; 0/33 fully closed current V5 roots.

Review the V41 workflow's actual log, not just job status. A synthetic positive control is never production authorization.
