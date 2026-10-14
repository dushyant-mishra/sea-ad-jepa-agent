# TD Real-Gate Blocker Resolution — Self-Audit V3

Status: `OUTCOME_BLIND_SELF_AUDIT__EXACT_G6_G8_ENGINEERING_LAWS_FROZEN__NO_REAL_EXECUTION_AUTHORITY`

This amendment further tightens the prospective solutions in Blocker Resolution V1 and Self-Audit V2. It is written without opening current human candidate outcomes. Where it conflicts with those documents, V3 controls.

## 1. G8 exact finite-sample technical-reference law

The calibration replicate count is not a free hyperparameter.

For a one-sided distribution-free split-conformal upper prediction bound with effective error rate `alpha_eff`, the calibration order statistic is

`r = ceil((n + 1) * (1 - alpha_eff))`.

The bound is estimable only if `r <= n`. Therefore the exact minimum calibration size is

`n_min(alpha_eff) = ceil(1 / alpha_eff - 1)`.

For the frozen G8 three-depth family `{25%, 50%, 75%}` under family alpha `0.01` and Bonferroni allocation,

`alpha_eff = 0.01 / 3`

and

`n_min = 299`

independent calibration realizations **per required donor/depth technical-reference unit**.

No smaller K may be used with a relaxed alpha. If compute/support cannot supply the required calibration resolution, G8 is `NOT_ESTIMABLE`.

The calibration and deciding displacement scores must be exchangeable under the same frozen thinning mechanism conditional on the authenticated raw-count input. This requires:

- exact nonnegative integer raw counts;
- same candidate protocol and same displacement metric;
- same depth p;
- same support/cell/donor/source/operator/address identities;
- independent deterministic seed namespaces for calibration, deciding evaluation and any null generation;
- pinned RNG implementation/environment;
- no calibration score derived from the deciding seed namespace.

The calibration bound is a **technical prediction envelope**, not a human biological effect-size threshold.

## 2. G6 exact matched diagnostic-probe family

G6 is an operational teacher-information diagnostic, not an information-theoretic proof of absence.

### 2.1 Probe family

The only allowed model is linear multi-output ridge on training-only standardized data.

For a training matrix `X` and multi-output target `Y`:

- standardize every X column using training rows only; constant columns map to zero;
- standardize every Y component using training rows only; a zero-variance required target component makes that fold `NOT_ESTIMABLE`;
- fit ridge under the normalized objective

`||Y - X B||_F^2 / n + lambda ||B||_F^2`.

The closed lambda family is exactly

`lambda_k = 2^k,  k in {-12,-11,...,12}`.

Because X is standardized and the objective is normalized by n, this family is dimensionless and shared exactly by teacher and student probes. No grid expansion, refinement, pruning or post-outcome extension is allowed.

### 2.2 Nested donor protocol

For every outer held-out donor:

1. outer training contains all other donors;
2. teacher and student use the identical outer donor split and target rows;
3. lambda is selected separately for teacher and student but with identical rights: the exact same 25-lambda family and exact same inner leave-one-donor-out folds;
4. each inner held-out donor contributes one donor-balanced mean squared error; rows/cells within a donor do not increase donor weight;
5. inner score for lambda is the arithmetic mean across inner donor MSEs;
6. choose the lambda with minimum inner score; exact ties select the **larger lambda** (more regularized / lower effective capacity);
7. refit on the complete outer-training donor set at the selected lambda;
8. evaluate one donor-balanced outer MSE on the held-out donor.

Teacher and student preprocessing, target standardization, fold identities, loss, alpha family, tie rule, library/environment and failure semantics must be identical. The only intended difference is the prospectively declared evidence matrix.

### 2.3 G6 donor contrast

With smaller loss better,

`delta_d = loss_student(d) - loss_teacher(d)`.

Positive delta means richer teacher evidence improved held-out target prediction.

A later biological G6 PASS requires the donor contrast to exceed the separately qualified refit/measurement margin when applicable.

### 2.4 Known-truth qualification required before human FAIL semantics

Before this probe can adjudicate human G6, it must pass an outcome-blind known-truth qualification suite containing at minimum:

- `TEACHER_PRIVATE_SIGNAL_PRESENT`: teacher has a planted predictive component unavailable to student; expected probe result PASS;
- `NO_TEACHER_PRIVATE_SIGNAL`: teacher and student contain the same predictive information; expected result is not PASS (FAIL or NOT_ESTIMABLE according to the exact donor test);
- `UNDERPOWERED_TEACHER_PRIVATE_SIGNAL`: positive truth with donor count below exact sign-test resolution; expected result NOT_ESTIMABLE.

If the known-truth positive world does not PASS, the probe is not qualified and no human G6 FAIL may be emitted.

Even after qualification, a human nonpositive result is interpreted only as failure to demonstrate an advantage under this frozen operational probe family. It is not a theorem that teacher-private information does not exist under every possible nonlinear decoder.

## 3. G6 compute matching

`MATCHED_COMPUTE` means matched **search rights and fitting protocol**, not equal raw FLOPs when evidence matrices have different feature counts. Both sides receive:

- the same 25 lambda candidates;
- the same outer/inner donor folds;
- one fit per lambda per inner fold;
- one outer refit at the selected lambda;
- identical preprocessing and target transformation;
- identical numeric precision and solver family.

No side may receive extra architecture search, early stopping, feature selection, nonlinear expansion or tuning budget.

## 4. Consequences for dependent gates

- G2/R4/C6/C4 may consume a qualified `U_refit`/`U_measurement` margin only when the reference metric and candidate deciding metric are identity-bound and commensurate.
- G7 may consume G8 only after the exact technical reference for the same candidate state-distance metric is qualified.
- A G8 reference from one candidate/metric cannot be copied to another merely because both are called 'distance'.

## 5. Current state

G8 is now `DESIGN_RESOLVED_READY_FOR_TDD` with an exact alpha-derived calibration law.

G6 is now `DESIGN_RESOLVED_READY_FOR_TDD` with a complete finite probe family, nested donor selection rule and known-truth qualification requirement.

Neither statement authorizes real value access or human gate execution.

Terminal:
`G6_G8_ENGINEERING_LAWS_EXACTLY_FROZEN__KNOWN_TRUTH_AND_FIXTURE_QUALIFICATION_NEXT__HUMAN_OUTCOMES_UNREAD__REAL_TD_OFF`
