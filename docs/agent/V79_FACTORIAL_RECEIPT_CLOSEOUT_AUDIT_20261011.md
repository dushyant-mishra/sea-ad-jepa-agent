# V79 Factorial Receipt Closeout Audit — 2026-10-11

## Scope

This audit closes the final internal engineering item that remained in the hardened factorial handoff: bounded, atomic, identity-scrubbed scientific receipt serialization.

Current implementation authority:
- PR #262
- branch `fix/v79-factorial-memory-hardening-20261010`
- head `9110c3fae6d34e43463d56631f43004bda33beb8`

No H0/H1/H2/H3/C_OBS/C_BIO scientific outcome was generated or read.

## Receipt hardening

`run_v79_factorial_tournament.py` now enforces a prospective receipt contract before scientific execution is ever enabled:

1. scientific receipt payloads are capped at 1 MiB JSON;
2. retained correlation matrices are refused rather than serialized;
3. selected universe positions and internal gene/address identifiers are refused;
4. recognizable gene identifiers in string payloads are refused;
5. non-finite JSON values are refused by strict serialization;
6. receipt writes use an fsynced same-directory temporary file followed by `os.replace`, so a crash cannot leave a partially written authoritative JSON at the final path.

The implementation remains fail-closed. It does not silently strip forbidden fields into apparent compliance.

## Verification

Fresh GitHub Actions evidence:
- run `38147114407`
- job `114492689105`
- conclusion `SUCCESS`
- focused suite: **94 passed in 1.04 s**

The run explicitly executed:
`tests/test_v79_factorial_receipt_contract_v1.py`

Those tests verify:
- internal correlation matrices are rejected;
- selected-universe/address identity is rejected;
- payloads above the fixed bound are rejected;
- bounded JSON is written atomically with no residual temporary file.

The same run also repeated the untouched-#253 versus hardened implementation fixture under one runtime. Integer count hash remained:
`3d1f4e7a710d96d2328a5deea8fb1919a122aa7902206594a0609a9d53b59afa`

Same-runner capture hash remained:
`51eb035286393d38733c3224ae31b5a518afdd6e6a46d5baaf7a0320e9d68f12`

## Macha integration implications

The factorial lane must consume no Macha output until PR #261 independently reaches a qualified terminal state.

Recent controller/code review adds the following acceptance conditions for any future Macha-derived authority:
- detection V1 failure at S4 cannot be hidden or reclassified;
- any V2 detection authority must come from the prospectively frozen final V2 configuration and complete qualified recovery, not launcher-specific accidental settings;
- code snapshot/configuration identity must be carried by the authority;
- snapshot-equivalence claims must cover the recovery paths actually consumed, not only the basic S1 path;
- provisional/local-only sampler outputs are not authority;
- corrected-TRAIN fitting must remain blocked until simulation qualification is complete;
- the eventual real-data workflow should use a compact authenticated analysis cache rather than repeatedly rebuilding the full 41,238-column TRAIN matrix for every fit.

These requirements do not alter H0-H3 outcomes because no outcome has been run.

## Remaining blockers are external, not internal engineering work

The factorial implementation now has no known unfinished internal engineering item before final preexecution review.

Definitive scientific execution remains blocked on:
1. independent qualification and acceptance/rejection of Macha biology and observation authorities;
2. prospective freezing of the final H1/H2 authority package;
3. fresh byte-authenticated preexecution replay using the final authority bytes, external registry bytes and repaired-marginal custody bytes;
4. independent review of that fresh gate receipt.

Only after those steps may the one-shot scientific tournament be enabled.

## Terminal audit state

`FACTORIAL_INTERNAL_ENGINEERING_CLOSED__MACHA_AUTHORITY_PENDING__FINAL_BYTE_CUSTODY_REPLAY_PENDING__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`

Still unauthorized:
- JEPA training/checkpoints;
- V78 retuning;
- TEST/Morabito;
- pathology;
- target-discovery modification;
- SCENIC+/ATAC target evidence in planted truth;
- post-outcome arm rescue.
