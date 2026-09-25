# PR #118 repair — qualification contract

Published **before** any expensive run, per execution step 2 of the audit.
Branch `repair/pr118-audit-fixes-20260925`, from live PR #118 head
`d719ce1619f8` (verified ancestor).

Live heads recorded at branch creation:

```
main    c49b13bd75c2      PR#92   bc09c0f432db
PR#77   9a2a30e4c4c9      PR#94   9cc155a659f9
PR#118  d719ce1619f8      PR#117  9c524f49dd14   (moved from 0a72e6eb)
PR#86   0ffb62cac6ea      PR#91   56600f66492b
```

`START_HERE.md` read from **current main**, not PR #118 ancestry: V25 is the
canonical takeover snapshot.

---

## 1. Frozen expected asset set

`evidence/FROZEN_EXPECTED_16_ASSET_MANIFEST_V1.json` pins **exactly 16 assets**,
4,450,940,052 bytes, each with study, filename, byte length, full SHA-256,
format from magic bytes, and an expected **role**.

Rule: the inventory must require exactly this set. **Any** missing asset, extra
asset, size mismatch, digest mismatch, unknown role, or asset lacking an
independent pinned digest is a **nonzero exit**. Enumerating whatever
directories happen to exist is no longer acceptable, and a sidecar sitting next
to its own asset is not independent authentication — the frozen manifest is the
independent authority and it lives in the repository, not beside the data.

Three assets carry `_RESERVED` roles and must not be opened by any producer:
`GSE254205_ad_raw.h5ad.gz`, `..._ATAC.tar.gz`, `..._iMG_LD_sort_RNA_seq.tar.gz`.

## 2. Negative-test matrix

Each fixture must produce a **true nonzero exit**, demonstrated, not assumed.

| # | adversary | target producer |
|---|---|---|
| N1 | same-byte-length corruption | inventory, manifest |
| N2 | altered `.sha256` sidecar | inventory |
| N3 | altered authenticated parent digest | donor-aware, bulk V2 |
| N4 | missing expected asset | inventory |
| N5 | unknown extra asset | inventory |
| N6 | asset with no sidecar | inventory (**currently fail-open**) |
| N7 | duplicate feature IDs | donor-aware, BIN1 V2 |
| N8 | duplicated guide / target identity | BIN1 V2, comparability |
| N9 | guide ↔ count-column order swap | donor-aware, BIN1 V2 |
| N10 | donor label swap | donor-aware |
| N11 | treatment/control swap | bulk V2, donor-aware |
| N12 | missing donor-matched NT | donor-aware |
| N13 | empty / zero-depth library | donor-aware, bulk V2 |
| N14 | negative, NaN or Inf counts | all numeric producers |
| N15 | misjoined features (row order drift) | donor-aware, bulk V2 |
| N16 | many-to-one gene collision | comparability, crosswalk |
| N17 | false zero-fill of absent genes | bulk V2, donor-aware |
| N18 | missing expected contrast | bulk V2 (**currently silent**) |
| N19 | stale exposure-ledger row | comparability (**currently stale**) |
| N20 | silently skipped test | CI gate |

## 3. Independent reproduction algorithm (P0-3)

A **separately authored** implementation, not a refactor of the producer under
test, recomputes GSE301119 effects from the four authenticated guide×donor raw
pseudobulk RDS inputs:

1. verify input RDS SHA-256 against the raw-pseudobulk manifest;
2. per donor, sum raw integer counts over NT guides → control library;
3. per donor, sum raw integer counts over a target's guides → target library;
4. `log2(count / libsize * 1e6 + 1)` for each;
5. effect = target − control, **within each donor separately**;
6. cross-donor value = mean over qualifying donors.

**Tolerance, declared now:** `max |delta| <= 1e-9` on every compared cell, both
modalities. Both sides are IEEE double from identical integers, so anything
above that is a real disagreement, not float noise.

**Comparison scope:** all estimable target×gene cells for **both** modalities —
36,601 × targets for CRISPRi and 19,162 × targets for CRISPRa — plus target
order, feature order, donor support masks and source digests.

**Predeclared targets** (fixed before recomputation), chosen to span the failure
modes rather than to look good:

```
HEXA      CRISPRa guide-variance failure (1 guide/donor)
FCGR2C    structurally unmeasured own gene, both modalities
HAVCR1    CRISPRi cross-donor failure (10-cell floor)
SYK       CRISPRi cross-donor failure
CLDN7     CRISPRa cross-donor failure
TYROBP    CRISPRa cross-donor failure
CSF1R     shared Day-8 / macrophage target
TGFBR2    shared Day-8 / macrophage target
SPI1      shared GSE335887 / macrophage target
DNMT1     unrelated downstream control
ACTB      housekeeping gene, not a target (downstream read)
GAPDH     housekeeping gene, not a target (downstream read)
```

**Sign checks that do not rely on the biology.** CRISPRi-down / CRISPRa-up is
*not* an independent sign check — a contrast-direction error flips both together
and still looks coherent. Instead:

* **planted asymmetric fixture** with known per-gene signs and magnitudes;
* **deliberately swapped numerator/denominator**, which must produce exactly
  negated effects and must be detected by the comparator.

**Donor-specific retention.** The current producer stores only the cross-donor
mean matrix plus donor-wise **own-gene** engagement. The repaired producer must
persist donor-wise effect matrices, or output sufficient to reconstruct each
gene's two donor values, so this reproduction is possible at all.

Source-pseudobulk parity is already established and is **not** this check.

## 4. Experimental units, frozen

```
GSE301119  donor            n=2; cells and guides are not donors
GSE178317  pooled prep      n=1; 4 capture wells are technical
GSE335887  parental line    WTC11; 8 GSMs are assay libraries, not donors
GSE311359  sample           n=7; 3 BIN1 cis elements are distinct interventions
GSE293118  immortalized     HMC3; no donor axis
GSE254205  bulk sample      9; 3 per condition
GSE240609  design cell      1 per 2x2 cell -> no biological SE
GSE241858  clone            2 per genotype; within-clone replicates collapse first
```

## 5. Exposure ledger freeze

Reconciled against **physical execution**, correcting the stale rows the audit
found:

```
GSE240609   was UNOPENED_RESERVED -> INSPECTED_DEVELOPMENT   (WP-D executed its contrasts)
GSE301119   INSPECTED_DEVELOPMENT                            (donor-aware executed)
GSE254205   INSPECTED_DEVELOPMENT_BULK_ONLY                  (3 auxiliary assays remain RESERVED)
GSE311359   INSPECTED_DEVELOPMENT
GSE178317   INSPECTED_DEVELOPMENT
GSE241858   INSPECTED_DEVELOPMENT
GSE293118   INSPECTED_DEVELOPMENT
GSE335887   UNOPENED_RESERVED                                (metadata only; no HDF5 opened)
GSE175721   UNOPENED_RESERVED                                (STOP; nothing computable)
```

No previously inspected dataset may be called prospective confirmation.

## 6. Status vocabulary, per evidence

`PHYSICAL_DATA_VERIFIED` · `CODE_TEST_PASS` · `INDEPENDENT_REPRODUCED` ·
`NOT_ESTIMABLE` · `UNOPENED_RESERVED` — each asserted only for the specific
evidence supporting it. Hand-authored literature/curator statements move to a
separately named assertion registry with source reference and digest, and are
never presented as machine-checked columns.

## 7. Outputs

New versioned directories only. Original raw inputs, V1 artifacts and receipts
are preserved byte-for-byte. Producers refuse an occupied output directory and
publish atomically after all validation passes.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
