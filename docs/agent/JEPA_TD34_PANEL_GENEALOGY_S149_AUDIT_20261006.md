# JEPA TD34 panel genealogy — S149-aware audit checkpoint

Status: `INDETERMINATE__PRIMARY_PANEL_PRODUCER_NOT_YET_RECOVERED`
Date: 2026-10-06
Branch: `audit/td34-genealogy-s149-20261006`

## Scope

This is a documentation-only provenance audit. It does not authorize training, Stage A, target selection, representation selection, optimizer/EMA mutation, 500K, Stage 4, TEST, or Morabito use.

## Why this audit exists

TD41/TD43 reused four deterministic 512-gene panels inherited from TD34. TD41's own pair selection is deterministic and outcome-independent, but that cannot establish that the upstream TD34 panel membership was S149-safe. The panel producer must therefore be traced independently.

## Primary evidence recovered

1. TD41S prospective freeze commit `a1bfebf3ecbc55d9594058f182202e5a90a882ff` states that it reuses "the same four deterministic 512-gene TD34 panels", enumerates every unordered pair inside each panel, ranks pairs by a SHA-256 address hash, and retains the first 4,096 pairs. It explicitly states that no pair is selected by expression, state label, recurrence, or outcome.

2. The TD30–TD36 closure ledger preserved in commit `ff85f5bb18dc7d438113c3a5662856a360d2cd8f` records TD34 as "Four 512-gene common-scalar panels" and preserves only the TD34 local script SHA-256 `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566` plus outcome summaries. The repository directory `target_discovery/iterations/td34_state_geometry_globalrow/` at that commit contains only `TD34_SUMMARY.csv`; the producer script and explicit panel-membership artifact are not present there.

3. The TD41/TD43 forensic protocol commit `54f67f5cd5138c47311e95441b4895076ffb7bfc` proves that later audits treated the four 512-gene panels as pre-existing objects and focused on pair support, complete-pair convergence, pair dominance, and matched wrong-cell measurement reliability. It does not reconstruct how the 512 genes were selected.

## Current provenance classification

`INDETERMINATE__PRIMARY_PROVENANCE_MISSING`

Reason: the durable repository evidence currently recovered proves the downstream TD41 pair-selection rule but does not yet prove the upstream TD34 gene-panel construction rule, its input split, or whether panel membership depended on pooled source/cohort measurement statistics.

This means the following stronger classifications are NOT yet justified:

- `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`
- `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES`

Either could still be correct; the primary producer is required to distinguish them.

## Historical-spillover audit

### Cleared so far

- TD41 pair identities themselves were not chosen from biological outcomes or expression magnitude at the TD41 step.
- TD41's later forensic work explicitly checked all retained endpoints against the 17,186-address all-42-operator common-scalar support space.
- TD34's reported downstream state geometry was already donor-balanced and guarded against the known reset-index B-row alias.

### Not cleared

- How the four 512-gene TD34 panels were selected from the common-scalar universe.
- Whether the panel-selection statistic used pooled cells, pooled sources, source composition, operator coverage, mean/detection abundance, covariance/topology, or another quantity vulnerable to the S149 measurement-process confound.
- Whether the panels were selected before or after any state/source inspection.
- Whether a local handoff archive contains the missing script or panel lists with hashes that can be matched to the preserved TD34 script SHA.

## Self-audit decision

Do not run or reinterpret any new TD41 outcome analysis until the TD34 panel producer is recovered or provenance is formally declared unrecoverable.

The correct next search order is:

1. recover the sealed/local handoff package referenced by commit `ff85f5bb18dc7d438113c3a5662856a360d2cd8f` and match its TD34 script against SHA-256 `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`;
2. identify the exact four 512-gene panel lists and their generating code;
3. trace every input used in panel membership back to its data split and source/operator aggregation rule;
4. classify the genealogy as S149-safe, S149-risk, or irrecoverably indeterminate;
5. only after that classification, finish TD41 adjudication.

## Concurrency protection

During this audit the shared handoff branch advanced independently to commit `d395acc379e5d7383a5b1efdcbd473d4499bec4e` for runtime/PR222 work. To prevent cross-lane historical spillover, this target-lineage audit was moved to the dedicated branch `audit/td34-genealogy-s149-20261006` and no mutation was made to `main` or the moving runtime lane.
