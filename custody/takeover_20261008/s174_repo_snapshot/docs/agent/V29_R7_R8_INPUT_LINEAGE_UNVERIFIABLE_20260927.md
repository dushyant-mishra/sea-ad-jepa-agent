# R7/R8 inputs are unverifiable, and the discovery materializer shares the defect

Date 2026-09-27.

## The discovery materializer has the same defect as the Level-4 one

`scripts/v4/foundation_materialize_discovery_expression.py`
(sha256 `ede646be8030ef1644d27496a98eb4661e1c95e4043bc44a6d520e81b7d0228f`)
uses the identical pattern that scrambled the Level-4 gene identities:

```
45: source_key = 'HVS_COMMON' if study=='HVS' else 'SEA_AD_COMMON'
46: mapping    = prov[prov.source_dataset_id.eq(source_key)][[
                     'source_feature_index','molecular_address_index']]
51: source_to_address = dict(zip(mapping.source_feature_index,
                                 mapping.molecular_address_index))
63: target = source_to_address.get(int(c))      # c is a SOURCE COLUMN INDEX
```

Same family collapse to `HVS_COMMON` / `SEA_AD_COMMON`, same table keyed by
`source_feature_index`, same use of that key as though it were the source
object's own column index. `HVS_COMMON`'s `source_feature_index` is the
Ensembl-ascending rank — 100.0% agreement with Ensembl-ID order — while an h5ad
`var` axis is genomic. So **any HVS or SEA-AD artifact produced by this path
carries scrambled gene identities**, by the same mechanism and for the same
reason.

NPH52 is unaffected here as it is at Level 4: its provenance is keyed to the
individual object, verified at 32,176 of 32,176 rows.

## What R7 and R8 actually consumed

Both read the same two files:

```
META   = Path('/tmp/jepa_tour_meta.csv')
MATRIX = Path('/tmp/jepa_tour_logexpr.npz')
assert META.exists() and MATRIX.exists(), \
    'original-data-derived development cache unavailable'
```

and `JEPA_R8_PACKAGE_MANIFEST_20260926.json` records:

```
"original_cell_level_data_included": false,
"original_bundle_copied":            false
```

So the development cache those results rest on is **not in the package, has no
recorded digest of its own, and no longer exists**. The packages hash their own
scripts and outputs meticulously and hash nothing about their input.

## The verdict is "unverifiable", not "wrong"

The cache cannot be checked, so R7/R8 cannot be shown to be either defective or
sound. Two observations pull in opposite directions and neither settles it:

- R8 reported 40.7% zero for the APOE panel in 361 microglia. The corrected
  FULL104 gives 24–43% zero and the **scrambled** view gave 74–84%. That
  resembles corrected data.
- The reliability review records that those microglia come from **2 operators**.
  If those are the HVS myeloid matrix and NPH52 MG, R8's microglia would be a
  mixture of one scrambled source and one sound one — which would be worse than
  either, and would not look obviously broken in aggregate.

Absent the cache, this stays undecided.

## Consequences

**`results/v29/R8_DEPTH_VS_PROGRAM_DISPERSION_V3.json` is marked
UNVERIFIABLE_INPUT and superseded.** That analysis reasoned entirely from R8's
recorded summary statistics — the zero fraction, the both-positive count, the
median sampling sd — to infer per-nucleus dispersion. Every one of those
quantities is a function of which genes the columns actually held. It is not
withdrawn as *wrong*; it is withdrawn as *uncheckable*, which for a
provenance-disciplined project is the same operational status.

Nothing is lost by this. The corrected FULL104 ladder answers the same question
on 187,909 nuclei with decoders verified cell-by-cell against authenticated
sources, rather than on 361 nuclei from a vanished cache.

**The earlier R7/R8 reliability verdict of INSUFFICIENTLY_MEASURED likewise
rests on unverifiable inputs** and should not be cited as evidence against the
candidate programs — which is the conclusion already reached on other grounds,
now with a documented cause.

## The general lesson for this project

A package that hashes its own scripts and outputs but not its inputs cannot be
audited later, however careful it looks. The R8 package is meticulous about
everything except the one thing that determined its numbers. Any future
development artifact must record a digest of every input it reads, including
scratch caches, or its results expire the moment the scratch directory is
cleared.

---

## UPGRADED: not unverifiable — DEFECTIVE. 2026-09-27

The verdict above was too soft, and two independent lines of evidence closed it.

### The exact shard R8 used, read from GitHub

The discovery corpus is in the repository history. Shard
`exports/foundation_corpus_discovery_v1/discovery_expression_shards/op19.counts.npz`
is operator 19 — the HVS myeloid matrix — 128 cells × 41,238 addresses of raw
int32 counts. Read straight out of git and probed with the verified HVS decoder:

| gene | naive address | naive detection | decoded column | decoded detection |
|---|---|---|---|---|
| APOE | 6186 | **0.0%** | 22730 | **55.5%** |
| CSF1R | 14980 | **0.0%** | 6276 | **76.6%** |
| CD74 | 392 | 10.9% | 6283 | **85.2%** |
| P2RY12 | 12469 | 19.5% | 4436 | **76.6%** |
| C1QA | 13365 | 0.0% | 286 | 28.9% |
| CX3CR1 | 12239 | 1.6% | 3688 | 32.0% |
| TREM2 | 2044 | **81.2%** | 6949 | 13.3% |

The discovery corpus carries the same scramble as Level-4, by the same
mechanism.

### The 361 microglia, reconstructed from frozen metadata

An independent audit (PR #185, commit `a597784d`) reconstructed R7/R8's subset
without touching expression outcomes:

- **128 HVS microglia, all operator 19**
- **233 SEA-AD microglia, all operator 25**
- **0 NPH52**
- 50 donors: 23 HVS + 27 SEA-AD

So the 128 HVS cells probed above **are** R8's HVS microglia, and the remaining
233 come from operator 25, also an affected family. My earlier guess that the
mixture was "HVS plus NPH52" was wrong: there is **no NPH52 in R7/R8 at all**,
and therefore no sound arm. Every named-gene measurement in R7 and R8 was
computed on scrambled coordinates.

### Revised status

`R8_DEPTH_VS_PROGRAM_DISPERSION_V3` and the underlying R7/R8 results move from
UNVERIFIABLE_INPUT to **DEFECTIVE_INPUT_DEMONSTRATED**. Their APOE, P2RY12 and
HLA-DRA program measurements, partner counts, split-half correlations and
held-out named-RNA readouts all require decoded replay before any of them mean
anything about those genes.

What survives: the donor-split mechanics, the anti-leak engineering, and the
contract design. Those are gene-label independent. The biological conclusions
are not.

**The INSUFFICIENTLY_MEASURED verdict cannot be used as evidence against the
candidate programs.** It was not a measurement of those programs.

### V44 is affected too

The tiny-teacher tournament binds the same 50k NPZ, output sha256
`4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`, whose own
audit records that exact digest and whose producer applies the same faulty
assumption. Its PCA and ridge arithmetic remain reproducible; it cannot be used
as biological evidence for choosing a teacher architecture until replayed on
corrected expression.
