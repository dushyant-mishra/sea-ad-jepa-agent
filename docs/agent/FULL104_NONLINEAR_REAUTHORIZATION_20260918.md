# FULL104 nonlinear challenge parameter re-authorization — 2026-09-18

The nonlinear challenge keeps the historical tree-ensemble capacity as a
pre-FULL104 confirmation hypothesis, not as a terminal result.

Current explicit model settings are 32 screened features, learning rate 0.1,
50 iterations, 15 leaves, minimum leaf size 20, L2 regularization 1.0 and 255
bins. Settings that had previously been implicit library defaults are now
spelled out so a package upgrade cannot silently change the challenge.

The historical random seed is not reused. The current seed is derived from the
current primary-parameter, outer-split and target-panel authority roots.

FULL104 sampling is new: at most 256 deterministic cells per donor, with equal
total training weight per donor. Across 104 donors this caps the challenge at
26,624 sampled cells while preserving every donor as an independent unit.

The historical nonlinear script and summary are bound only to document why this
model capacity is being independently re-tested. They cannot select the masking
policy or authorize training.
