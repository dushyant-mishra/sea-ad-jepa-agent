# V72 independent audit — Macha SCENIC+ head f8dc4935 — 2026-10-02

## Scope

Audited exact head:

`f8dc493516db079fd529e4a69f370d8b9db0dfad`

Primary files inspected:

- `scripts/v69/routeb_extract_pseudobulk_fragments_v1.py`
- `scripts/v69/routeb_call_peaks_and_consensus_v1.py`
- `scripts/v69/v69_barcode_identity.py`
- `scripts/v69/compare_bench_runs_v1.py`
- `results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json`
- `results/v64/V69_CISTARGET_TOOL_PIN_HAZARD_AND_SUCCESSOR_RECIPE_V1.json`

External implementation references checked:

- pycisTopic `pseudobulk_peak_calling.py`
- scatac_fragment_tools fragment splitter
- MACS BEDPE format documentation

This audit does not claim that Route-B pseudobulks or consensus peaks have been executed.

## Verified findings

### SCA1 — barcode suffix is not a donor key — VERIFIED

The shared guard correctly encodes the measured fact that suffixes 5, 6 and 7 span more than one donor.

The producer uses full-barcode metadata mappings rather than suffix inference.

### SCA2 — three-column pseudobulk BED is consistent with MACS BEDPE semantics — NO FINDING

An apparent concern was that the source 10x fragment record carries a fifth score/read-support column while Macha writes only chrom/start/end to pseudobulk BED.

pycisTopic's splitter preserves the fragment record columns, but MACS BEDPE itself is defined as a three-column fragment format: chromosome, leftmost position and rightmost position. Therefore dropping the extra columns for the BEDPE file is not, by itself, a divergence in MACS peak-calling semantics.

This was checked rather than assumed and is recorded as **examined, no finding**.

### SCA3 — storage comparator's artifact-kind repair is conceptually correct — VERIFIED

The comparator now strips the run-id prefix before comparing output artifact kinds and separately fails on collisions after stripping. This repairs the earlier impossible-to-pass filename-set gate without making genuine output-set differences invisible.

### SCA4 — seed/thread/output-equality boundary is explicit — VERIFIED AT RECEIPT LEVEL

The speed receipt clearly separates:

- ranking RNG seed fix;
- BLAS thread pinning;
- score-output equivalence;
- C: vs D: storage equivalence;
- union score reuse;
- still-unmeasured worker count/shard size at the audited head.

It correctly does not authorize a full custom cisTarget build at this head.

## New audit findings

### SCA5 — HIGH: the Route-B extractor does not verify the fragment SHA-256 before use

The acquisition receipt carries a fragment digest, and the extractor has a `sha256_file()` helper, but the execution gate checks only:

`fragments.stat().st_size == acq["local_bytes"]`

A different 63.6-GB file with exactly the same byte length would pass the input gate.

The user independently re-hashed the real fragment file in the execution chat and obtained the expected SHA-256. That manual verification is useful evidence, but it is not an executable custody guarantee in the producer.

#### Required repair

Before the extraction result can become a frozen Route-B authority, bind the actual fragment bytes to the acquisition receipt.

At minimum:

- require the acquisition receipt to contain SHA-256;
- recompute SHA-256 of the file used, or use a provably same-byte full-scan receipt whose binding to the current file is itself verified;
- fail closed on digest mismatch;
- write the verified digest into the pseudobulk receipt.

For a 63.6-GB file, avoid an unnecessary extra pass if possible by engineering one authenticated streaming path, but do not substitute file size for identity.

Status: **OPEN — custody defect blocks treating the pseudobulk producer as fully qualified.**

### SCA6 — HIGH: conflicting duplicate barcode rows are silently collapsed before the guard

The producer constructs mappings using:

`dict(zip(bc["barcode"], bc["donor"]))`

and similarly for subcluster.

Python dictionaries cannot retain duplicate keys. If the source table contains two rows for the same barcode with conflicting donors, the later row silently replaces the earlier one.

The shared guard then iterates the already-collapsed dictionary and contains logic intended to detect one barcode mapping to multiple donors. That branch can never detect a duplicate that was lost during `dict(...)` construction.

This is a classic check-after-normalisation false green.

#### Required repair

Audit the dataframe **before** converting it to dictionaries:

- duplicate full barcode rows;
- conflicting donor values per barcode;
- conflicting subcluster values per barcode;
- exact duplicate rows, with an explicit policy rather than silent collapse.

Only after those checks pass should the barcode→donor and barcode→subcluster dictionaries be created.

Add a behavioral test with one duplicated barcode mapped to two donors and prove the producer fails.

Status: **OPEN — donor-identity guard is incomplete in the current producer.**

### SCA7 — MEDIUM/HIGH: mutable path targets from cohort/QC receipts are not content-bound in the extractor

The producer reads:

- the cohort barcode table from a path stored in the cohort receipt;
- the per-barcode QC table from a path stored in the QC receipt.

It does not independently verify those table bytes against digests before using them, and the pseudobulk receipt does not currently bind their content hashes.

A receipt path is not a content identity. A file can change while retaining the same path.

#### Required repair

Where upstream receipts expose content digests, require and verify them.

If the upstream receipts currently lack digests, add successor receipts or a binding manifest before Route-B execution authority is frozen.

The pseudobulk receipt should record:

- cohort barcode-table SHA-256;
- QC table SHA-256;
- fragment SHA-256;
- producer SHA-256.

Status: **OPEN.**

### SCA8 — MEDIUM: empty consensus output is not handled as a structured fail-closed state

The consensus producer assumes `cdf` is nonempty and later calls `widths.min()` and `widths.max()`.

If peak calling produces no consensus regions, execution is likely to raise an ordinary pandas/numpy error rather than write the structured FAIL receipt expected from the producer.

#### Required repair

After `get_consensus_peaks`, explicitly test for zero rows and raise a named `FailClosed` status before computing width summaries.

Add a fixture where all pseudobulk peak sets are empty.

Status: **OPEN but not a current biological result.**

### SCA9 — blacklist decision is now prospectively resolved on Sol V72

The audited Macha head correctly refused to choose a blacklist silently.

Sol V72 now adds a prospective amendment selecting ENCODE's released preferred-default GRCh38 unified blacklist:

- accession `ENCFF356LFX`
- dataset `ENCSR636HFF`
- portal MD5 `393688b4f06c9ce26165d47433dd8c37`

The decision is made before a real Route-B consensus result is inspected.

Macha should not simply accept a filepath string. The producer should verify the pinned resource identity/digest and record blacklist attrition.

## Build recipe audit

Macha's finding that the existing Dockerfile clones `create_cisTarget_databases` from unpinned `master` is confirmed.

Sol V72 adds `docker/scenicplus/Dockerfile.successor_pinned` for future rebuilds only. It deliberately does not replace the recipe corresponding to the already-validated image.

The successor recipe:

- requires an explicit immutable cisTarget commit;
- verifies key tool-file SHA-256 values against the current validated image;
- requires caller-supplied digests for cbust/liftOver/bigWigAverageOverBed;
- records build binding inside the image.

It remains intentionally non-buildable until an exact upstream commit matching the current content and downloaded-tool digests are supplied. That is safer than guessing.

## Required Macha actions before real Route-B pseudobulk extraction is frozen

1. SHA-bind the fragments file, not just its length.
2. validate duplicate/conflicting barcode rows before dict conversion.
3. SHA-bind cohort and QC table bytes.
4. incorporate the prospectively pinned ENCFF356LFX blacklist and verify its bytes.
5. add structured empty-consensus failure.
6. add behavioral tests for all of the above.
7. preserve the current unexecuted producer as history rather than silently overwriting its provenance.

## Governance

- no broad eRegulon network is yet qualified at this audited head;
- Stage 4 remains NOT AUTHORIZED;
- Morabito remains PROTECTED;
- training remains OFF.
