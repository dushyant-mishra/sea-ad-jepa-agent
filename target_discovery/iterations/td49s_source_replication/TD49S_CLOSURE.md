# TD49S closure — NPH52 source-internal replication fails

Status: `NO_INDEPENDENT_SOURCE_REPLICATION_OF_QUERY_ORDINAL_TARGET__TD49S_FAIL`

Prospective freeze: `d44fe9c12513c1b4130e827528f5879eb68413e0`

Sequential rule required NPH52 first and prohibited SEA_AD execution if NPH52 failed.

NPH52:
- exact rank-sketch dense validation max difference: 6.66e-16
- 64/64 query coordinates measurable
- shortcut selected lambda multiplier: 0.01
- molecular broad-context selected multiplier: 10
- shortcut MSE: 0.6175976
- molecular MSE: 0.6286762
- Delta_tau: **-0.0179381**
- 23/64 query coordinates positive

Because observed Delta_tau <= 0, NPH52 fails PASS_SOURCE and no null refits are required to establish the prospective failure.

Per the frozen sequential rule, SEA_AD was not run.

The HVS TD48 result therefore does not establish source-internal replication.
No target/training authority.
