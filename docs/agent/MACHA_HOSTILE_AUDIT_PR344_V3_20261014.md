# Macha independent hostile audit — PR #344 production-synthetic V3 design

Date: 2026-10-14. Auditor: Macha (coordinator).

**Method.** Three scoped independent critics, per AGENTS.md:
- A: biology / rare / weak / local;
- B: targets / identifiability / real-lane compatibility;
- C: provenance / adversarial.

The coordinator then verified every decision-changing claim directly against code or text. Critic prompts were seeded with coordinator hypotheses to confirm or refute. The critics confirmed several, refuted none, and added many more. Dissent is preserved where severities differ.

**Read-only throughout.** No human candidate outcomes, DEV/SEALED data or pathology labels were opened. No implementation was done.

**Verdict:** `APPROVE_WITH_REQUIRED_AMENDMENTS`. The amendments are **preconditions to implementation planning** (§F).

---

## A. Custody verification

| object | verified identity | note |
|---|---|---|
| PR #344 audited head | `70503fe3dae3afe4cebeb8e2e0fdc71d1598c54f` | matched the expected head at audit start |
| PR #344 later heads | `c1aeaa59…`, then `4fee29f4a01d8806c3d0854bc48b79a47351c980` | deltas are docs/agent ledgers, handoff and checklist only; **0 spec files changed**, so all findings apply to `4fee29f4` |
| delta `dd5d8016`→`70503fe3` | `a6036b83` added `…external-audit-corrections-v1.md` | design-bearing (it changes R1, G11/G12, C4, G6, G8), although docs-only. The handoff's earlier "docs-only after dd5d8016" statement was stale; the owner has since corrected it. |
| V2 base | `8b667097…d8ce830` (632 lines) | |
| V3 amendment | `c9c7b0be…891b44b` (356 lines) | |
| cross-lane addendum | `a612210d…dc858` (133 lines) | |
| external-audit corrections V1 | `c34fff74…6040e` (135 lines) | |
| R5 self-audit | `f828a089…902` | |
| current state @70503fe3 | `7c1cb1ac…94e9` | |
| PR #324 / #325 | `bb5ca60c…` / `bfeb2b86…` | |
| PR #322 / #323 | `9a3de068…` / `606ee870…` | |
| PR #349 / #343 / #345 / #346 / #347 | `1ab453e5…` / `82d17bfb…` / `f16ba70f…` / `5a314bde…` / `877242a6…` | |
| PR #332 / #328 | `902054ad…` / `25bbdbe1…` | |
| **successors opened after the audited head** | #350 R1 v2 `9b9078c1` (03:51:35Z); #351 C4-requires-C6 `b9774be4` (03:52:19Z); #352 G6 margin `65e8cf41` (03:55:17Z) | **not bound by the design**; `70503fe3` was committed 03:51:02Z |
| V80 source | `b840067e4c9439e4cb4aa9e8c649ef2f6064a142` | |
| V80 receipt | `346407af…9c32` (1,922 B) = CI artifact `11867366245` (zip `97e264cf…`) | **defect found:** the in-repo copy at `139ff338` was 1,921 B, `70c65f99…`, invalid JSON (missing final `}`). **Repaired by the owner** at `e99d1f21`; Macha verified the bytes now equal `346407af…`. |

## B. Findings

Severity is the coordinator's final judgment. "Blocks" means it blocks **implementation planning**.

### CRITICAL

**B1 — The sealed test can be gamed: seed custody and outcome-driven generator tuning.** (Critic C F1, Critic A F11, coordinator.)
- **Where:**
  - 01 §13 says only "One frozen generator, at least two realization classes" and "Selective seed replacement/rerun after truth read is forbidden".
  - 02 §3.4 says "No world parameter may be changed after downstream outcomes are inspected **merely** to obtain a PASS".
  - 06 asserts "independently seeded" sealed realizations, but no controlling spec says so; 05 nonetheless marks it PASS.
- **Why:**
  - Nothing orders the generator freeze before downstream runs on development worlds. Dev outcomes, which are lawful with truth visible, can therefore tune difficulty before the sealed draw. This is the "holdout informed method development" failure.
  - "merely" makes the rule depend on intent.
  - Nothing prevents the producer selecting among sealed realizations.
  - The base derives random streams by integer offsets from one seed (#328 `unified_synthetic_integration_v1.py:243` `seed+100_003`, `:253` `seed+701+104729*p`), so the namespaces overlap.
- **Repair:**
  1. Hash-freeze the generator (code, parameter distributions, family mixture, difficulty grid) **before any downstream run on any realization**. Any later change is a new version, re-gates sealed generation, and may never reduce difficulty.
  2. Sealed root seed = H(controller-held ≥256-bit nonce ‖ generator hash ‖ class tag). Commit it before dev runs and reveal it after the fit freeze.
  3. Derive streams by hashing (class, world, component, scientific unit ID).
  4. The producer attests exactly one sealed realization per frozen budget.
  5. Keep an append-only ledger ordering generator commits against downstream runs.
  6. Add a sealed-only withheld mechanism variant to detect overfitting to the generator family.
- **Blocks: YES.**

**B2 — The R1 controller-truth estimand is undefined.** (Critic B F1, coordinator.)
- **Where:**
  - 01 §11: "Relational truth is induced by the biological manifold".
  - 04 §1: the ruler is the molecular addresses, "masked/abstained according to the downstream metric contract".
- **Why:**
  - No document says whether truth `q(i;j,k)` is computed on latent geometry, on the noise-free expected state under the frozen ruler, or on observations. No metric, address set or tie tolerance is given.
  - TD57B (`TD57B_PROSPECTIVE_SCREEN.md` §"Cell-cell concordance distance" @`dccf1868`, verified) uses "pair coordinates where at least one cell is nonzero/resolved". Each pair therefore has its own coordinate set, so a depth asymmetry between j and k alone can flip q.
  - On the expected state (no zeros) that rule is not defined.
  - The synthetic "right answer" therefore does not exist.
- **Repair:**
  - Define two truths prospectively. (a) The **estimand truth**: per-view q on the expected state under the frozen ruler, with a common-coordinate rule within each triplet and a tie tolerance. (b) The **latent-fidelity truth**, scored separately.
  - Add a hostile same-biology counterfactual with depth asymmetry inside a triplet.
- **Blocks: YES** (R1 unit).

**B3 — Evidence masking is unsound: normalization/QC descendants and the masked-address state are unspecified.** (Critic A F1–F3, coordinator. Critic C rated depth/evidence "GUARDED" with residuals; the coordinator sides with A because this is the area prior drafts failed.)
- **Where:**
  - 02 §4.1 holds "all generated measurement realizations" fixed and reveals a "subset of already-generated … evidence".
  - The #163/#178 normalization firewall is scoped only to value-blind q (01 §3.9).
  - 01 §7 defines only three support states.
- **Why:**
  - **Denominator dilemma.** If library size, nGenes or QC are computed over the full bundle, the masked total leaks as L_full − Σvisible. If they are recomputed over visible genes, the visible inputs change between levels, confounding evidence with depth.
  - **Masked-address state.** AGENTS.md: "MEASURED_SCALAR != STRUCTURALLY_UNMEASURED != MEASURED_COLLISION_UNRESOLVED != artificial training mask". A rights-masked address has no state of its own, so it defaults to STRUCTURALLY_UNMEASURED and becomes indistinguishable from a limited panel.
  - **Gameable label.** The real G7 validator checks only a label: #346 `td_real_evidence_ladder_contract_v1.py:49-59`, verified, inspects only the `operator_family` string. A thinning ladder labelled `BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION` passes.
  - **Modality conflict.** 02 §4.1 treats "revealing an already-generated additional modality" as evidence, while 02 §5.1 treats "modality availability pattern" as a measurement domain.
- **Repair:**
  1. Extend the normalization firewall to every rights-masked address and freeze one denominator rule (student inputs are visible raw values; no full-bundle totals).
  2. Add a fourth, distinct `WITHHELD_BY_EVIDENCE_RIGHTS` state or channel.
  3. Mask membership and order come from support and identity-keyed randomness only.
  4. The producer binds each rights token to a content hash of the subset it reveals.
  5. Settle modality-reveal ownership.
  6. Hostile tests: visible bytes identical across levels; poison invariance of masked values; a visible-total-only baseline cannot reproduce the evidence curve; swap detection between mask and structural absence.
- **Blocks: YES.**

**B4 — The mechanism vocabulary is shaped like the candidates, reviving a design the no-repeat ledger rejected.** (A F6, C F2, coordinator; raised from MAJOR to CRITICAL by the coordinator after verifying #325.)
- **Where:** 01 §4 families 10–13 ("additive shared + local/query", "non-additive shared x local/query", "additive shared + relational + query") mirror C6/C4. The #328 `derive_controller_truth` has a one-to-one decomposition (C1 shared, C2 relational, C3 query).
- **Why:**
  - The only guard is a name regex (`_CANDIDATE` in #328), which cannot detect structural mirroring.
  - Composites gain by construction.
  - #325's `TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md` line 11 reads "PR315 V1 candidate-shaped latent design | … | **FAILED AUDIT** | Do not implement". `TD_SYNTHETIC_HISTORICAL_CUSTODY_AUDIT_20261013.md` line 24 says it "risked qualifying candidates in a universe built in their image". Families 10–13 reintroduce that structure as mechanism vocabulary.
  - It also contradicts 01 §9 (no query latent) and §11 ("Do not copy candidate-shaped geometry").
- **Repair:**
  - Restate the families as biology (programs, regulators, niches, manifold), with the candidate mapping computed controller-side after realization.
  - Freeze a rationale for the family mixture.
  - Mandatory out-of-basis worlds that no C-block spans.
  - A capacity-only composite control (random extra block).
  - A deliberately wrong candidate basis as a hostile test.

### MAJOR (all block planning unless marked otherwise)

**B5 — There is no realism/difficulty acceptance criterion, and the implementation base is orthogonal by construction.** (A F7, coordinator, verified.)
- **Where:** 01 §4 is prose. The #328 base (`unified_synthetic_integration_v1.py:286-289`) places rare programs on disjoint contiguous gene blocks `(np.arange(block_width)+p*block_width)`, with one sign template and a fixed `rare_effect_scale=0.55` (`:107`). The mission's core+halo and unusual programs are absent.
- **Repair:** frozen machine checks for:
  - program overlap, and heterogeneity of sign and effect;
  - effect sizes in units of empirical technical noise;
  - eligibility not determined by a single latent label;
  - ceilings on trivial baselines (marker-only, PCA-linear, library-only, source-only);
  - joint comparison of **emitted observations only** against authenticated TRAIN (mean–variance, detection–mean, correlation spectrum, intrinsic dimension), with a stopping rule and never setting latents;
  - an explicit ban on reusing #328 block geometry as production biology.

**B6 — Estimability truth has no identifiable-but-underpowered class, and there is no precision budget.** (A F9, B F6, coordinator.)
- **Where:**
  - 02 §2.2 defines only `ESTIMABLE` and `NOT_ESTIMABLE_BY_CONSTRUCTION`, with ESTIMABLE meaning "enough information remains to identify", and "False abstention on a controller-ESTIMABLE case is a hard error".
  - 01 §10–11 and 04 §4 require underpowered cases that "may be NOT_ESTIMABLE".
- **Why:**
  - Identifiable is not the same as precise. Example: 7 donors under a two-sided sign test at .01 cannot reject (needs ≥8 nonzero donors, `td_target_tournament_precision.py`), so correct abstention is scored as a hard error. That creates a false-certainty incentive.
  - There are no donor or realization counts from a precision budget, and a single sealed draw, so known-truth PASS/FAIL can be a coin toss. No false-qualification rate is ever measured.
- **Repair:**
  - Add a third truth class tied to each pinned executor's finite-sample rule. It is computed controller-side on the realized fit evidence, and both a calibrated COMPLETE and NOT_ESTIMABLE are lawful for it.
  - Derive donor and realization counts from a precision budget.
  - Use replicate sealed worlds to measure operating characteristics.

**B7 — The calibration firewall is missing DEV/SEALED/hold-out and pathology.** (A F10, coordinator.)
- **Where:** 02 §3.1 provenance omits split membership. "Pathology" appears only as "disease/pathology truth" (02 §3.3).
- **Repair:**
  - Require calibration donors ∩ (DEV ∪ SEALED ∪ reserved hold-outs) = ∅, proven by donor-ID string.
  - Ban calibration stratified by pathology or a pathology proxy (including dataset-of-origin used as a disease proxy).
  - Rename the synthetic "development/sealed" realization classes so they do not collide with the real DEV/SEALED splits.

**B8 — Near-oracle teacher evidence is not prohibited.** (C F4, coordinator verified.)
- **Where:**
  - 03 §5 forbids the expected state as a teacher input, but not evidence that approximates it.
  - #328 `unified_synthetic_fit_view_v1.py:147-155`: same-nucleus ATAC = `0.20·log1p(expected_molecular_state) + 0.85·latent_signal + Gaussian noise`. That is dense, over all genes, and uses no count or fragment process.
  - 02 §4.2 "repeated observation realizations" of one nucleus are impossible for destructive assays, and averaging them converges on the expected state.
- **Why:** the G6 margin rehearsal would pass trivially.
- **Repair:**
  - Every teacher modality goes through a sparse count/fragment observer calibrated to authenticated envelopes; stress settings are labelled and excluded from G6 PASS analogues.
  - Repeated realizations are controller-only, or visible but unlinked.
  - Hostile ceiling: a frozen-capacity decoder from teacher evidence to the expected state must stay under an envelope-derived bound.

**B9 — The fit-custody exclusion list is discretionary, and the challenge role leaks.** (C F3, coordinator verified.)
- **Where:**
  - 01 §13: "semantic challenge roles **when revealing**". 01 §3.12: "where package shape could reveal role". Held-out outcomes and twin/counterfactual linkage are omitted.
  - #328 serializes `perturbation_arm` codes (`unified_synthetic_fit_view_v1.py:268`) whose meanings are fixed public constants (`unified_synthetic_integration_v1.py:39-43`: 1 = ACTIVE, 2 = MATCHED_PERTURB_NULL). The answer is fit-side.
- **Repair:**
  - A default-deny fit-side allowlist.
  - Opaque arm, twin and role identifiers.
  - Held-out outcomes, twin linkage and active/null role are controller-only.
  - Hostile test: role must be no better than chance-predictable from fit metadata or package shape.

**B10 — Value-dependent eligibility is not forbidden.** (C F5, A F3.)
- **Where:** nothing requires query selection, evidence masks or R1 ruler/relation membership to depend only on declared support.
- **Why:** if queries are drawn from detected addresses, being queried reveals q>0, which bypasses the q firewall.
- **Repair:**
  - Eligibility is a function of support state plus frozen identity-keyed randomness only; measured zero stays eligible.
  - Hostile test: eligibility is unchanged under within-support value permutation.

**B11 — There is no serialization or order-invariance law.** (C F6, coordinator.)
- **Where:** 01–04 never require invariance of readers, verdicts or commitments to JSON key order, `sort_keys`, shard/file/row order. They also never separate raw-byte hashes from semantic commitments. 02 §7 "bind … by hash" does not pin the registry's order.
- **Why:** this is the exact defect class that consumed the first TD phase-2 one-shot authorization ("frozen profile scale grid mismatch"; fix `1c383b92`), inside the packaging lineage 01 §3.12 adopts. #325 and #344 do not record it.
- **Repair:**
  - A canonical-serialization law.
  - Separate raw-byte and semantic hash fields.
  - Pin the 41,238-address registry by an ordered-content digest naming the exact artifact.
  - Permutation hostile tests against the real readers before any one-shot run.

**B12 — Controls are present but not verdict-bearing.** (C F7.)
- **Where:** only 01 §9 says "verdict-bearing", and only "where applicable". Regulatory twins (01 §10) and relational/graph nulls (01 §3.7, §11) are only "Include"/"require". "Capacity-matched" is undefined.
- **Repair:**
  - Every control is a hard gate, with a prospective applicability matrix frozen with the generator.
  - Nulls come from many matched draws.
  - Measure the empirical false-qualification rate on twin-only worlds, with the count set by a precision budget.

**B13 — `NOT_DIAGNOSED` is legitimized, and estimability truth is limited to sparse-positive families.** (C F8.)
- **Where:**
  - 01 §3.6: "a valid downstream result can be `NOT_DIAGNOSED` or `NOT_ESTIMABLE`". `NOT_DIAGNOSED` is V79's hard-FAIL status, and 02 §2.2 never names it.
  - Controller estimability truth is defined only for sparse-positive families, not for the G7/G8/G11 cases or the 02 §4.1 "ineligible" designations.
- **Repair:**
  - Map `NOT_DIAGNOSED` explicitly to a `NUMERICAL_FAILURE`-class hard failure, never lawful abstention.
  - Extend prospective per-case estimability truth to all families.

**B14 — There is no total precedence order, and live conflicts survive.** (B F7 rated MAJOR; C F9 rated MODERATE; the coordinator rates MAJOR.)
- **Where:** stated precedence is only 02>01 (02:13) and 04>03 (04:6). Live conflicts:
  - V2 §15 lifts the portfolio block on any "hash-bound repaired implementation" (which #332, with the bug, satisfies), while 04 §3 keeps it blocked;
  - two different portfolio blocker terminal strings;
  - 02 §4.1 "20/40/60/80/100%" vs the real G7 "not a tunable fraction grid";
  - G8 299 vs 599 (B16);
  - 03 §8 #9 still uses address-member wording;
  - 03 §4 REQUIRED/NOT_APPLICABLE_STRUCTURAL/BLOCKED_DEPENDENCY vs 04 §2;
  - two Stage70 labels (01 §3.7 vs §16);
  - checklist 08 #41 audits a "held-out outcomes" exclusion that no spec contains.
  - #350/#351/#352 are unbound.
- **Repair:** one consolidated controlling text with a total precedence order, a section-by-section supersession map, one definition per quantity, and explicit binding or classification of #350/#351/#352.

**B15 — R1 has no real executor to rehearse against.** (B F2.)
- **Where:**
  - #347 is rejected, and 04 binds no successor.
  - #350 `9b9078c1` is a static manifest. `distance_formula` is a label (`td_real_relational_manifest_v2.py:33`), with no d/q/null/decision code.
  - It hard-codes `REQUIRED_SOURCES=("HVS","NPH52","SEA_AD")`, so same-code-path rehearsal would need human source names, and it cannot express held-out-source worlds.
- **Repair:** add an explicit `BLOCKED_EXTERNAL_R1_EXECUTOR_AND_SOURCE_PARAMETERIZATION`.

**B16 — G8: the pinned constant contradicts the real lane's controlling law; "support fraction" is undefined; thinning is matrix-seeded.** (B F3, A F5, coordinator verified.)
- **Where:**
  - The real lane's `2026-10-14-td-real-blocked-gates-resolution-self-audit-v3.md` @`8ae96cbd` freezes `alpha_eff = 0.01/3` and `n_min = 299` "per required **donor**/depth technical-reference unit".
  - #343 (`td_real_measurement_reference_v1.py:40-46`) and 04 §5 use `0.01/6` → 599 per "depth/reference unit", with no donor dimension. The arithmetic is correct for each family; the families differ.
  - If PASS needs every donor inside the envelope, family-wise error across donors is uncontrolled (≈1−0.99^D).
  - The support fraction is a caller float; thinning takes a bare matrix with no support mask.
  - Three-state support cannot change under binomial thinning, so the endpoint is either vacuous (1.0) or a detection rate that contradicts "measured zero remains measurement".
  - Thinning is seeded per matrix, not per cell, which conflicts with shard invariance.
- **Repair:**
  - The real lane reconciles 299/599 and the unit (cross-lane; not decidable by the synthetic lane).
  - Define the support-fraction numerator and denominator in three-state terms.
  - Thin only MEASURED_SCALAR entries; pass collisions through unchanged; keep thinned-to-zero as MEASURED_SCALAR.
  - Key randomness to the cell.
  - Mark the G8 decision path BLOCKED_EXTERNAL.

**B17 — G6: "where the owning G6 contract requires it" is a loophole, and the real margin is degenerate.** (B F4, coordinator verified.)
- **Where:**
  - 04 §4. #345 emits PASS/FAIL from the sign alone, and its probe has **no random-number generator** (verified), so "seeded refits" give U_refit ≡ 0.
  - #352 accepts nonnegative caller-supplied margins, so all-zeros pass.
  - #345 sets `human_fail_semantics_qualified=True` from noise-free toy worlds whose null yields NOT_ESTIMABLE, so FAIL is never exercised.
  - 04 §4 omits a noisy no-teacher-signal null world.
- **Repair:**
  - Full G6 rehearsal is BLOCKED_EXTERNAL until a qualified, non-degenerate margin generator exists.
  - Hostile test: reject all-zero margins.
  - **Forbid synthetic worlds from emitting or satisfying any human qualification flag**, closing the synthetic-to-human authority channel.
  - Add the noisy null world.

**B18 — G11/G12 vs #349: transfer and support holes.** (B F5, coordinator verified `td_real_transfer_coverage_contract_v2.py:120-134`.)
- **Where:**
  - Only DONOR requires a fit plus held-out partition. SOURCE, OPERATOR_MATRIX, STUDY_FAMILY and TECHNOLOGY become REQUIRED with ≥2 supported levels and no held-out partition, while V3 §5 requires held-out transfer on every axis.
  - DIMENSIONS is fixed, with no biological-novelty axis.
  - `study_family` = `source` in the freezer.
  - A donor may sit in only one partition, which conflicts with V2 §6.1 "same-donor repeat observations".
  - No mapping exists from address states (collision, rights mask) to stratum states.
  - Whole-candidate BLOCKED-on-any-stratum is not pinned.
- **Repair:**
  - Pin these as hostile tests.
  - Label non-donor held-out transfer and novelty scoring as synthetic-only or BLOCKED_EXTERNAL.
  - Define the partition and support-state mappings (a collision is never UNSUPPORTED_STRUCTURAL).
- **Blocks:** Units 6–8.

**B19 — Source/cohort confounding is absent, and library size is treated as purely technical.** (A F8.)
- **Where:**
  - Source-independent donors make source-shortcut tests too easy. Real sources are confounded with cohort, and dataset-of-origin is a disease proxy.
  - Library size and RNA content partly depend on lineage, but 02 §3.2 drives the observer with mixed source-level envelopes.
- **Repair:**
  - A mandatory sampling-confounded allocation regime with a deconfounded twin.
  - A biological RNA-content term in the expected state.
  - Lineage-conditioned envelopes.
- **Blocks:** Units 2–3.

**B20 — The ATAC/fragment coordinate namespace is unbound.** (A F12, coordinator.)
- **Where:** 01 §8 covers barcode, hash and multiplicity; 02 §7 binds only the RNA 41,238 registry.
- **Missing:** genome build, contig naming, the gene-TSS annotation tied to the registry, the peak/tile registry, and sequence for motif-based Route-B/SCENIC+.
- **Blocks:** Units 5–6.

### MODERATE (plan must encode; not individually blocking unless noted)

- **B21.** The evidence curve is scored only against a realized, noisy full reference (02 §4.1). Also score against the noise-free expected state and hidden biology. (A F4; A rated MAJOR non-blocking.)
- **B22.** Pseudo-rarity has no mechanism. Add heterotypic doublets and ambient RNA as measurement-generated pseudo-novelty. (A F13.)
- **B23.** Novelty is not frozen. Rare regions present in fit biology aren't novel. Freeze a latent-density criterion, add new-module novelty, and add donor familiarity as a third factor. (A F14.)
- **B24.** There is no contaminated-null positive control. The null must share the delivery burden (#328's arm 2 is a no-op). Add a known small-leak null the pipeline must flag. (A F15, coordinator.)
- **B25.** Multimodal technical coupling is missing: a shared per-nucleus quality factor for same-nucleus views; independent draws, ID/order randomization and a row-alignment hostile test for separate-nucleus views. (A F16.)
- **B26.** Rare/local results can be averaged away. Require per-program and per-rare-stratum scoring, and rare regimes both spread across donors and concentrated in 1–2 donors. Restore the PR #324 queue attacks "forced rare-positive injection" and "donor split leakage". (A F17.)
- **B27.** Worlds are shaped around gates (04 §4, 03 §§2–6). Gate verdicts must be computed controller-side from biological parameters, never stored as generator labels. (A F18.)
- **B28.** R5's PASS labels are prose. Relabel them `DESIGN_TEXT_PRESENT__NOT_TESTED`. (C F10.)
- **B29.** Support tests can pass vacuously. Require minimum instance counts per support state per source (A3R: 786 collision-affected addresses, 288 never scalar-materializable), and poison tests on both non-scalar states. (C F11.)
- **B30.** Custody of the base and composed code path:
  - #328 is an unmerged stack, and the real executors sit on six different bases.
  - "wherever interfaces permit" and "thin" are undefined.
  - #328 is internally inconsistent on C4.
  - Declare each component SAME_CODE_PATH or NOT_REHEARSED prospectively. (C F12.)
- **B31.** TargetPortfolio residual gaps beyond the C4 hole:
  - `_qualification_status` accepts any "pass" string, so "under its own receipt" is not enforced;
  - `selected_candidate` and `foundation_candidates` are mutually exclusive, so C6 PASS + C2 PASS + C4 FAIL cannot be represented;
  - non-PASS raises instead of emitting NOT_ESTIMABLE.
  - #351 is not bound. (B F8.)
- **B32.** V79 over-promotion in the recovery ledger (added at `c1aeaa59`). "291 passed hard behaviors as non-regression requirements" includes the **85 post-terminal** V79 gates. V79's frozen terminal lock says post-terminal results "may map failure modes, but they cannot … select a model variant". Restrict binding non-regression to the 207 confirmatory rows, or obtain an explicit controller ruling. Label V79 worlds as non-blind known-answer regression, since their truth is now opened. (Coordinator.)

### MINOR

- **B33.** Stage70/71 labels differ from #325 (`INTERNAL_GAIN__NO_LOCKED_BENCHMARK_AUTHORITY` vs NEGATIVE_PRIOR / INTERNAL_ROBUSTNESS_ONLY). (C.)
- **B34.** V73–V75 detected-feature envelopes depend on the feature universe (96 vs 41,238); prove "address-agnostic" for each envelope. (A F19.)
- **B35.** Depth by repeated realization has no real-lane analogue; label it synthetic-only. (A F19, C F4.)

### Resolved during this audit

- The PR #344 handoff custody statement (`dd5d8016` "docs-only after") was corrected by the owner.
- The V80 in-repo receipt truncation was repaired by the owner at `e99d1f21`, and Macha verified the bytes. The bound receipt identity `346407af…` is now committed, so the CI artifact (expiring 2026-11-13) is no longer the only copy.

## C. Historical authority verdict

| object | verdict | note |
|---|---|---|
| Stage81A3 | NARROW_OK | "architecture incomplete" respected |
| A3R | NARROW_OK | pilot unfrozen; three-state support only (but see B3: the fourth "artificial mask" state is required by AGENTS.md) |
| V72–V75 | NARROW_OK | 96-feature boundary explicit (02 §3.5); minor: the 01 §3.3 heading "qualified" fits V75 only |
| V77 | NARROW_OK | qualitative only |
| V78 | NARROW_OK | prohibited negative prior |
| Stage70/71 | NARROW_OK (minor label mismatch, B33) | |
| V53–V58 | NARROW_OK | controls only |
| PR #163/#178 | NARROW_OK | but its firewall is under-scoped (B3, B10) |
| PR #199/#312 | NARROW_OK | |
| PR #318–321 | NARROW_OK as a pattern | its serialization defect class is not carried forward as a lesson (B11) |
| **PR #328** | **OVER_PROMOTED** | 01 §20.10 "supply the current candidate-neutral unified architecture"; §3.11 inherits its candidate mapping and its orthogonal block geometry (B4, B5), near-oracle ATAC (B8) and role-revealing fit view (B9). #325 classifies it FIXTURE_ONLY. |
| **V79** | **OVER_PROMOTED (moderate)** | 01 §3.6 legitimizes `NOT_DIAGNOSED` as "valid" (B13); the recovery ledger binds post-terminal gates as non-regression requirements (B32) |
| V80 | NARROW_OK | separate frozen package; principles only; custody repaired |

## D. Real-lane compatibility verdict

| gate | status | reason |
|---|---|---|
| G6 | **BLOCKED_EXTERNAL** | margin degenerate (U_refit ≡ 0); zero margins accepted; human-FAIL flag qualified on toy worlds (B17) |
| G7 | COMPATIBLE_WITH_AMENDMENT (static) / BLOCKED_EXTERNAL (decision) | label-only validator; no bundle binding; no decision executor (B3) |
| G8 | **BLOCKED_EXTERNAL** pending the real lane's 299/599 reconciliation | support fraction undefined; matrix-seeded thinning (B16) |
| G11/G12 | COMPATIBLE_WITH_AMENDMENT | non-donor held-out transfer, novelty axis, partition and support mappings (B18) |
| R1 | **BLOCKED_EXTERNAL** | truth undefined (B2); no executor; #350 static with human source names (B15) |
| TargetPortfolio | **BLOCKED_EXTERNAL** | the design correctly refuses to normalize the #332 C4 bug and encodes no buggy fixture semantics. #351 is unbound and receipts are unvalidated (B31). |

The design is directionally compatible. It does not import human thresholds or outcomes, and it correctly blocks C4. However, R5's "cross-lane PASS" overstates readiness: four of six gate paths are blocked externally.

## E. Leakage / circularity verdict

| vector | status | guard / gap |
|---|---|---|
| source shortcuts | PARTIALLY_GUARDED | 01 §6.2, 02 §6. The source-shortcut twin is not verdict-bearing (B12); no sampling confounding (B19) |
| candidate-shaped generation | **GAMEABLE** | B4 (also a #325 no-repeat conflict) |
| normalization leakage | **GAMEABLE** for evidence masks; guarded for q | B3, B10 |
| support coercion | PARTIALLY_GUARDED | 01 §7/§19, 04 §1/§5; gaps B3 (mask state), B11, B29 |
| outcome-driven world tuning | **GAMEABLE** | B1 |
| false abstention | PARTIALLY_GUARDED | 02 §2.2; holes B6, B13 |
| measurement-depth / evidence confounding | PARTIALLY_GUARDED | 02 §4.1–4.3; holes B3, B8, B16 (Critic C rated GUARDED; the coordinator disagrees) |

## F. Final verdict

`APPROVE_WITH_REQUIRED_AMENDMENTS`

**What is approved:** the design's architecture and direction:
- the causal order biology → expected state → observer;
- candidate-neutral intent;
- the support algebra as a base;
- V79/V80 separation;
- the evidence/depth and novelty/OOD separation principles;
- physical producer/fit/controller separation;
- the same-code-path requirement;
- non-compensation;
- explicit external blockers.

None of the findings requires rejecting this architecture.

**What is not yet lawful:** `WRITE_IMPLEMENTATION_PLAN_ONLY` is **not** the next lawful action. A plan written now would either inherit B1–B20 or decide them itself, which would make the plan the design authority.

**Next lawful action:** `WRITE_V3_1_CONSOLIDATED_CORRECTIVE_AMENDMENT_ONLY` (design text, no code), consisting of:
1. one consolidated controlling text with a total precedence order and supersession map (B14);
2. closure of B1–B13 and B19–B20 in that text;
3. explicit BLOCKED_EXTERNAL classes for G6, G8, R1 and full TargetPortfolio (B15–B18, B31), with explicit binding or classification of #350/#351/#352;
4. MODERATE items B21–B32 recorded as plan-binding requirements.

Then run a **focused re-audit of V3.1 against this findings list**, not a full re-archaeology. Only after that re-audit passes is the next lawful action `WRITE_IMPLEMENTATION_PLAN_ONLY`.

Approval grants no implementation, realization, fitting, scoring, target selection, representation selection, TD60, Stage4, synthetic training or real training.

Authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
