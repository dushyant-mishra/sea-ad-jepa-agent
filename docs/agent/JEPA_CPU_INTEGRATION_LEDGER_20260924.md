# JEPA CPU integration candidate — 2026-09-24

**Scope:** Code, safety gates, lightweight metadata census and synthetic/metadata tests only. Parent: Claude PR #77 @ `3e293a43e4d6dfb6bba85eaf188bdbbe5ecb2821`. This branch does **not** update historical heavy experimental outputs or main's canonical handoff. It does not issue new physical/experimental scientific authority.

## Exact independently developed source branches copied into this single candidate

| Lane | Full terminal source SHA | Integration scope |
|---|---|---|
| #82→#97 | `9100b9c0f2dfa93a69867d9017b73483d6abba57` | 4 files: source/script byte preflight, qualified-receipt scope restricted to preflight only, red-team CI |
| #87→#89→#98 | `037c048cf163009525874d51280b0cf6f8bebc11` | 5 files: HGNC/Ensembl/Entrez explicit feature identity and detection-vs-absence contract, scaling fix, tests |
| #84→#88→#90 | `3669e5c2a9f3e9466ce269efcbd696c4c28746b2` | 7 files: held-target baseline, donor-balanced guide scoring, outcome exposure ledger; no false prospective holdout |
| #92 | `bc09c0f432db6e17bec3047baeb0812975043937` | 4 files: GSE311359 duplicate-BIN1 guide STOP and fail-closed source producer; historical colliding V1 outputs remain NOT qualified |
| #91 | `56600f66492b18af20edcfe5d11761d2cdca9383` | 3 files: SHA-bound independent GSE301119 light metadata donor/guide census, not physical RNA reexecution |

All 23 copied source/test/workflow/docs files should be compared by actual file blob bytes against these terminal heads before any merge. Parent #77 remains a **draft** and retains existing physical V1 data under its original provenance. Do not relabel its GSE311359 guide-level V1 outputs on the strength of a passing source STOP test. The existing source-root rechecks do not prove downstream analysis execution or output correctness.

**Review gates:** independently inspect all resulting diffs and hosted workflows, report exact passed/skipped counts, check no unrelated changes, verify source head drift. No merge to `main` until parent PR #77's scientific STOPs and integration governance are adjudicated. Separate physical V2 work is required for #86 GSE254205, #94 GSE240609; source/protospacer rescue is required for GSE311359; GSE178317/GSE175721 guide assignment stays STOP without authentic source evidence. Full104 #83→#85 remains a separate chain, with N1 UNAUTHORIZED.

**Permanent boundaries:** TRAINING=OFF; AUDIT_B_N1=UNOPENED; D_SHARED_G5=UNOPENED; PROTECTED_OUTCOMES=UNOPENED; THERAPEUTIC_RANKING=OFF. No synthetic test result is a biological result.
