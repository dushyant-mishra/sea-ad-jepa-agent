# Waiver record — the LF-content versus Git-blob provenance label

    PROVENANCE_LABEL_WAIVER_ACCEPTED_BY_EXTERNAL_REVIEW__LIMITED_SCOPE

R6 item 5 offered two ways to resolve this: re-stamp the lane, or record an
explicit owner waiver. The owner chose the waiver on 2026-09-09, and the external
reviewer accepted it the same day as a limited review waiver, ruling
`LINEAGE_RECUT_REQUIRED_BEFORE_REAL_T0=False`.

Accepted on these terms, in the reviewer's own words:

    PROVENANCE_LABEL_WAIVER_ACCEPTED=True
    WAIVES_DIGEST_VALUES=False
    WAIVES_PACKAGE_ROOTS=False
    WAIVES_REPLAY_OBLIGATIONS=False
    ALLOWS_NEW_FALSE_LABELS=False

The last condition is enforced in code rather than left to convention. See
"Enforcement" below.

## The defect, stated exactly

Six T0 authority modules write

    "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"

into their package metadata while the digest they record under
`derivation_code_sha256` is the plain SHA-256 of the derivation module's
LF-normalized file content. A Git blob digest frames content as
`b"blob <len>\0" + content` and is a different value.

Measured on `t0_technical_completeness_authority_v1.py`:

    recorded in the package  64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    sha256 of LF content     64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49   <- match
    sha256 of blob framing   6045f84cd1ea7f642f2b91b15756be7e3bb9bdd97fd53224f88f1d04b6f81c4d
    git hash-object          0e8c701b5213a36fc7983b0c6890c93514eb2e9d

Reproduce with:

    python - <<'PY'
    import hashlib, pathlib
    c = pathlib.Path("scripts/v4/t0_technical_completeness_authority_v1.py"
                     ).read_text(encoding="utf-8").replace("\r\n", "\n"
                     ).encode("utf-8")
    print("lf_content ", hashlib.sha256(c).hexdigest())
    print("blob_framed", hashlib.sha256(b"blob %d\x00" % len(c) + c).hexdigest())
    PY

## Scope

Affected — label false, values correct:

    scripts/v4/t0_raw_source_row_authority_v1.py            (B2 population)
    scripts/v4/t0_technical_completeness_authority_v1.py
    scripts/v4/t0_at8_availability_authority_v1.py
    scripts/v4/t0_age_sex_authority_v1.py
    scripts/v4/t0_immune_fraction_authority_v1.py
    scripts/v4/t0_immune_support_count_authority_v1.py
    docs/agent/T0_B2_PRODUCTION_ARTIFACT_MANIFEST_20260909.md  (same claim in prose)

Not affected — these state the method accurately:

    scripts/v4/t0_eligible_donor_authority_v1.py
    scripts/v4/t0_eligible_donor_production_run_v1.py
    scripts/v4/t0_estimability_preflight_production_run_v1.py

Explicitly out of scope. This is **not** about `work_checkpoint`, whose
`bytes_authority` of `GIT_BLOB_BYTES_PLATFORM_INDEPENDENT` is accurate: that lane
genuinely validates tracked authorities from the immutable Git blob, which was
implemented deliberately after a CRLF checkout changed a tracked package
member's bytes. Two different mechanisms; only one is mislabelled.

## What is and is not at risk

Not at risk. Every recorded digest is correct as an LF-content SHA-256,
reproducible on any platform, and CRLF-safe — which is the property the field
exists to provide. A reviewer who reruns a committed runner recomputes the same
value, because the runners compute it the same way. No package root depends on
the label text, and no authority decision depends on it.

At risk, and the reason this is a defect rather than a typo. A reviewer who
reads the label and computes a Git blob digest independently gets a mismatch and
may reasonably conclude the packages are broken. That is a false alarm
manufactured by our own metadata, and it costs reviewer time in exactly the lane
whose purpose is to make verification cheap.

## Why the owner chose a waiver over re-stamping

Correcting the label changes each module's own content, therefore its
`derivation_code_sha256`, therefore the metadata member, therefore the package
root of every affected authority. The cascade:

    AT8 availability, age/sex, immune fraction, immune support   rebuild, seconds each
    B2 population raw-source    rebuild, re-hashes the 32,978,570,763-byte MTG asset
    technical completeness      rebuild, a full ~40-minute pass over the counts store
    eligible donors             rebuild, because its parent roots all move
    estimability preflight      rebuild, because its parent roots all move

Every root cited in DEC-024, DEC-025 and the review package index would move, and
each would need replaying again. The owner's judgment was that re-stamping a
false one-word label at that cost, before external review has ruled on the
substance, is producer-side churn rather than progress, and that the choice
belongs to review.

## Conditions of the waiver

1. The defect stays visible. It is recorded as finding F2 in the review package
   index, in DEC-025 and DEC-026, in the artifact manifest, and here.
2. No new artifact propagates the false label. The three modules written since
   the finding state the method accurately, and that is verified by test.
3. The waiver covers the label text only. It does not waive any digest value,
   any package root, or any replay obligation.
4. It does not extend past external review. If the reviewer requires a re-stamp,
   the lane is re-cut and every affected root is regenerated and replayed.
5. Real T0 does not run under this waiver. It is a documentation waiver, not an
   execution authorization.

## Recommended correction, when review rules on it

Replace the six occurrences with the accurate constant already used in the
eligible-donor lane:

    "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES"

and correct the prose in `T0_B2_PRODUCTION_ARTIFACT_MANIFEST_20260909.md`. Then
rebuild and replay in dependency order: the four small authorities, B2, technical
completeness, eligible donors, estimability preflight — regenerating every
manifest and decision record that cites a moved root.

## Enforcement of `ALLOWS_NEW_FALSE_LABELS=False`

`t0_input_dependency_contract_v1` now carries the canonical constant, the frozen
waiver set and a guard:

    ACCURATE_CODE_BYTE_SEMANTICS          the string new artifacts must declare
    WAIVED_FALSE_CODE_BYTE_SEMANTICS      the legacy string
    PROVENANCE_LABEL_WAIVER_MODULES       the six waived modules, frozen by count
    assert_byte_semantics_label_lawful()  refuses the legacy label outside that set
    assert_provenance_waiver_set_unchanged()  refuses growth of the waived set
    audit_byte_semantics_labels()         scans and classifies every T0 module

A new real-T0 module is not on the allowlist, so declaring the legacy label
raises `STOP_T0_NEW_ARTIFACT_CARRIES_THE_WAIVED_FALSE_BYTE_SEMANTICS_LABEL`.

The audit matches the *declaration site* rather than the bare label. Scanning for
the label itself flagged the contract module, which defines the constant without
declaring anything about its own artifacts — the same crude-substring error that
earlier refused an `age_present` header and a report's own
`at8_availability_root_sha256`. Third instance of that pattern; it is why the
guard matches a key/value pair.

Current audit:

    accurate        t0_eligible_donor_authority_v1.py
                    t0_eligible_donor_production_run_v1.py
                    t0_estimability_preflight_production_run_v1.py
    waived legacy   t0_age_sex_authority_v1.py
                    t0_at8_availability_authority_v1.py
                    t0_immune_fraction_authority_v1.py
                    t0_immune_support_count_authority_v1.py
                    t0_raw_source_row_authority_v1.py
                    t0_technical_completeness_authority_v1.py

## Status

    defect                      CONFIRMED, measured, reproducible
    digest values               CORRECT, unaffected
    package roots               UNAFFECTED by the label
    owner decision              WAIVE, do not re-stamp
    reviewer acceptance         ACCEPTED as a limited review waiver
    lineage re-cut required     False, per the reviewer's R6 ruling
    new false labels            REFUSED IN CODE
    real T0                     not authorized by this waiver; see the
                                authorization request
