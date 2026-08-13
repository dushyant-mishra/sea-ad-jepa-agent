# Stage81A3 Local-Only Artifact Policy

This checkpoint tracks compact, reviewable Stage81A3 reports and evidence
tables. It intentionally does not track model/checkpoint binaries, NumPy
diagnostic caches, run logs, or two large row-level detail tables. These files
are not authority surfaces and must not be mistaken for frozen architecture or
scientific decisions.

The exact local paths, byte sizes, SHA-256 values, roles, and reconstruction
scripts are recorded in
`results/v4/stage81a3_local_only_artifact_manifest.csv`. The source datasets
remain under `data/` and are intentionally outside Git; their official sources,
download hashes, and acquisition decisions are recorded by the tracked
Stage81A1 acquisition manifests and builders.

The omitted binary checkpoints belong to diagnostic or rejected RBB routes.
They are retained locally for forensic reproducibility but are not production
models. The two omitted large CSV files are deterministic detail outputs whose
review-level summaries and generating code are tracked. Pytest basetemp trees,
`.tmp/`, logs, raw data, and downloaded source archives remain machine-local.

Absence from Git does not authorize deletion. Any future cleanup must first
verify the corresponding hash and confirm that the artifact is reproducible or
superseded under the then-current governance state.
