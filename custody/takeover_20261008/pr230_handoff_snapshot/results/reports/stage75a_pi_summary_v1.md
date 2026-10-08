# Stage75A PI summary

Stage75A agrees with the critique of Stage74: the current perturbation audit is
a useful proof of concept, but not a state-specific perturbation simulator.

Current readiness:

- GSE174367 RNA/ATAC files available: `True`
- SCENIC+/CellOracle dependency stack complete: `False`
- motif/ranking/peak-to-gene resources complete: `False`
- ready for true Stage75B SCENIC+ run: `False`

Recommendation: acquire/install the missing SCENIC+/CellOracle resources in a
separate environment, then run Stage75B eGRN construction.
