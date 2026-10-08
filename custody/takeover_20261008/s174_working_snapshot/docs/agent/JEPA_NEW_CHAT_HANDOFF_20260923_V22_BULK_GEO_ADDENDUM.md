# JEPA Sep23 V22 operational addendum — new bulk-context analyses and independently reviewed GEO sample identities

**Read order:** `START_HERE.md` → current `JEPA_LATEST_HANDOFF_POINTER.json` → **this V22 addendum** → full `JEPA_NEW_CHAT_HANDOFF_20260923_PARALLEL_V21.md` → `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`. V22 updates **only developments after V21**; V21 remains the full source/branch/script/credential-free startup and architecture handoff. Always fetch live heads.

**Boundaries unchanged:** JEPA training OFF, real Audit-B N1 unopened, rare-tail molecular unopened, D_shared/G5 unopened, protected FULL104 outcomes unopened, therapeutic ranking OFF. A successful CPU check or source metadata preflight is never real experimental requalification.

## New heavy physical producer progress since V21

Claude's PR #77 advanced from `f34fae312a3006e9eefaa1dfb85749037de9dddd` to `3e293a43e4d6dfb6bba85eaf188bdbbe5ecb2821` with **GSE241858 and GSE240609 BULK disease-context V1** outputs.

* **GSE241858**: TREM2 R47H clone × inflammatory-context bulk RNA-seq. Authenticated bulk V1 receipt `analysis/therapeutic_perturbation_etl/evidence/bulk_disease/BULK_DISEASE_CONTEXT_SUMMARY.json`: 12 baseline samples, 23 cytokine samples, 28,395 original genes. Baseline 20,509 genes detected; cytokine 24,157. The producer averages within clone×treatment before effect contrasts; two independent iPSC clone units per genotype, not 6+ biological donors. The cytokine design is unbalanced (e.g. one CTRL_A LPS replicate) but preserves sample/clone structure. Do not overinterpret clone SE from n=2 per genotype or pretend this is CRISPR.
* **GSE240609**: APOE3 Christchurch × WT/PSEN neuron-context 2×2 expression study. Four samples, 27,154 genes; 19,045 detected. Public-GEO GSE240609 series *independently* identifies original sample titles: GSM7703564 APOE3CH-WT, GSM7703567 APOE3CH-PSEN1, GSM7703569 APOE3-WT, GSM7703571 APOE3-PSEN1. Current V1 effect CSV has 38,090 two-contrast gene rows; each factorial cell has ONE source sample, thus **no biological uncertainty estimable**. Critically, public GEO says these RNA samples were **CD11b purified microglia recovered after 10-day neuron–microglia coculture**, not bulk unfractionated coculture. Any response can depend on neuron genotype but is measured in purified microglia after coculture. Source: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE240609 .

## New independent review PR #94

`review/gse240609-public-geo-sample-identity-v2-20260923` @ `9cc155a659f9a70bf2f1e7a1fd9cc05283089cbf`, based on the latest observed PR #77 head. Draft PR #94: https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/94 . Hosted red-team workflow **9 passed, 0 skipped** at this head; review opened original lightweight sample-identity CSV and public GEO, NOT physical count matrices.

Found a fail-open in the V1 GSE240609 producer: genotype roles inferred from filename substrings with implicit default WT/APOE3, duplicate 2×2 cells overwritten in a dict, missing cells silently skipped. The four V1 labels happened to match independent public GEO titles, but these defaults are not permissible on altered input.

New modules:
* `analysis/therapeutic_perturbation_etl/scripts/gse240609_public_geo_sample_authority_v1.py` — frozen EXACT public GEO title/accession→genotype mapping, each bound to already authenticated source file basename and full SHA-256 from PR #77 producer receipts; exact four-source full 2×2 validation.
* `analysis/therapeutic_perturbation_etl/scripts/build_bulk_disease_context_effects_v2.py` — complete source checks BEFORE output creation, existing V1 results immutable, GSE241858 source-root checks, validated original 2×2, corrected `CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE` assay material and descriptive n=1 uncertainty.
* `tests/test_gse240609_public_geo_sample_authority_v1.py` — committed lightweight CSV versus GEO-title identity plus malformed source, swapped bytes, missing/duplicate factorial cell and actual V2 entrypoint early-stop adversaries. No skips.
* `analysis/therapeutic_perturbation_etl/GSE240609_PUBLIC_GEO_IDENTITY_REVIEW_20260923.md` — exact public title, original file digest, previous fallback defect and necessary GPU physical reexecution.

**PR #94 V2 CPU test PASS; physical V2 rerun NOT_EXECUTED.** Claude must run reviewed V2 on original authenticated source files in new output directory and independently compare unchanged original numerical expression contrasts to V1 within predeclared tolerance. Preserve no-uncertainty statement.

## Carry forward mandatory GSE311359 STOP from V21

Independent PR #92 @ `bc09c0f432db6e17bec3047baeb0812975043937` has 7/7 hosted red-team tests PASS. Its source SHA-pinned committed V1 guide-identity table has 381 rows but 379 distinct guide names, with `BIN1` repeated 3 times. PR #77 V1 producer collapses all three label keys into one per-sample pseudobulk index. Even though original V1 producer reported 27,737 assigned cells and 61/63 TSS genes repressed, do NOT promote its guide-level effects to fully qualified independent benchmark inputs until physically reviewed feature-ID→protospacer library identity and a versioned corrected V2 extraction.

GSE178317 guide-to-cell STOP also unchanged: authenticated processed enrichment arrays lack guide features; recover independent guide data or retain only LPS/differentiation-context bulk.

## Immediate parallel next work

Claude GPU: resolve GSE311359 duplicate BIN1 source features against real library before rerun; execute GSE240609 V2 public-GEO-pinned sample/byte-root validation and old-vs-new effect parity; proceed with authenticated GSE175721 organoid guide assignment, GSE301119 transcriptome-wide donor-aware DE, and remaining GSE254205 snRNA/ATAC/LD-sort assays; review GSE241858 clone-appropriate inferential limits.

Independent CPU: integrate #82 execution authority, #84/#88/#90 donor-balanced, target-excluded benchmark and exposure gate (metadata only until real outcomes qualified); #87/#89 cross-study feature schema requires separately authenticated actual gene annotation release; preserve SHA-pinned real metadata guide support #91. Independent red-team source contracts and never silently merge data from conflicting study designs.

FULL104: independently review #85 (successor to real adapter #83), maintain N1 hard STOP and all-104 raw-count reaggregation open. Do not open any protected experiment to settle software choices.

## Navigational PR snapshot

PR #77 `3e293a43e4d6dfb6bba85eaf188bdbbe5ecb2821`; PR #92 `bc09c0f432db6e17bec3047baeb0812975043937`; PR #94 `9cc155a659f9a70bf2f1e7a1fd9cc05283089cbf`; canonical V21 main handoff merged at `f5b70ae08c728b8336629cba0a61d1462d969225`. Re-fetch all SHA heads, workflow conclusions and actual script bytes before another change. Any changed upstream experimental code may require branch rebasing and requalification. This docs addendum is NOT a claim that PR #92 or #94 is merged into Claude's producer branch.

**Decision/claim boundary:** V1 physical producer outputs remain historical; V2 code/CI is not V2 physical execution; original study manuscripts' biological findings are not independently recreated merely by accessing processed tables.
