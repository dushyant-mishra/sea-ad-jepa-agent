# Historical foundation calibration archive intake — independently reproducible data integrity, NOT real authority

**2026-10-27.** Original uploaded input: `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`, `expression.zip`, `checkpoints.zip`, the two uploaded `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part00*` components and their external parts SHA-256 CSV. No full matrices, donor identifiers, per-cell values or checkpoint tensors are committed to GitHub.

**Scope:** source archive inventory, integrity and partition metadata; not biological calibration qualification, not an empirical human latent-state estimate, and not the production-realization generator. The actual uploaded archives are external runtime attachments and remain outside GitHub; CI can run reproducible *synthetic* archive hostile fixtures but does not have access to these human-data archive bytes.

## Verified physical data result, not merely a source description

Using the read-only `scripts/production_synthetic/foundation_calibration_split_intake_v1.py --input-dir <mounted location> --output <receipt> --full`:

| Observed item | Independently computed result |
|---|---|
| Bundle manifest identity | `da7c3daf507a66118131e88ae6685cf43eb14d4163539ade5e0705f6fb845cef`, equals the SHA declared in `BUNDLE_STATUS.json` |
| Manifest entries | **97 unique logical files**, exactly reconciled across archive groups |
| Main calibration ZIP | **48** manifest payload members, plus manifest/status metadata |
| Separate expression ZIP | **45** manifest members |
| Separate checkpoints ZIP | **3** manifest members |
| Split 41K expression ZIP | **1** large NPZ member, read through an on-demand seekable concatenation (never reassembled/extracted to a new file) |
| Part and combined archive SHA | Both uploaded part SHA strings and combined **607,959,761-byte** ZIP SHA `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7` agree with the independent parts CSV |
| Source member integrity | **97 / 97 member uncompressed SHA-256 and lengths match their manifest entries** including the metadata SQLite, expression matrix and checkpoints |
| Historical donor partitions | Unique donor IDs checked locally; aggregate only **104 reader-fit / 22 reader-validation / 23 reader-oracle** |
| Bundle-declared population/support | 6,351,753 metadata-cell rows; 50,000 frozen expression sample cells; 41,238 addresses; 42 operators |
| Protected-data declaration | Status declares no DEV/SEALED expression and no pathology fields; this script does **not** independently prove all semantic protected-data exclusions |

**Crucial provenance distinction:** the main ZIP alone contains only 48/97 declared payloads. They are *not missing from the logical historical package*: 45 are in the expression ZIP, three in the checkpoint ZIP and one in the separately split large expression archive. Do not label the historical export corrupted because an individual physical archive is partial.

A machine-readable, aggregate-only result is committed at `results/production_synthetic/foundation_calibration_split_intake_20261027.json`. The source code and synthetic-only hostile tests are checked in on this PR. Only the real mounted inputs were hashed locally; the CI fixture suites do **not** authenticate the raw archive bytes themselves.

## How this changes production-synthetic V3.1.1 readiness

The archive has an intact historically traceable **data lineage and split registry**. That is useful for auditing old experiments and understanding observation/support geometry, but **does not satisfy the current authenticated observation-calibration firewall**.

- Source is frozen at August 24, earlier than the October physical HVS/SEA-AD feature mapping correction and Macha's 8,915-block real reader-fit raw-count audit. The metadata scope and 50K expression development sample cannot be silently elevated into current 149-donor rawcount calibration issuer authority.
- PR #437 `scripts/production_synthetic/calibration_v1.py` explicitly has an empty `_AUTHENTICATED_CALIBRATION_REGISTRY`, and its authorized returns are fixture-consistent at most. A matching manifest SHA does not populate the code-pinned registry or attest that its observations satisfy current full-width raw-count and q-exclusion rights.
- V3.1.1 PR #344 allows authenticated real calibration to constrain **observation** distributions only, never hidden latent disease prevalence, gene regulatory truth or target-specific mechanisms. It forbids deriving synthetic biology from PR #328 gene blocks and requires candidate-neutral mechanisms, frozen realism thresholds, withheld-family custody and nonadaptive generator iteration.
- A source archive's reader-fit/validation/oracle split provenance does not establish independent cell-level physical unit identity, q-excluded normalization or real G7 E3 trust. Macha PR #449 R1/R2 remain RED. The separate G7 R3–R5 patch PR #470 does not change this.
- Existing PR #469 can pass source-generated PR #328 RNA measurements through the Task5 fixture bridge, but is not the authentic V3.1.1 CaseBundle→real producer→executor→truth adjudicator.
- No protected candidate/outcome source, new biological result, synthetic hidden truth or real human learning run was accessed in this integrity pass.

### Next lawful action for the production-synthetic lane

Use this archive only as **historical, hash-verified context**, not as a live calibration input. Identify an independently attested *current* full-width TRAIN observation-statistic producer using source-corrected gene identities, true raw counts, source/operator/donor support and legitimate evidence-rights normalizers; bind its output by exact authenticated source hash and split firewall. Then require Macha/independent review before Task3's code-pinned registry or production V3.1.1 realism can advance.

If current measurement authority is absent, the correct gate is `CALIBRATION_NOT_AUTHENTICATED`, not a fabricated target, silent old-archive substitution or permissive data-processing shortcut. Continue local synthetic mechanics tests without scientific promotion.

**Scientific invariant:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Reproduction instructions

```bash
python scripts/production_synthetic/foundation_calibration_split_intake_v1.py \
    --input-dir /path/to/uploaded/archive-set \
    --output historical_intake.json --full
python -m pytest -q tests/production_synthetic/test_foundation_calibration_split_intake_v1.py
```

The first requires the original user-supplied archives and their parts manifest; the second manufactures synthetic archives of the same structural layout and rejects SHA tampering, missing files, donor collisions and partial archive forgery. Neither author CI nor this result independently qualifies the full physical real-calibration producer.
