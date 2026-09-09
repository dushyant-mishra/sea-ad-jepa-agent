# Do not merge until real T0 artifacts replay — 2026-09-09

This review branch records the next target and should not be confused with a production candidate.

Do not merge R5/R6 production claims into `main` as accepted authority until these exist:

1. real 20,804-row raw-source population authority package;
2. replay report for that package;
3. real technical-completeness package;
4. replay report for that package;
5. exact artifact paths, sizes, SHA-256 hashes and package roots;
6. unchanged downstream gate statements.

Until then the correct status remains:

`STOP_T0_R5_REAL_POPULATION_AUTHORITY_NOT_MATERIALIZED`
