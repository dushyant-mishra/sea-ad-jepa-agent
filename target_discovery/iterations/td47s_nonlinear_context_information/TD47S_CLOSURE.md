# TD47S closure — nonlinear broad-context information screen fails

Status: `NO_NONLINEAR_COMPLEMENTARY_INFORMATION_FOR_INVERSION_FIELD__TD47S_FAIL`

Prospective freeze: `db9a4235d9d389013633937b75138b654fed0488`

Fixed K=32 broad-context kNN on held-out HVS donors:
- shortcut MSE reference: 0.9622490
- kNN MSE: 1.0037765
- Delta_knn: **-0.0431567**

16 donor/operator/depth/detection matched broken-context null Deltas ranged approximately -0.0477 to -0.0367.
Observed Delta did not exceed zero or the null maximum.

Predeclared target-gene-rank neighbor-space positive control:
- Delta: **+0.052842**

Thus the nonlinear screen is sensitive, and the joint inversion field is not established as complementary-evidence-inferable under either:
- donor-heldout nested linear ridge using all 16,930 non-target common genes; or
- donor-heldout fixed-K nonlinear neighbor regression in the same broad context.

Conclusion:
Do not promote the raw per-cell inversion field as the JEPA target.
The cross-source concordance geometry remains valid descriptive/validation evidence and motivates a different atomic target.

No target/training authority.
