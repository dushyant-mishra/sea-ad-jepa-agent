# TD real-tournament gate executor implementation plan — 2026-10-13 (read-only; no decision-rule code written)

## Coordinator verification addendum (Macha, added before publication)

The body below is the read-only planning audit's report, preserved verbatim. Before publishing, I re-checked its decision-changing claims myself:

- **Matrix:** 198 rows; 117 `RULE_NOT_MATERIALIZED`; 81 `NOT_APPLICABLE`; 0 callable. SHA-256 `aacae2efef959d744939ccd7af65859d16420568c3777e22ec17d3da165bdb7a` at PR #333 head `868da5e2df89e0ef01ff5da41c87444ebbd72b32`. Confirmed.
- **Wrong-cell null (finding §8.1):** confirmed in code. `scripts/v5/td_real_tournament_case_ledger_v1.py::_partner` explicitly skips same-donor cells (`other["donor_id"] == row["donor_id"] → continue`). It matches only on source, operator, split and query, and always picks the single fixed `min(donor_id, cell_id)` partner. The frozen `TD_84_CELL_TRUTH_TABLE_ROLE_AUDIT_20261011.md` states that the primary wrong-cell null "is required to preserve at least donor and operator" and that "relaxing donor preservation … would violate the frozen tournament design".
- **Composite pooling (finding §8.2):** confirmed in code. `td_real_tournament_falsifiers_v1.py::_target_student` concatenates the shared, relational and query blocks into one vector, which feeds one MSE.
- **Parallel lane has advanced since the audit snapshot.** Branch `engineering/td-real-gate-rule-materialization-20261013` is now **PR #334** at `976f15fb9e3b3de4f52cb7bd4aeebbec610974e1`. It adds a structural-executor qualification receipt and a historical-equivalence ledger (it supersedes the `4aa74df7` references below). Its own status is "five structural gate rules mechanically qualified; 17 required roles have callable qualified mechanics; 100 remain `RULE_NOT_MATERIALIZED`".
- **Defect §8.6 still stands at `976f15fb`.** `execute_structural_gate` authenticates its own executor bytes and hashes the evidence payload, but G1, R2 and Q2 still decide from caller-supplied booleans (`post_outcome_redesign`, `locality_rule_prefrozen`, `q_excluded_teacher_primary_anchor`).
  - Classification for G1/R2/Q1/Q2/Q3 here: **`CALLABLE_NEEDS_QUALIFICATION`**. Mechanics are qualified in unmerged PR #334; evidence authentication is not qualified.
  - I have not independently audited PR #334's qualification run.

No candidate outcome, DEV/SEALED data or pathology label was opened by the audit or by this verification.

---


Date: 2026-10-13. Auditor: Claude (read-only). Nothing in the repository or any existing worktree was modified.
Created only: detached worktree `D:/jepa_gate_plan_audit_868da5e2` (at 868da5e2) and files in this scratch folder.

## 0. Identities and verified counts

| item | value |
|---|---|
| PR #333 head | `868da5e2df89e0ef01ff5da41c87444ebbd72b32` (branch `audit/td-real-gate-executor-readiness-20261013`, base = PR #313 branch) |
| PR #313 head | `206167a1eb86f1dec5f8285db56accbcd469bce9` (branch `science/td-real-target-tournament-executor-20261012`; verified ancestor of #333 head) |
| PR #313 base | `science/td-target-tournament-scaffold-20261011` @ `816f480d5af5074b5b570c91b13e887fe8064b9c` |
| matrix path | `results/target_discovery/real_tournament/TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V1.csv` |
| matrix introduced by | commit `3335e1fa666f1f0338fd108dfa92ef78e2ec6382`; unchanged through 868da5e2 |
| matrix git blob | `158b02c1e54f38ee5f2e11af0ce0518d8a8422c1` |
| matrix SHA-256 (committed bytes, LF, no CR) | `aacae2efef959d744939ccd7af65859d16420568c3777e22ec17d3da165bdb7a` (identical in the new worktree checkout) |

Independent tally (own script `tally.py`, scratch): 198 rows = 6 candidates × 33 gates; required 117, all `RULE_NOT_MATERIALIZED`; non-required 81, all `NOT_APPLICABLE`; `CALLABLE_AND_QUALIFIED` 0, `CALLABLE_NEEDS_QUALIFICATION` 0, `BLOCKED_ON_DEPENDENCY` 0. Per candidate: C1 15, C2 19, C3 19, C6 24, C4 28, C5 12. Every required row has empty callable/executor/estimand/decision-rule hash fields, unit `donor`, source `observation_operator_not_biological_replicate`, the same support triplet (measured_zero VALID, structurally_unsupported ABSTAIN, imputation FORBIDDEN), and the same blocker. Summary JSON counts agree. Claims verified.

Important: a parallel live branch now exists: `origin/engineering/td-real-gate-rule-materialization-20261013` @ `4aa74df7852bae3565de3b4a3f686fe28e520d10` (stacked on 868da5e2, commits 18:02–18:08 EDT today, no PR yet). It materializes 5 structural rules (G1, R2, Q1, Q2, Q3) as `CALLABLE_NEEDS_QUALIFICATION`, and its plan Task 3 is a historical-equivalence ledger that overlaps this audit. This plan accounts for it; it should be coordinated, not duplicated.

## 1. Governing texts (citations used below)

- V2 spec `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md` (blob d996c504 per contract_v2): G-gates L93–139; S/R/Q/M names only L143–176; C4 rule L64, L232–241; status semantics L204–214; donor precision law L216–220; frozen-evidence chain L222–230; C5 L200–202, L243–245.
- V1 spec `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze.md` (superseded for execution but carries the only estimand prose for many gates): teacher/student rights L39–72; units L74–80; B0–B4 L82–116; C1 invariants L118–134; C2 locality L136–149; C3 controls L151–167; C4 L169–183; C5 L185–203; evidence/measurement response L205–224; transfer L226–235; coverage L237–253; G1–G12 L255–293; selection L295–304.
- C6 spec `docs/superpowers/specs/2026-10-12-td-c6-shared-query-composite-v1.md` L31–39, L51–56.
- Measurement prefreeze `docs/superpowers/specs/2026-10-11-td-measurement-noise-floor-prefreeze.md` L45–56, L71–84.
- TD60 `target_discovery/iterations/td60_learned_teacher_continuity/TD60_PROSPECTIVE_SCREEN.md` L18–36, L68–78, L163–235.
- TD57B `target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_PROSPECTIVE_SCREEN.md` L129–202.
- Null role: `docs/agent/TD_84_CELL_TRUTH_TABLE_ROLE_AUDIT_20261011.md` L24, L40, L61; `docs/agent/TD_HISTORICAL_TOKEN_IDENTITY_SHORTCUT_MECHANISM_AUDIT_20261011.md` L67–77.
- Precision: `scripts/v5/td_target_tournament_precision.py` L87–117; `scripts/v5/td_target_tournament_prefreeze_v2.py` L149–185; `custody/takeover_20261011/TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json` keys `precision_rules`, `design_constraints` (only those keys read).
- Gate case coverage: `docs/agent/TD_GATE_CASE_COVERAGE_QUALIFICATION_20261011.md` L32–36.
- PR #312 @ `2ca8a91a960c823cc327d3885d008d3695837e83`: `TD_TD60_SUCCESSOR_PORTFOLIO_READINESS_V1.json` (entry_conditions), `TD_REGULATORY_EVIDENCE_CONTRACT_V1.json` (claim_ladder, candidate_rules, source_rules), `TD_RARE_PROGRAM_QUALIFICATION_CONTRACT_V1.json` (candidate_application, decision_logic, stability_and_firewall), `TD_REAL_TOURNAMENT_EXECUTOR_READINESS_HANDOFF_V1.json`, `TD_RICH_TEACHER_PARTIAL_RNA_STUDENT_INTEGRATION_CONTRACT_V1.json`.
- PR #316 @ `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`: `docs/agent/TD_TEST_OF_TEST_QUALIFICATION_INTERFACE_20261012.md` L182 ("Before any candidate×gate role in #313 becomes real-execution-ready, TD must additionally bind a successful synthetic test-of-test qualification record for that exact executor/estimand/decision-rule identity"); `docs/agent/TD_QUALIFICATION_SYSTEM_REASSESSMENT_20261012.md` §7 L209–226.

## 2. Historical-audits index check (done before searching)

`docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` classifications relevant here (cited, not recomputed):
- "Same-cell thinning / measurement shortcut — ALREADY AUDITED AT TESTED MODEL CLASS" → index itself says "A later deep objective-aligned gate is still required" → not G8-equivalent.
- "Donor recurrence — ALREADY CHARACTERIZED" and "Donor generalization — ALREADY CHARACTERIZED AT LINEAR MODEL CLASS" → descriptive linear-probe statistics on the molecular view, not candidate-vs-falsifier donor contrasts → not G4/G11-equivalent.
- "QID semantic audit — ALREADY AUDITED": `matched-null state intervention != demonstrated paired-wrong-query intervention` → binding constraint on Q7.
- "Target-identity shortcut — OPEN" → S3 / B2 design input.
- Genuinely-open items 6 ("objective-aligned shortcut thresholds frozen before results") and 13 ("measurement-robustness decision rule") → G10/G8 thresholds ABSENT.
Classification of this audit's proposed work: OPEN (no record covers tournament gate executors).

Disclosure: this index (and the replay-interpretation prefreeze) contain historical (September/pre-tournament) descriptive real-data figures; I read them because they are the index/frozen interpretation contract. No current candidate outcome; no figure used as a threshold.

## 3. Exhaustive absence basis for "no equivalent / no implementation"

1. `git fetch origin --prune` (566 remote refs), then `git log --all -G'<24 quantitative gate IDs>' --name-only -- scripts tests docs` → 28 commits; the only code files ever touching these IDs are contract/scaffold/coverage/C6-extension/V79-extension/registry modules (list in `pickaxe_gate_ids.txt`). No gate-specific quantitative executor on any branch or in history.
2. `git log --all -G'(q_count_only|technical_plus_q|identity_support_only|query_agnostic|wrong_q)' -- scripts` → only `td_real_tournament_contract_v1.py`, historical v4 F1 contextual-target executor, and a Lane-A synthetic fixture. No falsifier baseline model implementation exists anywhere.
3. Exhaustive `git ls-files target_discovery/` listing at 868da5e2: the only executors are `td57b_exact_fast_wrapper.py`, `td57b_fixed_relational_recurrence.py`, `td59_replay_closure_executor_v1.py`. TD60 has a prospective screen only, no code.
4. Full listing of `scripts/v5/td_*` at 868da5e2 (41 modules) and script/test file lists of PRs #310, #311, #314 (none), #315 (none), #316, #318–#322, #328–#330.
5. `RELATIONAL_COLLAPSE_CALIBRATION_V1` (named as the source of collapse floors) is referenced on all refs but never materialized (`git log --all -S`).

## 4. Deduplicated gate implementation units (117 rows → 33 gates → 9 families)

Row coverage check: A 20 + B 39 + C 18 + D 5 + E 10 + F 14 + G 7 + H 4 = 117.

Common to every unit (hard rules applied): biological N = unique donors (V2 L216–220, precision helper binds donor IDs); source = stratum/observation operator, never N; measured zero is an eligible value, structurally unsupported abstains, no imputation; case and gate statuses are exactly PASS/FAIL/NOT_ESTIMABLE and NE never becomes FAIL or PASS (V2 L204–214); FAIL is not rescuable by any aggregate (V1 L298; bridge `td_real_tournament_gates_v1.py` L83–88); prospective freeze chain: prefreeze SHA → gate-case coverage → gate evidence → manifest (V2 L222–230); qualification requires a synthetic test-of-test record for the exact executor/estimand/rule identity (PR #316 interface L182).

### Family A — structural / provenance compliance (no numeric threshold by nature)

**A1 G1_INTEGRITY_LINEAGE** — C1,C2,C3,C6,C4,C5 (6 rows)
- Estimand: "Exact bytes, code, population, split, support, operator, teacher/student evidence rights, null seed and prefreeze identities are bound. No post-outcome redesign or relabeling." (V2 L93–95).
- Unit: n/a for decision (provenance); donor identity set must be bound.
- Support: n/a. Source/operator: operator descriptors and source family assignment must be among bound identities.
- Falsifiers: tamper tests (changed byte, changed split, relabelled case, self-declared hash).
- Rule frozen in framework: ABSENT at 868da5e2. Parallel branch rule (4aa74df7 `td_real_gate_rule_registry_v1.py` L38–47, L172–183): PASS iff required identity names unique/nonempty and bound SHA map exact and `post_outcome_redesign`/`post_outcome_relabeling` both false; missing fields NOT_ESTIMABLE; contradiction FAIL.
- Threshold source: none needed (structural).
- Historical equivalent: none. The V2 gate-governance registry is fixture-only (`docs/agent/TD_REAL_TOURNAMENT_EXECUTOR_QUALIFICATION_20261012.md` L95–103).
- Callable: `scripts/v5/td_real_gate_rule_registry_v1.py:evaluate_structural_gate` @ 4aa74df7 (unmerged).
- Prospective rule qualification still required: yes. Concern: rule accepts self-attested booleans/hash maps; V2 L228 says "A self-declared hash inside an object is not sufficient freeze authority" — the executor must recompute hashes from bytes.
- Classification: **CALLABLE_NEEDS_QUALIFICATION**.

**A2 R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING** — C2,C4 (2)
- Estimand: V1 L144–149: "Forbidden: nearest-third primary mining; treating historical nearest-half as the production neighborhood constant; post-outcome locality search. The exact production-scale relation must be defined from the future lawful target-tournament population under a frozen rule. If no lawful non-outcome rule exists, C2 is evaluated as broad/global only." V2 names only (L152).
- Unit: n/a (provenance). Source/operator: locality rule must not be source-tuned.
- Falsifiers: attempt to pass with a post-outcome locality, nearest-third, or historical nearest-half constant; PR #316 reassessment L216: "R2/R3 must not encode the old TD57C hard-locality overreach".
- Rule: parallel branch L48–52, L185–186: PASS iff `locality_rule_prefrozen` true and `fine_neighborhood_mining_used` false; missing NOT_ESTIMABLE.
- Threshold: none needed. Historical equivalent: none. Callable @ 4aa74df7.
- Concern: self-attested booleans; should verify the locality rule's hash precedes the outcome namespace and that it is not one of the forbidden constants.
- Classification: **CALLABLE_NEEDS_QUALIFICATION**.

**A3 Q1_Q_SCALAR_STUDENT_ABSENT + Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE** — C3,C6,C4 (3+3 = 6) — one implementation, two sink roles
- Estimand: V1 L62–68 ("q address is allowed as conditioning; q scalar is forbidden; q-derived full-library normalization is forbidden; QC features that deterministically leak q are forbidden ..."); V1 L153 ("independent normalization that excludes q").
- Unit: n/a (lineage). Support: n/a.
- Falsifiers: direct q edge, transitive q via QC/normalization node, omitted role, cycle (already in guard tests).
- Rule: parallel branch L54–59, L66–71: PASS iff required sink exists and `td_query_information_guard.assert_query_safe` accepts; missing NOT_ESTIMABLE; leak/invalid FAIL.
- Historical equivalent: component only — `scripts/v5/td_query_information_guard.py` blob 3ca60c5f (qualified, `TD_QUERY_LINEAGE_CONTRACT_QUALIFICATION_20261011.md`) — same estimand on an abstract graph, but it does not prove the declared graph equals the executed data flow; the gate wrapper is new.
- Callable: `td_real_gate_rule_registry_v1.evaluate_structural_gate` @ 4aa74df7 reusing the guard. Note PR #313 adapter only checks a key name `query_scalar_student` (`td_real_candidate_adapters_v1.py` L72–73) — not equivalent.
- Qualification still required: yes, including graph-to-code binding.
- Classification: **CALLABLE_NEEDS_QUALIFICATION**.

**A4 Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR** — C3,C6,C4 (3)
- Estimand: V1 L43 ("A teacher receiving query scalar x_q must have an otherwise identical q-excluded ablation") and L157 ("q-excluded teacher is primary anchor").
- Rule: parallel branch L60–64: PASS iff boolean `q_excluded_teacher_primary_anchor` true. Self-attested; no lineage check (the guard vocabulary has no teacher-primary-anchor sink, so a lineage version needs a prospective vocabulary extension).
- Historical equivalent: none. Callable @ 4aa74df7.
- Classification: **CALLABLE_NEEDS_QUALIFICATION** (weakest of the five; recommend lineage-based replacement).

**A5 M1_CIRCULARITY_CONTROL + M2_INDEPENDENT_PROVENANCE** — C5 (1+1)
- Estimand: V2 L245 "Regulatory evidence reused during target construction cannot later be called independent validation"; V1 L189–201 (allowed: "independent falsifier when circularity is controlled"; forbidden: "clean external validation when the same data generated the relation"); PR #312 regulatory contract `source_rules.same_nucleus_and_separate_nucleus_not_equivalent`, `missing_evidence: MISSING_NOT_ZERO`.
- Unit: donor (provenance disjointness evaluated per donor/dataset). Source: evidence class per PR #312 `evidence_classes`.
- Falsifiers: same-data reuse; same-nucleus vs separate-nucleus mislabel.
- Rule: ABSENT. Threshold: none intrinsically needed (provenance set disjointness), but evidence classes are undefined until C5 is instantiated.
- Historical equivalent: none.
- Classification: **BLOCKED_ON_DEPENDENCY** — dependency: dedicated C5 activation/instantiation contract (V1 L187 "disabled by default ... may be activated only where independently authenticated regulatory/chromatin support exists under a dedicated contract") naming which regulatory evidence builds the target vs which validates it.

**A6 M3_CAUSAL_CLAIM_FALSE** — C5 (1)
- Estimand: V1 L196–198 ("may not be treated as validated causal regulation"); PR #312 claim ladder R3 = REGULATORY_SUPPORT → CAUSAL_PERTURBATIONAL_PREDICTION; graph policy not_permitted "claim validated causal GRN".
- Rule: ABSENT; implementable now as a claim-label compliance check (no numeric threshold). Historical equivalent: none.
- Classification: **RULE_NOT_MATERIALIZED**.

### Family B — falsifier-defeat contrasts (one shared kernel)

Shared kernel: per-case contrast → per-donor delta → donor-level decision statistic within frozen decision family. Present pieces: PR #313 falsifier engine (`td_real_tournament_falsifiers_v1.py`: MSE delta `baseline_loss - student_loss`, donor mean, unsupported cases skipped); precision helper `sign_recurrence_gate` (exact two-sided donor sign test; `pass` iff estimable and positives>negatives and p<=alpha_eff; ties excluded); Bonferroni prefreeze (`alpha_eff = family_alpha / family_size`). Missing: baseline models (none exist anywhere, §3.2), frozen statistic choice, `family_alpha` (only 0.05 in test fixtures — NOT a frozen value), decision-family registry, per-block evidence for composites, rare-stratum reporting, case→gate aggregation. Threshold source for every Family-B gate: **ABSENT** (`TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json` precision_rules: `alpha_eff_must_be_frozen_before_outcomes: true`; design_constraints: `no_historical_performance_number_used_as_future_cutoff`).

**B1 G2_NONTRIVIAL_BIOLOGICAL_CONTENT** — all 6 candidates (6)
- Estimand: "Beats B0/B1/B2 and applicable B3 controls on donor-primary estimands." (V2 L97–99); B0 L86–88, B1 L90–94, B2 L96–100 of V1.
- Unit: donor. Support: falsifier engine skips STRUCTURALLY_UNSUPPORTED, keeps measured zero. Source: report per source before pooling (V1 L80).
- Falsifiers: constant_train_mean, technical_operator_only, address_support_operator (+ matched_wrong_cell where applicable).
- Rule: ABSENT. Historical equivalent: none (index "within-donor signal" is a descriptive ridge R2, different estimand).
- Classification: **RULE_NOT_MATERIALIZED**.

**B2 G3_CORRECT_CELL_SPECIFICITY + R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT** — G3 all 6; R3 C2,C4 (6+2 = 8) — R3 duplicates G3's relational clause ("relational candidates also defeat B4 where estimable", V2 L101–103)
- Estimand: V1 B3 L102–112 ("Preserves as much as possible: query/address identity; physical support; operator/source composition; donor-primary weighting; marginal scale; measurable target coordinates; while breaking cell-specific biological correspondence ... within frozen strata"); B4 L114–116 (wrong cell "from a predeclared teacher-local or matched biological neighborhood so that coarse cell-class structure alone cannot pass").
- Unit: donor. Support: null must preserve support state.
- Rule: ABSENT. Historical: TD57B/TD59 matched-Y null (within donor×operator depth/detection blocks; p95 of 64 nulls) is a kernel for molecular-view geometry, not this estimand; `scripts/v5/td_target_tournament_nulls.py` (qualified derangement, stratum = donor, operator, support_key, depth_bin, detection_bin) is the frozen null component.
- Blocking defect: PR #313 case ledger partner (`td_real_tournament_case_ledger_v1.py` L89–106) requires a **different donor**, matches only source/operator/split/query, ignores support/depth/detection, and picks one fixed `min(donor_id, cell_id)` partner per stratum (many-to-one, not a null distribution); pinned by `tests/v5/test_td_real_tournament_falsifiers_v1.py` L49–55. This contradicts `TD_84_CELL_TRUTH_TABLE_ROLE_AUDIT_20261011.md` L24/L40 ("primary wrong-cell null is required to preserve at least donor and operator ... relaxing donor preservation ... would violate the frozen tournament design") and the token-identity audit L75–77.
- Classification: **BLOCKED_ON_DEPENDENCY** — dependency: explicit prospective supersession of the PR #313 ledger wrong-cell partner to the frozen donor+operator(+support/depth/detection)-preserving derangement null with a frozen null-draw count, plus a frozen fine-neighborhood rule (shared with A2).

**B3 S3_IDENTITY_SUPPORT_BASELINE_DEFEAT** — C1,C2,C6,C4 (4)
- Estimand: token-identity audit L71–73: "the learned shared state must beat an explicit identity/support-only shortcut baseline under held-donor evaluation. A source/operator classifier alone is not enough". V2 names only (L147).
- Unit: donor (held-out donors). Falsifier: identity_support_only.
- Rule/threshold: ABSENT. Historical: none (index lists target-identity shortcut as OPEN).
- Classification: **RULE_NOT_MATERIALIZED**.

**B4 Q4–Q8 (q_count_only, q_address_only, query_agnostic, wrong_q, technical_plus_q defeat)** — C3,C6,C4 × 5 gates (15)
- Estimand: V1 L155–163 (controls list); token-identity audit L67–69 (q/address-only = "training-donor q-specific mean/bias"); QID index rule: wrong-q must be a demonstrated paired wrong-query intervention, not a matched-null state.
- Unit: donor; cases are (cell, q) — note PR #313 ledger allows one row per cell (L59–61), so only one q per cell is representable.
- Composite requirement: for C6/C4 the contrast must be evaluated on the query block only; PR #313 falsifier engine concatenates blocks into one MSE (L43–57), so a strong shared block can mask a failing query block.
- Rule/threshold: ABSENT. Historical: v4 F1 `qid_wrong_query_map` (`scripts/v4/run_contextual_target_f1_real_production_v1.py` L345 @ f1f14fdb, branch `f1-real-production-executor-20260904`) — a reusable paired-wrong-query construction, but different target (historical F1 contextual target), cosine margin, no donor-primary decision rule → not equivalent.
- Classification: **RULE_NOT_MATERIALIZED** (C3 rows first; composite rows need per-block evidence).

**B5 G10_COLLAPSE_SHORTCUT_RESISTANCE** — all 6 (6)
- Estimand: "Noncollapse is necessary but not sufficient. Candidate must also defeat its prospectively assigned shortcut baselines at the selected checkpoint/target definition." (V2 L129–131); V1 L286–287 ("Variance/rank/covariance health is necessary but not sufficient").
- Unit: donor (shortcut part); per source×view telemetry (TD60 L250–263 lists finite fraction, centered variance, median pairwise spread, entropy effective rank, tie fraction).
- Threshold: ABSENT — collapse floors "deliberately absent" pending `RELATIONAL_COLLAPSE_CALIBRATION_V1` (`docs/agent/TEACHER_STUDENT_RELATIONAL_TARGET_V2_20260908.md` L48), which does not exist on any ref; shortcut thresholds = index open item 6.
- Duplication: the shortcut part re-adjudicates B0/B1/B2/identity/q contrasts already owned by G2/S3/Q4–Q8.
- Classification: **RULE_NOT_MATERIALIZED**.

### Family C — donor / source / transfer replication

**C1 G4_DONOR_RECURRENCE** — all 6 (6)
- Estimand: "Donor is the biological replication unit. Repeated cells/queries/coordinates within a donor do not inflate N." (V2 L105–107); V1 L269–270 "No pooled-only success".
- Unit: donor. Callable component: `td_target_tournament_precision.sign_recurrence_gate` (qualified helper, `TD_PRECISION_NUMERIC_CUSTODY_QUALIFICATION_20261011.md`); `td_donor_resampling_audit.audit_cases` for dependence of resampled cases.
- Ambiguity: as written G4 is a property of G2/G3 endpoints, not a separate quantity; needs its own estimand (e.g., deterministic donor-half recurrence as in TD57B L140–151) or an explicit statement that it is the donor-level replication requirement of named endpoints.
- Threshold: ABSENT (alpha_eff). Historical: index "Donor recurrence" descriptive → not equivalent.
- Classification: **RULE_NOT_MATERIALIZED**.

**C2 G5_SOURCE_REPLICATION** — all 6 (6)
- Estimand: "HVS, NPH52 and SEA_AD are adjudicated explicitly. Source failure cannot be hidden by SEA_AD abundance. Unsupported specialist source combinations may be NOT_ESTIMABLE, never silently omitted." (V2 L109–111).
- Unit: donors within each source; source is a stratum (never N=3).
- Rule: ABSENT; case→gate aggregation deliberately not frozen (`TD_GATE_CASE_COVERAGE_QUALIFICATION_20261011.md` L34–36: "Different scientific gates can lawfully have different prospective treatment of source replication and NOT_ESTIMABLE"). Replay Pattern G ("NO_UNIVERSAL_SOURCE_REPLICATION") applies to replay only.
- Historical: TD49S iteration (not opened) is a historical target family → not equivalent.
- Classification: **RULE_NOT_MATERIALIZED**.

**C3 G11_TRANSFER** — all 6 (6)
- Estimand: "Meets every prospectively declared valid level among held-out donor, operator/matrix, study family and technology. Invalid/unavailable levels are NOT_ESTIMABLE, not omitted." (V2 L133–135; V1 L226–235).
- Unit: held-out donors. Rule/threshold: ABSENT; valid levels per candidate not declared.
- Historical: index LODO descriptive → not equivalent.
- Classification: **RULE_NOT_MATERIALIZED**.

### Family D — information rights

**D1 G6_TEACHER_INFORMATION_ADVANTAGE** — C1,C2,C3,C6,C4 (5)
- Estimand: "Teacher target is constructed from richer lawful evidence; student cannot access withheld target information directly or transitively." (V2 L113–115; rights V1 L39–72).
- Two parts: structural no-leak (lineage guard generalized beyond q) + quantitative information-advantage contrast. Parallel branch removed G6 from the structural set (commit 6bd829e0: "keep G6 blocked pending prospective contrast").
- Historical: replay "G6/G7" (`JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`) are corrected-value integrity checks — name collision, not equivalent.
- Classification: **RULE_NOT_MATERIALIZED**.

### Family E — evidence and measurement response

**E1 G7_EVIDENCE_CONVERGENCE** — C1,C2,C3,C6,C4 (5)
- Estimand: V1 L209–217: `C_i(p) = distance(z_i(p), z_i(full_evidence))`, `Delta_i(p->p') = distance(z_i(p'), z_i(p))`; "reproducible convergence/stabilization as biological evidence increases"; V1 L207 "Exact fractions and resampling counts require a separate precision/compute freeze".
- Unit: cell-level curves aggregated to donor. Rule/threshold: ABSENT ("under the frozen criterion" — criterion never frozen).
- Historical: replay "G7" name collision; TD58S (not opened) different object → not equivalent.
- Classification: **RULE_NOT_MATERIALIZED**.

**E2 G8_MEASUREMENT_ROBUSTNESS** — C1,C2,C3,C6,C4 (5)
- Estimand: V2 L121–123; measurement prefreeze L45–56 (same-cell split displacement; thinned-to-full displacement at 25/50/75/100%; donor-primary/source-explicit distributions) — explicitly diagnostics.
- Rule: measurement prefreeze L75: "this prefreeze does not invent a numeric equivalence/noninferiority margin"; L77–84 lawful sequence requires executing the empirical reference first and then freezing the margin in a new pre-outcome contract.
- Components: `td_measurement_noise_fixture.py` (synthetic-only split/thinning). Historical: index same-cell thinning audit → not equivalent.
- Classification: **BLOCKED_ON_DEPENDENCY** — dependency: authorized empirical same-cell count-split/depth reference under a separately frozen executor, then a margin contract not tuned to candidate performance.

### Family F — learned-state geometry stability

**F1 G9_LEARNED_TEACHER_CONTINUITY** — C1,C2,C6,C4 (4)
- Estimand: "For learned shared targets, rich-state geometry recurs across frozen disjoint views and donor-balanced refits before student success is considered." (V2 L125–127).
- Relational instantiation: TD60 (frozen rule L206–235: donor-half passes iff median donor latent-order agreement > 0.5 and > matched-null p95; 48/48; mechanics failure NOT_ESTIMABLE) — never executed, no code, requires successor u40 (L18–36).
- Sequencing conflict: PR #312 `TD_TD60_SUCCESSOR_PORTFOLIO_READINESS_V1.json` entry conditions include "audited real target tournament complete" and "explicit owner target-portfolio selection decision" and "bounded qualification-only u0_to_u40 authority"; its C1 line says learned-teacher continuity applies "if selected". The tournament makes G9 mandatory before selection. If G9 can only be NOT_ESTIMABLE in-tournament, the bridge makes C1/C2/C6/C4 NOT_ESTIMABLE and no foundation candidate can ever become ELIGIBLE.
- Duplication: V2 wording overlaps S1 (disjoint views) + S2 (donor-balanced refits).
- Classification: **BLOCKED_ON_DEPENDENCY** — dependency: controller decision on in-tournament G9 definition vs post-selection TD60 successor; if it requires a learned teacher, also successor u0 + bounded u0→u40 authority.

**F2 S1_DISJOINT_VIEW_RECURRENCE** — C1,C2,C6,C4 (4)
- Estimand: V1 L124 "disjoint-view teacher geometry recurrence"; V2 names only.
- Kernel: TD56S/TD57B disjoint-view triplet-order + matched-null p95 (TD57B L129–202) — historical object is molecular-view geometry, not the C1 target → not equivalent.
- Threshold: ABSENT for this object. Classification: **RULE_NOT_MATERIALIZED**.

**F3 S2_DONOR_BALANCED_SUBSPACE_STABILITY** — C1,C2,C6,C4 (4)
- Estimand: V1 L128 "subspace stability under donor-balanced refits"; L132 "If axes rotate but the subspace is stable, the scientific object is the stable subspace/block, not individual coordinates" (rotation-invariant metric required).
- Historical: none found. Threshold: ABSENT. Classification: **RULE_NOT_MATERIALIZED**.

**F4 R1_SCALE_FREE_RELATIONAL_RECURRENCE** — C2,C4 (2)
- Estimand: V1 L140–143 (global/broad donor-local scale-free order; mesoscale if replay supports); replay interpretation routing (Pattern A/B) limits the scale class.
- Kernels: TD57B executor (`target_discovery/iterations/td57b_independent_triplet_recurrence/td57b_fixed_relational_recurrence.py`), TD59 replay-closure executor, PR #316 `scripts/v5/td_relational_successor_gate_v2.py:evaluate_relational_profile` @ 2397ab83 (scale grid 1/8..1/2; PASS iff observed > 0.5 and > family p95; real-data HOLD pending known-truth qualification). All evaluate data geometry, not the C2 candidate target → not equivalent; reusing their PASS shape for R1 is a new prospective decision.
- Classification: **RULE_NOT_MATERIALIZED**.

### Family G — coverage / abstention

**G1' G12_COVERAGE_ABSTENTION + M4_SUPPORT_ABSTENTION** — G12 all 6; M4 C5 (6+1 = 7) — M4 duplicates G12 for C5 (C5 requires both)
- Estimand: V2 L137–139 ("Meets the prospectively frozen minimum eligible coverage without forced imputation and reports donor/source/operator/query support plus abstention reasons"); V1 L239–247 reporting list; V1 L203 specialist eligibility/abstention reported separately.
- Unit: donors/sources/operators/queries counts. Support: structural abstention counted, measured zero counted as eligible.
- Threshold: ABSENT — V1 L292–293 "The numeric threshold must be derived before execution from corpus/precision requirements".
- Historical: none. Classification: **RULE_NOT_MATERIALIZED** (both).

### Family H — increments over qualified constituents

**H1 R4_INCREMENT_OVER_C1_SHARED (C2,C4; 2), C6_INCREMENT_OVER_C1_C3 (C6; 1), C4_INCREMENT_OVER_CONSTITUENTS (C4; 1)** — one kernel
- Estimands: V2 L232–241 (C4: "added donor-primary biological information or robustness beyond the strongest qualified constituent ... does not reduce transfer, increase shortcut dependence, collapse coverage, or mix biological with measurement uncertainty"); C6 spec L37 (same, "beyond the stronger qualified constituent"); V1 L44 (C2 adds relational information beyond C1).
- Unit: donor. Rule/threshold: ABSENT; "stronger/strongest constituent" metric undefined.
- Classification: **BLOCKED_ON_DEPENDENCY** — dependency: qualified executors for the constituent endpoints (G2/G3/G4/G5/G10/G11/G12 per constituent) plus a frozen definition of the comparison metric; R4 additionally needs a frozen rule for C1 not qualified.

### Summary of classifications

| class | unique gates | rows |
|---|---|---|
| CALLABLE_AND_QUALIFIED | 0 | 0 |
| CALLABLE_NEEDS_QUALIFICATION (branch 4aa74df7, unmerged) | G1, R2, Q1, Q3, Q2 | 17 |
| RULE_NOT_MATERIALIZED | G2, G4, G5, G6, G7, G10, G11, G12, S1, S2, S3, R1, Q4–Q8, M3, M4 | 77 |
| BLOCKED_ON_DEPENDENCY | G3, R3, G8, G9, R4, C6_INC, C4_INC, M1, M2 | 23 |
| NOT_APPLICABLE (non-required) | — | 81 |

C5 rows of shared gates (G1–G5, G10–G12) are additionally execution-blocked by the C5 activation contract.

## 5. Shared building blocks

| id | block | existing pieces | gates served |
|---|---|---|---|
| BB1 | non-fixture gate-executor envelope + real registry (PASS/FAIL/NE + raw sufficient statistics + executor/estimand/rule SHA; byte-recomputed hashes) | `td_real_tournament_gates_v1.py`, `td_target_tournament_gate_evidence_v2.py`, branch registry @4aa74df7 | all |
| BB2 | falsifier baseline models B0, B1, B2, identity+support, q-count-only, q-address-only (training-donor q mean/bias), query-agnostic, wrong-q (paired), technical+q, q-excluded teacher | none anywhere; F1 `qid_wrong_query_map` as a construction reference | G2, G3, S3, Q4–Q8, G10 |
| BB3 | matched wrong-cell + fine-neighborhood nulls with multiple draws | `td_target_tournament_nulls.py` (qualified); PR #313 ledger partner must be superseded | G2(B3), G3, R3 |
| BB4 | per-block, case_id-keyed, donor-primary falsifier evidence with rare-stratum and per-source reporting | PR #313 falsifier engine (needs repair) | Families B, C, H |
| BB5 | donor-level decision statistic + decision-family registry + case→gate aggregator | `td_target_tournament_precision.py`, `td_target_tournament_prefreeze_v2.py`, `td_gate_case_coverage_v2.py` | B, C, F, G, H |
| BB6 | deterministic donor-split / source-stratified case generator + dependence guard | TD57B split recipe (L140–151), `td_donor_resampling_audit.py` | G4, G5, G11, S2 |
| BB7 | lineage/provenance guard (q-lineage; generalize for teacher anchor, evidence rights, regulatory provenance) | `td_query_information_guard.py` | Q1–Q3, G6, M1, M2 |
| BB8 | empirical count-split / depth-thinning executor | `td_measurement_noise_fixture.py` (synthetic only) | G8, G7 (contrast) |
| BB9 | geometry-recurrence kernel (triplet order + matched-null p95) | TD57B/TD59 executors, PR #316 gate v2 | S1, R1, G9 |
| BB10 | test-of-test qualification harness on frozen synthetic truth | PR #316 test-of-test interface + `td_test_qualification_package_v*`, V79 crosswalk worlds | every gate before CALLABLE_AND_QUALIFIED |

## 6. Recommended implementation order (dependencies first)

0. Controller decisions §7 Q1–Q4, Q17 (statistic, alpha, decision family, null construction, per-block evidence, population freeze).
1. BB1 + BB10 (envelope and qualification harness) — no biology.
2. Harden and qualify the 5 structural gates on branch 4aa74df7 (G1/R2 byte verification; Q2 via lineage); add M3.
3. BB3 supersession (null), BB4 repair (per-block, case_id keys, rare strata), BB2 baseline models.
4. BB5 statistic + aggregator; then G2, S3, Q4–Q8 for C3, then C6/C4 query-block versions; G10 shortcut part (telemetry only until collapse floors exist).
5. G3/R3 once BB3 lands.
6. BB6 → G4, G5, G11 on the endpoints from step 4.
7. G12/M4 after coverage minimum is derived (Q9).
8. G6 (structural part from BB7, contrast after Q-decision).
9. BB8 → G7; G8 only after empirical reference and margin contract.
10. BB9 → S1, S2, R1; G9 after the sequencing decision (Q6).
11. H1 increments after constituents qualify.
12. C5 activation contract → M1, M2.
13. Regenerate real readiness manifest with real hashes; outcome-blind QUALIFY; independent audit.

## 7. Controller-decision questions

- Q1. Decision statistic and alpha for Family B/C: MSE delta (current engine) vs rotation-invariant metric for latent targets; exact sign test vs permutation; `family_alpha` (ABSENT — 0.05 appears only in tests); decision-family membership; any minimum effect size (ABSENT).
- Q2. One authority per contrast: G2 vs G10 vs S3 vs Q4–Q8 (same baselines); G3 relational clause vs R3; G9 vs S1+S2; G12 vs M4; G4 vs donor-primary requirement of G2/G3. Which gate owns each contrast?
- Q3. Wrong-cell null: adopt `td_target_tournament_nulls.py` stratum (donor, operator, support_key, depth_bin, detection_bin) and supersede the PR #313 cross-donor ledger partner; null draw count; fine-neighborhood definition.
- Q4. Composite per-block evaluation: which block each Q/S/R gate tests for C6/C4.
- Q5. Case→gate aggregation per gate (especially G5, G11, G12): when does a NOT_ESTIMABLE case (invalid transfer level, unsupported source) make the gate NOT_ESTIMABLE vs PASS-on-valid-levels; is source disagreement FAIL or a source-conditional result?
- Q6. G9: in-tournament definition (non-trained teacher geometry?) vs post-selection TD60 successor; otherwise C1/C2/C6/C4 can never be ELIGIBLE.
- Q7. What produces Z_shared / Z_query / Z_rel targets and students for the real tournament, and does it need bounded teacher-training authority? (Upstream of every gate.)
- Q8. G8 ordering: is computing candidate measurement-displacement before the margin is frozen an outcome inspection?
- Q9. G12 coverage minimum derivation (precision budget from the frozen tournament population).
- Q10. G7 evidence-ladder fractions, resampling counts and stabilization criterion.
- Q11. G11 valid transfer levels per candidate.
- Q12. Increment metric ("stronger/strongest qualified constituent"); R4 when C1 is not qualified; should C4 also beat C6 (C6 spec L51–56) given C4_INCREMENT is defined over C2+C3?
- Q13. C5 instantiation: activation contract; C5 adapter carries `regulatory_student` (adapters L42), implying a learned teacher/student state for which V2 L200–202 requires a separately frozen G6–G9 extension.
- Q14. Rare-program fitness (PR #312 contract: required for C1/C3 and active C2/C6/C4) is not in the 33-gate universe: new gate (explicit prospective supersession of the PR #313 contract) or a mandatory case stratum inside existing gates? Its "critical loss" has no threshold.
- Q15. Which gate adjudicates the `q_excluded_teacher` falsifier delta (Q2 is structural)?
- Q16. Accept the branch-4aa74df7 structural rules as written (self-attested booleans) or require byte verification first?
- Q17. Freeze the real tournament population/donors/splits/support registry (V2 L28) — prerequisite for execution and for geometry-derived parameters (R1/R2/G12).

## 8. Hard-rule findings in PR #313 / #333 (and the branch)

1. Wrong-cell null contradicts frozen design (donor-preserving, support/depth/detection-matched): ledger L89–106, test L49–55 vs TD_84 audit L24/L40 and token-identity audit L75–77. Cross-donor partner confounds donor identity with cell specificity (donor-unit rule). Single fixed partner per stratum is not a null distribution.
2. Composite non-compensation at evidence level: falsifier engine concatenates shared/relational/query blocks into one MSE (L43–57); a strong block can mask a failing block (V2 L64; V1 L181).
3. C2→C1 constituent rule not enforced by routing V4 (L96–97 resolve only C6/C4) although the contract declares C2 parents [C1] (contract L83–90); relies on an unmaterialized R4.
4. Rare/local: only donor-mean deltas (falsifier L66–71); no rare stratum; rare preservation required by PR #312 is absent from the gate universe (AGENTS.md "Rare/local failures cannot be hidden by aggregate means").
5. QUALIFY fail-open: `_validate_manifest` (controller L37–45) accepts any 64-hex `manifest_sha256` and a boolean; it does not recompute the self-hash (which is reproducible as compact sorted JSON) or check per-role bindings (V2 L228).
6. Branch 4aa74df7 structural rules G1/R2/Q2 pass on self-attested inputs (registry L172–192).
7. Status precedence differs: routing V4 `_resolve_composite` (L85–88) puts UNRESOLVED before an ELIMINATED parent; `td_c6_candidate_extension_v1.adjudicate_constituents` (L52–55) puts FAIL first. No PASS rescue, but two authorities for one status.
8. Support granularity: ledger is one row per cell (L59–61) with a cell-level support state; it cannot represent per-(cell,q) support or V1 L165 zero-total panel abstention (which is value-dependent and should be reviewed against the measured-zero rule).
Preserved correctly: NOT_ESTIMABLE ≠ FAIL (bridge L83–88; ledger "no legal partner → NOT_ESTIMABLE"); composite cannot become ELIGIBLE with non-eligible parents (routing V4); C6/C4 failure leaves C1/C3/C2 statuses untouched; C5 specialist-only (bundle L65–73, routing L115); donor-primary aggregation; authority flags all false. No outcome inspection in #313/#333 code paths.

## 9. Files deliberately NOT opened

- All content of PR #314 branch `evidence/td-corrected-replay-outcome-7819aabd-20261012` (head c6899a29) — only its PR title appeared in a PR listing.
- `target_discovery/iterations/**/*_RESULT.md`, `*_CASE_TABLE.csv`, `*_PANEL0_RESULT.md`, `*_CLOSURE.md`, all of `td59_mesoscale_half_locality/replay_closure_20260908/*`, and all TD49S/TD58S iteration files (only the TD57B and TD60 PROSPECTIVE_SCREEN contracts were read).
- PR #312: `TD_CANDIDATE_QUALIFICATION_STATUS_LEDGER_V1.json`, `TD_POST_REPLAY_CANDIDATE_ADJUDICATION_MATRIX_V1.json`, `TD_RARE_PROGRAM_SAME_NUCLEUS_ASSAY_V1.json`, `TD_RARE_PROGRAM_MORABITO_SCENIC_FOLLOWUP_V1.json`, `TD_MULTIMODAL_EVIDENCE_LEDGER_V1.json`, `TD_DATASET_CANDIDATE_CLAIM_MATRIX_V1.csv`, `TD_REGULAR_PROGRAM_*`, `TD_BAYESIAN_RARE_PROGRAM_REASSESSMENT_PREFREEZE_V1.json`, `TD_GSE214979_SAME_NUCLEUS_PREFREEZE_V1.json`, `TD_RARE_SOURCE_OPERATOR_REASSESSMENT_PREFREEZE_V1.json`, `TD_WORKFLOW_CLOSEOUT_LEDGER_V1.json`, `TD_CONTINGENCY_AND_PIVOT_CONTRACT_V1.json`, `TD_POST_REPLAY_AUTHORITY_TRANSITION_CONTRACT_V1.json`, `JEPA_PROJECT_START_HERE_AUDIT_COMPENDIUM_20261012.md`, `JEPA_PROJECT_CONTEXT_INDEX_V1.json`, the STAT1/rare handoffs (possible outcome content).
- docs/agent: `TD_HISTORICAL_QUANTITATIVE_DESIGN_CALIBRATION_20261011.md`, `TD_HISTORICAL_EXECUTOR_FRESH_SCIENTIFIC_AUDIT_20261011.md`, `TD_SCIENTIFIC_TARGET_FRAMEWORK_AND_EVIDENCE_AUDIT_20261011.md`, `JEPA_TARGET_DISCOVERY_FULL_AUDIT_HANDOFF_20261009.md`, `TD_RELATIONAL_G4G5_POST_CRLF_REPAIR_EXECUTION_20261009.md`, `TD_MACHA_TARGET_DISCOVERY_FULL_SCRIPT_OUTPUT_AUDIT_20261011.md`, `TD_SCIENTIFIC_ADVANCE_SELF_AUDIT_20261011.md`, `TD_POST_G7_CORRECTED_REPLAY_READINESS_20261012.md`, handoffs (possible outcome content).
- PR #316 `TD_HISTORICAL_PASS_TEST_QUALITY_REASSESSMENT_20261012.md`; `TD_QUALIFICATION_SYSTEM_REASSESSMENT_20261012.md` read only §5-end via line range (one grep line showed a historical TD57B summary row).
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json`: only `precision_rules` and `design_constraints` printed; other sections seen as key names only.
- PRs #310, #311, #315, #318–#321, #328 results/packages; all `outputs/` trees; any DEV/SEALED RNA; any pathology labels.
