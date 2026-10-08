# V59 — external cis-map provenance matrix

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
PR #195 head `7b5860b3`. `TRAINING=OFF`. `TD60=BLOCKED`.
No molecular regulatory outcome opened. No target-gene overlap was computed for
any candidate.**

## The rubric, frozen before scoring

Scored on **structural and provenance facts only**. No criterion references
overlap with our target genes, program genes, Stage75F edges, or any observed
correspondence in a confirmation cohort. Ranking by overlap would spend the
target to choose the answer key.

| # | criterion | why it is structural |
|---|---|---|
| P1 | source-cohort independence from FULL104 / Morabito / GSE214979 / GSE272082 | a property of donor provenance |
| P2 | microglial specificity | a property of the assayed population |
| P3 | donor count | a count |
| P4 | **is RNA used to define the links?** | a property of the construction procedure |
| P5 | **does enhancer→gene direction come from contact or perturbation, or from covariance?** | a property of the estimator |
| P6 | did disease labels enter *object construction* (not downstream analysis)? | a property of the pipeline |
| P7 | possible donor/cohort overlap with our four sources | provenance |
| P8 | **does instantiating the map require one of our confirmation datasets?** | a dependency fact |
| P9 | which nuisance class remains shared after adoption | a structural statement |

P4, P5 and P8 are the load-bearing ones. P5 matters because a covariance-defined
link inherits exactly the circularity V50 was criticised for: a map built from
RNA↔ATAC covariance cannot test whether RNA↔ATAC covariance is biological. P8
matters because a pretrained model applied to our own ATAC yields a map that is
**not** external, however external the model was.

## The distinction that organises the whole field

**Method externality and substrate externality are separate axes.** A map is
external only if *both* hold.

```
pretrained method  x  OUR confirmation ATAC      -> NOT external
pretrained method  x  external ATAC/contact      -> external
published map from an external cohort            -> external
```

This is why "apply scE2G to our data" is not a shortcut to independence, and why
a published map from someone else's donors can be.

## The matrix

| | **Kosoy/Fullard microglia regulome** | **Corces adult brain** | **ABC (method)** | **scE2G (method)** |
|---|---|---|---|---|
| P1 cohort independence | external cohort; **overlap unverified** | external; cognitively healthy | n/a — a method | n/a — a method |
| P2 microglial specificity | **primary human microglia** | brain-wide scATAC; not microglia-specific E→G | inherits substrate | inherits substrate |
| P3 donors | **150** | adult human brain atlas | 131 cell types/tissues (maps) | n/a |
| P4 RNA used to define links | **No** — links from contact × accessibility | No | No | **No** (ATAC-only formulation) |
| P5 link direction from | **ABC: Hi-C contact × enhancer activity in OCRs** | contact/architecture substrate | contact × activity, validated vs **>3,500 CRISPR-tested E–G pairs** | trained vs **>10,000 CRISPR-evaluated element–gene pairs** |
| P6 disease labels in construction | **needs audit** — AD fine-mapping is downstream (21 loci, 18 refined to one gene, incl. KCNN4/FIBP/LRRC25), but whether the distributed map is genome-wide or AD-locus-restricted is unresolved | No — cognitively healthy donors | No | No |
| P7 donor overlap risk | **unverified**; different brain bank lineage from our four, but not confirmed | low | n/a | n/a |
| P8 needs our data to instantiate | **No** | No | yes — needs a substrate | **yes — and if that substrate is ours, the map is not external** |
| P9 nuisance still shared | postmortem human brain tissue; reference genome/annotation; sorted-population vs single-nucleus assay differences | as Kosoy, plus no microglial resolution | — | — |

## Scientific decision

**Outcome 2 — a partially external object exists — pending two provenance checks
that could move it to Outcome 1.**

The leading candidate is the **Kosoy/Fullard microglia regulome**, and the reason
is structural rather than biological: it is already the composition this problem
needs — an **externally validated method (ABC) applied to an external,
microglia-specific, 150-donor substrate**, with links defined by **Hi-C contact ×
accessibility, not by RNA covariance**. It therefore satisfies P4, P5 and P8
simultaneously, which none of the alternatives does on its own.

**Two checks decide between Outcome 1 and Outcome 2, and both are
provenance-only:**

1. **Donor/cohort overlap (P7).** The map's donor provenance must be established
   against SEA-AD, Morabito, GSE214979 and GSE272082. Unverified today. Note the
   existing precedent: GSE214979 already carries
   `UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP` with Morabito over donors
   1224/1230/1238, so this project has already seen "two external datasets" fail
   to be mutually independent.
2. **Disease-derived feature selection (P6).** The paper's headline is AD
   fine-mapping. If the *distributed* E–P map is genome-wide, disease labels
   entered only downstream analysis and construction is clean. If the distributed
   product is restricted to AD risk loci, then disease selection **is** in the
   object and it drops to Outcome 2 with that dependency named.

**If both clear → Outcome 1:** freeze Kosoy as the external cis object and design
the next synthetic gate around exactly its information structure — contact-based,
microglia-specific, RNA-free links at 150-donor scale.

**If either fails → Outcome 2:** state the residual dependency explicitly and
build the nuisance class around it. A disease-restricted map means the nuisance
class must include disease-associated locus selection; an overlapping cohort
means the agreement claim must exclude the overlapping donors or carry the
caveat, exactly as the UCI rule already requires.

**Corces** is not a cis object on its own — it is a substrate. Its correct role
is as an **externally frozen accessibility/architecture layer** that ABC or scE2G
could be instantiated on to produce a map touching neither our RNA nor our
confirmation ATAC. That composition is worth holding in reserve if Kosoy fails
its provenance checks.

**ABC and scE2G are methods, not objects.** Their CRISPR-validated pedigrees
(>3,500 and >10,000 element–gene pairs) validate *the method*, not any particular
microglial map, and neither original validation was in human microglia. Adopting
either does not import that validation into our setting.

## What this does not establish

Nothing here says a cis object will identify biology. **My own cross-modal cis
probe remains RED** (`claude/laneB-crossmodal-20260928` @ `671ccb3b`): its
planted positive cancels and the statistic currently favours the technical arm.
And the synthetic gate has failed at every scale tested — V54 `-0.0143`, V57's
192-seed n=18 `-0.0287`, relational variants `-0.176` and `-0.233`.

An external map changes the **information structure** available to a gate. It
does not make a failing gate pass. If a new prospectively frozen gate still fails
at n=18 with Kosoy's structure supplied, that is **Outcome 3** — record it and do
not spend Morabito.

## Explicitly not done

No candidate was scored on overlap with target genes, program genes or Stage75F
edges. No confirmation-cohort correspondence was inspected. The Kosoy
construction procedure was established from published description; the
distributed artifact itself has **not** been downloaded or audited, and P6/P7
remain open precisely because that audit has not run.
