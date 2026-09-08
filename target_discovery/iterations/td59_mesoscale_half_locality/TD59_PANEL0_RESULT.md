# TD59 Panel-0 result — nearest-half mesoscale recurrence survives first independent panel

Status: `TD59_PANEL0_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PANEL1_MAY_OPEN__NO_TRAINING_AUTHORITY`
Date: 2026-09-08

Prospective freeze:
`864651fbe56b973f6645866624513e827c2c54da`

Pre-outcome binding:
`f3eb86d26a306fe99ae2848dca89e9f2e9e25207`

Frozen local executor SHA-256:
`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`

## Result

TD59 Panel 0 evaluates the prospectively fixed nearest-half Z-selected mesoscale neighborhood using completely fresh Z/X/Y molecular views.

All three source families pass all four deterministic donor-half cases:

- HVS: 4/4 PASS
- NPH52: 4/4 PASS
- SEA_AD: 4/4 PASS
- Panel 0 total: **12/12 PASS**

### HVS

- split0/half0: 0.6071428571 > null p95 0.5517241379
- split0/half1: 0.5484625668 > null p95 0.5441558442
- split1/half0: 0.6071428571 > null p95 0.5178571429
- split1/half1: 0.5484625668 > null p95 0.5473059361

The weakest observed-minus-null-p95 margin in Panel 0 is therefore only:

`+0.0011566307718604563`

This narrow HVS margin is preserved explicitly and must not be described as a strong-margin result.

### NPH52

- split0/half0: 0.6253880266 > 0.5625000000
- split0/half1: 0.5883325730 > 0.5534188734
- split1/half0: 0.6163506941 > 0.5666648915
- split1/half1: 0.6086871134 > 0.5614011338

### SEA_AD

- split0/half0: 0.6145833333 > 0.5811518325
- split0/half1: 0.6291012839 > 0.5747126437
- split1/half0: 0.6323296355 > 0.5752351097
- split1/half1: 0.6153846154 > 0.5775248933

## Exact local result hashes

- HVS: `72fd84c60f96ec7ad07b0039efc46bb049778b2e54190056afd84cdc83d54df6`
- NPH52: `dbf5570164aa686d1ded67ac408c354e543680cf0ffa76ddac2279a49eb4d6ba`
- SEA_AD: `5601bc1f788b1cb5b9eb060d984bea22a86a20af7d014bf98e0b7b34a978727c`

## Mechanics audit

The direct/naive and optimized concordance-distance implementations agree with max absolute difference **0.0**.

Z-selector cutoff ties:
- HVS: 0
- NPH52: 0
- SEA_AD: 44 among 22,561 selectable anchors

The global-row tie break was prospectively frozen before outcome, so the SEA_AD ties do not create an outcome-dependent selection rule.

## Interpretation boundary

Panel 0 supports the nearest-half mesoscale hypothesis strongly enough to lawfully open the completely independent Panel 1, but it does **not** establish the final TD59 terminal because HVS contains a very narrow surviving case.

Panel 1 remained unopened until this Panel-0 result was preserved.

No production locality, loss weight, learned-teacher geometry, full-reader authority, or neural training is authorized.
