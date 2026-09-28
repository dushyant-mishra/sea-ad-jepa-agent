# Lane A+F self-audit addendum

Continues the project self-audit numbering. S5, S6 and S7 are recorded in the
commit message of `9e3900eb`. This file adds the items that surfaced while
writing that commit up, plus the disclosures that belong in the record rather
than in a message body.

## S8 - an expression-derived value was displayed during exploration

While inventorying `FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz` I printed the first
twenty unique values of the array named `source_library`, before establishing
what that field is. It is **not** a library identifier. Tracing it to
`scripts/v4/foundation_materialize_discovery_expression.py` and
`scripts/v4/stage81a3_foundation_biological_state_domain_qualification.py` shows
it is the raw library **total** - the sum of counts for the nucleus - which is an
expression-derived aggregate, not identity metadata.

- What was exposed: twenty integers, unlabelled by cell, from a 187,909-row array.
- Where it went: nowhere. No value entered any Lane A or Lane F artifact, any
  join, any statistic or any commit.
- Fix: `library_size_value` is now an explicit forbidden rule in
  `laneAF_identity_firewall_v1.py` (matching `source_library`, `library_size`,
  `raw_library_total`, `n_counts`, `total_counts`), and a mutation test asserts
  the rule fires on the literal name `source_library`.
- Status: disclosed, not concealed. The honest description is that the field was
  read before it was understood, which is the failure mode; the firewall rule now
  makes the same mistake impossible to repeat inside this lane.

## S9 - a scratchpad smoke run exists and is not evidence

A single-region smoke test was run to
`.../scratchpad/smoke_lec` before the production run. No number in any Lane A or
Lane F artifact, or in the commit message, comes from it. Every reported count
comes from
`D:/jepa_v5_outputs_20260925/out_laneAF-seaad-linkage/laneA_assay_origin_v1/`
and `.../laneF_feasibility_v1/`, whose SHA-256 values are recorded in
`LANEAF_OUTPUT_SHA256_MANIFEST.csv`.

## S10 - the MTG pairing shortfall is explained but not established

Within MTG, FULL104 holds 71,969 Multiome-GEX nuclei and 66,288 of them pair
exactly, leaving 5,681 unpaired. The leading explanation is QC attrition: the
local ATAC object is the `final-nuclei` release, so a Multiome nucleus whose ATAC
side failed ATAC QC has no row there. The symmetry is consistent with this -
138,118 ATAC Multiome nuclei intersect 133,084 MTG RNA Multiome nuclei, leaving
5,034 ATAC nuclei with no RNA counterpart either.

This is consistent with QC attrition; it does not demonstrate it. Demonstrating
it needs the `SEAAD_MTG_ATACseq_all-nuclei.2024-12-06.h5ad` object, which is
OPEN_PUBLIC but not local and was not downloaded. Until then the 5,681 are
reported as unmatched, with the cause recorded as unestablished.

## What was examined and found clean

- Every obs column read from every h5ad was checked against the firewall before
  the read, and the set is closed: `exp_component_name` / `index`, `method`,
  `library_prep`, `Donor ID`, `Brain Region`.
- The paired-cell export header was passed through `assert_identity_only` before
  the file was opened for writing.
- The FULL104 lineage shard headers were checked for forbidden columns on every
  one of the eleven SEA-AD shards read.
- The Level-4 selection manifest was projected to six identity columns, and that
  projection was firewall-checked; the manifest also carries
  `expression_asset_path`, `expression_asset_sha256` and `expression_row`, all of
  which the firewall rejects and none of which were read.
- No protected biological outcome was opened: no corrected FULL104 relational
  outcome, no protected pathology outcome, no teacher latent, no TD60 outcome,
  and none of the six reserved RNA addresses (2810, 4748, 10846, 13734, 14980,
  26659). The reserved-address arrays exist inside the myeloid npz that this lane
  opened for identity; `counts` and `address_available` were never indexed, and
  `np.load` on an npz is lazy, so those arrays were never decompressed.
