# Red-Team Review — V8 Round 1

VERDICT: PASS

1. Both prior falsifications now fail closed. A denied path with an empty hash list aborts because exactly seven paired unique paths/hashes are required. Supplying all seven original mixed NPH paths with their authentic hashes aborts with `original mixed NPH asset denied`. The built-in negative regression test also passes.
2. The fresh verifier independently authenticates the externally anchored frozen metadata manifest, `FULL104_ROW_LINEAGE.csv`, and all seven referenced NPH lineage shards before opening and comparing the fit-only derivatives. It proves 236,476 unique cells, exactly 17 fit donors, and protected-donor absence.
3. The staged package is fully manifest-covered and externally anchored; the frozen consumer returns only `normalized_values` and `observation_states` at 84 x 41,238. Failed attempts and round-0 STOP remain preserved, and Phase 2 is absent.

Most important attempted falsification: supply every original mixed NPH path and hash to the production firewall. Result: fail-closed abort.

Reviewed artifacts include `code/full104_production_expression_firewall.py`, `code/verify_nph_reader_fit_quarantine.R`, `ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv`, `CONSUMER_SELFTEST.json`, and the package manifest/external anchor.
