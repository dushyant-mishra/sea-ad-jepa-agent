# F1 contextual statistical estimand contract (pre-result)

For LayerNorm states, `cos(a,b)=dot(a,b)/(||a|| ||b||)`. For each recipient/query/evidence:

`A(c,q,e)=cos(S_correct(c,q,e),T_true(c,q))-cos(S_null(c,q,e),T_true(c,q))`.

The query-safe direct-token analogue uses `LN(Hq)` from the identical correct/null/teacher forwards and provenance: `A_direct=cos(D_correct,D_true)-cos(D_null,D_true)`. `Delta_ctx_minus_direct=A-A_direct`. Squared Euclidean is related telemetry only and creates no decision family.

All scalar comparisons occur per query before aggregation. Given an externally frozen operator prefix, the overall query-local cell effect is the equal mean over its lawful unique queries. For program k/operator o, query weight is `w(q,k)^2 / sum_{queried lawful q} w(q,k)^2`; the weighted mean of per-query A is `PANEL_CONDITIONED_PROGRAM_ADVANTAGE`. Never average 160-D states across q before A.

Hierarchy: average replicate cells within donor×operator; average lawful operators within donor; then give each donor equal weight. Source/operator-stratified donor summaries are separate. Primary evidence is 60%; 20/40/80/100 are secondary.

Evidence trend: for each donor, fit the OLS slope of its five A values against centered evidence fractions `(0.2,0.4,0.6,0.8,1.0)`; the population statistic is the equal-donor mean slope.

Query-identity vetoes at 60%: (1) within-cell correct-query margin `cos(S_cq,T_cq)-max_{q'!=q}cos(S_cq,T_cq')`, aggregated query→cell→donor; (2) within-cell Spearman correlation of upper-triangle S-vs-S and T-vs-T cross-query similarities, aggregated cell→donor. Ties use average Spearman ranks; max ties remain equal maxima.

Same-source, same-operator and same-donor distinct-cell margins use cosine and the frozen lawful candidate sets and are descriptive/falsification diagnostics. Source/operator/donor/support/depth audits are mandatory. All missingness is physical-support missingness and is reported; it is never imputed.
