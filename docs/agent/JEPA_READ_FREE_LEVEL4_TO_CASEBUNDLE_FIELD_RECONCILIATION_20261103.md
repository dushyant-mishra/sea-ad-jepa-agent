# JEPA read-free Level-4 → CaseBundle field reconciliation (2026-11-03)

## Cross-lane correction — reuse supersedes proposed engineering (2026-11-03)

**Correction to this document's earlier “Minimal next engineering task” section:** Do **NOT** initiate a new source-binding fixture, CaseBundle adapter, query-rights test suite, student redactor, model fit, or Level-4 read from this PR. The field matrix below describes **what older receipts individually attest**, NOT a missing implementation inventory. Its original 15 rows remain a source-specific retrospective, not authority to rebuild.

Relevant work *already done*, reviewed at its own scope:

- **Unified integrated biology:** #311 (real-data-matched rare), #315 (candidate-agnostic design), #328 original frozen integrated 480-cell RNA/ATAC/rare/perturbation fixture and #339 external `PASS_WITH_LIMITATIONS`; #344 production V3.1/V3.1.1 design and #431 prior cross-lane no-repeat audit. #328 is mechanics only; #531 and its erratum established that `VISIBILITY > 0` improperly conflates detection with structural support. Its old interpretation cannot be reused for real source-specific observability.
- **Relational test-of-test:** #318/#321 qualified nine synthetic challenges, already independently audited in #336 (`53820343`; `TEST_QUALIFICATION_ONLY`). No new Phase2 audit.
- **Previously executed synthesis→downstream:** #369 tested sealed gate mechanics; #440/#451 Task5 and downstream bridge; **#469** ran PR328-generated RNA → CaseBundle fixture → post-TD route with `TARGET_NONE` and planted C1; **#534** composed original frozen PR328/V80 with #474/Task5 hostile q-rights, q-in-BASE, source-forgery, off-ledger, collision and richer-depth cases. #534's **V80 exact benchmark identity mismatch remains RED at its latest head**; do not label the whole suite green or duplicate its tests. A mechanical right-/wrong-query **view change** is not a learned wrong-query biological recovery test.
- **Versioned D1 and student isolation:** #474/#478/#479 proved and attacked q-excluded depth; #491 adopted D1, rejecting D2; #502/#503/#504/#508/#510/#511 evolved the fixture-only rights/content boundary, preserving #507/#512 RED; #514/#515 created V2C+D1, #516/#518 attacked it, #521 packaged a restricted verifier, #522/#523 landed **scoped, independently reviewed fixture** on `main`, as recorded in its current execution map. No second V2C/D1 producer, Docker package, or student gate is required from #535. A restricted test container is **not a trusted physical issuer/launcher**.
- **Physical source/rights:** original #59/#69 Level-4 reads and source-label repair; #349 real support registry, #492 50k audit, #509 22-row source/ETL gap audit, #513/#528 eight-field issuer and QC/alias corrections. **Existing data are not missing** merely because #59's published donor-aggregate receipt does not contain per-cell CaseBundle rows. Preserve original source/QC rights and independence limits.

**Action after this crosswalk:** #535 is **DOCUMENTATION_ONLY__NO_IMPLEMENTATION_AUTHORIZED**. Independent reviewer should inspect existing #469/#534/#515/#523/#509/#513 and #431/#531 evidence **before** claiming any untested edge. A genuinely new task is warranted only after naming a falsifiable gap absent from those implementations, the accepted original tests, and stored receipts; then it must specify the result that would change the scientific conclusion and prospective authority. No duplicate experiments proposed.

**Unchanged terminal:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

---


**Scope:** compare existing original records and source code, not physical bytes. Do not open an additional Level-4 block, rerun ETL, run a target experiment, or promote a fixture. This is an append-only, flat-`main` audit companion to the already recorded November 3 [historical read recovery](https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/16e9c0c5d2beae5ab6fc77cb7460ef96b2f97423/docs/agent/JEPA_20261103_HISTORICAL_REAL_LEVEL4_READ_RECOVERY_AND_NO_REPEAT_CORRECTION.md). It does not repeat #509's 22-row source/ETL gap matrix.

**Question:** which individual source→CaseBundle fields are established *by retained receipts*? Do not confuse an existing raw source with a saved per-cell attestation. Full machine matrix: `results/target_discovery/unified_qualification_v1/JEPA_EXISTING_LEVEL4_TO_CASEBUNDLE_RECEIPT_COVERAGE_V1.json` (15 classified fields, original frozen refs with pinned Git blobs where available). Exact original path existence was checked at each source commit.

## Primary evidence and corrections

- **#59 raw execution:** original independent script blob `4193cfed494bf5c18968d813ee3553a41adb84db`, qualifying receipt blob `e3a0926a81a278f49f155906a11c1eb35baa95cb`; read 387 SHA-checked raw-count blocks for six prospectively selected donors, verified 8,915 metadata SHA entries, accounted for 4,553,407 metadata cells, and exactly matched donor-level `donor_nnz` and `donor_umi` at 17,186 strict-core addresses. The loop reads `selection_row`, `donor_id` and `source_library` from per-block metadata, but emits donor aggregates, not per-cell source/q/D1 attestations. **Do not call 8,915 verified metadata blocks 8,915 raw-count reads.**
- **#69 correction:** receipt blob `28418462bf4e4ddab0794bc8d7c759d121b67476`. Two SEA-AD and two NPH52 donor labels were swapped in #59's textual source mapping; the six numeric rows did not change. A source ID inherited from #59's uncorrected label table cannot be promoted.
- **#492/#509:** original 50k transformed-expression archive and comprehensive full-feature/source alias reconciliation exist, with specific scope and negative evidence. No reason to repeat the old ETL audit or an ephemeral #469 Task5 bridge.
- **#513/#528:** existing source/operator/alias accounting, QC summaries and correction of overclaimed provenance. For 4,118,213 SEA-AD cells, `source_library` agreed with same-deposit UMI metadata; this establishes internal consistency only, **not** independent molecule/source identity. HVS denominator discrepancy has *unknown cause*. SEA-AD `sample_id` is unique per nucleus, **not** a specimen identifier. NPH52 features and query selection remain blocked.
- **Original #451 Task5:** `KNOWN_TRUTH_CASEBUNDLE_V1` is `FIXTURE_ONLY`, and the validator treats `library_size` as a physical total; it explicitly does not verify full Task2 access or external source. Do not insert D1 into this `library_size`.
- **Main D1 V2C:** `observation_d1_base_only_student_v2c_fixture_v1.py` accepts *already redacted* BASE counts, not raw physical totals, and checks student view consistency against self-supplied policy. Its receipt is not external authentication or a real source issuer.

## Minimum field classification

| Field / semantic question | Retained evidence | Not established by that evidence |
|---|---|---|
| Original blocks, count reads, selected donor aggregates | #59 `EXISTING_PHYSICALLY_EVIDENCED` at 387 raw blocks / six donors | Complete source-bound individual CaseBundle |
| Correct canonical donor↔source label | #69 `EXISTING_PHYSICALLY_EVIDENCED` correction at six-donor scope | Source rights or unique real measurement identity |
| Cell/selection-row metadata, `source_library` | `PRESENT_BUT_UNQUALIFIED` | Signed per-cell count+physical-total pairing and query-safe roster |
| Per-cell raw count at query address | `NOT_RETAINED_IN_OLD_RECEIPT` (although raw counts were read) | Reconstructable per-cell value from donor sums; **do not infer this** |
| Source feature, structural/collision support, aliases and query rights | `PRESENT_BUT_UNQUALIFIED` (#509/#513) | Fully source-authenticated rights issuer; NPH52 is not estimable |
| Task2 access session, real private/public view commitments | `NOT_RETAINED_IN_OLD_RECEIPT` | Exact old #59 → Task2 session → real CaseBundle binding |
| Student D1 redaction | `PRESENT_BUT_UNQUALIFIED` (main fixture code) | Real issuer, independent student isolation or query-independent selection |
| SEA-AD specimen ID, NPH52 query issuance | `NOT_ESTIMABLE` in those current scopes | No fabricated specimen or off-ledger gene identity |

The machine matrix uses exact statuses for all 15 individual fields and distinguishes **not in an old receipt** from **physically unavailable**. No old scientific result is reopened by this classification.

## Minimal next engineering task — still synthetic-only

1. **No new source read.** Inspect exact existing raw-block reader/metadata trace and the main V2C D1 redaction boundary. Reuse #513's eight required release bindings (query address, alias rights, ladder, operator support, cell roster, custody, issuer provenance, view commitment). Avoid building a second policy/signature hierarchy.
2. In a **separate versioned source-binding fixture**, enforce source/selection-row uniqueness; corrected source IDs; a complete source-feature/alias policy; operator query measured-scalar eligibility; and a teacher-private physical total distinct from a student-only D1. Use synthetic hostile observations, including a deliberately altered source label, q-in-BASE, an off-ledger alias, collision, zero vs structural unmeasurement, and physical total vs D1.
3. The student-facing path must receive only already-redacted BASE counts and a custodied policy, never raw q counts, a private physical library total, or a teacher digest that could enumerate q. Treat any self-supplied authority as `FIXTURE_ONLY`.
4. Have Macha attack the exact proposed interface/hostile suite **without new real data reads**. A real execution plan can only be considered if one indispensable individual field is shown absent from every retained artifact and existing derivation, and the owner-delegated ceiling and access controls are separately satisfied. Existing #59 raw-read coverage must be considered first.

## Reviewer questions

Can an old aggregate `donor_umi` value be miscast as a per-cell q measurement? Can an original #59 swapped source label re-enter the pipeline? Can a D1 depth be treated as a physical total? Can an alias/structural state/QC-dependent cell roster be self-declared? Can a forged Task2 receipt or unkeyed digest be treated as source authentication? **Every such path must refuse or remain explicitly nonauthorizing.**

**Decision:** `REUSE_ORIGINAL_LEVEL4_READS__NO_NEW_READ_ASSIGNED__REAL_CASEBUNDLE_NOT_QUALIFIED`.

**Authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
