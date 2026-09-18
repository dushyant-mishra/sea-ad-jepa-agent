# FULL104 target-panel sizing and precision — 2026-09-18

The prospective FULL104 masking panel is frozen at 128 targets.

This number is not inherited from the historical 32-target exploratory run and
does not depend on which masking policy won there. FULL104 contains 104
independent donors, and the paired uncertainty procedure resamples both target
and donor dimensions. The target dimension is therefore required not to be
smaller than the donor dimension; the next power of two at or above 104 is 128.

Historical results remain useful only as a planning check: a four-fold increase
from 32 to 128 target units would, under ordinary square-root sampling behavior,
roughly halve target-sampling uncertainty. That observation did not choose the
128 value.

Precision is fixed at 95% confidence with 4096 paired target-and-donor bootstrap
replicates. The bootstrap seed is derived from current support, target-panel and
outer-split roots, not copied from historical runs.

If 128 targets are computationally expensive, the permitted response is to
improve streaming/caching with exact parity or fail closed. The target panel is
not reduced after terminal outcomes are inspected.
