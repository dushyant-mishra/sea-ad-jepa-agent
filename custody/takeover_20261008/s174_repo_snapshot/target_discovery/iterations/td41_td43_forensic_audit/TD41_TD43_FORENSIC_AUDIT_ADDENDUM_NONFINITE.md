# TD41/TD43 forensic audit technical addendum — non-finite dominance

Status: `FORENSIC_AUDIT_TECHNICAL_BINDING__FIRST_STRATIFICATION_QUARANTINED`

The first implementation of the pair-informativeness stratification exposed 17/4096 TD41 pairs in panel 0 for which the pooled dominance score was non-finite because at least one source lacked a finite conditional donor-mean direction.

The original protocol did not specify how such pairs enter equal-count quartiles. The first code path sorted them to the end and therefore contaminated Q4. Those first quartile outputs are `QUARANTINED_DIAGNOSTIC_ONLY` and may not support interpretation.

Binding treatment for the forensic audit:
1. calculate finite pooled dominance exactly as in the parent protocol;
2. pairs without finite pooled dominance are assigned only to `NOT_MEASURABLE_DOMINANCE`;
3. sort only finite pairs by (dominance, TD41 pair hash);
4. divide the finite sorted list into four strata with `numpy.array_split`, so stratum sizes differ by at most one;
5. report the non-finite count and its reason separately;
6. no non-finite pair contributes to Q1-Q4 statistics.

This changes no TD41 or TD43 scientific result or target definition. It only repairs an under-specified forensic stratification before any stratum-level interpretation is accepted.
