# F1 HC3 Command 15B provenance repair — external-review handoff

Terminal: `PASS_F1_HC3_15B_PROVENANCE_REPAIR_AWAITING_EXTERNAL_REVIEW`.

- The frozen 15B package remains byte-for-byte unchanged and is bound by manifest SHA-256 `a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174`.
- The exact selection-contract bytes are SHA-256 `3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac`.
- No pre-existing Git blob/commit or independent pre-result timestamp artifact was recoverable. The truthful chronology claim is `EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE`.
- Filesystem creation/modification metadata is recorded but is not represented as cryptographic time proof.
- Nine existing reviews are represented as structured records with exact content hashes; all bind the same frozen 15B manifest and selected-design SHA.
- All six required internal PASS reviews are authenticated by reviewer/lens IDs, exact source-section bytes, record hashes, and authority hashes. The three post-15B external reviews are preserved with their original PASS/CONCERN judgments.
- Independent validation confirms every 15B byte, chronology limitation, review record, source section and authority binding.
- No scientific judgment was regenerated. No nuisance rank, donor, threshold, HC3 rule, selection criterion, expression, outcome, model, training, EMA, F1 run, or 15C integration was introduced.

A separate local root anchor binds this supplemental package manifest after atomic publication. External review remains required before 15C.
