# Agent 2 — FULL104 full gene-universe coverage against external RNA/ATAC evidence

Status: **measured, complete over all 41,238 canonical addresses.**
Every number below is transcribed from the artifacts listed in the manifest,
not from intent. Nothing here is a projection from headline totals.

Governance: TRAINING=OFF · AUDIT_B_N1=UNOPENED ·
PROTECTED_FULL104_OUTCOMES=UNOPENED · D_SHARED_G5=UNOPENED ·
RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF

---

## 1. The headline comparison that was prohibited is not merely imprecise — it is a category error

The assignment forbade inferring coverage by comparing 41,238 against 61,770.
Resolving the Morabito matrix shows why that prohibition mattered:

| Quantity | Value | What it counts |
|---|---|---|
| Canonical FULL104 addresses | 41,238 | genes |
| GSE174367 snRNA **features** | 58,721 | genes |
| GSE174367 snRNA **barcodes** | 61,770 | **nuclei, not genes** |

`61,770` is the cell axis of the snRNA matrix (`matrix/shape = [58721, 61770]`).
Comparing it to a gene count compares genes against nuclei. The correct
feature-space figure is 58,721, and even that does not yield coverage without
per-address resolution, because the two spaces are not nested: the assay
contains features absent from the registry and the registry contains addresses
absent from the assay.

## 2. Inputs, authenticated

Both anchors were verified by digest before any measurement, and the builder
fails closed on mismatch.

| Input | Bytes | SHA-256 | Verdict |
|---|---:|---|---|
| `results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv` | 24,946,770 | `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd` | matches the required canonical digest |
| `outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv` | 2,372,002 | `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29` | genuine substrate root, **not** the 2,380,918-byte `e482d9da…` decoy |

The builder additionally refuses any manifest of 2,380,918 bytes or with the
`e482d9da` prefix, so the decoy cannot enter even by misconfiguration
(test 13).

**Self-audit note on digest field naming.** The assignment warned that two
fields bind the same digest under different names. Searching the repository for
the *key* `canonical_registry_sha256` returns nothing. Searching for the
*value* `7d61ed7b…` finds it bound as a plain `sha256` field inside the
artifacts map of `results/v4/stage81a2r_closure_hash_manifest.json` (line 38).
Searching by key spelling would have produced a false "not recorded" finding.

**Registry identity closure.** `molecular_address_index` was verified to cover
0…41,237 exactly once with no duplicate `molecular_address_id`, before any
coverage was computed. Identity is the registry's own key, never storage order.

**Frozen annotation release.** Ensembl 116 / GRCh38.p14
(`Homo_sapiens.GRCh38.116.gtf.gz`, 78,941 gene records), with HGNC complete set
2026-08-07 (45,031 records) and HGNC withdrawn 2026-08-04 (5,290 symbols).
The Morabito matrix is built on **GRCh38.p12.premrna2** — an older patch and a
pre-mRNA reference — so version disagreement is expected and is recorded
per address rather than absorbed.

**Coordination with lane-d.** Lane-d owns GSE174367 physical authentication and
the Stage75C peak-to-gene table; those files were not re-authenticated here.
Stage75C's frozen window parameters (promoter ±2,000 bp, distal ±100,000 bp)
are reused unchanged, and its nearest-gene attribution is carried only as a
cross-check column. Because Stage75C assigns each peak to exactly one nearest
gene, absence from it is **not** evidence of no nearby peak; the promoter and
distal states in this crosswalk therefore come from direct interval overlap
against Ensembl 116 TSS geometry, which has no such structural blind spot.

## 3. Per-address coverage — all 41,238 addresses, each individually resolved

One row per canonical address in
`agent2_full104_feature_crosswalk_v1.csv`. Every state column partitions all
41,238 addresses; the builder fails closed if any column fails to sum.

### 3.1 Morabito snRNA, genome-wide

| State | Addresses | Share |
|---|---:|---:|
| MEASURED_DETECTED | 31,455 | 76.28% |
| MEASURED_BUT_UNDETECTED | 7,626 | 18.49% |
| UNMEASURED | 2,122 | 5.15% |
| AMBIGUOUSLY_MAPPED | 35 | 0.08% |

**39,081 addresses (94.77%) are present and structurally measured** in Morabito
RNA; 2,122 are absent from the assay entirely; 35 resolve to more than one
feature and are held as ambiguous rather than forced to a winner.

The distinction that carries the science: the 7,626 MEASURED_BUT_UNDETECTED
addresses were assayed and observed zero. The 2,122 UNMEASURED addresses were
never assayed. Their count columns are left **empty**, not zero. Collapsing
these two states would have reported coverage as 39,081 + 2,122 = 41,203
(99.9%) instead of 94.77%, and would have fed 2,122 fabricated zeros into every
downstream statistic.

### 3.2 Mapping routes

| Route | Addresses |
|---|---:|
| `ensembl_stable_id` | 38,838 |
| `current_symbol` | 265 |
| `deprecated_alias_symbol` | 13 |
| `none` (no counterpart in assay) | 2,122 |

Symbol routes run **only** after the stable-ID route fails, so a symbol can
never override an identifier match.

### 3.3 Microglia-specific DETECTABLE coverage

Detectability is measured in the 4,126 barcodes labelled `MG`, not inferred
from presence in annotation.

| State | Addresses | Share |
|---|---:|---:|
| MEASURED_DETECTED in microglia | 24,824 | 60.20% |
| MEASURED_BUT_UNDETECTED in microglia | 14,257 | 34.57% |
| UNMEASURED | 2,122 | 5.15% |
| AMBIGUOUSLY_MAPPED | 35 | 0.08% |

Microglia-detectable coverage (60.20%) is far below genome-wide
present-in-annotation coverage (94.77%). 14,257 addresses are assayed but never
observed in a single microglial nucleus. These are exactly the addresses a
"present in the annotation" count would have silently promoted to covered.

298 of the 61,770 snRNA barcodes carry no cell-type metadata row. They are held
as UNKNOWN cell type and are **not** counted as non-microglia.

### 3.4 Annotation-supported regulatory geometry (Ensembl 116 TSS)

| State | Addresses |
|---|---:|
| PROMOTER_SUPPORTED | 25,987 |
| DISTAL_CANDIDATE_ONLY | 13,798 |
| NO_ANNOTATED_REGION_IN_ASSAYED_PEAK_SET | 698 |
| UNKNOWN (no resolvable Ensembl 116 coordinate, or gene on a contig carrying no assayed peaks) | 755 |

### 3.5 Experimentally accessible ATAC (measured from the 219,070 × 143,401 peak matrix)

| State | All nuclei | Microglia only |
|---|---:|---:|
| ACCESSIBLE_PROMOTER | 25,966 | 25,855 |
| ACCESSIBLE_DISTAL_ONLY | 13,814 | 13,911 |
| REGION_PRESENT_BUT_NOT_ACCESSIBLE | 5 | 19 |
| NO_ASSAYED_REGION | 698 | 698 |
| UNKNOWN | 755 | 755 |

`REGION_PRESENT_BUT_NOT_ACCESSIBLE` is a peak that was called but observed in
zero nuclei of that population — assayed and not accessible, which is not the
same as absent. 1,363 of the 219,070 peaks are zero across all nuclei.

### 3.6 Regulatory-evidence state and matched-comparison eligibility

| regulatory_evidence_state | Addresses |
|---|---:|
| REGULATORY_EVIDENCE_PRESENT | 37,971 |
| MAPPED_WITHOUT_REGULATORY_EVIDENCE | 676 |
| UNMEASURED | 2,122 |
| UNKNOWN | 434 |
| AMBIGUOUSLY_MAPPED | 35 |

| matched_rna_atac_state | Addresses |
|---|---:|
| ELIGIBLE_MATCHED_RNA_ATAC | 37,966 |
| NOT_ELIGIBLE_NO_ACCESSIBLE_REGION | 681 |
| UNMEASURED | 2,122 |
| UNKNOWN | 434 |
| AMBIGUOUSLY_MAPPED | 35 |

**Eligibility is structural, not same-cell.** GSE174367 snRNA and snATAC were
assayed on different nuclei from the same cohort, so these 37,966 addresses are
eligible for a matched comparison at pseudobulk or donor level. No same-nucleus
RNA–ATAC pairing is claimed or available.

## 4. Collisions — reported, never silently deduplicated

261 collision rows in `agent2_collision_report_v1.csv`.

| Collision type | Count |
|---|---:|
| `gene_symbol_multi_feature` | 216 |
| `ensembl_stable_id_multi_feature_par_y` | 45 |

The 58,721 snRNA features carry only 57,133 distinct symbols, so 216 symbols
each bind more than one feature. Symbol routes are used only after the
stable-ID route fails, and any symbol resolving to more than one feature is
recorded AMBIGUOUSLY_MAPPED with every candidate listed.

**The PAR_Y defect, found by inspecting output rather than intent.** 45 snRNA
features carry the CellRanger `_PAR_Y` suffix (pseudoautosomal Y copies:
`ENSG00000182378.13_PAR_Y` = PLCXD1, SHOX, GTPBP6, …). A PAR_Y feature shares
its Ensembl stable ID with the X copy, so those canonical addresses genuinely
resolve to **two** assay features. The first implementation treated the
suffixed string as an opaque key, silently dropped the Y copy, and reported a
one-to-many resolution as unique. Both copies are now indexed under the one
stable ID and the address surfaces as AMBIGUOUSLY_MAPPED with reason
`par_y_x_copy_pair`. This is why `addresses_ambiguously_mapped` is 35 and not
the 3 reported before the fix. Found before any downstream use.

35 addresses (not 45) are affected because not every PAR gene has a canonical
address in the registry. All 35 are listed in
`agent2_ambiguous_address_report_v1.csv`.

## 5. Transcription-factor coverage

All **10 of 10** Stage75F regulators (IRF8, STAT1 primary; BACH1, CEBPA, ELF1,
MITF, NRF1, RELA, SPI1, STAT3 secondary) resolve to a canonical address and are
**MEASURED_DETECTED genome-wide, MEASURED_DETECTED in microglia, and
ACCESSIBLE_PROMOTER in ATAC**. TF coverage is complete with no UNKNOWN.

Stage75F representation across the registry:

| stage75f_role | Addresses |
|---|---:|
| NOT_IN_STAGE75F | 41,200 |
| TARGET | 28 |
| REGULATOR | 9 |
| REGULATOR_AND_TARGET | 1 |

38 addresses carry Stage75F evidence, from 96 TF–target rows (24 primary + 72
secondary) over 10 tested regulators, 7 of which have supported targets.

**Stage75F is a HYPOTHESIS set** — motif-enrichment and sample-coactivity
evidence — not a validated regulatory network. The source tables carry
`validated_regulation=False`, `validated_grn_claim=False` and
`causal_validation_pass=False` on every row. No causal or therapeutic claim
follows from these columns.

## 6. Query-panel coverage

Panel used: `results/tables/discovery_targeted_manifold_audit_gene_list_v1.csv`
(45 genes). This is the currently proposed targeted-manifold audit panel; it is
named explicitly because the crosswalk is designed so coverage can be
recomputed for any other panel without rebuilding anything.

| | Count |
|---|---:|
| Panel genes declared | 45 |
| Resolving to a canonical address | 44 |
| **Absent from the canonical registry** | **1 (PLCG2)** |
| Resolving to more than one address | 0 |

Of the 44 with an address:

| State | Count |
|---|---:|
| RNA MEASURED_DETECTED | 44 / 44 |
| Microglia MEASURED_DETECTED | 42 / 44 |
| Microglia MEASURED_BUT_UNDETECTED | 2 / 44 |
| ATAC ACCESSIBLE_PROMOTER | 42 / 44 |
| ATAC ACCESSIBLE_DISTAL_ONLY | 2 / 44 |
| ELIGIBLE_MATCHED_RNA_ATAC | 44 / 44 |

**PLCG2 is worth flagging.** It is one of the best-established microglial
Alzheimer's risk genes, and it is absent from the FULL104 canonical address
registry — so no amount of external RNA/ATAC evidence can cover it under the
current address space. This is a property of the registry, not of the Morabito
data. It is reported as ABSENT_FROM_CANONICAL_REGISTRY rather than being
dropped or counted as covered.

To recompute for a different panel:

```
python scripts/agent2/agent2_coverage_matrix_and_panel_recompute_v1.py \
  --crosswalk <path>/agent2_full104_feature_crosswalk_v1.csv \
  --out-dir <out> --panel <new_panel.csv> --panel-field gene
```

## 7. Adversarial tests

`tests/agent2/test_agent2_full104_coverage_crosswalk_v1.py` —
**18 scenarios, 37 checks, 37 passed.**

Positive control (test 01) builds cleanly on valid input and asserts the
detectors do **not** fire when no defect is present.

| Planted defect | Test | Detected as |
|---|---|---|
| Unmapped identifier | 03 | UNMEASURED, empty count |
| Version-suffixed Ensembl ID | 04 | joins on stable ID, version retained |
| Version disagreement | 05 | flagged False (and True when versions agree) |
| Symbol collision | 06 | reported with every colliding feature |
| Deprecated symbol | 07 | resolved via HGNC alias route |
| Missing-vs-zero confusion | 08 | distinct states; absent feature has no count |
| Microglia missing-vs-zero | 09 | distinct states in the microglia column |
| Duplicated address | 10 | build rejected |
| Duplicated address index | 11 | build rejected |
| PAR_Y duplicate | 12 | AMBIGUOUSLY_MAPPED, reason recorded |
| Wrong registry digest | 02 | build rejected |
| Decoy block manifest | 13 | build rejected |
| Unassayed contig | 15 | UNKNOWN, never zero |
| Interval-overlap boundaries | 16, 17 | half-open boundary respected |

**Mutation check — proof the tests can fail.** Two safeguards were broken
deliberately and the corresponding checks flipped to FAIL, while an unmutated
control stayed green:

| Mutation | Result |
|---|---|
| Conflate UNMEASURED with MEASURED_BUT_UNDETECTED | check 08c FAILS |
| Restore the opaque-key PAR_Y handling | all 4 PAR_Y checks FAIL |
| No mutation (control) | 0 failures |

The second mutation reproduces the original PAR_Y defect exactly, confirming
the suite would have caught it.

## 8. Artifacts

Heavy files are referenced by path, size and digest rather than committed.
Output root: `D:/jepa_agent2_outputs_20260926`.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `full/agent2_full104_feature_crosswalk_v1.csv` | 16,383,559 | `4afff98d219450bef8d9ffff156c2190275254d1660657ab2d732ae6b48cf8ac` |
| `full/agent2_coverage_matrix_v1.csv` | 6,427 | `c05d7922bcdfe10000da15815cb56f24e5284ea65105bc0efd7ebfc8a605b31d` |
| `full/agent2_collision_report_v1.csv` | 60,517 | `55e704f23fd984d00e533b858193e9fe36daacabfb6682684de34fc324774961` |
| `full/agent2_ambiguous_address_report_v1.csv` | 4,607 | `ba51ef810ea27b9570a08f8ba980bb2893ca40de61e7f9283e225dd7662a5d12` |
| `full/agent2_query_panel_coverage_v1.csv` | 9,207 | `0df97c56cc17ff6f99a303b6811858bcfc18f21a26c7f833f0576d5af64f6e13` |
| `full/agent2_tf_coverage_v1.csv` | 832 | `35a63b65beb950d6f97518ca358c8d116a8627efba2b70569cec930698fa2749` |
| `full/agent2_coverage_provenance_v1.json` | 10,929 | `2606f73c399a213f3477aa8751e83a1e122246b2b6a60d57d975edbdde98f11e` |
| `full/agent2_coverage_matrix_summary_v1.json` | 1,380 | `33acd47367ad286f829bb21a34cdc290f6c91e5fd29a21feeab7792335bce60f` |
| `agent2_test_report_v1.json` | 4,840 | `c41bc2a22174d13688704e2e90d9a1d6cf38b695b93c4279194d12f7403cc079` |

## 9. Reproduction

Run from a clean worktree at this branch head. The builder authenticates both
anchors and fails closed on mismatch.

```
python scripts/agent2/agent2_full104_coverage_crosswalk_v1.py \
  --repo "D:/Jepa project" --out-dir D:/jepa_agent2_outputs_20260926/full

python scripts/agent2/agent2_coverage_matrix_and_panel_recompute_v1.py \
  --crosswalk D:/jepa_agent2_outputs_20260926/full/agent2_full104_feature_crosswalk_v1.csv \
  --out-dir D:/jepa_agent2_outputs_20260926/full \
  --panel "D:/Jepa project/results/tables/discovery_targeted_manifold_audit_gene_list_v1.csv"

AGENT2_TEST_REPORT=D:/jepa_agent2_outputs_20260926/agent2_test_report_v1.json \
  python tests/agent2/test_agent2_full104_coverage_crosswalk_v1.py
```

The full build reads both matrices end to end and completes in roughly two
minutes. No training, no regeneration of the 4.55M-cell FULL104 substrate, and
no access to protected SEA-AD pathology, sealed confirmation outcomes, terminal
masking results or D_shared. Morabito cell metadata was read for the
`Cell.Type` column only; its `Diagnosis`, `Tangle.Stage` and `Plaque.Stage`
columns were not used.

## 10. What remains UNKNOWN

Reported as UNKNOWN, never as zero:

- **755 addresses** have no resolvable Ensembl 116 coordinate, or sit on a
  contig carrying no assayed peaks. Their regulatory and ATAC states are
  UNKNOWN. A scaffold-placed gene is not the same as a gene with no regulatory
  region, and the two are not merged.
- **434 addresses** are RNA-resolved but UNKNOWN for matched-comparison
  eligibility because their ATAC geometry is unresolved.
- **35 addresses** are AMBIGUOUSLY_MAPPED; their detection state is UNKNOWN by
  construction, because assigning either copy's counts would be a choice the
  evidence does not support.
- **298 snRNA barcodes** have no cell-type label; their contribution to
  microglia-specific counts is UNKNOWN and excluded from the microglia
  denominator rather than assumed non-microglial.
