# TD46S closure — broad complementary rank context fails linear inversion-field screen

Status: `NO_BROAD_COMPLEMENTARY_EVIDENCE_FOR_INVERSION_FIELD__TD46S_FAIL`

Prospective freeze: `1eff51e12d30154564aec49b74a5d1d86320a0bb`

Exact broad context:
- 17,186 all-operator common-scalar addresses
- minus 256 target genes
- = 16,930 context genes

Sparse exact within-cell rank CountSketch validation:
- 32 deterministic dense checks
- max absolute sparse-vs-dense difference: **7.77e-16**
- PASS <=1e-10

Nested TRAIN-only ridge:
- shortcut selected multiplier: 1
- broad molecular context selected multiplier: 10

Held-out HVS donors:
- shortcut MSE: 0.9622490
- broad molecular MSE: 0.9736041
- Delta: **-0.0118006**
- 4/32 target coordinates positive

Predeclared target-gene sensitivity control:
- selected multiplier: 1
- positive-control MSE: 0.6258808
- Delta: **+0.349565**

Therefore the screen is sensitive, and adding the complete broad rank context still does not establish linear complementary-evidence predictability for the joint inversion field.

This is a linear-screen failure, not proof that nonlinear molecular information is absent.
No target/training authority.
