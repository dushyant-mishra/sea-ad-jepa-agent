# V59 — Kosoy/Fullard provenance checks 1 and 2

> ## SUPERSEDED AS A QUALIFICATION PATH — 2026-09-28
>
> **No institutional DUA will be pursued.** Both remaining checks are therefore
> reclassified `BLOCKED_BY_CONTROLLED_ACCESS__OUT_OF_SCOPE_FOR_THIS_PROJECT`:
>
> - donor identity crosswalk — needed portal access
> - distributed enhancer–gene artifact inspection — needed portal access
>
> **FreshMicro/Kosoy is demoted to published/supporting evidence only and must
> not become a load-bearing qualification dependency.** Outcome 2 was conditional
> on those two checks; they are now closed-unresolvable rather than open, so Kosoy
> cannot reach Outcome 1 and is not eligible as *the* frozen external cis object.
>
> Everything below remains accurate as public provenance and is preserved
> unedited. None of it depended on controlled access. The ROS/MAP-to-ROSMAP
> mutual-exclusivity constraint in particular still stands.

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`3c0f915cf1a1e827b24345f812d3e5a3524613cd`. `TRAINING=OFF`. `TD60=BLOCKED`.**

**No target-gene overlap, program-gene overlap, Stage75F-edge overlap or
confirmation-cohort correspondence was computed. Provenance and construction
facts only. No molecular regulatory outcome opened.**

Source for both checks: the open-access paper record
([PMC9388367](https://pmc.ncbi.nlm.nih.gov/articles/PMC9388367/),
*Nat Genet* 2022), read directly rather than from summaries.

---

## Decision: **OUTCOME 2**

Check 2 clears. Check 1 does **not** — it is *unresolved*, not failed. Under the
frozen rule, either dependency remaining means Outcome 2: adopt the object and
carry the dependency explicitly into the nuisance class.

---

## CHECK 2 — distributed-object scope: **CLEAR**

**Verdict: genome-wide, filtered only by generic technical criteria.**

| property | finding |
|---|---|
| scope | **24,497 E–P interactions across 9,890 unique genes**, full genome |
| construction | **ABC framework**: Hi-C-derived contact frequency × enhancer activity in open chromatin regions |
| contact input | microglia Hi-C, 19 technical replicates, 5 donors |
| activity input | ATAC-seq (this study) + published H3K27ac ChIP-seq |
| **is RNA used to define links?** | **No.** No RNA covariance enters link construction. |
| thresholds | ABC score ≥ **0.02**, **5 Mb** window around each TSS — the method defaults |
| disease involvement | **post-hoc only.** AD variant overlap was analysed by colocalisation *after* the map was built |

This is the property that matters most. A map built from **contact × accessibility**
does not inherit the circularity that a covariance-defined map would: it cannot
be accused of testing RNA↔ATAC covariance using RNA↔ATAC covariance. And because
AD enters only downstream, disease labels are **not** inside object construction.

**One qualification that belongs in the nuisance class, not in the verdict.** The
150 donors include "both AD and healthy aged donors" with no quantitative
breakdown given. So while disease was not a *selection* criterion, the
accessibility substrate is measured in a mixed AD/control population and the
activity weights reflect that. That is disease-*influenced measurement*, not
disease-derived feature selection — a weaker thing, but it must be named.

---

## CHECK 1 — cohort independence: **UNRESOLVED AT DONOR LEVEL**

**150 donors = 27 biopsies + 123 autopsies.** Named sources, verbatim from the
methods:

- **Rush University Medical Center / Rush Alzheimer's Disease Center (RADC),
  Chicago** — supplying the **Religious Orders Study (ROS)** and **Memory and
  Aging Project (MAP)** cohorts
- **Mount Sinai / JJ Peters VA Medical Center NIH Brain and Tissue Repository
  (NBTR), Bronx, NY**
- **Mount Sinai School of Medicine** — Living Brain Project biopsies

Against our confirmation sources:

| our source | institution | named in Kosoy? |
|---|---|---|
| FULL104 / SEA-AD | Allen Institute + University of Washington ADRC | no |
| Morabito GSE174367 | UC Irvine | no |
| GSE214979 | UCSF, **plus UCI-derived donors 1224/1230/1238** | no |
| GSE272082 | NIH NeuroBioBank + UTHealth Houston (PR #182) | no |

**Classification: not "proven disjoint".** No named institution is shared with
any of the four. But institution-level non-overlap is all the public record
supports, and the reason is specific rather than vague: **Kosoy has no NCBI
deposit at all** — searched and confirmed 0 hits across GEO, BioProject and SRA
— so there is no public accession layer to join through, and donor identifiers
live behind the AD Knowledge Portal under managed access. The full
layer-by-layer search is in
`results/v59/V59_DONOR_IDENTITY_EVIDENCE_TABLE_V1.json`.

**Why institution-level is not sufficient here, and this project already knows
it.** GSE214979 is deposited as a UCSF study and nonetheless contains UCI-derived
donors 1224/1230/1238 — which is why R3 carries
`UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP`. Institution-of-deposit is not
institution-of-donor. Applying the standard consistently means Kosoy gets the
same treatment: three named sources, none shared with our three established
cohorts, and **no donor-source chain**.

### The forward risk this check surfaced, which is the more important finding

**Kosoy draws from ROS/MAP — the ROSMAP cohort family.** The project's own
candidate inventory (V49/PR #188) lists **ROSMAP 2025 multiregion Multiome,
`syn66271521` / `syn66271522`**, as a controlled-access acquisition candidate.

If ROSMAP is ever adopted as a confirmation cohort, it would **overlap Kosoy at
the donor level by construction**, and any Kosoy-defined object would stop being
external to it. This is not a hypothetical: ROSMAP sits in the acquisition
manifest today.

**Standing constraint to record now, before either is adopted:**
> Kosoy-derived cis objects and ROSMAP-derived confirmation are **mutually
> exclusive** absent a resolved donor-level crosswalk. Choosing one forecloses
> the other.

---

## What Outcome 2 requires us to carry

1. **Unresolved donor-level overlap** with all four confirmation sources. Any
   agreement claim must state this, exactly as the UCI rule already requires for
   GSE214979 versus Morabito.
2. **ROSMAP mutual exclusivity**, as above.
3. **Mixed AD/control accessibility substrate** — activity weights come from a
   population including AD donors.
4. **Assay-format difference** — Kosoy profiles *sorted primary microglia*; our
   confirmation cohorts are *single-nucleus*. This shares no nuisance with them,
   which is good for independence, but it means the map's accessibility
   distribution is not the one our data is drawn from.

## What would move this to Outcome 1

A donor-level crosswalk between the AD Knowledge Portal Kosoy manifest
(`syn26207321`) and the donor manifests of SEA-AD, Morabito, GSE214979 and
GSE272082. That requires portal access and is a provenance task, not a scientific
one. Until it exists, **Outcome 2 stands** — and Outcome 2 is workable: the
dependency is nameable and can be built into the nuisance class rather than
silently assumed away.

## WITHDRAWN — my GSE272082 speculation was wrong

An earlier version of this section speculated that GSE272082 might be a
cerebellum study with 17 donors, and separately my evidence table stated its
institution, donor count and tissue were "not established in this project".

**Both were wrong, and the second contradicted project history.** PR #182 had
already reconstructed the cohort, and I verified it against
`results/lane_pm/lane_pm_gse272082_donor_reconstruction_v1.csv` before
correcting:

- **9 donors** — 4 sEOAD, 5 control
- **NIH NeuroBioBank** (`NIH*` libraries) and **UTHealth Houston** (`UT*`)
- **Cortical**: PFC n=9, EC n=6, HIP n=5 — *not* cerebellum
- Contact institute: University of Texas Health Science Center at Houston;
  consent obtained by UTHealth

The project brief's "n=9 donors" was correct and my doubt was unfounded. What
*does* remain open is molecular/cell-level authentication and — for the overlap
question specifically — any public identity bridge to Kosoy. So the pair stays
**UNRESOLVED for want of a shared key, not for want of cohort facts**, which is
a different and much narrower statement.

---

## Self-audit

**Starting SHA** `3c0f915cf1a1e827b24345f812d3e5a3524613cd`; **ending SHA** in the
commit. **Branch/worktree** `claude/v59-r3-audit-and-external-cis-20260928` in
`D:/jepa_wt_v59_20260928`. **Changed files:** this document only — class **docs**.

**External sources consulted:** the Kosoy paper open-access record (PMC9388367),
plus web search for the GSE272082 accession. **Access class:** `OPEN_PUBLIC` for
the paper text; `CONTROLLED_ACCESS` for the underlying AD Knowledge Portal data,
which I did **not** request and did **not** download.

**Molecular biological outcome opened: NO. Protected pathology opened: NO.**
No target-gene, program-gene or Stage75F overlap was computed for any candidate.
No confirmation-cohort correspondence inspected.

**Tests run:** none this step; no code changed. **Hosted CI:** none triggered, no
provenance claimed.

**Strongest alternative explanation for the Outcome 2 call:** that institution-level
disjointness plus the sheer size and geographic separation of the cohorts makes
donor overlap negligible in practice, and Outcome 1 is the pragmatic call. I
reject that because this project has already been caught by exactly that
reasoning once — the UCI donors inside a UCSF deposit — and the cost of being
wrong is an "independent" confirmation that is not independent.

**Strongest criticism of my own conclusion:** I read the paper record, not the
distributed artifact. My Check 2 verdict rests on the methods description of
24,497 interactions across 9,890 genes; I have **not** downloaded the Synapse
object and confirmed that the *distributed file* matches the *described* map. A
distributed product can be a filtered subset of what a paper describes. Check 2
should therefore be re-confirmed against the artifact before the object is
frozen, and until then it is "clear on the published record", not "clear on
inspection".

**What remains unknown:** donor-level overlap with all four sources; whether the
distributed Synapse artifact matches the described genome-wide map; GSE272082's
institution, donor count and tissue; and whether any of this changes the
information structure enough for a new n=18 gate to pass — which remains the
Outcome 3 risk regardless of how checks 1 and 2 resolve.
