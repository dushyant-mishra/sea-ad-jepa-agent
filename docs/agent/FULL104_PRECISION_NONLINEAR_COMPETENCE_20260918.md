# FULL104 precision and nonlinear competence successor — 2026-09-18

Status: prospective only; terminal FULL104 masking outcomes unopened; training off.

Two gaps are closed here.

## 1. 128 targets is a planning size, not proof of precision

The historical pre-FULL104 32-target challenge had its widest nonlinear 95% half-width
at about 0.00492. Under ordinary square-root scaling, 128 targets projects to about
0.00246. V4 therefore freezes a conservative 0.003 maximum two-sided half-width.

The historical summaries are hash-bound only as sample-size planning evidence.
They cannot choose a FULL104 masking policy. FULL104 must still fail closed if the
actual paired donor-target intervals are wider than 0.003.

## 2. Nonlinear "no shortcut" requires attacker competence

A nonlinear residual result cannot pass merely because the nonlinear attacker is
weak. The successor receipt requires the same nonlinear challenge to:

- show a planted shortcut above its shuffled-null noise;
- suppress that planted shortcut back to the null-noise level after masking; and
- place real residual shortcut predictability at or below the same null-noise level.

Thus historical nonlinear success motivates the challenge capacity, while current
FULL104 planted/shuffled controls prove the current implementation can actually
detect the kind of shortcut it is being asked to rule out.
