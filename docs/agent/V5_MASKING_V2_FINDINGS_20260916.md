# V5 masking V2 — cross-fitted shortcut predictability, findings 2026-09-16

Branch `authority/v5-masking-shortcut-predictability-v2-20260916`, from V1 head `897bb0c1`.
Contract frozen **before any real V2 result** at commit `15732d4c`, digest
`0c3e89cf2be164bb22d43e5ba5592d562b2f33c32b4aea78bfa460f825a44ecf`.

No training. No `D_shared`. No protected outcome. FULL104 read-only.

## Disposition

### `MASKING_V2_SHORTCUT_AUTHORITY_REMAINS_OPEN`

No masking condition met the frozen threshold. No threshold was changed after seeing results.

---

## Four design defects found by synthetic testing BEFORE the contract froze

Each would have produced confident nonsense on real data. This is the part of the lane I
consider most valuable.

| id | symptom | cause | fix |
|---|---|---|---|
| **V2-D1** | held-out R² **0.941** with *no* planted shortcut | a within-donor global factor lifts every address including the target, so anything predicts anything | measure **incrementally over a global-cell-state baseline**. The goal is reconstruction *without understanding broader cell state*; a global cell factor **is** broader cell state, so predicting from it is the legitimate signal |
| **V2-D2** | baseline R² **−22.3** (operator) and **−9.0** (source), inflating gain to **+22.2** / **+8.9** with nothing planted | train-fitted standardisation is mis-scaled on donors shifted by a batch effect | standardise features **within donor** |
| **V2-D3** | a genuine planted shortcut scored only **0.084** | raw incremental R² is normalised by a total variance the confound dominates | **partial R²** over the residual the baseline could not explain |
| **V2-D4** | per-donor level offsets distorted scoring | absolute-level prediction | **donor-centred** evaluation |

On real data, library size is exactly a V2-D1 factor, so the first V2 draft would have
reported shortcuts everywhere that were really depth.

**After the fixes, suppression and specificity hold together:**

| nuisance | null partial R² | with planted shortcut |
|---|---|---|
| none | −0.054 | 0.903 |
| donor | −0.054 | 0.903 |
| operator | −0.055 | 0.903 |
| source | −0.054 | 0.901 |
| within-donor depth | −0.001 | 0.673 |
| within-donor global shift | −0.014 | 0.802 |

Donor, operator and source now give results *identical* to the no-confound case, because
per-donor standardisation removes them exactly.

## Calibration — synthetic only

Rule declared before reading numbers: maximise planted recall subject to null partial
R² < 0.10 on every nuisance; tie-break smallest budget, then largest alpha. Selected
**m=20, α=1e-2** (recall 1.000, min planted 0.884, max null −0.0135). Note **α=1e-1 fails
the null constraint** — heavy shrinkage also shrinks the baseline and inflates partial R².
The frozen rule caught that.

---

## Real FULL104 result — power ladder level 1 (blocks/op = 3)

56,503 cells, 76 donors, 2,000 common-core addresses, 60 targets × 10 outer folds = 600
evaluations at matched burden (400 of 2,000 addresses).

| condition | mean partial R² | median | n |
|---|---|---|---|
| U uniform | −0.3317 | −0.1304 | 600 |
| V1 control (frozen K,R, same budget) | −0.3290 | −0.1265 | 600 |
| **V2 shortcut co-mask** | −0.3319 | −0.1198 | 600 |

**V2 vs U: 0.1% reduction** (absolute +0.0003), fraction of targets improved 0.398.
The contract required **≥30% relative and ≥0.02 absolute**. **FAIL.**

### Why: there is almost nothing to remove

Discovery partial R² — can a cheap attacker beat global cell state at all, on held-out
donors?

| statistic | value |
|---|---|
| median | **−0.7112** |
| p90 | +0.0088 |
| max | +0.1830 |
| fraction > 0 | 0.145 |
| fraction ≥ 0.05 floor | **0.040** |

Only **22 of 600** target-fold evaluations produced any shortcut set at all. For the other
578, the frozen `NO_SHORTCUT` branch applied and V2 correctly degenerated to uniform
masking — which is why V2 ≈ U.

**Reading:** once global cell state is accounted for, a deliberately cheap linear attacker
has essentially no residual ability to reconstruct a target from other addresses on donors
it never saw. The median is strongly negative: the candidate features actively *hurt*
relative to the baseline alone.

This does **not** say molecular dependence is absent. It says the specific threat model —
cheap local interpolation from a few visible partners, beyond broader cell state — is
weakly supported at this power, for common-core targets, against a linear attacker.

---

## Ladder status — INCOMPLETE

| level | blocks/op | status |
|---|---|---|
| 1 | 3 | **executed** (above) |
| 2 | 8 | **still executing** |
| 3 | 20 | **not yet executed** |

The contract requires executing every level. Stopping at level 1 is *not* cherry-picking a
pass — level 1 failed — but the ladder is not complete, so the level-2/3 power question is
**NOT YET ANSWERED**. The disposition above is correct regardless, since nothing qualified.

---

## Masking-authority schema repair — COMPLETE, schema only

`CurrentMaskingPolicyAuthorityV2` repairs the V1 defect: enumerated vocabulary (40
arbitrary-identifier attacks fail closed, including TD57/59/60 and corrmask/pearson
names), exact registry root as an allowlist of one, raw artifact digests rejected where an
authority root is required, and five roles that must be mutually distinct so none can
stand in for another. A test asserts **no mask-fraction field exists** on the authority,
preserving the V1 finding that burden belongs to a separate evidence-budget authority.

**No production masking policy was instantiated or frozen** — V2 has not qualified. The
frozen `MaskingAuthorityV1` is untouched; this is a successor.

---

## Test accounting

| category | count |
|---|---|
| PASSED | 18 shortcut-predictability synthetic + 61 masking-authority attacks + 19 V1 estimator (unchanged) |
| FAILED | 0 at HEAD (4 genuine failures during development drove V2-D1…D4) |
| SKIPPED / DESELECTED | 0 / 0 |
| NOT ESTIMABLE | source/operator leakage probe and per-source heterogeneity — not reached, because no policy qualified |
| NOT EXECUTED | power-ladder levels 2 and 3; native/non-common-core targets |
| HEAVY/DATA-DEPENDENT | level 1 executed read-only; levels 2–3 in progress |

---

## Residual risks

1. **Attacker capacity.** A linear ridge over ≤64 screened features is deliberately weak. A
   nonlinear attacker could find routes it cannot. The contract forbade escalation in this
   lane, so "no cheap shortcut" means *no cheap linear shortcut*.
2. **Screening false negatives.** Recall was qualified on synthetic plants (1.000), not on
   real shortcuts, which are unknown by construction.
3. **Power.** Levels 2–3 unexecuted.
4. **Scope.** Common-core targets only; native support not evaluated.
5. **Production geometry** remains unchosen and could change the shortcut landscape.
