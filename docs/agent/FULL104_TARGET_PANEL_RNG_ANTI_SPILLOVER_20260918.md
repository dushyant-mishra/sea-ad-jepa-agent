# FULL104 target panel and RNG anti-spillover successor — 2026-09-18

The production target count is not inherited from discovery target panels or
test fixtures. Target selection is deterministic only after a separate,
outcome-blind runtime/precision decision supplies the target count.

Given that count, the selector hashes the current 17,053-target eligibility
receipt plus each eligible address. Expression values, masking outcomes,
historical target lists and exploratory rankings are not inputs.

The masking RNG no longer accepts a hand-entered global production seed. V2
derives it from the current registry, outer split, target panel and burden
authority roots. This prevents a historical discovery seed from being carried
forward merely because it was already used.
