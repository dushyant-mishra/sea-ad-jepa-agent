# T0 Technical Completeness / Eligibility Acceptance Oracle V1

Status: **EXTERNAL REVIEW ORACLE — PATHOLOGY-BLIND**

This oracle follows the frozen executable dependency contract on producer head
`24b2c9ff...`.

## Exact Q summaries

For each authenticated accepted broad-IMMUNE cell:

`qdepth_cell = log1p(source_library)`

`qdetect_cell = count_nonzero(A) / 35076`

where `A` is the full 35,076-address B1 T0 projection for that cell.

Per donor:

`Q_DEPTH = mean(qdepth_cell)`

`Q_DETECT = mean(qdetect_cell)`

Q_DETECT uses all 35,076 measured addresses, not the 28,061 SCORING subset.

## Technical completeness

Only after all parent authorities have passed globally:

`technical_complete(d)=True`

iff the frozen six definedness/computability conjuncts hold:

1. donor belongs to the accepted op31 candidate donor universe;
2. donor has at least one authenticated accepted cell;
3. accepted cells close correctly through authenticated B2;
4. raw-count/source_library information required for the summaries is lawful;
5. Q_DEPTH is computable and finite;
6. Q_DETECT is computable, finite and in its lawful range.

Forbidden:

- Q_DEPTH minimum;
- Q_DETECT minimum;
- cells-per-donor QC threshold;
- using the 80-cell tail floor;
- any post-hoc donor-quality threshold.

Low but finite depth/detection must remain technically complete.

Authority/provenance failure is a global STOP, never
`technical_complete=False`.

## Eligible donor authority

Eligibility is a separate authority after technical completeness:

`eligible = AT8_available & technical_complete & finite(age) & nonempty(sex)`

It must bind the externally accepted roots for:

- candidate donor universe;
- AT8 availability;
- technical completeness/Q summaries;
- age/sex authority.

It must not read numeric AT8 magnitude.

The final eligible donor set is an output of this authority, not of B2.

If eligible donors < 36:

`STOP_T0_DESIGN_NOT_EXECUTABLE_UNDER_FROZEN_ELIGIBILITY`

No threshold, split or eligibility conjunct may be changed to rescue the design.

## Deterministic roles

Only after eligible authority is frozen:

- namespace `T0-DISCOVERY-CONFIRM-V2`;
- SHA-256 donor IDs under the frozen namespace;
- sort by `(split_hash, donor_id)`;
- first 18 = CONFIRMATION;
- remainder = DISCOVERY;
- require discovery >= 18.

The 80-cell support floor determines tail measurability only and never changes
parent eligibility or role assignment.
