# TD57A result — scale-free triplet relational target survives all donor blocks

Status: `TD57A_SCALE_FREE_TRIPLET_RELATIONAL_TARGET_SURVIVES__NO_TARGET_AUTHORITY`

Prospective freeze:
`94799072b62e9efe6156744ae2449b5ed6c2908f`

## Why TD57A supersedes incomplete TD57S execution

TD57S used exact top-hash enumeration over every possible triplet. That is mechanically tractable in HVS/NPH52 but requires ~112 million SHA-256 candidate evaluations in SEA_AD.

TD57A prospectively replaced only that sampling mechanism with a direct deterministic uniform finite-index sampler. No TD57S result was inherited.

Sampler preflight:
- exact anchor/partner-pair unranking is bijective for exhaustive n=4..25 test populations;
- sampled indices are unique, in-range and deterministic;
- `TD57A_SAMPLER_PREFLIGHT_PASS`.

## Primary donor-block results

Each source was tested in:
- split 0 / H0
- split 0 / H1
- split 1 / H0
- split 1 / H1

All 12 half-cases satisfy:
- observed median donor triplet agreement >0.5;
- observed > matched Y-cell null p95.

### HVS — 4/4 PASS
- split0/H0: observed **0.61719**, p95 **0.51563**
- split0/H1: **0.63636**, p95 **0.52632**
- split1/H0: **0.64076**, p95 **0.50702**
- split1/H1: **0.61780**, p95 **0.52038**

36 donors were measurable overall.

### NPH52 — 4/4 PASS
- split0/H0: observed **0.66582**, p95 **0.58214**
- split0/H1: **0.64390**, p95 **0.57718**
- split1/H0: **0.64176**, p95 **0.58590**
- split1/H1: **0.65486**, p95 **0.56275**

16 donors measurable overall.

### SEA_AD — 4/4 PASS
- split0/H0: observed **0.72270**, p95 **0.67262**
- split0/H1: **0.73997**, p95 **0.67708**
- split1/H0: **0.72775**, p95 **0.67987**
- split1/H1: **0.73066**, p95 **0.67057**

46 donors measurable overall.

The SEA_AD direct sampler addressed a finite triplet population of 112,267,341 without enumerating all candidates and retained 21,844 prospectively sampled stratum triplets.

## Null-measurability adversarial audit

The first implementation let a null score only triplets already resolved in observed Y.

A stricter interpretation was independently executed:
- keep every observed X-resolved triplet;
- after each Y-cell permutation, let that null world independently determine whether Y is resolved;
- recompute donor agreements from that null-specific scorable set.

HVS and NPH52 terminals and null distributions were essentially unchanged.

SEA_AD stricter-null p95 values:
- split0/H0: **0.67291**
- split0/H1: **0.67708**
- split1/H0: **0.67969**
- split1/H1: **0.67057**

All four still PASS.

Therefore the null-measurability interpretation is non-material to the TD57A terminal.

## Interpretation

TD57A establishes, label-free and donor-block recurrently, that two disjoint Molecular Ledger views agree on a **scale-free relational ordering**:

for anchor cell i and partners j,k, the view-X and view-Y molecular geometries agree above matched wrong-cell nulls on which partner is closer to i.

This is stronger than TD56 for target design because:
- it does not require absolute distance calibration;
- the target is invariant to source-specific monotone rescaling of molecular distance;
- it has a direct relational training form (triplet/ranking loss);
- it still requires correct-cell Y alignment;
- it survives independent donor halves in all three source families.

No latent-axis transfer, hidden-gene scalar reconstruction, state labels, clustering, graph matching or source-specific coordinate map is used.

## What remains

TD57A does NOT establish:
- student partial-evidence predictability;
- evidence-response behavior;
- measurement-depth behavior of the relational target;
- production triplet sampling/pair width;
- full 4.553M reader_fit qualification;
- JEPA training authority.

The next gate must test whether the triplet ordering remains predictable when the student receives prospectively masked lawful evidence while the teacher uses the richer lawful view.

## Local artifact identities

- primary execution script SHA-256: `cca6894b4635a8305eb461233218eb1cf59c8387f33710acb3696b02f1b22730`
- stricter-null execution script SHA-256: `c3989fd0e5524b51610a05480210ca96518d73480cb4a2138340e77eb93b3ef8`
- HVS result SHA-256: `e631a905986499463cea69094f1b8a247939b413fa47bfd72ef1b1c8adbbd9f7`
- NPH52 result SHA-256: `5baab2527d4c717ee3d223e30609aca7edb2a5ee17e21bbfeab95e403696d1fe`
- SEA_AD result SHA-256: `f0ae31c0d29d40edf8590378af7ec13d4dde114af7dd785945995a92113ae4cb`

No biological labels were opened.
No target authority or JEPA training authorization.
