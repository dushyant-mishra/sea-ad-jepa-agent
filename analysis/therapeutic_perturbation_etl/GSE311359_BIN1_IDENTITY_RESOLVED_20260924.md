# GSE311359 — BIN1 feature identity **RESOLVED** from the deposited data

Date: 2026-09-24
Supersedes the blocking premise of `GSE311359_BIN1_COLLAPSE_CONFIRMED_20260924.md`
and of PR #92, both of which held that an authentic feature-ID to
protospacer/target mapping had to come from the depositors or the authors.

```
defect (phantom pseudobulk rows)        CONFIRMED, unchanged
authentic feature identity              PRESENT IN THE DEPOSITED FILES
required external source                NONE
other 82 targets unaffected             CONFIRMED by exhaustive check
physical V2 rebuild                     STILL REQUIRED
```

## What was actually wrong

The three colliding features were read by their **display name** (column 2 of
`features.tsv`). Column 1 carries the feature ID, and it was never ambiguous:

```
ENSG00000136717   BIN1   Gene Expression         <- the BIN1 gene itself
BIN1_enh_1        BIN1   CRISPR Guide Capture    <- enhancer 1
BIN1_enh_2        BIN1   CRISPR Guide Capture    <- enhancer 2
BIN1_enh_2_AS     BIN1   CRISPR Guide Capture    <- enhancer 2, antisense
```

The V1 producer keyed pseudobulk on `ref_names[r]`, the display name, which is
`BIN1` for all three. The depositors had already distinguished them.

This is the same failure the project has recorded before in a different guise: a
name is not an identity. The identity of a capture feature is its row and its
feature ID in the authenticated census, never its display label.

## Exhaustive check — the collision is confined to BIN1

Over all 381 guide features in the deposited feature table:

```
total features                              36,982
  Gene Expression                           36,601
  CRISPR Guide Capture                         381
unique guide feature IDs                       381   -> ALL DISTINCT
unique guide display names                     379
display names shared by >1 guide feature         1   -> BIN1 only
guide IDs colliding with a Gene Expression ID    0
```

**Exactly one display name collides, and it is BIN1.** PR #92 allowed the other
82 targets "scoped validity only if independent tests confirm they were
unaffected". That test has now been run exhaustively over the whole feature
table: no other guide shares a name, so no other target could have been
collapsed by this defect.

### Feature-table parity across the seven samples

Required before any pooled aggregation. All seven feature tables are identical
in ID, name, type **and order**:

```
GSM9324129_S1 .. GSM9324135_S7    36,982 features each
distinct feature-table signatures: 1
```

## What the three BIN1 features actually are

They are **three distinct cis-regulatory element perturbations**, not one gene
perturbation measured three times, and not replicates of each other:

* `BIN1_enh_1` — a first enhancer
* `BIN1_enh_2` — a second, different enhancer
* `BIN1_enh_2_AS` — the antisense orientation at that second enhancer

Consequences for the rebuild:

1. **They must not be pooled.** Summing them would average three different
   interventions, which is a different error from the phantom-row defect but
   equally wrong.
2. **They are not a direct BIN1 knockdown.** BIN1 is the *nominated* gene
   asserted by the depositor's own feature ID, not a verified cis-target
   relationship established by this project. The distinction matters: the
   GSE293118 precedent forbids inventing a nearest-gene mapping, and this is not
   that, because the depositor named it — but it is still an assertion carried
   from the source, and it is recorded as such.
3. **Antisense orientation is a separate condition**, not a technical duplicate
   of `BIN1_enh_2`.

## Status change

```
was    STOP_AUTHOR_SOURCE_MISSING_FOR_BIN1
now    STOP_PENDING_PHYSICAL_V2_REBUILD
```

The blocker is no longer missing author data. It is that the V1 aggregation is
keyed on the wrong column and must be rebuilt keyed on **feature row index and
feature ID**, with the three BIN1 elements kept as three separate cis-element
units and reported as nominated-gene perturbations rather than direct BIN1
knockdown.

Until that rebuild runs and is independently verified:

* the V1 BIN1 target effect remains **invalid** and must not be used;
* no BIN1 value may be produced by selecting or averaging one of the three rows;
* the other 82 targets are confirmed unaffected by this specific defect, though
  their V1 values still inherit the name-keyed aggregation and should be
  reproduced under ID keying before reuse.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · THERAPEUTIC_RANKING=OFF
```
