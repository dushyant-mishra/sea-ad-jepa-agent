# V79 Rare-Biology Real-Data Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prospectively governed rare-biological-state synthetic qualification layer matched to already-authenticated real RNA, ATAC, spatial and perturbation assets, without modifying Q00-Q11 or rerunning completed ETL.

**Architecture:** Keep V79 V2_CORE as Layer A measurement/statistical qualification. Add an independent Layer B donor-structured rare biological truth family and Layer C teacher/student qualification. Calibrate ranges only from already-authorized TRAIN/cached development evidence, freeze truth/gates before realization, and preserve physical truth/fit custody separation.

**Tech Stack:** Python, NumPy/Pandas/SciPy, existing V79 contract/generator/scorer patterns, pytest, JSON/CSV provenance manifests.

**Spec:** `docs/agent/V79_RARE_BIOLOGY_REALDATA_INTEGRATION_SPEC_20261012.md`

## Global Constraints

- Q00-Q11 immutable; never regenerate or amend them.
- No new ETL/reacquisition when an authenticated cache/manifest already exists.
- No pathology, DEV, SEALED or TEST outcome use for calibration/selection.
- Morabito is protected from target/representation selection and is separate-nucleus evidence only.
- Historical rare1/rare5 are threshold roles on the same innovation direction; do not treat them as distinct biological programs.
- Stage75-79/cisTarget resources are regulatory topology/support, not causal truth.
- Rare biology cannot be rescued by aggregate/common-state metrics.
- JEPA training remains OFF.

## Review Focus

1. Source/operator confounding must not define rare truth; add explicit conditional/source-shuffle tests in Task 2.
2. Donor-restricted true biology must survive nuisance correction; add donor-subset truth tests in Task 3.
3. Separate-nucleus and same-nucleus worlds must remain different evidence classes; test schema separation in Task 4.
4. Technical pseudo-rare controls must be frequency matched but biologically null; test truth labels and observation-only perturbation in Task 4.
5. Student uncertainty must rise when teacher-private evidence is required; test underidentified world behavior in Task 6.

---

### Task 1: Freeze assimilation and capability authorities

**Files:**
- Existing: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`
- Existing: `results/v79/rare_biology_integration/V79_REALDATA_RARE_PROGRAM_ASSIMILATION_20261012.md`
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_INPUT_AUTHORITY_V1.json`
- Test: `tests/v79/test_v79_rare_biology_input_authority.py`

**Interfaces:**
- Consumes: recorded SHA-256 identities and role classifications.
- Produces: one machine-readable authority file with asset IDs, permitted roles, prohibited roles and required hashes.

- [ ] Write tests that reject missing required hashes, role escalation, Morabito same-cell claims and Q00-Q11 mutation authority.
- [ ] Run targeted tests and confirm RED.
- [ ] Implement the authority JSON plus validator using existing V79 fail-closed patterns.
- [ ] Run targeted tests and confirm GREEN.
- [ ] Commit only Task 1 files.

### Task 2: Build TRAIN-only empirical calibration summaries

**Files:**
- Create: `scripts/v79/derive_v79_rare_biology_calibration_v1.py`
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_CALIBRATION_CONTRACT_V1.json`
- Test: `tests/v79/test_v79_rare_biology_calibration_v1.py`

**Interfaces:**
- Consumes: existing frozen 41K TRAIN/discovery caches, donor/operator metadata, program weights and support masks.
- Produces: donor/lineage/source/operator-conditioned distributions for prevalence, module score, support and measurement-depth sensitivity; no pathology fields.

- [ ] Write tests for TRAIN-only provenance, donor/source conditioning, deterministic summaries and explicit rejection of global innovation-tail thresholding.
- [ ] Run tests and confirm RED.
- [ ] Implement deterministic read-only summary derivation.
- [ ] Run tests and confirm GREEN on fixtures.
- [ ] Execute only against already-authenticated local caches when physically available; preserve receipt/hashes.
- [ ] Commit Task 2 code/tests/contract; keep large derived caches local with hash manifests if needed.

### Task 3: Freeze donor-structured rare truth semantics

**Files:**
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_TRUTH_CONTRACT_V1.json`
- Create: `scripts/v79/v79_rare_biology_truth.py`
- Test: `tests/v79/test_v79_rare_biology_truth.py`

**Interfaces:**
- Consumes: Task 2 calibration summaries and frozen regulatory topology template.
- Produces: deterministic donor propensities, cell-level R labels/activity, rare1-like/rare5-like regimes and donor-restricted regimes.

- [ ] Write tests for reproducibility, donor heterogeneity, exact-zero donors, recurrence across multiple donors and independence from source/operator/depth.
- [ ] Run tests RED.
- [ ] Implement minimal truth generator.
- [ ] Run tests GREEN.
- [ ] Commit.

### Task 4: Implement modality-matched rare worlds and technical twins

**Files:**
- Create: `scripts/v79/generate_v79_rare_biology_worlds.py`
- Create: `scripts/v79/v79_rare_biology_world_writer.py`
- Test: `tests/v79/test_v79_rare_biology_worlds.py`

**Interfaces:**
- Consumes: Task 3 truth and existing V79 observation-model primitives.
- Produces: RB00-RB07 blinded fit/student views plus controller truth.

- [ ] Write tests for each world family, including separate-nucleus RB04 versus same-nucleus RB05 and frequency-matched biologically-null RB02.
- [ ] Test that Q00-Q11 paths/bytes are never touched.
- [ ] Run RED.
- [ ] Implement worlds using shared biological truth followed by modality-specific observation operators.
- [ ] Run GREEN.
- [ ] Commit without realizing production worlds.

### Task 5: Implement regulatory topology template and controls

**Files:**
- Create: `scripts/v79/build_v79_rare_regulatory_template.py`
- Create: `results/v79/rare_biology_integration/V79_RARE_REGULATORY_TEMPLATE_CONTRACT_V1.json`
- Test: `tests/v79/test_v79_rare_regulatory_template.py`

**Interfaces:**
- Consumes: exact Stage75-79/cisTarget tables named in Task 1.
- Produces: frozen topology template plus degree/size-matched random controls; no causal labels.

- [ ] Write tests for source hashes, regulator/target membership, matched control size/degree and absence of causal activation/repression claims.
- [ ] Run RED.
- [ ] Implement deterministic extraction/control construction.
- [ ] Run GREEN.
- [ ] Commit.

### Task 6: Implement rare-biology scorer and teacher/student falsifiers

**Files:**
- Create: `scripts/v79/score_v79_rare_biology.py`
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_SCORING_CONTRACT_V1.json`
- Test: `tests/v79/test_v79_rare_biology_scorer.py`

**Interfaces:**
- Consumes: controller truth and blinded teacher/student outputs.
- Produces: separate hard gates for teacher preservation, pseudo-rare rejection, student recovery, uncertainty/abstention, donor recurrence, multimodal concordance, context controls and perturbation support.

- [ ] Write tests for first-hard-fail, rare1/rare5 separate reporting, no aggregate rescue, underidentified-student uncertainty and technical-twin rejection.
- [ ] Run RED.
- [ ] Implement scorer with write-once controller receipt following V79 patterns.
- [ ] Run GREEN.
- [ ] Commit.

### Task 7: Prospective realization package and controller review

**Files:**
- Create: `docs/agent/V79_RARE_BIOLOGY_REALIZATION_REVIEW_V1.md`
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_REALIZATION_AUTHORITY_CANDIDATE_V1.json`
- Test: relevant full rare-biology test suite plus existing V79 trust-domain tests.

**Interfaces:**
- Consumes: Tasks 1-6 exact heads/hashes.
- Produces: review-only realization candidate; does not realize worlds without explicit controller authorization.

- [ ] Run all targeted rare-biology tests and existing V79 firewall tests.
- [ ] Hash code/contracts/inputs and freeze seed derivation/world count.
- [ ] Verify no Q00-Q11 byte/path mutation.
- [ ] Publish review candidate and STOP for controller authority.

### Task 8: Map synthetic gates to lawful real-data validation

**Files:**
- Create: `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_SYNTHETIC_TO_REAL_VALIDATION_MAP_V1.csv`
- Create: `docs/agent/V79_RARE_BIOLOGY_REAL_VALIDATION_PROTOCOL_V1.md`

**Interfaces:**
- Consumes: Task 1 capability matrix and final scoring contract.
- Produces: one-to-one mapping of each synthetic claim to FOUNDATION/Morabito/GSE214979/GSE272082/spatial/perturbation evidence class and its limitations.

- [ ] Map every hard synthetic gate to at least one lawful real-data falsifier or mark `NO_REAL_FALSIFIER_YET`.
- [ ] Preserve exposure/pairing/donor limitations verbatim.
- [ ] Verify no external asset is silently promoted to target-selection authority.
- [ ] Commit.
