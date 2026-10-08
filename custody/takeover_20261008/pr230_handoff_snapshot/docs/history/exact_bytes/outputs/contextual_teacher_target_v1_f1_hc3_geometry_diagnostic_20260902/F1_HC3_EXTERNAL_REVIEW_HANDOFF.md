# F1 HC3 geometry diagnostic — external-review handoff

Terminal: `STOP_F1_HC3_SVD_NUMERICAL_NONREPRODUCIBLE`.

The historical rank-18/df-86 HC3 failure, the two unit-leverage donors, the mandatory-base estimability, the raw-column order dependence, and the donor-isolating operator-mixture root cause were reproduced outcome-blind.

The diagnostic frontier is **not promotable**. Review found that NPH52's nominal second residual component is projection roundoff: augmented-space rank increment is one, while residual rescaling reports two. This makes 35 of 105 frontier rows constructed-rank-deficient, contrary to the frozen engine's full-column-rank gate. The validator reproduced rather than falsified that defect. Actual ill-conditioned Gram-inverse leverage is also not basis-stable enough for the claimed certification.

No design/rank/operator subset/estimator is selected or frozen. No expression, model, checkpoint, candidate outcome, training, or EMA was accessed. Do not resume F1 evaluation from this package. A separate prospective instruction is required to define stable residual-rank and leverage arithmetic.
