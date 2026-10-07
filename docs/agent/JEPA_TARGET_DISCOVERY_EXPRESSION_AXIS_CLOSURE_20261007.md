# JEPA target-discovery expression-axis closure — 2026-10-07

## Scope
This checkpoint closes the historical question of whether the exact 50K discovery expression matrix used by TD34/TD41 could have had source gene identifiers misbound to 41,238 molecular-address columns.

## Primary recovered sources
1. `scripts/v4/foundation_materialize_discovery_expression.py` (user-recovered original producer)
2. `scripts/v4/foundation_materialize_nph_discovery_sample.R` (user-recovered NPH helper)
3. `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` (user-recovered execution audit)
4. Frozen Stage81A2R 41,238 molecular-address registry/provenance authorities already present in Git history.

## HVS / SEA-AD column binding
The Python producer reads the frozen source-provenance table and constructs an explicit `source_feature_index -> molecular_address_index` mapping per source family. Collision-authority rows are excluded. It refuses duplicate source-feature or duplicate molecular-address targets. Raw source counts are then written into sparse matrix column `molecular_address_index`, not left in native source feature order. Cell and donor identity are also checked against the frozen selection before reading each source row.

## NPH52 column binding
The recovered R helper independently follows the same rule. For each NPH source object it reads `source_feature_index` and `molecular_address_index` from the frozen provenance table, applies the same collision exclusions, refuses non-injective mappings, selects raw `counts`, and writes a 41,238-column sparse shard with output column `molecular_address_index + 1` (R indexing).

Therefore all three foundation source families are materialized into the common 41,238-address coordinate system by explicit mapping, not by assuming native feature position equals molecular-address position.

## Exact historical NPZ binding
The recovered `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` records:
- schema `foundation-discovery-expression-v1`
- cells: 50,000
- addresses: 41,238
- normalization: `log1p(raw_count*10000/full_source_library) exactly once`
- output SHA-256: `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

That SHA is the exact historical inner 50K discovery NPZ already authenticated from the reassembled expression archive.

## Revised classification
`DISCOVERY_EXPRESSION_ADDRESS_AXIS_PRIMARY_SOURCE_VERIFIED`

This closes the previously open HVS/SEA-AD/NPH52 address-axis provenance gap for the exact 50K discovery matrix used in the target-discovery lineage.

## Important non-upgrade
This does NOT by itself promote TD34/TD41/TD43 or any later target candidate to production target authority. Separate questions remain about target definition, q-safety, S149/source-composition effects, donor estimands, normalization-derived shortcuts, and the scientific interpretation of historical outcomes.

## Consequence for TD34/TD41 archaeology
The prior caution should now be narrowed:
- historical row-reset/global-row bugs remain real and must stay excluded;
- the exact 50K discovery expression matrix itself is now primary-source bound to the 41,238 molecular-address coordinate system across HVS, SEA-AD, and NPH52;
- therefore the specific hypothesis that TD34/TD41 used jumbled gene IDs because the discovery NPZ column order was unbound is no longer supported by the recovered materialization source and audit.
