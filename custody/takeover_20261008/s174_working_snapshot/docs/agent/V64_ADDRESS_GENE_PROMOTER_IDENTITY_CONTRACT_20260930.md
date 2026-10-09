# V64 address ↔ gene ↔ promoter identity contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE IDENTITY/BRIDGE CONTRACT — no biological outcome opened

## 1. Problem

The project contains multiple molecular namespaces whose cardinalities are not interchangeable:

- molecular **addresses** used by the FULL104/operator-support system;
- genes;
- transcripts;
- candidate promoters/TSSs;
- regulatory elements;
- E2 edges.

A count in one namespace must never be silently re-labelled as a count in another.

In particular, an address measured by all operators is not assumed to map 1:1 to a gene.

## 2. Required namespace keys

Every bridge table must declare both source and destination namespaces.

Preferred explicit fields include:

- `address_id`
- `gene_id`
- `gene_symbol`
- `transcript_id`
- `candidate_promoter_id`
- `regulatory_element_id`

Null or ambiguous mappings remain explicit.

## 3. Mapping cardinality is evidence, not inconvenience

For every bridge report:

- source rows;
- unique source IDs;
- destination rows;
- unique destination IDs;
- 0-to-1, 1-to-1, 1-to-many, many-to-1, and ambiguous counts where meaningful;
- unresolved/unmapped count.

Do not de-duplicate many-to-one mappings without reporting the collapse.

Do not expand one-to-many mappings and then use row count as entity count.

## 4. FULL104 common-address denominator

A common-address list may be used as an **address-level measurement-support denominator**.

It may not be used as:
- gene denominator;
- promoter denominator;
- E2-gene coverage denominator;

until a versioned, audited address→gene bridge is applied.

If a future file establishes 17,186 addresses measured in all 42 operators, the canonical statement is:

> 17,186 common measured addresses

not:

> 17,186 genes

unless the audited bridge proves 1:1 gene identity for the relevant subset.

## 5. Promoter bridge

Promoter analysis requires:

`address/gene -> gene identity -> transcript/TSS candidate -> promoter evidence`

The GENCODE-defined promoter candidate universe remains separate from Nott promoter annotations.

Nott promoter evidence may support or map candidates but does not redefine the annotation denominator.

## 6. E2 coverage fractions

Before computing an E2 coverage fraction against a FULL104 backbone, freeze:

- numerator namespace;
- denominator namespace;
- exact bridge;
- ambiguity policy;
- unmapped policy;
- version/hash of all bridge inputs.

Forbidden example:

`E2 genes / common addresses`

unless address↔gene equivalence has been explicitly proven.

## 7. Smoke-test expectations

Tests should fail if:
- an address count is labelled as genes without bridge evidence;
- unique-gene count is inferred from bridge row count;
- ambiguous mapping is coerced to a single gene without a declared policy;
- not-mapped is coerced to absence of biology.

## Governance

TRAINING OFF.
Phase B STOPPED.
Stage 4 NOT AUTHORIZED.
This contract authorizes no biological coverage claim by itself.
