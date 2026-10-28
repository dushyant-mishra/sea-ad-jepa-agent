# Macha review, observation-contract and G7 cross-head delta (2026-10-28)

**Append-only.** New files only, stacked on #322 head `dfaba7967a77`. No frozen receipt, verdict or earlier file is changed. Machine mirror: `results/target_discovery/unified_qualification_v1/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.json`.

**Evidence labels**

| Label | Meaning |
|---|---|
| **[tested]** | Executed code behavior; LOCAL or CI as stated. |
| **[source]** | Repository source or artifact, read directly. |
| **[inference]** | Scientific reasoning from those facts. |
| **[unavailable]** | Cannot be authenticated with the data on hand. |

**Authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## 1. Exact-head verdicts (independent; author lane ChatGPT for all three)

| PR | Head | Verdict | RED PR | CI (review run) |
|---|---|---|---|---|
| #479 V2 normalization view | `ae762d70` | **REPAIR_REQUIRED** | #481 | 40734273672: inherited 124 passed; review 19 failed / 5 passed |
| #476 G7 R5X/R6 snapshot | `26031df2` | **ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS** | #482 | 40735376242: inherited 60 passed / 11 deselected; review 18 failed / 3 passed |
| #477 PS canonical V1/V2 | `c83088de` | **ACCEPT_INCREMENTAL_WITH_LIMITATIONS** | #483 | 40736368351: inherited 35 passed / 1 deselected ×4; review 8 failed / 2 passed ×4 |

LOCAL results were identical on Windows numpy 2.4.6, Windows numpy 1.26.4 and WSL numpy 1.26.4. Verdict comments are on each PR.

### #479: REPAIR_REQUIRED

**Holds.**
- [tested] **Complete student outcome is invariant to all withheld mass.** Across 240 seeded worlds, the exact bytes or the refusal class and message never changed: 123 views and 117 refusals. The teacher view moved in 118 (positive control).
- No physical total is published.
- No shared mutable state.

**RED.**
- **A1:** the consumer validates a depth carrying the physical total, an offset or a scale.
- **A2:** "student" is a self-declared label: non-base rights can be exposed, including the query after relabelling.
- **A3:** an R5X metaclass route in `_view_snapshot`.
- **A4:** the refusal class of an empty-base cell depends on withheld mass. This is **inherited from Macha #474**.

**C (conservation).** The equality rule is not sufficient: an in-ledger alias passes it [tested]. It is also far too strict: every real cell with residual mass is refused [source].

**Limitations.**
- The teacher digest is an unkeyed commitment, opened by enumeration from the student view [tested].
- Barcode reuse fails closed [tested].

### #476: ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS

- **Fixed [tested]:** every #472 R5X and R6 case passes.
- **R1/R2/R1D:** 11 stay RED.
- **New R5X route [tested],** pre-existing since `7452243f`: `_strict_json` runs `type(obj) in (bool, int, str)`. It escapes as `RuntimeError` on all seven binder arguments and on both other entry points.
- **Composition gap [tested]:** V3 takes no binder receipt. Forged rows that the binder refuses still decide PASS when V3 is called directly.

### #477: ACCEPT_INCREMENTAL_WITH_LIMITATIONS

- **Fixed [tested]:** V1 (`intc`/`uintc`) and V2 (type names in messages) are closed: #473 passes 23/23 in three environments.
- **Pre-existing routes [tested]:**
  - `isinstance` reads a payload `__class__` in `semantic_sha256` (`5ea1c2e6`, Macha lane) and in `_iter_rows` (`f2c7de76`).
  - A chained payload `__cause__`.
- **T2-D** remains RED.

## 2. Production observation contract (scientific recommendation; not implemented)

**Chain:** authenticated deposited bytes → private physical source row → issued per-query rights policy → released rights-bound view → measured teacher target → student prediction.

### Source facts that shape it
- [source] **The physical total contains the query.** `source_library` is the whole-row raw sum *before* address mapping (`scripts/v4/materialize_full104_phase2_expression.py:222`), so it includes the query, off-ledger features and blocked collision features.
- [source] **Collision mass never belongs to a measured address.** Blocked features are removed from the mapping (lines 178–181), and the mapping is enforced injective (line 182). All **11,449** FULL104 (matrix, address) collision pairs have operator state 2, which is exactly the state matrix's total of state-2 entries. So blocked mass never holds molecules of a `MEASURED_SCALAR` address. Probe: `observation_source_census_probe.py`.
- [source] **Residual mass is material for SEA-AD and NPH52** (#475, pooled): SEA-AD 3.99% (max 25% in a row), NPH52 1.4%, HVS 0.0.
- [source] **Our roster ignores expression.** `build_full104_phase2_metadata_selection.py` orders cells by a keyed hash of identity fields under per-donor caps, and is frozen with `no_expression_opened`.
- [unavailable] **Depositor QC rules are not recorded** in the repository, so the depositors' row-inclusion rules remain an assumption.
- [inference] **Mitochondrial queries are QC-entangled.** Typical snRNA QC filters on whole-transcriptome totals and mitochondrial fraction. The address universe holds **30 `MT-*` addresses**, plus 122 `RPS`/`RPL` addresses and `MALAT1`/`NEAT1`. A query on an `MT-*` address would be truncated by the depositors' own selection.

### Recommended released depth: D1 = Σ base-visible `MEASURED_SCALAR` counts (`depth_rule = VISIBLE_BASE_MAPPED_SUM_V1`)
- **It needs no private input,** so noninterference holds by construction.
- **It is ladder-invariant,** satisfying G7 E3's byte law and V3.1.1's E3.
- **It equals V2's depth inside V2's domain** [tested].
- **It runs on real rows with residual mass,** which V2 refuses.
- **It turns R2 leak detection into an exact consumer law:** depth must equal the sum of the base-right scalar rows. This replaces G7's heuristic pooled-total screen.

**Optional D2 = D1 + residual, named `base_excluded_physical_depth`.** It is admissible only per (query, operator) after an off-ledger alias audit, which checks unmapped source features' symbol and locus against the query using var metadata. Collision mass is already safe (above). No consumer can verify D2, so it is **never the default**.

### Field-level schema

| Layer | Field | Semantics | Status |
|---|---|---|---|
| Physical source row (private) | `asset_sha256`, `matrix_id`, `source_id`, `operator_index` | Deposited matrix | **AUTHENTICATED** (asset registry and materializer journal) |
| | `expression_row`, `canonical_cell_id` | Row in that matrix; checked against H5 obs (lines 215–217) | **AUTHENTICATED_AS_DEPOSITED_ROW** |
| | `cell_key = (source_id, matrix_id, expression_row)` | Source-scoped cell; barcodes repeat across libraries | DERIVED |
| | `donor_id` | Source-namespace label | AS_DEPOSITED; cross-source identity **NOT_ESTIMABLE** (R1D) |
| | specimen/library key | e.g. SEA-AD `sample_name` + barcode | CANDIDATE, not frozen; within-source donor registry blocked |
| | `physical_row_total` | Whole-row raw sum (line 222) | **AUTHENTICATED_DERIVATION**; never released |
| | `mapped_counts[41,238]` | Frozen address space `95d2cafe`; per-matrix injective map | **AUTHENTICATED_DERIVATION** |
| | `collision_blocked_mass`, `off_ledger_mass` | Residual decomposition | DERIVABLE; **not stored** (ETL addition, `reader_fit` only) |
| | `operator_state[42 × 41,238]` | SU / MS / MCU | **AUTHENTICATED CONTRACT** |
| | physical nucleus, UMI/read lineage | | **NOT_ESTIMABLE** (BAM/FASTQ forbidden) |
| | depositor QC and roster rules | Which rows exist | **NOT_RECORDED**; per-query QC-entanglement flag |
| Query rights policy (issued before outcome access) | `query_address_id`, ordered `base_evidence_rights`, ladder, `qc_entangled` | Frozen per query | **ISSUER ABSENT** (fixture only) |
| Released student view | rows: `cell_key`, `donor_id`, `source_id`, `operator_id`, `address_id`, `evidence_right`, `state`, `count` | Four states kept distinct; measured zero = MS with count 0 | per V2 |
| | `base_evidence_rights`, `normalization_depth` (= D1), `depth_rule` | Exact consumer law; no physical total, residual or teacher digest | proposed |
| Teacher view (custodied) | student fields + non-base MS rows; the same D1 | Its digest is as sensitive as its values | proposed |
| Measured teacher target | From teacher-view MS query rows with D1 offset | SU → no target; MCU outside base → NOT_ESTIMABLE; never physical, simulator or surrogate input | target qualification separate (C1/C2/C3/C5) |
| Student prediction | From student view only | Donor-held-out within source | R1D blocks cross-source unit claims |

**CaseBundle V1 and G7's physical `count ≤ library_size`** stay unchanged and valid for custodian-internal physical-total views. V2 is a separate schema; renaming or weakening `library_size` is **not** proposed.

## 3. G7 cross-head interoperability (#479 V2 × #476 G7 E3 + V3)

Probe: `v2_g7_crosshead_probe.py`, LOCAL. It records both trees' source blob hashes; the review-branch heads differ from the PR heads by tests only.

| Category | Result |
|---|---|
| 1. Schema compatibility | **No.** V2 rows give "evidence atom fields are not exact". V2's two-view ladder gives "three or more rights levels" required. G7 atoms carry no `cell_id`, so a per-cell depth law has no key. |
| 2. Same-code-path mechanics | Only through a probe-only rename adapter (V2 depth → `library_size`): **6 of 200** conserved worlds accepted, 194 refused by `count ≤ library_size`. With zero-withheld units: 174 refused by that check plus 26 false refusals by the pooled-total screen. The binder binds an accepted package. **V3 is not reachable:** it needs a qualified decision token, per-unit margins and displacements from a frozen representation, and it takes no binder receipt. |
| 3. Authenticated physical provenance | Not established (R1/R1D/R2). |
| 4. Known-truth scientific qualification | Not available (PS Task 4 absent). |
| 5. Human execution authorization | None. |

**Conclusion [inference].** A rename adapter is not justified: it reintroduces the physical/normalizer conflation. A justified change would be a *versioned* G7 E3 content law: per-cell atoms, the D1 law replacing `count ≤ library_size` above the base and the pooled screen, with G7 E3 V1 kept for old fixtures. That is a contract change for the deciding lane. The G7 decision law is not altered here.

## 4. Remaining tasks

1. **ChatGPT, #479 repair:** carry base rights; exact D1 consumer law; identity dispatch.
   - **A4** is in Macha #474's producer; Macha will author a RED-first one-line repair on request.
2. **ChatGPT, #476 and #477 follow-ups:**
   - identity dispatch in `_strict_json`;
   - a composed bind-then-decide entry point;
   - `type(x) is` before `isinstance`, and `from None`.
3. **Deciding lane:**
   - adopt or reject D1 as the released depth;
   - decide whether D2 is ever admissible;
   - decide whether a versioned G7 E3 content law is wanted.
4. **ETL (`reader_fit` only):** store `collision_blocked_mass` and `off_ledger_mass` per row. Before any D2 use, run the off-ledger alias audit from var metadata.
5. **External:**
   - recover depositor QC methods from publications or portal documentation, not BAM;
   - freeze SEA-AD specimen keys (the R1D within-source registry).
6. **Macha, PS Task 3:** author the repair of #437 R1 (float numeric alias) and R2 (`OBS_` name spoof) against the immutable #480 tests, for independent review.
7. **PS Task 4** stays absent and gated by Tasks 1–3; T2-D RED.
