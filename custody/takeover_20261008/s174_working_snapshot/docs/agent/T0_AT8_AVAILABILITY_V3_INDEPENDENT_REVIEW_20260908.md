# T0 AT8 availability V3 — independent review result

Date: 2026-09-08

Candidate:
- ZIP SHA-256: `01ce9b37e592ee694c0cb6edc2b1095908943997216bd70e8f792416a78a70a2`
- availability root: `e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b`
- package root: `5ed35e084f888c688bc77edcda542c0a2c7f56d3f24b7cf8689aa07733bb2fdc`
- packaged derivation code: `a78f58709418c1b341a0570d657a44ece706861fbeb5ecedd2307053841b3e`

## Decision

`STOP_T0_AT8_AVAILABILITY_V3_WRITE_FREEZE_BINDING_NOT_CLOSED`

V3 is **not independently accepted**. The donor-role STOP remains active.

The frozen V3 bytes themselves are internally consistent:
- the review ZIP digest reproduces;
- all top-level declared members reproduce their byte counts and SHA-256 digests;
- the inner package root reproduces;
- the availability root reproduces;
- the packaged suite runs from the extraction root: 26/26 PASS;
- the registry contains 84 unique sorted donors, all 84 marked available;
- the 46-donor witness contains 46 unique donors, recomputes to
  `f89838342622348f126217686084bf69901b1a50aca97ce94b176b779e294d64`,
  is a subset of the frozen registry, and all 46 witness donors are marked
  available.

V2's extraction-layout defect was independently reproduced: its test module
does not import from the archive layout. V3 fixes that packaging issue.

## Blocking defect found in V3 implementation

The source reader correctly authenticates one captured byte buffer, and the V3
loader correctly authenticates and parses one captured byte buffer per package
member. The package writer did not follow the same rule.

`_write_flat_package` wrote the intended member bytes to disk and then reopened
those paths to compute byte counts and hashes for the manifest. Therefore the
returned in-memory metadata and the bytes committed by the returned package root
could diverge if a same-length substitution occurred between write and hash.

The defect was reproduced before repair. A synthetic build replaced only
`membership_donor_set_sha256` in the just-written metadata with 64 zeroes.
The builder returned the original membership digest, while the on-disk package
contained zeroes. Because the writer hashed the substituted path bytes, the
manifest and package root authenticated the substituted metadata, and
`load_availability_authority` accepted it against the roots returned by that
same build.

This is a write/freeze binding defect. It changes no T0 scientific rule and
does not demonstrate that the already-frozen V3 registry is wrong, but a
production authority may not be accepted while its freezer can silently bind
bytes different from those the builder intended.

## Repair

Branch:
`t0/v20-pathology-blind-materialization-20260908`

Implementation commit:
`8ef9dc19c9f66a94aa7068458eb665ea1e04c2c2`

Regression-test commit / current repair head:
`0edb56595febaf1f7b9a0ea1760bb934653e63f4`

The writer now computes the manifest rows, member digests and package root
directly from captured in-memory payload bytes **before any member is written**.
It then materializes those already-committed bytes. A filesystem substitution
during materialization therefore makes subsequent package verification fail
against the returned roots rather than redefining the authority.

The new regression reproduces the former same-length metadata substitution and
requires the repaired package to fail closed. The repaired V3 module plus the
new regression passes 27/27 in the independent sandbox.

## Required successor

Do not relabel V3 as accepted and do not edit its frozen metadata in place.

Because the derivation implementation changed, the exact frozen pathology
source must be authenticated again by SHA-256
`ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a`
and the authority rebuilt with the repaired code.

Expected invariant, subject to actual rebuild:
- availability root should remain
  `e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b`
  if the boolean derivation is unchanged.

Must change:
- derivation-code SHA-256;
- package root;
- review ZIP SHA-256.

A V4 review package must then be independently rechecked. Until that succeeds,
`STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND` remains active.

The numeric pathology source was not present in the independent sandbox, and
numeric AT8 values were not opened. Therefore no new production package root is
asserted here.
