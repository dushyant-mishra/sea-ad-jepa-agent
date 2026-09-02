# WINDOWS_WSL_TOPOLOGY.md — Canonical Project + Compute Backends

## Canonical project
Windows:
`D:\Jepa project`

This is the authoritative Antigravity IDE workspace and Git/project location.

## WSL view of the same files
`/mnt/d/Jepa project`

This is not a second clone. It is the same underlying project filesystem.

## Operating rule
Agent/IDE may remain Windows-native.
Compute may be Windows-native or WSL-native.

Examples:
- Windows Python / PowerShell against `D:\Jepa project`
- WSL Python/R/CUDA environment against `/mnt/d/Jepa project`

Do not relocate the repo to `~/Jepa project` just because a Linux environment is useful.

## Path handling
Prefer project-relative paths:
- `data/...`
- `results/...`
- `scripts/...`
- `src/...`

When absolute paths are unavoidable:
- Windows: `D:\Jepa project\<relative>`
- WSL: `/mnt/d/Jepa project/<relative>`

Historical artifacts may contain either syntax. Do not rewrite them solely for path normalization.

## Environment provenance
A Windows/WSL execution change is an execution-environment change, not a change in scientific dataset/project identity.

Record:
- OS/backend
- executable path
- Python/R version
- Torch/CUDA version
- GPU
- project root representation
- git HEAD
- relevant file hashes

## Integrity check
When switching backends, verify:
- both resolve the same git HEAD
- both point to the same project root contents
- no second clone is being used accidentally
