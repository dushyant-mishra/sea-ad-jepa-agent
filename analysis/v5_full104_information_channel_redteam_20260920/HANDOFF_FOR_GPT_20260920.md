# Handoff — FULL104 information-channel red-team

**For:** GPT, continuing from GitHub without the 30–60 GB substrate locally.
**Date:** 2026-09-20

```
branch : audit/v5-full104-information-channel-redteam-20260920
head   : abcea57c1934ed70dea16fbad32e73b3d07d719d
base   : a215bb77c4dbaa4bb60ad5b7ed54c2d574c8bf2a  (cleaned PR #32 head)
PR     : #33 (draft)  https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/33
```

Everything below is reproducible from the repository. Large artifacts are
content-addressed rather than committed; see §7.

---

## 0. Read this first — one finding was withdrawn

An earlier revision of this lane reported that the control-calibration cache was
distorted (HVS 9.1× over-represented, biased toward high-complexity cells).
**Both claims were wrong and are withdrawn.** They compared the cache against the
population marginal, which the design explicitly rejects.

If you are working from any earlier copy of `CALIBRATION_CACHE_COVERAGE_AUDIT.md`
or `CROSS_AUDIT_INTERACTIONS.md`, discard the cache findings. The corrected
report at head `abcea57c` carries a correction notice and the cause. **Audit G's
outcome is `NO_ISSUE_FOUND`.**

---

## 1. What this lane is

Seven reconnaissance audits (A–G) of information channels exposed by the actual
FULL104 code and history. **No current authority was modified** — not pass1, not
Census Authority V2, not the 17,053-target eligibility set, not the burden
ladder, not the masking policy, not G3/G4/G5, not any terminal run contract.

Standing boundaries, unbroken throughout:

```
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED / PATHOLOGY / DEV / SEALED = SEALED
TERMINAL_BURDEN_SELECTED = NO
MASKING_POLICY_SELECTED = NO
TRAINING_OFF
```

`core_measured_zero_frequency = 0.8329826626244999` remains authoritative and was
not re-derived or challenged.

---

## 2. Findings, ranked by consequence

### A — the normalization denominator identifies the source perfectly (`NEW_FINDING` / `OPEN`)

Both authenticated materializers compute `source_library` from the **raw source
expression before** ledger mapping. Verified verbatim in source, not inferred:
Python/H5 SHA `575d02a4…` line `libraries.append(int(np.rint(values).sum()))`
precedes `keep = targets >= 0`; NPH52 R SHA `ca595536…` line 45 `colSums` over
full counts follows line 42 which drops collision-blocked features.

Over all 4,553,407 cells:

| | |
|---|---|
| total source library | 122,517,308,792 |
| total ledger mass | 117,838,742,268 |
| **outside-ledger mass** | **4,678,566,524** |
| **pooled fraction outside ledger** | **0.0381869841** |
| fraction reaching the strict core | 0.5735088987 |
| cells with any outside-ledger mass | 4,354,643 (95.63%) |

Strongly source-dependent:

| source | cells | outside-ledger mean | max | core fraction |
|---|---|---|---|---|
| HVS | 198,718 | **0.000000** | 0.000000 | 0.950307 |
| NPH52 | 236,476 | 0.014000 | 0.039530 | 0.896396 |
| SEA_AD | 4,118,213 | 0.039857 | 0.250000 | 0.545215 |

**Donor-honest leave-one-donor-out nearest-centroid on the three denominator
fractions alone: source accuracy `1.0000` (104/104 donors), majority baseline
0.4423.** Operator 0.3173 against 0.2596 — weak.

Within-source spread is small (NPH52 0.0035, SEA_AD 0.0034, HVS exactly 0), so
the channel behaves as a **categorical dataset tag**, not a continuous covariate.

### D — the attacker's estimand cannot express that channel (`NEW_FINDING` / `OPEN`)

This is what makes A consequential.

The primary score is a **within-donor centred** correlation. Measured: applying an
independent random affine transform per donor changes `D1_CURRENT` by
**`0.000e+00`** — bit-identical — while train-only and no-adaptation regimes move
by 9.5e-04 and 1.07e-03.

**This audit refuted the hypothesis it started from.** I expected D1 to hide a
donor-level channel that D2/D3 would reveal. On `donor_scale_nuisance` all three
regimes sit at their null floor, because the blindness comes from the **score**
(`yc = yd − yd.mean()`, `pc = pred − pred.mean()`), not the standardization.
**Changing D1 → D2 would not restore visibility.**

Consequence: `G3_DESIGN_BLOCKER__ESTIMAND_CANNOT_EXPRESS_DONOR_OR_SOURCE_LEVEL_CHANNELS`.
A capacity-matched G3 attacker inheriting this score inherits the blindness
however much capacity it is given. **G3 must settle the estimand, not only
capacity and functional form.**

### B — address-count parity is not evidence parity (`NEW_FINDING` / `OPEN`)

Per-address burden is extremely heterogeneous: UMI mass median 577,996 against a
max of 3,545,668,963 — a 6,134× spread.

Screening-selected addresses versus the baseline they displace (512-address pool,
512 targets, 8 partners, all cells):

| burden | selected | baseline | ratio |
|---|---|---|---|
| detected tokens | 1,662,009 | 821,726 | **2.02×** |
| UMI mass | 26,135,689 | 4,876,587 | **5.36×** |
| detection entropy | 0.4263 | 0.3097 | 1.38× |

Implied excess over uniform at equal address count: **+1.03% detected tokens and
+4.84% UMI mass at the 5% rung**, decaying to +0.10% / +0.48% at 50%.

Classified `G_BURDEN_ADDRESS_PARITY_DOES_NOT_IMPLY_EVIDENCE_PARITY`.

### C — global eligibility ≠ per-source estimability (`NEW_FINDING` / `OPEN`)

| | targets | share |
|---|---|---|
| estimable in all three sources | **14,526** | **85.18%** |
| one weak source | 2,447 | 14.35% |
| two weak sources | 80 | 0.47% |

The mechanism, from the frozen scorer: `r = 0.0 if den <= _EPS`. A donor where the
target does not vary yields `rss_y = 0`, so `r² = 0` — **the best possible score**,
contributed for free.

| source | zero-variance pairs | fraction | targets with any | targets with **all** donors silent |
|---|---|---|---|---|
| HVS | 887 | 0.127% | 380 | 0 |
| NPH52 | 6,220 | 2.146% | **4,976** | 0 |
| SEA_AD | 23,344 | 2.976% | 2,031 | **75** |

**75 targets have every SEA_AD donor silent** — a full third of the verdict is
identically zero and cannot fail.

### E — the screening score tracks neither component (`PARTIALLY_AUDITED` / `OPEN`)

512 pairs, all cells, zero non-estimable.

```
corr(E3, E1 co-detection)             = +0.1774
corr(E3, E2 quantitative covariation) = -0.0721
```

The production screening shape is **not** selecting quantitatively co-varying
partners. But real covariation exists in the data: E2 mean 0.2600 exceeds E1 mean
0.1424.

Categories deliberately **not** frozen (`UNFROZEN__CONTINUOUS_ONLY`).

### F — design only, no number (`OPEN`)

No lawful teacher representation exists. Marked
`CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION`. The decomposition and six
known-composition controls are committed and passing, so the measurement becomes
unavoidable once a teacher exists. **Do not fabricate a stand-in.**

### G — no issue (`NO_ISSUE_FOUND`)

The cache is equal-donor-weighted by design (`FULL104_MASKING_NONLINEAR_CHALLENGE_20260918.md`:
*"each donor receives equal total fit weight so large donors cannot dominate
merely because they contain more cells"*). Against that target:

| measure | design target | observed | deviation |
|---|---|---|---|
| mean core nonzeros | 3,370.1 | 3,371.6 | **+0.05%** |
| HVS share | 39.42% | 39.78% | +0.36pp |
| low-tail cells | 420 | 403 | ratio 0.959 |

HVS and SEA_AD at exactly `donors × 1024`. Within-donor selection is
`row_priority(manifest_sha, donor_code, selection_row)` — a hash of scientific
identity, blind to expression content, so a complexity bias is mechanically
impossible.

---

## 3. What to challenge

These are the weakest points. Attack them.

1. **Audit E's pool is 512 of 17,186 addresses.** The best partner within a small
   pool may be poor absolutely, which could itself depress both correlations.
   The full-universe computation is the honest test and was not run — it costs one
   streaming pass per target per fold.
2. **Audit B's ratios come from the same 512-address pool.** The per-address
   burden distribution is from all 17,186, but the *selection* comparison is not.
3. **Audit D is fixtures only.** The affine-invariance result is exact and
   general, but the magnitudes (null floor ~0.0019, signal ~0.795) are fixture
   properties and do not transfer.
4. **Audit A's predictiveness uses donor-mean features.** Cell-level donor
   separability was 0.0343 against a 0.0096 chance rate — above chance but weak,
   and reported as a separability diagnostic, not an out-of-donor claim.
5. **The denominator channel's magnitude in a trained model is unmeasured.** The
   fixture in Audit D put it at ~0.0004 excess over its own negative control at
   32 features; production sees 17,186 addresses sharing one denominator. That is
   a reason **not** to treat 0.0004 as an upper bound, and equally not to treat it
   as evidence the effect is large.

---

## 4. The question that sizes everything, and is not answered

**Does source track disease status in this 104-donor assembly?**

The structural part needs no sealed data: SEA-AD spans AD neuropathology by
design, NPH52 is living NPH biopsy patients, HVS is a third population. Three
cohorts, three disease distributions — so source *is* entangled with disease.
That makes Audit A a plausible disease shortcut, not merely a batch nuisance.

The **magnitude** needs per-donor outcomes and was not opened. If it is opened,
the constraint is: the magnitude may size the risk but **must not be used to
select between the candidate repairs**, or the confirmation set is burned.

Note for method discipline: pathology-blindness constrains the model and the
method selection. It does not forbid knowing the study design.

---

## 5. Open repairs — all `PROPOSED_REPAIR_REQUIRED`, none selected

Discovery and policy choice were kept separable on purpose. **Do not implement
any of these as if it were a bug fix.**

**A (denominator).** (i) Re-derive the denominator from ledger mass — removes the
channel but changes what normalization means, since it is no longer depth
normalization against actual sequencing depth. (ii) Keep the biological library
and carry `fraction_outside_ledger` as a declared covariate. (iii) Change the
estimand so between-donor structure is visible.

**B (burden).** (i) Preserve detected-token burden instead of address count.
(ii) Preserve UMI-mass burden — stricter, since UMI mass is far more skewed.
(iii) Keep address parity and report burden as a covariate, making the
equivalence claim explicitly conditional.

**C (estimability).** (i) Require per-source estimability prospectively and accept
a smaller universe. (ii) Let a source abstain rather than contribute `r² = 0`,
which changes the estimand. (iii) Keep the rule and report per-source estimable
counts with every verdict. **The target set was deliberately not shrunk** —
removing targets after seeing which are weak selects the evaluation population
using the evaluation.

---

## 6. Revised dependency order

The prior order was: close audits → decide repairs → freeze G4 → justify G5 → H3
→ H4/G2 → G4 execution → G3 → F13/F14/F15 → terminal masking → training.

**Audit D changes one step.** G3 was scoped as capacity and functional form; it
now also requires settling the **estimand**, which sits upstream of building any
stronger attacker.

**Audits B and C both bear on whether the masking estimand is well posed.** That
should be settled before a margin is attached to it, so do not proceed to G4/G5
mechanically.

---

## 7. Artifacts

Committed, all under `analysis/v5_full104_information_channel_redteam_20260920/`:

```
README.md                                    lane index and verification protocol
NORMALIZATION_DENOMINATOR_AUDIT_REPORT.md    A
MASK_EFFECTIVE_BURDEN_AUDIT_REPORT.md        B
TARGET_SOURCE_ESTIMABILITY_AUDIT_REPORT.md   C
ATTACKER_STANDARDIZATION_ESTIMAND_AUDIT.md   D
PARTNER_CODETECTION_DECOMPOSITION_REPORT.md  E
TARGET_IDENTITY_ZERO_STRATIFIED_DESIGN.md    F
CALIBRATION_CACHE_COVERAGE_AUDIT.md          G  (carries the withdrawal notice)
CROSS_AUDIT_INTERACTIONS.md                  status table across all seven
EVIDENCE_SHA256.csv                          45 rows, byte size + SHA-256
EXTERNAL_ARTIFACTS.json                      uncommitted artifacts, content-addressed
scripts/                                     every producing script
evidence/audit_{a,b,c,d,e,f,g}/              compact JSON + CSV
```

**Not committed**, held on the GPU machine and content-addressed:

| role | path | bytes | SHA-256 | cell-level? |
|---|---|---|---|---|
| Audit A per-cell denominator | `D:/jepa_full104_redteam_20260920_external/audit_a_cell_level_denominator_v1.npz` | 42,283,767 | `9ff45071fb09f5d89340a7cca76ab77ab826533f29e9dd80b33a821645283cd1` | **yes** |
| core sufficient statistics (B, C, E) | `D:/jepa_full104_redteam_20260920_external/core_sufficient_statistics_v1.npz` | 242,087,519 | `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae` | no |

Every aggregate needed to challenge a conclusion is committed. You cannot
recompute those two from GitHub, but you can verify byte-identity against the
artifact the numbers came from.

Key upstream roots: pass1 `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`,
block manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`,
Census Authority V2 `7a090d4078239e9bc161ae60c289b7f1a5bbb02e7cf3e6bcc0ae9c284b89ee21`.

---

## 8. Verification standard used

Every audit: implement → unit test → **positive control with a known answer** →
**negative control capable of falsifying the test** → real execution → fail-closed
invariants → **independent recomputation of headline totals by a second route** →
red-team → commit. Status is derived from evidence, never declared by the caller.
Unmeasurable quantities are reported `NOT_MEASURABLE` with a reason, never as
zero and never silently omitted.

Two cross-producer corroborations worth relying on:

- Audit A's `L_ledger` accumulated both via `csr.sum(axis=1)` and via
  `np.add.reduceat` over raw `data`/`indptr`, agreement required per block; and
  its observed per-cell core nonzero counts matched `cell_nnz_core` in the
  authenticated pass1 NPZ — a different script from a different session — exactly
  across all 4,553,407 cells.
- Audit A's `total_core_mass` (70,264,766,840) independently equals the
  statistics pass's `total_core_umi`. Different code paths, different runs.

**90 audit-lane tests pass, 0 skipped.** All wired into CI.

Reproduction requires `PYTHONPATH=src` and the environment's native DLL directory
on `PATH` — a hard precondition, see
`analysis/v5_full104_pass1_rebuild_20260920/SOLVER_ENVIRONMENT_DIAGNOSIS_CORRECTION_20260920.md`.

---

## 9. What NOT to do

- Do not open terminal masking outcomes, D_shared, pathology, or DEV/SEALED.
- Do not select a terminal burden or masking policy, or construct a terminal run
  contract.
- Do not authorize training.
- Do not implement any §5 repair as a bug fix — each is a scientific position.
- Do not shrink the 17,053-target set based on Audit C.
- Do not freeze Audit E's categories.
- Do not fabricate a teacher representation for Audit F.
- Do not re-raise Audit G's withdrawn cache findings.

```
TRAINING_OFF
```
