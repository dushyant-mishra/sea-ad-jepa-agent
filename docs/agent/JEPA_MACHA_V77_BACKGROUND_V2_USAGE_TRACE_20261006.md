# JEPA Macha/V77 — Background V2 usage trace

Date: 2026-10-06
Parent audit head before write: `8df6345d6126eed8d45046057051ba13938aace9`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

Background V2 is scientifically S149-contaminated as a biological calibration because it was designed to imitate the historical pooled RNA graph. However, the later evidence checked in this audit does not silently inherit Background V2.

Independent provenance checks show Background V1 for:

- preserved 100K/full-scale V77 worlds in `V77_SUPERSEDED_REBUILD_CUSTODY_V1.json`;
- world A_REPLICA, B, C, D, E, FULL and suppressed-component twins listed there;
- repaired S146/S147 component detect/reject rerun (`OBS_ARGS --background v1`);
- the current S157 paired challenge (`--background v1`).

The observer CLI also defaults to `--background v1`; V2 must be selected explicitly.

## Classification

`BACKGROUND_V2_BIOLOGICAL_CALIBRATION = S149_SUPERSEDED`

but

`BACKGROUND_V2_SILENT_SPILLOVER_INTO_AUDITED_CURRENT_S146_S147_OR_S157_EVIDENCE = NOT_FOUND`

This is an important distinction. The contaminated idea remains in the repository for historical/mechanistic work, but the current repaired-support and S157 evidence audited here are not downstream of it.

## Biological meaning

We do not need to throw away the newer identifiability and support-repair findings because an older synthetic background was tuned to a bad real-data graph. Those newer experiments used the simpler V1 background instead.

The V1 background is not thereby biologically validated; it is simply not contaminated by that specific S149 calibration route.

## Remaining caution

Some historical Step-3/search/dynamic-range receipts still use pooled real envelopes or pooled-derived logic even when they do not use Background V2 directly. Those receipts remain quarantined by the earlier audit documents and must not regain biological authority merely because their underlying observer used V1.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object, calibration target or estimand winner.
