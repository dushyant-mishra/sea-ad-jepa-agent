# Day-8 spent-screen descriptive characterization — measured development result

Source: committed same-experiment published CRISPRbrain iTF Day-8 RNA table, compressed SHA-256 `201e8fb28a63dfb91ae5f37a77f9641a90c3cdf4c618943a55699c512227079f`, uncompressed `41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39`. Executable producer `scripts/describe_spent_day8_transcriptome_v1.py`; adversarial synthetic tests and physical execution PASS in [GitHub Actions run 36085934862](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36085934862). Artifact `Day8-EXPOSED-DESCRIPTIVE-ONLY`, ID `10843946278`: 234,591-byte JSON SHA-256 `e6f64356117f239441fad8b1406d3159877c8154743ff6ba5fcd0e5d2055a4ab`, available for per-target and all 741 pair details. No other CRISPRbrain outcome profiles were inspected.

## Observed published response geometry

- **39 targets**, 343,707 target–gene DE rows, 10,549 unique gene labels, no missing FDR entries; 741 pairs, every pair with estimable signed cosine on mutually measured *off-target* genes.
- Median per-target number of off-target features with *depositor-reported* FDR <0.05: **15**, range 0–775; **10/39** targets have zero such genes. Median per-target |published log2FC| >=0.5 burden: **8** genes, range 0–368; 13/39 have none. The paper's DE FDR is model-conditional, **not** independent-differentiation biological uncertainty.
- The signed cosine across all 741 target pairs (shared measured genes, excluding both directly targeted genes) has median **0.1184**. Only 55/741 are >0.3; four are <-0.3. This is heterogeneous response geometry, not a demonstration that all unseen target responses are unlearnable.
- Descriptively high-similarity target pairs include `CDK12–MED1` cosine 0.711, 234 shared depositor-FDR hits; `MAP2K6–MAPK14` 0.662, 13; `CSF2RA–CSF2RB` 0.657, 20; `NDUFA8–NDUFS5` 0.566, 14; `CSF1R–CSF2RB` 0.535, 24. These pairs share reported response geometry *within the same pooled biological preparation*; they are not independent validations of pathway causality.

Historical benchmark: no-change baseline all-gene MAE 0.07188 versus cross-target mean 0.06864, while training-only reactive subset MAE 0.21898 versus 0.21613 (mean worse on 20 of 39 targets). A weak global mean is entirely compatible with identifiable subsets of functionally related perturbation responses. Don't declare benchmark unlearnable or set the JEPA evaluation metric by repeatedly reusing this screen.

## Scope / remaining ETL

This producer is **descriptive** (fixed conventional effect thresholds, no predictive scoring rule selected). Day-8 transcriptome was already fully inspected and is DEVELOPMENT only. Four 10x wells are capture/technical partitions of one pool; no biological SE, independent replication, prospective confirmation or training authority. The published FDR calls depend on depositors' pipeline assumptions. Do not use response-derived gene sets from this artifact for a held-out test or treat it as cross-experiment discovery.

The processed profiles in GSE335887 for Day-12 iTF and Day-28 iMG share 31 intervention target identities absent from Day-8 and originate from the same WTC11 parental line. Their unpublished response comparisons remain reserved; first finish source/lineage/guide/feature authority for a cross-differentiation-protocol evaluation, **not** new-donor generalization.
