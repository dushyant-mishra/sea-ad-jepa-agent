# Prospective natural-weight/full-feature refit-null contract

This document is frozen before any sensitivity result exists.

For donor `d`, donor×operator stratum `g`, full donor size `N_d`, stratum size `n_dg`, and nested cap sample size `m_dg=min(cap,n_dg)`, every selected cell has finite-population expansion weight:

`w_idg = (1/104) * (1/N_d) * (n_dg/m_dg)`.

Therefore each donor has total weight `1/104`, every stratum has its natural mass `n_dg/(104*N_d)`, and at `ALL` every original cell has exact weight `1/(104*N_d)`.

Every observed and matched-null fit is performed independently in the original 512-dimensional A/B feature space to rank 320. No observed projection, top-32 restriction, diagonal-only substitute, or reuse of an observed eigensystem is legal. The null uses 256 matched view derangements; replicate `r` receives exactly one paired source-stratified donor bootstrap, not a Cartesian bootstrap.

Caps 4, 16, 64, 256, and 1024 are nonselecting diagnostics. `ALL` is mandatory and is the only selecting population. The exact stopping/routing rules are in the JSON contract and cannot change after outcomes are observed.
