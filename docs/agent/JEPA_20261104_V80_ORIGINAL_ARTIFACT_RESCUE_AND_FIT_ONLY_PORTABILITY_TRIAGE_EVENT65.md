# V80 original artifact rescue and bounded portability diagnosis (event65)
**2026-11-04, Sol — original bytes retrieved and SHA-verified. No controller truth opened; no world regenerated; no estimator fitted.**

## Read first — this is actual artifact recovery, not another synthetic world
I used GitHub Actions' **original** V80 producer run [38504094639](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/38504094639), not PR #534's regenerated V80 arrays or any new producer. The original archived ZIPs were downloaded into the **owner conversation's file sandbox**; three raw ZIP SHA-256 digests match the original #348 archived-artifact identities **exactly**.

| Role | Original artifact ID | Original ZIP bytes | Original ZIP SHA-256 | GitHub original expiry UTC |
|---|---:|---:|---|---|
| **FIT** | `11867590706` | 660,628 | `4cec8966cff7bdddb3640903f4525328d23ed3482e2b232ead1bc440993fca71` | 2026-11-13 03:01:56 |
| **CONTROLLER — sealed, controller-only** | `11866917064` | 6,844,053 | `184d58c6988c81f8f23597510c2113542d1fc55af04409448c14adb8892d3f46` | 2026-11-13 03:01:58 |
| **ORIGINAL RECEIPT** | `11867366245` | 1,274 | `97e264cfe76709f5098b346e56130716640e6c8ce8562974d6ab126ac82a47fe` | 2026-11-13 03:02:00 |

**Only FIT and PACKAGE RECEIPT were opened and hashed internally.** Original fit entry `fit_transport.json` is 8,935,002 bytes with SHA-256 `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`; original receipt entry `V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json` is 1,922 bytes with SHA-256 `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`. These exactly match the frozen Git #348 package claims. The original controller ZIP was **only raw-file SHA-256 hashed**; its JSON content was **not extracted, parsed, displayed, used as a source, or copied to Git**.

The owner conversation files are:
`V80-original-fit-transport-artifact.zip`, `V80-original-controller-transport-SEALED.zip`, `V80-original-receipt-artifact.zip`, `V80-original-artifacts-custody-receipt.json`.
**Important:** This is a VERIFIED RECOVERY OF ORIGINAL ZIP BYTES, **NOT** proof of long-term independently access-controlled custody. The controller archive remains an owner-only, sealed transport. Its presence in the same chat file sandbox does not establish actor segregation; transfer to a separately controlled controller store and recorded external durable receipt still require an authorized owner custodian. Do not let the fit/student lane fetch controller content merely because the owner has an original archive. Do not embed/upload raw ZIPs to repository audit docs, CI diagnostics, or public channels.

## #534 failure triaged using archived fit only, without relaxing the original identity
- #348 original frozen producer had Python **3.11.9** and NumPy **2.3.5** (`.github/workflows/v80-sparse-positive-benchmark.yml` and original receipt). #534's failed CI [run 41665058401](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41665058401) **also used exactly Python 3.11.9 / NumPy 2.3.5**. The suggestion to fix this by merely pinning NumPy 2.3.5 is therefore **not supported**.
- #534 current-run V80 benchmark SHA: `faf80c897ab6f568ec2ca243471b1e3329950ce86e9ab69b7b5c3e3891c7b769`, vs original pinned `16a08b29c7e083377f4dde6e16ac6d55a3358ed45475c74161fbaba29a4afc38`; #534 fit transport digest reports `b33e72a6852b9ec5696d6184f05f2b448419e22242c8535147ab7dd866c361ab`, vs original fit `77f89e8336ec2a2d0184abbd81bfd7d6ff04f2dc57aa80891b6d8021869737b3`. **The #534 failure is real and fail-closed.**
- Direct comparison of all **eight frozen original fit** `support` and `design_matrix` array `.tobytes()` SHA-256 values (NumPy bool and float64 respectively) against #534's **CI-reported full-world support and design digests** produced **8/8 exact matches in both categories**. This controls for gross support/donor/design drift. It does **not** establish that observed outcomes, latent probabilities, controller truth, or benchmark digest match. In fact, overall identity differs. Why later numerical/stochastic arrays diverge is **not yet proven**; CPU numerical behavior is a possible hypothesis, not a demonstrated root cause.
- #534 generated-world V80 fit diagnostics are **not** evidence for changing the original frozen outcome arrays. The archived original fit transport is the correct non-controller side of the reference. The original #348 controller archive stays inaccessible to fit-only testing.
- Independent original V80 benchmark package remains `BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN`; original **V79 NOT_QUALIFIED** remains. Do not infer successor model qualification or count-valued CaseBundle support from V80 continuous positive outcomes.

## Remaining exact action, not another audit
1. **Owner/custodian:** put controller ZIP in an independently access-controlled *controller-only* durable store, fit ZIP + package receipt in fit-permitted original artifact store, preserve SHA/size/origin/expiry and independently verify retrieval. Conversation file copies are available now but alone do not meet separated security custody.
2. **#534 author:** keep current portability test RED rather than update the pinned V80 hash. Any future cross-host portability experiment must be its own predeclared, non-authorizing technical diagnostic, not an algorithm or world revision. Compare the original archived fit bytes; do not read controller truth in fit process. Source-level analysis of stochastic drift is optional only if decision-bearing and independently scoped; SHA/OS alone is not a fix.
3. **Do not re-run #348, regenerate V80 to replace an original artifact, change V79 selection law or proceed to training.** The original benchmark is preserved as a package regardless of a later cross-machine numerical mismatch.

**Source anchors:** [#348](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/348), [#534](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/534), #348 original [receipt](https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/e99d1f214e76a5e3911eea438c32a1e60f70754f/results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json), event64 Task4 custody, event63 original downstream no-repeat.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
