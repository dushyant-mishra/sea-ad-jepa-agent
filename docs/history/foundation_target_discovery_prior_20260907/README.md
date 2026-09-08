# Foundation Target Discovery — historical evidence import

Status: `HISTORICAL_EVIDENCE_ONLY__NO_TARGET_OR_EXECUTION_AUTHORITY`

Imported on 2026-09-07 into `planning/foundation-target-discovery-v1-20260907`.

Primary historical source:
- branch: `stage81a3r-real-train-global-state-20260814`
- head: `e8b72d0161e6a61ef5d3753fdbab8ae9234ed977`
- terminal commit: `Freeze Stage81A3 representation contract`

Purpose:
1. keep exact prior target/representation attempts in the active Target Discovery branch;
2. prevent rediscovery of already-tested negative or bounded results;
3. preserve exact historical artifacts rather than conversational summaries;
4. quarantine pathology-bearing discovery work from the current pathology-blind target-selection lane.

The imported files are historical evidence only. They do not authorize old dimensions, thresholds, masks, donor counts, or sampling constants in the current 4,553,407-cell / 104-donor reader_fit problem.

Distinctions that must remain explicit:
- PCA/REP was a representation/basis comparison, not proof of a final biological target.
- Historical `d_global=224` was an ordered linear global-state candidate under an earlier 149-TRAIN-donor / 4,726-cell qualification and explicitly did not establish biological sufficiency.
- 60/40 masking was a mechanism test, not target authority.
- donor water-fill was a sampler allocation scheme, not a biological-target waterfall.
- 20→40→60→80→100 is an evidence-response diagnostic, not a historically frozen coarse→fine target hierarchy.
- pathology-driven discovery-atlas artifacts are referenced in the quarantine ledger, not copied into this lane.

Read `HISTORY_GATE.md` before any new candidate is proposed or promoted.
