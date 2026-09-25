# Microglial cross-screen metadata overlap — physical source-verified result

Date: 2026-09-24 EDT. GitHub Actions run [36085328435](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36085328435), workflow head `2a481bb80bfd52c7a0d48d143d3635aff8f56ef2`, artifact ID `10843298823` (`CRISPRbrain-five-screen-METADATA-ONLY-overlap`). Artifact JSON SHA-256 `fd4a1623e1bf3abaece5857d887a032133b0133b7d358454ce78d7d0bd1d8f88`, 13,590 bytes. **CI passed all adversarial tests and physically checked all five committed gzips** against full compressed and uncompressed SHA-256.

Only the metadata columns `Gene` and `name` were used. No numerical response, FDR, expression or outcome data from the four reserved screens was extracted or examined. Day-8 outcomes were previously spent for development.

| RNA/Protein comparison | Common perturbed target labels | Common same-modality measured feature labels |
|---|---:|---:|
| Day-8 iTF RNA / Day-12 iTF RNA | **0** | 10,037 |
| Day-8 iTF RNA / Day-28 iPSC-microglia RNA | **0** | 9,653 |
| Day-12 iTF RNA / Day-28 iPSC-microglia RNA | **31/31** | **13,489** |
| Day-12 iTF CITE protein / Day-28 iPSC-microglia CITE protein | **31/31** | **167** |

All four Day-12/Day-28 RNA and CITE screens carry the same 31 perturbation *labels*. Both CITE panels contain 170 processed protein feature labels, with 167 shared. RNA/protein feature intersection is deliberately not treated as comparable expression space. Literal labels are not frozen molecular identifier mapping.

**Interpretation:** Day-8 cannot support same-target transport testing against either 31-target screen. The 31-target iTF/iPSC CROP RNA pair is the relevant metadata *candidate*, not an authorized biological replication or independent confirmation. Its culture protocol, differentiation stage (Day 12 vs Day 28), 10x chemistry (v3 vs v2), and potentially donor/line provenance differ or remain unverified.

**Important catalog contradictions:** The iTF CROP screen combined two CROP experiments, one paired with its iTF CITE dataset; they cannot be called independent RNA/protein replication. The iPSC CITE catalogue calls its differentiation six-TF, but its iPSC CROP counterpart says cytokine-directed; verify actual sample/paper manifests before treating these arms as paired. Catalogue text says 180 proteins measured, while the acquired processed CITE table has 170 feature labels. These are source-document inconsistencies, not findings from reserved effect profiles.

**Next gate:** authenticated parental cell line/clone, guide-library/sample identities, independent biological preparations, feature crosswalk and rechecked exposure ledger. Only then freeze a study-pair estimand and evaluation design before opening reserved transcriptome response values.

Authority: `METADATA_ONLY__NOT_BIOLOGICAL_COMPARABILITY__NO_PREDICTION_OR_TRAINING`. All FULL104, N1, D_shared and therapeutic ranking stops unchanged.


## Self-gene row addendum — distinct from whole-screen gene presence

Re-ran the physical five-screen source-hash check with a metadata-only **per-target own-gene row** census. [Successful GitHub Actions run 36087371680](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36087371680), artifact ID `10844756520`, JSON SHA-256 `8bd4cc3ad9002d8439c0378e7c60df28ef4c73ba1499839d7e8caa24b2bde834` (21,776 bytes). This read only `Gene` and `name` labels and did not inspect effect or FDR columns.

- Already-inspected Day8 RNA: 36/39 target names occur in the whole screen gene universe but only **35/39** have an own-gene row. **AURKB** appears somewhere in the screen but has **no AURKB×AURKB row**; EPOR, PLK1 and RPS6KA6 are absent from the overall gene universe. A global feature census is insufficient to assert direct-target engagement measurability.
- Day12 iTF RNA: **30/31** own rows, POU5F1 absent.
- Day28 cytokine iMG RNA: **29/31** own rows, POU5F1 and SMAD3 absent.

These are observed structural-presence facts, not inferred low expression or negative engagement. Any subsequent engagement QC must fail closed on a missing own row rather than zero-fill it; no new downstream response values were exposed by this metadata audit.
