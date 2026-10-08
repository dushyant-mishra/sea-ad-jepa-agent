# F1 HC3 Command 15B — independent review record

## Review 1: prospective selection, statistics and authority chronology

VERDICT: CONCERN

- Independent recomputation from the manifested dominance audit gives 70 rows, 30 admissible rows, and the sole Pareto/universal maximum `(5,0,4)`. The rule filters on the frozen admissibility boolean and forbids outcome/power optimization and tie-breaking.
- Selection occurs before synthetic engine checks and uses only authenticated 15A4/nuisance artifacts. Current values are explicitly prohibited from transfer to future cohorts.
- The executable enforces the exact contract hash before application, but the chronology timestamps recorded in the authority are hard-coded source literals. The package therefore enforces runtime order without independently authenticating historical authorship time.

Blocker: none for the mathematical selection. Before 15C, either externally anchor a trustworthy pre-application contract record or preserve the chronology limitation explicitly.

## Review 2: numerical linear algebra and HC3

VERDICT: PASS

- All 17 package-manifest entries verify. Independent reconstruction is array- and byte-exact to the selected design SHA `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.
- SVD and pivoted QR both give rank 16 and df 88. Leverage differs by about `6.66e-16`; all 104 donor deletions retain rank. Independent HC3 covariance arithmetic and invertible optional-basis checks agree.
- Adding `NPH52_residual_svd_score_01` produces the intended fail-closed geometry: deleting `NPH52::human_NPH_906` loses rank and the HC3 boundary is violated.

Blocker/falsification: any reconstruction mismatch, rank/leverage disagreement beyond tolerance, donor rank loss, nonfinite HC3 arithmetic, or acceptance of the NPH adversary. None occurred.

## Review 3: provenance, firewall, dataset and biology semantics

VERDICT: CONCERN

- All 17 package-manifest entries and three source snapshots match their byte sizes and SHA-256 values. There are no missing or unlisted package files.
- Source inspection finds no expression, checkpoint, model-forward, outcome, training or EMA access. The design retains 104 unique donors: 41 HVS, 17 NPH52 and 46 SEA-AD. Excluded optional directions are not described as source or biology exclusion.
- The finalizer authenticates internal reviews using label substrings and a count of PASS text rather than structured, hash-bound review records. The package manifest also needs an independent external root anchor against coordinated replacement.

Blocker: machine-readable authenticated review records and an independent package-root anchor are required for stronger provenance before 15C.

