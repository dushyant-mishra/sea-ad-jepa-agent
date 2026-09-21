# Audit B — actual masking burden versus nominal address burden

Date: 2026-09-20
Status: **`NEW_FINDING` / `OPEN`. No masking policy changed. No terminal masking
score computed, inspected or implied.**

Produced by `scripts/audit_b_effective_burden_20260920.py` from the shared core
sufficient statistics over all 8,915 blocks and all 4,553,407 cells.
Evidence: `evidence/audit_b/`.

---

## 1. The premise under test

`apply_burden_preserving_swaps` guarantees exact **address-count** parity, and
the parity test in `tests/test_v5_audit_b_mask_plan_v1.py` confirms it holds
exactly: every policy masks `co_mask_count + 1` addresses, and the swap sets are
equal-sized.

The census burden table uses `remaining = (1 - f) * cell_nnz_core`, an
expected-uniform-address approximation that never applies the actual
TOP8 / RIDGE8 / PREFIX3 masks. So the open question is whether equal address
count means equal evidence removed.

## 2. Per-address burden is extremely heterogeneous

Across the 17,186 strict-core addresses:

| burden measure | median | p95 | max | spread (max/median) |
|---|---|---|---|---|
| **B2** detected tokens | 260,522 | 3,053,046 | 4,198,103 | 16× |
| **B3** UMI mass | 577,996 | 15,396,228 | **3,545,668,963** | **6,134×** |
| B4 normalized signal *(diagnostic only)* | 176,714 | 2,771,681 | 22,887,034 | 130× |
| detection probability | 0.1 | 0.7 | 0.9 | — |
| **B5** detection entropy *(supporting)* | 0.2 | 0.7 | 0.7 | — |

Addresses are not interchangeable. Masking *an* address and masking *that*
address remove wildly different amounts of evidence — six thousandfold different
for UMI mass between the median and the heaviest address.

## 3. Targeted selection systematically picks heavier addresses

Comparing the addresses the production screening score selects against the pool
baseline they displace (512-address deterministic pool, 512 targets, 8 partners
each, all 4,553,407 cells):

| burden measure | selected mean | baseline mean | **ratio** |
|---|---|---|---|
| **B2** detected tokens | 1,662,009 | 821,726 | **2.02×** |
| **B3** UMI mass | 26,135,689 | 4,876,587 | **5.36×** |
| **B5** detection entropy | 0.4263 | 0.3097 | 1.38× |

The screening score correlates 0.360 with an address's detection rate.

So at **identical address count**, a targeted policy swaps in addresses carrying
**twice the detected genes and over five times the RNA mass** of the random
addresses it swaps out.

## 4. What that means at each burden rung

Because every mask difference is carried by at most `targeted_partner_cap = 8`
swapped addresses out of the whole mask, the effect is bounded and shrinks as the
rung grows:

| rung | addresses masked | fraction of detected tokens removed (uniform) | **extra detected tokens vs uniform** | **extra UMI mass vs uniform** |
|---|---|---|---|---|
| **5%** | 859 | 0.049983 | **+1.03%** | **+4.84%** |
| 10% | 1,718 | 0.099965 | +0.51% | +2.42% |
| 15% | 2,577 | 0.149948 | +0.34% | +1.61% |
| 20% | 3,437 | 0.199988 | +0.26% | +1.21% |
| 30% | 5,155 | 0.299953 | +0.17% | +0.81% |
| 50% | 8,592 | 0.499942 | +0.10% | +0.48% |

At the 5% rung — the first rung the ladder would evaluate — a targeted policy
removes about **4.8% more RNA mass** than the uniform policy it is compared
against, while removing exactly the same number of addresses.

## 5. Classification

```
G_BURDEN_ADDRESS_PARITY_DOES_NOT_IMPLY_EVIDENCE_PARITY
```

Confirmed on the full substrate. The parity the masking contract guarantees is
real but is not the parity the scientific comparison needs.

`zero != missing` is preserved throughout: B2 (detected tokens) and B3 (UMI mass)
are reported separately precisely because masking a measured zero removes
evidence of non-detection while removing no UMI mass. Neither is described as "no
information removed".

B4 is labelled `DIAGNOSTIC_ONLY__NOT_CALLED_INFORMATION_WITHOUT_AN_INFORMATION_THEORETIC_ARGUMENT`
and B5 `SUPPORTING_DETECTION_ENTROPY_BURDEN`; neither carries authority.

## 6. Why this matters for G5

If two policies remove different amounts of evidence at the same address count,
then comparing them against a single equivalence margin δ compares conditions
that are not exchangeable. A residual difference between UNIFORM and TOP8 would
be partly a burden difference, not purely a targeting effect — so an equivalence
claim would be conditional on burden rather than on policy.

The effect is largest at exactly the rung the ladder opens first.

## 7. Verification

The structural route — burden differences carried *only* by the swapped
addresses — is pinned by
`test_added_and_dropped_sets_have_equal_size_and_explain_the_whole_difference`,
which asserts `mask == (base - dropped) | added` for every policy and target.

The calculator has both controls. The positive control constructs burden that
increases with address index and requires the ratio to exceed 1.1. The negative
control **reverses** screening strength relative to burden and requires the ratio
to fall **below 1** — without it, a calculator that always reported an advantage
would manufacture this entire finding. 9 tests, 0 skipped.

Rung arithmetic is pinned to the frozen `(17185 * pct) // 100` rule, with the 5%
rung at exactly 859.

## 8. What is not concluded, and the repair

No policy is changed. No terminal masking score was computed or inspected. The
mask-plan generator is held-out-blind, verified empirically by perturbing every
held-out donor's counts and requiring no plan to change.

```
PROPOSED_REPAIR_REQUIRED
```

The options are genuinely different contracts, not one bug fix:

1. **Preserve detected-token burden** instead of address count when swapping.
2. **Preserve UMI-mass burden** instead — a different and stricter constraint,
   since UMI mass is the more skewed quantity.
3. **Keep address parity and report burden as a covariate**, making the
   equivalence claim explicitly conditional on it.

Each changes what "burden-preserving" means. **None is selected here**, and the
choice must not be made by observing which one favours a policy.

```
ADDRESS_COUNT_PARITY            = HOLDS EXACTLY
EVIDENCE_BURDEN_PARITY          = DOES NOT HOLD
MASKING_POLICY_CHANGED          = NO
TERMINAL_MASKING_SCORES         = NOT COMPUTED
TRAINING_OFF
```
