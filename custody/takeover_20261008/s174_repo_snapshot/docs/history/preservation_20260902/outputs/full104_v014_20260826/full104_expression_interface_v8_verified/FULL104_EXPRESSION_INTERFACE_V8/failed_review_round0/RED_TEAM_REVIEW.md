# Red-Team review — round 0

Verdict: `STOP`

Two engineering blockers were found:

1. `assert_fit_only_nph_assets()` iterated `zip(asset_paths, asset_hashes)` without enforcing equal lengths or exactly seven unique pairs. A denied original path plus an empty hash list returned without aborting.
2. The fresh verifier compared derivatives to a package-local expected-lineage copy rather than independently authenticating and reopening the frozen FULL104 lineage index and seven NPH shards.

All other challenged boundaries passed. Round 0 cannot authorize publication or Phase 2.
