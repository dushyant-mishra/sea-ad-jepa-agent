# TD G7 external audit checklist — ff4a21f9 — 2026-10-11

This document is an audit checklist only. It creates no execution, biological-replay, target-selection, TD60, Stage4, or training authority.

## Frozen execution identity

- implementation commit: `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`
- G7 script SHA-256: `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`
- accepted G6 evidence commit: `c595af589821bee28eb77e88e44b79dc81835e7a`
- accepted G6 receipt SHA-256: `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`
- accepted G6 values SHA-256: `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`
- accepted G6 metadata SHA-256: `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`
- G7 operational authorization SHA-256: `19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee`
- code-consumed owner decision SHA-256: `3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`
- code-consumed runtime authorization SHA-256: `28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Expected PASS terminal:

`PASS_TD_G7_S174_EXACT_OVERLAP`

## Audit requirements when Macha returns

1. Exact code identity: HEAD must be `ff4a21f9...`; worktree clean before and after; G7/common/G6 hashes must match the qualified identities.
2. One-shot custody: fresh G7 output path and fresh attempt marker; no pre-existing receipt/output; no in-place repair or rerun after marker creation.
3. Authority binding: the run must use the exact operational-release record above and the exact code-consumed owner/runtime bytes required by the executable.
4. Accepted G6 prerequisite: G7 must re-verify the complete five-file G6 namespace, receipt/manifest/start-marker authority trace, G6 artifact hashes and structural payload validity before the G7 value comparison.
5. S174 authority: exact G1b PASS result/freeze must authenticate; every rebuilt-cache shard used by G7 must match its frozen SHA-256 and geometry.
6. Physical source custody: each HVS/SEA source actually opened by G7 must hash to its frozen source identity immediately before value use.
7. Overlap accounting: record exact overlap-cell count, exact number of replay addresses checked, per-matrix accounting and total mismatch count.
8. PASS semantics: PASS requires nonzero natural overlap and zero mismatches. Zero overlap is `NOT_ESTIMABLE`, not PASS. Any mismatch is a G7 failure/stop condition.
9. Output custody: capture the G7 receipt SHA-256, attempt-marker SHA-256, stdout, stderr, exact command, environment, exit code, timing and all warnings.
10. Downstream stop: corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4 and training must remain untouched.

## Interpretation boundary

G7 is an integrity cross-check between corrected physical H5AD values and the separately authorized S174 substrate on overlapping natural cells at the exact frozen replay addresses. A G7 PASS is not biological validation and does not select a target.

Only after external acceptance of G7 may a separate corrected-replay authority for TD56/57B/57C/59 be considered.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
