# JEPA ↔ intervention-response interface — frozen specification V1

Date: 2026-09-23
Status: **SPECIFICATION ONLY — designed, deliberately not trained, not implemented**

Versioned interface between a future **frozen** V5 representation and the measured
intervention responses produced in this lane.

---

## 0. The scientific task

```
initial cellular state  +  experimentally defined intervention  +  context
        ->  predicted post-intervention cellular state
```

Three commitments follow from that sentence and constrain everything below.

**The intervention is experimentally defined.** It is a guide, a modality, a dose
or a genotype — an object with provenance in an authenticated experimental record.
It is not a gene name someone decided to zero out.

**The response model is separate from the foundation model.** V5 supplies a
frozen representation. The intervention-response model is a distinct, separately
versioned artifact that consumes it. They are not co-trained, and no result from
one is authority for the other.

**Erasing a gene from an expression vector is not CRISPR knockdown.** This is the
load-bearing prohibition. Measured CRISPRi in this lane gives a median target
log2FC of −0.811 with 44 % of targets beyond two-fold and 17 % *not* repressed at
all — a distribution with real variance, incomplete penetrance and guide-dependent
efficiency. Setting an input coordinate to zero represents none of that. It also
ignores compensation, off-target effects and the fact that a knockdown's
downstream signature is not the arithmetic removal of the gene's own contribution.
Any component that performs input erasure and calls the result a perturbation
prediction is out of specification.

## 1. Interface boundary

```
  ┌──────────────────┐        frozen, versioned by SHA
  │   V5 encoder     │  ──►  z_state  (no gradient crosses this line)
  └──────────────────┘
            │
            ▼
  ┌──────────────────────────────────────────────┐
  │  intervention-response model  (separate)      │
  │    z_state + intervention + context           │
  │         ──► Δ̂  +  uncertainty  +  OOD        │
  └──────────────────────────────────────────────┘
```

The V5 side is consumed by content-addressed SHA. If that SHA changes, every
downstream receipt is invalid and must be reissued — the same rule the FULL104
lane applies to its heavy artifacts.

## 2. Inputs

### 2.1 `z_state` — initial cellular state
Frozen V5 embedding of the pre-intervention cell or pseudobulk unit, plus the
measurement mask that produced it. Carries the encoder SHA and the substrate SHA.

### 2.2 `intervention` — the experimentally defined object

| field | example | required |
|---|---|---|
| `modality` | `CRISPRi`, `CRISPRa`, `noncoding_CRISPRi`, `genotype`, `pharmacological` | yes |
| `target_id` | `BIN1`, `rs10792832`, `del1`, `APOE4`, `GNE317` | yes |
| `target_class` | `gene`, `noncoding_variant`, `noncoding_deletion`, `genotype`, `compound` | yes |
| `guide_id` | `BIN1_1` | where the assay defines guides |
| `dose`, `time`, `treatment_context` | | where the assay defines them |
| `engagement_measurable` | bool | yes |
| `measured_engagement` | log2FC of the target's own feature | where defined |

`target_class` is not cosmetic. GSE293118 contains 73 noncoding variants and 3
deletions whose engagement **cannot** be read from a same-named feature; the
interface must represent "engagement unavailable" as a first-class state rather
than substituting a proxy. Likewise `RPA1-SMYD4` is a read-through locus with no
single measured symbol.

### 2.3 `context`
Cell model, donor or line, batch, assay platform, and the measurement mask of the
target assay. Context is an input, not a nuisance to be averaged away: GSE301119
is primary human macrophage, GSE293118 is the HMC3 line, and a model that cannot
represent that difference cannot be evaluated on Q3 transport.

## 3. Outputs

| output | requirement |
|---|---|
| `delta_hat` | predicted expression-space shift, on the *target assay's* measured features only |
| `uncertainty` | per-feature; must widen for unseen targets and unseen contexts |
| `ood_score` | explicit out-of-distribution signal, reported with every prediction |
| `applicable_mask` | features the model declines to predict |

A prediction for an unmeasured feature is not permitted. The model returns a mask
rather than a number, for the same reason the ETL refuses to zero-fill an absent
gene: an unmeasured quantity is unknown, not zero.

## 4. Unseen perturbation targets

The interface must accept a `target_id` never seen in training and either produce
a prediction with honestly widened uncertainty or decline via `applicable_mask`.
It must not silently fall back to the mean effect while reporting the confidence
of a seen target. The baseline suite in the benchmarking specification exists
partly to detect exactly that failure.

## 5. Versioning and receipts

Every evaluation emits a receipt binding:

* V5 encoder SHA and substrate SHA;
* intervention-response model SHA;
* ETL receipt SHAs for every dataset used;
* the exposure status of each dataset at evaluation time;
* partition unit and split definition;
* baseline scores alongside model scores;
* `jepa_training_authorized: false` unless separately granted.

## 6. Explicitly out of scope for V1

* Training anything.
* Therapeutic ranking, disease-state reversal, drug-efficacy claims.
* Treating a JEPA counterfactual as a measured intervention effect.
* Merging model systems, doses, timepoints or modalities into one response space.
* Any use of FULL104 protected outcomes.

## 7. Open design questions, recorded rather than resolved

1. **Pseudobulk or single cell?** The measured effects in this lane are guide ×
   donor pseudobulk. A single-cell interface would need a defensible account of
   what a per-cell intervention effect means given incomplete penetrance.
2. **How should incomplete engagement be represented?** 17 % of CRISPRi targets
   were not repressed. Conditioning on measured engagement risks leaking the
   outcome; ignoring it models an intervention that did not occur.
3. **What is the cis-target of a noncoding element?** Required before GSE293118's
   73 variants can contribute anything beyond transcriptome-wide response.
4. **Two donors is not a donor distribution.** GSE301119 has D1 and D2 only.

These are listed because an interface that silently picks an answer to any of
them would be making a scientific choice inside an engineering artifact.

```
STATUS: SPECIFICATION_ONLY__NOT_IMPLEMENTED__NOT_TRAINED
JEPA_TRAINING=OFF · THERAPEUTIC_RANKING=OFF · PROTECTED_FULL104_OUTCOMES=UNOPENED
```
