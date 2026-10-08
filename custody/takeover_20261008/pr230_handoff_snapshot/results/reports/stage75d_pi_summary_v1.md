# Stage75D PI summary

Stage75D prepared the WSL execution scripts needed before a true SCENIC+ eGRN
run. It did not install or download the large DBs inside Codex.

Run in WSL from the repo root:

```bash
bash scripts/stage75d_create_scenicplus_env_wsl.sh
bash scripts/stage75d_download_large_cistarget_resources_wsl.sh
```

Then Stage75E should verify the environment/files before running SCENIC+.
