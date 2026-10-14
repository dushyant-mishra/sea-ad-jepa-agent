# TD Real-Gate Blocker Resolution — Self-Audit V2

Status: `OUTCOME_BLIND_SELF_AUDIT__CORRECTS_V1_BEFORE_IMPLEMENTATION`

This amendment corrects weaknesses found during recursive self-audit of `2026-10-13-td-real-blocked-gates-resolution-v1.md`. Where this document conflicts with V1, this V2 amendment controls.

## 1. G6 diagnostic scope correction

A fixed ridge probe can prove a teacher-evidence advantage when it detects one, but failure of a finite diagnostic family cannot prove information-theoretic absence of teacher-private information.

Therefore G6 is operationally scoped as follows:

- PASS: the prospectively frozen matched ridge probe shows a donor-recurrent teacher-evidence advantage beyond qualified refit/measurement variability;
- FAIL: permitted only after the probe family itself has passed a separate known-truth rejection-power qualification for the exact target geometry under the alternatives the gate claims to reject;
- otherwise a nonpositive biological result is `NOT_ESTIMABLE_FOR_TEACHER_INFORMATION_ADVANTAGE`, not automatic FAIL.

The probe qualification must include positive known-truth worlds with teacher-private signal, negative worlds with no extra teacher information, and underpowered worlds. No current human candidate outcome may be used to qualify the probe.

## 2. G8 independent technical-reference correction

V1 compared full-to-thinned displacement with pairwise displacement between two p-thinnings. Pairwise p-thinning distance can have a different variance scale and may be an overly permissive reference.

V2 freezes a replicate-envelope design instead.

For each depth p in `{0.25, 0.50, 0.75}` and each donor, generate a prospectively fixed number K of independent p-thinnings under a calibration seed namespace. The candidate is evaluated on every calibration thinning using the same frozen displacement metric.

The calibration object stores, per donor/depth:

- the Fréchet/medoid center under the frozen metric;
- the empirical technical-replicate displacement distribution around that center;
- a one-sided prediction bound at the gate-local frozen error rate, computed by a prospectively fixed finite-sample order-statistic rule;
- support/abstention counts.

A deciding thinning uses a disjoint seed namespace. The full-count candidate state is compared with the calibration center and deciding thinning. PASS requires the full/deciding states to remain within the precomputed technical-replicate prediction envelope for every required depth/source stratum. A depth exceeding the frozen envelope is FAIL; insufficient calibration resolution/support is `NOT_ESTIMABLE`.

K and the exact finite-sample order-statistic rule must be chosen from the desired gate-local error rate before candidate values and then hash-bound. They are engineering precision parameters, not tuned biological margins.

## 3. G9 / S1 / S2 null-bound correction

V1 used the median of the null distribution. That is too weak for a substantive recurrence claim.

For recurrence/stability gates, the donor-preserving null comparison must use the prospectively frozen adverse null bound at the gate-local error rate:

- for a larger-is-better recurrence statistic: `delta_d = observed_d - q_(1-alpha_gate)(null_d)`;
- for a smaller-is-better displacement statistic: `delta_d = q_(alpha_gate)(null_d) - observed_d`.

The null statistic must be generated under frozen seeds or exact enumeration where practical. PASS additionally requires the observed recurrence/stability to exceed `U_refit` / `U_measurement` as applicable. Null significance alone is not sufficient.

## 4. R1 null-bound correction

For `R1_SCALE_FREE_RELATIONAL_RECURRENCE`, use the frozen relational statistic on the same predeclared pairs/scales. If Spearman recurrence is used, Fisher-z is only a monotone numerical transform.

Define:

`delta_d = z(rho_observed_d) - q_(1-alpha_gate)( z(rho_null_d) )`

and require `delta_d - U_refit_d` to pass donor-primary testing for every required predeclared scale/source stratum. No median-null comparison, nearest-fraction search, or fine-locality mining is permitted.

## 5. G12 anti-trivial-scope correction

A foundation candidate may not pass G12 by voluntarily shrinking its claim to an easy subset.

Before outcomes, the frozen population/support registry must define the **mandatory claim envelope** for each candidate:

- foundation candidates C1/C2/C3/C6/C4 must include every population stratum in which their required evidence is physically present and lawfully available under the frozen candidate contract;
- C5 may use a narrower specialist envelope only where its specialist evidence is physically supported;
- unsupported strata are abstained and reported, not imputed;
- a stratum that belongs to the mandatory claim envelope but lacks inferential resolution makes G12 `NOT_ESTIMABLE`, not silently out-of-scope.

Thus there is no arbitrary universal coverage percentage, but there is also no post-hoc claim-scope escape hatch.

## 6. C6 comparator correction

V1's per-donor `max(C1,C3)` comparator creates an avoidable selection effect and can switch comparator identity across donors.

C6 must instead beat **both independently qualified constituents** under the same matched held-out donor cases:

- `delta_C1,d = score(C6)_d - score(C1)_d`
- `delta_C3,d = score(C6)_d - score(C3)_d`

Each contrast must separately exceed its matched `m_d = max(U_refit_d,U_measurement_d)` under the frozen within-gate multiplicity rule. PASS requires both contrasts PASS plus non-worsening transfer/shortcut/coverage/uncertainty checks. Either estimable failed constituent comparison makes C6 increment FAIL; unresolved comparison -> `NOT_ESTIMABLE`.

This is stronger than donor-wise strongest-constituent selection and faithfully answers whether fusion adds value beyond both constituents.

## 7. Noise/reference separation

Reference artifacts are not allowed to reuse the deciding stochastic realization.

At minimum, seed namespaces must be disjoint for:

- technical calibration;
- refit calibration;
- gate deciding evaluation;
- donor-preserving null generation.

Reference-generation code, seeds, environment, input identity and receipt hashes must be bound before any real gate outcome is interpreted.

## 8. Updated state after V2 self-audit

The blocker set is no longer treated as scientifically unsolved en masse.

- G2: prospective noise-relative magnitude rule specified; waits qualified reference artifact.
- G6: matched operational probe rule specified; waits known-truth probe qualification and code freeze.
- G7: terminal plateau rule specified; waits G8/reference + evidence manifest.
- G8: technical replicate-envelope rule specified; waits fixture qualification/reference generation.
- G9: adverse-null + stability rule specified; waits alignment metric/executor qualification.
- G11: decision law specified; exact applicability matrix waits static population/evidence registry.
- G12: mandatory claim-envelope rule specified; waits static support registry.
- S1/S2: adverse-null recurrence/stability rules specified; wait common engine qualification.
- R1: adverse-null relational recurrence rule specified; waits common/specialized engine qualification.
- R4: noise-relative increment rule specified; waits C1 qualification + references.
- C6 increment: two-constituent noise-relative increment rule specified; waits C1+C3 qualification + references.
- C4 increment: C4-vs-C6 noise-relative increment rule specified; waits C6 qualification + references.

No item is left as a generic 'we do not know what to do.' Remaining blockers are explicit dependencies or executor qualifications that occur before real outcome adjudication.

Authority remains unchanged:
`OUTCOMES_UNREAD__REAL_TD_OFF__TARGET_NONE__REPRESENTATION_NONE__STAGE4_OFF__TRAINING_OFF`
