# Macha — G7 one-shot runbook at ff4a21f9

## Authority

Replacement G6 is externally accepted.

Fresh operational release:

`custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json`

SHA-256:

`19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee`

Scope:

`EXECUTE_G7_ONCE_AT_ff4a21f9__AGAINST_ACCEPTED_G6__FRESH_OUTPUT__STOP_FOR_EXTERNAL_AUDIT`

This fresh operational file is a governance release after external G6 acceptance. The G7 executable itself intentionally consumes the same exact G6/G7 integrity authority bytes as G6:

- owner decision SHA-256 `3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`
- runtime value authorization SHA-256 `28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Do not alter or reserialize those code-consumed files.

## Exact executable

Detached clean worktree at:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Qualified G7 SHA-256:

`f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Entrypoint:

`scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`

## Accepted G6 prerequisite

Use the immutable accepted G6 namespace only.

Required hashes:

- `G6_EXECUTION_START.json` `49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1`
- `G6_RECEIPT.json` `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`
- `MANIFEST.json` `4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf`
- values NPZ `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`
- metadata NPZ `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`

The G7 code independently validates the complete G6 namespace, authority trace, hashes, structure, Sample-A identities and frozen replay-address geometry before spending the G7 attempt.

## Pre-start checks

Before the G7 start marker can exist:

1. Verify clean detached HEAD exactly `ff4a21f9...`.
2. Verify the G7 script SHA above and the qualified common/G6 identities.
3. Verify the fresh G7 operational authorization SHA.
4. Verify the original code-consumed owner/runtime authorization SHA values above.
5. Verify the accepted G6 namespace and all five artifact hashes.
6. Verify the exact PR259 preflight, mapping receipt and replay manifest bytes.
7. Verify Sample-A freeze, provenance, collision ledger and Macha/S174 freeze pins.
8. Verify the G1b authority and S174 cache are present at their frozen locations.
9. Choose a fresh never-used G7 output receipt path. The adjacent `.STARTED_NOT_A_PASS.json` path must also not exist.

Any pre-start mismatch means STOP before spending G7.

## G7 arguments

The executable requires exactly these logical inputs:

- `--preflight-result`
- `--mapping-receipt`
- `--value-authorization`
- `--owner-decision`
- `--g6-receipt`
- `--replay-manifest`
- `--sample-freeze`
- `--provenance`
- `--collision-ledger`
- `--macha-freeze`
- `--s174-cache-root`
- `--source-root`
- `--out`

Use the already authenticated paths from the accepted G6 run and the frozen S174/G1b substrate. Do not substitute semantically equivalent copies where the code requires exact physical hashes.

## One-shot rule

G7 creates an immutable start marker before value-bearing cross-check work.

Once that marker exists, the attempt is spent. Preserve PASS, FAIL, NOT_ESTIMABLE, exception or partial outcome exactly. Do not delete the marker, repair the output in place, or rerun using the same output name.

## Expected terminals

PASS:

`PASS_TD_G7_S174_EXACT_OVERLAP`

Mismatch/failure terminal:

`STOP_TD_G7_S174_CROSSCHECK_MISMATCH`

No natural overlap:

`NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`

`NOT_ESTIMABLE` is not a biological PASS.

## Return to auditor

Return:

- exact command
- exact HEAD and clean-worktree evidence before/after
- Python/package environment
- fresh G7 operational authorization hash
- code-consumed owner/runtime authorization hashes
- accepted G6 five-file hashes
- G7 start-marker hash
- G7 receipt hash if written
- terminal status
- overlap-cell count
- checked-address count
- mismatch count
- per-matrix/source diagnostics from the receipt
- S174 shard authentication summary
- physical source authentication summary
- stdout/stderr and exit code
- confirmation that no downstream task ran.

## STOP

**STOP AFTER G7.**

Do not run corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4 or training.

Those require a new decision after external G7 audit.
