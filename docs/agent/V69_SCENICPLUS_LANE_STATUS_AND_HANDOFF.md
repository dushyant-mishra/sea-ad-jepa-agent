# V69 external SCENIC+/eRegulon regulatory architecture — lane status and handoff

Branch: `claude/v69-scenicplus-external-network-20261001`
Worktree: `D:/jepa_wt_v69_scenicplus_20261001`
Outputs: `D:/jepa_v5_outputs_20260925/v69_scenicplus`
Base: `origin/chatgpt/v64-privileged-information-recoverability-20260930` @ `84e10964`

**Read this first:** no regulatory network exists yet. The substrate, the cohort, the
prospective freeze, the Route-A region universe and the structural crosswalk layer are
done and authenticated. The eRegulons are not built. Nothing in this lane has opened a
protected outcome.

---

## 1. What is DONE and authenticated

### Substrate acquisition (mandate item 1)

Every object below was verified against the **server-declared Content-Length** before
a digest was computed. The acquisition tool refuses to emit a PASS receipt on a
byte-count mismatch, so a silently truncated download cannot become an authenticated
artifact.

| object | bytes | sha256 |
|---|---|---|
| `GSE214979_cell_metadata.csv.gz` | 8,820,297 | `8ce4e0c78747cfa6fb2a556468893df0d378e3f53085e52955f3ecdcc944394b` |
| `GSE214979_filtered_feature_bc_matrix.h5` | 1,369,492,123 | `8f4315b59c252c8e907dbc7cd9a46b3acfe4878b7fff7e65309027d281581bb2` |
| `v10nr_clust_public.zip` (10,249 motifs) | 89,706,219 | `70dab42794f42471a3c22f5efe78ec2c8af96127656607cb0a929b4adffc2b97` |
| `motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl` | 98,718,421 | `81eb754118e27e854974301b1400fcf519489f8be5249239671fb288cb501c31` |
| `hg38.analysisSet.fa.gz` | 949,157,663 | `cb69cd39fa5309b156f5cba45bd70553776d4e2c5c7000d1eed6c7bca8b8f459` |
| `cbust` binary | — | `4c10c768a17dacc8cc01bc71b2f3e0bf540d460054c4edccaf71c9a6d9655c72` |

`GSE214979_atac_fragments.tsv.gz` — server-declared **63,641,120,882 bytes** — was in
flight at the time of writing. Its receipt is written only on exact byte completeness;
see section 3.

### Matrix authentication

187,215 features × 105,332 cells, 927,291,782 nonzeros, **36,601 Gene Expression +
150,614 Peaks**, genome build **GRCh38** single-valued across every feature. Peaks
carry `chr:start-end`; genes carry Ensembl IDs and their own loci.

### Cohort freeze (mandate item 2) — pathology-blind

The metadata was **audited, not assumed**: 105,332 nuclei × 32 columns, donor column
`id` (15 donors), published annotation `predicted.id`, which agrees **exactly** with
the published subcluster prefix in `subs`. The producer fails closed if that agreement
ever breaks.

| population | nuclei | donors |
|---|---|---|
| `ALL_MICROGLIA` | 3,179 | 15 |
| `DEV_NO_MORABITO_OVERLAP` (default) | 2,534 | 12 |

Donor exclusion `{1224, 1230, 1238}`: all three are present, and that set is **verified
to equal exactly** the donors whose `Repository` is UCI — nothing more, nothing less.
That is consistent with the recorded `UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP` concern
but does **not** verify individual-level overlap with Morabito, which deposits
pseudonymous `Sample-NN` identifiers. No shared stable key layer was resolved. The
exclusion stays labelled `CONSERVATIVE_PROSPECTIVE`.

Pathology blindness is demonstrated, not asserted: a positive control flips every
value of `Status`, `Braak`, `Diagnosis` and `APOE_Status` across the whole frame and
confirms both population digests are bit-identical.

### Route A substrate and region universe (mandate item 3, Route A)

RNA and submitted-peak matrices for both populations, e.g. default population RNA nnz
3,771,894 and ATAC nnz 7,979,525; no cell has zero detected features in either
modality. Region universe: **150,561 regions, 126,142,895 bp**, median width 865 bp,
BED sha256 `dd0d2d00904345c1b6489de99f62d95581b82fed7946cefa3254ca815a73be32`.

53 peaks (0.035%) lie on unplaced scaffolds that the reference spells differently
(`GL000194.1` vs `chrUn_GL000194v1`). They are **dropped, counted and listed**, labelled
`STRUCTURALLY_UNSCOREABLE`, under a prospective bound of 1% above which the run stops —
because a large drop would mean a systematic naming mismatch, which looks identical at
first glance.

### Route A is not subject to the prior failure

The previous Stage75F attempt could not map peaks to genes from a processed matrix.
Route A was tested against that failure **before** any network was built:

- peaks with parseable GRCh38 coordinates: 150,614 / 150,614 (100%)
- genes with parseable GRCh38 coordinates: 36,588 / 36,601 (99.96%)
- same-nucleus pairing: 2,534 RNA and 2,534 ATAC cells, **same barcodes**
- genes with ≥1 peak within 150 kb of TSS: 35,829 / 36,588 (97.9%), median 20 peaks

Stage75F's blocker was the absence of same-cell pairing, which left proximity as the
only possible link. GSE214979 is a Multiome, so region-to-gene can be learned from
within-cell covariance. This says nothing about whether the network will be good.

### Prospective freeze (mandate items 3, 7, 8) + two amendments

Written while **zero** eRegulons, route statistics, control statistics and Stage-4
artifacts existed. Every constant carries either an external rationale or an explicit
`CONVENTION` label. Highlights:

- Both routes share the same nuclei by construction, so the comparison tests
  **region-definition sensitivity only** and may never be reported as general
  robustness.
- A **route-sensitivity positive control (C7) is mandatory**: without proving that
  changing the peak definition *can* break the agreement test, the test cannot fail
  and therefore means nothing.
- Program-level is a pre-declared **success mode**, not a failure, at 12 donors.
- Fewer than 8 QC-passing donors ⇒ no program may be called donor-stable at all.
- **Amendment 1**: build a custom cisTarget database for *both* routes, so the region
  universe is the single varying factor. The original design would have confounded
  region universe with database type.
- **Amendment 2**: full consensus region universes only, never per-TF handfuls;
  `MIN_REGIONS_FOR_A_RESOLVED_PROGRAM = 100` with sub-threshold programs reported
  `UNRESOLVED` rather than absent; schema-parity check between the scores and rankings
  databases; explicit unmapped-region lists; extended-only motif support as a separate
  evidence class.

### Control C1 denominator (mandate item 8)

Built from the pinned annotation table alone — no expression, no accessibility, no
network, no outcome — so it cannot be contaminated by a result.

**253,096 annotation rows, 27,072 distinct motifs, 1,605 TFs. Direct-annotation supply
per TF: min 0, median 6, mean 11.9, max 144. 110 TFs have no directly annotated motif
at all.** A 144-fold spread in how many chances a TF gets to be called enriched.

Direct / orthology / similarity / extended are counted separately, because the prior
Stage75F run shows they come apart badly: 7 of its 10 TFs reached motif support with
**zero** direct motifs.

### Structural crosswalk layer (mandate items 10, 11 — substrate only)

**Stage-4 genome build resolved empirically, not assumed.** The NIH-CARD design
contract speaks of an "hg19-primary distance convention" and the pair keys embed an
hg19 coordinate, which invites the wrong conclusion. All 57 enumerated-control pair
keys match the **hg38** columns of the design artifact exactly and **0 of 57** match
hg19. GSE214979 and Stage-4 are therefore in the same build and **no liftOver is
needed**.

| | measured |
|---|---|
| GSE214979 RNA features resolving to a FULL104 address | 35,445 / 36,601 |
| structurally unmeasured in FULL104 | 1,156 |
| Stage-4 genes present in GSE214979 | 4,370 / 4,372 |
| FULL104 source support | SEA-AD 35,445 · NPH52 30,436 · HVS 17,947 |
| peaks overlapping a Stage-4 interval | 17,686 / 150,614 |
| Stage-4 intervals reached by some peak | 22,991 / 32,153 (71.5%) |

Stage-4 vocabulary reconciled across all 8 Phase-B shards: 4,372 genes, 32,153
intervals, 37,419 pair keys. The outcome-bearing `t3_value`/`t4_value` arrays were seen
and **not read**; the receipt records that per shard.

### Execution environment

Validated container `sha256:520053641b60c03e9bbb219f9f8c630a01cce03569ef45d1d50c807b0d441200`.
Every tool executed and its own version captured: bedtools v2.31.1, macs2 2.2.9.1,
samtools 1.24, meme 5.5.9, cbust, MALLET, liftOver, bigWigAverageOverBed,
`create_cistarget_motif_databases.py`. scenicplus 1.0a2, pycisTopic 2.0a0, pycistarget
1.1, numpy 1.26.4. `pip check`: no broken requirements. 235 pip packages recorded.

**Provenance caveat, carried deliberately:** the image id and the recipe digests are
two separate facts. That the image was *built from* either recipe is **UNVERIFIED** —
Docker retains no such binding and layer history is not proof. No receipt in this lane
says "built from recipe X".

---

## 2. What is NOT done

- **No eRegulons exist.** Neither Route A nor Route B has a network.
- **The custom cisTarget databases are not built.** A benchmark was run to measure the
  cost rather than estimate it; see the benchmark receipt.
- **Route B is not executed.** The fragments were being acquired; QC, consensus peak
  calling and the Route-B region universe have not run.
- **No controls have been computed** beyond C1's denominator. C2–C7 are defined and
  frozen, not run.
- **No donor-stability analysis**, no Route-A/Route-B comparison.
- **No program-level crosswalks** (mandate items 10 and 11 require per-program
  reporting; only the reusable address-resolution substrate exists).
- **No source adapters instantiated** (mandate item 12).
- **No frozen network receipt** (mandate item 9) — there is no network to freeze.

---

## 3. Exact next steps, in order

1. Confirm the fragments receipt is `PASS__BYTE_COMPLETE_AND_DIGESTED` against
   63,641,120,882 bytes. If it is not, resume rather than proceed — Route B must never
   run on a truncated file.
2. Run `scripts/v69/routeb_fragment_qc_and_donor_split_v1.py` on the full file.
3. Acquire and SHA-pin a GRCh38 TSS annotation (currently `UNACQUIRED`) to complete the
   TSS-enrichment QC arm.
4. Build the Route-A custom cisTarget database over the 150,561-region universe
   (`scripts/v69/build_custom_cistarget_db_v1.sh`, full mode).
5. Donor-aware pseudobulk MACS peak calling → Route-B consensus region universe →
   second custom cisTarget database.
6. Topic modelling and SCENIC+ for each route separately; freeze Route A as
   `GSE214979_SCENICPLUS_SUBMITTED_PEAKS_V1` **before** Route B results are used.
7. Controls C2–C7, donor stability, Route-A/B comparison, then the frozen network
   receipt.

Only then do the program-level crosswalks and source adapters become computable.

---

## 4. Governance

| boundary | state |
|---|---|
| Stage-4 biological correspondence | **UNOPENED** |
| Morabito biological replication | **UNOPENED / PROTECTED** |
| recoverability TEST | **SEALED** |
| JEPA training | **OFF** |
| pathology labels in construction | **NEVER USED** |
| Stage-4 hidden-confound result | **UNMODIFIED** |

The Stage-4 synthetic qualification result (planted biology Δ ≈ +0.785, hidden
within-donor metacell-varying technical confound Δ ≈ +0.654, control-vs-control ≈ 0)
has not been touched. Part of the value of an external network is that its failure
mode is *different*.

Another lane's worktree `D:/jepa_wt_v64_sampler_20260930` and outputs
`v64_phase_b` / `v64_stage4_synthetic` were never written to; `v64_phase_b` was read
read-only for vocabulary and was not mounted into any container.

---

## 5. Self-audit lane

See `docs/agent/V69_SCENICPLUS_SELF_AUDIT_LANE.md` — items S1–S11, including two that
this lane cannot close (the route comparison shares nuclei by construction; the
substrate is 12 donors), one belonging to another branch, and one (S9) caught by an
independent trace rather than by me.
