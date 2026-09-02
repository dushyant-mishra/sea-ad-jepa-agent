# Dataset-Fidelity Review — V8 Round 1

VERDICT: PASS

1. The externally anchored frozen metadata manifest and all seven NPH lineage shards were independently authenticated and reopened. The derivatives contain exactly 236,476 unique lawful cells from 17 reader-fit donors across operators 35–41, with zero rows from `human_NPH_1025` or `human_NPH_878`.
2. The unchanged selection SHA-256 is `2f2eacee4274a0e07684e1744adf3750aae6b712f86264e061ccf517a6240acb`: 84 unique lawful reader-fit cells, exactly two per each of 42 operators. The only model inputs are float32 `normalized_values` and uint8 `observation_states`, shape 84 x 41,238. Non-scalar numeric entries are zero and 1,751,880 measured-zero slots remain measured evidence.
3. All 42 source assets are authenticated (24 HVS, 11 SEA-AD, seven fit-only NPH derivatives). Deterministic replay and row identity pass. No protected-expression access, Phase-2 derivation, calibration, or training occurred.

Falsification: any derivative with an extra, missing, duplicate, non-fit, or protected cell; any changed authority/asset/selection hash; any non-scalar nonzero; any third model-input field; or any invalid package root revokes this PASS.

Reviewed artifacts include `NPH_READER_FIT_FRESH_PROCESS_VERIFICATION.csv`, `interface_check_v8r1/FULL104_EXPRESSION_INTERFACE_PREFLIGHT.json`, `model_inputs/FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz`, and the package manifest/external anchor.
