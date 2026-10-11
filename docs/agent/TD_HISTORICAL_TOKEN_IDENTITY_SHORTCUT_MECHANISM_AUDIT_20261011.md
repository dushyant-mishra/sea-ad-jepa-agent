# Historical token-identity/support shortcut mechanism audit — 2026-10-11

Status: `MECHANISTIC_SHORTCUT_AUDIT_COMPLETE__IDENTITY_SUPPORT_CHANNEL_EXPLICIT__NO_TARGET_AUTHORITY`

Source authority: authenticated `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`, SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.

Reviewed frozen code:
- `code/gene_tokenizer.py`
- `code/ipb_jepa.py`
- `code/masking.py`

No legacy checkpoint pickle was executed. Attempted `torch.load(..., weights_only=True)` refused the old pickle because it contains unsupported legacy NumPy globals; this audit did not bypass that safety boundary.

## 1. Gene identity is an explicit high-capacity token channel

The historical tokenizer computes, for every observed gene token:

`identity_component = identity_projection(gene_identity(gene_ids))`

and separately:

`value_component = value_encoder(expression_scalar)`

then returns:

`LayerNorm(identity_component + value_component)`.

Thus every token carries a trainable gene/address-identity vector in addition to the expression value. Address identity is scientifically necessary for a gene-aware model, but token geometry is not automatically biological-state geometry merely because expression is also present.

## 2. Measurement support can encode operator/source without any operator embedding

The encoder's valid gene set is defined directly by the physical measurement mask (and student hidden-target mask). Tokens for unmeasured/hidden genes are absent from the valid set.

Therefore the *set of gene identities presented to the encoder* is itself a measurement-support fingerprint. If different operators/source families measure different address sets, operator/source information can enter the representation even when no `operator_id`, `source_id`, `dataset_id`, or matrix embedding is supplied.

This is consistent with the historical shortcut atlas: strong source/operator/support decodability existed despite the reviewed encoder having no free source/operator embedding.

## 3. Historical target-block queries also contain direct identity structure

The block predictor forms each target-block query by averaging the identity embeddings of the block's member genes and applying an identity projection, plus a learned block-mask vector.

The hidden-gene readout likewise embeds hidden gene identities directly.

This makes query/address identity a legitimate conditioning channel for prediction, but it also means block/query prediction can be strong for identity reasons unless value-specific and same-cell biological correspondence are challenged explicitly.

## 4. Why the u0 shortcut result is especially informative

The calibration bundle reports that even at u0, address + operator explain approximately:

- 99.938% of rich-H variance;
- 99.950% of partial-H variance.

Because this occurs before meaningful JEPA learning, it cannot be used as evidence that training discovered a biological coordinate system. It is compatible with strong architectural identity/support structure already present at initialization.

The later u205 result remaining near the same regime therefore cannot be promoted merely because the geometry is stable.

## 5. Binding design consequences

### A. Do not promote token-level H geometry as biological state by default

Gene-token H is expected to retain gene identity. A biological target must demonstrate information beyond identity/support/operator structure.

### B. Excluding explicit operator IDs is insufficient

Future models must treat physical support/measurement state as an observation-process channel and explicitly test whether the biological state adds signal beyond it.

### C. C2 measured query targets require an address-only baseline

A q-conditioned model may legitimately know q identity, but it must beat a baseline that uses q/address identity alone (for example the training-donor q-specific mean/bias) in addition to q-count-only and generic-cell controls.

### D. C3/C4 learned-state candidates require identity+support baseline defeat

In addition to conditional technology-imprint testing, the learned shared state must beat an explicit identity/support-only shortcut baseline under held-donor evaluation. A source/operator classifier alone is not enough because identity/support can carry the shortcut implicitly.

### E. Matched wrong-cell nulls must preserve support identity

Breaking support or address composition makes an unrealistically easy null. The frozen wrong-cell null therefore continues to preserve donor, operator, support, depth and detection strata while breaking cell-specific biological correspondence.

### F. Query identity and biological state must stay conceptually separate

Query address is a conditioning variable. It is not evidence that the cell occupies a particular biological state. The structured target keeps q identity/support outside the claim that `Z_shared` itself is biological.

## 6. Scaffold consequence

The synthetic tournament contract should explicitly add:

- `Q5_Q_ADDRESS_ONLY_DEFEAT` to C2;
- `L6_IDENTITY_SUPPORT_BASELINE_DEFEAT` to C3;
- both appropriate identity/support controls to C4.

These are falsification gates, not training objectives.

## Authority boundary

This historical mechanistic audit does not authorize corrected values, G6/G7, corrected replay, real target-tournament execution, target selection, representation selection, TD60, Stage4, pathology or training.

Terminal:
`IDENTITY_SUPPORT_SHORTCUT_MECHANISM_BOUND__EXPLICIT_BASELINE_DEFEAT_REQUIRED__NO_TARGET_AUTHORITY`
