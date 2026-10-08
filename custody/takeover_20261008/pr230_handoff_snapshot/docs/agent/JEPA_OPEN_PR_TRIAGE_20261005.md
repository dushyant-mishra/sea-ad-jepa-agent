# JEPA OPEN-PR TRIAGE — 2026-10-05

This ledger distinguishes repository navigation cleanup from scientific retraction.

## Canonical landing state

`main@ab6685019783810db3b1f129f1d72ac2881b223d` is the current startup/navigation surface after PR #212.

The current scientific boundary remains:

- V75 100K measurement architecture stands within scope;
- 500K not authorized;
- no qualified production target winner;
- learned-state scaling ladder stopped;
- training off;
- Stage 4 not authorized;
- width 160 is not biological dimensional authority.

## Closed as superseded navigation/custody

These PRs were closed because their active integration/navigation role was superseded. Their branches/history remain preserved:

| PR | Historical role | Cleanup classification |
|---|---|---|
| #16 | Sep-11 governance lane-separation repair | `SUPERSEDED__NAVIGATION__HISTORICAL_FINDING_PRESERVED` |
| #34 | historical handoff/support lane | `SUPERSEDED__NAVIGATION` |
| #37 | Sep-21 FULL104 ETL + takeover | `SUPERSEDED__NAVIGATION` |
| #40 | historical handoff/support lane | `SUPERSEDED__NAVIGATION` |
| #53 | historical handoff/support lane | `SUPERSEDED__NAVIGATION` |
| #68 | historical handoff/support lane | `SUPERSEDED__NAVIGATION` |
| #123 | V26 handoff publication | `SUPERSEDED__NAVIGATION` |
| #148 | V27 independent-audit handoff with stale BLAS wording | `SUPERSEDED__NAVIGATION__CORRECTIVE_NOTICE_ADDED` |
| #150 | V28 verified evidence/new-chat handoff | `SUPERSEDED__NAVIGATION__HISTORICAL_EVIDENCE_PRESERVED` |
| #159 | V32 local-evidence handoff | `SUPERSEDED__NAVIGATION` |
| #167 | V38 reviewed takeover/branch map | `SUPERSEDED__NAVIGATION` |
| #174 | custody/data publication | `CUSTODY_ONLY__PRESERVED` |
| #183 | V45 handoff + custody-gap boundary | `SUPERSEDED__NAVIGATION__CUSTODY_HISTORY_PRESERVED` |
| #184 | custody publication | `CUSTODY_ONLY__PRESERVED` |
| #186 | custody publication | `CUSTODY_ONLY__PRESERVED` |
| #190 | V51 regulatory-redteam/chat-custody handoff | `SUPERSEDED__NAVIGATION__HISTORICAL_EVIDENCE_PRESERVED` |
| #197 | V63 external-regulatory handoff/chat custody | `SUPERSEDED__NAVIGATION__CUSTODY_HISTORY_PRESERVED` |
| #208 | V75 chat-runtime custody + stale learned-160D takeover | `SUPERSEDED__NAVIGATION__CUSTODY_HISTORY_PRESERVED` |
| #210 | Oct-5 custody + historical target-authority reconciliation | `CUSTODY_ONLY__PRESERVED__MIRRORED_TO_MAIN` |
| #211 | Oct-5 cleanup staging branch | `SUPERSEDED__STAGING__AUDIT_LEDGER_PRESERVED` |

## Intentionally retained open

The following remain open because they carry substantive scientific, implementation, data, review, or audit evidence and have not been individually closed by a successor:

- PR #207 — V75 measurement authority remains relevant within scope; only its next-action text is superseded.
- PR #178 — corrective historical authority containing S9/gradient retractions and target-comparison result.
- PR #163 — prospective target-design evidence; no target winner selected.
- PR #199 — recoverability/regulatory architecture work; substantive design/tests, not merely navigation.
- PR #195 — regulatory independence / external-anchor evidence.
- PR #162 — physical replay evidence.
- PR #154 — historical authority sweep/red-team evidence.
- PR #152 — prospective target decision/red-team tests.
- PR #136, #118, #117, #77 — substantive ETL/baseline/data evidence.
- PR #42, #41, #36, #33, #20, #18 — substantive FULL104/masking/target mechanics and audit evidence.

Age alone is not grounds for closure.

## High-risk live claim policy

When a substantive PR contains one stale/retracted sentence but also unique scientific evidence, prefer an explicit corrective comment/body amendment over closing the whole PR.

Known examples:

- PR #147: S9 BLAS diagnosis retracted by PR #178.
- PR #207: V75 result stands; post-V75 learned-160D next action superseded.
- PR #31: stale environment wording flagged; substantive content preserved.

## Next tranche

1. search remaining open PRs for titles/bodies dominated by `handoff`, `takeover`, `custody`, `governance`, or `pointer`;
2. individually verify changed paths before closure;
3. keep science/data/audit PRs open unless a successor unambiguously closes their active role;
4. do not delete branches yet;
5. only consider branch deletion after exact ancestry + unique-byte/evidence preservation review.
