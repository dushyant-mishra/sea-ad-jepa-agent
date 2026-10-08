## Review 2: numerical linear algebra and HC3

VERDICT: PASS

- All 17 package-manifest entries verify. Independent reconstruction is array- and byte-exact to the selected design SHA `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.
- SVD and pivoted QR both give rank 16 and df 88. Leverage differs by about `6.66e-16`; all 104 donor deletions retain rank. Independent HC3 covariance arithmetic and invertible optional-basis checks agree.
- Adding `NPH52_residual_svd_score_01` produces the intended fail-closed geometry: deleting `NPH52::human_NPH_906` loses rank and the HC3 boundary is violated.

Blocker/falsification: any reconstruction mismatch, rank/leverage disagreement beyond tolerance, donor rank loss, nonfinite HC3 arithmetic, or acceptance of the NPH adversary. None occurred.

