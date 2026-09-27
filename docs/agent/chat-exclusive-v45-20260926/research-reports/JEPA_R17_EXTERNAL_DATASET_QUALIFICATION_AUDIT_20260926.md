# R17 — Recovering and auditing the external-validation workstream

**Scope:** Independent read of connected GitHub PR #181 at `b1a6909dbefa040387bc48c0ae9e9b0116d81ed1`, against PR #164, PR #175, and independently available primary publications/GEO records. Local R17 control software is *a development-stage custody gate*, not a data- or training-authority issuer. **No biological outcome matrix or participant data were obtained or inspected here.**

## Findings that materially alter the handoff

1. **The dataset search was already underway, not wholly abandoned.** Claude's PR #181 contains a substantial external dataset registry and GEO metadata cache, but the branch is formally `INCOMPLETE_STOPPED` and explicitly forbids citing its numbers as qualified results. Reuse the producer and compact metadata; audit the output, do not redo the entire search.
2. **ROSMAP 2025 is an additional controlled-access resource.** The Xiong/Liu multiregion paper describes 111 total aged/AD individuals and supplies snATAC and multiome access at Synapse `syn66271521` and `syn66271522`. The earlier PFC study `syn52293417` is included in the newer study; it is not independent replication. A data-use agreement is required to access participant-level data. Crucially, `111` is the **study-level total**, not an authenticated count of donors with usable *paired microglial* RNA and ATAC. PR #181 overstates this distinction when presenting 111 as the paired count. Do not infer any zero donor overlap with FULL104 merely from cohort institution names; an independent donor-identity/lineage review is pending.
3. **Anderson GSE214637/GSE214979:** Related superseries/data subseries, not two replications. Reported 15 donors (7 AD, 8 control), same-nucleus RNA/ATAC. Actual microglial donor support, exact processed matrices and prior project exposure remain unaudited. PR #181 records a very large supplementary directory total (~66 GB, rounded; not a required single download). Individual processed RNA/ATAC matrix and cell metadata can make a bounded pilot materially cheaper than raw fragments. Do not call 20 paired libraries 20 independent donors.
4. **GSE272082:** Primary GEO record confirms four early-onset AD patients and five controls, PFC/EC/HIP regions and same-nucleus multiome. The series currently displays 42 GSMs and an additional NIH30 replicate, but these do not increase the nine independent human donors. Small per-sample filtered 10X feature-barcode HDF5 files are deposited alongside huge ATAC fragments: authenticate only what is necessary for a donor and microglia feasibility census, without using ATAC peak observations for model design.
5. **Morabito internal discrepancy:** PR #164's authenticated Lane D reports 18 *shared microglial* donors, while incomplete PR #181 reports 19 shared sample labels at the whole-series level. These may both be true (whole-tissue shared labels versus subset usable microglia), but they must be reconciled by an exact join before any sample-size/power calculation. PR #175 has already inspected same-assay observed ATAC accessibility summaries; the external outcome is NOT fully pristine. Update the contamination register before evaluating anything.

## Designed and physically tested R17 safeguard

`external_benchmark_gate_v1.py` checks typed identity and evidence assertions, outcome-exposure and DUA constraints, separate study-wide/paired/microglial donor counts and non-independence of historical subseries. All four tracked datasets fail closed because the exact paired microglial donor count, per-file bytes and independently approved evaluation protocol have **not** been established in this environment. The code never treats a study-wide headcount as proof of a paired microglial denominator. Tested 15 cases including fake donor counts, same-cohort rebranding, lost outcome quarantine, unsupported string attestations, duplicate accessions and controlled-access bypass. This is a preparatory declaration validator: booleans and typed receipts do **not** authenticate remote data on their own. Physical source reconciliation and human governance are separate.

## Concrete parallel handoff to Claude

- **Lane E1 (open paired pilot):** authenticate the Anderson processed H5 and cell metadata by byte count/SHA; read donor/sample/assay key, then report *unique paired microglial donor IDs*, per-donor usable nuclei, query-program measurement support, and whether RNA/ATAC were physically linked by barcode. Keep observed ATAC accessibilities sealed. Repeat a bounded equivalent census for GSE272082, counting donors rather than brain regions or paired modality GSMs. First produce a file manifest rather than pulling every fragment archive.
- **Lane E2 (controlled independent cohort):** request/verify authorized ROSMAP access through the user's institutional DUA; public metadata alone can establish study design but **not** exact paired microglia donor eligibility. Determine assay-specific donor intersection and whether any previous PFC donor/reused files overlap, and audit overlap against FULL104 source populations before independent-replication claims. Do not treat the predecessor PFC cohort as replication.
- **Lane E3 (Morabito salvage):** exact 18-versus-19 join, PR175 exposure register revision and outcome-blind preregistration. Distinguish genome annotation availability from observed ATAC availability. Match only donor-level pseudobulk, never pretend separate nuclei are paired.
- **Lane E4 (pre-registered evaluation):** freeze one primary query-specific biological endpoint and one incremental full-permitted-RNA comparator; reserve ATAC outcomes until eligibility, donor support, power and false-control ability are established. Never choose genes or thresholds using observed ATAC accessibility from the evaluation cohort.

**Status:** R17 source/metadata reconnaissance + executable contract; *no* actual paired-microglial census from new external files; *no* biological outcome scored; *no* production code or branch mutated; `TRAINING=OFF`.

## Source links

- [Claude's unfinished external registry, PR #181](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/181)
- [Lane D original Morabito audit, PR #164](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/164)
- [Agent 2 coverage and ATAC aggregate exposure, PR #175](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/175)
- [Xiong/Liu 2025 multiregion ROSMAP paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12573303/)
- [2025 multiregion controlled multiome](https://www.synapse.org/Synapse:syn66271522)
- [GSE214979](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE214979)
- [GSE272082](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE272082)
