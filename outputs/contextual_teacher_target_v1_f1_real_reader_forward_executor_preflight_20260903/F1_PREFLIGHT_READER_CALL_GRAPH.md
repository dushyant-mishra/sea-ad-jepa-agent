# F1 preflight reader call graph

`reader plan (67 lawful rows)` -> `64 authenticated Level-4 CSR blocks` -> `float32 log1p10k normalization exactly once` -> `normalized_values + observation_states` -> `prospective evidence mask (q withheld)` -> `IPBEncoder student view` -> `query-local H_q - mean(H_context)` -> `LayerNorm`.

Identity/provenance remains in a sidecar and never enters the model-facing mapping. Physical block sorting is restored to frozen logical cell order before forward execution.
