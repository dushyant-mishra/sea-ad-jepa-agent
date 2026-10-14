# TD real G11/G12 population/support registry V2 audit — 2026-10-14

Status: `POPULATION_AND_SPLIT_IDENTITIES_FROZEN__CANDIDATE_EVIDENCE_SUPPORT_NOT_YET_FROZEN__NO_BIOLOGICAL_AUTHORITY`

## Purpose

This repair was performed outcome-blind. It exists because the qualified V1 G11/G12 static contract could not safely instantiate the real registry without losing two decision-bearing distinctions required by the earlier prospective tournament law:

1. reader split identity was absent from each stratum, even though donor transfer is a held-out claim;
2. candidate support was a boolean, which would collapse unresolved evidence-rights/address/query support into either false structural absence or an unjustified true support claim.

No human candidate outcome was opened.

## Exact decision-bearing ancestry

- prospective multi-target prefreeze V2: PR #275 qualified executable/documentation lineage, where exact population, donor identities, source families, operators, support registry, evidence rights, split identities and observation descriptors must be frozen before outcomes;
- blocker-resolution V1/V2: PR #341, where G11 waits the static population/evidence-rights registry and G12 requires the mandatory claim envelope to be fixed before outcomes;
- G11/G12 V1 mechanics: PR #342 exact qualified source head `f7e90c41bab10c7ff4abb3e69446975634483656`.

Branch-tip movement on audit/handoff surfaces was checked separately and was documentation-only; no moving branch tip was treated as executable authority.

## Historical population custody used

Only metadata/custody bytes were used. Expression and candidate outcomes remained closed.

Frozen calibration bundle SHA-256:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Inside that bundle:

- `foundation_metadata_rows.sqlite` SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`;
- `reader_donor_split.csv` SHA-256 `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`.

Reconciliation result:

- 6,351,753 metadata rows;
- 149 donors;
- 42 operators;
- 3 sources;
- 2,028 exact donor×operator strata;
- reader partitions: 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle`;
- all current foundation observation strata are `snRNA-seq`.

The producer refuses a donor/partition mismatch, duplicate split donor, donor-roster mismatch, production database hash mismatch, production split hash mismatch or population-count drift.

## V2 scientific corrections

### 1. Split-bound strata

Every stratum now binds `reader_partition`. A donor may occur in exactly one reader partition. DONOR transfer cannot become `REQUIRED` merely because two donors exist: supported `reader_fit` and supported held-out (`reader_validation` or `reader_oracle`) donor strata must both exist.

### 2. Three-state candidate support

Per-stratum candidate support is now exactly one of:

- `SUPPORTED`;
- `UNSUPPORTED_STRUCTURAL`;
- `BLOCKED_EVIDENCE_CONTRACT`.

If any stratum for a candidate remains `BLOCKED_EVIDENCE_CONTRACT`, its mandatory claim envelope is incomplete and G11/G12 remain `NOT_ESTIMABLE`/`BLOCKED_DEPENDENCY`. This prevents unresolved evidence rights from being silently converted into either support or biological absence.

### 3. Current conservative support classification

The population is frozen, but exact candidate evidence support is not yet frozen.

Therefore, across all 2,028 frozen population strata:

- C1/C2/C3/C6/C4 = `BLOCKED_EVIDENCE_CONTRACT`;
- C5 = `UNSUPPORTED_STRUCTURAL` in this RNA-only foundation registry pending a separately frozen regulatory/chromatin specialist evidence registry.

This is intentional. RNA presence alone is not sufficient to certify:

- C1 exact teacher/evidence-right support;
- C2 exact repaired relation-address support;
- C3 exact query/address support;
- C6/C4 inherited constituent support.

### 4. Technology transfer remains unavailable

Current frozen foundation population provides only one technology level (`snRNA-seq`). Even after candidate support is resolved, G11 TECHNOLOGY transfer remains structurally blocked unless a prospectively frozen lawful second technology enters the claim envelope.

## Frozen result

Receipt:
`results/target_discovery/real_tournament/TD_REAL_POPULATION_SUPPORT_REGISTRY_FREEZE_RECEIPT_V2.json`

Canonical generated registry payload SHA-256:
`50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`

The full generated registry remains external/local custody because it is mechanically reproducible from the exact metadata database and split bytes above and contains the 2,028 donor×operator rows. The tracked receipt binds its canonical payload identity.

Derived tracked contract:
`results/target_discovery/real_tournament/TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2.json`

Current interpretation:

- all foundation candidates: `SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE`;
- C5: `NO_SUPPORTED_STRATA__NOT_ESTIMABLE` within the current RNA-only foundation registry;
- all G11 transfer dimensions remain `BLOCKED_DEPENDENCY` until candidate-specific evidence support is frozen;
- all authority flags remain false.

## Recursive self-audit record

Round 1: verified canonical #322/#323 tip movement was documentation-only; retained #342 exact qualified source as the executable ancestor.

Round 2: rejected an attempted registry based only on separate donor and operator summaries; recovered the exact 2,028 donor×operator pairs from the frozen metadata database instead.

Round 3: found V1 omitted reader split identity and would allow DONOR transfer to become required without a held-out population; repaired with split-bound strata and fit+held-out requirement.

Round 4: rejected the first generated draft that marked every RNA stratum supported for every foundation candidate; historical prefreeze requires exact evidence-rights/support binding, and relational/query candidates need address/query-specific support.

Round 5: replaced boolean support with the three-state support law so unresolved evidence contracts remain explicitly blocked rather than being misclassified as structural absence.

## Dependency consequence

The previous action order must be refined. Population/split custody is now frozen, but final G11/G12 applicability cannot be completed before candidate evidence support is materialized.

Required upstream support freezes now include:

- C1 exact teacher target/evidence rights;
- C2 actual repaired relational member-address manifest and support overlay;
- C3 exact query set/address support/evidence rights;
- C6 and C4 inherited constituent support;
- C5 separate regulatory/chromatin evidence registry if the specialist is pursued.

This is a dependency correction, not permission to open outcomes.

Binding terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
