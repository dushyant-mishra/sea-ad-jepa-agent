# V29 all-repository-branch tip audit — independent source discovery successor

This extends the separately immutable 114-open-PR file-tree sweep in PR154. At the fixed, re-fetched September26 GitHub snapshot there were **263 live branches pointing to 232 distinct tip commits**. The PR154 snapshot covers **114** of those tips; we fetched the **118 additional branch-tip recursive trees**, all without API errors or truncation. Both branch snapshots were re-fetched unchanged immediately before publication. The total bounded path-filter sweep now covers **ALL 232 CURRENT branch tips**, not all historical commits and **not** any raw bytes solely on the separate GPU laptop.

Among the 118 additional heads the filter returned **233 head×JSON appearances** from **41 distinct path+Git blob SHA pairs**. Ten of those 41 were already present in the 114 open-PR candidate set, giving **31 additional unique path+SHA versions** and **49 total unique path+SHA variants** in the combined branch/PR scope. This is a deduplicated filename/blob inventory, **not 49 current V5 authority artifacts** or new training permission. The complete 263 names→tip SHAs and all 31 extra candidate paths and contributing branches are in the machine-readable report.

Nine potentially confusing source-specific artifacts were actually opened and their declared schema/status inspected:
- V5 EMA exposure derivation is a *prospective rule candidate*: actual numeric half-life is unfrozen, so it cannot be promoted into current `EmaTimescaleAuthorityV2`.
- The V5 schedule-governance candidate **explicitly says no active production schedule authority**; its full-coverage V3 candidate awaits independent review.
- Prospective D_shared **dimension-precision** authority is for a different estimand/heldout chain, not an automatic substitute for base-V5 `QualificationPrecisionAuthorityV1`; G5 remains sealed.
- Both historical C2 critical-test manifests are declarations of past test sets. The GPU variant explicitly requires historical **128×8 / 48 protected** geometry, which the current104 production authority must not silently inherit.
- The historical real-data smoke report is specifically **mechanics-only nonauthority**, not actual authorized FULL104 V5 training.
- FULL104 reconnaissance remains outcome-blind and not D_shared result or training authority.
- The support-family mass source is an earlier, unissued weighting candidate, not authority for an arbitrary frozen split.
- An old dataset-first schedule V3 is explicitly a bounded mechanics proposal without execution authority.

The other 22 new path+SHA versions were **not individually source-schema validated**, including historical handoff manifests and older method results. Their status stays path-only, not a statement of global absence. New own-class validations actually executed by this branch-tip audit: **zero**; new V2 closure roots: **zero**. PR149's six originally validated candidates stand, with the two V3-vs-V1 consumer mismatches independently demonstrated in PR151. The owner scientific decisions, exactly 33 root slots, B1 frozen reader_fit contract, authentic original Level4 block-manifest byte check and GPU disk inspection remain separate tasks. No re-run of PR146/PR149 metadata extraction, no false S9 BLAS alarm, no protected data or training.

Red-team: `PYTHONPATH=. python -m pytest -q tests/test_v29_all_branch_tip_scope.py`. Its fixtures reject missing branches, duplicate tip accounting, inflated closure, false GPU access, historical-critical-test promotion, EMA defaults and any reclassification of path-only hits as verified production authorities.
