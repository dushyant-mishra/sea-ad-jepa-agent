# P3 executed — 2,673 neuron and 2,078 oligodendrocyte valid negatives

Mechanical execution only, against the rules frozen on canonical at
`8ff7ed1f`. No scientific design happened here: no threshold change, no rescue
rule, no alternative liftover semantics, no widened overlap, no external gene
repair, no post-result tuning.

```
input authentication: all 6 exact-byte checks PASS
VALID_P3_NEGATIVES   neuron 2,673   oligodendrocyte 2,078
```

## Two independent cross-checks passed before any result was read

**1. My orientation implementation reproduces the one that produced P1S, exactly.**
P1S resolved gene uniqueness on `Nearest Ensembl` alone; this executor splits that
class into unique-symbol and symbol-unresolved, so their sum must reproduce the
committed P1S count. On the microglia interactome:

| class | here | committed P1S |
|---|---|---|
| `PROMOTER_PROMOTER` | 7,614 | 7,614 |
| `NO_ACTIVE_PROMOTER_MATCH` | 32,978 | 32,978 |
| unique-Ensembl promoter-distal | 61,624 | 61,624 |

**2. My source-side counts reproduce canonical's independent implementation,
exactly.** Canonical computed these without C3, because its runtime cannot run
liftOver. Recomputing them here from the same frozen rules tests two separate
implementations against each other on six numbers:

| | unique gene resolved | GSE73721 matched | expression eligible |
|---|---|---|---|
| neuron — here | 65,772 | 53,803 | 31,690 |
| neuron — canonical | 65,772 | 53,803 | 31,690 |
| oligodendrocyte — here | 40,793 | 32,755 | 22,377 |
| oligodendrocyte — canonical | 40,793 | 32,755 | 22,377 |

All six match to the unit. These are **not** funnel stages — they are a
reconciliation, reported separately from the frozen funnel, which puts C3 first.

## The attrition funnel, against preserved source denominators

Classes are mutually exclusive and are required to sum back to the original source
interaction count. Both do, exactly.

**Neuron — denominator 93,290**

| stage | n | % of source |
|---|---|---|
| `FAIL_C3_EXACT_IDENTITY` | 1,550 | 1.661% |
| `FAIL_ORIENTATION_NOT_EXACTLY_ONE_PROMOTER` | 25,024 | 26.824% |
| `FAIL_GENE_ENSEMBL_UNRESOLVED` | 1,988 | 2.131% |
| `FAIL_JOIN_SYMBOL_UNRESOLVED` | 50 | 0.054% |
| `FAIL_NOT_IN_EXPRESSION_REFERENCE` | 11,689 | 12.530% |
| `FAIL_EXPRESSION_INELIGIBLE_TRIVIAL` | 21,761 | 23.326% |
| `FAIL_MICROGLIA_DISTAL_NOT_ACCESSIBLE_TRIVIAL` | 25,424 | 27.253% |
| `RELATIONSHIP_PRESENT_IN_MICROGLIA` | 3,131 | 3.356% |
| **`VALID_P3_NEGATIVE`** | **2,673** | **2.865%** |
| sum | 93,290 | 100.000% |

**Oligodendrocyte — denominator 61,895**

| stage | n | % of source |
|---|---|---|
| `FAIL_C3_EXACT_IDENTITY` | 1,091 | 1.763% |
| `FAIL_ORIENTATION_NOT_EXACTLY_ONE_PROMOTER` | 19,066 | 30.804% |
| `FAIL_GENE_ENSEMBL_UNRESOLVED` | 1,663 | 2.687% |
| `FAIL_JOIN_SYMBOL_UNRESOLVED` | 24 | 0.039% |
| `FAIL_NOT_IN_EXPRESSION_REFERENCE` | 7,790 | 12.586% |
| `FAIL_EXPRESSION_INELIGIBLE_TRIVIAL` | 10,196 | 16.473% |
| `FAIL_MICROGLIA_DISTAL_NOT_ACCESSIBLE_TRIVIAL` | 17,041 | 27.532% |
| `RELATIONSHIP_PRESENT_IN_MICROGLIA` | 2,946 | 4.760% |
| **`VALID_P3_NEGATIVE`** | **2,078** | **3.357%** |
| sum | 61,895 | 100.000% |

### C3 behaves the same on the negative cell types as on microglia

| track | source | C3 exact-identity retained | retention |
|---|---|---|---|
| microglia (committed) | 104,802 | 102,701 | 97.995% |
| neuron | 93,290 | 91,740 | 98.339% |
| oligodendrocyte | 61,895 | 60,804 | 98.237% |

Forward-admissible was 91,741 (neuron) and 60,804 (oligodendrocyte); the round
trip removed exactly 1 and 0 further pairs. No pair in either track violated
exact identity on re-verification.

## What the numbers mean

Only about 3% of source interactions survive to become valid negatives, and the
bulk of the loss is not coordinate failure — C3 costs under 2%. The two dominant
losses are **orientation** (27–31%: the contact is promoter–promoter, or neither
anchor hits an active promoter of that cell type) and the **two triviality
filters** (expression and microglial accessibility, together 41–51%).

That triviality attrition is the contract working as designed. A neuron contact
whose gene is not expressed in microglia, or whose distal region is not accessible
in microglia, tells you nothing by being absent from the microglia map — the
absence is explained without any regulatory claim. Excluding those is what makes
the remaining set informative.

`RELATIONSHIP_PRESENT_IN_MICROGLIA` — 3,131 and 2,946 — is the interesting
complement: contacts that exist in a non-microglial cell type *and* also exist in
microglia, on the same gene with overlapping distal intervals. These are shared
regulatory relationships, not negatives, and they are correctly removed.

## Self-audit lane (continuing from S25)

**S26 — I applied the wrong gene-uniqueness rule to the microglia reference map,
and caught it before commit.** The frozen contract defines the reference as
*"unique-Ensembl-resolved"*; the separate both-unique rule (`Nearest Ensembl`
**and** `Gene Name`) lives under `orientation_and_gene_identity`, which governs the
neuron/oligodendrocyte **candidate** side, where the symbol is required for the
GSE73721 join. My first run required both on the reference too. That shrinks the
reference, which means fewer relationships are found present, which **inflates**
valid negatives — a bias in the direction that flatters the result. Measured
effect: reference 60,252 → 60,340 edges (7,603 → 7,606 genes); neuron 2,675 →
2,673; oligodendrocyte 2,080 → 2,078. Small, but it was wrong in the permissive
direction and is now fixed with the reasoning recorded in the code.

**S27 — the contract's definition of "trivial" is ambiguous for one class, and I
declined to resolve it.** It defines trivial negatives as *"expression-fail or
microglial-accessibility-fail"* but does not say whether a symbol absent from
GSE73721 is an expression failure or a join failure. Both readings are reported
in the result JSON (`trivial_negatives.fraction_narrow` and `fraction_wide`).
**Neither changes `VALID_P3_NEGATIVES`**, because that class is excluded under
either reading — so this is a labelling question, not a result question, and
picking one after seeing the numbers would have been an unforced exposure-informed
choice of exactly the kind the density panel already cost us.

**Examined and clean:** every funnel reconciles to its source denominator; the six
input digests are checked before anything is read and the script exits on
mismatch; the microglia reference is rebuilt from authenticated sources rather
than imported from an intermediate; no AD loci, JEPA targets, Morabito, NIH-CARD
or project RNA were opened.

## Reconstructibility

`results/v64/p3_intermediates/` carries the per-edge valid-negative tables for both
cell types — source row index, `Nearest Ensembl`, `Gene Name`, and the distal hg38
interval — so both counts can be reconstructed rather than taken on assertion, plus
the full run log.

## Governance

`E2_NOTT_CANDIDATE` is **not instantiated** — stopping here as instructed, pending
audit of the complete funnel and lineage. `TRAINING=OFF`. `TD60=BLOCKED`.
