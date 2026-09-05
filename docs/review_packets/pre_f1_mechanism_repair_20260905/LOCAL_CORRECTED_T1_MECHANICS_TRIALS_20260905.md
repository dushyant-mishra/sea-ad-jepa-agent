# Local Corrected-T1 Mechanics Trials — 2026-09-05

Status: **mechanics-only exploratory diagnostics**. No real F1 biological outcome was opened. No DEV/SEALED/pathology expression was used.

## Runtime and fixture

- CPU-only PyTorch 2.10.0
- frozen T1 u0 initialization
- frozen 84-cell technical truth-table fixture
- two technical HVS cells, operators 0 and 1
- first 1,024 molecular addresses
- four common measured query addresses: 0, 338, 685, 1023
- 15 updates
- AdamW lr 1e-4, wd 0.01
- EMA 0.996

The exact historical `full104_model_components_v2.py` bytes remain unrecovered. Therefore the singleton/directional arms below are **diagnostic analogues**, not historical planned-code authority.

## Arms

- **R0:** existing IPB + historical BlockPredictor + block-mean JEPA control.
- **R1:** existing BlockPredictor used with singleton query blocks against Contextual Teacher Target V1.
- **R2:** R1 predictor path with a prospective analogue of the recovered directional cell-pair cosine semantics.
- **R12:** untuned equal-weight existence test, contextual MSE + directional analogue.

## Gradient coverage

On update 1, all 48 tensors in `{attention_norm,query,key,value} × 6 blocks` received nonzero gradients in every tested arm.

Summed first-step norms:

| arm | attention_norm | Q | K | V |
|---|---:|---:|---:|---:|
| R0 | 0.49856 | 0.01660 | 0.07213 | 4.12848 |
| R1 | 0.12324 | 0.00395 | 0.01730 | 1.00879 |
| R2 | 0.20200 | 0.02652 | 0.09946 | 1.98512 |

The directional analogue produced ~6.7× the initial Q gradient and ~5.7× the K gradient of contextual MSE alone.

After 15 updates all 12 Q, 12 K, 12 V and 12 attention-output tensors had nonzero Adam first/second moments.

Observed Q/K/V relative movement was ~1.25%–2.51%; exact pure AdamW decay for 15 steps is only ~1.5e-5 relative. This local path is genuinely learning rather than reproducing historical decay-only Q/K/V.

## Objective behavior

- R0 block mean: `2.3058 -> 0.5615`
- R1 contextual MSE: `2.0446 -> 1.3012`
- R2 directional analogue: `0.9592 -> 0.4018`
- R2 descriptive contextual MSE: `2.0446 -> 2.0678` (did not improve)
- R12 contextual MSE: `2.0446 -> 1.5237`
- R12 directional loss: `0.9592 -> 0.4956`

Thus the directional-only objective can improve directional geometry without improving contextual-target MSE, while the untuned combined existence test improved both.

The coefficient 1.0 in R12 is **not** a selected production weight.

## IPB backbone routing

Initial six-block IPB routing was near-uniform:
- `N_eff/N ~ 0.9944–0.9961`
- max/uniform ~1.18–1.24×
- query-map cosine ~0.99979–0.99988.

After 15 updates, R1/R2/R12 changed these only marginally. Even with healthy Q/K/V gradients, the ELU+1 IPB backbone remained extremely diffuse on this short fixture.

## Predictor router

The singletonized existing BlockPredictor uses ordinary softmax cross-attention.

Initial:
- mean `N_eff/N = 0.95541`
- max/uniform = 1.8596×
- query-map cosine = 0.98907

After R1 contextual MSE:
- `N_eff/N = 0.96610` (more diffuse)
- max/uniform = 1.6498×
- query-map cosine = 0.99060 (queries more similar)

After R2 directional analogue:
- `N_eff/N = 0.94927` (sharper)
- max/uniform = 1.9404×
- query-map cosine = 0.98694 (more query-specific)

After R12 combined:
- `N_eff/N = 0.95173`
- max/uniform = 1.9082×
- query-map cosine = 0.98754

## Interpretation

1. Historical T1's zero Q/K/V optimizer path is not inevitable under the mathematical objective: a repaired CPU path gives healthy gradients/moments.
2. Contextual Target V1 by itself does not automatically force selective routing.
3. The directional cell-pair objective produces qualitatively stronger Q/K pressure and query-specific predictor routing.
4. The selective-routing effect appears first in the predictor's softmax router, while the IPB backbone remains almost uniform.
5. This strengthens the case for corrected-T1 causal reruns before any backbone redesign.

## Required caveats

- CPU, not historical WSL CUDA.
- 1,024-address slice, not 41,238.
- two technical cells / four queries.
- repeated small-fixture updates.
- historical BlockPredictor singletonized, not exact unrecovered SingletonQueryPredictor.
- directional objective is a semantic analogue, not exact recovered historical bytes.
- no biological or production claim is authorized from this experiment.
