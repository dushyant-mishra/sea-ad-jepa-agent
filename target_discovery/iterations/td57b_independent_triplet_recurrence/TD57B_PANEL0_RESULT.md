# TD57B Panel 0 result — independent gene views survive donor-block triplet-order recurrence

Status: `TD57B_PANEL0_PASS__PANEL1_STILL_UNOPENED`
Date: 2026-09-08

Prospective freeze:
`dccf186868f5ff7070d7e6b32cbb0fef0a6d7cdb`

Local executor binding:
`4de0920244309376415b37bcef9e2edd9898933c`

Exact fast-kernel binding before SEA_AD:
`6fa084fe24757e2da443fc58e8073e843d1b77cd`

## Panel 0

Gene-ranking positions:
- X 1024..1535
- Y 1536..2047

These genes are disjoint from TD56/TD57A positions 0..1023.

Pair-address hashes:
- X `f0869188d5858777196896c98075907096ad6af9f98fead8a5692d57c57f6f13`
- Y `ca01396a8214bafd2bddb4f1899427867401a04a86f347a3e738512918c2db6d`

### HVS — 4/4 PASS

- split0/half0: observed 0.6451613; p95 0.5394737
- split0/half1: observed 0.6854839; p95 0.5263158
- split1/half0: observed 0.6688596; p95 0.5271617
- split1/half1: observed 0.6336466; p95 0.5287829
- measurable donors total: 36
- result SHA-256: `fbee6cef249533523ba97558f52f388a378c4e5aa86c5be630b0ed9d20085d2f`

### NPH52 — 4/4 PASS

- split0/half0: observed 0.6697719; p95 0.5756048
- split0/half1: observed 0.6761778; p95 0.5618202
- split1/half0: observed 0.6973684; p95 0.5759494
- split1/half1: observed 0.6562500; p95 0.5625000
- measurable donors total: 16
- result SHA-256: `114cc044ae66fe5c530412c6ca2d9f469eaba048fe0b1f256e746fe0093a5557`

### SEA_AD — 4/4 PASS

- split0/half0: observed 0.7417974; p95 0.6972740
- split0/half1: observed 0.7306003; p95 0.6927083
- split1/half0: observed 0.7319224; p95 0.6944046
- split1/half1: observed 0.7453770; p95 0.6927083
- measurable donors total: 46
- result SHA-256: `d149a37c40c43d03c49c8e1783f87a233f64874ef920f8fabe0a9e3d0b846c1e`

## Self-audit

Across all 12 donor-half cases:
- 12/12 PASS;
- minimum observed - null_p95 = **0.0375178075**;
- minimum observed - null_max = **0.0326836262**;
- null-specific measurable donor counts equal the observed measurable count in every case.

Independent implementation checks:
- real-data vectorized distance vs direct naive distance: max abs difference **0.0** in deterministic checks from HVS, NPH52 and SEA_AD;
- independently recomputed triplet populations and sampled counts match exactly:
  - HVS 11,583 population / 3,762 sampled;
  - NPH52 906,330 / 3,630;
  - SEA_AD 112,267,341 / 21,844;
- SEA_AD full replay output was byte-identical to the first completed output.

## Meaning

Panel 0 supports donor-block recurrence of a **scale-free anchored ordering of concordance distances** on an independent gene set.

This does not yet close TD57B because Panel 1 remained unopened during all Panel-0 execution and audits.

No learned-embedding, local-neighborhood, target, or training authority.

Next lawful action: Panel 1 HVS only.
