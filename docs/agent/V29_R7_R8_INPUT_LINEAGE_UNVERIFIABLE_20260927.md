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
