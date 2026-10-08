# TD58S result — primary 60% partial-evidence relational target survives all sources

Status: `TD58S_PRIMARY60_PARTIAL_EVIDENCE_RELATIONAL_TARGET_SURVIVES__NO_TARGET_AUTHORITY`

Prospective freeze:
`0ef3ce5e4ca5ce49137fc82042e8474af49f3287`

## Frozen screen result

Student:
- disjoint X molecular view;
- exactly 307/512 visible X genes;
- two independent fixed address masks;
- 2,048 pair-order coordinates derived only from visible genes.

Teacher:
- full disjoint Y relational triplet target from TD57A.

Every source was evaluated under:
2 masks × 2 donor splits × 2 halves = 8 cases.

All 24 cases PASS:
observed median donor triplet agreement >0.5 and above matched teacher-cell null p95.

### HVS — 8/8 PASS

Mask 0:
- split0/H0: 0.57031 vs p95 0.51333
- split0/H1: 0.62143 vs 0.51429
- split1/H0: 0.57813 vs 0.52632
- split1/H1: 0.62143 vs 0.51695

Mask 1:
- split0/H0: 0.60333 vs 0.50000
- split0/H1: 0.61567 vs 0.51648
- split1/H0: 0.61667 vs 0.51471
- split1/H1: 0.59091 vs 0.51974

### NPH52 — 8/8 PASS

Mask 0:
- split0/H0: 0.65789 vs 0.58824
- split0/H1: 0.62295 vs 0.57609
- split1/H0: 0.62195 vs 0.57073
- split1/H1: 0.64674 vs 0.59286

Mask 1:
- split0/H0: 0.64094 vs 0.58013
- split0/H1: 0.60326 vs 0.56020
- split1/H0: 0.62500 vs 0.56604
- split1/H1: 0.60326 vs 0.59211

### SEA_AD — 8/8 PASS

Mask 0:
- split0/H0: 0.72578 vs 0.66913
- split0/H1: 0.71701 vs 0.67382
- split1/H0: 0.70959 vs 0.66618
- split1/H1: 0.72754 vs 0.67971

Mask 1:
- split0/H0: 0.71635 vs 0.66428
- split0/H1: 0.70659 vs 0.67188
- split1/H0: 0.69792 vs 0.65743
- split1/H1: 0.72656 vs 0.67873

## Interpretation

The scale-free TD57A relational target remains identifiable when the student is restricted to the project’s primary ~60% molecular evidence level under two independent fixed address masks.

The effect is weaker than full evidence in HVS/NPH52, as expected, but remains donor-block recurrent and correct-cell-specific under the matched teacher-cell null.

This is the first current target-discovery object to jointly satisfy in the 50k falsification setting:
- label-free construction;
- exact Molecular Ledger identity;
- disjoint molecular teacher/student views;
- three-source recurrence;
- donor-block recurrence;
- scale-free relational semantics;
- correct-cell alignment;
- primary-60% evidence survival.

## Remaining limitation

TD58 uses a **shared address mask across cells**. It does not test heterogeneous cell-specific evidence masks.

That is the next higher-priority gate before the full evidence ladder.

No production evidence mask, pair width, architecture, target authority or JEPA training authorization.
