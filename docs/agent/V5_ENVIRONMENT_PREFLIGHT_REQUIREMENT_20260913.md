# V5 environment preflight requirement — 2026-09-13

Status: `REQUIRED_BEFORE_LOCAL_OR_HEAVY_EXECUTION`

Claude's heavy-machine verification demonstrated that the relevant V5 suites cannot collect in the default conda environment because the package import path requires torch, while the documented project environment `sea-ad-jepa-v3` executes them successfully.

This is an operational authority risk: an unavailable test environment must never be reported as a pass, and skipped/uncollected tests must never be treated as green evidence.

Before any conclusion-bearing local/heavy V5 execution, record:

- active environment name;
- Python version;
- torch version;
- CUDA availability and device when GPU execution is required;
- import success for `sea_ad_jepa.v5`;
- collection count for the declared test suites;
- passed/failed/skipped/error counts;
- exact git HEAD;
- worktree cleanliness;
- `core.autocrlf` and relevant `.gitattributes` resolution when hash-bound text authorities are read.

Fail closed on:

- collection error;
- required dependency missing;
- skipped critical test;
- wrong environment where the required suite cannot execute;
- dirty worktree affecting authority files;
- EOL translation of hash-bound authority bytes.

Current documented heavy-machine environment:

`sea-ad-jepa-v3`

This document defines the requirement only. An executable preflight script/test is still to be implemented.

`training_authorized = false`
