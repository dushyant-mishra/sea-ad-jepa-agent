# TD57C result — nearest-third three-view local geometry fails in HVS

Status: `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`
Date: 2026-09-08

Prospective freeze:
`0c6d3f120cac2fd7f0a2f51f006d20d43a8136d1`

Metadata-only locality freeze:
`1a38eccaeaf55ddd2a88f5d3b9a573d7de037286`

Exact local executor:
- path `/mnt/data/td57c_three_view_local_geometry.py`
- SHA-256 `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

## Frozen sequential outcome

Only Panel 0 HVS was opened.

HVS Panel 0:
- split0/half0 observed 0.5370370; null p95 0.5555556 -> FAIL
- split0/half1 observed 0.5872340; null p95 0.5864549 -> PASS
- split1/half0 observed 0.5416667; null p95 0.5806452 -> FAIL
- split1/half1 observed 0.5872340; null p95 0.5833333 -> PASS

Therefore HVS Panel 0 = **2/4 FAIL**.

Per the prospective sequential rule:
- NPH52 was not opened;
- SEA_AD was not opened;
- Panel 1 was not opened.

Result artifact:
- `/mnt/data/td57c_p0_hvs.json`

## Implementation/self-audit

The failure is not attributable to a known mechanics or support defect:

- exact replay was byte-identical;
- direct/naive vs vectorized distance checks gave max absolute difference 0.0;
- all 17 structurally eligible HVS donors remained measurable;
- zero selector-distance ties occurred at the nearest-third cutoff;
- therefore the global_row tie-break never affected the observed local neighborhood;
- observed/null measurable donor counts were equal in every case.

The donor-level local signal is heterogeneous rather than uniformly absent: some donors are near/below chance while others retain strong local agreement.

## Post-failure same-X/Y unrestricted diagnostic

To determine whether TD57C failed because the new X/Y gene panel itself was bad or because nearest-third localization was too aggressive, a post-failure diagnostic reused the exact same:

- HVS source;
- Panel-0 X genes;
- Panel-0 Y genes;
- TD57C X pair hash `1546f245e20df358c380da26471b48bbe07b2c68d061372c68837ff3de2d81c0`;
- TD57C Y pair hash `61d9aebf23260a30650ecbb39f725e243bbbb9c13919972852108da56b1812e7`;
- structural donor split rule;
- matched Y-cell depth/detection null.

The only change was removing the Z-selected nearest-third restriction and sampling unrestricted within-stratum triplets.

Post-failure diagnostic result:
- split0/half0: 0.5932203 > p95 0.5274725 -> PASS
- split0/half1: 0.6338374 > p95 0.5427632 -> PASS
- split1/half0: 0.5859375 > p95 0.5263158 -> PASS
- split1/half1: 0.6338374 > p95 0.5419048 -> PASS
- 4/4 PASS.

Diagnostic artifact:
- `/mnt/data/td57c_postfail_global_same_xy_forensic.json`

Diagnostic script:
- `/mnt/data/td57c_global_same_xy_forensic.py`

This diagnostic is explicitly **post-failure and cannot rescue TD57C**.

## Interpretation

TD57C falsifies the specific proposal that the relational training signal should be concentrated entirely inside a **nearest-one-third neighborhood selected by an independent concordance view** on the 50k pilot.

The failure is localized:
- the same molecular X/Y views still reproduce unrestricted relational order;
- therefore the new panel itself is not the explanation;
- aggressive locality removes enough recurrent signal in HVS that the frozen 4/4 donor-half rule is no longer met.

This means the next objective design should **not** hard-code nearest-third local mining as the primary relational loss.

It does not falsify:
- TD56 relational geometry;
- TD57B donor-recurrent scale-free relational order;
- broader/mesoscale affinity matching;
- mixed global + local objectives;
- learned-geometry continuity tests;
- full-reader locality that may be estimable with much denser donor/operator sampling.

## Next lawful agenda

Before neural objective integration, design a new bounded gate that asks whether there is a **locality frontier** rather than assuming the deepest local scale is valid.

Important constraints:
1. TD57C is terminal FAIL and may not be rescued by changing 1/3 to 1/2 after outcome.
2. A successor must use prospectively frozen unused genes or an explicitly diagnostic-only status.
3. The new scientific question should compare coarse/mesoscale/local relational information without selecting the winning locality after seeing the same outcome.
4. Production neighborhood scale must ultimately be derived on the complete 4,553,407-cell reader_fit population.
5. Do not modify the frozen Teacher/Student V3 mechanics branch yet.
6. No u1 training is authorized.

Frozen terminal:
`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`
