# JEPA PR163 target-family S149 re-adjudication — 2026-10-06

Status: AUDIT/DOCUMENTATION ONLY. Training OFF. Stage 4 NOT AUTHORIZED. TEST sealed. Morabito protected.

## Historical candidate state

PR #163 is explicitly non-authorizing and selects no candidate. It defines four target constructions around where the hidden query scalar is withheld from the teacher.

### T_A — query value in teacher

Status: `CLOSED_FOR_STATED_BIOLOGICAL_GOAL`.

The query value enters the teacher before contextual mixing, so the teacher target is a function of the value the student is asked to infer. This is indirect scalar reconstruction, not a query-local latent state independent of that scalar.

### T_B1 — value-blind query slot; teacher hides query only

Status: `LIVE_CANDIDATE__S149_AWARE_BY_DESIGN__NOT_YET_S149_QUALIFIED_BY_REAL_RNA_OUTCOME`.

Strength: query scalar is removed before teacher attention. Teacher sees the other measured genes, giving a richer but q-blind context.

S149 requirement still missing: demonstrate with real RNA, using donors as the replicate, that the target contains query-local information within each observation process and transports across HVS/NPH52/SEA-AD rather than encoding source/operator structure.

### T_B2 — value-blind query slot; teacher hides full student mask

Status: `LIVE_DIAGNOSTIC_CANDIDATE__S149_AWARE_BY_DESIGN__COLLAPSE_RISK__NOT_YET_REAL_RNA_QUALIFIED`.

The query scalar is withheld correctly, but teacher and student see essentially the same molecular evidence. This creates a serious risk that the target becomes an EMA-smoothed copy of the student's own input rather than a rich query-local biological target.

### T_C — whole-block values withheld

Status: `BLOCKED__INHERITS_UNRESOLVED_BLOCKING_AUTHORITY`.

Although q leakage is reduced, the target becomes block-local and inherits the historical block-construction failure. S149 does not rescue that blocker.

### T_D residualization modifier

Status: `DIAGNOSTIC_ONLY`.

Removing the query scalar statistically after it has entered the teacher cannot prove the leak is fully gone and risks erasing biological signal along with technical dependence.

## S149 safeguards already present in PR163 design

The design correctly requires:
- donors, not cells, as the independent unit;
- donor-clustered uncertainty;
- per-source reporting rather than a pooled headline;
- no source/operator input into the primary molecular path;
- query masking based on declared support, not realized expression;
- q-safe normalization as a separate prerequisite.

These are design properties only. They do not establish that a candidate target is biologically transportable across observation processes.

## PR178 historical-spillover guard

PR #178's corrected synthetic T_A/T_B experiment is explicitly `NOT_INFORMATIVE` for the real biological decision. Its final fixture still depends on an arbitrary synthetic split of signal between q and program genes and the historical review itself concludes that the comparison needs real RNA.

Therefore no synthetic PR178 result may be cited as evidence that T_B1 or T_B2 is biologically superior.

## Current decision

No historical real-RNA experiment found in this audit qualifies T_B1 or T_B2 under S149.

The smallest lawful next experiment is a prospective, development-only real-RNA target audit with:
1. q-safe/value-independent normalization;
2. query scalar physically absent before teacher tokenization;
3. donor-disjoint evaluation;
4. HVS, NPH52 and SEA-AD scored separately;
5. a cross-source transport requirement rather than pooled performance;
6. query-exchangeability and identity-only controls;
7. source/operator predictability reported as a disqualifying shortcut diagnostic;
8. no training authorization, Stage 4, TEST, pathology or Morabito opening.

No numeric acceptance threshold is selected here after outcome exposure.
