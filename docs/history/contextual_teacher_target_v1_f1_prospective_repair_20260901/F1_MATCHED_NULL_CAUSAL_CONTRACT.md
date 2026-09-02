# F1 matched-null causal contract (pre-result)

For recipient cell `c`, query `q`, and evidence level `e`, the single primary matched control is a wrong-input test against the true recipient teacher.

- `T_true(c,q)`: recipient normalized values, recipient three-state `M_physical`, all lawful scalar context except q, q identity retained and q scalar withheld; teacher role; exact all-eligible context mean.
- `S_correct(c,q,e)`: recipient normalized values and recipient `M_physical/U_evidence(e,q)`; student role.
- `S_null(c,q,e)`: normalized scalar vector from the frozen donor-distinct source row `P(c)`, but recipient `M_physical`, `U_evidence(e,q)`, q identity, operator/source and row query identity. Both source and recipient must bind to authenticated reader-fit lineage/assets and exactly-once normalization.

Every comparison uses the same `T_true(c,q)`. A nullized teacher is forbidden because it would create a coherent pseudo-cell rather than test recovery of recipient biology. Post-H substitution is forbidden.

The within-operator bijection exactly preserves raw source-row expression marginals, measured-zero frequencies, and cross-gene covariance on the frozen evaluation population. This claim is intentionally limited to the unconditional source-expression row matrix: the recipient-conditioned evidence/query masking is retained rather than permuted, so no query/evidence-conditioned input-covariance preservation is claimed.

Tensor DAG: `recipient identity/operator -> recipient M_physical -> recipient U_evidence/q mask`; `P(c) authenticated normalized values -> six-block student forward -> S_null`; `recipient normalized values -> rich safe teacher forward -> T_true`; then `cos(S_correct,T_true)-cos(S_null,T_true)`. The permutation occurs before the encoder. It changes normalized values, not M, U, q, operator or source.

Caching: `T_true` is reusable across all five evidence levels and the matched-null comparison. `S_correct` differs across evidence levels. Every distinct `(null input,e,q)` requires its own six-block forward. No context cap/subsampling is lawful.
