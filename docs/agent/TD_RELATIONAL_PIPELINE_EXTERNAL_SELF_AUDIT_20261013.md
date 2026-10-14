# TD relational synthetic → qualification pipeline external self-audit

Date: 2026-10-13
Reviewer posture: hostile external reviewer / fail closed
Status: `BLOCKED_BEFORE_BLINDED_EXECUTION__REPAIR_REQUIRED`

This review was performed after synthetic V2 preflight certification and before any `execute_blinded_fit(...)` call.

## Material findings

1. **Controller truth is co-transported with blinded inputs.** The synthetic V2 archive places `controller_manifest.json` in the same archive as pre-fit files. Directory separation is not custody.
2. **The current TD runner receives the controller path before blinded execution.** It delays reading the file, but the same process has the truth path from startup. Strong blindness requires two separate invocations.
3. **The controller hash is not a hiding commitment.** `controller_truth_sha256` commits to a small finite semantic mapping, but the V2 controller schema carries no high-entropy controller-only nonce. Offline mapping recovery is therefore a plausible pre-fit leak.
4. **Deterministic public realization reconstructs opaque semantics.** Synthetic V2 uses a public fixed capability→challenge permutation and fixed biological-role→control ordering.
5. **Source-visibility stress changes the deterministic triplet-cap seed.** The synthetic world changes `source`, while TD hashes `source` into triplet capping, confounding visibility stress with a different sampled subset.
6. **The five controller roles are not all materially constructed in V2.** Generic common-cell masks are relabeled as matched biological roles without prospective role-specific construction.
7. **Certification executes from the PR merge commit while reporting the head SHA.** The files are currently equivalent, but evidence identity should be exact.
8. **TD output path guards do not protect fit custody.** An output can be placed inside `fit_dir` and overwrite an authenticated fit input after validation.

## Required successor repairs

- split blinded fit and controller adjudication into two process phases;
- no controller artifact/path in phase-1 custody;
- controller manifest successor carries a 256-bit controller-only blind nonce;
- phase 2 accepts and verifies the exact frozen blinded-receipt SHA before reading controller truth;
- outputs cannot collide with or live inside authenticated fit custody;
- synthetic successor transports pre-fit and controller material separately;
- final realization mapping uses controller-only entropy;
- broad/source-stress pair shares the same sampling identity; only observation/support changes;
- role-faithful matched controls are prospectively built and structurally tested;
- certification checks out exact branch head and exact TD head.

The prior TD V2 implementation and synthetic V2 package remain preserved as historical engineering evidence. No biological test result exists to reinterpret.

Authority remains closed for real TD execution, target selection, TD60, Stage4, and training.
