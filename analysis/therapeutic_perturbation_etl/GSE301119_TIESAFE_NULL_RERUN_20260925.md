# GSE301119 tie-safe rerun — the negative-control finding survives the correction

**Verdict: good news for the finding, bad news for the dataset.** PR #127's
tie-safe tail algorithm was a correct and necessary fix, and I ran it because it
threatened a number I had already published. It did not overturn it. The
negative control still fails, and the tail-recurrence agreement that looked
suspicious is real rather than an artifact of arbitrary tie-breaking.

## Why this rerun happened

My earlier two-arm run used `np.argpartition` to pick the top/bottom 25 features.
That breaks ties arbitrarily. In a matrix where thousands of genes have an effect
of exactly zero, arbitrary tie-breaking can place zero-effect genes into a
"most extreme" tail and fabricate recurrent markers.

I had reported observed down-tail recurrence of **17.69 %** against a null of
**17.69 %** and argued it was a genuine coincidence of two independent
computations. A collapse check confirmed the two were not the same array (118
distinct null values, correlation 0.548). **But that check could not rule out
that both paths were driven by the same tie-breaking artifact** — which would
make them share a mechanism rather than agree independently. That is the question
this rerun answers.

## Provenance

```
protocol   PR #127 head 1317d54d6ab6 (review/pr125-tie-aware-null-and-runbook)
           clean worktree, verified
input      D:/jepa_perturb_outputs_20260923/gse301119_neutral_export
cert       NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json, produced by
           certify_gse301119_neutral_identity_v2.R on this machine
           both modalities: ALL_FOUR_NEUTRAL_EXPORT_FILES_RECONSTRUCTED_
                            BYTE_IDENTICAL_FROM_ORIGINAL_RDS
           v1_export_receipt_sha256 2cda0294... matches the export receipt
output     gse301119_null_tiesafe_v1/GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1.json
           6,663,276 bytes
           sha256 1a649776b97dc93b4ddf486a0e43c59d9a3e77ff3aa398aca54abbfc17f31e4c
```

The mandatory source-identity certificate and its prerequisites were verified
**before** the rerun, as the runbook requires. The certifier rebuilds all four
neutral export files from the authenticated RDS and demands exact byte agreement;
it is not a metadata-hash comparison.

## What the fix changed, and what it did not

**It did not touch the estimator.** Effects and null medians are **bit-identical**
across the two runs — `max|delta| = 0.000e+00` on observed log2FC, on the
cell-sampling null median and on the depth-only null median, over all 5,663
sentinel observations. That is the control that proves the fix altered only tail
membership.

**It changed tail membership slightly.** 13 of 5,663 observed booleans and 411 of
5,663 null fractions moved — so ties were a real but minor effect here, not a
dominant one.

| | tie-unsafe | **tie-safe** |
|---|---|---|
| observed top-25 **down** | 17.69 % | **17.4642 %** (989/5663) |
| null top-25 **down** | 17.69 % | **17.4470 %** |
| difference | 7.24e-05 | **1.726e-04** |
| observed top-25 **up** | 3.62 % | **3.6023 %** (204/5663) |
| null top-25 **up** | 4.83 % | **4.8036 %** |

**The finding stands.** Under a rule that makes zero-effect genes ineligible and
refuses to assign tied boundary features at all, the null still reproduces the
observed down-tail recurrence rate to four significant figures, and the up-tail
rate is still **higher under the null than under the real data**. The collapse
re-check also still passes: 118 distinct null values, 3,023 strictly interior,
arrays not identical, correlation 0.5496.

## The core verdict is unchanged

| | observed | cell-sampling null | depth-only null |
|---|---|---|---|
| median log2FC | −1.3446 | **−1.5040** | −0.0461 |
| exceedance at or above 0.50 | — | **72.8 %** | 26.4 % |

The negative control fails for the same reason as before: NT-versus-NT
comparisons produce effects the same size and direction as real perturbations.
The GSE301119 CPM-based effect sizes remain on scientific hold and must not be
promoted to JEPA targets or benchmark truth.

## Self-audit

**S13 — raised by me, and now resolved against my own concern.** I flagged that
my published recurrence numbers might be a shared tie-breaking artifact and that
my collapse check was structurally unable to detect it. The rerun shows they were
not. The right conclusion is that the original check was **insufficient**, not
that it was wrong: it ruled out array aliasing but not mechanism-sharing, and I
said so before running the test rather than after seeing the result.

The superseded runs, both of which must not be cited:
* single-arm at head `6cd4424b`, 4,149,646 B, `5ff0e7b7…`;
* two-arm tie-unsafe at head `5260e70c`, 6,663,852 B, `4155670b…`.

The current result is the tie-safe run at PR #127 head `1317d54d6ab6`.

## Status

```
COMPLETED_AND_PHYSICALLY_EXECUTED : identity certification + tie-safe two-arm null
INDEPENDENTLY_REPRODUCED          : not claimed - same author, corrected protocol
DEVELOPMENT_RESULT                : negative control FAILS; effects stay on hold
SCIENTIFICALLY_QUALIFIED          : none
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
