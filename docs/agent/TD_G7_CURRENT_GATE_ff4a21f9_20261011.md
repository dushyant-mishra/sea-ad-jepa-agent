# Target discovery — current G7 gate

Replacement G6 at exact executable head `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0` is externally accepted.

External disposition:

`ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY`

Accepted G6 evidence:
- evidence branch `evidence/td-g6-replacement-ff4a21f9-20261011`
- evidence commit `c595af589821bee28eb77e88e44b79dc81835e7a`
- receipt terminal `PASS_TD_G6_SOURCE_LIBRARY_EXACT`
- G6 receipt SHA-256 `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`
- values SHA-256 `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`
- metadata SHA-256 `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`

The detected-count diagnostic is accepted as an audit diagnostic: 22,560 changed rows are all SEA_AD; HVS has 0 changes; NPH52 has 0 by authenticated pass-through construction. This does not create biological authority.

Fresh G7 operational authorization:

`custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee`

Operational scope:

`EXECUTE_G7_ONCE_AT_ff4a21f9__AGAINST_ACCEPTED_G6__FRESH_OUTPUT__STOP_FOR_EXTERNAL_AUDIT`

G7 must still use the exact code-consumed G6/G7 integrity authority bytes required by the executable:
- owner decision SHA-256 `3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`
- runtime authorization SHA-256 `28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Expected G7 PASS terminal:

`PASS_TD_G7_S174_EXACT_OVERLAP`

G7 is one attempt only. Use a fresh output path. Once its start marker exists, preserve the outcome and do not repair or rerun in place.

STOP after G7 and return the complete evidence for external audit.

Still unauthorized: corrected TD56/57B/57C/59 replay, TD60, target selection, representation selection, Stage4, and training.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
