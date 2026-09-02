## Review 3: provenance, firewall, dataset and biology semantics

VERDICT: CONCERN

- All 17 package-manifest entries and three source snapshots match their byte sizes and SHA-256 values. There are no missing or unlisted package files.
- Source inspection finds no expression, checkpoint, model-forward, outcome, training or EMA access. The design retains 104 unique donors: 41 HVS, 17 NPH52 and 46 SEA-AD. Excluded optional directions are not described as source or biology exclusion.
- The finalizer authenticates internal reviews using label substrings and a count of PASS text rather than structured, hash-bound review records. The package manifest also needs an independent external root anchor against coordinated replacement.

Blocker: machine-readable authenticated review records and an independent package-root anchor are required for stronger provenance before 15C.

