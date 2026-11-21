# Unified Task 2 — narrow independent Macha recheck packet

Date: 2026-10-15

## Authority state

Task 0 remains frozen at `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.

Unified Task 1 remains independently accepted/frozen at `799d2e235901dfad9ce3b305c767a1c989e362f6`.

Unified Task 2 remains OPEN and Unified Task 3 remains BLOCKED.

Rejected Task 2 candidate: `2c391137bf0564d31d39efa1ec0a61e198dbf027` (closed PR #388).
Independent rejection evidence: Macha review head `d2efb33774e6ce1b6a62958a375c168d01f596c6`.

Current repair candidate for recheck only:
`c7dfff1cee608e4a101855d42cf0af08491c2aaf` on draft PR #390.

This packet requests re-check of only T2-B1 through T2-B4, as authorized by Macha's prior verdict. It is not a request to repeat settled Task 0/1 audits.

## RED custody

PR #389 preserves the first direct reproduction of Macha's four blockers. Initial RED head `9e22823bade5736b7c5b8a67d8c50025bc21b44d` produced 5 intended failures with 95 prior unified tests passing.

A second controller self-audit noticed that an already-forged authoritative policy could still reach harness session issuance/access validation without re-resolving split bytes. RED2 at `bf8a90277edb9c35060ce663a34d3221fa6781b3` therefore extended B1 to those authority-consumption points before final GREEN.

## T2-B1 repair — population authority

Current-TD population authority now requires raw reader-split resolution at every implemented authority-consuming boundary:

- manifest population binding;
- public population-policy validation;
- `require_current_td_population_authority`;
- authoritative harness session issuance;
- authoritative producer-access validation.

At each such boundary the code re-resolves the claimed reader-split bytes, recomputes SHA-256, parses exactly 149 donors with 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle`, reconstructs the exact 104 fit-donor set, recomputes the five `DONOR_SHA256_ORDER_ROUND_ROBIN_V1` folds and requires exact equality.

A policy containing invented donors or lawful donors in non-lawful folds therefore cannot obtain current-TD authority merely by copying digest strings.

The historical population-registry digest `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d` is retained only as a **custody annotation**. It is deliberately not used as a population-authority predicate because Task 2 does not presently re-resolve the registry's raw bytes. This implements Macha's permitted resolution: verify the bytes or drop the digest from authority.

## T2-B2 repair — observed access

Authoritative current-TD access can no longer be validated from an arbitrary producer-supplied ledger resolver.

`HarnessAccessRegistry` now:

- owns session issuance;
- holds the reader-fit values passed to the session gateway;
- generates a harness-specific session id;
- records the session-generated events;
- creates `OBSERVED_ACCESS_LEDGER_V2_HARNESS_ATTESTED`;
- HMAC-attests the canonical ledger with a harness-held key;
- stores the ledger internally;
- resolves only ledgers that were actually stored by that registry and whose HMAC still verifies.

For an authoritative access policy, `validate_producer_access` requires that harness registry. A hand-made V1 ledger/receipt does not become authoritative merely because its fields look lawful.

This remains application-level enforcement, not an OS sandbox. Protected partitions still must remain physically absent from producer processes where later runtime qualification requires that isolation.

## T2-B3 repair — duplicate sub-policy consistency

The cross-fit, protected-partition and reader-partition policy objects are now deterministic canonical derivations of the bound access policy. Manifest validation resolves those sub-policy objects and requires exact equality to the derived payloads.

Contradictory language such as `biological values allowed`, `folds chosen later`, or `rescue estimability` cannot coexist with the current access policy and still validate merely by carrying the right object role.

## T2-B4 repair — missing manifest identity surface

`TD_EXECUTION_MANIFEST_V1` now explicitly requires:

- `normalization_library_contract_sha`;
- `target_portfolio_code_identity_sha`;
- `target_portfolio_policy_sha`;
- `unit_execution_identity_table_sha`.

The per-unit table is closed and binds, per `unit_id`:

- producer code identity;
- executor code identity;
- producer policy identity;
- executor policy identity;
- unit schema identity;
- metric definition identity;
- reference-producer identity;
- falsifier-control identity.

Nested semantic identities are re-resolved and role/digest checked. Code identities are Git-blob identities recomputed from actual bytes when resolved.

## Exact-head controller evidence

Exact candidate: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`.

- Task 2 workflow `38679766634`, job `116241404892`: SUCCESS.
  - focused existing Task 2 suite: 31 passed;
  - complete `tests/v5/td_unified`: 103 passed.
- frozen Task 1 workflow `38679766549`: SUCCESS.
- inherited unified synthetic integration workflow `38679766529`: SUCCESS.

These are controller-side execution facts, not independent acceptance.

## Cross-fit scientific limitation carried forward

Macha accepted the prospective switch to `DONOR_SHA256_ORDER_ROUND_ROBIN_V1` for pooled donor-level use. Macha's source replay showed:

- fold 0: HVS 7 / NPH52 4 / SEA_AD 10;
- fold 1: HVS 7 / NPH52 2 / SEA_AD 12;
- fold 2: HVS 11 / NPH52 6 / SEA_AD 4;
- fold 3: HVS 7 / NPH52 4 / SEA_AD 10;
- fold 4: HVS 9 / NPH52 1 / SEA_AD 10.

Therefore this five-fold law may support pooled donor-level cross-fit analyses but must **not** be used to claim stable per-fold source-stratified metrics, because fold 4 holds out only one NPH52 donor.

## Requested independent verdict

Please attack exact head `c7dfff1cee608e4a101855d42cf0af08491c2aaf`, focusing only on whether T2-B1, B2, B3 and B4 are actually closed.

A passing test suite is not sufficient. Re-run/adapt the original hostile probes and try at least:

1. forged 104-donor authoritative policy with correct SHA strings;
2. lawful donor set with folds that violate the frozen assignment law;
3. authoritative session issuance/access validation without a raw split resolver or with altered split bytes;
4. hand-made clean observed-access ledger/receipt that never came from the harness;
5. contradictory redundant sub-policy objects;
6. omitted/role-spoofed/nested-spoofed B4 identity objects.

If any blocker remains, reject this exact head and report the minimal defect. If all four are closed, explicitly state acceptance of exact head `c7dfff1c...` for Unified Task 2 freeze eligibility.

No target, representation, Stage 4, biological-result or training authority is granted by either outcome.

Global authority remains exactly:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
