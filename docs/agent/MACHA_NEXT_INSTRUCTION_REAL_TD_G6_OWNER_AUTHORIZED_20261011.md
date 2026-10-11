# Macha next instruction — REAL target discovery: execute G6 once under owner authorization

Date: 2026-10-11

Lane: **REAL TARGET DISCOVERY ONLY**. Do not mix with the separate synthetic-dataset lane.

Owner/external-auditor state:

- qualified implementation: `fafd4309cc086c95076cefdc94064e8b66e58ae4`;
- qualification accepted: `217 passed / 0 failed / 0 skipped`;
- original PR #259 compatibility accepted: `1 passed / 0 skipped / 0 failed`;
- owner decision exists and is immutable;
- runtime authorization exists and is bound to that owner decision;
- G6/G7 integrity only is authorized;
- corrected biological replay, target selection, TD60 and training remain unauthorized.

## Exact owner authority

Owner decision path:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_fafd4309.json`

Owner decision physical SHA-256:

`36599b7ade189e051b6e156d53ea1acd4caf42794f26b152d7eada0513a1a273`

Decision:

`AUTHORIZE_G6_G7_INTEGRITY_ONLY`

Runtime authorization path:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_fafd4309.json`

Runtime authorization physical SHA-256:

`7cc66f601d6fc294ef9255f4e9ac4b1e1f16db56d1ddf52cf1fb839646fc91fa`

The authorization binds:

- implementation `fafd4309cc086c95076cefdc94064e8b66e58ae4`;
- common script `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`;
- G6 script `614af59cf6f4f0a8910235fcdef8b8b3ec1aae47ecf98c30bfaa3eaa1b3a07ad`;
- G7 script `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`;
- exact PR #259 driver `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- exact PR #259 mapping receipt `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
- exact replay manifest `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.

## Execute G6 once — canonical data machine only

1. Create a fresh clean detached worktree at exactly:
   `fafd4309cc086c95076cefdc94064e8b66e58ae4`.
2. Verify `git rev-parse HEAD` is exact and `git status --short` is empty.
3. Bring the owner-decision and runtime-authorization files into the execution environment **byte-for-byte**. Do not regenerate, reformat or normalize them. Verify the physical SHA-256 values above.
4. Verify the original physical PR #259 driver, mapping receipt and replay manifest bytes against their exact pins.
5. Verify every frozen input required by G6 before choosing/spending an output namespace, including the exact source H5AD tree, sample freeze, provenance, collision ledger, Macha freeze, TD artifacts ZIP and historical CSR arrays.
6. Choose a new, never-used G6 output directory.
7. Run the real G6 V2 entrypoint exactly once under the bound decision/authorization.
8. Preserve stdout/stderr, exact command, environment versions, start marker, receipt, manifest, values NPZ and metadata NPZ.
9. If G6 stops or fails for any reason, preserve the spent namespace and STOP. Do not retry under the same logical attempt and do not patch around the failure.
10. If G6 reports `PASS_TD_G6_SOURCE_LIBRARY_EXACT`, independently hash every G6 output and record the complete five-file namespace.
11. **STOP after G6. Do not run G7 yet.** The owner/external auditor must audit the real G6 receipt/materialization first.

## Forbidden

- no corrected TD56/57B/57C/59 replay;
- no TD60;
- no target selection;
- no representation selection;
- no Stage 4;
- no training;
- no use of the synthetic-dataset lane as biological evidence.

Current terminal before real G6:

`OWNER_AUTHORIZED_G6G7_INTEGRITY_ONLY__G6_READY_ON_CANONICAL_DATA_MACHINE__G7_WAIT_FOR_EXTERNAL_G6_AUDIT__NO_BIOLOGICAL_REPLAY_AUTHORITY`
